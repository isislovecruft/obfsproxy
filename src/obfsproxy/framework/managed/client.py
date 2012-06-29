#!/usr/bin/python
# -*- coding: utf-8 -*-

import monocle
from monocle import _o, Return
monocle.init('tornado')

from monocle.stack import eventloop
from monocle.stack.network import add_service

from obfsproxy.framework.socks import SocksHandler
from obfsproxy.transports.dummy import DummyClient

from pyptlib.easy.client import init, reportSucess, reportFailure, reportEnd

class TransportLaunchException(Exception):
  pass

class ManagedClient:
    def __init__(self):
        self.handler=SocksHandler()
    
        supportedTransports = ['dummy', 'rot13']

        matchedTransports=init(supportedTransports)
        for transport in matchedTransports:
          try:
            self.launchClient(transport, 8182)
            reportSuccess(transport, 5, ('127.0.0.1', 8182), None, None)
          except TransportLaunchException:
            reportFailure(transport, 'Failed to launch')
        reportEnd()

        eventloop.run()

    def launchClient(self, name, port):
        if name != self.supportedTransport:
            raise TransportLaunchException('Tried to launch unsupported transport %s'
                     % name)

        client = DummyClient()
        self.handler.setTransport(client)
        add_service(Service(self.handler, port=port))

if __name__ == '__main__':
    client = ManagedClient()
