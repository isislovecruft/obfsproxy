#!/usr/bin/python
# -*- coding: utf-8 -*-


class BaseDaemon:

    def __init__(self, tunnel):
        self.decodedSocket = tunnel.local
        self.encodedSocket = tunnel.remote

    def read(
        self,
        socket,
        data,
        maxlen,
        ):
        remaining = maxlen - len(data)
        return data + socket.read(remaining)

    def checkTransition(
        self,
        data,
        maxlen,
        newState,
        ):
        if len(data) == maxlen:
            state = newState
            return True
        else:
            return False

    def start(self):
        pass

    def receivedDecoded(self):
        pass

    def receivedEncoded(self):
        pass

    def end(self):
        pass


