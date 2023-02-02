# This file is under MIT license. The license file can be obtained in the root directory of this module.

import logging


class ReceiverSocketListener:
    """
    Base class for listener of a ReceiverSocketBase.
    """

    def on_data(self, data: bytes, current_time: float) -> None:
        raise NotImplementedError

    def on_periodic_callback(self, current_time: float) -> None:
        raise NotImplementedError


class ReceiverSocketBase:
    """
    Base class for abstracting a UDP receiver socket.
    """

    def __init__(self, listener: ReceiverSocketListener):
        self._logger: logging.Logger = logging.getLogger('sacn')
        self._listener: ReceiverSocketListener = listener

    def start(self) -> None:
        raise NotImplementedError

    def stop(self) -> None:
        raise NotImplementedError

    def join_multicast(self, multicast_addr: str) -> None:
        raise NotImplementedError

    def leave_multicast(self, multicast_addr: str) -> None:
        raise NotImplementedError
