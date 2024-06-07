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


import sys
import bpy
import os
from threading import Timer
import time
import json
import uuid as py_uuid
import re
from datetime import datetime
import traceback
from types import SimpleNamespace

import pymvr
from .mvr import load_mvr

from . import param as param
from . import fixture as fixture
from . import tracker as tracker
from .universe import DMX_Universe
from .data import DMX_Value, DMX_Data
from .gdtf import DMX_GDTF
from .artnet import DMX_ArtNet
from .acn import DMX_sACN
from .network import DMX_Network
from .logging import DMX_Log

from .panels import recorder as recorder
from .panels import setup as setup
from .panels.protocols import protocols as panels_protocols
from .panels.protocols import artnet as panels_artnet
from .panels.protocols import sacn as panels_sacn
from .panels.protocols import osc as panels_osc
from .panels.protocols import psn as panels_psn
from .panels.protocols import mvr as panels_mvr
from .panels.protocols import universes as panels_universes
from .panels.protocols import live as panels_live
from .panels import fixtures as fixtures
from .panels import groups as groups
from .panels import programmer as programmer
from .panels import profiles as Profiles
from .panels import distribute as distribute

from .preferences import DMX_Preferences, DMX_Regenrate_UUID
from .group import FixtureGroup, DMX_Group
from .osc_utils import DMX_OSC_Templates
from .osc import DMX_OSC
from .mdns import DMX_Zeroconf

from .util import rgb_to_cmy, ShowMessageBox, cmy_to_rgb, flatten_color
from .mvr_objects import DMX_MVR_Object
from .mvr_xchange import DMX_MVR_Xchange_Commit, DMX_MVR_Xchange_Client, DMX_MVR_Xchange
from .mvrx_protocol import DMX_MVR_X_Client, DMX_MVR_X_Server
import bpy.utils.previews
from .material import set_light_nodes
from bpy.props import (BoolProperty,
                       StringProperty,
                       IntProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       PointerProperty,
                        EnumProperty,
                       CollectionProperty)

from bpy.types import (PropertyGroup,
                       Object,
                       Collection,
                       NodeTree)

from .i18n import DMX_Lang
_ = DMX_Lang._

class DMX(PropertyGroup):

    # Base classes to be registered
    # These should be registered before the DMX class, so it can register properly

    classes_base = (param.DMX_Param,
                    param.DMX_Model_Param,
                    fixture.DMX_Fixture_Object,
                    fixture.DMX_Fixture_Image,
                    fixture.DMX_Emitter_Material,
                    fixture.DMX_IES_Data,
                    fixture.DMX_Geometry_Node,
                    fixture.DMX_Fixture_Channel,
                    fixture.DMX_Fixture,
                    tracker.DMX_Tracker_Object,
                    tracker.DMX_Tracker,
                    DMX_MVR_Object,
                    DMX_Group,
                    DMX_Universe,
                    DMX_Value,
                    setup.DMX_PT_Setup,
                    panels_mvr.DMX_OP_MVR_Download,
                    panels_mvr.DMX_OP_MVR_Import,
                    DMX_MVR_Xchange_Commit,
                    DMX_MVR_Xchange_Client,
                    DMX_MVR_Xchange,
                    DMX_Regenrate_UUID,
                    DMX_Preferences)

    # Classes to be registered
    # The registration is done in two steps. The second only runs
    # after the user requests to setup the addon.

    classes_setup = (setup.DMX_OT_Setup_NewShow,)

    classes = ( panels_protocols.DMX_PT_DMX,
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
                setup.DMX_OT_Reload_Addon,
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
                panels_mvr.DMX_OP_MVR_Refresh,
                panels_mvr.DMX_OP_MVR_Request,
                fixtures.DMX_OT_Fixture_ForceRemove,
                fixtures.DMX_OT_Fixture_SelectNext,
                fixtures.DMX_OT_Fixture_SelectPrevious,
                fixtures.DMX_OT_Fixture_SelectNextTarget,
                fixtures.DMX_OT_Fixture_SelectPreviousTarget,
                setup.DMX_OT_VersionCheck,
                programmer.DMX_PT_Programmer,
                recorder.DMX_OT_Recorder_AddKeyframe,
                recorder.DMX_PT_Recorder,
                recorder.DMX_PT_DMX_Recorder_Delete,
                recorder.DMX_OT_Recorder_Delete_Keyframes_Selected,
                recorder.DMX_OT_Recorder_Delete_Keyframes_All,
                setup.DMX_OT_Fixture_Set_Cycles_Beams_Size_Small,
                setup.DMX_OT_Fixture_Set_Cycles_Beams_Size_Normal)

    linkedToFile = False
    _keymaps = []
    fixtures_filter = []
    custom_icons = None

    def register():
        #custom icons
        DMX.custom_icons = bpy.utils.previews.new()

        ADDON_PATH = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(ADDON_PATH, "assets", "icons")
        DMX.custom_icons.load("DEFAULT_TEST", os.path.join(path, "erlenmeyer.png"), "IMAGE")
        DMX.custom_icons.load("PRODUCTION_ASSIST", os.path.join(path, "pa.png"), "IMAGE")
        DMX.custom_icons.load("GMA3", os.path.join(path, "ma.png"), "IMAGE")
        DMX.custom_icons.load("GDTF_FILE", os.path.join(path, "gdtf_file_icon_small.png"), "IMAGE")
        DMX.custom_icons.load("MVR_FILE", os.path.join(path, "mvr_file_icon_small.png"), "IMAGE")

        for cls in DMX.classes_setup:
            bpy.utils.register_class(cls)

        # register key shortcuts
        wm = bpy.context.window_manager
        km = wm.keyconfigs.addon.keymaps.new(name='3D View Generic', space_type='VIEW_3D')
        kmi = km.keymap_items.new('dmx.fixture_next', 'RIGHT_ARROW', 'PRESS', ctrl=True, shift=False)
        DMX._keymaps.append((km, kmi))
        kmi = km.keymap_items.new('dmx.fixture_previous', 'LEFT_ARROW', 'PRESS', ctrl=True, shift=False)
        DMX._keymaps.append((km, kmi))
        kmi = km.keymap_items.new('dmx.fixture_next_target', 'RIGHT_ARROW', 'PRESS', ctrl=True, shift=True)
        DMX._keymaps.append((km, kmi))
        kmi = km.keymap_items.new('dmx.fixture_previous_target', 'LEFT_ARROW', 'PRESS', ctrl=True, shift=True)
        DMX._keymaps.append((km, kmi))
        kmi = km.keymap_items.new('dmx.reload_addon', 'R', 'PRESS', ctrl=True, alt=True)
        DMX._keymaps.append((km, kmi))

    def unregister():
        # unregister keymaps
        for km, kmi in DMX._keymaps: km.keymap_items.remove(kmi)
        DMX._keymaps.clear()
        bpy.utils.previews.remove(DMX.custom_icons)


        if (DMX.linkedToFile):
            for cls in DMX.classes:
                bpy.utils.unregister_class(cls)
            DMX.linkedToFile = False
        else:
            for cls in DMX.classes_setup:
                bpy.utils.unregister_class(cls)


    # Blender RNA Properties

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

    collection: PointerProperty(
        name = _("DMX Collection"),
        type = Collection)

    volume: PointerProperty(
        name = "Volume Scatter Box",
        type = Object)

    volume_nodetree: PointerProperty(
        name = "Volume Scatter Shader Node Tree",
        type = NodeTree)

    # DMX Properties
    # These should be parsed to file

    fixtures: CollectionProperty(
        name = "DMX Fixtures",
        type = fixture.DMX_Fixture)

    trackers: CollectionProperty(
        name = "Trackers",
        type = tracker.DMX_Tracker)

    trackers_i : IntProperty(
        name = _("Trackers Item"),
        description=_("The selected element on the trackers list"),
        default = 0
        )

    groups: CollectionProperty(
        name = "DMX Groups",
        type = DMX_Group)

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
            default = 10,
            )

    def get_fixture_by_index(self, index):
        for idx, fixture in enumerate(self.fixtures):
            if idx == index:
                return fixture

    def on_ui_selection_change(self, context):
        """ If fixture selection is changed via UILists 'normal' interaction, rather then an operator.
        Not currently used, as this starts to create circular updates and we would need to pass info
        if fixture was actually being selected or unselected.
        """
        return
        for idx, fixture in enumerate(self.fixtures):
            if idx == self.selected_fixture_index:
                if not fixture.is_selected():
                    #fixture.toggleSelect()
                    fixture.select()
                    return

    selected_fixture_index: IntProperty(
            default = 0,
            update = on_ui_selection_change
            ) # Just a fake value, we need as the Fixture list requires it

    fixture_properties_editable: BoolProperty(
        name = _("Editable"),
        default = False)

    # New DMX Scene
    # - Remove any previous DMX objects/collections
    # - Create DMX collection
    # - Create DMX universes
    # - Link to file
    def new(self):

        # Remove old DMX collection from file if present
        if ("DMX" in bpy.data.collections):
            bpy.data.collections.remove(bpy.data.collections["DMX"])

        # Remove old Volume object from file if present
        if ("DMX_Volume" in bpy.data.objects):
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

        scene.world.node_tree.nodes['Background'].inputs[0].default_value = (0,0,0,0)

        # Create a DMX universe
        self.addUniverse()

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

        DMX_GDTF.getManufacturerList()
        Profiles.DMX_Fixtures_Local_Profile.loadLocal()
        Profiles.DMX_Fixtures_Import_Gdtf_Profile.loadShare()
        DMX_Log.enable(self.logging_level)
        DMX_Log.log.info("BlenderDMX: Linking to file")


        # Link pointer properties to file objects
        if ("DMX" in bpy.data.collections):
            self.collection = bpy.data.collections["DMX"]
        else:
            self.collection = None

        if ("DMX_Volume" in bpy.data.objects):
            self.volume = bpy.data.objects["DMX_Volume"]
        else:
            self.volume = None

        DMX_Log.log.info(f"DMX collection: {self.collection}")
        DMX_Log.log.info(f"DMX_Volume object: {self.volume}")

        if (self.collection):
            # Second step registration (if not already registered)
            if (not DMX.linkedToFile):
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
        if (dmx.artnet_enabled and dmx.artnet_status != 'online'):
            dmx.artnet_enabled = False
            dmx.artnet_status = 'offline'
        if (dmx.sacn_enabled and dmx.sacn_status != 'online'):
            dmx.sacn_enabled = False
            dmx.sacn_status = 'offline'
        if dmx.osc_enabled:
            dmx.osc_enabled = False

        for tracker_item in dmx.trackers:
            tracker_item.enabled = False
            if not len(tracker_item.ip_address):
                if len(DMX_Network.cards(None, None)):
                    tracker_item.ip_address = DMX_Network.cards(None, None)[0][0]
                else:
                    DMX_Log.log.warning("No network card detected")

        # Rebuild group runtime dictionary (evaluating if this is gonna stay here)
        #DMX_Group.runtime = {}
        #for group in self.groups:
        #    group.rebuild()

        self.logging_level = "DEBUG" # setting high logging level to see initialization
        self.migrations()
        self.ensure_application_uuid()
        self.check_python_version()
        self.check_blender_version()
        if bpy.app.version >= (4, 2):
            # do not do version check online in 4.2 and up
            pass
        else:
            Timer(1, bpy.ops.dmx.check_version, ()).start()
        self.logging_level = "ERROR" # setting default logging level

    # Unlink Add-on from file
    # This is only called when the DMX collection is externally removed
    def unlinkFile(self):
        print("INFO", "Unlinking from file")

        # Unlink pointer properties
        self.collection  = None
        self.volume = None

        # Second step unregistration
        if (DMX.linkedToFile):
            for cls in self.classes:
                bpy.utils.unregister_class(cls)
            DMX.linkedToFile = False

    # Callback Properties

    # # Setup > Background > Color

    def check_python_version(self):
        if not sys.version_info >= (3, 8):
            DMX_Log.log.error(f"Python version of at least 3.8 is needed, you are using {sys.version} ❌")
            return
        DMX_Log.log.info(f"Python version: {sys.version} ✅")

    def check_blender_version(self):
        if not bpy.app.version >= (3, 4):
            DMX_Log.log.error(f"Blender version of at least 3.4 is needed, you are using {bpy.app.version} ❌")
            return
        DMX_Log.log.info(f"Blender version: {bpy.app.version} ✅")

    def ensure_application_uuid(self):
        prefs = bpy.context.preferences.addons[__package__].preferences
        application_uuid = prefs.get("application_uuid", 0)
        if application_uuid == 0:
            prefs["application_uuid"] = str(py_uuid.uuid4()) # must never be 0

    def migrations(self):
        """Provide migration scripts when bumping the data_version"""
        file_data_version = 1 # default data version before we started setting it up

        if ("DMX_DataVersion" in self.collection):
            file_data_version = self.collection["DMX_DataVersion"]

        DMX_Log.log.info(f"Data version: {file_data_version}")

        if file_data_version < 2: # migration for sw. version 0.5 → 1.0
            DMX_Log.log.info("Running migration 1→2")
            dmx = bpy.context.scene.dmx

            for fixture in dmx.fixtures:
                for obj in fixture.objects:
                    if any(obj.name == name for name in ['Body', 'Base']):
                        DMX_Log.log.info(f"updating {obj.name}")
                        obj.name = 'Root'

                for light in fixture.lights:
                    DMX_Log.log.info("Adding shutter and dimmer value fields to light object")
                    if "shutter_value" not in light.object.data:
                        light.object.data["shutter_value"] = 0
                    if "shutter_dimmer_value" not in light.object.data:
                        light.object.data["shutter_dimmer_value"] = 0
                    if "shutter_counter" not in light.object.data:
                        light.object.data["shutter_counter"] = 0

        if file_data_version < 3:
            DMX_Log.log.info("Running migration 2→3")
            dmx = bpy.context.scene.dmx
            DMX_Log.log.info("Add UUID to fixtures")
            for fixture in dmx.fixtures:
                if "uuid" not in fixture:
                    DMX_Log.log.info(f"Adding UUID to {fixture.name}")
                    fixture.uuid = str(py_uuid.uuid4())
            DMX_Log.log.info("Add UUID to groups, convert groups to json")
            for group in dmx.groups:
                if "uuid" not in group:
                    DMX_Log.log.info("Adding UUID to {group.name}")
                    group.uuid = str(py_uuid.uuid4())
                DMX_Log.log.info("Migrating group")
                group.dump = json.dumps([x[1:-1] for x in group.dump.strip('[]').split(', ')])

        if file_data_version < 4:
            DMX_Log.log.info("Running migration 3→4")
            dmx = bpy.context.scene.dmx

            def findFixtureUuidDuplicates(uuid):
                found = []
                for fixture in self.fixtures:
                    if fixture is None:
                        continue
                    if fixture.uuid == uuid:
                        found.append(fixture)
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
            for fixture in dmx.fixtures:
                duplicates = findFixtureUuidDuplicates(fixture.uuid)
                if len(duplicates) > 1:
                    for fixture in duplicates:
                        u = fixture.uuid
                        fixture.uuid = str(py_uuid.uuid4())
                        DMX_Log.log.info(("Updating fixture", fixture.name, u, fixture.uuid))

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
                        fixture = dmx.fixtures[g_fixture]
                        if fixture is not None:
                            uuid_list.append(fixture.uuid)
                group.dump = json.dumps(uuid_list)
            DMX_Log.log.info("Groups updated")

        if file_data_version < 5:
            DMX_Log.log.info("Running migration 4→5")
            dmx = bpy.context.scene.dmx
            for fixture in dmx.fixtures:
                if "dmx_values" not in fixture:
                    DMX_Log.log.info("Adding dmx_value array to fixture")
                    fixture["dmx_values"] = []

        if file_data_version < 6:
            DMX_Log.log.info("Running migration 5→6")
            DMX_Log.log.info("To make gobos working again, edit fixtures with gobos - re-load GDTF files (Fixtures → Edit, uncheck Re-address only)")

        if file_data_version < 7:
            DMX_Log.log.info("Running migration 6→7")
            dmx = bpy.context.scene.dmx
            for fixture in dmx.fixtures:
                for light in fixture.lights:
                    DMX_Log.log.info("Adding nodes to light")
                    set_light_nodes(light)


            if "DMX_Volume" in bpy.data.objects:
                objs = bpy.data.objects
                objs.remove(objs["DMX_Volume"], do_unlink=True)
                DMX_Log.log.info("Removing Volume box due to old structure, you need to create it new")

            if "DMX_Volume" in bpy.data.materials:
                objs = bpy.data.materials
                objs.remove(objs["DMX_Volume"], do_unlink=True)
                DMX_Log.log.info("Removing Volume box material due to old structure, you need to create it new")

        if file_data_version < 8:
            DMX_Log.log.info("Running migration 7→8")
            dmx = bpy.context.scene.dmx
            for fixture in dmx.fixtures:
                if "slot_colors" not in fixture:
                    DMX_Log.log.info("Adding slot_colors array to fixture")
                    fixture["slot_colors"] = []

        if file_data_version < 9:
            DMX_Log.log.info("Running migration 8→9")
            dmx = bpy.context.scene.dmx
            for fixture in dmx.fixtures:
                fixture.gel_color_rgb = list(int((255/1)*i) for i in fixture.gel_color[:3])
                DMX_Log.log.info("Converting gel color to rgb")

        if file_data_version < 10:
            DMX_Log.log.info("Running migration 9→10")
            dmx = bpy.context.scene.dmx

            for fixture in dmx.fixtures:
                for obj in fixture.objects:
                    if 'Target' in obj.name:
                        if "uuid" not in obj.object:
                            DMX_Log.log.info(f"Add uuid to {obj.name}")
                            obj.object["uuid"] = str(py_uuid.uuid4())

        DMX_Log.log.info("Migration done.")
        # add here another if statement for next migration condition... like:
        # if file_data_version < 6: #...

        self.collection["DMX_DataVersion"] = self.data_version # set data version to current


    def onBackgroundColor(self, context):
        context.scene.world.node_tree.nodes['Background'].inputs[0].default_value = self.background_color

    background_color: FloatVectorProperty(
        name = "Background Color",
        subtype = "COLOR",
        size = 4,
        min = 0.0,
        max = 1.0,
        default = (0.0,0.0,0.0,1.0),
        update = onBackgroundColor
        )

    # # Setup > Models > Display Pigtails, Select geometries

    def onDisplayPigtails(self, context):
        for fixture in self.fixtures:
            for obj in fixture.collection.objects:
                if "pigtail" in obj.get("geometry_type", ""):
                    obj.hide_set(not self.display_pigtails)
                    obj.hide_viewport = not self.display_pigtails
                    obj.hide_render = not self.display_pigtails

    def onDisplay2D(self, context):
        bpy.context.window_manager.dmx.pause_render = True # this stops the render loop, to prevent slowness and crashes
        if self.display_2D:
            self.volume_enabled = False
            area  = [area for area in bpy.context.window.screen.areas if area.type == "VIEW_3D"][0]
            with bpy.context.temp_override(
                window=bpy.context.window,
                area=area,
                region=[region for region in area.regions if region.type == 'WINDOW'][0],
                screen=bpy.context.window.screen
            ):
                bpy.ops.view3d.view_axis(type='TOP', align_active=True)
                bpy.ops.view3d.view_selected()
                area.spaces[0].shading.type = 'MATERIAL'

        for fixture in self.fixtures:
            for obj in fixture.collection.objects:
                if obj.get("2d_symbol", None) == "all":
                    obj.hide_set(not self.display_2D)
                    obj.hide_viewport = not self.display_2D
                    obj.hide_render = not self.display_2D
                    if self.display_device_label == "NONE":
                        obj.show_name = False
                    elif self.display_device_label == "NAME":
                        obj.name = f"{fixture.name}"
                        obj.show_name = True
                    elif self.display_device_label == "DMX":
                        obj.name = f"{fixture.universe}.{fixture.address}"
                        obj.show_name = True
                    elif self.display_device_label == "FIXTURE_ID":
                        if fixture.fixture_id:
                            obj.name = f"{fixture.fixture_id}"
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
        bpy.context.window_manager.dmx.pause_render = self.display_2D # re-enable renderer if in 3D

    display_pigtails: BoolProperty(
        name = _("Display Pigtails"),
        default = False,
        update = onDisplayPigtails)

    display_2D: BoolProperty(
        name = _("Display 2D View"),
        default = False,
        update = onDisplay2D)

    display_device_label: EnumProperty(
        name = _("Device Label"),
        default = "NAME",
        items= [
                ("NONE", _("None"), "Do not display any label"),
                ("NAME", _("Name"), "Name"),
                ("DMX", _("DMX"), "DMX Address"),
                ("FIXTURE_ID", _("Fixture ID"), "Fixture ID"),
        ],
        update = onDisplay2D)

    def onSelectGeometries(self, context):
        for fixture in self.fixtures:
            for obj in fixture.collection.objects:
                if obj.get("geometry_root", False):
                    continue
                if obj.get("2d_symbol", None):
                    continue
                if "Target" in obj.name:
                    continue
                obj.hide_select = not self.select_geometries

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
        for fixture in self.fixtures:
            fixture.render(skip_cache=True)

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
        name = _("Disable Overlays"),
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
        if (not self.volume_nodetree):
            self.volume_nodetree = self.volume.data.materials[0].node_tree
        self.volume_nodetree.nodes["Noise Texture"].inputs['Scale'].default_value = self.volume_noise_scale

    volume_noise_scale: FloatProperty(
        name = _("Noise Scale"),
        description=_("Volume Noise Scale"),
        default = 1,
        min = 0,
        max = 100,
        update = onVolumeNoiseScale)

    def onVolumeDensity(self, context):
        if (not self.volume_nodetree):
            self.volume_nodetree = self.volume.data.materials[0].node_tree
        self.volume_nodetree.nodes["Volume Scatter"].inputs['Density'].default_value = self.volume_density

    volume_density: FloatProperty(
        name = _("Density"),
        description=_("Volume Scatter Density"),
        default = 0.1,
        min = 0,
        max = 1,
        update = onVolumeDensity)


    def onMultiplyIntensity(self, context):
        for fixture in self.fixtures:
            fixture.render(skip_cache=True)

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

    #zeroconf - mvr-xchange

    def onZeroconfEnableDiscovery(self, context):
        if self.zeroconf_enabled:
            clients  = bpy.context.window_manager.dmx.mvr_xchange.mvr_xchange_clients
            clients.clear()
            DMX_Log.log.info("Enable mdns discovery")
            DMX_Zeroconf.enable_discovery()
        else:
            DMX_Log.log.info("Disable mdns discovery")
            DMX_Zeroconf.close()
            clients  = bpy.context.window_manager.dmx.mvr_xchange.mvr_xchange_clients
            clients.clear()

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
            DMX_Log.log.debug((selected_client.ip_address, selected_client.station_name))
            DMX_MVR_X_Server.enable() # start the MVR-xchange TCP server for incoming connections
            DMX_MVR_X_Server._instance.server.get_port()
            DMX_Zeroconf.enable_server(selected_client.service_name, DMX_MVR_X_Server.get_port()) # start mdns server and advertise the TCP MVR server
            DMX_MVR_X_Client.join(selected_client) # start MVR-xchange client TCP connection and send MVR_JOIN message
        else:
            DMX_Log.log.info("leave client")
            DMX_MVR_X_Client.leave()
            DMX_Log.log.info("disable client")
            DMX_MVR_X_Client.disable()
            DMX_Log.log.info("disable server")
            DMX_MVR_X_Server.disable()
            DMX_Log.log.info("disable mdns")
            DMX_Zeroconf.disable_server()
            DMX_Log.log.info("disabled all")




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
        if (self.artnet_enabled):
            DMX_ArtNet.enable()
        else:
            DMX_ArtNet.disable()

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
        name = _("Enable MVR-xchange discovery"),
        description=_("Enables MVR-xchange discovery"),
        default = False,
        update = onZeroconfEnableDiscovery
    )

    mvrx_enabled : BoolProperty(
        name = _("Enable MVR-xchange connection"),
        description=_("Connects to MVR-xchange client"),
        default = False,
        update = onMVR_xchange_enable
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
        for fixture in self.fixtures:
            if fixture.collection is None:
                continue
            if fixture.is_selected():
                fixture.setDMX({
                    'Dimmer':int(255*self.programmer_dimmer)
                })
        self.render()

    programmer_dimmer: FloatProperty(
        name = "Programmer Dimmer",
        default = 0,
        min = 0,
        max = 1,
        update = onProgrammerDimmer)

    # # Programmer > Color

    def onProgrammerColor(self, context):
        for fixture in self.fixtures:
            if fixture.collection is None:
                continue
            if fixture.is_selected():
                rgb=[int(255*x) for x in self.programmer_color]
                cmy=rgb_to_cmy(rgb)

                fixture.setDMX({
                    'ColorAdd_R':rgb[0],
                    'ColorAdd_G':rgb[1],
                    'ColorAdd_B':rgb[2],
                    'ColorRGB_Red':rgb[0],
                    'ColorRGB_Green':rgb[1],
                    'ColorRGB_Blue':rgb[2],
                    'ColorSub_C':cmy[0],
                    'ColorSub_M':cmy[1],
                    'ColorSub_Y':cmy[2],

                })
        self.render()

    programmer_color: FloatVectorProperty(
        name = "",
        subtype = "COLOR",
        size = 4,
        min = 0.0,
        max = 1.0,
        default = (1.0,1.0,1.0,1.0),
        update = onProgrammerColor)

    # # Programmer > Pan/Tilt

    def onProgrammerPan(self, context):
        for fixture in self.fixtures:
            if fixture.collection is None:
                continue
            if fixture.is_selected():
                fixture.setDMX({
                    'Pan':int(255*(self.programmer_pan+1)/2)
                })
        self.render()

    programmer_pan: FloatProperty(
        name = "Programmer Pan",
        min = -1.0,
        max = 1.0,
        default = 0.0,
        update = onProgrammerPan)

    def onProgrammerTilt(self, context):
        for fixture in self.fixtures:
            if fixture.collection is None:
                continue
            if fixture.is_selected():
                fixture.setDMX({
                    'Tilt':int(255*(self.programmer_tilt+1)/2)
                })
        self.render()

    def onProgrammerZoom(self, context):
        for fixture in self.fixtures:
            if fixture.collection is None:
                continue
            if fixture.is_selected():
                fixture.setDMX({
                    'Zoom':int(self.programmer_zoom)
                })
        self.render()

    def onProgrammerColorWheel(self, context):
        for fixture in self.fixtures:
            if fixture.collection is None:
                continue
            if fixture.is_selected():
                fixture.setDMX({
                    'Color1':int(self.programmer_color_wheel),
                    'Color2':int(self.programmer_color_wheel),
                    'ColorMacro1':int(self.programmer_color_wheel)
                })
        self.render()

    def onProgrammerGobo(self, context):
        for fixture in self.fixtures:
            if fixture.collection is None:
                continue
            if fixture.is_selected():
                fixture.setDMX({
                    'Gobo1':int(self.programmer_gobo),
                    'Gobo2':int(self.programmer_gobo)
                })
        self.render()

    def onProgrammerGoboIndex(self, context):
        for fixture in self.fixtures:
            if fixture.collection is None:
                continue
            if fixture.is_selected():
                fixture.setDMX({
                    'Gobo1Pos':int(self.programmer_gobo_index),
                    'Gobo1PosRotate':int(self.programmer_gobo_index),
                    'Gobo2Pos':int(self.programmer_gobo_index),
                    'Gobo2PosRotate':int(self.programmer_gobo_index)
                })
        self.render()

    def onProgrammerShutter(self, context):
        for fixture in self.fixtures:
            if fixture.collection is None:
                continue
            if fixture.is_selected():
                fixture.setDMX({
                    'Shutter1':int(self.programmer_shutter)
                })
        self.render()

    programmer_tilt: FloatProperty(
        name = "Programmer Tilt",
        min = -1.0,
        max = 1.0,
        default = 0.0,
        update = onProgrammerTilt)

    programmer_zoom: IntProperty(
        name = "Programmer Zoom",
        min = 1,
        max = 180,
        default = 25,
        update = onProgrammerZoom)

    programmer_color_wheel: IntProperty(
        name = "Programmer Color Wheel",
        min = 0,
        max = 255,
        default = 0,
        update = onProgrammerColorWheel)

    programmer_gobo: IntProperty(
        name = "Programmer Gobo",
        min = 0,
        max = 255,
        default = 0,
        update = onProgrammerGobo)

    programmer_gobo_index: IntProperty(
        name = "Gobo Rotation",
        min = 0,
        max = 255,
        default = 63,
        update = onProgrammerGoboIndex)

    programmer_shutter: IntProperty(
        name = "Programmer Shutter",
        min = 0,
        max = 255,
        default = 0,
        update = onProgrammerShutter)

    # # Programmer > Sync

    def syncProgrammer(self):
        selected = self.selectedFixtures()
        n = len(selected)
        if (n < 1):
            self.programmer_dimmer = 0
            self.programmer_color = (255,255,255,255)
            self.programmer_pan = 0
            self.programmer_tilt = 0
            self.programmer_zoom = 25
            self.programmer_shutter = 0
            self.programmer_color_wheel = 0
            self.programmer_gobo = 0
            self.programmer_gobo_index = 63
            return
        elif (n > 1): return
        active = selected[0]
        data = active.getProgrammerData()
        if 'Dimmer' in data:
            self.programmer_dimmer = data['Dimmer']/255.0
        if 'Shutter1' in data:
            self.programmer_shutter = int(data['Shutter1']/256.0)
        if ('Zoom' in data):
            self.programmer_zoom = int(data['Zoom'])
        if ('Color1' in data):
            self.programmer_color_wheel = int(data['Color1'])
        if ('Color2' in data):
            self.programmer_color_wheel = int(data['Color2'])
        if ('ColorMacro1' in data):
            self.programmer_color_wheel = int(data['ColorMacro1'])
        if ('Gobo1' in data):
            self.programmer_gobo = int(data['Gobo1'])
        if ('Gobo2' in data):
            self.programmer_gobo = int(data['Gobo2'])
        if ('Gobo1Pos' in data):
            self.programmer_gobo_index = int(data['Gobo1Pos'])
        if ('Gobo1PosRotate' in data):
            self.programmer_gobo_index = int(data['Gobo1PosRotate'])
        if ('Gobo2Pos' in data):
            self.programmer_gobo_index = int(data['Gobo2Pos'])
        if ('Gobo2PosRotate' in data):
            self.programmer_gobo_index = int(data['Gobo2PosRotate'])
        if ('ColorAdd_R' in data and 'ColorAdd_G' in data and 'ColorAdd_B' in data):
            rgb = [data['ColorAdd_R'],data['ColorAdd_G'],data['ColorAdd_B']]
            self.programmer_color = (*flatten_color(rgb), 255)
        if ('ColorRGB_Red' in data and 'ColorRGB_Green' in data and 'ColorRGB_Blue' in data):
            rgb = [data['ColorRGB_Red'],data['ColorRGB_Green'],data['ColorRGB_Blue']]
            self.programmer_color = (*flatten_color(rgb), 255)
        if ('ColorSub_C' in data and 'ColorSub_M' in data and 'ColorSub_Y' in data):
            rgb = cmy_to_rgb([data['ColorSub_C'], data['ColorSub_M'], data['ColorSub_Y']])
            self.programmer_color = (1/256*rgb[0], 1/256*rgb[1], 1/256*rgb[2], 255)
        #if ('ColorAdd_C' in data and 'ColorAdd_M' in data and 'ColorAdd_Y' in data):
        #    rgb = cmy_to_rgb([data['ColorAdd_C'], data['ColorAdd_M'], data['ColorAdd_Y']])
        #    self.programmer_color = (1/256*rgb[0], 1/256*rgb[1], 1/256*rgb[2], 255)
        if ('Pan' in data):
            self.programmer_pan = data['Pan']/127.0-1
        if ('Tilt' in data):
            self.programmer_tilt = data['Tilt']/127.0-1


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
    # Kernel Methods
    # # Fixtures
    def addFixture(self, name, profile, universe, address, mode, gel_color, display_beams, add_target, position=None, focus_point=None, uuid = None, fixture_id="", custom_id=0, fixture_id_numeric=0, unit_number=0):
        # TODO: fix order of attributes to match fixture.build()
        dmx = bpy.context.scene.dmx
        new_fixture = dmx.fixtures.add()
        new_fixture.uuid = str(py_uuid.uuid4()) # ensure clean uuid
        try:
            new_fixture.build(name, profile, mode, universe, address, gel_color, display_beams, add_target, position, focus_point, uuid, fixture_id, custom_id, fixture_id_numeric, unit_number)
        except Exception as e:
            DMX_Log.log.error(f"Error while adding fixture {e}")
            dmx.fixtures.remove(len(dmx.fixtures)-1)
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
                if (obj.object):
                    bpy.data.objects.remove(obj.object)
        bpy.data.collections.remove(fixture.collection)
        self.fixtures.remove(self.fixtures.find(fixture.name))

    def getFixture(self, collection):
        for fixture in self.fixtures:
            if (fixture.collection == collection):
                return fixture

    def findFixture(self, object):
        for fixture in self.fixtures:
            if fixture is None:
                continue
            if (object.name in fixture.collection.objects):
                return fixture
        return None

    def findFixtureByUUID(self, uuid):
        for fixture in self.fixtures:
            if fixture is None:
                continue
            if  fixture.uuid == uuid:
                return fixture
        return None

    def selectedFixtures(self):
        selected = []
        for fixture in self.fixtures:
            if fixture.is_selected():
                selected.append(fixture)
        return selected


    def sortedFixtures(self):

        def string_to_pairs(s, pairs=re.compile(r"(\D*)(\d*)").findall):
            return [(text.lower(), int(digits or 0)) for (text, digits) in pairs(s)[:-1]]

        sorting_order = self.fixtures_sorting_order

        if sorting_order == "ADDRESS":
            fixtures = sorted(self.fixtures, key=lambda c: string_to_pairs(str(c.universe*1000+c.address)))
        elif sorting_order == "NAME":
            fixtures = sorted(self.fixtures, key=lambda c: string_to_pairs(c.name))
        elif sorting_order == "FIXTURE_ID":
            fixtures = sorted(self.fixtures, key=lambda c: string_to_pairs(str(c.fixture_id)))
        elif sorting_order == "UNIT_NUMBER":
            fixtures = sorted(self.fixtures, key=lambda c: string_to_pairs(str(c.unit_number)))
        else:
            fixtures = self.fixtures

        return fixtures


    def addMVR(self, file_name):

        bpy.context.window_manager.dmx.pause_render = True # this stops the render loop, to prevent slowness and crashes

        load_mvr(self, file_name)

        bpy.context.window_manager.dmx.pause_render = False # re-enable render loop
        DMX_GDTF.getManufacturerList()
        Profiles.DMX_Fixtures_Local_Profile.loadLocal()

    def clean_up_empty_mvr_collections(self,collections):
        for collection in collections.children:
            if len(collection.all_objects)  == 0:
                collections.children.unlink(collection)


    def export_mvr(self, file_name):

        start_time = time.time()
        bpy.context.window_manager.dmx.pause_render = True # this stops the render loop, to prevent slowness and crashes
        dmx = bpy.context.scene.dmx

        folder_path = os.path.dirname(os.path.realpath(__file__))
        folder_path = os.path.join(folder_path, "assets", "profiles")

        try:
            fixtures_list = []
            mvr = pymvr.GeneralSceneDescriptionWriter()
            pymvr.UserData().to_xml(parent = mvr.xml_root)
            scene = pymvr.SceneElement().to_xml(parent = mvr.xml_root)
            layers = pymvr.LayersElement().to_xml(parent = scene)
            layer = pymvr.Layer(name = "DMX").to_xml(parent = layers)
            child_list = pymvr.ChildList().to_xml(parent = layer)
            for dmx_fixture in dmx.fixtures:
                    fixture_object = dmx_fixture.to_mvr_fixture()
                    focus_point = dmx_fixture.focus_to_mvr_focus_point()
                    if focus_point is not None:
                        child_list.append(focus_point.to_xml())
                    child_list.append(fixture_object.to_xml())
                    file_path = os.path.join(folder_path, fixture_object.gdtf_spec)
                    fixtures_list.append((file_path, fixture_object.gdtf_spec))

            pymvr.AUXData().to_xml(parent = scene)
            mvr.files_list = list(set(fixtures_list))
            mvr.write_mvr(file_name)

        except Exception as e:
            traceback.print_exception(e)
            return SimpleNamespace(ok=False, error=str(e))

        bpy.context.window_manager.dmx.pause_render = False # re-enable render loop
        print("INFO", "MVR scene exported in %.4f sec." % (time.time() - start_time))
        return SimpleNamespace(ok=True)


    def ensureUniverseExists(self, universe):
        # Allocate universes to be able to control devices
        dmx = bpy.context.scene.dmx
        for _ in range(len(dmx.universes), universe+1):
            self.addUniverse()
        self.universes_n = len(self.universes)

    def createMVR_Client(self, station_name = "", station_uuid = "", service_name = "", ip_address = "", port = 0, provider = ""):

        prefs = bpy.context.preferences.addons[__package__].preferences
        application_uuid = prefs.get("application_uuid", str(py_uuid.uuid4()))  # must never be 0
        if application_uuid == station_uuid:
            DMX_Log.log.info("This is myself, do not register as an MVR-xchange provider")
            return

        clients  = bpy.context.window_manager.dmx.mvr_xchange.mvr_xchange_clients
        for client in clients:
            if client.station_uuid == station_uuid:
                return # client already in the list

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

    def removeMVR_Client(self, station_name, station_uuid, service_name, ip_addres, port):
        clients  = bpy.context.window_manager.dmx.mvr_xchange.mvr_xchange_clients
        for client in clients:
            if client.station_uuid == station_uuid:
                clients.remove(client)
                break

    def updateMVR_Client(self, station_uuid, station_name=None, service_name = None, ip_address=None, port=None, provider=None):
        clients  = bpy.context.window_manager.dmx.mvr_xchange.mvr_xchange_clients
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
            self.createMVR_Client(station_name, station_uuid, service_name, ip_address, port)

    def createMVR_Commits(self, commits, station_uuid):
        clients  = bpy.context.window_manager.dmx.mvr_xchange.mvr_xchange_clients
        for client in clients:
            if client.station_uuid == station_uuid:
                #client.commits.clear()

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

    def fetched_mvr_downloaded_file(self, commit):
        clients  = bpy.context.window_manager.dmx.mvr_xchange.mvr_xchange_clients
        now = int(datetime.now().timestamp())
        for client in clients:
            if client.station_uuid == commit.station_uuid:
                for c_commit in client.commits:
                    if c_commit.commit_uuid == commit.commit_uuid:
                        c_commit.timestamp_saved = now


    # # Groups

    def createGroup(self, name):
        dmx = bpy.context.scene.dmx
        group = dmx.groups.add()
        group.name = name
        group.uuid = str(py_uuid.uuid4()) #ensure clean uuid
        group.update()
        DMX_Log.log.info(group.dump)
        if (not len(group.dump)):
            DMX_Log.log.info("DMX Group: no fixture selected!")
            dmx.groups.remove(len(dmx.groups)-1)
            return False
        return True

    def updateGroup(self, i):
        dmx = bpy.context.scene.dmx
        if (i >= 0 and i < len(self.groups)):
            dmx.groups[i].update()

    def renameGroup(self, i, name):
        dmx = bpy.context.scene.dmx
        if (i >= 0 and i < len(self.groups)):
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
            self.disable_overlays = False # overlay must be enabled
            for fixture in self.fixtures:
                selected = False
                if fixture is None:
                    continue
                if fixture.collection is None:
                    continue
                if fixture.is_selected():
                    selected = True
                for light in fixture.lights:
                    light.object.data.show_cone = selected

        elif self.volume_preview == "ALL":
            self.disable_overlays = False # overlay must be enabled
            for fixture in self.fixtures:
                for light in fixture.lights:
                    light.object.data.show_cone = True
        else:
            for fixture in self.fixtures:
                for light in fixture.lights:
                    light.object.data.show_cone = False

    # # Universes

    def addUniverse(self):
        id = len(self.universes)
        DMX_Universe.add(self, id, "Universe %d"%id)

    def removeUniverse(self, i):
        DMX_Universe.remove(self, i)

    # # Render

    def render(self):
        if bpy.context.scene.tool_settings.use_keyframe_insert_auto:
            #make the frame the same for all fixtures
            current_frame = bpy.data.scenes[0].frame_current
        else:
            current_frame = None

        for fixture in self.fixtures:
            fixture.render(current_frame=current_frame)
        for tracker in self.trackers:
            tracker.render(current_frame=current_frame)

    def set_fixtures_filter(self, fixtures_filter):
        DMX.fixtures_filter = fixtures_filter

    def update_laser_collision_collect(self):
        for fixture in self.fixtures:
            for nodes in fixture.geometry_nodes:
                collection_info = nodes.node.nodes["Collection Info"]
                collection = bpy.context.window_manager.dmx.collections_list
                collection_info.inputs[0].default_value = collection

