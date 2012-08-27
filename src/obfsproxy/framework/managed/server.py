#!/usr/bin/python
# -*- coding: utf-8 -*-

import monocle
from monocle import _o, Return
monocle.init('tornado')

from monocle.stack import eventloop
from monocle.stack.network import add_service, Service

from obfsproxy.framework.proxy import ProxyHandler

from obfsproxy.transports.dummy import DummyClient
from obfsproxy.transports.rot13 import Rot13Client
from obfsproxy.transports.dust_transport import DustClient
from obfsproxy.transports.obfs3 import Obfs3Client

from pyptlib.easy.server import init, reportSuccess, reportFailure, \
    reportEnd


class TransportLaunchException(Exception):

    pass


class ManagedServer:

    def __init__(self):
        self.handler = ProxyHandler()

        self.supportedTransports = {
            'dummy': DummyClient,
            'rot13': Rot13Client,
            'dust': DustClient,
            'obfs3': Obfs3Client,
            }

        matchedTransports = init(self.supportedTransports)
        for transport in matchedTransports:
            try:
                self.launchServer(transport, 8183)
                reportSuccess(transport, ('127.0.0.1', 8183), None)
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
