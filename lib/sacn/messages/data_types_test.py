# This file is under MIT license. The license file can be obtained in the root directory of this module.


import pytest
from typing import Any, Callable
from dmx.sacn.messages.data_types import CID


def create_valid_cid() -> CID:
    return CID(tuple(range(0, 16)))


def cid_failing_test_cases(apply_to: Callable[[Any], None]):
    def char_range(char1, char2):
        """Generates the characters from `c1` to `c2`, ranged just like python."""
        for c in range(ord(char1), ord(char2)):
            yield chr(c)

    # test that constructor validates cid
    with pytest.raises(ValueError):
        apply_to(tuple(char_range('A', 'Q')))
    # test that CID must be 16 elements
    with pytest.raises(ValueError):
        apply_to(tuple(range(0, 17)))
    with pytest.raises(ValueError):
        apply_to(tuple(range(0, 15)))
    # test that CID only contains valid byte values
    with pytest.raises(ValueError):
        apply_to(tuple(range(250, 266)))
    with pytest.raises(ValueError):
        apply_to(tuple(char_range('b', 'r')))
    # test that CID is a tuple
    with pytest.raises(TypeError):
        apply_to(range(0, 16))


def test_cid_constructor():
    # normal values must work
    tuple1 = tuple(range(0, 16))
    tuple2 = tuple(range(1, 17))
    cid1 = CID(tuple1)
    cid2 = CID(tuple2)
    assert cid1.value == tuple1
    assert cid2.value == tuple2

    def apply_constructor(value) -> None:
        CID(value)

    cid_failing_test_cases(apply_constructor)


def test_cid_setter():
    tuple1 = tuple(range(0, 16))
    tuple2 = tuple(range(1, 17))

    cid = CID(tuple(range(2, 18)))
    # normal values must work
    cid.value = tuple1
    assert cid.value == tuple1
    cid.value = tuple2
    assert cid.value == tuple2

    def apply_setter(value) -> None:
        cid.value = value

    cid_failing_test_cases(apply_setter)


def test_cid_equals():
    tuple1 = tuple(range(0, 16))
    tuple2 = tuple(range(0, 16))

    cid1 = CID(tuple1)
    cid2 = CID(tuple2)
    assert cid1 == cid2
