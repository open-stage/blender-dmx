# This file is under MIT license. The license file can be obtained in the root directory of this module.

import pytest
import sacn
from sacn.messages.data_packet import DataPacket
from sacn.receiving.receiver_socket_test import ReceiverSocketTest


def get_receiver():
    socket = ReceiverSocketTest()
    receiver = sacn.sACNreceiver(socket=socket)
    # wire up for unit test
    receiver._handler.socket._listener = receiver._handler
    return receiver, socket


def test_constructor():
    receiver, _ = get_receiver()
    assert receiver._callbacks is not None
    assert receiver._handler is not None


def test_listen_on_availability_change():
    receiver, socket = get_receiver()

    called = False

    @receiver.listen_on('availability')
    def callback_available(universe, changed):
        assert changed == 'available'
        assert universe == 1
        nonlocal called
        called = True

    packet = DataPacket(
        cid=tuple(range(0, 16)),
        sourceName='Test',
        universe=1,
        dmxData=tuple(range(0, 16))
    )
    socket.call_on_data(bytes(packet.getBytes()), 0)
    assert called


def test_listen_on_dmx_data_change():
    receiver, socket = get_receiver()

    packetSend = DataPacket(
        cid=tuple(range(0, 16)),
        sourceName='Test',
        universe=1,
        dmxData=tuple(range(0, 16))
    )

    called = False

    @receiver.listen_on('universe', universe=packetSend.universe)
    def callback_packet(packet):
        assert packetSend.__dict__ == packet.__dict__
        nonlocal called
        called = True

    socket.call_on_data(bytes(packetSend.getBytes()), 0)
    assert called


def test_remove_listener():
    receiver, socket = get_receiver()

    packetSend = DataPacket(
        cid=tuple(range(0, 16)),
        sourceName='Test',
        universe=1,
        dmxData=tuple(range(0, 16))
    )

    called = 0

    def callback_packet(packet):
        assert packetSend.__dict__ == packet.__dict__
        nonlocal called
        called += 1

    # register listener multiple times
    receiver.register_listener('universe', callback_packet, universe=packetSend.universe)
    receiver.register_listener('universe', callback_packet, universe=packetSend.universe)

    socket.call_on_data(bytes(packetSend.getBytes()), 0)
    assert called == 2

    # change DMX data to trigger a change
    packetSend.dmxData = tuple(range(16, 32))
    packetSend.sequence_increase()

    receiver.remove_listener(callback_packet)

    # removing a listener does not exist, should do nothing
    receiver.remove_listener(None)

    socket.call_on_data(bytes(packetSend.getBytes()), 0)
    assert called == 2


def test_remove_listener_from_universe():
    receiver, socket = get_receiver()

    test_universe_one = 1
    test_universe_two = 2

    packet_send = DataPacket(
        cid=tuple(range(0, 16)),
        sourceName='Test',
        universe=test_universe_one,
        dmxData=tuple(range(0, 16))
    )

    called = 0

    def callback_packet(packet):
        assert packet_send.__dict__ == packet.__dict__
        nonlocal called
        called += 1

    # register listener multiple times
    receiver.register_listener('universe', callback_packet, universe=test_universe_one)
    receiver.register_listener('universe', callback_packet, universe=test_universe_two)

    packet_send.universe = test_universe_one
    socket.call_on_data(bytes(packet_send.getBytes()), 0)
    assert called == 1
    packet_send.universe = test_universe_two
    socket.call_on_data(bytes(packet_send.getBytes()), 0)
    assert called == 2

    # change DMX data to trigger a change
    packet_send.dmxData = tuple(range(16, 32))
    packet_send.sequence_increase()

    test_universe_removed = test_universe_one
    receiver.remove_listener_from_universe(test_universe_removed)

    # removing from a universe that does not exist, should do nothing
    receiver.remove_listener_from_universe(12345)

    # call to the removed universe should not happen
    packet_send.universe = test_universe_removed
    socket.call_on_data(bytes(packet_send.getBytes()), 0)
    assert called == 2
    # other universes should not be affected
    packet_send.universe = test_universe_two
    socket.call_on_data(bytes(packet_send.getBytes()), 0)
    assert called == 3


def test_invalid_listener():
    receiver, socket = get_receiver()

    with pytest.raises(TypeError):
        @receiver.listen_on('test')
        def callback():
            pass


def test_possible_universes():
    receiver, socket = get_receiver()

    assert receiver.get_possible_universes() == ()
    packet = DataPacket(
        cid=tuple(range(0, 16)),
        sourceName='Test',
        universe=1,
        dmxData=tuple(range(0, 16))
    )
    socket.call_on_data(bytes(packet.getBytes()), 0)
    assert receiver.get_possible_universes() == tuple([1])


def test_join_multicast():
    receiver, socket = get_receiver()

    assert socket.join_multicast_called is None
    receiver.join_multicast(1)
    assert socket.join_multicast_called == '239.255.0.1'

    with pytest.raises(TypeError):
        receiver.join_multicast('test')


def test_leave_multicast():
    receiver, socket = get_receiver()

    assert socket.leave_multicast_called is None
    receiver.leave_multicast(1)
    assert socket.leave_multicast_called == '239.255.0.1'

    with pytest.raises(TypeError):
        receiver.leave_multicast('test')


def test_start():
    receiver, socket = get_receiver()

    assert socket.start_called is False
    receiver.start()
    assert socket.start_called is True


def test_stop():
    receiver, socket = get_receiver()

    assert socket.stop_called is False
    receiver.stop()
    assert socket.stop_called is True


def test_stop_destructor():
    receiver, socket = get_receiver()

    assert socket.stop_called is False
    receiver.__del__()
    assert socket.stop_called is True
