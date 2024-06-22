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

from bpy.types import Menu, Operator, Panel, UIList
from ...data import DMX_Data

from ...i18n import DMX_Lang
_ = DMX_Lang._


class DMX_UL_LiveDMX_items(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.alignment = 'CENTER'
        layout.label(text=f"{index+1}: {DMX_Data._live_view_data[index]}")

    def invoke(self, context, event):
        pass

class DMX_PT_DMX_LiveDMX(Panel):
    bl_label = _("Live DMX")
    bl_idname = "DMX_PT_DMX_LiveDMX"
    bl_parent_id = "DMX_PT_DMX"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"
    bl_options = {'DEFAULT_CLOSED'}


    def draw(self, context):
        layout = self.layout
        dmx = context.scene.dmx
        selected_universe = dmx.get_selected_live_dmx_universe()
        if selected_universe is None: # this should not happen
            raise ValueError("Missing selected universe, as if DMX base class is empty...")

        row = layout.row()
        row.prop(dmx, "selected_live_dmx", text=_("Source"))
        row = layout.row()
        col = row.column()
        col.label(text=f"{selected_universe.id}")
        col.ui_units_x = 2
        col = row.column()
        row.label(text=f"{selected_universe.name}")
        col = row.column()
        row.label(text=f"{selected_universe.input}")
        layout.template_list("DMX_UL_LiveDMX_items", "", dmx, "dmx_values", dmx, "dmx_value_index", type='GRID')

