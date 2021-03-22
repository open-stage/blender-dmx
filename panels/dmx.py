#
#   BlendexDMX > Panels > DMX
#
#   - Setup DMX Universes
#   - Setup ArtNet (Future)
#
#   http://www.github.com/hugoaboud/BlenderDMX
#

import bpy
from bpy.props import PointerProperty

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
    bl_idname = "dmx.menu.universe"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        dmx = scene.dmx

        # "Add"
        row = layout.row()
        #row.operator("dmx.add_universe", text="Add", icon="ADD")

# Operators #

# Sub-panels #

class DMX_PT_DMX_Universes(Panel):
    bl_label = "Universes"
    bl_idname = "dmx.panel.dmx.universes"
    bl_parent_id = "dmx.panel.dmx"
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
    bl_label = "ArtNet"
    bl_idname = "dmx.panel.dmx.artnet"
    bl_parent_id = "dmx.panel.dmx"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        dmx = context.scene.dmx


# Panel #

class DMX_PT_DMX(Panel):
    bl_label = "DMX"
    bl_idname = "dmx.panel.dmx"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        dmx = context.scene.dmx
