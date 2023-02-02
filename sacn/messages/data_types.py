# This file is under MIT license. The license file can be obtained in the root directory of this module.

"""
This file includes custom types for the usage in sACN packets.
"""


class CID:
    """
    CID stores a special case of a tuple that must have a length of 16 byte elements.
    """

    def __init__(self, cid: tuple):
        self.value = cid

    @property
    def value(self) -> tuple:
        return self._cid

    @value.setter
    def value(self, cid: tuple):
        if type(cid) is not tuple:
            raise TypeError(f'cid must be a 16 byte tuple! value was {cid}')
        if (len(cid) != 16 or not all((isinstance(x, int) and (0 <= x <= 255)) for x in cid)):
            raise ValueError(f'cid must be a 16 byte tuple! value was {cid}')
        self._cid = cid

    def __eq__(self, other: 'CID') -> bool:
        return self.value == other.value
