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
from .logging_setup import DMX_Log


class DMX_GDTF_File:
    instance = None
    profiles_list = {}
    # filename: name, short_name, filename, modes

    # manfacturer_name:  {profiles}

    def __init__(self):
        super(DMX_GDTF_File, self).__init__()
        DMX_GDTF_File.read_cache()

    @staticmethod
    def get_profiles_path():
        dmx = bpy.context.scene.dmx
        ADDON_PATH = dmx.get_addon_path()
        return os.path.join(ADDON_PATH, "assets", "profiles")

    @staticmethod
    def read_cache():
        dmx = bpy.context.scene.dmx
        dir_path = dmx.get_addon_path()
        try:
            DMX_Log.log.info("Read cache")
        except Exception as e:
            print("INFO", "Read cache")

        try:
            with open(os.path.join(dir_path, "fixtures_data.json")) as f:
                fixtures_data = json.load(f)
                DMX_GDTF_File.profiles_list = fixtures_data.get("profiles_list", {})
        except Exception:
            pass

    @staticmethod
    def write_cache():
        try:
            DMX_Log.log.info("Writing profiles cache...")
        except Exception:
            print("INFO", "Writing profiles cache...")
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
    def add_to_data(file_name):
        if DMX_GDTF_File.instance is None:
            DMX_GDTF_File.instance = DMX_GDTF_File()
        filepath = os.path.join(DMX_GDTF_File.get_profiles_path(), file_name)
        try:
            with DMX_GDTF_File.load_gdtf_profile(filepath) as fixture_type:
                modes = []
                for mode in fixture_type.dmx_modes:
                    modes.append(
                        {
                            "mode_name": mode.name,
                            "dmx_channels_count": mode.dmx_channels_count,
                            "description": mode.description,
                            "dmx_breaks": [
                                dmx_break.as_dict() for dmx_break in mode.dmx_breaks
                            ],
                        }
                    )

                revisions = fixture_type.revisions.sorted()
                revision = ""
                if revisions:
                    revision = revisions[0].text
                data = {
                    "name": f"{fixture_type.name}",
                    "short_name": fixture_type.short_name,
                    "manufacturer_name": f"{fixture_type.manufacturer}",
                    "filename": file_name,
                    "modes": modes,
                    "revision": revision,
                }
                if file_name not in DMX_GDTF_File.profiles_list:
                    DMX_GDTF_File.profiles_list[file_name] = data
        except Exception as e:
            DMX_Log.log.error((file_name, e))

    @staticmethod
    def recreate_data(recreate_profiles=False):
        DMX_Log.log.info("Regenerating fixture profiles list...")
        if recreate_profiles:
            DMX_GDTF_File.profiles_list = {}
        for file in os.listdir(DMX_GDTF_File.get_profiles_path()):
            if file not in DMX_GDTF_File.profiles_list:
                DMX_GDTF_File.add_to_data(file)

    @staticmethod
    def remove_from_data(file_name):
        if DMX_GDTF_File.instance is None:
            DMX_GDTF_File.instance = DMX_GDTF_File()
        if file_name in DMX_GDTF_File.profiles_list:
            del DMX_GDTF_File.profiles_list[file_name]

    @staticmethod
    def get_manufacturers_list():
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
    def get_manufacturer_profiles_list(manufacturer):
        if DMX_GDTF_File.instance is None:
            DMX_GDTF_File.instance = DMX_GDTF_File()
        # List profiles in folder

        profiles = [
            profile
            for profile in DMX_GDTF_File.profiles_list.values()
            if manufacturer == profile["manufacturer_name"]
        ]
        if profiles:
            profiles.sort(key=lambda x: x["name"])
        return tuple(profiles)

    @staticmethod
    def get_profile_dmx_modes_info(file_name):
        if DMX_GDTF_File.instance is None:
            DMX_GDTF_File.instance = DMX_GDTF_File()
        """Returns an array, keys are mode names, value is channel count"""
        gdtf_profile = DMX_GDTF_File.profiles_list.get(file_name)
        modes_info = []
        for mode in gdtf_profile["modes"]:
            modes_info.append(
                {
                    "mode_name": mode["mode_name"],
                    "dmx_channels_count": mode["dmx_channels_count"],
                    "dmx_breaks_count": len(mode["dmx_breaks"]),
                }
            )
        return modes_info

    @staticmethod
    def load_gdtf_profile(file_name):
        path = os.path.join(DMX_GDTF_File.get_profiles_path(), file_name)
        profile = pygdtf.FixtureType(path)
        return profile
