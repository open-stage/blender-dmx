# This file is under MIT license. The license file can be obtained in the root directory of this module.

import pytest
from dmx.sacn.messages.root_layer import RootLayer
from dmx.sacn.sending.sender_socket_base import SenderSocketBase, SenderSocketListener


def test_abstract_sender_socket_listener():
    listener = SenderSocketListener()
    with pytest.raises(NotImplementedError):
        listener.on_periodic_callback(1.0)


def test_abstract_sender_socket_base():
    socket = SenderSocketBase(None)
    with pytest.raises(NotImplementedError):
        socket.start()
    with pytest.raises(NotImplementedError):
        socket.stop()
    with pytest.raises(NotImplementedError):
        socket.send_unicast(RootLayer(1, tuple(range(0, 16)), (0, 0, 0, 0)), 'test')
    with pytest.raises(NotImplementedError):
        socket.send_multicast(RootLayer(1, tuple(range(0, 16)), (0, 0, 0, 0)), 'test', 12)
    with pytest.raises(NotImplementedError):
        socket.send_broadcast(RootLayer(1, tuple(range(0, 16)), (0, 0, 0, 0)))
