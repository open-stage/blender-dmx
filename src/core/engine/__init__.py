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
        pass
        for fixture in core.fixtures:
            render = fixture.roots[0].object['render']

            dimmer = self._renderable_data(render, 'Dimmer')
            if (dimmer): self.render_dimmer(dimmer)

            color = self._renderable_data(render, 'ColorAdd')
            if (color): self.render_color(color)

            # for geom in geoms:
            #     
            #     if (dimmer): self.render_dimmer(geom, dimmer)
                
        