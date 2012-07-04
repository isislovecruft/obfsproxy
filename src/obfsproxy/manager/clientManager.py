#!/usr/bin/python
# -*- coding: utf-8 -*-

import os

from obfsproxy.manager.manager import Manager


class ClientManager(Manager):

    def __init__(self):
        Manager.__init__(self)

        os.environ['TOR_PT_CLIENT_TRANSPORTS'] = 'dummy'


if __name__ == '__main__':
    manager = ClientManager()
    manager.launch()