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

from bpy.types import Panel

from ...i18n import DMX_Lang

_ = DMX_Lang._


class DMX_PT_DMX_ArtNet(Panel):
    bl_label = _("Art-Net")
    bl_idname = "DMX_PT_DMX_ArtNet"
    bl_parent_id = "DMX_PT_DMX"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        dmx = context.scene.dmx

        artnet_universes = []
        for universe in dmx.universes:
            if universe.input == "ARTNET":
                artnet_universes.append(universe)

        row = layout.row()
        row.prop(dmx, "artnet_ipaddr", text=_("IPv4"))
        row.enabled = not dmx.artnet_enabled

        row = layout.row()
        row.prop(dmx, "artnet_enabled")
        row.enabled = len(artnet_universes) > 0
        row = layout.row()
        row.label(text=_("Art-Net set for {} universe(s)").format(len(artnet_universes)))
        layout.label(text=_("Status") + ": " + layout.enum_item_name(dmx, "artnet_status", dmx.artnet_status))
