#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
The dust_transport module contains the DustDaemon, DustClient, and DustServer classes which implement the Dust transport.
"""

from dust.extensions.lite.lite_socket2 import lite_socket, makeSession, \
    makeEphemeralSession, createEphemeralKeypair
from dust.core.dust_packet import IV_SIZE, KEY_SIZE

from obfsproxy.transports.base import BaseDaemon

HANDSHAKE = 0
STREAM = 1

HANDSHAKE_SIZE = IV_SIZE + KEY_SIZE


class DustDaemon(BaseDaemon):

    """
    DustDaemon is the base class for DustClient and DustServer.
    It implements the functionality which is common across both the client and server implementations.
    """

    def __init__(self, downstreamConnection, upstreamConnection):
        """
        Initializes the daemon with a downstream and upstream socket.
        This also sets the protocol state to HANDSHAKE_WRITE and generates an ephemeral keypair.
        """

        BaseDaemon.__init__(self, downstreamConnection,
                            upstreamConnection)

        self.state = HANDSHAKE_WRITE
        self.ekeypair = createEphemeralKeypair()
        self.epub = bytes('')

    def start(self):
        """
        This is the callback method which is called by the framework when a new connection has been made.
        In the Dust protocol, on start the public part of the ephemeral keypair is written upstream.
        """

        self.upstreamConnection.write(self.ekeypair.public.bytes)

    def receivedDownstream(self):
        """
        This is the callback method which is called by the framework when bytes have been received on the downstream socket.
        In the Dust protocol, downstream bytes are buffered until the handshake is complete and the protocol is in STREAM mode, at which point all bytes received from downstream are encrypted and sent upstream.
        """

        # If we're in streaming mode, encode and write the incoming data

        if self.state == STREAM:
            data = self.downstreamConnection.readAll()
            if data:
                self.upstreamConnection.write(self.coder.encode(data))

        # Else do nothing, data will buffer until we've done the handshake

    def receivedUpstream(self, data):
        """
        This is the callback method which is called by the framework when bytes have been received on the upstream socket.
        In the Dust protocol, the upstream handshake is read, and then the protocol is switched to STREAM mode, at which point all bytes received from upstream are encrypted and sent downstream.
        """

        if self.state == HANDSHAKE:
            self.epub = self.read(self.upstreamConnection, self.epub,
                                  HANDSHAKE_SIZE)
            if self.checkTransition(self.epub, HANDSHAKE_SIZE, STREAM):
                esession = makeEphemeralSession(self.ekeypair,
                        self.epub)
                self.coder = lite_socket(esession)

                data = self.downstreamConnection.readAll()
                if data:
                    self.upstreamConnection.write(self.coder.encode(data))

                data = self.upstreamConnection.readAll()
                if data:
                    self.downstreamConnection.write(self.coder.decode(data))
        else:
            data = self.upstreamConnection.readAll()
            if data:
                self.downstreamConnection.write(self.coder.decode(data))

    def end(self):
        """
        This is the callback method which is called by the framework when the connection is closed.
        In DustDaemon it does nothing.
        """

        pass


class DustClient(DustDaemon):

    """
    DustClient is a client for the Dust protocol.
    In this simplified implementation of the protocol, the client and the server are identical and both just trivially subclass DustDaemon.
    """

    pass


class DustServer(DustDaemon):

    """
    DustServer is a server for the Dust protocol.
    In this simplified implementation of the protocol, the client and the server are identical and both just trivially subclass DustDaemon.
    """

    pass


