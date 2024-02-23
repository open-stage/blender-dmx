import bpy
import os
import shutil
from bpy.types import Operator, Menu

from bpy.props import IntProperty, StringProperty, CollectionProperty
from dmx.gdtf import *
import dmx.panels.profiles as Profiles
from dmx.logging import *

from dmx.i18n import DMX_Lang
_ = DMX_Lang._

# Import Fixtures


class DMX_OP_Import_Fixture_From_Share(Operator):
    bl_label = _("Import from Share")
    bl_description = _("Import fixture from GDTF Share")
    bl_idname = "dmx.import_fixture_from_share"
    bl_options = {"UNDO"}

    index: IntProperty()

    def execute(self, context):
        Profiles.controller.DMX_Fixtures_Manager.import_from_share(self, self.index)
        DMX_GDTF.getManufacturerList()
        return {"FINISHED"}


class DMX_OP_Import_Fixture_Update_Share(Operator):
    bl_label = _("Update GDTF Share index")
    bl_description = _("Update data index of GDTF Share")
    bl_idname = "dmx.import_fixture_update_share"
    bl_options = {"UNDO"}

    def execute(self, context):
        Profiles.controller.DMX_Fixtures_Manager.update_share_index(self)
        return {"FINISHED"}


class DMX_OP_Import_Fixture_From_File(Operator):
    bl_label = _("Import from file")
    bl_description = _("Import fixture from local filesystem")
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
            DMX_Log.log.info("Importing GDTF Profile: {}".format(file_path))
            shutil.copy(file_path, folder_path)
        DMX_GDTF.getManufacturerList()
        Profiles.DMX_Fixtures_Local_Profile.loadLocal()
        return {"FINISHED"}


class DMX_OP_Delete_Local_Fixture(Operator):
    bl_label = _("Delete fixture")
    bl_description = _("Delete fixture from local filesystem")
    bl_idname = "dmx.delete_local_fixture"
    bl_options = {"UNDO"}

    index: IntProperty()

    def execute(self, context):
        Profiles.controller.DMX_Fixtures_Manager.delete_local_fixture(self, self.index)
        DMX_GDTF.getManufacturerList()
        Profiles.DMX_Fixtures_Local_Profile.loadLocal()
        return {"FINISHED"}


class DMX_OP_Update_Local_Fixtures(Operator):
    bl_label = _("Refresh files listing")
    bl_description = _("Update list of local files")
    bl_idname = "dmx.update_local_fixtures"
    bl_options = {"UNDO"}

    def execute(self, context):
        DMX_GDTF.getManufacturerList()
        Profiles.DMX_Fixtures_Local_Profile.loadLocal(show_errors=True)
        return {"FINISHED"}
