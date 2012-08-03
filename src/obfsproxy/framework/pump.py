#!/usr/bin/python
# -*- coding: utf-8 -*-

import monocle
from monocle import _o, Return

from monocle.stack.network import ConnectionLost

from obfsproxy.util import encode
from obfsproxy.framework.tunnel import Tunnel

class Pump(object):
    def __init__(self, local, remote, transportClass):
        self.local=local
        self.remote=remote

        tunnel=Tunnel()
        self.transport=transportClass(tunnel)
        self.tunnel=tunnel.invert()

    def run(self):
        self.transport.start()
        monocle.launch(self.pumpLocal)
        yield self.pumpRemote()

    @_o
    def pumpLocal(self):
        while True:
            data=self.tunnel.local.read_some()
            if data:
                try:
                    yield self.local.write(data)
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
                data = yield self.local.read_some()
                if data:
                    self.tunnel.local.write(data)
                    self.transport.decodedReceived()
            except ConnectionLost:
                print 'Client connection closed'
                return
            except IOError:
                return

    @_o
    def pumpRemote(self):
        while True:
            data=self.tunnel.remote.read_some()
            if data:
                try:
                    yield self.remote.write(data)
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
                data = yield self.remote.read_some()
                if data:
                    self.tunnel.remote.write(data)
                    self.transport.encodedReceived()
            except ConnectionLost:
                print 'Client connection closed'
                return
            except IOError:
                return
