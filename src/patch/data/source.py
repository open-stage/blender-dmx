import bpy
from bpy.types import PropertyGroup
from bpy.props import ( EnumProperty,
                        StringProperty )

from src.i18n import DMX_i18n

class DMX_Source:
    
    types = [
        ('blenderdmx', 'BlenderDMX', ''),
        ('artnet', 'ArtNet', ''),
        ('sacn', 'sACN', '')
    ]

class DMX_Patch_Source(PropertyGroup):

    type: EnumProperty(
        name = DMX_i18n.PROP_PATCH_SOURCE_TYPE,
        description = DMX_i18n.PROP_PATCH_SOURCE_TYPE_DESC,
        items = DMX_Source.types
    )
