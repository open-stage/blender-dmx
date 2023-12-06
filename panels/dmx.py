#
#   BlendexDMX > Panels > DMX
#
#   - Setup DMX Universes
#   - Setup ArtNet (Future)
#
#   http://www.github.com/open-stage/BlenderDMX
#

import bpy
from dmx.data import DMX_Data
from bpy.props import (PointerProperty,
                       EnumProperty,
                       StringProperty)

from bpy.types import (Panel,
                       Menu,
                       Operator,
                       UIList,
                       PropertyGroup)

from dmx.material import getVolumeScatterMaterial
from dmx.util import getSceneRect
from dmx.osc import DMX_OSC
from dmx.osc_utils import DMX_OSC_Templates





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


# Sub-panels #
class DMX_PT_DMX_OSC(Panel):
    bl_label = "OSC"
    bl_idname = "DMX_PT_DMX_OSC"
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
        row.prop(dmx, "osc_enabled")
        row = layout.row()
        row.prop(dmx, "osc_target_address")
        row.enabled = not dmx.osc_enabled
        row = layout.row()
        row.prop(dmx, "osc_target_port")
        row.enabled = not dmx.osc_enabled

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
    bl_label = "Network"
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

class DMX_UL_LiveDMX_items(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.alignment = 'CENTER'
        layout.label(text=f"{index+1}: {item.channel}")

    def invoke(self, context, event):
        pass

class DMX_PT_DMX_LiveDMX(Panel):
    bl_label = "Live DMX"
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

        row = layout.row()
        row.prop(dmx, "selected_live_dmx_source", text="Source")
        row.prop(dmx, "selected_live_dmx_universe", text="Universe")
        layout.template_list("DMX_UL_LiveDMX_items", "", dmx, "dmx_values", dmx, "dmx_value_index", type='GRID')

# Panel #

class DMX_PT_DMX(Panel):
    bl_label = "Protocols"
    bl_idname = "DMX_PT_DMX"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        dmx = context.scene.dmx
