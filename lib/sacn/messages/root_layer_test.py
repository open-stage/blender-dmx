# This file is under MIT license. The license file can be obtained in the root directory of this module.

import pytest
from dmx.sacn.messages.root_layer import \
    byte_tuple_to_int, \
    int_to_bytes, \
    make_flagsandlength, \
    RootLayer


def test_int_to_bytes():
    assert int_to_bytes(0xFFFF) == [0xFF, 0xFF]
    assert int_to_bytes(0x1234) == [0x12, 0x34]
    # test that the value cannot exceed two bytes
    with pytest.raises(ValueError):
        int_to_bytes(0x123456)
    assert int_to_bytes(0x0001) == [0x00, 0x01]


def test_byte_tuple_to_int():
    assert byte_tuple_to_int((0x00, 0x00)) == 0x0000
    assert byte_tuple_to_int((0xFF, 0xFF)) == 0xFFFF
    assert byte_tuple_to_int((0x12, 0x34)) == 0x1234
    # test different length of tuples
    with pytest.raises(ValueError):
        byte_tuple_to_int(())
    with pytest.raises(TypeError):
        byte_tuple_to_int(1)
    with pytest.raises(ValueError):
        byte_tuple_to_int((1, 2, 3))
    with pytest.raises(ValueError):
        byte_tuple_to_int((1, 'string'))
    with pytest.raises(ValueError):
        byte_tuple_to_int((1, 500))


def test_eq():
    cid = tuple(range(0, 16))
    cid2 = tuple(range(1, 17))
    vec = tuple(range(0, 4))
    vec2 = tuple(range(1, 5))
    assert RootLayer(0, cid, vec) == RootLayer(0, cid, vec)
    assert RootLayer(0, cid, vec) != RootLayer(1, cid, vec)
    assert RootLayer(0, cid, vec) != RootLayer(0, cid, vec2)
    assert RootLayer(0, cid, vec) != RootLayer(0, cid2, vec)
    assert (RootLayer(0, cid, vec) == (1, 2, 3)) is False


def test_make_flagsandlength():
    assert make_flagsandlength(0x123) == [0x71, 0x23]
    with pytest.raises(ValueError):
        assert make_flagsandlength(0x1234) == [0x72, 0x34]
    assert make_flagsandlength(0x001) == [0x70, 0x01]


def test_cid():
    cid1 = tuple(range(0, 16))
    cid2 = tuple(range(1, 17))
    vector1 = (1, 2, 3, 4)

    def char_range(char1, char2):
        """Generates the characters from `c1` to `c2`, ranged just like python."""
        for c in range(ord(char1), ord(char2)):
            yield chr(c)

    # test constructor
    packet = RootLayer(123, cid1, vector1)
    assert packet.cid == cid1
    packet.cid = cid2
    assert packet.cid == cid2
    # test that constructor validates cid
    with pytest.raises(ValueError):
        RootLayer(length=123, cid=tuple(char_range('A', 'Q')), vector=vector1)
    # test that CID must be 16 elements
    with pytest.raises(ValueError):
        packet.cid = tuple(range(0, 17))
    with pytest.raises(ValueError):
        packet.cid = tuple(range(0, 15))
    # test that CID only contains valid byte values
    with pytest.raises(ValueError):
        packet.cid = tuple(range(250, 266))
    with pytest.raises(ValueError):
        packet.cid = tuple(char_range('b', 'r'))
    # test that CID is a tuple
    with pytest.raises(TypeError):
        packet.cid = range(0, 16)


def test_root_layer_bytes():
    cid = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16)
    vector = (1, 2, 3, 4)
    # test that the vector length must be 4
    with pytest.raises(ValueError):
        RootLayer(0, cid, ())
    # test that the cid length must be 16
    with pytest.raises(ValueError):
        RootLayer(0, (), vector)
    packet = RootLayer(0x123456, cid, vector)
    shouldBe = [
        # initial static vector
        0, 0x10, 0, 0, 0x41, 0x53, 0x43, 0x2d, 0x45,
        0x31, 0x2e, 0x31, 0x37, 0x00, 0x00, 0x00,
        # length value
        0x74, 0x46
    ]
    # vector
    shouldBe.extend(vector)
    # cid
    shouldBe.extend(cid)
    assert packet.getBytes() == shouldBe


def test_int_byte_transitions():
    # test the full 0-65534 range, though only using 0-63999 currently
    for input_i in range(65536):
        converted_i = byte_tuple_to_int(tuple(int_to_bytes(input_i)))
        assert input_i == converted_i
