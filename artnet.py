import bpy

from socket import (socket, AF_INET, SOCK_DGRAM, SHUT_RDWR)
from struct import unpack
import threading

from dmx.data import DMX_Data

# ArtnetPacket class taken from here:
# https://gist.github.com/alarrosa14/07bd1ee88a19204cbf22
# Thank you, @alarrosa!

ARTNET_PORT = 6454

class ArtnetPacket:

    ARTNET_HEADER = b'Art-Net\x00'

    def __init__(self):
        self.op_code = None
        self.ver = None
        self.sequence = None
        self.physical = None
        self.universe = None
        self.length = None
        self.data = None

    def __str__(self):
        return ("ArtNet package:\n - op_code: {0}\n - version: {1}\n - "
                "sequence: {2}\n - physical: {3}\n - universe: {4}\n - "
                "length: {5}\n - data : {6}").format(
            self.op_code, self.ver, self.sequence, self.physical,
            self.universe, self.length, [c for c in self.data])

    def build(udp_data):

        if unpack('!8s', udp_data[:8])[0] != ArtnetPacket.ARTNET_HEADER:
            print("Received a non Art-Net packet")
            return None

        packet = ArtnetPacket()
        (packet.op_code, packet.ver, packet.sequence, packet.physical,
            packet.universe, packet.length) = unpack('!HHBBHH', udp_data[8:18])
        (packet.universe,) = unpack('<H', udp_data[14:16])

        packet.data = unpack(
            '{0}s'.format(int(packet.length)),
            udp_data[18:18+int(packet.length)])[0]

        return packet

class DMX_ArtNet(threading.Thread):

    _thread = None

    def __init__(self, ip_addr, *args, **kwargs):
        super(DMX_ArtNet, self).__init__(*args, **kwargs)
        self._dmx = bpy.context.scene.dmx
        self._socket = socket(AF_INET, SOCK_DGRAM)
        self._socket.bind((ip_addr, ARTNET_PORT))
        self._socket.settimeout(30)
        self._stopped = False

    def stop(self):
        try:
            self._socket.shutdown(SHUT_RDWR)
        except Exception as e:
            print(e)
        self._stopped = True

    def run(self):
        while not self._stopped:
            try:
                data, _ = self._socket.recvfrom(1024)
                packet = ArtnetPacket.build(data)
                self._dmx.artnet_status = 'online'

                if (packet.universe >= len(self._dmx.universes)):
                    continue
                if (not self._dmx.universes[packet.universe]):
                    continue
                if (self._dmx.universes[packet.universe].input != 'ARTNET'):
                    continue
                
                DMX_Data.set_universe(packet.universe, bytearray(packet.data))
                
                #print(packet)
            except Exception as e:
                print(e)
                #self._socket.close()
        print('Closing socket...')
        self._dmx.artnet_status = 'socket_close'
        self._socket.close()
        self._dmx.artnet_status = 'offline'
    
    @staticmethod
    def run_render():
        bpy.context.scene.dmx.render()
        return (1.0/60.0)
    
    @staticmethod
    def enable():
        if (DMX_ArtNet._thread):
            return print('ArtNet client already started.')
        
        dmx = bpy.context.scene.dmx
            
        print('Starting ArtNet client...')
        print('\t%s:%s' % (dmx.artnet_ipaddr, ARTNET_PORT))
        dmx.artnet_status = 'socket_open'

        DMX_ArtNet._thread = DMX_ArtNet(dmx.artnet_ipaddr)
        DMX_ArtNet._thread.start()
        
        bpy.app.timers.register(DMX_ArtNet.run_render)

        dmx.artnet_status = 'listen'
        print('ArtNet client started.')
    
    @staticmethod
    def disable():
        if (bpy.app.timers.is_registered(DMX_ArtNet.run_render)):
            bpy.app.timers.unregister(DMX_ArtNet.run_render)
            
        dmx = bpy.context.scene.dmx

        if (DMX_ArtNet._thread):
            print('Stopping ArtNet client...', end='', flush=True)
            dmx.artnet_status = 'stop'
            DMX_ArtNet._thread.stop()
            DMX_ArtNet._thread.join()
            DMX_ArtNet._thread = None
            dmx.artnet_status = 'offline'
            print('DONE')
        elif(dmx):
            dmx.artnet_status = 'offline'
                
    @staticmethod
    def status():
        return [
            ('offline', 'Offline', ''),
            ('socket_open', 'Opening socket...', ''),
            ('listen', 'Waiting for data...', ''),
            ('online', 'Online', ''),
            ('stop', 'Stopping thread...', ''),
            ('socket_close', 'Closing socket...', ''),
        ]
