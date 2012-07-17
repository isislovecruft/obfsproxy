#!/usr/bin/python
# -*- coding: utf-8 -*-

from dust.extensions.lite.lite_socket2 import makeSession, makeEphemeralSession, createEphemeralKeypair
from dust.core.dust_packet import IV_SIZE, KEY_SIZE

from obfsproxy.crypto.aes import AESCoder

HANDSHAKE=0
STREAM=1

HANDSHAKE_SIZE=IV_SIZE+KEY_SIZE

class Obfs3Daemon:

    def __init__(self, client, server):
        self.client=client
        self.server=server
        self.state=HANDSHAKE_WRITE
        self.encodeBuffer=bytes('')
        self.decodeBuffer=bytes('')
        self.ekeypair=createEphemeralKeypair()

    def read(self, data, count):
        if data:
            self.decodeBuffer=self.decodeBuffer+data
        if len(self.decodeBuffer)>=count:
            data=self.decodeBuffer[:count]
            self.decodeBuffer=self.decodeBuffer[count:]
            return data
        else:
            return None

    def encode(self, data):
        if self.state==HANDSHAKE:
            self.encodeBuffer=self.encodeBuffer+data
        else:
            return self.coder.encode(data)

    def decode(self, data):
        if self.state==HANDSHAKE:
            epub=self.read(data, HANDSHAKE_SIZE)
            if epub:
                esession=makeEphemeralSession(self.ekeypair, epub)
                self.coder=AESCoder(esession)
                self.state=STREAM
                self.server.write(self.encode(self.encodeBuffer))
                return decode(self.decodeBuffer)
            else:
                return None
        else:
            return self.coder.decode(data)

    def end(self):
        pass

class Obfs3Client(Obfs3Daemon):

    def start(self):
        self.server.write(self.ekeypair.public.bytes)

class Obfs3Server(Obfs3Daemon):

    def start(self):
        self.client.write(ekeypair.public.bytes)
