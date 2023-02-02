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

class DMX_OT_Programmer_SelectAll(Operator):
    bl_label = "DMX > Programmer > Select All"
    bl_idname = "dmx.select_all"
    bl_description = "Select every object in the Scene"
    bl_options = {'UNDO'}

    def execute(self, context):
        dmx = context.scene.dmx
        for fixture in dmx.fixtures:
            fixture.select()
        return {'FINISHED'}

class DMX_OT_Programmer_SelectInvert(Operator):
    bl_label = "DMX > Programmer > Invert selection"
    bl_idname = "dmx.select_invert"
    bl_description = "Invert the selection"
    bl_options = {'UNDO'}

    def execute(self, context):
        dmx = context.scene.dmx
        selected = []
        for fixture in dmx.fixtures:
            for obj in fixture.collection.objects:
                if (obj in bpy.context.selected_objects):
                    selected.append(fixture)
                    fixture.unselect() 

        for fixture in dmx.fixtures:
            if fixture not in selected:
                fixture.select()

        return {'FINISHED'}

class DMX_OT_Programmer_SelectEveryOther(Operator):
    bl_label = "DMX > Programmer > Select every other light"
    bl_idname = "dmx.select_every_other"
    bl_description = "Select every other light"
    bl_options = {'UNDO'}

    def execute(self, context):
        bpy.ops.object.select_all(action='DESELECT')
        dmx = context.scene.dmx
        for idx, fixture in enumerate(dmx.fixtures):
            if idx % 2 == 0:
                fixture.select()

        return {'FINISHED'}

class DMX_OT_Programmer_Clear(Operator):
    bl_label = "DMX > Programmer > Clear"
    bl_idname = "dmx.clear"
    bl_description = "Clear all DMX values to default and update fixtures"
    bl_options = {'UNDO'}

    def execute(self, context):
        scene = context.scene
        if (not len(bpy.context.selected_objects)):
            for fixture in scene.dmx.fixtures:
                fixture.clear()
        else:
            for fixture in scene.dmx.fixtures:
                for obj in fixture.collection.objects:
                    if (obj in bpy.context.selected_objects):
                        fixture.clear()
                        break
        scene.dmx.programmer_color = (1.0, 1.0, 1.0, 1.0)
        scene.dmx.programmer_dimmer = 0.0
        scene.dmx.programmer_pan = 0.0
        scene.dmx.programmer_tilt = 0.0
        scene.dmx.programmer_zoom = 0
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
                    for body in fixture.collection.objects:
                        if ('Body' in body.name):
                            bodies.append(body)
                        elif ('Base' in body.name):
                            bodies.append(body)
                        elif ('Emitter' in body.name):
                            bodies.append(body)
                    break

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
                    break

        if (len(targets)):
            bpy.ops.object.select_all(action='DESELECT')
            for target in targets:
                target.select_set(True)
        return {'FINISHED'}

# Panels #

class DMX_PT_Programmer(Panel):
    bl_label = "Programmer"
    bl_idname = "DMX_PT_Programmer"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        dmx = scene.dmx


        row = layout.row()
        row.operator("dmx.select_all", text='', icon='SELECT_EXTEND')
        row.operator("dmx.select_invert", text='', icon='SELECT_SUBTRACT')
        row.operator("dmx.select_every_other", text='', icon='SELECT_INTERSECT')
        row.operator("dmx.deselect_all", text='', icon='SELECT_SET')

        selected = len(bpy.context.selected_objects) > 0
        row = layout.row()
        row.operator("dmx.select_bodies", text="Bodies")
        row.operator("dmx.select_targets", text="Targets")
        row.enabled = selected

        layout.template_color_picker(scene.dmx,"programmer_color", value_slider=True)
        layout.prop(scene.dmx,"programmer_dimmer", text="Dimmer")

        layout.prop(scene.dmx,"programmer_pan", text="Pan")
        layout.prop(scene.dmx,"programmer_tilt", text="Tilt")

        layout.prop(scene.dmx,"programmer_zoom", text="Zoom")

        if (selected):
            layout.operator("dmx.clear", text="Clear")
        else:
            layout.operator("dmx.clear", text="Clear All")
