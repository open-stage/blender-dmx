# This file is under MIT license. The license file can be obtained in the root directory of this module.

from dmx.sacn.messages.data_packet import DataPacket, calculate_multicast_addr
from dmx.sacn.receiving.receiver_handler import ReceiverHandler, ReceiverHandlerListener
from dmx.sacn.receiving.receiver_socket_base import ReceiverSocketBase
from typing import Tuple

LISTEN_ON_OPTIONS = ('availability', 'universe')


class sACNreceiver(ReceiverHandlerListener):
    def __init__(self, bind_address: str = '0.0.0.0', bind_port: int = 5568, socket: ReceiverSocketBase = None):
        """
        Make a receiver for sACN data. Do not forget to start and add callbacks for receiving messages!
        :param bind_address: if you are on a Windows system and want to use multicast provide a valid interface
        IP-Address! Otherwise omit.
        :param bind_port: Default: 5568. It is not recommended to change this value!
        Only use when you know what you are doing!
        :param socket: Provide a special socket implementation if necessary. Must be derived from ReceiverSocketBase,
        only use if the default socket implementation of this library is not sufficient.
        """

        self._callbacks: dict = {}
        self._handler: ReceiverHandler = ReceiverHandler(bind_address, bind_port, self, socket)

    def on_availability_change(self, universe: int, changed: str) -> None:
        callbacks = []
        # call nothing, if the list with callbacks is empty
        try:
            callbacks = self._callbacks[LISTEN_ON_OPTIONS[0]]
        except KeyError:
            pass
        for callback in callbacks:
            # fire callbacks if this is the first received packet for this universe
            callback(universe=universe, changed=changed)

    def on_dmx_data_change(self, packet: DataPacket) -> None:
        callbacks = []
        # call nothing, if the list with callbacks is empty
        try:
            callbacks = self._callbacks[packet.universe]
        except KeyError:
            pass
        for callback in callbacks:
            callback(packet)

    def listen_on(self, trigger: str, **kwargs) -> callable:
        """
        This is a simple decorator for registering a callback for an event. You can also use 'register_listener'.
        A list with all possible options is available via LISTEN_ON_OPTIONS.
        :param trigger: Currently supported options: 'availability', 'universe'
        """
        def decorator(f):
            self.register_listener(trigger, f, **kwargs)
            return f
        return decorator

    def register_listener(self, trigger: str, func: callable, **kwargs) -> None:
        """
        Register a listener for the given trigger. Raises an TypeError when the trigger is not a valid one.
        To get a list with all valid triggers, use LISTEN_ON_OPTIONS.
        :param trigger: the trigger on which the given callback should be used.
        Currently supported: 'availability', 'universe'
        :param func: the callback. The parameters depend on the trigger. See README for more information
        """
        if trigger in LISTEN_ON_OPTIONS:
            if trigger == LISTEN_ON_OPTIONS[1]:  # if the trigger is universe, use the universe from args as key
                universe = kwargs[LISTEN_ON_OPTIONS[1]]
                try:
                    self._callbacks[universe].append(func)
                except KeyError:
                    self._callbacks[universe] = [func]
            try:
                self._callbacks[trigger].append(func)
            except KeyError:
                self._callbacks[trigger] = [func]
        else:
            raise TypeError(f'The given trigger "{trigger}" is not a valid one!')

    def remove_listener(self, func: callable) -> None:
        """
        Removes the given function from all listening options (see LISTEN_ON_OPTIONS).
        If the function never was registered, nothing happens. Note: if a function was registered multiple times,
        this remove function needs to be called only once.
        :param func: the callback
        """
        for _trigger, listeners in self._callbacks.items():
            while True:
                try:
                    listeners.remove(func)
                except ValueError:
                    break

    def remove_listener_from_universe(self, universe: int) -> None:
        """
        Removes all listeners from the given universe. This does only have effect on the 'universe' listening trigger.
        If no function was registered for this universe, nothing happens.
        :param universe: the universe to clear
        """
        self._callbacks.pop(universe, None)

    def join_multicast(self, universe: int) -> None:
        """
        Joins the multicast address that is used for the given universe. Note: If you are on Windows you must have given
        a bind IP-Address for this feature to function properly. On the other hand you are not allowed to set a bind
        address if you are on any other OS.
        :param universe: the universe to join the multicast group.
        The network hardware has to support the multicast feature!
        """
        self._handler.socket.join_multicast(calculate_multicast_addr(universe))

    def leave_multicast(self, universe: int) -> None:
        """
        Try to leave the multicast group with the specified universe. This does not throw any exception if the group
        could not be leaved.
        :param universe: the universe to leave the multicast group.
        The network hardware has to support the multicast feature!
        """
        self._handler.socket.leave_multicast(calculate_multicast_addr(universe))

    def start(self) -> None:
        """
        Starts a new thread that handles the input. If a thread is already running, the thread will be restarted.
        """
        self.stop()  # stop an existing thread
        self._handler.socket.start()

    def stop(self) -> None:
        """
        Stops a running thread and closes the underlying socket. If no thread was started, nothing happens.
        Do not reuse the socket after calling stop once.
        """
        self._handler.socket.stop()

    def get_possible_universes(self) -> Tuple[int]:
        """
        Get all universes that are possible because a data packet was received. Timeouted data is removed from the list,
        so the list may change over time. Depending on sources that are shutting down their streams.
        :return: a tuple with all universes that were received so far and hadn't a timeout
        """
        return tuple(self._handler.get_possible_universes())

    def __del__(self):
        # stop a potential running thread
        self.stop()
