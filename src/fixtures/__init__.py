import bpy
from bpy.types import PropertyGroup
from bpy.props import CollectionProperty, IntProperty

from .data.profile import *
from .ui.list import *
from .ui.operator import *
from .ui.panel import *
from src.patch import *

from .controller import DMX_Fixtures_Manager
from src.lang import DMX_Lang

_ = DMX_Lang._

# Module Data Structure


class DMX_Fixtures(PropertyGroup, DMX_Fixtures_Manager):
    placeholder: IntProperty(default=0)


class DMX_Fixtures_Share_Imports(PropertyGroup):
    # GDTF Share Import profiles
    share_profiles: CollectionProperty(type=DMX_Fixtures_Import_Gdtf_Profile)
    selected_fixture: IntProperty(default=0)

    selected_mode: IntProperty(default=0)


# Add-on Module Registering

classes = (
    # Data Structures
    DMX_Fixtures_Import_Gdtf_Profile_Dmx_Mode,
    DMX_Fixtures_Import_Gdtf_Profile,
    DMX_Fixtures_Share_Imports,
    DMX_Fixtures,
    # Lists
    DMX_UL_Share_Fixtures,
    DMX_UL_Share_Fixtures_Dmx_Modes,
    DMX_UL_Local_Fixtures,
    # Operators
    DMX_OP_Import_Fixture_From_File,
    DMX_OP_Import_Fixture_From_Share,
    DMX_OP_Import_Fixture_Update_Share,
    DMX_OP_Delete_Local_Fixture,
    DMX_OP_Update_Local_Fixtures,
    # Panel
    DMX_PT_Fixtures_Import,
    DMX_PT_Fixtures_Import_Profile_Detail,
    DMX_PT_Fixtures_Local_Fixtures,
)
