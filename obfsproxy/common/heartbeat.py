"""heartbeat code"""

import datetime

import obfsproxy.common.log as log

class Heartbeat(object):
    """
    Represents obfsproxy's heartbeat.

    It keeps stats on a number of things that the obfsproxy operator
    might be interested in, and every now and then it reports them in
    the logs.
    """

    def __init__(self):
        self.n_unique_ips = 0
        self.n_connections = 0
        self.started = datetime.datetime.now()
        self.last_reset = self.started

    def register_ip(self, ip): # XXX NOP
        pass

    def register_connection(self):
        """Register a new connection."""

        self.n_connections += 1

    def reset_stats(self):
        """Reset stats."""

        self.n_connections = 0
        self.n_unique_ips = 0
        self.last_reset = datetime.datetime.now()

    def say_uptime(self):
        """Log uptime information."""

        now = datetime.datetime.now()
        delta = now - self.started

        if delta.days:
            log.info("Heartbeat: obfsproxy's uptime is %d day(s), %d hour(s) and %d minute(s)." % \
                         (delta.days, delta.seconds//3600, (delta.seconds//60)%60))
        else:
            log.info("Heartbeat: obfsproxy's uptime is %d hour(s) and %d minute(s)." % \
                         (delta.seconds//3600, (delta.seconds//60)%60))

    def say_stats(self):
        """Log connection stats."""

        now = datetime.datetime.now()
        reset_delta = now - self.last_reset

        log.info("Heartbeat: During the last %d hour(s) we saw %d connection(s)." % \
                     (reset_delta.seconds//3600 + reset_delta.days*24, self.n_connections))

        # Reset stats every 24 hours.
        if (reset_delta.days > 0):
            log.debug("Resetting heartbeat.")
            self.reset_stats()

    def talk(self):
        """Do a heartbeat."""

        self.say_uptime()
        self.say_stats()

# A heartbeat singleton.
heartbeat = Heartbeat()
