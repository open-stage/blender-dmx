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
    bl_label = "DMX > Programmer > Deselect All"
    bl_idname = "dmx.deselect_all"
    bl_description = "Deselect every object in the Scene"
    bl_options = {'UNDO'}

    def execute(self, context):
        bpy.ops.object.select_all(action='DESELECT')
        return {'FINISHED'}

class DMX_OT_Programmer_Clear(Operator):
    bl_label = "DMX > Programmer > Clear"
    bl_idname = "dmx.clear"
    bl_description = "Clear all DMX values to default and update fixtures"
    bl_options = {'UNDO'}

    def execute(self, context):
        scene = context.scene
        bpy.ops.object.select_all(action='DESELECT')
        for fixture in scene.dmx.fixtures:
            fixture.clear()
        scene.dmx.programmer_color = (1.0, 1.0, 1.0, 1.0)
        scene.dmx.programmer_dimmer = 0.0
        return {'FINISHED'}

class DMX_OT_Programmer_SelectBodies(Operator):
    bl_label = "DMX > Programmer > Select Bodies"
    bl_idname = "dmx.select_bodies"
    bl_description = "Select body from every fixture element selected"
    bl_options = {'UNDO'}

    def execute(self, context):
        dmx = context.scene.dmx
        bodies = []
        for fixture in dmx.fixtures:
            for obj in fixture.collection.objects:
                if (obj in bpy.context.selected_objects):
                    if ('Body' in fixture.objects):
                        bodies.append(fixture.objects['Body'].object)
                    elif ('Emitter' in fixture.objects):
                        bodies.append(fixture.objects['Emitter'].object)

        if (len(bodies)):
            bpy.ops.object.select_all(action='DESELECT')
            for body in bodies:
                body.select_set(True)
        return {'FINISHED'}

class DMX_OT_Programmer_SelectTargets(Operator):
    bl_label = "DMX > Programmer > Select Targets"
    bl_idname = "dmx.select_targets"
    bl_description = "Select target from every fixture element selected"
    bl_options = {'UNDO'}

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
        layout.operator("dmx.deselect_all", text="Deselect All")

        row = layout.row()
        row.operator("dmx.select_bodies", text="Bodies")
        row.operator("dmx.select_targets", text="Targets")

        layout.prop(scene.dmx,"programmer_color", text="")
        layout.prop(scene.dmx,"programmer_dimmer", text="Dimmer")

        layout.prop(scene.dmx,"programmer_pan", text="Pan")
        layout.prop(scene.dmx,"programmer_tilt", text="Tilt")

        layout.operator("dmx.clear", text="Clear")
