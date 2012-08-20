#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
This module contains the Manager class, the base class for client and server managers.
Managers are command line tools used for testing transports. They simulate Tor by launching transports and providing similar environment variables as would be provided by Tor.
Managers are only necessary for testing. In actual deployment, Tor can be used.
"""

import os
import sys
import subprocess


class Manager:

    """ The Manager class is the base class for client and server managers. """

    def __init__(self):
        """
        Initialize the environment variables which are used by both clients and servers.
        These are TOR_PT_STATE_LOCATION and TOR_PT_MANAGED_TRANSPORT_VER
        """

        os.environ['TOR_PT_STATE_LOCATION'] = '/'
        os.environ['TOR_PT_MANAGED_TRANSPORT_VER'] = '1'

    def launch(self):
        """
        Launch the client or server process and wait for it to exit, in the meantime printing any output it generates.
        Launching of the client and server is identical.
        The client/server behavior is determined by which environment variables have been set by the ClientManager and ServerManager subclasses.
        """

        p = subprocess.Popen(['python', '-u', 'src/cli.py', '--managed'
                             ], stdout=subprocess.PIPE)
        line = p.stdout.readline().strip()
        while line != None and line != '':
            print str(line)
            sys.stdout.flush()
            line = p.stdout.readline().strip()
        print 'Done!'


