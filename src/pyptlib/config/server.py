import os

from pyptlib.config.config import Config

"""
Configuration for a Pluggable Transport server.
"""

__docformat__ = 'restructuredtext'

class ServerConfig(Config):
  extendedServerPort=None # TOR_PT_EXTENDED_SERVER_PORT
  ORPort=None             # TOR_PT_ORPORT
  serverBindAddr={}       # TOR_PT_SERVER_BINADDR
  
  #Public methods
  
  def __init__(self): # throws EnvError
    Config.__init__(self)
    
    self.extendedServerPort=self.get('TOR_PT_EXTENDED_SERVER_PORT')
    self.ORPort=self.get('TOR_PT_ORPORT')
    
    binds=self.get('TOR_PT_SERVER_BINDADDR').split(',')
    for bind in binds:
      key,value=bind.split('-')
      self.serverBindAddr[key]=value
    
    self.transports=self.get('TOR_PT_SERVER_TRANSPORTS').split(',')
    if '*' in self.transports:
      self.allTransportsEnabled=True
      self.transports.remove('*')      
    
  # Returns a tuple (str,int) representing the address of the Tor server port as reported by Tor
  def getExtendedServerPort(self):
    return self.extendedServerPort
    
  # Returns a tuple (str,int) representing the address of the Tor OR port as reported by Tor
  def getORPort(self):
    return self.ORPort
    
  # Returns a dict {str: (str,int)} representing the addresses for each transport as reported by Tor
  def getServerBindAddresses(self):
    return self.serverBindAddr
    
  # Returns a list of strings representing the server transports reported by Tor. If present, '*' is stripped from this list and used to set allTransportsEnabled to True.
  def getServerTransports(self):
    return self.transports
    
  # Write a message to stdout specifying a supported transport
  # Takes: str, (str, int), MethodOptions
  def writeMethod(self, name, address, options): # SMETHOD
    if options:
      print('SMETHOD %s %s:%s %s' % (name, address[0], address[1], options))
    else:
      print('SMETHOD %s %s:%s' % (name, address[0], address[1]))
    
  # Write a message to stdout specifying that an error occurred setting up the specified method
  # Takes: str, str
  def writeMethodError(self, name, message): # SMETHOD-ERROR
    print('SMETHOD-ERROR %s %s' % (name, message))
    
  # Write a message to stdout specifying that the list of supported transports has ended
  def writeMethodEnd(self): # SMETHODS DONE
    print('SMETHODS DONE')

class MethodOptions:
  forward=False         # FORWARD
  args={}               # ARGS
  declare={}            # DECLARE
  useExtendedPort=False # USE-EXTENDED-PORT

  #Public methods
  
  def __init__(self):
    pass

  # Sets forward to True    
  def setForward(self):
    self.forward=True
  
  # Adds a key-value pair to args
  def addArg(self, key, value):
    self.args[key]=value

  # Adds a key-value pair to declare    
  def addDeclare(self, key, value):
    self.declare[key]=value
    
  # Sets useExtendedPort to True
  def setUserExtendedPort(self):
    self.useExtendedPort=True

  def __str__(self):
    options=[]
    if self.forward:
      options.append('FORWARD:1')
    if len(self.args)>0:
      argstr='ARGS:'
      for key in self.args:
        value=self.args[key]
        argstr=argstr+key+'='+value+','
      argstr=argstr[:-1] # Remove trailing comma
      options.append(argstr)
    if len(self.declare)>0:
      decs='DECLARE:'
      for key in self.declare:
        value=self.declare[key]
        decs=decs+key+'='+value+','
      decs=decs[:-1] # Remove trailing comma      
      options.append(decs)
    if self.useExtendedPort:
      options.append('USE-EXTENDED-PORT:1')

    return ' '.join(options)
