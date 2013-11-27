#!/usr/bin/python
# -*- coding: utf-8 -*-

from twisted.internet import reactor, error

from pyptlib.server import ServerTransportPlugin
from pyptlib.config import EnvError

import obfsproxy.transports.transports as transports
import obfsproxy.network.launch_transport as launch_transport
import obfsproxy.common.log as logging
import obfsproxy.common.transport_config as transport_config

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
    server_transport_options = ptserver.config.getServerTransportOptions()

    for transport, transport_bindaddr in ptserver.getBindAddresses().items():

        # Will hold configuration parameters for the pluggable transport module.
        pt_config = transport_config.TransportConfig()
        pt_config.setStateLocation(ptserver.config.getStateLocation())
        transport_options = ""

        if server_transport_options and transport in server_transport_options:
            transport_options = server_transport_options[transport]
            pt_config.setServerTransportOptions(transport_options)

        # Call setup() method for this tranpsort.
        transport_class = transports.get_transport_class(transport, 'server')
        transport_class.setup(pt_config)

        try:
            if ext_orport:
                addrport = launch_transport.launch_transport_listener(transport,
                                                                      transport_bindaddr,
                                                                      'ext_server',
                                                                      ext_orport,
                                                                      pt_config,
                                                                      ext_or_cookie_file=authcookie)
            else:
                addrport = launch_transport.launch_transport_listener(transport,
                                                                      transport_bindaddr,
                                                                      'server',
                                                                      orport,
                                                                      pt_config)
        except transports.TransportNotFound:
            log.warning("Could not find transport '%s'" % transport)
            ptserver.reportMethodError(transport, "Could not find transport.")
            continue
        except error.CannotListenError:
            log.warning("Could not set up listener for '%s'." % transport)
            ptserver.reportMethodError(transport, "Could not set up listener.")
            continue

        should_start_event_loop = True

        extra_log = "" # Include server transport options in the log message if we got 'em
        if transport_options:
            extra_log = " (server transport options: '%s')" % str(transport_options)
        log.debug("Successfully launched '%s' at '%s'%s" % (transport, log.safe_addr_str(str(addrport)), extra_log))

        # Potentially filter the transport options
        # with the transport's get_public_options() method
        public_options_dict = transport_class.get_public_options(transport_options)
        public_options_str  = None

        # if we have filter
        if public_options_dict is not None:
            optlist            = []
            for k, v in public_options_dict.items():
                optlist.append("%s=%s" % (k,v))
            public_options_str = ",".join(optlist)

            log.debug("do_managed_server: sending only public_options to tor: %s" % public_options_str)

        # Report success for this transport.
        # If public_options_str is None then all of the
        # transport options from ptserver are used instead.
        ptserver.reportMethodSuccess(transport, addrport, public_options_str)

    ptserver.reportMethodsEnd()

    if should_start_event_loop:
        log.info("Starting up the event loop.")
        reactor.run()
    else:
        log.info("No transports launched. Nothing to do.")
