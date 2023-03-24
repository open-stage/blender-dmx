import bpy
from bpy.types import Panel

from src.i18n import DMX_i18n
from src.icon import DMX_Icon

from .operator import ( DMX_OP_Patch_Universe_Add,
                        DMX_OP_Patch_Fixture_Add,
                        DMX_OP_Patch_Fixture_AddBatch,
                        DMX_OP_Patch_Build,
                        DMX_OP_Import_Fixture_Update_Share,
                        DMX_OP_Import_Fixture_From_File)
from src.lang import DMX_Lang
_ = DMX_Lang._

class DMX_PT_Patch(Panel):
    bl_label = DMX_i18n.PANEL_PATCH
    bl_idname = 'DMX_PT_Patch'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"
    
    def draw(self, context):
        layout = self.layout
        patch = context.scene.dmx.patch

        layout.label(
            text=DMX_i18n.PANEL_PATCH_UNIVERSES,
            icon=DMX_Icon.UNIVERSE
        )
        layout.template_list(
            "DMX_UL_Patch_Universes", "",
            patch, "universes",
            patch, "selected_universe",
            rows=4
        )

        layout.operator(
            DMX_OP_Patch_Universe_Add.bl_idname,
            icon=DMX_Icon.UNIVERSE
        )

        layout.label(
            text=DMX_i18n.PANEL_PATCH_FIXTURES,
            icon=DMX_Icon.FIXTURE
        )
        layout.template_list(
            "DMX_UL_Patch_Fixtures", "",
            patch, "fixtures",
            patch, "selected_fixture",
            rows=8
        )
        
        row = layout.row()
        row.operator(
            DMX_OP_Patch_Fixture_Add.bl_idname,
            icon=DMX_Icon.FIXTURE
        )
        row.operator(
            DMX_OP_Patch_Fixture_AddBatch.bl_idname,
            icon=DMX_Icon.FIXTURE_BATCH
        )

        layout.operator(
            DMX_OP_Patch_Build.bl_idname,
            icon=DMX_Icon.BUILD
        )

class DMX_PT_Patch_Import(Panel):
    bl_label = _("Fixures import")
    bl_idname = 'DMX_PT_Patch_Import'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"
    bl_parent_id = "DMX_PT_Patch"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        imports = context.window_manager.dmx.imports

        layout.template_list(
            "DMX_UL_Share_Fixtures", "",
            imports, "share_profiles",
            imports, "selected_fixture",
            rows=8
        )

        layout.operator(
            DMX_OP_Import_Fixture_Update_Share.bl_idname,
            icon=DMX_Icon.URL
        )
        layout.operator(
            DMX_OP_Import_Fixture_From_File.bl_idname,
            icon=DMX_Icon.FILE
        )

class DMX_PT_Patch_Import_Profile_Detail(Panel):
    bl_label = _("Fixure detail")
    bl_idname = 'DMX_PT_Patch_Import_Profile_Detail'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"
    bl_parent_id = "DMX_PT_Patch"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        imports = context.window_manager.dmx.imports
        profiles = imports.share_profiles
        selected = imports.selected_fixture
        if not profiles:
            return
        fixture=profiles[selected]

        col = layout.column()
        col.emboss = 'NONE'
        col.prop(fixture, "manufacturer")
        col.prop(fixture, "fixture")
        col.prop(fixture, "revision")
        col.prop(fixture, "uploader")
        col.prop(fixture, "creator")
        col.prop(fixture, "rating")
        layout.template_list(
            "DMX_UL_Share_Fixtures_Dmx_Modes", "",
            fixture, "modes",
            imports, "selected_mode",
        )
