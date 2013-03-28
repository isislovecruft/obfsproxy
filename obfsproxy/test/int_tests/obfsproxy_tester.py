#!/usr/bin/python

from twisted.internet import reactor
from twisted.internet import protocol

import os
import logging
import subprocess
import threading

obfsproxy_env = {}
obfsproxy_env.update(os.environ)

class ObfsproxyProcess(protocol.ProcessProtocol):
    """
    Represents the behavior of an obfsproxy process.
    """
    def __init__(self):
        self.stdout_data = ''
        self.stderr_data = ''

        self.name = 'obfs_%s' % hex(id(self))

    def connectionMade(self):
        pass

    def outReceived(self, data):
        """Got data in stdout."""
        logging.debug('%s: outReceived got %d bytes of data.' % (self.name, len(data)))
        self.stdout_data += data

    def errReceived(self, data):
        """Got data in stderr."""
        logging.debug('%s: errReceived got %d bytes of data.' % (self.name, len(data)))
        self.stderr_data += data

    def inConnectionLost(self):
        """stdin closed."""
        logging.debug('%s: stdin closed' % self.name)

    def outConnectionLost(self):
        """stdout closed."""
        logging.debug('%s: outConnectionLost, stdout closed!' % self.name)
        # XXX Fail the test if stdout is not clean.
        if self.stdout_data != '':
            logging.warning('%s: stdout is not clean: %s' % (self.name, self.stdout_data))

    def errConnectionLost(self):
        """stderr closed."""
        logging.debug('%s: errConnectionLost, stderr closed!' % self.name)

    def processExited(self, reason):
        """Process exited."""
        logging.debug('%s: processExited, status %s' % (self.name, str(reason.value.exitCode)))

    def processEnded(self, reason):
        """Process ended."""
        logging.debug('%s: processEnded, status %s' % (self.name, str(reason.value.exitCode)))

    def kill(self):
        """Kill the process."""
        logging.debug('%s: killing' % self.name)
        self.transport.signalProcess('KILL')
        self.transport.loseConnection()

class Obfsproxy(object):
    def __init__(self, *args, **kwargs):
        # Fix up our argv
        argv = []
        argv.extend(('python', '../../../../bin/obfsproxy', '--log-min-severity=warning'))

        # Extend hardcoded argv with user-specified options.
        if len(args) == 1 and (isinstance(args[0], list) or
                               isinstance(args[0], tuple)):
            argv.extend(args[0])
        else:
            argv.extend(args)

        # Launch obfsproxy
        self.obfs_process = ObfsproxyProcess()
        reactor.spawnProcess(self.obfs_process, 'python', args=argv,
                             env=obfsproxy_env)

        logging.debug('spawnProcess with %s' % str(argv))

    def kill(self):
        """Kill the obfsproxy process."""
        self.obfs_process.kill()
