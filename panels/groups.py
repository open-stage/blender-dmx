#    Copyright Hugo Aboud, vanous
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

import json

import bpy
from bpy.props import StringProperty
from bpy.types import Menu, Operator, Panel, UIList

from ..i18n import DMX_Lang

_ = DMX_Lang._
# List #


class DMX_UL_Group(UIList):
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        icon = "GROUP_VERTEX"
        fixture_count = len(json.loads(item.dump))
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            layout.label(text=f"{item.name} ({fixture_count})", icon=icon)
        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.label(text="", icon=icon)


# Menus #


class DMX_MT_Group(Menu):
    bl_label = _("DMX > Group Menu")
    bl_idname = "DMX_MT_Group"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        dmx = scene.dmx

        row = layout.row()
        row.operator("dmx.create_group", text=_("Create"), icon="ADD")
        row.enabled = len(bpy.context.selected_objects) and 1

        row = layout.row()
        row.operator("dmx.update_group", text=_("Update"), icon="FILE_REFRESH")
        row.enabled = (
            len(bpy.context.selected_objects)
            and len(dmx.groups)
            and scene.dmx.group_list_i >= 0
            and scene.dmx.group_list_i < len(dmx.groups)
        )

        row = layout.row()
        row.operator("dmx.rename_group", text=_("Rename"), icon="SYNTAX_OFF")
        row.enabled = (
            len(dmx.groups)
            and scene.dmx.group_list_i >= 0
            and scene.dmx.group_list_i < len(dmx.groups)
        )

        row = layout.row()
        row.operator("dmx.remove_group", text=_("Remove"), icon="REMOVE")
        row.enabled = (
            len(dmx.groups)
            and scene.dmx.group_list_i >= 0
            and scene.dmx.group_list_i < len(dmx.groups)
        )


# Operators #


class DMX_OT_Group_Create(Operator):
    bl_label = _("DMX > Group > Create")
    bl_idname = "dmx.create_group"
    bl_description = _("Create DMX group from selected fixtures")
    bl_options = {"UNDO"}

    name: StringProperty(name=_("Name"), description=_("Group Name"), default="Group")

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, "name")

    def execute(self, context):
        scene = context.scene
        dmx = scene.dmx
        if self.name not in dmx.groups:
            if dmx.createGroup(self.name):
                return {"FINISHED"}
        return {"CANCELLED"}

    def invoke(self, context, event):
        self.name = "Group " + str(len(context.scene.dmx.groups) + 1)
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class DMX_OT_Group_Update(Operator):
    bl_label = "DMX > Group > Update"
    bl_idname = "dmx.update_group"
    bl_description = "Replace DMX group fixtures with selected ones"
    bl_options = {"UNDO"}

    def execute(self, context):
        dmx = context.scene.dmx
        dmx.updateGroup(dmx.group_list_i)
        return {"FINISHED"}


class DMX_OT_Group_Rename(Operator):
    bl_label = "DMX > Group > Rename"
    bl_idname = "dmx.rename_group"
    bl_description = "Rename selected DMX group"
    bl_options = {"UNDO"}

    name: StringProperty(name="Name", default="Group")

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, "name")

    def execute(self, context):
        scene = context.scene
        dmx = scene.dmx
        if self.name not in dmx.groups:
            dmx.renameGroup(dmx.group_list_i, self.name)
            return {"FINISHED"}
        return {"CANCELLED"}

    def invoke(self, context, event):
        group = context.scene.dmx.groups[context.scene.dmx.group_list_i]
        self.name = group.name
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class DMX_OT_Group_Remove(Operator):
    bl_label = "DMX > Group > Remove"
    bl_idname = "dmx.remove_group"
    bl_description = "Remove selected DMX group"
    bl_options = {"UNDO"}

    def execute(self, context):
        dmx = context.scene.dmx
        dmx.removeGroup(dmx.group_list_i)
        return {"FINISHED"}


# Panel #


class DMX_PT_Groups(Panel):
    bl_label = "Groups"
    bl_idname = "DMX_PT_Groups"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        dmx = scene.dmx

        layout.template_list(
            "DMX_UL_Group", "", scene.dmx, "groups", scene.dmx, "group_list_i", rows=4
        )

        layout.menu("DMX_MT_Group", text="...", icon="GROUP_VERTEX")

        row = layout.row()
        row.prop(bpy.context.window_manager.dmx, "aditive_selection")
        row.prop(bpy.context.window_manager.dmx, "subtractive_selection")
