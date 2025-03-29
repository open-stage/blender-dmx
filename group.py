# Copyright (C) 2020 Hugo Aboud, vanous
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
import uuid

import bpy
from bpy.props import StringProperty
from bpy.types import PropertyGroup


class FixtureGroup:
    def __init__(self, name, uuid):
        self.name = name
        self.uuid = uuid


class DMX_Group(PropertyGroup):
    # This is only used to save the group to file
    # as a json representation of the fixture names array
    dump: StringProperty(name="DMX Groups")

    uuid: StringProperty(
        name="UUID", description="Unique ID, used for MVR", default=str(uuid.uuid4())
    )
    # The current groups are stored and acessed here
    # I'm not sure this data is safe for use with Undo
    # Commenting until a veredict is reached
    # runtime = {}

    # <update>
    # Iterate all selected objects looking for fixture components
    # Store a list with those fixtures
    def update(self):
        # Get selected fixtures
        sel_fixtures = []
        for fixture in bpy.context.scene.dmx.fixtures:
            for obj in fixture.collection.objects:
                if obj in bpy.context.selected_objects:
                    sel_fixtures.append(fixture)
        # If there's any fixture selected, clear fixtures list
        # and repopulate it
        if len(sel_fixtures):
            # self.runtime[self.name] = sel_fixtures;
            self.dump = json.dumps([fixture.uuid for fixture in sel_fixtures])
        else:
            self.dump = ""

    def select(self):
        # Comment left here for legacy reasons. We now use json to serialize the array
        # Rebuilding the groups array everytime takes a long time
        # This was done to avoid inconsistencies on Undo of unrelated Operators,
        # which seems to mess with the runtime volatile data declared as runtime
        # However, a better way should be considered (a Blender String Array)
        # for fixture in self.runtime[self.name]:
        dmx = bpy.context.scene.dmx

        if (
            bpy.context.window_manager.dmx.aditive_selection
            or bpy.context.window_manager.dmx.subtractive_selection
        ):
            pass
        else:
            bpy.ops.object.select_all(action="DESELECT")

        for fixture in [
            dmx.findFixtureByUUID(f_uuid) for f_uuid in json.loads(self.dump)
        ]:
            if fixture is not None:
                if bpy.context.window_manager.dmx.subtractive_selection:
                    fixture.unselect()
                else:
                    fixture.select()
        bpy.context.scene.dmx.updatePreviewVolume()
