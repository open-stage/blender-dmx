bl_info = {
    "name": "DMX",
    "description": "Create and control DMX fixtures",
    "author": "hugoaboud",
    "version": (0, 0, 5),
    "blender": (2, 80, 0),
    "location": "3D View > DMX",
    "warning": "", # used for warning icon and text in addons panel
    "wiki_url": "http://www.github.com/hugoaboud/BlenderDMX",
    "tracker_url": "",
    "category": "Lighting"
}

import bpy

from dmx.util import getMesh, getBodyMaterial

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

    # Classes to be registered
    # The registration is done in two steps. The second only runs
    # after the user requests to setup the addon.

    classes_setup = (DMX_OT_Setup_NewShow,
                    DMX_PT_Setup)

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
                DMX_ListItem_Group,
                DMX_UL_Group,
                DMX_MT_Group,
                DMX_OT_Group_Create,
                DMX_OT_Group_Update,
                DMX_OT_Group_Rename,
                DMX_OT_Group_Remove,
                DMX_PT_Groups,
                DMX_OT_Programmer_DeselectAll,
                DMX_OT_Programmer_Clear,
                DMX_PT_Programmer  )

    def register():
        for cls in DMX.classes_setup:
            bpy.utils.register_class(cls)

    def unregister():
        for cls in DMX.classes_setup:
            bpy.utils.unregister_class(cls)
            if (self.collection):
                for cls in DMX.classes:
                    bpy.utils.unregister_class(cls)

    # Base Properties

    collection: PointerProperty(
        name = "DMX Collection",
        type = Collection)

    volume: PointerProperty(
        name = "Volume Scatter Box",
        type = Object)

    volume_nodetree: PointerProperty(
        name = "Volume Scatter Shader Node Tree",
        type = NodeTree)

    # Internal data (static)
    # This should be parsed to file

    fixtures = []
    groups = []

    # Setup the DMX scene

    def setup(self, collection):

        # Store collection created by the operator
        self.collection = collection

        # Second step registration
        for cls in self.classes:
            bpy.utils.register_class(cls)

        # Create group list RNA and clear leftovers from past runs
        bpy.types.Scene.group_list = CollectionProperty(type=DMX_ListItem_Group)
        bpy.context.scene.group_list.clear()

        # Set background to black (to match with menu)
        bpy.context.scene.world.node_tree.nodes['Background'].inputs[0].default_value = (0,0,0,0)

        # Append handlers
        #bpy.app.handlers.undo_post.append(onUndo)
        #bpy.app.handlers.depsgraph_update_post.append(onDepsGraph)

    # Handlers

    def onUndo(self, scene):
        #print("UNDO")
        pass

    def onDepsGraph(self, scene):
        #print("DEPS GRAPH")
        pass

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
            if (fixture.spot):
                fixture.spot.data.show_cone = self.volume_preview

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
        self.fixtures[self.fixture_list_i].body.select_set(True)

    fixture_list_i : IntProperty(
        name = "Fixture List Item",
        description="The selected element on the fixture list",
        default = 0,
        update = onFixtureList
        )

    # # Groups > List

    def onGroupList(self, context):
        for fixture in self.groups[self.group_list_i].fixtures:
            fixture.body.select_set(True)

    group_list_i : IntProperty(
        name = "Group List i",
        description="The selected element on the group list",
        default = 0,
        update = onGroupList
        )

    # # Programmer > Color

    def onProgrammerColor(self, context):
        for fixture in self.fixtures:
            for obj in fixture.collection.objects:
                if (obj in bpy.context.selected_objects):
                    fixture.setColor(self.programmer_color)

    programmer_color: FloatVectorProperty(
        name = "Programmer Color",
        subtype = "COLOR",
        size = 4,
        min = 0.0,
        max = 1.0,
        default = (1.0,1.0,1.0,1.0),
        update = onProgrammerColor
        )

    # # Programmer > Dimmer

    def onProgrammerDimmer(self, context):
        for fixture in self.fixtures:
            for obj in fixture.collection.objects:
                if (obj in bpy.context.selected_objects):
                    fixture.setDimmer(self.programmer_dimmer)

    programmer_dimmer: FloatProperty(
        name = "Programmer Dimmer",
        default = 1,
        min = 0,
        max = 1,
        update = onProgrammerDimmer)

    # Kernel Methods

    # # Fixtures

    def addFixture(self, fixture):
        self.fixtures.append(fixture)

    def removeFixture(self, i):
        if (i >= 0 and i < len(self.fixtures)):
            bpy.data.collections.remove(self.fixtures[i].collection)
            del self.fixtures[i]

    def getFixture(self, collection):
        for fixture in self.fixtures:
            if (fixture.collection == collection):
                return fixture

    # # Groups

    def createGroup(self, context, name):
        group = Group(self,name)
        if (len(group.fixtures)):
            self.groups.append(group)
            context.scene.group_list.add()
            context.scene.group_list[-1].name = name

    def updateGroup(self, i):
        if (i >= 0 and i < len(self.groups)):
            self.groups[i].update()

    def removeGroup(self, context, i):
        del self.groups[i]
        context.scene.group_list.remove(i)

# Handlers #

@bpy.app.handlers.persistent
def onLoadFile(scene):
    print("FILE LOADED")
    if (hasattr(bpy.context.scene, 'dmx')):
        print("HAS DMX")
        bpy.context.scene.dmx.setup(bpy.data.collections["DMX"])

def onUndo(scene):
    scene.dmx.onUndo(scene)

def onDepsGraph(scene):
    scene.dmx.onDepsGraph(scene)

#
# Blender Add-On
#

def register():
    bpy.utils.register_class(DMX)
    bpy.types.Scene.dmx = PointerProperty(type=DMX)

    bpy.app.handlers.load_post.append(onLoadFile)

def unregister():
    bpy.types.Scene.dmx.unregister()

    bpy.app.handlers.load_post.clear()

if __name__ == "__main__":
    register()
