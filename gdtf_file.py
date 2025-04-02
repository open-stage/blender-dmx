# Copyright (C) 2025 vanous
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

import os

import bpy
import pygdtf


class DMX_GDTF_File:
    @staticmethod
    def getProfilesPath():
        dmx = bpy.context.scene.dmx
        ADDON_PATH = dmx.get_addon_path()
        return os.path.join(ADDON_PATH, "assets", "profiles")

    @staticmethod
    def getManufacturerList():
        # List profiles in folder
        manufacturers_names = set()
        # TODO cache this, as it can make a slow addon start
        for file in os.listdir(DMX_GDTF_File.getProfilesPath()):
            # Parse info from file name: Manufacturer@Device@Revision.gdtf
            if "@" not in file:
                file = os.path.join(DMX_GDTF_File.getProfilesPath(), file)
                with pygdtf.FixtureType(file) as fixture_type:
                    name = f"{fixture_type.manufacturer}"
            else:
                name = file.split("@")[0]
            manufacturers_names.add(name)
        manufacturers = bpy.context.window_manager.dmx.manufacturers
        manufacturers.clear()
        for name in sorted(manufacturers_names):
            manufacturers.add().name = name

    @staticmethod
    def getProfileList(manufacturer):
        # List profiles in folder
        profiles = []
        for file in os.listdir(DMX_GDTF_File.getProfilesPath()):
            # Parse info from file name: Company@Model.gdtf
            if "@" not in file:
                file = os.path.join(DMX_GDTF_File.getProfilesPath(), file)
                with pygdtf.FixtureType(file) as fixture_type:
                    info = [
                        f"{fixture_type.manufacturer}",
                        f"{fixture_type.long_name}",
                        "",
                    ]
            else:
                info = file.split("@")
            if info[0] == manufacturer:
                # Remove ".gdtf" from the end of the string
                if info[-1][-5:].lower() == ".gdtf":
                    info[-1] = info[-1][:-5]
                # Add to list (identifier, short name, full name)
                profiles.append((file, info[1], (info[2] if len(info) > 2 else "")))

        return tuple(profiles)

    @staticmethod
    def getModes(profile):
        """Returns an array, keys are mode names, value is channel count"""
        gdtf_profile = DMX_GDTF_File.loadProfile(profile)
        modes = {}
        for mode in gdtf_profile.dmx_modes:
            modes[mode.name] = mode.dmx_channels_count
        return modes

    @staticmethod
    def loadProfile(filename):
        path = os.path.join(DMX_GDTF_File.getProfilesPath(), filename)
        profile = pygdtf.FixtureType(path)
        return profile
