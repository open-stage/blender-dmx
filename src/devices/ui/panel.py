import bpy
from bpy.types import Panel

from src.icon import DMX_Icon

from .operator import (
    DMX_OP_Import_Fixture_Update_Share,
    DMX_OP_Import_Fixture_From_File,
)
from src.lang import DMX_Lang

_ = DMX_Lang._


class DMX_PT_Devices_Import(Panel):
    bl_label = _("DMX Fixtures import")
    bl_idname = "DMX_PT_Patch_Import"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    # bl_parent_id = "DMX_PT_Patch"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        imports = context.window_manager.dmx.imports

        layout.template_list(
            "DMX_UL_Share_Fixtures",
            "",
            imports,
            "share_profiles",
            imports,
            "selected_fixture",
            rows=8,
        )

        layout.operator(DMX_OP_Import_Fixture_Update_Share.bl_idname, icon=DMX_Icon.URL)
        layout.operator(DMX_OP_Import_Fixture_From_File.bl_idname, icon=DMX_Icon.FILE)


class DMX_PT_Devices_Import_Profile_Detail(Panel):
    bl_label = _("Fixture details")
    bl_idname = "DMX_PT_Patch_Import_Profile_Detail"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    bl_parent_id = "DMX_PT_Patch_Import"
    # bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        imports = context.window_manager.dmx.imports
        profiles = imports.share_profiles
        selected = imports.selected_fixture
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


class DMX_PT_Devices_Local_Fixtures(Panel):
    bl_label = _("DMX Local fixtures")
    bl_idname = "DMX_PT_Local_Fixtures"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    # bl_parent_id = "DMX_PT_Patch"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        patch = context.scene.dmx.patch

        layout.template_list(
            "DMX_UL_Local_Fixtures",
            "",
            patch,
            "profiles",
            patch,
            "selected_fixture",
            rows=8,
        )
