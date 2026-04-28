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

import uuid as py_uuid

import bpy
from bpy.props import StringProperty
from bpy.types import Operator, Panel, UIList

from ..i18n import DMX_Lang

_ = DMX_Lang._
# List #


def _active_class(dmx):
    if 0 <= dmx.class_list_i < len(dmx.classing):
        return dmx.classing[dmx.class_list_i]
    return None


def _fixture_members(class_item, dmx):
    return [fixture for fixture in dmx.fixtures if fixture.classing == class_item.uuid]


def _object_members(class_item, dmx):
    return [
        obj
        for obj in bpy.context.scene.objects
        if obj.get("classing", None) == class_item.uuid
    ]


class DMX_UL_Class(UIList):
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        dmx = context.scene.dmx
        fixture_count = len(_fixture_members(item, dmx))
        object_count = len(_object_members(item, dmx))
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            row = layout.row(align=True)
            row.label(text=f"{item.name}")
            row.label(text=f"F:{fixture_count} O:{object_count}")
            row.prop(item, "enabled", text="")
        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.label(text=str(item.id), icon=icon)


class DMX_OT_Class_Create(Operator):
    bl_label = _("Create")
    bl_idname = "dmx.create_mvr_class"
    bl_description = _("Create MVR class")
    bl_options = {"UNDO"}

    name: StringProperty(
        name=_("Name"), description=_("MVR Class Name"), default="Class"
    )

    def draw(self, context):
        self.layout.prop(self, "name")

    def execute(self, context):
        dmx = context.scene.dmx
        if dmx.find_class_by_name(self.name):
            return {"CANCELLED"}
        class_item = dmx.classing.add()
        class_item.name = self.name
        class_item.uuid = str(py_uuid.uuid4())
        dmx.class_list_i = max(0, len(dmx.classing) - 1)
        return {"FINISHED"}

    def invoke(self, context, event):
        self.name = f"Class {len(context.scene.dmx.classing) + 1}"
        return context.window_manager.invoke_props_dialog(self)


class DMX_OT_Class_Remove(Operator):
    bl_label = _("Remove")
    bl_idname = "dmx.remove_mvr_class"
    bl_description = _("Remove selected MVR class")
    bl_options = {"UNDO"}

    def execute(self, context):
        dmx = context.scene.dmx
        class_item = _active_class(dmx)
        if class_item is None:
            return {"CANCELLED"}

        class_uuid = class_item.uuid

        for fixture in dmx.fixtures:
            if fixture.classing == class_uuid:
                fixture.classing = ""

        for obj in context.scene.objects:
            if obj.get("classing", None) == class_uuid:
                del obj["classing"]

        dmx.classing.remove(dmx.class_list_i)
        dmx.class_list_i = min(dmx.class_list_i, len(dmx.classing) - 1)
        return {"FINISHED"}


class DMX_OT_Class_Rename(Operator):
    bl_label = _("Rename Class")
    bl_idname = "dmx.rename_mvr_class"
    bl_description = _("Rename selected MVR class")
    bl_options = {"UNDO"}

    name: StringProperty(
        name=_("Name"), description=_("MVR Class Name"), default="Class"
    )

    def draw(self, context):
        self.layout.prop(self, "name")

    def execute(self, context):
        dmx = context.scene.dmx
        class_item = _active_class(dmx)
        if class_item is None or not self.name:
            return {"CANCELLED"}
        class_item.name = self.name
        return {"FINISHED"}

    def invoke(self, context, event):
        class_item = _active_class(context.scene.dmx)
        if class_item is None:
            return {"CANCELLED"}
        self.name = class_item.name
        return context.window_manager.invoke_props_dialog(self)


class DMX_OT_Class_Select(Operator):
    bl_label = _("Select")
    bl_idname = "dmx.select_mvr_class_members"
    bl_description = _("Select fixtures and objects in the selected MVR class")
    bl_options = {"UNDO"}

    def execute(self, context):
        dmx = context.scene.dmx
        class_item = _active_class(dmx)
        if class_item is None:
            return {"CANCELLED"}

        bpy.ops.object.select_all(action="DESELECT")

        for fixture in _fixture_members(class_item, dmx):
            fixture.select()

        object_members = _object_members(class_item, dmx)
        for obj in object_members:
            try:
                obj.select_set(True)
            except RuntimeError:
                continue

        if object_members:
            context.view_layer.objects.active = object_members[0]

        return {"FINISHED"}


class DMX_OT_Class_Assign_Selected(Operator):
    bl_label = _("Assign Selected")
    bl_idname = "dmx.assign_selected_to_mvr_class"
    bl_description = _("Assign selected fixtures and objects to the selected MVR class")
    bl_options = {"UNDO"}

    def execute(self, context):
        dmx = context.scene.dmx
        class_item = _active_class(dmx)
        if class_item is None:
            return {"CANCELLED"}

        for fixture in dmx.fixtures:
            if fixture.is_selected():
                fixture.classing = class_item.uuid

        for obj in context.selected_objects:
            obj["classing"] = class_item.uuid

        return {"FINISHED"}


class DMX_OT_Class_Unassign_Selected(Operator):
    bl_label = _("Unassign Selected")
    bl_idname = "dmx.unassign_selected_from_mvr_class"
    bl_description = _(
        "Remove selected fixtures and objects from the selected MVR class"
    )
    bl_options = {"UNDO"}

    def execute(self, context):
        dmx = context.scene.dmx
        class_item = _active_class(dmx)
        if class_item is None:
            return {"CANCELLED"}

        for fixture in dmx.fixtures:
            if fixture.is_selected() and fixture.classing == class_item.uuid:
                fixture.classing = ""

        for obj in context.selected_objects:
            if obj.get("classing", None) == class_item.uuid:
                del obj["classing"]

        return {"FINISHED"}


# Panel #


class DMX_PT_Classes(Panel):
    bl_label = _("Classes")
    bl_idname = "DMX_PT_Classes"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        row = layout.row()
        row.template_list(
            "DMX_UL_Class", "", scene.dmx, "classing", scene.dmx, "class_list_i", rows=4
        )

        col = row.column(align=True)
        col.operator("dmx.create_mvr_class", text="", icon="ADD")
        col.operator("dmx.remove_mvr_class", text="", icon="REMOVE")
        col.operator("dmx.rename_mvr_class", text="", icon="SYNTAX_OFF")
        col.operator(
            "dmx.select_mvr_class_members", text="", icon="RESTRICT_SELECT_OFF"
        )

        if _active_class(scene.dmx) is None:
            return

        row = layout.row(align=True)
        row.operator("dmx.assign_selected_to_mvr_class", icon="ADD")
        row.operator("dmx.unassign_selected_from_mvr_class", icon="REMOVE")
