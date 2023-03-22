import bpy
from bpy.types import PropertyGroup
from bpy.props import ( CollectionProperty,
                        IntProperty )

from .data.profile import *
from .data.fixture import *
from .data.fixture_batch import *
from .data.universe import *
from .data.source import *
from .ui.list import *
from .ui.menu import *
from .ui.operator import *
from .ui.panel import *

from .controller import DMX_Patch_Controller
from src.lang import DMX_Lang
_ = DMX_Lang._

# Module Data Structure

class DMX_Patch(PropertyGroup, DMX_Patch_Controller):

    # GDTF Profiles

    profiles: CollectionProperty(
        type = DMX_Patch_Profile
    )

    # GDTF Share Import profiles
    share_profiles: CollectionProperty(
        type = DMX_Patch_Import_Gdtf_Profile
    )

    # Fixtures
    
    fixtures: CollectionProperty(
        type = DMX_Patch_Fixture
    )

    fixture_batches: CollectionProperty(
        type = DMX_Patch_FixtureBatch
    )

    # Universes

    universes: CollectionProperty(
        type = DMX_Patch_Universe
    )

    # Sources

    sources: CollectionProperty(
        type = DMX_Patch_Source
    )

    # [UI]

    selected_fixture: IntProperty(
        default = 0
    )

    selected_universe: IntProperty(
        default = 0
    )

# Add-on Module Registering

classes = (

    # Data Structures
    DMX_Patch_FixtureBreak,
    DMX_Patch_Fixture,
    DMX_Patch_FixtureBatch,
    DMX_Patch_ProfileBreak,
    DMX_Patch_ProfileMode,
    DMX_Patch_Profile,
    DMX_Patch_Import_Gdtf_Profile,
    DMX_Patch_Source,
    DMX_Patch_Universe,
    DMX_Patch,
    
    # Lists
    DMX_UL_Patch_Fixtures,
    DMX_UL_Patch_Universes,
    DMX_UL_Share_Fixtures,

    # Menus
    DMX_OP_MT_Patch_SelectUniverse,
    DMX_MT_Patch_SelectUniverse,
    DMX_OP_MT_Patch_SelectMode,
    DMX_MT_Patch_SelectMode,

    # Operators
    DMX_OP_Patch_Source_Configure,
    DMX_OP_Patch_Universe_Add,
    DMX_OP_Patch_Universe_Remove,
    DMX_OP_Patch_Fixture_Add,
    DMX_OP_Patch_Fixture_AddBatch,
    DMX_OP_Patch_Fixture_Remove,
    DMX_OP_Patch_Build,
    DMX_OP_Import_Fixture_From_File,
    DMX_OP_Import_Fixture_From_Share,
    DMX_OP_Import_Fixture_Update_Share,
    
    # Panel
    DMX_PT_Patch,
    DMX_PT_Patch_Import
)
