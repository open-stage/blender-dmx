from src.core.types import *
from src.core import const

from src.core.builder.material import DMX_Material

class DMX_FixtureEngine:
    '''
    The part of the engine responsible for driving objects
    and material parameters from dmx values.
    '''

    def render_dimmer(self, data: any) -> None:
        '''
        Update the intensity of emitter shaders and lights.
        '''
        for geom, [value,] in data:
            for shader in geom['emitter_shaders']:
                shader.nodes[DMX_Material.EMITTER_NODE_NAME].inputs[1].default_value = value
            for light in geom['lights']:
                light.data.energy = value * 1000  
        
    def render_color(self, data: FixtureData) -> None:
        '''
        Update the color of emitter shaders and lights.
        '''
        for geom, [r,g,b,h,s,v] in data:
            pass
        pass
        # for geom, fn_val in data:
        #     ch, r = fn_val.get('ColorAdd_R', (None, None))
        #     ch, g = fn_val.get('ColorAdd_G', (None, None))
        #     ch, b = fn_val.get('ColorAdd_B', (None, None))
            


        # rgb = list(map(data.get, const.Function.RGB))
        # hsv = list(map(data.get, const.Function.HSV))
        # if not rgb and not hsv: return

        # for geometry, value in dimmer:
        #     for shader in geometry['emitter_shaders']:
        #         shader.nodes[DMX_Material.EMITTER_NODE_NAME].inputs[0].default_value = value
        #     for light in geometry['lights']:
        #         light.data.color = value
