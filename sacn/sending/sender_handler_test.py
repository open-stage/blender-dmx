# This file is under MIT license. The license file can be obtained in the root directory of this module.

from typing import Dict
from dmx.sacn.messages.data_packet import DataPacket, calculate_multicast_addr
from dmx.sacn.messages.sync_packet import SyncPacket
from dmx.sacn.messages.universe_discovery import UniverseDiscoveryPacket
from dmx.sacn.sending.output import Output
from dmx.sacn.sending.sender_handler import SenderHandler
from dmx.sacn.sending.sender_socket_test import SenderSocketTest


def get_handler():
    cid = tuple(range(0, 16))
    source_name = 'test'
    outputs: Dict[int, Output] = {
        1: Output(
            packet=DataPacket(
                cid=cid,
                sourceName=source_name,
                universe=1,
            )
        )
    }
    socket = SenderSocketTest()
    handler = SenderHandler(
        cid=cid,
        source_name=source_name,
        outputs=outputs,
        bind_address='0.0.0.0',
        bind_port=5568,
        fps=30,
        socket=socket,
    )
    handler.manual_flush = True
    # wire up listener for tests
    socket._listener = handler
    return handler, socket, cid, source_name, outputs


def test_universe_discovery_packets():
    handler, socket, cid, source_name, outputs = get_handler()
    handler.manual_flush = True
    current_time = 100.0

    assert handler.universe_discovery is True
    assert socket.send_broadcast_called is None

    # test that the universe discovery can be disabled
    handler.universe_discovery = False
    socket.call_on_periodic_callback(current_time)
    assert socket.send_broadcast_called is None
    handler.universe_discovery = True

    # if no outputs are specified, there is an empty universe packet send
    socket.call_on_periodic_callback(current_time)
    assert socket.send_broadcast_called == UniverseDiscoveryPacket(cid, source_name, (1,))


def test_send_out_interval():
    handler, socket, cid, source_name, outputs = get_handler()
    handler.manual_flush = False
    current_time = 100.0

    assert handler.manual_flush is False
    assert socket.send_unicast_called is None

    # first send packet due to interval
    socket.call_on_periodic_callback(current_time)
    assert socket.send_unicast_called[0].__dict__ == DataPacket(cid, source_name, 1, sequence=0).__dict__
    assert socket.send_unicast_called[1] == '127.0.0.1'

    # interval must be 1 seconds
    socket.call_on_periodic_callback(current_time+0.99)
    assert socket.send_unicast_called[0].__dict__ == DataPacket(cid, source_name, 1, sequence=0).__dict__
    socket.call_on_periodic_callback(current_time+1.01)
    assert socket.send_unicast_called[0].__dict__ == DataPacket(cid, source_name, 1, sequence=1).__dict__


def test_multicast():
    handler, socket, cid, source_name, outputs = get_handler()
    handler.manual_flush = False
    current_time = 100.0
    outputs[1].multicast = True
    outputs[1].ttl = 123

    assert handler.manual_flush is False
    assert socket.send_multicast_called is None
    assert outputs[1].multicast is True
    assert outputs[1].ttl == 123

    # first send packet due to interval
    socket.call_on_periodic_callback(current_time)
    assert socket.send_multicast_called[0].__dict__ == DataPacket(cid, source_name, 1, sequence=0).__dict__
    assert socket.send_multicast_called[1] == calculate_multicast_addr(1)

    # only send out on dmx change
    # test same data as before
    # TODO: currently there is no "are the values different" check.
    # If it is implemented, enable the following line:
    # outputs[1].dmx_data = (0, 0)
    socket.call_on_periodic_callback(current_time)
    assert socket.send_multicast_called[0].__dict__ == DataPacket(cid, source_name, 1, sequence=0).__dict__
    assert socket.send_multicast_called[1] == calculate_multicast_addr(1)

    # test change in data as before
    outputs[1].dmx_data = (1, 2)
    socket.call_on_periodic_callback(current_time)
    assert socket.send_multicast_called[0].__dict__ == DataPacket(cid, source_name, 1, sequence=1, dmxData=(1, 2)).__dict__
    assert socket.send_multicast_called[1] == calculate_multicast_addr(1)

    # assert that no unicast was send
    assert socket.send_unicast_called is None


def test_unicast():
    handler, socket, cid, source_name, outputs = get_handler()
    handler.manual_flush = False
    current_time = 100.0
    outputs[1].multicast = False
    destination = "1.2.3.4"
    outputs[1].destination = destination

    assert handler.manual_flush is False
    assert socket.send_unicast_called is None
    assert outputs[1].multicast is False

    # first send packet due to interval
    socket.call_on_periodic_callback(current_time)
    assert socket.send_unicast_called[0].__dict__ == DataPacket(cid, source_name, 1, sequence=0).__dict__
    assert socket.send_unicast_called[1] == destination

    # only send out on dmx change
    # test same data as before
    # TODO: currently there is no "are the values different" check.
    # If it is implemented, enable the following line:
    # outputs[1].dmx_data = (0, 0)
    socket.call_on_periodic_callback(current_time)
    assert socket.send_unicast_called[0].__dict__ == DataPacket(cid, source_name, 1, sequence=0).__dict__
    assert socket.send_unicast_called[1] == destination

    # test change in data as before
    outputs[1].dmx_data = (1, 2)
    socket.call_on_periodic_callback(current_time)
    assert socket.send_unicast_called[0].__dict__ == DataPacket(cid, source_name, 1, sequence=1, dmxData=(1, 2)).__dict__
    assert socket.send_unicast_called[1] == destination

    # assert that no multicast was send
    assert socket.send_multicast_called is None


def test_send_out_all_universes():
    handler, socket, cid, source_name, outputs = get_handler()
    handler.manual_flush = True
    current_time = 100.0
    outputs[1].multicast = False
    destination = "1.2.3.4"
    outputs[1].destination = destination

    assert handler.manual_flush is True
    assert socket.send_unicast_called is None
    assert socket.send_multicast_called is None
    assert outputs[1].multicast is False

    # check that send packets due to interval are suppressed
    socket.call_on_periodic_callback(current_time)
    assert socket.send_unicast_called is None
    assert socket.send_multicast_called is None

    # after calling send_out_all_universes, the DataPackets need to send, as well as one SyncPacket
    sync_universe = 63999
    handler.send_out_all_universes(sync_universe, outputs, current_time)
    assert socket.send_unicast_called[0].__dict__ == DataPacket(cid, source_name, 1, sequence=0, sync_universe=sync_universe).__dict__
    assert socket.send_unicast_called[1] == destination
    assert socket.send_multicast_called[0].__dict__ == SyncPacket(cid, sync_universe, 0).__dict__
    assert socket.send_multicast_called[1] == calculate_multicast_addr(sync_universe)


def test_send_out_all_universes_sequence_increment():
    handler, socket, cid, source_name, outputs = get_handler()
    handler.manual_flush = True
    current_time = 100.0
    sync_universe = 63999

    # check that the sequence number never exceeds the range [0-255]
    for i in range(0, 300):
        handler.send_out_all_universes(sync_universe, outputs, current_time)
        assert socket.send_multicast_called[0].__dict__ == SyncPacket(cid, sync_universe, (i % 256)).__dict__
