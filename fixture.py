#
#   BlendexDMX > Fixture
#   Base class for a lighting fixture
#
#   http://www.github.com/hugoaboud/BlenderDMX
#

import bpy
import math
import mathutils

from dmx.material import getEmitterMaterial
from dmx.model import DMX_Model
from dmx.logging import DMX_Log

from dmx.param import DMX_Param, DMX_Model_Param

from dmx.gdtf import DMX_GDTF
from dmx.data import DMX_Data
from dmx.util import cmy_to_rgb

from bpy.props import (IntProperty,
                       FloatProperty,
                       BoolProperty,
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

class DMX_Emitter_Material(PropertyGroup):
    material: PointerProperty(
        name = "Emitter > Material",
        type = Material)

class DMX_Fixture_Channel(PropertyGroup):
    id: StringProperty(
        name = "Fixture > Channel > ID",
        default = '')
    default: IntProperty(
        name = "Fixture > Channel > Default",
        default = 0)
    geometry: StringProperty(
        name = "Fixture > Geometry",
        default = '')

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

    emitter_materials: CollectionProperty(
        name = "Fixture > Materials",
        type = DMX_Emitter_Material)

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
        
    display_beams: BoolProperty(
        name = "Display beams",
        description="Display beam projection and cone",
        default = True)

    gel_color: FloatVectorProperty(
        name = "Gel Color",
        subtype = "COLOR",
        size = 4,
        min = 0.0,
        max = 1.0,
        default = (1.0,1.0,1.0,1.0))

    def build(self, name, profile, mode, universe, address, gel_color, display_beams, mvr_position = None):

        # (Edit) Store objects positions
        old_pos = {obj.name:obj.object.location.copy() for obj in self.objects}
        
        # (Edit) Collection with this name already exists, delete it
        if (self.name in bpy.data.collections):
            for obj in bpy.data.collections[self.name].objects:
                bpy.data.objects.remove(obj)
            bpy.data.collections.remove(bpy.data.collections[self.name])

        # Data Properties
        self.name = name
        self.profile = profile
        self.mode = mode

        # DMX Properties
        self.universe = universe
        self.address = address
        self.gel_color = list(gel_color)
        self.display_beams = display_beams

        # (Edit) Clear links and channel cache
        self.lights.clear()
        self.objects.clear()
        self.channels.clear()

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
        model_collection = DMX_Model.getFixtureModelCollection(gdtf_profile, self.mode, self.display_beams)
        links = {}
        for obj in model_collection.objects:
            # Copy object
            links[obj.name] = obj.copy()
            # If light, copy object data
            if (obj.type == 'LIGHT'):
                links[obj.name].data = obj.data.copy()
                self.lights.add()
                light_name=f'Light{len(self.lights)}'
                self.lights[-1].name = light_name
                self.lights[light_name].object = links[obj.name]
            # Store reference to body, base and target
            if ('Base' in obj.name):
                self.objects.add()
                self.objects[-1].name = 'Base'
                self.objects['Base'].object = links[obj.name]
            elif ('Body' in obj.name):
                self.objects.add()
                self.objects[-1].name = 'Body'
                self.objects['Body'].object = links[obj.name]
            elif ('Head' in obj.name):
                self.objects.add()
                self.objects[-1].name = 'Head'
                self.objects['Head'].object = links[obj.name]
            elif ('Target' in obj.name):
                self.objects.add()
                self.objects[-1].name = 'Target'
                self.objects['Target'].object = links[obj.name]
            # Link new object to collection
            self.collection.objects.link(links[obj.name])

        # Relink constraints
        for obj in self.collection.objects:
            for constraint in obj.constraints:
                constraint.target = links[constraint.target.name]

        # (Edit) Reload old position
        bpy.context.view_layer.update()
        for obj in self.objects:
            if (obj.name in old_pos):
                obj.object.location = old_pos[obj.name]
            elif (obj.name == 'Base'):
                if ('Body' in old_pos):
                    obj.object.location = old_pos['Body']
            elif (obj.name == 'Body'):
                if ('Base' in old_pos):
                    obj.object.location = old_pos['Base']

        # Set position from MVR
        if mvr_position is not None:
            for obj in self.objects:
                if (obj.name == 'Base'):
                    obj.object.matrix_world=mvr_position.matrix
                elif (obj.name == 'Body'):
                    obj.object.matrix_world=mvr_position.matrix

        # Setup emitter
        for obj in self.collection.objects:
            if "beam" in obj.name.lower():
                emitter = obj
                self.emitter_materials.add()
                self.emitter_materials[-1].name = obj.name

                emitter_material = getEmitterMaterial(obj.name)
                emitter.active_material = emitter_material
                emitter.material_slots[0].link = 'OBJECT'
                emitter.material_slots[0].material = emitter_material
                emitter.material_slots[0].material.shadow_method = 'NONE' # eevee
                self.emitter_materials[-1].material = emitter_material


        # Link collection to DMX collection
        bpy.context.scene.dmx.collection.children.link(self.collection)

        # Set Pigtail visibility
        for obj in self.collection.objects:
            if "Pigtail" in obj.name:
                obj.hide_set(not bpy.context.scene.dmx.display_pigtails)

        # Build DMX channels cache
        for ch in DMX_GDTF.getChannels(gdtf_profile, self.mode):
            self.channels.add()
            self.channels[-1].id = ch['id']
            self.channels[-1].default = ch['default']
            self.channels[-1].geometry = ch['geometry']
        
        self.clear()
        bpy.context.scene.dmx.render()
    
    # Interface Methods #

    def setDMX(self, pvalues):
        channels = [c.id for c in self.channels]
        for param, value in pvalues.items():
            for idx, channel in enumerate(channels):
                if channel == param:
                    DMX_Data.set(self.universe, self.address+idx, value)

    def render(self):
        channels = [c.id for c in self.channels]
        data = DMX_Data.get(self.universe, self.address, len(channels))
        panTilt = [None,None]
        rgb = [None,None,None]
        cmy = [None,None,None]
        zoom = None
        mixing={} #for now, only RGB mixing is per geometry
        for c in range(len(channels)):
            geometry=self.channels[c].geometry
            if geometry not in mixing.keys():
                mixing[geometry]=[None, None, None]
            if (channels[c] == 'Dimmer'): self.updateDimmer(data[c])
            elif (channels[c] == 'ColorAdd_R'): mixing[geometry][0] = data[c]
            elif (channels[c] == 'ColorAdd_G'): mixing[geometry][1] = data[c]
            elif (channels[c] == 'ColorAdd_B'): mixing[geometry][2] = data[c]
            elif (channels[c] == 'ColorSub_C'): cmy[0] = data[c]
            elif (channels[c] == 'ColorSub_M'): cmy[1] = data[c]
            elif (channels[c] == 'ColorSub_Y'): cmy[2] = data[c]
            elif (channels[c] == 'Pan'): panTilt[0] = data[c]
            elif (channels[c] == 'Tilt'): panTilt[1] = data[c]
            elif (channels[c] == 'Zoom'): zoom = data[c]
       
        for geometry, rgb in mixing.items():
            if (rgb[0] != None and rgb[1] != None and rgb[2] != None):
                if len(mixing) == 1 or not self.light_object_for_geometry_exists(mixing): 
                    # do not apply for simple devices as trickle down is not implemented...
                    self.updateRGB(rgb, None)
                else:
                    self.updateRGB(rgb, geometry)
        
        if (cmy[0] != None and cmy[1] != None and cmy[2] != None):
            self.updateCMY(cmy)

        if (panTilt[0] != None and panTilt[1] != None):
            self.updatePanTilt(panTilt[0], panTilt[1])
        if (zoom != None):
            self.updateZoom(zoom)

    def light_object_for_geometry_exists(self, mixing):
        """Check if there is any light or emitter matching geometry name of a color attribute"""
        for geo in mixing.keys():
            for light in self.lights:
                if geo in light.object.data.name:
                    return True
            for emitter_material in self.emitter_materials:
                if geo in emitter_material.name:
                    return True
        return False

    def updateDimmer(self, dimmer):
        try:
            for emitter_material in self.emitter_materials:
                emitter_material.material.node_tree.nodes[1].inputs[STRENGTH].default_value = 10*(dimmer/255.0)
            for light in self.lights:
                light.object.data.energy = (dimmer/255.0) * light.object.data['flux']
        except Exception as e:
            print("Error updating dimmer", e)
                
        return dimmer

    def updateRGB(self, rgb, geometry):
        DMX_Log.log.info(("color change for geometry", geometry))
        try:
            rgb = [c/255.0-(1-gel) for (c, gel) in zip(rgb, self.gel_color[:3])]
            #rgb = [c/255.0 for c in rgb]
            for emitter_material in self.emitter_materials:
                DMX_Log.log.info(("emitter:", emitter_material.name))
                if geometry is not None:
                    if f"{geometry}" in emitter_material.name:
                        DMX_Log.log.info("matched emitter")
                        emitter_material.material.node_tree.nodes[1].inputs[COLOR].default_value = rgb + [1]
                else:
                    emitter_material.material.node_tree.nodes[1].inputs[COLOR].default_value = rgb + [1]
            for light in self.lights:
                if geometry is not None:
                    DMX_Log.log.info(("light:", light.object.data.name))
                    if f"{geometry}" in light.object.data.name:
                        DMX_Log.log.info("matched light")
                        light.object.data.color = rgb
                else:
                    light.object.data.color = rgb
        except Exception as e:
            print("Error updating RGB", e)
        return rgb


    def updateCMY(self, cmy):
        rgb=[0,0,0]
        rgb=cmy_to_rgb(cmy)
        rgb = [c/255.0-(1-gel) for (c, gel) in zip(rgb, self.gel_color[:3])]
        #rgb = [c/255.0 for c in rgb]
        for emitter_material in self.emitter_materials:
            emitter_material.material.node_tree.nodes[1].inputs[COLOR].default_value = rgb + [1]
        for light in self.lights:
            light.object.data.color = rgb
        return cmy

    def updateZoom(self, zoom):
        try:
            spot_size=zoom*3.1415/180.0
            for light in self.lights:
                light.object.data.spot_size=spot_size
        except Exception as e:
            print("Error updating zoom", e)
        return zoom


    def updatePanTilt(self, pan, tilt):
        pan = (pan/127.0-1)*355*(math.pi/360)
        tilt = (tilt/127.0-1)*130*(math.pi/180)

        base = self.objects['Base'].object
        head_location = self.objects['Head'].object.matrix_world.translation
        target = self.objects['Target'].object
        
        eul = mathutils.Euler((0.0,base.rotation_euler[1]+tilt,base.rotation_euler[0]+pan), 'XYZ')
        vec = mathutils.Vector((0.0,0.0,-(target.location-head_location).length))
        vec.rotate(eul)

        target.location = vec + head_location

    def getProgrammerData(self):
        channels = [c.id for c in self.channels]
        data = DMX_Data.get(self.universe, self.address, len(channels))
        params = {}
        for c in range(len(channels)):
            params[channels[c]] = data[c]
        return params

    def select(self):
        if ('Body' in self.objects):
            self.objects['Body'].object.select_set(True)
        elif ('Base' in self.objects):
            self.objects['Base'].object.select_set(True)
    
    def unselect(self):
        if ('Body' in self.objects):
            self.objects['Body'].object.select_set(False)
        elif ('Base' in self.objects):
            self.objects['Base'].object.select_set(False)
        if ('Target' in self.objects):
            self.objects['Target'].object.select_set(False)

    def toggleSelect(self):
        selected = False
        for obj in self.objects:
            if (obj.object in bpy.context.selected_objects):
                selected = True
                break
        if (selected): self.unselect()
        else: self.select()

    def clear(self):
        for i, ch in enumerate(self.channels):
            data = DMX_Data.set(self.universe, self.address+i, ch.default)

    def onDepsgraphUpdate(self):
        # Check if any object was deleted
        for obj in self.objects:
            if (not len(obj.object.users_collection)):
                bpy.context.scene.dmx.removeFixture(self)
                break
