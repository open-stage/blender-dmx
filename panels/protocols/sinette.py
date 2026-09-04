# Copyright (C) 2026 vanous
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


class DMX_PT_DMX_Sinette(Panel):
    bl_label = _("Sinette")
    bl_idname = "DMX_PT_DMX_Sinette"
    bl_parent_id = "DMX_PT_DMX"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        dmx = context.scene.dmx
        sinette_universes = [
            universe for universe in dmx.universes if universe.input == "Sinette"
        ]

        row = layout.row()
        row.prop(dmx, "sinette_enabled")
        row.enabled = len(sinette_universes) > 0
        layout.label(
            text=_("Sinette set for {} universe(s)").format(len(sinette_universes))
        )
        layout.label(text=_("Status") + ": " + dmx.sinette_status)
