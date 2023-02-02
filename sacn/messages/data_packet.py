# This file is under MIT license. The license file can be obtained in the root directory of this module.

"""
This represents a framing layer and a DMP layer from the E1.31 Standard
Information about sACN: http://tsp.esta.org/tsp/documents/docs/E1-31-2016.pdf
"""

from dmx.sacn.messages.root_layer import \
    VECTOR_DMP_SET_PROPERTY, \
    VECTOR_E131_DATA_PACKET, \
    VECTOR_ROOT_E131_DATA, \
    RootLayer, \
    int_to_bytes, \
    byte_tuple_to_int, \
    make_flagsandlength


class DataPacket(RootLayer):
    def __init__(self, cid: tuple, sourceName: str, universe: int, dmxData: tuple = (), priority: int = 100,
                 sequence: int = 0, streamTerminated: bool = False, previewData: bool = False,
                 forceSync: bool = False, sync_universe: int = 0, dmxStartCode: int = 0x00):
        super().__init__(126 + len(dmxData), cid, VECTOR_ROOT_E131_DATA)
        self.sourceName: str = sourceName
        self.priority = priority
        self.syncAddr = sync_universe
        self.universe = universe
        self.option_StreamTerminated: bool = streamTerminated
        self.option_PreviewData: bool = previewData
        self.option_ForceSync: bool = forceSync
        self.sequence = sequence
        self.dmxStartCode = dmxStartCode
        self.dmxData = dmxData

    def __str__(self):
        return f'sACN DataPacket: Universe: {self._universe}, Priority: {self._priority}, Sequence: {self._sequence}, ' \
               f'CID: {self._cid}'

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
    def priority(self) -> int:
        return self._priority

    @priority.setter
    def priority(self, priority: int):
        if type(priority) is not int:
            raise TypeError(f'priority must be an integer! Type was {type(priority)}')
        if priority not in range(0, 201):
            raise ValueError(f'priority must be in range [0-200]! value was {priority}')
        self._priority = priority

    @property
    def universe(self) -> int:
        return self._universe

    @universe.setter
    def universe(self, universe: int):
        if type(universe) is not int:
            raise TypeError(f'universe must be an integer! Type was {type(universe)}')
        if universe not in range(1, 64000):
            raise ValueError(f'universe must be [1-63999]! value was {universe}')
        self._universe = universe

    @property
    def syncAddr(self) -> int:
        return self._syncAddr

    @syncAddr.setter
    def syncAddr(self, sync_universe: int):
        if type(sync_universe) is not int:
            raise TypeError(f'sync_universe must be an integer! Type was {type(sync_universe)}')
        if sync_universe not in range(0, 64000):
            raise ValueError(f'sync_universe must be [1-63999]! value was {sync_universe}')
        self._syncAddr = sync_universe

    @property
    def sequence(self) -> int:
        return self._sequence

    @sequence.setter
    def sequence(self, sequence: int):
        if type(sequence) is not int:
            raise TypeError(f'sequence must be an integer! Type was {type(sequence)}')
        if sequence not in range(0, 256):
            raise ValueError(f'sequence is a byte! values: [0-255]! value was {sequence}')
        self._sequence = sequence

    def sequence_increase(self):
        self._sequence += 1
        if self._sequence > 0xFF:
            self._sequence = 0

    @property
    def dmxStartCode(self) -> int:
        return self._dmxStartCode

    @dmxStartCode.setter
    def dmxStartCode(self, dmxStartCode: int):
        """
        DMX start code values: 0x00 for level data; 0xDD for per address priority data
        """
        if type(dmxStartCode) is not int:
            raise TypeError(f'dmx start code must be an integer! Type was {type(dmxStartCode)}')
        if dmxStartCode not in range(0, 256):
            raise ValueError(f'dmx start code is a byte! values: [0-255]! value was {dmxStartCode}')
        self._dmxStartCode = dmxStartCode

    @property
    def dmxData(self) -> tuple:
        return self._dmxData

    @dmxData.setter
    def dmxData(self, data: tuple):
        """
        For legacy devices and to prevent errors, the length of the DMX data is normalized to 512
        """
        if len(data) > 512 or \
                not all((isinstance(x, int) and (0 <= x <= 255)) for x in data):
            raise ValueError(f'dmxData is a tuple with a max length of 512! The data in the tuple has to be valid bytes! '
                             f'Length was {len(data)}')
        newData = [0]*512
        for i in range(0, min(len(data), 512)):
            newData[i] = data[i]
        self._dmxData = tuple(newData)
        # in theory this class supports dynamic length, so the next line is correcting the length
        self.length = 126 + len(self._dmxData)

    def getBytes(self) -> tuple:
        rtrnList = super().getBytes()
        # Flags and Length Framing Layer:-------
        rtrnList.extend(make_flagsandlength(self.length - 38))
        # Vector Framing Layer:-----------------
        rtrnList.extend(VECTOR_E131_DATA_PACKET)
        # sourceName:---------------------------
        # UTF-8 encode the string
        tmpSourceName = str(self._sourceName).encode('UTF-8')
        rtrnList.extend(tmpSourceName)
        # pad to 64 bytes
        rtrnList.extend([0] * (64 - len(tmpSourceName)))
        # priority------------------------------
        rtrnList.append(self._priority)
        # syncAddress---------------------------
        rtrnList.extend(int_to_bytes(self._syncAddr))
        # sequence------------------------------
        rtrnList.append(self._sequence)
        # Options Flags:------------------------
        tmpOptionsFlags = 0
        # stream terminated:
        tmpOptionsFlags += int(self.option_StreamTerminated) << 6
        # preview data:
        tmpOptionsFlags += int(self.option_PreviewData) << 7
        # force synchronization
        tmpOptionsFlags += int(self.option_ForceSync) << 5
        rtrnList.append(tmpOptionsFlags)
        # universe:-----------------------------
        rtrnList.extend(int_to_bytes(self._universe))
        # DMP Layer:---------------------------------------------------
        # Flags and Length DMP Layer:-----------
        rtrnList.extend(make_flagsandlength(self.length - 115))
        # Vector DMP Layer:---------------------
        rtrnList.append(VECTOR_DMP_SET_PROPERTY)
        # Some static values (Address & Data Type, First Property addr, ...)
        rtrnList.extend([0xa1, 0x00, 0x00, 0x00, 0x01])
        # Length of the data:-------------------
        lengthDmxData = len(self._dmxData)+1
        rtrnList.extend(int_to_bytes(lengthDmxData))
        # DMX data:-----------------------------
        rtrnList.append(self._dmxStartCode)  # DMX Start Code
        rtrnList.extend(self._dmxData)
        return tuple(rtrnList)

    @staticmethod
    def make_data_packet(raw_data) -> 'DataPacket':
        """
        Converts raw byte data to a sACN DataPacket. Note that the raw bytes have to come from a 2016 sACN Message.
        This does not support DMX Start code!
        :param raw_data: raw bytes as tuple or list
        :raises TypeError: when the binary data does not match the criteria for a valid DMX data-packet
        :return: a DataPacket with the properties set like the raw bytes
        """
        # Check if the length is sufficient
        if len(raw_data) < 126:
            raise TypeError('The length of the provided data is not long enough! Min length is 126!')
        # Check if the three Vectors are correct
        if tuple(raw_data[18:22]) != tuple(VECTOR_ROOT_E131_DATA) or \
           tuple(raw_data[40:44]) != tuple(VECTOR_E131_DATA_PACKET) or \
           raw_data[117] != VECTOR_DMP_SET_PROPERTY:  # REMEMBER: when slicing: [inclusive:exclusive]
            raise TypeError('Some of the vectors in the given raw data are not compatible to the E131 Standard!')

        tmpPacket = DataPacket(cid=tuple(raw_data[22:38]), sourceName=bytes(raw_data[44:108]).decode('utf-8').replace('\0', ''),
                               universe=byte_tuple_to_int(raw_data[113:115]))  # high byte first
        tmpPacket.priority = raw_data[108]
        tmpPacket.syncAddr = byte_tuple_to_int(raw_data[109:111])
        tmpPacket.sequence = raw_data[111]
        tmpPacket.option_PreviewData = bool(raw_data[112] & 0b10000000)  # use the 7th bit as preview_data
        tmpPacket.option_StreamTerminated = bool(raw_data[112] & 0b01000000)  # use bit 6 as stream terminated
        tmpPacket.option_ForceSync = bool(raw_data[112] & 0b00100000)  # use bit 5 as force sync
        tmpPacket.dmxStartCode = raw_data[125]
        tmpPacket.dmxData = raw_data[126:638]
        return tmpPacket

    def calculate_multicast_addr(self) -> str:
        return calculate_multicast_addr(self.universe)


def calculate_multicast_addr(universe: int) -> str:
    hi_byte = universe >> 8  # a little bit shifting here
    lo_byte = universe & 0xFF  # a little bit mask there
    return f'239.255.{hi_byte}.{lo_byte}'
