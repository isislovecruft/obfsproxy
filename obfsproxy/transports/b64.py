#!/usr/bin/python
# -*- coding: utf-8 -*-

""" This module contains an implementation of the 'b64' transport. """

from obfsproxy.transports.base import BaseDaemon

import base64

import obfsproxy.common.log as log

class B64Daemon(BaseDaemon):

    """
    B64Daemon is the base class for B64Client and B64Server.
    Since the protocol is so simple, B64Daemon provides all of the functionality for the b64 protocol implementation.
    """

    def receivedDownstream(self, data, circuit):
        """ XXX DOCDOC
        receivedDownstream is the event which is called when bytes are received from the downstream socket.
        The b64 protocol encodes them with the b64 function and then writes the result to the upstream socket.
        """

        log.warning("downstream: Received '''%s'''" % (str(data)))
        circuit.upstream.write(base64.b64decode(data))
        return ''

    def receivedUpstream(self, data, circuit):
        """
        receivedUpstream is the event which is called when bytes are received from the upstream socket.
        The b64 protocol encodes them with the b64 function and then writes the result to the downstream socket.
        """

        log.warning("upstream: Received '''%s'''" % (str(data)))
        circuit.downstream.write(base64.b64encode(data))
        return ''


class B64Client(B64Daemon):

    """
    B64Client is a client for the 'b64' protocol.
    Since this protocol is so simple, the client and the server are identical and both just trivially subclass B64Daemon.
    """

    pass


class B64Server(B64Daemon):

    """
    B64Server is a server for the 'b64' protocol.
    Since this protocol is so simple, the client and the server are identical and both just trivially subclass B64Daemon.
    """

    pass


