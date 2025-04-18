# Copyright (C) 2023 vanous
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
from bpy.props import CollectionProperty, IntProperty, StringProperty
from bpy.types import PropertyGroup

from ....i18n import DMX_Lang
from ....gdtf_file import DMX_GDTF_File

_ = DMX_Lang._


class DMX_Fixtures_Local_ProfileMode(PropertyGroup):
    name: StringProperty(name=_("Name"), description=_("The name of the DMX profile."))

    footprint: IntProperty(name=_("Channel count"), description=_("Number of channels"))


class DMX_Fixtures_Local_Profile(PropertyGroup):
    name: StringProperty(name=_("Name"), description=_("The name of the DMX profile."))

    short_name: StringProperty(
        name=_("Short Name"),
        description=_(
            "The short name of the DMX profile, all caps, used as suggestion for fixture names."
        ),
    )

    filename: StringProperty(
        name=_("Filename"), description=_("The name of the DMX profile.")
    )

    modes: CollectionProperty(type=DMX_Fixtures_Local_ProfileMode)

    @staticmethod
    def loadLocal(write_cache=False):
        print("load local profiles")
        local_profiles = bpy.context.window_manager.dmx.imports.local_profiles
        local_profiles.clear()
        DMX_GDTF_File.recreate_data()
        if write_cache:
            DMX_GDTF_File.write_cache()
        profiles = dict(sorted(DMX_GDTF_File.profiles_list.items(), key=lambda x: x[0]))

        for profile in profiles.values():
            local_profile = local_profiles.add()
            local_profile.name = f"{profile['manufacturer_name']} @ {profile['name']} @ {profile['revision']}"
            local_profile.short_name = profile["short_name"]
            local_profile.filename = profile["filename"]

            for mode in profile["modes"]:
                local_mode = local_profile.modes.add()
                local_mode.name = mode["mode_name"]
                local_mode.footprint = mode["dmx_channels_count"]


def MultiLineMessage(message=[], title="Message Box", icon="INFO"):
    def draw(self, context):
        for n in message:
            self.layout.label(text=n)

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)
