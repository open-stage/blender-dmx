import bpy
from bpy.types import ( PropertyGroup,
                        Object,
                        Collection )
from bpy.props import ( BoolProperty,
                        FloatVectorProperty,
                        IntProperty,
                        IntVectorProperty,
                        CollectionProperty,
                        PointerProperty,
                        StringProperty )

from src.i18n import DMX_i18n
from .pointer import DMX_Material, DMX_Object

class DMX_FixtureChannel(PropertyGroup):

    offset: IntVectorProperty(
        size = 4,
        default = (0,0,0,0)
    )

    universe: IntProperty(
        min = 0
    )

    function: StringProperty(
        default = ''
    )

    geometry: PointerProperty(
        type = Object
    )

    default: IntProperty(
        default = 0
    )

    
class DMX_Fixture(PropertyGroup):

    # Identifier (Synced to Patch)

    id: IntProperty(
        name = "Fixture > Id"
    )

    name: StringProperty(
        name = "Fixture > Name"
    )

    # Blender Pointers

    collection: PointerProperty(
        name = "Fixture > Collection",
        type = Collection)

    roots: CollectionProperty(
        name = "Fixture > Roots",
        type = DMX_Object
    )

    # mobiles: CollectionProperty(
    #     name = "Fixture > Mobiles",
    #     type = DMX_Object
    # )

    # targets: CollectionProperty(
    #     name = "Fixture > Mobiles",
    #     type = DMX_Object
    # )

    # emitters: CollectionProperty(
    #     name = "Fixture > Materials",
    #     type = DMX_Material)

    # lights: CollectionProperty(
    #     name = "Fixture > Lights",
    #     type = DMX_Object
    # )

    # Channels

    channels: CollectionProperty(
        name = "Fixture > Channels",
        type = DMX_FixtureChannel
    )
