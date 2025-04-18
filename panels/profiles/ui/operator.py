# Copyright (C) 2023 vanous
#
# This file is part of BlenderDMX.
#
# BlenderDMX is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# BlenderDMX is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <https://www.gnu.org/licenses/>.

import os
import shutil

import bpy
from bpy.props import CollectionProperty, IntProperty, StringProperty
from bpy.types import Operator

from ....gdtf_file import DMX_GDTF_File
from ....i18n import DMX_Lang
from ....logging import DMX_Log
from ....panels import profiles as Profiles

_ = DMX_Lang._

# Import Fixtures


class DMX_OP_Import_Fixture_From_Share(Operator):
    bl_label = _("Import from Share")
    bl_description = _("Import fixture from GDTF Share")
    bl_idname = "dmx.import_fixture_from_share"
    bl_options = {"UNDO"}

    index: IntProperty()

    def execute(self, context):
        Profiles.controller.DMX_Fixtures_Manager.import_from_share(self, self.index)
        DMX_GDTF_File.getManufacturerList()
        return {"FINISHED"}


class DMX_OP_Import_Fixture_Update_Share(Operator):
    bl_label = _("Update GDTF Share index")
    bl_description = _("Update data index of GDTF Share")
    bl_idname = "dmx.import_fixture_update_share"
    bl_options = {"UNDO"}

    def execute(self, context):
        Profiles.controller.DMX_Fixtures_Manager.update_share_index(self)
        return {"FINISHED"}


class DMX_OP_Delete_Local_Fixture(Operator):
    bl_label = _("Delete fixture")
    bl_description = _("Delete fixture from local filesystem")
    bl_idname = "dmx.delete_local_fixture"
    bl_options = {"UNDO"}

    index: IntProperty()

    def execute(self, context):
        Profiles.controller.DMX_Fixtures_Manager.delete_local_fixture(self, self.index)
        DMX_GDTF_File.getManufacturerList()
        Profiles.DMX_Fixtures_Local_Profile.loadLocal()
        return {"FINISHED"}


class DMX_OP_Update_Local_Fixtures(Operator):
    bl_label = _("Refresh files listing")
    bl_description = _("Update list of local files")
    bl_idname = "dmx.update_local_fixtures"
    bl_options = {"UNDO"}

    def execute(self, context):
        DMX_GDTF_File.getManufacturerList()
        Profiles.DMX_Fixtures_Local_Profile.loadLocal(write_cache=True)
        return {"FINISHED"}
