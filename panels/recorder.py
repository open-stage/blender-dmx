#
#   BlendexDMX > Panels > Recorder
#
#   - Generates DMX values
#
#   http://www.github.com/open-stage/BlenderDMX
#

import bpy

from bpy.types import Panel, Operator
from dmx.logging import DMX_Log


class DMX_OT_Recorder_AddKeyframe(Operator):
    bl_label = "DMX > Recorder > Add Keyframe"
    bl_idname = "dmx.recorder_add_keyframe"
    bl_description = "Add a Keyframe with the current DMX data"
    bl_options = {"UNDO"}

    def execute(self, context):
        # DMX_Recorder.add_keyframe()
        dmx = bpy.context.scene.dmx
        DMX_Log.log.debug("run add frame")

        # make the frame the same for all fixtures
        current_frame = bpy.data.scenes[0].frame_current
        for fixture in dmx.fixtures:
            fixture.render(skip_cache=True, current_frame=current_frame)
            DMX_Log.log.debug(f"keyframe fixture {fixture.name}")
        return {"FINISHED"}


def clear_animation_data(fixture):
    DMX_Log.log.debug(f"clear animation data of a fixture: {fixture.name}")
    for obj in fixture.collection.objects:
        if obj.animation_data:
            obj.animation_data.action = None
            obj.animation_data_clear()

    for emitter_material in fixture.emitter_materials:
        etree = emitter_material.material.node_tree

        if etree.animation_data:
            etree.animation_data.action = None
            etree.animation_data_clear()

    for light in fixture.lights:
        ld = light.object.data

        if ld.animation_data:
            ld.animation_data.action = None
            ld.animation_data_clear()

        ld_tree = ld.node_tree
        if ld_tree.animation_data:
            ld_tree.animation_data.action = None
            ld_tree.animation_data_clear()


class DMX_OT_Recorder_Delete_Keyframes_All(Operator):
    bl_label = "DMX > Recorder > Delete Keyframes for all fixtures"
    bl_idname = "dmx.recorder_delete_keyframes_all"
    bl_description = "Deletes all keyframes from all fixtures"
    bl_options = {"UNDO"}

    def execute(self, context):
        dmx = context.scene.dmx

        for fixture in dmx.fixtures:
            clear_animation_data(fixture)

        return {"FINISHED"}


class DMX_OT_Recorder_Delete_Keyframes_Selected(Operator):
    bl_label = "DMX > Recorder > Delete All Keyframes from selected fixtures"
    bl_idname = "dmx.recorder_delete_keyframes_selected"
    bl_description = "Deletes all keyframes from selected fixtures"
    bl_options = {"UNDO"}

    def execute(self, context):
        dmx = context.scene.dmx

        selected = []
        for fixture in dmx.fixtures:
            for obj in fixture.collection.objects:
                if obj in bpy.context.selected_objects:
                    selected.append(fixture)

        for fixture in dmx.fixtures:
            if fixture in selected:
                clear_animation_data(fixture)

        return {"FINISHED"}


# Panels #


class DMX_PT_Recorder(Panel):
    bl_label = "Keyframe Recorder"
    bl_idname = "DMX_PT_Recorder"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.operator("dmx.recorder_add_keyframe", text="Add Keyframe", icon="PLUS")
        layout.prop(scene.tool_settings, "use_keyframe_insert_auto")


class DMX_PT_DMX_Recorder_Delete(Panel):
    bl_label = "Delete Keyframes"
    bl_idname = "DMX_PT_DMX_Recorder_Delete"
    bl_parent_id = "DMX_PT_Recorder"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        dmx = context.scene.dmx
        selected_fixtures = []
        for fixture in dmx.fixtures:
            for obj in fixture.collection.objects:
                if obj in bpy.context.selected_objects:
                    selected_fixtures.append(fixture)

        selected = len(selected_fixtures) > 0
        fixtures_exist = len(dmx.fixtures) > 0

        row = layout.row()
        row.operator("dmx.recorder_delete_keyframes_selected", text="Delete from selected fixtures", icon="SELECT_DIFFERENCE")
        row.enabled = selected

        row = layout.row()
        row.operator("dmx.recorder_delete_keyframes_all", text="Delete from all fixtures", icon="SELECT_EXTEND")
        row.enabled = fixtures_exist
