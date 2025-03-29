# Copyright (C) 2024 vanous
#
# This file is part of BlenderDMX.
#
# BlenderDMX is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# BlenderDMX is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <https://www.gnu.org/licenses/>.

import bpy
from bpy.types import Operator, Panel

from ..i18n import DMX_Lang
from ..logging import DMX_Log

_ = DMX_Lang._


class DMX_OT_Recorder_AddKeyframe(Operator):
    bl_label = _("DMX > Recorder > Add Keyframe")
    bl_idname = "dmx.recorder_add_keyframe"
    bl_description = _("Add a Keyframe with the current DMX data")
    bl_options = {"UNDO"}

    def execute(self, context):
        # DMX_Recorder.add_keyframe()
        dmx = bpy.context.scene.dmx
        DMX_Log.log.debug("run add frame")
        render_paused_state = bpy.context.window_manager.dmx.pause_render
        if render_paused_state is True:
            bpy.context.window_manager.dmx.pause_render = False

        # make the frame the same for all fixtures
        current_frame = bpy.data.scenes[0].frame_current
        for fixture in dmx.fixtures:
            if bpy.context.window_manager.dmx.keyframe_only_selected:
                if not fixture.is_selected():
                    continue
            fixture.render(skip_cache=True, current_frame=current_frame)
            DMX_Log.log.debug(f"keyframe fixture {fixture.name}")
        bpy.context.window_manager.dmx.pause_render = render_paused_state
        return {"FINISHED"}


def clear_tracker_animation_data(tracker):
    DMX_Log.log.debug(f"clear animation data of a tracker: {tracker.name}")
    for obj in tracker.collection.objects:
        if obj.animation_data:
            obj.animation_data.action = None
            obj.animation_data_clear()


def clear_fixture_animation_data(fixture):
    DMX_Log.log.debug(f"clear animation data of a fixture: {fixture.name}")
    for obj in fixture.collection.objects:
        if obj.animation_data:
            obj.animation_data.action = None
            obj.animation_data_clear()

        if "gobo" in obj.get("geometry_type", ""):
            material = fixture.gobo_materials[obj.name].material
            material_tree = material.node_tree

            if material_tree.animation_data:
                material_tree.animation_data.action = None
                material_tree.animation_data_clear()

    for emitter_material in fixture.emitter_materials:
        etree = emitter_material.material.node_tree

        if etree.animation_data:
            etree.animation_data.action = None
            etree.animation_data_clear()

    for nodes in fixture.geometry_nodes:
        if nodes.node.animation_data:
            nodes.node.animation_data.action = None
            nodes.node.animation_data_clear()

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
    bl_label = _("DMX > Recorder > Delete Keyframes for all fixtures")
    bl_idname = "dmx.recorder_delete_keyframes_all"
    bl_description = _("Deletes all keyframes from all fixtures")
    bl_options = {"UNDO"}

    def execute(self, context):
        dmx = context.scene.dmx

        for fixture in dmx.fixtures:
            clear_fixture_animation_data(fixture)

        for tracker in dmx.trackers:
            clear_tracker_animation_data(tracker)

        return {"FINISHED"}


class DMX_OT_Recorder_Delete_Keyframes_Selected(Operator):
    bl_label = _("DMX > Recorder > Delete All Keyframes from selected fixtures")
    bl_idname = "dmx.recorder_delete_keyframes_selected"
    bl_description = _("Deletes all keyframes from selected fixtures")
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
                clear_fixture_animation_data(fixture)

        return {"FINISHED"}


# Panels #


class DMX_PT_Recorder(Panel):
    bl_label = _("Keyframe Recorder")
    bl_idname = "DMX_PT_Recorder"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        dirty_cache = False
        for fixture in scene.dmx.fixtures:
            if fixture.dmx_cache_dirty:
                dirty_cache = True
                break
        row = layout.row()
        row.operator("dmx.recorder_add_keyframe", text=_("Add Keyframe"), icon="PLUS")
        row.enabled = dirty_cache
        layout.prop(scene.tool_settings, "use_keyframe_insert_auto")
        row = layout.row()
        row.prop(bpy.context.window_manager.dmx, "keyframe_only_selected")
        row.enabled = scene.tool_settings.use_keyframe_insert_auto is False


class DMX_PT_DMX_Recorder_Delete(Panel):
    bl_label = _("Delete Keyframes")
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
                    break

        selected = len(selected_fixtures) > 0
        fixtures_exist = len(dmx.fixtures) > 0

        row = layout.row()
        row.operator(
            "dmx.recorder_delete_keyframes_selected",
            text=_("Delete from selected fixtures"),
            icon="SELECT_DIFFERENCE",
        )
        row.enabled = selected

        row = layout.row()
        row.operator(
            "dmx.recorder_delete_keyframes_all",
            text=_("Delete from all fixtures"),
            icon="SELECT_EXTEND",
        )
        row.enabled = fixtures_exist


class DMX_PT_DMX_Recorder_Drivers(Panel):
    bl_label = _("Objects with #bdmx drivers")
    bl_idname = "DMX_PT_DMX_Recorder_Drivers"
    bl_parent_id = "DMX_PT_Recorder"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        show_enable_button, show_disable_button = show_drivers_buttons(context)
        row = layout.row()
        row.operator("dmx.recorder_enable_drivers", icon="RECORD_ON")
        row.enabled = show_enable_button

        row = layout.row()
        row.operator("dmx.recorder_disable_drivers", icon="PLAY")
        row.enabled = show_disable_button


class DMX_OT_Recorder_Enable_Drivers(Operator):
    bl_label = _("Enable Keying - Disable Playback")
    bl_idname = "dmx.recorder_enable_drivers"
    bl_description = _("Enable disabled bdmx drivers")
    bl_options = {"UNDO"}

    def execute(self, context):
        enable_drivers(context, True)
        return {"FINISHED"}


class DMX_OT_Recorder_Disable_Drivers(Operator):
    bl_label = _("Disable Keying - Enable Playback")
    bl_idname = "dmx.recorder_disable_drivers"
    bl_description = _("Disable bdmx drivers")
    bl_options = {"UNDO"}

    def execute(self, context):
        enable_drivers(context, False)
        return {"FINISHED"}


def show_drivers_buttons(context):
    show_enable_drivers = False
    show_disable_drivers = False

    for obj in context.scene.objects:
        if obj.data is None:
            continue
        if not hasattr(obj.animation_data, "drivers"):
            continue
        drivers = obj.animation_data.drivers
        for fcurve in drivers:
            driver = fcurve.driver
            if driver is not None:
                if driver.expression.startswith("#bdmx"):
                    show_enable_drivers = True
                if driver.expression.startswith("bdmx"):
                    show_disable_drivers = True

            if show_enable_drivers and show_disable_drivers:
                return (show_enable_drivers, show_disable_drivers)

        if show_enable_drivers and show_disable_drivers:
            return (show_enable_drivers, show_disable_drivers)

    return (show_enable_drivers, show_disable_drivers)


def enable_drivers(context, enable):
    for obj in context.scene.objects:
        if obj.data is None:
            continue
        if not hasattr(obj.animation_data, "drivers"):
            continue
        drivers = obj.animation_data.drivers
        for fcurve in drivers:
            driver = fcurve.driver
            if driver is not None:
                if enable:
                    if driver.expression.startswith("#bdmx"):
                        expression = driver.expression
                        driver.expression = expression[1:]
                else:
                    if driver.expression.startswith("bdmx"):
                        # obj.animation_data.drivers.remove(fcurve)
                        expression = driver.expression
                        driver.expression = f"#{expression}"
                        print("INFO", "Removing drivers will print errors but it works")
