#!/usr/bin/python
# -*- coding: utf-8 -*-

import monocle
from monocle import _o, Return
monocle.init('tornado')

from monocle.stack import eventloop
from monocle.stack.network import add_service

from obfsproxy.framework.proxy import ProxyHandler
from obfsproxy.transports.dummy import DummyClient

from pyptlib.easy.server import init, reportSucess, reportFailure, \
    reportEnd


class TransportLaunchException(Exception):

    pass


class ManagedServer:

    def __init__(self):
        self.handler = ProxyHandler()

        supportedTransports = ['dummy', 'rot13']

        matchedTransports = init(supportedTransports)
        for transport in matchedTransports:
            try:
                self.launchServer(transport, 8182)
                reportSuccess(transport, ('127.0.0.1', 8182), None)
            except TransportLaunchException:
                reportFailure(transport, 'Failed to launch')
        reportEnd()

        eventloop.run()

    def launchServer(self, name, port):
        if name != self.supportedTransport:
            raise TransportLaunchException('Tried to launch unsupported transport %s'
                     % name)

        server = DummyServer()
        self.handler.setTransport(server)
        add_service(Service(self.handler, port=port))


if __name__ == '__main__':
    server = ManagedServer()
