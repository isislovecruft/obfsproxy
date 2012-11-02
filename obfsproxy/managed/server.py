#!/usr/bin/python
# -*- coding: utf-8 -*-

from twisted.internet import reactor, error, address, tcp

from pyptlib.server import init, reportSuccess, reportFailure, reportEnd
from pyptlib.config import EnvError

import obfsproxy.network.network as network
import obfsproxy.transports.transports as transports
import obfsproxy.network.launch_transport as launch_transport
import obfsproxy.common.log as log

import pprint

def do_managed_server():
    should_start_event_loop = False

    try:
        managedInfo = init(transports.transports.keys())
    except EnvError:
        log.warning("Server managed-proxy protocol failed.")
        return

    log.debug("pyptlib gave us the following data:\n'%s'", pprint.pformat(managedInfo))

    for transport, transport_bindaddr in managedInfo['transports'].items():
        try:
            addrport = launch_transport.launch_transport_listener(transport,
                                                                  transport_bindaddr,
                                                                  'server',
                                                                  managedInfo['orport'])
        except transports.TransportNotFound:
            log.warning("Could not find transport '%s'" % transport)
            reportFailure(transport, "Could not find transport.")
            continue
        except error.CannotListenError:
            log.warning("Could not set up listener for '%s'." % transport)
            reportFailure(transport, "Could not set up listener.")
            continue

        should_start_event_loop = True
        log.debug("Successfully launched '%s' at '%s'" % (transport, str(addrport)))
        reportSuccess(transport, addrport, None)

    reportEnd()

    if should_start_event_loop:
        log.info("Starting up the event loop.")
        reactor.run()
    else:
        log.info("No transports launched. Nothing to do.")
