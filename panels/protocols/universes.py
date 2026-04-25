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
from bpy.props import EnumProperty, IntProperty
from bpy.types import Menu, Operator, Panel, UIList

from ...i18n import DMX_Lang
from ...universe import network_options_list

_ = DMX_Lang._


class DMX_MT_Universe(Menu):
    bl_label = _("DMX > Universe Menu")
    bl_idname = "DMX_MT_Universe"

    def draw(self, context):
        pass


class DMX_OP_Universe_Add(Operator):
    bl_label = _("Add Universe")
    bl_idname = "dmx.add_universe"
    bl_description = _("Allocate and select a specific DMX universe")
    bl_options = {"UNDO"}

    universe_id: IntProperty(
        name=_("Universe ID"),
        description=_("Universe number to create or select"),
        default=0,
        min=0,
        max=511,
    )

    input: EnumProperty(
        name=_("Input"),
        description=_("Input source of the universe"),
        items=network_options_list,
        default="BLENDERDMX",
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "universe_id")
        layout.prop(self, "input")

    def execute(self, context):
        dmx = context.scene.dmx
        dmx.ensureUniverseExists(self.universe_id)
        dmx.universes_show_all = True
        dmx.universe_list_i = self.universe_id
        if self.universe_id < len(dmx.universes):
            dmx.universes[self.universe_id].input = self.input
        return {"FINISHED"}

    def invoke(self, context, event):
        dmx = context.scene.dmx
        universe = dmx.get_selected_universe()
        if universe is not None:
            self.universe_id = universe.id
            self.input = universe.input
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class DMX_UL_Universe(UIList):
    def filter_items(self, context, data, propname):
        visible_indices = set(data.get_visible_universe_indices())

        flags = []
        for index, universe in enumerate(getattr(data, propname)):
            visible = data.universes_show_all or index in visible_indices
            flags.append(self.bitflag_filter_item if visible else 0)

        return flags, []

    def draw_item(self, context, layout, dmx, item, icon, active_data, active_propname):
        icon = "FILE_VOLUME"
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            col = layout.column()
            col.label(text=f"{item.id}", icon=icon)
            col.ui_units_x = 3
            col = layout.column()
            col.label(text=item.name)
            col = layout.column()
            input_label = item.input
            if dmx.universes_show_all and item.id in dmx.get_used_universe_ids():
                input_label = f"{item.input} • {_('Patched')}"
            col.label(text=input_label)
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
        visible_count = len(dmx.get_visible_universe_indices())

        row = layout.row(align=True)
        row.prop(dmx, "universes_show_all", text=_("Show All Universes"))
        row.label(
            text=_("Visible: {} / Allocated: {}").format(visible_count, dmx.universes_n)
        )

        row = layout.row()
        row.operator("dmx.add_universe", text=_("Add Universe"), icon="ADD")

        layout.template_list(
            "DMX_UL_Universe", "", dmx, "universes", dmx, "universe_list_i"
        )

        universe = dmx.get_selected_universe()
        if universe is not None:
            layout.prop(universe, "name")
            layout.prop(universe, "input")
