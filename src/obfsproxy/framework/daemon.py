#!/usr/bin/env python

import sys
import time

from struct import unpack
from socket import inet_ntoa

import monocle
from monocle import _o, Return
monocle.init('tornado')

from monocle.stack import eventloop
from monocle.stack.network import add_service, Service, Client, ConnectionLost
from pyptlib.framework.loopback import FakeSocket

from pyptlib.framework.shared import *
from pyptlib.framework.socks import *

class Daemon:
  config=None
  handler=None

  supportedTransportVersion='1'
  supportedTransport='dummy'

  def __init__(self, configManager, handler):
    self.config=configManager
    self.handler=handler

    if self.config.checkManagedTransportVersion(self.supportedTransportVersion):
      self.config.writeVersion(self.supportedTransportVersion)
    else:
      self.config.writeVersionError()
      raise UnsupportedManagedTransportVersionException()

    if not self.config.checkTransportEnabled(self.supportedTransport):
      raise NoSupportedTransportsException()

  def run(self):
    eventloop.run()

class UnsupportedManagedTransportVersionException(Exception):
  pass

class NoSupportedTransportsException(Exception):
  pass

class TransportLaunchException(Exception):
  def __init__(self, message):
    self.message=message

