from typing import List, Tuple

class DMX_DataEngine:

    def _get_coords(self, universe: int, offset: Tuple[int]) -> List[Tuple[int]]:
        addresses = [
            (o - 1 + universe*512)
            for o in offset
            if o != 0
        ]
        coords = [(
            i & 31,
            (i >> 5) & 31,
            (i >> 10) & 31
        ) for i in addresses]
        return coords, len(coords)

    # Read Fixture DMX Data

    def _read_channel_value(self, channel: 'DMX_FixtureChannel'):
        # DMX data is stored in a 32*32*32 bytes vector,
        # which support 64 universes of 512 bytes
        # We need to split into 3 dimensions since Blender
        # only allows a maximum size of 32 for each dimension,
        # and 3 dimensions.
        coords, res = self._get_coords(
            channel.universe,
            channel.offset
        )
        # This part code is intentionally verbose, in order
        # to avoid building loops. This method runs hundreds of
        # times for each frame and should be as optimized
        # as possible.
        a,b,c = coords[0]
        value = self.buffer[a][b][c] << 8*(res-1)
        if (res > 1):
            a,b,c = coords[1]
            value += self.buffer[a][b][c] << 8*(res-2)
            if (res > 2):
                a,b,c = coords[2]
                value += self.buffer[a][b][c] << 8*(res-3)
                if (res > 3):
                    a,b,c = coords[2]
                    value += self.buffer[a][b][c] << 8*(res-4)
        # In order to accomodate for different resolution values,
        # They are normalized to the [0..1] float range.
        return value / (256 ** res)
        
    def _build_fixture_data(self, fixture: 'DMX_Fixture'):
        data = {}
        for channel in fixture.channels:
            if (channel.offset[0] == 0):
                continue
            value = self._read_channel_value(channel)
            fn = channel.function
            if fn not in data:
                data[fn] = []
            data[fn].append((channel.geometry,value))
        return data

    # Write Fixture DMX Data (via Programmer)

    def _parse_programmer_data(self, fixture: 'DMX_Fixture', data: object):
        channel_data = [
            (ch, data[ch.function]) for ch in fixture.channels
            if ch.function in data
        ]
        if not channel_data:
            return None

        coords_value = []
        for ch, data in channel_data:
            if (ch.offset[0] == 0):
                continue
            coords, res = self._get_coords(ch.universe, ch.offset)

            data = int(data * (256 ** res))
            value = [0]*res
            value[0] = (data >> 8*(res-1)) & 255
            if (res > 1):
                value[1] = (data >> 8*(res-2)) & 255
                if (res > 2):
                    value[2] = (data >> 8*(res-3)) & 255
                    if (res > 3):
                        value[3] = (data >> 8*(res-4)) & 255
            coords_value += zip(coords, value)
        return coords_value

    def _write_channel_value(self, coords: Tuple[int], value: int):
        a, b, c = coords
        self.buffer[a][b][c] = value