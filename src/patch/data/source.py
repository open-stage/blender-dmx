import bpy
from bpy.types import PropertyGroup
from bpy.props import EnumProperty, StringProperty


from i18n import DMX_Lang

_ = DMX_Lang._


class DMX_Source:
    types = [
        ("blenderdmx", "BlenderDMX", ""),
        ("artnet", "ArtNet", ""),
        ("sacn", "sACN", ""),
    ]


class DMX_Patch_Source(PropertyGroup):
    type: EnumProperty(
        name=_("Type"), description=_("The type of DMX source."), items=DMX_Source.types
    )
