import os

from pyptlib.config.config import Config

"""
Configuration for a Pluggable Transport client.
"""

__docformat__ = 'restructuredtext'

class ClientConfig(Config):  
  #Public methods
  
  def __init__(self): # throws EnvError
    Config.__init__(self)
    
    self.transports=self.get('TOR_PT_CLIENT_TRANSPORTS').split(',')
    if '*' in self.transports:
      self.allTransportsEnabled=True
      self.transports.remove('*')      

  # Returns a list of strings representing the client transports reported by Tor. If present, '*' is stripped from this list and used to set allTransportsEnabled to True.
  def getClientTransports(self):
    return self.transports

  # Write a message to stdout specifying a supported transport
  # Takes: str, int, (str, int), [str], [str]
  def writeMethod(self, name, socksVersion, address, args, optArgs): # CMETHOD
    methodLine='CMETHOD %s socks%s %s:%s' % (name, socksVersion, address[0], address[1])
    if args and len(args)>0:
      methodLine=methodLine+' ARGS='+args.join(',')
    if optArgs and len(optArgs)>0:
      methodLine=methodLine+' OPT-ARGS='+args.join(',')
    print(methodLine) 
   
  # Write a message to stdout specifying that an error occurred setting up the specified method
  # Takes: str, str
  def writeMethodError(self, name, message): # CMETHOD-ERROR
    print('CMETHOD-ERROR %s %s' % (name, message))
    
  # Write a message to stdout specifying that the list of supported transports has ended
  def writeMethodEnd(self): # CMETHODS DONE
    print('CMETHODS DONE')
