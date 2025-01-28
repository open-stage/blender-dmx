#    Copyright Hugo Aboud
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

from bpy.types import Menu, Panel, UIList

from ...i18n import DMX_Lang

_ = DMX_Lang._


class DMX_MT_Universe(Menu):
    bl_label = _("DMX > Universe Menu")
    bl_idname = "DMX_MT_Universe"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        dmx = scene.dmx

        # "Add"
        row = layout.row()
        # row.operator("dmx.add_universe", text="Add", icon="ADD")


class DMX_UL_Universe(UIList):
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname
    ):
        ob = data
        icon = "FILE_VOLUME"
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            col = layout.column()
            col.label(text=f"{item.id}", icon=icon)
            col.ui_units_x = 3
            col = layout.column()
            col.prop(item, "name", text="", emboss=False)
            col = layout.column()
            col.label(text=item.input)
        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.label(text=str(item.id), icon=icon)


class DMX_PT_DMX_Universes(Panel):
    bl_label = _("Universes")
    bl_idname = "DMX_PT_DMX_Universes"
    bl_parent_id = "DMX_PT_DMX"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        dmx = context.scene.dmx

        layout.prop(dmx, "universes_n", text=_("Universes"))

        layout.template_list(
            "DMX_UL_Universe", "", dmx, "universes", dmx, "universe_list_i"
        )

        if dmx.universe_list_i < dmx.universes_n:
            universe = dmx.universes[dmx.universe_list_i]
            layout.prop(universe, "name")
            layout.prop(universe, "input")
