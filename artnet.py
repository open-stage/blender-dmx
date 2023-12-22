import bpy

from socket import socket, AF_INET, SOCK_DGRAM, SHUT_RDWR, SOL_SOCKET, SO_BROADCAST, SO_REUSEADDR
import struct
import threading

from dmx.data import DMX_Data
from dmx.network import DMX_Network
# ArtnetPacket class taken from here:
# https://gist.github.com/alarrosa14/07bd1ee88a19204cbf22
# Thank you, @alarrosa!

ARTNET_PORT = 6454


class ArtnetPacket:
    ARTNET_HEADER = b"Art-Net\x00"
    opcode_ArtDMX = 0x5000
    opcode_ArtPoll = 0x2000

    def __init__(self):
        self.op_code = None
        self.ver = None
        self.sequence = None
        self.physical = None
        self.universe = None
        self.length = None
        self.data = None

    def __str__(self):
        return ("ArtNet package:\n - op_code: {0}\n - version: {1}\n - " "sequence: {2}\n - physical: {3}\n - universe: {4}\n - " "length: {5}\n - data : {6}").format(
            self.op_code, self.ver, self.sequence, self.physical, self.universe, self.length, [c for c in self.data]
        )

    def build(udp_data):
        if struct.unpack("!8s", udp_data[:8])[0] != ArtnetPacket.ARTNET_HEADER:
            print("Received a non Art-Net packet")
            return None

        packet = ArtnetPacket()
        (packet.op_code, packet.ver, packet.sequence, packet.physical, packet.universe, packet.length) = struct.unpack("!HHBBHH", udp_data[8:18])
        (packet.universe,) = struct.unpack("<H", udp_data[14:16])

        packet.data = struct.unpack("{0}s".format(int(packet.length)), udp_data[18 : 18 + int(packet.length)])[0]

        return packet


class DMX_ArtNet(threading.Thread):
    _thread = None

    def __init__(self, ip_addr, *args, **kwargs):
        super(DMX_ArtNet, self).__init__(*args, **kwargs)
        self._dmx = bpy.context.scene.dmx
        self.ip_addr = ip_addr
        self._socket = socket(AF_INET, SOCK_DGRAM)
        self._socket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        self._socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
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
            data = self._socket.recv(1024)
            print("data", data)
            if struct.unpack("!8s", data[:8])[0] != ArtnetPacket.ARTNET_HEADER:
                continue
            opcode = struct.unpack("<H", data[8:10])[0]
            if opcode == ArtnetPacket.opcode_ArtDMX:
                self.handleArtNet(data)
            elif opcode == ArtnetPacket.opcode_ArtPoll:
                self.handle_ArtPoll()
            # print(packet)
            # self._socket.close()
        print("Closing socket...")
        self._dmx.artnet_status = "socket_close"
        self._socket.close()
        self._dmx.artnet_status = "offline"

    def handle_ArtPoll(self):
        """ArtPoll is a message to find out which other ArtNet devices are in the network.
        Sends an ArtPollReply message as an answer."""
        self._socket.sendto(self.build_ArtPollReply(), ("<broadcast>", ARTNET_PORT))

    def handleArtNet(self, data):
        packet = ArtnetPacket.build(data)
        self._dmx.artnet_status = "online"
        if packet.universe >= len(self._dmx.universes):
            return
        if not self._dmx.universes[packet.universe]:
            return
        if self._dmx.universes[packet.universe].input != "ARTNET":
            return
        DMX_Data.set_universe(packet.universe, bytearray(packet.data), "ARTNET")

    def build_ArtPollReply(self):
        """Builds an ArtPollReply message."""
        content = []
        # Name, 7byte + 0x00
        content.append(b"Art-Net\x00")
        # OpCode ArtPollReply -> 0x2100, Low Byte first
        content.append(struct.pack("<H", 0x2100))
        # Protocol Version 14, High Byte first
        # content.append(struct.pack('>H', 14))  # <- not in ArtPollReply
        # IP
        if len(DMX_Network.cards(None, None)):
            ip = DMX_Network.cards(None, None)[-1][0]
        else:
            ip = "0.0.0.0"
        ip = [int(i) for i in ip.split(".")]
        content += [i.to_bytes() for i in ip]
        # Port
        content.append(struct.pack("<H", 0x1936))
        # Firmware Version
        content.append(struct.pack("!H", 1))
        # Net and subnet of this node
        content.append(ip[1].to_bytes())
        content.append(ip[0].to_bytes())
        # OEM Code (E:Cue 1x DMX Out)
        content.append(struct.pack("H", 0)) #0000
        # UBEA Version -> Nope -> 0
        # Status1
        content.append(struct.pack("H", 0))
        # Manufacture ESTA Code
        content.append(struct.pack("<H", 32767)) # test code
        # Short Name
        content.append(struct.pack("18s", b"BlenderDMX"))
        content.append(struct.pack("64s", b"BlenderDMX GDTF & MVR plugin for Blender"))
        description=b"#0001 [0000] BlenderDMX. All your GDTFs are belong to us."
        content.append(struct.pack("64s", description))
        #ports
        content.append(struct.pack(">H", 8)) #0000
        content.append(struct.pack(">L", 0)) #0000
        content.append(struct.pack("46s", b"")) #0000

        # stitch together
        return b"".join(content)

    @staticmethod
    def run_render():
        bpy.context.scene.dmx.render()
        return 1.0 / 60.0

    @staticmethod
    def enable():
        if DMX_ArtNet._thread:
            return print("ArtNet client already started.")

        dmx = bpy.context.scene.dmx

        print("Starting ArtNet client...")
        print("\t%s:%s" % (dmx.artnet_ipaddr, ARTNET_PORT))
        dmx.artnet_status = "socket_open"

        DMX_ArtNet._thread = DMX_ArtNet(dmx.artnet_ipaddr)
        DMX_ArtNet._thread.start()

        bpy.app.timers.register(DMX_ArtNet.run_render)

        dmx.artnet_status = "listen"
        print("ArtNet client started.")

    @staticmethod
    def disable():
        if bpy.app.timers.is_registered(DMX_ArtNet.run_render):
            bpy.app.timers.unregister(DMX_ArtNet.run_render)

        dmx = bpy.context.scene.dmx

        if DMX_ArtNet._thread:
            print("Stopping ArtNet client...", end="", flush=True)
            dmx.artnet_status = "stop"
            DMX_ArtNet._thread.stop()
            DMX_ArtNet._thread.join()
            DMX_ArtNet._thread = None
            dmx.artnet_status = "offline"
            print("DONE")
        elif dmx:
            dmx.artnet_status = "offline"

    @staticmethod
    def status():
        return [
            ("offline", "Offline", ""),
            ("socket_open", "Opening socket...", ""),
            ("listen", "Waiting for data...", ""),
            ("online", "Online", ""),
            ("stop", "Stopping thread...", ""),
            ("socket_close", "Closing socket...", ""),
        ]
