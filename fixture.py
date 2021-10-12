#
#   BlendexDMX > Fixture
#   Base class for a lighting fixture
#
#   http://www.github.com/hugoaboud/BlenderDMX
#

import bpy

from dmx.material import getEmitterMaterial
from dmx.model import DMX_Model

from dmx.param import DMX_Param, DMX_Model_Param

from dmx.gdtf import DMX_GDTF
from dmx.data import DMX_Data

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

# Shader Nodes default labels
# Blender API naming convention is inconsistent for internationalization
# Every label used is listed here, so it's easier to fix it on new API updates
STRENGTH = "Strength"
COLOR = "Color"

class DMX_Fixture_Object(PropertyGroup):
    object: PointerProperty(
        name = "Fixture > Object",
        type = Object)

class DMX_Fixture_Channel(PropertyGroup):
    id: StringProperty(
        name = "Fixture > Channel > ID",
        default = '')
    default: IntProperty(
        name = "Fixture > Channel > Default",
        default = 0)

class DMX_Fixture(PropertyGroup):

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

    # DMX properties

    profile: StringProperty(
        name = "Fixture > Profile",
        default = "")
    
    mode : StringProperty(
        name = "Fixture > Mode",
        description="Fixture DMX Mode",
        default = '')
    
    channels: CollectionProperty(
        name = "Fixture > Channels",
        type = DMX_Fixture_Channel
    )

    universe : IntProperty(
        name = "Fixture > Universe",
        description="Fixture DMX Universe",
        default = 0,
        min = 0,
        max = 511)

    address : IntProperty(
        name = "Fixture > Address",
        description="Fixture DMX Address",
        default = 1,
        min = 1,
        max = 512)
        
    gel_color: FloatVectorProperty(
        name = "Gel Color",
        subtype = "COLOR",
        size = 4,
        min = 0.0,
        max = 1.0,
        default = (1.0,1.0,1.0,1.0))

    def create(self, name, profile, mode, universe, address, gel_color):

        # Data Properties
        self.name = name
        self.profile = profile
        self.mode = mode

        # DMX Properties
        self.universe = universe
        self.address = address
        self.gel_color = gel_color

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
        gdtf_profile = DMX_GDTF.loadProfile(profile)
        model_collection = DMX_Model.getFixtureModelCollection(gdtf_profile)
        links = {}
        for obj in model_collection.objects:
            # Copy object
            links[obj] = obj.copy()
            # If light, copy object data
            if (obj.type == 'LIGHT'):
                links[obj].data = obj.data.copy()
                self.lights.add()
                self.lights[-1].name = 'Light'
                self.lights['Light'].object = links[obj]
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
            if ('Beam' in obj.name):
                emitter = obj
        assert emitter

        self.emitter_material = getEmitterMaterial(name)
        emitter.active_material = self.emitter_material
        emitter.material_slots[0].link = 'OBJECT'
        emitter.material_slots[0].material = self.emitter_material
        emitter.material_slots[0].material.shadow_method = 'NONE' # eevee

        
        #self.emitter_material.node_tree.nodes[1].inputs[STRENGTH].default_value = self.model_params['emission'].value

        # Link collection to DMX collection
        bpy.context.scene.dmx.collection.children.link(self.collection)

        # Build DMX channels cache
        for ch in DMX_GDTF.getChannels(gdtf_profile, self.mode):
            self.channels.add()
            self.channels[-1].id = ch['id']
            self.channels[-1].default = ch['default']
        

    def edit(self, name, profile, universe, address, mode, gel_color):
        gdtf_profile = DMX_GDTF.loadProfile(profile)
        self.create(name, profile, gdtf_profile, universe, address, mode, gel_color)

    # Interface Methods #

    def setDMX(self, pvalues):
        channels = [c.id for c in self.channels]
        for param, value in pvalues.items():
            if (param not in channels): return
            p = channels.index(param)
            DMX_Data.set(self.universe, self.address+p, value)

    def render(self):
        channels = [c.id for c in self.channels]
        data = DMX_Data.get(self.universe, self.address, len(channels))
        panTilt = [None,None]
        rgb = [None,None,None]
        for c in range(len(channels)):
            if (channels[c] == 'Dimmer'): self.updateDimmer(data[c])
            elif (channels[c] == 'R'): rgb[0] = data[c]
            elif (channels[c] == 'G'): rgb[1] = data[c]
            elif (channels[c] == 'B'): rgb[2] = data[c]
        
        if (rgb[0] != None and rgb[1] != None and rgb[2] != None):
            self.updateRGB(rgb)

    def updateDimmer(self, dimmer):
        self.emitter_material.node_tree.nodes[1].inputs[STRENGTH].default_value = 10*(dimmer/255.0)
        for light in self.lights:
            light.object.data.energy = (dimmer/255.0) * light.object.data['flux']
        return dimmer

    def updateRGB(self, rgb):
        rgb = [c/255.0 for c in rgb]
        self.emitter_material.node_tree.nodes[1].inputs[COLOR].default_value = rgb + [1]
        for light in self.lights:
            light.object.data.color = rgb
        return rgb

    def select(self):
        if ('Body' in self.objects):
            self.objects['Body'].object.select_set(True)

    def clear(self):
        pass
        """
        self.channels = DMX_Fixture_Channels.cache[self.profile]
        for dmx_param in self.channels:
            dmx_param.toDefault()
        self.update()
        """
