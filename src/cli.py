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
import obfsproxy.transports.base as base
import obfsproxy.common.log as log

# XXX kill these
sys.path.insert(0,
                os.path.realpath(os.path.join(os.path.dirname(__file__),
                '../../Dust/py')))
sys.path.insert(0,
                os.path.realpath(os.path.join(os.path.dirname(__file__),
                '../../pyptlib/src')))

from pyptlib.easy.util import checkClientMode

try:
    from obfsproxy.framework.managed.server import ManagedServer
    from obfsproxy.framework.managed.client import ManagedClient
except Exception, e:
    log.error('Error loading framework: ' + str(e))

def set_up_cli_parsing():
    """Set up our CLI parser. Register our arguments and options and
    query individual transports to register their own external-mode
    arguments."""

    parser = argparse.ArgumentParser(
        description='py-obfsproxy: A pluggable transports proxy written in Python')
    subparsers = parser.add_subparsers(title='supported transports', dest='name')

    parser.add_argument('--log-file', help='set logfile')
    parser.add_argument('--log-min-severity', default='warning',
                        choices=['error', 'warning', 'info', 'debug'],
                        help='set minimum logging severity (default: %(default)s)')
    parser.add_argument('--no-log', action='store_true', default=False,
                        help='disable logging')
    parser.add_argument('--no-safe-logging', action='store_true',
                        default=False,
                        help='disable safe (scrubbed address) logging')

    """Managed mode is a subparser for now because there are no
    optional subparsers: bugs.python.org/issue9253"""
    sp = subparsers.add_parser("managed", help="managed mode")

    """Add a subparser for each transport."""
    for transport, transport_class in base.transports.items():
        subparser = subparsers.add_parser(transport, help='%s help' % transport)
        transport_class['client'].register_external_mode_cli(subparser) # XXX

    return parser

def do_managed_mode(): # XXX bad code
    """This function starts obfsproxy's managed-mode functionality."""

    # XXX original code caught exceptions here!!!
    if checkClientMode():
        log.error('client')
        ManagedClient()
    else:
        log.error('server')
        ManagedServer()

def do_external_mode(args):
    """This function starts obfsproxy's external-mode functionality."""

    assert(args)
    assert(args.name)
    assert(args.name in base.transports)

    our_class = base.get_transport_class_from_name_and_mode(args.name, args.mode)

    if (our_class is None):
        log.error("Transport class was not found for '%s' in mode '%s'" % (args.name, args.mode))
        sys.exit(1)


    # XXX ugly code:
    from obfsproxy.framework.proxy import ProxyHandler
    from monocle.stack import eventloop
    from monocle.stack.network import add_service, Service

    handler = ProxyHandler(args.dest[0], int(args.dest[1]))
    handler.setTransport(our_class)
    add_service(Service(handler.handle, bindaddr=args.listen_addr[0], port=int(args.listen_addr[1])))
    eventloop.run()

def main(argv):
    parser = set_up_cli_parsing()

    args = parser.parse_args()

    if args.log_file:
        log.set_log_file(args.log_file)
    if args.log_min_severity:
        log.set_log_severity(args.log_min_severity)
    if args.no_log:
        log.disable_logs()
    if args.no_safe_logging:
        pass # XXX

    # XXX do sanity checks. like in case managed is set along with external options etc.

    log.error('py-obfsproxy CLI loaded')
    log.warning('argv: ' + str(sys.argv))

    if (args.name == 'managed'):
        do_managed_mode()
    else:
        do_external_mode(args)

if __name__ == '__main__':
    main(sys.argv[1:])
