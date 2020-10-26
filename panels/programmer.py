#
#   BlendexDMX > Panels > Programmer
#
#   - Set selected fixtures color
#   - Set selected fixtures intensity
#   - Clear selection
#
#   http://www.github.com/hugoaboud/BlenderDMX
#

import bpy

from bpy.types import (Panel,
                       Operator)

# Operators #

class DMX_OT_Programmer_DeselectAll(Operator):
    bl_label = "Deselect All"
    bl_idname = "dmx.deselect_all"

    def execute(self, context):
        bpy.ops.object.select_all(action='DESELECT')
        return {'FINISHED'}

class DMX_OT_Programmer_Clear(Operator):
    bl_label = "Clear"
    bl_idname = "dmx.clear"

    def execute(self, context):
        scene = context.scene
        bpy.ops.object.select_all(action='DESELECT')
        for fixture in scene.dmx.fixtures:
            fixture.clear()
        scene.dmx.programmer_color = (1.0, 1.0, 1.0, 1.0)
        scene.dmx.programmer_dimmer = 0.0
        return {'FINISHED'}

class DMX_OT_Programmer_SelectTargets(Operator):
    bl_label = "Select Targets"
    bl_idname = "dmx.select_targets"

    def execute(self, context):
        dmx = context.scene.dmx
        targets = []
        for fixture in dmx.fixtures:
            for obj in fixture.collection.objects:
                if (obj in bpy.context.selected_objects):
                    if ('Target' in fixture.objects):
                        targets.append(fixture.objects['Target'].object)

        if (len(targets)):
            bpy.ops.object.select_all(action='DESELECT')
            for target in targets:
                target.select_set(True)
        return {'FINISHED'}
# Panels #

class DMX_PT_Programmer(Panel):
    bl_label = "Programmer"
    bl_idname = "dmx.panel.programmer"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"

    @classmethod
    def poll(self,context):
        return context.object is not None

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        dmx = scene.dmx

        #layout.prop(mytool, "programmer_color", text="")
        layout.operator("dmx.deselect_all")
        layout.operator("dmx.select_targets")
        layout.prop(scene.dmx,"programmer_color", text="")
        layout.prop(scene.dmx,"programmer_dimmer", text="Dimmer")
        layout.operator("dmx.clear")
