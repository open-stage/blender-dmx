import bpy
from bpy.types import Operator, Menu


from src.lang import DMX_Lang

_ = DMX_Lang._

class DMX_OP_Programmer_SelectAll(Operator):
    bl_label = 'Select All'
    bl_description = 'Select every fixture in the scene.'
    bl_idname = "dmx.programmer_select_all"
    bl_options = {'UNDO'}

    def execute(self, context):
        dmx = context.scene.dmx
        for fixture in dmx.fixtures:
            fixture.select()
        return {'FINISHED'}

class DMX_OP_Programmer_SelectInvert(Operator):
    bl_label = 'Invert Selection'
    bl_description = 'Invert the selection of fixtures.'
    bl_idname = "dmx.programmer_select_invert"
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

class DMX_OP_Programmer_SelectEveryOther(Operator):
    bl_label = 'Select Every Other'
    bl_description = 'Select every other light.'
    bl_idname = "dmx.programmer_select_every_other"
    bl_description = "Select every other light"
    bl_options = {'UNDO'}

    def execute(self, context):
        bpy.ops.object.select_all(action='DESELECT')
        dmx = context.scene.dmx
        for idx, fixture in enumerate(dmx.fixtures):
            if idx % 2 == 0:
                fixture.select()

        return {'FINISHED'}

class DMX_OP_Programmer_DeselectAll(Operator):
    bl_label = 'Deselect All'
    bl_description = 'Deselect every object in the scene.'
    bl_idname = "dmx.programmer_deselect_all"
    bl_options = {'UNDO'}

    def execute(self, context):
        bpy.ops.object.select_all(action='DESELECT')
        return {'FINISHED'}

class DMX_OP_Programmer_SelectBodies(Operator):
    bl_label = 'Bodies'
    bl_description = 'Select body from every fixture selected.'
    bl_idname = "dmx.programmer_select_bodies"
    bl_options = {'UNDO'}

    def execute(self, context):
        dmx = context.scene.dmx
        bodies = []
        for fixture in dmx.fixtures:
            for obj in fixture.collection.objects:
                if (obj in bpy.context.selected_objects):
                    for body in fixture.collection.objects:
                        if body.get("geometry_root", False):
                            bodies.append(body)
                    break

        if (len(bodies)):
            bpy.ops.object.select_all(action='DESELECT')
            for body in bodies:
                body.select_set(True)
        return {'FINISHED'}

class DMX_OP_Programmer_SelectTargets(Operator):
    bl_label = 'Targets'
    bl_description = 'Select target from every fixture selected.'
    bl_idname = "dmx.programmer_select_targets"
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

class DMX_OP_Programmer_Clear(Operator):
    bl_label = 'Clear'
    bl_description = 'Clears the selected fixtures.'
    bl_idname = "dmx.programmer_clear"
    bl_options = {'UNDO'}

    def execute(self, context):
        print('[CLEAR FIXTURES]')
        return {'FINISHED'}
