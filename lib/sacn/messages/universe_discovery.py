"""
This class represents an universe discovery packet of the E1.31 Standard.
"""
from typing import List

from dmx.sacn.messages.root_layer import \
    VECTOR_ROOT_E131_EXTENDED, \
    VECTOR_E131_EXTENDED_DISCOVERY, \
    VECTOR_UNIVERSE_DISCOVERY_UNIVERSE_LIST,\
    RootLayer, \
    int_to_bytes, \
    byte_tuple_to_int, \
    make_flagsandlength


class UniverseDiscoveryPacket(RootLayer):
    def __init__(self, cid: tuple, sourceName: str, universes: tuple, page: int = 0, lastPage: int = 0):
        self.sourceName: str = sourceName
        self.page: int = page
        self.lastPage: int = lastPage
        self.universes: tuple = universes
        super().__init__((len(universes) * 2) + 120, cid, VECTOR_ROOT_E131_EXTENDED)

    @property
    def sourceName(self) -> str:
        return self._sourceName

    @sourceName.setter
    def sourceName(self, sourceName: str):
        if type(sourceName) is not str:
            raise TypeError(f'sourceName must be a string! Type was {type(sourceName)}')
        tmp_sourceName_length = len(str(sourceName).encode('UTF-8'))
        if tmp_sourceName_length > 63:
            raise ValueError(f'sourceName must be less than 64 bytes when UTF-8 encoded! "{sourceName}" is {tmp_sourceName_length} bytes')
        self._sourceName = sourceName

    @property
    def page(self) -> int:
        return self._page

    @page.setter
    def page(self, page: int):
        if type(page) is not int:
            raise TypeError(f'Page must be an integer! Type was {type(page)}')
        if page not in range(0, 256):
            raise ValueError(f'Page is a byte! values: [0-255]! value was {page}')
        self._page = page

    @property
    def lastPage(self) -> int:
        return self._lastPage

    @lastPage.setter
    def lastPage(self, lastPage: int):
        if type(lastPage) is not int:
            raise TypeError(f'lastPage must be an integer! Type was {type(lastPage)}')
        if lastPage not in range(0, 256):
            raise ValueError(f'lastPage is a byte! values: [0-255]! value was {lastPage}')
        self._lastPage = lastPage

    @property
    def universes(self) -> tuple:
        return tuple(self._universes)

    @universes.setter
    def universes(self, universes: tuple):
        if len(universes) > 512 or \
                not all((isinstance(x, int) and (0 <= x <= 63999)) for x in universes):
            raise ValueError(f'Universes is a tuple with a max length of 512! The data in the tuple has to be valid universe numbers! '
                             f'Length was {len(universes)}')
        self._universes = sorted(universes)
        self.length = 120 + (len(universes) * 2)  # generate new length value for the packet

    def getBytes(self) -> list:
        rtrnList = super().getBytes()
        # Flags and Length Framing Layer:--------------------
        rtrnList.extend(make_flagsandlength(self.length - 38))
        # Vector Framing Layer:------------------------------
        rtrnList.extend(VECTOR_E131_EXTENDED_DISCOVERY)
        # source Name Framing Layer:-------------------------
        # sourceName:---------------------------
        # UTF-8 encode the string
        tmpSourceName = str(self._sourceName).encode('UTF-8')
        rtrnList.extend(tmpSourceName)
        # pad to 64 bytes
        rtrnList.extend([0] * (64 - len(tmpSourceName)))
        # reserved fields:-----------------------------------
        rtrnList.extend([0] * 4)
        # Universe Discovery Layer:-------------------------------------
        # Flags and Length:----------------------------------
        rtrnList.extend(make_flagsandlength(self.length - 112))
        # Vector UDL:----------------------------------------
        rtrnList.extend(VECTOR_UNIVERSE_DISCOVERY_UNIVERSE_LIST)
        # page:----------------------------------------------
        rtrnList.append(self._page & 0xFF)
        # last page:-----------------------------------------
        rtrnList.append(self._lastPage & 0xFF)
        # universes:-----------------------------------------
        for universe in self._universes:  # universe is a 16-bit number!
            rtrnList.extend(int_to_bytes(universe))

        return rtrnList

    @staticmethod
    def make_universe_discovery_packet(raw_data) -> 'UniverseDiscoveryPacket':
        # Check if the length is sufficient
        if len(raw_data) < 120:
            raise TypeError('The length of the provided data is not long enough! Min length is 120!')
        # Check if the three Vectors are correct
        # REMEMBER: when slicing: [inclusive:exclusive]
        if tuple(raw_data[18:22]) != tuple(VECTOR_ROOT_E131_EXTENDED) or \
           tuple(raw_data[40:44]) != tuple(VECTOR_E131_EXTENDED_DISCOVERY) or \
           tuple(raw_data[114:118]) != tuple(VECTOR_UNIVERSE_DISCOVERY_UNIVERSE_LIST):
            raise TypeError('Some of the vectors in the given raw data are not compatible to the E131 Standard!')

        # tricky part: convert plain bytes to a useful list of 16-bit values for further use
        # Problem: the given raw_byte can be longer than the dynamic length of the list of universes
        # first: extract the length from the Universe Discovery Layer (UDL)
        length = (byte_tuple_to_int((raw_data[112], raw_data[113])) & 0xFFF) - 8
        # remember: UDL has 8 bytes plus the universes
        # remember: Flags and length includes a 12-bit length field
        universes = convert_raw_data_to_universes(raw_data[120:120 + length])
        tmpPacket = UniverseDiscoveryPacket(cid=tuple(raw_data[22:38]), sourceName=bytes(raw_data[44:108]).decode('utf-8').replace('\0', ''),
                                            universes=universes)
        tmpPacket._page = raw_data[118]
        tmpPacket._lastPage = raw_data[119]
        return tmpPacket

    @staticmethod
    def make_multiple_uni_disc_packets(cid: tuple, sourceName: str, universes: list) -> List['UniverseDiscoveryPacket']:
        """
        Creates a list with universe discovery packets based on the given data. It creates automatically enough packets
        for the given universes list.
        :param cid: the cid to use in all packets
        :param sourceName: the source name to use in all packets
        :param universes: the universes. Can be longer than 512, but has to be shorter than 256*512.
        The values in the list should be [1-63999]
        :return: a list full of universe discovery packets
        """
        tmpList = []
        # divide len(universes) with 512 and round up; // is integer division
        num_of_packets = (len(universes) + 512 - 1) // 512
        universes.sort()  # E1.31 wants that the send out universes are sorted
        for i in range(0, num_of_packets):
            if i == num_of_packets - 1:
                tmpUniverses = universes[i * 512:len(universes)]
                # if we are here, then the for is in the last loop
            else:
                tmpUniverses = universes[i * 512:(i + 1) * 512]
            # create new UniverseDiscoveryPacket and append it to the list. Page and lastPage are getting special values
            tmpList.append(UniverseDiscoveryPacket(cid=cid, sourceName=sourceName, universes=tmpUniverses,
                                                   page=i, lastPage=num_of_packets - 1))
        return tmpList


def convert_raw_data_to_universes(raw_data) -> tuple:
    """
    converts the raw data to a readable universes tuple. The raw_data is scanned from index 0 and has to have
    16-bit numbers with high byte first. The data is converted from the start to the beginning!
    :param raw_data: the raw data to convert
    :return: tuple full with 16-bit numbers
    """
    if len(raw_data) % 2 != 0:
        raise TypeError('The given data does not have an even number of elements!')
    rtrnList = []
    for i in range(0, len(raw_data), 2):
        rtrnList.append(byte_tuple_to_int((raw_data[i], raw_data[i + 1])))
    return tuple(rtrnList)
