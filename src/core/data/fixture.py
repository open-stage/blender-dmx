import bpy
from bpy.types import ( PropertyGroup,
                        Object,
                        Collection )
from bpy.props import ( IntProperty,
                        IntVectorProperty,
                        BoolProperty,
                        CollectionProperty,
                        PointerProperty,
                        StringProperty )

from .pointer import DMX_Object

class DMX_FixtureChannel(PropertyGroup):
    '''
    A channel that belongs to a dynamic fixture,
    and acts as the interface between DMX channels and fixture geometry.
    '''

    # The coordinates of the 4 channels on the buffer
    coords: IntVectorProperty(
        size = 4
    )

    # Channel resolution in bytes. 0 = virtual channel
    resolution: IntProperty(
        default = 1
    )

    # The dmx function of the channel, ex: Dimmer, ColorAdd_R, etc.
    function: StringProperty(
        default = ''
    )

    # The geometry to which this channel refers
    # This geometry is often a parent to multiple geometries
    # controlled by the channel
    geometry: PointerProperty(
        type = Object
    )

    # The default value of the channel when it's cleared
    default: IntProperty(
        default = 0
    )
        
class DMX_Fixture(PropertyGroup):
    '''
    A dynamic fixture, built from a `PatchFixture` by the
    `FixtureBuilder`, which controls a fixture collection.
    '''

    # Unique ID (Sync to Patch)
    id: IntProperty()

    # Unique Name (Sync to Patch)
    name: StringProperty()

    # Blender Collection
    collection: PointerProperty(
        type = Collection
    )

    # Root Blender Objects
    # Used for saving and restoring fixture position
    # on rebuild
    roots: CollectionProperty(
        type = DMX_Object
    )

    # DMX Channels
    channels: CollectionProperty(
        type = DMX_FixtureChannel
    )
