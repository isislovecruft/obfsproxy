#!/usr/bin/python
# -*- coding: utf-8 -*-

from twisted.internet import reactor, error

import obfsproxy.network.launch_transport as launch_transport
import obfsproxy.transports.transports as transports
import obfsproxy.common.log as logging

from pyptlib.client import init, reportSuccess, reportFailure, reportEnd
from pyptlib.config import EnvError

import pprint

log = logging.get_obfslogger()

def do_managed_client():
    """Start the managed-proxy protocol as a client."""

    should_start_event_loop = False

    try:
        managedInfo = init(transports.transports.keys())
    except EnvError, err:
        log.warning("Client managed-proxy protocol failed (%s)." % err)
        return

    log.debug("pyptlib gave us the following data:\n'%s'", pprint.pformat(managedInfo))

    for transport in managedInfo['transports']:
        try:
            addrport = launch_transport.launch_transport_listener(transport, None, 'socks', None)
        except transports.TransportNotFound:
            log.warning("Could not find transport '%s'" % transport)
            reportFailure(transport, "Could not find transport.")
            continue
        except error.CannotListenError:
            log.warning("Could not set up listener for '%s'." % transport)
            reportFailure(transport, "Could not set up listener.")
            continue

        should_start_event_loop = True
        log.debug("Successfully launched '%s' at '%s'" % (transport, log.safe_addr_str(str(addrport))))
        reportSuccess(transport, 4, addrport, None, None)

    reportEnd()

    if should_start_event_loop:
        log.info("Starting up the event loop.")
        reactor.run()
    else:
        log.info("No transports launched. Nothing to do.")
