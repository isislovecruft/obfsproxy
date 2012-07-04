#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse

from pyptlib.easy.util import checkClientMode

from obfsproxy.framework.managed.server import ManagedServer
from obfsproxy.framework.managed.client import ManagedClient

protocols = ['dummy', 'rot13']

if __name__ == '__main__':
    parser = \
        argparse.ArgumentParser(description='* Available protocols: '
                                + ' '.join(protocols))
    parser.add_argument('--log-file', nargs=1, help='set logfile')
    parser.add_argument('--log-min-severity', nargs=1, default='notice'
                        , choices=['warn', 'notice', 'info', 'debug'],
                        help='set minimum logging severity (default: %(default)s)'
                        )
    parser.add_argument('--no-log', action='store_false', default=True,
                        help='disable logging')
    parser.add_argument('--no-safe-logging', action='store_false',
                        default=True,
                        help='disable safe (scrubbed address) logging')
    parser.add_argument('--managed', action='store_true',
                        default=False,
                        help='enabled managed mode, for use when called by tor'
                        )

#    parser.add_argument('--dest', nargs=1,
#                        help='set destination, enable client mode instead of server mode'
#                        )

#    parser.add_argument('obfsproxy_args')
#    parser.add_argument('protocol_name')
#    parser.add_argument('protocol_args')
#    parser.add_argument('protocol_options')
#    parser.add_argument('protocol_name')

    args = parser.parse_args()

    daemon = None
    if args.managed:
        if checkClientMode():
            daemon = ManagedClient()
        else:
            daemon = ManagedServer()
    else:
        print 'Unsupported mode. Only managed mode is available at the moment.'

#        if dest:
#            daemon = ExternalClient()
#        else:
#            daemon = ExternalServer()
