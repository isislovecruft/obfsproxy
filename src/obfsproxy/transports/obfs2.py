#!/usr/bin/python
# -*- coding: utf-8 -*-

import os

import random
import hmac
import hashlib
import base64

from obfsproxy.crypto.aes import AESCoder
from obfsproxy.util import decode, uncompact
from obfsproxy.transports.base import BaseDaemon

MAGIC_VALUE      = decode('2BF5CA7E')
SEED_LENGTH      = 16
MAX_PADDING      = 8192
HASH_ITERATIONS  = 100000

KEYLEN = 16 # is the length of the key used by E(K,s) -- that is, 16.
IVLEN  = 16 # is the length of the IV used by E(K,s) -- that is, 16.

HASHLEN = 16 # is the length of the output of H() -- that is, 32.

READ_SEED=0
READ_PADKEY=1
READ_PADLEN=2
READ_PADDING=3
STREAM=4

# H(x) is SHA256 of x.
def h(x):
    hasher = hashlib.sha256()
    hasher.update(x)
    return hasher.digest()

# H^n(x) is H(x) called iteratively n times.
def hn(x, n):
    data=x
    for x in range(n):
        data=h(data)
    return data

# E(k,s) is the AES-CTR-128 encryption of s using K as key.
def e(k, s):
    cipher=AESCoder(k)
    return cipher.encode(s)

# D(k, s) is the AES-CTR-128 decryption of s using K as key.
def d(k, s):
    cipher=AESCoder(k)
    return cipher.decode(s)

# UINT32(n) is the 4 byte value of n in big-endian (network) order.
def uint32(n):
    return struct.pack('!I', (n))

def decodeUint32(bs):
    return struct.unpack('!I', bs)[0]

# SR(n) is n bytes of strong random data.
def sr(n):
    return os.urandom(n)

# WR(n) is n bytes of weaker random data.
def wr(n):
    return ''.join(chr(random.randint(0,255)) for _ in range(n))

# MAC(s, x) = H(s | x | s)
def mac(s, x):
    return h(s+x+s)

class Obfs2Daemon(BaseDaemon):

    def __init__(self, decodedSocket, encodedSocket):
        self.decodedSocket=decodedSocket
        self.encodedSocket=encodedSocket
        self.otherSeed=bytes('')
        self.otherPadKeyEncrypted=bytes('')
        self.otherPadLenBytes=bytes('')

    def start(self):
        # The initiator generates:
        # INIT_SEED = SR(SEED_LENGTH)

        self.seed=sr(SEED_LENGTH)
        self.padKey=self.derivePadKey(self.seed, self.padString)

        # Each then generates a random number PADLEN in range from 0 through MAX_PADDING (inclusive).
        self.padLen=random.nextInt(MAX_PADDING) % MAX_PADDING

        # The initiator then sends:
        # INIT_SEED | E(INIT_PAD_KEY, UINT32(MAGIC_VALUE) | UINT32(PADLEN) | WR(PADLEN))
        self.server.write(self.seed+e(self.padKey, uint32(MAGIC_VALUE))+uint32(self.padLen)+wr(self.padLen))

        self.state=READ_SEED

    def receivedDecoded(self):
        if state==STREAM:
            data=self.decodedSocket.readAll()
            encodedData=encode(data)
            self.encodedSocket.write(encodedData)

    def receivedEncoded(self):
        if state==READ_SEED:
            self.otherSeed=self.read(self.encodedSocket, self.otherSeed, SEED_LENGTH)
            if self.checkTransition(self.otherSeed, SEED_LENGTH, READ_PADKEY):
                self.otherPadKeyDerived=self.derivePadKey(self.otherSeed, not self.server)
        elif state==READ_PADKEY:
            self.otherPadKeyEncrypted=self.read(self.encodedSocket, self.otherPadKeyEncrypted, KEYLEN)
            if self.checkTransition(self.otherPadKeyEncrypted, KEYLEN, READ_PADLEN):
                if self.otherPadKeyEncrypted!=self.otherPadKeyDerived:
                    self.encodedSocket.disconnect()
                    self.decodedSocket.disconnect()
        elif state==READ_PADLEN:
            self.otherPadLenBytes=self.read(self.encodedSocket, self.otherPadLenBytes, 4)
            if self.checkTransition(self.otherPadLenBytes, 4, READ_PADDING):
                self.otherPadLen=decodeUint32(self.otherPadLenBytes)
                if self.otherPadLen>MAX_PADDING:
                    self.encodedSocket.disconnect()
                    self.decodedSocket.disconnect()
        elif state==READ_PADDING:
            self.otherPadding=self.read(self.encodedSocket, self.otherPadding, self.otherPadLen)
            if self.checkTransition(self.otherPadding, self.otherPadLen, READ_PADDING):
                self.secret=self.deriveSecret(self.seed, self.otherSeed, self.server)
                self.otherSecret=self.deriveSecret(self.otherSeed, self.seed, not self.server)
                # INIT_KEY = INIT_SECRET[:KEYLEN]
                # RESP_KEY = RESP_SECRET[:KEYLEN]
                self.key=self.secret[:KEYLEN]
                self.otherKey=self.otherSecret[:KEYLEN]

                # INIT_IV = INIT_SECRET[KEYLEN:]
                # RESP_IV = RESP_SECRET[KEYLEN:]
                self.iv=self.secret[KEYLEN:]
                self.otheriv=self.otherSecret[KEYLEN:]

                self.cipher=initCipher(self.iv, self.key)
                self.otherCipher=initCipher(self.otheriv, self.otherKey)
        elif state==STREAM:
            data=self.encodedSocket.readAll()
            decodedData=decode(data)
            self.decodedSocket.write(decodedData)

    def derivePadKey(self, seed, padString):
        return mac(padString, seed)[:KEYLEN]

    def deriveSecret(self, seed, otherSeed, server):
        if server:
            # RESP_SECRET = MAC("Responder obfuscated data", INIT_SEED|RESP_SEED)
            return mac(self.padString, otherSeed+seed)
        else:
            # INIT_SECRET = MAC("Initiator obfuscated data", INIT_SEED|RESP_SEED)
            return mac(self.padString, seed+otherSeed)

    def initCipher(self, iv, key):
        coder=AESCoder(key)
        coder.encode(iv)
        return coder

    def end(self):
        pass

class Obfs2Client(Obfs2Daemon):

    def __init__(self, decodedSocket, encodedSocket):
        self.padString='Initiator obfuscation padding'
        self.otherPadString='Responder obfuscation padding'

class Obfs2Server(Obfs2Daemon):

    def __init__(self, decodedSocket, encodedSocket):
        self.padString='Responder obfuscation padding'
        self.otherPadString='Initiator obfuscation padding'
