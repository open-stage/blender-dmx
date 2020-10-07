#
#   BlendexDMX > Group
#   A group of fixtures
#
#   http://www.github.com/hugoaboud/BlenderDMX
#

import bpy

from bpy.props import (PointerProperty,
                       CollectionProperty)

from bpy.types import (ID,
                       Property,
                       PropertyGroup)

from dmx.fixture import *

class DMX_Group_Fixture(PropertyGroup):
    def seraa(self, context):
        pass
    fixture: PointerProperty(
        name = "DMX Group Fixture",
        type = DMX_Fixture
    )

class DMX_Group(PropertyGroup):
    fixtures: CollectionProperty(
        name = "DMX Groups",
        type = DMX_Group_Fixture
    )

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
            self.fixtures.clear()
            for fixture in sel_fixtures:
                self.fixtures.add()
                self.fixtures[-1].name = str(len(self.fixtures)-1)
                self.fixtures[-1].fixture = fixture
