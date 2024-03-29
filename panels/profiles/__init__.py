import bpy
from bpy.types import PropertyGroup
from bpy.props import CollectionProperty, IntProperty

from .data.share_profile import *
from .data.local_profile import *
from .ui.list import *
from .ui.operator import *
from .ui.panel import *
from .controller.manager import *


from .controller import DMX_Fixtures_Manager

# Module Data Structure


class DMX_Fixtures(PropertyGroup, DMX_Fixtures_Manager):
    placeholder: IntProperty(default=0)
    # do not erase. This rna class provides access to the DMX_Fixtures_Manager


class DMX_Fixtures_Imports(PropertyGroup):
    # GDTF Share Import profiles
    share_profiles: CollectionProperty(type=DMX_Fixtures_Import_Gdtf_Profile)
    local_profiles: CollectionProperty(type=DMX_Fixtures_Local_Profile)
    selected_share_fixture: IntProperty(default=0)
    selected_local_fixture: IntProperty(default=0)
    selected_mode: IntProperty(default=0)
    local_fixture_selected_mode: IntProperty(default=0)

classes = (
    # Data Structures
    DMX_Fixtures_Local_ProfileMode,
    DMX_Fixtures_Import_Gdtf_Profile_Dmx_Mode,
    DMX_Fixtures_Import_Gdtf_Profile,
    DMX_Fixtures_Local_Profile,
    DMX_Fixtures_Imports,
    # Lists
    DMX_UL_Share_Fixtures,
    DMX_UL_Share_Fixtures_Dmx_Modes,
    DMX_UL_Local_Fixtures,
    DMX_UL_Local_Fixtures_Dmx_Modes,
    # Operators
    DMX_OP_Import_Fixture_From_File,
    DMX_OP_Import_Fixture_From_Share,
    DMX_OP_Import_Fixture_Update_Share,
    DMX_OP_Delete_Local_Fixture,
    DMX_OP_Update_Local_Fixtures,
    # Panel
    DMX_PT_Profiles_Holder,
    DMX_PT_Fixtures_Import,
    DMX_PT_Fixtures_Import_Profile_Detail,
    DMX_PT_Fixtures_Local_Fixtures,
    DMX_PT_Fixtures_Local_Profile_Detail,
)
