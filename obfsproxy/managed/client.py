#!/usr/bin/python
# -*- coding: utf-8 -*-

# XXX put listener/client-creation functions in their own file
import obfsproxy.network.socks as socks
from twisted.internet import reactor, error

import obfsproxy.transports.transports as transports

from pyptlib.client import init, reportSuccess, reportFailure, reportEnd
from pyptlib.config import EnvException

import obfsproxy.common.log as log
import pprint

class ManagedClient:

    def __init__(self):
        try:
            managedInfo = init(transports.transports.keys())
        except EnvException:
            log.warn("Client managed-proxy protocol failed.")
            return

        log.debug("pyptlib gave us the following data:\n'%s'", pprint.pformat(managedInfo))

        for transport in managedInfo['transports']:
            ok, addrport = self.launchClient(transport, managedInfo) # XXX start using exceptions
            if ok:
                log.debug("Successfully launched '%s' at '%s'" % (transport, str(addrport)))
                reportSuccess(transport, 4, addrport, None, None) # XXX SOCKS v4 hardcoded
            else:
                log.info("Failed to launch '%s'" % transport)
                reportFailure(transport, 'Failed to launch')

        reportEnd()

        log.info("Starting up the event loop.")
        reactor.run()

    # XXX turn into a function to be used by exteral-mode code, etc.
    def launchClient(self, name, managedInfo):
        """
        Launch a client of transport 'name' using the environment
        information in 'managedInfo'.

        Return a tuple (<ok>, (<addr>, <port>)), where <ok> is whether
        the function was successful, and (<addr>, <port> is a tuple
        representing where we managed to bind.
        """

        clientClass = transports.get_transport_class_from_name_and_mode(name, 'client')
        if not clientClass:
            log.error("Could not find transport class for '%s' (%s)." % (name, 'client'))
            return False, None

        factory = socks.SOCKSv4Factory(clientClass)

        try:
            addrport = reactor.listenTCP(0, factory, interface='localhost')
        except error.CannotListenError:
            log.error("Could not set up a client listener.")
            return False, None

        return True, (addrport.getHost().host, addrport.getHost().port)
