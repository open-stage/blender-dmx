import bpy
from bpy.types import UIList

from src.icon import DMX_Icon

from .operator import DMX_OP_Import_Fixture_From_Share, DMX_OP_Delete_Local_Fixture
from src.lang import DMX_Lang

_ = DMX_Lang._


class DMX_UL_Share_Fixtures(UIList):
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        self.use_filter_show = True
        layout.context_pointer_set("share_profiles", item)

        col = layout.column()
        col.emboss = "NONE"
        icon = DMX_Icon.COMMUNITY
        if item.uploader == "Manuf.":
            icon = DMX_Icon.FAKE_USER_ON
        col.prop(item, "name", text="", icon=icon)
        col = layout.column()
        col.operator(
            DMX_OP_Import_Fixture_From_Share.bl_idname, text="", icon=DMX_Icon.IMPORT
        ).index = index


class DMX_UL_Share_Fixtures_Dmx_Modes(UIList):
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        main_col = layout.column()
        main_col.emboss = "NONE"
        row = main_col.row()
        if index == 0:
            row.emboss = "PULLDOWN_MENU"
            col = row.column()
            col.ui_units_x = 5
            col.label(text=_("DMX Mode Name"))
            col = row.column()
            col.ui_units_x = 5
            col.label(text=_("Footprint"))
            row = main_col.row()

        col = row.column()
        col.label(text=f"{item.name}")
        col = row.column()
        col.label(text=f"{item.footprint}")


class DMX_UL_Local_Fixtures(UIList):
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        self.use_filter_show = True

        col = layout.column()
        col.emboss = "NONE"
        col.prop(item, "name", text="")
        col = layout.column()
        col.operator(
            DMX_OP_Delete_Local_Fixture.bl_idname, text="", icon=DMX_Icon.CANCEL
        ).index = index
