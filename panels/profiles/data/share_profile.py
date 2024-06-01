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

    name: StringProperty(name=_("Fixture name"), description=_("Manufacturer and fixture name"), update=onUpdate)
    fixture: StringProperty(name=_("Fixture name"), description=_("Fixture name"))
    manufacturer: StringProperty(name=_("Manufacturer"), description=_("Manufacturer name"))

    revision: StringProperty(name=_("Revision"), description=_("Revision text"))

    uploader: StringProperty(name=_("Uploaded by"), description=_("File uploaded by"))

    creator: StringProperty(name=_("Created by"), description=_("File created by"))
    rating: StringProperty(
        name=_("Rating"),
    )

    rid: IntProperty(name=_("Revision ID"), description=_("File identifier in the GDTF Share"))

    modes: CollectionProperty(name=_("DMX Modes"), type=DMX_Fixtures_Import_Gdtf_Profile_Dmx_Mode)

    @staticmethod
    def get_profile_list():
        """List all GDTF files in \"Profiles\" folder"""
        dir_path = os.path.dirname(os.path.abspath(__file__))
        try:
            with open(os.path.join(dir_path, "..", "..", "..", "share_api_client", "data.json")) as f:
                data = json.load(f)
        except:
            data = []
        return data

    @staticmethod
    def loadShare():
        print("loading start")
        imports = bpy.context.window_manager.dmx.imports
        imports.share_profiles.clear()
        profiles = DMX_Fixtures_Import_Gdtf_Profile.get_profile_list()

        for profile in profiles:
            share_profile = imports.share_profiles.add()
            name = f"{profile['manufacturer']}@{profile['fixture']}@{profile['revision']}"
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

        print("loading done")
