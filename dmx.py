# Copyright (C) 2020 Hugo Aboud, Sebastian, vanous
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

import json
import logging
import os
import re
import sys
import time
import traceback
import uuid as py_uuid
from datetime import datetime
from pathlib import Path
from threading import Timer
from types import SimpleNamespace

import bpy
import bpy.utils.previews
import pymvr
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    FloatProperty,
    FloatVectorProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)
from bpy.types import Collection, Object, PropertyGroup

from . import fixture
from . import param as param
from . import tracker as tracker
from .acn import DMX_sACN
from .artnet import DMX_ArtNet
from .blender_utils import copy_blender_profiles, get_application_version
from .data import DMX_Data, DMX_Value
from .gdtf_file import DMX_GDTF_File
from .group import DMX_Group
from .i18n import DMX_Lang
from .logging_setup import DMX_Log
from .material import get_gobo_material, set_light_nodes
from .mdns import DMX_Zeroconf
from .mvr import load_mvr
from .mvr_objects import DMX_MVR_Class, DMX_MVR_Object
from .mvrx_protocol import DMX_MVR_X_Client, DMX_MVR_X_Server, DMX_MVR_X_WS_Client
from .mvrxchange.mvr_xchange_blender import (
    DMX_MVR_Xchange,
    DMX_MVR_Xchange_Client,
    DMX_MVR_Xchange_Commit,
)
from .network import DMX_Network
from .node_arranger import DMX_OT_ArrangeSelected
from .osc import DMX_OSC
from .osc_utils import DMX_OSC_Templates
from .panels import classing as classing
from .panels import distribute as distribute
from .panels import fixtures as fixtures
from .panels import groups as groups
from .panels import profiles as Profiles
from .panels import programmer as programmer
from .panels import recorder as recorder
from .panels import setup as setup
from .panels import subfixtures as subfixtures
from .panels.protocols import artnet as panels_artnet
from .panels.protocols import live as panels_live
from .panels.protocols import mvr as panels_mvr
from .panels.protocols import osc as panels_osc
from .panels.protocols import protocols as panels_protocols
from .panels.protocols import psn as panels_psn
from .panels.protocols import sacn as panels_sacn
from .panels.protocols import universes as panels_universes
from .preferences import DMX_Preferences, DMX_Regenrate_UUID
from .universe import DMX_Universe
from .util import (
    ShowMessageBox,
    cmy_to_rgb,
    draw_top_message,
    flatten_color,
    rgb_to_cmy,
)

_ = DMX_Lang._


class DMX(PropertyGroup):
    # Base classes to be registered
    # These should be registered before the DMX class, so it can register properly

    classes_base = (
        param.DMX_Param,
        param.DMX_Model_Param,
        fixture.DMX_Fixture_Object,
        fixture.DMX_Fixture_Image,
        fixture.DMX_Emitter_Material,
        fixture.DMX_IES_Data,
        fixture.DMX_Geometry_Node,
        fixture.DMX_Fixture_Channel_Function,
        fixture.DMX_Fixture_Channel,
        fixture.DMX_Break,
        fixture.DMX_Fixture,
        tracker.DMX_Tracker_Object,
        tracker.DMX_Tracker,
        DMX_MVR_Object,
        DMX_Group,
        DMX_MVR_Class,
        DMX_Universe,
        DMX_Value,
        setup.DMX_PT_Setup,
        panels_mvr.DMX_OP_MVR_Download,
        panels_mvr.DMX_OP_MVR_WS_Download,
        panels_mvr.DMX_OP_MVR_Import,
        panels_mvr.DMX_OP_MVR_WS_Import,
        DMX_MVR_Xchange_Commit,
        DMX_MVR_Xchange_Client,
        DMX_MVR_Xchange,
        DMX_Regenrate_UUID,
        DMX_Preferences,
        subfixtures.DMX_Subfixture,
    )

    # Classes to be registered
    # The registration is done in two steps. The second only runs
    # after the user requests to setup the addon.

    classes_setup = (setup.DMX_OT_Setup_NewShow,)

    classes = (
        panels_protocols.DMX_PT_DMX,
        panels_universes.DMX_UL_Universe,
        panels_universes.DMX_MT_Universe,
        panels_universes.DMX_PT_DMX_Universes,
        panels_live.DMX_PT_DMX_LiveDMX,
        panels_artnet.DMX_PT_DMX_ArtNet,
        panels_sacn.DMX_PT_DMX_sACN,
        setup.DMX_OT_Setup_Volume_Create,
        setup.DMX_PT_Setup_Volume,
        setup.DMX_PT_Setup_Viewport,
        setup.DMX_PT_Setup_Logging,
        setup.DMX_OT_Setup_Open_LogFile,
        setup.DMX_PT_Setup_Import,
        setup.DMX_PT_Setup_Export,
        setup.DMX_PT_Setup_Extras,
        fixtures.DMX_MT_Fixture,
        fixtures.DMX_MT_Fixture_Manufacturers,
        fixtures.DMX_MT_Fixture_Profiles,
        fixtures.DMX_MT_Fixture_Mode,
        fixtures.DMX_OT_Fixture_Item,
        fixtures.DMX_OT_Fixture_Profiles,
        fixtures.DMX_OT_Fixture_Mode,
        panels_live.DMX_UL_LiveDMX_items,
        fixtures.DMX_OT_Fixture_Add,
        fixtures.DMX_OT_Fixture_Edit,
        fixtures.DMX_OT_Fixture_Remove,
        setup.DMX_OT_Export_Custom_Data,
        setup.DMX_OT_Import_Custom_Data,
        setup.DMX_OT_Clear_Custom_Data,
        setup.DMX_OT_Copy_Custom_Data,
        setup.DMX_OT_Setup_RemoveDMX,
        setup.DMX_OT_Reload_Addon,
        setup.DMX_OT_Setup_EnableSelectGeometries,
        fixtures.DMX_OT_IES_Import,
        fixtures.DMX_OT_IES_Remove,
        fixtures.DMX_PT_Fixtures,
        groups.DMX_UL_Group,
        groups.DMX_MT_Group,
        groups.DMX_OT_Group_Create,
        groups.DMX_OT_Group_Update,
        groups.DMX_OT_Group_Rename,
        groups.DMX_OT_Group_Remove,
        groups.DMX_PT_Groups,
        classing.DMX_UL_Class,
        classing.DMX_PT_Classes,
        subfixtures.DMX_PT_Subfixtures,
        subfixtures.DMX_UL_Subfixture,
        subfixtures.DMX_OT_Subfixture_Clear,
        subfixtures.DMX_OT_Subfixture_SelectVisible,
        programmer.DMX_OT_Programmer_DeselectAll,
        programmer.DMX_OT_Programmer_SelectAll,
        programmer.DMX_OT_Programmer_SelectFiltered,
        programmer.DMX_OT_Programmer_SelectInvert,
        programmer.DMX_OT_Programmer_SelectEveryOther,
        programmer.DMX_OT_Programmer_Clear,
        programmer.DMX_OT_Programmer_SelectBodies,
        programmer.DMX_OT_Programmer_SelectTargets,
        programmer.DMX_OT_Programmer_SelectCamera,
        programmer.DMX_OT_Programmer_TargetsToZero,
        programmer.DMX_OT_Programmer_CenterToSelected,
        programmer.DMX_OT_Programmer_Apply_Manually,
        programmer.DMX_OT_Programmer_Set_Ignore_Movement,
        programmer.DMX_OT_Programmer_Reset_Color,
        programmer.DMX_OT_Programmer_ResetTargets,
        programmer.DMX_MT_PIE_Reset,
        programmer.DMX_OT_Programmer_Unset_Ignore_Movement,
        programmer.DMX_OT_Programmer_Set_Lock_Movement_Rotation,
        programmer.DMX_OT_Programmer_Set_Track_Target,
        programmer.DMX_OT_Programmer_Unset_Track_Target,
        programmer.DMX_OT_Programmer_Set_Use_Physical,
        programmer.DMX_OT_Programmer_Unset_Use_Physical,
        distribute.DMX_PT_AlignAndDistributePanel,
        distribute.DMX_OP_AlignLocationOperator,
        distribute.DMX_OP_DistributeWithGapOperator,
        distribute.DMX_OP_DistributeEvenlyOperator,
        distribute.DMX_OP_DistributeCircle,
        panels_osc.DMX_PT_DMX_OSC,
        panels_psn.DMX_UL_Tracker,
        panels_psn.DMX_OP_DMX_Tracker_Add,
        panels_psn.DMX_OP_DMX_Tracker_Remove,
        panels_psn.DMX_PT_DMX_Trackers,
        panels_psn.DMX_OT_Tracker_Followers,
        panels_psn.DMX_OT_Tracker_Followers_Add_Target,
        panels_psn.DMX_OT_Tracker_Followers_Remove_Target,
        panels_psn.DMX_UL_Tracker_Followers,
        panels_psn.DMX_OP_Unlink_Fixture_Tracker,
        panels_psn.DMX_OP_Link_Fixture_Tracker,
        fixtures.DMX_UL_Fixtures,
        panels_mvr.DMX_PT_DMX_MVR_X,
        panels_mvr.DMX_UL_MVR_Commit,
        panels_mvr.DMX_UL_MVR_WS_Commit,
        panels_mvr.DMX_OP_MVR_Refresh,
        panels_mvr.DMX_OP_MVR_Request,
        panels_mvr.DMX_OP_MVR_WS_Refresh,
        panels_mvr.DMX_OP_MVR_X_Export,
        panels_mvr.DMX_UL_MVR_Shared_Commit,
        panels_mvr.DMX_UL_MVR_Stations,
        panels_mvr.DMX_OP_MVR_RemoveSharedCommit,
        fixtures.DMX_OT_Fixture_ForceRemove,
        fixtures.DMX_OT_Fixture_SelectNext,
        fixtures.DMX_OT_Fixture_SelectPrevious,
        fixtures.DMX_OT_Fixture_SelectNextTarget,
        fixtures.DMX_OT_Fixture_SelectPreviousTarget,
        programmer.DMX_PT_Programmer,
        recorder.DMX_OT_Recorder_AddKeyframe,
        recorder.DMX_PT_Recorder,
        recorder.DMX_OT_Recorder_Enable_Drivers,
        recorder.DMX_OT_Recorder_Disable_Drivers,
        recorder.DMX_PT_DMX_Recorder_Drivers,
        recorder.DMX_PT_DMX_Recorder_Delete,
        recorder.DMX_OT_Recorder_Delete_Keyframes_Selected,
        recorder.DMX_OT_Recorder_Delete_Keyframes_All,
        setup.DMX_OT_Fixture_Set_Cycles_Beams_Size_Small,
        setup.DMX_OT_Fixture_Set_Cycles_Beams_Size_Normal,
        setup.DMX_OT_Fixture_Set_Eevee_Cutoff_Distance,
    )

    linkedToFile = False
    _keymaps = []
    fixtures_filter = []
    custom_icons = None

    def register():
        # custom icons
        DMX.custom_icons = bpy.utils.previews.new()

        ADDON_PATH = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(ADDON_PATH, "assets", "icons")
        DMX.custom_icons.load(
            "DEFAULT_TEST", os.path.join(path, "erlenmeyer.png"), "IMAGE"
        )
        DMX.custom_icons.load(
            "PRODUCTION_ASSIST", os.path.join(path, "pa.png"), "IMAGE"
        )
        DMX.custom_icons.load("GMA3", os.path.join(path, "ma.png"), "IMAGE")
        DMX.custom_icons.load(
            "GDTF_FILE", os.path.join(path, "gdtf_file_icon_small.png"), "IMAGE"
        )
        DMX.custom_icons.load(
            "BLENDER_DMX", os.path.join(path, "blender_dmx.png"), "IMAGE"
        )
        DMX.custom_icons.load(
            "MVR_FILE", os.path.join(path, "mvr_file_icon_small.png"), "IMAGE"
        )

        for cls in DMX.classes_setup:
            bpy.utils.register_class(cls)

        # register key shortcuts
        wm = bpy.context.window_manager
        km = wm.keyconfigs.addon.keymaps.new(
            name="3D View Generic", space_type="VIEW_3D"
        )
        kmi = km.keymap_items.new(
            "dmx.fixture_next", "RIGHT_ARROW", "PRESS", ctrl=True, shift=False
        )
        DMX._keymaps.append((km, kmi))
        kmi = km.keymap_items.new(
            "dmx.fixture_previous", "LEFT_ARROW", "PRESS", ctrl=True, shift=False
        )
        DMX._keymaps.append((km, kmi))
        kmi = km.keymap_items.new(
            "dmx.fixture_next_target", "RIGHT_ARROW", "PRESS", ctrl=True, shift=True
        )
        DMX._keymaps.append((km, kmi))
        kmi = km.keymap_items.new(
            "dmx.fixture_previous_target", "LEFT_ARROW", "PRESS", ctrl=True, shift=True
        )
        DMX._keymaps.append((km, kmi))
        kmi = km.keymap_items.new("dmx.reload_addon", "R", "PRESS", ctrl=True, alt=True)
        DMX._keymaps.append((km, kmi))

    def unregister():
        # unregister keymaps
        for km, kmi in DMX._keymaps:
            km.keymap_items.remove(kmi)
        DMX._keymaps.clear()
        bpy.utils.previews.remove(DMX.custom_icons)

        if DMX.linkedToFile:
            for cls in DMX.classes:
                bpy.utils.unregister_class(cls)
            DMX.linkedToFile = False
        else:
            for cls in DMX.classes_setup:
                bpy.utils.unregister_class(cls)

    # Blender RNA Properties
    # fmt: off
    # fixture listing columns
    column_fixture_id: BoolProperty(
        name = _("Fixture ID"),
        default = True)

    column_unit_number: BoolProperty(
        name = _("Unit Number"),
        default = False)

    column_custom_id: BoolProperty(
        name = _("Custom ID"),
        default = False)

    column_fixture_id_numeric: BoolProperty(
        name = "Fixture ID Numeric",
        default = False)

    column_dmx_address: BoolProperty(
        name = _("DMX Address"),
        default = True)

    column_fixture_position: BoolProperty(
        name = _("Position"),
        default = False)

    column_fixture_rotation: BoolProperty(
        name = _("Rotation"),
        default = False)

    column_fixture_footprint: BoolProperty(
        name = _("Footprint"),
        default = False)

    column_fixture_physical_properties: BoolProperty(
        name = _("Physical Properties"),
        default = False)

    collection: PointerProperty(
        name = _("DMX Collection"),
        type = Collection)

    volume: PointerProperty(
        name = "Volume Scatter Box",
        type = Object)

    # DMX Properties
    # These should be parsed to file

    fixtures: CollectionProperty(
        name = "DMX Fixtures",
        type = fixture.DMX_Fixture)

    trackers: CollectionProperty(
        name = "PSN Servers",
        type = tracker.DMX_Tracker)

    trackers_i : IntProperty(
        name = _("Selected PSN Server"),
        description=_("The selected element on the PSN server list"),
        default = 0
        )

    groups: CollectionProperty(
        name = "DMX Groups",
        type = DMX_Group)

    classing: CollectionProperty(
        name = "DMX MVR Classes",
        type = DMX_MVR_Class)

    class_list_i : IntProperty(
        name = _("Class List i"),
        description=_("The selected element on the class list"),
        default = 0,
        )
    universes: CollectionProperty(
        name = "DMX Groups",
        type = DMX_Universe)

    mvr_objects: CollectionProperty(
        name = "MVR Objects",
        type = DMX_MVR_Object)

    def prepare_empty_buffer(self, context):
        # Clear the buffer on change of every protocol
        DMX_Data.prepare_empty_buffer()


    def get_dmx_universes(self, context):
        data = []
        for universe in self.universes:
            data.append((str(universe.id), universe.name, str(universe.input), "", universe.id))
        return data

    def get_selected_live_dmx_universe(self):
        selected_universe = None
        for universe in self.universes:
            selected_universe = universe
            if self.selected_live_dmx == str(universe.id):
                break
        return selected_universe

    def reset_live_dmx_data(self, context):
        DMX_Data._live_view_data = [0] * 512

    selected_live_dmx: EnumProperty(
        name = _("Universe"),
        description="",
        update = reset_live_dmx_data,
        items = get_dmx_universes
    )

    dmx_values: CollectionProperty( # this only creates an array which is used for live view panel.
        name = "DMX buffer",        # but the values themselves come from DMX_Data class because
        type = DMX_Value            # updating this RNA many times per second crashed blender
    )

    dmx_value_index: IntProperty() # Unused, but the live DMX UI Panel requires it

    data_version: IntProperty(
            name = "BlenderDMX data version, bump when changing RNA structure and provide migration script",
            default = 12,
            )

    def get_fixture_by_index(self, index):
        for idx, fixture_ in enumerate(self.fixtures):
            if idx == index:
                return fixture_

    def on_ui_selection_change(self, context):
        """ If fixture selection is changed via UILists 'normal' interaction, rather then an operator.
        Not currently used, as this starts to create circular updates and we would need to pass info
        if fixture was actually being selected or unselected.
        """
        return
        for idx, fixture_ in enumerate(self.fixtures):
            if idx == self.selected_fixture_index:
                if not fixture_.is_selected():
                    #fixture.toggleSelect()
                    fixture_.select()
                    return

    selected_fixture_index: IntProperty(
            default = 0,
            update = on_ui_selection_change
            ) # Just a fake value, we need as the Fixture list requires it

    fixture_properties_editable: BoolProperty(
        name = _("Editable"),
        default = False)

    default_channel_functions: CollectionProperty(
        name = "Fixture > Channels > Channel Functions",
        type = fixture.DMX_Fixture_Channel_Function
    )

    def get_default_channel_function_by_attribute(self, attribute):
        for ch_function in self.default_channel_functions:
            if attribute == ch_function.attribute:
                return ch_function


    # fmt: on

    # New DMX Scene
    # - Remove any previous DMX objects/collections
    # - Create DMX collection
    # - Create DMX universes
    # - Link to file
    def new(self):
        # Remove old DMX collection from file if present
        if "DMX" in bpy.data.collections:
            bpy.data.collections.remove(bpy.data.collections["DMX"])

        # Remove old Volume object from file if present
        if "DMX_Volume" in bpy.data.objects:
            bpy.data.objects.remove(bpy.data.objects["DMX_Volume"])

        # Create a new DMX collection on the file
        bpy.ops.collection.create(name="DMX")
        collection = bpy.data.collections["DMX"]
        # Unlink any objects or collections
        for c in collection.objects:
            collection.objects.unlink(c)
        for c in collection.children:
            collection.children.unlink(c)
        # Link collection to scene
        bpy.context.scene.collection.children.link(collection)

        # Set background to black (so it match the panel)
        scene = bpy.context.scene

        if scene.world is None:
            # create a new world
            new_world = bpy.data.worlds.new("New World")
            new_world.use_nodes = True
            scene.world = new_world
        world = scene.world
        world.use_nodes = True

        SHADER_NODE_BG = bpy.app.translations.pgettext("ShaderNodeBackground")
        SHADER_NODE_WO = bpy.app.translations.pgettext("ShaderNodeOutputWorld")

        new_link = False
        if "Background" not in world.node_tree.nodes:
            bg = world.node_tree.nodes.new(SHADER_NODE_BG)
            bg.name = "Background"
            new_link = True
        else:
            bg = world.node_tree.nodes["Background"]

        if "World Output" not in world.node_tree.nodes:
            wo = world.node_tree.nodes.new(SHADER_NODE_WO)
            wo.name = "World Output"
            new_link = True
        else:
            wo = world.node_tree.nodes["World Output"]
        if new_link:
            world.node_tree.links.new(bg.outputs[0], wo.inputs[0])

        scene.world.node_tree.nodes["Background"].inputs[0].default_value = (0, 0, 0, 1)

        # Create a DMX universe
        self.addUniverse()
        self.generate_project_uuid()
        self.generate_default_channel_functions()

        # Link addon to file
        self.linkFile()

    # Link Add-on to file
    # This is only called on two situations: "Create New Show" or "onLoadFile"
    # - Link DMX Collection (if present)
    # - Link Volume Object (if present)
    # - If DMX collection was linked, register addon
    # - Allocate static universe data
    def linkFile(self):
        print("INFO", "Linking to file")

        DMX_Log.enable(self.logging_level)
        DMX_Log.log.info("BlenderDMX: Linking to file")

        # Link pointer properties to file objects
        if "DMX" in bpy.data.collections:
            self.collection = bpy.data.collections["DMX"]
        else:
            self.collection = None

        if "DMX_Volume" in bpy.data.objects:
            self.volume = bpy.data.objects["DMX_Volume"]
        else:
            self.volume = None

        DMX_Log.log.info(f"DMX collection: {self.collection}")
        DMX_Log.log.info(f"DMX_Volume object: {self.volume}")

        if self.collection:
            # Second step registration (if not already registered)
            if not DMX.linkedToFile:
                for cls in self.classes:
                    bpy.utils.register_class(cls)
                DMX.linkedToFile = True

        # Sync number of universes
        self.universes_n = len(self.universes)

        # Allocate universes data
        DMX_Data.setup(self.universes_n)

        # make sure that selection of ip address points to an item in enum
        dmx = bpy.context.scene.dmx
        if not len(dmx.artnet_ipaddr):
            if len(DMX_Network.cards(None, None)):
                dmx.artnet_ipaddr = DMX_Network.cards(None, None)[0][0]
            else:
                DMX_Log.log.warning("No network card detected")
                return

        # Reset network status
        dmx = bpy.context.scene.dmx
        if dmx.artnet_enabled and dmx.artnet_status != "online":
            dmx.artnet_enabled = False
            dmx.artnet_status = "offline"
        if dmx.sacn_enabled and dmx.sacn_status != "online":
            dmx.sacn_enabled = False
            dmx.sacn_status = "offline"
        if dmx.osc_enabled:
            dmx.osc_enabled = False
        if dmx.mvrx_enabled:
            dmx.mvrx_enabled = False
        if dmx.mvrx_socket_client_enabled:
            dmx.mvrx_socket_client_enabled = False

        for tracker_item in dmx.trackers:
            tracker_item.enabled = False
            if not len(tracker_item.ip_address):
                if len(DMX_Network.cards(None, None)):
                    tracker_item.ip_address = DMX_Network.cards(None, None)[0][0]
                else:
                    DMX_Log.log.warning("No network card detected")

        # Rebuild group runtime dictionary (evaluating if this is gonna stay here)
        # DMX_Group.runtime = {}
        # for group in self.groups:
        #    group.rebuild()

        self.logging_level = "DEBUG"  # setting high logging level to see initialization
        try:
            self.migrations()
        except Exception as e:
            traceback.print_exception(e)
        self.ensure_application_uuid()
        # enable in extension
        self.ensure_directories_exist()
        Timer(1, self.copy_default_profiles_to_user_folder, ()).start()
        self.check_python_version()
        self.check_blender_version()
        self.print_extension_version()

        Profiles.DMX_Fixtures_Local_Profile.loadLocal()
        DMX_GDTF_File.get_manufacturers_list()
        Profiles.DMX_Fixtures_Import_Gdtf_Profile.loadShare()
        self.logging_level = "ERROR"  # setting default logging level

    # Unlink Add-on from file
    # This is only called when the DMX collection is externally removed
    def unlinkFile(self):
        print("INFO", "Unlinking from file")

        # Unlink pointer properties
        self.collection = None
        self.volume = None

        # Second step unregistration
        if DMX.linkedToFile:
            for cls in self.classes:
                bpy.utils.unregister_class(cls)
            DMX.linkedToFile = False

    # Callback Properties

    # # Setup > Background > Color

    def check_python_version(self):
        if not sys.version_info >= (3, 8):
            DMX_Log.log.error(
                f"Python version of at least 3.8 is needed, you are using {sys.version} ❌"
            )
            return
        DMX_Log.log.info(f"Python version: {sys.version} ✅")

    def check_blender_version(self):
        if not bpy.app.version >= (3, 4):
            DMX_Log.log.error(
                f"Blender version of at least 3.4 is needed, you are using {bpy.app.version} ❌"
            )
            return
        DMX_Log.log.info(f"Blender version: {bpy.app.version} ✅")

    def print_extension_version(self):
        current_version = get_application_version()
        DMX_Log.log.info(f"BlenderDMX version: {current_version}")

    def ensure_directories_exist(self):
        list_paths = []
        list_paths.append(os.path.join("assets", "profiles"))
        list_paths.append(os.path.join("assets", "models"))
        list_paths.append(os.path.join("assets", "models", "mvr"))
        list_paths.append(os.path.join("assets", "mvrs"))
        for path in list_paths:
            bpy.utils.extension_path_user(__package__, path=path, create=True)

    def copy_default_profiles_to_user_folder(self):
        copy_blender_profiles()
        Profiles.DMX_Fixtures_Local_Profile.loadLocal()
        DMX_GDTF_File.get_manufacturers_list()

    def ensure_application_uuid(self):
        prefs = bpy.context.preferences.addons[__package__].preferences
        application_uuid = prefs.get("application_uuid", 0)
        if application_uuid == 0:
            prefs["application_uuid"] = str(py_uuid.uuid4())  # must never be 0

    def migrations(self):
        """Provide migration scripts when bumping the data_version"""
        file_data_version = 1  # default data version before we started setting it up
        hide_gobo_message = False

        if "DMX_DataVersion" in self.collection:
            file_data_version = self.collection["DMX_DataVersion"]

        DMX_Log.log.info(f"Data version: {file_data_version}")

        if file_data_version < 2:  # migration for sw. version 0.5 → 1.0
            DMX_Log.log.info("Running migration 1→2")
            dmx = bpy.context.scene.dmx

            for fixture_ in dmx.fixtures:
                for obj in fixture_.objects:
                    if any(obj.name == name for name in ["Body", "Base"]):
                        DMX_Log.log.info(f"updating {obj.name}")
                        obj.name = "Root"

                for light in fixture_.lights:
                    DMX_Log.log.info(
                        "Adding shutter and dimmer value fields to light object"
                    )
                    if "shutter_value" not in light.object.data:
                        light.object.data["shutter_value"] = 0
                    if "shutter_dimmer_value" not in light.object.data:
                        light.object.data["shutter_dimmer_value"] = 0
                    if "shutter_counter" not in light.object.data:
                        light.object.data["shutter_counter"] = 0

        if file_data_version < 3:
            hide_gobo_message = True
            DMX_Log.log.info("Running migration 2→3")
            dmx = bpy.context.scene.dmx
            DMX_Log.log.info("Add UUID to fixtures")
            for fixture_ in dmx.fixtures:
                if "uuid" not in fixture_:
                    DMX_Log.log.info(f"Adding UUID to {fixture_.name}")
                    fixture_.uuid = str(py_uuid.uuid4())
            DMX_Log.log.info("Add UUID to groups, convert groups to json")
            for group in dmx.groups:
                if "uuid" not in group:
                    DMX_Log.log.info("Adding UUID to {group.name}")
                    group.uuid = str(py_uuid.uuid4())
                DMX_Log.log.info("Migrating group")
                group.dump = json.dumps(
                    [x[1:-1] for x in group.dump.strip("[]").split(", ")]
                )

        if file_data_version < 4:
            DMX_Log.log.info("Running migration 3→4")
            dmx = bpy.context.scene.dmx

            def findFixtureUuidDuplicates(uuid):
                found = []
                for fixture_ in self.fixtures:
                    if fixture_ is None:
                        continue
                    if fixture_.uuid == uuid:
                        found.append(fixture_)
                return found

            def findGroupUuidDuplicates(uuid):
                found = []
                for group in self.groups:
                    if group is None:
                        continue
                    if group.uuid == uuid:
                        found.append(group)
                return found

            DMX_Log.log.info("Ensure unique fixture UUID")
            duplicates = []
            for fixture_ in dmx.fixtures:
                duplicates = findFixtureUuidDuplicates(fixture_.uuid)
                if len(duplicates) > 1:
                    for fixture_ in duplicates:
                        u = fixture_.uuid
                        fixture_.uuid = str(py_uuid.uuid4())
                        DMX_Log.log.info(
                            ("Updating fixture", fixture_.name, u, fixture_.uuid)
                        )

            DMX_Log.log.info("Ensure unique group UUID")
            duplicates = []
            for group in dmx.groups:
                duplicates = findGroupUuidDuplicates(group.uuid)
                if len(duplicates) > 1:
                    for group in duplicates:
                        u = group.uuid
                        group.uuid = str(py_uuid.uuid4())
                        DMX_Log.log.info(("Updating group", group.name, u, group.uuid))

            DMX_Log.log.info("Convert groups from fixture names to UUIDs")
            for group in dmx.groups:
                grouped_fixtures = json.loads(group.dump)
                uuid_list = []
                for g_fixture in grouped_fixtures:
                    if g_fixture in dmx.fixtures:
                        fixture_ = dmx.fixtures[g_fixture]
                        if fixture_ is not None:
                            uuid_list.append(fixture_.uuid)
                group.dump = json.dumps(uuid_list)
            DMX_Log.log.info("Groups updated")

        if file_data_version < 5:
            DMX_Log.log.info("Running migration 4→5")
            dmx = bpy.context.scene.dmx
            for fixture_ in dmx.fixtures:
                if "dmx_values" not in fixture_:
                    DMX_Log.log.info("Adding dmx_value array to fixture")
                    fixture_["dmx_values"] = []

        if file_data_version < 6:
            DMX_Log.log.info("Running migration 5→6")
            DMX_Log.log.info(
                "To make gobos working again, edit fixtures with gobos - re-load GDTF files (Fixtures → Edit, uncheck Re-address only)"
            )

        if file_data_version < 7:
            DMX_Log.log.info("Running migration 6→7")
            dmx = bpy.context.scene.dmx
            for fixture_ in dmx.fixtures:
                for light in fixture_.lights:
                    DMX_Log.log.info("Adding nodes to light")
                    set_light_nodes(light)

            if "DMX_Volume" in bpy.data.objects:
                objs = bpy.data.objects
                objs.remove(objs["DMX_Volume"], do_unlink=True)
                DMX_Log.log.info(
                    "Removing Volume box due to old structure, you need to create it new"
                )

            if "DMX_Volume" in bpy.data.materials:
                objs = bpy.data.materials
                objs.remove(objs["DMX_Volume"], do_unlink=True)
                DMX_Log.log.info(
                    "Removing Volume box material due to old structure, you need to create it new"
                )

        if file_data_version < 8:
            DMX_Log.log.info("Running migration 7→8")
            dmx = bpy.context.scene.dmx
            for fixture_ in dmx.fixtures:
                if "slot_colors" not in fixture_:
                    DMX_Log.log.info("Adding slot_colors array to fixture")
                    fixture_["slot_colors"] = []

        if file_data_version < 9:
            DMX_Log.log.info("Running migration 8→9")
            dmx = bpy.context.scene.dmx
            for fixture_ in dmx.fixtures:
                fixture_.gel_color_rgb = list(
                    int((255 / 1) * i) for i in fixture_.gel_color[:3]
                )
                DMX_Log.log.info("Converting gel color to rgb")

        if file_data_version < 10:
            DMX_Log.log.info("Running migration 9→10")
            dmx = bpy.context.scene.dmx

            for fixture_ in dmx.fixtures:
                for obj in fixture_.objects:
                    if "Target" in obj.name:
                        if "uuid" not in obj.object:
                            DMX_Log.log.info(f"Add uuid to {obj.name}")
                            obj.object["uuid"] = str(py_uuid.uuid4())

        if file_data_version < 11:
            DMX_Log.log.info("Running migration 10→11")
            dmx = bpy.context.scene.dmx
            d = DMX_OT_ArrangeSelected()

            for fixture_ in dmx.fixtures:
                fixture_.gobo_materials.clear()
                for obj in fixture_.collection.objects:
                    if "gobo" in obj.get("geometry_type", ""):
                        material = fixture_.gobo_materials.add()
                        material.name = obj.name
                        gobo_material = get_gobo_material(obj.name)
                        obj.active_material = gobo_material
                        if hasattr(obj.active_material, "shadow_method"):
                            obj.active_material.shadow_method = "CLIP"
                        obj.active_material.blend_method = "BLEND"
                        obj.material_slots[
                            0
                        ].link = (
                            "OBJECT"  # ensure that each fixture has it's own material
                        )
                        obj.material_slots[0].material = gobo_material
                        material.material = gobo_material
                        DMX_Log.log.info(f"Recreate gobo material {fixture_.name}")
                for light in fixture_.lights:
                    set_light_nodes(light)

                if len(fixture_.images) > 0:
                    old_gobos = fixture_.images["gobos"]
                    if old_gobos is not None:
                        gobo1 = fixture_.images.add()
                        gobo1.name = "gobos1"
                        gobo1.image = old_gobos.image
                        gobo1.count = old_gobos.count

                        gobo2 = fixture_.images.add()
                        gobo2.name = "gobos2"
                        gobo2.image = old_gobos.image
                        gobo2.count = old_gobos.count

                fixture_.hide_gobo()
                for item in fixture_.gobo_materials:
                    ntree = item.material.node_tree
                    d.process_tree(ntree)
                for item in fixture_.geometry_nodes:
                    ntree = item.node
                    d.process_tree(ntree)

                for light in fixture_.lights:  # CYCLES
                    light_obj = light.object
                    ntree = light_obj.data.node_tree
                    d.process_tree(ntree)
            if not hide_gobo_message:
                temp_data = bpy.context.window_manager.dmx
                message = "This show file has been made in older version of BlenderDMX. Most likely you need to re-edit fixtures: Fixtures → Edit, uncheck Re-address only, this will re-build the fixtures from their GDTF files. Sorry for the inconvenience."
                temp_data.migration_message = message
                ShowMessageBox(message=message, title="Updating info!", icon="ERROR")
                bpy.types.VIEW3D_HT_tool_header.prepend(draw_top_message)

        if file_data_version < 12:
            DMX_Log.log.info("Running migration 11→12")
            dmx = bpy.context.scene.dmx

            for fixture_ in dmx.fixtures:
                DMX_Log.log.info(f"Migrate address/universe of {fixture_.name}")
                new_break = fixture_.dmx_breaks.add()
                new_break.dmx_break = 1
                new_break.address = fixture_["address"]
                new_break.universe = fixture_["universe"]
                new_break.channels_count = len(fixture_["channels"])
                del fixture_["address"]
                del fixture_["universe"]

        # add here another if statement for next migration condition... like:
        # if file_data_version < 6:
        # ...

        DMX_Log.log.info("Migration done.")

        self.collection["DMX_DataVersion"] = (
            self.data_version
        )  # set data version to current

    def onBackgroundColor(self, context):
        context.scene.world.node_tree.nodes["Background"].inputs[
            0
        ].default_value = self.background_color

    background_color: FloatVectorProperty(
        name="Background Color",
        subtype="COLOR",
        size=4,
        min=0.0,
        max=1.0,
        default=(0.0, 0.0, 0.0, 1.0),
        update=onBackgroundColor,
    )

    # # Setup > Models > Display Pigtails, Select geometries

    def onDisplayLabel(self, context):
        for fixture_ in self.fixtures:
            for obj in fixture_.collection.objects:
                if obj.get("geometry_root", False):
                    if self.display_device_label == "NONE":
                        obj.show_name = False
                    elif self.display_device_label == "NAME":
                        obj.name = f"{fixture_.name}"
                        obj.show_name = self.enable_device_label
                    elif self.display_device_label == "DMX":
                        obj.name = f"{fixture_.universe}.{fixture_.address}"
                        obj.show_name = self.enable_device_label
                    elif self.display_device_label == "FIXTURE_ID":
                        if fixture_.fixture_id:
                            obj.name = f"{fixture_.fixture_id}"
                            obj.show_name = self.enable_device_label
                        else:
                            obj.show_name = False
                    break

    def onDisplayPigtails(self, context):
        for fixture_ in self.fixtures:
            for obj in fixture_.collection.objects:
                if "pigtail" in obj.get("geometry_type", ""):
                    obj.hide_set(not self.display_pigtails)
                    obj.hide_viewport = not self.display_pigtails
                    obj.hide_render = not self.display_pigtails

    def onDisplay2D(self, context):
        bpy.context.window_manager.dmx.pause_render = (
            True  # this stops the render loop, to prevent slowness and crashes
        )
        if self.display_2D:
            self.volume_enabled = False
            area = [
                area
                for area in bpy.context.window.screen.areas
                if area.type == "VIEW_3D"
            ][0]
            with bpy.context.temp_override(
                window=bpy.context.window,
                area=area,
                region=[region for region in area.regions if region.type == "WINDOW"][
                    0
                ],
                screen=bpy.context.window.screen,
            ):
                bpy.ops.view3d.view_axis(type="TOP", align_active=True)
                bpy.ops.view3d.view_selected()
                area.spaces[0].shading.type = "MATERIAL"

        for fixture_ in self.fixtures:
            for obj in fixture_.collection.objects:
                if obj.get("2d_symbol", None) == "all":
                    obj.hide_set(not self.display_2D)
                    obj.hide_viewport = not self.display_2D
                    obj.hide_render = not self.display_2D
                    if self.display_device_label == "NONE":
                        obj.show_name = False
                    elif self.display_device_label == "NAME":
                        obj.name = f"{fixture_.name}"
                        obj.show_name = True
                    elif self.display_device_label == "DMX":
                        obj.name = f"{fixture_.universe}.{fixture_.address}"
                        obj.show_name = True
                    elif self.display_device_label == "FIXTURE_ID":
                        if fixture_.fixture_id:
                            obj.name = f"{fixture_.fixture_id}"
                            obj.show_name = True
                        else:
                            obj.show_name = False
                else:
                    obj.hide_set(self.display_2D)
                    obj.hide_viewport = self.display_2D
                    obj.hide_render = self.display_2D
                    if "pigtail" in obj.get("geometry_type", ""):
                        obj.hide_set(not self.display_pigtails)
                        obj.hide_viewport = not self.display_pigtails
                        obj.hide_render = not self.display_pigtails
        bpy.context.window_manager.dmx.pause_render = (
            self.display_2D
        )  # re-enable renderer if in 3D

    # fmt: off
    def update_device_label(self, context):
        self.onDisplay2D(context)
        self.onDisplayLabel(context)

    display_pigtails: BoolProperty(
        name = _("Display Pigtails"),
        default = False,
        update = onDisplayPigtails)

    display_2D: BoolProperty(
        name = _("Display 2D View"),
        default = False,
        update = onDisplay2D)

    enable_device_label: BoolProperty(
        name = _("Display Device Label"),
        default = False,
        update = onDisplayLabel)

    display_device_label: EnumProperty(
        name = _("Device Label"),
        default = "NAME",
        items= [
                ("NONE", _("None"), "Do not display any label"),
                ("NAME", _("Name"), "Name"),
                ("DMX", _("DMX"), "DMX Address"),
                ("FIXTURE_ID", _("Fixture ID"), "Fixture ID"),
        ],
        update = update_device_label)

    def onSelectGeometries(self, context):
        # confirmation dialog
        bpy.ops.dmx.enabling_geometry_selection('INVOKE_DEFAULT')
        # the actual logic is now in the confirmation dialog's execute() function

    select_geometries: BoolProperty(
        name = _("Allow Selecting Geometries"),
        default = False,
        update = onSelectGeometries)


    # # Logging levels

    def onLoggingLevel(self, context):
        DMX_Log.set_level(self.logging_level)

    logging_level: EnumProperty(
        name= _("Logging Level"),
        description= "logging level",
        default = "DEBUG",
        items= [
                ('CRITICAL', _("Critical"), "", "TOOL_SETTINGS", 0),
                ('ERROR', _("Error"), "", 'ERROR', 1),
                ('WARNING', _("Warning"), "", "CANCEL", 2),
                ('INFO', _("Info"), "", "INFO", 3),
                ('DEBUG', _("Debug"), "", "OUTLINER_OB_LIGHT",4),
        ],
        update = onLoggingLevel
        )

    # # Setup > Volume > Preview Volume

    def onVolumePreview(self, context):
        self.updatePreviewVolume()

    #volume_preview: BoolProperty(
    #    name = "Preview Volume",
    #    default = False,
    #    update = onVolumePreview)


    volume_preview: EnumProperty(
        name= _("Simple beam"),
        description= _("Display 'fake' beam cone"),
        default = "NONE",
        items= [
                ("NONE", _("None"), "Cone not displayed"),
                ("SELECTED", _("Selected fixtures"), "Shift select multiple"),
                ("ALL", _("All fixtures"), "All fixtures"),
        ],
        update = onVolumePreview
        )

    def onReducedBeam(self, context):
        for fixture_ in self.fixtures:
            fixture_.render(skip_cache=True)

    reduced_beam_diameter_in_cycles: EnumProperty(
        name= _("Beam Lens Diameter in Cycles"),
        description= _("Beam diameter is reduced to minimum when projecting gobos to prevent blur on gobo edge"),
        default = "REDUCED",
        items= [
                ("REDUCED", _("Reduced"), "Reduced beam diameter, sharp gobos"),
                ("FULL", _("Full width"), "Wide beam diameter, blurry gobos"),
                ("CUSTOM", _("Custom per each beam"), "Based on `beam_radius_pin_sized_for_gobos` attribute on each spot light object"),
        ],
        update = onReducedBeam
        )
    # # Setup > Volume > Disable Overlays

    def onDisableOverlays(self, context):
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.overlay.show_extras = not self.disable_overlays
                        space.overlay.show_relationship_lines = not self.disable_overlays
                        break


    disable_overlays: BoolProperty(
        name = _("Disable Beam Outlines"),
        default = False,
        update = onDisableOverlays)

    # # Setup > Volume > Enabled

    def onVolumeEnabled(self, context):
        if self.volume is not None:
            self.volume.hide_set(not self.volume_enabled)

    volume_enabled: BoolProperty(
        name = _("Enable Volume Scatter"),
        default = True,
        update = onVolumeEnabled)

    # #  Setup > Volume > Density

    def onVolumeNoiseScale(self, context):
        volume_nodetree = self.volume.data.materials[0].node_tree
        volume_nodetree.nodes["Noise Texture"].inputs['Scale'].default_value = self.volume_noise_scale

    volume_noise_scale: FloatProperty(
        name = _("Noise Scale"),
        description=_("Volume Noise Scale"),
        default = 1,
        min = 0,
        max = 100,
        update = onVolumeNoiseScale)

    def onVolumeDensity(self, context):
        volume_nodetree = self.volume.data.materials[0].node_tree
        volume_nodetree.nodes["Volume Scatter"].inputs['Density'].default_value = self.volume_density

    volume_density: FloatProperty(
        name = _("Density"),
        description=_("Volume Scatter Density"),
        default = 0.1,
        min = 0,
        max = 1,
        update = onVolumeDensity)


    def onMultiplyIntensity(self, context):
        for fixture_ in self.fixtures:
            fixture_.render(skip_cache=True)

    beam_intensity_multiplier: FloatProperty(
        name = _("Multiply beams intensity"),
        default = 1,
        min=0.001,
        update = onMultiplyIntensity
        )

    # # DMX > Universes > Number of Universes

    def onUniverseN(self, context):
        n = self.universes_n
        old_n = len(self.universes)
        # Shrinking
        if (n < old_n):
            for _ in range(n, old_n):
                self.removeUniverse(n)
        # Growing
        elif (n > old_n):
            for _ in range(old_n, n):
                self.addUniverse()
        # Set data
        DMX_Data.setup(n)


    universes_n : IntProperty(
        name = _("Number of universes"),
        description=_("The number of universes set on the panel"),
        default = 0,
        min = 0,
        soft_min = 1,
        max = 511,
        update = onUniverseN)

    # # DMX > Universes > List Index

    universe_list_i : IntProperty(
        name = _("Universe List Item"),
        description=_("The selected element on the universe list"),
        default = 0
        )

    # # DMX > ArtNet > Network Cards
    artnet_ipaddr : EnumProperty(
        name = _("IPv4 Address for ArtNet signal"),
        description=_("The network card/interface to listen for ArtNet DMX data"),
        items = DMX_Network.cards
    )

    # fmt: on

    # zeroconf - mvr-xchange

    def onZeroconfEnableDiscovery(self, context):
        clients = bpy.context.window_manager.dmx.mvr_xchange.mvr_xchange_clients
        clients.clear()
        shared_commits = bpy.context.window_manager.dmx.mvr_xchange.shared_commits
        shared_commits.clear()
        if self.zeroconf_enabled:
            DMX_Log.log.info("Enable mdns discovery")
            DMX_Zeroconf.enable_discovery()

            DMX_MVR_X_Server.enable()  # start the MVR-xchange TCP server for incoming connections
            DMX_MVR_X_Server._instance.server.get_port()

            mvr_x_group = (
                bpy.context.window_manager.dmx.mvr_xchange.mvr_x_group or "WorkGroup"
            )
            DMX_Zeroconf.enable_server(
                mvr_x_group, DMX_MVR_X_Server.get_port()
            )  # start mdns server and advertise the TCP MVR server

        else:
            self.mvrx_enabled = False
            DMX_MVR_X_Server.disable()
            DMX_Log.log.info("disable mdns")
            DMX_Zeroconf.disable_server()
            DMX_Log.log.info("Disable mdns discovery")
            DMX_Zeroconf.close()
            DMX_Log.log.info("disabled all")

    def onMVR_xchange_enable(self, context):
        if self.mvrx_enabled:
            clients = context.window_manager.dmx.mvr_xchange
            all_clients = context.window_manager.dmx.mvr_xchange.mvr_xchange_clients
            selected = clients.selected_mvr_client
            selected_client = None
            for selected_client in all_clients:
                if selected_client.station_uuid == selected:
                    break
            if not selected_client:
                return

            bpy.context.window_manager.dmx.mvr_xchange.mvr_x_group = (
                selected_client.service_name
            )
            DMX_Log.log.debug(
                (selected_client.ip_address, selected_client.station_name)
            )
            DMX_MVR_X_Server.enable()  # start the MVR-xchange TCP server for incoming connections
            DMX_MVR_X_Server._instance.server.get_port()
            DMX_Zeroconf.disable_server()
            DMX_Zeroconf.enable_server(
                selected_client.service_name, DMX_MVR_X_Server.get_port()
            )  # start mdns server and advertise the TCP MVR server
            # except Exception as e:
            #    DMX_Log.log.error("Error registering an mdns server")
            DMX_MVR_X_Client.join(
                selected_client
            )  # start MVR-xchange client TCP connection and send MVR_JOIN message
        else:
            DMX_Log.log.info("leave client")
            DMX_MVR_X_Client.leave()
            DMX_Log.log.info("disable client")
            DMX_MVR_X_Client.disable()

    def onMVR_xchange_socket_enable(self, context):
        shared_commits = bpy.context.window_manager.dmx.mvr_xchange.shared_commits
        shared_commits.clear()
        ws_commits = bpy.context.window_manager.dmx.mvr_xchange.websocket_commits
        ws_commits.clear()
        if self.mvrx_socket_client_enabled:
            DMX_Log.log.info("joining server")
            url = self.mvr_x_ws_url
            DMX_Log.log.debug(url)
            if url:
                DMX_MVR_X_WS_Client.join(
                    url
                )  # start MVR-xchange WS client connection and send MVR_JOIN message
        else:
            DMX_Log.log.info("leave server")
            DMX_MVR_X_WS_Client.leave()
            DMX_Log.log.info("disable server")
            DMX_MVR_X_WS_Client.disable()

    # OSC functionality

    def onOscEnable(self, context):
        if self.osc_enabled:
            DMX_OSC.enable()
            DMX_OSC_Templates.read()
        else:
            DMX_OSC.disable()

    # # DMX > sACN > Enable
    def onsACNEnable(self, context):
        if self.sacn_enabled:
            DMX_sACN.enable()

        else:
            DMX_sACN.disable()

    # # DMX > ArtNet > Enable

    def onArtNetEnable(self, context):
        if self.artnet_enabled:
            DMX_ArtNet.enable()
        else:
            DMX_ArtNet.disable()

    # fmt: off
    artnet_enabled : BoolProperty(
        name = _("Enable Art-Net Input"),
        description=_("Enables the input of DMX data throught Art-Net on the selected network interface"),
        default = False,
        update = onArtNetEnable
    )

    sacn_enabled : BoolProperty(
        name = _("Enable sACN Input"),
        description=_("Enables the input of DMX data throught sACN on all detected network interfaces"),
        default = False,
        update = onsACNEnable
    )

    osc_enabled : BoolProperty(
        name = _("Enable OSC Output"),
        description=_("Enables Open Sound Control protocol to send fixture selection to a console"),
        default = False,
        update = onOscEnable
    )

    osc_target_address : StringProperty(
        name = _("OSC Target address"),
        description=_("Address of the host where you want to send the OSC signal. Address ending on .255 is a broadcast address to all hosts on the network"),
        default="0.0.0.0"
    )

    osc_target_port : IntProperty(
        name = _("OSC Target port"),
        description=_("Port number of the host where you want to send the OSC signal"),
        default=42000
    )

    zeroconf_enabled : BoolProperty(
        name = _("Enable Local MVR-xchange"),
        description=_("Enables MVR-xchange sharing and discovery"),
        default = False,
        update = onZeroconfEnableDiscovery
    )

    project_application_uuid: StringProperty(
        default=str(py_uuid.uuid4()),
        name="Per project application UUID",
        description="Used for example for MVR xchange",
    )

    mvrx_enabled : BoolProperty(
        name = _("Connect to a selected station"),
        description=_("Connects to an MVR-xchange station"),
        default = False,
        update = onMVR_xchange_enable
    )

    mvrx_socket_client_enabled : BoolProperty(
        name = _("Enable Internet MVR-xchange"),
        description=_("Enables Internet based MVR-xchange sharing and discovery"),
        default = False,
        update = onMVR_xchange_socket_enable
    )

    mvr_x_ws_url: StringProperty(name="URL", description="URL", default="")

    mvrx_hostname_in_service : BoolProperty(
        name = _("Add hostname to MVR-xchange service"),
        description=_("Add computer name as sub-sub service in mDNS"),
        default = False,
    )

    mvrx_per_project_station_uuid : BoolProperty(
        name = _("Use per-project Station UUID"),
        description=_("Generates a random UUID for every blend file"),
        default = True,
    )
    # # DMX > ArtNet > Status

    artnet_status : EnumProperty(
        name = _("Art-Net Status"),
        items = DMX_ArtNet.status()
    )
    sacn_status : StringProperty(
        name = _("sACN Status"),
        default = "offline"
    )

    # # Groups > List

    def onGroupList(self, context):
        self.groups[self.group_list_i].select()

    group_list_i : IntProperty(
        name = _("Group List i"),
        description=_("The selected element on the group list"),
        default = 0,
        update = onGroupList
        )
    # fmt: on

    def onProgrammerApplyManually(self, context):
        self.onProgrammerPan(context)
        self.onProgrammerTilt(context)
        self.onProgrammerColor(context)
        self.onProgrammerDimmer(context)
        self.onProgrammerColorWheel(context)
        self.onProgrammerGobo(context)
        self.onProgrammerGoboIndex(context)
        self.onProgrammerShutter(context)
        self.onProgrammerZoom(context)

    # # Programmer > Dimmer

    def onProgrammerDimmer(self, context):
        for fixture_ in self.fixtures:
            if fixture_.collection is None:
                continue
            if fixture_.is_selected():
                fixture_.setDMX({"Dimmer": int(255 * self.programmer_dimmer)})
        self.render()

    # fmt: off
    programmer_dimmer: FloatProperty(
        name = "Programmer Dimmer",
        default = 0,
        min = 0,
        max = 1,
        update = onProgrammerDimmer)

    # fmt: on
    # # Programmer > Color

    def onProgrammerColor(self, context):
        for fixture_ in self.fixtures:
            if fixture_.collection is None:
                continue
            if fixture_.is_selected():
                rgb = [int(255 * x) for x in self.programmer_color]
                cmy = rgb_to_cmy(rgb)
                automatic_white = self.calculate_automatic_white()

                fixture_.setDMX(
                    {
                        "ColorAdd_R": rgb[0],
                        "ColorAdd_G": rgb[1],
                        "ColorAdd_B": rgb[2],
                        "ColorRGB_Red": rgb[0],
                        "ColorRGB_Green": rgb[1],
                        "ColorRGB_Blue": rgb[2],
                        "ColorSub_C": cmy[0],
                        "ColorSub_M": cmy[1],
                        "ColorSub_Y": cmy[2],
                        "ColorAdd_W": automatic_white,
                    }
                )
        self.render()

    def calculate_automatic_white(self):
        rgb = [int(255 * x) for x in self.programmer_color]
        if rgb[0] == rgb[1] == rgb[2]:
            return rgb[0]
        min_rgb = min(rgb)
        if min_rgb == 0:
            return 0
        average_rgb = sum(rgb) / len(rgb)
        automatic_white = int(average_rgb * (1 - (min_rgb / 255)))

        return automatic_white

    def onProgrammerTilt(self, context):
        for fixture_ in self.fixtures:
            if fixture_.collection is None:
                continue
            if fixture_.is_selected():
                fixture_.setDMX({"Tilt": int(255 * (self.programmer_tilt + 1) / 2)})
        self.render()

    def onProgrammerTiltRotate(self, context):
        for fixture_ in self.fixtures:
            if fixture_.collection is None:
                continue
            if fixture_.is_selected():
                fixture_.setDMX({"TiltRotate": int(self.programmer_tilt_rotate)})
        self.render()

    def onProgrammerPan(self, context):
        for fixture_ in self.fixtures:
            if fixture_.collection is None:
                continue
            if fixture_.is_selected():
                fixture_.setDMX({"Pan": int(255 * (self.programmer_pan + 1) / 2)})
        self.render()

    def onProgrammerPanRotate(self, context):
        for fixture_ in self.fixtures:
            if fixture_.collection is None:
                continue
            if fixture_.is_selected():
                fixture_.setDMX({"PanRotate": int(self.programmer_pan_rotate)})
        self.render()

    def onProgrammerZoom(self, context):
        for fixture_ in self.fixtures:
            if fixture_.collection is None:
                continue
            if fixture_.is_selected():
                fixture_.setDMX({"Zoom": int(self.programmer_zoom)})
        self.render()

    def onProgrammerColorTemperature(self, context):
        for fixture_ in self.fixtures:
            if fixture_.collection is None:
                continue
            if fixture_.is_selected():
                fixture_.setDMX(
                    {
                        "CTO": int(self.programmer_color_temperature),
                        "CTC": int(self.programmer_color_temperature),
                        "CTB": int(self.programmer_color_temperature),
                    }
                )
        self.render()

    def onProgrammerIris(self, context):
        for fixture_ in self.fixtures:
            if fixture_.collection is None:
                continue
            if fixture_.is_selected():
                fixture_.setDMX(
                    {
                        "Iris": int(self.programmer_iris),
                    }
                )
        self.render()

    def onProgrammerColorWheel(self, context):
        for fixture_ in self.fixtures:
            if fixture_.collection is None:
                continue
            if fixture_.is_selected():
                fixture_.setDMX(
                    {
                        "Color1": int(self.programmer_color_wheel),
                        "Color2": int(self.programmer_color_wheel),
                        "ColorMacro1": int(self.programmer_color_wheel),
                    }
                )
        self.render()

    def onProgrammerGobo1(self, context):
        for fixture_ in self.fixtures:
            if fixture_.collection is None:
                continue
            if fixture_.is_selected():
                fixture_.setDMX(
                    {
                        "Gobo1": int(self.programmer_gobo1),
                    }
                )
        self.render()

    def onProgrammerGoboIndex1(self, context):
        for fixture_ in self.fixtures:
            if fixture_.collection is None:
                continue
            if fixture_.is_selected():
                fixture_.setDMX(
                    {
                        "Gobo1Pos": int(self.programmer_gobo_index1),
                        "Gobo1PosRotate": int(self.programmer_gobo_index1),
                    }
                )
        self.render()

    def onProgrammerGobo2(self, context):
        for fixture_ in self.fixtures:
            if fixture_.collection is None:
                continue
            if fixture_.is_selected():
                fixture_.setDMX(
                    {
                        "Gobo2": int(self.programmer_gobo2),
                    }
                )
        self.render()

    def onProgrammerGoboIndex2(self, context):
        for fixture_ in self.fixtures:
            if fixture_.collection is None:
                continue
            if fixture_.is_selected():
                fixture_.setDMX(
                    {
                        "Gobo2Pos": int(self.programmer_gobo_index2),
                        "Gobo2PosRotate": int(self.programmer_gobo_index2),
                    }
                )
        self.render()

    def onProgrammerShutter(self, context):
        for fixture_ in self.fixtures:
            if fixture_.collection is None:
                continue
            if fixture_.is_selected():
                fixture_.setDMX({"Shutter1": int(self.programmer_shutter)})
        self.render()

    def onProgrammerPanMode(self, context):
        for fixture_ in self.fixtures:
            if fixture_.collection is None:
                continue
            if fixture_.is_selected():
                fixture_.setDMX({"PanMode": int(self.programmer_pan_mode)})
        self.render()

    def onProgrammerTiltMode(self, context):
        for fixture_ in self.fixtures:
            if fixture_.collection is None:
                continue
            if fixture_.is_selected():
                fixture_.setDMX({"TiltMode": int(self.programmer_tilt_mode)})
        self.render()

    # fmt: off

    programmer_color: FloatVectorProperty(
        name = "",
        subtype = "COLOR",
        size = 4,
        min = 0.0,
        max = 1.0,
        default = (1.0,1.0,1.0,1.0),
        update = onProgrammerColor)

    programmer_pan: FloatProperty(
        name = "Programmer Pan",
        min = -1.0,
        max = 1.0,
        default = 0.0,
        update = onProgrammerPan)

    programmer_pan_rotate: IntProperty(
        name = "Programmer Pan Rotate",
        min = 0,
        max = 255,
        default = 128,
        update = onProgrammerPanRotate)

    programmer_tilt: FloatProperty(
        name = "Programmer Tilt",
        min = -1.0,
        max = 1.0,
        default = 0.0,
        update = onProgrammerTilt)

    programmer_tilt_rotate: IntProperty(
        name = "Programmer Tilt Rotate",
        min = 0,
        max = 255,
        default = 128,
        update = onProgrammerTiltRotate)

    programmer_zoom: IntProperty(
        name = "Programmer Zoom",
        min = 0,
        max = 255,
        default = 128,
        update = onProgrammerZoom)

    programmer_color_wheel: IntProperty(
        name = "Programmer Color Wheel",
        min = 0,
        max = 255,
        default = 0,
        update = onProgrammerColorWheel)

    programmer_color_temperature: IntProperty(
        name = "Programmer Color Temperature",
        min = 0,
        max = 255,
        default = 0,
        update = onProgrammerColorTemperature)

    programmer_iris: IntProperty(
        name = "Programmer Iris",
        min = 0,
        max = 255,
        default = 0,
        update = onProgrammerIris)

    programmer_gobo1: IntProperty(
        name = "Programmer Gobo1",
        min = 0,
        max = 255,
        default = 0,
        update = onProgrammerGobo1)

    programmer_gobo_index1: IntProperty(
        name = "Gobo1 Rotation",
        min = 0,
        max = 255,
        default = 63,
        update = onProgrammerGoboIndex1)

    programmer_gobo2: IntProperty(
        name = "Programmer Gobo2",
        min = 0,
        max = 255,
        default = 0,
        update = onProgrammerGobo2)

    programmer_gobo_index2: IntProperty(
        name = "Gobo2 Rotation",
        min = 0,
        max = 255,
        default = 63,
        update = onProgrammerGoboIndex2)

    programmer_shutter: IntProperty(
        name = "Programmer Shutter",
        min = 0,
        max = 255,
        default = 0,
        update = onProgrammerShutter)

    programmer_pan_mode: IntProperty(
        name = "Programmer PanMode",
        min = 0,
        max = 255,
        default = 0,
        update = onProgrammerPanMode)

    programmer_tilt_mode: IntProperty(
        name = "Programmer TiltMode",
        min = 0,
        max = 255,
        default = 0,
        update = onProgrammerTiltMode)

    # fmt: on

    # # Programmer > Sync

    def syncProgrammer(self):
        selected = self.selectedFixtures()
        n = len(selected)
        if n < 1:
            self.programmer_dimmer = 0
            self.programmer_color = (255, 255, 255, 255)
            self.programmer_pan = 0
            self.programmer_pan_rotate = 128
            self.programmer_tilt = 0
            self.programmer_tilt_rotate = 128
            self.programmer_zoom = 25
            self.programmer_shutter = 0
            self.programmer_color_wheel = 0
            self.programmer_color_temperature = 0
            self.programmer_iris = 0
            self.programmer_gobo1 = 0
            self.programmer_gobo_index1 = 63
            self.programmer_gobo2 = 0
            self.programmer_gobo_index2 = 63
            self.programmer_tilt_mode = 0
            self.programmer_pan_mode = 0
            return
        elif n > 1:
            return
        active = selected[0]
        data = active.getProgrammerData()
        if "Dimmer" in data:
            self.programmer_dimmer = data["Dimmer"] / 255.0
        if "Shutter1" in data:
            self.programmer_shutter = int(data["Shutter1"] / 256.0)
        if "Zoom" in data:
            self.programmer_zoom = int(data["Zoom"])
        if "Color1" in data:
            self.programmer_color_wheel = int(data["Color1"])
        if "Color2" in data:
            self.programmer_color_wheel = int(data["Color2"])
        if "ColorMacro1" in data:
            self.programmer_color_wheel = int(data["ColorMacro1"])
        if "CTC" in data:
            self.programmer_color_temperature = int(data["CTC"])
        if "CTO" in data:
            self.programmer_color_temperature = int(data["CTO"])
        if "CTB" in data:
            self.programmer_color_temperature = int(data["CTB"])
        if "Iris" in data:
            self.programmer_iris = int(data["Iris"])
        if "Gobo1" in data:
            self.programmer_gobo1 = int(data["Gobo1"])
        if "Gobo2" in data:
            self.programmer_gobo2 = int(data["Gobo2"])
        if "Gobo1Pos" in data:
            self.programmer_gobo_index1 = int(data["Gobo1Pos"])
        if "Gobo1PosRotate" in data:
            self.programmer_gobo_index1 = int(data["Gobo1PosRotate"])
        if "Gobo2Pos" in data:
            self.programmer_gobo_index2 = int(data["Gobo2Pos"])
        if "Gobo2PosRotate" in data:
            self.programmer_gobo_index2 = int(data["Gobo2PosRotate"])
        if "ColorAdd_R" in data and "ColorAdd_G" in data and "ColorAdd_B" in data:
            rgb = [data["ColorAdd_R"], data["ColorAdd_G"], data["ColorAdd_B"]]
            self.programmer_color = (*flatten_color(rgb), 255)
        if (
            "ColorRGB_Red" in data
            and "ColorRGB_Green" in data
            and "ColorRGB_Blue" in data
        ):
            rgb = [data["ColorRGB_Red"], data["ColorRGB_Green"], data["ColorRGB_Blue"]]
            self.programmer_color = (*flatten_color(rgb), 255)
        if "ColorSub_C" in data and "ColorSub_M" in data and "ColorSub_Y" in data:
            rgb = cmy_to_rgb(
                [data["ColorSub_C"], data["ColorSub_M"], data["ColorSub_Y"]]
            )
            self.programmer_color = (
                1 / 256 * rgb[0],
                1 / 256 * rgb[1],
                1 / 256 * rgb[2],
                255,
            )
        # if ('ColorAdd_C' in data and 'ColorAdd_M' in data and 'ColorAdd_Y' in data):
        #    rgb = cmy_to_rgb([data['ColorAdd_C'], data['ColorAdd_M'], data['ColorAdd_Y']])
        #    self.programmer_color = (1/256*rgb[0], 1/256*rgb[1], 1/256*rgb[2], 255)
        if "Pan" in data:
            self.programmer_pan = data["Pan"] / 127.0 - 1
        if "Tilt" in data:
            self.programmer_tilt = data["Tilt"] / 127.0 - 1
        if "PanRotate" in data:
            self.programmer_pan_rotate = int(data["PanRotate"])
        if "TiltRotate" in data:
            self.programmer_tilt_rotate = int(data["TiltRotate"])
        if "PanMode" in data:
            self.programmer_pan_mode = int(data["PanMode"])
        if "TiltMode" in data:
            self.programmer_tilt_mode = int(data["TiltMode"])

    # fmt: off
    fixtures_sorting_order: EnumProperty(
        name= _("Order by"),
        description= _("Fixture sorting order"),
        default = "ADDRESS",
        items= [
                ("NAME", _("Name"), "", "", 0),
                ("FIXTURE_ID", _("Fixture ID"), "", "", 1),
                ("ADDRESS", _("DMX Address"), "", "", 2),
                ("UNIT_NUMBER", _("Unit Number"), "", "", 3),
        ],
        )

    # fmt: on
    # Kernel Methods
    # # Fixtures
    def addFixture(
        self,
        name,
        profile,
        mode,
        dmx_breaks,
        gel_color,
        display_beams,
        add_target,
        position=None,
        focus_point=None,
        uuid=None,
        fixture_id="",
        custom_id=0,
        fixture_id_numeric=0,
        unit_number=0,
        classing=None,
    ):
        # TODO: fix order of attributes to match fixture.build()
        dmx = bpy.context.scene.dmx
        new_fixture = dmx.fixtures.add()
        new_fixture.uuid = str(py_uuid.uuid4())  # ensure clean uuid
        try:
            new_fixture.build(
                name,
                profile,
                mode,
                dmx_breaks,
                gel_color,
                display_beams,
                add_target,
                position,
                focus_point,
                uuid,
                fixture_id,
                custom_id,
                fixture_id_numeric,
                unit_number,
                classing=classing,
            )
        except Exception as e:
            DMX_Log.log.error(f"Error while adding fixture {e}")
            dmx.fixtures.remove(len(dmx.fixtures) - 1)
            ShowMessageBox(
                f"{e}",
                "Error while adding a fixture, see console for more details",
                "ERROR",
            )
            traceback.print_exception(e)
            DMX_Log.log.exception(e)

    def removeFixture(self, fixture):
        try:
            self.remove_fixture_from_groups(fixture.uuid)
        except Exception as e:
            DMX_Log.log.error(f"Error while removing group {e}")

        if fixture.collection.objects is not None:
            for obj in fixture.collection.objects:
                bpy.data.objects.remove(obj)
        if fixture.objects is not None:
            for obj in fixture.objects:
                if obj.object:
                    bpy.data.objects.remove(obj.object)
        bpy.data.collections.remove(fixture.collection)
        self.fixtures.remove(self.fixtures.find(fixture.name))

    def getFixture(self, collection):
        for fixture_ in self.fixtures:
            if fixture_.collection == collection:
                return fixture_

    def findFixture(self, object):
        for fixture_ in self.fixtures:
            if fixture_ is None:
                continue
            if object.name in fixture_.collection.objects:
                return fixture_
        return None

    def findFixtureByUUID(self, uuid):
        for fixture_ in self.fixtures:
            if fixture_ is None:
                continue
            if fixture_.uuid == uuid:
                return fixture_
        return None

    def selectedFixtures(self):
        selected = []
        for fixture_ in self.fixtures:
            if fixture_.is_selected():
                selected.append(fixture_)
        return selected

    def sortedFixtures(self):
        def string_to_pairs(s, pairs=re.compile(r"(\D*)(\d*)").findall):
            return [
                (text.lower(), int(digits or 0)) for (text, digits) in pairs(s)[:-1]
            ]

        sorting_order = self.fixtures_sorting_order

        if sorting_order == "ADDRESS":
            fixtures = sorted(
                self.fixtures,
                key=lambda c: string_to_pairs(
                    str(c.dmx_breaks[0].universe * 1000 + c.dmx_breaks[0].address)
                ),
            )
        elif sorting_order == "NAME":
            fixtures = sorted(self.fixtures, key=lambda c: string_to_pairs(c.name))
        elif sorting_order == "FIXTURE_ID":
            fixtures = sorted(
                self.fixtures, key=lambda c: string_to_pairs(str(c.fixture_id))
            )
        elif sorting_order == "UNIT_NUMBER":
            fixtures = sorted(
                self.fixtures, key=lambda c: string_to_pairs(str(c.unit_number))
            )
        else:
            fixtures = self.fixtures

        return fixtures

    def addMVR(self, file_name, import_focus_points=True):
        bpy.context.window_manager.dmx.pause_render = (
            True  # this stops the render loop, to prevent slowness and crashes
        )

        load_mvr(self, file_name, import_focus_points=import_focus_points)

        bpy.context.window_manager.dmx.pause_render = False  # re-enable render loop
        Profiles.DMX_Fixtures_Local_Profile.loadLocal()
        DMX_GDTF_File.get_manufacturers_list()

    def clean_up_empty_mvr_collections(self, collections):
        for collection in collections.children:
            if len(collection.all_objects) == 0:
                collections.children.unlink(collection)

    def get_addon_path(self):
        if bpy.app.version >= (4, 2):
            try:
                return bpy.utils.extension_path_user(__package__, path="", create=True)
            except ValueError:
                return os.path.dirname(os.path.realpath(__file__))
        return os.path.dirname(os.path.realpath(__file__))

    def export_mvr(self, file_name):
        start_time = time.time()
        bpy.context.window_manager.dmx.pause_render = (
            True  # this stops the render loop, to prevent slowness and crashes
        )
        dmx = bpy.context.scene.dmx

        folder_path = self.get_addon_path()
        folder_path = os.path.join(folder_path, "assets", "profiles")

        try:
            fixtures_list = []
            mvr = pymvr.GeneralSceneDescriptionWriter()
            pymvr.UserData().to_xml(parent=mvr.xml_root)
            scene = pymvr.SceneElement().to_xml(parent=mvr.xml_root)
            layers = pymvr.LayersElement().to_xml(parent=scene)
            layer = pymvr.Layer(name="DMX").to_xml(parent=layers)
            child_list = pymvr.ChildList().to_xml(parent=layer)
            for dmx_fixture in dmx.fixtures:
                fixture_object = dmx_fixture.to_mvr_fixture()
                focus_point = dmx_fixture.focus_to_mvr_focus_point()
                if focus_point is not None:
                    child_list.append(focus_point.to_xml())
                child_list.append(fixture_object.to_xml())
                file_path = os.path.join(folder_path, fixture_object.gdtf_spec)
                fixtures_list.append((file_path, fixture_object.gdtf_spec))

            pymvr.AUXData().to_xml(parent=scene)
            mvr.files_list = list(set(fixtures_list))
            mvr.write_mvr(file_name)
            file_size = Path(file_name).stat().st_size

        except Exception as e:
            traceback.print_exception(e)
            return SimpleNamespace(ok=False, error=str(e))

        bpy.context.window_manager.dmx.pause_render = False  # re-enable render loop
        print("INFO", "MVR scene exported in %.4f sec." % (time.time() - start_time))
        return SimpleNamespace(ok=True, file_size=file_size)

    def ensureUniverseExists(self, universe):
        # Allocate universes to be able to control devices
        dmx = bpy.context.scene.dmx
        for _ in range(len(dmx.universes), universe + 1):
            self.addUniverse()
        self.universes_n = len(self.universes)

    def createMVR_Client(
        self,
        station_name="",
        station_uuid="",
        service_name="",
        ip_address="",
        port=0,
        provider="",
    ):
        prefs = bpy.context.preferences.addons[__package__].preferences
        application_uuid = prefs.get(
            "application_uuid", str(py_uuid.uuid4())
        )  # must never be 0
        if self.mvrx_per_project_station_uuid:
            application_uuid = self.project_application_uuid
        application_uuid = application_uuid.upper()

        if application_uuid == station_uuid:
            if not DMX_Log.log.isEnabledFor(logging.DEBUG):
                DMX_Log.log.info(
                    "This is myself, do not register as an MVR-xchange provider"
                )
                return

        clients = bpy.context.window_manager.dmx.mvr_xchange.mvr_xchange_clients
        for client in clients:
            if client.station_uuid == station_uuid:
                return  # client already in the list

        if ip_address == "":
            return

        client = clients.add()
        client.station_name = station_name or ""
        client.station_uuid = station_uuid
        client.service_name = service_name
        client.provider = provider or ""
        now = int(datetime.now().timestamp())
        client.last_seen = now
        client.ip_address = ip_address
        client.port = port
        if provider:
            client.provider = provider

    def removeMVR_Client(
        self, station_name, station_uuid, service_name, ip_addres, port
    ):
        clients = bpy.context.window_manager.dmx.mvr_xchange.mvr_xchange_clients
        for client in clients:
            if client.station_uuid == station_uuid:
                clients.remove(client)
                break

    def updateMVR_Client(
        self,
        station_uuid,
        station_name=None,
        service_name=None,
        ip_address=None,
        port=None,
        provider=None,
    ):
        clients = bpy.context.window_manager.dmx.mvr_xchange.mvr_xchange_clients
        updated = False

        for client in clients:
            if client.station_uuid == station_uuid:
                if station_name:
                    client.station_name = station_name
                now = int(datetime.now().timestamp())
                client.last_seen = now
                if ip_address:
                    client.ip_address = ip_address
                if port:
                    client.port = port
                if provider:
                    client.provider = provider
                if service_name:
                    client.service_name = service_name
                updated = True
                break
        if not updated:
            self.createMVR_Client(
                station_name, station_uuid, service_name, ip_address, port
            )

    def createMVR_Commits(self, commits, station_uuid):
        clients = bpy.context.window_manager.dmx.mvr_xchange.mvr_xchange_clients
        for client in clients:
            if client.station_uuid == station_uuid:
                # client.commits.clear()

                for commit in commits:
                    skip = False
                    if "FileName" in commit:
                        filename = commit["FileName"]
                    else:
                        filename = commit["Comment"]
                    if not len(filename):
                        filename = commit["FileUUID"]

                    for existing_commit in client.commits:
                        if existing_commit.commit_uuid == commit["FileUUID"]:
                            skip = True
                            continue
                    if not skip:
                        now = int(datetime.now().timestamp())
                        client.last_seen = now
                        new_commit = client.commits.add()
                        new_commit.station_uuid = station_uuid
                        new_commit.comment = commit["Comment"]
                        new_commit.commit_uuid = commit["FileUUID"]
                        new_commit.file_size = commit["FileSize"]
                        new_commit.file_name = filename
                        new_commit.timestamp = now

    def createMVR_WS_Commits(self, commits, station_uuid):
        stored_commits = bpy.context.window_manager.dmx.mvr_xchange.websocket_commits

        for commit in commits:
            skip = False
            if "FileName" in commit:
                filename = commit["FileName"]
            else:
                filename = commit["Comment"]
            if not len(filename):
                filename = commit["FileUUID"]

            for existing_commit in stored_commits:
                if existing_commit.commit_uuid == commit["FileUUID"]:
                    skip = True
                    continue
            if not skip:
                now = int(datetime.now().timestamp())
                new_commit = stored_commits.add()
                new_commit.station_uuid = station_uuid
                new_commit.comment = commit["Comment"]
                new_commit.commit_uuid = commit["FileUUID"]
                new_commit.file_size = commit["FileSize"]
                new_commit.file_name = filename
                new_commit.timestamp = now

    def createMVR_Shared_Commit(self, commit):
        commits = bpy.context.window_manager.dmx.mvr_xchange.shared_commits
        now = int(datetime.now().timestamp())
        new_commit = commits.add()
        new_commit.comment = commit.comment
        new_commit.commit_uuid = commit.file_uuid
        new_commit.file_size = commit.file_size
        new_commit.file_name = commit.file_name
        new_commit.timestamp = now

        if DMX_MVR_X_WS_Client._instance is not None:
            DMX_MVR_X_WS_Client._instance.client.send_commit(new_commit)

        if DMX_MVR_X_Client._instance is not None:
            DMX_MVR_X_Client.send_commit(new_commit)

    def fetched_mvr_downloaded_file(self, commit):
        clients = bpy.context.window_manager.dmx.mvr_xchange.mvr_xchange_clients
        now = int(datetime.now().timestamp())
        for client in clients:
            if client.station_uuid == commit.station_uuid:
                for c_commit in client.commits:
                    if c_commit.commit_uuid == commit.commit_uuid:
                        c_commit.timestamp_saved = now

    def request_failed_mvr_downloaded_file(self, commit):
        clients = bpy.context.window_manager.dmx.mvr_xchange.mvr_xchange_clients
        for client in clients:
            if client.station_uuid == commit.station_uuid:
                for c_commit in client.commits:
                    if c_commit.commit_uuid == commit.commit_uuid:
                        c_commit.timestamp_saved = -1

    def fetched_mvr_downloaded_ws_file(self, commit):
        websocket_commits = bpy.context.window_manager.dmx.mvr_xchange.websocket_commits
        now = int(datetime.now().timestamp())
        for c_commit in websocket_commits:
            if c_commit.commit_uuid == commit.commit_uuid:
                c_commit.timestamp_saved = now

    def request_failed_mvr_downloaded_ws_file(self, commit):
        websocket_commits = bpy.context.window_manager.dmx.mvr_xchange.websocket_commits
        for c_commit in websocket_commits:
            if c_commit.commit_uuid == commit.commit_uuid:
                c_commit.timestamp_saved = -1

    # # Groups

    def createGroup(self, name):
        dmx = bpy.context.scene.dmx
        group = dmx.groups.add()
        group.name = name
        group.uuid = str(py_uuid.uuid4())  # ensure clean uuid
        group.update()
        DMX_Log.log.info(group.dump)
        if not len(group.dump):
            DMX_Log.log.info("DMX Group: no fixture selected!")
            dmx.groups.remove(len(dmx.groups) - 1)
            return False
        return True

    def updateGroup(self, i):
        dmx = bpy.context.scene.dmx
        if i >= 0 and i < len(self.groups):
            dmx.groups[i].update()

    def renameGroup(self, i, name):
        dmx = bpy.context.scene.dmx
        if i >= 0 and i < len(self.groups):
            dmx.groups[i].name = name

    def removeGroup(self, i):
        bpy.context.scene.dmx.groups.remove(i)

    def remove_fixture_from_groups(self, fixture_uuid):
        dmx = bpy.context.scene.dmx
        for group in dmx.groups:
            dump = json.loads(group.dump)
            if fixture_uuid in dump:
                dump.remove(fixture_uuid)
                group.dump = json.dumps(dump)

    # # Preview Volume

    def updatePreviewVolume(self):
        if self.volume_preview == "SELECTED":
            self.disable_overlays = False  # overlay must be enabled
            for fixture_ in self.fixtures:
                selected = False
                if fixture_ is None:
                    continue
                if fixture_.collection is None:
                    continue
                if fixture_.is_selected():
                    selected = True
                for light in fixture_.lights:
                    light.object.data.show_cone = selected

        elif self.volume_preview == "ALL":
            self.disable_overlays = False  # overlay must be enabled
            for fixture_ in self.fixtures:
                for light in fixture_.lights:
                    light.object.data.show_cone = True
        else:
            for fixture_ in self.fixtures:
                for light in fixture_.lights:
                    light.object.data.show_cone = False

    # # Universes

    def addUniverse(self):
        id = len(self.universes)
        DMX_Universe.add(self, id, "Universe %d" % id)

    def removeUniverse(self, i):
        DMX_Universe.remove(self, i)

    def generate_project_uuid(self):
        self.project_application_uuid = str(py_uuid.uuid4())

    def generate_default_channel_functions(self):
        self.default_channel_functions.clear()
        defaults = [
            ["Zoom", 0, 120],
            ["Pan", 270, -270],
            ["Tilt", -135, 135],
            ["PanRotate", 500, -500],
            ["TiltRotate", 500, -500],
            ["CTC", 2700, 12000],
            ["CTB", 2700, 12000],
            ["CT0", 2700, 12000],
            ["Iris", 0, 1],
        ]
        for default in defaults:
            new_function = self.default_channel_functions.add()
            new_function.attribute = default[0]
            new_function.name_ = f"{default[0]} 1"
            new_function.dmx_from = 0
            new_function.dmx_to = 255
            new_function.physical_from = default[1]
            new_function.physical_to = default[2]

    # # Render

    def render(self):
        if bpy.context.scene.tool_settings.use_keyframe_insert_auto:
            # make the frame the same for all fixtures
            current_frame = bpy.data.scenes[0].frame_current
        else:
            current_frame = None

        for fixture_ in self.fixtures:
            fixture_.render(current_frame=current_frame)
        for tracker_ in self.trackers:
            tracker_.render(current_frame=current_frame)

    def set_fixtures_filter(self, fixtures_filter):
        DMX.fixtures_filter = fixtures_filter

    def update_laser_collision_collect(self):
        for fixture_ in self.fixtures:
            for nodes in fixture_.geometry_nodes:
                collection_info = nodes.node.nodes["Collection Info"]
                collection = bpy.context.window_manager.dmx.collections_list
                collection_info.inputs[0].default_value = collection
