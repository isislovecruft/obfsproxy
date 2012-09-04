#!/usr/bin/python
# -*- coding: utf-8 -*-

""" This module contains an implementation of the 'rot13' transport. """

from obfsproxy.transports.base import BaseDaemon


class Rot13Daemon(BaseDaemon):

    """
    Rot13Daemon is the base class for Rot13Client and Rot13Server.
    Since the protocol is so simple, Rot13Daemon provides all of the functionality for the rot13 protocol implementation.
    """

    def rot13(self, data):
        """
        The rot13 method performs a rot13 transformation on just the alphabetical characters in the data.
        """

        for x in range(len(data)):
            ascii = ord(data[x])
            if ascii >= 97 and ascii <= 122:  # a-z
                data[x] = (ascii - 97 + 13) % 26 + 97
            elif ascii >= 65 and ascii <= 90:

                                      # A-Z

                data[x] = (ascii - 65 + 13) % 26 + 65

        return data

    def receivedDownstream(self, data):
        """
        receivedDownstream is the event which is called when bytes are received from the downstream socket.
        The rot13 protocol encodes them with the rot13 function and then writes the result to the upstream socket.
        """

        return self.rot13(data)

    def receivedUpstream(self, data):
        """
        receivedUpstream is the event which is called when bytes are received from the upstream socket.
        The rot13 protocol encodes them with the rot13 function and then writes the result to the downstream socket.
        """

        return self.rot13(data)


class Rot13Client(Rot13Daemon):

    """
    Rot13Client is a client for the 'rot13' protocol.
    Since this protocol is so simple, the client and the server are identical and both just trivially subclass Rot13Daemon.
    """

    pass


class Rot13Server:

    """
    Rot13Server is a server for the 'rot13' protocol.
    Since this protocol is so simple, the client and the server are identical and both just trivially subclass Rot13Daemon.
    """

    pass


