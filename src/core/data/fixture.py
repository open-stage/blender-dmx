import bpy
from bpy.types import ( PropertyGroup,
                        Object,
                        Collection )
from bpy.props import ( BoolProperty,
                        FloatVectorProperty,
                        IntProperty,
                        CollectionProperty,
                        PointerProperty,
                        StringProperty )

from src.i18n import DMX_i18n
from .pointer import DMX_Material, DMX_Object

class DMX_FixtureChannel(PropertyGroup):

    id: StringProperty(
        name = "Fixture > Channel > ID",
        default = ''
    )

    default: IntProperty(
        name = "Fixture > Channel > Default",
        default = 0
    )
    
    geometry: StringProperty(
        name = "Fixture > Geometry",
        default = ''
    )

class DMX_Fixture(PropertyGroup):

    # Identifier (Synced to Patch)

    id: IntProperty(
        name = "Patch Id",
    )

    # Blender Pointers

    collection: PointerProperty(
        name = "Fixture > Collection",
        type = Collection)

    objects: CollectionProperty(
        name = "Fixture > Objects",
        type = DMX_Object
    )

    lights: CollectionProperty(
        name = "Fixture > Lights",
        type = DMX_Object
    )

    emitters: CollectionProperty(
        name = "Fixture > Materials",
        type = DMX_Material)

    # Channels

    channels: CollectionProperty(
        name = "Fixture > Channels",
        type = DMX_FixtureChannel
    )

    virtual_channels: CollectionProperty(
        name = "Fixture > Virtual Channels",
        type = DMX_FixtureChannel
    )

    # DMX State

    def clear(self):
        pass