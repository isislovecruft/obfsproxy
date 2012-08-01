#!/usr/bin/python
# -*- coding: utf-8 -*-

from dust.extensions.lite.lite_socket2 import makeSession, makeEphemeralSession, createEphemeralKeypair
from dust.core.dust_packet import IV_SIZE, KEY_SIZE

from obfsproxy.crypto.aes import AESCoder
from obfsproxy.transports.base import BaseDaemon

HANDSHAKE=0
STREAM=1

HANDSHAKE_SIZE=IV_SIZE+KEY_SIZE

class Obfs3Daemon(BaseDaemon):

    def __init__(self, decodedSocket, encodedSocket):
        BaseDaemon.__init__(self, decodedSocket, encodedSocket)

        self.state=HANDSHAKE_WRITE
        self.ekeypair=createEphemeralKeypair()
        self.epub=bytes('')

    def start(self):
        self.encodedSocket.write(self.ekeypair.public.bytes)

    def receivedDecoded(self):
        # If we're in streaming mode, encode and write the incoming data
        if self.state==STREAM:
            data=self.decodedSocket.readAll()
            if data:
                self.encodedSocket.write(self.coder.encode(data))
        # Else do nothing, data will buffer until we've done the handshake

    def receivedEncoded(self, data):
        if self.state==HANDSHAKE:
            self.epub=self.read(self.encodedSocket, self.epub, HANDSHAKE_SIZE)
            if self.checkTransition(self.epub, HANDSHAKE_SIZE, STREAM):
                esession=makeEphemeralSession(self.ekeypair, self.epub)
                self.coder=AESCoder(esession)

                data=self.decodedSocket.readAll()
                if data:
                    self.encodedSocket.write(self.coder.encode(data))

                data=self.encodedSocket.readAll()
                if data:
                    self.decodedSocket.write(self.coder.decode(data))
        else:
            data=self.encodedSocket.readAll()
            if data:
                self.decodedSocket.write(self.coder.decode(data))

    def end(self):
        pass

class Obfs3Client(Obfs3Daemon):
    pass

class Obfs3Server(Obfs3Daemon):
    pass
