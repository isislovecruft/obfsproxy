# XXX modulify transports and move this to a single import
import obfsproxy.transports.dummy as dummy
import obfsproxy.transports.b64 as b64
import obfsproxy.transports.obfs2 as obfs2
import obfsproxy.transports.obfs3 as obfs3

transports = { 'dummy' : {'client' : dummy.DummyClient, 'server' : dummy.DummyServer },
               'b64' : {'client' : b64.B64Client, 'server' : b64.B64Server },
               'obfs2' : {'client' : obfs2.Obfs2Client, 'server' : obfs2.Obfs2Server },
               'obfs3' : {'client' : obfs3.Obfs3Client, 'server' : obfs3.Obfs3Server } }

def get_transport_class(name, role):
    # Rewrite equivalent roles.
    if role == 'socks':
        role = 'client'
    elif role == 'ext_server':
        role = 'server'

    # Find the correct class
    if (name in transports) and (role in transports[name]):
        return transports[name][role]
    else:
        raise TransportNotFound

class TransportNotFound(Exception): pass

