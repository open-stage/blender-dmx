# This file is under MIT license. The license file can be obtained in the root directory of this module.

import logging
from dmx.sacn.messages.root_layer import RootLayer

DEFAULT_PORT = 5568


class SenderSocketListener:
    """
    Base class for listener of a SenderSocketListener.
    """

    def on_periodic_callback(self, time: float) -> None:
        raise NotImplementedError


class SenderSocketBase:
    """
    Base class for abstracting a UDP sending socket.
    """

    def __init__(self, listener: SenderSocketListener):
        self._logger: logging.Logger = logging.getLogger('sacn')
        self._listener: SenderSocketListener = listener

    def start(self) -> None:
        raise NotImplementedError

    def stop(self) -> None:
        raise NotImplementedError

    def send_unicast(self, data: RootLayer, destination: str) -> None:
        raise NotImplementedError

    def send_multicast(self, data: RootLayer, destination: str, ttl: int) -> None:
        raise NotImplementedError

    def send_broadcast(self, data: RootLayer) -> None:
        raise NotImplementedError
