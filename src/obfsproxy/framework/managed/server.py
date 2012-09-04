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
    reportEnd


class TransportLaunchException(Exception):

    pass


class ManagedServer:

    def __init__(self):
        self.supportedTransports = {
            'dummy': DummyServer,
            'rot13': Rot13Server,
            'dust': DustServer,
            'obfs3': Obfs3Server,
            }

        managed_info = init(self.supportedTransports)
        if managed_info is None: # XXX what is this function supposed to return?!
            print "failz" # XXX make sure that pyptlib has whined to Tor.
            return

        self.orport_handler = ProxyHandler(*managed_info['orport'])

        for transport, transport_bindaddr in managed_info['transports'].items():
            try:
                self.launchServer(transport, transport_bindaddr[1])
                reportSuccess(transport, transport_bindaddr, None)
            except TransportLaunchException:
                reportFailure(transport, 'Failed to launch')
        reportEnd()

        eventloop.run()

    def launchServer(self, name, port):
        if not name in self.supportedTransports:
            raise TransportLaunchException('Tried to launch unsupported transport %s'
                     % name)

        serverClass = self.supportedTransports[name]
        self.orport_handler.setTransport(serverClass)
        add_service(Service(self.orport_handler.handle, port=port))


if __name__ == '__main__':
    server = ManagedServer()
