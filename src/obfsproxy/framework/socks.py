from struct import unpack
from socket import inet_ntoa

import monocle
from monocle import _o, Return

from pyptlib.util import encode

from pyptlib.framework.shared import pump

def uncompact(x):
    ip, port = unpack("!4sH", x)
    return inet_ntoa(ip), port

@_o
def readHandshake(input):
  version=yield input.read(1)
  print('version: '+encode(str(version)))
  nauth=yield input.read(1)
  nauth=unpack('B', nauth)[0]
  auths=[]
  for x in range(nauth):
    auth=yield input.read(1)
    auth=unpack('B', auth)[0]
    auths.append(auth)

@_o
def sendHandshake(output):
  yield output.write(b"\x05\x00")

@_o
def readRequest(input):
  version=yield input.read(1)
  command=yield input.read(1)
  reserved=yield input.read(1)
  addrtype=yield input.read(1)
  dest=yield input.read(6)

  yield Return(dest)

@_o
def sendResponse(dest, output):
  yield output.write(b"\x05\x00\x00\x01"+dest)

class SocksHandler:
  transport=None

  def setTransport(self, transport):
    self.transport=transport

  @_o
  def handle(self, conn):
    print('handle_socks')
    yield readHandshake(conn)
    print('read handshake')
    yield sendHandshake(conn)
    print('send handshake')
    dest=yield readRequest(conn)
    print('read request: '+str(dest))
    yield sendResponse(dest, conn)
    print('sent response')

    addr, port=uncompact(dest)
    print(addr)
    print(port)

    client = Client()
    yield client.connect(addr, port)
    print('connected '+str(addr)+', '+str(port))
    monocle.launch(pump, conn, client, None)
    yield pump(client, conn, None)
