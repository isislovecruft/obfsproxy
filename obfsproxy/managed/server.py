#!/usr/bin/python
# -*- coding: utf-8 -*-

from twisted.internet import reactor, error

from pyptlib.server import init, reportSuccess, reportFailure, reportEnd
from pyptlib.config import EnvError

import obfsproxy.transports.transports as transports
import obfsproxy.network.launch_transport as launch_transport
import obfsproxy.common.log as logging

import pprint

log = logging.get_obfslogger()

def do_managed_server():
    """Start the managed-proxy protocol as a server."""

    should_start_event_loop = False

    try:
        managed_info = init(transports.transports.keys())
    except EnvError, err:
        log.warning("Server managed-proxy protocol failed (%s)." % err)
        return

    log.debug("pyptlib gave us the following data:\n'%s'", pprint.pformat(managed_info))

    for transport, transport_bindaddr in managed_info['transports'].items():
        try:
            if managed_info['ext_orport']:
                addrport = launch_transport.launch_transport_listener(transport,
                                                                      transport_bindaddr,
                                                                      'ext_server',
                                                                      managed_info['ext_orport'],
                                                                      managed_info['auth_cookie_file'])
            else:
                addrport = launch_transport.launch_transport_listener(transport,
                                                                      transport_bindaddr,
                                                                      'server',
                                                                      managed_info['orport'])
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
        reportSuccess(transport, addrport, None)

    reportEnd()

    if should_start_event_loop:
        log.info("Starting up the event loop.")
        reactor.run()
    else:
        log.info("No transports launched. Nothing to do.")
