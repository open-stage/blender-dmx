#
#   BlendexDMX > Fixtures > Tube
#   Tube Fixture, with a tubular emitter
#   This fixture doesn't load any model, instead it creates a cylinder primitive
#   according to the model diameter.
#
#   http://www.github.com/hugoaboud/BlenderDMX
#

import bpy
from dmx.fixture import Fixture

class TubeFixture(Fixture):
    def __init__(self, dmx, name, address, model, emission, length, default_color):
        # DMX
        super().__init__(dmx, name, address, model, emission, default_color, False)
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

        self.setColor(default_color)

    def edit(self, name, address, model, length, emission, default_color):
        self.name = name
        self.collection.name = name
        self.address = address
        self.length = length
        self.emission = emission
        self.emitter_power.default_value = emission
        self.default_color = default_color

    def icon(self):
        return 'MESH_CYLINDER'

    def setDimmer(self, dimmer):
        self.emitter_power.default_value = dimmer*self.emission

    def setColor(self, color):
        self.emitter_color.default_value = color
