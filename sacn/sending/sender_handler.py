# This file is under MIT license. The license file can be obtained in the root directory of this module.

from typing import Dict
from dmx.sacn.messages.universe_discovery import UniverseDiscoveryPacket
from dmx.sacn.messages.sync_packet import SyncPacket
from dmx.sacn.messages.data_packet import calculate_multicast_addr
from dmx.sacn.sending.output import Output
from dmx.sacn.sending.sender_socket_base import SenderSocketBase, SenderSocketListener
from dmx.sacn.sending.sender_socket_udp import SenderSocketUDP

SEND_OUT_INTERVAL = 1
E131_E131_UNIVERSE_DISCOVERY_INTERVAL = 10


class SenderHandler(SenderSocketListener):
    # TODO: start using type CID instead of tuple
    def __init__(self, cid: tuple, source_name: str, outputs: Dict[int, Output], bind_address: str, bind_port: int, fps: int, socket: SenderSocketBase = None):
        """
        This is a private class and should not be used elsewhere. It handles the sender state with sACN specific values.
        Uses a UDP sender socket with the given bind-address and -port, if the socket was not provided (i.e. None).
        """
        if socket is None:
            self.socket: SenderSocketBase = SenderSocketUDP(self, bind_address, bind_port, fps)
        else:
            self.socket: SenderSocketBase = socket

        self._CID = cid
        self._source_name = source_name
        self.universe_discovery: bool = True
        self._last_time_universe_discover: float = 0
        self._outputs: Dict[int, Output] = outputs
        self.manual_flush: bool = False
        self._sync_sequence = 0

    def on_periodic_callback(self, current_time: float) -> None:
        # send out universe discovery packets if necessary
        if self.universe_discovery and \
              abs(current_time - self._last_time_universe_discover) >= E131_E131_UNIVERSE_DISCOVERY_INTERVAL:
            self.send_universe_discovery_packets()
            self._last_time_universe_discover = current_time

        # go through the list of outputs and send everything out that has to be send out
        # Note: dict may changes size during iteration (multithreading)
        [self.send_out(output, current_time) for output in list(self._outputs.values())
            # only send if the manual flush feature is disabled
            # send out when the 1 second interval is over
            if not self.manual_flush and \
            (output._changed or abs(current_time - output._last_time_send) >= SEND_OUT_INTERVAL)]

    def send_out(self, output: Output, current_time: float):
        # 1st: Destination (check if multicast)
        if output.multicast:
            udp_ip = output._packet.calculate_multicast_addr()
            self.socket.send_multicast(output._packet, udp_ip, output.ttl)
        else:
            udp_ip = output.destination
            self.socket.send_unicast(output._packet, udp_ip)

        output._last_time_send = current_time
        # increase the sequence counter
        output._packet.sequence_increase()
        # the changed flag is not necessary any more
        output._changed = False

    def send_universe_discovery_packets(self):
        packets = UniverseDiscoveryPacket.make_multiple_uni_disc_packets(
            cid=self._CID, sourceName=self._source_name, universes=list(self._outputs.keys()))
        for packet in packets:
            self.socket.send_broadcast(packet)

    def send_out_all_universes(self, sync_universe: int, universes: dict, current_time: float):
        """
        Sends out all universes in one go. This is not done by this thread! This is done by the caller's thread.
        This uses the E1.31 sync mechanism to try to sync all universes.
        Note that not all receivers support this feature.
        """
        # go through the list of outputs and send everything out
        # Note: dict may changes size during iteration (multithreading)
        for output in list(universes.values()):
            output._packet.syncAddr = sync_universe  # temporarily set the sync universe
            self.send_out(output, current_time)
            output._packet.syncAddr = 0

        sync_packet = SyncPacket(cid=self._CID, syncAddr=sync_universe, sequence=self._sync_sequence)
        # Increment sequence number for next time.
        self._sync_sequence += 1
        if self._sync_sequence > 255:
            self._sync_sequence = 0
        self.socket.send_multicast(sync_packet, calculate_multicast_addr(sync_universe), 255)

    def start(self):
        self.socket.start()

    def stop(self):
        self.socket.stop()
