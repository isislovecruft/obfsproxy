#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging

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
	logging.error('buffer read_some '+str(len(self.buffer))+' '+str(self))
        logging.error('before '+str(self.buffer))
        data=self.read(len(self.buffer))
        logging.error('after '+str(self.buffer))
        return data

    def write(self, bs):
        logging.error('buffer write '+str(len(bs))+' '+str(self))
        logging.error('before '+str(self.buffer))
        self.buffer=self.buffer+bs
        logging.error('after '+str(self.buffer))

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
        if remote:
            self.remote=remote
        else:
            self.remote=Channel()

    def invert(self):
        return Tunnel(self.local.invert(), self.remote.invert())

