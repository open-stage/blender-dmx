import bpy
import os
import shutil
from bpy.types import Operator, Menu

from bpy.props import ( IntProperty, StringProperty, CollectionProperty )
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

# Import Fixtures

class DMX_OP_Import_Fixture_From_Share(Operator):
    bl_label = _("Import from Share")
    bl_description = _("Import fixture from GDTF Share")
    bl_idname = "dmx.import_fixture_from_share"
    bl_options = {'UNDO'}

    index: IntProperty()

    def execute(self, context):
        context.scene.dmx.patch.import_from_share(self.index)
        return {'FINISHED'}

class DMX_OP_Import_Fixture_Update_Share(Operator):
    bl_label = _("Update GDTF Share index")
    bl_description = _("Update data index of GDTF Share")
    bl_idname = "dmx.import_fixture_update_share"
    bl_options = {'UNDO'}

    def execute(self, context):
        context.scene.dmx.patch.update_share_index()
        return {'FINISHED'}

class DMX_OP_Import_Fixture_From_File(Operator):
    bl_label = _("Import from file")
    bl_description = _("Import fixture from local filesystem")
    bl_idname = "dmx.import_fixture_from_file"
    bl_options = {'UNDO'}

    filter_glob: StringProperty(default="*.gdtf", options={'HIDDEN'})

    directory: StringProperty(
        name = _("File Path"),
        maxlen = 1024,
        default = "" )

    files: CollectionProperty(
        name = _("Files"),
        type = bpy.types.OperatorFileListElement
    )

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, "files")

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        folder_path = os.path.dirname(os.path.realpath(__file__))
        folder_path = os.path.join(folder_path, '..', '..', '..', 'assets', 'profiles')

        for file in self.files:
            file_path = os.path.join(self.directory, file.name)
            print('Importing GDTF Profile: %s' % file_path)
            shutil.copy(file_path, folder_path)
        Patch.DMX_Patch_Profile.load()
        return {'FINISHED'}


