from struct import unpack
from socket import inet_ntoa

import monocle
from monocle import _o, Return

from pyptlib.util import encode

from pyptlib.framework.shared import pump

class ProxyHandler:
  transport=None

  def setTransport(self, transport):
    self.transport=transport

  @_o
  def handle(self, conn):
    print('connection')
    client = Client()
    yield client.connect('blanu.net', 7051)

    coder=yield handshake(client)

    monocle.launch(pump, conn, client, coder.encrypt)
    yield pump(client, conn, coder.decrypt)

