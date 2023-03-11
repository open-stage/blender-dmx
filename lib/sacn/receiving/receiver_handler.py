# This file is under MIT license. The license file can be obtained in the root directory of this module.

from typing import Dict, List

from dmx.sacn.messages.data_packet import DataPacket
from dmx.sacn.receiving.receiver_socket_base import ReceiverSocketBase, ReceiverSocketListener
from dmx.sacn.receiving.receiver_socket_udp import ReceiverSocketUDP

E131_NETWORK_DATA_LOSS_TIMEOUT_ms = 2500


class ReceiverHandlerListener:
    """
    Listener interface that defines methods for listening on changes on the ReceiverHandler.
    """

    def on_availability_change(self, universe: int, changed: str) -> None:
        raise NotImplementedError

    def on_dmx_data_change(self, packet: DataPacket) -> None:
        raise NotImplementedError


class ReceiverHandler(ReceiverSocketListener):
    def __init__(self, bind_address: str, bind_port: int, listener: ReceiverHandlerListener, socket: ReceiverSocketBase = None):
        """
        This is a private class and should not be used elsewhere. It handles the receiver state with sACN specific values.
        Calls any changes in the data streams on the listener.
        Uses a UDP receiver socket with the given bind-address and -port, if the socket was not provided (i.e. None).
        """
        if socket is None:
            self.socket: ReceiverSocketBase = ReceiverSocketUDP(self, bind_address, bind_port)
        else:
            self.socket: ReceiverSocketBase = socket
        self._listener: ReceiverHandlerListener = listener
        # previousData for storing the last data that was send in a universe to check if the data has changed
        self._previousData: Dict[int, tuple] = {}
        # priorities are stored here. This is for checking if the incoming data has the best priority.
        # universes are the keys and
        # the value is a tuple with the last priority and the time when this priority recently was received
        self._priorities: Dict[int, tuple] = {}
        # store the last timestamp when something on an universe arrived for checking for timeouts
        self._lastDataTimestamps: Dict[int, float] = {}
        # store the last sequence number of a universe here:
        self._lastSequence: Dict[int, int] = {}

    def on_data(self, data: bytes, current_time: float) -> None:
        try:
            tmp_packet = DataPacket.make_data_packet(data)
        except TypeError:  # try to make a DataPacket. If it fails just ignore it
            return

        self.check_for_stream_terminated_and_refresh_timestamp(tmp_packet, current_time)
        self.refresh_priorities(tmp_packet, current_time)
        if not self.is_legal_priority(tmp_packet):
            return
        if not self.is_legal_sequence(tmp_packet):  # check for bad sequence number
            return
        self.fire_callbacks_universe(tmp_packet)

    def on_periodic_callback(self, current_time: float) -> None:
        # check all DataTimestamps for timeouts
        for key, value in list(self._lastDataTimestamps.items()):
            #  this is converted to list, because the length of the dict changes
            if check_timeout(current_time, value):
                self.fire_timeout_callback_and_delete(key)

    def check_for_stream_terminated_and_refresh_timestamp(self, packet: DataPacket, current_time: float) -> None:
        # refresh the last timestamp on a universe, but check if its the last message of a stream
        # (the stream is terminated by the Stream termination bit)
        if packet.option_StreamTerminated:
            self.fire_timeout_callback_and_delete(packet.universe)
        else:
            # check if we add or refresh the data in lastDataTimestamps
            if packet.universe not in self._lastDataTimestamps.keys():
                # fire callbacks if this is the first received packet for this universe
                self._listener.on_availability_change(universe=packet.universe, changed='available')
            self._lastDataTimestamps[packet.universe] = current_time

    def fire_timeout_callback_and_delete(self, universe: int):
        self._listener.on_availability_change(universe=universe, changed='timeout')
        # delete the timestamp so that the callback is not fired multiple times
        try:
            del self._lastDataTimestamps[universe]
        except KeyError:
            pass  # drop exception, if there was no last timestamp
        # delete sequence entries so that no packet out of order problems occur
        try:
            del self._lastSequence[universe]
        except KeyError:
            pass  # drop exception, if there was no last sequence number

    def refresh_priorities(self, packet: DataPacket, current_time: float) -> None:
        # check the priority and refresh the priorities dict
        # check if the stored priority has timeouted and make the current packets priority the new one
        if packet.universe not in self._priorities.keys() or \
           self._priorities[packet.universe] is None or \
           check_timeout(current_time, self._priorities[packet.universe][1]) or \
           self._priorities[packet.universe][0] <= packet.priority:  # if the send priority is higher or
            # equal than the stored one, than make the priority the new one
            self._priorities[packet.universe] = (packet.priority, current_time)

    def is_legal_sequence(self, packet: DataPacket) -> bool:
        """
        Check if the Sequence number of the DataPacket is legal.
        For more information see page 17 of http://tsp.esta.org/tsp/documents/docs/E1-31-2016.pdf.
        :param packet: the packet to check
        :return: true if the sequence is legal. False if the sequence number is bad
        """
        # if the sequence of the packet is smaller than the last received sequence, return false
        # therefore calculate the difference between the two values:
        try:  # try, because self.lastSequence might not been initialized
            diff = packet.sequence - self._lastSequence[packet.universe]
            # if diff is between ]-20,0], return False for a bad packet sequence
            if diff <= 0 and diff > -20:
                return False
        except KeyError:
            pass
        # if the sequence is good, return True and refresh the list with the new value
        self._lastSequence[packet.universe] = packet.sequence
        return True

    def is_legal_priority(self, packet: DataPacket):
        """
        Check if the given packet has high enough priority for the stored values for the packet's universe.
        :param packet: the packet to check
        :return: returns True if the priority is good. Otherwise False
        """
        # check if the packet's priority is high enough to get processed
        if packet.priority < self._priorities[packet.universe][0]:
            return False  # return if the universe is not interesting
        else:
            return True

    def fire_callbacks_universe(self, packet: DataPacket) -> None:
        # call the listeners for the universe but before check if the data has changed
        # check if there are listeners for the universe before proceeding
        if packet.universe not in self._previousData.keys() or \
           self._previousData[packet.universe] is None or \
           self._previousData[packet.universe] != packet.dmxData:
            # set previous data and inherit callbacks
            self._previousData[packet.universe] = packet.dmxData
            self._listener.on_dmx_data_change(packet)

    def get_possible_universes(self) -> List[int]:
        return list(self._lastDataTimestamps.keys())


def time_millis(current_time: float) -> int:
    return int(round(current_time * 1000))


def check_timeout(current_time: float, time: float) -> bool:
    return abs(time_millis(current_time) - time_millis(time)) > E131_NETWORK_DATA_LOSS_TIMEOUT_ms
