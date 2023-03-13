import os
import bpy
import copy
from mathutils import Euler, Matrix

from bpy.types import Object

from lib import pygdtf
from lib.io_scene_3ds.import_3ds import load_3ds
from src.log import DMX_Log

from src.util import sanitize_obj_name

class DMX_GDTF():

    # Paths

    @classmethod
    def _get_profiles_path(self):
        ADDON_PATH = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(ADDON_PATH,'..','..','assets','profiles')

    @classmethod
    def _get_primitive_path(self, primitive: str):
        ADDON_PATH = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(ADDON_PATH,'..','..','assets','primitives', primitive+'.obj')

    @classmethod
    def _get_fixture_models_path(self, fixture_type_id):
        ADDON_PATH = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(ADDON_PATH,'..','..','assets','models',fixture_type_id)

    # File Utilities

    @classmethod
    def extract_model_file(self, gdtf: pygdtf.FixtureType, file: pygdtf.Resource):
        extension = file.extension.lower()

        inside_zip_path = f"models/{extension}/{file.name}.{file.extension}"
        to_folder_path = DMX_GDTF._get_fixture_models_path(gdtf.fixture_type_id)       
        gdtf._package.extract(inside_zip_path, to_folder_path)

        return os.path.join(to_folder_path, inside_zip_path), extension

    # UI Utility
    # TODO: review usage

    @classmethod
    def get_manufacturer_list(self):
        # List profiles in folder
        manufacturers = set()
        for file in os.listdir(DMX_GDTF._get_profiles_path()):
            # Parse info from file name: Company@Model.gdtf
            info = file.split('@')
            # Remove ".gdtf" from the end of the string
            info[-1] = info[-1][:-5]
            # Add to list (identifier, short name, full name)
            manufacturers.add((info[0], info[0], ''))
        return tuple(sorted(manufacturers))

    @classmethod
    def get_profile_list(self, manufacturer):
        # List profiles in folder
        profiles = []
        for file in os.listdir(DMX_GDTF._get_profiles_path()):
            # Parse info from file name: Company@Model.gdtf
            info = file.split('@')
            if (info[0] == manufacturer):
                # Remove ".gdtf" from the end of the string
                info[-1] = info[-1][:-5]
                # Add to list (identifier, short name, full name)
                profiles.append((file, info[1], (info[2] if len(info) > 2 else '')))

        return tuple(profiles)

    @classmethod
    def get_modes(self, profile):
        """Returns an array, keys are mode names, value is channel count"""
        gdtf_profile = DMX_GDTF.loadProfile(profile)
        modes = {}
        for mode in gdtf_profile.dmx_modes:
            dmx_channels = pygdtf.utils.get_dmx_channels(gdtf_profile)
            dmx_channels_flattened = [channel for break_channels in dmx_channels for channel in break_channels]
            modes[mode.name] = len(dmx_channels_flattened)
        return modes
 
    # Load GDTF file

    @classmethod
    def load_fixture_type(self, filename: str) -> pygdtf.FixtureType:
        path = os.path.join(DMX_GDTF._get_profiles_path(), filename)
        return pygdtf.FixtureType(path)

    # Build

    @classmethod
    def get_geometry_channel_metadata(self, gdtf: pygdtf.FixtureType, mode_name: str):
        # Returns the channels and virtual channels by geometry name.
        # We assume a single logical channel by channel for now, which is 
        # exposed through the "attribute" string
        channels = {}
        virtual_channels = {}
        mode = pygdtf.utils.get_dmx_mode_by_name(gdtf, mode_name)

        if (mode == None):
            raise Exception(f'Mode {mode_name} not found on profile {gdtf.name}.')

        for channel in mode.dmx_channels:
            geom = channel.geometry
            metadata = {
                'dmx_break': channel.dmx_break,
                'default': {
                    'byte_count': channel.default.byte_count,
                    'value': channel.default.value,
                },
                'highlight': {
                    'byte_count': channel.highlight.byte_count,
                    'value': channel.highlight.value,
                },
                'attribute': channel.logical_channels[0].attribute.str_link
            }

            if (channel.offset == None):
                if (geom not in virtual_channels):
                    virtual_channels[geom] = []
                virtual_channels[geom].append(metadata)
            else:
                if (geom not in channels):
                    channels[geom] = []
                channels[geom].append({
                    **metadata,
                    'coarse': channel.offset[0],
                    'fine': channel.offset[1] if len(channel.offset) > 1 else None
                })

        return channels, virtual_channels

    @classmethod
    def get_collection_name(self, gdtf: pygdtf.FixtureType, mode: str):
        revision = gdtf.revisions[-1].text if len(gdtf.revisions) else ''
        return f"{gdtf.manufacturer}, {gdtf.name}, {mode}, {revision}"

    @classmethod
    def get_model_name(self, gdtf: pygdtf.FixtureType, mode: str):
        return self.get_collection_name(gdtf, mode) + ' MODEL'

    @classmethod
    def get_model_primitive_type(self, model: pygdtf.Model):
        primitive = str(model.primitive_type)
        if (primitive.endswith('1_1')):
            primitive = primitive[:-3]
        if primitive == 'Undefined':
            return 'file', None
        elif primitive in ['Base','Conventional','Head','Yoke']:
            return 'gdtf', primitive
        else:
            return 'primitive', primitive
        

