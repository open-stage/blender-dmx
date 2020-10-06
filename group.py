#
#   BlendexDMX > Group
#   A group of fixtures
#
#   http://www.github.com/hugoaboud/BlenderDMX
#

import bpy
from bpy.types import ID

class Group:

    def __init__(self, dmx, name):
        super().__init__(self)
        self.dmx = dmx
        self.name = name
        self.fixtures = []
        self.update()

    # <update>
    # Iterate all selected objects looking for fixture components
    # Store a list with those fixtures

    def update(self):
        fixtures = []
        for fixture in self.dmx.fixtures:
            for obj in fixture.collection.objects:
                if (obj in bpy.context.selected_objects):
                    fixtures.append(fixture)
        if (len(fixtures)):
            self.fixtures = fixtures
