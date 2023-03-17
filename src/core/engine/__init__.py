from typing import Dict, List

import bpy
from bpy.types import ( PropertyGroup )
from bpy.props import ( IntVectorProperty )

from .data_engine import DMX_DataEngine
from .fixture_engine import DMX_FixtureEngine

class DMX_Engine(
    PropertyGroup,
    DMX_DataEngine,
    DMX_FixtureEngine
):
    '''
    The engine responsible for DMX data I/O and fixture rendering.
    '''

    # A buffer of 64 universes of 512 channels
    # This is the largest IntVector allowed by Blender, so
    # reading/writing must be done through 3D coordinates.
    buffer: IntVectorProperty(
        min = 0,
        max = 255,
        size = (32,32,32)
    )

    def program(self, fixtures: List['DMX_Fixture'], programmer_data: Dict[str,float]):
        '''
        Write DMX data to the buffer at channels covered by the given fixtures.
        '''
        for fixture in fixtures:
            channel_data = self._parse_programmer_data(fixture, programmer_data)
            for coords, value in channel_data:
                self._write_channel_value(coords, value)

    def render(self, core: 'DMX_Core') -> None:
        '''
        Read DMX data from the buffer and update fixtures with it.
        '''
        for fixture in core.fixtures:
            data = self._build_fixture_data(fixture)
            self.render_dimmer(fixture, data)
    
            
        