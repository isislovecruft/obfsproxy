#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
This module contains the ClientManager class, which implemnts a client manager.
Managers are command line tools used for testing transports. They simulate Tor by launching transports and providing similar environment variables as would be provided by Tor.
Managers are only necessary for testing. In actual deployment, Tor can be used.
"""

import os
import sys

from obfsproxy.manager.manager import Manager


class ClientManager(Manager):

    """ The ClientManager class implemnts a client manager. """

    def __init__(self, transport):
        """
        Call superclass initializer to initialize the environment variables which are used by both clients and servers.
        Then initialize the environment variable which is used bo just clients.
        This is TOR_PT_CLIENT_TRANSPORTS.
        """

        Manager.__init__(self)

        os.environ['TOR_PT_CLIENT_TRANSPORTS'] = transport


if __name__ == '__main__':
    if len(sys.argv)<2:
      print('clientManager [transport]')
    else:
      try:
        transport = sys.argv[1]
        manager = ClientManager(transport)
        manager.launch()
      except Exception as e:
        print('Exception: '+str(e))
