#
#   BlendexDMX > Fixtures > Spot
#   Fixed Spot Fixture, with an emitter and a spot light source.
#   An empty object is created as a target to allow for easy design.
#
#   http://www.github.com/hugoaboud/BlenderDMX
#

import bpy
from dmx.fixture import *

class DMX_SpotFixture():

    @classmethod
    def create(self, fixture, model, name, address, emission, default_color, angle, power):

        # Define subclass so the DMX_Fixture class can store a reference to it
        fixture.subclass = 'DMX_SpotFixture'
        fixture.__annotations__['subcls'] = DMX_SpotFixture

        # Create generic fixture from model
        fixture._create(model, name, address, emission, default_color)

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

    def edit(self, name, address, model, power, emission, angle, default_color):
        self.name = name
        self.collection.name = name
        self.address = address
        self.power = power
        self.spot.data.energy = power
        self.emission = emission
        self.emitter_power.default_value = emission
        self.angle = angle
        self.spot.data.spot_size = (angle/180.0)*3.141516
        self.default_color = default_colors
        self.setColor(default_color)

    @classmethod
    def icon(self):
        return 'LIGHT_SPOT'

    @classmethod
    def setDMX(self, fixture, pvalues):
        # State variable to call update color only once if RGB change simultaneously
        updateColor = False

        print("pvalues", pvalues)

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
