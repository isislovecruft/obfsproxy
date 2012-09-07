#!/usr/bin/python
# -*- coding: utf-8 -*-

""" The pump module contains the Pump class, which takes care of moving bytes between the upstream and downstream connections. """

import logging
from traceback import print_exc

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

        monocle.launch(self.pumpUpstream)
        yield self.pumpDownstream()

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

        logging.error('pumpIn yielding '+str(input))
        try:
            data = yield input.read_some()
        except ConnectionLost as e:
            logging.error('pumpIn: Connection lost')
            yield Return(False)
        except IOError:
            print 'IOError'
            print_exc()
            yield Return(False)
        except Exception, e:
            print 'Exception'
            print e
            yield Return(False)

        if data:
            logging.error('pumpIn read ' + str(len(data)))
            try:
                output.write(data)
                logging.error('pumpIn wrote %d' % (len(data)))
                callback()
            except ConnectionLost:
                print 'pumpIn: Connection lost'
                yield Return(False)
            except IOError:
                print 'IOError'
                print_exc()
                yield Return(False)
            except Exception, e:
                print 'Exception'
                print e
                yield Return(False)
        else:
            logging.error('pumpIn no data')

        logging.error('pumpIn returning True')
        yield Return(True)

    @_o
    def pumpOut(self, input, output):
        logging.error('pumpOut yield')
        try:
            data = input.read_some()
        except ConnectionLost:
            print 'pumpOut: Connection lost'
            return
        except IOError:
            print 'IOError'
            print_exc()
            return
        except Exception, e:
            print 'Exception'
            print e
            return

        if data:
            logging.error('pumpOut read ' + str(len(data)))
            try:
                yield output.write(data)
                logging.error('pumpOut wrote %d' % (len(data)))
            except ConnectionLost:
                print 'pumpOut: Connection lost'
                return
            except IOError:
                print 'IOError'
                print_exc()
                return
            except Exception, e:
                print 'Exception'
                print e
                return
        else:
            logging.error('pumpOut no data')

    @_o
    def pumpUpstream(self):
        try:
            pumping=True
            while pumping:
                logging.error('pump upstream')
                pumping=yield self.pumpIn(self.downstream, self.circuit.downstream, self.transport.receivedDownstream)
                yield self.drain()
                logging.error('pumping: '+str(pumping))
        except Exception as e:
            logging.error('Exception in pumpUpstream')
            logging.error(e)

    @_o
    def pumpDownstream(self):
        try:
            pumping=True
            while pumping:
                logging.error('pump downstream')
                pumping=yield self.pumpIn(self.upstream, self.circuit.upstream, self.transport.receivedUpstream)
                yield self.drain()
        except Exception as e:
            logging.error('Exception in pumpDownstream')
            logging.error(e)
