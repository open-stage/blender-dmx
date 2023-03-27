import bpy
from bpy.types import Panel

from src.icon import DMX_Icon

from .operator import (
    DMX_OP_Patch_Universe_Add,
    DMX_OP_Patch_Fixture_Add,
    DMX_OP_Patch_Fixture_AddBatch,
    DMX_OP_Patch_Build,
)
from i18n import DMX_Lang

_ = DMX_Lang._


class DMX_PT_Patch(Panel):
    bl_label = _("DMX Patch")
    bl_idname = "DMX_PT_Patch"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout
        patch = context.scene.dmx.patch

        layout.label(text=_("Universes"), icon=DMX_Icon.UNIVERSE)
        layout.template_list(
            "DMX_UL_Patch_Universes",
            "",
            patch,
            "universes",
            patch,
            "selected_universe",
            rows=4,
        )

        layout.operator(DMX_OP_Patch_Universe_Add.bl_idname, icon=DMX_Icon.UNIVERSE)

        layout.label(text=_("Fixtures"), icon=DMX_Icon.FIXTURE)
        layout.template_list(
            "DMX_UL_Patch_Fixtures",
            "",
            patch,
            "fixtures",
            patch,
            "selected_fixture",
            rows=8,
        )

        row = layout.row()
        row.operator(DMX_OP_Patch_Fixture_Add.bl_idname, icon=DMX_Icon.FIXTURE)
        row.operator(
            DMX_OP_Patch_Fixture_AddBatch.bl_idname, icon=DMX_Icon.FIXTURE_BATCH
        )

        layout.operator(DMX_OP_Patch_Build.bl_idname, icon=DMX_Icon.BUILD)
