from src.core.types import *

class DMX_DataEngine:
    '''
    The part of the engine responsible for reading from
    and writing to the DMX buffer.
    '''

    # [ Read ]

    def _read_channel_value(self, channel: 'DMX_FixtureChannel') -> float:
        '''
        Read a [0..1] channel value from the buffer.
        '''
        coords = channel.coords
        res = channel.resolution
        
        # (This part code is intentionally verbose, in order
        # to avoid building loops. This method runs hundreds of
        # times for each frame and should be as optimized
        # as possible.)
        # Converts a list of bytes of size n to a n-bytes int.
        value = self.buffer[coords[0]][coords[1]][coords[2]] << 8*(res-1)
        if (res > 1):
            value += self.buffer[coords[3]][coords[4]][coords[5]] << 8*(res-2)
            if (res > 2):
                value += self.buffer[coords[6]][coords[7]][coords[8]] << 8*(res-3)
                if (res > 3):
                    value += self.buffer[coords[9]][coords[10]][coords[11]] << 8*(res-4)
        
        # In order to accomodate for different resolution values,
        # they are normalized to the [0..1] float range.
        return value / (256 ** res)
        
    def _build_fixture_data(self, fixture: 'DMX_Fixture') -> FixtureData:
        '''
        Return a fixture data object: a list of values
        by geometry for each dmx function of a given fixture.
        '''
        data = {}
        for channel in fixture.channels:
            if (channel.resolution == 0):
                continue
            value = self._read_channel_value(channel)
            fn = channel.function
            if fn not in data:
                data[fn] = []
            data[fn].append((channel.geometry,value))
        return data

    # [ Write ]

    def _write_channel_value(self, channel: 'DMX_FixtureChannel', value: float) -> None:
        '''
        Write a [0..1] channel value to the buffer.
        '''       
        coords = channel.coords
        res = channel.resolution

        # (This part code is intentionally verbose, in order
        # to avoid building loops. This method runs hundreds of
        # times for each frame and should be as optimized
        # as possible.)
        # Converts a n-bytes int to a list of bytes of size n.
        value = int(value * (256 ** res - 1))
        self.buffer[coords[0]][coords[1]][coords[2]] = (value >> 8*(res-1)) & 255
        if (res > 1):
            self.buffer[coords[3]][coords[4]][coords[5]] = (value >> 8*(res-2)) & 255
            if (res > 2):
                self.buffer[coords[6]][coords[7]][coords[8]] = (value >> 8*(res-3)) & 255
                if (res > 3):
                    self.buffer[coords[9]][coords[10]][coords[11]] = (value >> 8*(res-4)) & 255

    def _parse_programmer_data(self, fixture: 'DMX_Fixture', fn_data: FunctionData) -> ChannelData:
        '''
        Convert function data (a float value by function) to
        channel data (a float value by channel) for a given fixture.
        '''
        return [
            (ch, fn_data[ch.function]) for ch in fixture.channels
            if ch.resolution > 0 and ch.function in fn_data
        ]