import logging

"""
Code that keeps track of the connections of PITS.
"""

def remove_key(d, key):
    """
    Return a dictionary identical to 'd' but with 'key' (and its
    value) removed.
    """
    r = dict(d)
    del r[key]
    return r

class PITSConnectionHandler(object):
    """
    Responsible for managing PITS connections.

    Attributes:
    'active_outbound_conns', is a dictionary mapping outbound connection identifiers with their objects.
    'active_inbound_conns', is a dictionary mapping inbound connection identifiers with their objects.
    """

    def __init__(self):
        # { "id1" : <OutboundConnection #1>, "id2": <OutboundConnection #2> }
        self.active_outbound_conns = {}

        # { "id1" : <InboundConnection #1>, "id2": <InboundConnection #2> }
        self.active_inbound_conns = {}

    def register_conn(self, conn, identifier, direction):
        """
        Register connection 'conn' with 'identifier'. 'direction' is
        either "inbound" or "outbound".
        """

        if direction == 'inbound':
            self.active_inbound_conns[identifier] = conn
            logging.debug("active_inbound_conns: %s" % str(self.active_inbound_conns))
        elif direction == 'outbound':
            self.active_outbound_conns[identifier] = conn
            logging.debug("active_outbound_conns: %s" % str(self.active_outbound_conns))

    def unregister_conn(self, identifier, direction):
        """
        Unregister connection 'conn' with 'identifier'. 'direction' is
        either "inbound" or "outbound".
        """

        if direction == 'inbound':
            self.active_inbound_conns = remove_key(self.active_inbound_conns, identifier)
            logging.debug("active_inbound_conns: %s" % str(self.active_inbound_conns))
        elif direction == 'outbound':
            self.active_outbound_conns = remove_key(self.active_outbound_conns, identifier)
            logging.debug("active_outbound_conns: %s" % str(self.active_outbound_conns))

    def find_conn(self, identifier, direction):
        """
        Find connection with 'identifier'. 'direction' is either
        "inbound" or "outbound".

        Raises NoSuchConn.
        """

        conn = None

        try:
            if direction == 'inbound':
                conn = self.active_inbound_conns[identifier]
            elif direction == 'outbound':
                conn = self.active_outbound_conns[identifier]
        except KeyError:
            logging.warning("find_conn: Could not find '%s' connection with identifier '%s'" %
                            (direction, identifier))
            raise NoSuchConn()

        logging.debug("Found '%s' conn with identifier '%s': '%s'" % (direction, identifier, conn))
        return conn

    def send_data_through_conn(self, identifier, direction, data):
        """
        Send 'data' through connection with 'identifier'.
        """

        try:
            conn = self.find_conn(identifier, direction)
        except KeyError:
            logging.warning("send_data_through_conn: Could not find '%s' connection "
                            "with identifier '%s'" % (direction, identifier))
            raise NoSuchConn()

        conn.write(data)

    def close_conn(self, identifier, direction):
        """
        Send EOF through connection with 'identifier'.
        """

        try:
            conn = self.find_conn(identifier, direction)
        except KeyError:
            logging.warning("close_conn: Could not find '%s' connection "
                            "with identifier '%s'" % (direction, identifier))
            raise NoSuchConn()

        conn.close()

class NoSuchConn(Exception): pass
