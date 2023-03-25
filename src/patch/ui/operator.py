import bpy
import os
import shutil
from bpy.types import Operator, Menu

from bpy.props import IntProperty
from src import patch as Patch


from src.lang import DMX_Lang

_ = DMX_Lang._

from src.patch.controller import DMX_Patch_Controller
from src.lang import DMX_Lang

_ = DMX_Lang._

# Source > Configure


class DMX_OP_Patch_Source_Configure(Operator):
    bl_label = _("Add Universe")
    bl_description = _("Add a new Universe to the Patch.")
    bl_idname = "dmx.patch_source_configure"
    bl_options = {"UNDO"}

    def execute(self, context):
        context.scene.dmx.patch.configure_source()
        return {"FINISHED"}


# Universe > Add


class DMX_OP_Patch_Universe_Add(Operator):
    bl_label = _("Add Universe")
    bl_description = _("Add a new Universe to the Patch.")
    bl_idname = "dmx.patch_universe_add"
    bl_options = {"UNDO"}

    def execute(self, context):
        context.scene.dmx.patch.add_universe()
        return {"FINISHED"}


# Universe > Remove


class DMX_OP_Patch_Universe_Remove(Operator):
    bl_label = _("Remove Fixture")
    bl_description = _("Remove this Fixture from the Patch.")
    bl_idname = "dmx.patch_universe_remove"
    bl_options = {"UNDO"}

    index: IntProperty()

    def execute(self, context):
        print("self index", self.index)
        context.scene.dmx.patch.remove_universe(self.index)
        return {"FINISHED"}


# Fixture > Add


class DMX_OP_Patch_Fixture_Add(Operator):
    bl_label = _("Add Single Fixture")
    bl_description = _("Add a single new Fixture to the Patch.")
    bl_idname = "dmx.patch_fixture_add"
    bl_options = {"UNDO"}

    def execute(self, context):
        context.scene.dmx.patch.add_fixture()
        return {"FINISHED"}


# Fixture > Add Batch


class DMX_OP_Patch_Fixture_AddBatch(Operator):
    bl_label = _("Add Fixture Batch")
    bl_description = _("Add new Fixture Batch to the Patch.")
    bl_idname = "dmx.patch_fixture_addbatch"
    bl_options = {"UNDO"}

    def execute(self, context):
        context.scene.dmx.patch.add_fixture_batch()
        return {"FINISHED"}


# Fixture > Remove


class DMX_OP_Patch_Fixture_Remove(Operator):
    bl_label = _("Remove Fixture")
    bl_description = _("Remove this Fixture from the Patch.")
    bl_idname = "dmx.patch_fixture_remove"
    bl_options = {"UNDO"}

    index: IntProperty()

    def execute(self, context):
        context.scene.dmx.patch.remove_fixture(self.index)
        return {"FINISHED"}


# Build Fixtures


class DMX_OP_Patch_Build(Operator):
    bl_label = _("Build Fixtures")
    bl_description = _(
        "After completing the patch, you should click this button to build/update the fixture geometry."
    )
    bl_idname = "dmx.patch_build"
    bl_options = {"UNDO"}

    def execute(self, context):
        try:
            bpy.context.scene.dmx.core.build_patch()
        except Exception as e:
            self.report({"ERROR"}, str(e))
            raise e
            return {"CANCELLED"}
        return {"FINISHED"}
