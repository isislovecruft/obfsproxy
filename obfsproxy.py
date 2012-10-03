#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
This is the command line interface to py-obfsproxy.
It is designed to be a drop-in replacement for the obfsproxy executable.
Currently, not all of the obfsproxy command line options have been implemented.
"""

import os
import sys
import argparse
import obfsproxy.transports.transports as transports
import obfsproxy.common.log as log

from pyptlib.util import checkClientMode

from obfsproxy.managed.server import ManagedServer
from obfsproxy.managed.client import ManagedClient

def set_up_cli_parsing():
    """Set up our CLI parser. Register our arguments and options and
    query individual transports to register their own external-mode
    arguments."""

    parser = argparse.ArgumentParser(
        description='py-obfsproxy: A pluggable transports proxy written in Python')
    subparsers = parser.add_subparsers(title='supported transports', dest='name')

    parser.add_argument('--log-file', help='set logfile')
    parser.add_argument('--log-min-severity',
                        choices=['error', 'warning', 'info', 'debug'],
                        help='set minimum logging severity (default: %(default)s)')
    parser.add_argument('--no-log', action='store_true', default=False,
                        help='disable logging')
# XXX
#    parser.add_argument('--no-safe-logging', action='store_true',
#                        default=False,
#                        help='disable safe (scrubbed address) logging')

    """Managed mode is a subparser for now because there are no
    optional subparsers: bugs.python.org/issue9253"""
    sp = subparsers.add_parser("managed", help="managed mode")

    """Add a subparser for each transport. Also add a
    transport-specific function to later validate the parsed
    arguments."""
    for transport, transport_class in transports.transports.items():
        subparser = subparsers.add_parser(transport, help='%s help' % transport)
        transport_class['client'].register_external_mode_cli(subparser) # XXX
        subparser.set_defaults(validation_function=transport_class['client'].validate_external_mode_cli)

    return parser

def do_managed_mode(): # XXX bad code
    """This function starts obfsproxy's managed-mode functionality."""

    # XXX original code caught exceptions here!!!
    if checkClientMode():
        log.debug('Entering client managed-mode.')
        ManagedClient()
    else:
        log.error('Entering server managed-mode.')
        ManagedServer()

def do_external_mode(args):
    """This function starts obfsproxy's external-mode functionality."""

    assert(args)
    assert(args.name)
    assert(args.name in transports.transports)

    transportClass = transports.get_transport_class_from_name_and_mode(args.name, args.mode)
    if (transportClass is None):
        log.error("Transport class was not found for '%s' in mode '%s'" % (args.name, args.mode))
        sys.exit(1)

    # XXX functionify
    import obfsproxy.network.network as network
    import obfsproxy.network.socks as socks
    from twisted.internet import reactor, error, address, tcp

    if (args.mode == 'client') or (args.mode == 'server'):
        factory = network.StaticDestinationServerFactory(args.dest, args.mode, transportClass)
    elif args.mode == 'socks':
        factory = socks.SOCKSv4Factory(transportClass)

    reactor.listenTCP(int(args.listen_addr[1]), factory)
    reactor.run()


def consider_cli_args(args):
    """Check out parsed CLI arguments and take the appropriate actions."""

    if args.log_file:
        log.set_log_file(args.log_file)
    if args.log_min_severity:
        log.set_log_severity(args.log_min_severity)
    if args.no_log:
        log.disable_logs()

    # validate:
    if (args.name == 'managed') and (not args.log_file) and (args.log_min_severity):
        log.error("obfsproxy in managed-proxy mode can only log to a file!")
        sys.exit(1)
    elif (args.name == 'managed') and (not args.log_file):
        # managed proxies without a logfile must not log at all.
        log.disable_logs()

def main(argv):
    parser = set_up_cli_parsing()

    args = parser.parse_args()

    consider_cli_args(args)

    log.debug('obfsproxy starting up!')
    log.debug('argv: ' + str(sys.argv))
    log.debug('args: ' + str(args))

    if (args.name == 'managed'):
        do_managed_mode()
    else:
        # Pass parsed arguments to the appropriate transports so that
        # they can initialize and setup themselves. Exit if the
        # provided arguments were corrupted.
        if (args.validation_function(args) == False):
            sys.exit(1)

        do_external_mode(args)

if __name__ == '__main__':
    main(sys.argv[1:])
