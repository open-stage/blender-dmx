#
#   BlendexDMX > Panels > Recorder
#
#   - Generates DMX values
#
#   http://www.github.com/open-stage/BlenderDMX
#

import bpy

from bpy.types import (Panel,
                       Operator)
from dmx.logging import DMX_Log

class DMX_OT_Recorder_AddKeyframe(Operator):
    bl_label = "DMX > Recorder > Add Keyframe"
    bl_idname = "dmx.recorder_add_keyframe"
    bl_description = "Add a Keyframe with the current DMX data"
    bl_options = {'UNDO'}

    def execute(self, context):
        #DMX_Recorder.add_keyframe()
        dmx = bpy.context.scene.dmx
        DMX_Log.log.debug("run add frame")
        for fixture in dmx.fixtures:
            #self.add_fixture_keyframe(fixture)
            fixture.render(record=True)
            DMX_Log.log.debug(f"keyframe fixture {fixture.name}")
        return {'FINISHED'}

# Panels #

class DMX_PT_Recorder(Panel):
    bl_label = "Recorder"
    bl_idname = "DMX_PT_Recorder"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.operator("dmx.recorder_add_keyframe", text='Add Keyframe', icon='PLUS')
