#!/usr/bin/python
# -*- coding: utf-8 -*-

from obfsproxy.transports.base import BaseDaemon


class DummyDaemon(BaseDaemon):

    def receivedDecoded(self):
        data = self.decodedSocket.readAll()
        self.encodedSocket.write(data)

    def receivedEncoded(self):
        data = self.encodedSocket.readAll()
        self.decodedSocket.write(data)


class DummyClient(DummyDaemon):

    pass


class DummyServer(DummyDaemon):

    pass


