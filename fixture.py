#
#   BlendexDMX > Fixture
#   Base class for a lighting fixture
#
#   http://www.github.com/open-stage/BlenderDMX
#

import bpy
import math
import mathutils
import uuid

from dmx.material import getEmitterMaterial
from dmx.model import DMX_Model
from dmx.logging import DMX_Log

from dmx.param import DMX_Param, DMX_Model_Param
from dmx import pygdtf

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


class DMX_Manufacturer(PropertyGroup):
    name: StringProperty (
        name = "Name",
        description = "Name of the manufacturer",
        default = "Manufacturer 0")


manufacturers: CollectionProperty(
    name = "Manufacturers",
    description = "Fixture GDTF Manufacturers",
    type = DMX_Manufacturer
)


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
    virtual_channels: CollectionProperty(
        name = "Fixture > Virtual Channels",
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

    uuid: StringProperty(
        name = "UUID",
        description = "Unique ID, used for MVR",
        default = str(uuid.uuid4())
            )
        
    fixture_id: StringProperty(
        name = "FixtureID",
        description = "The Fixture ID is an identifier for the instance of this fixture that can be used to activate / select them for programming.",
        default = ""
            )

    unit_number: IntProperty(
        name = "UnitNumber",
        description = "The identification of a fixture on its position. Use this as an alternative numbering scheme if the planning and programming numbering is different.",
        default = 0
            )

    fixture_id_numeric: IntProperty(
        name = "FixtureIDNumeric",
        description = "The Fixture ID is an identifier for the instance of this fixture that can be used to activate / select them for programming.",
        default = 0
            )

    custom_id: IntProperty(
        name = "CustomId",
        description = "The Fixture ID is an identifier for the instance of this fixture that can be used to activate / select them for programming.",
        default = 0
            )

    display_beams: BoolProperty(
        name = "Display beams",
        description="Display beam projection and cone",
        default = True)

    add_target: BoolProperty(
        name = "Add Target",
        description="Add target for beam to follow",
        default = True)

    gel_color: FloatVectorProperty(
        name = "Gel Color",
        subtype = "COLOR",
        size = 4,
        min = 0.0,
        max = 1.0,
        default = (1.0,1.0,1.0,1.0))

    def build(self, name, profile, mode, universe, address, gel_color, display_beams, add_target, mvr_position = None, 
              focus_point = None, uuid = None, fixture_id="", custom_id=0, fixture_id_numeric=0, unit_number=0):

        # (Edit) Store objects positions
        old_pos = {obj.name:obj.object.location.copy() for obj in self.objects}
        old_rot = {obj.name:obj.object.rotation_euler.copy() for obj in self.objects}
        
        # (Edit) Collection with this name already exists, delete it
        if (self.name in bpy.data.collections):
            for obj in bpy.data.collections[self.name].objects:
                bpy.data.objects.remove(obj)
            bpy.data.collections.remove(bpy.data.collections[self.name])

        # Data Properties
        self.name = name
        self.profile = profile
        self.mode = mode
        if fixture_id is not None:
            self.fixture_id = fixture_id
        if custom_id is not None:
            self.custom_id = custom_id
        if fixture_id_numeric is not None:
            self.fixture_id_numeric = fixture_id_numeric
        if unit_number is not None:
            self.unit_number = unit_number
        if uuid is not None:
            self.uuid = uuid

        # DMX Properties
        self.universe = universe
        self.address = address
        self.gel_color = list(gel_color)
        self.display_beams = display_beams
        self.add_target = add_target

        # (Edit) Clear links and channel cache
        self.lights.clear()
        self.objects.clear()
        self.channels.clear()
        self.virtual_channels.clear()
        self.emitter_materials.clear()

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


        # Handle if dmx mode doesn't exist (maybe this is MVR import and GDTF files were replaced)
        # use mode[0] as default
        if not any(self.mode == mode.name for mode in gdtf_profile.dmx_modes):
            self.mode = gdtf_profile.dmx_modes[0].name

        model_collection = DMX_Model.getFixtureModelCollection(gdtf_profile, self.mode, self.display_beams, self.add_target)

        # Build DMX channels cache
        dmx_channels = pygdtf.utils.get_dmx_channels(gdtf_profile, self.mode)
        # Merge all DMX breaks together
        dmx_channels_flattened = [channel for break_channels in dmx_channels for channel in break_channels]
        for ch in dmx_channels_flattened:
            self.channels.add()
            self.channels[-1].id = ch['id']
            self.channels[-1].geometry = ch['geometry']

            # Set shutter to 0, we don't want strobing by default
            # and are not reading real world values yet
            if "shutter" in ch['id'].lower():
                self.channels[-1].default = 0
            else:
                self.channels[-1].default = ch['default']

        # Build cache of virtual channels
        _virtual_channels = pygdtf.utils.get_virtual_channels(gdtf_profile, self.mode)
        for ch in _virtual_channels:
            self.virtual_channels.add()
            self.virtual_channels[-1].id = ch['id']
            self.virtual_channels[-1].geometry = ch['geometry']
            self.virtual_channels[-1].default = ch['default']

        links = {}
        base = self.get_root(model_collection)
        head = self.get_tilt(model_collection)
        DMX_Log.log.info(f"Head: {head}, Base: {base}")

        for obj in model_collection.objects:
            # Copy object
            links[obj.name] = obj.copy()
            # If light, copy object data, 
            # Cache access to base (root) and head for faster rendering.
            # Fixtures with multiple pan/tilts will still have issues
            # but that would anyway require geometry → attribute approach
            if obj.type == 'LIGHT':
                links[obj.name].data = obj.data.copy()
                self.lights.add()
                light_name=f'Light{len(self.lights)}'
                self.lights[-1].name = light_name
                self.lights[light_name].object = links[obj.name]
            elif 'Target' in obj.name:
                self.objects.add()
                self.objects[-1].name = 'Target'
                self.objects['Target'].object = links[obj.name]
            elif base.name == obj.name:
                self.objects.add()
                self.objects[-1].name = "Root"
                self.objects["Root"].object = links[obj.name]
            elif head is not None and head.name == obj.name:
                self.objects.add()
                self.objects[-1].name = "Head"
                self.objects["Head"].object = links[obj.name]
            elif obj.get("2d_symbol", None) == "all":
                self.objects.add().name = "2D Symbol"
                self.objects["2D Symbol"].object = links[obj.name]

            # Link all other object to collection
            self.collection.objects.link(links[obj.name])

        # Relink constraints
        for obj in self.collection.objects:
            for constraint in obj.constraints:
                constraint.target = links[constraint.target.name]

        # (Edit) Reload old positions and rotations
        bpy.context.view_layer.update()
        for obj in self.objects:
            if obj.name in old_pos:
                obj.object.location = old_pos[obj.name]

            if obj.object.get("geometry_root", False):
                if obj.name in old_rot:
                    obj.object.rotation_mode = 'XYZ'
                    obj.object.rotation_euler = old_rot[obj.name]

        # Set position from MVR
        if mvr_position is not None:
            for obj in self.objects:
                if obj.object.get("geometry_root", False):
                    obj.object.matrix_world=mvr_position

        # Set target's position from MVR
        if focus_point is not None:
            for obj in self.objects:
                if 'Target' in obj.name:
                    obj.object.matrix_world=focus_point

        # Setup emitter
        for obj in self.collection.objects:
            if "beam" in obj.get("geometry_type", ""):
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

        # Set Pigtail visibility and Beam selection
        for obj in self.collection.objects:
            if "pigtail" in obj.get("geometry_type", ""):
                obj.hide_set(not bpy.context.scene.dmx.display_pigtails)
            if obj.get("geometry_root", False):
                continue
            if "Target" in obj.name:
                continue
            if obj.get("2d_symbol", None) == "all":
                obj.hide_set(not bpy.context.scene.dmx.display_2D)
                continue

            obj.hide_select = not bpy.context.scene.dmx.select_geometries
 
        self.clear()
        bpy.context.scene.dmx.render()
    
    # Interface Methods #

    def setDMX(self, pvalues):
        channels = [c.id for c in self.channels]
        virtuals = [c.id for c in self.virtual_channels]
        for attribute, value in pvalues.items():
            for idx, channel in enumerate(channels):
                if channel == attribute:
                    DMX_Log.log.info(("Set DMX data", channel, value))
                    DMX_Data.set(self.universe, self.address+idx, value)
            for vchannel in virtuals:
                if vchannel == attribute:
                    DMX_Log.log.info(("Set Virtual data", attribute, value))
                    DMX_Data.set_virtual(self.name, attribute, value)

    def render(self):
        if bpy.context.window_manager.dmx.pause_render:
        # do not run dender loop during MVR import
            return
        channels = [c.id for c in self.channels]
        data = DMX_Data.get(self.universe, self.address, len(channels))
        data_virtual = DMX_Data.get_virtual(self.name)
        virtual_channels = [c.id for c in self.virtual_channels]
        shutterDimmer = [None, None]
        panTilt = [None,None]
        rgb = [None,None,None]
        cmy = [None,None,None]
        zoom = None
        rgb_mixing_geometries={} #for now, only RGB mixing is per geometry
        xyz_moving_geometries={}
        xyz_rotating_geometries={}
        
        for attribute in virtual_channels:
            geometry = None # for now. But, no way to know, as BlenderDMX controls are universal
            if attribute in data_virtual:
                if attribute == "Shutter1": shutterDimmer[0] = data_virtual[attribute]
                elif attribute == "Dimmer": shutterDimmer[1] = data_virtual[attribute]
                elif attribute == "ColorAdd_R": rgb_mixing_geometries[geometry][0] = data_virtual[attribute]
                elif attribute == "ColorAdd_G": rgb_mixing_geometries[geometry][1] = data_virtual[attribute]
                elif attribute == "ColorAdd_B": rgb_mixing_geometries[geometry][2] = data_virtual[attribute]
                elif attribute == "ColorSub_C": cmy[0] = data_virtual[attribute]
                elif attribute == "ColorSub_M": cmy[1] = data_virtual[attribute]
                elif attribute == "ColorSub_Y": cmy[2] = data_virtual[attribute]
                elif attribute == "Pan": panTilt[0] = data_virtual[attribute]
                elif attribute == "Tilt": panTilt[1] = data_virtual[attribute]
                elif attribute == "Zoom": zoom = data_virtual[attribute]
                elif attribute == "XYZ_X": xyz_moving_geometries[geometry][0] = data_virtual[attribute]
                elif attribute == "XYZ_Y": xyz_moving_geometries[geometry][1] = data_virtual[attribute]
                elif attribute == "XYZ_Z": xyz_moving_geometries[geometry][2] = data_virtual[attribute]
                elif attribute == "Rot_X": xyz_rotating_geometries[geometry][0] = data_virtual[attribute]
                elif attribute == "Rot_Y": xyz_rotating_geometries[geometry][1] = data_virtual[attribute]
                elif attribute == "Rot_Z": xyz_rotating_geometries[geometry][2] = data_virtual[attribute]

        for c in range(len(channels)):
            geometry=self.channels[c].geometry
            if geometry not in rgb_mixing_geometries.keys():
                rgb_mixing_geometries[geometry]=[None, None, None]
            if geometry not in xyz_moving_geometries.keys():
                xyz_moving_geometries[geometry]=[None, None, None]
            if geometry not in xyz_rotating_geometries.keys():
                xyz_rotating_geometries[geometry]=[None, None, None]
            if (channels[c] == 'Dimmer'): shutterDimmer[1] = data[c]
            elif (channels[c] == 'Shutter1'): shutterDimmer[0] = data[c]
            elif (channels[c] == 'ColorAdd_R'): rgb_mixing_geometries[geometry][0] = data[c]
            elif (channels[c] == 'ColorAdd_G'): rgb_mixing_geometries[geometry][1] = data[c]
            elif (channels[c] == 'ColorAdd_B'): rgb_mixing_geometries[geometry][2] = data[c]
            elif (channels[c] == 'ColorSub_C'): cmy[0] = data[c]
            elif (channels[c] == 'ColorSub_M'): cmy[1] = data[c]
            elif (channels[c] == 'ColorSub_Y'): cmy[2] = data[c]
            elif (channels[c] == 'Pan'): panTilt[0] = data[c]
            elif (channels[c] == 'Tilt'): panTilt[1] = data[c]
            elif (channels[c] == 'Zoom'): zoom = data[c]
            elif (channels[c] == 'XYZ_X'): xyz_moving_geometries[geometry][0] = data[c]
            elif (channels[c] == 'XYZ_Y'): xyz_moving_geometries[geometry][1] = data[c]
            elif (channels[c] == 'XYZ_Z'): xyz_moving_geometries[geometry][2] = data[c]
            elif (channels[c] == 'Rot_X'): xyz_rotating_geometries[geometry][0] = data[c]
            elif (channels[c] == 'Rot_Y'): xyz_rotating_geometries[geometry][1] = data[c]
            elif (channels[c] == 'Rot_Z'): xyz_rotating_geometries[geometry][2] = data[c]
       
        for geometry, rgb in rgb_mixing_geometries.items():
            if (rgb[0] != None and rgb[1] != None and rgb[2] != None):
                if len(rgb_mixing_geometries) == 1 or not self.light_object_for_geometry_exists(rgb_mixing_geometries):
                    # do not apply for simple devices as trickle down is not implemented...
                    self.updateRGB(rgb, None)
                else:
                    self.updateRGB(rgb, geometry)
            else:
                # TODO: eliminate code duplication?
                # This ensures that devices without RGB/CMY can still have color from the gel
                if len(rgb_mixing_geometries) == 1 or not self.light_object_for_geometry_exists(rgb_mixing_geometries):
                    # do not apply for simple devices as trickle down is not implemented...
                    self.updateRGB([255, 255, 255], None)
                else:
                    self.updateRGB([255, 255, 255], geometry)
        
        if (cmy[0] != None and cmy[1] != None and cmy[2] != None):
            self.updateCMY(cmy)

        if panTilt[0] != None or panTilt[1] != None:
            if panTilt[0] is None:
                panTilt[0] = 191 # if the device doesn't have pan, align head with base
            if panTilt[1] is None:
                panTilt[1] = 190

            self.updatePanTilt(panTilt[0], panTilt[1])

        if (zoom != None):
            self.updateZoom(zoom)
        
        for geometry, xyz in xyz_moving_geometries.items():
            self.updatePosition(geometry=geometry, x=xyz[0], y=xyz[1], z=xyz[2])

        for geometry, xyz in xyz_rotating_geometries.items():
            self.updateRotation(geometry=geometry, x=xyz[0], y=xyz[1], z=xyz[2])

        if shutterDimmer[0] is not None or shutterDimmer[1] is not None:
            if shutterDimmer[0] is None:
                shutterDimmer[0] = 0 # if device doesn't have shutter, set default value
            self.updateShutterDimmer(shutterDimmer[0], shutterDimmer[1])

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

    def get_channel_by_attribute(self, attribute):
        for channel in self.channels:
            if channel.id == attribute:
                return channel

    def updateShutterDimmer(self, shutter, dimmer):
        last_shutter_value = 0
        last_dimmer_value = 0
        try:
            for emitter_material in self.emitter_materials:
                if shutter > 0:
                    break # no need to do the expensive value settings if we do this anyway in shutter timer
                emitter_material.material.node_tree.nodes[1].inputs[STRENGTH].default_value = 10*(dimmer/255.0)

            for light in self.lights:
                last_shutter_value = light.object.data['shutter_value']
                last_dimmer_value = light.object.data['shutter_dimmer_value']
                light.object.data['shutter_value']=shutter
                light.object.data['shutter_dimmer_value']=dimmer
                if shutter > 0:
                    break # no need to do the expensive value settings if we do this anyway in shutter timer
                light.object.data.energy = (dimmer/255.0) * light.object.data['flux']

        except Exception as e:
            print("Error updating dimmer", e)

        if (last_shutter_value == 0 or last_dimmer_value == 0) and shutter != 0:
                bpy.app.timers.register(self.runStrobe)
                DMX_Log.log.info("Register shutter timer")

        return dimmer
    
    def runStrobe(self):
        try:

            exit_timer = False
            dimmer_value = 0 # reused also for emitter

            for light in self.lights:
                if light.object.data['shutter_value'] == 0:
                    exit_timer= True
                if light.object.data['shutter_dimmer_value'] == 0:
                    exit_timer = True
                dimmer_value = 0
                if light.object.data['shutter_counter'] == 1:
                    dimmer_value = light.object.data['shutter_dimmer_value']
                if light.object.data['shutter_counter'] > light.object.data['shutter_value']:
                    light.object.data['shutter_counter'] = 0

                light.object.data.energy = (dimmer_value/255.0) * light.object.data['flux']
                light.object.data['shutter_counter'] +=1

            # Here we can reuse data we got from the light object...
            for emitter_material in self.emitter_materials:
                emitter_material.material.node_tree.nodes[1].inputs[STRENGTH].default_value = 10*(dimmer_value/255.0)

            if exit_timer:
                DMX_Log.log.info("Killing shutter timer")
                return None # exit the timer

        except Exception as e:
            DMX_Log.log.error("Error updating lights and emitters", e)
            DMX_Log.log.info("Killing shutter timer")
            return None # kills the timer
        return 1.0/24.0

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
    
    def updatePosition(self, geometry = None, x=None, y=None, z=None):
        if geometry is None:
            geometry = self.objects["Root"].object
        else:
            geometry = self.get_object_by_geometry_name(geometry)

        if x is not None:
            geometry.location.x = (128-x) * 0.1
        if y is not None:
            geometry.location.y = (128-y) * 0.1
        if z is not None:
            geometry.location.z = (128-z) * 0.1
    
    def updateRotation(self, geometry = None, x=None, y=None, z=None):
        if geometry is None:
            geometry = self.objects["Root"].object
        else:
            geometry = self.get_object_by_geometry_name(geometry)

        geometry.rotation_mode = 'XYZ'
        if x is not None:
            geometry.rotation_euler[0] = (x/127.0-1)*360*(math.pi/360)
        if y is not None:
            geometry.rotation_euler[1] = (y/127.0-1)*360*(math.pi/360)
        if z is not None:
            geometry.rotation_euler[2] = (z/127.0-1)*360*(math.pi/360)
        
    def updatePanTilt(self, pan, tilt):
        DMX_Log.log.info("Updating pan tilt")
        pan = (pan/127.0-1)*540*(math.pi/360)
        tilt = (tilt/127.0-1)*270*(math.pi/360)

        base = self.objects["Root"].object

        if "Target" in self.objects:
            # calculate target position, head will follow
            try:
                head = self.objects["Head"].object
            except Exception as e:
                self.updatePanTiltDirectly(pan, tilt)
                DMX_Log.log.info("Escaping pan tilt update, not enough data")
                return

            head_location = head.matrix_world.translation
            pan = pan + base.rotation_euler[2] # take base z rotation into consideration

            target = self.objects['Target'].object
            
            eul = mathutils.Euler((0.0,base.rotation_euler[1]+tilt,base.rotation_euler[0]+pan), 'XYZ')
            vec = mathutils.Vector((0.0,0.0,-(target.location-head_location).length))
            vec.rotate(eul)

            target.location = vec + head_location
        else:
            # for fixtures where we decided not to use target
            self.updatePanTiltDirectly(pan, tilt)

    def updatePanTiltDirectly(self, pan, tilt):
        pan_geometry = self.get_mobile_type("yoke")
        tilt_geometry = self.get_mobile_type("head")
        if pan_geometry:
            pan_geometry.rotation_euler[2] = pan
        if tilt_geometry:
            tilt_geometry.rotation_euler[0] = tilt



    def get_object_by_geometry_name(self, geometry):
        for obj in self.collection.objects:
            if "original_name" not in obj:
                continue
            if obj["original_name"] == geometry:
                return obj

    def get_mobile_type(self, mobile_type):
        for obj in self.collection.objects:
            if obj.get("mobile_type", None) == mobile_type:
                return obj


    def get_root(self, model_collection):
        for obj in model_collection.objects:
            if obj.get("geometry_root", False):
                return obj

    def get_tilt(self, model_collection):
        for obj in model_collection.objects:
            for channel in self.channels:
                if "Tilt" == channel.id and channel.geometry == obj.get("original_name", "None"):
                    return obj
            for channel in self.virtual_channels:
                if "Tilt" == channel.id and channel.geometry == obj.get("original_name", "None"):
                    return obj


    def getProgrammerData(self):
        channels = [c.id for c in self.channels]
        data = DMX_Data.get(self.universe, self.address, len(channels))
        params = {}
        for c in range(len(channels)):
            params[channels[c]] = data[c]
        return params

    def select(self):
        dmx = bpy.context.scene.dmx
        if dmx.display_2D:
            # in 2D view deselect the 2D symbol, unhide the fixture and select base, 
            # to allow movement and rotation 
            self.objects["2D Symbol"].object.select_set(False)

            for obj in self.collection.objects:
                if "pigtail" in obj.get("geometry_type", ""):
                    obj.hide_set(not bpy.context.scene.dmx.display_pigtails)
                if obj.get("2d_symbol", None):
                    continue
                obj.hide_set(False)
            self.objects["Root"].object.select_set(True)

        else:
            self.objects["Root"].object.select_set(True)
    
    def unselect(self):
        dmx = bpy.context.scene.dmx
        self.objects["Root"].object.select_set(False)
        if ('Target' in self.objects):
            self.objects['Target'].object.select_set(False)
        if "2D Symbol" in self.objects:
            self.objects["2D Symbol"].object.select_set(False)
        if dmx.display_2D:
            for obj in self.collection.objects:
                if obj.get("2d_symbol", None):
                    continue
                obj.hide_set(True)


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
