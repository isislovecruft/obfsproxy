#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
The socks module contains the SocksHandler class, which implements the client-side handling of pluggable transports.
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


def uncompact(x):
    """ uncompact is a convenience method for unpacking an IPv4 address from its byte representation. """

    (ip, port) = unpack('!4sH', x)
    return (inet_ntoa(ip), port)


@_o
def readHandshake(conn):
    """ readHandshake reads the SOCKS handshake information to the SOCKS client. """

    version = (yield conn.read(1))
    logging.info('version: %s' % encode(str(version)))
    nauth = (yield conn.read(1))
    nauth = unpack('B', nauth)[0]
    auths = []
    for x in range(nauth):
        auth = (yield conn.read(1))
        auth = unpack('B', auth)[0]
        auths.append(auth)


@_o
def sendHandshake(output):
    """ sendHandshake sends the SOCKS handshake information to the SOCKS client. """

    yield output.write('\x05\x00')


@_o
def readRequest(conn):
    """ readRequest reads the SOCKS request information from the client and returns the bytes represneting the IPv4 destination. """

    version = (yield conn.read(1))
    command = (yield conn.read(1))
    reserved = (yield conn.read(1))
    addrtype = (yield conn.read(1))
    dest = (yield conn.read(6))

    yield Return(dest)


@_o
def sendResponse(dest, output):
    """ sendResponse sends the SOCKS response to the request. """

    yield output.write('\x05\x00\x00\x01' + dest)


class SocksHandler:

    """
    The SocksHandler class implements the client-side handling of pluggable transports.
    """

    transport = None

    def setTransport(self, transport):
        """ setTransport sets the pluggable transport for this proxy server """

        self.transport = transport

    @_o
    def handle(self, conn):
        """ handle is called by the framework to establish a new connection to the proxy server and start processing when an incoming SOCKS client connection is established. """

        logging.info('handle_socks')
        yield readHandshake(conn)
        logging.error('read handshake')
        yield sendHandshake(conn)
        logging.error('send handshake')
        dest = (yield readRequest(conn))
#        logging.error('read request: %s' % str(dest))
        yield sendResponse(dest, conn)
        logging.error('sent response')

        (addr, port) = uncompact(dest)
	logging.error('connecting %s:%d' % (addr, port))

        logging.info(addr)
        logging.info(port)

        client = Client()
        yield client.connect(addr, port)
        logging.info('connected %s:%d' % (addr, port))

        self.pump = Pump(conn, client, self.transport)
        self.pump.run()


