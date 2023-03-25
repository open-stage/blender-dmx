import bpy
import os
import shutil
from bpy.types import Operator, Menu

from bpy.props import ( IntProperty)
from src import patch as Patch

from src.i18n import DMX_i18n
from src.patch.controller import DMX_Patch_Controller
from src.lang import DMX_Lang
_ = DMX_Lang._

# Source > Configure

class DMX_OP_Patch_Source_Configure(Operator):
    bl_label = DMX_i18n.OP_PATCH_UNIVERSE_ADD
    bl_description = DMX_i18n.OP_PATCH_UNIVERSE_ADD_DESC
    bl_idname = "dmx.patch_source_configure"
    bl_options = {'UNDO'}

    def execute(self, context):
        context.scene.dmx.patch.configure_source()
        return {'FINISHED'}

# Universe > Add

class DMX_OP_Patch_Universe_Add(Operator):
    bl_label = DMX_i18n.OP_PATCH_UNIVERSE_ADD
    bl_description = DMX_i18n.OP_PATCH_UNIVERSE_ADD_DESC
    bl_idname = "dmx.patch_universe_add"
    bl_options = {'UNDO'}

    def execute(self, context):
        context.scene.dmx.patch.add_universe()
        return {'FINISHED'}

# Universe > Remove

class DMX_OP_Patch_Universe_Remove(Operator):
    bl_label = DMX_i18n.OP_PATCH_FIXTURE_REMOVE
    bl_description = DMX_i18n.OP_PATCH_FIXTURE_REMOVE_DESC
    bl_idname = "dmx.patch_universe_remove"
    bl_options = {'UNDO'}

    index: IntProperty()

    def execute(self, context):
        print("self index", self.index)
        context.scene.dmx.patch.remove_universe(self.index)
        return {'FINISHED'}

# Fixture > Add

class DMX_OP_Patch_Fixture_Add(Operator):
    bl_label = DMX_i18n.OP_PATCH_FIXTURE_ADD
    bl_description = DMX_i18n.OP_PATCH_FIXTURE_ADD_DESC
    bl_idname = "dmx.patch_fixture_add"
    bl_options = {'UNDO'}

    def execute(self, context):
        context.scene.dmx.patch.add_fixture()
        return {'FINISHED'}

# Fixture > Add Batch

class DMX_OP_Patch_Fixture_AddBatch(Operator):
    bl_label = DMX_i18n.OP_PATCH_FIXTURE_ADDBATCH
    bl_description = DMX_i18n.OP_PATCH_FIXTURE_ADDBATCH_DESC
    bl_idname = "dmx.patch_fixture_addbatch"
    bl_options = {'UNDO'}

    def execute(self, context):
        context.scene.dmx.patch.add_fixture_batch()
        return {'FINISHED'}

# Fixture > Remove

class DMX_OP_Patch_Fixture_Remove(Operator):
    bl_label = DMX_i18n.OP_PATCH_FIXTURE_REMOVE
    bl_description = DMX_i18n.OP_PATCH_FIXTURE_REMOVE_DESC
    bl_idname = "dmx.patch_fixture_remove"
    bl_options = {'UNDO'}

    index: IntProperty()

    def execute(self, context):
        context.scene.dmx.patch.remove_fixture(self.index)
        return {'FINISHED'}

# Build Fixtures

class DMX_OP_Patch_Build(Operator):
    bl_label = DMX_i18n.OP_PATCH_BUILD
    bl_description = DMX_i18n.OP_PATCH_BUILD_DESC
    bl_idname = "dmx.patch_build"
    bl_options = {'UNDO'}

    def execute(self, context):
        try:
            bpy.context.scene.dmx.core.build_patch()
        except Exception as e:
            self.report({"ERROR"}, str(e))
            raise e
            return {'CANCELLED'}
        return {'FINISHED'}

