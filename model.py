#
#   BlendexDMX > Model
#   Handles the creation of different models
#
#   http://www.github.com/open-stage/BlenderDMX
#

import bpy

from dmx.gdtf import DMX_GDTF
from dmx.logging import DMX_Log


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
            new_collection = DMX_GDTF.buildCollection(profile, dmx_mode, display_beams, add_target)
        except Exception as e:
            DMX_Log.log.error(f"Error {e}")
            if name in collections:
                collections.remove(collections[name])
            return None
        return new_collection
