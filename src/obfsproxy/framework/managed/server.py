#!/usr/bin/python
# -*- coding: utf-8 -*-

import monocle
from monocle import _o, Return
monocle.init('tornado')

from monocle.stack import eventloop
from monocle.stack.network import add_service, Service

from obfsproxy.framework.proxy import ProxyHandler

from obfsproxy.transports.dummy import DummyServer
from obfsproxy.transports.rot13 import Rot13Server
from obfsproxy.transports.dust_transport import DustServer
from obfsproxy.transports.obfs3 import Obfs3Server

from pyptlib.easy.server import init, reportSuccess, reportFailure, \
    reportEnd, getORPort


class TransportLaunchException(Exception):

    pass


class ManagedServer:

    def __init__(self):
        self.handler = ProxyHandler(*getORPort())

        self.supportedTransports = {
            'dummy': DummyServer,
            'rot13': Rot13Server,
            'dust': DustServer,
            'obfs3': Obfs3Server,
            }

        matchedTransports = init(self.supportedTransports)
        for transport in matchedTransports:
            try:
                self.launchServer(transport, 1051)
                reportSuccess(transport, ('127.0.0.1', 1051), None)
            except TransportLaunchException:
                reportFailure(transport, 'Failed to launch')
        reportEnd()

        eventloop.run()

    def launchServer(self, name, port):
        if not name in self.supportedTransports:
            raise TransportLaunchException('Tried to launch unsupported transport %s'
                     % name)

        serverClass = self.supportedTransports[name]
        self.handler.setTransport(serverClass)
        add_service(Service(self.handler.handle, port=port))


if __name__ == '__main__':
    server = ManagedServer()
