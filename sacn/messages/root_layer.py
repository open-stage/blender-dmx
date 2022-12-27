# This file is under MIT license. The license file can be obtained in the root directory of this module.


"""
This represents a root layer of an ACN Message.
Information about sACN: http://tsp.esta.org/tsp/documents/docs/E1-31-2016.pdf
"""

_FIRST_INDEX = \
    (0, 0x10, 0, 0, 0x41, 0x53, 0x43, 0x2d, 0x45,
     0x31, 0x2e, 0x31, 0x37, 0x00, 0x00, 0x00)

VECTOR_E131_DATA_PACKET = (0, 0, 0, 0x02)
VECTOR_DMP_SET_PROPERTY = 0x02
VECTOR_ROOT_E131_DATA = (0, 0, 0, 0x4)

VECTOR_ROOT_E131_EXTENDED = (0, 0, 0, 0x8)

VECTOR_E131_EXTENDED_SYNCHRONIZATION = (0, 0, 0, 0x1)
VECTOR_E131_EXTENDED_DISCOVERY = (0, 0, 0, 0x2)
VECTOR_UNIVERSE_DISCOVERY_UNIVERSE_LIST = (0, 0, 0, 0x1)


class RootLayer:
    def __init__(self, length: int, cid: tuple, vector: tuple):
        self.length = length
        if (len(vector) != 4):
            raise ValueError('the length of the vector is not 4!')
        self._vector = vector
        self.cid = cid

    def getBytes(self) -> list:
        '''Returns the Root layer as list with bytes'''
        tmpList = []
        tmpList.extend(_FIRST_INDEX)
        # first append the high byte from the Flags and Length
        # high 4 bit: 0x7 then the bits 8-11(indexes) from _length
        length = self.length - 16
        tmpList.extend(make_flagsandlength(length))

        tmpList.extend(self._vector)
        tmpList.extend(self._cid)
        return tmpList

    @property
    def length(self) -> int:
        return self._length

    @length.setter
    def length(self, value: int):
        self._length = value & 0xFFF  # only use the least 12-Bit

    @property
    def cid(self) -> tuple:
        return self._cid

    @cid.setter
    def cid(self, cid: tuple):
        if type(cid) is not tuple:
            raise TypeError(f'cid must be a 16 byte tuple! value was {cid}')
        if (len(cid) != 16 or not all((isinstance(x, int) and (0 <= x <= 255)) for x in cid)):
            raise ValueError(f'cid must be a 16 byte tuple! value was {cid}')
        self._cid = cid

    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False
        return self.__dict__ == other.__dict__


def int_to_bytes(integer_value: int) -> list:
    """
    Converts a single integer number to an list with the length 2 with highest
    byte first.
    The returned list contains values in the range [0-255]
    :param integer: the integer to convert
    :return: the list with the high byte first
    """
    if not (isinstance(integer_value, int) and 0 <= integer_value <= 65535):
        raise ValueError(f'integer_value to be packed must be unsigned short: [0-65535]! value was {integer_value}')
    return [(integer_value >> 8) & 0xFF, integer_value & 0xFF]


def byte_tuple_to_int(in_tuple: tuple) -> int:
    """
    Converts two element byte tuple (highest first) to integer.
    :param in_tuple: the integer to convert
    :return: the integer value
    """
    if ((len(in_tuple) != 2) or not all(isinstance(x, int) for x in in_tuple) or not all(0 <= x <= 255 for x in in_tuple)):
        raise ValueError(f'in_tuple must be a two byte tuple! value was {in_tuple}')
    return int((in_tuple[0] << 8) + in_tuple[1])


def make_flagsandlength(in_length: int) -> list:
    """
    Converts a length value in a Flags and Length list with two bytes in the
    correct order.
    :param length: the length to convert. should be 12-bit value
    :return: the list with the two bytes
    """
    if (in_length > 0xFFF):
        raise ValueError(f'length must be no greater than a 12-bit value! value was {in_length}')
    return [(0x7 << 4) + ((in_length & 0xF00) >> 8), in_length & 0xFF]
