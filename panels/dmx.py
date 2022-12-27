#
#   BlendexDMX > Panels > DMX
#
#   - Setup DMX Universes
#   - Setup ArtNet (Future)
#
#   http://www.github.com/hugoaboud/BlenderDMX
#

import bpy
from bpy.props import (PointerProperty,
                       StringProperty)

from bpy.types import (Panel,
                       Menu,
                       Operator,
                       UIList,
                       PropertyGroup)

from dmx.material import getVolumeScatterMaterial
from dmx.util import getSceneRect

# List #

class DMX_UL_Universe(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        ob = data
        icon = "FILE_VOLUME"
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "name", text="", emboss=False, icon=icon)
            layout.label(text=item.input)
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text=str(item.id), icon=icon)

# Menus #

class DMX_MT_Universe(Menu):
    bl_label = "DMX > Universe Menu"
    bl_idname = "DMX_MT_Universe"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        dmx = scene.dmx

        # "Add"
        row = layout.row()
        #row.operator("dmx.add_universe", text="Add", icon="ADD")

class DMX_MT_NetworkCard(Menu):
    bl_label = "DMX > ArtNet > Network Card Menu"
    bl_idname = "DMX_MT_NetworkCard"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        dmx = scene.dmx
        for card in DMX_Network.cards():
            row = layout.row()
            #row.context_pointer_set("add_edit_panel", context.add_edit_panel)
            row.operator(DMX_OT_Network_Card.bl_idname).ip_addr = card['ip']

# Operators #

class DMX_OT_Network_Card(Operator):
    bl_label = "DMX > ArtNet > Select Network Card"
    bl_idname = "dmx.pick_network_card"

    ip_addr: StringProperty(
        name = "IPv4",
        description = "ArtNet IPv4 Address",
        default = ""
    )

    def execute(self, context):
        bpy.context.dmx.artnet_ip_addr = ip_addr
        return {'FINISHED'}

# Sub-panels #

class DMX_PT_DMX_Universes(Panel):
    bl_label = "Universes"
    bl_idname = "DMX_PT_DMX_Universes"
    bl_parent_id = "DMX_PT_DMX"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        dmx = context.scene.dmx

        layout.prop(dmx, "universes_n", text="Universes")

        layout.template_list("DMX_UL_Universe", "", dmx, "universes", dmx, "universe_list_i")

        if (dmx.universe_list_i < dmx.universes_n):
            universe = dmx.universes[dmx.universe_list_i]
            layout.prop(universe, "name")
            layout.prop(universe, "input")

        #layout.menu("dmx.menu.universe", text="...", icon="FILE_VOLUME")

class DMX_PT_DMX_ArtNet(Panel):
    bl_label = "Ethernet"
    bl_idname = "DMX_PT_DMX_ArtNet"
    bl_parent_id = "DMX_PT_DMX"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        dmx = context.scene.dmx

        row = layout.row()
        row.prop(dmx, "artnet_ipaddr", text="IPv4")
        row.enabled = not dmx.artnet_enabled
        
        row = layout.row()
        row.prop(dmx, "artnet_enabled")
        row = layout.row()
        row.prop(dmx, "sacn_enabled")
        row.enabled = (dmx.artnet_status == 'offline' or dmx.artnet_status == 'listen' or dmx.artnet_status == 'online')

        layout.label(text='Status: ' + layout.enum_item_name(dmx, 'artnet_status', dmx.artnet_status))


# Panel #

class DMX_PT_DMX(Panel):
    bl_label = "DMX"
    bl_idname = "DMX_PT_DMX"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        dmx = context.scene.dmx
