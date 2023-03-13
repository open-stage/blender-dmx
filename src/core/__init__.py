import bpy
from bpy.types import ( PropertyGroup,
                        Collection )
from bpy.props import ( CollectionProperty,
                        BoolProperty,
                        PointerProperty,
                        IntProperty )

from .data.pointer import *
from .data.fixture import *
from .data.data import *

from .fixture_builder import DMX_FixtureBuilder

# Module Data Structure

class DMX_Core(PropertyGroup):
    
    # 

    collection: PointerProperty(
        type = Collection
    )

    fixtures: CollectionProperty(
        type = DMX_Fixture
    )

    # Render Settings

    display_pigtails: BoolProperty(
        default = False
    )

    # Build methods
    def build_patch(self):
        patch = bpy.context.scene.dmx.patch
        for fixture in patch.fixtures:
            DMX_FixtureBuilder.build(fixture)

# Add-on Module Registering

classes = (

    # Data Structures
    DMX_Material,
    DMX_Object,
    DMX_Universe,
    DMX_Data,
    DMX_FixtureChannel,
    DMX_Fixture,
    DMX_Core

)