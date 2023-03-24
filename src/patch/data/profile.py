import bpy
import os
from lib import pygdtf
import json

from bpy.types import PropertyGroup
from bpy.props import ( StringProperty,
                        CollectionProperty,
                        IntProperty )

from src.i18n import DMX_i18n
from src.lang import DMX_Lang
_ = DMX_Lang._


class DMX_Patch_ProfileBreak(PropertyGroup):

    n_channels: IntProperty(
        name = DMX_i18n.PROP_PATCH_PROFILE_NAME,
        description = DMX_i18n.PROP_PATCH_PROFILE_NAME_DESC
    )

class DMX_Patch_ProfileMode(PropertyGroup):

    name: StringProperty(
        name = DMX_i18n.PROP_PATCH_PROFILE_NAME,
        description = DMX_i18n.PROP_PATCH_PROFILE_NAME_DESC
    )

    breaks: CollectionProperty(
        name = DMX_i18n.PROP_PATCH_PROFILE_NAME,
        description = DMX_i18n.PROP_PATCH_PROFILE_NAME_DESC,
        type = DMX_Patch_ProfileBreak
    )


class DMX_Patch_Profile(PropertyGroup):

    name: StringProperty(
        name = DMX_i18n.PROP_PATCH_PROFILE_NAME,
        description = DMX_i18n.PROP_PATCH_PROFILE_NAME_DESC
    )

    short_name: StringProperty(
        name = DMX_i18n.PROP_PATCH_PROFILE_SHORT_NAME,
        description = DMX_i18n.PROP_PATCH_PROFILE_SHORT_NAME_DESC
    )

    filename: StringProperty(
        name = DMX_i18n.PROP_PATCH_PROFILE_NAME,
        description = DMX_i18n.PROP_PATCH_PROFILE_NAME_DESC
    )

    modes: CollectionProperty(
        type = DMX_Patch_ProfileMode
    )

    @staticmethod
    def get_profiles_path() -> str:
        """Return the path to the "profiles" folder."""

        FILE_PATH = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(FILE_PATH,'..','..','..','assets','profiles')

    @staticmethod
    def get_profile_list():
        """List gdtf files in in profiles folder"""

        profiles_path = DMX_Patch_Profile.get_profiles_path()
        profiles = []
        for file in os.listdir(profiles_path):
            file_path = os.path.join(profiles_path, file)
            try:
                fixture_type = pygdtf.FixtureType(file_path)
                modes=[]
                for mode in fixture_type.dmx_modes:
                    channels=pygdtf.utils.get_dmx_channels(fixture_type, mode.name)
                    dmx_breaks = []
                    for dmx_break in channels:
                        dmx_breaks.append(len(dmx_break))
                    modes.append({"name": mode.name, "breaks":tuple(dmx_breaks)})
                profiles.append({"name": f"{fixture_type.manufacturer} @ {fixture_type.long_name}",
                             "short_name": fixture_type.short_name,
                             "filename": file,
                             "modes":modes})
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
            patch.profiles[-1].name = profile['name']
            patch.profiles[-1].short_name = profile['short_name']
            patch.profiles[-1].filename = profile['filename']

            for mode in profile['modes']:
                patch.profiles[-1].modes.add()
                patch.profiles[-1].modes[-1].name = mode['name']
                for n in mode['breaks']:
                    patch.profiles[-1].modes[-1].breaks.add()
                    patch.profiles[-1].modes[-1].breaks[-1].n_channels = n


class DMX_Patch_Import_Gdtf_Profile_Dmx_Mode(PropertyGroup):
    name: StringProperty(
        name = _("Mode name")
        )
    footprint: IntProperty(
            name = _("DMX Footprint")
            )

class DMX_Patch_Import_Gdtf_Profile(PropertyGroup):

    name: StringProperty(
        name = _("Fixture name"),
        description = _("Manufacturer and fixture name")
    )
    fixture: StringProperty(
        name = _("Fixture name"),
        description = _("Fixture name")
    )
    manufacturer: StringProperty(
        name = _("Manufacturer"),
        description = _("Manufacturer name")
    )

    revision: StringProperty(
        name = _("Revision"),
        description = _("Revision text")
    )

    uploader: StringProperty(
        name = _("Uploaded by"),
        description = _("File uploaded by")
    )

    creator: StringProperty(
        name = _("Created by"),
        description = _("File created by")
    )
    rating: StringProperty(
        name = _("Rating"),
    )


    rid: IntProperty(
        name = _("Revision ID"),
        description = _("File identifier in the GDTF Share") 
    )

    modes: CollectionProperty(
            name = _("Dmx Modes"),
            type = DMX_Patch_Import_Gdtf_Profile_Dmx_Mode
            )




    @staticmethod
    def get_profile_list():
        """List gdtf files in in profiles folder"""
        dir_path = os.path.dirname(os.path.abspath(__file__))
        try:
            with open(os.path.join(dir_path, '..', '..', '..', 'lib', 'share_api_client', "data.json")) as f:
                data = json.load(f)
        except:
            data = []
        return data

    @staticmethod
    def load():
        print("loading start")
        imports = bpy.context.window_manager.dmx.imports
        imports.share_profiles.clear()
        profiles = DMX_Patch_Import_Gdtf_Profile.get_profile_list()


        for profile in profiles:
            imports.share_profiles.add()
            name = f"{profile['manufacturer']}@{profile['fixture']}@{profile['revision']}"
            imports.share_profiles[-1].name = name
            imports.share_profiles[-1].fixture = profile['fixture']
            imports.share_profiles[-1].manufacturer = profile['manufacturer']
            imports.share_profiles[-1].revision = profile['revision']
            imports.share_profiles[-1].uploader = profile['uploader']
            imports.share_profiles[-1].rid = profile['rid']
            imports.share_profiles[-1].creator = profile['creator']
            imports.share_profiles[-1].rating = profile['rating']
            for mode in profile["modes"]:
                imports.share_profiles[-1].modes.add()
                imports.share_profiles[-1].modes[-1].name = mode["name"]
                imports.share_profiles[-1].modes[-1].footprint = mode["dmxfootprint"]

        print("loading done")

