#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
The proxy module contains the ProxyHandler class, which implements the server-side handling of pluggable transports.
"""

from struct import unpack
from socket import inet_ntoa

import monocle
monocle.init('tornado')

from monocle import _o, Return
from monocle.stack.network import Client

from obfsproxy.util import encode

from obfsproxy.framework.pump import Pump


class ProxyHandler:
    """
    The ProxyHandler class implements the server-side handling of pluggable transports.
    """
    transport = None

    def setTransport(self, transport):
        """ setTransport sets the pluggable transport for this proxy server """
        self.transport = transport

    @_o
    def handle(self, conn):
        """ handle is called by the framework to establish a new proxy connection to the Tor server and start processing when an incoming client connection is established. """
        print 'connection'
        client = Client()
        yield client.connect('blanu.net', 80) # FIXME - remove hardcoded destination

        self.pump=Pump(conn, client, self.transport)
        self.pump.run()


