# This file is under MIT license. The license file can be obtained in the root directory of this module.

"""
This is a server for sending out sACN and receiving sACN data.
http://tsp.esta.org/tsp/documents/docs/E1-31-2016.pdf
"""

import random
import time
from typing import Dict, List, Optional

from dmx.sacn.messages.data_packet import DataPacket
from dmx.sacn.sending.output import Output
from dmx.sacn.sending.sender_socket_base import SenderSocketBase, DEFAULT_PORT
from dmx.sacn.sending.sender_handler import SenderHandler


class sACNsender:
    def __init__(self, bind_address: str = '0.0.0.0', bind_port: int = DEFAULT_PORT,
                 source_name: str = 'default source name', cid: tuple = (),
                 fps: int = 30, universeDiscovery: bool = True,
                 sync_universe: int = 63999, socket: SenderSocketBase = None):
        """
        Creates a sender object. A sender is used to manage multiple sACN universes and handles their sending.
        DMX data is send out every second, when no data changes. Some changes may be not send out, because the fps
        setting defines how often packets are send out to prevent network overuse. So if you change the DMX values too
        often in a second they may not all been send. Vary the fps parameter to your needs (Default=30).
        Note that a bind address is needed on Windows for sending out multicast packets.
        :param bind_address: the IP-Address to bind to.
        For multicast on a Windows machine this must be set to a proper value otherwise omit.
        :param bind_port: optionally bind to a specific port. Default=5568. It is not recommended to change the port.
        Change the port number if you have trouble with another program or the sACNreceiver blocking the port
        :param source_name: the source name used in the sACN packets.
        :param cid: the cid. If not given, a random CID will be generated.
        :param fps: the frames per second. See above explanation. Has to be >0
        :param sync_universe: universe to send sync packets on.
        :param socket: Provide a special socket implementation if necessary. Must be derived from SenderSocketBase,
        only use if the default socket implementation of this library is not sufficient.
        """
        if len(cid) != 16:
            cid = tuple(int(random.random() * 255) for _ in range(0, 16))
        self._outputs: Dict[int, Output] = {}
        self._sender_handler = SenderHandler(cid, source_name, self._outputs, bind_address, bind_port, fps, socket)
        self.universeDiscovery = universeDiscovery
        self._sync_universe: int = sync_universe

    @property
    def universeDiscovery(self) -> bool:
        return self._sender_handler.universe_discovery

    @universeDiscovery.setter
    def universeDiscovery(self, universeDiscovery: bool) -> None:
        self._sender_handler.universe_discovery = universeDiscovery

    @property
    def manual_flush(self) -> bool:
        return self._sender_handler.manual_flush

    @manual_flush.setter
    def manual_flush(self, manual_flush: bool) -> None:
        self._sender_handler.manual_flush = manual_flush

    def flush(self, universes: List[int] = []):
        """
        Sends out all universes in one go. This is done on the caller's thread!
        This uses the E1.31 sync mechanism to try to sync all universes.
        Note that not all receivers support this feature.
        :param universes: a list of universes to send. If not given, all will be sent.
        :raises ValueError: when attempting to flush a universe that is not activated.
        """
        for uni in universes:
            if uni not in self._outputs:
                raise ValueError(f'Cannot flush universe {uni}, it is not active!')
        self._sender_handler.send_out_all_universes(
            self._sync_universe,
            self._outputs if not universes else {uni: self._outputs[uni] for uni in universes},
            time.time()
        )

    def activate_output(self, universe: int) -> None:
        """
        Activates a universe that's then starting to sending every second.
        See http://tsp.esta.org/tsp/documents/docs/E1-31-2016.pdf for more information
        :param universe: the universe to activate
        """
        check_universe(universe)
        # check, if the universe already exists in the list:
        if universe in self._outputs:
            return
        # add new sending:
        new_output = Output(DataPacket(cid=self._sender_handler._CID, sourceName=self._sender_handler._source_name, universe=universe))
        self._outputs[universe] = new_output

    def deactivate_output(self, universe: int) -> None:
        """
        Deactivates an existing sending. Every data from the existing sending output will be lost.
        (TTL, Multicast, DMX data, ..)
        :param universe: the universe to deactivate. If the universe was not activated before, no error is raised
        """
        check_universe(universe)
        try:  # try to send out three messages with stream_termination bit set to 1
            self._outputs[universe]._packet.option_StreamTerminated = True
            for _ in range(0, 3):
                self._sender_handler.send_out(self._outputs[universe], time.time())
        except KeyError:
            pass
        try:
            del self._outputs[universe]
        except KeyError:
            pass

    def get_active_outputs(self) -> tuple:
        """
        Returns a list with all active outputs. Useful when iterating over all sender indexes.
        :return: list: a list with int (every int is a activated universe. May be not sorted)
        """
        return tuple(self._outputs.keys())

    def move_universe(self, universe_from: int, universe_to: int) -> None:
        """
        Moves an sending from one universe to another. All settings are being restored and only the universe changes
        :param universe_from: the universe that should be moved
        :param universe_to: the target universe. An existing universe will be overwritten
        """
        check_universe(universe_from)
        check_universe(universe_to)
        # store the sending object and change the universe in the packet of the sending
        tmp_output = self._outputs[universe_from]
        # deactivate sending
        self.deactivate_output(universe_from)
        # activate new sending with the new universe
        tmp_output._packet.universe = universe_to
        tmp_output._packet.option_StreamTerminated = False
        self._outputs[universe_to] = tmp_output

    def __getitem__(self, item: int) -> Optional[Output]:
        try:
            return self._outputs[item]
        except KeyError:
            return None

    def start(self) -> None:
        """
        Starts or restarts a new Thread with the parameters given in the constructor.
        """
        self.stop()
        self._sender_handler.start()

    def stop(self) -> None:
        """
        Stops a running thread and closes the underlying socket. If no thread was started, nothing happens.
        Do not reuse the socket after calling stop once.
        """
        self._sender_handler.stop()

    def __del__(self):
        # stop a potential running thread
        self.stop()


def check_universe(universe: int):
    if universe not in range(1, 64000):
        raise ValueError(f'Universe must be between [1-63999]! Universe was {universe}')
