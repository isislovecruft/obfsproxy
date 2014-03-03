from twisted.internet import reactor, protocol, error

import obfsproxy.common.log as logging
import obfsproxy.network.network as network
import obfsproxy.transports.base as base

import csv
import socket
import struct

log = logging.get_obfslogger()

"""
SOCKS5 Server:

This is a SOCKS5 server written specifically for Tor Pluggable Transports.  It
is compliant with RFC 1928 and RFC 1929 with the following exceptions.

 * GSSAPI Authentication is not and will not ever be supported.
 * The SOCKS5 CMDs BIND and UDP ASSOCIATE are not supported.
 * The SOCKS5 ATYP DOMAINNAME is not supported.  This is a intentional design
   choice.  While it would be trivial to support this, Pluggable Transports
   hitting up DNS is a DNS leak, and it is Tor's problem to pass acceptable
   addresses.
"""

#
# SOCKS Server States
#
_SOCKS_ST_READ_METHODS = 1
_SOCKS_ST_AUTHENTICATING = 2
_SOCKS_ST_READ_REQUEST = 3
_SOCKS_ST_CONNECTING = 4
_SOCKS_ST_ESTABLISHED = 5

#
# SOCKS5 Constants
#
_SOCKS_VERSION = 0x05
_SOCKS_AUTH_NO_AUTHENTICATION_REQUIRED = 0x00
#_SOCKS_AUTH_GSSAPI = 0x01
_SOCKS_AUTH_USERNAME_PASSWORD = 0x02
_SOCKS_AUTH_NO_ACCEPTABLE_METHODS = 0xFF
_SOCKS_CMD_CONNECT = 0x01
#_SOCKS_CMD_BIND = 0x02
#_SOCKS_CMD_UDP_ASSOCIATE = 0x03
_SOCKS_ATYP_IP_V4 = 0x01
#_SOCKS_ATYP_DOMAINNAME = 0x03
_SOCKS_ATYP_IP_V6 = 0x04
_SOCKS_RSV = 0x00
_SOCKS_REP_SUCCEDED = 0x00
_SOCKS_REP_GENERAL_FAILURE = 0x01
_SOCKS_REP_CONNECTION_NOT_ALLOWED = 0x02
_SOCKS_REP_NETWORK_UNREACHABLE = 0x03
_SOCKS_REP_HOST_UNREACHABLE = 0x04
_SOCKS_REP_CONNECTION_REFUSED = 0x05
_SOCKS_REP_TTL_EXPIRED = 0x06
_SOCKS_REP_COMMAND_NOT_SUPPORTED = 0x07
_SOCKS_REP_ADDRESS_TYPE_NOT_SUPPORTED = 0x08
_SOCKS_RFC1929_VER = 0x01
_SOCKS_RFC1929_SUCCESS = 0x00
_SOCKS_RFC1929_FAIL = 0x01

def _split_socks_args(args_str):
    """
    Given a string containing the SOCKS arguments (delimited by
    semicolons, and with semicolons and backslashes escaped), parse it
    and return a list of the unescaped SOCKS arguments.
    """
    return csv.reader([args_str], delimiter=';', escapechar='\\').next()

class SOCKSv5Outgoing(network.GenericProtocol):
    """
    Represents a downstream connection from our SOCKS server to a remote peer.

    Attributes:
    circuit: The curcuit object this connection belongs to.
    buffer: Buffer that holds data waiting to be processed.
    """

    name = None

    _socks = None

    def __init__(self, socks):
        self.name = "socks_down_%s" % hex(id(self))
        self._socks = socks

        network.GenericProtocol.__init__(self, socks.circuit)

    def connectionMade(self):
        self._socks._other_conn = self
        self._socks.setup_circuit()
        # XXX: The transport should do this after handshaking
        self._socks.send_reply(_SOCKS_REP_SUCCEDED)

    def dataReceived(self, data):
        log.debug("%s: Received %d bytes." % (self.name, len(data)))

        assert self.circuit.circuitIsReady()
        self.buffer.write(data)
        self.circuit.dataReceived(self.buffer, self)

class SOCKSv5Protocol(network.GenericProtocol):
    """
    Represents an upstream connection from a SOCKS client to our SOCKS server.

    Attributes:
    circuit: The curcuit object this connection belongs to.
    buffer: Buffer that holds data waiting to be processed.
    """

    name = None

    _state = None
    _auth_method = None
    _other_conn = None

    def __init__(self, circuit):
        self.name = "socks_up_%s" % hex(id(self))
        self._state = _SOCKS_ST_READ_METHODS

        network.GenericProtocol.__init__(self, circuit)

    def connectionLost(self, reason):
        network.GenericProtocol.connectionLost(self, reason)

    def dataReceived(self, data):
        log.debug("%s: Received %d bytes." % (self.name, len(data)))
        self.buffer.write(data)

        if self._state == _SOCKS_ST_READ_METHODS:
            self._process_method_select()
        elif self._state == _SOCKS_ST_AUTHENTICATING:
            self._process_authentication()
        elif self._state == _SOCKS_ST_READ_REQUEST:
            self._process_request()
        elif self._state == _SOCKS_ST_CONNECTING:
            # This is NEVER supposed to happen, we could be nice and buffer the
            # data, but people that fail to implement a SOCKS5 client deserve to
            # be laughed at.
            log.warning("%s: Client sent data when connecting" % self.name)
            self.transport.loseConnection()
        elif self._state == _SOCKS_ST_ESTABLISHED:
            assert self.circuit.circuitIsReady()
            self.circuit.dataReceived(self.buffer, self)
        else:
            log.warning("%s: Invalid state in SOCKS5 Server: '%d'" % (self.name, self._state))
            self.transport.loseConnection()

    def _process_method_select(self):
        """
        Parse Version Identifier/Method Selection Message, and send a response
        """

        msg = self.buffer.peek()
        if len(msg) < 2:
            return
        ver, nmethods = struct.unpack("BB", msg[0:2])
        if ver != _SOCKS_VERSION:
            log.warning("%s: Invalid SOCKS version: '%d'" % (self.name, ver))
            self.transport.loseConnection()
            return
        if nmethods == 0:
            log.warning("%s: No Authentication method present" % self.name)
            self.transport.loseConnection()
            return

        #
        # Ensure that the entire message is present, and find the "best"
        # authentication method.
        #
        # In a perfect world, the transport will specify that authentication
        # is required, but since tor will do the work for us, this will
        # suffice.
        #

        if len(msg) < 2 + nmethods:
            return
        methods = msg[2:2 + nmethods]
        if chr(_SOCKS_AUTH_USERNAME_PASSWORD) in methods:
            log.debug("%s: Username/Password Authentication" % self.name)
            self._auth_method = _SOCKS_AUTH_USERNAME_PASSWORD
        elif chr(_SOCKS_AUTH_NO_AUTHENTICATION_REQUIRED) in methods:
            log.debug("%s: No Authentication Required" % self.name)
            self._auth_method = _SOCKS_AUTH_NO_AUTHENTICATION_REQUIRED
        else:
            log.warning("%s: No Compatible Authentication method" % self.name)
            self._auth_method = _SOCKS_AUTH_NO_ACCEPTABLE_METHODS

        # Ensure there is no trailing garbage
        self.buffer.drain(2 + nmethods)
        if len(self.buffer) > 0:
            log.warning("%s: Peer sent trailing garbage after method select" % self.name)
            self.transport.loseConnection()
            return

        # Send Method Selection Message
        self.transport.write(struct.pack("BB", _SOCKS_VERSION, self._auth_method))
        if self._auth_method == _SOCKS_AUTH_NO_ACCEPTABLE_METHODS:
            self.transport.loseConnection()
            return

        self._state = _SOCKS_ST_AUTHENTICATING

    def _process_authentication(self):
        """
        Handle client data when authenticating
        """

        if self._auth_method == _SOCKS_AUTH_NO_AUTHENTICATION_REQUIRED:
            self._state = _SOCKS_ST_READ_REQUEST
            self._process_request()
        elif self._auth_method == _SOCKS_AUTH_USERNAME_PASSWORD:
            self._process_rfc1929_request()
        else:
            log.warning("%s: Peer sent data when we failed to negotiate auth" % (self.name))
            self.buffer.drain()
            self.transport.loseConnection()

    def _process_rfc1929_request(self):
        """
        Handle RFC1929 Username/Password authentication requests
        """

        msg = self.buffer.peek()
        if len(msg) < 2:
            return

        # Parse VER, ULEN
        ver, ulen = struct.unpack("BB", msg[0:2])
        if ver != _SOCKS_RFC1929_VER:
            log.warning("%s: Invalid RFC1929 version: '%d'" % (self.name, ver))
            self._send_rfc1929_reply(False)
            return
        if ulen == 0:
            log.warning("%s: Username length is 0" % self.name)
            self._send_rfc1929_reply(False)
            return
        if len(msg) < 2 + ulen:
            return
        uname = msg[2:2 + ulen]
        if len(msg) < 2 + ulen + 1:
            return
        plen = struct.unpack("B", msg[2 + ulen])[0]
        if len(msg) < 2 + ulen + 1 + plen:
            return
        if plen == 0:
            log.warning("%s: Password length is 0" % self.name)
            self._send_rfc1929_reply(False)
            return
        passwd = msg[2 + ulen + 1:2 + ulen + 1 + plen]

        #
        # Begin the pt-spec specific SOCKS auth braindamage:
        #

        args = uname
        if plen > 1 or ord(passwd[0]) != 0:
            args += passwd
        try:
            split_args = _split_socks_args(args)
        except csvError, err:
            log.warning("split_socks_args failed (%s)" % str(err))
            self._send_rfc1929_reply(False)
            return
        try:
            self.circuit.transport.handle_socks_args(split_args)
        except base.SOCKSArgsError:
            # Transports should log the issue themselves
            self._send_rfc1929_reply(False)
            return

        # Ensure there is no trailing garbage
        self.buffer.drain(2 + ulen + 1 + plen)
        if len(self.buffer) > 0:
            log.warning("%s: Peer sent trailing garbage after RFC1929 auth" % self.name)
            self.transport.loseConnection()
            return

        self._send_rfc1929_reply(True)

    def _send_rfc1929_reply(self, success):
        """
        Send a RFC1929 Username/Password Authentication response
        """

        if success == True:
            self.transport.write(struct.pack("BB", 1, _SOCKS_RFC1929_SUCCESS))
            self._state = _SOCKS_ST_READ_REQUEST
        else:
            self.transport.write(struct.pack("BB", 1, _SOCKS_RFC1929_FAIL))
            self.transport.loseConnection()

    def _process_request(self):
        """
        Parse the client request, and setup the TCP/IP connection
        """

        msg = self.buffer.peek()
        if len(msg) < 4:
            return

        ver, cmd, rsv, atyp = struct.unpack("BBBB", msg[0:4])
        if ver != _SOCKS_VERSION:
            log.warning("%s: Invalid SOCKS version: '%d'" % (self.name, ver))
            self.send_reply(_SOCKS_REP_GENERAL_FAILURE)
            return
        if cmd != _SOCKS_CMD_CONNECT:
            log.warning("%s: Invalid SOCKS command: '%d'" % (self.name, cmd))
            self.send_reply(_SOCKS_REP_COMMAND_NOT_SUPPORTED)
            return
        if rsv != _SOCKS_RSV:
            log.warning("%s: Invalid SOCKS RSV: '%d'" % (self.name, rsv))
            self.send_reply(_SOCKS_REP_GENERAL_FAILURE)
            return

        # Deal with the address
        addr = None
        if atyp == _SOCKS_ATYP_IP_V4:
            if len(msg) < 4 + 4 + 2:
                return
            addr = socket.inet_ntoa(msg[4:8])
            self.buffer.drain(4 + 4)
        elif atyp == _SOCKS_ATYP_IP_V6:
            if len(msg) < 4 + 16 + 2:
                return
            try:
                addr = socket.inet_ntop(socket.AF_INET6, msg[4:16])
            except:
                log.warning("%s: Failed to parse IPv6 address" % self.name)
                self.send_reply(_SOCKS_REP_ADDRESS_TYPE_NOT_SUPPORTED)
                return
            self.buffer.drain(4 + 16)
        else:
            log.warning("%s: Invalid SOCKS address type: '%d'" % (self.name, atyp))
            self.send_reply(_SOCKS_REP_ADDRESS_TYPE_NOT_SUPPORTED)
            return

        # Deal with the port
        port = struct.unpack("!H", self.buffer.read(2))[0]

        # Ensure there is no trailing garbage
        if len(self.buffer) > 0:
            log.warning("%s: Peer sent trailing garbage after request" % self.name)
            self.send_reply(_SOCKS_REP_GENERAL_FAILURE)
            return

        # Connect -> addr/port
        d = protocol.ClientCreator(reactor, SOCKSv5Outgoing, self).connectTCP(addr, port)
        d.addErrback(self._handle_connect_failure)

        self._state = _SOCKS_ST_CONNECTING

    def _handle_connect_failure(self, failure):
        log.warning("%s: Failed to connect to peer: %s" % (self.name, failure))

        # Map common twisted errors to SOCKS error codes
        if failure.type == error.NoRouteError:
            self.send_reply(_SOCKS_REP_NETWORK_UNREACHABLE)
        elif failure.type == error.ConnectionRefusedError:
            self.send_reply(_SOCKS_REP_CONNECTION_REFUSED)
        elif failure.type == error.TCPTimedOutError:
            self.send_reply(_SOCKS_REP_TTL_EXPIRED)
        elif failure.type == error.UnsupportedAddressFamily:
            self.send_reply(_SOCKS_REP_ADDRESS_TYPE_NOT_SUPPORTED)
        else:
            self.send_reply(_SOCKS_REP_GENERAL_FAILURE)

    def setup_circuit(self):
        assert self._other_conn
        self.circuit.setDownstreamConnection(self._other_conn)
        self.circuit.setUpstreamConnection(self)

    def send_reply(self, reply):
        """
        Send a reply to the request, and complete circuit setup
        """

        if reply == _SOCKS_REP_SUCCEDED:
            host = self.transport.getHost()
            port = host.port
            try:
                raw_addr = socket.inet_aton(host.host)
                self.transport.write(struct.pack("BBBB", _SOCKS_VERSION, reply, _SOCKS_RSV, _SOCKS_ATYP_IP_V4) + raw_addr + struct.pack("!H",port))
            except socket.error:
                try:
                    raw_addr = socket.inet_pton(socket.AF_INET6, host.host)
                    self.transport.write(struct.pack("BBBB", _SOCKS_VERSION, reply, _SOCKS_RSV, _SOCKS_ATYP_IP_V6) + raw_addr + struct.pack("!H",port))
                except:
                    log.warning("%s: Failed to parse bound address" % self.name)
                    self.send_reply(_SOCKS_REP_GENERAL_FAILURE)
                    return

            self._state = _SOCKS_ST_ESTABLISHED
        else:
            self.transport.write(struct.pack("!BBBBIH", _SOCKS_VERSION, reply, _SOCKS_RSV, _SOCKS_ATYP_IP_V4, 0, 0))
            self.transport.loseConnection()

class SOCKSv5Factory(protocol.Factory):
    """
    A SOCKSv5 Factory.
    """

    def __init__(self, transport_class, pt_config):
        # XXX self.logging = log
        self.transport_class = transport_class
        self.pt_config  = pt_config

        self.name = "socks_fact_%s" % hex(id(self))

    def startFactory(self):
        log.debug("%s: Starting up SOCKS server factory." % self.name)

    def buildProtocol(self, addr):
        log.debug("%s: New connection." % self.name)

        circuit = network.Circuit(self.transport_class())

        return SOCKSv5Protocol(circuit)
