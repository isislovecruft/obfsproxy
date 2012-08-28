#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
This module contains the ServerManager class, which implemnts a server manager.
Managers are command line tools used for testing transports. They simulate Tor by launching transports and providing similar environment variables as would be provided by Tor.
Managers are only necessary for testing. In actual deployment, Tor can be used.
"""

import os
import sys

from obfsproxy.manager.manager import Manager


class ServerManager(Manager):

    """ The ServerManager class implemnts a client manager. """

    def __init__(self, transport):
        """
        Call superclass initializer to initialize the environment variables which are used by both clients and servers.
        Then initialize the environment variables which are used bo just servers.
        These are TOR_PT_EXTENDED_SERVER_PORT, TOR_PT_ORPORT, TOR_PT_SERVER_BINDADDR, and TOR_PT_SERVER_TRANSPORTS.
        """

        Manager.__init__(self)

        os.environ['TOR_PT_EXTENDED_SERVER_PORT'] = '127.0.0.1:22211'
        os.environ['TOR_PT_ORPORT'] = '127.0.0.1:43210'
        os.environ['TOR_PT_SERVER_BINDADDR'] = transport \
            + '-127.0.0.1:46466'
        os.environ['TOR_PT_SERVER_TRANSPORTS'] = transport


if __name__ == '__main__':
    if len(sys.argv)<2:
      print('serverManager [transport]')
    else:
      transport = sys.argv[1]
      manager = ServerManager(transport)
      manager.launch()
