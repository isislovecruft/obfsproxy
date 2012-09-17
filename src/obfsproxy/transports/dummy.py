#!/usr/bin/python
# -*- coding: utf-8 -*-

""" This module contains an implementation of the 'dummy' transport. """

from obfsproxy.transports.base import BaseDaemon


class DummyDaemon(BaseDaemon):

    """
    DummyDaemon is the base class for DummyClient and DummyServer.
    Since the protocol is so simple, DummyDaemon provides all of the
    functionality for the dummy protocol implementation.
    """

    def receivedDownstream(self, data, circuit):
        """
        receivedDownstream is the event which is called when bytes are received from the downstream socket.
        The dummy protocol just writes these to the upstream socket.
        """

        circuit.upstream.write(data)
        return ''

    def receivedUpstream(self, data, circuit):
        """
        receivedUpstream is the event which is called when bytes are received from the upstream socket.
        The dummy protocol just writes these to the downstream socket.
        """

        circuit.downstream.write(data)
        return ''

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


