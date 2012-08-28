#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
This is the command line interface to py-obfsproxy.
It is designed to be a drop-in replacement for the obfsproxy executable.
Currently, not all of the obfsproxy command line options have been implemented.
"""

import os
import sys
import logging

logging.basicConfig(filename='pyobfslog.txt', loglevel=logging.DEBUG)
logging.error('py-obfsproxy CLI loaded')
logging.error('argv: ' + str(sys.argv))

import argparse

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
    logging.error('Error loading framework: ' + str(e))

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

    try:
        args = parser.parse_args()
    except Exception, e:
        logging.error('Exception parsing')
        logging.error(str(e))

    if args.log_file and len(args.log_file)>0:
      logging.error('file logging: '+str(args.log_file[0])+' '+str(os.path.exists(args.log_file[0])))
      logging.config.fileConfig(str(args.log_file[0]), disable_existing_loggers=False)
      logging.error('new logging in place')

    logging.error('py-obfsproxy CLI loaded')

    try:
        daemon = None
        if args.managed:
            if checkClientMode():
                logging.error('client')
                daemon = ManagedClient()
            else:
                logging.error('server')
                daemon = ManagedServer()
        else:
            logging.error('Unsupported mode. Only managed mode is available at the moment.'
                      )
    except:
      logging.exception('Exception launching daemon')
