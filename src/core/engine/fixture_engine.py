from src.core.types import *
from src.core import const

from src.core.builder.material import DMX_Material

class DMX_FixtureEngine:
    '''
    The part of the engine responsible for driving objects
    and material parameters from dmx values.
    '''

    def render_dimmer(self, fixture: 'DMX_Fixture', data: FixtureData) -> None:
        '''
        Update the intensity of emitter shaders.
        '''
        dimmer = data.get(const.Function.Dimmer, None)
        if not dimmer: return

        for geometry, value in dimmer:
            for shader in geometry['emitter_shaders']:
                shader.nodes[DMX_Material.EMITTER_NODE_NAME].inputs[1].default_value = value
