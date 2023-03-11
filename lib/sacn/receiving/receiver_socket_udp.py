# This file is under MIT license. The license file can be obtained in the root directory of this module.

import socket
import threading
import time
from dmx.sacn.receiving.receiver_socket_base import ReceiverSocketBase, ReceiverSocketListener

THREAD_NAME = 'sACN input/receiver thread'


class ReceiverSocketUDP(ReceiverSocketBase):
    """
    Implements a receiver socket with a UDP socket of the OS.
    """

    def __init__(self, listener: ReceiverSocketListener, bind_address: str, bind_port: int):
        super().__init__(listener=listener)

        self._bind_address: str = bind_address
        self._bind_port: int = bind_port
        self._enabled_flag: bool = True

        # initialize the UDP socket
        self._socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        try:
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except socket.error:  # Not all systems support multiple sockets on the same port and interface
            pass
        self._socket.bind((self._bind_address, self._bind_port))
        self._logger.info(f'Bind receiver socket to IP: {self._bind_address} port: {self._bind_port}')

    def start(self):
        # initialize thread infos
        self._thread = threading.Thread(
            target=self.receive_loop,
            name=THREAD_NAME
        )
        # self._thread.setDaemon(True)  # TODO: might be beneficial to use a daemon thread
        self._thread.start()

    def receive_loop(self) -> None:
        """
        Implements the run method inherited by threading.Thread
        """
        self._logger.info(f'Started {THREAD_NAME}')
        self._socket.settimeout(0.1)  # timeout as 100ms
        self._enabled_flag = True
        while self._enabled_flag:
            # before receiving: invoke periodic callback
            self._listener.on_periodic_callback(time.time())
            # receive the data
            try:
                raw_data = list(self._socket.recv(2048))  # greater than 1144 because the longest possible packet
                # in the sACN standard is the universe discovery packet with a max length of 1144
            except socket.timeout:
                continue  # if a timeout happens just go through while from the beginning
            self._listener.on_data(raw_data, time.time())

        self._logger.info(f'Stopped {THREAD_NAME}')

    def stop(self) -> None:
        """
        Stops a running thread and closes the underlying socket. If no thread was started, nothing happens.
        Do not reuse the socket after calling stop once.
        """
        self._enabled_flag = False
        try:
            self._thread.join()
            # stop the socket, after the loop terminated
            self._socket.close()
        except AttributeError:
            pass

    def join_multicast(self, multicast_addr: str) -> None:
        """
        Join a specific multicast address by string. Only IPv4.
        """
        # Windows: https://learn.microsoft.com/en-us/windows/win32/winsock/ipproto-ip-socket-options
        # Linux: https://man7.org/linux/man-pages/man7/ip.7.html
        self._socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP,
                                socket.inet_aton(multicast_addr) +
                                socket.inet_aton(self._bind_address))

    def leave_multicast(self, multicast_addr: str) -> None:
        """
        Leave a specific multicast address by string. Only IPv4.
        """
        # Windows: https://learn.microsoft.com/en-us/windows/win32/winsock/ipproto-ip-socket-options
        # Linux: https://man7.org/linux/man-pages/man7/ip.7.html
        try:
            self._socket.setsockopt(socket.IPPROTO_IP, socket.IP_DROP_MEMBERSHIP,
                                    socket.inet_aton(multicast_addr) +
                                    socket.inet_aton(self._bind_address))
        except socket.error:  # try to leave the multicast group for the universe
            pass
