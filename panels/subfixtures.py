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

from bpy.types import Panel, Menu, Operator, UIList

from bpy.props import BoolProperty, StringProperty, CollectionProperty

from bpy.types import PropertyGroup
from ..i18n import DMX_Lang

_ = DMX_Lang._
# List #


class DMX_UL_Subfixture(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            col = layout.column()
            col.ui_units_x = 3
            col = layout.column()
            col.label(text=f"{item.name}")
            col = layout.column()
            col.prop(item, "enabled", text="")
        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.label(text=str(item.id), icon=icon)

    def filter_items(self, context, data, propname):
        #temp_data = bpy.context.window_manager.dmx
        vgroups = getattr(data, propname)
        helper_funcs = bpy.types.UI_UL_list
        temp_data = bpy.context.window_manager.dmx

        # Default return values.
        flt_flags = []
        flt_neworder = []

        flt_flags = helper_funcs.filter_items_by_name(self.filter_name, self.bitflag_filter_item, vgroups, "name")
        if not flt_flags:
            flt_flags = [self.bitflag_filter_item] * len(vgroups)
        temp_data.set_filtered_subfixtures(flt_flags)
        return flt_flags,[]

class DMX_OT_Subfixture_SelectVisible(Operator):
    bl_label = _("Select visible")
    bl_idname = "dmx.select_visible_subfixtures"
    bl_description = _("Select visible subfixtures")
    bl_options = {"UNDO"}

    def execute(self, context):
        temp_data = bpy.context.window_manager.dmx
        for fixture, enabled in zip(temp_data.subfixtures, temp_data.filtered_subfixtures):
            if enabled:
                fixture.enabled = True
        return {"FINISHED"}

class DMX_OT_Subfixture_Clear(Operator):
    bl_label = _("Clear selection")
    bl_idname = "dmx.clear_subfixtures"
    bl_description = _("Clear subfixture selection")
    bl_options = {"UNDO"}

    def execute(self, context):
        temp_data = bpy.context.window_manager.dmx
        #temp_data.active_subfixtures.clear()
        for sf in temp_data.subfixtures:
            sf.enabled=False
        return {"FINISHED"}

# Panel #


class DMX_PT_Subfixtures(Panel):
    bl_label = "Subfixtures"
    bl_idname = "DMX_PT_Subfixtures"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        dmx = scene.dmx
        temp_data = bpy.context.window_manager.dmx

        layout.template_list("DMX_UL_Subfixture", "", temp_data, "subfixtures", temp_data, "active_subfixture_i", rows=4)

        selected = ",".join([s.name for s in temp_data.active_subfixtures])
        row = layout.row()
        col1 = row.column()
        col1.label(text=f"Selected: {len(selected)} {selected}")
        col2 = row.column()
        col3 = row.column()
        col2.operator("dmx.select_visible_subfixtures", icon="CHECKBOX_HLT", text="")
        col3.operator("dmx.clear_subfixtures", icon="CHECKBOX_DEHLT", text="")

class DMX_Subfixture(PropertyGroup):
    name: StringProperty()

    def onEnable(self, context):
        enabled = self.enabled
        temp_data = bpy.context.window_manager.dmx

        if enabled:
            if self.name not in temp_data.active_subfixtures:
                temp_data.active_subfixtures.add().name = self.name
        else:
            if self.name in temp_data.active_subfixtures:
                for index, item in enumerate(temp_data.active_subfixtures):
                    if item.name == self.name:
                        temp_data.active_subfixtures.remove(index)
                        break

    enabled: BoolProperty(update=onEnable, default=False)
