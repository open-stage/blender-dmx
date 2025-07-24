# Copyright (C) 2020 Hugo Aboud, Kaspars Jaudzems, vanous
#
# This file is part of BlenderDMX.
#
# BlenderDMX is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# BlenderDMX is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <https://www.gnu.org/licenses/>.

import struct
import threading
from socket import (
    AF_INET,
    SHUT_RDWR,
    SO_BROADCAST,
    SO_REUSEADDR,
    SOCK_DGRAM,
    SOL_SOCKET,
    socket,
)

import bpy

from .data import DMX_Data
from .logging_setup import DMX_Log
from .network import DMX_Network

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
        self.net = None
        self.subnet = None
        self.universe = None
        self.length = None
        self.data = None

    def __str__(self):
        return (
            "ArtNet package:\n - op_code: {0}\n - version: {1}\n - "
            "sequence: {2}\n - physical: {3}\n - universe: {4}\n - "
            "length: {5}\n - data : {6}"
        ).format(
            self.op_code,
            self.ver,
            self.sequence,
            self.physical,
            f"{self.net}.{self.subnet}.{self.universe}",
            self.length,
            [c for c in self.data],
        )

    def build(udp_data):
        if struct.unpack("!8s", udp_data[:8])[0] != ArtnetPacket.ARTNET_HEADER:
            DMX_Log.log.debug("Received a non Art-Net packet")
            return None

        packet = ArtnetPacket()
        (
            packet.op_code,
            packet.ver,
            packet.sequence,
            packet.physical,
            sub_uni,
            packet.net,
            packet.length,
        ) = struct.unpack("!HHBBBBH", udp_data[8:18])
        (packet.subnet, packet.universe) = sub_uni >> 4, sub_uni & 0x0F

        packet.data = struct.unpack(
            "{0}s".format(int(packet.length)), udp_data[18 : 18 + int(packet.length)]
        )[0]

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
        try:
            self._socket.bind((ip_addr, ARTNET_PORT))
        except OSError as e:
            DMX_Log.log.error(e)
            self._dmx.artnet_status = "socket_error"
            raise ValueError("Socket opening error")

        # self._socket.settimeout(30)
        self._stopped = False
        # Used with the universe number to determine the Art-Net Port-Address
        self.net = 0
        self.subnet = 0

    def stop(self):
        try:
            self._socket.shutdown(SHUT_RDWR)
        except Exception as e:
            DMX_Log.log.error(f"Error while stopping {e}")
            self._stopped = True
            raise ValueError("Socket closing error")
        self._stopped = True

    def run(self):
        while not self._stopped:
            data = b""
            try:
                data = self._socket.recv(1024)
            except Exception as e:
                DMX_Log.log.error(e)
            if len(data) < 8:
                continue
            if struct.unpack("!8s", data[:8])[0] != ArtnetPacket.ARTNET_HEADER:
                continue
            opcode = struct.unpack("<H", data[8:10])[0]
            if opcode == ArtnetPacket.opcode_ArtDMX:
                self.handleArtNet(data)
            elif opcode == ArtnetPacket.opcode_ArtPoll:
                self.handle_ArtPoll()
            # DMX_Log.log.debug(packet)
            # self._socket.close()
        DMX_Log.log.info("Closing socket...")
        self._dmx.artnet_status = "socket_close"
        self._socket.close()
        self._dmx.artnet_status = "offline"
        self._stopped = True

    def handle_ArtPoll(self):
        """ArtPoll is a message to find out which other ArtNet devices are in the network.
        Sends an ArtPollReply message as an answer."""
        self._socket.sendto(self.build_ArtPollReply(), ("<broadcast>", ARTNET_PORT))

    def handleArtNet(self, data):
        packet = ArtnetPacket.build(data)

        try:
            if self._dmx.artnet_status != "online":
                self._dmx.artnet_status = "online"
        except Exception as e:
            DMX_Log.log.error(f"Error when setting status {e}")

        if not (packet.net == self.net and packet.subnet == self.subnet):
            DMX_Log.log.info("rejected {packet}")
            return
        # we are not checking if we are actually subscribed to the universe
        # so all packets with matching net and subnet will be accepted
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
        content.append(ArtnetPacket.ARTNET_HEADER)
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
        content += [struct.pack("B", i) for i in ip]
        # Port
        content.append(struct.pack("<H", 0x1936))
        # Firmware Version
        content.append(struct.pack("!H", 1))
        # Net and subnet of this node
        content.append(struct.pack("B", self.net))  # NetSwitch
        content.append(struct.pack("B", self.subnet))  # SubSwitch

        # BlenderDMX OEM registered code, do not reuse if copying this code.
        # Programmers: do not copy for other Art-Net implementations,
        # apply for your OEM code here: https://art-net.org.uk/join-the-club/oem-code-application/
        # the process is simple.
        content.append(struct.pack("H", 0x962C))

        # UBEA Version -> Nope -> 0
        # Status1
        content.append(struct.pack("H", 0))
        # Manufacture ESTA Code
        content.append(
            struct.pack("<H", 32767)
        )  # ESTA RDM test code since we did not apply
        # Short Name
        content.append(struct.pack("18s", b"BlenderDMX"))
        content.append(struct.pack("64s", b"BlenderDMX GDTF & MVR plugin for Blender"))
        description = b"#0001 [0000] BlenderDMX. All your GDTFs are belong to us."
        content.append(struct.pack("64s", description))
        # ports
        num_ports = 0  # how many universes do we want to subscribe to
        subscribed_universes = []
        for idx, universe in enumerate(self._dmx.universes):
            if universe.input == "ARTNET":
                num_ports += 1
                subscribed_universes.append(idx)

            # the spec limits this to a max of 4 per ArtPollReply
            # for more than 4 ports, we would need to send multiple replies
            # and set BindIndex
            if num_ports == 4:
                break

        # NumPortsLo/Hi, may be ignored by nodes
        content.append(struct.pack(">H", num_ports))
        for i in range(4):  # PortTypes
            if i < num_ports:
                content.append(struct.pack("B", 0b1000_0000))  # Output DMX
            else:
                content.append(struct.pack("B", 0))
        content.append(struct.pack(">L", 0))  # GoodInput

        for i in range(4):  # GoodOutputA
            if self._dmx.artnet_status == "online":
                # confirm we are receiving DMX data. ideally we would check this for every universe individually
                content.append(struct.pack("B", 0b1000_0000))
            else:
                content.append(struct.pack("B", 0))  # not receiving any data

        for i in range(4):  # SwIn
            content.append(struct.pack("B", 5))

        for i in range(4):  # SwOut
            if i < num_ports:
                content.append(struct.pack("B", subscribed_universes[i]))
            else:
                content.append(struct.pack("B", 0))

        # AcnPriority, SwMacro, SwRemote, Spare[3]
        content.append(struct.pack("6s", b""))
        content.append(struct.pack("B", 0x06))  # Style: StVisual, a visualiser
        content.append(struct.pack("27s", b""))  # 0000

        # stitch together
        return b"".join(content)

    @staticmethod
    def run_render():
        bpy.context.scene.dmx.render()
        return 1.0 / 60.0

    @staticmethod
    def enable():
        if DMX_ArtNet._thread:
            DMX_Log.log.warning("ArtNet client was already started before.")
            return

        dmx = bpy.context.scene.dmx

        DMX_Log.log.info("Starting ArtNet client...")
        DMX_Log.log.info("\t%s:%s" % (dmx.artnet_ipaddr, ARTNET_PORT))
        dmx.artnet_status = "socket_open"

        try:
            DMX_ArtNet._thread = DMX_ArtNet(dmx.artnet_ipaddr)
        except Exception as e:
            DMX_Log.log.error(e)
            return
        DMX_ArtNet._thread.start()

        bpy.app.timers.register(DMX_ArtNet.run_render)

        dmx.artnet_status = "listen"
        DMX_Log.log.info("ArtNet client started.")

    @staticmethod
    def disable():
        if bpy.app.timers.is_registered(DMX_ArtNet.run_render):
            bpy.app.timers.unregister(DMX_ArtNet.run_render)

        dmx = bpy.context.scene.dmx

        if DMX_ArtNet._thread:
            DMX_Log.log.info("Stopping ArtNet client...")
            dmx.artnet_status = "stop"
            try:
                DMX_ArtNet._thread.stop()
                DMX_ArtNet._thread.join()
            except Exception as e:
                DMX_Log.log.exception(e)
            DMX_ArtNet._thread = None
            dmx.artnet_status = "offline"
            DMX_Log.log.info("DONE")
        elif dmx:
            dmx.artnet_status = "offline"

    @staticmethod
    def status():
        return [
            ("offline", "Offline", ""),
            ("socket_open", "Opening socket...", ""),
            (
                "socket_error",
                "Error opening socket... Close other Art-Net applications, re-enable Art-Net in BlenderDMX and start the other application",
                "",
            ),
            ("listen", "Waiting for data...", ""),
            ("online", "Online", ""),
            ("stop", "Stopping thread...", ""),
            ("socket_close", "Closing socket...", ""),
        ]
