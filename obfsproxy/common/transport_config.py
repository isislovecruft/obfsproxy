# -*- coding: utf-8 -*-

"""
Provides a class which represents a pluggable transport's configuration.
"""

class TransportConfig( object ):

    """
    This class embeds configuration options for pluggable transport modules.

    The options are set by obfsproxy and then passed to the transport's class
    constructor.  The pluggable transport might want to use these options but
    does not have to.  An example of such an option is the state location which
    can be used by the pluggable transport to store persistent information.
    """

    def __init__( self ):
        """
        Initialise a `TransportConfig' object.
        """

        self.stateLocation = None

    def setStateLocation( self, stateLocation ):
        """
        Set the given `stateLocation'.
        """

        self.stateLocation = stateLocation

    def getStateLocation( self ):
        """
        Return the stored `stateLocation'.
        """

        return self.stateLocation

    def __str__( self ):
        """
        Return a string representation of the `TransportConfig' instance.
        """

        return str(vars(self))
