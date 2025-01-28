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
import os
import json

from bpy.types import PropertyGroup
from bpy.props import StringProperty, CollectionProperty, IntProperty

from ....i18n import DMX_Lang

_ = DMX_Lang._


class DMX_Fixtures_Import_Gdtf_Profile_Dmx_Mode(PropertyGroup):
    name: StringProperty(name=_("Mode name"))
    footprint: IntProperty(name=_("DMX Footprint"))


class DMX_Fixtures_Import_Gdtf_Profile(PropertyGroup):
    def onUpdate(self, context):
        # for UI updates only
        return

    name: StringProperty(
        name=_("Fixture name"),
        description=_("Manufacturer and fixture name"),
        update=onUpdate,
    )
    fixture: StringProperty(name=_("Fixture name"), description=_("Fixture name"))
    manufacturer: StringProperty(
        name=_("Manufacturer"), description=_("Manufacturer name")
    )

    revision: StringProperty(name=_("Revision"), description=_("Revision text"))

    uploader: StringProperty(name=_("Uploaded by"), description=_("File uploaded by"))

    creator: StringProperty(name=_("Created by"), description=_("File created by"))
    rating: StringProperty(
        name=_("Rating"),
    )

    rid: IntProperty(
        name=_("Revision ID"), description=_("File identifier in the GDTF Share")
    )

    modes: CollectionProperty(
        name=_("DMX Modes"), type=DMX_Fixtures_Import_Gdtf_Profile_Dmx_Mode
    )

    @staticmethod
    def get_profile_list():
        """List all GDTF files in \"Profiles\" folder"""
        dmx = bpy.context.scene.dmx
        dir_path = dmx.get_addon_path()
        try:
            with open(os.path.join(dir_path, "data.json")) as f:
                data = json.load(f)
        except Exception as e:
            print("INFO", e)
            data = []
        return data

    @staticmethod
    def loadShare():
        print("INFO", "loading start")
        imports = bpy.context.window_manager.dmx.imports
        imports.share_profiles.clear()
        profiles = DMX_Fixtures_Import_Gdtf_Profile.get_profile_list()

        for profile in profiles:
            share_profile = imports.share_profiles.add()
            name = (
                f"{profile['manufacturer']}@{profile['fixture']}@{profile['revision']}"
            )
            share_profile.name = name
            share_profile.fixture = profile["fixture"]
            share_profile.manufacturer = profile["manufacturer"]
            share_profile.revision = profile["revision"]
            share_profile.uploader = profile["uploader"]
            share_profile.rid = profile["rid"]
            share_profile.creator = profile["creator"]
            share_profile.rating = profile["rating"]
            for mode in profile["modes"]:
                local_mode = share_profile.modes.add()
                local_mode.name = mode["name"]
                local_mode.footprint = mode["dmxfootprint"]

        print("INFO", "loading done")
