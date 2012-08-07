#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging

import monocle
monocle.init('tornado')

from monocle import _o, Return

from monocle.stack.network import ConnectionLost

from obfsproxy.util import encode
from obfsproxy.framework.tunnel import Tunnel

class Pump(object):
    def __init__(self, local, remote, transportClass):
	logging.error('pump init')
        self.local=local
        self.remote=remote

        self.tunnel=Tunnel()
        self.transport=transportClass(self.tunnel.invert())

        logging.error('Buffers:')
        logging.error('local in: '+str(self.tunnel.local.incomingBuffer))
        logging.error('local out: '+str(self.tunnel.local.outgoingBuffer))
        logging.error('remote in: '+str(self.tunnel.remote.incomingBuffer))
        logging.error('remote out: '+str(self.tunnel.remote.outgoingBuffer))

    @_o
    def run(self):
	logging.error('pump run')
        self.transport.start()

        self.drain()

        monocle.launch(self.pumpLocal)
        yield self.pumpRemote()
        logging.error('end pump run')

    @_o
    def drain(self):
        logging.error('drain')
        yield self.pumpOut(self.tunnel.local, self.local)
        yield self.pumpOut(self.tunnel.remote, self.remote)

    @_o
    def pumpIn(self, input, output, callback):
        logging.error('pumpIn')
        data=yield input.read_some()
        if data:
            logging.error('Pump read '+str(len(data))+' from tunnel')
            try:
                output.write(data)
                callback()
            except ConnectionLost:
                print 'Connection lost'
                return
            except IOError:
                print 'IOError'
                return
            except Exception, e:
                print 'Exception'
                print e
                return

    @_o
    def pumpOut(self, input, output):
        logging.error('pumpOut')
        data=input.read_some()
        if data:
            logging.error('Pump read '+str(len(data))+' from tunnel')
            try:
                yield output.write(data)
            except ConnectionLost:
                print 'Connection lost'
                return
            except IOError:
                print 'IOError'
                return
            except Exception, e:
                print 'Exception'
                print e
                return

    @_o
    def pumpLocal(self):
	logging.error('pump local')
        while True:
            yield self.pumpIn(self.local, self.tunnel.local, self.transport.decodedReceived)
            yield self.drain()

    @_o
    def pumpRemote(self):
	logging.error('pump remote')
        while True:
            yield self.pumpIn(self.remote, self.tunnel.remote, self.transport.encodedReceived)
            yield self.drain()
