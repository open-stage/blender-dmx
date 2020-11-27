#
#   BlendexDMX > Fixtures > Spot
#   Fixed Spot Fixture, with an emitter and a spot light source.
#   An empty object is created as a target to allow for easy design.
#
#   http://www.github.com/hugoaboud/BlenderDMX
#

import bpy
from mathutils import Vector
from math import sin, cos, pi

from dmx.fixture import DMX_Fixture

from bpy.props import (BoolProperty,
                       IntProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       EnumProperty,
                       StringProperty)

from bpy.types import Operator

class DMX_SpotFixture():

    # Models that can be assigned to this type of fixture

    MODELS = (
        ('par_64','Par 64','Par Can, diam: 8"','ANTIALIASED',0),
        ('source_four','Ellipsoidal','ETC Source Four, Ellipsoidal Reflector Spotlight','PMARKER_SEL',1),
        ('source_four_par','Source Par','ETC Source Four PAR','ALIASED',2),
        ('parled_64','Par LED 64','Par LED 64','SEQ_CHROMA_SCOPE',3),
        ('moving_beam','Moving Beam 5R','Moving Beam 5R','CURSOR',4)
    )

    # Fixture Icon

    @classmethod
    def icon(self):
        return 'LIGHT_SPOT'

    # Create / Edit

    @classmethod
    def create(self, fixture, name, model, address, moving, emission, power, angle, focus, default_color):

        # Define subclass so the DMX_Fixture class can store a reference to it
        fixture.subclass = 'spot.DMX_SpotFixture'
        if (fixture.subclass not in DMX_Fixture.subclasses):
            DMX_Fixture.subclasses[fixture.subclass] = DMX_SpotFixture

        # Create generic fixture from model
        fixture._create(name, model, address, emission, default_color)

        # DMX Parameters
        fixture.dmx_params.add()
        fixture.dmx_params[-1].name = 'pan'
        fixture.dmx_params[-1].default = 0.5
        fixture.dmx_params.add()
        fixture.dmx_params[-1].name = 'tilt'
        fixture.dmx_params[-1].default = 0.5

        # Model Parameters
        fixture.model_params.add()
        fixture.model_params[-1].name = 'power'
        fixture.model_params[-1].value = power
        fixture.model_params.add()
        fixture.model_params[-1].name = 'angle'
        fixture.model_params[-1].value = angle
        fixture.model_params.add()
        fixture.model_params[-1].name = 'focus'
        fixture.model_params[-1].value = focus
        fixture.model_params.add()
        fixture.model_params[-1].name = 'moving'
        fixture.model_params[-1].value = moving

        # Light source settings
        for obj in fixture.collection.objects:
            if (obj.type == 'LIGHT'):
                obj.data.energy = power
                obj.data.spot_size = (angle/180.0)*3.141516
                obj.data.spot_blend = focus
                obj.data.color = (fixture.dmx_params['R'].default,fixture.dmx_params['G'].default,fixture.dmx_params['B'].default)
                fixture.lights.add()
                fixture.lights[-1].object = obj
        fixture.clear()

    @classmethod
    def edit(self, fixture):
        fixture.lights[0].object.data.energy = fixture.model_params['power'].value
        fixture.lights[0].object.data.spot_size = (fixture.model_params['angle'].value/180.0)*3.141516
        fixture.lights[0].object.data.spot_blend = fixture.model_params['focus'].value
        # TODO: change model (?)

    # DMX

    @classmethod
    def setDMX(self, fixture, pvalues):
        # State variable to call update color only once if RGB change simultaneously
        updateColor = False
        # State variable to call update pan/tilt only once if Pan/Tilt change simultaneously
        updatePanTilt = False

        # Update dmx parameters if they are available on the fixture
        for param, value in pvalues.items():
            if (param in fixture.dmx_params):
                fixture.dmx_params[param].value = value
                # Update fixture parameters (single parameters)
                if (param == 'dimmer'): self.updateDimmer(fixture)
                # Mark cumulative color parameters to be updated
                if (param == 'R' or param == 'G' or param == 'B'): updateColor = True
                # If is moving fixture, mark cumulative parameters to be updated
                if (fixture.model_params['moving'].value and (param == 'pan' or param == 'tilt')): updatePanTilt = True

        # Update fixture parameters (cumulative parameters)
        if (updateColor): self.updateColor(fixture)
        if (updatePanTilt): self.updatePanTilt(fixture)

    @classmethod
    def update(self, fixture):
        self.updateDimmer(fixture)
        self.updateColor(fixture)
        self.updatePanTilt(fixture)

    @classmethod
    def updateDimmer(self, fixture):
        dimmer = fixture.updateDimmer()
        fixture.lights[0].object.data.energy = fixture.model_params['power'].value*dimmer

    @classmethod
    def updateColor(self, fixture):
        color = fixture.updateColor()
        fixture.lights[0].object.data.color = color[:3]

    @classmethod
    def updatePanTilt(self, fixture):

        pan = fixture.dmx_params['pan'].value*2-1
        tilt = fixture.dmx_params['tilt'].value*2-1

        pan_axis = sin(pan*pi)*Vector((0,1,0))+cos(pan*pi)*Vector((1,0,0))
        axis = sin(tilt*pi/2)*pan_axis+cos(tilt*pi/2)*Vector((0,0,-1))
        axis *= 2

        fixture.objects['Target'].object.location = fixture.objects['Body'].object.matrix_local @ axis

    @classmethod
    def select(self, fixture):
        fixture.objects['Body'].object.select_set(True)

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

    moving: BoolProperty(
        name = "Moving",
        description = "Spot Fixture Moving",
        default = False)

    emission: FloatProperty(
        name = "Emission",
        description = "Spot Fixture Emission",
        default = 10,
        min = 1,
        max = 1000)

    power: FloatProperty(
        name = "Power",
        description = "Spot Fixture Power",
        default = 100,
        min = 1,
        max = 10000)

    angle: FloatProperty(
        name = "Angle",
        description = "Spot Fixture Angle",
        default = 30,
        min = 1,
        max = 180)

    focus: FloatProperty(
        name = "Focus",
        description = "Spot Fixture Focus",
        default = 0.15,
        min = 0,
        max = 1)

    default_color: FloatVectorProperty(
        name = "Default Color",
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
        col.prop(self, "model")

        if (self.model == "moving_beam"):
            self.moving = True;

        col.prop(self, "address")
        col.prop(self, "moving")
        col.prop(self, "emission")
        col.prop(self, "power")
        col.prop(self, "angle")
        col.prop(self, "focus")
        col.prop(self, "default_color")
        if (self.units > 0):
            col.prop(self, "units")

class DMX_OT_Fixture_AddSpot(Operator, DMX_SpotFixture_Operator):
    bl_label = "DMX: Add Spot Fixture"
    bl_idname = "dmx.add_spot_fixture"
    bl_options = {'UNDO'}

    def execute(self, context):
        scene = context.scene
        dmx = scene.dmx
        if (self.name in bpy.data.collections):
            return {'CANCELLED'}
        for i in range(self.units):
            dmx.addSpotFixture(self.name+str(i+1), self.model, self.address, self.moving, self.emission, self.power, self.angle, self.focus, list(self.default_color))
        return {'FINISHED'}

    def invoke(self, context, event):
        self.name = "Spot "+str(len(context.scene.dmx.fixtures)+1)
        self.units = 1
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
        model_params = {'emission':self.emission, 'power':self.power, 'angle':self.angle, 'focus':self.focus}
        fixture.edit(self.name, self.model, self.address, model_params, list(self.default_color))
        return {'FINISHED'}

    def invoke(self, context, event):
        scene = context.scene
        fixture = scene.dmx.fixtures[scene.dmx.fixture_list_i]
        self.name = fixture.name
        self.model = fixture.model
        self.address = fixture.address
        self.moving = fixture.model_params['moving'].value
        self.emission = fixture.model_params['emission'].value
        self.power = fixture.model_params['power'].value
        self.angle = fixture.model_params['angle'].value
        self.focus = fixture.model_params['focus'].value
        self.default_color = (fixture.dmx_params['R'].default,fixture.dmx_params['G'].default,fixture.dmx_params['B'].default,1)
        self.units = 0
        wm = context.window_manager
        return wm.invoke_props_dialog(self)
