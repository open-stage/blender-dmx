import bpy
from bpy.types import PropertyGroup
from bpy.props import CollectionProperty, IntProperty

from .data.profile import *
from .ui.list import *
from .ui.operator import *
from .ui.panel import *
from src.patch import *

from .controller import DMX_Devices_Manager
from src.lang import DMX_Lang

_ = DMX_Lang._

# Module Data Structure

class DMX_Devices(PropertyGroup, DMX_Devices_Manager):
    placeholder: IntProperty(default=0)

class DMX_Devices_Share_Imports(PropertyGroup):
    # GDTF Share Import profiles
    share_profiles: CollectionProperty(type=DMX_Devices_Import_Gdtf_Profile)
    selected_fixture: IntProperty(default=0)

    selected_mode: IntProperty(default=0)


# Add-on Module Registering

classes = (
    # Data Structures
    DMX_Devices_Import_Gdtf_Profile_Dmx_Mode,
    DMX_Devices_Import_Gdtf_Profile,
    DMX_Devices_Share_Imports,
    DMX_Devices,
    # Lists
    DMX_UL_Share_Fixtures,
    DMX_UL_Share_Fixtures_Dmx_Modes,
    DMX_UL_Local_Fixtures,
    # Operators
    DMX_OP_Import_Fixture_From_File,
    DMX_OP_Import_Fixture_From_Share,
    DMX_OP_Import_Fixture_Update_Share,
    DMX_OP_Delete_Local_Fixture,
    # Panel
    DMX_PT_Devices_Import,
    DMX_PT_Devices_Import_Profile_Detail,
    DMX_PT_Devices_Local_Fixtures,
)
