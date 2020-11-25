#
#   BlendexDMX > Fixtures > Tube
#   Tube Fixture, with a tubular emitter
#   This fixture doesn't load any model, instead it creates a cylinder primitive
#   according to the model diameter.
#
#   http://www.github.com/hugoaboud/BlenderDMX
#


import bpy
from dmx.fixture import DMX_Fixture

from bpy.props import (IntProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       EnumProperty,
                       StringProperty)

from bpy.types import Operator

from dmx.material import getEmitterMaterial

class DMX_TubeFixture():

    # Models that can be assigned to this type of fixture

    MODELS = (
        ('t8','T8','T8, diam: 1"','',0),
        ('t5','t5','T5, diam: 5/8"','',1),
    )

    # Fixture Icon

    @classmethod
    def icon(self):
        return 'MESH_CYLINDER'

    # Create / Edit

    @classmethod
    def create(self, fixture, name, model, address, emission, length, default_color):

        # Define subclass so the DMX_Fixture class can store a reference to it
        fixture.subclass = 'tube.DMX_TubeFixture'
        if (fixture.subclass not in DMX_Fixture.subclasses):
            DMX_Fixture.subclasses[fixture.subclass] = DMX_TubeFixture

        # Create generic fixture
        fixture._create(name, None, address, emission, default_color)
        fixture.model = model

        # Model Parameters
        fixture.model_params.add()
        fixture.model_params[-1].name = 'length'
        fixture.model_params[-1].value = length

        # Resolution: number of faces around the cylinder
        # If you want a more smooth surface, increase this
        resolution = 8

        # Radius from model
        if (model == 't8'):
            radius = 0.0127
        elif (model == 't5'):
            radius = 0.0079

        # Emitter from Primitive
        bpy.ops.mesh.primitive_cylinder_add(vertices=resolution, radius=radius, depth=length)
        fixture.objects.add()
        fixture.objects[-1].name = 'Emitter'
        fixture.objects[-1].object = bpy.context.active_object
        emitter = fixture.objects['Emitter'].object
        bpy.ops.collection.objects_remove_all()
        fixture.collection.objects.link(emitter)

        material = getEmitterMaterial(name)
        emitter.active_material = material
        emitter.material_slots[0].link = 'OBJECT'
        emitter.material_slots[0].material = material
        fixture.emitter_material = material

        # Clear fixture
        fixture.clear()

    @classmethod
    def edit(self, fixture):
        pass

    # DMX

    @classmethod
    def setDMX(self, fixture, pvalues):
        # State variable to call update color only once if RGB change simultaneously
        updateColor = False

        # Update dmx parameters if they are available on the fixture
        for param, value in pvalues.items():
            if (param in fixture.dmx_params):
                fixture.dmx_params[param].value = value

                # Update fixture parameters (single parameters)
                if (param == 'dimmer'): self.updateDimmer(fixture)
                # Mark cumulative parameters to be updated
                if (param == 'R' or param == 'G' or param == 'B'): updateColor = True

        # Update fixture parameters (cumulative parameters)
        if (updateColor): self.updateColor(fixture)

    @classmethod
    def update(self, fixture):
        self.updateDimmer(fixture)
        self.updateColor(fixture)

    @classmethod
    def updateDimmer(self, fixture):
        dimmer = fixture.updateDimmer()

    @classmethod
    def updateColor(self, fixture):
        color = fixture.updateColor()

    @classmethod
    def select(self, fixture):
        fixture.objects['emitter'].object.select_set(True)

# Operators

class DMX_TubeFixture_Operator():
    name: StringProperty(
        name="Name",
        default="Tube")

    model: EnumProperty(
        name = "Model",
        description = "Tube Fixture Model",
        items=DMX_TubeFixture.MODELS)

    address: IntProperty(
        name = "Address",
        description = "DMX Address",
        default = 1,
        min = 1,
        max = 512)

    emission: FloatProperty(
        name = "Emission",
        description = "Tube Fixture Emission",
        default = 10,
        min = 1,
        max = 1000)

    length: FloatProperty(
        name = "Length",
        description = "Tube Fixture Length",
        default = 1.2,
        min = 0.1,
        max = 10)

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
        col.prop(self, "model")
        col.prop(self, "address")
        col.prop(self, "emission")
        col.prop(self, "length")
        col.prop(self, "default_color")

class DMX_OT_Fixture_AddTube(Operator, DMX_TubeFixture_Operator):
    bl_label = "Add Tube"
    bl_idname = "dmx.add_tube_fixture"
    bl_options = {'UNDO'}
    
    def execute(self, context):
        scene = context.scene
        dmx = scene.dmx
        if (self.name in bpy.data.collections):
            return {'CANCELLED'}
        dmx.addTubeFixture(self.name, self.model, self.address, self.emission, self.length, list(self.default_color))
        return {'FINISHED'}

    def invoke(self, context, event):
        self.name = "Tube "+str(len(context.scene.dmx.fixtures)+1)
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

class DMX_OT_Fixture_EditTube(Operator, DMX_TubeFixture_Operator):
    bl_label = "DMX: Edit Tube"
    bl_idname = "dmx.edit_tube_fixture"

    def execute(self, context):
        scene = context.scene
        dmx = scene.dmx
        fixture = dmx.fixtures[scene.dmx.fixture_list_i]
        if (self.name != fixture.name and self.name in bpy.data.collections):
            return {'CANCELLED'}
        model_params = {'emission':self.emission, 'length':self.length}
        fixture.edit(self.name, self.model, self.address, model_params, list(self.default_color))
        return {'FINISHED'}

    def invoke(self, context, event):
        scene = context.scene
        fixture = scene.dmx.fixtures[scene.dmx.fixture_list_i]
        self.name = fixture.name
        self.model = fixture.model
        self.address = fixture.address
        self.emission = fixture.model_params['emission'].value
        self.length = fixture.model_params['length'].value
        self.default_color = (fixture.dmx_params['R'].default,fixture.dmx_params['G'].default,fixture.dmx_params['B'].default,1)
        wm = context.window_manager
        return wm.invoke_props_dialog(self)
