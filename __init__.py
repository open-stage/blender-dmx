bl_info = {
    "name": "DMX",
    "description": "DMX Visualization, with GDTF and ArtNet support.",
    "author": "hugoaboud",
    "version": (0, 5, 0),
    "blender": (2, 90, 0),
    "location": "3D View > DMX",
    "warning": "", # used for warning icon and text in addons panel
    "wiki_url": "http://www.github.com/hugoaboud/blenderDMX/wiki",
    "tracker_url": "",
    "category": "Lighting"
}

import sys
import bpy
import os
import atexit

from dmx.fixture import *
from dmx.group import *
from dmx.universe import *
from dmx.data import *
from dmx.artnet import *
from dmx.acn import *
from dmx.network import *

from dmx.panels.setup import *
from dmx.panels.dmx import *
from dmx.panels.fixtures import *
from dmx.panels.groups import *
from dmx.panels.programmer import *
from dmx.util import rgb_to_cmy

from bpy.props import (BoolProperty,
                       IntProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       PointerProperty,
                       CollectionProperty)

from bpy.types import (PropertyGroup,
                       Object,
                       Collection,
                       NodeTree)

class DMX(PropertyGroup):

    # Base classes to be registered
    # These should be registered before the DMX class, so it can register properly

    classes_base = (DMX_Param,
                    DMX_Model_Param,
                    DMX_Fixture_Object,
                    DMX_Fixture_Channel,
                    DMX_Fixture,
                    DMX_Group,
                    DMX_Universe,
                    DMX_PT_Setup)

    # Classes to be registered
    # The registration is done in two steps. The second only runs
    # after the user requests to setup the addon.

    classes_setup = (DMX_OT_Setup_NewShow,)

    classes = ( DMX_UL_Universe,
                DMX_MT_Universe,
                DMX_MT_NetworkCard,
                DMX_OT_Network_Card,
                DMX_PT_DMX,
                DMX_PT_DMX_Universes,
                DMX_PT_DMX_ArtNet,
                DMX_OT_Setup_Volume_Create,
                DMX_PT_Setup_Background,
                DMX_PT_Setup_Volume,
                DMX_PT_Setup_Models,
                DMX_MT_Fixture,
                DMX_MT_Fixture_Manufacturers,
                DMX_MT_Fixture_Profiles,
                DMX_MT_Fixture_Mode,
                DMX_OT_Fixture_Item,
                DMX_OT_Fixture_Profiles,
                DMX_OT_Fixture_Mode,
                DMX_OT_Fixture_Add,
                DMX_OT_Fixture_Edit,
                DMX_OT_Fixture_Remove,
                DMX_OT_Fixture_Import_GDTF,
                DMX_PT_Fixtures,
                DMX_UL_Group,
                DMX_MT_Group,
                DMX_OT_Group_Create,
                DMX_OT_Group_Update,
                DMX_OT_Group_Rename,
                DMX_OT_Group_Remove,
                DMX_PT_Groups,
                DMX_OT_Programmer_DeselectAll,
                DMX_OT_Programmer_Clear,
                DMX_OT_Programmer_SelectBodies,
                DMX_OT_Programmer_SelectTargets,
                DMX_PT_Programmer  )

    linkedToFile = False

    def register():
        for cls in DMX.classes_setup:
            bpy.utils.register_class(cls)

    def unregister():
        for cls in DMX.classes_setup:
            bpy.utils.unregister_class(cls)
        if (DMX.linkedToFile):
            for cls in DMX.classes:
                bpy.utils.unregister_class(cls)
            DMX.linkedToFile = False

    # Blender RNA Properties

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
        bpy.context.scene.world.node_tree.nodes['Background'].inputs[0].default_value = (0,0,0,0)

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

        # Reset ArtNet status
        dmx = bpy.context.scene.dmx
        if (dmx.artnet_enabled and dmx.artnet_status != 'online'):
            dmx.artnet_enabled = False
            dmx.artnet_status = 'offline'
        if (dmx.sacn_enabled and dmx.artnet_status != 'online'):
            dmx.sacn_enabled = False
            dmx.artnet_status = 'offline'

        # Rebuild group runtime dictionary (evaluating if this is gonna stay here)
        #DMX_Group.runtime = {}
        #for group in self.groups:
        #    group.rebuild()

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

    # # Setup > Models > Display Pigtails

    def onDisplayPigtails(self, context):
        self.updateDisplayPigtails()

    display_pigtails: BoolProperty(
        name = "Display pigtails",
        default = False,
        update = onDisplayPigtails)


    # # Setup > Volume > Preview Volume

    def onVolumePreview(self, context):
        self.updatePreviewVolume()

    volume_preview: BoolProperty(
        name = "Preview Volume",
        default = False,
        update = onVolumePreview)

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
        name = "Art-Net IPv4 Address",
        description="The network card/interface to listen for ArtNet data",
        items = DMX_Network.cards()
    )

    # # DMX > sACN > Enable

    def onsACNEnable(self, context):
        dmx = bpy.context.scene.dmx
        if (self.sacn_enabled):
            DMX_ACN.enable()
            dmx.artnet_status = 'online'
            
        else:
            DMX_ACN.disable()
            dmx.artnet_status = 'online'
            
    # # DMX > ArtNet > Enable

    def onArtNetEnable(self, context):
        if (self.artnet_enabled):
            DMX_ArtNet.enable()
        else:
            DMX_ArtNet.disable()

    artnet_enabled : BoolProperty(
        name = "Enable Art-Net Input",
        description="Enables the input of DMX data throught Art-Net.",
        default = False,
        update = onArtNetEnable
    )

    sacn_enabled : BoolProperty(
        name = "Enable sACN Input",
        description="Enables the input of DMX data throught sACN.",
        default = False,
        update = onsACNEnable
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
        name = "Programmer Color",
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
            for obj in fixture.collection.objects:
                if (obj in bpy.context.selected_objects):
                    fixture.setDMX({
                        'Zoom':int((255/180)*self.programmer_zoom)
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
    # # Programmer > Sync

    def syncProgrammer(self):
        n = len(bpy.context.selected_objects)
        if (n < 1):
            self.programmer_dimmer = 0
            self.programmer_color = (255,255,255,255)
            self.programmer_pan = 0
            self.programmer_tilt = 0
            self.programmer_zoom = 25
            return
        elif (n > 1): return
        if (not bpy.context.active_object): return
        active = self.findFixture(bpy.context.active_object)
        if (not active): return
        data = active.getProgrammerData()
        self.programmer_dimmer = data['Dimmer']/256.0
        if ('Zoom' in data):
            self.programmer_zoom = int(data['Zoom']/256.0)
        if ('ColorAdd_R' in data and 'ColorAdd_G' in data and 'ColorAdd_B' in data):
            self.programmer_color = (data['ColorAdd_R'],data['ColorAdd_G'],data['ColorAdd_B'],255)
        if ('Pan' in data):
            self.programmer_pan = data['Pan']/127.0-1
        if ('Tilt' in data):
            self.programmer_tilt = data['Tilt']/127.0-1


    # Kernel Methods

    # # Fixtures

    def addFixture(self, name, profile, universe, address, mode, gel_color):
        bpy.app.handlers.depsgraph_update_post.clear()
        dmx = bpy.context.scene.dmx
        dmx.fixtures.add()
        dmx.fixtures[-1].build(name, profile, mode, universe, address, gel_color)
        bpy.app.handlers.depsgraph_update_post.append(onDepsgraph)

    def removeFixture(self, fixture):
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
            if (object.name in fixture.collection.objects):
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

    # # Groups

    def createGroup(self, name):
        dmx = bpy.context.scene.dmx
        dmx.groups.add()
        group = dmx.groups[-1]
        group.name = name
        group.update()
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

    # # Preview Volume

    def updatePreviewVolume(self):
        for fixture in self.fixtures:
            if (bpy.context.active_object.name in fixture.collection.objects):
                for light in fixture.lights:
                    light.object.data.show_cone = self.volume_preview
            else:
                for light in fixture.lights:
                    light.object.data.show_cone = False

    # # Universes

    def addUniverse(self):
        id = len(self.universes)
        DMX_Universe.add(self, id, "DMX %d"%id)
        print("DMX", "DMX_Universe created: ", universe)

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
    DMX_ACN.disable()

@bpy.app.handlers.persistent
def onUndo(scene):
    if (not scene.dmx.collection and DMX.linkedToFile):
        scene.dmx.unlinkFile()

# Callbacks #

def onActiveChanged(*args):
    dmx = bpy.context.scene.dmx
    if (dmx.volume_preview):
        dmx.updatePreviewVolume()

#
# Blender Add-On
#

def register():
    # Register Base Classes
    for cls in DMX.classes_base:
        bpy.utils.register_class(cls)

    # Register addon main class
    bpy.utils.register_class(DMX)
    bpy.types.Scene.dmx = PointerProperty(type=DMX)

    # Append handlers
    bpy.app.handlers.load_post.append(onLoadFile)
    bpy.app.handlers.undo_post.append(onUndo)

    # since 2.91.0 unregister is called also on Blender exit
    if bpy.app.version <= (2, 91, 0):
        atexit.register(DMX_ArtNet.disable)
        atexit.register(DMX_ACN.disable)

def unregister():
    # Stop ArtNet
    DMX_ArtNet.disable()
    DMX_ACN.disable()

    try:
        # Unregister Base Classes
        for cls in DMX.classes_base:
            bpy.utils.unregister_class(cls)

        # Unregister addon main class
        bpy.utils.unregister_class(DMX)
    except Exception as e:
        print(e)

    # Append handlers
    bpy.app.handlers.load_post.clear()
    bpy.app.handlers.undo_post.clear()

if __name__ == "__main__":
    register()
