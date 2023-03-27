import bpy
import os
from lib import pygdtf

from bpy.types import PropertyGroup
from bpy.props import StringProperty, CollectionProperty, IntProperty

from i18n import DMX_Lang

_ = DMX_Lang._


class DMX_Patch_ProfileBreak(PropertyGroup):
    n_channels: IntProperty(
        name=_(_("Name")), description=_("The name of the DMX profile.")
    )


class DMX_Patch_ProfileMode(PropertyGroup):
    name: StringProperty(name=_("Name"), description=_("The name of the DMX profile."))

    breaks: CollectionProperty(
        name=_(_("Name")),
        description=_("The name of the DMX profile."),
        type=DMX_Patch_ProfileBreak,
    )


class DMX_Patch_Profile(PropertyGroup):
    name: StringProperty(name=_("Name"), description=_("The name of the DMX profile."))

    short_name: StringProperty(
        name=_(_("Short Name")),
        description="The short name of the DMX profile, all caps, used as suggestion for fixture names.",
    )

    filename: StringProperty(
        name=_(_("Filename")), description=_("The name of the DMX profile.")
    )

    modes: CollectionProperty(type=DMX_Patch_ProfileMode)

    @staticmethod
    def get_profiles_path() -> str:
        """Return the path to the "profiles" folder."""

        FILE_PATH = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(FILE_PATH, "..", "..", "..", "assets", "profiles")

    @staticmethod
    def get_profile_list():
        """List gdtf files in in profiles folder"""

        profiles_path = DMX_Patch_Profile.get_profiles_path()
        profiles = []
        for file in os.listdir(profiles_path):
            file_path = os.path.join(profiles_path, file)
            try:
                fixture_type = pygdtf.FixtureType(file_path)
                modes = []
                for mode in fixture_type.dmx_modes:
                    channels = pygdtf.utils.get_dmx_channels(fixture_type, mode.name)
                    dmx_breaks = []
                    for dmx_break in channels:
                        dmx_breaks.append(len(dmx_break))
                    modes.append({"name": mode.name, "breaks": tuple(dmx_breaks)})
                profiles.append(
                    {
                        "name": f"{fixture_type.manufacturer} @ {fixture_type.long_name}",
                        "short_name": fixture_type.short_name,
                        "filename": file,
                        "modes": modes,
                    }
                )
            except Exception as e:
                print("Error parsing file", file, e)

        return profiles

    @staticmethod
    def load():
        patch = bpy.context.scene.dmx.patch
        patch.profiles.clear()
        profiles = DMX_Patch_Profile.get_profile_list()

        for profile in profiles:
            patch.profiles.add()
            patch.profiles[-1].name = profile["name"]
            patch.profiles[-1].short_name = profile["short_name"]
            patch.profiles[-1].filename = profile["filename"]

            for mode in profile["modes"]:
                patch.profiles[-1].modes.add()
                patch.profiles[-1].modes[-1].name = mode["name"]
                for n in mode["breaks"]:
                    patch.profiles[-1].modes[-1].breaks.add()
                    patch.profiles[-1].modes[-1].breaks[-1].n_channels = n
