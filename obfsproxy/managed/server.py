#!/usr/bin/python
# -*- coding: utf-8 -*-

# XXX put listener/client-creation functions in their own file
import obfsproxy.network.network as network
from twisted.internet import reactor, error, address, tcp

import obfsproxy.transports.transports as transports

from pyptlib.server import init, reportSuccess, reportFailure, reportEnd
from pyptlib.config import EnvError

import obfsproxy.common.log as log
import pprint

class ManagedServer:

    def __init__(self):
        try:
            managedInfo = init(transports.transports.keys())
        except EnvError:
            log.warn("Server managed-proxy protocol failed.")
            return

        log.debug("pyptlib gave us the following data:\n'%s'", pprint.pformat(managedInfo))

        for transport, transport_bindaddr in managedInfo['transports'].items():
            ok, addrport = self.launchServer(transport, transport_bindaddr, managedInfo)
            if ok:
                log.debug("Successfully launched '%s' at '%s'" % (transport, str(addrport)))
                reportSuccess(transport, addrport, None)
            else:
                log.info("Failed to launch '%s' at '%s'" % (transport, str(addrport)))
                reportFailure(transport, 'Failed to launch')

        reportEnd()

        log.info("Starting up the event loop.")
        reactor.run()

    def launchServer(self, name, bindaddr, managedInfo):
        """
        Launch a client of transport 'name' using the environment
        information in 'managedInfo'.

        Return a tuple (<ok>, (<addr>, <port>)), where <ok> is whether
        the function was successful, and (<addr>, <port> is a tuple
        representing where we managed to bind.
        """

        serverClass = transports.get_transport_class_from_name_and_mode(name, 'server')
        if not serverClass:
            log.error("Could not find transport class for '%s' (%s)." % (name, 'server'))
            return False, None

        factory = network.StaticDestinationServerFactory(managedInfo['orport'], 'server', serverClass)

        try:
            addrport = reactor.listenTCP(int(bindaddr[1]), factory)
        except CannotListenError:
            log.error("Could not set up a listener for TCP port '%s'." % bindaddr[1])
            return False, None

        return True, (addrport.getHost().host, addrport.getHost().port)

if __name__ == '__main__':
    server = ManagedServer()
