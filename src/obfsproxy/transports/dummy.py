#!/usr/bin/python
# -*- coding: utf-8 -*-

<<<<<<< HEAD
import logging
=======
""" This module contains an implementation of the 'dummy' transport. """
>>>>>>> aaa6decd2a9f03db165cf03e0d369113bc5818c1

from obfsproxy.transports.base import BaseDaemon


class DummyDaemon(BaseDaemon):

<<<<<<< HEAD
    def decodedReceived(self):
        logging.error('dummy decoded received')
        data = self.decodedSocket.read_some()
        self.encodedSocket.write(data)
        logging.error('wrote '+str(len(data))+' encoded')

    def encodedReceived(self):
        logging.error('dummy encoded received')
        data = self.encodedSocket.read_some()
        self.decodedSocket.write(data)
=======
    """
    DummyDaemon is the base class for DummyClient and DummyServer.
    Since the protocol is so simple, DummyDaemon provides all of the functionality for the dummy protocol implementation.
    """

    def receivedDownstream(self):
        """
        receivedDownstream is the event which is called when bytes are received from the downstream socket.
        The dummy protocol just writes these to the upstream socket.
        """

        data = self.downstreamConnection.readAll()
        self.upstreamConnection.write(data)

    def receivedUpstream(self):
        """
        receivedUpstream is the event which is called when bytes are received from the upstream socket.
        The dummy protocol just writes these to the downstream socket.
        """

        data = self.upstreamConnection.readAll()
        self.downstreamConnection.write(data)
>>>>>>> aaa6decd2a9f03db165cf03e0d369113bc5818c1


class DummyClient(DummyDaemon):

    """
    DummyClient is a client for the 'dummy' protocol.
    Since this protocol is so simple, the client and the server are identical and both just trivially subclass DummyDaemon.
    """

    pass


class DummyServer(DummyDaemon):

    """
    DummyServer is a server for the 'dummy' protocol.
    Since this protocol is so simple, the client and the server are identical and both just trivially subclass DummyDaemon.
    """

    pass


