import bpy
import os
import shutil
from bpy.types import Operator, Menu

from bpy.props import IntProperty, StringProperty, CollectionProperty
from dmx.gdtf import *
import dmx.panels.profiles as Profiles


# Import Fixtures


class DMX_OP_Import_Fixture_From_Share(Operator):
    bl_label = "Import from Share"
    bl_description = "Import fixture from GDTF Share"
    bl_idname = "dmx.import_fixture_from_share"
    bl_options = {"UNDO"}

    index: IntProperty()

    def execute(self, context):
        #context.scene.dmx.profiles.import_from_share(self.index)
        Profiles.controller.DMX_Fixtures_Manager.import_from_share(self, self.index)
        DMX_GDTF.getManufacturerList()
        return {"FINISHED"}


class DMX_OP_Import_Fixture_Update_Share(Operator):
    bl_label = "Update GDTF Share index"
    bl_description = "Update data index of GDTF Share"
    bl_idname = "dmx.import_fixture_update_share"
    bl_options = {"UNDO"}

    def execute(self, context):
        Profiles.controller.DMX_Fixtures_Manager.update_share_index(self)
        return {"FINISHED"}


class DMX_OP_Import_Fixture_From_File(Operator):
    bl_label = "Import from file"
    bl_description = "Import fixture from local filesystem"
    bl_idname = "dmx.import_fixture_from_file"
    bl_options = {"UNDO"}

    filter_glob: StringProperty(default="*.gdtf", options={"HIDDEN"})

    directory: StringProperty(name="File Path", maxlen=1024, default="")

    files: CollectionProperty(name="Files", type=bpy.types.OperatorFileListElement)

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, "files")

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        folder_path = os.path.dirname(os.path.realpath(__file__))
        folder_path = os.path.join(folder_path, "..", "..", "..", "assets", "profiles")

        for file in self.files:
            file_path = os.path.join(self.directory, file.name)
            print("Importing GDTF Profile: %s" % file_path)
            shutil.copy(file_path, folder_path)
        Profiles.DMX_Fixtures_Local_Profile.loadLocal()
        #Patch.DMX_Patch_Profile.load()
        return {"FINISHED"}


class DMX_OP_Delete_Local_Fixture(Operator):
    bl_label = "Delete fixture"
    bl_description = "Delete fixture from local filesystem"
    bl_idname = "dmx.delete_local_fixture"
    bl_options = {"UNDO"}

    index: IntProperty()

    def execute(self, context):
        #context.scene.dmx.profiles.delete_local_fixture(self.index)
        Profiles.controller.DMX_Fixtures_Manager.delete_local_fixture(self, self.index)
        #Profiles.DMX_Patch_Controller.DMX_Fixtures_Manager.delete_local_fixture
        Profiles.DMX_Fixtures_Local_Profile.loadLocal()
        return {"FINISHED"}

class DMX_OP_Update_Local_Fixtures(Operator):
    bl_label = "Refresh files listing"
    bl_description = "Update list of local files"
    bl_idname = "dmx.update_local_fixtures"
    bl_options = {"UNDO"}

    def execute(self, context):
        DMX_GDTF.getManufacturerList()
        #DMX_Fixtures_Local_Profile.load()

        Profiles.DMX_Fixtures_Local_Profile.loadLocal()
        #Patch.DMX_Patch_Profile.load()
        return {"FINISHED"}
