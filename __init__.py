bl_info = {
    "name": "DMX",
    "description": "DMX visualization and programming, with GDTF/MVR and Network support",
    "author": "open-stage",
    "version": (1, 0, 4),
    "blender": (3, 0, 0),
    "location": "3D View > DMX",
    "doc_url": "https://github.com/open-stage/blender-dmx/wiki",
    "tracker_url": "https://github.com/open-stage/blender-dmx/issues",
    "category": "Lighting",
}

import sys
import bpy
import os
import atexit
from operator import attrgetter
from threading import Timer
import time
import json
import uuid as py_uuid
import re

from dmx.pymvr import GeneralSceneDescription
from dmx.mvr import extract_mvr_textures, process_mvr_child_list

from dmx.fixture import *
from dmx.group import *
from dmx.universe import *
from dmx.data import *
from dmx.gdtf import *
from dmx.artnet import *
from dmx.acn import DMX_sACN
from dmx.network import *
from dmx.logging import *

from dmx.panels.setup import *
from dmx.panels.dmx import *
from dmx.panels.fixtures import *
from dmx.panels.groups import *
from dmx.panels.programmer import *
import dmx.panels.profiles as Profiles

from dmx.preferences import DMX_Preferences
from dmx.group import FixtureGroup
from dmx.osc_utils import DMX_OSC_Templates
from dmx.osc import DMX_OSC

from dmx.util import rgb_to_cmy, xyY2rgbaa, ShowMessageBox
from dmx.mvr_objects import DMX_MVR_Object 

from bpy.props import (BoolProperty,
                       StringProperty,
                       IntProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       PointerProperty,
                       CollectionProperty)

from bpy.types import (PropertyGroup,
                       Object,
                       Collection,
                       NodeTree)


class DMX_TempData(PropertyGroup):

    pause_render: BoolProperty(
        description="The renderer is paused during MVR import and in 2D view. This checkbox allows to re-enable it in case of some failure during import, which would leave it paused",
        name = "Pause renderer",
        default = False)

    manufacturers: CollectionProperty(
            name = "Manufacturers",
            type=PropertyGroup
            )

    imports: PointerProperty(
            name = "Imports",
            type=Profiles.DMX_Fixtures_Imports
            )

    aditive_selection: BoolProperty(
        name = "Add to selection",
        description="When selecting a group, add to existing selection",
        default = True)

class DMX(PropertyGroup):

    # Base classes to be registered
    # These should be registered before the DMX class, so it can register properly

    classes_base = (DMX_Param,
                    DMX_Model_Param,
                    DMX_Fixture_Object,
                    DMX_Emitter_Material,
                    DMX_Fixture_Channel,
                    DMX_Fixture,
                    DMX_MVR_Object,
                    DMX_Group,
                    DMX_Universe,
                    DMX_Value,
                    DMX_PT_Setup,
                    DMX_Preferences)

    # Classes to be registered
    # The registration is done in two steps. The second only runs
    # after the user requests to setup the addon.

    classes_setup = (DMX_OT_Setup_NewShow,)

    classes = ( DMX_UL_Universe,
                DMX_MT_Universe,
                DMX_PT_DMX,
                DMX_PT_DMX_Universes,
                DMX_PT_DMX_ArtNet,
                DMX_PT_DMX_LiveDMX,
                DMX_OT_Setup_Volume_Create,
                DMX_PT_Setup_Background,
                DMX_PT_Setup_Volume,
                DMX_PT_Setup_Debug,
                DMX_MT_Fixture,
                DMX_MT_Fixture_Manufacturers,
                DMX_MT_Fixture_Profiles,
                DMX_MT_Fixture_Mode,
                DMX_OT_Fixture_Item,
                DMX_OT_Fixture_Profiles,
                DMX_OT_Fixture_Mode,
                DMX_UL_LiveDMX_items,
                DMX_OT_Fixture_Add,
                DMX_OT_Fixture_Edit,
                DMX_OT_Fixture_Remove,
                DMX_OT_Fixture_Import_GDTF,
                DMX_OT_Fixture_Import_MVR,
                DMX_PT_Fixtures,
                DMX_UL_Group,
                DMX_MT_Group,
                DMX_OT_Group_Create,
                DMX_OT_Group_Update,
                DMX_OT_Group_Rename,
                DMX_OT_Group_Remove,
                DMX_PT_Groups,
                DMX_OT_Programmer_DeselectAll,
                DMX_OT_Programmer_SelectAll,
                DMX_OT_Programmer_SelectInvert,
                DMX_OT_Programmer_SelectEveryOther,
                DMX_OT_Programmer_Clear,
                DMX_OT_Programmer_SelectBodies,
                DMX_OT_Programmer_SelectTargets,
                DMX_OT_Programmer_SelectCamera,
                DMX_OT_Programmer_TargetsToZero,
                DMX_PT_Fixture_Columns_Setup,
                DMX_OT_Programmer_Set_Ignore_Movement,
                DMX_OT_Programmer_Unset_Ignore_Movement,
                DMX_PT_DMX_OSC,
                DMX_OT_Fixture_ForceRemove,
                DMX_OT_Fixture_SelectNext,
                DMX_OT_Fixture_SelectPrevious,
                DMX_PT_Programmer)

    linkedToFile = False
    _keymaps = []

    def register():
        for cls in DMX.classes_setup:
            bpy.utils.register_class(cls)

        # register key shortcuts
        wm = bpy.context.window_manager
        km = wm.keyconfigs.addon.keymaps.new(name='3D View Generic', space_type='VIEW_3D')
        kmi = km.keymap_items.new('dmx.fixture_next', 'RIGHT_ARROW', 'PRESS', ctrl=True)
        DMX._keymaps.append((km, kmi))
        kmi = km.keymap_items.new('dmx.fixture_previous', 'LEFT_ARROW', 'PRESS', ctrl=True)
        DMX._keymaps.append((km, kmi))

    def unregister():
        # unregister keymaps
        for km, kmi in DMX._keymaps: km.keymap_items.remove(kmi)
        DMX._keymaps.clear()

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
        name = "Fixture ID",
        default = True)

    column_unit_number: BoolProperty(
        name = "Unit Number",
        default = False)

    column_custom_id: BoolProperty(
        name = "Custom ID",
        default = False)

    column_fixture_id_numeric: BoolProperty(
        name = "Fixture ID Numeric",
        default = False)

    column_dmx_address: BoolProperty(
        name = "DMX Address",
        default = True)

    column_fixture_remove: BoolProperty(
        name = "Remove Fixture",
        default = False)

    collection: PointerProperty(
        name = "DMX Collection",
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
        type = DMX_Fixture)

    groups: CollectionProperty(
        name = "DMX Groups",
        type = DMX_Group)

    universes : CollectionProperty(
        name = "DMX Groups",
        type = DMX_Universe)

    mvr_objects: CollectionProperty(
        name = "MVR Objects",
        type = DMX_MVR_Object)

    def prepare_empty_buffer(self, context):
        # Clear the buffer on change of every protocol
        DMX_Data.prepare_empty_buffer()

    selected_live_dmx_source : EnumProperty(
        name = "DMX Source",
        description="The network protocol for which to show live DMX values",
        default = "BLENDERDMX",
        items = network_options_list,
        update = prepare_empty_buffer,
    )
    selected_live_dmx_universe: IntProperty(
        min = 0,
        update = prepare_empty_buffer,
    )

    dmx_values: CollectionProperty(
        name = "DMX buffer",
        type = DMX_Value
    )

    dmx_value_index: IntProperty() # Just a fake value, we need as the live DMX UI Panel requires it

    data_version: IntProperty(
            name = "BlenderDMX data version, bump when changing RNA structure and provide migration script",
            default = 4,
            )

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
        print("DMX", "Linking to file")

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

        print("DMX", "\tDMX collection:", self.collection)
        print("DMX", "\tDMX_Volume object:", self.volume)

        if (self.collection):
            # Second step registration (if not already registered)
            if (not DMX.linkedToFile):
                for cls in self.classes:
                    bpy.utils.register_class(cls)
                for cls in self.classes_setup:
                    bpy.utils.unregister_class(cls)
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
                return print("No network card detected")

        # Reset ArtNet status
        dmx = bpy.context.scene.dmx
        if (dmx.artnet_enabled and dmx.artnet_status != 'online'):
            dmx.artnet_enabled = False
            dmx.artnet_status = 'offline'
        if (dmx.sacn_enabled and dmx.artnet_status != 'online'):
            dmx.sacn_enabled = False
            dmx.artnet_status = 'offline'
        if dmx.osc_enabled:
            dmx.osc_enabled = False

        # Rebuild group runtime dictionary (evaluating if this is gonna stay here)
        #DMX_Group.runtime = {}
        #for group in self.groups:
        #    group.rebuild()

        self.migrations()

    # Unlink Add-on from file
    # This is only called when the DMX collection is externally removed
    def unlinkFile(self):
        print("DMX", "Unlinking from file")

        # Unlink pointer properties
        self.collection  = None
        self.volume = None

        # Second step unregistration
        if (DMX.linkedToFile):
            for cls in self.classes_setup:
                bpy.utils.register_class(cls)
            for cls in self.classes:
                bpy.utils.unregister_class(cls)
            DMX.linkedToFile = False

    # Callback Properties

    # # Setup > Background > Color

    def migrations(self):
        """Provide migration scripts when bumping the data_version"""
        file_data_version = 1 # default data version before we started setting it up

        if ("DMX_DataVersion" in self.collection):
            file_data_version = self.collection["DMX_DataVersion"]
        print("Data version", file_data_version)

        if file_data_version < 2: # migration for sw. version 0.5 → 1.0
            print("Running migration 1→2")
            dmx = bpy.context.scene.dmx

            for fixture in dmx.fixtures:
                for obj in fixture.objects:
                    if any(obj.name == name for name in ['Body', 'Base']):
                        print("updating", obj.name)
                        obj.name = 'Root'

        if file_data_version < 3:
            print("Running migration 2→3")
            dmx = bpy.context.scene.dmx
            print("Add UUID to fixtures")
            for fixture in dmx.fixtures:
                if "uuid" not in fixture:
                    print("Adding UUID to", fixture.name)
                    fixture.uuid = str(py_uuid.uuid4())
            print("Add UUID to groups, convert groups to json")
            for group in dmx.groups:
                if "uuid" not in group:
                    print("Adding UUID to", group.name)
                    group.uuid = str(py_uuid.uuid4())
                print("Migrating group")
                group.dump = json.dumps([x[1:-1] for x in group.dump.strip('[]').split(', ')])

        if file_data_version < 4:
            print("Running migration 3→4")
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

            print("Ensure unique fixture UUID")
            duplicates = []
            for fixture in dmx.fixtures:
                duplicates = findFixtureUuidDuplicates(fixture.uuid)
                if len(duplicates) > 1:
                    for fixture in duplicates:
                        u = fixture.uuid
                        fixture.uuid = str(py_uuid.uuid4())
                        print("Updating fixture", fixture.name, u, fixture.uuid)

            print("Ensure unique group UUID")
            duplicates = []
            for group in dmx.groups:
                duplicates = findGroupUuidDuplicates(group.uuid)
                if len(duplicates) > 1:
                    for group in duplicates:
                        u = group.uuid
                        group.uuid = str(py_uuid.uuid4())
                        print("Updating group", group.name, u, group.uuid)

            print("Convert groups from fixture names to UUIDs")
            for group in dmx.groups:
                grouped_fixtures = json.loads(group.dump)
                uuid_list = []
                for g_fixture in grouped_fixtures:
                    if g_fixture in dmx.fixtures:
                        fixture = dmx.fixtures[g_fixture]
                        if fixture is not None:
                            uuid_list.append(fixture.uuid)
                group.dump = json.dumps(uuid_list)
            print("Groups updated")

        print("Migration done")

        # add here another if statement for next migration condition... like:
        # if file_data_version < 5: #...

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
                area.spaces[0].shading.type = 'SOLID'

        for fixture in self.fixtures:
            for obj in fixture.collection.objects:
                if obj.get("2d_symbol", None) == "all":
                    obj.hide_set(not self.display_2D)
                else:
                    obj.hide_set(self.display_2D)
                    if "pigtail" in obj.get("geometry_type", ""):
                        obj.hide_set(not self.display_pigtails)
        bpy.context.window_manager.dmx.pause_render = self.display_2D # re-enable renderer if in 3D

    display_pigtails: BoolProperty(
        name = "Display Pigtails",
        default = False,
        update = onDisplayPigtails)

    display_2D: BoolProperty(
        name = "Display 2D VIew",
        default = False,
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
        name = "Allow Selecting Geometries",
        default = False,
        update = onSelectGeometries)

    # # Logging levels

    def onLoggingLevel(self, context):
        DMX_Log.log.setLevel(self.logging_level)

    logging_level: bpy.props.EnumProperty(
        name= "Logging Level",
        description= "logging level",
        default = "ERROR",
        items= [
                ('CRITICAL', "Critical", "", "TOOL_SETTINGS", 0),
                ('ERROR', "Error", "", 'ERROR', 1),
                ('WARNING', "Warning", "", "CANCEL", 2),
                ('DEBUG', "Debug", "", "OUTLINER_OB_LIGHT",3),
                ('INFO', "Info", "", "INFO", 4),
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

    volume_preview: bpy.props.EnumProperty(
        name= "Simple beam",
        description= "Display 'fake' beam cone",
        default = "NONE",
        items= [
                ("NONE", "None", "Cone not displayed"),
                ("SELECTED", "Selected fixtures", "Shift select multiple"),
                ("ALL", "All fixtures", "All fixtures"),
        ],
        update = onVolumePreview
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
        name = "Disable Overlays",
        default = False,
        update = onDisableOverlays)

    # # Setup > Volume > Enabled

    def onVolumeEnabled(self, context):
        if self.volume is not None:
            self.volume.hide_set(not self.volume_enabled)

    volume_enabled: BoolProperty(
        name = "Enable Volume Scatter",
        default = True,
        update = onVolumeEnabled)

    # #  Setup > Volume > Density

    def onVolumeDensity(self, context):
        if (not self.volume_nodetree):
            self.volume_nodetree = self.volume.data.materials[0].node_tree
        self.volume_nodetree.nodes[1].inputs['Density'].default_value = self.volume_density

    volume_density: FloatProperty(
        name = "Density",
        description="Volume Scatter Density",
        default = 1,
        min = 0,
        max = 1,
        update = onVolumeDensity)

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
        name = "Number of universes",
        description="The number of universes set on the panel",
        default = 0,
        min = 0,
        soft_min = 1,
        max = 511,
        update = onUniverseN)

    # # DMX > Universes > List Index

    universe_list_i : IntProperty(
        name = "Universe List Item",
        description="The selected element on the universe list",
        default = 0
        )

    # # DMX > ArtNet > Network Cards

    artnet_ipaddr : EnumProperty(
        name = "IPv4 Address for ArtNet signal",
        description="The network card/interface to listen for ArtNet DMX data",
        items = DMX_Network.cards
    )

    # OSC functionality

    def onOscEnable(self, context):
        if self.osc_enabled:
            DMX_OSC.enable()
            DMX_OSC_Templates.read()
        else:
            DMX_OSC.disable()

    # # DMX > sACN > Enable
    def onsACNEnable(self, context):
        dmx = bpy.context.scene.dmx
        if (self.sacn_enabled):
            DMX_sACN.enable()
            dmx.artnet_status = 'online'
            
        else:
            DMX_sACN.disable()
            dmx.artnet_status = 'online'
            
    # # DMX > ArtNet > Enable

    def onArtNetEnable(self, context):
        if (self.artnet_enabled):
            DMX_ArtNet.enable()
        else:
            DMX_ArtNet.disable()

    artnet_enabled : BoolProperty(
        name = "Enable Art-Net Input",
        description="Enables the input of DMX data throught Art-Net on the selected network interface",
        default = False,
        update = onArtNetEnable
    )

    sacn_enabled : BoolProperty(
        name = "Enable sACN Input",
        description="Enables the input of DMX data throught sACN on all detected network interfaces",
        default = False,
        update = onsACNEnable
    )

    osc_enabled : BoolProperty(
        name = "Enable OSC Output",
        description="Enables Open Sound Control protocol to send fixture selection to a console",
        default = False,
        update = onOscEnable
    )

    osc_target_address : StringProperty(
        name = "Target address",
        description="Address of the host where you want to send the OSC signal. Address ending on .255 is a broadcast address to all hosts on the network",
        default="0.0.0.0"
    )

    osc_target_port : IntProperty(
        name = "Target port",
        description="Port number of the host where you want to send the OSC signal",
        default=42000
    )
    # # DMX > ArtNet > Status

    artnet_status : EnumProperty(
        name = "Art-Net Status",
        items = DMX_ArtNet.status()
    )

    # # Groups > List

    def onGroupList(self, context):
        self.groups[self.group_list_i].select()

    group_list_i : IntProperty(
        name = "Group List i",
        description="The selected element on the group list",
        default = 0,
        update = onGroupList
        )

    # # Programmer > Dimmer

    def onProgrammerDimmer(self, context):
        bpy.app.handlers.depsgraph_update_post.clear()
        for fixture in self.fixtures:
            if fixture.collection is None:
                continue
            for obj in fixture.collection.objects:
                if (obj in bpy.context.selected_objects):
                    fixture.setDMX({
                        'Dimmer':int(255*self.programmer_dimmer)
                    })
        self.render()
        bpy.app.handlers.depsgraph_update_post.append(onDepsgraph)

    programmer_dimmer: FloatProperty(
        name = "Programmer Dimmer",
        default = 0,
        min = 0,
        max = 1,
        update = onProgrammerDimmer)

    # # Programmer > Color

    def onProgrammerColor(self, context):
        

        bpy.app.handlers.depsgraph_update_post.clear()
        for fixture in self.fixtures:
            if fixture.collection is None:
                continue
            for obj in fixture.collection.objects:
                if (obj in bpy.context.selected_objects):
                    rgb=[int(255*x) for x in self.programmer_color]
                    cmy=rgb_to_cmy(rgb)

                    fixture.setDMX({
                        'ColorAdd_R':rgb[0],
                        'ColorAdd_G':rgb[1],
                        'ColorAdd_B':rgb[2],
                        'ColorSub_C':cmy[0],
                        'ColorSub_M':cmy[1],
                        'ColorSub_Y':cmy[2]
                    })
        self.render()
        bpy.app.handlers.depsgraph_update_post.append(onDepsgraph)

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
        bpy.app.handlers.depsgraph_update_post.clear()
        for fixture in self.fixtures:
            if fixture.collection is None:
                continue
            for obj in fixture.collection.objects:
                if (obj in bpy.context.selected_objects):
                    fixture.setDMX({
                        'Pan':int(255*(self.programmer_pan+1)/2)
                    })
        self.render()
        bpy.app.handlers.depsgraph_update_post.append(onDepsgraph)

    programmer_pan: FloatProperty(
        name = "Programmer Pan",
        min = -1.0,
        max = 1.0,
        default = 0.0,
        update = onProgrammerPan)

    def onProgrammerTilt(self, context):
        bpy.app.handlers.depsgraph_update_post.clear()
        for fixture in self.fixtures:
            if fixture.collection is None:
                continue
            for obj in fixture.collection.objects:
                if (obj in bpy.context.selected_objects):
                    fixture.setDMX({
                        'Tilt':int(255*(self.programmer_tilt+1)/2)
                    })
        self.render()
        bpy.app.handlers.depsgraph_update_post.append(onDepsgraph)

    def onProgrammerZoom(self, context):
        bpy.app.handlers.depsgraph_update_post.clear()
        for fixture in self.fixtures:
            if fixture.collection is None:
                continue
            for obj in fixture.collection.objects:
                if (obj in bpy.context.selected_objects):
                    fixture.setDMX({
                        'Zoom':int((255/180)*self.programmer_zoom)
                    })
        self.render()
        bpy.app.handlers.depsgraph_update_post.append(onDepsgraph)

    def onProgrammerShutter(self, context):
        bpy.app.handlers.depsgraph_update_post.clear()
        for fixture in self.fixtures:
            if fixture.collection is None:
                continue
            for obj in fixture.collection.objects:
                if (obj in bpy.context.selected_objects):
                    fixture.setDMX({
                        'Shutter1':int(self.programmer_shutter)
                    })
        self.render()
        bpy.app.handlers.depsgraph_update_post.append(onDepsgraph)

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

    programmer_shutter: IntProperty(
        name = "Programmer Shutter",
        min = 0,
        max = 255,
        default = 0,
        update = onProgrammerShutter)
    # # Programmer > Sync

    def syncProgrammer(self):
        n = len(bpy.context.selected_objects)
        if (n < 1):
            self.programmer_dimmer = 0
            self.programmer_color = (255,255,255,255)
            self.programmer_pan = 0
            self.programmer_tilt = 0
            self.programmer_zoom = 25
            self.programmer_shutter = 0
            return
        elif (n > 1): return
        if (not bpy.context.active_object): return
        active = self.findFixture(bpy.context.active_object)
        if (not active): return
        data = active.getProgrammerData()
        if 'Dimmer' in data:
            self.programmer_dimmer = data['Dimmer']/256.0
        if 'Shutter1' in data:
            self.programmer_shutter = int(data['Shutter1']/256.0)
        if ('Zoom' in data):
            self.programmer_zoom = int(data['Zoom']/256.0)
        if ('ColorAdd_R' in data and 'ColorAdd_G' in data and 'ColorAdd_B' in data):
            self.programmer_color = (data['ColorAdd_R'],data['ColorAdd_G'],data['ColorAdd_B'],255)
        if ('Pan' in data):
            self.programmer_pan = data['Pan']/127.0-1
        if ('Tilt' in data):
            self.programmer_tilt = data['Tilt']/127.0-1


    fixtures_sorting_order: bpy.props.EnumProperty(
        name= "Sort by",
        description= "Fixture sorting order",
        default = "ADDRESS",
        items= [
                ("ADDRESS", "DMX Address", "", "", 0),
                ("NAME", "Name", "", "", 1),
                ("FIXTURE_ID", "Fixture ID", "", "", 2),
                ("UNIT_NUMBER", "Unit Number", "", "", 3),
        ],
        )
    # Kernel Methods
    # # Fixtures
    def addFixture(self, name, profile, universe, address, mode, gel_color, display_beams, add_target, position=None, focus_point=None, uuid = None, fixture_id="", custom_id=0, fixture_id_numeric=0, unit_number=0):
        # TODO: fix order of attributes to match fixture.build()
        bpy.app.handlers.depsgraph_update_post.clear()
        dmx = bpy.context.scene.dmx
        new_fixture = dmx.fixtures.add()
        new_fixture.uuid = str(py_uuid.uuid4()) # ensure clean uuid
        try:
            new_fixture.build(name, profile, mode, universe, address, gel_color, display_beams, add_target, position, focus_point, uuid, fixture_id, custom_id, fixture_id_numeric, unit_number)
        except Exception as e:
            print("Error while adding fixture", e)
            dmx.fixtures.remove(len(dmx.fixtures)-1)
            ShowMessageBox(
                f"{e}",
                "Error while adding a fixture, see console for more details",
                "ERROR",
            )
        bpy.app.handlers.depsgraph_update_post.append(onDepsgraph)

    def removeFixture(self, fixture):
        self.remove_fixture_from_groups(fixture.uuid)
        for obj in fixture.collection.objects:
            bpy.data.objects.remove(obj)
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
            for obj in fixture.collection.objects:
                if (obj in bpy.context.selected_objects):
                    selected.append(fixture)
                    break
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

        bpy.app.handlers.depsgraph_update_post.clear()

        star_time = time.time()
        bpy.context.window_manager.dmx.pause_render = True # this stops the render loop, to prevent slowness and crashes
        already_extracted_files = {}
        mvr_scene = GeneralSceneDescription(file_name)
        current_path = os.path.dirname(os.path.realpath(__file__))
        extract_to_folder_path = os.path.join(current_path, "assets", "profiles")
        media_folder_path = os.path.join(current_path, "assets", "models", "mvr")
        extract_mvr_textures(mvr_scene, media_folder_path)

        for layer_index, layer in enumerate(mvr_scene.layers):

            layer_collection_name = layer.name or f"Layer {layer_index}"
            if layer_collection_name in bpy.context.scene.collection.children:
                layer_collection = bpy.context.scene.collection.children[layer_collection_name]
            else:
                layer_collection = bpy.data.collections.new(layer.name or f"Layer {layer_index}")
                bpy.context.scene.collection.children.link(layer_collection)

            g_name = layer.name or "Layer"
            g_name = f"{g_name} {layer_index}"
            fixture_group = FixtureGroup(g_name, layer.uuid)

            process_mvr_child_list(
                self,
                layer.child_list,
                layer_index,
                extract_to_folder_path,
                mvr_scene,
                already_extracted_files,
                layer_collection,
                fixture_group
            )
            self.clean_up_empty_mvr_collections(layer_collection)
            if len(layer_collection.all_objects) == 0:
                bpy.context.scene.collection.children.unlink(layer_collection)

        bpy.context.window_manager.dmx.pause_render = False # re-enable render loop
        bpy.app.handlers.depsgraph_update_post.append(onDepsgraph)
        print("MVR scene loaded in %.4f sec." % (time.time() - star_time))

    def clean_up_empty_mvr_collections(self,collections):
        for collection in collections.children:
            if len(collection.all_objects)  == 0:
                collections.children.unlink(collection)

    def ensureUniverseExists(self, universe):
        # Allocate universes to be able to control devices
        dmx = bpy.context.scene.dmx
        for _ in range(len(dmx.universes), universe+1):
            self.addUniverse()
        self.universes_n = len(self.universes)

    # # Groups

    def createGroup(self, name):
        dmx = bpy.context.scene.dmx
        group = dmx.groups.add()
        group.name = name
        group.uuid = str(py_uuid.uuid4()) #ensure clean uuid
        group.update()
        print(group.dump)
        if (not len(group.dump)):
            print("DMX Group: no fixture selected!")
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
                for obj in fixture.collection.objects:
                    if obj in bpy.context.selected_objects:
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
        DMX_Universe.add(self, id, "DMX %d"%id)

    def removeUniverse(self, i):
        DMX_Universe.remove(self, i)

    # # Render

    def render(self):
        for fixture in self.fixtures:
            fixture.render()


# Handlers #


def onDepsgraph(scene):
    scene = bpy.context.scene
    depsgraph = bpy.context.evaluated_depsgraph_get()

    for update in depsgraph.updates:
        obj = update.id.evaluated_get(depsgraph)
        # Selection changed, sync programmer
        if (obj.rna_type.name == 'Scene'):
            if "dmx" in scene: # dmx may not be in scene during installation
                scene.dmx.syncProgrammer()
            continue
        # Fixture updated
        found = False
        for fixture in scene.dmx.fixtures:
            for f_obj in fixture.objects:
                if (obj.name == f_obj.object.name):
                    fixture.onDepsgraphUpdate()
                    found = True
                    break
            if found: break


@bpy.app.handlers.persistent
def onLoadFile(scene):
    if ('DMX' in bpy.data.scenes['Scene'].collection.children):
        print("DMX", "File contains DMX show, linking...")
        bpy.context.scene.dmx.linkFile()
    else:
        bpy.context.scene.dmx.unlinkFile()

    # Selection callback
    handle = object()
    subscribe_to = bpy.types.LayerObjects, "active"
    bpy.msgbus.subscribe_rna(
        key=subscribe_to,
        owner=handle,
        args=(None,),
        notify=onActiveChanged,
        options={"PERSISTENT",}
    )

    bpy.app.handlers.depsgraph_update_post.append(onDepsgraph)

    # Stop ArtNet
    DMX_ArtNet.disable()
    DMX_sACN.disable()
    DMX_OSC.disable()

@bpy.app.handlers.persistent
def onUndo(scene):
    if (not scene.dmx.collection and DMX.linkedToFile):
        scene.dmx.unlinkFile()

# Callbacks #

def onActiveChanged(*args):
    dmx = bpy.context.scene.dmx
    if dmx.volume_preview == "SELECTED":
        dmx.updatePreviewVolume()

    if dmx.display_2D:
        selected = False
        for fixture in dmx.fixtures:
            if bpy.context.active_object is not None and bpy.context.active_object.name in fixture.collection.objects:
                selected = True
                fixture.select()
            else:
                fixture.unselect()
        if selected:
            bpy.context.window_manager.dmx.pause_render = False
        else:
            bpy.context.window_manager.dmx.pause_render = True


#
# Hot-Reload
#

def clean_module_imports():
    modules = dict(sys.modules)
    for name in modules.keys():
        if (name == __name__):
            continue
        if name.startswith(__name__):
            del sys.modules[name]
    return None 

#
# Blender Add-On
#

def onRegister():
    onLoadFile(None)

def register():

    # Register Base Classes
    for cls in DMX.classes_base:
        bpy.utils.register_class(cls)

    # Register addon main class
    bpy.utils.register_class(DMX)
    bpy.types.Scene.dmx = PointerProperty(type=DMX)


    for cls in Profiles.classes:
        bpy.utils.register_class(cls)

    bpy.utils.register_class(DMX_TempData)
    bpy.types.WindowManager.dmx = PointerProperty(type=DMX_TempData)

    # Append handlers
    bpy.app.handlers.load_post.append(onLoadFile)
    bpy.app.handlers.undo_post.append(onUndo)

    # since 2.91.0 unregister is called also on Blender exit
    if bpy.app.version <= (2, 91, 0):
        atexit.register(DMX_ArtNet.disable)
        atexit.register(DMX_sACN.disable)
        atexit.register(DMX_OSC.disable)
    
    Timer(1, onRegister, ()).start()

def unregister():
    # Stop ArtNet
    DMX_ArtNet.disable()
    DMX_sACN.disable()
    DMX_OSC.disable()

    try:
        for cls in Profiles.classes:
            bpy.utils.unregister_class(cls)

        # Unregister Base Classes
        for cls in DMX.classes_base:
            bpy.utils.unregister_class(cls)

        # Unregister addon main class
        bpy.utils.unregister_class(DMX_TempData)
        bpy.utils.unregister_class(DMX)

    except Exception as e:
        print(e)

    # Append handlers
    bpy.app.handlers.load_post.clear()
    bpy.app.handlers.undo_post.clear()

    clean_module_imports()

if __name__ == "__main__":
    register()
