#!/usr/bin/python

import sys
import logging
import time
import socket
import collections

from twisted.internet import task, reactor, defer

import pits_network as network
import pits_connections as conns
import obfsproxy_tester
import pits_transcript as transcript

def usage():
    print "PITS usage:\n\tpits.py test_case.pits"

CLIENT_OBFSPORT = 42000 # XXX maybe randomize?
SERVER_OBFSPORT = 62000

class PITS(object):
    """
    The PITS system. It executes the commands written in test case
    files.

    Attributes:
    'transcript', is the PITS transcript. It's being written while
    the tests are running.

    'inbound_listener', the inbound PITS listener.

    'client_obfs' and 'server_obfs', the client and server obfpsroxy processes.
    """

    def __init__(self):
        # Set up the transcript
        self.transcript = transcript.Transcript()

        # Set up connection handler
        self.conn_handler = conns.PITSConnectionHandler()

        # Set up our fake network:
        # <PITS OUTBOUND CONNECTION> -> CLIENT_OBFSPORT -> SERVER_OBFSPRORT -> <PITS inbound listener>

        # Set up PITS inbound listener
        self.inbound_factory = network.PITSInboundFactory(self.transcript, self.conn_handler)
        self.inbound_listener = reactor.listenTCP(0, self.inbound_factory, interface='localhost')

        self.client_obfs = None
        self.server_obfs = None

        logging.debug("PITS initialized.")

    def get_pits_inbound_address(self):
        """Return the address of the PITS inbound listener."""
        return self.inbound_listener.getHost()

    def launch_obfsproxies(self, obfs_client_args, obfs_server_args):
        """Launch client and server obfsproxies with the given cli arguments."""
        # Set up client Obfsproxy.
        self.client_obfs = obfsproxy_tester.Obfsproxy(*obfs_client_args)

        # Set up server Obfsproxy.
        self.server_obfs = obfsproxy_tester.Obfsproxy(*obfs_server_args)

        time.sleep(1)

    def pause(self, tokens):
        """Read a parse command."""
        if len(tokens) > 1:
            raise InvalidCommand("Too big pause line.")

        if not tokens[0].isdigit():
            raise InvalidCommand("Invalid pause argument (%s)." % tokens[0])

        time.sleep(int(tokens[0]))

    def init_conn(self, tokens):
        """Read a connection establishment command."""
        if len(tokens) > 1:
            raise InvalidCommand("Too big init connection line.")

        # Before firing up the connetion, register its identifier to
        # the PITS subsystem.
        self.inbound_factory.register_new_identifier(tokens[0])

        # Create outbound socket. tokens[0] is its identifier.
        factory = network.PITSOutboundFactory(tokens[0], self.transcript, self.conn_handler)
        reactor.connectTCP('127.0.0.1', CLIENT_OBFSPORT, factory)

    def transmit(self, tokens, direction):
        """Read a transmit command."""
        if len(tokens) < 2:
            raise InvalidCommand("Too small transmit line.")

        identifier = tokens[0]
        data = " ".join(tokens[1:]) # concatenate rest of the line
        data = data.decode('string_escape') # unescape string

        try:
            self.conn_handler.send_data_through_conn(identifier, direction, data)
        except conns.NoSuchConn, err:
            logging.warning("Wanted to send some data, but I can't find '%s' connection with id '%s'." % \
                                (direction, identifier))
            # XXX note it to transcript

        logging.debug("Sending '%s' from '%s' socket '%s'." % (data, direction, identifier))

    def eof(self, tokens, direction):
        """Read a transmit EOF command."""
        if len(tokens) > 1:
            raise InvalidCommand("Too big EOF line.")

        identifier = tokens[0]

        try:
            self.conn_handler.close_conn(identifier, direction)
        except conns.NoSuchConn, err:
            logging.warning("Wanted to EOF, but I can't find '%s' connection with id '%s'." % \
                                (direction, identifier))
            # XXX note it to transcript

        logging.debug("Sending EOF from '%s' socket '%s'." % (identifier, direction))

    def do_command(self, line):
        """
        Parse command from 'line'.

        Throws InvalidCommand.
        """
        logging.debug("Parsing %s" % repr(line))

        line = line.rstrip()

        if line == '': # Ignore blank lines
            return

        tokens = line.split(" ")

        if len(tokens) < 2:
            raise InvalidCommand("Too few tokens: '%s'." % line)

        if tokens[0] == 'P':
            self.pause(tokens[1:])
        elif tokens[0] == '!':
            self.init_conn(tokens[1:])
        elif tokens[0] == '>':
            self.transmit(tokens[1:], 'outbound')
        elif tokens[0] == '<':
            self.transmit(tokens[1:], 'inbound')
        elif tokens[0] == '*':
            self.eof(tokens[1:], 'inbound')
        elif tokens[0] == '#': # comment
            pass
        else:
            logging.warning("Unknown token in line: '%s'" % line)

    def cleanup(self):
        logging.debug("Cleanup.")
        self.inbound_listener.stopListening()
        self.client_obfs.kill()
        self.server_obfs.kill()

class TestReader(object):
    """
    Read and execute a test case from a file.

    Attributes:
    'script', is the text of the test case file.
    'test_case_line', is a generator that yields the next line of the test case file.
    'pits', is the PITS system responsible for this test case.
    'assertTrue', is a function pointer to a unittest.assertTrue
                  function that should be used to validate this test.
    """
    def __init__(self, test_assertTrue_func, fname):
        self.assertTrue = test_assertTrue_func

        self.script = open(fname).read()
        self.test_case_line = self.test_case_line_gen()

        self.pits = PITS()

    def test_case_line_gen(self):
        """Yield the next line of the test case file."""
        for line in self.script.split('\n'):
            yield line

    def do_test(self, obfs_client_args, obfs_server_args):
        """
        Start a test case with obfsproxies with the given arguments.
        """

        # Launch the obfsproxies
        self.pits.launch_obfsproxies(obfs_client_args, obfs_server_args)

        # We call _do_command() till we read the whole test case
        # file. After we read the file, we call
        # transcript.test_was_success() to verify the test run.
        d = task.deferLater(reactor, 0.2, self._do_command)
        return d

    def _do_command(self):
        """
        Read and execute another command from the test case file.
        If the test case file is over, verify that the test was succesful. 
        """

        try:
            line = self.test_case_line.next()
        except StopIteration: # Test case is over.
            return self.assertTrue(self.pits.transcript.test_was_success(self.script))

        time.sleep(0.3)

        self.pits.do_command(line)

        # 0.4 seconds should be enough time for the network operations to complete,
        # so that we can move to the next command.
        d = task.deferLater(reactor, 0.4, self._do_command)
        return d

    def cleanup(self):
        self.pits.cleanup()

class InvalidCommand(Exception): pass

