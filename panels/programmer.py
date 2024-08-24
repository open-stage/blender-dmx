#    Copyright vanous
#
#    This file is part of BlenderDMX.
#
#    BlenderDMX is free software: you can redistribute it and/or modify it
#    under the terms of the GNU General Public License as published by the Free
#    Software Foundation, either version 3 of the License, or (at your option)
#    any later version.
#
#    BlenderDMX is distributed in the hope that it will be useful, but WITHOUT
#    ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
#    FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
#    more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program. If not, see <https://www.gnu.org/licenses/>.

import bpy
from bpy.types import Operator, Panel, Menu
from ..osc_utils import DMX_OSC_Handlers

from bpy.props import StringProperty

from ..i18n import DMX_Lang

_ = DMX_Lang._
# Operators #


class DMX_OT_Programmer_Reset_Color(Operator):
    bl_label = _("Reset Colors")
    bl_idname = "dmx.reset_color"
    bl_description = _("Reset Colors")
    bl_options = {"UNDO"}

    def execute(self, context):
        dmx = context.scene.dmx
        dmx.programmer_color = (1.0, 1.0, 1.0, 1.0)
        return {"FINISHED"}

class DMX_OT_Programmer_Set_Ignore_Movement(Operator):
    bl_label = _("Lock Movement")
    bl_idname = "dmx.ignore_movement_true"
    bl_description = _("Ignore pan/tilt DMX data")
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
                fixture.ignore_movement_dmx = True
        return {"FINISHED"}


class DMX_OT_Programmer_Unset_Ignore_Movement(Operator):
    bl_label = _("Unlock Movement")
    bl_idname = "dmx.ignore_movement_false"
    bl_description = _("Allow pan/tilt DMX data")
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
                fixture.ignore_movement_dmx = False
                fixture.ignore_movement_dmx = False
        return {"FINISHED"}


class DMX_OT_Programmer_DeselectAll(Operator):
    bl_label = _("Deselect All")
    bl_idname = "dmx.deselect_all"
    bl_description = _("Deselect every fixture in the Scene")
    bl_options = {"UNDO"}

    def execute(self, context):
        bpy.ops.object.select_all(action="DESELECT")

        DMX_OSC_Handlers.fixture_clear()
        bpy.context.scene.dmx.updatePreviewVolume()
        return {"FINISHED"}


class DMX_OT_Programmer_SelectAll(Operator):
    bl_label = _("Select All")
    bl_idname = "dmx.select_all"
    bl_description = _("Select every fixture in the Scene")
    bl_options = {"UNDO"}

    def execute(self, context):
        dmx = context.scene.dmx
        for fixture in dmx.fixtures:
            fixture.select()
        bpy.context.scene.dmx.updatePreviewVolume()
        return {"FINISHED"}


class DMX_OT_Programmer_SelectFiltered(Operator):
    bl_label = _("Select Visible (only filtered)")
    bl_idname = "dmx.select_filtered"
    bl_description = _("Select every fixture which is visible in the fixtures list")
    bl_options = {"UNDO"}

    def execute(self, context):
        dmx = context.scene.dmx
        for fixture, enabled in zip(dmx.fixtures, dmx.fixtures_filter):
            if enabled:
                fixture.select()
        bpy.context.scene.dmx.updatePreviewVolume()
        return {"FINISHED"}


class DMX_OT_Programmer_SelectInvert(Operator):
    bl_label = _("Invert selection")
    bl_idname = "dmx.select_invert"
    bl_description = _("Invert the selection")
    bl_options = {"UNDO"}

    def execute(self, context):
        dmx = context.scene.dmx
        selected = []
        for fixture in dmx.fixtures:
            for obj in fixture.collection.objects:
                if obj in bpy.context.selected_objects:
                    selected.append(fixture)
                    fixture.unselect()

        for fixture in dmx.fixtures:
            if fixture not in selected:
                fixture.select()

        bpy.context.scene.dmx.updatePreviewVolume()
        return {"FINISHED"}


class DMX_OT_Programmer_SelectEveryOther(Operator):
    bl_label = _("Select every other light")
    bl_idname = "dmx.select_every_other"
    bl_description = _("Select every other light")
    bl_options = {"UNDO"}

    def execute(self, context):
        bpy.ops.object.select_all(action="DESELECT")
        dmx = context.scene.dmx
        for idx, fixture in enumerate(dmx.fixtures):
            if idx % 2 == 0:
                fixture.select()

        bpy.context.scene.dmx.updatePreviewVolume()
        return {"FINISHED"}


class DMX_OT_Programmer_Clear(Operator):
    bl_label = _("Clear")
    bl_idname = "dmx.clear"
    bl_description = _("Clear all DMX values to default and update fixtures")
    bl_options = {"UNDO"}

    def execute(self, context):
        scene = context.scene
        dmx = context.scene.dmx
        selected_fixtures = False
        for fixture in dmx.fixtures:
            if fixture.is_selected():
                selected_fixtures = True
                break

        if not selected_fixtures:
            for fixture in dmx.fixtures:
                fixture.clear()
        else:
            for fixture in dmx.fixtures:
                if fixture.is_selected():
                    fixture.clear()

        scene.dmx.programmer_color = (1.0, 1.0, 1.0, 1.0)
        scene.dmx.programmer_dimmer = 0.0
        scene.dmx.programmer_pan = 0.0
        scene.dmx.programmer_tilt = 0.0
        scene.dmx.programmer_zoom = 25
        scene.dmx.programmer_color_wheel = 0
        scene.dmx.programmer_color_temperature = 0
        scene.dmx.programmer_gobo = 0
        scene.dmx.programmer_gobo_index = 63
        scene.dmx.programmer_shutter = 0

        return {"FINISHED"}


class DMX_OT_Programmer_Apply_Manually(Operator):
    bl_label = _("Apply")
    bl_idname = "dmx.apply"
    bl_description = _("Apply these values manually when render is paused")
    bl_options = {"UNDO"}

    def execute(self, context):
        scene = context.scene
        bpy.context.window_manager.dmx.pause_render = False
        scene.dmx.onProgrammerApplyManually(context)
        bpy.context.window_manager.dmx.pause_render = True

        return {"FINISHED"}


class DMX_OT_Programmer_TargetsToZero(Operator):
    bl_label = _("Targets to zero")
    bl_idname = "dmx.targets_to_zero"
    bl_description = _("Set Targets' position to 0 of the Scene")
    bl_options = {"UNDO"}

    def execute(self, context):
        dmx = context.scene.dmx
        select_targets(dmx)
        for fixture in dmx.fixtures:
            for obj in fixture.collection.objects:
                if obj.get("geometry_root", False):
                    body = obj
                    break
            for obj in fixture.collection.objects:
                if obj in bpy.context.selected_objects:
                    if "Target" in fixture.objects:
                        fixture.objects["Target"].object.location = (0, 0, 0)
                    break

        return {"FINISHED"}

class DMX_OT_Programmer_CenterToSelected(bpy.types.Operator):
    bl_idname = "dmx.center_to_selected"
    bl_label = _("Center View to Selected")
    bl_description = _("Set View to center on selected objects")

    def execute(self, context):
        cursor_location = context.scene.cursor.location.copy()
        bpy.ops.view3d.snap_cursor_to_selected()
        bpy.ops.view3d.view_center_cursor()
        context.scene.cursor.location = cursor_location
        return {'FINISHED'}

class DMX_MT_PIE_Reset(Menu):
    bl_label = _("Reset targets")
    bl_idname = "DMX_MT_PIE_Reset"
    bl_description = _("Reset position of target of selected fixtures")

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        col = pie.column(align=True)
        col.operator("dmx.reset_targets", text="+", icon="EVENT_X").axis = "x"
        col.operator("dmx.reset_targets", text="-", icon="EVENT_X").axis = "-x"
        col = pie.column(align=True)
        col.operator("dmx.reset_targets", text="+", icon="EVENT_Y").axis = "y"
        col.operator("dmx.reset_targets", text="-", icon="EVENT_Y").axis = "-y"
        col = pie.column(align=True)
        col.operator("dmx.reset_targets", text="+", icon="EVENT_Z").axis = "z"
        col.operator("dmx.reset_targets", text="-", icon="EVENT_Z").axis = "-z"


class DMX_OT_Programmer_ResetTargets(Operator):
    bl_label = _("Reset targets")
    bl_idname = "dmx.reset_targets"
    bl_options = {"UNDO"}
    bl_description = _("Reset position of target of selected fixtures")

    axis: StringProperty(default="-z")

    def execute(self, context):
        dmx = context.scene.dmx
        select_targets(dmx)
        axis = self.axis

        for fixture in dmx.fixtures:
            for obj in fixture.collection.objects:
                if obj.get("geometry_root", False):
                    body = obj
                    break
            for obj in fixture.collection.objects:
                if obj in bpy.context.selected_objects:
                    if "Target" in fixture.objects:
                        if body is not None:
                            x = body.location[0]
                            y = body.location[1]
                            z = body.location[2]
                            if axis == "-x":
                                fixture.objects["Target"].object.location = (x - 2, y, z)
                            if axis == "-y":
                                fixture.objects["Target"].object.location = (x, y - 2, z)
                            if axis == "-z":
                                fixture.objects["Target"].object.location = (x, y, z - 2)
                            if axis == "x":
                                fixture.objects["Target"].object.location = (x + 2, y, z)
                            if axis == "y":
                                fixture.objects["Target"].object.location = (x, y + 2, z)
                            if axis == "z":
                                fixture.objects["Target"].object.location = (x, y, z + 2)
                    break

        return {"FINISHED"}


class DMX_OT_Programmer_SelectBodies(Operator):
    bl_label = _("Select Fixtures")
    bl_idname = "dmx.select_bodies"
    bl_description = _("Select base/body of every selected fixture")
    bl_options = {"UNDO"}

    def execute(self, context):
        dmx = context.scene.dmx
        bodies = []
        for fixture in dmx.fixtures:
            for obj in fixture.collection.objects:
                if obj in bpy.context.selected_objects:
                    for body in fixture.collection.objects:
                        if body.get("geometry_root", False):
                            bodies.append(body)
                    break

        if len(bodies):
            bpy.ops.object.select_all(action="DESELECT")
            for body in bodies:
                body.select_set(True)
        return {"FINISHED"}


class DMX_OT_Programmer_SelectTargets(Operator):
    bl_label = _("Select Targets")
    bl_idname = "dmx.select_targets"
    bl_description = _("Select target from every fixture element selected")
    bl_options = {"UNDO"}

    def execute(self, context):
        dmx = context.scene.dmx
        select_targets(dmx)
        return {"FINISHED"}


class DMX_OT_Programmer_SelectCamera(Operator):
    bl_label = _("Select Camera")
    bl_idname = "dmx.toggle_camera"
    bl_description = _("Select camera of the selected fixture")
    bl_options = {"UNDO"}

    def execute(self, context):
        dmx = context.scene.dmx
        region = next(iter([area.spaces[0].region_3d for area in bpy.context.screen.areas if area.type == "VIEW_3D"]), None)
        for fixture in dmx.fixtures:
            for obj in fixture.collection.objects:
                if obj in bpy.context.selected_objects:
                    for obj in fixture.collection.objects:
                        if "MediaCamera" in obj.name:
                            bpy.context.scene.camera = obj
                            if region:
                                if region.view_perspective == "CAMERA":
                                    region.view_perspective = "PERSP"
                                else:
                                    region.view_perspective = "CAMERA"
                            break
        return {"FINISHED"}


# Panels #


class DMX_PT_Programmer(Panel):
    bl_label = _("Programmer")
    bl_idname = "DMX_PT_Programmer"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"


    def draw(self, context):
        layout = self.layout
        scene = context.scene
        dmx = scene.dmx
        temp_data = bpy.context.window_manager.dmx

        locked = False
        selected_fixtures = []
        for fixture in dmx.fixtures:
            for obj in fixture.collection.objects:
                if obj in bpy.context.selected_objects:
                    selected_fixtures.append(fixture)
                    if fixture.ignore_movement_dmx is True:
                        locked = True
                    break


        selected = len(selected_fixtures) > 0

        selected_fixture_label = ""
        selected_fixture_class = None
        if len(selected_fixtures) == 0:
            selected_fixture_label = _("Nothing selected")
        elif len(selected_fixtures) == 1:
            selected_fixture_label = selected_fixtures[0].name
            selected_fixture_class = selected_fixtures[0]
        else:
            profiles=[]
            for sel_fixture in selected_fixtures:
                if sel_fixture.gdtf_long_name:
                    name = sel_fixture.gdtf_long_name
                else:
                    name = sel_fixture.profile.removesuffix(".gdtf")

                profiles.append(f"{name}-{sel_fixture.mode}")
            profiles = list(set(profiles))
            if len(profiles)==1:
                selected_fixture_label = f"{len(selected_fixtures)} {profiles[0]}"
                selected_fixture_class = selected_fixtures[0]
            else:
                selected_fixture_label = _("{} selected").format(len(selected_fixtures))

        if temp_data.selected_fixture_label != selected_fixture_label:
            temp_data.subfixtures.clear()
        temp_data.selected_fixture_label = selected_fixture_label

        row = layout.row()
        row.operator("dmx.select_all", text="", icon="SELECT_EXTEND")
        row.operator("dmx.select_invert", text="", icon="SELECT_SUBTRACT")
        row.operator("dmx.select_every_other", text="", icon="SELECT_INTERSECT")
        c0 = row.column()
        c1 = row.column()
        c2 = row.column()
        c3 = row.column()
        c4 = row.column()
        c5 = row.column()
        c6 = row.column()
        c0.operator("dmx.select_filtered", text="", icon="SELECT_DIFFERENCE")
        c1.operator("dmx.deselect_all", text="", icon="SELECT_SET")
        c2.operator("dmx.targets_to_zero", text="", icon="LIGHT_POINT")
        c3.menu("DMX_MT_PIE_Reset", text="", icon="LIGHT_SPOT")
        c4.operator("dmx.ignore_movement_true", text="", icon="LOCKED")
        c5.operator("dmx.ignore_movement_false", text="", icon="UNLOCKED")
        c6.operator("dmx.center_to_selected", text="", icon="ZOOM_IN")
        c1.enabled = c2.enabled = c3.enabled = c4.enabled = selected
        c5.enabled = locked and selected

        row = layout.row()
        row.label(text=selected_fixture_label)
        row = layout.row()
        row.operator("dmx.select_bodies", text=_("Bodies"))
        row.operator("dmx.select_targets", text=_("Targets"))
        if len(selected_fixtures) == 1:
            for obj in selected_fixtures[0].collection.objects:
                if "MediaCamera" in obj.name:
                    row.operator("dmx.toggle_camera", text=_("Camera"))
        row.enabled = selected

        row=layout.row()
        box = layout.column().box()



        if selected_fixture_class is not None:
            all_channels=[]
            for channel in selected_fixture_class.channels:
                if channel.geometry not in all_channels:
                    all_channels.append(channel.geometry)

            for channel in selected_fixture_class.virtual_channels:
                if channel.geometry not in all_channels:
                    all_channels.append(channel.geometry)

            if len(temp_data.subfixtures) < 1:
                tmp_active = [x.name for x in temp_data.active_subfixtures]
                temp_data.active_subfixtures.clear()
                for channel in all_channels:
                    sub = temp_data.subfixtures.add()
                    sub.name = channel
                    if channel in tmp_active:
                        sub.enabled = True
                        if channel not in temp_data.active_subfixtures:
                            temp_data.active_subfixtures.add().name = channel

            if selected_fixtures[0].has_attributes(["ColorAdd_R", "ColorAdd_G", "ColorAdd_B", "ColorSub_C",
                                                    "ColorSub_M", "ColorAdd_Y", "ColorAdd_WW", "ColorAdd_CW",
                                                    "ColorAdd_RY", "ColorAdd_GY", "ColorAdd_UV", "ColorRGB_Red",
                                                    "ColorRGB_Blue", "ColorRGB_Green"]):
                box.template_color_picker(scene.dmx, "programmer_color", value_slider=True)
                row = box.row()
                col1 = row.column()
                col2 = row.column()
                col1.prop(scene.dmx, "programmer_color")
                col2.operator("dmx.reset_color", icon="TRASH", text="")

            if selected_fixtures[0].has_attributes(["Dimmer"]):
                box.prop(scene.dmx, "programmer_dimmer", text=_("Dimmer"), translate=False, slider = True)

            if selected_fixtures[0].has_attributes(["Pan"]):
                row = box.row()
                col1 = row.column()
                col1.prop(scene.dmx, "programmer_pan", text=_("Pan"), translate=False, slider = True)


                if selected_fixtures[0].ignore_movement_dmx == True:
                    col2 = row.column()
                    col2.operator("dmx.ignore_movement_false", text="", icon="UNLOCKED")
                    col1.enabled = False
            if selected_fixtures[0].has_attributes(["Tilt"]):
                row = box.row()
                col1 = row.column()
                col1.prop(scene.dmx, "programmer_tilt", text=_("Tilt"), translate=False, slider = True)
                if selected_fixtures[0].ignore_movement_dmx == True:
                    col2 = row.column()
                    col2.operator("dmx.ignore_movement_false", text="", icon="UNLOCKED")
                    col1.enabled = False
            if selected_fixtures[0].has_attributes(["Zoom"]):
                box.prop(scene.dmx, "programmer_zoom", text=_("Zoom"), translate=False, slider = True)
            if selected_fixtures[0].has_attributes(["Color1", "Color2", "ColorMacro1"]):
                box.prop(scene.dmx, "programmer_color_wheel", text=_("Color Wheel"), translate=False)
            if selected_fixtures[0].has_attributes(["CTO", "CTC", "CTB"]):
                box.prop(scene.dmx, "programmer_color_temperature", text=_("Color Temperature"), translate=False)
            if selected_fixtures[0].has_attributes(["Gobo"]):
                box.prop(scene.dmx, "programmer_gobo", text=_("Gobo"), translate=False)
                box.prop(scene.dmx, "programmer_gobo_index", text=_("Gobo Rotation"), translate=False)
            if selected_fixtures[0].has_attributes(["shutter"], lower=True):
                box.prop(scene.dmx, "programmer_shutter", text=_("Strobe"), translate=False)
        else:

            box.template_color_picker(scene.dmx, "programmer_color", value_slider=True)
            row = box.row()
            col1 = row.column()
            col2 = row.column()
            col1.prop(scene.dmx, "programmer_color")
            col2.operator("dmx.reset_color", icon="TRASH", text="")

            box.prop(scene.dmx, "programmer_dimmer", text=_("Dimmer"), translate=False, slider = True)

            row = box.row()
            col1 = row.column()
            col1.prop(scene.dmx, "programmer_pan", text=_("Pan"), translate=False, slider = True)
            if locked:
                col2 = row.column()
                col2.operator("dmx.ignore_movement_false", text="", icon="UNLOCKED")
            row = box.row()
            col1 = row.column()
            col1.prop(scene.dmx, "programmer_tilt", text=_("Tilt"), translate=False, slider = True)
            if locked:
                col2 = row.column()
                col2.operator("dmx.ignore_movement_false", text="", icon="UNLOCKED")

            box.prop(scene.dmx, "programmer_zoom", text=_("Zoom"), translate=False, slider = True)
            box.prop(scene.dmx, "programmer_color_wheel", text=_("Color Wheel"), translate=False)
            box.prop(scene.dmx, "programmer_color_temperature", text=_("Color Temperature"), translate=False)
            box.prop(scene.dmx, "programmer_gobo", text=_("Gobo"), translate=False)
            box.prop(scene.dmx, "programmer_gobo_index", text=_("Gobo Rotation"), translate=False)
            box.prop(scene.dmx, "programmer_shutter", text=_("Strobe"), translate=False)

        box.enabled = selected

        dmx = context.scene.dmx

        if selected:
            if bpy.context.window_manager.dmx.pause_render:
                layout.operator("dmx.apply", text=_("Apply"))
            layout.operator("dmx.clear", text=_("Clear"))
        else:
            layout.operator("dmx.clear", text=_("Clear All"))


def select_targets(dmx):
    targets = []
    for fixture in dmx.fixtures:
        for obj in fixture.collection.objects:
            if obj in bpy.context.selected_objects:
                if "Target" in fixture.objects:
                    targets.append(fixture.objects["Target"].object)
                break

    if len(targets):
        bpy.ops.object.select_all(action="DESELECT")
        for target in targets:
            target.select_set(True)
