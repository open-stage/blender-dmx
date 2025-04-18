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
import json


class DMX_GDTF_File:
    instance = None
    profiles_list = {}
    # filename: name, short_name, filename, modes

    # manfacturer_name:  {profiles}

    def __init__(self):
        super(DMX_GDTF_File, self).__init__()
        DMX_GDTF_File.read_cache()

    @staticmethod
    def read_cache():
        print("reading cache")
        dmx = bpy.context.scene.dmx
        dir_path = dmx.get_addon_path()
        try:
            with open(os.path.join(dir_path, "fixtures_data.json")) as f:
                fixtures_data = json.load(f)
                DMX_GDTF_File.profiles_list = fixtures_data.get("profiles_list", {})
        except Exception as e:
            ...

    @staticmethod
    def write_cache():
        print("writing cache")
        if DMX_GDTF_File.instance is None:
            DMX_GDTF_File.instance = DMX_GDTF_File()
        dmx = bpy.context.scene.dmx
        dir_path = dmx.get_addon_path()
        try:
            with open(os.path.join(dir_path, "fixtures_data.json"), "w") as f:
                fixtures_data = {
                    "profiles_list": DMX_GDTF_File.profiles_list,
                }
                json.dump(fixtures_data, f)
        except Exception as e:
            print("INFO", e)

    @staticmethod
    def add_to_data(filename):
        if DMX_GDTF_File.instance is None:
            DMX_GDTF_File.instance = DMX_GDTF_File()
        filepath = os.path.join(DMX_GDTF_File.getProfilesPath(), filename)
        with DMX_GDTF_File.loadProfile(filepath) as fixture_type:
            modes = []
            for mode in fixture_type.dmx_modes:
                modes.append(
                    {
                        "mode_name": mode.name,
                        "dmx_channels_count": mode.dmx_channels_count,
                        "description": mode.description,
                    }
                )

            data = {
                "name": f"{fixture_type.manufacturer} @ {fixture_type.long_name}",
                "short_name": fixture_type.short_name,
                "manufacturer_name": f"{fixture_type.manufacturer}",
                "filename": filename,
                "modes": modes,
            }

            DMX_GDTF_File.profiles_list[filename] = data

    @staticmethod
    def recreate_data():
        if DMX_GDTF_File.instance is None:
            DMX_GDTF_File.instance = DMX_GDTF_File()
        for file in os.listdir(DMX_GDTF_File.getProfilesPath()):
            if file not in DMX_GDTF_File.profiles_list:
                DMX_GDTF_File.add_to_data(file)
        DMX_GDTF_File.write_cache()

    @staticmethod
    def remove_from_data(fixture):
        if DMX_GDTF_File.instance is None:
            DMX_GDTF_File.instance = DMX_GDTF_File()
        # remove from the data
        ...

    @staticmethod
    def getProfilesPath():
        dmx = bpy.context.scene.dmx
        ADDON_PATH = dmx.get_addon_path()
        return os.path.join(ADDON_PATH, "assets", "profiles")

    @staticmethod
    def getManufacturerList():
        if DMX_GDTF_File.instance is None:
            DMX_GDTF_File.instance = DMX_GDTF_File()
        # List profiles in folder

        manufacturers_names = set(
            [
                profile["manufacturer_name"]
                for profile in DMX_GDTF_File.profiles_list.values()
            ]
        )
        manufacturers = bpy.context.window_manager.dmx.manufacturers
        manufacturers.clear()
        for name in sorted(manufacturers_names):
            manufacturers.add().name = name

    @staticmethod
    def getProfileList(manufacturer):
        if DMX_GDTF_File.instance is None:
            DMX_GDTF_File.instance = DMX_GDTF_File()
        # List profiles in folder

        profiles = [
            profile
            for profile in DMX_GDTF_File.profiles_list.values()
            if manufacturer == profile["manufacturer_name"]
        ]
        return tuple(profiles)

    @staticmethod
    def getModes(file_name):
        if DMX_GDTF_File.instance is None:
            DMX_GDTF_File.instance = DMX_GDTF_File()
        """Returns an array, keys are mode names, value is channel count"""
        gdtf_profile = DMX_GDTF_File.profiles_list.get(file_name)
        for mode in gdtf_profile.dmx_modes:
            modes[mode.name] = mode.dmx_channels_count
        return modes

    @staticmethod
    def loadProfile(file_name):
        path = os.path.join(DMX_GDTF_File.getProfilesPath(), file_name)
        profile = pygdtf.FixtureType(path)
        return profile
