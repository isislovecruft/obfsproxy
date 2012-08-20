#!/usr/bin/python
# -*- coding: utf-8 -*-

""" The pump module contains the Pump class, which takes care of moving bytes between the upstream and downstream connections. """

import monocle
from monocle import _o, Return

from monocle.stack.network import ConnectionLost

from obfsproxy.util import encode
from obfsproxy.framework.circuit import Circuit

class Pump(object):
    """ The Pump class takes care of moving bytes between the upstream and downstream connections. """
    def __init__(self, downstream, upstream, transportClass):
        """ Initializes the downstream and upstream instance variables, instantiates the transportClass, and sets up a circuit. """
        self.downstream=downstream
        self.upstream=upstream

        circuit=Circuit()
        self.transport=transportClass(circuit)
        self.circuit=circuit.invert()

    def run(self):
        """ Calls the start event on the transport and initiates pumping between upstream and downstream connections in both directions. """
        self.transport.start()
        monocle.launch(self.pumpDownstream)
        yield self.pumpUpstream()

    @_o
    def pumpDownstream(self):
        """ Handle the downstream connection. """
        while True:
            data=self.circuit.downstream.read_some()
            if data:
                try:
                    yield self.downstream.write(data)
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

            try:
                data = yield self.downstream.read_some()
                if data:
                    self.circuit.downstream.write(data)
                    self.transport.receivedDownstream()
            except ConnectionLost:
                print 'Client connection closed'
                return
            except IOError:
                return

    @_o
    def pumpUpstream(self):
        """ Handle the upstream connection. """
        while True:
            data=self.circuit.upstream.read_some()
            if data:
                try:
                    yield self.upstream.write(data)
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

            try:
                data = yield self.upstream.read_some()
                if data:
                    self.circuit.upstream.write(data)
                    self.transport.receivedUpstream()
            except ConnectionLost:
                print 'Client connection closed'
                return
            except IOError:
                return
