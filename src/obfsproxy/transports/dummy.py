#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging

from obfsproxy.transports.base import BaseDaemon


class DummyDaemon(BaseDaemon):

    def decodedReceived(self):
        logging.error('dummy decoded received')
        data = self.decodedSocket.read_some()
        self.encodedSocket.write(data)
        logging.error('wrote '+str(len(data))+' encoded')

    def encodedReceived(self):
        logging.error('dummy encoded received')
        data = self.encodedSocket.read_some()
        self.decodedSocket.write(data)


class DummyClient(DummyDaemon):

    pass


class DummyServer(DummyDaemon):

    pass


