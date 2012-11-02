#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
The obfs2 module implements the obfs2 protocol.
"""

import os
import random
import hashlib
import struct

import obfsproxy.common.aes as aes
import obfsproxy.transports.base as base

import obfsproxy.common.log as log

MAGIC_VALUE = 0x2BF5CA7E
SEED_LENGTH = 16
MAX_PADDING = 8192
HASH_ITERATIONS = 100000

KEYLEN = 16  # is the length of the key used by E(K,s) -- that is, 16.
IVLEN = 16  # is the length of the IV used by E(K,s) -- that is, 16.
HASHLEN = 16  # is the length of the output of H() -- that is, 32.

ST_WAIT_FOR_KEY = 0
ST_WAIT_FOR_PADDING = 1
ST_OPEN = 2

def h(x):
    """ H(x) is SHA256 of x. """

    hasher = hashlib.sha256()
    hasher.update(x)
    return hasher.digest()


def hn(x, n):
    """ H^n(x) is H(x) called iteratively n times. """

    for _ in xrange(n):
        data = h(x)
    return data

def htonl(n):
    return struct.pack('!I', n)


def ntohl(bs):
    return struct.unpack('!I', bs)[0]


def random_bytes(n):
    """ Returns n bytes of strong random data. """

    return os.urandom(n)

def mac(s, x):
    """ # MAC(s, x) = H(s | x | s) """

    return h(s + x + s)

class Obfs2Transport(base.BaseTransport):
    """
    Obfs2Transport implements the obfs2 protocol.
    """

    def __init__(self):
        """Initialize the obfs2 pluggable transport."""

        # Our state.
        self.state = ST_WAIT_FOR_KEY

        if self.we_are_initiator:
            self.initiator_seed = random_bytes(SEED_LENGTH) # Initiator's seed.
            self.responder_seed = None # Responder's seed.
        else:
            self.initiator_seed = None # Initiator's seed.
            self.responder_seed = random_bytes(SEED_LENGTH) # Responder's seed

        # Shared secret seed.
        self.secret_seed = None

        # Crypto to encrypt outgoing data.
        self.send_crypto = None
        # Crypto to encrypt outgoing padding. Generate it now.
        self.send_padding_crypto = \
            self._derive_padding_crypto(self.initiator_seed if self.we_are_initiator else self.responder_seed,
                                     self.send_pad_keytype)
        # Crypto to decrypt incoming data.
        self.recv_crypto = None
        # Crypto to decrypt incoming padding.
        self.recv_padding_crypto = None

        # Number of padding bytes left to read.
        self.padding_left_to_read = 0

        # If it's True, it means that we received upstream data before
        # we had the chance to set up our crypto (after receiving the
        # handshake). This means that when we set up our crypto, we
        # must remember to push the cached upstream data downstream.
        self.pending_data_to_send = False

    def handshake(self, circuit):
        """
        Do the obfs2 handshake:
        SEED | E_PAD_KEY( UINT32(MAGIC_VALUE) | UINT32(PADLEN) | WR(PADLEN) )
        """

        padding_length = random.randint(0, MAX_PADDING)
        seed = self.initiator_seed if self.we_are_initiator else self.responder_seed

        handshake_message = seed + self.send_padding_crypto.crypt(htonl(MAGIC_VALUE) + htonl(padding_length) + random_bytes(padding_length))

        log.debug("obfs2 handshake: %s queued %d bytes (padding_length: %d).",
                  "initiator" if self.we_are_initiator else "responder",
                  len(handshake_message), padding_length)

        circuit.downstream.write(handshake_message)

    def receivedUpstream(self, data, circuit):
        """
        Got data from upstream. We need to obfuscated and proxy them downstream.
        """
        if not self.send_crypto:
            log.debug("Got upstream data before doing handshake. Caching.")
            self.pending_data_to_send = True
            return

        log.debug("obfs2 receivedUpstream: Transmitting %d bytes.", len(data))
        # Encrypt and proxy them.
        circuit.downstream.write(self.send_crypto.crypt(data.read()))

    def receivedDownstream(self, data, circuit):
        """
        Got data from downstream. We need to de-obfuscate them and
        proxy them upstream.
        """
        log_prefix = "obfs2 receivedDownstream" # used in logs

        if self.state == ST_WAIT_FOR_KEY:
            log.debug("%s: Waiting for key." % log_prefix)
            if len(data) < SEED_LENGTH + 8:
                log.debug("%s: Not enough bytes for key (%d)." % (log_prefix, len(data)))
                return data # incomplete

            if self.we_are_initiator:
                self.responder_seed = data.read(SEED_LENGTH)
            else:
                self.initiator_seed = data.read(SEED_LENGTH)

            # Now that we got the other seed, let's set up our crypto.
            self.send_crypto = self._derive_crypto(self.send_keytype)
            self.recv_crypto = self._derive_crypto(self.recv_keytype)
            self.recv_padding_crypto = \
                self._derive_padding_crypto(self.responder_seed if self.we_are_initiator else self.initiator_seed,
                                            self.recv_pad_keytype)

            # XXX maybe faster with a single d() instead of two.
            magic = ntohl(self.recv_padding_crypto.crypt(data.read(4)))
            padding_length = ntohl(self.recv_padding_crypto.crypt(data.read(4)))

            log.debug("%s: Got %d bytes of handshake data (padding_length: %d, magic: %s)" % \
                          (log_prefix, len(data), padding_length, hex(magic)))

            if magic != MAGIC_VALUE:
                raise base.PluggableTransportError("obfs2: Corrupted magic value '%s'" % hex(magic))
            if padding_length > MAX_PADDING:
                raise base.PluggableTransportError("obfs2: Too big padding length '%s'" % padding_length)

            self.padding_left_to_read = padding_length
            self.state = ST_WAIT_FOR_PADDING

        while self.padding_left_to_read:
            if not data: return

            n_to_drain = self.padding_left_to_read
            if (self.padding_left_to_read > len(data)):
                n_to_drain = len(data)

            data.drain(n_to_drain)
            self.padding_left_to_read -= n_to_drain
            log.debug("%s: Consumed %d bytes of padding, %d still to come (%d).",
                      log_prefix, n_to_drain, self.padding_left_to_read, len(data))

        self.state = ST_OPEN
        log.debug("%s: Processing %d bytes of application data.",
                  log_prefix, len(data))

        if self.pending_data_to_send:
            log.debug("%s: We got pending data to send and our crypto is ready. Pushing!" % log_prefix)
            self.receivedUpstream(circuit.upstream.buffer, circuit) # XXX touching guts of network.py
            self.pending_data_to_send = False

        circuit.upstream.write(self.recv_crypto.crypt(data.read()))

    def _derive_crypto(self, pad_string): # XXX consider secret_seed
        """
        Derive and return an obfs2 key using the pad string in 'pad_string'.
        """
        secret = mac(pad_string, self.initiator_seed + self.responder_seed)
        return aes.AES_CTR_128(secret[:KEYLEN], secret[KEYLEN:])

    def _derive_padding_crypto(self, seed, pad_string): # XXX consider secret_seed
        """
        Derive and return an obfs2 padding key using the pad string in 'pad_string'.
        """
        secret = mac(pad_string, seed)
        return aes.AES_CTR_128(secret[:KEYLEN], secret[KEYLEN:])

class Obfs2Client(Obfs2Transport):

    """
    Obfs2Client is a client for the obfs2 protocol.
    The client and server differ in terms of their padding strings.
    """

    def __init__(self):
        self.send_pad_keytype = 'Initiator obfuscation padding'
        self.recv_pad_keytype = 'Responder obfuscation padding'
        self.send_keytype = "Initiator obfuscated data"
        self.recv_keytype = "Responder obfuscated data"
        self.we_are_initiator = True

        Obfs2Transport.__init__(self)


class Obfs2Server(Obfs2Transport):

    """
    Obfs2Server is a server for the obfs2 protocol.
    The client and server differ in terms of their padding strings.
    """

    def __init__(self):
        self.send_pad_keytype = 'Responder obfuscation padding'
        self.recv_pad_keytype = 'Initiator obfuscation padding'
        self.send_keytype = "Responder obfuscated data"
        self.recv_keytype = "Initiator obfuscated data"
        self.we_are_initiator = False

        Obfs2Transport.__init__(self)


