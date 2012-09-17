# XXX modulify transports and move this to a single import
import obfsproxy.transports.dummy as dummy
import obfsproxy.transports.b64 as b64
import obfsproxy.transports.dust_transport as dust
# XXX obfs2 is broken...
#import obfsproxy.transports.obfs2 as obfs2
#import obfsproxy.transports.obfs3 as obfs3

transports = { 'dummy' : {'client' : dummy.DummyClient, 'socks' : dummy.DummyClient, 'server' : dummy.DummyServer },
               'b64' : {'client' : b64.B64Client, 'socks' : b64.B64Client, 'server' : b64.B64Server },
               'dust' :  {'client' : dust.DustClient, 'socks' : dust.DustClient, 'server' : dust.DustServer } }
#               'obfs2' : {'client' : obfs2.Obfs2Client, 'socks' : obfs2.Obfs2Client,  'server' : obfs2.Obfs2Server },
#               'obfs3' : {'client' : obfs3.Obfs3Client, 'socks' : obfs3.Obfs3Client,  'server' : obfs3.Obfs3Server }

def get_transport_class_from_name_and_mode(name, mode):
    if (name in transports) and (mode in transports[name]):
        return transports[name][mode]
    else:
        return None
