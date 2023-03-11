import bpy
from bpy.types import ( PropertyGroup,
                        Object,
                        Collection )
from bpy.props import ( BoolProperty,
                        IntVectorProperty,
                        IntProperty,
                        CollectionProperty,
                        PointerProperty,
                        StringProperty )

from src.i18n import DMX_i18n

class DMX_Universe(PropertyGroup):

    buffer: IntVectorProperty(
        name = "Universe Buffer",
        # default = [[0 for _ in range(32)] for _ in range(16)],
        min = 0,
        max = 255,
        size = (16,32)
    )

class DMX_Data(PropertyGroup):

    universes: CollectionProperty(
        name = "Universe Buffers",
        type = DMX_Universe
    )