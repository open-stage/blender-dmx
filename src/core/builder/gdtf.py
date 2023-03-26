from typing import Tuple

import os
import shutil

from lib import pygdtf
from src.core.types import *

class DMX_GDTF_Processor():
    '''
    A GDTF profile parsed by pygdtf, with helper methods.
    '''

    # [ Paths ]

    @classmethod
    def _get_profiles_path(self) -> str:
        '''
        Return the path to the "profiles" folder.
        '''
        FILE_PATH = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(FILE_PATH,'..','..','..','assets','profiles')

    @classmethod
    def _get_primitive_path(self, primitive: str) -> str:
        '''
        Return the path to the "primitives" folder.
        '''
        FILE_PATH = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(FILE_PATH,'..','..','..','assets','primitives', primitive+'.obj')

    @classmethod
    def _get_fixture_models_path(self, fixture_type_id) -> str:
        '''
        Return the path to the folder that stores GDTF Models for this Fixture.
        '''
        FILE_PATH = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(FILE_PATH,'..','..','..','assets','models',fixture_type_id)

    # [ Constructor ]

    def __init__(self, filename: str) -> None:
        path = os.path.join(DMX_GDTF_Processor._get_profiles_path(), filename)
        self.fixture_type = pygdtf.FixtureType(path)
    
    # [ Parsing Helpers ]

    def extract_model_file(self, file: pygdtf.Resource) -> Tuple[str, str]:
        '''
        Extract a given GDTF Resource from the GDTF zip file,
        and return the extracted folder path + the file extension.
        '''
        extension = file.extension.lower()
        dir_name = "gltf"
        if "3ds" == extension:
            dir_name = "3ds"

        inside_zip_path = f"models/{dir_name}/{file.name}.{file.extension}"
        to_folder_path = DMX_GDTF_Processor._get_fixture_models_path(self.fixture_type.fixture_type_id)
        self.fixture_type._package.extract(inside_zip_path, to_folder_path)

        return os.path.join(to_folder_path, inside_zip_path), extension
    
    def delete_fixture_model_folder(self) -> None:
        '''
        Delete the folder that stores GDTF Models for this Fixture.
        '''
        folder_path = DMX_GDTF_Processor._get_fixture_models_path(self.fixture_type.fixture_type_id)
        if (os.path.exists(folder_path)):
            shutil.rmtree(folder_path)

    def get_model_primitive_type(self, model: pygdtf.Model) -> None:
        '''
        Return the type of primitive of the given model.
        Options: file, gdtf, primitive
        '''
        primitive = str(model.primitive_type)
        if (primitive.endswith('1_1')):
            primitive = primitive[:-3]
        if model.file.name != '': 
            #if primitive == 'Undefined' is not a good test as the model can have both, maybe due to GDTF Builder issue.
            return 'file', None
        elif primitive in ['Base','Conventional','Head','Yoke']:
            return 'gdtf', primitive
        else:
            return 'primitive', primitive

    # [ Build Helpers ]

    def build_geometry_channel_metadata(self, mode_name: str) -> ChannelMetadata:
        '''
        Build and return the metadata that will be stored
        into an Object of the Fixture Model.

        We assume a single logical channel by channel for now,
        which is  exposed through the "function" string.
        '''
        # TODO: this uses old implementation which doesn't take geometry references into account.
        # References are used very frequently and thus GDTF dmx chart cannot be 
        # determined by dmx mode but by geometry tree. The tree must be assembled
        # and traversed including geometry references first, to get correct dmx mode layout. 
        # BlenderDMX 1.0 did this correctly

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

    def get_collection_name(self, mode_name: str) -> str:
        '''
        Get the Fixture Collection name for a given mode.
        '''
        return f'{self.fixture_type.fixture_type_id}-{mode_name}'

    def get_model_collection_name(self, mode_name: str) -> str:
        '''
        Get the Model Collection name for a given mode.
        '''
        return self.get_collection_name(mode_name) + '-MODEL'
