#
#   BlendexDMX > Fixture
#   Base class for a light fixture
#
#   http://www.github.com/hugoaboud/BlenderDMX
#

import bpy

from dmx.material import getEmitterMaterial
from dmx.model import getFixtureModelCollection

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
        name = "Fixture > Object",
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

    lights: CollectionProperty(
        name = "Fixture > Lights",
        type = DMX_Fixture_Object
    )

    emitter_material: PointerProperty(
        name = "Fixture > Emitter Material",
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

        # Create clean Collection
        # (Blender creates the collection with selected objects/collections)
        bpy.ops.collection.create(name=name)
        self.collection = bpy.data.collections[name]

        for c in self.collection.objects:
            self.collection.objects.unlink(c)
        for c in self.collection.children:
            self.collection.children.unlink(c)

        # Import and deep copy Fixture Model Collection
        if (model):
            self.model = model
            model_collection = getFixtureModelCollection(model)
            links = {}
            for obj in model_collection.objects:
                # Copy object
                links[obj] = obj.copy()
                # If light, copy object data
                if (obj.type == 'LIGHT'):
                    links[obj].data = obj.data.copy()
                # Store reference to body and target
                if ('Body' in obj.name):
                    self.objects.add()
                    self.objects[-1].name = 'Body'
                    self.objects['Body'].object = links[obj]
                elif ('Target' in obj.name):
                    self.objects.add()
                    self.objects[-1].name = 'Target'
                    self.objects['Target'].object = links[obj]
                # Link new object to collection
                self.collection.objects.link(links[obj])

            # Relink constraints
            for obj in self.collection.objects:
                for constraint in obj.constraints:
                    constraint.target = links[constraint.target]

            # Setup emitter
            for obj in self.collection.objects:
                if ('Emitter' in obj.name):
                    emitter = obj
            assert emitter

            material = getEmitterMaterial(name)
            emitter.active_material = material
            emitter.material_slots[0].link = 'OBJECT'
            emitter.material_slots[0].material = material
            emitter.material_slots[0].material.shadow_method = 'NONE' # eevee

            self.emitter_material = emitter.material_slots[0].material
            self.emitter_material.node_tree.nodes[1].inputs['Strength'].default_value = self.model_params['emission'].value

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
