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

from bpy.types import Panel

from ...i18n import DMX_Lang

_ = DMX_Lang._


class DMX_PT_DMX_OSC(Panel):
    bl_label = _("OSC")
    bl_idname = "DMX_PT_DMX_OSC"
    bl_parent_id = "DMX_PT_DMX"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        dmx = context.scene.dmx

        row = layout.row()
        row.prop(dmx, "osc_enabled")
        row = layout.row()
        row.prop(dmx, "osc_target_address")
        row.enabled = not dmx.osc_enabled
        row = layout.row()
        row.prop(dmx, "osc_target_port")
        row.enabled = not dmx.osc_enabled
