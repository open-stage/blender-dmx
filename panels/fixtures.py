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

from dmx.model import DMX_Model
from dmx.gdtf import DMX_GDTF

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
    bl_label = "DMX > Fixture Menu"
    bl_idname = "dmx.menu.fixture"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        dmx = scene.dmx

        # "Add"
        row = layout.row()
        row.operator("dmx.add_fixture", text="Add", icon="ADD")

        # "Edit"
        """
        row = layout.row()
        if (len(dmx.fixtures) and scene.dmx.fixture_list_i >= 0 and scene.dmx.fixture_list_i < len(dmx.fixtures)):
            fixture = dmx.fixtures[scene.dmx.fixture_list_i]
            if (fixture.subclass == 'spot.DMX_SpotFixture'):
                row.operator("dmx.edit_spot_fixture", text = "Edit", icon="GREASEPENCIL")
            elif (fixture.subclass == 'tube.DMX_TubeFixture'):
                row.operator("dmx.edit_tube_fixture", text = "Edit", icon="GREASEPENCIL")
        else:
            row.label(text="Edit", icon="GREASEPENCIL")
            row.enabled = False
        """

        # "Remove"
        row = layout.row()
        row.operator("dmx.remove_fixture", text="Remove", icon="REMOVE")
        row.enabled = (len(dmx.fixtures) and scene.dmx.fixture_list_i >= 0 and scene.dmx.fixture_list_i < len(dmx.fixtures))

# Operators #


class DMX_Fixture_AddEdit():
    bl_label = "DMX > Fixture > Add"
    bl_idname = "dmx.add_fixture"
    bl_description = "Adds a new DMX fixture to the Scene"
    bl_options = {'UNDO'}

    name: StringProperty(
        name="Name",
        default="Fixture")

    # Callback to load Profile items only once for each invoke
    profile_list_items = []
    def profileListItems(self, context):
        if (not len(DMX_Fixture_AddEdit.profile_list_items)):
            DMX_Fixture_AddEdit.profile_list_items = DMX_GDTF.getProfileList()
        return DMX_Fixture_AddEdit.profile_list_items

    profile: EnumProperty(
        name = "Profile",
        description = "Fixture GDTF Profile",
        items=profileListItems)

    address: IntProperty(
        name = "Address",
        description = "DMX Address",
        default = 1,
        min = 1,
        max = 512)

    gel_color: FloatVectorProperty(
        name = "Gel Color",
        subtype = "COLOR",
        size = 4,
        min = 0.0,
        max = 1.0,
        default = (1.0,1.0,1.0,1.0))

    units: IntProperty(
        name = "Units",
        description = "How many units of this light to add",
        default = 1,
        min = 1,
        max = 1024)

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, "name")
        col.prop(self, "profile")
        col.prop(self, "address")
        col.prop(self, "gel_color")
        if (self.units > 0):
            col.prop(self, "units")

class DMX_OT_Fixture_Add(Operator, DMX_Fixture_AddEdit):
    bl_label = "DMX: Add Fixture"
    bl_idname = "dmx.add_fixture"
    bl_options = {'UNDO'}

    def execute(self, context):
        scene = context.scene
        dmx = scene.dmx
        # TODO: Check every name (when adding multiple fixtures)
        if (self.name in bpy.data.collections):
            return {'CANCELLED'}

        for i in range(self.units):
            dmx.addFixture(self.name+" "+str(i+1), self.profile, self.address, list(self.gel_color))
        return {'FINISHED'}

    def invoke(self, context, event):
        self.name = "Fixture "+str(len(context.scene.dmx.fixtures)+1)
        self.units = 1
        DMX_Fixture_AddEdit.profile_list_items = []
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

class DMX_OT_Fixture_Edit(Operator, DMX_Fixture_AddEdit):
    bl_label = "DMX: Edit Fixture"
    bl_idname = "dmx.edit_fixture"
    bl_options = {'UNDO'}

    def execute(self, context):
        scene = context.scene
        dmx = scene.dmx
        fixture = dmx.fixtures[scene.dmx.fixture_list_i]
        if (self.name != fixture.name and self.name in bpy.data.collections):
            return {'CANCELLED'}
        fixture.edit(self.name, self.profile, self.address, list(self.gel_color))
        return {'FINISHED'}

    def invoke(self, context, event):
        scene = context.scene
        fixture = scene.dmx.fixtures[scene.dmx.fixture_list_i]
        self.name = fixture.name
        self.profile = fixture.profile
        self.address = fixture.address
        self.gel_color = (fixture.dmx_params['R'].default,fixture.dmx_params['G'].default,fixture.dmx_params['B'].default,1)
        self.units = 0
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

class DMX_OT_Fixture_Remove(Operator):
    bl_label = "DMX > Fixture > Remove"
    bl_idname = "dmx.remove_fixture"
    bl_description = "Remove selected DMX fixture from Scene"
    bl_options = {'UNDO'}

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
