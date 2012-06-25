#!/usr/bin/env python -u

import os
import sys

import argparse

from struct import unpack
from socket import inet_ntoa

import monocle
from monocle import _o, Return
monocle.init('tornado')

from monocle.stack import eventloop
from monocle.stack.network import add_service, Service, Client, ConnectionLost
from pyptlib.framework.loopback import FakeSocket

from pyptlib.framework.socks import SocksHandler

from pyptlib.config.config import EnvException
from pyptlib.config.client import ClientConfig
from pyptlib.framework.daemon import *

from pyptlib.transports.dummy import DummyClient

class ManagedClient(Daemon):
  def __init__(self):
    try:
      Daemon.__init__(self, ClientConfig(), SocksHandler())
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
      self.launchClient(self.supportedTransport, 8182)
      self.config.writeMethod(self.supportedTransport, 5, ('127.0.0.1', 8182), None, None)
    except TransportLaunchException as e:
      print('error 3')
      self.config.writeMethodError(self.supportedTransport, e.message)

    self.config.writeMethodEnd()
    
    self.run()
      
  def launchClient(self, name, port):
    if name!=self.supportedTransport:
      raise TransportLaunchException('Tried to launch unsupported transport %s' % (name))

    client=DummyClient()
    self.handler.setTransport(client)
    add_service(Service(self.handler, port=port))    

if __name__=='__main__':
  sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
  server=ManagedClient()
  