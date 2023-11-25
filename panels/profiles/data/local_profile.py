import bpy
import os

from bpy.types import PropertyGroup
from bpy.props import StringProperty, CollectionProperty, IntProperty
from dmx import pygdtf

class DMX_Fixtures_Local_ProfileMode(PropertyGroup):
    name: StringProperty(name="Name", description="The name of the DMX profile.")

    footprint: IntProperty(
        name="Channel count",
        description="Number of channels"
    )


class DMX_Fixtures_Local_Profile(PropertyGroup):
    name: StringProperty(name="Name", description="The name of the DMX profile.")

    short_name: StringProperty(
        name="Short Name",
        description="The short name of the DMX profile, all caps, used as suggestion for fixture names.",
    )

    filename: StringProperty(name="Filename", description="The name of the DMX profile.")

    modes: CollectionProperty(type=DMX_Fixtures_Local_ProfileMode)

    @staticmethod
    def get_profiles_path() -> str:
        """Return the path to the "profiles" folder."""

        FILE_PATH = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(FILE_PATH, "..", "..", "..", "assets", "profiles")

    @staticmethod
    def get_profile_list(show_errors = False):
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
            MultiLineMessage(message=errors, title="Some fixtures could not be processed", icon="ERROR")
        return profiles

    @staticmethod
    def loadLocal(show_errors = False):
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