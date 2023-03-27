import bpy
from bpy.types import UIList

from src.icon import DMX_Icon

from .operator import (
    DMX_OP_Patch_Source_Configure,
    DMX_OP_Patch_Fixture_Remove,
    DMX_OP_Patch_Universe_Remove,
)
from .menu import DMX_MT_Patch_SelectUniverse, DMX_MT_Patch_SelectMode
from i18n import DMX_Lang

_ = DMX_Lang._


class DMX_UL_Patch_Fixtures(UIList):
    cols = [1.25, 3, 5, 2, 2, 1.5, 3.25]

    def _split_row(self, layout, factors):
        cols = []
        for i in range(len(factors[:-1])):
            f = factors[i] / sum(factors[i:])
            split = layout.split(factor=f)
            col = split.column()
            cols.append(col)
            layout = split.column()
        cols.append(layout)
        return cols

    def draw_header(self, context, layout):
        layout.emboss = "PULLDOWN_MENU"
        col = layout.column()
        col.ui_units_x = 1
        col.label(text="")

        col = layout.column()
        col.ui_units_x = 2
        col.label(text="ID")

        col = layout.column()
        col.ui_units_x = 10
        col.label(text="Name")

        col = layout.column()
        col.ui_units_x = 16
        col.label(text="Profile")

        col = layout.column()
        col.ui_units_x = 7
        col.label(text="Mode")

    def _draw_icon(self, layout, icon):
        col = layout.column()
        col.ui_units_x = 1
        col.label(icon=icon)
        return col

    def _draw_id_name_profile_mode(self, cols, item, patch):
        cols[0].emboss = 'NONE'
        cols[0].alert = len(item.name) == 0 or len(item.profile) == 0
        cols[0].prop(item, 'id', text='', slider=True)

        cols[1].prop(item, "name", text="")

        cols[2].prop_search(
            item, "profile", patch, "profiles", text="", icon=DMX_Icon.GDTF_PROFILE
        )

        if len(item.profile):
            cols[3].menu(
                DMX_MT_Patch_SelectMode.bl_idname,
                text=item.get_mode_str(mini=True) or "",
            )

    def _draw_break(self, context, cols, item, break_index):
        cols[4].prop(item.breaks[break_index], 'address', text = '')

        universe = item.get_universe_str(context, break_index, mini=True)
        cols[5].context_pointer_set("fixture_break", item.breaks[break_index])
        cols[5].alert = (universe != None)
        cols[5].menu(
            DMX_MT_Patch_SelectUniverse.bl_idname,
            text = universe or ''
        )

    def _draw_ops(self, cols, item, index, is_batch_root=False):
        row = cols[6].row()
        col = row.column()
        col.ui_units_x = 1
        if (is_batch_root):
            col.label(text='')
        else:
            col.prop(item, 'gel_color', text='')
        col = row.column()
        col.ui_units_x = 1
        if (is_batch_root):
            col.label(text='')
        else:
            col.prop(item, 'create_lights', text='', icon=DMX_Icon.CREATE_LIGHTS)
        col = row.column()
        col.ui_units_x = 1
        col.operator(
            DMX_OP_Patch_Fixture_Remove.bl_idname, text="", icon=DMX_Icon.REMOVE
        ).index = index

    def draw_fixture_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        patch = context.scene.dmx.patch
        main_col = layout.column()
        row = main_col.row()

        icon = self._draw_icon(row, icon=DMX_Icon.FIXTURE)
        icon.alert = len(item.name) == 0 or len(item.profile) == 0

        cols = self._split_row(row, DMX_UL_Patch_Fixtures.cols)
        
        self._draw_id_name_profile_mode(cols, item, patch)
        if (len(item.breaks)):
            self._draw_break(context, cols, item, 0)      
        self._draw_ops(cols, item, index)

        if (len(item.breaks) > 1):
            for break_i in range(1,len(item.breaks)):
                row = main_col.row()
                self.draw_extra_break(context, row, item, break_i)

    def draw_extra_break(self, context, layout, item, break_i):
        self._draw_icon(layout, DMX_Icon.BREAK)
        cols = self._split_row(layout, DMX_UL_Patch_Fixtures.cols)
        self._draw_break(context, cols, item, break_i)
    
    def draw_batch_item(self, context, layout, item, is_root = False):
        batch = item.get_batch(context)
        icon = self._draw_icon(layout, DMX_Icon.FIXTURE)
        icon.alert = len(batch.name) == 0 or (item.batch_index == 0 and len(item.profile) == 0)
        
        cols = self._split_row(layout, DMX_UL_Patch_Fixtures.cols)

        cols[0].emboss = "NONE"
        cols[0].alert = len(batch.name) == 0 or (
            item.batch_index == 0 and len(item.profile) == 0
        )
        cols[0].enabled = False
        cols[0].prop(item, "id", text="", slider=True)

        cols[1].emboss = "NONE"
        cols[1].ui_units_x = 10
        cols[1].label(text=f"{batch.name} {item.batch_index+1}")

        cols[4].enabled = is_root or (not batch.sequential)
        cols[4].prop(item, "address", text="")

        cols[5].enabled = is_root or (not batch.sequential)
        cols[5].menu(
            DMX_MT_Patch_SelectUniverse.bl_idname,
            text=item.get_universe_str(context, mini=True),
        )

        row = cols[6].row()
        col = row.column()
        col.ui_units_x = 1
        col.prop(item, "gel_color", text="")
        col = row.column()
        col.ui_units_x = 1
        col.prop(item, "create_lights", text="", icon=DMX_Icon.CREATE_LIGHTS)
        col = row.column()
        col.ui_units_x = 1
        col.operator(
            DMX_OP_Patch_Fixture_Remove.bl_idname, text="", icon=DMX_Icon.REMOVE
        ).index = index

    def draw_batch_root_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        patch = context.scene.dmx.patch
        batch = item.get_batch(context)

        main_col = layout.column()
        row = main_col.row()

        col = row.column()
        col.alert = len(batch.name) == 0 or len(item.profile) == 0
        col.prop(batch, "expand", text="", icon=DMX_Icon.FIXTURE_BATCH)

        cols = self._split_row(row, DMX_UL_Patch_Fixtures.cols)

        self._draw_id_name_profile_mode(cols, item, patch)

        if not batch.expand:
            if (len(item.breaks)):
                self._draw_break(context, cols, item, 0)

        # if (batch.expand):
        #     cols[4].label(text='')
        # else:
        #     cols[4].prop(item, 'address', text='')

        # if (batch.expand):
        #     cols[5].label(text='')
        # else:
        #     cols[5].menu(
        #         DMX_MT_Patch_SelectUniverse.bl_idname,
        #         text = item.get_universe_str(context, mini=True)
        #     )

        self._draw_ops(cols, item, index, batch.expand)

        # if (batch.expand):
        #     row = main_col.row()
        #     self.draw_batch_item(context, row, item, True)

    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        main_col = layout.column()
        row = main_col.row()
        if index == 0:
            self.draw_header(context, row)
            row = main_col.row()

        row.context_pointer_set("fixture", item)
        if item.batch == -1:
            self.draw_fixture_item(
                context, row, data, item, icon, active_data, active_propname, index
            )
        else:
            if item.batch_index == 0:
                self.draw_batch_root_item(
                    context, row, data, item, icon, active_data, active_propname, index
                )
            else:
                self.draw_batch_item(context, row, item)

    def filter_items(self, context, data, propname):
        items = getattr(data, propname)

        expanded_batches = []
        for item in items:
            if not item.batch_index == 0:
                continue
            batch = item.get_batch(context)
            if batch.expand:
                expanded_batches.append(item.batch)

        filtered = [self.bitflag_filter_item] * len(items)
        for i, item in enumerate(items):
            if item.batch == -1:
                continue
            if item.batch in expanded_batches:
                continue
            if item.batch_index > 0:
                filtered[i] &= ~self.bitflag_filter_item
        ordered = []
        return filtered, ordered


class DMX_UL_Patch_Universes(UIList):
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        layout.context_pointer_set("universe", item)

        col = layout.column()
        col.alert = len(item.name) == 0
        col.label(icon=DMX_Icon.UNIVERSE)

        col = layout.column()
        col.ui_units_x = 1
        col.label(text=str(item.number))

        col = layout.column()
        col.prop(item, "name", text="")

        col = layout.column()
        col.prop_menu_enum(item, "source", text=item.get_source_str())

        col = layout.column()
        col.operator(
            DMX_OP_Patch_Source_Configure.bl_idname, icon=DMX_Icon.CONFIGURE, text=""
        )

        col = layout.column()
        col.operator(
            DMX_OP_Patch_Universe_Remove.bl_idname, text="", icon=DMX_Icon.REMOVE
        ).index = index
