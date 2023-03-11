# This file is under MIT license. The license file can be obtained in the root directory of this module.

import pytest
from dmx.sacn.messages.data_packet import DataPacket
from dmx.sacn.receiving.receiver_handler import ReceiverHandler, ReceiverHandlerListener, E131_NETWORK_DATA_LOSS_TIMEOUT_ms
from dmx.sacn.receiving.receiver_socket_test import ReceiverSocketTest


class ReceiverHandlerListenerTest(ReceiverHandlerListener):
    def __init__(self):
        self.on_availability_change_universe: int = None
        self.on_availability_change_changed: str = None
        self.on_dmx_data_change_packet: DataPacket = None

    def on_availability_change(self, universe: int, changed: str) -> None:
        self.on_availability_change_universe = universe
        self.on_availability_change_changed = changed

    def on_dmx_data_change(self, packet: DataPacket) -> None:
        self.on_dmx_data_change_packet = packet


def get_handler():
    bind_address = 'Test'
    bind_port = 1234
    listener = ReceiverHandlerListenerTest()
    socket = ReceiverSocketTest()
    handler = ReceiverHandler(bind_address, bind_port, listener, socket)
    # wire up for unit test
    socket._listener = handler
    return handler, listener, socket


def test_constructor():
    handler, _, _ = get_handler()
    assert handler._listener is not None
    assert handler._previousData is not None
    assert handler._priorities is not None
    assert handler._lastDataTimestamps is not None
    assert handler._lastSequence is not None


def test_first_packet():
    _, listener, socket = get_handler()
    assert listener.on_availability_change_changed is None
    assert listener.on_availability_change_universe is None
    assert listener.on_dmx_data_change_packet is None
    packet = DataPacket(
        cid=tuple(range(0, 16)),
        sourceName='Test',
        universe=1,
        dmxData=tuple(range(0, 16))
    )
    socket.call_on_data(bytes(packet.getBytes()), 0)
    assert listener.on_availability_change_changed == 'available'
    assert listener.on_availability_change_universe == 1
    assert listener.on_dmx_data_change_packet.__dict__ == packet.__dict__


def test_first_packet_stream_terminated():
    _, listener, socket = get_handler()
    assert listener.on_availability_change_changed is None
    assert listener.on_availability_change_universe is None
    assert listener.on_dmx_data_change_packet is None
    packet = DataPacket(
        cid=tuple(range(0, 16)),
        sourceName='Test',
        universe=1,
        dmxData=tuple(range(0, 16)),
        streamTerminated=True
    )
    socket.call_on_data(bytes(packet.getBytes()), 0)
    assert listener.on_availability_change_changed == 'timeout'
    assert listener.on_availability_change_universe == 1
    assert listener.on_dmx_data_change_packet.__dict__ == packet.__dict__


def test_invalid_packet_bytes():
    _, listener, socket = get_handler()
    assert listener.on_availability_change_changed is None
    assert listener.on_availability_change_universe is None
    assert listener.on_dmx_data_change_packet is None
    # provide 'random' data that is no DataPacket
    socket.call_on_data(bytes(x % 256 for x in range(0, 512)), 0)
    assert listener.on_availability_change_changed is None
    assert listener.on_availability_change_universe is None
    assert listener.on_dmx_data_change_packet is None


def test_invalid_priority():
    # send a lower priority on a second packet
    _, listener, socket = get_handler()
    assert listener.on_dmx_data_change_packet is None
    packet1 = DataPacket(
        cid=tuple(range(0, 16)),
        sourceName='Test',
        universe=1,
        dmxData=tuple(range(0, 16)),
        priority=100
    )
    socket.call_on_data(bytes(packet1.getBytes()), 0)
    assert listener.on_dmx_data_change_packet.__dict__ == packet1.__dict__
    packet2 = DataPacket(
        cid=tuple(range(0, 16)),
        sourceName='Test',
        universe=1,
        dmxData=tuple(range(0, 16)),
        priority=99
    )
    socket.call_on_data(bytes(packet2.getBytes()), 1)
    # second packet does not override the previous one
    assert listener.on_dmx_data_change_packet.__dict__ == packet1.__dict__


def test_invalid_sequence():
    # send a lower sequence on a second packet
    def case_goes_through(sequence_a: int, sequence_b: int):
        _, listener, socket = get_handler()
        assert listener.on_dmx_data_change_packet is None
        packet1 = DataPacket(
            cid=tuple(range(0, 16)),
            sourceName='Test',
            universe=1,
            dmxData=tuple(range(0, 16)),
            sequence=sequence_a
        )
        socket.call_on_data(bytes(packet1.getBytes()), 0)
        assert listener.on_dmx_data_change_packet.__dict__ == packet1.__dict__
        packet2 = DataPacket(
            cid=tuple(range(0, 16)),
            sourceName='Test',
            universe=1,
            # change DMX data to simulate data from another source
            dmxData=tuple(range(1, 17)),
            sequence=sequence_b
        )
        socket.call_on_data(bytes(packet2.getBytes()), 1)
        assert listener.on_dmx_data_change_packet.__dict__ == packet2.__dict__

    case_goes_through(100, 80)
    case_goes_through(101, 102)
    case_goes_through(255, 0)
    case_goes_through(0, 236)
    with pytest.raises(AssertionError):
        case_goes_through(100, 81)
    with pytest.raises(AssertionError):
        case_goes_through(100, 99)
    # Note: this should probably also fail, but the algorithm from the E1.31 spec does not
    # work with wrap around 255...
    case_goes_through(0, 255)


def test_possible_universes():
    handler, _, socket = get_handler()
    assert handler.get_possible_universes() == []
    packet = DataPacket(
        cid=tuple(range(0, 16)),
        sourceName='Test',
        universe=1,
        dmxData=tuple(range(0, 16))
    )
    # add universe 1
    socket.call_on_data(bytes(packet.getBytes()), 0)
    assert handler.get_possible_universes() == [1]
    # add universe 2
    packet.universe = 2
    socket.call_on_data(bytes(packet.getBytes()), 0)
    assert handler.get_possible_universes() == [1, 2]
    # remove universe 2
    packet.option_StreamTerminated = True
    socket.call_on_data(bytes(packet.getBytes()), 0)
    assert handler.get_possible_universes() == [1]


def test_universe_timeout():
    _, listener, socket = get_handler()
    assert listener.on_availability_change_changed is None
    assert listener.on_availability_change_universe is None
    packet = DataPacket(
        cid=tuple(range(0, 16)),
        sourceName='Test',
        universe=1,
        dmxData=tuple(range(0, 16))
    )
    socket.call_on_data(bytes(packet.getBytes()), 0)
    socket.call_on_periodic_callback(0)
    assert listener.on_availability_change_changed == 'available'
    assert listener.on_availability_change_universe == 1
    # wait the specified amount of time and check, that a timeout was triggered
    # add 10ms of grace time
    socket.call_on_periodic_callback((E131_NETWORK_DATA_LOSS_TIMEOUT_ms / 1000) + 0.01)
    assert listener.on_availability_change_changed == 'timeout'
    assert listener.on_availability_change_universe == 1


def test_universe_stream_terminated():
    _, listener, socket = get_handler()
    assert listener.on_availability_change_changed is None
    assert listener.on_availability_change_universe is None
    packet = DataPacket(
        cid=tuple(range(0, 16)),
        sourceName='Test',
        universe=1,
        dmxData=tuple(range(0, 16))
    )
    socket.call_on_data(bytes(packet.getBytes()), 0)
    assert listener.on_availability_change_changed == 'available'
    assert listener.on_availability_change_universe == 1
    packet.sequence_increase()
    packet.option_StreamTerminated = True
    socket.call_on_data(bytes(packet.getBytes()), 0)
    assert listener.on_availability_change_changed == 'timeout'
    assert listener.on_availability_change_universe == 1


def test_abstract_receiver_handler_listener():
    listener = ReceiverHandlerListener()
    with pytest.raises(NotImplementedError):
        listener.on_availability_change(1, 'test')
    with pytest.raises(NotImplementedError):
        listener.on_dmx_data_change(DataPacket(
            cid=tuple(range(0, 16)),
            sourceName='Test',
            universe=1
        ))
