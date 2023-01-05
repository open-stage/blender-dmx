#
#   BlendexDMX > Model
#   Handles the creation of different models
#
#   http://www.github.com/hugoaboud/BlenderDMX
#

import os.path
import bpy

from dmx.material import getEmitterMaterial
from dmx.gdtf import DMX_GDTF

class DMX_Model():

    #   Return the fixture model collection by profile
    #   If not imported, build the collection from the GDTF profile
    #   This collection is then deep-copied by the Fixture class
    #   to create a fixture collection.
    @staticmethod
    def getFixtureModelCollection(profile, dmx_mode):

        # Make sure the profile was passed as an argument, otherwise return None
        if (profile == None):
            return None

        name = DMX_GDTF.getName(profile, dmx_mode)

        # If the fixture collection was already imported for this model
        # just return it
        if (name in bpy.data.collections):
            return bpy.data.collections[name]

        # Otherwise, build it from profile
        return DMX_GDTF.buildCollection(profile, dmx_mode)
