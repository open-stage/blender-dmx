# This file is under MIT license. The license file can be obtained in the root directory of this module.

import pytest
from dmx.sacn.messages.sync_packet import SyncPacket
from dmx.sacn.messages.general_test import property_number_range_check


def test_constructor():
    # positive tests
    cid = tuple(range(0, 16))
    syncAddr = 12
    sequence = 127
    packet = SyncPacket(cid, syncAddr, sequence)
    assert packet.length == 49
    assert packet.cid == cid
    assert packet.syncAddr == syncAddr
    assert packet.sequence == sequence
    # using wrong values for CID
    with pytest.raises(ValueError):
        SyncPacket(tuple(range(0, 17)), syncAddr, sequence)


def test_sync_universe():
    packet = SyncPacket(tuple(range(0, 16)), 1, 1)
    # test property setter
    def property(i): packet.syncAddr = i
    # test constructor for the same parameter
    def constructor(i): SyncPacket(tuple(range(0, 16)), i, 1)
    property_number_range_check(1, 63999, property, constructor)


def test_sequence():
    packet = SyncPacket(tuple(range(0, 16)), 1, 1)
    # test property setter
    def property(i): packet.sequence = i
    # test constructor for the same parameter
    def constructor(i): SyncPacket(tuple(range(0, 16)), 1, i)
    property_number_range_check(0, 255, property, constructor)


def test_sequence_increment():
    # Test that the sequence number can be increased and the wrap around at 255 is correct
    built_packet = SyncPacket(tuple(range(0, 16)), 1, 1)
    built_packet.sequence = 78
    built_packet.sequence_increase()
    assert built_packet.sequence == 79
    built_packet.sequence = 255
    built_packet.sequence_increase()
    assert built_packet.sequence == 0


def test_get_bytes():
    # Use the example present in the E1.31 spec in appendix B
    cid = (0xef, 0x07, 0xc8, 0xdd, 0x00, 0x64, 0x44, 0x01, 0xa3, 0xa2, 0x45, 0x9e, 0xf8, 0xe6, 0x14, 0x3e)
    syncAddr = 7962
    sequence = 67  # Note: the spec states 367, which is a mistake in the spec
    packet = SyncPacket(cid, syncAddr, sequence)
    assert packet.getBytes() == [
        # preamble size
        0x00, 0x10,
        # postamble size
        0x00, 0x00,
        # ACN packet identifier
        0x41, 0x53, 0x43, 0x2d, 0x45, 0x31, 0x2e, 0x31, 0x37, 0x00, 0x00, 0x00,
        # flags and length; again a mistake in the E1.31 spec, as this states '0x70, 0x30'
        # this would violate the parent spec E1.17 (ACN) section 2.4.2
        0x70, 0x21,
        # Root vector
        0x00, 0x00, 0x00, 0x08,
        # CID
        0xef, 0x07, 0xc8, 0xdd, 0x00, 0x64, 0x44, 0x01, 0xa3, 0xa2, 0x45, 0x9e, 0xf8, 0xe6, 0x14, 0x3e,
        # Framing flags and length; again propably a mistake as with the flags and length above
        0x70, 0x0b,
        # Framing vector
        0x00, 0x00, 0x00, 0x01,
        # sequence number
        0x43,
        # sync address
        0x1f, 0x1a,
        # reserved fields
        0x00, 0x00,
    ]


def test_parse_sync_packet():
    # Use the example present in the E1.31 spec in appendix B
    raw_data = [
        # preamble size
        0x00, 0x10,
        # postamble size
        0x00, 0x00,
        # ACN packet identifier
        0x41, 0x53, 0x43, 0x2d, 0x45, 0x31, 0x2e, 0x31, 0x37, 0x00, 0x00, 0x00,
        # flags and length; again a mistake in the E1.31 spec, as this states '0x70, 0x30'
        # this would violate the parent spec E1.17 (ACN) section 2.4.2
        0x70, 0x21,
        # Root vector
        0x00, 0x00, 0x00, 0x08,
        # CID
        0xef, 0x07, 0xc8, 0xdd, 0x00, 0x64, 0x44, 0x01, 0xa3, 0xa2, 0x45, 0x9e, 0xf8, 0xe6, 0x14, 0x3e,
        # Framing flags and length; again propably a mistake as with the flags and length above
        0x70, 0x0b,
        # Framing vector
        0x00, 0x00, 0x00, 0x01,
        # sequence number
        0x43,
        # sync address
        0x1f, 0x1a,
        # reserved fields
        0x00, 0x00,
    ]
    packet = SyncPacket.make_sync_packet(raw_data)
    assert packet.length == 49
    assert packet.cid == (0xef, 0x07, 0xc8, 0xdd, 0x00, 0x64, 0x44, 0x01, 0xa3, 0xa2, 0x45, 0x9e, 0xf8, 0xe6, 0x14, 0x3e)
    assert packet.sequence == 67
    assert packet.syncAddr == 7962

    # test for invalid data
    # test for too short data arrays
    for i in range(1, 47):
        with pytest.raises(TypeError):
            SyncPacket.make_sync_packet([x % 256 for x in range(0, i)])
    # test for invalid vectors
    with pytest.raises(TypeError):
        SyncPacket.make_sync_packet([x % 256 for x in range(0, 47)])


def test_byte_construction_and_deconstruction():
    built_packet = SyncPacket(tuple(range(0, 16)), 12, 127)
    read_packet = SyncPacket.make_sync_packet(built_packet.getBytes())
    assert built_packet == read_packet
