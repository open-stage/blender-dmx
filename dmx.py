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

MESH_PATH = 'C:\\Users\\Aboud\\Desktop\\LAB\\BlenderDMX\\mesh\\'

def getBodyMaterial():
    if ('FixtureBody' not in bpy.data.materials):
        material = bpy.data.materials.new("FixtureBody")
        material.diffuse_color = (0.1,0.1,0.1,1.0)
    else:
        material = bpy.data.materials['FixtureBody']
    return material

def getMesh(model):
    mesh = {}
    if (model+"_body" not in bpy.data.meshes and model+"_body" not in bpy.data.meshes):
        imported_object = bpy.ops.import_scene.obj(filepath=MESH_PATH+model+'.obj')
        for i in range(len(bpy.context.selected_objects)):
            obj = bpy.context.selected_objects[i]
            # delete materials
            for m in obj.data.materials:
                if (m): bpy.data.materials.remove(m)
            obj.data.materials.clear()
            # rename mesh
            if ("Body" in obj.name):
                obj.data.name = model+"_body"
                mesh['body'] = bpy.data.meshes[model+"_body"]
            elif ("Emitter" in obj.name):
                obj.data.name = model+"_emitter"
                mesh['emitter'] = bpy.data.meshes[model+"_emitter"]
            elif ("Surface" in obj.name):
                obj.data.name = model+"_surface"
                mesh['surface'] = bpy.data.meshes[model+"_surface"]
        bpy.ops.object.delete()
    else:
        if (model+"_body" in bpy.data.meshes): mesh['body'] = bpy.data.meshes[model+"_body"]
        if (model+"_emitter" in bpy.data.meshes): mesh['emitter'] = bpy.data.meshes[model+"_emitter"]
        if (model+"_surface" in bpy.data.meshes): mesh['surface'] = bpy.data.meshes[model+"_surface"]
    return mesh

def getSceneRect():
    min = [float("inf"),float("inf"),float("inf")]
    max = [-float("inf"),-float("inf"),-float("inf")]

    for obj in bpy.context.scene.objects:
        if (obj.data and hasattr(obj.data, 'vertices')):
            for vertex in obj.data.vertices:
                vtx = obj.matrix_world @ vertex.co
                for i in range(3):
                    if (vtx[i] < min[i]): min[i] = vtx[i]
                    if (vtx[i] > max[i]): max[i] = vtx[i]
        else:
            for i in range(3):
                if (obj.location[i] < min[i]): min[i] = obj.location[i]
                if (obj.location[i] > max[i]): max[i] = obj.location[i]

    return (min, max)

##
#   Fixture: interactive constrained lights and objects that can be controlled
#   by the DMX tab or Art-Net
##

class Fixture:
    def __init__(self, dmx, name, address, model, emission, createObjs):
        print("AM I RUNNING")
        self.dmx = dmx
        self.name = name
        self.address = address
        self.model = model
        self.emission = emission

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

        # Create Objects
        if not createObjs: return

        # Mesh
        mesh = getMesh(self.model)

        # Body
        self.body = bpy.data.objects.new('Body', mesh['body'])
        self.collection.objects.link(self.body)

        if (not len(self.body.data.materials)):
            self.body.data.materials.append(getBodyMaterial())

        # Emitter
        self.emitter = bpy.data.objects.new('Emitter', mesh['emitter'])
        self.collection.objects.link(self.emitter)

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

        self.emitter.active_material = material
        self.emitter.material_slots[0].link = 'OBJECT'
        self.emitter.material_slots[0].material = material

        self.emitter.cycles_visibility.shadow = False

        # Surface
        self.surface = None
        if ('surface' in mesh):
            self.surface = bpy.data.objects.new('Surface', mesh['surface'])
            self.collection.objects.link(self.surface)

            if (not len(self.surface.data.materials)):
                self.surface.data.materials.append(getBodyMaterial())

            self.surface.cycles_visibility.shadow = False

            constraint = self.surface.constraints.new('COPY_LOCATION')
            constraint.target = self.body


    def icon(self):
        return ''
    def setDimmer(self, dimmer):
        pass
    def setColor(self, color):
        pass

class SpotFixture(Fixture):
    def __init__(self, dmx, name, address, model, emission, power, angle, color):
        # base
        print("PLS RUN")
        super().__init__(dmx, name, address, model, emission, True)

        print("SPOT MODEL " + model)
        self.power = power
        self.angle = angle

        if (model == 'par64'): radius = 0.1
        elif (model == 'parled64'): radius = 0.12

        # Target
        bpy.ops.object.empty_add(type='PLAIN_AXES',radius=radius,location=(0,0,-1))
        self.target = bpy.context.active_object
        self.target.name = "Target"

        bpy.ops.collection.objects_remove_all()
        self.collection.objects.link(self.target)
        #bpy.context.scene.collection.objects.unlink(self.target)

        # Body
        constraint = self.body.constraints.new('TRACK_TO')
        constraint.target = self.target
        constraint.track_axis = 'TRACK_NEGATIVE_Z'
        constraint.up_axis = 'UP_Y'

        # Emitter
        constraint = self.emitter.constraints.new('COPY_LOCATION')
        constraint.target = self.body
        constraint = self.emitter.constraints.new('TRACK_TO')
        constraint.target = self.target
        constraint.track_axis = 'TRACK_NEGATIVE_Z'
        constraint.up_axis = 'UP_Y'

        # Surface
        if (self.surface):
            constraint = self.surface.constraints.new('TRACK_TO')
            constraint.target = self.target
            constraint.track_axis = 'TRACK_NEGATIVE_Z'
            constraint.up_axis = 'UP_Y'

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
    def __init__(self, dmx, name, address, model, emission, length, color):
        # DMX
        super().__init__(dmx, name, address, model, emission, False)
        self.length = length

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

class DMX_Setup_Volume_Create(Operator):
    bl_label = "Create Volume Box"
    bl_idname = "dmx.create_volume"

    def execute(self, context):
        dmx = context.scene.dmx
        # Get scene bounds
        min, max = getSceneRect()
        pos = [min[i]+(max[i]-min[i])/2 for i in range(3)]
        scale = [max[i]-min[i] for i in range(3)]
        # Remove old DMX collection if present
        if ("VolumeScatter" not in bpy.data.objects):
            bpy.ops.mesh.primitive_cube_add(size=1.0)
            dmx.volume = bpy.context.selected_objects[0]
            dmx.volume.name = "VolumeScatter"
            dmx.volume.display_type = 'WIRE'

            material = bpy.data.materials.new("VolumeScatter")
            material.use_nodes = True
            material.node_tree.nodes.remove(material.node_tree.nodes[1])
            material.node_tree.nodes.new("ShaderNodeVolumeScatter")
            material.node_tree.links.new(material.node_tree.nodes[0].inputs[1], material.node_tree.nodes[1].outputs[0])

            dmx.volume_density = material.node_tree.nodes[1].inputs['Density']
            dmx.volume.data.materials.append(material)

        else:
            dmx.volume = bpy.data.objects["VolumeScatter"]

        dmx.volume.location = pos
        dmx.volume.scale = scale

        bpy.ops.object.select_all(action='DESELECT')
        dmx.volume.select_set(True)
        bpy.ops.collection.objects_remove_all()
        bpy.context.scene.collection.objects.link(dmx.volume)

        return {'FINISHED'}

class DMX_Setup_Background_Panel(Panel):
    bl_label = "Background"
    bl_idname = "setup_background_panel"
    bl_parent_id = "setup_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(self,context):
        return context.object is not None

    def draw(self, context):
        layout = self.layout
        dmx = context.scene.dmx
        layout.prop(context.scene.dmx_props,'background_color',text='')

class DMX_Setup_Volume_Panel(Panel):
    bl_label = "Volume Scatter"
    bl_idname = "setup_volume_panel"
    bl_parent_id = "setup_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(self,context):
        return context.object is not None

    def draw(self, context):
        layout = self.layout
        dmx = context.scene.dmx
        layout.operator("dmx.create_volume", text = ('Update Volume Box' if dmx.volume else 'Create Volume Box'), icon='MESH_CUBE')

        row = layout.row()
        row.prop(context.scene.dmx_props, 'volume_enabled')
        row.enabled = (dmx.volume != None)

        row = layout.row()
        row.prop(context.scene.dmx_props, 'volume_density')
        row.enabled = (dmx.volume != None)

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
        default = 100,
        min = 1,
        max = 10000)

    emission: FloatProperty(
        name = "Emission",
        description = "Spot Fixture Emission",
        default = 10,
        min = 1,
        max = 1000)

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
        if (self.name in [coll.name for coll in bpy.data.collections]):
            return {'CANCELLED'}
        dmx.addFixture(SpotFixture(dmx, self.name, self.address, self.model, self.emission, self.power, self.angle, (1,1,1,1)))
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
        default = 100,
        min = 1,
        max = 10000)

    emission: FloatProperty(
        name = "Emission",
        description = "Spot Fixture Emission",
        default = 10,
        min = 1,
        max = 1000)

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
        dmx.addFixture(TubeFixture(dmx, self.name, self.address, self.model, self.emission, self.length, (1,1,1,1)))
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
        default = 10,
        min = 1,
        max = 1000)

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
    bl_options = {'DEFAULT_CLOSED'}

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

    def onBackgroundColor(self, context):
        context.scene.dmx.onBackgroundColor(self.background_color)

    background_color: FloatVectorProperty(
        name = "Background Color",
        subtype = "COLOR",
        size = 4,
        min = 0.0,
        max = 1.0,
        default = (0.0,0.0,0.0,1.0),
        update = onBackgroundColor
        )

    def onVolumeEnabled(self, context):
        context.scene.dmx.onVolumeEnabled(self.volume_enabled)

    volume_enabled: BoolProperty(
        name = "Enabled",
        description = "Volume Scatter Enabled",
        default = True,
        update = onVolumeEnabled)

    def onVolumeDensity(self, context):
        context.scene.dmx.onVolumeDensity(self.volume_density)

    volume_density: FloatProperty(
        name = "Density",
        description="Volume Scatter Density",
        default = 1,
        min = 0,
        max = 1,
        update = onVolumeDensity)

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

    classes = (DMX_Setup_Volume_Create,
              DMX_Setup_Background_Panel,
              DMX_Setup_Volume_Panel,
              DMX_Fixture_UL_List,
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
        self.volume = None
        self.volume_density = 1.0
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

        # Set background to black (to match with menu)
        bpy.context.scene.world.node_tree.nodes['Background'].inputs[0].default_value = (0,0,0,0)

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

    def onBackgroundColor(self, color):
        bpy.context.scene.world.node_tree.nodes['Background'].inputs[0].default_value = color

    def onVolumeEnabled(self, enabled):
        self.volume.hide_set(not enabled)

    def onVolumeDensity(self, density):
        self.volume_density.default_value = density

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
