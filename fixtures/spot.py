#
#   BlendexDMX > Fixtures > Spot
#   Fixed Spot Fixture, with an emitter and a spot light source.
#   An empty object is created as a target to allow for easy design.
#
#   http://www.github.com/hugoaboud/BlenderDMX
#

import bpy
from dmx.fixture import Fixture

class SpotFixture(Fixture):
    def __init__(self, dmx, name, address, model, emission, power, angle, default_color):
        # base
        super().__init__(dmx, name, address, model, emission, default_color, True)

        # Properties
        self.power = power
        self.angle = angle

        if (model == 'par64'): radius = 0.1
        elif (model == 'parled64' or model == 'sourcefour'): radius = 0.12

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
        self.emitter.hide_select = True

        # Surface
        if (self.surface):
            constraint = self.surface.constraints.new('TRACK_TO')
            constraint.target = self.target
            constraint.track_axis = 'TRACK_NEGATIVE_Z'
            constraint.up_axis = 'UP_Y'
            self.surface.hide_select = True

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

        self.setColor(default_color)

        # Link collection to scene
        dmx.collection.children.link(self.collection)

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

    def icon(self):
        return 'LIGHT_SPOT'

    def setDimmer(self, dimmer):
        self.spot.data.energy = self.power*dimmer
        self.emitter_power.default_value = self.emission*dimmer

    def setColor(self, color):
        self.spot.data.color = color[:3]
        self.emitter_color.default_value = color
