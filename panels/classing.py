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
from bpy.types import Menu, Operator, Panel, UIList

from ..i18n import DMX_Lang

_ = DMX_Lang._
# List #


class DMX_UL_Class(UIList):
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
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


# Panel #


class DMX_PT_Classes(Panel):
    bl_label = "Classes"
    bl_idname = "DMX_PT_Classes"
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
            "DMX_UL_Class", "", scene.dmx, "classing", scene.dmx, "class_list_i", rows=4
        )
