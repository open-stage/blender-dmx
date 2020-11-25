bl_info = {
    "name": "DMX",
    "description": "Create and control DMX fixtures",
    "author": "hugoaboud",
    "version": (0, 2, 8),
    "blender": (2, 90, 0),
    "location": "3D View > DMX",
    "warning": "", # used for warning icon and text in addons panel
    "wiki_url": "http://www.github.com/hugoaboud/BlenderDMX",
    "tracker_url": "",
    "category": "Lighting"
}

import sys
import bpy
import os

from dmx.fixture import *
from dmx.fixtures.spot import *
from dmx.fixtures.tube import *
from dmx.group import *

from dmx.panels.setup import *
from dmx.panels.fixtures import *
from dmx.panels.groups import *
from dmx.panels.programmer import *

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

# Main Class #

class DMX(PropertyGroup):

    # Base classes to be registered
    # These should be registered before the DMX class, so it can register properly

    classes_base = (DMX_Param,
                    DMX_Model_Param,
                    DMX_Fixture_Object,
                    DMX_Fixture,
                    DMX_Group,
                    DMX_PT_Setup)

    # Classes to be registered
    # The registration is done in two steps. The second only runs
    # after the user requests to setup the addon.


    classes_setup = (DMX_OT_Setup_NewShow,)

    classes = ( DMX_OT_Setup_Volume_Create,
                DMX_PT_Setup_Background,
                DMX_PT_Setup_Volume,
                DMX_UL_Fixture,
                DMX_MT_Fixture,
                DMX_MT_Fixture_Add,
                DMX_OT_Fixture_AddSpot,
                DMX_OT_Fixture_EditSpot,
                DMX_OT_Fixture_AddTube,
                DMX_OT_Fixture_EditTube,
                DMX_OT_Fixture_Remove,
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
    # This should be parsed to file

    fixtures: CollectionProperty(
        name = "DMX Fixtures",
        type = DMX_Fixture)

    groups: CollectionProperty(
        name = "DMX Groups",
        type = DMX_Group)

    # New DMX Scene
    # - Remove any previous DMX objects/collections
    # - Create DMX collection
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

        # Link addon to file
        self.linkFile()

    # Link Add-on to file
    # This is only called on two situations: "Create New Show" or "onLoadFile"
    # - Link DMX Collection (if present)
    # - Link Volume Object (if present)
    # - If DMX collection was linked, register addon
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

        # Rebuild fixture subclass dictionary
        for fixture in self.fixtures:
            if (fixture.subclass not in DMX_Fixture.subclasses):
                print("DMX", "\tLinking fixture subclass ", fixture.subclass)
                subcls = fixture.subclass.split('.')
                DMX_Fixture.subclasses[fixture.subclass] = getattr(getattr(sys.modules['dmx.fixtures'],subcls[0]),subcls[1])

        # Rebuild group runtime dictionary
        DMX_Group.runtime = {}
        for group in self.groups:
            group.rebuild()

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

    # # Setup > Volume > Preview

    def onVolumePreview(self, context):
        for fixture in self.fixtures:
            for light in fixture.lights:
                light.object.data.show_cone = self.volume_preview

    volume_preview: BoolProperty(
        name = "Preview Volume",
        default = False,
        update = onVolumePreview)

    # # Setup > Volume > Enabled

    def onVolumeEnabled(self, context):
        self.volume.hide_set(not self.volume_enabled)

    volume_enabled: BoolProperty(
        name = "Enable Volume Scatter",
        default = True,
        update = onVolumeEnabled)

    # #  Setup > Volume > Density

    def onVolumeDensity(self, context):
        self.volume_nodetree.nodes[1].inputs['Density'].default_value = self.volume_density

    volume_density: FloatProperty(
        name = "Density",
        description="Volume Scatter Density",
        default = 1,
        min = 0,
        max = 1,
        update = onVolumeDensity)

    # # Fixtures > List

    def onFixtureList(self, context):
        self.fixtures[self.fixture_list_i].select()

    fixture_list_i : IntProperty(
        name = "Fixture List Item",
        description="The selected element on the fixture list",
        default = 0,
        update = onFixtureList
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
        for fixture in self.fixtures:
            for obj in fixture.collection.objects:
                if (obj in bpy.context.selected_objects):
                    fixture.setDMX({'dimmer':self.programmer_dimmer})

    programmer_dimmer: FloatProperty(
    name = "Programmer Dimmer",
    default = 0,
    min = 0,
    max = 1,
    update = onProgrammerDimmer)

    # # Programmer > Color

    def onProgrammerColor(self, context):
        for fixture in self.fixtures:
            for obj in fixture.collection.objects:
                if (obj in bpy.context.selected_objects):
                    fixture.setDMX({'R':self.programmer_color[0],'G':self.programmer_color[1],'B':self.programmer_color[2]})

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
        for fixture in self.fixtures:
            for obj in fixture.collection.objects:
                if (obj in bpy.context.selected_objects):
                    fixture.setDMX({'pan':(self.programmer_pan+1)/2})

    programmer_pan: FloatProperty(
        name = "Programmer Pan",
        min = -1.0,
        max = 1.0,
        default = 0.0,
        update = onProgrammerPan)

    def onProgrammerTilt(self, context):
        for fixture in self.fixtures:
            for obj in fixture.collection.objects:
                if (obj in bpy.context.selected_objects):
                    fixture.setDMX({'tilt':(self.programmer_tilt+1)/2})

    programmer_tilt: FloatProperty(
        name = "Programmer Tilt",
        min = -1.0,
        max = 1.0,
        default = 0.0,
        update = onProgrammerTilt)

    # Kernel Methods

    # # Fixtures

    def addSpotFixture(self, name, model, address, moving, emission, power, angle, focus, default_color):
        dmx = bpy.context.scene.dmx
        dmx.fixtures.add()
        fixture = dmx.fixtures[-1]
        DMX_SpotFixture.create(fixture, name, model, address, moving, emission, power, angle, focus, default_color)

    def addTubeFixture(self, name, model, address, emission, length, default_color):
        dmx = bpy.context.scene.dmx
        dmx.fixtures.add()
        fixture = dmx.fixtures[-1]
        DMX_TubeFixture.create(fixture, name, model, address, emission, length, default_color)

    def removeFixture(self, i):
        if (i >= 0 and i < len(self.fixtures)):
            bpy.data.collections.remove(self.fixtures[i].collection)
            self.fixtures.remove(i)

    def getFixture(self, collection):
        for fixture in self.fixtures:
            if (fixture.collection == collection):
                return fixture

    # # Groups

    def createGroup(self, name):
        dmx = bpy.context.scene.dmx
        dmx.groups.add()
        group = dmx.groups[-1]
        group.name = name
        group.update()
        if (name not in DMX_Group.runtime):
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

# Handlers #

@bpy.app.handlers.persistent
def onLoadFile(scene):
    if ('DMX' in bpy.data.scenes['Scene'].collection.children):
        print("DMX", "File contains DMX show, linking...")
        bpy.context.scene.dmx.linkFile()
    else:
        bpy.context.scene.dmx.unlinkFile()

@bpy.app.handlers.persistent
def onUndo(scene):
    if (not scene.dmx.collection and DMX.linkedToFile):
        scene.dmx.unlinkFile()

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

def unregister():
    # Unregister Base Classes
    for cls in DMX.classes_base:
        bpy.utils.unregister_class(cls)

    # Unregister addon main class
    bpy.utils.unregister_class(DMX)

    # Append handlers
    bpy.app.handlers.load_post.clear()
    bpy.app.handlers.undo_post.clear()

if __name__ == "__main__":
    register()
