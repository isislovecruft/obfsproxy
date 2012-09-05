#!/usr/bin/python
# -*- coding: utf-8 -*-

""" The pump module contains the Pump class, which takes care of moving bytes between the upstream and downstream connections. """

from traceback import print_exc

import monocle
monocle.init('tornado')

from monocle import _o, Return

from monocle.stack.network import ConnectionLost

from obfsproxy.util import encode
from obfsproxy.framework.circuit import Circuit

import obfsproxy.common.log as log

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
        log.error('drain')
        yield self.pumpOut(self.circuit.downstream, self.downstream)
        yield self.pumpOut(self.circuit.upstream, self.upstream)

    @_o
    def pumpIn(
        self,
        input,
        output,
        callback,
        ):

        log.error('pumpIn yielding '+str(input))
	try:
	    data = yield input.read_some()
        except ConnectionLost:
            log.error('pumpIn: Connection lost')
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
            log.error('pumpIn read ' + str(len(data)))
            try:
	        output.write(data)
		log.error('pumpIn wrote %d' % (len(data)))
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
		log.error('pumpIn no data')

        logging.error('pumpIn returning True')
        yield Return(True)

    @_o
    def pumpOut(self, input, output):
        log.error('pumpOut yield')
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
            log.error('pumpOut read ' + str(len(data)))
            try:
                yield output.write(data)
		log.error('pumpOut wrote %d' % (len(data)))
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
	    log.error('pumpOut no data')

    @_o
    def pumpUpstream(self):
        pumping=True
        while pumping:
	    log.error('pump upstream')
            pumping=yield self.pumpIn(self.downstream, self.circuit.downstream,
                              self.transport.receivedDownstream)
            yield self.drain()

    @_o
    def pumpDownstream(self):
        pumping=True
        while pumping:
            log.error('pump downstream')
            pumping=yield self.pumpIn(self.upstream, self.circuit.upstream,
                              self.transport.receivedUpstream)
            yield self.drain()
