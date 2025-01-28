#    Copyright vanous
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


import bpy

from .gdtf import DMX_GDTF
from .logging import DMX_Log


class DMX_Model:
    #   Return the fixture model collection by profile
    #   If not imported, build the collection from the GDTF profile
    #   This collection is then deep-copied by the Fixture class
    #   to create a fixture collection.
    @staticmethod
    def getFixtureModelCollection(profile, dmx_mode, display_beams, add_target):
        collections = bpy.data.collections

        # Make sure the profile was passed as an argument, otherwise return None
        if profile == None:
            return None

        name = DMX_GDTF.getName(profile, dmx_mode, display_beams, add_target)
        # If the fixture collection was already imported for this model
        # just return it
        if name in collections:
            DMX_Log.log.debug(f"Getting collection from cache: {name}")
            return collections[name]

        # Otherwise, build it from profile
        try:
            new_collection = DMX_GDTF.buildCollection(
                profile, dmx_mode, display_beams, add_target
            )
        except Exception as e:
            DMX_Log.log.error(f"Error {e}")
            if name in collections:
                collections.remove(collections[name])
            return None
        return new_collection
