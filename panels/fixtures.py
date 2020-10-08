#
#   BlendexDMX > Panels > Fixtures
#
#   - Add/Edit/Remove Fixtures
#   - Select Fixtures by name for programming
#
#   http://www.github.com/hugoaboud/BlenderDMX
#

import bpy

from bpy.props import (IntProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       EnumProperty,
                       StringProperty)

from bpy.types import (Panel,
                       Menu,
                       Operator,
                       UIList,
                       PropertyGroup)

from dmx.fixtures.spot import DMX_SpotFixture
from dmx.fixtures.tube import DMX_TubeFixture

# List #

class DMX_UL_Fixture(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        ob = data
        fixture = context.scene.dmx.getFixture(item)
        icon = fixture.icon()
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "name", text="", emboss=False, icon=icon)
            layout.label(text="(DMX "+str(fixture.address)+")")
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon=icon)

# Menus #

class DMX_MT_Fixture(Menu):
    bl_label = "Fixture Menu"
    bl_idname = "dmx.menu.fixture"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        dmx = scene.dmx
        layout.menu("dmx.menu.add_fixture", text="Add", icon="ADD")

        row = layout.row()
        if (len(dmx.fixtures) and scene.dmx.fixture_list_i >= 0 and scene.dmx.fixture_list_i < len(dmx.fixtures)):
            fixture = dmx.fixtures[scene.dmx.fixture_list_i]
            if (fixture.subclass == 'DMX_SpotFixture'):
                row.operator("dmx.edit_spot_fixture", text = "Edit", icon="GREASEPENCIL")
            elif (fixture.subclass == 'DMX_TubeFixture'):
                row.operator("dmx.edit_tube_fixture", text = "Edit", icon="GREASEPENCIL")
        else:
            row.label(text="Edit", icon="GREASEPENCIL")
            row.enabled = False

        row = layout.row()
        row.operator("dmx.remove_fixture", text="Remove", icon="REMOVE")
        row.enabled = (len(dmx.fixtures) and scene.dmx.fixture_list_i >= 0 and scene.dmx.fixture_list_i < len(dmx.fixtures))

class DMX_MT_Fixture_Add(Menu):
    bl_label = "Add Fixture"
    bl_idname = "dmx.menu.add_fixture"

    def draw(self, context):
        layout = self.layout
        layout.operator("dmx.add_spot_fixture", text="Fixed Spot", icon="LIGHT_SPOT")
        layout.operator("dmx.add_tube_fixture", text="Tubular", icon="MESH_CYLINDER")


# Operators #

class DMX_OT_Fixture_Remove(Operator):
    bl_label = "Remove Fixture"
    bl_idname = "dmx.remove_fixture"

    def execute(self, context):
        scene = context.scene
        dmx = scene.dmx
        dmx.removeFixture(scene.dmx.fixture_list_i)
        return {'FINISHED'}

# Panel #

class DMX_PT_Fixtures(Panel):
    bl_label = "Fixtures"
    bl_idname = "dmx.panel.fixtures"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"

    @classmethod
    def poll(self,context):
        return context.object is not None

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        dmx = scene.dmx

        layout.template_list("DMX_UL_Fixture", "", scene.dmx.collection, "children", scene.dmx, "fixture_list_i")
        layout.menu("dmx.menu.fixture", text="...", icon="OUTLINER_DATA_LIGHT")

        #row = layout.row()
        #row.operator("dmx.remove_fixture")
        #row.enabled = (len(dmx.fixtures) and scene.dmx.fixture_list_i >= 0 and scene.dmx.fixture_list_i < len(dmx.fixtures))
