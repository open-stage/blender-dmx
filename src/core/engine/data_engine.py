from src.core.types import *

class DMX_DataEngine:
    '''
    The part of the engine responsible for reading from
    and writing to the DMX buffer.
    '''

    # A buffer of 64 universes of 512 channels
    buffer = [0]*64*512

    # [ Read ]

    def _read_channel_value(self, meta: [int]) -> float:
        '''
        Read a [0..1] channel value from the buffer.
        '''
        res, *coords = meta

        if (res == 0):
            return None
        
        # (This part code is intentionally verbose, in order
        # to avoid building loops. This method runs hundreds of
        # times for each frame and should be as optimized
        # as possible.)
        # Converts a list of bytes of size n to a n-bytes int.
        value = DMX_DataEngine.buffer[coords[0]] << 8*(res-1)
        if (res > 1):
            value += DMX_DataEngine.buffer[coords[1]] << 8*(res-2)
            if (res > 2):
                value += DMX_DataEngine.buffer[coords[2]] << 8*(res-3)
                if (res > 3):
                    value += DMX_DataEngine.buffer[coords[3]] << 8*(res-4)
        
        # In order to accomodate for different resolution values,
        # they are normalized to the [0..1] float range.
        return value / (256 ** res)
        
    def _renderable_data(self, render_meta, renderable):
        '''
        Return the data for a renderable, from a given render meta.
        '''
        meta = render_meta.get(renderable, None)
        # No data for this renderable
        if (meta is None): 
            return None
        # Read data for each channel of each geometry of this renderable
        data = [
            [
                self._read_channel_value(coord)
                for coord in geom
            ]
            for geom in meta['coords']
        ]
        return zip(meta['geoms'], data)

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
        DMX_DataEngine.buffer[coords[0]] = (value >> 8*(res-1)) & 255
        if (res > 1):
            DMX_DataEngine.buffer[coords[1]] = (value >> 8*(res-2)) & 255
            if (res > 2):
                DMX_DataEngine.buffer[coords[2]] = (value >> 8*(res-3)) & 255
                if (res > 3):
                    DMX_DataEngine.buffer[coords[3]] = (value >> 8*(res-4)) & 255

    def _parse_programmer_data(self, fixture: 'DMX_Fixture', fn_data: FunctionData) -> ChannelData:
        '''
        Convert function data (a float value by function) to
        channel data (a float value by channel) for a given fixture.
        '''
        return [
            (ch, fn_data[ch.function]) for ch in fixture.channels
            if ch.resolution > 0 and ch.function in fn_data
        ]