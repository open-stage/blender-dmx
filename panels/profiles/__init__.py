#    Copyright vanous
#
#    This file is part of BlenderDMX.
#
#    BlenderDMX is free software: you can redistribute it and/or modify it
#    under the terms of the GNU General Public License as published by the Free
#    Software Foundation, either version 3 of the License, or (at your option)
#    any later version.
#
#    BlenderDMX is distributed in the hope that it will be useful, but WITHOUT
#    ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
#    FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
#    more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program. If not, see <https://www.gnu.org/licenses/>.

from bpy.types import PropertyGroup
from bpy.props import CollectionProperty, IntProperty

from .data.share_profile import DMX_Fixtures_Import_Gdtf_Profile_Dmx_Mode, DMX_Fixtures_Import_Gdtf_Profile
from .data.local_profile import DMX_Fixtures_Local_ProfileMode, DMX_Fixtures_Local_Profile
from .ui.list import DMX_UL_Share_Fixtures, DMX_UL_Share_Fixtures_Dmx_Modes, DMX_UL_Local_Fixtures, DMX_UL_Local_Fixtures_Dmx_Modes
from .ui.operator import DMX_OP_Import_Fixture_From_Share, DMX_OP_Import_Fixture_Update_Share, DMX_OP_Import_Fixture_From_File, DMX_OP_Delete_Local_Fixture, DMX_OP_Update_Local_Fixtures
from .ui.panel import DMX_PT_Fixtures_Import, DMX_PT_Fixtures_Import_Profile_Detail, DMX_PT_Fixtures_Local_Fixtures, DMX_PT_Fixtures_Local_Profile_Detail, DMX_PT_Profiles_Holder
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
