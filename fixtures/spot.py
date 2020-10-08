#
#   BlendexDMX > Fixtures > Spot
#   Fixed Spot Fixture, with an emitter and a spot light source.
#   An empty object is created as a target to allow for easy design.
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

class DMX_SpotFixture():

    # Models that can be assigned to this type of fixture

    MODELS = (
        ('par64','PAR 64','Par Can, diam: 8"','ANTIALIASED',0),
        ('sourcefour','SOURCE FOUR','Source Four PAR','ALIASED',1),
        ('parled64','PAR LED 64','PAR LED 64','SEQ_CHROMA_SCOPE',2)
    )

    # Fixture Icon

    @classmethod
    def icon(self):
        return 'LIGHT_SPOT'

    # Create / Edit

    @classmethod
    def create(self, fixture, name, model, address, emission, angle, power, default_color):

        # Define subclass so the DMX_Fixture class can store a reference to it
        fixture.subclass = 'spot.DMX_SpotFixture'
        if (fixture.subclass not in DMX_Fixture.subclasses):
            DMX_Fixture.subclasses[fixture.subclass] = DMX_SpotFixture

        # Create generic fixture from model
        fixture._create(name, model, address, emission, default_color)

        # Model Parameters
        fixture.model_params.add()
        fixture.model_params[-1].name = 'angle'
        fixture.model_params[-1].value = angle
        fixture.model_params.add()
        fixture.model_params[-1].name = 'power'
        fixture.model_params[-1].value = power

        # Set light radius from model
        # TODO: take from model profile
        if (model == 'par64'): radius = 0.1
        elif (model == 'parled64' or model == 'sourcefour'): radius = 0.12

        # Body (always present and main constrain object on spot models)
        body = fixture.objects['body'].object

        ## New Objects

        # Target
        bpy.ops.object.empty_add(type='PLAIN_AXES',radius=radius,location=(0,0,-1))
        fixture.objects.add()
        fixture.objects[-1].name = 'target'
        fixture.objects[-1].object = bpy.context.active_object
        target = fixture.objects['target'].object
        target.name = "Target"
        bpy.ops.collection.objects_remove_all()
        fixture.collection.objects.link(target)

        # Spot
        light_data = bpy.data.lights.new(name="Spot", type='SPOT')
        light_data.energy = power
        light_data.spot_size = (angle/180.0)*3.141516
        light_data.shadow_soft_size = radius

        fixture.objects.add()
        fixture.objects[-1].name = 'spot'
        fixture.objects[-1].object = bpy.data.objects.new(name="Spot", object_data=light_data)
        spot = fixture.objects[-1].object

        constraint = spot.constraints.new('COPY_LOCATION')
        constraint.target = body
        constraint = spot.constraints.new('TRACK_TO')
        constraint.target = target
        constraint.track_axis = 'TRACK_NEGATIVE_Z'
        constraint.up_axis = 'UP_Y'

        spot.data.color = (fixture.dmx_params['R'].default,fixture.dmx_params['G'].default,fixture.dmx_params['B'].default)

        spot.hide_select = True
        fixture.collection.objects.link(spot)

        ## Default objects

        # Emitter
        emitter = fixture.objects['emitter'].object
        constraint = emitter.constraints.new('COPY_LOCATION')
        constraint.target = body
        constraint = emitter.constraints.new('TRACK_TO')
        constraint.target = target
        constraint.track_axis = 'TRACK_NEGATIVE_Z'
        constraint.up_axis = 'UP_Y'
        emitter.hide_select = True
        emitter.material_slots[0].material.shadow_method = 'NONE' # eevee
        emitter.cycles_visibility.shadow = False # cycles

        # Body
        body = fixture.objects['body'].object
        constraint = body.constraints.new('TRACK_TO')
        constraint.target = target
        constraint.track_axis = 'TRACK_NEGATIVE_Z'
        constraint.up_axis = 'UP_Y'

        # Surface (optional)
        if ('surface' in fixture.objects):
            surface = fixture.objects['surface'].object
            constraint = surface.constraints.new('COPY_LOCATION')
            constraint.target = body
            constraint = surface.constraints.new('TRACK_TO')
            constraint.target = target
            constraint.track_axis = 'TRACK_NEGATIVE_Z'
            constraint.up_axis = 'UP_Y'
            surface.hide_select = True
            surface.material_slots[0].material.shadow_method = 'NONE' # eevee
            surface.cycles_visibility.shadow = False # cycles

        fixture.clear()

    @classmethod
    def edit(self, fixture):
        fixture.objects['spot'].object.data.spot_size = (fixture.model_params['angle'].value/180.0)*3.141516
        fixture.objects['spot'].object.data.energy = fixture.model_params['power'].value

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
        fixture.objects['spot'].object.data.energy = fixture.model_params['power'].value*dimmer

    @classmethod
    def updateColor(self, fixture):
        color = fixture.updateColor()
        fixture.objects['spot'].object.data.color = color[:3]

    @classmethod
    def select(self, fixture):
        fixture.objects['body'].object.select_set(True)

# Operators

class DMX_SpotFixture_Operator():
    name: StringProperty(
        name="Name",
        default="Spot")

    model: EnumProperty(
        name = "Model",
        description = "Spot Fixture Model",
        items=DMX_SpotFixture.MODELS)

    address: IntProperty(
        name = "Address",
        description = "DMX Address",
        default = 1,
        min = 1,
        max = 512)

    emission: FloatProperty(
        name = "Emission",
        description = "Spot Fixture Emission",
        default = 10,
        min = 1,
        max = 1000)

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
        col.prop(self, "angle")
        col.prop(self, "power")
        col.prop(self, "default_color")

class DMX_OT_Fixture_AddSpot(Operator, DMX_SpotFixture_Operator):
    bl_label = "Add Spot"
    bl_idname = "dmx.add_spot_fixture"

    def execute(self, context):
        scene = context.scene
        dmx = scene.dmx
        if (self.name in bpy.data.collections):
            return {'CANCELLED'}
        dmx.addSpotFixture(self.name, self.model, self.address, self.emission, self.angle, self.power, list(self.default_color))
        return {'FINISHED'}

    def invoke(self, context, event):
        self.name = "Spot "+str(len(context.scene.dmx.fixtures)+1)
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

class DMX_OT_Fixture_EditSpot(Operator, DMX_SpotFixture_Operator):
    bl_label = "DMX: Edit Spot"
    bl_idname = "dmx.edit_spot_fixture"

    def execute(self, context):
        scene = context.scene
        dmx = scene.dmx
        fixture = dmx.fixtures[scene.dmx.fixture_list_i]
        if (self.name != fixture.name and self.name in bpy.data.collections):
            return {'CANCELLED'}
        model_params = {'emission':self.emission, 'angle':self.angle, 'power':self.power}
        fixture.edit(self.name, self.model, self.address, model_params, list(self.default_color))
        return {'FINISHED'}

    def invoke(self, context, event):
        scene = context.scene
        fixture = scene.dmx.fixtures[scene.dmx.fixture_list_i]
        self.name = fixture.name
        self.model = fixture.model
        self.address = fixture.address
        self.power = fixture.model_params['power'].value
        self.emission = fixture.model_params['emission'].value
        self.angle = fixture.model_params['angle'].value
        self.default_color = (fixture.dmx_params['R'].default,fixture.dmx_params['G'].default,fixture.dmx_params['B'].default,1)
        wm = context.window_manager
        return wm.invoke_props_dialog(self)
