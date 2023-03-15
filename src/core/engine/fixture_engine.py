import bpy
from bpy.types import Object

from typing import Dict, List, Tuple

class DMX_FixtureEngine:

    def _get_objs_of_type(self, obj: Object, geometry_type: str):
        objs = []
        stack = [obj]
        while len(stack):
            obj = stack.pop(0)
            if obj['geometry_type'] == geometry_type:
                objs.append(obj)
            stack += obj.children
        return objs        
        
    def render_dimmer(self, fixture: 'DMX_Fixture', channel_data: Dict[str, List[Tuple[Object, float]]]):
        dimmer = channel_data.get('Dimmer', None)
        if not dimmer: return

        for geometry, value in dimmer:
            beams = self._get_objs_of_type(geometry, 'GeometryBeam')
            for beam in beams:
                beam.data.materials[0].node_tree.nodes['DMX_Dimmer'].inputs[1].default_value = value
