import bpy
from bpy.types import PropertyGroup
from bpy.props import BoolProperty, IntProperty, StringProperty


from i18n import DMX_Lang

_ = DMX_Lang._


class DMX_Patch_FixtureBatch(PropertyGroup):
    # Identification

    name: StringProperty(
        name=_("Name"),
        description=_("A unique name for the fixture batch."),
    )

    # Batch Settings

    units: IntProperty(
        name=_("Units"),
        description=_("The number of fixtures inside this batch."),
        min=1,
        max=999,
        default=1,
    )

    # DMX Addressing

    sequential: BoolProperty(
        name=_(
            "Sequential",
        ),
        description=_(
            "True if the batch fixtures are addressed sequentially, according to the footprint.",
        ),
        default=True,
    )

    footprint: IntProperty(
        name=_(
            "Footprint",
        ),
        description=_(
            "Overrides the footprint of each fixture.",
        ),
        min=0,
        max=512,
        default=0,
    )

    # [UI]

    expand: BoolProperty(
        name=_(
            "Expand",
        ),
        description=_(
            "Expands/shrinks the list of fixtures in this batch.",
        ),
        default=True,
    )
