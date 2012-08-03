#!/usr/bin/python
# -*- coding: utf-8 -*-

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
    (ip, port) = unpack('!4sH', x)
    return (inet_ntoa(ip), port)


@_o
def readHandshake(input):
    version = (yield input.read(1))
    logging.info('version: %s' % (encode(str(version))))
    nauth = (yield input.read(1))
    nauth = unpack('B', nauth)[0]
    auths = []
    for x in range(nauth):
        auth = (yield input.read(1))
        auth = unpack('B', auth)[0]
        auths.append(auth)


@_o
def sendHandshake(output):
    yield output.write('\x05\x00')


@_o
def readRequest(input):
    version = (yield input.read(1))
    command = (yield input.read(1))
    reserved = (yield input.read(1))
    addrtype = (yield input.read(1))
    dest = (yield input.read(6))

    yield Return(dest)


@_o
def sendResponse(dest, output):
    yield output.write('\x05\x00\x00\x01' + dest)


class SocksHandler:

    transport = None

    def setTransport(self, transport):
        self.transport = transport

    @_o
    def handle(self, conn):
        logging.info('handle_socks')
        yield readHandshake(conn)
        logging.info('read handshake')
        yield sendHandshake(conn)
        logging.info('send handshake')
        dest = (yield readRequest(conn))
        logging.info('read request: %s' % (str(dest)))
        yield sendResponse(dest, conn)
        logging.info('sent response')

        (addr, port) = uncompact(dest)

#        addr='127.0.0.1'
#        port=8183

        logging.info(addr)
        logging.info(port)

        client = Client()
        yield client.connect(addr, port)
        logging.info('connected %s:%d' % (addr, port))

        self.pump=Pump(conn, client, self.transport)
        self.pump.run()
