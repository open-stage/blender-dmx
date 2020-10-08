#
#   BlendexDMX > Fixture
#   Base class for a light fixture
#
#   http://www.github.com/hugoaboud/BlenderDMX
#

import bpy

from dmx.util import getBodyMaterial, getSurfaceMaterial

from dmx.model import populateModel

from dmx.param import DMX_Param, DMX_Model_Param

from bpy.props import (IntProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       PointerProperty,
                       StringProperty,
                       CollectionProperty)

from bpy.types import (PropertyGroup,
                       Collection,
                       Object,
                       Material)

class DMX_Fixture_Object(PropertyGroup):
    object: PointerProperty(
        name = "Fixture > Collection",
        type = Object)

class DMX_Fixture(PropertyGroup):

    # Used to get class type from name faster
    # The values are registered by the subclasses when an object of that
    # subclass is created
    subclasses = {}

    # Blender RNA #

    collection: PointerProperty(
        name = "Fixture > Collection",
        type = Collection)

    objects: CollectionProperty(
        name = "Fixture > Objects",
        type = DMX_Fixture_Object
    )

    emitter_material: PointerProperty(
        name = "Fixture > Emitter Nodes",
        type = Material)

    # Model properties

    subclass : StringProperty(
        name = "Fixture > Subclass",
        description="Fixture Subclass Type Name")

    model : StringProperty(
        name = "Fixture > Model",
        description="Fixture 3D Model")

    model_params : CollectionProperty(
        name = "Fixture > Model Parameters",
        type = DMX_Model_Param
    )

    # DMX properties

    address : IntProperty(
        name = "Fixture > DMX Address",
        description="Fixture DMX Address",
        default = 1,
        min = 1,
        max = 512)

    dmx_params : CollectionProperty(
        name = "Fixture > DMX Parameters",
        type = DMX_Param
    )

    # A fixture should not be created with this method. Instead, use the
    # create method from the fixtures subclasses
    def _create(self, name, model, address, emission, default_color):

        # Data Properties
        self.name = name
        self.model = model

        # Create default model parameters
        self.model_params.add()
        self.model_params[-1].name = 'emission'
        self.model_params[-1].value = emission
        self.model_params.add()

        # DMX Properties
        self.address = address

        # Collection with this name already exists, delete it
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

        # Link collection to DMX collection
        bpy.context.scene.dmx.collection.children.link(self.collection)

        # Create default DMX params (dimmer + color)
        # in the future, only dimmer
        self.dmx_params.add()
        self.dmx_params[-1].name = 'dimmer'
        self.dmx_params[-1].default = 0
        self.dmx_params.add()
        self.dmx_params[-1].name = 'R'
        self.dmx_params[-1].default = default_color[0]
        self.dmx_params.add()
        self.dmx_params[-1].name = 'G'
        self.dmx_params[-1].default = default_color[1]
        self.dmx_params.add()
        self.dmx_params[-1].name = 'B'
        self.dmx_params[-1].default = default_color[2]

        # Populate collection with objects loaded from the model
        components = populateModel(self.collection, model)

        # No components means there's no mesh with this name or
        # the object will be generated using primitives
        # by the fixture sub class, so nothing to link here
        if (not components):
            return

        # Emitter
        self.objects.add()
        self.objects[-1].name = 'emitter'
        self.objects[-1].object = components['emitter']
        self.emitter_material = self.objects[-1].object.material_slots[0].material

        # Set emission (white)
        self.emitter_material.node_tree.nodes[1].inputs['Strength'].default_value = self.model_params['emission'].value

        # Body (optional)
        self.body = None
        if ('body' in components):
            self.objects.add()
            self.objects[-1].name = 'body'
            self.objects[-1].object = components['body']

        # Surface (optional)
        self.surface = None
        if ('surface' in components):
            self.objects.add()
            self.objects[-1].name = 'surface'
            self.objects[-1].object = components['surface']

    def edit(self, name, model, address, model_params, default_color):
        self.name = name
        self.collection.name = name
        #self.model = model
        self.address = address
        for param in model_params.keys():
            if (param in self.model_params):
                self.model_params[param].value = model_params[param ]
        self.dmx_params['R'].default = default_color[0]
        self.dmx_params['G'].default = default_color[1]
        self.dmx_params['B'].default = default_color[2]

        self.emitter_material.node_tree.nodes[1].inputs['Strength'].default_value = self.model_params['emission'].value*self.dmx_params['dimmer'].value

        self.subclasses[self.subclass].edit(self)

        self.update()


    # Interface Methods #

    def icon(self):
        return self.subclasses[self.subclass].icon()

    def setDMX(self, pvalues):
        self.subclasses[self.subclass].setDMX(self, pvalues)

    def update(self):
        self.subclasses[self.subclass].update(self)

    def updateDimmer(self):
        dimmer = self.dmx_params['dimmer'].value
        self.emitter_material.node_tree.nodes[1].inputs['Strength'].default_value = self.model_params['emission'].value*dimmer
        return dimmer

    def updateColor(self):
        color = [self.dmx_params['R'].value,self.dmx_params['G'].value,self.dmx_params['B'].value,1]
        self.emitter_material.node_tree.nodes[1].inputs['Color'].default_value = color
        return color

    def select(self):
        self.subclasses[self.subclass].select(self)

    def clear(self):
        for dmx_param in self.dmx_params:
            dmx_param.toDefault()
        self.update()
