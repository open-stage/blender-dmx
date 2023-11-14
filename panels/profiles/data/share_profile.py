import bpy
import os
import json

from bpy.types import PropertyGroup
from bpy.props import StringProperty, CollectionProperty, IntProperty


class DMX_Fixtures_Import_Gdtf_Profile_Dmx_Mode(PropertyGroup):
    name: StringProperty(name="Mode name")
    footprint: IntProperty(name="DMX Footprint")


class DMX_Fixtures_Import_Gdtf_Profile(PropertyGroup):
    name: StringProperty(name="Fixture name", description="Manufacturer and fixture name")
    fixture: StringProperty(name="Fixture name", description="Fixture name")
    manufacturer: StringProperty(name="Manufacturer", description="Manufacturer name")

    revision: StringProperty(name="Revision", description="Revision text")

    uploader: StringProperty(name="Uploaded by", description="File uploaded by")

    creator: StringProperty(name="Created by", description="File created by")
    rating: StringProperty(
        name="Rating",
    )

    rid: IntProperty(name="Revision ID", description="File identifier in the GDTF Share")

    modes: CollectionProperty(name="DMX Modes", type=DMX_Fixtures_Import_Gdtf_Profile_Dmx_Mode)

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
