#
#   BlendexDMX > Fixture
#   Base class for a light fixture
#
#   http://www.github.com/hugoaboud/BlenderDMX
#

import bpy

from dmx.util import getMesh, getBodyMaterial, getSurfaceMaterial

class Fixture():
    def __init__(self, dmx, name, address, model, emission, default_color, createObjs):
        # DMX object
        self.dmx = dmx

        # Data Properties
        self.name = name
        self.model = model

        # TODO: take these from profile
        self.emission = emission
        self.default_color = default_color

        # DMX Properties
        self.address = address

        # Fixture (collection) with this name already exists, delete it
        if (name in bpy.data.collections):
            bpy.data.collections.remove(bpy.data.collections[name])

        # Create collection
        bpy.ops.collection.create(name=name)
        self.collection = bpy.data.collections[name]

        # Unlink any objects/collections
        # (Blender creates the collection with selected objects/collections)
        for c in self.collection.objects:
            self.collection.objects.unlink(c)
        for c in self.collection.children:
            self.collection.children.unlink(c)

        # If this fixture should create model objects
        # TODO: reorganize this
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
        material.shadow_method = 'NONE'

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
                self.surface.data.materials.append(getSurfaceMaterial())

            material.shadow_method = 'NONE'
            self.surface.cycles_visibility.shadow = False

            constraint = self.surface.constraints.new('COPY_LOCATION')
            constraint.target = self.body

    # Interface Methods #

    def icon(self):
        return ''

    def setDimmer(self, dimmer):
        pass

    def setColor(self, color):
        pass

    def clear(self):
        self.setDimmer(0)
        self.setColor(self.default_color)
