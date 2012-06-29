#!/usr/bin/python
# -*- coding: utf-8 -*-
import os

from pyptlib.manager.manager import Manager


class ServerManager(Manager):

    def __init__(self):
        Manager.__init__(self)

        os.environ['TOR_PT_EXTENDED_SERVER_PORT'] = '127.0.0.1:22211'
        os.environ['TOR_PT_ORPORT'] = '127.0.0.1:43210'
        os.environ['TOR_PT_SERVER_BINDADDR'] = 'dummy-127.0.0.1:46466'
        os.environ['TOR_PT_SERVER_TRANSPORTS'] = 'dummy'


if __name__ == '__main__':
    manager = ServerManager()
    manager.launch('src/pyptlib/framework/server.py')
