#!/usr/bin/python
# -*- coding: utf-8 -*-

import obfsproxy.common.log as logging
import argparse

log = logging.get_obfslogger()

"""
This module contains BaseTransport, a pluggable transport skeleton class.
"""

def addrport(string):
    """
    Receive '<addr>:<port>' and return [<addr>,<port>].
    Used during argparse CLI parsing.
    """

    addrport = string.split(':')

    if (len(addrport) != 2):
        msg = "'%s' is not in <addr>:<port> format" % string
        raise argparse.ArgumentTypeError(msg)

    return addrport

class BaseTransport:
    """
    The BaseTransport class is a skeleton class for pluggable transports.
    It contains callbacks that your pluggable transports should
    override and customize.
    """

    def __init__(self):
        pass

    def handshake(self, circuit):
        """
        The Circuit 'circuit' was completed, and this is a good time
        to do your transport-specific handshake on its downstream side.
        """
        pass

    def circuitDestroyed(self, circuit):
        """
        Circuit 'circuit' was tore down.
        Both connections of the circuit are closed when this callback triggers.
        """
        pass

    def receivedDownstream(self, data, circuit):
        """
        Received 'data' in the downstream side of 'circuit'.
        'data' is an obfsproxy.network.buffer.Buffer.
        """
        pass

    def receivedUpstream(self, data, circuit):
        """
        Received 'data' in the upstream side of 'circuit'.
        'data' is an obfsproxy.network.buffer.Buffer.
        """
        pass

    @classmethod
    def register_external_mode_cli(cls, subparser):
        """
        Given an argparse ArgumentParser in 'subparser', register
        some default external-mode CLI arguments.

        Transports with more complex CLI are expected to override this
        function.
        """

        subparser.add_argument('mode', choices=['server', 'client', 'socks'])
        subparser.add_argument('listen_addr', type=addrport)
        subparser.add_argument('--dest', type=addrport, help='Destination address')

    @classmethod
    def validate_external_mode_cli(cls, args):
        """
        Given the parsed CLI arguments in 'args', validate them and
        make sure they make sense. Return True if they are kosher,
        otherwise return False.

        Override for your own needs.
        """

        # If we are not 'socks', we need to have a static destination
        # to send our data to.
        if (args.mode != 'socks') and (not args.dest):
            log.error("'client' and 'server' modes need a destination address.")
            return False

        return True

class PluggableTransportError(Exception): pass
