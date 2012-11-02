import obfsproxy.network.network as network
import obfsproxy.transports.transports as transports
import obfsproxy.network.socks as socks
from twisted.internet import reactor

def launch_transport_listener(transport, bindaddr, role, remote_addrport):
    """
    Launch a listener for 'transport' in role 'role' (socks/client/server).

    If 'bindaddr' is set, then listen on bindaddr. Otherwise, listen
    on an ephemeral port on localhost.
    'remote_addrport' is the TCP/IP address of the other end of the
    circuit. It's not used if we are in 'socks' role.

    Return a tuple (addr, port) representing where we managed to bind.

    Throws obfsproxy.transports.transports.TransportNotFound if the
    transport could not be found.

    Throws twisted.internet.error.CannotListenError if the listener
    could not be set up.
    """

    transport_class = transports.get_transport_class(transport, role)
    listen_host = bindaddr[0] if bindaddr else 'localhost'
    listen_port = int(bindaddr[1]) if bindaddr else 0

    if role == 'socks':
        factory = socks.SOCKSv4Factory(transport_class)
    else:
        assert(remote_addrport)
        factory = network.StaticDestinationServerFactory(remote_addrport, role, transport_class)

    if role == 'server':
        addrport = reactor.listenTCP(listen_port, factory)
    else:
        addrport = reactor.listenTCP(listen_port, factory, interface=listen_host)

    return (addrport.getHost().host, addrport.getHost().port)
