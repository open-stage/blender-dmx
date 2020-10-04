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
    def __init__(self, dmx, name, address, model):
        self.dmx = dmx
        self.name = name
        self.address = address
        self.model = model

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

    def icon(self):
        return ''
    def setDimmer(self, dimmer):
        pass
    def setColor(self, color):
        pass

class SpotFixture(Fixture):
    def __init__(self, dmx, name, address, model, power, emission, angle, color):
        # base
        super().__init__(dmx, name, address, model)

        self.power = power
        self.emission = emission
        self.angle = angle

        if (model == 'par64'):
            resolution = 16
            radius = 0.13
            depth = 0.41

        elif (model == 'parled64'):
            resolution = 16
            radius = 0.1
            depth = 0.07

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
        self.emitter_power.default_value = emission

        self.emitter_color = material.node_tree.nodes[1].inputs['Color']
        self.emitter_color.default_value = (1,1,1,1)

        self.emitter.data.materials.append(material)
        self.emitter.hide_select = True
        self.emitter.cycles_visibility.shadow = False
        self.collection.objects.link(self.emitter)
        #bpy.context.scene.collection.objects.unlink(self.emitter)

        # Spot
        light_data = bpy.data.lights.new(name="Spot", type='SPOT')
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

    def edit(self, name, address, model, power, emission, angle):
        self.name = name
        self.collection.name = name
        self.address = address
        self.power = power
        self.spot.data.energy = power
        self.emission = emission
        self.emitter_power.default_value = emission
        self.angle = angle
        self.spot.data.spot_size = (angle/180.0)*3.141516

    def icon(self):
        return 'LIGHT_SPOT'

    def setDimmer(self, dimmer):
        self.spot.data.energy = self.power*dimmer
        self.emitter_power.default_value = self.emission*dimmer

    def setColor(self, color):
        self.spot.data.color = color[:3]
        self.emitter_color.default_value = color

class TubeFixture(Fixture):
    def __init__(self, dmx, name, address, model, length, emission, color):
        # DMX
        super().__init__(dmx, name, address, model)
        self.length = length
        self.emission = emission

        resolution = 8
        if (model == 'T8'):
            radius = 0.0127
        elif (model == 'T5'):
            radius = 0.0079

        # Body
        bpy.ops.mesh.primitive_cylinder_add(vertices=resolution, radius=radius, depth=length)
        self.body = bpy.context.active_object
        self.body.name = "Body"

        if (name in bpy.data.materials):
            bpy.data.materials.remove(bpy.data.materials[name])
        material = bpy.data.materials.new(name)
        material.use_nodes = True

        material.node_tree.nodes.remove(material.node_tree.nodes[1])
        material.node_tree.nodes.new("ShaderNodeEmission")
        material.node_tree.links.new(material.node_tree.nodes[0].inputs[0], material.node_tree.nodes[1].outputs[0])

        self.emitter_power = material.node_tree.nodes[1].inputs['Strength']
        self.emitter_power.default_value = emission
        self.emitter_color = material.node_tree.nodes[1].inputs['Color']
        self.emitter_color.default_value = (1,1,1,1)

        self.body.data.materials.append(material)

        bpy.ops.collection.objects_remove_all()
        self.collection.objects.link(self.body)

        # Link collection to scene
        dmx.collection.children.link(self.collection)

    def edit(self, name, address, model, length, emission):
        self.name = name
        self.collection.name = name
        self.address = address
        self.length = length
        self.emission = emission
        self.emitter_power.default_value = emission

    def icon(self):
        return 'MESH_CYLINDER'

    def setDimmer(self, dimmer):
        self.emitter_power.default_value = dimmer*self.emission

    def setColor(self, color):
        self.emitter_color.default_value = color

##
#   Group
##

class Group:
    def __init__(self, dmx, name):
        self.dmx = dmx
        self.name = name
        self.fixtures = []
        self.update()

    def update(self):
        fixtures = []
        for fixture in self.dmx.fixtures:
            for obj in fixture.collection.objects:
                if (obj in bpy.context.selected_objects):
                    fixtures.append(fixture)
        if (len(fixtures)):
            self.fixtures = fixtures

###
#   Add-On
###

from bpy.props import ( BoolProperty,
                        IntProperty,
                        FloatProperty,
                        FloatVectorProperty,
                        EnumProperty,
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
        context.scene.dmx.setup(context, collection)
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

class DMX_Fixture_UL_List(UIList):
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
    bl_idname = "fixture_menu_add"

    def draw(self, context):
        layout = self.layout
        layout.operator("dmx.add_spot_fixture", text="Fixed Spot", icon="LIGHT_SPOT")
        layout.operator("dmx.add_tube_fixture", text="Tubular", icon="MESH_CYLINDER")

class DMX_Fixture_Menu(Menu):
    bl_label = "Fixture Menu"
    bl_idname = "fixture_menu"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        dmx = scene.dmx
        layout.menu(DMX_Fixture_MenuAdd.bl_idname, text="Add", icon="ADD")

        row = layout.row()
        if (len(dmx.fixtures) and scene.dmx_props.fixture_list_i >= 0 and scene.dmx_props.fixture_list_i < len(dmx.fixtures)):
            fixture = dmx.fixtures[scene.dmx_props.fixture_list_i]
            if (isinstance(fixture, SpotFixture)):
                row.operator("dmx.edit_spot_fixture", text = "Edit", icon="GREASEPENCIL")
            elif (isinstance(fixture, TubeFixture)):
                row.operator("dmx.edit_tube_fixture", text = "Edit", icon="GREASEPENCIL")
        else:
            row.label(text="Edit", icon="GREASEPENCIL")
            row.enabled = False

        row = layout.row()
        row.operator("dmx.remove_fixture", text="Remove", icon="REMOVE")
        row.enabled = (len(dmx.fixtures) and scene.dmx_props.fixture_list_i >= 0 and scene.dmx_props.fixture_list_i < len(dmx.fixtures))

class DMX_Fixture_AddSpot(Operator):
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
        items=(('par64','PAR 64','Par Can, diam: 8"','ANTIALIASED',0),('parled64','PAR LED 64','PAR LED 64','ALIASED',1))
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
        default = 1000,
        min = 1,
        max = 10000)

    emission: FloatProperty(
        name = "Emission",
        description = "Spot Fixture Emission",
        default = 1,
        min = 1,
        max = 10)

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, "name")
        col.prop(self, "address")
        col.prop(self, "model")
        col.prop(self, "angle")
        col.prop(self, "power")
        col.prop(self, "emission")

    def execute(self, context):
        scene = context.scene
        dmx = scene.dmx
        dmx.addFixture(SpotFixture(dmx, self.name, self.address, self.model, self.power, self.emission, self.angle, (1,1,1,1)))
        return {'FINISHED'}

    def invoke(self, context, event):
        self.name = "Spot "+str(len(context.scene.dmx.fixtures)+1)
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

class DMX_Fixture_EditSpot(Operator):
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
        items=(('par64','PAR 64','Par Can, diam: 8"','ANTIALIASED',0),('parled64','PAR LED 64','PAR LED 64','ALIASED',1))
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
        default = 1000,
        min = 1,
        max = 10000)

    emission: FloatProperty(
        name = "Emission",
        description = "Spot Fixture Emission",
        default = 1,
        min = 1,
        max = 10)

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, "name")
        col.prop(self, "address")
        col.prop(self, "model")
        col.prop(self, "angle")
        col.prop(self, "power")
        col.prop(self, "emission")

    def execute(self, context):
        scene = context.scene
        dmx = scene.dmx
        dmx.fixtures[scene.dmx_props.fixture_list_i].edit(self.name, self.address, self.model, self.power, self.emission, self.angle)
        return {'FINISHED'}

    def invoke(self, context, event):
        scene = context.scene
        fixture = scene.dmx.fixtures[scene.dmx_props.fixture_list_i]
        self.name = fixture.name
        self.address = fixture.address
        self.model = fixture.model
        self.power = fixture.power
        self.emission = fixture.emission
        self.angle = fixture.angle
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

class DMX_Fixture_AddTube(Operator):
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
        default = 3,
        min = 1,
        max = 10)

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, "name")
        col.prop(self, "address")
        col.prop(self, "model")
        col.prop(self, "length")
        col.prop(self, "emission")

    def execute(self, context):
        scene = context.scene
        dmx = scene.dmx
        dmx.addFixture(TubeFixture(dmx, self.name, self.address, self.model, self.length, self.emission, (1,1,1,1)))
        return {'FINISHED'}

    def invoke(self, context, event):
        self.name = "Tube "+str(len(context.scene.dmx.fixtures)+1)
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

class DMX_Fixture_EditTube(Operator):
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
        default = 3,
        min = 1,
        max = 10)

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, "name")
        col.prop(self, "address")
        col.prop(self, "model")
        col.prop(self, "length")
        col.prop(self, "emission")

    def execute(self, context):
        scene = context.scene
        dmx = scene.dmx
        dmx.fixtures[scene.dmx_props.fixture_list_i].edit(self.name, self.address, self.model, self.length, self.emission)
        return {'FINISHED'}

    def invoke(self, context, event):
        fixture = context.scene.dmx.fixtures[context.scene.dmx_props.fixture_list_i]
        self.name = fixture.name
        fixture.collection.name = self.name
        self.address = fixture.address
        self.length = fixture.length
        self.emission = fixture.emission
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

        layout.template_list("DMX_Fixture_UL_List", "", dmx.collection, "children", scene.dmx_props, "fixture_list_i")
        layout.menu(DMX_Fixture_Menu.bl_idname, text="...", icon="OUTLINER_DATA_LIGHT")
        #row = layout.row()
        #row.operator("dmx.remove_fixture")
        #row.enabled = (len(dmx.fixtures) and scene.dmx_props.fixture_list_i >= 0 and scene.dmx_props.fixture_list_i < len(dmx.fixtures))

##
#   "Groups" panel
##

class DMX_Group_ListItem(PropertyGroup):
    name: StringProperty(
        name="Name",
        default="Group")

class DMX_Group_UL_List(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        icon = 'STICKY_UVS_LOC'
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(text = item.name, icon = icon)
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon = icon)

class DMX_Group_Create(Operator):
    bl_label = "Create Group"
    bl_idname = "dmx.create_group"

    name: StringProperty(
        name = "Name",
        description = "Group Name",
        default = "Group")

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, "name")

    def execute(self, context):
        scene = context.scene
        dmx = scene.dmx
        dmx.createGroup(context, self.name)
        return {'FINISHED'}

    def invoke(self, context, event):
        self.name = "Group " + str(len(context.scene.dmx.groups)+1)
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

class DMX_Group_Update(Operator):
    bl_label = "Update Group"
    bl_idname = "dmx.update_group"

    def execute(self, context):
        scene = context.scene
        dmx = scene.dmx
        dmx.updateGroup(scene.dmx_props.group_list_i)
        return {'FINISHED'}

class DMX_Group_Rename(Operator):
    bl_label = "Edit Tube"
    bl_idname = "dmx.rename_group"

    name: StringProperty(
        name="Name",
        default="Group")

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, "name")

    def execute(self, context):
        scene = context.scene
        dmx = scene.dmx
        dmx.groups[scene.dmx_props.group_list_i].name = self.name
        scene.group_list[scene.dmx_props.group_list_i].name = self.name
        return {'FINISHED'}

    def invoke(self, context, event):
        group = context.scene.dmx.groups[context.scene.dmx_props.group_list_i]
        self.name = group.name
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

class DMX_Group_Remove(Operator):
    bl_label = "Remove Group"
    bl_idname = "dmx.remove_group"

    def execute(self, context):
        scene = context.scene
        dmx = scene.dmx
        dmx.removeGroup(context, scene.dmx_props.group_list_i)
        return {'FINISHED'}

class DMX_Group_Menu(Menu):
    bl_label = "Group Menu"
    bl_idname = "group_menu"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        dmx = scene.dmx

        row = layout.row()
        row.operator("dmx.create_group", text="Create", icon="ADD")
        row.enabled = (len(bpy.context.selected_objects) and 1)

        row = layout.row()
        row.operator("dmx.update_group", text="Update", icon="FILE_REFRESH")
        row.enabled = (len(bpy.context.selected_objects) and len(dmx.groups) and scene.dmx_props.group_list_i >= 0 and scene.dmx_props.group_list_i < len(dmx.groups))

        row = layout.row()
        row.operator("dmx.rename_group", text="Rename", icon="SYNTAX_OFF")
        row.enabled = (len(dmx.groups) and scene.dmx_props.group_list_i >= 0 and scene.dmx_props.group_list_i < len(dmx.groups))

        row = layout.row()
        row.operator("dmx.remove_group", text="Remove", icon="REMOVE")
        row.enabled = (len(dmx.groups) and scene.dmx_props.group_list_i >= 0 and scene.dmx_props.group_list_i < len(dmx.groups))

class DMX_Group_Panel(Panel):
    bl_label = "Groups"
    bl_idname = "groups_panel"
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

        layout.template_list("DMX_Group_UL_List", "", scene, "group_list", scene.dmx_props, "group_list_i", rows=4)

        layout.menu(DMX_Group_Menu.bl_idname, text="...", icon="STICKY_UVS_LOC")

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

    def onGroupList(self, context):
        context.scene.dmx.onGroupList(self.group_list_i)

    group_list_i : IntProperty(
        name = "Group List i",
        description="The selected element on the group list",
        default = 0,
        update = onGroupList
        )


class DMX():

    classes_setup = (DMX_Setup_BlankShow,
                    DMX_Setup_Panel)

    classes = (DMX_Fixture_UL_List,
              DMX_Fixture_MenuAdd,
              DMX_Fixture_Menu,
              DMX_Fixture_AddSpot,
              DMX_Fixture_EditSpot,
              DMX_Fixture_AddTube,
              DMX_Fixture_EditTube,
              DMX_Fixture_Remove,
              DMX_Fixture_Panel,
              DMX_Group_ListItem,
              DMX_Group_UL_List,
              DMX_Group_Create,
              DMX_Group_Update,
              DMX_Group_Rename,
              DMX_Group_Remove,
              DMX_Group_Menu,
              DMX_Group_Panel,
              DMX_Programmer_ClearSelection,
              DMX_Programmer_Panel)

    def __init__(self):
        self.collection = None
        self.fixtures = []
        self.groups = []

        #self.fixture_index = IntProperty(name = "List Fixture Index", default = 0)

        self.selected_fixture = 0

    def setup(self, context, collection):

        self.collection = collection
        #bpy.utils.register_class(ListItem)
        #self.collection.list = CollectionProperty(type=ListItem)

        for cls in self.classes:
            bpy.utils.register_class(cls)

        # Create group list and clear leftovers from past runs
        bpy.types.Scene.group_list = CollectionProperty(type=DMX_Group_ListItem)
        context.scene.group_list.clear()

    def register(self):
        for cls in self.classes_setup:
            bpy.utils.register_class(cls)

    def unregister(self):
        for cls in self.classes:
            bpy.utils.unregister_class(cls)
        if (self.collection):
            for cls in self.classes_setup:
                bpy.utils.unregister_class(cls)

    def addFixture(self, fixture):
        self.fixtures.append(fixture)

    def removeFixture(self, i):
        if (i >= 0 and i < len(self.fixtures)):
            bpy.data.collections.remove(self.fixtures[i].collection)
            del self.fixtures[i]

    def getFixture(self, collection):
        for fixture in self.fixtures:
            if (fixture.collection == collection):
                return fixture

    def createGroup(self, context, name):
        group = Group(self,name)
        if (len(group.fixtures)):
            self.groups.append(group)
            context.scene.group_list.add()
            context.scene.group_list[-1].name = name

    def updateGroup(self, i):
        if (i >= 0 and i < len(self.groups)):
            self.groups[i].update()

    def removeGroup(self, context, i):
        del self.groups[i]
        context.scene.group_list.remove(i)

    def onFixtureList(self, i):
        self.fixtures[i].body.select_set(True)

    def onGroupList(self, i):
        print(self.groups[i])
        print(self.groups[i].fixtures)
        for fixture in self.groups[i].fixtures:
            fixture.body.select_set(True)

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
