#!/usr/bin/python
# -*- coding: utf-8 -*-

""" The circuit module contains the Buffer, Connection, and Circuit classes, which are used for managing connections. """


class Buffer(object):

    """ The Buffer class manages an internal byte buffer, allowing for reading and writing. """

    def __init__(self):
        """ Initialize the Buffer with an empty byte buffer. """

        self.buffer = bytes('')

    def read(self, x):
        """ Read exactly x bytes from the buffer. If x bytes are not available, return None. """

        if len(self.buffer) < x:
            return None
        else:
            data = self.buffer[:x]
            self.buffer = self.buffer[x:]
            return data

    def read_some(self):
        """ Read all of the bytes from the buffer. """

        return self.read(len(self.buffer))

    def write(self, bs):
        """ Write the bytes bs to the buffer. """

        self.buffer = self.buffer + bs


class Connection(object):

    """ The Connection class contains two buffers, incoming and outgoing. It allows for reading from the incoming buffer and writing to the outgoing buffer. A Connection can be inverted to flip the incoming and outgoing buffers. """

    def __init__(self, incoming=None, outgoing=None):
        """ Initialize the Connection's incoming and outgoing buffers. If either buffer is supplied as an optional parameters, reuse that Buffer, otherwise create a new empty Buffer. """

        if incoming:
            self.incomingBuffer = incoming
        else:
            self.incomingBuffer = Buffer()

        if outgoing:
            self.outgoingBuffer = outgoing
        else:
            self.outgoingBuffer = Buffer()

    def invert(self):
        """ Returns a Connection with the incoming and outgoing buffers switched. """

        return Connection(self.outgoingBuffer, self.incomingBuffer)

    def read(self, x):
        """ Read exactly x bytes from the incoming buffer. If x bytes are not available, return None. """

        return self.incomingBuffer.read(x)

    def read_some(self):
        """ Read all of the bytes from the incoming buffer. """

        return self.incomingBuffer.read_some()

    def write(self, bs):
        """ Write the bytes bs to the outgoing buffer. """

        self.outgoingBuffer.write(bs)


class Circuit(object):

    """ The Circuit class contains two connections, one upstream and one downstream. """

    def __init__(self, downstream=None, upstream=None):
        """ Initialize the Circuit's upstream and downstream conections. If either connection is supplied as an optional parameters, reuse that Connection, otherwise create a new Connection. """

        if downstream:
            self.downstream = downstream
        else:
            self.downstream = Connection()
        if remove:
            self.upstream = upstream
        else:
            self.upstream = Connection()

    def invert(self):
        """ Returns a Circuit with the incoming and outgoing buffers switched on the Connections. """

        return Circuit(self.downstream.invert(), self.upstream.invert())


