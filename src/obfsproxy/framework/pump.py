#!/usr/bin/python
# -*- coding: utf-8 -*-

""" The pump module contains the Pump class, which takes care of moving bytes between the upstream and downstream connections. """

import logging

import monocle
monocle.init('tornado')

from monocle import _o, Return

from monocle.stack.network import ConnectionLost

from obfsproxy.util import encode
from obfsproxy.framework.circuit import Circuit


class Pump(object):

    """ The Pump class takes care of moving bytes between the upstream and downstream connections. """

    def __init__(
        self,
        downstream,
        upstream,
        transportClass,
        ):
        """ Initializes the downstream and upstream instance variables, instantiates the transportClass, and sets up a circuit. """

        self.downstream = downstream
        self.upstream = upstream

        circuit = Circuit()
        self.transport = transportClass(circuit)
        self.circuit = circuit.invert()

    @_o
    def run(self):
        """ Calls the start event on the transport and initiates pumping between upstream and downstream connections in both directions. """

        self.transport.start()

        self.drain()

        monocle.launch(self.pumpDownstream)
        yield self.pumpUpstream()

    @_o
    def drain(self):
        logging.error('drain')
        yield self.pumpOut(self.circuit.downstream, self.downstream)
        yield self.pumpOut(self.circuit.upstream, self.upstream)

    @_o
    def pumpIn(
        self,
        input,
        output,
        callback,
        ):
        logging.error('pumpIn')
        data = (yield input.read_some())
        if data:
            logging.error('Pump read ' + str(len(data)) + ' from tunnel'
                          )
            try:
                data = (yield self.downstream.read_some())
                if data:
                    self.circuit.downstream.write(data)
                    self.transport.receivedDownstream()
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
        data = input.read_some()
        if data:
            logging.error('Pump read ' + str(len(data)) + ' from tunnel'
                          )
            try:
                yield output.write(data)
            except:
                logging.error('Error pumping out')

    @_o
    def pumpUpstream(self):
        logging.error('pump local')
        while True:
            yield self.pumpIn(self.dowstream, self.circuit.dowstream,
                              self.transport.downstreamReceived)
            yield self.drain()

    @_o
    def pumpDownstream(self):
        logging.error('pump remote')
        while True:
            yield self.pumpIn(self.upstream, self.circuit.upstream,
                              self.transport.upstreamReceived)
            yield self.drain()


