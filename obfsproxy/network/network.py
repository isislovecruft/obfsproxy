# XXX fix imports
from twisted.python import failure
from twisted.internet import reactor, error, address, tcp
from twisted.internet.protocol import Protocol, Factory, ClientFactory

import obfsproxy.common.log as log

"""
Networking subsystem:

A "Connection" is a bidirectional communications channel, usually
backed by a network socket. For example, the communication channel
between tor and obfsproxy is a 'connection'. In the code, it's
represented by a Twisted's twisted.internet.protocol.Protocol.

A 'Circuit' is a pair of connections, referred to as the 'upstream'
and 'downstream' connections. The upstream connection of a circuit
communicates in cleartext with the higher-level program that wishes to
make use of our obfuscation service. The downstream connection
communicates in an obfuscated fashion with the remote peer that the
higher-level client wishes to contact. In the code, it's represented
by the custom Circuit class.

The diagram below might help demonstrate the relationship between
connections and circuits:

                                   Downstream

       'Circuit C'      'Connection CD'   'Connection SD'     'Circuit S'
                     +-----------+          +-----------+
     Upstream    +---|Obfsproxy c|----------|Obfsproxy s|----+   Upstream
                 |   +-----------+    ^     +-----------+    |
 'Connection CU' |                    |                      | 'Connection SU'
           +------------+           Sent over       +--------------+
           | Tor Client |           the net         |  Tor Bridge  |
           +------------+                           +--------------+

In the above diagram, "Obfsproxy c" is the client-side obfsproxy, and
"Obfsproxy s" is the server-side obfsproxy. "Connection CU" is the
Client's Upstream connection, the communication channel between tor
and obfsproxy. "Connection CD" is the Client's Downstream connection,
the communication channel between obfsproxy and the remote peer. These
two connections form the client's circuit "Circuit C".

A 'listener' is a listening socket bound to a particular obfuscation
protocol, represented using Twisted's t.i.p.Factory. Connecting to a
listener creates one connection of a circuit, and causes this program
to initiate the other connection (possibly after receiving in-band
instructions about where to connect to). A listener is said to be a
'client' listener if connecting to it creates the upstream connection,
and a 'server' listener if connecting to it creates the downstream
connection.

There are two kinds of client listeners: a 'simple' client listener
always connects to the same remote peer every time it needs to
initiate a downstream connection; a 'socks' client listener can be
told to connect to an arbitrary remote peer using the SOCKS protocol.
"""

class Circuit(Protocol):
    """
    A Circuit holds a pair of connections. The upstream connection and
    the downstream. The circuit proxies data from one connection to
    the other.

    Attributes:
    transport: the pluggable transport we should use to
               obfuscate traffic on this circuit.

    downstream: the downstream connection
    upstream: the upstream connection
    """

    def __init__(self, transport):
        self.transport = transport # takes a transport
        self.downstream = None # takes a connection
        self.upstream = None # takes a connection

        self.closed = False # True if the circuit is closed.

        self.name = "circ_%s" % hex(id(self))

    def setDownstreamConnection(self, conn): # XXX merge set{Downstream,Upstream}Connection.
        """
        Set the downstream connection of a circuit.
        """

        log.debug("%s: Setting downstream connection (%s)." % (self.name, conn.name))
        assert(not self.downstream)
        self.downstream = conn

        """We just completed the circuit.

        Do a dummy dataReceived on the initiating connection in case
        it has any buffered data that must be flushed to the network.

        Also, call the transport-specific handshake method since this
        is a good time to perform a handshake.
        """
        if self.circuitIsReady():
            self.upstream.dataReceived('') # XXX kind of a hack.
            self.transport.handshake(self)

    def setUpstreamConnection(self, conn):
        """
        Set the upstream connection of a circuit.
        """

        log.debug("%s: Setting upstream connection (%s)." % (self.name, conn.name))
        assert(not self.upstream)
        self.upstream = conn

        """We just completed the circuit.

        Do a dummy dataReceived on the initiating connection in case
        it has any buffered data that must be flushed to the network.

        Also, call the transport-specific handshake method since this
        is a good time to perform a handshake.
        """
        if self.circuitIsReady():
            self.downstream.dataReceived('')
            self.transport.handshake(self)

    def circuitIsReady(self):
        """
        Return True if the circuit is completed.
        """

        return self.downstream and self.upstream

    def dataReceived(self, data, conn):
        """
        We received 'data' on 'conn'. Pass the data to our transport,
        and then proxy it to the other side.

        Requires both downstream and upstream connections to be set.

        Returns the bytes that were not used by the transport.
        """
        log.debug("%s: Received %d bytes." % (self.name, len(data)))

        assert(self.downstream and self.upstream)
        assert((conn is self.downstream) or (conn is self.upstream))

        if conn is self.downstream:
            leftovers = self.transport.receivedDownstream(data, self)
        else:
            leftovers = self.transport.receivedUpstream(data, self)

        return leftovers

    def close(self):
        """
        Tear down the circuit.
        """
        if self.closed: return # NOP if already closed

        log.info("%s: Tearing down circuit." % self.name)

        if self.downstream: self.downstream.close()
        if self.upstream: self.upstream.close()
        self.closed = True

        self.transport.circuitDestroyed(self)

class StaticDestinationProtocol(Protocol):
    """
    Represents a connection to a static destination (as opposed to a
    SOCKS connection).

    Attributes:
    mode: 'server' or 'client'
    circuit: The circuit this connection belongs to.
    direction: 'downstream' or 'upstream'

    buffer: Buffer that holds data that can't be proxied right
            away. This can happen because the circuit is not yet
            complete, or because the pluggable transport needs more
            data before deciding what to do.
    """

    def __init__(self, circuit, mode):
        self.mode = mode
        self.circuit = circuit
        self.direction = None # XXX currently unused

        self.closed = False # True if connection is closed.

        self.name = "conn_%s" % hex(id(self))

    def connectionMade(self):
        """
        Callback for when a connection is successfully established.

        Find the connection's direction in the circuit, and register
        it in our circuit.
        """

        # Initialize the buffer for this connection:
        self.buffer = ''

        # Find the connection's direction and register it in the circuit.
        if self.mode == 'client' and not self.circuit.upstream:
            log.info("%s: connectionMade (client): " \
                     "Setting it as upstream on our circuit." % self.name)

            self.circuit.setUpstreamConnection(self)
            self.direction = 'upstream'
        elif self.mode == 'client':
            log.info("%s: connectionMade (client): " \
                     "Setting it as downstream on our circuit." % self.name)

            self.circuit.setDownstreamConnection(self)
            self.direction = 'downstream'
        elif self.mode == 'server' and not self.circuit.downstream:
            log.info("%s: connectionMade (server): " \
                     "Setting it as downstream on our circuit." % self.name)

            self.circuit.setDownstreamConnection(self)
            self.direction = 'downstream'
        elif self.mode == 'server':
            log.info("%s: connectionMade (server): " \
                     "Setting it as upstream on our circuit." % self.name)

            self.circuit.setUpstreamConnection(self)
            self.direction = 'upstream'

    def connectionLost(self, reason):
        log.info("%s: Connection was lost (%s)." % (self.name, reason.getErrorMessage()))
        self.circuit.close()

    def connectionFailed(self, reason):
        log.info("%s: Connection failed to connect (%s)." % (self.name, reason.getErrorMessage()))
        self.circuit.close()

    def dataReceived(self, data):
        """
        We received some data from the network. See if we have a
        complete circuit, and pass the data to it they get proxied.

        XXX: Can also be called with empty 'data' because of
        Circuit.setDownstreamConnection(). Document or split function.
        """
        if (not self.buffer) and (not data):
            log.info("%s: dataReceived called without a reason.", self.name)
            return

        log.debug("%s: Received %d bytes (and %d cached):\n%s" \
                  % (self.name, len(data), len(self.buffer), str(data)))

        # Circuit is not fully connected yet, cache what we got.
        if not self.circuit.circuitIsReady():
            log.debug("%s: Caching them %d bytes." % (self.name, len(data)))
            self.buffer += data
            return

        # Send received and buffered data to the circuit. Buffer the
        # data that the transport could not use.
        self.buffer = self.circuit.dataReceived(self.buffer + data, self)

    def write(self, buf):
        """
        Write 'buf' to the underlying transport.
        """
        log.debug("%s: Writing %d bytes." % (self.name, len(buf)))

        self.transport.write(buf)

    def close(self):
        """
        Close the connection.
        """
        if self.closed: return # NOP if already closed

        log.debug("%s: Closing connection." % self.name)

        self.transport.loseConnection()
        self.closed = True

class StaticDestinationClientFactory(Factory):
    """
    Created when our listener receives a client connection. Makes the
    connection that connects to the other end of the circuit.
    """

    def __init__(self, circuit, mode):
        self.circuit = circuit
        self.mode = mode

        self.name = "fact_c_%s" % hex(id(self))

    def buildProtocol(self, addr):
        return StaticDestinationProtocol(self.circuit, self.mode)

    def startedConnecting(self, connector):
        log.debug("%s: Client factory started connecting." % self.name)

    def clientConnectionLost(self, connector, reason):
        pass # connectionLost event is handled on the Protocol.

    def clientConnectionFailed(self, connector, reason):
        pass # connectionFailed event is handled on the Protocol.

class StaticDestinationServerFactory(Factory):
    """
    Represents a listener. Upon receiving a connection, it creates a
    circuit and tries to establish the other side of the circuit. It
    then listens for data to obfuscate and proxy.

    Attributes:

    remote_host: The IP/DNS information of the host on the other side
                 of the circuit.
    remote_port: The TCP port fo the host on the other side of the circuit.
    mode: 'server' or 'client'
    transport: the pluggable transport we should use to
               obfuscate traffic on this connection.
    """

    def __init__(self, remote_addrport, mode, transport):
        self.remote_host = remote_addrport[0]
        self.remote_port = int(remote_addrport[1])
        self.mode = mode
        self.transport = transport

        self.name = "fact_s_%s" % hex(id(self))

        assert(self.mode == 'client' or self.mode == 'server')

    def startFactory(self):
        log.info("%s: Starting up static destination server factory." % self.name)

    def buildProtocol(self, addr):
        log.info("%s: New connection." % self.name)

        circuit = Circuit(self.transport)

        # XXX instantiates a new factory for each client
        clientFactory = StaticDestinationClientFactory(circuit, self.mode)
        reactor.connectTCP(self.remote_host, self.remote_port, clientFactory)

        return StaticDestinationProtocol(circuit, self.mode)

