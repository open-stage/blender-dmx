import bpy
from bpy.types import Panel

from src.i18n import DMX_i18n
from src.icon import DMX_Icon

from .operator import ( DMX_OP_Patch_Universe_Add,
                        DMX_OP_Patch_Fixture_Add,
                        DMX_OP_Patch_Fixture_AddBatch,
                        DMX_OP_Patch_Build,
                        DMX_OP_Import_Fixture_Update_Share,
                        DMX_OP_Import_Fixture_From_File,
                        DMX_OP_Save_Patch_Api_Key)
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

        layout.label(
            text="Fixtures import",
            icon=DMX_Icon.IMPORT
        )
        layout.template_list(
            "DMX_UL_Share_Fixtures", "",
            patch, "share_profiles",
            patch, "selected_fixture",
            rows=8
        )
        row = layout.row()

        row.prop(context.window_manager.dmx, 'share_api_key', text = '')

        layout.operator(
            DMX_OP_Save_Patch_Api_Key.bl_idname,
            icon=DMX_Icon.URL
        )

        layout.operator(
            DMX_OP_Import_Fixture_Update_Share.bl_idname,
            icon=DMX_Icon.URL
        )
        layout.operator(
            DMX_OP_Import_Fixture_From_File.bl_idname,
            icon=DMX_Icon.FILE
        )
