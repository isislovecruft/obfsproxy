#!/usr/bin/python
# -*- coding: utf-8 -*-

from twisted.internet import reactor, error

from pyptlib.server import ServerTransportPlugin
from pyptlib.config import EnvError

import obfsproxy.transports.transports as transports
import obfsproxy.network.launch_transport as launch_transport
import obfsproxy.common.log as logging

import pprint

log = logging.get_obfslogger()

def do_managed_server():
    """Start the managed-proxy protocol as a server."""

    should_start_event_loop = False

    ptserver = ServerTransportPlugin()
    try:
        ptserver.init(transports.transports.keys())
    except EnvError, err:
        log.warning("Server managed-proxy protocol failed (%s)." % err)
        return

    log.debug("pyptlib gave us the following data:\n'%s'", pprint.pformat(ptserver.getDebugData()))

    ext_orport = ptserver.config.getExtendedORPort()
    authcookie = ptserver.config.getAuthCookieFile()
    orport = ptserver.config.getORPort()
    for transport, transport_bindaddr in ptserver.getBindAddresses().items():
        try:
            if ext_orport:
                addrport = launch_transport.launch_transport_listener(transport,
                                                                      transport_bindaddr,
                                                                      'ext_server',
                                                                      ext_orport,
                                                                      authcookie)
            else:
                addrport = launch_transport.launch_transport_listener(transport,
                                                                      transport_bindaddr,
                                                                      'server',
                                                                      orport)
        except transports.TransportNotFound:
            log.warning("Could not find transport '%s'" % transport)
            ptserver.reportMethodError(transport, "Could not find transport.")
            continue
        except error.CannotListenError:
            log.warning("Could not set up listener for '%s'." % transport)
            ptserver.reportMethodError(transport, "Could not set up listener.")
            continue

        should_start_event_loop = True
        log.debug("Successfully launched '%s' at '%s'" % (transport, log.safe_addr_str(str(addrport))))
        ptserver.reportMethodSuccess(transport, addrport, None)

    ptserver.reportMethodsEnd()

    if should_start_event_loop:
        log.info("Starting up the event loop.")
        reactor.run()
    else:
        log.info("No transports launched. Nothing to do.")
