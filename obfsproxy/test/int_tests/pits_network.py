from twisted.internet.protocol import Protocol, Factory, ClientFactory
from twisted.internet import reactor, error, address, tcp

import logging

class GenericProtocol(Protocol):
    """
    Generic PITS connection. Contains useful methods and attributes.
    """
    def __init__(self, identifier, direction, transcript, conn_handler):
        self.identifier = identifier
        self.direction = direction
        self.transcript = transcript
        self.conn_handler = conn_handler

        self.closed = False

        self.conn_handler.register_conn(self, self.identifier, self.direction)

        # If it's inbound, note the connection establishment to the transcript.
        if self.direction == 'inbound':
            self.transcript.write('! %s' % self.identifier)
        logging.debug("Registered '%s' connection with identifier %s" % (direction, identifier))

    def connectionLost(self, reason):
        logging.debug("%s: Connection was lost (%s)." % (self.name, reason.getErrorMessage()))

        # If it's inbound, note the connection fail to the transcript.
        if self.direction == 'inbound':
            self.transcript.write('* %s' % self.identifier)

        self.close()

    def connectionFailed(self, reason):
        logging.warning("%s: Connection failed to connect (%s)." % (self.name, reason.getErrorMessage()))
        # XXX Note connection fail to transcript?
        self.close()

    def dataReceived(self, data):
        logging.debug("'%s' connection '%s' received %s" % (self.direction, self.identifier, repr(data)))

        # Note data to the transcript.
        symbol = '>' if self.direction == 'inbound' else '<'
        self.transcript.write('%s %s %s' % (symbol, self.identifier, data.encode("string_escape")))

    def write(self, buf):
        """
        Write 'buf' to the underlying transport.
        """
        logging.debug("Connection '%s' writing %s" % (self.identifier, repr(buf)))
        self.transport.write(buf)

    def close(self):
        """
        Close the connection.
        """
        if self.closed: return # NOP if already closed

        logging.debug("%s: Closing connection." % self.name)

        self.transport.loseConnection()

        self.conn_handler.unregister_conn(self.identifier, self.direction)

        self.closed = True

class OutboundConnection(GenericProtocol):
    def __init__(self, identifier, transcript, conn_handler):
        self.name = "out_%s_%s" % (identifier, hex(id(self)))
        GenericProtocol.__init__(self, identifier, 'outbound', transcript, conn_handler)

class InboundConnection(GenericProtocol):
    def __init__(self, identifier, transcript, conn_handler):
        self.name = "in_%s_%s" % (identifier, hex(id(self)))
        GenericProtocol.__init__(self, identifier, 'inbound', transcript, conn_handler)

class PITSOutboundFactory(Factory):
    """
    Outbound PITS factory.
    """
    def __init__(self, identifier, transcript, conn_handler):
        self.transcript = transcript
        self.conn_handler = conn_handler

        self.identifier = identifier
        self.name = "out_factory_%s" % hex(id(self))

    def buildProtocol(self, addr):
        # New outbound connection.
        return OutboundConnection(self.identifier, self.transcript, self.conn_handler)

    def startFactory(self):
        logging.debug("%s: Started up PITS outbound listener." % self.name)

    def stopFactory(self):
        logging.debug("%s: Shutting down PITS outbound listener." % self.name)

    def startedConnecting(self, connector):
        logging.debug("%s: Client factory started connecting." % self.name)

    def clientConnectionLost(self, connector, reason):
        logging.debug("%s: Connection lost (%s)." % (self.name, reason.getErrorMessage()))

    def clientConnectionFailed(self, connector, reason):
        logging.debug("%s: Connection failed (%s)." % (self.name, reason.getErrorMessage()))


class PITSInboundFactory(Factory):
    """
    Inbound PITS factory
    """
    def __init__(self, transcript, conn_handler):
        self.transcript = transcript
        self.conn_handler = conn_handler

        self.name = "in_factory_%s" % hex(id(self))

        # List with all the identifiers observed while parsing the
        # test case file so far.
        self.identifiers_seen = []
        # The number of identifiers used so far to name incoming
        # connections. Normally it should be smaller than the length
        # of 'identifiers_seen'.
        self.identifiers_used_n = 0

    def buildProtocol(self, addr):
        # New inbound connection.
        identifier = self._get_identifier_for_new_conn()
        return InboundConnection(identifier, self.transcript, self.conn_handler)

    def register_new_identifier(self, identifier):
        """Register new connection identifier."""

        if identifier in self.identifiers_seen:
            # The identifier was already in our list. Broken test case
            # or broken PITS.
            logging.warning("Tried to register identifier '%s' more than once (list: %s)."
                            "Maybe your test case is broken, or this could be a bug." %
                            (identifier, self.identifiers_seen))
            return

        self.identifiers_seen.append(identifier)

    def _get_identifier_for_new_conn(self):
        """
        We got a new incoming connection. Find the next identifier
        that we should use, and return it.
        """
        # BUG len(identifiers_seen) == 0 , identifiers_used == 0
        # NORMAL len(identifiers_seen) == 1, identifiers_used == 0
        # BUG len(identifiers_seen) == 2, identifiers_used == 3
        if (self.identifiers_used_n >= len(self.identifiers_seen)):
            logging.warning("Not enough identifiers for new connection (%d, %s)" %
                            (self.identifiers_used_n, str(self.identifiers_seen)))
            assert(False)

        identifier = self.identifiers_seen[self.identifiers_used_n]
        self.identifiers_used_n += 1

        return identifier


    def startFactory(self):
        logging.debug("%s: Started up PITS inbound listener." % self.name)

    def stopFactory(self):
        logging.debug("%s: Shutting down PITS inbound listener." % self.name)
        # XXX here we should close all existiing connections
