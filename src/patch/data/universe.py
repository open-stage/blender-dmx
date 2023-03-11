import bpy
from bpy.types import PropertyGroup
from bpy.props import ( EnumProperty,
                        IntProperty,
                        StringProperty )

from src.i18n import DMX_i18n

from .source import DMX_Source

class DMX_Patch_Universe(PropertyGroup):

    # Identification

    name : StringProperty(
        name = DMX_i18n.PROP_PATCH_UNIVERSE_NAME,
        description = DMX_i18n.PROP_PATCH_UNIVERSE_NAME_DESC
    )

    # DMX Addressing

    number: IntProperty(
        name = DMX_i18n.PROP_PATCH_UNIVERSE_NUMBER,
        description = DMX_i18n.PROP_PATCH_UNIVERSE_NUMBER_DESC,
        default = 1,
        min = 1,
        max = 512
    )

    # DMX Source

    source: EnumProperty(
        name = DMX_i18n.PROP_PATCH_UNIVERSE_SOURCE,
        description = DMX_i18n.PROP_PATCH_UNIVERSE_SOURCE_DESC,
        items = DMX_Source.types
    )

    # Getters

    def get_source_str(self):
        for type, name, _ in DMX_Source.types:
            if (self.source == type):
                return name
        return None