import bpy
import os
import json

from bpy.types import PropertyGroup
from bpy.props import StringProperty, CollectionProperty, IntProperty

from src.lang import DMX_Lang

_ = DMX_Lang._


class DMX_Fixtures_Import_Gdtf_Profile_Dmx_Mode(PropertyGroup):
    name: StringProperty(name=_("Mode name"))
    footprint: IntProperty(name=_("DMX Footprint"))


class DMX_Fixtures_Import_Gdtf_Profile(PropertyGroup):
    name: StringProperty(
        name=_("Fixture name"), description=_("Manufacturer and fixture name")
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
        name=_("Dmx Modes"), type=DMX_Fixtures_Import_Gdtf_Profile_Dmx_Mode
    )

    @staticmethod
    def get_profile_list():
        """List gdtf files in in profiles folder"""
        dir_path = os.path.dirname(os.path.abspath(__file__))
        try:
            with open(
                os.path.join(
                    dir_path, "..", "..", "..", "lib", "share_api_client", "data.json"
                )
            ) as f:
                data = json.load(f)
        except:
            data = []
        return data

    @staticmethod
    def load():
        print("loading start")
        imports = bpy.context.window_manager.dmx.imports
        imports.share_profiles.clear()
        profiles = DMX_Fixtures_Import_Gdtf_Profile.get_profile_list()

        for profile in profiles:
            imports.share_profiles.add()
            name = (
                f"{profile['manufacturer']}@{profile['fixture']}@{profile['revision']}"
            )
            imports.share_profiles[-1].name = name
            imports.share_profiles[-1].fixture = profile["fixture"]
            imports.share_profiles[-1].manufacturer = profile["manufacturer"]
            imports.share_profiles[-1].revision = profile["revision"]
            imports.share_profiles[-1].uploader = profile["uploader"]
            imports.share_profiles[-1].rid = profile["rid"]
            imports.share_profiles[-1].creator = profile["creator"]
            imports.share_profiles[-1].rating = profile["rating"]
            for mode in profile["modes"]:
                imports.share_profiles[-1].modes.add()
                imports.share_profiles[-1].modes[-1].name = mode["name"]
                imports.share_profiles[-1].modes[-1].footprint = mode["dmxfootprint"]

        print("loading done")
