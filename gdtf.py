#
#   BlendexDMX > GDTF
#   Handles GDTF profiles
#
#   http://www.github.com/hugoaboud/BlenderDMX
#

from dmx import pygdtf
import os

from dmx.fixtures.spot import DMX_SpotFixture

class DMX_GDTF():

    @staticmethod
    def getProfilesPath():
        ADDON_PATH = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(ADDON_PATH,'data','profiles')

    @staticmethod
    def getProfileList():
        # List profiles in folder
        profiles = []
        for file in os.listdir(DMX_GDTF.getProfilesPath()):
            # Parse info from file name: Company@Model.gdtf
            info = file.split('@')
            if (len(info) == 2): info[1] = info[1][:-5]
            if (len(info) == 3): info[2] = info[2][:-5]
            # Add to list (identifier, short name, full name)
            profiles.append((file, info[1], info[0]+" | "+info[1]))

        return tuple(profiles)

    @staticmethod
    def getProfileClass(name):
        return DMX_SpotFixture

    @staticmethod
    def loadProfile(filename):
        path = os.path.join(DMX_GDTF.getProfilesPath(), filename)
        profile = pygdtf.FixtureType(path)
        return profile
