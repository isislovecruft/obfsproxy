#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
This module contains BaseDaemon, a base class for implementing pluggable transport clients and server.
It is not necessary to subclass BaseDaemon in order to implement pluggable transports.
However, BaseDaemon provides utility methods that are useful for a variety of common transports.
"""

def addrport(string):
  """Receive '<addr>:<port>' and return [<addr>,<port>]. Used during
  argparse CLI parsing."""

  addrport = string.split(':')

  if (len(addrport) != 2):
    msg = "'%s' is not in <addr>:<port> format" % string
    raise argparse.ArgumentTypeError(msg)

  return addrport

class BaseDaemon:

    """
    The BaseDaemon class is a base class for implementing pluggable transport clients and server.
    """

    def __init__(self, circuit):
        """ Store the upstream and downstream sockets for use in other methods. """

        self.downstreamConnection = circuit.downstream
        self.upstreamConnection = circuit.upstream

    @staticmethod
    def register_external_mode_cli(subparser):
        """ Given an argparse ArgumentParser in 'subparser', register
        some default external-mode CLI arguments. Transports with more
        complex CLI are expected to override this function."""

        subparser.add_argument('mode', choices=['server','client','socks'])
        subparser.add_argument('listen_addr', type=addrport)
        subparser.add_argument('--dest', type=addrport, help='Destination address')

    def read(
        self,
        socket,
        data,
        maxlen,
        ):
        """
        This read method is a convience method which takes a socket to read from, some existing data, and a maxlength.
        It reads bytes from socket and appends them to data until data is equal to maxlen, or the socket has no more bytes ready.
        It returns a new data object which is a combination of data and the bytes read from socket and which is <= maxlen.
        """

        remaining = maxlen - len(data)
        return data + socket.read(remaining)

    def checkTransition(
        self,
        data,
        maxlen,
        newState,
        ):
        """
        This is a convience method for state-based protocols which need to read fixed length data from the socket before they can change states.
        The checkTransition method takes some data, a max length, and state identifier.
        If len(data) == maxlen then the state is set to the state is set to newState and True is returned.
        Otherwise, the state stays the same and False is returned.
        """

        if len(data) == maxlen:
            state = newState
            return True
        else:
            return False

    def start(self):
        """
        This is the callback method which is called by the framework when a new connection has been made.
        In BaseDaemon it does nothing.
        It is overridden by subclasses.
        """

        pass

    def receivedDownstream(self):
        """
        This is the callback method which is called by the framework when bytes have been received on the downstream socket.
        In BaseDaemon it does nothing.
        It is overridden by subclasses.
        """

        pass

    def receivedUpstream(self):
        """
        This is the callback method which is called by the framework when bytes have been received on the upstream socket.
        In BaseDaemon it does nothing.
        It is overridden by subclasses.
        """

        pass

    def end(self):
        """
        This is the callback method which is called by the framework when the connection is closed.
        In BaseDaemon it does nothing.
        It is overridden by subclasses.
        """

        pass

# XXX modulify transports and move this to a single import
import obfsproxy.transports.dummy as dummy
import obfsproxy.transports.rot13 as rot13
import obfsproxy.transports.dust_transport as dust
# XXX obfs2 is broken...
#import obfsproxy.transports.obfs2 as obfs2
import obfsproxy.transports.obfs3 as obfs3

transports = { 'dummy' : {'client' : dummy.DummyClient, 'server' : dummy.DummyServer },
               'rot13' : {'client' : rot13.Rot13Client, 'server' : rot13.Rot13Server },
               'dust' :  {'client' : dust.DustClient, 'server' : dust.DustServer },
#               'obfs2' : {'client' : obfs2.Obfs2Client, 'server' : obfs2.Obfs2Server },
               'obfs3' : {'client' : obfs3.Obfs3Client, 'server' : obfs3.Obfs3Server } }

def get_transport_class_from_name_and_mode(name, mode):
    if (name in transports) and (mode in transports[name]):
        return transports[name][mode]
    else:
        return None
