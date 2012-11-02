#!/usr/bin/python
# -*- coding: utf-8 -*-

""" This module contains an implementation of the 'dummy' transport. """

from obfsproxy.transports.base import BaseTransport


class DummyTransport(BaseTransport):
    """
    Implements the dummy protocol. A protocol that simply proxies data
    without obfuscating them.
    """

    def receivedDownstream(self, data, circuit):
        """
        Got data from downstream; relay them upstream.
        """

        circuit.upstream.write(data.read())

    def receivedUpstream(self, data, circuit):
        """
        Got data from upstream; relay them downstream.
        """

        circuit.downstream.write(data.read())

class DummyClient(DummyTransport):

    """
    DummyClient is a client for the 'dummy' protocol.
    Since this protocol is so simple, the client and the server are identical and both just trivially subclass DummyTransport.
    """

    pass


class DummyServer(DummyTransport):

    """
    DummyServer is a server for the 'dummy' protocol.
    Since this protocol is so simple, the client and the server are identical and both just trivially subclass DummyTransport.
    """

    pass


