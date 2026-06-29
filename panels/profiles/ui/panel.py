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

import bpy
from bpy.types import Panel

from ....i18n import DMX_Lang
from ....icon import DMX_Icon
from .operator import DMX_OP_Update_Local_Fixtures

_ = DMX_Lang._


class DMX_PT_Fixtures_Local_Fixtures(Panel):
    bl_label = _("Local Fixture files")
    bl_parent_id = "DMX_PT_Profiles"
    bl_idname = "DMX_PT_Local_Fixtures"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"
    # bl_parent_id = "DMX_PT_Patch"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout

        imports = bpy.context.window_manager.dmx.imports

        layout.template_list(
            "DMX_UL_Local_Fixtures",
            "",
            imports,
            "local_profiles",
            imports,
            "selected_local_fixture",
            rows=8,
        )

        layout.operator(
            DMX_OP_Update_Local_Fixtures.bl_idname, icon=DMX_Icon.FILE_REFRESH
        )
        layout.operator(
            "dmx.import_gdtf_into_scene", text=_("Import GDTF Profile"), icon="IMPORT"
        )


class DMX_PT_Fixtures_Local_Profile_Detail(Panel):
    bl_label = _("Local Fixture details")
    bl_parent_id = "DMX_PT_Profiles"
    bl_idname = "DMX_PT_Fixtures_Local_Profile_Detail"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"
    bl_parent_id = "DMX_PT_Local_Fixtures"
    # bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        local_profiles = bpy.context.window_manager.dmx.imports.local_profiles
        selected_fixture = bpy.context.window_manager.dmx.imports.selected_local_fixture
        imports = context.window_manager.dmx.imports
        if not local_profiles:
            return
        if selected_fixture >= len(local_profiles):
            # this happens after deleting from the bottom of the list
            return

        fixture = local_profiles[selected_fixture]

        col = layout.column()
        col.emboss = "NONE"
        col.prop(fixture, "name")
        col.prop(fixture, "filename")

        layout.template_list(
            "DMX_UL_Local_Fixtures_Dmx_Modes",
            "",
            fixture,
            "modes",
            imports,
            "local_fixture_selected_mode",
        )


class DMX_PT_Profiles_Holder(Panel):
    bl_label = _("Profiles")
    bl_idname = "DMX_PT_Profiles"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        pass

    @classmethod
    def poll(self, context):
        dmx = context.scene.dmx
        return dmx.collection is not None
