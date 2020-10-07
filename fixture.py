#
#   BlendexDMX > Fixture
#   Base class for a light fixture
#
#   http://www.github.com/hugoaboud/BlenderDMX
#

import bpy

from dmx.util import getBodyMaterial, getSurfaceMaterial

from dmx.model import populateCollection

from dmx.param import DMX_Param, DMX_Model_Param

from dmx.fixtures.spot import DMX_SpotFixture

from bpy.props import (IntProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       PointerProperty,
                       StringProperty,
                       CollectionProperty)

from bpy.types import (PropertyGroup,
                       Collection,
                       Object,
                       NodeTree)

class DMX_Fixture_Object(PropertyGroup):
    object: PointerProperty(
        name = "Fixture > Collection",
        type = Object)

class DMX_Fixture(PropertyGroup):

    # Blender RNA #

    collection: PointerProperty(
        name = "Fixture > Collection",
        type = Collection)

    objects: CollectionProperty(
        name = "Fixture > Objects",
        type = DMX_Fixture_Object
    )

    emitter_nodes: PointerProperty(
        name = "Fixture > Emitter Nodes",
        type = NodeTree)

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
    def _create(self, model, name, address, emission, default_color):

        # Data Properties
        self.model = model
        self.name = name

        # Create default model parameters
        self.model_params.add()
        self.model_params[-1].name = 'emission'
        self.model_params[-1].value = emission
        self.model_params.add()
        self.model_params[-1].name = 'default_R'
        self.model_params[-1].value = default_color[0]
        self.model_params.add()
        self.model_params[-1].name = 'default_G'
        self.model_params[-1].value = default_color[1]
        self.model_params.add()
        self.model_params[-1].name = 'default_B'
        self.model_params[-1].value = default_color[2]

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
        self.dmx_params.add()
        self.dmx_params[-1].name = 'R'
        self.dmx_params.add()
        self.dmx_params[-1].name = 'G'
        self.dmx_params.add()
        self.dmx_params[-1].name = 'B'

        # Populate collection with objects loaded from the model
        components = populateCollection(self.collection, model)

        # No components means the object will be generated using primitives
        # by the fixture sub class, so nothing to link here
        if (not components):
            return

        # Emitter
        self.objects.add()
        self.objects[-1].name = 'emitter'
        self.objects[-1].object = components['emitter']
        emitter = self.objects[-1].object
        fixture.__annotations__['emitter_strength'] = emitter.active_material.node_tree.nodes[1].inputs['Strength']
        fixture.__annotations__['emitter_color'] = emitter.active_material.node_tree.nodes[1].inputs['Color']

        # Set emission and default color (white)
        fixture.__annotations__['emitter_strength'].default_value = self.model_params['emission'].value
        fixture.__annotations__['emitter_color'].default_value = (self.model_params['default_R'].value,self.model_params['default_G'].value,self.model_params['default_B'].value,1)

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

        # Clear fixture
        self.clear()

    # Interface Methods #

    def icon(self):
        return self.__annotations__['subcls'].icon()

    def setDMX(self, pvalues):
        self.__annotations__['subcls'].setDMX(self, pvalues)

    def updateDimmer(self):
        dimmer = self.dmx_params['dimmer'].value
        self.__annotations__['emitter_strength'].default_value = self.model_params['emission'].value*dimmer
        return dimmer

    def updateColor(self):
        color = [self.dmx_params['R'].value,self.dmx_params['G'].value,self.dmx_params['B'].value,1]
        self.__annotations__['emitter_color'].default_value = color
        return color

    def select(self):
        self.__annotations__['subcls'].select(self)

    def clear(self):
        self.dmx_params['dimmer'].value = 0
        self.dmx_params['R'].value = self.model_params['default_R'].value
        self.dmx_params['G'].value = self.model_params['default_G'].value
        self.dmx_params['B'].value = self.model_params['default_B'].value
