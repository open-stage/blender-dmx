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
    # If this is None, the models will be loaded based on the prefix
    MODELS = (
        ('t8','T8','T8, diam: 1"','',0),
        ('t5','t5','T5, diam: 5/8"','',1),
    )
    PREFIX = "Tube"

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

        # Create emitter from Primitive
        bpy.ops.mesh.primitive_cylinder_add(vertices=resolution, radius=radius, depth=length)
        fixture.objects.add()
        fixture.objects[-1].name = 'Emitter'
        fixture.objects[-1].object = bpy.context.active_object
        emitter = fixture.objects['Emitter'].object
        emitter.name = 'Emitter'
        bpy.ops.collection.objects_remove_all()
        fixture.collection.objects.link(emitter)

        # Assign material to emitter
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
        fixture.objects['Emitter'].object.select_set(True)
