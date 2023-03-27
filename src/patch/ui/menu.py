import bpy
from bpy.types import Operator, Menu
from bpy.props import IntProperty, StringProperty


from i18n import DMX_Lang

_ = DMX_Lang._

from src.patch.controller import DMX_Patch_Controller

# [Select Universe]


class DMX_OP_MT_Patch_SelectUniverse(Operator):
    bl_label = _("DMX Universe")
    bl_idname = "dmx.patch_selectuniverse"

    universe: IntProperty()

    def execute(self, context):
        context.fixture_break.universe = self.universe + 1
        return {"FINISHED"}


class DMX_MT_Patch_SelectUniverse(Menu):
    bl_label = _("DMX Universe")
    bl_idname = "DMX_MT_Patch_SelectUniverse"

    def draw(self, context):
        layout = self.layout
        patch = context.scene.dmx.patch
        layout.context_pointer_set("fixture", context.fixture)
        layout.context_pointer_set("fixture_break", context.fixture_break)
        for i, universe in enumerate(patch.universes):
            row = layout.row()
            op = row.operator(
                DMX_OP_MT_Patch_SelectUniverse.bl_idname,
                text=f"{universe.number}: {universe.name}",
            )
            op.universe = i


# [Select Mode]


class DMX_OP_MT_Patch_SelectMode(Operator):
    bl_label = _("DMX Universe")
    bl_idname = "dmx.patch_fixture_selectmode"

    mode: StringProperty()

    def execute(self, context):
        context.fixture.mode = self.mode
        DMX_Patch_Controller.on_select_mode(context.fixture, context)
        return {"FINISHED"}


class DMX_MT_Patch_SelectMode(Menu):
    bl_label = _("DMX Universe")
    bl_idname = "DMX_MT_Patch_SelectMode"

    profile: StringProperty()

    def draw(self, context):
        layout = self.layout
        patch = context.scene.dmx.patch

        profile_name = context.fixture.profile
        if len(profile_name) == 0:
            layout.label(text=_("No Profile selected"))
            return

        profile = patch.profiles[profile_name]
        modes = profile.modes

        layout.context_pointer_set("fixture", context.fixture)
        for mode in modes:
            row = layout.row()

            breaks = [b.n_channels for b in mode.breaks]
            if len(breaks) == 1:
                n_channels = str(breaks[0])
            else:
                n_channels = "+".join(str(b) for b in breaks)

            op = row.operator(
                DMX_OP_MT_Patch_SelectMode.bl_idname,
                text=f"{mode.name}, {n_channels} channels",
            )
            op.mode = mode.name
