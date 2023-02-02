# This file is under MIT license. The license file can be obtained in the root directory of this module.

import pytest
from dmx.sacn.messages.universe_discovery import UniverseDiscoveryPacket
from dmx.sacn.messages.general_test import property_number_range_check


def test_constructor():
    # positive tests
    cid = tuple(range(0, 16))
    sourceName = 'Test'
    universes = tuple(range(0, 512))
    page = 0
    lastPage = 1
    packet = UniverseDiscoveryPacket(cid, sourceName, universes, page, lastPage)
    assert packet.length == 120 + (2 * len(universes))
    assert packet.cid == cid
    assert packet.sourceName == sourceName
    assert packet.universes == universes
    assert packet.page == page
    assert packet.lastPage == lastPage
    # using wrong values for CID
    with pytest.raises(ValueError):
        UniverseDiscoveryPacket(tuple(range(0, 17)), sourceName, universes)


def test_sourceName():
    # test string has 25 characters but is 64 bytes (1 too many) when UTF-8 encoded
    overlength_string = "𔑑覱֪I𤵎⠣Ķ'𫳪爓Û:𢏴㓑ò4𰬀鿹џ>𖬲膬ЩJ𞄇"
    packet = UniverseDiscoveryPacket(tuple(range(0, 16)), 'Test', ())
    # test property setter
    with pytest.raises(TypeError):
        packet.sourceName = 0x33
    with pytest.raises(ValueError):
        packet.sourceName = overlength_string
    # test constructor
    with pytest.raises(ValueError):
        packet = UniverseDiscoveryPacket(tuple(range(0, 16)), overlength_string, ())


def test_page():
    packet = UniverseDiscoveryPacket(tuple(range(0, 16)), 'Test', ())
    # test property setter
    def property(i): packet.page = i
    # test constructor for the same parameter
    def constructor(i): UniverseDiscoveryPacket(tuple(range(0, 16)), 'Test', (), i)
    property_number_range_check(0, 255, property, constructor)


def test_last_page():
    packet = UniverseDiscoveryPacket(tuple(range(0, 16)), 'Test', ())
    # test property setter
    def property(i): packet.lastPage = i
    # test constructor for the same parameter
    def constructor(i): UniverseDiscoveryPacket(tuple(range(0, 16)), 'Test', (), 0, i)
    property_number_range_check(0, 255, property, constructor)


def test_universes():
    packet = UniverseDiscoveryPacket(tuple(range(0, 16)), 'Test', ())

    def execute_universes_expect(universes: tuple):
        with pytest.raises(ValueError):
            packet.universes = universes
        with pytest.raises(ValueError):
            UniverseDiscoveryPacket(tuple(range(0, 16)), 'Test', universes)

    # test valid lengths
    for i in range(1, 513):
        universes = tuple(range(0, i))
        # test property setter
        packet.universes = universes
        assert packet.length == 120 + (2 * len(universes))
        # test constructor for the same parameter
        UniverseDiscoveryPacket(tuple(range(0, 16)), 'Test', universes)

    # test that the universes list is sorted
    packet.universes = (3, 1, 2)
    assert packet.universes == (1, 2, 3)

    # test for non-int and out of range values values in tuple
    execute_universes_expect(tuple('string'))
    execute_universes_expect(tuple(range(64000, 65000)))

    # test for tuple-length > 512
    execute_universes_expect(tuple(range(0, 513)))


def test_make_multiple_uni_disc_packets():
    # test with a list that spawns three packets
    universes = list(range(0, 1026))
    packets = UniverseDiscoveryPacket.make_multiple_uni_disc_packets(tuple(range(0, 16)), 'Test', universes)
    assert len(packets) == 3
    assert packets[0].universes == tuple(range(0, 512))
    assert packets[1].universes == tuple(range(512, 1024))
    assert packets[2].universes == tuple(range(1024, 1026))
    assert packets[0].page == 0
    assert packets[1].page == 1
    assert packets[2].page == 2
    assert packets[0].lastPage == 2
    assert packets[1].lastPage == 2
    assert packets[2].lastPage == 2
    # test with a list that spawns one packet
    universes = list(range(0, 2))
    packets = UniverseDiscoveryPacket.make_multiple_uni_disc_packets(tuple(range(0, 16)), 'Test', universes)
    assert len(packets) == 1
    assert packets[0].universes == tuple(universes)
    assert packets[0].page == 0
    assert packets[0].lastPage == 0


def test_get_bytes():
    cid = (0xef, 0x07, 0xc8, 0xdd, 0x00, 0x64, 0x44, 0x01, 0xa3, 0xa2, 0x45, 0x9e, 0xf8, 0xe6, 0x14, 0x3e)
    packet = UniverseDiscoveryPacket(cid, 'Source_A', (1, 2, 3), 0, 1)
    assert packet.getBytes() == [
        # preamble size
        0x00, 0x10,
        # postamble size
        0x00, 0x00,
        # ACN packet identifier
        0x41, 0x53, 0x43, 0x2d, 0x45, 0x31, 0x2e, 0x31, 0x37, 0x00, 0x00, 0x00,
        # flags and length
        0x70, 0x6e,
        # Root vector
        0x00, 0x00, 0x00, 0x08,
        # CID
        0xef, 0x07, 0xc8, 0xdd, 0x00, 0x64, 0x44, 0x01, 0xa3, 0xa2, 0x45, 0x9e, 0xf8, 0xe6, 0x14, 0x3e,
        # Framing flags and length
        0x70, 0x58,
        # Framing vector
        0x00, 0x00, 0x00, 0x02,
        # Source name 'Source_A'
        0x53, 0x6f, 0x75, 0x72, 0x63, 0x65, 0x5f, 0x41, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        # reserved
        0x00, 0x00, 0x00, 0x00,
        # universe discovery layer - flags and length
        0x70, 0x0e,
        # vector
        0x00, 0x00, 0x00, 0x01,
        # page
        0x00,
        # last page
        0x01,
        # universes as 16-bit integers
        0x00, 0x01, 0x00, 0x02, 0x00, 0x03,
    ]


def test_parse_sync_packet():
    raw_data = [
        # preamble size
        0x00, 0x10,
        # postamble size
        0x00, 0x00,
        # ACN packet identifier
        0x41, 0x53, 0x43, 0x2d, 0x45, 0x31, 0x2e, 0x31, 0x37, 0x00, 0x00, 0x00,
        # flags and length
        0x70, 0x6e,
        # Root vector
        0x00, 0x00, 0x00, 0x08,
        # CID
        0xef, 0x07, 0xc8, 0xdd, 0x00, 0x64, 0x44, 0x01, 0xa3, 0xa2, 0x45, 0x9e, 0xf8, 0xe6, 0x14, 0x3e,
        # Framing flags and length
        0x70, 0x58,
        # Framing vector
        0x00, 0x00, 0x00, 0x02,
        # Source name 'Source_A'
        0x53, 0x6f, 0x75, 0x72, 0x63, 0x65, 0x5f, 0x41, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        # reserved
        0x00, 0x00, 0x00, 0x00,
        # universe discovery layer - flags and length
        0x70, 0x0e,
        # vector
        0x00, 0x00, 0x00, 0x01,
        # page
        0x00,
        # last page
        0x01,
        # universes as 16-bit integers
        0x00, 0x01, 0x00, 0x02, 0x00, 0x03,
    ]
    packet = UniverseDiscoveryPacket.make_universe_discovery_packet(raw_data)
    assert packet.length == 126
    assert packet.cid == (0xef, 0x07, 0xc8, 0xdd, 0x00, 0x64, 0x44, 0x01, 0xa3, 0xa2, 0x45, 0x9e, 0xf8, 0xe6, 0x14, 0x3e)
    assert packet.sourceName == 'Source_A'
    assert packet.page == 0
    assert packet.lastPage == 1
    assert packet.universes == (1, 2, 3)

    # test for invalid data
    # test for too short data arrays
    for i in range(1, 120):
        with pytest.raises(TypeError):
            UniverseDiscoveryPacket.make_universe_discovery_packet([x % 256 for x in range(0, i)])
    # test for invalid vectors
    with pytest.raises(TypeError):
        UniverseDiscoveryPacket.make_universe_discovery_packet([x % 256 for x in range(0, 126)])
    # test for odd universes list length
    raw_data = raw_data[0:len(raw_data) - 1]
    with pytest.raises(TypeError):
        UniverseDiscoveryPacket.make_universe_discovery_packet(raw_data)


def test_byte_construction_and_deconstruction():
    built_packet = UniverseDiscoveryPacket(tuple(range(0, 16)), 'Test', tuple(range(0, 512)), 0, 1)
    read_packet = UniverseDiscoveryPacket.make_universe_discovery_packet(built_packet.getBytes())
    assert built_packet == read_packet
