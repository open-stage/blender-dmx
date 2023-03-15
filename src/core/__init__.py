import bpy
from bpy.types import ( PropertyGroup,
                        Collection )
from bpy.props import ( CollectionProperty,
                        BoolProperty,
                        PointerProperty,
                        IntProperty )

from .data.pointer import *
from .data.fixture import *

from .controller import DMX_Core_Controller
from .engine import DMX_Engine

# Module Data Structure

class DMX_Core(PropertyGroup, DMX_Core_Controller):
    
    # 

    collection: PointerProperty(
        type = Collection
    )

    fixtures: CollectionProperty(
        type = DMX_Fixture
    )

    # DMX Engine

    engine: PointerProperty(
        type = DMX_Engine
    )

    # Render Settings

    display_pigtails: BoolProperty(
        default = False
    )

# Add-on Module Registering

classes = (

    # Data Structures
    DMX_Material,
    DMX_Object,
    DMX_FixtureChannel,
    DMX_Fixture,
    DMX_Engine,
    DMX_Core

)