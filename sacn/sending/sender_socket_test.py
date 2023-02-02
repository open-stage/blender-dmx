# This file is under MIT license. The license file can be obtained in the root directory of this module.

import copy
from dmx.sacn.messages.root_layer import RootLayer
from dmx.sacn.sending.sender_socket_base import SenderSocketBase


class SenderSocketTest(SenderSocketBase):
    def __init__(self, listener=None):
        super().__init__(listener)
        self.start_called: bool = False
        self.stop_called: bool = False
        self.send_unicast_called: (RootLayer, str) = None
        self.send_multicast_called: (RootLayer, str, int) = None
        self.send_broadcast_called: RootLayer = None

    def start(self) -> None:
        self.start_called = True

    def stop(self) -> None:
        self.stop_called = True

    def send_unicast(self, data: RootLayer, destination: str) -> None:
        self.send_unicast_called = (copy.deepcopy(data), copy.deepcopy(destination))

    def send_multicast(self, data: RootLayer, destination: str, ttl: int) -> None:
        self.send_multicast_called = (copy.deepcopy(data), copy.deepcopy(destination), ttl)

    def send_broadcast(self, data: RootLayer) -> None:
        self.send_broadcast_called = copy.deepcopy(data)

    def call_on_periodic_callback(self, time: float) -> None:
        self._listener.on_periodic_callback(time)
