import bpy
from bpy.types import Operator, Menu
from bpy.props import ( IntProperty,
                        StringProperty )

from src.i18n import DMX_i18n

# [Select Universe]

class DMX_OP_MT_Patch_SelectUniverse(Operator):
    bl_label = DMX_i18n.MENU_PATCH_SELECT_UNIVERSE_OP
    bl_idname = "dmx.patch_selectuniverse"

    universe: IntProperty()

    def execute(self, context):
        context.fixture.universe = self.universe + 1
        return {'FINISHED'}

class DMX_MT_Patch_SelectUniverse(Menu):
    bl_label = DMX_i18n.MENU_PATCH_SELECT_UNIVERSE
    bl_idname = "DMX_MT_Patch_SelectUniverse"

    def draw(self, context):
        layout = self.layout
        patch = context.scene.dmx.patch
        layout.context_pointer_set("fixture", context.fixture)
        for i, universe in enumerate(patch.universes):
            row = layout.row()
            op = row.operator(
                DMX_OP_MT_Patch_SelectUniverse.bl_idname,
                text=f"{universe.number}: {universe.name}"
            ).universe = i

# [Select Mode]

class DMX_OP_MT_Patch_SelectMode(Operator):
    bl_label = DMX_i18n.MENU_PATCH_SELECT_MODE_OP
    bl_idname = "dmx.patch_fixture_selectmode"

    name: StringProperty()
    n_channels: IntProperty()

    def execute(self, context):
        context.fixture.mode = self.name
        context.fixture.n_channels = self.n_channels
        return {'FINISHED'}

class DMX_MT_Patch_SelectMode(Menu):
    bl_label = DMX_i18n.MENU_PATCH_SELECT_MODE
    bl_idname = "DMX_MT_Patch_SelectMode"

    def draw(self, context):
        layout = self.layout
        patch = context.scene.dmx.patch
        
        # TODO: read modes from profile
        modes = [
            ('Default', 12),
            ('Special', 24)
        ]

        layout.context_pointer_set("fixture", context.fixture)
        for name, n_channels in modes:
            row = layout.row()
            op = row.operator(
                DMX_OP_MT_Patch_SelectMode.bl_idname,
                text=f'{name}, {n_channels} channels'
            )
            op.name = name
            op.n_channels = n_channels