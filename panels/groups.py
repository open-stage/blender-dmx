#
#   BlendexDMX > Panels > Groups
#
#   - Create/Update/Rename/Remove Groups
#   - Select Fixtures by group for programming
#
#   http://www.github.com/hugoaboud/BlenderDMX
#

import bpy

from bpy.props import (StringProperty)

from bpy.types import (Panel,
                       Menu,
                       Operator,
                       PropertyGroup,
                       UIList)

# List #

class DMX_ListItem_Group(PropertyGroup):
    name: StringProperty(
        name="Name",
        default="Group")

class DMX_UL_Group(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        icon = 'STICKY_UVS_LOC'
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(text = item.name, icon = icon)
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon = icon)

# Menus #

class DMX_MT_Group(Menu):
    bl_label = "Group Menu"
    bl_idname = "dmx.menu.group"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        dmx = scene.dmx

        row = layout.row()
        row.operator("dmx.create_group", text="Create", icon="ADD")
        row.enabled = (len(bpy.context.selected_objects) and 1)

        row = layout.row()
        row.operator("dmx.update_group", text="Update", icon="FILE_REFRESH")
        row.enabled = (len(bpy.context.selected_objects) and len(dmx.groups) and scene.dmx.group_list_i >= 0 and scene.dmx.group_list_i < len(dmx.groups))

        row = layout.row()
        row.operator("dmx.rename_group", text="Rename", icon="SYNTAX_OFF")
        row.enabled = (len(dmx.groups) and scene.dmx.group_list_i >= 0 and scene.dmx.group_list_i < len(dmx.groups))

        row = layout.row()
        row.operator("dmx.remove_group", text="Remove", icon="REMOVE")
        row.enabled = (len(dmx.groups) and scene.dmx.group_list_i >= 0 and scene.dmx.group_list_i < len(dmx.groups))

# Operators #

class DMX_OT_Group_Create(Operator):
    bl_label = "Create Group"
    bl_idname = "dmx.create_group"

    name: StringProperty(
        name = "Name",
        description = "Group Name",
        default = "Group")

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, "name")

    def execute(self, context):
        scene = context.scene
        dmx = scene.dmx
        dmx.createGroup(context, self.name)
        return {'FINISHED'}

    def invoke(self, context, event):
        self.name = "Group " + str(len(context.scene.dmx.groups)+1)
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

class DMX_OT_Group_Update(Operator):
    bl_label = "Update Group"
    bl_idname = "dmx.update_group"

    def execute(self, context):
        scene = context.scene
        dmx = scene.dmx
        dmx.updateGroup(scene.dmx.group_list_i)
        return {'FINISHED'}

class DMX_OT_Group_Rename(Operator):
    bl_label = "Edit Tube"
    bl_idname = "dmx.rename_group"

    name: StringProperty(
        name="Name",
        default="Group")

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, "name")

    def execute(self, context):
        scene = context.scene
        dmx = scene.dmx
        dmx.groups[scene.dmx.group_list_i].name = self.name
        scene.group_list[scene.dmx.group_list_i].name = self.name
        return {'FINISHED'}

    def invoke(self, context, event):
        group = context.scene.dmx.groups[context.scene.dmx.group_list_i]
        self.name = group.name
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

class DMX_OT_Group_Remove(Operator):
    bl_label = "Remove Group"
    bl_idname = "dmx.remove_group"

    def execute(self, context):
        scene = context.scene
        dmx = scene.dmx
        dmx.removeGroup(context, scene.dmx.group_list_i)
        return {'FINISHED'}

# Panel #

class DMX_PT_Groups(Panel):
    bl_label = "Groups"
    bl_idname = "dmx.panel.groups"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(self,context):
        return context.object is not None

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        dmx = scene.dmx

        layout.template_list("DMX_UL_Group", "", scene, "group_list", scene.dmx, "group_list_i", rows=4)

        layout.menu("dmx.menu.group", text="...", icon="STICKY_UVS_LOC")
