#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import subprocess


class Manager:

    def __init__(self):
        os.environ['TOR_PT_STATE_LOCATION'] = '/'
        os.environ['TOR_PT_MANAGED_TRANSPORT_VER'] = '1'

    def launch(self):
        p = subprocess.Popen(['python', '-u', 'src/cli.py', '--managed'
                             ], stdout=subprocess.PIPE)
        line = p.stdout.readline().strip()
        while line != None and line != '':
            print str(line)
            sys.stdout.flush()
            line = p.stdout.readline().strip()
        print 'Done!'


