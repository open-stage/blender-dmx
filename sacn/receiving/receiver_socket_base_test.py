# This file is under MIT license. The license file can be obtained in the root directory of this module.

import pytest
from dmx.sacn.receiving.receiver_socket_base import ReceiverSocketBase, ReceiverSocketListener


def test_abstract_receiver_socket_listener():
    listener = ReceiverSocketListener()
    with pytest.raises(NotImplementedError):
        listener.on_data([], 0)
    with pytest.raises(NotImplementedError):
        listener.on_periodic_callback(0)


def test_abstract_receiver_socket_base():
    socket = ReceiverSocketBase(None)
    with pytest.raises(NotImplementedError):
        socket.start()
    with pytest.raises(NotImplementedError):
        socket.stop()
    with pytest.raises(NotImplementedError):
        socket.join_multicast('test')
    with pytest.raises(NotImplementedError):
        socket.leave_multicast('test')
