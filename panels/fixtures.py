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
                       UIList)

from dmx.fixtures.spot import *
from dmx.fixtures.tube import *

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
            if (isinstance(fixture, SpotFixture)):
                row.operator("dmx.edit_spot_fixture", text = "Edit", icon="GREASEPENCIL")
            elif (isinstance(fixture, TubeFixture)):
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

class DMX_OT_Fixture_AddSpot(Operator):
    bl_label = "Add Spot"
    bl_idname = "dmx.add_spot_fixture"

    name: StringProperty(
        name="Name",
        default="Spot")

    address: IntProperty(
        name = "Address",
        description = "DMX Address",
        default = 1,
        min = 1,
        max = 512)

    model: EnumProperty(
        name = "Model",
        description = "Spot Fixture Model",
        items=(('par64','PAR 64','Par Can, diam: 8"','ANTIALIASED',0),('sourcefour','SOURCE FOUR','Source Four PAR','ALIASED',1),('parled64','PAR LED 64','PAR LED 64','SEQ_CHROMA_SCOPE',2))
    )

    angle: FloatProperty(
        name = "Angle",
        description = "Spot Fixture Angle",
        default = 30,
        min = 1,
        max = 180)

    power: FloatProperty(
        name = "Power",
        description = "Spot Fixture Power",
        default = 100,
        min = 1,
        max = 10000)

    emission: FloatProperty(
        name = "Emission",
        description = "Spot Fixture Emission",
        default = 10,
        min = 1,
        max = 1000)

    default_color: FloatVectorProperty(
        name = "Default Color",
        subtype = "COLOR",
        size = 4,
        min = 0.0,
        max = 1.0,
        default = (1.0,1.0,1.0,1.0))

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, "name")
        col.prop(self, "address")
        col.prop(self, "model")
        col.prop(self, "angle")
        col.prop(self, "power")
        col.prop(self, "emission")
        col.prop(self, "default_color")

    def execute(self, context):
        scene = context.scene
        dmx = scene.dmx
        if (self.name in [coll.name for coll in bpy.data.collections]):
            return {'CANCELLED'}
        dmx.addFixture(SpotFixture(dmx, self.name, self.address, self.model, self.emission, self.power, self.angle, list(self.default_color)))
        return {'FINISHED'}

    def invoke(self, context, event):
        self.name = "Spot "+str(len(context.scene.dmx.fixtures)+1)
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

class DMX_OT_Fixture_EditSpot(Operator):
    bl_label = "Edit Spot"
    bl_idname = "dmx.edit_spot_fixture"

    name: StringProperty(
        name="Name",
        default="Spot")

    address: IntProperty(
        name = "Address",
        description = "DMX Address",
        default = 1,
        min = 1,
        max = 512)

    model: EnumProperty(
        name = "Model",
        description = "Spot Fixture Model",
        items=(('par64','PAR 64','Par Can, diam: 8"','ANTIALIASED',0),('sourcefour','SOURCE FOUR','Source Four PAR','ALIASED',1),('parled64','PAR LED 64','PAR LED 64','SEQ_CHROMA_SCOPE',2))
    )

    angle: FloatProperty(
        name = "Angle",
        description = "Spot Fixture Angle",
        default = 30,
        min = 1,
        max = 180)

    power: FloatProperty(
        name = "Power",
        description = "Spot Fixture Power",
        default = 100,
        min = 1,
        max = 10000)

    emission: FloatProperty(
        name = "Emission",
        description = "Spot Fixture Emission",
        default = 10,
        min = 1,
        max = 1000)

    default_color: FloatVectorProperty(
        name = "Default Color",
        subtype = "COLOR",
        size = 4,
        min = 0.0,
        max = 1.0,
        default = (1.0,1.0,1.0,1.0))

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, "name")
        col.prop(self, "address")
        col.prop(self, "model")
        col.prop(self, "angle")
        col.prop(self, "power")
        col.prop(self, "emission")
        col.prop(self, "default_color")

    def execute(self, context):
        scene = context.scene
        dmx = scene.dmx
        dmx.fixtures[scene.dmx.fixture_list_i].edit(self.name, self.address, self.model, self.power, self.emission, self.angle, list(self.default_color))
        return {'FINISHED'}

    def invoke(self, context, event):
        scene = context.scene
        fixture = scene.dmx.fixtures[scene.dmx.fixture_list_i]
        self.name = fixture.name
        self.address = fixture.address
        self.model = fixture.model
        self.power = fixture.power
        self.emission = fixture.emission
        self.angle = fixture.angle
        self.default_color = fixture.default_color
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

class DMX_OT_Fixture_AddTube(Operator):
    bl_label = "Add Tube"
    bl_idname = "dmx.add_tube_fixture"

    name: StringProperty(
        name="Name",
        default="Spot")

    address: IntProperty(
        name = "Address",
        description = "DMX Address",
        default = 1,
        min = 1,
        max = 512)

    model: EnumProperty(
        name = "Model",
        description = "Tube Fixture Model",
        items=(('T8','T8','Tubular Light, diam 1"'),('T5','T5','Tubular Light, diam 5/8"'))
    )

    length: FloatProperty(
        name = "Length",
        description = "Tube Fixture Length",
        default = 1.2,
        min = 0.01,
        max = 10)

    emission: FloatProperty(
        name = "Emission",
        description = "Tube Fixture Emission",
        default = 10,
        min = 1,
        max = 1000)

    default_color: FloatVectorProperty(
        name = "Default Color",
        subtype = "COLOR",
        size = 4,
        min = 0.0,
        max = 1.0,
        default = (1.0,1.0,1.0,1.0))

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, "name")
        col.prop(self, "address")
        col.prop(self, "model")
        col.prop(self, "length")
        col.prop(self, "emission")
        col.prop(self, "default_color")

    def execute(self, context):
        scene = context.scene
        dmx = scene.dmx
        dmx.addFixture(TubeFixture(dmx, self.name, self.address, self.model, self.emission, self.length, list(self.default_color)))
        return {'FINISHED'}

    def invoke(self, context, event):
        self.name = "Tube "+str(len(context.scene.dmx.fixtures)+1)
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

class DMX_OT_Fixture_EditTube(Operator):
    bl_label = "Edit Tube"
    bl_idname = "dmx.edit_tube_fixture"

    name: StringProperty(
        name="Name",
        default="Spot")

    address: IntProperty(
        name = "Address",
        description = "DMX Address",
        default = 1,
        min = 1,
        max = 512)

    model: EnumProperty(
        name = "Model",
        description = "Tube Fixture Model",
        items=(('T8','T8','Tubular Light, diam 1"','EVENT_F8',0),('T5','T5','Tubular Light, diam 5/8"','EVENT_F5',1))
    )

    length: FloatProperty(
        name = "Length",
        description = "Tube Fixture Length",
        default = 1.2,
        min = 0.01,
        max = 10)

    emission: FloatProperty(
        name = "Emission",
        description = "Tube Fixture Emission",
        default = 10,
        min = 1,
        max = 1000)

    default_color: FloatVectorProperty(
        name = "Default Color",
        subtype = "COLOR",
        size = 4,
        min = 0.0,
        max = 1.0,
        default = (1.0,1.0,1.0,1.0))

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, "name")
        col.prop(self, "address")
        col.prop(self, "model")
        col.prop(self, "length")
        col.prop(self, "emission")
        col.prop(self, "default_color")

    def execute(self, context):
        scene = context.scene
        dmx = scene.dmx
        dmx.fixtures[scene.dmx.fixture_list_i].edit(self.name, self.address, self.model, self.length, self.emission, list(self.default_color))
        return {'FINISHED'}

    def invoke(self, context, event):
        fixture = context.scene.dmx.fixtures[context.scene.dmx.fixture_list_i]
        self.name = fixture.name
        fixture.collection.name = self.name
        self.address = fixture.address
        self.length = fixture.length
        self.emission = fixture.emission
        self.default_color = fixture.default_color
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

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
