#
#   BlendexDMX > Group
#   A group of fixtures
#
#   http://www.github.com/hugoaboud/BlenderDMX
#

import bpy

from bpy.props import (PointerProperty,
                       StringProperty,
                       CollectionProperty)

from bpy.types import (ID,
                       Property,
                       PropertyGroup)

from dmx.fixture import *

class DMX_Group(PropertyGroup):

    # This is only used to save the group to file
    # as a string representation of the fixture names array
    dump: StringProperty(
        name = "DMX Groups"
    )

    # The actual groups are stored and acessed here
    runtime = {}

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
            self.runtime[self.name] = sel_fixtures;
            self.dump = str([fixture.name for fixture in sel_fixtures])

    def select(self):
        for fixture in self.runtime[self.name]:
            fixture.select()

    def rebuild(self):
        fixtures = bpy.context.scene.dmx.fixtures
        self.runtime[self.name] = [fixtures[fxt[1:-1]] for fxt in self.dump.strip('[]').split(', ')]
