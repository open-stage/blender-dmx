import bpy
from bpy.types import Object

from src.patch.data.fixture import DMX_Patch_Fixture
from .gdtf import DMX_GDTF

class DMX_Model():

    def __init__(patch: DMX_Patch_Fixture):
        
        name = DMX_GDTF.get_collection_name(profile, dmx_mode)

        # If the fixture collection was already imported for this model
        # just return it
        if (name in bpy.data.collections):
            self.collection = bpy.data.collections[name]
        
        # Otherwise, build it from profile
        else:
            self.collection = DMX_GDTF.build_collection(profile, dmx_mode, display_beams)

    def get_root(self) -> Object:
        for obj in self.collection.objects:
            if obj.get("geometry_root", False):
                return obj

    def get_head(self):
        for obj in self.collection.objects:
            for channel in self.channels:
                if "Tilt" == channel.id and channel.geometry == obj.get("original_name", "None"):
                    return obj
            for channel in self.virtual_channels:
                if "Tilt" == channel.id and channel.geometry == obj.get("original_name", "None"):
                    return obj