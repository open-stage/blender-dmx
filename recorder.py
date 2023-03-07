#
#   BlendexDMX > Recorder
#

import bpy
from dmx.fixture import STRENGTH, COLOR

class DMX_Recorder:

    @classmethod
    def add_fixture_keyframe(self, fixture):
        t = bpy.data.scenes[0].frame_current

        channels = [c.id for c in fixture.channels]
        has_color = False
        has_pan = False
        has_tilt = False
        has_zoom = False

        for c in channels:
            if c.startswith('Color'):
                has_color = True
            elif c == 'Pan':
                has_pan = True
            elif c == 'Tilt':
                has_tilt = True
            elif c == 'Zoom':
                has_zoom = True

        # Dimmer
        for light in fixture.lights:
            light.object.data.keyframe_insert(data_path='energy', frame=t)
            # Color
            if (has_color):
                light.object.data.keyframe_insert(data_path='color', frame=t)

        for emitter_material in fixture.emitter_materials:
            emitter_node = emitter_material.material.node_tree.nodes[1]
            
            # Dimmer
            strength = emitter_node.inputs[STRENGTH]
            strength.keyframe_insert(data_path='default_value', frame=t)

            # Color
            if (has_color):
                color = emitter_node.inputs[COLOR]
                color.keyframe_insert(data_path='default_value', frame=t)

    @classmethod
    def add_keyframe(self):
        dmx = bpy.context.scene.dmx
        for fixture in dmx.fixtures:
            self.add_fixture_keyframe(fixture)
