import bpy
from bpy.types import ( PropertyGroup )
from bpy.props import ( IntVectorProperty )

from typing import Dict, List
from .data_engine import DMX_DataEngine

class DMX_Engine(PropertyGroup, DMX_DataEngine):

    buffer: IntVectorProperty(
        # default = [[0 for _ in range(32)] for _ in range(16)],
        min = 0,
        max = 255,
        size = (32,32,32)
    )

    def render(self, core: 'DMX_Core'):
        for fixture in core.fixtures:
            data = self._build_fixture_data(fixture)
            print(data)
        
    def program(self, fixtures: List['DMX_Fixture'], data: Dict[str,float]):
        for fixture in fixtures:
            coords_value = self._parse_programmer_data(fixture, data)
            for coords, value in coords_value:
                self._write_channel_value(coords, value)
            
        