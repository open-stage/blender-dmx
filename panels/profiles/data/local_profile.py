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

from bpy.types import PropertyGroup
from bpy.props import StringProperty, CollectionProperty, IntProperty
import pygdtf

from ....i18n import DMX_Lang

_ = DMX_Lang._


class DMX_Fixtures_Local_ProfileMode(PropertyGroup):
    name: StringProperty(name=_("Name"), description=_("The name of the DMX profile."))

    footprint: IntProperty(name=_("Channel count"), description=_("Number of channels"))


class DMX_Fixtures_Local_Profile(PropertyGroup):
    name: StringProperty(name=_("Name"), description=_("The name of the DMX profile."))

    short_name: StringProperty(
        name=_("Short Name"),
        description=_("The short name of the DMX profile, all caps, used as suggestion for fixture names."),
    )

    filename: StringProperty(name=_("Filename"), description=_("The name of the DMX profile."))

    modes: CollectionProperty(type=DMX_Fixtures_Local_ProfileMode)

    @staticmethod
    def get_profiles_path() -> str:
        """Return the path to the "profiles" folder."""

        FILE_PATH = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(FILE_PATH, "..", "..", "..", "assets", "profiles")

    @staticmethod
    def get_profile_list(show_errors=False):
        """List gdtf files in in profiles folder"""

        profiles_path = DMX_Fixtures_Local_Profile.get_profiles_path()
        profiles = []
        errors = []
        for file in os.listdir(profiles_path):
            file_path = os.path.join(profiles_path, file)
            try:
                fixture_type = pygdtf.FixtureType(file_path)
                modes_info = pygdtf.utils.get_dmx_modes_info(fixture_type)

                profiles.append(
                    {
                        "name": f"{fixture_type.manufacturer} @ {fixture_type.long_name}",
                        "short_name": fixture_type.short_name,
                        "filename": file,
                        "modes": modes_info,
                    }
                )
            except Exception as e:
                print("Error parsing file", file, e)
                errors.append(f"{file}: {e}")

        if show_errors and errors:
            MultiLineMessage(message=errors, title=_("Some fixtures could not be processed"), icon="ERROR")
        return profiles

    @staticmethod
    def loadLocal(show_errors=False):
        local_profiles = bpy.context.window_manager.dmx.imports.local_profiles
        local_profiles.clear()
        profiles = DMX_Fixtures_Local_Profile.get_profile_list(show_errors)

        for profile in profiles:
            local_profile = local_profiles.add()
            local_profile.name = profile["name"]
            local_profile.short_name = profile["short_name"]
            local_profile.filename = profile["filename"]

            for mode in profile["modes"]:
                local_mode = local_profile.modes.add()
                local_mode.name = mode["mode_name"]
                local_mode.footprint = mode["mode_dmx_channel_count"]


def MultiLineMessage(message=[], title="Message Box", icon="INFO"):
    def draw(self, context):
        for n in message:
            self.layout.label(text=n)

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)
