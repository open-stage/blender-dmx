# This file is under MIT license. The license file can be obtained in the root directory of this module.

import pytest
import sacn
from dmx.sacn.sender import check_universe
from dmx.sacn.messages.data_packet import DataPacket
from dmx.sacn.sending.sender_socket_test import SenderSocketTest


def test_constructor():
    cid = tuple(range(0, 16))
    source_name = 'test'
    socket = SenderSocketTest()

    # test default values for constructor
    sender = sacn.sACNsender(socket=socket)
    assert sender._sender_handler._source_name == 'default source name'
    assert len(sender._sender_handler._CID) == 16
    assert sender.universeDiscovery is True
    assert sender._sync_universe == 63999
    assert sender.manual_flush is False

    # test explicit values for constructor
    bind_address = 'test_address'
    bind_port = 1234
    fps = 40
    universe_discovery = False
    sync_universe = 4567
    sender = sacn.sACNsender(bind_address, bind_port, source_name, cid, fps, universe_discovery, sync_universe, socket)
    assert sender._sender_handler._source_name == source_name
    assert sender._sender_handler._CID == cid
    assert sender.universeDiscovery == universe_discovery
    assert sender._sync_universe == sync_universe
    assert sender.manual_flush is False


def test_universe_discovery_setting():
    socket = SenderSocketTest()
    sender = sacn.sACNsender(socket=socket)
    assert sender.universeDiscovery is True
    assert sender._sender_handler.universe_discovery is True
    sender.universeDiscovery = False
    assert sender.universeDiscovery is False
    assert sender._sender_handler.universe_discovery is False


def test_manual_flush_setting():
    socket = SenderSocketTest()
    sender = sacn.sACNsender(socket=socket)
    assert sender.manual_flush is False
    assert sender._sender_handler.manual_flush is False
    sender.manual_flush = True
    assert sender.manual_flush is True
    assert sender._sender_handler.manual_flush is True


def test_flush():
    socket = SenderSocketTest()
    sync_universe = 1234
    sender = sacn.sACNsender(sync_universe=sync_universe, socket=socket)

    assert socket.send_unicast_called is None
    # test that non-active universes throw exception
    with pytest.raises(ValueError):
        sender.flush([1, 2])

    assert socket.send_unicast_called is None
    # test that no active universes triggers nothing
    sender.flush()
    assert socket.send_unicast_called is None

    # activate universe 1
    sender.activate_output(1)
    assert socket.send_unicast_called is None
    # test that no parameters triggers flushing of all universes
    sender.flush()
    assert socket.send_unicast_called[0].__dict__ == DataPacket(
        sender._sender_handler._CID, sender._sender_handler._source_name, 1, sync_universe=sync_universe).__dict__

    # activate universe 2
    sender.activate_output(2)
    # test that a list with only universe 1 triggers flushing of only this universe
    sender.flush([1])
    assert socket.send_unicast_called[0].__dict__ == DataPacket(
        sender._sender_handler._CID, sender._sender_handler._source_name, 1, sequence=1, sync_universe=sync_universe).__dict__


def test_activate_output():
    socket = SenderSocketTest()
    sender = sacn.sACNsender(socket=socket)

    # start with no universes active
    assert list(sender._outputs.keys()) == []

    # activate one universe
    sender.activate_output(1)
    assert list(sender._outputs.keys()) == [1]

    # activate another universe
    sender.activate_output(63999)
    assert list(sender._outputs.keys()) == [1, 63999]

    # check that a universe can not be enabled twice
    sender.activate_output(1)
    assert list(sender._outputs.keys()) == [1, 63999]


def test_deactivate_output():
    socket = SenderSocketTest()
    sender = sacn.sACNsender(socket=socket)

    # check that three packets with stream-termination bit set are send out on deactivation
    sender.activate_output(100)
    assert socket.send_unicast_called is None
    sender.deactivate_output(100)
    assert socket.send_unicast_called[0].__dict__ == DataPacket(
        sender._sender_handler._CID, sender._sender_handler._source_name, 100, sequence=2, streamTerminated=True).__dict__

    # start with no universes active
    assert list(sender._outputs.keys()) == []
    sender.deactivate_output(1)
    assert list(sender._outputs.keys()) == []

    # one universe active
    sender.activate_output(1)
    assert list(sender._outputs.keys()) == [1]
    sender.deactivate_output(1)
    assert list(sender._outputs.keys()) == []

    # two universes active
    sender.activate_output(10)
    sender.activate_output(11)
    assert list(sender._outputs.keys()) == [10, 11]
    sender.deactivate_output(10)
    assert list(sender._outputs.keys()) == [11]

    # deactivate no active universe
    assert list(sender._outputs.keys()) == [11]
    sender.deactivate_output(99)
    assert list(sender._outputs.keys()) == [11]


def test_get_active_outputs():
    socket = SenderSocketTest()
    sender = sacn.sACNsender(socket=socket)

    # none active
    assert sender.get_active_outputs() == tuple([])

    # one active
    sender.activate_output(1)
    assert sender.get_active_outputs() == tuple([1])

    # two active
    sender.activate_output(2)
    assert sender.get_active_outputs() == tuple([1, 2])


def test_move_universe():
    socket = SenderSocketTest()
    sender = sacn.sACNsender(socket=socket)

    sender.activate_output(1)
    output = sender._outputs[1]
    assert list(sender._outputs.keys()) == [1]
    assert sender._outputs[1] == output
    sender.move_universe(1, 2)
    assert list(sender._outputs.keys()) == [2]
    assert sender._outputs[2] == output


def test_getitem():
    socket = SenderSocketTest()
    sender = sacn.sACNsender(socket=socket)

    assert sender[1] is None
    sender.activate_output(1)
    assert sender[1] == sender._outputs[1]


def test_start():
    socket = SenderSocketTest()
    sender = sacn.sACNsender(socket=socket)

    assert socket.start_called is False
    sender.start()
    assert socket.start_called is True

    # a second time is not allowed to throw an exception
    assert socket.start_called is True
    sender.start()
    assert socket.start_called is True


def test_stop():
    socket = SenderSocketTest()
    sender = sacn.sACNsender(socket=socket)

    assert socket.stop_called is False
    sender.stop()
    assert socket.stop_called is True

    # a second time is not allowed to throw an exception
    assert socket.stop_called is True
    sender.stop()
    assert socket.stop_called is True


def test_output_destination():
    socket = SenderSocketTest()
    sender = sacn.sACNsender(socket=socket)
    sender.activate_output(1)

    # test default
    assert sender[1].destination == '127.0.0.1'
    # test setting and retriving the value
    test = 'test'
    sender[1].destination = test
    assert sender[1].destination == test


def test_output_multicast():
    socket = SenderSocketTest()
    sender = sacn.sACNsender(socket=socket)
    sender.activate_output(1)

    # test default
    assert sender[1].multicast is False
    # test setting and retriving the value
    test = True
    sender[1].multicast = test
    assert sender[1].multicast == test


def test_output_ttl():
    socket = SenderSocketTest()
    sender = sacn.sACNsender(socket=socket)
    sender.activate_output(1)

    # test default
    assert sender[1].ttl == 8
    # test setting and retriving the value
    test = 16
    sender[1].ttl = test
    assert sender[1].ttl == test


def test_output_priority():
    socket = SenderSocketTest()
    sender = sacn.sACNsender(socket=socket)
    sender.activate_output(1)

    # test default
    assert sender[1].priority == 100
    # test setting and retriving the value
    test = 200
    sender[1].priority = test
    assert sender[1].priority == test


def test_output_preview_data():
    socket = SenderSocketTest()
    sender = sacn.sACNsender(socket=socket)
    sender.activate_output(1)

    # test default
    assert sender[1].preview_data is False
    # test setting and retriving the value
    test = True
    sender[1].preview_data = test
    assert sender[1].preview_data == test


def test_output_dmx_data():
    socket = SenderSocketTest()
    sender = sacn.sACNsender(socket=socket)
    sender.activate_output(1)

    # test default
    assert sender[1].dmx_data == tuple([0]*512)
    # test setting and retriving the value
    test = tuple([x % 256 for x in range(0, 512)])
    sender[1].dmx_data = test
    assert sender[1].dmx_data == test


def test_check_universe():
    with pytest.raises(ValueError):
        check_universe(0)
    with pytest.raises(ValueError):
        check_universe(64000)
    check_universe(1)
    check_universe(63999)
