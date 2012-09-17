#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
The obfs2 module implements the obfs2 protocol.
"""

import os

import random
import hmac
import hashlib
import b64

from obfsproxy.common.aes import AESCoder
from obfsproxy.transports.base import BaseDaemon

MAGIC_VALUE = decode('2BF5CA7E')
SEED_LENGTH = 16
MAX_PADDING = 8192
HASH_ITERATIONS = 100000

KEYLEN = 16  # is the length of the key used by E(K,s) -- that is, 16.
IVLEN = 16  # is the length of the IV used by E(K,s) -- that is, 16.

HASHLEN = 16  # is the length of the output of H() -- that is, 32.

READ_SEED = 0
READ_PADKEY = 1
READ_PADLEN = 2
READ_PADDING = 3
STREAM = 4


def h(x):
    """ H(x) is SHA256 of x. """

    hasher = hashlib.sha256()
    hasher.update(x)
    return hasher.digest()


def hn(x, n):
    """ H^n(x) is H(x) called iteratively n times. """

    data = x
    for x in range(n):
        data = h(data)
    return data


def e(k, s):
    """ E(k,s) is the AES-CTR-128 encryption of s using K as key. """

    cipher = AESCoder(k)
    return cipher.encode(s)


def d(k, s):
    """ D(k, s) is the AES-CTR-128 decryption of s using K as key. """

    cipher = AESCoder(k)
    return cipher.decode(s)


def uint32(n):
    """ UINT32(n) is the 4 byte value of n in big-endian (network) order. """

    return struct.pack('!I', n)


def decodeUint32(bs):
    """
    decodeUint32(bs) is the reverse of uint32(n).
    It returns the int value represneted by the 4 byte big-endian (network) order encoding represented by bs.
    """

    return struct.unpack('!I', bs)[0]


def sr(n):
    """ SR(n) is n bytes of strong random data. """

    return os.urandom(n)


def wr(n):
    """ WR(n) is n bytes of weaker random data. """

    return ''.join(chr(random.randint(0, 255)) for _ in range(n))


def mac(s, x):
    """ # MAC(s, x) = H(s | x | s) """

    return h(s + x + s)

class Obfs2Daemon(BaseDaemon):

    """
    Obfs2Daemon implements the obfs2 protocol.
    It is subclassed by Obfs2Client and Obfs2Server.
    """

    def __init__(self, downstreamConnection, upstreamConnection):
        """
        Initializes the Obfs2Daemon instance with the upstream and downstream connections.
        Also initializes the seed, padkey, and padlen buffers to be empty byte strings.
        """

        self.downstreamConnection = downstreamConnection
        self.upstreamConnection = upstreamConnection
        self.otherSeed = bytes('')
        self.otherPadKeyEncrypted = bytes('')
        self.otherPadLenBytes = bytes('')

    def start(self):
        """
        This is the callback method which is called by the framework when a new connection has been made.
        In the obfs2 protocol, on start the seed, encrypted magic value, padding length, and padding are written upstream.
        """

        # The initiator generates:
        # INIT_SEED = SR(SEED_LENGTH)

        self.seed = sr(SEED_LENGTH)
        self.padKey = self.derivePadKey(self.seed, self.padString)

        # Each then generates a random number PADLEN in range from 0 through MAX_PADDING (inclusive).

        self.padLen = random.nextInt(MAX_PADDING) % MAX_PADDING

        # The initiator then sends:
        # INIT_SEED | E(INIT_PAD_KEY, UINT32(MAGIC_VALUE) | UINT32(PADLEN) | WR(PADLEN))

        self.server.write(self.seed + e(self.padKey,
                          uint32(MAGIC_VALUE)) + uint32(self.padLen)
                          + wr(self.padLen))

        self.state = READ_SEED

    def receivedDownstream(self):
        """
        This is the callback method which is called by the framework when bytes have been received on the downstream socket.
        In the obfs2 protocol, downstream bytes are buffered until the handshake is complete and the protocol is in STREAM mode, at which point all bytes received from downstream are encrypted and sent upstream.
        """

        if state == STREAM:
            data = self.downstreamConnection.read_some()
            encodedData = e(padKey, data)
            self.upstreamConnection.write(encodedData)

    def receivedUpstream(self):
        """
        This is the callback method which is called by the framework when bytes have been received on the upstream socket.
        In the obfs2 protocol, the upstream data stream is read to find the following values:
            - seed
            - padding key
            - padding length
            - padding
        The protocol is then switched to STREAM mode, at which point all bytes received from upstream are encrypted and sent downstream.
        """

        if state == READ_SEED:
            self.otherSeed = self.read(self.upstreamConnection,
                    self.otherSeed, SEED_LENGTH)
            if self.checkTransition(self.otherSeed, SEED_LENGTH,
                                    READ_PADKEY):
                self.otherPadKeyDerived = \
                    self.derivePadKey(self.otherSeed, not self.server)
        elif state == READ_PADKEY:
            self.otherPadKeyEncrypted = \
                self.read(self.upstreamConnection,
                          self.otherPadKeyEncrypted, KEYLEN)
            if self.checkTransition(self.otherPadKeyEncrypted, KEYLEN,
                                    READ_PADLEN):
                if self.otherPadKeyEncrypted != self.otherPadKeyDerived:
                    self.upstreamConnection.disconnect()
                    self.downstreamConnection.disconnect()
        elif state == READ_PADLEN:
            self.otherPadLenBytes = self.read(self.upstreamConnection,
                    self.otherPadLenBytes, 4)
            if self.checkTransition(self.otherPadLenBytes, 4,
                                    READ_PADDING):
                self.otherPadLen = decodeUint32(self.otherPadLenBytes)
                if self.otherPadLen > MAX_PADDING:
                    self.upstreamConnection.disconnect()
                    self.downstreamConnection.disconnect()
        elif state == READ_PADDING:
            self.otherPadding = self.read(self.upstreamConnection,
                    self.otherPadding, self.otherPadLen)
            if self.checkTransition(self.otherPadding,
                                    self.otherPadLen, READ_PADDING):
                self.secret = self.deriveSecret(self.seed,
                        self.otherSeed, self.server)
                self.otherSecret = self.deriveSecret(self.otherSeed,
                        self.seed, not self.server)

                # INIT_KEY = INIT_SECRET[:KEYLEN]
                # RESP_KEY = RESP_SECRET[:KEYLEN]

                self.key = self.secret[:KEYLEN]
                self.otherKey = self.otherSecret[:KEYLEN]

                # INIT_IV = INIT_SECRET[KEYLEN:]
                # RESP_IV = RESP_SECRET[KEYLEN:]

                self.iv = self.secret[KEYLEN:]
                self.otheriv = self.otherSecret[KEYLEN:]

                self.cipher = initCipher(self.iv, self.key)
                self.otherCipher = initCipher(self.otheriv,
                        self.otherKey)
        elif state == STREAM:
            data = self.upstreamConnection.read_some()
            decodedData = d(padKey, data)
            self.downstreamConnection.write(decodedData)

    def derivePadKey(self, seed, padString):
        """ derivePadKey returns the MAC of the padString and seed. """

        return mac(padString, seed)[:KEYLEN]

    def deriveSecret(
        self,
        seed,
        otherSeed,
        server,
        ):
        """ deriveSecret returns the MAC of the stored padString, the seed, and the otherSeed. """

        if server:

            # RESP_SECRET = MAC("Responder obfuscated data", INIT_SEED|RESP_SEED)

            return mac(self.padString, otherSeed + seed)
        else:

            # INIT_SECRET = MAC("Initiator obfuscated data", INIT_SEED|RESP_SEED)

            return mac(self.padString, seed + otherSeed)

    def initCipher(self, iv, key):
        """ initCipher initializes the AES cipher using the given key and IV. """

        coder = AESCoder(key)
        coder.encode(iv)
        return coder

    def end(self):
        """
        This is the callback method which is called by the framework when the connection is closed.
        In Obfs2Daemon it does nothing.
        """

        pass


class Obfs2Client(Obfs2Daemon):

    """
    Obfs2Client is a client for the obfs2 protocol.
    The client and server differ in terms of their padding strings.
    """

    def __init__(self, downstreamConnection, upstreamConnection):
        self.padString = 'Initiator obfuscation padding'
        self.otherPadString = 'Responder obfuscation padding'


class Obfs2Server(Obfs2Daemon):

    """
    Obfs2Server is a server for the obfs2 protocol.
    The client and server differ in terms of their padding strings.
    """

    def __init__(self, downstreamConnection, upstreamConnection):
        self.padString = 'Responder obfuscation padding'
        self.otherPadString = 'Initiator obfuscation padding'


