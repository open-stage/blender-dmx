#
#   BlendexDMX > Group
#   A group of fixtures
#
#   http://www.github.com/open-stage/BlenderDMX
#

import bpy
import uuid
import json

from bpy.props import (PointerProperty,
                       StringProperty,
                       CollectionProperty)

from bpy.types import (ID,
                       Property,
                       PropertyGroup)

from dmx.fixture import *

class FixtureGroup():
    def __init__(self, name, uuid):
        self.name = name
        self.uuid = uuid

class DMX_Group(PropertyGroup):

    # This is only used to save the group to file
    # as a json representation of the fixture names array
    dump: StringProperty(
        name = "DMX Groups"
    )

    uuid: StringProperty(
        name = "UUID",
        description = "Unique ID, used for MVR",
        default = str(uuid.uuid4())
            )
    # The current groups are stored and acessed here
    # I'm not sure this data is safe for use with Undo
    # Commenting until a veredict is reached
    #runtime = {}

    # <update>
    # Iterate all selected objects looking for fixture components
    # Store a list with those fixtures
    def update(self):
        # Get selected fixtures
        sel_fixtures = []
        for fixture in bpy.context.scene.dmx.fixtures:
            for obj in fixture.collection.objects:
                if (obj in bpy.context.selected_objects):
                    sel_fixtures.append(fixture)
        # If there's any fixture selected, clear fixtures list
        # and repopulate it
        if (len(sel_fixtures)):
            #self.runtime[self.name] = sel_fixtures;
            self.dump = json.dumps([fixture.uuid for fixture in sel_fixtures])
        else:
            self.dump = ''

    def select(self):
        # Comment left here for legacy reasons. We now use json to serialize the array
        # Rebuilding the groups array everytime takes a long time
        # This was done to avoid inconsistencies on Undo of unrelated Operators,
        # which seems to mess with the runtime volatile data declared as runtime
        # However, a better way should be considered (a Blender String Array)
        #for fixture in self.runtime[self.name]:
        dmx = bpy.context.scene.dmx

        if not bpy.context.window_manager.dmx.aditive_selection:
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.scene.dmx.updatePreviewVolume()

        for fixture in [dmx.findFixtureByUUID(f_uuid) for f_uuid in json.loads(self.dump)]:
            if fixture is not None:
                fixture.select()
        bpy.context.scene.dmx.updatePreviewVolume()

