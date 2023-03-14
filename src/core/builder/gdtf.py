import os
import bpy
import copy
import shutil
from mathutils import Euler, Matrix

from bpy.types import Object

from lib import pygdtf
from lib.io_scene_3ds.import_3ds import load_3ds
from src.log import DMX_Log

from src.util import sanitize_obj_name

class DMX_GDTF():

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

    # Paths

    @classmethod
    def _get_profiles_path(self):
        FILE_PATH = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(FILE_PATH,'..','..','..','assets','profiles')

    @classmethod
    def _get_primitive_path(self, primitive: str):
        FILE_PATH = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(FILE_PATH,'..','..','..','assets','primitives', primitive+'.obj')

    @classmethod
    def _get_fixture_models_path(self, fixture_type_id):
        FILE_PATH = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(FILE_PATH,'..','..','..','assets','models',fixture_type_id)

    # Constructor

    def __init__(self, filename: str):
        path = os.path.join(DMX_GDTF._get_profiles_path(), filename)
        self.fixture_type = pygdtf.FixtureType(path)
    
    # Parsing Helpers

    def extract_model_file(self, file: pygdtf.Resource):
        extension = file.extension.lower()

        inside_zip_path = f"models/{extension}/{file.name}.{file.extension}"
        to_folder_path = DMX_GDTF._get_fixture_models_path(self.fixture_type.fixture_type_id)       
        self.fixture_type._package.extract(inside_zip_path, to_folder_path)

        return os.path.join(to_folder_path, inside_zip_path), extension
    
    def delete_fixture_model_folder(self) -> None:
        folder_path = DMX_GDTF._get_fixture_models_path(self.fixture_type.fixture_type_id)
        if (os.path.exists(folder_path)):
            shutil.rmtree(folder_path)

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

    # Build Helpers

    def get_geometry_channel_metadata(self, mode_name: str):
        # Returns the channels and virtual channels by geometry name.
        # We assume a single logical channel by channel for now, which is 
        # exposed through the "function" string
        channels = {}
        mode = pygdtf.utils.get_dmx_mode_by_name(self.fixture_type, mode_name)

        if (mode == None):
            raise Exception(f'Mode {mode_name} not found on profile {self.fixture_type.name}.')

        for channel in mode.dmx_channels:
            geom = channel.geometry
            if (geom not in channels):
                channels[geom] = []
            channels[geom].append({
                'dmx_break': channel.dmx_break,
                'default': {
                    'byte_count': channel.default.byte_count,
                    'value': channel.default.value,
                },
                'highlight': {
                    'byte_count': channel.highlight.byte_count,
                    'value': channel.highlight.value,
                },
                'function': channel.logical_channels[0].attribute.str_link,
                'offset': channel.offset # None if virtual channel, or [coarse, fine, ultra, uber]
            })

        return channels

    def get_collection_name(self, mode_name: str):
        return f'{self.fixture_type.fixture_type_id}-{mode_name}'

    def get_model_collection_name(self, mode_name: str):
        return self.get_collection_name(mode_name) + '-MODEL'
