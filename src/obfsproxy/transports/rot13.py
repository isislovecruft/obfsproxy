#!/usr/bin/python
# -*- coding: utf-8 -*-


def rot13(data):
    for x in range(len(data)):
        ascii = ord(data[x])
        if ascii >= 97 and ascii <= 122:  # a-z
            data[x] = (ascii - 97 + 13) % 26 + 97
        elif ascii >= 65 and ascii <= 90:

                                  # A-Z

            data[x] = (ascii - 65 + 13) % 26 + 65
    return data


class Rot13Daemon:

    def __init__(self, client, server):
        pass

    def encode(self, data):
        return rot13(data)

    def decode(self, data):
        return rot13(data)


class Rot13Client(Rot13Daemon):

    pass


class Rot13Server:

    pass


