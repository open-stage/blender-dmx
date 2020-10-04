bl_info = {
    "name": "DMX",
    "description": "Simulates a DMX environment",
    "author": "hugoaboud",
    "version": (0, 0, 1),
    "blender": (2, 80, 0),
    "location": "3D View > DMX",
    "warning": "", # used for warning icon and text in addons panel
    "wiki_url": "http://www.github.com/hugoaboud/BlenderDMX",
    "tracker_url": "",
    "category": "Lighting"
}

import bpy
import bmesh

##
#   Setup
##

def getBodyMaterial():
    if ('FixtureBody' not in bpy.data.materials):
        material = bpy.data.materials.new("FixtureBody")
        material.diffuse_color = (0.1,0.1,0.1,1.0)
    else:
        material = bpy.data.materials['FixtureBody']
    return material

##
#   Fixture: interactive constrained lights and objects that can be controlled
#   by the DMX tab or Art-Net
##

class Fixture:

    def __init__(self, dmx, name, resolution, radius, depth, angle, color, power, address):
        # DMX
        self.address = address

        # Fixture (collection) with this name already exists, delete it
        if (name in bpy.data.collections):
            bpy.data.collections.remove(bpy.data.collections[name])

        # Create collection
        bpy.ops.collection.create(name=name)
        self.collection = bpy.data.collections[name]

        # Unlink any leftovers (I can't figure out why, but sometimes Blender will
        # link some existing objects to the new collection)
        for c in self.  collection.objects:
            self.collection.objects.unlink(c)
        for c in self.collection.children:
            self.collection.children.unlink(c)

        # Target
        bpy.ops.object.empty_add(type='PLAIN_AXES',radius=radius,location=(0,0,-1))
        self.target = bpy.context.active_object
        self.target.name = "Target"

        bpy.ops.collection.objects_remove_all()
        self.collection.objects.link(self.target)
        #bpy.context.scene.collection.objects.unlink(self.target)

        # Body
        bpy.ops.mesh.primitive_cylinder_add(vertices=resolution, radius=radius, depth=depth)
        self.body = bpy.context.active_object
        self.body.name = "Body"

        bpy.ops.object.mode_set(mode="EDIT")
        mesh = bmesh.from_edit_mesh(self.body.data)
        mesh.faces.ensure_lookup_table()
        bmesh.ops.delete(mesh, geom=[mesh.faces[resolution+1]], context='FACES_KEEP_BOUNDARY')
        bpy.ops.object.mode_set(mode="OBJECT")

        constraint = self.body.constraints.new('TRACK_TO')
        constraint.target = self.target
        constraint.track_axis = 'TRACK_NEGATIVE_Z'
        constraint.up_axis = 'UP_Y'

        self.body.data.materials.append(getBodyMaterial())
        bpy.ops.collection.objects_remove_all()
        self.collection.objects.link(self.body)
        #bpy.context.scene.collection.objects.unlink(self.body)

        # Emitter
        bpy.ops.mesh.primitive_cylinder_add(vertices=resolution, radius=radius, depth=depth)
        self.emitter = bpy.context.active_object
        self.emitter.name = "Emitter"

        bpy.ops.object.mode_set(mode="EDIT")
        mesh = bmesh.from_edit_mesh(self.emitter.data)
        mesh.faces.ensure_lookup_table()
        bmesh.ops.delete(mesh, geom=mesh.faces[:resolution+1], context='FACES_KEEP_BOUNDARY')
        bpy.ops.object.mode_set(mode="OBJECT")

        constraint = self.emitter.constraints.new('COPY_LOCATION')
        constraint.target = self.body
        constraint = self.emitter.constraints.new('TRACK_TO')
        constraint.target = self.target
        constraint.track_axis = 'TRACK_NEGATIVE_Z'
        constraint.up_axis = 'UP_Y'

        bpy.ops.collection.objects_remove_all()

        if (name in bpy.data.materials):
            bpy.data.materials.remove(bpy.data.materials[name])
        material = bpy.data.materials.new(name)
        material.use_nodes = True

        material.node_tree.nodes.remove(material.node_tree.nodes[1])
        material.node_tree.nodes.new("ShaderNodeEmission")
        material.node_tree.links.new(material.node_tree.nodes[0].inputs[0], material.node_tree.nodes[1].outputs[0])

        self.emitter_power = material.node_tree.nodes[1].inputs['Strength']
        self.emitter_color = material.node_tree.nodes[1].inputs['Color']
        self.emitter_color.default_value = (1,1,1,1)

        self.emitter.data.materials.append(material)
        self.emitter.hide_select = True
        self.emitter.cycles_visibility.shadow = False
        self.collection.objects.link(self.emitter)
        #bpy.context.scene.collection.objects.unlink(self.emitter)

        # Spot
        light_data = bpy.data.lights.new(name="Spot", type='SPOT')
        self.power = power
        light_data.energy = power
        light_data.spot_size = (angle/180.0)*3.141516
        light_data.shadow_soft_size = radius
        self.spot = bpy.data.objects.new(name="Spot", object_data=light_data)

        constraint = self.spot.constraints.new('COPY_LOCATION')
        constraint.target = self.body
        constraint = self.spot.constraints.new('TRACK_TO')
        constraint.target = self.target
        constraint.track_axis = 'TRACK_NEGATIVE_Z'
        constraint.up_axis = 'UP_Y'

        self.spot.hide_select = True
        self.collection.objects.link(self.spot)

        # Link collection to scene
        dmx.collection.children.link(self.collection)

    def icon(self):
        return 'LIGHT_SPOT'

    def setDimmer(self, dimmer):
        self.spot.data.energy = self.power*dimmer
        self.emitter_power.default_value = dimmer

    def setColor(self, color):
        self.spot.data.color = color[:3]
        self.emitter_color.default_value = color

###
#   Add-On
###

from bpy.props import (BoolProperty,
                        IntProperty,
                        FloatProperty,
                        FloatVectorProperty,
                        StringProperty,
                        PointerProperty,
                        CollectionProperty)

from bpy.types import (Collection,
                       Panel,
                       Menu,
                       Operator,
                       PropertyGroup,
                       UIList)

##
#   "Setup" panel
##

class DMX_Setup_BlankShow(Operator):
    bl_label = "Create Blank Show"
    bl_idname = "dmx.blank_show"

    def execute(self, context):
        # Remove old DMX collection if present
        if ("DMX" in bpy.data.collections):
            bpy.data.collections.remove(bpy.data.collections["DMX"])

        # Create a new DMX collection
        bpy.ops.collection.create(name="DMX")
        collection = bpy.data.collections["DMX"]

        # Unlink any leftovers (I can't figure out why, but sometimes Blender will
        # link some existing objects to the new collection)
        for c in collection.objects:
            collection.objects.unlink(c)
        for c in collection.children:
            collection.children.unlink(c)

        # Link collection to scene
        bpy.context.scene.collection.children.link(collection)

        # DMX setup done
        context.scene.dmx.setup(collection)
        return {'FINISHED'}

class DMX_Setup_Panel(Panel):
    bl_label = "Setup"
    bl_idname = "setup_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"

    @classmethod
    def poll(self,context):
        return context.object is not None

    def draw(self, context):
        layout = self.layout
        dmx = context.scene.dmx
        if (not dmx.collection): layout.operator("dmx.blank_show")


##
#   "Fixtures" panel
##

class DMX_Fixture_Item(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        ob = data
        fixture = context.scene.dmx.getFixture(item)
        icon = fixture.icon()
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            # You should always start your row layout by a label (icon + text), or a non-embossed text field,
            # this will also make the row easily selectable in the list! The later also enables ctrl-click rename.
            # We use icon_value of label, as our given icon is an integer value, not an enum ID.
            # Note "data" names should never be translated!
            layout.prop(item, "name", text="", emboss=False, icon=icon)
            layout.label(text="(DMX "+str(fixture.address)+")")
        # 'GRID' layout type should be as compact as possible (typically a single icon!).
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon=icon)

class DMX_Fixture_MenuAdd(Menu):
    bl_label = "Add Fixture"
    bl_idname = "fixture_menu"

    def draw(self, context):
        layout = self.layout

        layout.operator("dmx.add_spot_fixture")

class DMX_Fixture_AddSpot(Operator):
    bl_label = "Add Spot"
    bl_idname = "dmx.add_spot_fixture"

    resolution: IntProperty(
        name = "Resolution",
        description = "Spot Fixture Resolution",
        default = 16,
        min = 3,
        max = 64)

    radius: FloatProperty(
        name = "Radius",
        description = "Spot Fixture Radius",
        default = 0.1,
        min = 0.01,
        max = 1)

    depth: FloatProperty(
        name = "Depth",
        description = "Spot Fixture Depth",
        default = 0.1,
        min = 0.01,
        max = 1)

    angle: FloatProperty(
        name = "Angle",
        description = "Spot Fixture Angle",
        default = 30,
        min = 1,
        max = 180)

    power: FloatProperty(
        name = "Power",
        description = "Spot Fixture Power",
        default = 1000,
        min = 1,
        max = 10000)

    address: IntProperty(
        name = "Address",
        description = "DMX Address",
        default = 1,
        min = 1,
        max = 512)

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, "resolution")
        col.prop(self, "radius")
        col.prop(self, "depth")
        col.prop(self, "angle")
        col.prop(self, "power")
        col.prop(self, "address")

    def execute(self, context):
        scene = context.scene
        dmx = scene.dmx
        dmx.addSpotFixture(Fixture(dmx, "Spot "+str(len(dmx.fixtures)+1), self.resolution, self.radius, self.depth, self.angle, (1,1,1,1), self.power, self.address))
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

class DMX_Fixture_Remove(Operator):
    bl_label = "Remove Fixture"
    bl_idname = "dmx.remove_fixture"

    def execute(self, context):
        scene = context.scene
        dmx = scene.dmx
        dmx.removeFixture(scene.dmx_props.fixture_list_i)
        return {'FINISHED'}

class DMX_Fixture_Panel(Panel):
    bl_label = "Fixtures"
    bl_idname = "fixtures_panel"
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

        layout.template_list("DMX_Fixture_Item", "", dmx.collection, "children", scene.dmx_props, "fixture_list_i", rows=8)
        layout.menu(DMX_Fixture_MenuAdd.bl_idname, text="Add Fixture", icon="OUTLINER_DATA_LIGHT")
        row = layout.row()
        row.operator("dmx.remove_fixture")
        row.enabled = (len(dmx.fixtures) and scene.dmx_props.fixture_list_i >= 0 and scene.dmx_props.fixture_list_i < len(dmx.fixtures))

##
#   "Programmer" panel
##

class DMX_Programmer_ClearSelection(Operator):
    bl_label = "Clear Selection"
    bl_idname = "dmx.clear_selection"

    def execute(self, context):
        bpy.ops.object.select_all(action='DESELECT')
        return {'FINISHED'}


class DMX_Programmer_Panel(Panel):
    bl_label = "Programmer"
    bl_idname = "programmer_panel"
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

        #layout.prop(mytool, "programmer_color", text="")
        layout.operator("dmx.clear_selection")
        layout.prop(scene.dmx_props,"programmer_color", text="")
        layout.prop(scene.dmx_props,"programmer_dimmer", text="Dimmer")

class DMX_Properties(PropertyGroup):

    def onFixtureList(self, context):
        context.scene.dmx.onFixtureList(self.fixture_list_i)

    fixture_list_i : IntProperty(
        name = "Fixture List i",
        description="The selected element on the fixture list",
        default = 0,
        update = onFixtureList
        )

    def onProgrammerColor(self, context):
        context.scene.dmx.onProgrammerColor(self.programmer_color)

    programmer_color: FloatVectorProperty(
        name = "Programmer Color",
        subtype = "COLOR",
        size = 4,
        min = 0.0,
        max = 1.0,
        default = (1.0,1.0,1.0,1.0),
        update = onProgrammerColor
        )

    def onProgrammerDimmer(self, context):
        context.scene.dmx.onProgrammerDimmer(self.programmer_dimmer)

    programmer_dimmer: FloatProperty(
        name = "Programmer Dimmer",
        default = 1,
        min = 0,
        max = 1,
        update = onProgrammerDimmer)


class DMX():

    classes_setup = (DMX_Setup_BlankShow,
                    DMX_Setup_Panel)

    classes = (DMX_Fixture_Item,
              DMX_Fixture_MenuAdd,
              DMX_Fixture_AddSpot,
              DMX_Fixture_Remove,
              DMX_Fixture_Panel,
              DMX_Programmer_ClearSelection,
              DMX_Programmer_Panel)

    def __init__(self):
        self.collection = None
        self.fixtures = []

        #self.fixture_index = IntProperty(name = "List Fixture Index", default = 0)

        self.selected_fixture = 0

    def setup(self, collection):

        self.collection = collection
        #bpy.utils.register_class(ListItem)
        #self.collection.list = CollectionProperty(type=ListItem)

        for cls in self.classes:
            bpy.utils.register_class(cls)

    def register(self):
        for cls in self.classes_setup:
            bpy.utils.register_class(cls)

    def unregister(self):
        for cls in self.classes:
            bpy.utils.unregister_class(cls)
        if (self.collection):
            for cls in self.classes_setup:
                bpy.utils.unregister_class(cls)

    def addSpotFixture(self, fixture):
        self.fixtures.append(fixture)

    def removeFixture(self, i):
        if (i < len(self.fixtures)):
            bpy.data.collections.remove(self.fixtures[i].collection)
            del self.fixtures[i]

    def getFixture(self, collection):
        for fixture in self.fixtures:
            if (fixture.collection == collection):
                return fixture

    def onFixtureList(self, i):
        self.fixtures[i].body.select_set(True)

    def onProgrammerColor(self, color):
        for fixture in self.fixtures:
            for obj in fixture.collection.objects:
                if (obj in bpy.context.selected_objects):
                    fixture.setColor(color)

    def onProgrammerDimmer(self, dimmer):
        for fixture in self.fixtures:
            for obj in fixture.collection.objects:
                if (obj in bpy.context.selected_objects):
                    fixture.setDimmer(dimmer)

def register():
    bpy.types.Scene.dmx = DMX()
    bpy.types.Scene.dmx.register()

    bpy.utils.register_class(DMX_Properties)
    bpy.types.Scene.dmx_props = PointerProperty(type=DMX_Properties)

def unregister():
    bpy.types.Scene.dmx.unregister()
    del bpy.types.Scene.dmx

    bpy.utils.unregister_class(DMX_Properties)

if __name__ == "__main__":
    register()
