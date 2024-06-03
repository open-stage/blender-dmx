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

import bpy
from bpy.types import Panel

from ....icon import DMX_Icon

from .operator import (
    DMX_OP_Import_Fixture_Update_Share,
    DMX_OP_Update_Local_Fixtures,
)
from ....in_gdtf import DMX_OT_Import_GDTF

from ....i18n import DMX_Lang

_ = DMX_Lang._


class DMX_PT_Fixtures_Import(Panel):
    bl_label = _("GDTF Share")
    bl_idname = "DMX_PT_Fixtures_Import"
    bl_parent_id = "DMX_PT_Profiles"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"
    # bl_parent_id = "DMX_PT_Patch"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        imports = context.window_manager.dmx.imports
        if not bpy.app.online_access:
            row = layout.row()
            row.label(text = _("You must Allow Online access for this to work:"))
            prefs = context.preferences
            system = prefs.system
            row = layout.row()
            row.prop(system, "use_online_access", text="Allow Online Access")
        else:
            layout.template_list(
                "DMX_UL_Share_Fixtures",
                "",
                imports,
                "share_profiles",
                imports,
                "selected_share_fixture",
                rows=8,
            )

            layout.operator(DMX_OP_Import_Fixture_Update_Share.bl_idname, icon=DMX_Icon.URL)


class DMX_PT_Fixtures_Import_Profile_Detail(Panel):
    bl_label = _("Fixture details")
    bl_idname = "DMX_PT_Fixtures_Import_Profile_Detail"
    bl_space_type = "VIEW_3D"
    bl_parent_id = "DMX_PT_Profiles"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"
    bl_parent_id = "DMX_PT_Fixtures_Import"
    # bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        imports = context.window_manager.dmx.imports
        profiles = imports.share_profiles
        selected = imports.selected_share_fixture
        if not profiles:
            return
        fixture = profiles[selected]

        col = layout.column()
        col.emboss = "NONE"
        col.prop(fixture, "manufacturer")
        col.prop(fixture, "fixture")
        col.prop(fixture, "revision")
        col.prop(fixture, "uploader")
        col.prop(fixture, "creator")
        col.prop(fixture, "rating")
        layout.template_list(
            "DMX_UL_Share_Fixtures_Dmx_Modes",
            "",
            fixture,
            "modes",
            imports,
            "selected_mode",
        )


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

        layout.operator(DMX_OP_Update_Local_Fixtures.bl_idname, icon=DMX_Icon.FILE_REFRESH)
        layout.operator("dmx.import_gdtf_into_scene", text=_("Import GDTF Profile"), icon="IMPORT")

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
        layout = self.layout
        dmx = context.scene.dmx

    @classmethod
    def poll(self, context):
        dmx = context.scene.dmx
        return dmx.collection is not None
