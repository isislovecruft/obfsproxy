#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
The proxy module contains the ProxyHandler class, which implements the server-side handling of pluggable transports.
"""

import logging

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

    def __init__(self, addr, port):
        self.addr = addr
        self.port = port

    def setTransport(self, transport):
        """ setTransport sets the pluggable transport for this proxy server """

        self.transport = transport

    @_o
    def handle(self, conn):
        """ handle is called by the framework to establish a new proxy connection to the Tor server and start processing when an incoming client connection is established. """

        logging.error('connection')
        logging.error('connecting %s:%d' % (self.addr, self.port))
        logging.error('types: %s:%s' % (str(type(self.addr)), str(type(self.port))))
        client = Client()

	try:
	    yield client.connect(self.addr, self.port)
	except Exception as e:
	    logging.error('Error connecting to destination')
            return

        self.pump = Pump(conn, client, self.transport)
        self.pump.run()


