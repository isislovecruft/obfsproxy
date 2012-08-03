#!/usr/bin/python
# -*- coding: utf-8 -*-

class Buffer(object):
    def __init__(self):
        self.buffer=bytes('')

    def read(self, x):
        if len(self.buffer)<x:
            return None
        else:
            data=self.buffer[:x]
            self.buffer=self.buffer[x:]
            return data

    def read_some(self):
        return self.read(len(self.buffer))

    def write(self, bs):
        self.buffer=self.buffer+bs

class Channel(object):
    def __init__(self, incoming=None, outgoing=None):
        if incoming:
            self.incomingBuffer=incoming
        else:
            self.incomingBuffer=Buffer()

        if outgoing:
            self.outgoingBuffer=outgoing
        else:
            self.outgoingBuffer=Buffer()

    def invert(self):
        return Channel(self.outgoingBuffer, self.incomingBuffer)

    def read(self, x):
        return self.incomingBuffer.read(x)

    def read_some(self):
        return self.incomingBuffer.read_some()

    def write(self, bs):
        self.outgoingBuffer.write(bs)

class Tunnel(object):
    def __init__(self, local=None, remote=None):
        if local:
            self.local=local
        else:
            self.local=Channel()
        if remove:
            self.remote=remote
        else:
            self.remote=Channel()

    def invert(self):
        return Tunnel(self.local.invert(), self.remote.invert())

