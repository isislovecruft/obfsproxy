#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
This is the command line interface to py-obfsproxy.
It is designed to be a drop-in replacement for the obfsproxy executable.
Currently, not all of the obfsproxy command line options have been implemented.
"""

import sys

import obfsproxy.network.launch_transport as launch_transport
import obfsproxy.transports.transports as transports
import obfsproxy.common.log as logging
import obfsproxy.common.argparser as argparser
import obfsproxy.common.heartbeat as heartbeat
import obfsproxy.common.transport_config as transport_config
import obfsproxy.managed.server as managed_server
import obfsproxy.managed.client as managed_client
from obfsproxy import __version__

from pyptlib.config import checkClientMode

from twisted.internet import task # for LoopingCall

log = logging.get_obfslogger()

def set_up_cli_parsing():
    """Set up our CLI parser. Register our arguments and options and
    query individual transports to register their own external-mode
    arguments."""

    parser = argparser.MyArgumentParser(
        description='py-obfsproxy: A pluggable transports proxy written in Python')
    subparsers = parser.add_subparsers(title='supported transports', dest='name')

    parser.add_argument('-v', '--version', action='version', version=__version__)
    parser.add_argument('--log-file', help='set logfile')
    parser.add_argument('--log-min-severity',
                        choices=['error', 'warning', 'info', 'debug'],
                        help='set minimum logging severity (default: %(default)s)')
    parser.add_argument('--no-log', action='store_true', default=False,
                        help='disable logging')
    parser.add_argument('--no-safe-logging', action='store_true',
                        default=False,
                        help='disable safe (scrubbed address) logging')
    parser.add_argument('--data-dir', help='where persistent information should be stored.',
                        default=None)

    # Managed mode is a subparser for now because there are no
    # optional subparsers: bugs.python.org/issue9253
    subparsers.add_parser("managed", help="managed mode")

    # Add a subparser for each transport. Also add a
    # transport-specific function to later validate the parsed
    # arguments.
    for transport, transport_class in transports.transports.items():
        subparser = subparsers.add_parser(transport, help='%s help' % transport)
        transport_class['base'].register_external_mode_cli(subparser)
        subparser.set_defaults(validation_function=transport_class['base'].validate_external_mode_cli)

    return parser

def do_managed_mode():
    """This function starts obfsproxy's managed-mode functionality."""

    if checkClientMode():
        log.info('Entering client managed-mode.')
        managed_client.do_managed_client()
    else:
        log.info('Entering server managed-mode.')
        managed_server.do_managed_server()

def do_external_mode(args):
    """This function starts obfsproxy's external-mode functionality."""

    assert(args)
    assert(args.name)
    assert(args.name in transports.transports)

    from twisted.internet import reactor

    pt_config = transport_config.TransportConfig()
    pt_config.setStateLocation(args.data_dir)

    # Run setup() method.
    run_transport_setup(pt_config)

    launch_transport.launch_transport_listener(args.name, args.listen_addr, args.mode, args.dest, pt_config, args.ext_cookie_file)
    log.info("Launched '%s' listener at '%s:%s' for transport '%s'." % \
                 (args.mode, log.safe_addr_str(args.listen_addr[0]), args.listen_addr[1], args.name))
    reactor.run()

def consider_cli_args(args):
    """Check out parsed CLI arguments and take the appropriate actions."""

    if args.log_file:
        log.set_log_file(args.log_file)
    if args.log_min_severity:
        log.set_log_severity(args.log_min_severity)
    if args.no_log:
        log.disable_logs()
    if args.no_safe_logging:
        log.set_no_safe_logging()

    # validate:
    if (args.name == 'managed') and (not args.log_file) and (args.log_min_severity):
        log.error("obfsproxy in managed-proxy mode can only log to a file!")
        sys.exit(1)
    elif (args.name == 'managed') and (not args.log_file):
        # managed proxies without a logfile must not log at all.
        log.disable_logs()

def run_transport_setup(pt_config):
    """Run the setup() method for our transports."""
    for transport, transport_class in transports.transports.items():
        transport_class['base'].setup(pt_config)

def pyobfsproxy():
    """Actual pyobfsproxy entry-point."""
    parser = set_up_cli_parsing()

    args = parser.parse_args()

    consider_cli_args(args)

    log.warning('Obfsproxy (version: %s) starting up.' % (__version__))

    log.debug('argv: ' + str(sys.argv))
    log.debug('args: ' + str(args))

    # Fire up our heartbeat.
    l = task.LoopingCall(heartbeat.heartbeat.talk)
    l.start(3600.0, now=False) # do heartbeat every hour

    # Initiate obfsproxy.
    if (args.name == 'managed'):
        do_managed_mode()
    else:
        # Pass parsed arguments to the appropriate transports so that
        # they can initialize and setup themselves. Exit if the
        # provided arguments were corrupted.

        # XXX use exceptions
        if (args.validation_function(args) == False):
            sys.exit(1)

        do_external_mode(args)

def run():
    """Fake entry-point so that we can log unhandled exceptions."""

    # Pyobfsproxy's CLI uses "managed" whereas C-obfsproxy uses
    # "--managed" to configure managed-mode. Python obfsproxy can't
    # recognize "--managed" because it uses argparse subparsers and
    # http://bugs.python.org/issue9253 is not yet solved. This is a crazy
    # hack to maintain CLI compatibility between the two versions. we
    # basically inplace replace "--managed" with "managed" in the argument
    # list.
    if len(sys.argv) > 1 and '--managed' in sys.argv:
        for n, arg in enumerate(sys.argv):
            if arg == '--managed':
                sys.argv[n] = 'managed'

    try:
        pyobfsproxy()
    except Exception, e:
        log.exception(e)
        raise

if __name__ == '__main__':
    run()
