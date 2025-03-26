#    Copyright Hugo Aboud, vanous
#
#    This file is part of BlenderDMX.
#
#    BlenderDMX is free software: you can redistribute it and/or modify it
#    under the terms of the GNU General Public License as published by the Free
#    Software Foundation, either version 3 of the License, or (at your option)
#    any later version.
#
#    BlenderDMX is distributed in the hope that it will be useful, but WITHOUT
#    ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
#    FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
#    more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program. If not, see <https://www.gnu.org/licenses/>.


import math
import os
import random
import traceback
import uuid as py_uuid

import bpy
import mathutils
import pygdtf
import pymvr
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    FloatVectorProperty,
    IntProperty,
    IntVectorProperty,
    PointerProperty,
    StringProperty,
)
from bpy.types import (
    Collection,
    GeometryNodeTree,
    Image,
    Material,
    Object,
    PropertyGroup,
    Text,
)

from .data import DMX_Data
from .gdtf import DMX_GDTF
from .logging import DMX_Log
from .material import (
    get_gobo_material,
    get_ies_node,
    getEmitterMaterial,
    getGeometryNodes,
    set_light_nodes,
)
from .model import DMX_Model
from .node_arranger import DMX_OT_ArrangeSelected
from .osc_utils import DMX_OSC_Handlers
from .util import add_rgb, cmy_to_rgb, colors_to_rgb, kelvin_table, rgb2xyY

# Shader Nodes default labels
# Blender API naming convention is inconsistent for internationalization
# Every label used is listed here, so it's easier to fix it on new API updates
STRENGTH = "Strength"
COLOR = "Color"

# fmt: off

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

class DMX_Fixture_Image(PropertyGroup):
    image: PointerProperty(
        name = "Fixture > Image",
        type = Image)
    count: IntProperty(
            default = 0
            )

class DMX_Emitter_Material(PropertyGroup):
    material: PointerProperty(
        name = "Emitter > Material",
        type = Material)

class DMX_Geometry_Node(PropertyGroup):
    node: PointerProperty(
        name = "Geometry Node",
        type = GeometryNodeTree)

class DMX_IES_Data(PropertyGroup):
    ies: PointerProperty(
        name = "Spot > IES",
        type = Text)


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

# fmt: on
class DMX_Fixture(PropertyGroup):
    # fmt: off
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

    images: CollectionProperty(
        name = "Fixture > Images",
        type = DMX_Fixture_Image
    )

    emitter_materials: CollectionProperty(
        name = "Fixture > Materials",
        type = DMX_Emitter_Material)

    geometry_nodes: CollectionProperty(
        name = "Fixture > Geometry Nodes",
        type = DMX_Geometry_Node)

    gobo_materials: CollectionProperty(
        name = "Fixture > Gobo Materials",
        type = DMX_Emitter_Material)

    ies_data: CollectionProperty(
        name = "Fixture > IES Files",
        type = DMX_IES_Data)

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

    gdtf_long_name: StringProperty(
        name = "Fixture > Name",
        default = "")

    gdtf_manufacturer: StringProperty(
        name = "Fixture > Manufacturer",
        default = "")

    def ensure_universe_exists(self, context):
        dmx = bpy.context.scene.dmx
        dmx.ensureUniverseExists(self.universe)

    universe : IntProperty(
        name = "Fixture > Universe",
        description="Fixture DMX Universe",
        default = 0,
        min = 0,
        max = 511,
        update = ensure_universe_exists
        )

    address : IntProperty(
        name = "Fixture > Address",
        description="Fixture DMX Address",
        default = 1,
        min = 1,
        max = 512)

    uuid: StringProperty(
        name = "UUID",
        description = "Unique ID, used for MVR",
        default = str(py_uuid.uuid4())
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

    dmx_cache_dirty: BoolProperty(
        name = "DMX cache dirty",
        description="if dmx data has changed but keyframe has not been saved yet",
        default = False)

    gel_color_rgb: IntVectorProperty(
        name = "Gel Color",
        subtype = "COLOR",
        size = 3,
        min = 0,
        max = 255,
        default = (255,255,255))

    gel_color: FloatVectorProperty(
        name = "Unused",
        subtype = "COLOR",
        size = 4,
        min = 0.0,
        max = 1.0,
        default = (1.0,1.0,1.0,1.0))

    ignore_movement_dmx: BoolProperty(
        name = "Ignore movement DMX",
        description="Stay in position set by Target",
        default = False)

    classing: StringProperty(
        name = "Classing UUID",
        description = "Classing - logical grouping across different layers",
        default = ""
            )

    lock_pan_rotation: BoolProperty(
        name = "Lock Pan Rotation",
        description="Lock Pan Rotation",
        default = False)

    lock_tilt_rotation: BoolProperty(
        name = "Lock Tilt Rotation",
        description="Lock Tilt Rotation",
        default = False)
    # fmt: on

    def build(
        self,
        name,
        profile,
        mode,
        universe,
        address,
        gel_color,
        display_beams,
        add_target,
        mvr_position=None,
        focus_point=None,
        uuid=None,
        fixture_id="",
        custom_id=0,
        fixture_id_numeric=0,
        unit_number=0,
        classing="",
    ):
        # (Edit) Store objects positions
        old_pos = {obj.name: obj.object.location.copy() for obj in self.objects}
        old_rot = {obj.name: obj.object.rotation_euler.copy() for obj in self.objects}

        # (Edit) Collection with this name already exists, delete it
        if self.name in bpy.data.collections:
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
        if classing is not None:
            self.classing = classing

        # DMX Properties
        self.universe = universe
        self.address = address
        self.gel_color_rgb = list(int((255 / 1) * i) for i in gel_color[:3])
        self.display_beams = display_beams
        self.add_target = add_target

        # (Edit) Clear links and channel cache
        self.lights.clear()
        self.images.clear()
        self.objects.clear()
        self.channels.clear()
        self.virtual_channels.clear()
        self.emitter_materials.clear()
        self.geometry_nodes.clear()
        self.gobo_materials.clear()
        self.ies_data.clear()
        self.dmx_cache_dirty = False

        # Custom python data storage, outside of bpy.props. So called ID props
        self["dmx_values"] = []

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
        self.gdtf_long_name = gdtf_profile.long_name
        self.gdtf_manufacturer = gdtf_profile.manufacturer

        # Handle if dmx mode doesn't exist (maybe this is MVR import and GDTF files were replaced)
        # use mode[0] as default
        if not any(self.mode == mode.name for mode in gdtf_profile.dmx_modes):
            self.mode = gdtf_profile.dmx_modes[0].name

        model_collection = DMX_Model.getFixtureModelCollection(
            gdtf_profile, self.mode, self.display_beams, self.add_target
        )

        dmx_mode = gdtf_profile.dmx_modes.get_mode_by_name(mode)

        if dmx_mode is None:
            dmx_mode = profile.dmx_modes[0]
            mode = dmx_mode.name

        dmx_channels_flattened = dmx_mode.dmx_channels.as_dict()

        has_gobos = False
        for ch in dmx_channels_flattened:
            channel = self.channels.add()
            channel.id = ch["attribute"]
            channel.geometry = ch["geometry"]

            # Set shutter to 0, we don't want strobing by default
            # and are not reading real world values yet
            if "shutter" in ch["attribute"].lower():
                channel.default = 0
            # blender programmer cannot control white, set it to 0
            elif "ColorAdd_W" in ch["attribute"]:
                channel.default = 0
            else:
                channel.default = ch["default"]

            if "Gobo" in ch["attribute"]:
                has_gobos = True

        # Build cache of virtual channels
        _virtual_channels = dmx_mode.virtual_channels.as_dict()
        for ch in _virtual_channels:
            virtual_channel = self.virtual_channels.add()
            virtual_channel.id = ch["attribute"]
            virtual_channel.geometry = ch["geometry"]
            virtual_channel.default = ch["default"]
            if "Gobo" in ch["attribute"]:
                has_gobos = True

        # Get all gobos
        if has_gobos:
            gobo_seq = DMX_GDTF.extract_gobos_as_sequence(gdtf_profile)
            if gobo_seq is not None:
                gobo1 = self.images.add()
                gobo1.name = "gobos1"
                gobo1.image = gobo_seq[0]
                gobo1.count = gobo_seq[0]["count"]
                gobo1.image.pack()
                gobo2 = self.images.add()
                gobo2.name = "gobos2"
                gobo2.image = gobo_seq[1]
                gobo2.count = gobo_seq[1]["count"]
                gobo2.image.pack()

        if "gobos1" not in self.images:
            has_gobos = False  # faulty GDTF might have channels but no images

        self["slot_colors"] = []
        slot_colors = DMX_GDTF.get_wheel_slot_colors(gdtf_profile)
        if len(slot_colors) > 1:
            self["slot_colors"] = slot_colors[
                :255
            ]  # limit number of colors to an 8bit control channel

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

            if obj.type == "LIGHT":
                links[obj.name].data = obj.data.copy()
                self.lights.add()
                light_name = f"Light{len(self.lights)}"
                self.lights[-1].name = light_name
                self.lights[light_name].object = links[obj.name]
                if has_gobos:
                    self.lights[
                        light_name
                    ].object.data.shadow_soft_size = 0.001  # larger spot diameter causes gobos to be blurry in Cycles
                    self.lights[light_name].object.data.shadow_buffer_clip_start = 0.002
            elif "Target" in obj.name:
                self.objects.add()
                self.objects[-1].name = "Target"
                self.objects["Target"].object = links[obj.name]
                self.objects["Target"].object["uuid"] = str(py_uuid.uuid4())
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

        # Reparent children
        for obj in model_collection.objects:
            for child in obj.children:
                if child.name in links:
                    links[child.name].parent = links[obj.name]
        # Relink constraints
        for obj in self.collection.objects:
            for constraint in obj.constraints:
                constraint.target = links[constraint.target.name]

        # (Edit) Reload old positions and rotations
        bpy.context.view_layer.update()
        for obj in self.objects:
            if obj.object.get("geometry_root", False):
                if obj.name in old_pos:
                    obj.object.location = old_pos[obj.name]
                if obj.name in old_rot:
                    obj.object.rotation_mode = "XYZ"
                    obj.object.rotation_euler = old_rot[obj.name]

        # Set position from MVR
        if mvr_position is not None:
            for obj in self.objects:
                if obj.object.get("geometry_root", False):
                    obj.object.matrix_world = mvr_position

        # Set target's position from MVR
        if focus_point is not None:
            for obj in self.objects:
                if "Target" in obj.name:
                    obj.object.matrix_world = focus_point

        # Setup emitter
        for obj in self.collection.objects:
            if "beam" in obj.get("geometry_type", ""):
                emitter = obj
                new_material = self.emitter_materials.add()
                new_material.name = obj.name
                new_material["parent_geometries"] = list(
                    set(obj.get("parent_geometries", []))
                )

                emitter_material = getEmitterMaterial(obj.name)
                emitter.active_material = emitter_material
                emitter.material_slots[0].link = "OBJECT"
                emitter.material_slots[0].material = emitter_material
                if hasattr(emitter.material_slots[0].material, "shadow_method"):
                    emitter.material_slots[0].material.shadow_method = "NONE"  # eevee
                new_material.material = emitter_material

            if "gobo" in obj.get("geometry_type", ""):
                material = self.gobo_materials.add()
                material.name = obj.name

                gobo_material = get_gobo_material(obj.name)
                obj.active_material = gobo_material
                if hasattr(obj.active_material, "shadow_method"):
                    obj.active_material.shadow_method = "CLIP"
                obj.active_material.blend_method = "BLEND"
                obj.material_slots[
                    0
                ].link = "OBJECT"  # ensure that each fixture has it's own material
                obj.material_slots[0].material = gobo_material
                material.material = gobo_material

                gobo_radius = obj.get("gobo_radius", 0)
                if gobo_radius:
                    obj.dimensions = (gobo_radius, gobo_radius, 0)

            # Setup laser geometry nodes
            if "laser" in obj.get("geometry_type", ""):
                # emitter
                emitter = obj
                self.emitter_materials.add()
                self.emitter_materials[-1].name = obj.name
                emitter_material = getEmitterMaterial(obj.name)
                if hasattr(emitter_material, "shadow_method"):
                    emitter_material.shadow_method = (
                        "NONE"  # laser beam should not cast shadows
                    )
                self.emitter_materials[-1].material = emitter_material
                # laser beam
                geo_node = obj
                node = self.geometry_nodes.add()
                node.name = obj.name
                modifier = geo_node.modifiers.new(type="NODES", name="base_object")
                node_group = getGeometryNodes(obj)
                modifier.node_group = node_group
                node.node = node_group

        # setup light for gobo in cycles
        for light in self.lights:
            set_light_nodes(light)

        # Link collection to DMX collection
        bpy.context.scene.dmx.collection.children.link(self.collection)

        # Set Pigtail visibility and Beam selection
        for obj in self.collection.objects:
            if "pigtail" in obj.get("geometry_type", ""):
                obj.hide_set(not bpy.context.scene.dmx.display_pigtails)
                obj.hide_viewport = (
                    not bpy.context.scene.dmx.display_pigtails
                )  # keyframing
                obj.hide_render = not bpy.context.scene.dmx.display_pigtails
            if obj.get("geometry_root", False):
                continue
            if "Target" in obj.name:
                continue
            if obj.get("2d_symbol", None) == "all":
                obj.hide_set(not bpy.context.scene.dmx.display_2D)
                obj.hide_viewport = not bpy.context.scene.dmx.display_2D  # keyframing
                obj.hide_render = not bpy.context.scene.dmx.display_2D
                continue

            obj.hide_select = not bpy.context.scene.dmx.select_geometries

        self.clear()
        self.hide_gobo()
        d = DMX_OT_ArrangeSelected()
        for item in self.gobo_materials:
            ntree = item.material.node_tree
            d.process_tree(ntree)
        for item in self.geometry_nodes:
            ntree = item.node
            d.process_tree(ntree)

        for light in self.lights:  # CYCLES
            light_obj = light.object
            ntree = light_obj.data.node_tree
            d.process_tree(ntree)

        self.render()

    # Interface Methods #

    def setDMX(self, pvalues):
        temp_data = bpy.context.window_manager.dmx

        # channels = [c.id for c in self.channels]
        # virtuals = [c.id for c in self.virtual_channels]

        for attribute, value in pvalues.items():
            for idx, channel in enumerate(self.channels):
                if channel.id == attribute:
                    if len(temp_data.active_subfixtures) > 0:
                        if any(
                            channel.geometry == g.name
                            for g in temp_data.active_subfixtures
                        ):
                            DMX_Log.log.info(("Set DMX data", channel.id, value))
                            DMX_Data.set(self.universe, self.address + idx, value)
                    else:
                        DMX_Log.log.info(("Set DMX data", channel, value))
                        DMX_Data.set(self.universe, self.address + idx, value)
            for vchannel in self.virtual_channels:
                if vchannel.id == attribute:
                    if len(temp_data.active_subfixtures) > 0:
                        if any(
                            vchannel.geometry == g.name
                            for g in temp_data.active_subfixtures
                        ):
                            DMX_Log.log.info(("Set Virtual data", attribute, value))
                            geometry = next(
                                vchannel.geometry == g.name
                                for g in temp_data.active_subfixtures
                            )
                            DMX_Data.set_virtual(self.name, attribute, geometry, value)
                    else:
                        DMX_Log.log.info(("Set Virtual data", attribute, value))
                        DMX_Data.set_virtual(self.name, attribute, None, value)

    def render(self, skip_cache=False, current_frame=None):
        if bpy.context.window_manager.dmx.pause_render:
            # do not run render loop when paused
            return

        channels = [c.id for c in self.channels]
        # virtual_channels = [c.id for c in self.virtual_channels]

        data = DMX_Data.get(self.universe, self.address, len(channels))
        data_virtual = DMX_Data.get_virtual(self.name)

        s_data = [int(b) for b in data] + [
            int(b["value"]) for b in data_virtual.values()
        ]  # create cache
        if (
            list(self["dmx_values"]) == s_data
        ):  # this helps to eliminate flicker with Ethernet DMX signal when the data for this particular device is not changing
            if (
                skip_cache is False
            ):  # allow to save a keyframe when using the programmer in Blender
                DMX_Log.log.debug("caching DMX")
                return
            if (
                self.dmx_cache_dirty is False
            ):  # we care about keyframe saving only if there is data to be saved
                DMX_Log.log.debug("caching DMX")
                return
        else:  # we have new dmx data, mark the cache as dirty, so we know we can save a keyframe when needed
            self.dmx_cache_dirty = True

        DMX_Log.log.debug(f"{current_frame=}, {self.dmx_cache_dirty=}")

        self["dmx_values"] = s_data
        panTilt = [None, None, 1, 1]  # pan, tilt, 1 = 8bit, 256 = 16bit
        cmy = [None, None, None]
        zoom = None
        color1 = None
        ctc = None
        iris = None
        rgb_mixing_geometries = {}
        xyz_moving_geometries = {}
        xyz_rotating_geometries = {}
        shutter_dimmer_geometries = {}  # item: shutter, dimmer, unused, dimmer bits
        pan_rotating_geometries = {}
        tilt_rotating_geometries = {}

        pan_cont_rotating_geometries = {}
        tilt_cont_rotating_geometries = {}

        gobo1 = [
            None,
            None,
        ]  # gobo selection (Gobo1), gobo indexing/rotation (Gobo1Pos)
        gobo2 = [
            None,
            None,
        ]  # gobo selection (Gobo2), gobo indexing/rotation (Gobo2Pos)

        for vchannel in self.virtual_channels:
            geometry = str(
                vchannel.geometry
            )  # for now. But, no way to know, as BlenderDMX controls are universal
            if geometry not in rgb_mixing_geometries.keys():
                rgb_mixing_geometries[geometry] = [
                    None
                ] * 12  # R, G, B, White, WW, CW, Amber, Lime, UV, cyan, magenta, yellow
            if geometry not in xyz_moving_geometries.keys():
                xyz_moving_geometries[geometry] = [None, None, None]
            if geometry not in xyz_rotating_geometries.keys():
                xyz_rotating_geometries[geometry] = [None, None, None]
            if geometry not in shutter_dimmer_geometries.keys():
                shutter_dimmer_geometries[geometry] = [None, None, None, 1]  # + bits
            if geometry not in pan_rotating_geometries.keys():
                pan_rotating_geometries[geometry] = [None, 1]
            if geometry not in tilt_rotating_geometries.keys():
                tilt_rotating_geometries[geometry] = [None, 1]
            if geometry not in pan_cont_rotating_geometries.keys():
                pan_cont_rotating_geometries[geometry] = [None, 1]
            if geometry not in tilt_cont_rotating_geometries.keys():
                tilt_cont_rotating_geometries[geometry] = [None, 1]
            if vchannel.id in data_virtual:
                if vchannel.id == "Shutter1":
                    shutter_dimmer_geometries[geometry][0] = data_virtual[vchannel.id][
                        "value"
                    ]
                elif vchannel.id == "Dimmer":
                    shutter_dimmer_geometries[geometry][1] = data_virtual[vchannel.id][
                        "value"
                    ]
                elif vchannel.id == "+Dimmer":
                    shutter_dimmer_geometries[geometry][1] = (
                        shutter_dimmer_geometries[geometry][1] * 256
                        + data_virtual[vchannel.id]["value"]
                    )
                    shutter_dimmer_geometries[geometry][3] = 256

                elif vchannel.id == "ColorAdd_R" or vchannel.id == "ColorRGB_Red":
                    rgb_mixing_geometries[geometry][0] = data_virtual[vchannel.id][
                        "value"
                    ]
                elif vchannel.id == "ColorAdd_G" or vchannel.id == "ColorRGB_Green":
                    rgb_mixing_geometries[geometry][1] = data_virtual[vchannel.id][
                        "value"
                    ]
                elif vchannel.id == "ColorAdd_B" or vchannel.id == "ColorRGB_Blue":
                    rgb_mixing_geometries[geometry][2] = data_virtual[vchannel.id][
                        "value"
                    ]
                elif vchannel.id == "ColorSub_C":
                    cmy[0] = data_virtual[vchannel.id]["value"]
                elif vchannel.id == "ColorSub_M":
                    cmy[1] = data_virtual[vchannel.id]["value"]
                elif vchannel.id == "ColorSub_Y":
                    cmy[2] = data_virtual[vchannel.id]["value"]
                elif vchannel.id == "Pan":
                    panTilt[0] = data_virtual[vchannel.id]["value"]
                    pan_rotating_geometries[geometry][0] = data_virtual[vchannel.id][
                        "value"
                    ]
                elif vchannel.id == "+Pan":
                    panTilt[0] = panTilt[0] * 256 + data_virtual[vchannel.id]["value"]
                    panTilt[2] = 256  # 16bit
                    pan_rotating_geometries[geometry][0] = (
                        pan_rotating_geometries[geometry][0] * 256
                        + data_virtual[vchannel.id]["value"]
                    )
                    pan_rotating_geometries[geometry][2] = 256

                elif vchannel.id == "Tilt":
                    panTilt[1] = data_virtual[vchannel.id]["value"]
                    tilt_rotating_geometries[geometry][0] = data_virtual[vchannel.id][
                        "value"
                    ]
                elif vchannel.id == "+Tilt":
                    panTilt[1] = panTilt[1] * 256 + data_virtual[vchannel.id]["value"]
                    panTilt[3] = 256  # 16bit
                    tilt_rotating_geometries[geometry][0] = (
                        tilt_rotating_geometries[geometry][0] * 256
                        + data_virtual[vchannel.id]["value"]
                    )
                    tilt_rotating_geometries[geometry][2] = 256

                elif vchannel.id == "PanRotate":
                    pan_cont_rotating_geometries[geometry][0] = data_virtual[
                        vchannel.id
                    ]["value"]

                elif vchannel.id == "TiltRotate":
                    tilt_cont_rotating_geometries[geometry][0] = data_virtual[
                        vchannel.id
                    ]["value"]

                elif vchannel.id == "Zoom":
                    zoom = data_virtual[vchannel.id]["value"]
                elif vchannel.id == "XYZ_X":
                    xyz_moving_geometries[geometry][0] = data_virtual[vchannel.id][
                        "value"
                    ]
                elif vchannel.id == "XYZ_Y":
                    xyz_moving_geometries[geometry][1] = data_virtual[vchannel.id][
                        "value"
                    ]
                elif vchannel.id == "XYZ_Z":
                    xyz_moving_geometries[geometry][2] = data_virtual[vchannel.id][
                        "value"
                    ]
                elif vchannel.id == "Rot_X":
                    xyz_rotating_geometries[geometry][0] = data_virtual[vchannel.id][
                        "value"
                    ]
                elif vchannel.id == "Rot_Y":
                    xyz_rotating_geometries[geometry][1] = data_virtual[vchannel.id][
                        "value"
                    ]
                elif vchannel.id == "Rot_Z":
                    xyz_rotating_geometries[geometry][2] = data_virtual[vchannel.id][
                        "value"
                    ]

        for c in range(len(channels)):
            geometry = str(self.channels[c].geometry)
            if geometry not in rgb_mixing_geometries.keys():
                rgb_mixing_geometries[geometry] = [None] * 12
            if geometry not in xyz_moving_geometries.keys():
                xyz_moving_geometries[geometry] = [None, None, None]
            if geometry not in xyz_rotating_geometries.keys():
                xyz_rotating_geometries[geometry] = [None, None, None]
            if geometry not in shutter_dimmer_geometries.keys():
                shutter_dimmer_geometries[geometry] = [None, None, None, 1]  # + bits
            if geometry not in pan_rotating_geometries.keys():
                pan_rotating_geometries[geometry] = [None, 1]
            if geometry not in tilt_rotating_geometries.keys():
                tilt_rotating_geometries[geometry] = [None, 1]
            if geometry not in pan_cont_rotating_geometries.keys():
                pan_cont_rotating_geometries[geometry] = [None, 1]
            if geometry not in tilt_cont_rotating_geometries.keys():
                tilt_cont_rotating_geometries[geometry] = [None, 1]

            if channels[c] == "Dimmer":
                shutter_dimmer_geometries[geometry][1] = data[c]
            if channels[c] == "+Dimmer":
                shutter_dimmer_geometries[geometry][1] = (
                    shutter_dimmer_geometries[geometry][1] * 256 + data[c]
                )
                shutter_dimmer_geometries[geometry][3] = 256
            elif channels[c] == "Shutter1":
                shutter_dimmer_geometries[geometry][0] = data[c]
            elif channels[c] == "ColorAdd_R" or channels[c] == "ColorRGB_Red":
                rgb_mixing_geometries[geometry][0] = data[c]
            elif channels[c] == "ColorAdd_G" or channels[c] == "ColorRGB_Green":
                rgb_mixing_geometries[geometry][1] = data[c]
            elif channels[c] == "ColorAdd_B" or channels[c] == "ColorRGB_Blue":
                rgb_mixing_geometries[geometry][2] = data[c]
            elif channels[c] == "ColorAdd_W":
                rgb_mixing_geometries[geometry][3] = data[c]
            elif channels[c] == "ColorAdd_WW":
                rgb_mixing_geometries[geometry][4] = data[c]
            elif channels[c] == "ColorAdd_CW":
                rgb_mixing_geometries[geometry][5] = data[c]
            elif channels[c] == "ColorAdd_RY":
                rgb_mixing_geometries[geometry][6] = data[c]
            elif channels[c] == "ColorAdd_GY":
                rgb_mixing_geometries[geometry][7] = data[c]
            elif channels[c] == "ColorAdd_UV":
                rgb_mixing_geometries[geometry][8] = data[c]
            elif channels[c] == "ColorAdd_C":
                rgb_mixing_geometries[geometry][9] = data[c]
            elif channels[c] == "ColorAdd_M":
                rgb_mixing_geometries[geometry][10] = data[c]
            elif channels[c] == "ColorAdd_Y":
                rgb_mixing_geometries[geometry][11] = data[c]
            elif channels[c] == "ColorSub_C":
                cmy[0] = data[c]
            elif channels[c] == "ColorSub_M":
                cmy[1] = data[c]
            elif channels[c] == "ColorSub_Y":
                cmy[2] = data[c]
            elif channels[c] == "Pan":
                panTilt[0] = data[c]
                pan_rotating_geometries[geometry][0] = data[c]
            elif channels[c] == "+Pan":
                panTilt[0] = panTilt[0] * 256 + data[c]
                panTilt[2] = 256  # 16bit
                pan_rotating_geometries[geometry][0] = (
                    pan_rotating_geometries[geometry][0] * 256 + data[c]
                )
                pan_rotating_geometries[geometry][1] = 256
            elif channels[c] == "Tilt":
                panTilt[1] = data[c]
                tilt_rotating_geometries[geometry][0] = data[c]
            elif channels[c] == "+Tilt":
                panTilt[1] = panTilt[1] * 256 + data[c]
                panTilt[3] = 256  # 16bit
                tilt_rotating_geometries[geometry][0] = (
                    tilt_rotating_geometries[geometry][0] * 256 + data[c]
                )
                tilt_rotating_geometries[geometry][1] = 256

            elif channels[c] == "PanRotate":
                pan_cont_rotating_geometries[geometry][0] = data[c]
            elif channels[c] == "TiltRotate":
                tilt_cont_rotating_geometries[geometry][0] = data[c]
            elif channels[c] == "Zoom":
                zoom = data[c]
            elif channels[c] == "Color1":
                color1 = data[c]
            elif channels[c] == "Color2":
                color1 = data[c]
            elif channels[c] == "CTC":
                ctc = data[c]
            elif channels[c] == "CTO":
                ctc = data[c]
            elif channels[c] == "CTB":
                ctc = data[c]
            elif channels[c] == "Iris":
                iris = data[c]
            elif channels[c] == "ColorMacro1":
                color1 = data[c]
            elif channels[c] == "Gobo1":
                gobo1[0] = data[c]
            elif channels[c] == "Gobo1Pos" or channels[c] == "Gobo1PosRotate":
                gobo1[1] = data[c]
            elif channels[c] == "Gobo2":
                gobo2[0] = data[c]
            elif channels[c] == "Gobo2Pos" or channels[c] == "Gobo2PosRotate":
                gobo2[1] = data[c]
            elif channels[c] == "XYZ_X":
                xyz_moving_geometries[geometry][0] = data[c]
            elif channels[c] == "XYZ_Y":
                xyz_moving_geometries[geometry][1] = data[c]
            elif channels[c] == "XYZ_Z":
                xyz_moving_geometries[geometry][2] = data[c]
            elif channels[c] == "Rot_X":
                xyz_rotating_geometries[geometry][0] = data[c]
            elif channels[c] == "Rot_Y":
                xyz_rotating_geometries[geometry][1] = data[c]
            elif channels[c] == "Rot_Z":
                xyz_rotating_geometries[geometry][2] = data[c]

        self.remove_unset_geometries_from_multigeometry_attributes_all(
            rgb_mixing_geometries
        )
        self.remove_unset_geometries_from_multigeometry_attributes_all(
            xyz_moving_geometries
        )
        self.remove_unset_geometries_from_multigeometry_attributes_all(
            xyz_rotating_geometries
        )
        self.remove_unset_geometries_from_multigeometry_attributes_3(
            shutter_dimmer_geometries
        )
        self.remove_unset_geometries_from_multigeometry_attributes_1(
            pan_rotating_geometries
        )
        self.remove_unset_geometries_from_multigeometry_attributes_1(
            tilt_rotating_geometries
        )
        self.remove_unset_geometries_from_multigeometry_attributes_1(
            pan_cont_rotating_geometries
        )
        self.remove_unset_geometries_from_multigeometry_attributes_1(
            tilt_cont_rotating_geometries
        )

        colorwheel_color = None
        if color1 is not None:
            colorwheel_color = self.get_colorwheel_color(color1)
        color_temperature = None
        if ctc is not None:
            color_temperature = self.get_color_temperature(ctc)

        for geometry, colors in rgb_mixing_geometries.items():
            if len(rgb_mixing_geometries) == 1:
                geometry = None
            self.updateRGB(
                colors, geometry, colorwheel_color, color_temperature, current_frame
            )

        if not len(rgb_mixing_geometries):  # handle units without mixing
            if (
                not all([c == 255 for c in self.gel_color_rgb])
                or colorwheel_color is not None
                or color_temperature is not None
            ):  # gel color is set and has priority or there is a color wheel or color_temperature
                self.updateRGB(
                    [255] * 12, None, colorwheel_color, color_temperature, current_frame
                )

        if cmy[0] is not None and cmy[1] is not None and cmy[2] is not None:
            self.updateCMY(cmy, colorwheel_color, color_temperature, current_frame)

        if "Target" in self.objects:
            if self.ignore_movement_dmx:
                # programming by target, dmx for p/t locked
                if "Target" in self.objects:
                    target = self.objects["Target"].object
                    if current_frame and self.dmx_cache_dirty:
                        target.keyframe_insert(
                            data_path="location", frame=current_frame
                        )
                        target.keyframe_insert(
                            data_path="rotation_euler", frame=current_frame
                        )
            else:
                if panTilt[0] is None:
                    panTilt[0] = (
                        0 * panTilt[2]
                    )  # if the device doesn't have pan, align head with base
                if panTilt[1] is None:
                    panTilt[1] = 0 * panTilt[3]
                pan = (panTilt[0] / (panTilt[2] * 127.0) - 1) * 540 * (math.pi / 360)
                tilt = (panTilt[1] / (panTilt[3] * 127.0) - 1) * 270 * (math.pi / 360)
                self.updatePanTiltViaTarget(pan, tilt, current_frame)

        else:  # no Target
            for geometry, pan_vals in pan_rotating_geometries.items():
                pan = (pan_vals[0] / (pan_vals[1] * 127.0) - 1) * 540 * (math.pi / 360)
                self.updatePTDirectly(geometry, "pan", pan, current_frame)
            for geometry, tilt_vals in tilt_rotating_geometries.items():
                tilt = (
                    (tilt_vals[0] / (tilt_vals[1] * 127.0) - 1) * 270 * (math.pi / 360)
                )
                self.updatePTDirectly(geometry, "tilt", tilt, current_frame)

        for geometry, pan_rotate in pan_cont_rotating_geometries.items():
            self.set_pan_tilt_rotation(
                geometry=geometry,
                axis="pan",
                rotation=pan_rotate[0],
                current_frame=current_frame,
            )

        for geometry, tilt_rotate in tilt_cont_rotating_geometries.items():
            self.set_pan_tilt_rotation(
                geometry=geometry,
                axis="tilt",
                rotation=tilt_rotate[0],
                current_frame=current_frame,
            )

        if zoom is not None:
            self.updateZoom(zoom, current_frame)

        self.hide_gobo_geometry(gobo1, gobo2, iris, current_frame)

        if gobo1[0] is not None:
            self.updateGobo(gobo1, 1, current_frame)

        if gobo2[0] is not None:
            self.updateGobo(gobo2, 2, current_frame)

        if iris is not None:
            if 0 <= iris <= 255:
                iris = iris * 12 / 255
                self.update_iris(iris, current_frame)

        for geometry, xyz in xyz_moving_geometries.items():
            self.updatePosition(
                geometry=geometry,
                x=xyz[0],
                y=xyz[1],
                z=xyz[2],
                current_frame=current_frame,
            )

        for geometry, xyz in xyz_rotating_geometries.items():
            self.updateRotation(
                geometry=geometry,
                x=xyz[0],
                y=xyz[1],
                z=xyz[2],
                current_frame=current_frame,
            )

        for geometry, shutter_dimmer in shutter_dimmer_geometries.items():
            if len(shutter_dimmer_geometries) == 1:
                geometry = None
            if shutter_dimmer[0] is not None or shutter_dimmer[1] is not None:
                if shutter_dimmer[0] is None:
                    shutter_dimmer[0] = (
                        0  # if device doesn't have shutter, set default value
                    )
                if shutter_dimmer[1] is None:
                    shutter_dimmer[1] = (
                        100  # if device doesn't have dimmer, set default value
                    )
                self.updateShutterDimmer(
                    shutter_dimmer[0],
                    shutter_dimmer[1],
                    geometry,
                    shutter_dimmer[3],
                    current_frame,
                )

        self.keyframe_objects_with_bdmx_drivers(current_frame)

        if current_frame:
            self.dmx_cache_dirty = False
        # end of render block

    def set_pan_tilt_rotation(self, geometry, axis, rotation, current_frame):
        if axis == "pan":
            mobile_type = "yoke"
            offset = 2
            lock_rotation = self.lock_pan_rotation

        else:  # tilt
            mobile_type = "head"
            offset = 0
            lock_rotation = self.lock_tilt_rotation

        if geometry is None:
            geometry = self.get_mobile_type(mobile_type)
        else:
            geometry = self.get_object_by_geometry_name(geometry)
        if geometry:
            geometry.rotation_mode = "XYZ"
            geometry.driver_remove("rotation_euler", offset)

            if lock_rotation:
                rotation = rotation / 128 * 360 * (math.pi / 360)
                geometry.rotation_euler[offset] = (
                    rotation  # just some value, not very precise
                )
            else:
                if rotation != 0:
                    driver = geometry.driver_add("rotation_euler", offset)
                    value = (
                        rotation - 128
                    )  # rotating in both direction, slowest in the middle
                    driver.driver.expression = f"frame*{value * 0.005}"

            if current_frame and self.dmx_cache_dirty:
                geometry.keyframe_insert(data_path="location", frame=current_frame)
                geometry.keyframe_insert(
                    data_path="rotation_euler", frame=current_frame
                )

    def remove_unset_geometries_from_multigeometry_attributes_all(self, dictionary):
        """Remove items with values of all None"""

        remove_empty_items = []
        for geometry, items in dictionary.items():
            if all([i == None for i in items]):
                remove_empty_items.append(geometry)
        for geo in remove_empty_items:
            del dictionary[geo]

    def remove_unset_geometries_from_multigeometry_attributes_1(self, dictionary):
        """Remove items with 1 value of None"""

        remove_empty_items = []
        for geometry, items in dictionary.items():
            if items[0] is None:
                remove_empty_items.append(geometry)
        for geo in remove_empty_items:
            del dictionary[geo]

    def remove_unset_geometries_from_multigeometry_attributes_3(self, dictionary):
        """Remove items with 3 value of None"""

        remove_empty_items = []
        for geometry, items in dictionary.items():
            if items[0] is None and items[1] is None and items[2] is None:
                remove_empty_items.append(geometry)
        for geo in remove_empty_items:
            del dictionary[geo]

    def light_object_for_geometry_exists(self, geometry):
        """Check if there is any light or emitter matching geometry name of a color attribute"""
        for light in self.lights:
            if geometry in light.object.data.name:
                return True
        for emitter_material in self.emitter_materials:
            if geometry in emitter_material.name:
                return True
        return False

    def get_channel_by_attribute(self, attribute):
        for channel in self.channels:
            if channel.id == attribute:
                return channel

    def updateShutterDimmer(self, shutter, dimmer, geometry, bits, current_frame):
        DMX_Log.log.info(("set shutter, dimmer", shutter, dimmer, geometry))
        dmx = bpy.context.scene.dmx
        if geometry is not None:
            geometry = geometry.replace(" ", "_")
        last_shutter_value = 0
        last_dimmer_value = 0
        try:
            for emitter_material in self.emitter_materials:
                if shutter > 0 and shutter != 255:
                    break  # no need to do the expensive value settings if we do this anyway in shutter timer
                if geometry is not None:
                    if geometry in emitter_material.name or any(
                        g in geometry for g in emitter_material["parent_geometries"]
                    ):
                        DMX_Log.log.info(("matched emitter", geometry))
                        emitter_material.material.node_tree.nodes[1].inputs[
                            STRENGTH
                        ].default_value = 1 * (dimmer / (255.0 * bits))
                else:
                    emitter_material.material.node_tree.nodes[1].inputs[
                        STRENGTH
                    ].default_value = 1 * (dimmer / (255.0 * bits))
                if current_frame and self.dmx_cache_dirty:
                    emitter_material.material.node_tree.nodes[1].inputs[
                        STRENGTH
                    ].keyframe_insert(data_path="default_value", frame=current_frame)

            for light in self.lights:
                last_shutter_value = light.object.data["shutter_value"]
                last_dimmer_value = light.object.data["shutter_dimmer_value"]
                light.object.data["shutter_value"] = shutter
                light.object.data["shutter_dimmer_value"] = dimmer
                light.object.data["shutter_dimmer_bits"] = bits
                flux = light.object.data["flux"] * dmx.beam_intensity_multiplier
                # we should improve this to get more Cycles/Eevee compatibility... add a driver which would adjust the intensity
                # depending on the IES linking or not, adding drivers: https://blender.stackexchange.com/a/314329/176407
                # plus, we would still need to calculate correct energy, so they match between Cycles/Eevee
                # here are some ideas: https://blender.stackexchange.com/a/180533/176407
                if shutter > 0 and shutter != 255:
                    break  # no need to do the expensive value settings if we do this anyway in shutter timer

                if geometry is not None:
                    if geometry in light.object.data.name or any(
                        g in geometry for g in light.object.data["parent_geometries"]
                    ):
                        DMX_Log.log.info("matched emitter")
                        light.object.data.energy = (dimmer / (255.0 * bits)) * flux

                else:
                    light.object.data.energy = (dimmer / (255.0 * bits)) * flux

                if current_frame and self.dmx_cache_dirty:
                    light.object.data.keyframe_insert(
                        data_path="energy", frame=current_frame
                    )

            for nodes in self.geometry_nodes:
                vector = nodes.node.nodes["Vector"]
                if dimmer > 0:
                    vector.vector = (0, 0, -1)
                else:
                    vector.vector = (0, 0, 0)
                if current_frame and self.dmx_cache_dirty:
                    vector.keyframe_insert(data_path="vector", frame=current_frame)

        except Exception as e:
            DMX_Log.log.error(f"Error updating dimmer {e}")

        if (
            last_shutter_value == 0
            or last_shutter_value == 255
            or last_dimmer_value == 0
        ) and (shutter > 0 and shutter != 255):
            bpy.app.timers.register(self.runStrobe)
            DMX_Log.log.info("Register shutter timer")

        return dimmer

    def runStrobe(self):
        # TODO: try to convert strobe to a blender driver, less resources and keyframable
        try:
            exit_timer = False
            dimmer_value = 0  # reused also for emitter
            dimmer_bits = 1

            for light in self.lights:
                if light.object.data["shutter_value"] == 0:
                    exit_timer = True
                if light.object.data["shutter_value"] == 255:
                    exit_timer = True
                if light.object.data["shutter_dimmer_value"] == 0:
                    exit_timer = True
                dimmer_value = 0
                flux = light.object.data["flux"]
                if light.object.data["shutter_counter"] == 1:
                    dimmer_value = light.object.data["shutter_dimmer_value"]
                    dimmer_bits = light.object.data["shutter_dimmer_bits"]
                if (
                    light.object.data["shutter_counter"]
                    > light.object.data["shutter_value"]
                ):
                    light.object.data["shutter_counter"] = 0

                light.object.data.energy = (dimmer_value / (255.0 * dimmer_bits)) * flux
                light.object.data["shutter_counter"] += 1

            # Here we can reuse data we got from the light object...
            for emitter_material in self.emitter_materials:
                emitter_material.material.node_tree.nodes[1].inputs[
                    STRENGTH
                ].default_value = 1 * (dimmer_value / (255.0 * dimmer_bits))

            if exit_timer:
                DMX_Log.log.info("Killing shutter timer")
                return None  # exit the timer

        except Exception as e:
            DMX_Log.log.error(f"Error updating lights and emitters {e}")
            DMX_Log.log.info("Killing shutter timer")
            return None  # kills the timer
        return 1.0 / 24.0

    def updateRGB(
        self, colors, geometry, colorwheel_color, color_temperature, current_frame
    ):
        if geometry is not None:
            geometry = geometry.replace(" ", "_")
        DMX_Log.log.info(("color change for geometry", geometry, colors))
        colors = [
            c if c is not None else 0 for c in colors
        ]  # replace None with 0, can happen if someone maps colors across geometries...
        rgb = colors_to_rgb(colors)
        DMX_Log.log.info(("color change for geometry", geometry, colors, rgb))
        if colorwheel_color is not None:
            rgb = add_rgb(rgb, colorwheel_color[:3])
        if color_temperature is not None:
            rgb = add_rgb(rgb, color_temperature[:3])
        rgb = add_rgb(self.gel_color_rgb, rgb)
        rgb = [c / 255.0 for c in rgb]
        DMX_Log.log.info(("color change for geometry", geometry, colors, rgb))

        try:
            for emitter_material in self.emitter_materials:
                DMX_Log.log.info(
                    (
                        "emitter:",
                        emitter_material.name,
                        list(emitter_material["parent_geometries"]),
                    )
                )
                if geometry is not None:
                    if geometry in emitter_material.name or any(
                        g in geometry for g in emitter_material["parent_geometries"]
                    ):
                        DMX_Log.log.info("matched emitter")
                        emitter_material.material.node_tree.nodes[1].inputs[
                            COLOR
                        ].default_value = rgb + [1]
                else:
                    emitter_material.material.node_tree.nodes[1].inputs[
                        COLOR
                    ].default_value = rgb + [1]

                if current_frame and self.dmx_cache_dirty:
                    emitter_material.material.node_tree.nodes[1].inputs[
                        COLOR
                    ].keyframe_insert(data_path="default_value", frame=current_frame)

            for light in self.lights:
                if geometry is not None:
                    DMX_Log.log.info(
                        ("light:", light.object.data.name, "geometry:", geometry, rgb)
                    )
                    if geometry in light.object.data.name or any(
                        g in geometry for g in light.object.data["parent_geometries"]
                    ):
                        DMX_Log.log.info("matched light")
                        light.object.data.color = rgb
                else:
                    light.object.data.color = rgb

                if current_frame and self.dmx_cache_dirty:
                    light.object.data.keyframe_insert(
                        data_path="color", frame=current_frame
                    )
        except Exception as e:
            DMX_Log.log.error(f"Error updating RGB {e}")
            traceback.print_exception(e)
        return rgb

    def updateCMY(self, cmy, colorwheel_color, color_temperature, current_frame):
        rgb = [0, 0, 0]
        rgb = cmy_to_rgb(cmy)
        if all([c == 255 for c in rgb]) and (
            colorwheel_color is not None or color_temperature is not None
        ):
            rgb = [
                0,
                0,
                0,
            ]  # without this, default white would always be overwriting ctc

        if colorwheel_color is not None:
            rgb = add_rgb(rgb, colorwheel_color)
        if color_temperature is not None:
            rgb = add_rgb(rgb, color_temperature[:3])
        if not all([c == 255 for c in self.gel_color_rgb]):
            rgb = add_rgb(self.gel_color_rgb, rgb)

        rgb = [c / 255.0 for c in rgb]

        for emitter_material in self.emitter_materials:
            emitter_material.material.node_tree.nodes[1].inputs[COLOR].default_value = (
                rgb + [1]
            )
            if current_frame and self.dmx_cache_dirty:
                emitter_material.material.node_tree.nodes[1].inputs[
                    COLOR
                ].keyframe_insert(data_path="default_value", frame=current_frame)
        for light in self.lights:
            light.object.data.color = rgb
            if current_frame and self.dmx_cache_dirty:
                light.object.data.keyframe_insert(
                    data_path="color", frame=current_frame
                )
        return cmy

    def updateZoom(self, zoom, current_frame):
        try:
            spot_size = math.radians(zoom)
            gobo_diameter = 2.2 * 0.01 * math.tan(math.radians(zoom / 2))
            # 2x because result is 1/2 of diameter
            # .2 because there was a bit of a spill
            # 0.01 is distance from the beam
            # zoom/2 because we need 1/2 of the beam angle

            for obj in self.collection.objects:
                if "gobo" in obj.get("geometry_type", ""):
                    beam_diameter = obj.get("beam_radius", 0) * 2
                    if beam_diameter:
                        if gobo_diameter > beam_diameter:
                            gobo_diameter = beam_diameter
                    obj.dimensions = (gobo_diameter, gobo_diameter, 0)
                    if current_frame and self.dmx_cache_dirty:
                        obj.keyframe_insert(data_path="scale", frame=current_frame)

                if "laser" in obj.get("geometry_type", ""):
                    # multiplication makes this easy to only apply on used axis
                    # but we could also re-calculate this to proper angle

                    obj.rotation_euler[0] = obj.get("rot_x", 0) * zoom * 0.1
                    obj.rotation_euler[1] = obj.get("rot_y", 0) * zoom * 0.1
                    obj.rotation_euler[2] = obj.get("rot_z", 0) * zoom * 0.1
                    if current_frame and self.dmx_cache_dirty:
                        obj.keyframe_insert(
                            data_path="rotation_euler", frame=current_frame
                        )

            for light in self.lights:
                light.object.data.spot_size = spot_size

                if current_frame and self.dmx_cache_dirty:
                    light.object.data.keyframe_insert(
                        data_path="spot_size", frame=current_frame
                    )

        except Exception as e:
            DMX_Log.log.error(f"Error updating zoom {e}")
        return zoom

    def get_colorwheel_color(self, color1):
        if not len(self["slot_colors"]) or color1 == 0:
            return

        colors = self["slot_colors"]
        index = int(color1 / int(255 / (len(colors) - 1)))

        if len(colors) > index:
            return list(colors[index])

    def get_color_temperature(self, ctc):
        if ctc == 0:
            return
        if 1 <= ctc <= 255:
            ctc = 1000 + (ctc - 1) * (12000 - 1000) / (255 - 1)
            ctc -= ctc % -100  # round to full 100s
            return kelvin_table[ctc]
        else:
            return

    def update_iris(self, iris, current_frame):
        for obj in self.collection.objects:  # EEVEE
            if "gobo" in obj.get("geometry_type", ""):
                material = self.gobo_materials[obj.name].material
                mix = material.node_tree.nodes.get("Iris Size")
                DMX_Log.log.debug(("found iris", material, mix))
                iris_size = mix.inputs[3]
                iris_size.default_value = iris

                if current_frame and self.dmx_cache_dirty:
                    # light_obj.data.keyframe_insert(data_path="shadow_soft_size", frame=current_frame)
                    iris_size.keyframe_insert(
                        data_path="default_value", frame=current_frame
                    )

        for light in self.lights:  # CYCLES
            light_obj = light.object
            mix = light_obj.data.node_tree.nodes.get("Iris Size")
            iris_size = mix.inputs[3]
            iris_size.default_value = iris

            if current_frame and self.dmx_cache_dirty:
                # light_obj.data.keyframe_insert(data_path="shadow_soft_size", frame=current_frame)
                iris_size.keyframe_insert(
                    data_path="default_value", frame=current_frame
                )

    def updateGobo(self, gobo, n, current_frame):
        if "gobos1" not in self.images:
            self.hide_gobo([1, 2], current_frame=current_frame)
            return

        if gobo is None:
            self.hide_gobo([n], current_frame=current_frame)
            return

        if gobo[0] == 0:
            self.hide_gobo([n], current_frame=current_frame)
            return

        gobos = self.images["gobos1"]
        if not gobos.count:
            self.hide_gobo([1, 2], current_frame=current_frame)
            return

        DMX_Log.log.debug(("update gobo", gobo, n))
        self.hide_gobo([n], False, current_frame=current_frame)
        index = int(gobo[0] / int(255 / (gobos.count - 1)))
        self.set_gobo_slot(n, index, current_frame=current_frame)
        if gobo[1] is not None:
            self.set_gobo_rotation(gobo, n, current_frame=current_frame)

    def set_gobo_rotation(self, gobo, n, current_frame):
        for obj in self.collection.objects:  # EEVEE
            if "gobo" in obj.get("geometry_type", ""):
                material = self.gobo_materials[obj.name].material
                gobo_rotation = material.node_tree.nodes.get(f"Gobo{n}Rotation")
                if gobo[1] < 128:  # half for indexing
                    gobo_rotation.inputs[3].driver_remove("default_value")
                    gobo_rotation.inputs[3].default_value = (
                        (gobo[1] / 62.0 - 1) * 360 * (math.pi / 360)
                    )
                else:  # half for rotation
                    driver = gobo_rotation.inputs[3].driver_add("default_value")
                    value = (
                        gobo[1] - 128 - 62
                    )  # rotating in both direction, slowest in the middle
                    driver.driver.expression = f"frame*{value * 0.005}"

                if current_frame and self.dmx_cache_dirty:
                    gobo_rotation.inputs[3].keyframe_insert(
                        data_path="default_value", frame=current_frame
                    )

        for light in self.lights:  # CYCLES
            light_obj = light.object
            gobo_rotation = light_obj.data.node_tree.nodes.get(f"Gobo{n}Rotation")
            if gobo[1] < 128:  # half for indexing
                gobo_rotation.inputs[3].driver_remove("default_value")
                gobo_rotation.inputs[3].default_value = (
                    (gobo[1] / 62.0 - 1) * 360 * (math.pi / 360)
                )
            else:  # half for rotation
                driver = gobo_rotation.inputs[3].driver_add("default_value")
                value = (
                    gobo[1] - 128 - 62
                )  # rotating in both direction, slowest in the middle
                driver.driver.expression = f"frame*{value * 0.005}"

            if current_frame and self.dmx_cache_dirty:
                gobo_rotation.inputs[3].keyframe_insert(
                    data_path="default_value", frame=current_frame
                )

    def updatePosition(self, geometry=None, x=None, y=None, z=None, current_frame=None):
        if geometry is None:
            geometry = self.objects["Root"].object
        else:
            geometry = self.get_object_by_geometry_name(geometry)

        if x is not None:
            geometry.location.x = (128 - x) * 0.1
        if y is not None:
            geometry.location.y = (128 - y) * 0.1
        if z is not None:
            geometry.location.z = (128 - z) * 0.1
        if geometry is not None:
            if current_frame and self.dmx_cache_dirty:
                geometry.keyframe_insert(data_path="location", frame=current_frame)

    def updateRotation(self, geometry=None, x=None, y=None, z=None, current_frame=None):
        if geometry is None:
            geometry = self.objects["Root"].object
        else:
            geometry = self.get_object_by_geometry_name(geometry)

        geometry.rotation_mode = "XYZ"
        if x is not None:
            geometry.rotation_euler[0] = (x / 127.0 - 1) * 360 * (math.pi / 360)
        if y is not None:
            geometry.rotation_euler[1] = (y / 127.0 - 1) * 360 * (math.pi / 360)
        if z is not None:
            geometry.rotation_euler[2] = (z / 127.0 - 1) * 360 * (math.pi / 360)
        if geometry is not None:
            if current_frame and self.dmx_cache_dirty:
                geometry.keyframe_insert(
                    data_path="rotation_euler", frame=current_frame
                )

    def updatePanTiltViaTarget(self, pan, tilt, current_frame):
        DMX_Log.log.info("Updating pan tilt")

        base = self.objects["Root"].object
        pan = pan + base.rotation_euler[2]  # take base z rotation into consideration
        tilt = tilt + base.rotation_euler[0]  # take base x rotation into consideration

        # calculate target position, head will follow
        try:
            head = self.objects["Head"].object
        except Exception as e:
            self.updatePTDirectly(None, "pan", pan, current_frame)
            self.updatePTDirectly(None, "tilt", tilt, current_frame)
            DMX_Log.log.info(
                "Updating pan/tilt directly via geometries, not via Target due to not located Head"
            )
            return

        head_location = head.matrix_world.translation

        target = self.objects["Target"].object

        eul = mathutils.Euler(
            (0.0, base.rotation_euler[1] + tilt, base.rotation_euler[0] + pan), "XYZ"
        )
        vec = mathutils.Vector((0.0, 0.0, -(target.location - head_location).length))
        vec.rotate(eul)

        target.location = vec + head_location

        if current_frame and self.dmx_cache_dirty:
            target.keyframe_insert(data_path="location", frame=current_frame)
            target.keyframe_insert(data_path="rotation_euler", frame=current_frame)

    def updatePTDirectly(self, geometry, axis_type, value, current_frame):
        if axis_type == "pan":
            mobile_type = "yoke"
            offset = 2
        else:  # tilt
            mobile_type = "head"
            offset = 0
        if geometry is None:
            geometry = self.get_mobile_type(mobile_type)
        else:
            geometry = self.get_object_by_geometry_name(geometry)
        if geometry:
            geometry.rotation_mode = "XYZ"
            geometry.rotation_euler[offset] = value
            if current_frame and self.dmx_cache_dirty:
                geometry.keyframe_insert(data_path="location", frame=current_frame)
                geometry.keyframe_insert(
                    data_path="rotation_euler", frame=current_frame
                )

    def keyframe_objects_with_bdmx_drivers(self, current_frame=None):
        if current_frame and self.dmx_cache_dirty:
            for obj in bpy.data.objects:
                if obj.data is None:
                    continue
                if not hasattr(obj.animation_data, "drivers"):
                    continue

                for fcurve in obj.animation_data.drivers:
                    driver = fcurve.driver
                    if driver is not None:
                        if driver.expression.startswith("bdmx"):
                            obj.keyframe_insert(fcurve.data_path, frame=current_frame)

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
        if model_collection.objects is None:
            return None
        for obj in model_collection.objects:
            if obj.get("geometry_root", False):
                return obj

    def get_tilt(self, model_collection):
        for obj in model_collection.objects:
            for channel in self.channels:
                if "Tilt" == channel.id and channel.geometry == obj.get(
                    "original_name", "None"
                ):
                    return obj
            for channel in self.virtual_channels:
                if "Tilt" == channel.id and channel.geometry == obj.get(
                    "original_name", "None"
                ):
                    return obj

    def getProgrammerData(self):
        channels = [c.id for c in self.channels]
        data = DMX_Data.get(self.universe, self.address, len(channels))
        params = {}
        for c in range(len(channels)):
            params[channels[c]] = data[c]
        return params

    def select(self, select_target=False):
        dmx = bpy.context.scene.dmx
        if dmx.display_2D:
            # in 2D view deselect the 2D symbol, unhide the fixture and select base,
            # to allow movement and rotation
            self.objects["2D Symbol"].object.select_set(False)
            targets = []

            for obj in self.collection.objects:
                if "Target" in self.objects:
                    targets.append(self.objects["Target"].object)
                if "pigtail" in obj.get("geometry_type", ""):
                    obj.hide_set(not bpy.context.scene.dmx.display_pigtails)
                    obj.hide_viewport = (
                        not bpy.context.scene.dmx.display_pigtails
                    )  # keyframing
                    obj.hide_render = not bpy.context.scene.dmx.display_pigtails
                if obj.get("2d_symbol", None):
                    continue
                obj.hide_set(False)
                obj.hide_viewport = False  # keyframing
                obj.hide_render = False

            if not select_target:
                if "Root" in self.objects:
                    try:
                        self.objects["Root"].object.select_set(True)
                    except Exception as e:
                        DMX_Log.log.error(
                            f"Fixture doesn't exist, remove it via Fixture list → Edit → X"
                        )
            else:
                if len(targets):
                    for target in targets:
                        target.select_set(True)

        else:
            if not select_target:
                if "Root" in self.objects:
                    try:
                        self.objects["Root"].object.select_set(True)
                    except Exception as e:
                        DMX_Log.log.error(
                            f"Fixture doesn't exist, remove it via Fixture list → Edit → X"
                        )
            else:
                targets = []
                for obj in self.collection.objects:
                    if "Target" in self.objects:
                        targets.append(self.objects["Target"].object)

                if len(targets):
                    for target in targets:
                        target.select_set(True)

        DMX_OSC_Handlers.fixture_selection(self)
        dmx.updatePreviewVolume()
        self.sync_fixture_selection()

    def sync_fixture_selection(self):
        """This sets the active selection in the Fixtures list, as
        we may select by shortcuts, mouse or an operator"""

        dmx = bpy.context.scene.dmx
        for idx, fixture in enumerate(dmx.fixtures):
            if fixture == self:
                dmx.selected_fixture_index = idx
                return

    def unselect(self):
        dmx = bpy.context.scene.dmx
        if "Root" in self.objects:
            try:
                self.objects["Root"].object.select_set(False)
            except Exception as e:
                DMX_Log.log.error(
                    f"Fixture doesn't exist, remove it via Fixture list → Edit → X"
                )
        if "Target" in self.objects:
            self.objects["Target"].object.select_set(False)
        if "2D Symbol" in self.objects:
            try:
                self.objects["2D Symbol"].object.select_set(False)
            except Exception as e:
                DMX_Log.log.error(
                    f"Fixture doesn't exist, remove it via Fixture list → Edit → X"
                )
        if dmx.display_2D:
            for obj in self.collection.objects:
                if obj.get("2d_symbol", None):
                    continue
                obj.hide_set(True)
                obj.hide_viewport = True  # need for keyframing
                obj.hide_render = True
        dmx.updatePreviewVolume()
        self.sync_fixture_selection()

    def toggleSelect(self):
        selected = False
        for obj in self.objects:
            if obj.object in bpy.context.selected_objects:
                selected = True
                break
        if selected:
            self.unselect()
        else:
            self.select()

    def is_selected(self):
        selected = False
        for obj in self.objects:
            if obj.object in bpy.context.selected_objects:
                selected = True
                break
        return selected

    def clear(self):
        for i, ch in enumerate(self.channels):
            DMX_Data.set(self.universe, self.address + i, ch.default)
        self.render()

    def set_gobo_slot(self, n, index=-1, current_frame=None):
        gobos = self.images[f"gobos{n}"]
        for obj in self.collection.objects:  # EEVEE
            if "gobo" in obj.get("geometry_type", ""):
                material = self.gobo_materials[obj.name].material
                texture = material.node_tree.nodes.get(f"Gobo{n}Texture")
                DMX_Log.log.debug(("Found gobo nodes:", n, material, texture))
                if texture.image is None:
                    texture.image = gobos.image
                    texture.image.source = "SEQUENCE"
                    texture.image_user.frame_duration = 1
                    texture.image_user.use_auto_refresh = True
                texture.image_user.frame_offset = index

                if current_frame and self.dmx_cache_dirty:
                    texture.image_user.keyframe_insert(
                        data_path="frame_offset", frame=current_frame
                    )
                break

        for light in self.lights:  # CYCLES
            light_obj = light.object
            texture = light_obj.data.node_tree.nodes.get(f"Gobo{n}Texture")
            if texture.image is None:
                texture.image = gobos.image
                texture.image.source = "SEQUENCE"
                texture.image_user.frame_duration = 1
                texture.image_user.use_auto_refresh = True
            texture.image_user.frame_offset = index

            if current_frame and self.dmx_cache_dirty:
                texture.image_user.keyframe_insert(
                    data_path="frame_offset", frame=current_frame
                )

    def set_spot_diameter_to_point(self, light_obj):
        if bpy.context.scene.dmx.reduced_beam_diameter_in_cycles == "REDUCED":
            light_obj.data.shadow_soft_size = 0.01
        elif bpy.context.scene.dmx.reduced_beam_diameter_in_cycles == "CUSTOM":
            if light_obj.data.get("beam_radius_pin_sized_for_gobos", True):
                light_obj.data.shadow_soft_size = 0.01
        elif bpy.context.scene.dmx.reduced_beam_diameter_in_cycles == "FULL":
            size = light_obj.data.get("beam_radius", 0.01)
            light_obj.data.shadow_soft_size = size

    def set_spot_diameter_to_normal(self, light_obj):
        size = light_obj.data.get("beam_radius", 0.01)
        light_obj.data.shadow_soft_size = size

    def hide_gobo_geometry(self, gobo1, gobo2, iris, current_frame=None):
        hide = True

        if gobo1[0] is not None:
            if gobo1[0] != 0:
                hide = False

        if gobo2[0] is not None:
            if gobo2[0] != 0:
                hide = False

        if iris is not None:
            if iris != 0:
                hide = False
        for obj in self.collection.objects:
            if "gobo" in obj.get("geometry_type", ""):
                obj.hide_viewport = hide
                obj.hide_render = hide
                if current_frame and self.dmx_cache_dirty:
                    obj.keyframe_insert("hide_viewport", frame=current_frame)
                    obj.keyframe_insert("hide_render", frame=current_frame)

        for light in self.lights:  # CYCLES
            light_obj = light.object
            if hide:
                self.set_spot_diameter_to_normal(
                    light_obj
                )  # make the beam large if no gobo is used
            else:
                self.set_spot_diameter_to_point(light_obj)
            if current_frame and self.dmx_cache_dirty:
                light_obj.data.keyframe_insert(
                    data_path="shadow_soft_size", frame=current_frame
                )

    def hide_gobo(self, n=[1, 2], hide=True, current_frame=None):
        for obj in self.collection.objects:
            if "gobo" in obj.get("geometry_type", ""):
                material = self.gobo_materials[obj.name].material
                for i in n:
                    mix_factor = material.node_tree.nodes.get(f"Gobo{i}Mix").inputs[
                        "Factor"
                    ]
                    mix_factor.default_value = 1 if hide else 0
                    if current_frame and self.dmx_cache_dirty:
                        DMX_Log.log.debug(("hide gobo", hide, i))
                        mix_factor.keyframe_insert(
                            data_path="default_value", frame=current_frame
                        )

        for light in self.lights:  # CYCLES
            light_obj = light.object
            for i in n:
                mix_factor = light_obj.data.node_tree.nodes.get(f"Gobo{i}Mix").inputs[
                    "Factor"
                ]
                mix_factor.default_value = 1 if hide else 0
                if current_frame and self.dmx_cache_dirty:
                    mix_factor.keyframe_insert(
                        data_path="default_value", frame=current_frame
                    )

    def has_attributes(self, attributes, lower=False):
        temp_data = bpy.context.window_manager.dmx

        def low(id):
            if lower:
                return id.lower()
            else:
                return id

        if len(temp_data.active_subfixtures) > 0:
            in_fixture_real = [
                low(channel.id)
                for channel in self.channels
                if any(channel.geometry == g.name for g in temp_data.active_subfixtures)
            ]
            in_fixture_virtual = [
                low(channel.id)
                for channel in self.virtual_channels
                if any(channel.geometry == g.name for g in temp_data.active_subfixtures)
            ]

            real = any(
                any(attribute == item for item in in_fixture_real)
                for attribute in attributes
            )
            virtual = any(
                any(attribute == item for item in in_fixture_virtual)
                for attribute in attributes
            )
        else:
            in_fixture_real = [low(channel.id) for channel in self.channels]
            in_fixture_virtual = [low(channel.id) for channel in self.virtual_channels]

            real = any(
                any(attribute == item for item in in_fixture_real)
                for attribute in attributes
            )
            virtual = any(
                any(attribute == item for item in in_fixture_virtual)
                for attribute in attributes
            )

        return real or virtual

    def add_ies(self, ies_file_path):
        if os.path.isfile(ies_file_path):
            with open(ies_file_path, "r", encoding="cp1252") as f:
                ies_file = f.read()
        else:
            return

        unique_name = f"{self.uuid}-255"
        if unique_name in bpy.data.texts:
            bpy.data.texts.remove(bpy.data.texts[unique_name])

        if "255" in self.ies_data:
            ies_data = self.ies_data["255"]
        else:
            ies_data = self.ies_data.add()
            ies_data.name = "255"

        ies_data.ies = bpy.data.texts.new(unique_name)
        ies_data.ies.from_string(ies_file)
        for light in self.lights:
            light_obj = light.object
            ies = light_obj.data.node_tree.nodes.get("IES Texture")
            if ies is None:
                ies = get_ies_node(light_obj)
            ies.ies = ies_data.ies

    def remove_ies(self):
        self.ies_data.clear()
        zoom_ranges = ["255"]
        for zoom_range in zoom_ranges:
            unique_name = f"{self.uuid}-{zoom_range}"
            if unique_name in bpy.data.texts:
                bpy.data.texts.remove(bpy.data.texts[unique_name])
        for light in self.lights:
            light_obj = light.object
            ies = light_obj.data.node_tree.nodes.get("IES Texture")
            if ies is not None:
                light_obj.data.node_tree.nodes.remove(ies)

    def to_mvr_fixture(self):
        matrix = 0
        uuid_focus_point = None
        for obj in self.objects:
            if obj.object.get("geometry_root", False):
                m = obj.object.matrix_world
                matrix = [list(col) for col in m.col]
            if "Target" in obj.name:
                uuid_focus_point = obj.object.get("uuid", None)

        r, g, b = list(self.gel_color_rgb)[:3]
        x, y, z = rgb2xyY(r, g, b)
        color = f"{x},{y},{z}"

        return pymvr.Fixture(
            name=self.name,
            uuid=self.uuid,
            gdtf_spec=self.profile,
            gdtf_mode=self.mode,
            fixture_id=self.fixture_id,
            addresses=[
                pymvr.Address(dmx_break=0, universe=self.universe, address=self.address)
            ],
            matrix=pymvr.Matrix(matrix),
            focus=uuid_focus_point,
            color=color,
            classing=self.classing,
        )

    def focus_to_mvr_focus_point(self):
        for obj in self.objects:
            if "Target" in obj.name:
                matrix = None
                uuid_ = None
                m = obj.object.matrix_world
                matrix = [list(col) for col in m.col]
                uuid_ = obj.object.get("uuid", None)
                if matrix is None or uuid_ is None:
                    DMX_Log.log.error(f"Matrix or uuid of a Target not defined")
                    return
                return pymvr.FocusPoint(
                    matrix=pymvr.Matrix(matrix),
                    uuid=uuid_,
                    name=f"Target for {self.name}",
                )

    def onDepsgraphUpdate(self):
        # TODO: rename this and hook again somewhere.
        # After not touching depsgraph (was causing slowdowns and crashes),
        # we do not have this functionality
        # Check if any object was deleted
        for obj in self.objects:
            if not len(obj.object.users_collection):
                bpy.context.scene.dmx.removeFixture(self)
                break

        # check if target is moving and the rest of objects is not selected
        # (programming by target)
        if "Target" in self.objects:
            target = self.objects["Target"].object
            update_by_target = False
            for obj in self.objects:
                if obj.object in bpy.context.selected_objects:
                    if obj.object != target:
                        # exit early if body (any part) and target were selected and moved
                        return
                    if obj.object == target:
                        update_by_target = True
            if update_by_target:
                self.ignore_movement_dmx = True
                return
