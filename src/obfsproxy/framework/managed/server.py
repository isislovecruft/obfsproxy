#!/usr/bin/env python -u

import os
import sys

from struct import unpack
from socket import inet_ntoa

import monocle
from monocle import _o, Return
monocle.init('tornado')

from monocle.stack import eventloop
from monocle.stack.network import add_service, Service, Client

from pyptlib.framework.shared import pump

from pyptlib.config.config import EnvException
from pyptlib.config.server import ServerConfig, MethodOptions
from pyptlib.framework.daemon import *

from pyptlib.framework.proxy import ProxyHandler

from pyptlib.transports.dummy import DummyServer

class ManagedServer(Daemon):
  def __init__(self):
    try:
      Daemon.__init__(self, ServerConfig(), ProxyHandler())
    except EnvException:
      print('error 0')
      return
    except UnsupportedManagedTransportVersionException:
      print('error 1')
      return
    except NoSupportedTransportsException:
      print('error 2')
      return

    try:
      self.launchServer(self.supportedTransport, 8182)
      self.config.writeMethod(self.supportedTransport, ('127.0.0.1', 8182), MethodOptions())
    except TransportLaunchException as e:
      print('error 3')
      self.config.writeMethodError(self.supportedTransport, e.message)

    self.config.writeMethodEnd()

    self.run()

  def launchServer(self, name, port):
    if name!=self.supportedTransport:
      raise TransportLaunchException('Tried to launch unsupported transport %s' % (name))

    client=DummyServer()
    self.handler.setTransport(client)
    add_service(Service(self.handler, port=port))

if __name__=='__main__':
  sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
  server=ManagedServer()

