# Copyright (C) 2020 Hugo Aboud, Kaspars Jaudzems, vanous
#
# This file is part of BlenderDMX.
#
# BlenderDMX is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# BlenderDMX is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <https://www.gnu.org/licenses/>.

import math
import os
import traceback
from types import SimpleNamespace
import uuid as py_uuid
from itertools import zip_longest

import bpy
import mathutils
import pymvr
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    FloatVectorProperty,
    IntProperty,
    IntVectorProperty,
    FloatProperty,
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
from .i18n import DMX_Lang
from .gdtf_file import DMX_GDTF_File
from .logging_setup import DMX_Log
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
from .color_utils import (
    add_rgb,
    cmy_to_rgb,
    colors_to_rgb,
    kelvin_table,
    kelvin_to_rgb,
    rgb2xyY,
)

# Shader Nodes default labels
# Blender API naming convention is inconsistent for internationalization
# Every label used is listed here, so it's easier to fix it on new API updates
STRENGTH = "Strength"
COLOR = "Color"

_ = DMX_Lang._
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

# fmt: on


class DMX_Fixture_Channel_Set(PropertyGroup):
    def dmx_to_physical(self, dmx_value):
        # test if this works or if we need physical_min, physical_max
        dmx_range = self.dmx_to - self.dmx_from
        if dmx_range == 0:
            return self.physical_from

        if ((self.dmx_from - self.dmx_to) + self.physical_from) == 0:
            return (self.dmx_from - self.dmx_from) * (
                self.physical_to - self.physical_from
            )
        return (dmx_value - self.dmx_from) * (self.physical_to - self.physical_from) / (
            self.dmx_to - self.dmx_from
        ) + self.physical_from

    # fmt: off

    name_: StringProperty(
        name = "Name",
        default = '')
    dmx_from: IntProperty(
        name = "DMX From",
        default = 1)
    dmx_to: IntProperty(
        name = "DMX To",
        default = 1)
    physical_from: FloatProperty(
        name = "Physical From",
        default = 1)
    physical_to: FloatProperty(
        name = "Physical To",
        default = 1)
    wheel_slot: IntProperty(
        name = "Wheel Slot",
        default = 0)


class DMX_Fixture_Channel_Function(PropertyGroup):
    def dmx_to_physical(self, dmx_value):
        # test if this works or if we need physical_min, physical_max
        dmx_range = self.dmx_to - self.dmx_from
        if dmx_range == 0:
            return self.physical_from

        if ((self.dmx_from - self.dmx_to) + self.physical_from) == 0:
            return (self.dmx_from - self.dmx_from) * (
                self.physical_to - self.physical_from
            )
        return (dmx_value - self.dmx_from) * (self.physical_to - self.physical_from) / (
            self.dmx_to - self.dmx_from
        ) + self.physical_from

    # fmt: off

    attribute: StringProperty(
        name = "Attribute",
        default = '')
    name_: StringProperty(
        name = "Name",
        default = "")
    dmx_from: IntProperty(
        name = "DMX From",
        default = 1)
    dmx_to: IntProperty(
        name = "DMX To",
        default = 1)
    physical_from: FloatProperty(
        name = "Physical From",
        default = 1)
    physical_to: FloatProperty(
        name = "Physical To",
        default = 1)
    mode_master: StringProperty(
        name = "Mode master",
        default = '')
    mode_from: IntProperty(
        name = "Mode From",
        default = 1)
    mode_to: IntProperty(
        name = "Mode To",
        default = 1)
    mm_dmx_break: IntProperty(
        name = "ModeMaster break",
        default = 1)
    mm_offsets: IntVectorProperty(
        name = "ModeMaster offsets",
        size = 2,
        default = (0,0))
    mm_offsets_bytes: IntProperty(
        name = "ModeMaster Bytes",
        default = 1)
    channel_sets: CollectionProperty(
        name = "Fixture > Channels > Channel Functions > Channel Sets",
        type = DMX_Fixture_Channel_Set
    )


# fmt: on
class DMX_Fixture_Channel(PropertyGroup):
    def has_attribute(self, attribute):
        return any(
            getattr(item, "attribute") == attribute for item in self.channel_functions
        )

    def get_function_attribute_data(self, dmx_value, dmx_data, skip_mode_master=False):
        wheel_slot = None
        for ch_f in self.channel_functions:
            # get a function which contains dmx from/to encapsulating our current dmx value
            if ch_f.dmx_from <= dmx_value <= ch_f.dmx_to:
                DMX_Log.log.debug(("have a function", ch_f.attribute))
                if ch_f.mode_master != "" and skip_mode_master is False:
                    DMX_Log.log.debug("check if mm confirms it")
                    mode_from = ch_f.mode_from
                    mode_to = ch_f.mode_to
                    mm_dmx_value_coarse = dmx_data[ch_f.mm_dmx_break].get(
                        ch_f.mm_offsets[0], None
                    )
                    if mm_dmx_value_coarse is not None:
                        mm_dmx_value_fine = None
                        mm_dmx_value_final = mm_dmx_value_coarse
                        if ch_f.mm_offsets_bytes > 1:
                            mm_dmx_value_fine = dmx_data[ch_f.mm_dmx_break][
                                ch_f.mm_offsets[1]
                            ]
                            mm_dmx_value_final = (
                                mm_dmx_value_coarse << 8
                            ) | mm_dmx_value_fine

                        DMX_Log.log.debug(
                            ("mm_dmx_value", mm_dmx_value_final, mode_from, mode_to)
                        )
                        if mode_from <= mm_dmx_value_final <= mode_to:
                            DMX_Log.log.debug(
                                ("return the function confirmed by mm", ch_f.attribute)
                            )
                            attribute = ch_f.attribute
                            physical_value = ch_f.dmx_to_physical(
                                dmx_value
                            )  # calculate physical value for this dmx value

                            for ch_s in ch_f.channel_sets:
                                if ch_s.dmx_from <= dmx_value <= ch_s.dmx_to:
                                    wheel_slot = ch_s.wheel_slot
                                    physical_value = ch_s.dmx_to_physical(
                                        dmx_value
                                    )  # calculate physical value for this dmx value
                            return attribute, physical_value, wheel_slot

                        DMX_Log.log.debug("try another channel function or exit")
                else:
                    DMX_Log.log.debug(("no mm, return", ch_f.attribute))
                    attribute = ch_f.attribute
                    physical_value = ch_f.dmx_to_physical(
                        dmx_value
                    )  # calculate physical value for this dmx value

                    for ch_s in ch_f.channel_sets:
                        if ch_s.dmx_from <= dmx_value <= ch_s.dmx_to:
                            wheel_slot = ch_s.wheel_slot
                            physical_value = ch_s.dmx_to_physical(
                                dmx_value
                            )  # calculate physical value for this dmx value
                    return attribute, physical_value, wheel_slot
        DMX_Log.log.debug("exit with None")
        return None, None, None

    # fmt: off
    attribute: StringProperty(
        name = "Attribute",
        default = '')
    name_: StringProperty(
        name = "Name",
        default = "")
    # do not use "name" as blender will be adding 001 to ensure unique names...

    offsets: IntVectorProperty(
        name = "DMX Channel offset",
        size = 2,
        default = (0,0))
    offsets_bytes: IntProperty(
        name = "Bytes",
        default = 1)
    defaults: IntVectorProperty(
        name = "Fixture > Channel > Default",
        size = 2,
        default = (0,0))
    geometry: StringProperty(
        name = "Fixture > Geometry",
        default = '')
    dmx_break: IntProperty(
        name = "DMX Break of the channel",
        default = 1)
    channel_functions: CollectionProperty(
        name = "Fixture > Channels > Channel Functions",
        type = DMX_Fixture_Channel_Function
    )


class DMX_Break(PropertyGroup):
    def ensure_universe_exists(self, context):
        dmx = bpy.context.scene.dmx
        dmx.ensureUniverseExists(self.universe)

    dmx_break: IntProperty(
        name="DMX Break",
        description="DMX entry point",
        default=0,
        min=0,
        max=511,
    )
    universe: IntProperty(
        name="Fixture > Universe",
        description="Fixture DMX Universe",
        default=0,
        min=0,
        max=511,
        update=ensure_universe_exists,
    )

    address: IntProperty(
        name="Fixture > Address", description="Fixture DMX Address", default=1, min=1
    )  # no max for now

    channels_count: IntProperty(
        name="Number of channels",
        description="Number of DMX channels",
        default=0,
        min=0,
    )  # no max for now


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

    def on_use_target(self, context):
        self.follow_target_constraint_enable(self.use_target)

    use_target: BoolProperty(
        name = "Use Target",
        description="Follow the target",
        update = on_use_target,
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

    dmx_breaks:  CollectionProperty(
            name = "DMX Break",
            type = DMX_Break)

    use_fixtures_channel_functions: BoolProperty(
        name = _("Use Fixtures Physical Properties"),
        description = _("Use Channel Functions of this fixture"),
        default = True)

    # fmt: on

    def build(
        self,
        name,
        profile,
        mode,
        dmx_breaks,
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
        bpy.ops.object.select_all(action="DESELECT")
        for obj in bpy.data.objects:
            obj.select_set(False)
        # clear possible existing selections in Blender

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

        self.gel_color_rgb = [int(255 * i) for i in gel_color[:3]]
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
        self.dmx_breaks.clear()

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
        gdtf_profile = DMX_GDTF_File.load_gdtf_profile(profile)
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
            dmx_mode = gdtf_profile.dmx_modes[0]
            mode = dmx_mode.name

        has_gobos = False

        self.process_channels(dmx_mode.dmx_channels, self.channels)
        self.process_channels(dmx_mode.virtual_channels, self.virtual_channels)

        for channel in self.channels:
            if "Gobo" in channel.attribute:
                has_gobos = True
                break
        if not has_gobos:
            for channel in self.virtual_channels:
                if "Gobo" in channel.attribute:
                    has_gobos = True
                    break

        for mode_dmx_break, provided_dmx_break in zip_longest(
            dmx_mode.dmx_breaks, dmx_breaks
        ):
            if mode_dmx_break is None:
                continue
            if provided_dmx_break is None:
                provided_dmx_break = SimpleNamespace(dmx_break=0, address=0, universe=0)
            new_break = self.dmx_breaks.add()
            new_break.dmx_break = mode_dmx_break.dmx_break
            new_break.universe = provided_dmx_break.universe
            new_break.address = provided_dmx_break.address
            new_break.channels_count = mode_dmx_break.channels_count

        if not self.dmx_breaks:
            new_break = self.dmx_breaks.add()
            new_break.dmx_break = 0
            new_break.universe = 0
            new_break.address = 0
            new_break.channels_count = 0

        # Get all gobos
        if has_gobos:
            gobo_wheels_links = set(
                [
                    (ch_fnc.attribute.str_link, ch_fnc.wheel.str_link)
                    for channel in dmx_mode.dmx_channels
                    for logical in channel.logical_channels
                    for ch_fnc in logical.channel_functions
                    if ch_fnc.attribute.str_link in ["Gobo1", "Gobo2"]
                ]
            )

            if gobo_wheels_links:
                gobo_seq = DMX_GDTF.extract_gobos_as_sequence(
                    gdtf_profile, gobo_wheels_links
                )
                for gobo in gobo_seq:
                    gobo1 = self.images.add()
                    gobo1.name = gobo["attribute"]
                    gobo1.image = gobo
                    gobo1.count = gobo["count"]
                    gobo1.attribute = gobo["attribute"]
                    gobo1.wheel = gobo["wheel"]
                    gobo1.image.pack()

        if "Gobo1" not in self.images:
            has_gobos = False  # faulty GDTF might have channels but no images

        color_wheels_links = set(
            [
                (ch_fnc.attribute.str_link, ch_fnc.wheel.str_link)
                for channel in dmx_mode.dmx_channels
                for logical in channel.logical_channels
                for ch_fnc in logical.channel_functions
                if ch_fnc.attribute.str_link
                in ["Color1", "Color2", "Color3", "ColorMacro1"]
            ]
        )

        self["slot_colors"] = {}

        if color_wheels_links:
            slot_colors = DMX_GDTF.get_wheel_slot_colors(
                gdtf_profile, color_wheels_links
            )
            self["slot_colors"] = slot_colors

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
                for slot in emitter.material_slots:
                    # handle beam geometries with multiple material slots
                    slot.link = "OBJECT"
                    slot.material = emitter_material
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

    def process_channels(self, dmx_mode_channels, channels):
        for dmx_channel in dmx_mode_channels:
            new_channel = channels.add()
            new_channel.attribute = dmx_channel.attribute.str_link
            new_channel.name_ = dmx_channel.name
            new_channel.geometry = dmx_channel.geometry
            new_channel.dmx_break = dmx_channel.dmx_break
            if dmx_channel.offset is not None:
                new_channel.offsets = tuple((dmx_channel.offset + [0])[:2])
                new_channel.offsets_bytes = len(dmx_channel.offset)
            else:
                # virtual channels are 8 bit now
                new_channel.offsets = (0, 0)
                new_channel.offsets_bytes = 1

            # blender programmer cannot control white, set it to 0
            if "ColorAdd_W" in dmx_channel.attribute.str_link:
                new_channel.defaults = (0, 0)
            else:
                fine_default = 0
                if new_channel.offsets_bytes > 1:
                    fine_default = dmx_channel.default.get_value(fine=True)
                new_channel.defaults = (dmx_channel.default.get_value(), fine_default)

            for logical_channel in dmx_channel.logical_channels:
                for channel_function in logical_channel.channel_functions:
                    new_channel_function = new_channel.channel_functions.add()
                    new_channel_function.attribute = channel_function.attribute.str_link
                    new_channel_function.name_ = channel_function.name

                    if channel_function.mode_master is not None:
                        mode_master = channel_function.mode_master.str_link
                        new_channel_function.mode_master = (
                            mode_master if mode_master is not None else ""
                        )
                        new_channel_function.mode_from = (
                            channel_function.mode_from.value
                        )
                        new_channel_function.mode_to = channel_function.mode_to.value

                    # virtual channels have byte count 4 which is too much for blender int
                    # and we treat them as 8 bit only anyways
                    if channel_function.dmx_from.byte_count > 2:
                        new_channel_function.dmx_from = (
                            channel_function.dmx_from.get_value()
                        )
                    else:
                        new_channel_function.dmx_from = channel_function.dmx_from.value

                    if channel_function.dmx_to.byte_count > 2:
                        new_channel_function.dmx_to = (
                            channel_function.dmx_to.get_value()
                        )
                    else:
                        new_channel_function.dmx_to = channel_function.dmx_to.value

                    new_channel_function.physical_from = (
                        channel_function.physical_from.value
                    )
                    new_channel_function.physical_to = (
                        channel_function.physical_to.value
                    )

                    for channel_set in channel_function.channel_sets:
                        new_channel_set = new_channel_function.channel_sets.add()
                        new_channel_set.name_ = channel_set.name or ""
                        if channel_set.dmx_from.byte_count > 2:
                            new_channel_set.dmx_from = channel_set.dmx_from.get_value()
                        else:
                            new_channel_set.dmx_from = channel_set.dmx_from.value

                        if channel_set.dmx_to.byte_count > 2:
                            new_channel_set.dmx_to = channel_set.dmx_to.get_value()
                        else:
                            new_channel_set.dmx_to = channel_set.dmx_to.value

                        new_channel_set.physical_from = channel_set.physical_from.value
                        new_channel_set.physical_to = channel_set.physical_to.value
                        new_channel_set.wheel_slot = channel_set.wheel_slot_index

        # create a link from channel function to a mode_master channel:
        for dmx_channel in channels:
            modemasters_exist = False
            for ch_function in dmx_channel.channel_functions:
                if ch_function.mode_master != "":
                    for ch in channels:
                        if ch.name_ == ch_function.mode_master:
                            modemasters_exist = True
                            ch_function.mm_dmx_break = ch.dmx_break
                            ch_function.mm_offsets = ch.offsets
                            ch_function.mm_offsets_bytes = ch.offsets_bytes
            if not modemasters_exist:
                # create some caching of dmx channel data
                # we ignore channels with mode dependencies
                # as checking for the cache and then finding that we need
                # to re-calculate the value anyways is probably more expensive
                dmx_channel["cached_channel"] = {
                    "dmx_value": -1,
                    "attribute": None,
                    "value": -1,
                    "index": -1,
                }

    # Interface Methods #

    def setDMX(self, pvalues):
        temp_data = bpy.context.window_manager.dmx

        # channels = [c.id for c in self.channels]
        # virtuals = [c.id for c in self.virtual_channels]

        for attribute, value in pvalues.items():
            for channel in self.channels:
                if channel.attribute == attribute or channel.has_attribute(attribute):
                    if len(temp_data.active_subfixtures) > 0:
                        if any(
                            channel.geometry == g.name
                            for g in temp_data.active_subfixtures
                        ):
                            for dmx_break in self.dmx_breaks:
                                if dmx_break.dmx_break == channel.dmx_break:
                                    DMX_Log.log.info(
                                        ("Set DMX data", channel.attribute, value)
                                    )
                                    DMX_Data.set(
                                        dmx_break.universe,
                                        dmx_break.address + channel.offsets[0] - 1,
                                        value,
                                    )
                    else:
                        for dmx_break in self.dmx_breaks:
                            if dmx_break.dmx_break == channel.dmx_break:
                                DMX_Log.log.info(
                                    (
                                        "Set DMX data",
                                        channel.attribute,
                                        channel.offsets[0],
                                        value,
                                    )
                                )
                                DMX_Data.set(
                                    dmx_break.universe,
                                    dmx_break.address + channel.offsets[0] - 1,
                                    value,
                                )
            for vchannel in self.virtual_channels:
                if vchannel.attribute == attribute:
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

        dmx_data = {}
        data_for_cached = []

        for dmx_break in self.dmx_breaks:
            new_data = DMX_Data.get(
                dmx_break.universe, dmx_break.address, dmx_break.channels_count
            )
            result = {i: value for i, value in enumerate(new_data, 1)}
            dmx_data[dmx_break.dmx_break] = result
            data_for_cached += new_data

        data_virtual = DMX_Data.get_virtual(self.name)

        cached_dmx_data = [int(b) for b in data_for_cached] + [
            int(b["value"]) for b in data_virtual.values()
        ]  # create cache
        if (
            list(self["dmx_values"]) == cached_dmx_data
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

        dmx = bpy.context.scene.dmx
        self["dmx_values"] = cached_dmx_data
        panTilt = [None, None]
        cmy = [None, None, None]
        zoom = None
        color1 = None
        color2 = None
        color3 = None
        color4 = None
        ctc = None, None
        iris = None
        rgb_mixing_geometries = {}
        xyz_moving_geometries = {}
        xyz_rotating_geometries = {}
        shutter_dimmer_geometries = {}  # dimmer, shutter, strobe
        pan_rotating_geometries = {}
        tilt_rotating_geometries = {}

        pan_cont_rotating_geometries = {}
        tilt_cont_rotating_geometries = {}

        gobo1 = [
            None,
            None,
            None,
        ]  # gobo selection (Gobo1), gobo indexing Gobo1Pos, rotation (Gobo1PosRotate)
        gobo2 = [
            None,
            None,
            None,
        ]  # gobo selection (Gobo2), gobo indexing Gobo2Pos, rotation (Gobo2PosRotate)

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
                shutter_dimmer_geometries[geometry] = [None, None, None]
            if geometry not in pan_rotating_geometries.keys():
                pan_rotating_geometries[geometry] = [None]
            if geometry not in tilt_rotating_geometries.keys():
                tilt_rotating_geometries[geometry] = [None]
            if geometry not in pan_cont_rotating_geometries.keys():
                pan_cont_rotating_geometries[geometry] = [None]
            if geometry not in tilt_cont_rotating_geometries.keys():
                tilt_cont_rotating_geometries[geometry] = [None]

            DMX_Log.log.debug(("virtual", vchannel.attribute))
            if vchannel.attribute in data_virtual:
                dmx_value_virtual = data_virtual[vchannel.attribute]["value"]
                DMX_Log.log.debug(("data virtual", dmx_value_virtual))
                channel_function_attribute = None

                (
                    channel_function_attribute,
                    channel_function_physical_value,
                    channel_set_wheel_slot,
                ) = vchannel.get_function_attribute_data(
                    dmx_value_virtual, None, skip_mode_master=True
                )
                if not self.use_fixtures_channel_functions:
                    channel_function = dmx.get_default_channel_function_by_attribute(
                        channel_function_attribute
                    )
                    if channel_function:
                        channel_function_attribute = channel_function.attribute
                        channel_function_physical_value = (
                            channel_function.dmx_to_physical(dmx_value_virtual)
                        )

                DMX_Log.log.debug(
                    (
                        "virtual result",
                        channel_function_attribute,
                        channel_function_physical_value,
                    )
                )

                if channel_function_attribute == "Dimmer":
                    shutter_dimmer_geometries[geometry][0] = (
                        channel_function_physical_value
                    )
                elif channel_function_attribute == "Shutter1":
                    shutter_dimmer_geometries[geometry][1] = (
                        channel_function_physical_value if dmx_value_virtual > 0 else 1
                    )
                    # we set the shutter to be open by default

                elif channel_function_attribute == "Shutter1Strobe":
                    shutter_dimmer_geometries[geometry][2] = (
                        channel_function_physical_value
                    )
                elif (
                    vchannel.attribute == "ColorAdd_R"
                    or vchannel.attribute == "ColorRGB_Red"
                ):
                    rgb_mixing_geometries[geometry][0] = data_virtual[
                        vchannel.attribute
                    ]["value"]
                elif (
                    vchannel.attribute == "ColorAdd_G"
                    or vchannel.attribute == "ColorRGB_Green"
                ):
                    rgb_mixing_geometries[geometry][1] = data_virtual[
                        vchannel.attribute
                    ]["value"]
                elif (
                    vchannel.attribute == "ColorAdd_B"
                    or vchannel.attribute == "ColorRGB_Blue"
                ):
                    rgb_mixing_geometries[geometry][2] = data_virtual[
                        vchannel.attribute
                    ]["value"]
                elif vchannel.attribute == "ColorSub_C":
                    cmy[0] = data_virtual[vchannel.attribute]["value"]
                elif vchannel.attribute == "ColorSub_M":
                    cmy[1] = data_virtual[vchannel.attribute]["value"]
                elif vchannel.attribute == "ColorSub_Y":
                    cmy[2] = data_virtual[vchannel.attribute]["value"]
                elif channel_function_attribute == "Pan":
                    panTilt[0] = channel_function_physical_value
                    pan_rotating_geometries[geometry][0] = (
                        channel_function_physical_value
                    )

                elif channel_function_attribute == "Tilt":
                    panTilt[1] = channel_function_physical_value
                    tilt_rotating_geometries[geometry][0] = (
                        channel_function_physical_value
                    )

                elif channel_function_attribute == "PanRotate":
                    pan_cont_rotating_geometries[geometry][0] = (
                        channel_function_physical_value
                    )

                elif channel_function_attribute == "TiltRotate":
                    tilt_cont_rotating_geometries[geometry][0] = (
                        channel_function_physical_value
                    )

                elif channel_function_attribute == "Zoom":
                    zoom = channel_function_physical_value

                elif channel_function_attribute == "CTC":
                    ctc = channel_function_physical_value, dmx_value_virtual
                elif channel_function_attribute == "CTO":
                    ctc = channel_function_physical_value, dmx_value_virtual
                elif channel_function_attribute == "CTB":
                    ctc = channel_function_physical_value, dmx_value_virtual
                elif vchannel.attribute == "XYZ_X":
                    xyz_moving_geometries[geometry][0] = data_virtual[
                        vchannel.attribute
                    ]["value"]
                elif vchannel.attribute == "XYZ_Y":
                    xyz_moving_geometries[geometry][1] = data_virtual[
                        vchannel.attribute
                    ]["value"]
                elif vchannel.attribute == "XYZ_Z":
                    xyz_moving_geometries[geometry][2] = data_virtual[
                        vchannel.attribute
                    ]["value"]
                elif vchannel.attribute == "Rot_X":
                    xyz_rotating_geometries[geometry][0] = data_virtual[
                        vchannel.attribute
                    ]["value"]
                elif vchannel.attribute == "Rot_Y":
                    xyz_rotating_geometries[geometry][1] = data_virtual[
                        vchannel.attribute
                    ]["value"]
                elif vchannel.attribute == "Rot_Z":
                    xyz_rotating_geometries[geometry][2] = data_virtual[
                        vchannel.attribute
                    ]["value"]

        for channel in self.channels:
            if channel.dmx_break not in dmx_data:
                continue  # this happens before the fixture is fully patched

            geometry = channel.geometry
            if geometry not in rgb_mixing_geometries.keys():
                rgb_mixing_geometries[geometry] = [None] * 12
            if geometry not in xyz_moving_geometries.keys():
                xyz_moving_geometries[geometry] = [None, None, None]
            if geometry not in xyz_rotating_geometries.keys():
                xyz_rotating_geometries[geometry] = [None, None, None]
            if geometry not in shutter_dimmer_geometries.keys():
                shutter_dimmer_geometries[geometry] = [None, None, None]
            if geometry not in pan_rotating_geometries.keys():
                pan_rotating_geometries[geometry] = [None]
            if geometry not in tilt_rotating_geometries.keys():
                tilt_rotating_geometries[geometry] = [None]
            if geometry not in pan_cont_rotating_geometries.keys():
                pan_cont_rotating_geometries[geometry] = [None]
            if geometry not in tilt_cont_rotating_geometries.keys():
                tilt_cont_rotating_geometries[geometry] = [None]

            if not channel.offsets:
                # if channel has no address, we cannot continue
                DMX_Log.log.error(
                    (
                        "No offsets in channel, skipping",
                        channel.attribute,
                        channel.offsets_bytes,
                    )
                )
                continue

            dmx_value_coarse = dmx_data[channel.dmx_break].get(channel.offsets[0], None)
            if dmx_value_coarse is None:
                DMX_Log.log.error(
                    (
                        "Address offset not in dmx data, skipping. You may have to re-insert or re-edit the GDTF fixture into the scene",
                        channel.attribute,
                        channel.dmx_break,
                        channel.offsets[0],
                    )
                )
                continue

            dmx_value_fine = None
            dmx_value_final = dmx_value_coarse
            if channel.offsets_bytes > 1:
                dmx_value_fine = dmx_data[channel.dmx_break][channel.offsets[1]]
                dmx_value_final = (dmx_value_coarse << 8) | dmx_value_fine

            skip_attr_search = False
            if "cached_channel" in channel:
                cached_dmx = channel["cached_channel"].get("dmx_value")
                cached_attr = channel["cached_channel"].get("attribute", None)
                cached_value = channel["cached_channel"].get("value")
                cached_slot = channel["cached_channel"].get("index")

                if dmx_value_final == int(cached_dmx) and cached_attr is not None:
                    skip_attr_search = True
                    channel_function_attribute = cached_attr
                    channel_function_physical_value = cached_value
                    channel_set_wheel_slot = cached_slot
                    DMX_Log.log.debug(
                        (
                            "use cached data",
                            channel.name_,
                            channel_function_attribute,
                            channel_function_physical_value,
                            channel_set_wheel_slot,
                        )
                    )

            if not skip_attr_search and self.use_fixtures_channel_functions:
                DMX_Log.log.debug(
                    ("search for fresh attribute data", channel.attribute)
                )
                DMX_Log.log.debug(
                    (
                        "start function search",
                        channel.name_,
                        channel.offsets,
                        channel.offsets_bytes,
                    )
                )

                (
                    channel_function_attribute,
                    channel_function_physical_value,
                    channel_set_wheel_slot,
                ) = channel.get_function_attribute_data(dmx_value_final, dmx_data)

                if "cached_channel" in channel:
                    DMX_Log.log.debug(("set cached data", channel.attribute))
                    channel["cached_channel"]["dmx_value"] = dmx_value_final
                    channel["cached_channel"]["attribute"] = channel_function_attribute
                    channel["cached_channel"]["value"] = channel_function_physical_value
                    channel["cached_channel"]["index"] = channel_set_wheel_slot or -1

            if not self.use_fixtures_channel_functions:
                channel_function = dmx.get_default_channel_function_by_attribute(
                    channel_function_attribute
                )
                if channel_function:
                    channel_function_attribute = channel_function.attribute
                    channel_function_physical_value = channel_function.dmx_to_physical(
                        dmx_value_coarse
                    )

            DMX_Log.log.debug(
                (
                    "channel function",
                    channel_function_attribute,
                    channel_function_physical_value,
                    dmx_value_coarse,
                )
            )

            if channel_function_attribute == "Dimmer":
                shutter_dimmer_geometries[geometry][0] = channel_function_physical_value
            elif channel_function_attribute == "Shutter1":
                shutter_dimmer_geometries[geometry][1] = (
                    channel_function_physical_value if dmx_value_coarse > 0 else 1
                )
            # we set the shutter to be open by default

            elif channel_function_attribute == "Shutter1Strobe":
                shutter_dimmer_geometries[geometry][2] = channel_function_physical_value
            elif (
                channel.attribute == "ColorAdd_R" or channel.attribute == "ColorRGB_Red"
            ):
                rgb_mixing_geometries[geometry][0] = dmx_data[channel.dmx_break][
                    channel.offsets[0]
                ]
            elif (
                channel.attribute == "ColorAdd_G"
                or channel.attribute == "ColorRGB_Green"
            ):
                rgb_mixing_geometries[geometry][1] = dmx_data[channel.dmx_break][
                    channel.offsets[0]
                ]
            elif (
                channel.attribute == "ColorAdd_B"
                or channel.attribute == "ColorRGB_Blue"
            ):
                rgb_mixing_geometries[geometry][2] = dmx_data[channel.dmx_break][
                    channel.offsets[0]
                ]
            elif channel.attribute == "ColorAdd_W":
                rgb_mixing_geometries[geometry][3] = dmx_data[channel.dmx_break][
                    channel.offsets[0]
                ]
            elif channel.attribute == "ColorAdd_WW":
                rgb_mixing_geometries[geometry][4] = dmx_data[channel.dmx_break][
                    channel.offsets[0]
                ]
            elif channel.attribute == "ColorAdd_CW":
                rgb_mixing_geometries[geometry][5] = dmx_data[channel.dmx_break][
                    channel.offsets[0]
                ]
            elif channel.attribute == "ColorAdd_RY":
                rgb_mixing_geometries[geometry][6] = dmx_data[channel.dmx_break][
                    channel.offsets[0]
                ]
            elif channel.attribute == "ColorAdd_GY":
                rgb_mixing_geometries[geometry][7] = dmx_data[channel.dmx_break][
                    channel.offsets[0]
                ]
            elif channel.attribute == "ColorAdd_UV":
                rgb_mixing_geometries[geometry][8] = dmx_data[channel.dmx_break][
                    channel.offsets[0]
                ]
            elif channel.attribute == "ColorAdd_C":
                rgb_mixing_geometries[geometry][9] = dmx_data[channel.dmx_break][
                    channel.offsets[0]
                ]
            elif channel.attribute == "ColorAdd_M":
                rgb_mixing_geometries[geometry][10] = dmx_data[channel.dmx_break][
                    channel.offsets[0]
                ]
            elif channel.attribute == "ColorAdd_Y":
                rgb_mixing_geometries[geometry][11] = dmx_data[channel.dmx_break][
                    channel.offsets[0]
                ]
            elif channel.attribute == "ColorSub_C":
                cmy[0] = dmx_data[channel.dmx_break][channel.offsets[0]]
            elif channel.attribute == "ColorSub_M":
                cmy[1] = dmx_data[channel.dmx_break][channel.offsets[0]]
            elif channel.attribute == "ColorSub_Y":
                cmy[2] = dmx_data[channel.dmx_break][channel.offsets[0]]
            elif channel_function_attribute == "Pan":
                panTilt[0] = channel_function_physical_value
                pan_rotating_geometries[geometry][0] = channel_function_physical_value
            elif channel_function_attribute == "Tilt":
                panTilt[1] = channel_function_physical_value
                tilt_rotating_geometries[geometry][0] = channel_function_physical_value

            elif channel_function_attribute == "PanRotate":
                pan_cont_rotating_geometries[geometry][0] = (
                    channel_function_physical_value
                )
            elif channel_function_attribute == "TiltRotate":
                tilt_cont_rotating_geometries[geometry][0] = (
                    channel_function_physical_value
                )
            elif channel_function_attribute == "Zoom":
                zoom = channel_function_physical_value
            elif channel_function_attribute == "Color1":
                color1 = channel_set_wheel_slot
            elif channel_function_attribute == "Color2":
                color2 = channel_set_wheel_slot
            elif channel_function_attribute == "Color3":
                color3 = channel_set_wheel_slot
            elif channel_function_attribute == "ColorMacro1":
                color4 = channel_set_wheel_slot
            elif channel_function_attribute == "CTC":
                ctc = channel_function_physical_value, dmx_value_coarse
            elif channel_function_attribute == "CTO":
                ctc = channel_function_physical_value, dmx_value_coarse
            elif channel_function_attribute == "CTB":
                ctc = channel_function_physical_value, dmx_value_coarse
            elif channel_function_attribute == "Iris":
                iris = channel_function_physical_value
            elif channel_function_attribute == "Gobo1":
                gobo1[0] = channel_set_wheel_slot
            elif channel_function_attribute == "Gobo1Pos":
                gobo1[1] = channel_function_physical_value
            elif channel_function_attribute == "Gobo1PosRotate":
                gobo1[2] = channel_function_physical_value
            elif channel_function_attribute == "Gobo2":
                gobo2[0] = channel_set_wheel_slot
            elif channel_function_attribute == "Gobo2Pos":
                gobo2[1] = channel_function_physical_value
            elif channel_function_attribute == "Gobo2PosRotate":
                gobo2[2] = channel_function_physical_value
            elif channel.attribute == "XYZ_X":
                xyz_moving_geometries[geometry][0] = dmx_data[channel.dmx_break][
                    channel.offsets[0]
                ]
            elif channel.attribute == "XYZ_Y":
                xyz_moving_geometries[geometry][1] = dmx_data[channel.dmx_break][
                    channel.offsets[0]
                ]
            elif channel.attribute == "XYZ_Z":
                xyz_moving_geometries[geometry][2] = dmx_data[channel.dmx_break][
                    channel.offsets[0]
                ]
            elif channel.attribute == "Rot_X":
                xyz_rotating_geometries[geometry][0] = dmx_data[channel.dmx_break][
                    channel.offsets[0]
                ]
            elif channel.attribute == "Rot_Y":
                xyz_rotating_geometries[geometry][1] = dmx_data[channel.dmx_break][
                    channel.offsets[0]
                ]
            elif channel.attribute == "Rot_Z":
                xyz_rotating_geometries[geometry][2] = dmx_data[channel.dmx_break][
                    channel.offsets[0]
                ]

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

        if color1 is not None and color1 != 1:
            colorwheel_color = self.get_colorwheel_color(color1, "Color1")
        if color2 is not None and color2 != 1:
            colorwheel_color = self.get_colorwheel_color(color2, "Color2")
        if color3 is not None and color3 != 1:
            colorwheel_color = self.get_colorwheel_color(color3, "Color3")
        if color4 is not None and color4 != 1:
            colorwheel_color = self.get_colorwheel_color(color4, "ColorMacro1")

        color_temperature = None
        if ctc[0] is not None:
            color_temperature = self.get_color_temperature(*ctc)

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

        if "Target" in self.objects and self.use_target:
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
                pan = math.radians(panTilt[0] or 0)
                tilt = math.radians(panTilt[1] or 0)
                self.updatePanTiltViaTarget(pan, tilt, current_frame)

        else:  # no Target
            for geometry, pan_vals in pan_rotating_geometries.items():
                self.set_pan_tilt_no_rotation(geometry=geometry, axis="pan")
                pan = math.radians(pan_vals[0])
                self.updatePTDirectly(geometry, "pan", pan, current_frame)
            for geometry, tilt_vals in tilt_rotating_geometries.items():
                self.set_pan_tilt_no_rotation(geometry=geometry, axis="tilt")
                tilt = math.radians(tilt_vals[0])
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
            self.update_zoom(zoom, current_frame)

        self.hide_gobo_geometry(gobo1, gobo2, iris, current_frame)

        if gobo1[0] is not None:
            self.update_gobo(gobo1, 1, current_frame)

        if gobo2[0] is not None:
            self.update_gobo(gobo2, 2, current_frame)

        if iris is not None:
            if 0 <= iris <= 255:
                iris = 12 - (iris * 12)
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
            shutter_dimmer[1] = (
                shutter_dimmer[1] if shutter_dimmer[1] is not None else 1
            )
            # if device doesn't have shutter, set default value
            shutter_dimmer[0] = (
                shutter_dimmer[0] if shutter_dimmer[0] is not None else 1
            )
            # if device doesn't have dimmer, set default value
            self.update_shutter_dimmer(
                shutter_dimmer[0],
                shutter_dimmer[1],
                shutter_dimmer[2],
                geometry,
                zoom,
                current_frame,
            )

        self.keyframe_objects_with_bdmx_drivers(current_frame)

        if current_frame:
            self.dmx_cache_dirty = False
        # end of render block

    def set_pan_tilt_no_rotation(self, geometry, axis):
        if axis == "pan":
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
            geometry.driver_remove("rotation_euler", offset)

    def set_pan_tilt_rotation(self, geometry, axis, rotation, current_frame):
        if axis == "pan":
            mobile_type = "yoke"
            offset = 2

        else:  # tilt
            mobile_type = "head"
            offset = 0
        if self.use_target:
            # autodisable target tracking as pan/tilt rotate
            # cannot work with track constraint
            self.use_target = False

        if geometry is None:
            geometry = self.get_mobile_type(mobile_type)
        else:
            geometry = self.get_object_by_geometry_name(geometry)
        if geometry:
            geometry.rotation_mode = "XYZ"
            geometry.driver_remove("rotation_euler", offset)

            if rotation != 0:
                driver = geometry.driver_add("rotation_euler", offset)
                value = rotation
                driver.driver.expression = f"{value} * (3.14159 / 180) * (frame / {bpy.context.scene.render.fps})"

            if current_frame and self.dmx_cache_dirty:
                geometry.keyframe_insert(data_path="location", frame=current_frame)
                geometry.keyframe_insert(
                    data_path="rotation_euler", frame=current_frame
                )

    def remove_unset_geometries_from_multigeometry_attributes_all(self, dictionary):
        """Remove items with values of all None"""

        remove_empty_items = []
        for geometry, items in dictionary.items():
            if all([i is None for i in items]):
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
            if channel.attribute == attribute:
                return channel

    def update_shutter_dimmer(
        self, dimmer, shutter, strobe, geometry, zoom, current_frame
    ):
        DMX_Log.log.info(
            ("set dimmer, shutter, strobe", dimmer, shutter, strobe, geometry)
        )
        if strobe == 0:  # prevent division by zero
            strobe = None
            shutter = 0

        dimmer = dimmer * round(shutter)  # get a discreet value from channel function
        dmx = bpy.context.scene.dmx
        if geometry is not None:
            geometry = geometry.replace(" ", "_")
        try:
            for emitter_material in self.emitter_materials:
                if geometry is not None:
                    if geometry in emitter_material.name or any(
                        g in geometry
                        for g in emitter_material.get("parent_geometries", [])
                    ):
                        DMX_Log.log.info(("matched emitter", geometry))

                        strength_input = emitter_material.material.node_tree.nodes[
                            1
                        ].inputs[STRENGTH]
                        strength_input.driver_remove("default_value")
                        if strobe is not None:
                            driver = strength_input.driver_add("default_value").driver
                            driver.expression = f"1 if (frame % ({bpy.context.scene.render.fps} / {strobe})) < 1 else 0 * {dimmer}"
                        else:
                            strength_input.default_value = dimmer

                else:
                    strength_input = emitter_material.material.node_tree.nodes[
                        1
                    ].inputs[STRENGTH]
                    strength_input.driver_remove("default_value")
                    if strobe is not None:
                        driver = strength_input.driver_add("default_value").driver
                        driver.expression = f"1 if (frame % ({bpy.context.scene.render.fps} / {strobe})) < 1 else 0 * {dimmer}"
                    else:
                        strength_input.default_value = dimmer

                if current_frame and self.dmx_cache_dirty:
                    emitter_material.material.node_tree.nodes[1].inputs[
                        STRENGTH
                    ].keyframe_insert(data_path="default_value", frame=current_frame)

            for light in self.lights:
                flux = light.object.data["flux"] * dmx.beam_intensity_multiplier
                if zoom is None:
                    value = flux * dimmer
                else:
                    # zoom = math.degrees(light.object.data.spot_size)
                    zoom_compensation = flux / (pow(max(zoom, 2), 0.1))
                    value = dimmer * zoom_compensation * 1.5

                # we should improve this to get more Cycles/Eevee compatibility... add a driver which would adjust the intensity
                # depending on the IES linking or not, adding drivers: https://blender.stackexchange.com/a/314329/176407
                # plus, we would still need to calculate correct energy, so they match between Cycles/Eevee
                # here are some ideas: https://blender.stackexchange.com/a/180533/176407

                if geometry is not None:
                    if geometry in light.object.data.name or any(
                        g in geometry
                        for g in light.object.data.get("parent_geometries", [])
                    ):
                        DMX_Log.log.info("matched emitter")
                        light.object.data.driver_remove("energy")
                        if strobe is not None:
                            driver = light.object.data.driver_add("energy").driver
                            DMX_Log.log.info("matched light")
                            driver.expression = f"(1 if (frame % ({bpy.context.scene.render.fps} / {strobe})) < 1 else 0) * {value}"
                        else:
                            light.object.data.energy = value

                else:
                    light.object.data.driver_remove("energy")
                    if strobe is not None:
                        driver = light.object.data.driver_add("energy").driver
                        DMX_Log.log.info("matched light")
                        driver.expression = f"(1 if (frame % ({bpy.context.scene.render.fps} / {strobe})) < 1 else 0) * {value}"
                    else:
                        light.object.data.energy = value

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
                        list(emitter_material.get("parent_geometries", [])),
                    )
                )
                if geometry is not None:
                    if geometry in emitter_material.name or any(
                        g in geometry
                        for g in emitter_material.get("parent_geometries", [])
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
                        g in geometry
                        for g in light.object.data.get("parent_geometries", [])
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

    def update_zoom(self, zoom, current_frame):
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
                if not hasattr(light.object.data, "spot_size"):
                    continue
                light.object.data.spot_size = spot_size

                if current_frame and self.dmx_cache_dirty:
                    light.object.data.keyframe_insert(
                        data_path="spot_size", frame=current_frame
                    )

        except Exception as e:
            DMX_Log.log.error(f"Error updating zoom {e}")
        return zoom

    def get_colorwheel_color(self, color, attribute):
        if not len(self["slot_colors"]) or color == 0 or color == 1:
            return
        if attribute not in self["slot_colors"]:
            return

        colors = self["slot_colors"][attribute]

        if len(colors) > color:
            return list(colors[color - 1])

    def get_color_temperature(self, ctc, dmx_value):
        if dmx_value == 0:
            return None

        if ctc < 101:
            # for fixtures that do not define physical range
            # get ct form dmx range
            if 1 <= dmx_value <= 255:
                ctc = 1000 + (dmx_value - 1) * (20000 - 1000) / (255 - 1)

        ctc = max(1000, min(20000, ctc))
        ctc -= ctc % -100  # round to full 100s
        return kelvin_table[ctc]

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

    def update_gobo(self, gobo, n, current_frame):
        if "Gobo1" not in self.images:
            self.hide_gobo([1, 2], current_frame=current_frame)
            return

        if gobo is None:
            self.hide_gobo([n], current_frame=current_frame)
            return

        if gobo[0] == 1:
            self.hide_gobo([n], current_frame=current_frame)
            return

        gobos = self.images[f"Gobo{n}"]
        if not gobos.count:
            self.hide_gobo([1, 2], current_frame=current_frame)
            return

        DMX_Log.log.debug(("update gobo", gobo, n))
        self.hide_gobo([n], False, current_frame=current_frame)
        gobo_index = gobo[0] - 2  # 1 is empty, 2 is first, we start from 0...
        self.set_gobo_slot(n, gobo_index, current_frame=current_frame)
        if gobo[1] is not None:
            self.set_gobo_indexing(gobo[1], n, current_frame=current_frame)
        elif gobo[2] is not None:
            self.set_gobo_rotation(gobo[2], n, current_frame=current_frame)

    def set_gobo_indexing(self, value, n, current_frame):
        for obj in self.collection.objects:  # EEVEE
            if "gobo" in obj.get("geometry_type", ""):
                material = self.gobo_materials[obj.name].material
                gobo_rotation = material.node_tree.nodes.get(f"Gobo{n}Rotation")
                gobo_rotation.inputs[3].driver_remove("default_value")
                gobo_rotation.inputs[3].default_value = math.radians(value)
                if current_frame and self.dmx_cache_dirty:
                    gobo_rotation.inputs[3].keyframe_insert(
                        data_path="default_value", frame=current_frame
                    )

        for light in self.lights:  # CYCLES
            light_obj = light.object
            gobo_rotation = light_obj.data.node_tree.nodes.get(f"Gobo{n}Rotation")
            gobo_rotation.inputs[3].driver_remove("default_value")
            gobo_rotation.inputs[3].default_value = math.radians(value)

            if current_frame and self.dmx_cache_dirty:
                gobo_rotation.inputs[3].keyframe_insert(
                    data_path="default_value", frame=current_frame
                )

    def set_gobo_rotation(self, value, n, current_frame):
        for obj in self.collection.objects:  # EEVEE
            if "gobo" in obj.get("geometry_type", ""):
                material = self.gobo_materials[obj.name].material
                gobo_rotation = material.node_tree.nodes.get(f"Gobo{n}Rotation")
                driver = gobo_rotation.inputs[3].driver_add("default_value")
                driver.driver.expression = f"{value} * (3.14159 / 180) * (frame / {bpy.context.scene.render.fps})"

                if current_frame and self.dmx_cache_dirty:
                    gobo_rotation.inputs[3].keyframe_insert(
                        data_path="default_value", frame=current_frame
                    )

        for light in self.lights:  # CYCLES
            light_obj = light.object
            gobo_rotation = light_obj.data.node_tree.nodes.get(f"Gobo{n}Rotation")
            driver = gobo_rotation.inputs[3].driver_add("default_value")
            driver.driver.expression = (
                f"{value} * (3.14159 / 180) * (frame / {bpy.context.scene.render.fps})"
            )

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
        DMX_Log.log.info(("Updating pan tilt", pan, tilt))

        base = self.objects["Root"].object
        pan = pan + base.rotation_euler[2]  # take base z rotation into consideration
        tilt = tilt + base.rotation_euler[0]  # take base x rotation into consideration

        # calculate target position, head will follow
        try:
            head = self.objects["Head"].object
        except Exception:
            self.updatePTDirectly(None, "pan", pan, current_frame)
            self.updatePTDirectly(None, "tilt", tilt, current_frame)
            DMX_Log.log.info(
                "Updating pan/tilt directly via geometries, not via Target due to not located Head"
            )
            return

        head_location = head.matrix_world.translation

        target = self.objects["Target"].object

        eul = mathutils.Euler(
            (base.rotation_euler.x + tilt, 0.0, base.rotation_euler.y + pan), "XYZ"
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
            value = value + geometry.get("applied_rotation", [0, 0, 0])[offset]
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
                if "Tilt" == channel.attribute and channel.geometry == obj.get(
                    "original_name", "None"
                ):
                    return obj
            for channel in self.virtual_channels:
                if "Tilt" == channel.attribute and channel.geometry == obj.get(
                    "original_name", "None"
                ):
                    return obj

    def getProgrammerData(self):
        params = {}

        for dmx_break in self.dmx_breaks:
            data = DMX_Data.get(
                dmx_break.universe, dmx_break.address, dmx_break.channels_count
            )

            for idx, d in enumerate(data, 1):
                for channel in self.channels:
                    if (
                        channel.dmx_break == dmx_break.dmx_break
                        and channel.offsets[0] == idx
                    ):
                        params[channel.attribute] = d
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
                    except Exception:
                        DMX_Log.log.error(
                            "Fixture doesn't exist, remove it via Fixture list → Edit → X"
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
                    except Exception:
                        DMX_Log.log.error(
                            "Fixture doesn't exist, remove it via Fixture list → Edit → X"
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
            except Exception:
                DMX_Log.log.error(
                    "Fixture doesn't exist, remove it via Fixture list → Edit → X"
                )
        if "Target" in self.objects:
            self.objects["Target"].object.select_set(False)
        if "2D Symbol" in self.objects:
            try:
                self.objects["2D Symbol"].object.select_set(False)
            except Exception:
                DMX_Log.log.error(
                    "Fixture doesn't exist, remove it via Fixture list → Edit → X"
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
        for dmx_break in self.dmx_breaks:
            for channel in self.channels:
                if channel.dmx_break == dmx_break.dmx_break:
                    for byte, offset in enumerate(channel.offsets):
                        DMX_Data.set(
                            dmx_break.universe,
                            dmx_break.address + offset - 1,
                            channel.defaults[byte],
                        )
        self.render()

    def set_gobo_slot(self, n, index=-1, current_frame=None):
        gobos = self.images[f"Gobo{n}"]
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
        if hasattr(self, "collection"):
            if hasattr(self.collection, "objects"):
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
                low(channel.attribute)
                for channel in self.channels
                if any(channel.geometry == g.name for g in temp_data.active_subfixtures)
            ]
            in_fixture_virtual = [
                low(channel.attribute)
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
            in_fixture_real = [low(channel.attribute) for channel in self.channels]
            in_fixture_virtual = [
                low(channel.attribute) for channel in self.virtual_channels
            ]

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

    def to_mvr_fixture(self, universe_add=False):
        matrix = 0
        uuid_focus_point = None
        add_to_universe = 1 if universe_add else 0

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
                pymvr.Address(
                    dmx_break=index,
                    universe=dmx_break.universe + add_to_universe,
                    address=dmx_break.address,
                )
                for index, dmx_break in enumerate(self.dmx_breaks)
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
                    DMX_Log.log.error("Matrix or uuid of a Target not defined")
                    return
                return pymvr.FocusPoint(
                    matrix=pymvr.Matrix(matrix),
                    uuid=uuid_,
                    name=f"Target for {self.name}",
                )

    def follow_target_constraint_enable(self, enabled):
        for obj in self.collection.objects:
            for constraint in obj.constraints:
                if constraint.name == "FollowTarget":
                    constraint.enabled = enabled

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
