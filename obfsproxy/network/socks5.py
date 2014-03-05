from twisted.internet import reactor, protocol, error
from twisted.python import log

from operator import methodcaller
import socket
import struct

"""
SOCKS5 Server:

This is a SOCKS5 server.  There are many others like it but this one is mine.
It is compliant with RFC 1928 and RFC 1929, with the following limitations:

 * GSSAPI Autentication is not supported
 * BIND/UDP_ASSOCIATE are not implemented, and will return a CommandNotSupported
   SOCKS5 error, and close the connection.
"""

#
# SOCKS5 Constants
#
_SOCKS_VERSION = 0x05
_SOCKS_AUTH_NO_AUTHENTICATION_REQUIRED = 0x00
_SOCKS_AUTH_GSSAPI = 0x01
_SOCKS_AUTH_USERNAME_PASSWORD = 0x02
_SOCKS_AUTH_NO_ACCEPTABLE_METHODS = 0xFF
_SOCKS_CMD_CONNECT = 0x01
_SOCKS_CMD_BIND = 0x02
_SOCKS_CMD_UDP_ASSOCIATE = 0x03
_SOCKS_ATYP_IP_V4 = 0x01
_SOCKS_ATYP_DOMAINNAME = 0x03
_SOCKS_ATYP_IP_V6 = 0x04
_SOCKS_RSV = 0x00
_SOCKS_RFC1929_VER = 0x01
_SOCKS_RFC1929_SUCCESS = 0x00
_SOCKS_RFC1929_FAIL = 0x01

class SOCKSv5Reply(object):
    """
    SOCKSv5 reply codes
    """

    __slots__ = ['Succeded', 'GeneralFailure', 'ConnectionNotAllowed',
                 'NetworkUnreachable', 'HostUnreachable', 'ConnectionRefused',
                 'TTLExpired', 'CommandNotSupported', 'AddressTypeNotSupported']

    Succeeded = 0x00
    GeneralFailure = 0x01
    ConnectionNotAllowed = 0x02
    NetworkUnreachable = 0x03
    HostUnreachable = 0x04
    ConnectionRefused = 0x05
    TTLExpired = 0x06
    CommandNotSupported = 0x07
    AddressTypeNotSupported = 0x08


class SOCKSv5Outgoing(protocol.Protocol):

    socks = None

    def __init__(self, socks):
        self.socks = socks

    def connectionMade(self):
        self.socks.otherConn = self
        self.socks.send_reply(SOCKSv5Reply.Succeeded)

    def connectionLost(self, reason):
        self.socks.transport.loseConnection()

    def dataReceived(self, data):
        self.socks.log(self, data)
        self.transport.write(data)

    def write(self, data):
        self.socks.log(self, data)
        self.transport.write(data)


class SOCKSv5Protocol(protocol.Protocol):
    """
    Represents an upstream connection from a SOCKS client to our SOCKS server.
    """

    buf = None
    state = None
    authMethod = None
    otherConn = None

    # State values
    ST_INIT = 0
    ST_READ_METHODS = 1
    ST_AUTHENTICATING = 2
    ST_READ_REQUEST = 3
    ST_CONNECTING = 4
    ST_ESTABLISHED = 5

    # Authentication methods
    ACCEPTABLE_AUTH_METHODS = [
        _SOCKS_AUTH_USERNAME_PASSWORD,
        _SOCKS_AUTH_NO_AUTHENTICATION_REQUIRED
    ]
    AUTH_METHOD_VTABLE = {
        _SOCKS_AUTH_USERNAME_PASSWORD: methodcaller('processRfc1929Request'),
        _SOCKS_AUTH_NO_AUTHENTICATION_REQUIRED: methodcaller('processNoAuthRequired')
    }

    # Commands
    ACCEPTABLE_CMDS = [
        _SOCKS_CMD_CONNECT,
        _SOCKS_CMD_BIND,
        _SOCKS_CMD_UDP_ASSOCIATE
    ]

    def __init__(self, logging=None, reactor=reactor):
        self.logging = logging
        self.reactor = reactor
        self.state = self.ST_INIT

    def connectionMade(self):
        self.buf = _ByteBuffer()
        self.otherConn = None
        self.state = self.ST_READ_METHODS
        self.authMethod = _SOCKS_AUTH_NO_ACCEPTABLE_METHODS

    def connectionLost(self, reason):
        if self.otherConn:
            self.otherConn.transport.loseConnection()

    def dataReceived(self, data):
        if self.state == self.ST_ESTABLISHED:
            self.processEstablishedData(data)
            return

        self.buf.add(data)
        if self.state == self.ST_READ_METHODS:
            self.processMethodSelect()
        elif self.state == self.ST_AUTHENTICATING:
            self.processAuthentication()
        elif self.state == self.ST_READ_REQUEST:
            self.processRequest()
        elif self.state == self.ST_CONNECTING:
            # This only happens when the client is busted
            log.msg("Client sent data before receiving response")
            self.transport.loseConnection()
        else:
            log.msg("Invalid state in SOCKS5 Server: '%d'" % self.state)
            self.transport.loseConnection()

    def processEstablishedData(self, data):
        assert self.otherConn
        self.otherConn.write(self.buf)

    def processMethodSelect(self):
        """
        Parse Version Identifier/Method Selection Message, and send a response
        """

        msg = self.buf.peek()
        if len(msg) < 2:
            return

        ver = msg.get_uint8()
        nmethods = msg.get_uint8()
        if ver != _SOCKS_VERSION:
            log.msg("Invalid SOCKS version: '%d'" % ver)
            self.transport.loseConnection()
            return
        if nmethods == 0:
            log.msg("No Authentication method(s) present")
            self.transport.loseConnection()
            return
        if len(msg) < nmethods:
            return

        # Select the best method
        methods = msg.get(nmethods)
        for method in self.ACCEPTABLE_AUTH_METHODS:
            if method in methods:
                self.authMethod = method
                break
        if self.authMethod == _SOCKS_AUTH_NO_ACCEPTABLE_METHODS:
            log.msg("No Acceptable Authentication Methods")
            self.authMethod = _SOCKS_AUTH_NO_ACCEPTABLE_METHODS

        # Ensure there is no trailing garbage
        if len(msg) > 0:
            log.msg("Peer sent trailing garbage after method select")
            self.transport.loseConnection()
            return
        self.buf.clear()

        # Send Method Selection Message
        msg = _ByteBuffer()
        msg.add_uint8(_SOCKS_VERSION)
        msg.add_uint8(self.authMethod)
        self.transport.write(str(msg))

        if self.authMethod == _SOCKS_AUTH_NO_ACCEPTABLE_METHODS:
            self.transport.loseConnection()
            return

        self.state = self.ST_AUTHENTICATING

    def processAuthentication(self):
        """
        Handle client data when authenticating
        """

        if self.authMethod in self.AUTH_METHOD_VTABLE:
            self.AUTH_METHOD_VTABLE[self.authMethod](self)
        else:
            # Should *NEVER* happen
            log.msg("Peer sent data when we failed to negotiate auth")
            self.buf.clear()
            self.transport.loseConnection()

    def processRfc1929Request(self):
        """
        Handle RFC1929 Username/Password authentication requests
        """

        msg = self.buf.peek()
        if len(msg) < 2:
            return

        # Parse VER, ULEN
        ver = msg.get_uint8()
        ulen = msg.get_uint8()
        if ver != _SOCKS_RFC1929_VER:
            log.msg("Invalid RFC1929 version: '%d'" % ver)
            self.sendRfc1929Reply(False)
            return
        if ulen == 0:
            log.msg("Username length is 0")
            self.sendRfc1929Reply(False)
            return

        # Process PLEN
        if len(msg) < ulen:
            return
        uname = msg.get(ulen)

        # Parse PLEN
        if len(msg) < 1:
            return
        plen = msg.get_uint8()
        if len(msg) < plen:
            return
        if plen == 0:
            log.msg("Password length is 0")
            self.sendRfc1929Reply(False)
            return
        passwd = msg.get(plen)

        # Ensure there is no trailing garbage
        if len(msg) > 0:
            log.msg("Peer sent trailing garbage after RFC1929 auth")
            self.transport.loseConnection()
            return
        self.buf.clear()

        if not self.processRfc1929Auth(str(uname), str(passwd)):
            self.sendRfc1929Reply(False)
        else:
            self.sendRfc1929Reply(True)

    def processRfc1929Auth(self, uname, passwd):
        """
        Handle the RFC1929 Username/Password received from the client
        """

        return False

    def sendRfc1929Reply(self, success):
        """
        Send a RFC1929 Username/Password Authentication response
        """

        msg = _ByteBuffer()
        msg.add_uint8(_SOCKS_RFC1929_VER)
        if success:
            msg.add_uint8(_SOCKS_RFC1929_SUCCESS)
            self.transport.write(str(msg))
            self.state = self.ST_READ_REQUEST
        else:
            msg.add_uint8(_SOCKS_RFC1929_FAIL)
            self.transport.write(str(msg))
            self.transport.loseConnection()

    def processNoAuthRequired(self):
        """
        Handle the RFC1928 No Authentication Required
        """

        self.state = self.ST_READ_REQUEST
        self.processRequest()

    def processRequest(self):
        """
        Parse the client request, and setup the TCP/IP connection
        """

        msg = self.buf.peek()
        if len(msg) < 4:
            return

        # Parse VER, CMD, RSV, ATYP
        ver = msg.get_uint8()
        cmd = msg.get_uint8()
        rsv = msg.get_uint8()
        atyp = msg.get_uint8()
        if ver != _SOCKS_VERSION:
            log.msg("Invalid SOCKS version: '%d'" % ver)
            self.sendReply(SOCKSv5Reply.GeneralFailure)
            return
        if cmd not in self.ACCEPTABLE_CMDS:
            log.msg("Invalid SOCKS command: '%d'" % cmd)
            self.sendReply(SOCKSv5Reply.CommandNotSupported)
            return
        if rsv != _SOCKS_RSV:
            log.msg("Invalid SOCKS RSV: '%d'" % rsv)
            self.sendReply(SOCKSv5Reply.GeneralFailure)
            return

        # Deal with the address
        addr = None
        if atyp == _SOCKS_ATYP_IP_V4:
            if len(msg) < 4:
                return
            addr = socket.inet_ntoa(str(msg.get(4)))
        elif atyp == _SOCKS_ATYP_IP_V6:
            if len(msg) < 16:
                return
            try:
                addr = socket.inet_ntop(socket.AF_INET6, str(msg.get(16)))
            except:
                log.msg("Failed to parse IPv6 address")
                self.sendReply(SOCKSv5Reply.AddressTypeNotSupported)
                return
        elif atyp == _SOCKS_ATYP_DOMAINNAME:
            if len(msg) < 1:
                return
            alen = msg.get_uint8()
            if alen == 0:
                log.msg("Domain name length is 0")
                self.sendReply(SOCKSv5Reply.GeneralFailure)
                return
            if len(msg) < alen:
                return
            addr = str(msg.get(alen))
        else:
            log.msg("Invalid SOCKS address type: '%d'" % atyp)
            self.sendReply(SOCKSv5Reply.AddressTypeNotSupported)
            return

        # Deal with the port
        if len(msg) < 2:
            return
        port = msg.get_uint16(True)

        # Ensure there is no trailing garbage
        if len(msg) > 0:
            log.msg("Peer sent trailing garbage after request")
            self.transport.loseConnection()
            return
        self.buf.clear()

        if cmd == _SOCKS_CMD_CONNECT:
            self.processCmdConnect(addr, port)
        elif cmd == _SOCKS_CMD_BIND:
            self.processCmdBind(addr, port)
        elif cmd == _SOCKS_CMD_UDP_ASSOCIATE:
            self.processCmdUdpAssociate(addr, port)
        else:
            # Should *NEVER* happen
            log.msg("Unimplemented command received")
            self.transport.loseConnection()

    def processCmdConnect(self, addr, port):
        """
        Open a TCP/IP connection to the peer
        """

        d = self.connectClass(addr, port, SOCKSv5Outgoing, self)
        d.addErrback(self.handleCmdConnectFailure)
        self.state = self.ST_CONNECTING

    def connectClass(self, addr, port, klass, *args):
        return protocol.ClientCreator(reactor, klass, *args).connectTCP(addr, port)

    def handleCmdConnectFailure(self, failure):
        log.err(failure, "Failed to connect to peer")

        # Map common twisted errors to SOCKS error codes
        if failure.type == error.NoRouteError:
            self.sendReply(SOCKSv5Reply.NetworkUnreachable)
        elif failure.type == error.ConnectionRefusedError:
            self.sendReply(SOCKSv5Reply.ConnectionRefused)
        elif failure.type == error.TCPTimedOutError or failure.type == error.TimeoutError:
            self.sendReply(SOCKSv5Reply.TTLExpired)
        elif failure.type == error.UnsupportedAddressFamily:
            self.sendReply(SOCKSv5Reply.AddressTypeNotSupported)
        else:
            self.sendReply(SOCKSv5Reply.GeneralFailure)

    def processCmdBind(self, addr, port):
        self.sendReply(SOCKSv5Reply.CommandNotSupported)

    def processCmdUdpAssociate(self, addr, port):
        self.sendReply(SOCKSv5Reply.CommandNotSupported)

    def sendReply(self, reply):
        """
        Send a reply to the request, and complete circuit setup
        """

        msg = _ByteBuffer()
        msg.add_uint8(_SOCKS_VERSION)
        msg.add_uint8(reply)
        msg.add_uint8(_SOCKS_RSV)
        if reply == SOCKSv5Reply.Succeeded:
            host = self.transport.getHost()
            port = host.port
            try:
                raw_addr = socket.inet_aton(host.host)
                msg.add_uint8(_SOCKS_ATYP_IP_V4)
                msg.add(raw_addr)
            except socket.error:
                try:
                    raw_addr = socket.inet_pton(socket.AF_INET6, host.host)
                    msg.add_uint8(_SOCKS_ATYP_IP_V6)
                    msg.add(raw_addr)
                except:
                    log.msg("Failed to parse bound address")
                    self.sendReply(SOCKSv5Reply.GeneralFailure)
                    return
            msg.add_uint16(port, True)
            self.transport.write(str(msg))

            self.state = self.ST_ESTABLISHED
        else:
            msg.add_uint8(_SOCKS_ATYP_IP_V4)
            msg.add_uint32(0, True)
            msg.add_uint16(0, True)
            self.transport.write(str(msg))
            self.transport.loseConnection()

    def log(self, proto, data):
        pass


class SOCKSv5Factory(protocol.Factory):
    """
    A SOCKSv5 Factory.
    """

    def __init__(self, log):
        self.logging = log

    def buildProtocol(self, addr):
        return SOCKSv5Protocol(self.logging, reactor)


class _ByteBuffer(bytearray):
    """
    A byte buffer, based on bytearray.  get_* always removes reads from the
    head (and is destructive), and add_* appends to the tail.
    """

    def add_uint8(self, val):
        self.extend(struct.pack("B", val))

    def get_uint8(self):
        return self.pop(0)

    def add_uint16(self, val, htons=False):
        if htons:
            self.extend(struct.pack("!H", val))
        else:
            self.extend(struct.pack("H", val))

    def get_uint16(self, ntohs=False):
        if ntohs:
            ret = struct.unpack("!H", self[0:2])[0]
        else:
            ret = struct.unpack("H", self[0:2])[0]
        del self[0:2]
        return ret

    def add_uint32(self, val, htonl=False):
        if htonl:
            self.extend(struct.pack("!I", val))
        else:
            self.extend(struct.pack("I", val))

    def add(self, val):
        self.extend(val)

    def get(self, len):
        ret = self[0:len]
        del self[0:len]
        return ret

    def peek(self):
        ret = _ByteBuffer()
        ret[:] = self
        return ret

    def clear(self):
        del self[0:]

    def __repr__(self):
        return self.decode('ISO-8859-1')
