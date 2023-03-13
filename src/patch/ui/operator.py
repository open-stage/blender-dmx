import bpy
from bpy.types import Operator, Menu

from bpy.props import ( IntProperty )

from src.i18n import DMX_i18n

# Source > Configure

class DMX_OP_Patch_Source_Configure(Operator):
    bl_label = DMX_i18n.OP_PATCH_UNIVERSE_ADD
    bl_description = DMX_i18n.OP_PATCH_UNIVERSE_ADD_DESC
    bl_idname = "dmx.patch_source_configure"
    bl_options = {'UNDO'}

    def execute(self, context):
        print('[OP: ADD UNIVERSE]')
        return {'FINISHED'}

# Universe > Add

class DMX_OP_Patch_Universe_Add(Operator):
    bl_label = DMX_i18n.OP_PATCH_UNIVERSE_ADD
    bl_description = DMX_i18n.OP_PATCH_UNIVERSE_ADD_DESC
    bl_idname = "dmx.patch_universe_add"
    bl_options = {'UNDO'}

    def execute(self, context):
        universes = bpy.context.scene.dmx.patch.universes
        universes.add()
        universes[-1].name = f'Universe {len(universes)}'
        for i, universe in enumerate(universes):
            universe.number = i+1
        return {'FINISHED'}

# Universe > Remove

class DMX_OP_Patch_Universe_Remove(Operator):
    bl_label = DMX_i18n.OP_PATCH_FIXTURE_REMOVE
    bl_description = DMX_i18n.OP_PATCH_FIXTURE_REMOVE_DESC
    bl_idname = "dmx.patch_universe_remove"
    bl_options = {'UNDO'}

    index: IntProperty()

    def execute(self, context):
        universes = bpy.context.scene.dmx.patch.universes
        universes.remove(self.index)
        for i, universe in enumerate(universes):
            universe.number = i+1
        return {'FINISHED'}

# Fixture > Add

class DMX_OP_Patch_Fixture_Add(Operator):
    bl_label = DMX_i18n.OP_PATCH_FIXTURE_ADD
    bl_description = DMX_i18n.OP_PATCH_FIXTURE_ADD_DESC
    bl_idname = "dmx.patch_fixture_add"
    bl_options = {'UNDO'}

    def execute(self, context):
        patch = bpy.context.scene.dmx.patch
        fixtures = patch.fixtures
        fixtures.add()
        fixtures[-1].id = patch.new_fixture_id()
        return {'FINISHED'}

# Fixture > Add Batch

class DMX_OP_Patch_Fixture_AddBatch(Operator):
    bl_label = DMX_i18n.OP_PATCH_FIXTURE_ADDBATCH
    bl_description = DMX_i18n.OP_PATCH_FIXTURE_ADDBATCH_DESC
    bl_idname = "dmx.patch_fixture_addbatch"
    bl_options = {'UNDO'}

    def execute(self, context):
        print('[OP: ADD FIXTURE BATCH]')
        return {'FINISHED'}

# Fixture > Remove

class DMX_OP_Patch_Fixture_Remove(Operator):
    bl_label = DMX_i18n.OP_PATCH_FIXTURE_REMOVE
    bl_description = DMX_i18n.OP_PATCH_FIXTURE_REMOVE_DESC
    bl_idname = "dmx.patch_fixture_remove"
    bl_options = {'UNDO'}

    index: IntProperty()

    def execute(self, context):
        bpy.context.scene.dmx.patch.fixtures.remove(self.index)
        return {'FINISHED'}

# Build Fixtures

class DMX_OP_Patch_Build(Operator):
    bl_label = DMX_i18n.OP_PATCH_BUILD
    bl_description = DMX_i18n.OP_PATCH_BUILD_DESC
    bl_idname = "dmx.patch_build"
    bl_options = {'UNDO'}

    def execute(self, context):
        bpy.context.scene.dmx.core.build_patch()
        return {'FINISHED'}