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

from bpy.types import Panel

from ...i18n import DMX_Lang

_ = DMX_Lang._


class DMX_PT_DMX_sACN(Panel):
    bl_label = _("sACN")
    bl_idname = "DMX_PT_DMX_sACN"
    bl_parent_id = "DMX_PT_DMX"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        dmx = context.scene.dmx

        sacn_universes = []
        for index, universe in enumerate(dmx.universes):
            if index == 0:  # invalid for sACN
                continue
            if universe.input == "sACN":
                sacn_universes.append(universe)

        row = layout.row()
        row.prop(dmx, "sacn_enabled")
        row.enabled = len(sacn_universes) > 0
        row = layout.row()
        row.label(text=_("sACN set for {} universe(s)").format(len(sacn_universes)))
        layout.label(text=_("Status") + ": " + dmx.sacn_status)
