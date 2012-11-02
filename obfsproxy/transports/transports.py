# XXX modulify transports and move this to a single import
import obfsproxy.transports.dummy as dummy
import obfsproxy.transports.b64 as b64
import obfsproxy.transports.obfs2 as obfs2

transports = { 'dummy' : {'client' : dummy.DummyClient, 'socks' : dummy.DummyClient, 'server' : dummy.DummyServer },
               'b64' : {'client' : b64.B64Client, 'socks' : b64.B64Client, 'server' : b64.B64Server },
               'obfs2' : {'client' : obfs2.Obfs2Client, 'socks' : obfs2.Obfs2Client,  'server' : obfs2.Obfs2Server } }

def get_transport_class(name, role):
    if (name in transports) and (role in transports[name]):
        return transports[name][role]
    else:
        raise TransportNotFound

class TransportNotFound(Exception): pass

