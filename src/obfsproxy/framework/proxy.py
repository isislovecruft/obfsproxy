#!/usr/bin/python
# -*- coding: utf-8 -*-

from struct import unpack
from socket import inet_ntoa

import monocle
from monocle import _o, Return
from monocle.stack.network import Client

from pyptlib.util import encode

from obfsproxy.framework.shared import pump


class ProxyHandler:

    transport = None

    def setTransport(self, transport):
        self.transport = transport

    @_o
    def handle(self, conn):
        print 'connection'
        client = Client()
        yield client.connect('blanu.net', 80)

        monocle.launch(pump, conn, client, None)
        yield pump(client, conn, None)


