import bpy
from bpy.types import PropertyGroup
from bpy.props import EnumProperty, IntProperty, StringProperty


from i18n import DMX_Lang

_ = DMX_Lang._

from .source import DMX_Source


class DMX_Patch_Universe(PropertyGroup):
    # Identification

    name: StringProperty(
        name=_("Name"),
        description=_("A unique name for the DMX universe."),
    )

    # DMX Addressing

    number: IntProperty(
        name=_("Number"),
        description=_("The number of the DMX universe."),
        default=1,
        min=1,
        max=512,
    )

    # DMX Source

    source: EnumProperty(
        name=_("Source"),
        description=_("The type of DMX source of the universe."),
        items=DMX_Source.types,
    )

    # Getters

    def get_source_str(self):
        for type, name, _ in DMX_Source.types:
            if self.source == type:
                return name
        return None
