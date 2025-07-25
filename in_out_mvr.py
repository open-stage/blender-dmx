# Copyright (C) 2024 vanous
#
# This file is part of BlenderDMX.
#
# BlenderDMX is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# BlenderDMX is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <https://www.gnu.org/licenses/>.

import os
import shutil
from types import SimpleNamespace
import uuid as py_uuid
from pathlib import Path

import bpy
from bpy_extras.io_utils import ExportHelper, ImportHelper

from .logging_setup import DMX_Log

if bpy.app.version >= (4, 2):
    from bpy_extras.io_utils import poll_file_object_drop

from threading import Timer

from bpy.props import BoolProperty, CollectionProperty, StringProperty
from bpy.types import Operator

from .i18n import DMX_Lang

_ = DMX_Lang._


def createDMXcollection():
    dmx = bpy.context.scene.dmx
    if not dmx.collection:
        bpy.context.scene.dmx.new()


class DMX_OT_LoadShare_MVR(Operator, ImportHelper):
    """Load and Share My Virtual Rig file via MVR-xchange"""

    bl_idname = "dmx.load_and_share_mvr"
    bl_label = "Select MVR to Share"
    bl_options = {"PRESET", "UNDO"}

    filename_ext = ".mvr"
    filter_glob: StringProperty(default="*.mvr", options={"HIDDEN"})

    def execute(self, context):
        scene = context.scene
        dmx = scene.dmx
        if self.filepath:
            print("INFO", f"Processing MVR file: {self.filepath}")
            ADDON_PATH = dmx.get_addon_path()
            uuid = str(py_uuid.uuid4()).upper()
            new_file = os.path.join(ADDON_PATH, "assets", "mvrs", f"{uuid}.mvr")
            shutil.copy(self.filepath, new_file)

            mvr_x = context.window_manager.dmx.mvr_xchange
            comment = mvr_x.commit_message
            if comment == "":
                comment = "File shared"
            file = Path(self.filepath)
            commit = SimpleNamespace(
                file_size=file.stat().st_size,
                file_uuid=uuid,
                file_name=file.stem,
                comment=comment,
            )
            dmx.createMVR_Shared_Commit(commit)
        return {"FINISHED"}


class DMX_OT_SaveShared_MVR(Operator, ExportHelper):
    """Save the MVR file received via MVR-xchange"""

    bl_idname = "dmx.mvr_save_file"
    bl_label = "Save MVR"
    bl_options = {"PRESET", "UNDO"}

    filename_ext = ".mvr"
    uuid: StringProperty(options={"HIDDEN"})

    def execute(self, context):
        scene = context.scene
        dmx = scene.dmx

        if self.filepath and self.uuid:
            print("INFO", f"Processing MVR file: {self.uuid} {self.filepath}")
            ADDON_PATH = dmx.get_addon_path()
            mvr_file = os.path.join(ADDON_PATH, "assets", "mvrs", f"{self.uuid}.mvr")
            try:
                shutil.copy(mvr_file, self.filepath)
            except Exception as e:
                DMX_Log.log.error(f"Error copying MVR file: {e}")

        return {"FINISHED"}


class DMX_OT_Import_MVR(Operator, ImportHelper):
    """Import My Virtual Rig"""

    bl_idname = "dmx.import_mvr_into_scene"
    bl_label = "Import MVR (.mvr)"
    bl_options = {"PRESET", "UNDO"}

    filename_ext = ".mvr"
    filter_glob: StringProperty(default="*.mvr", options={"HIDDEN"})
    files: CollectionProperty(
        type=bpy.types.OperatorFileListElement, options={"HIDDEN", "SKIP_SAVE"}
    )
    directory: StringProperty(subtype="DIR_PATH")

    import_focus_points: BoolProperty(
        name=_("Import Focus Points as Targets"),
        description=_("Create Targets from MVR Focus Points"),
        default=True,
    )

    def draw(self, context):
        dmx = context.scene.dmx
        if not dmx.collection:
            Timer(0.5, createDMXcollection, ()).start()
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        box = layout.column().box()
        box.prop(self, "import_focus_points")

    def execute(self, context):
        dmx = context.scene.dmx
        for file in self.files:
            if not file.name:
                continue
            file_path = os.path.join(self.directory, file.name)
            print("INFO", f"Processing MVR file: {file_path}")
            dmx.addMVR(file_path, import_focus_points=self.import_focus_points)
        return {"FINISHED"}


class DMX_OT_Export_MVR(Operator, ExportHelper):
    """Export My Virtual Rig"""

    bl_idname = "dmx.export_mvr_from_scene"
    bl_label = "Export MVR (.mvr)"
    bl_options = {"PRESET", "UNDO"}

    filename_ext = ".mvr"

    def draw(self, context):
        dmx = context.scene.dmx
        if not dmx.collection:
            Timer(0.5, createDMXcollection, ()).start()
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

    def execute(self, context):
        dmx = context.scene.dmx
        DMX_Log.log.info(self.filepath)
        result = dmx.export_mvr(self.filepath)

        if result.ok:
            self.report({"INFO"}, "Data exported to: {}".format(self.filepath))
        else:
            self.report({"ERROR"}, result.error)

        return {"FINISHED"}


if bpy.app.version >= (4, 1):

    class DMX_IO_FH_MVR(bpy.types.FileHandler):
        bl_idname = "IO_FH_mvr"
        bl_label = "MVR"
        bl_import_operator = "dmx.import_mvr_into_scene"
        bl_export_operator = "dmx.export_mvr_from_scene"
        bl_file_extensions = ".mvr"

        @classmethod
        def poll_drop(cls, context):
            if bpy.app.version >= (4, 2):
                return poll_file_object_drop(context)


def menu_func_export(self, context):
    self.layout.operator(
        DMX_OT_Export_MVR.bl_idname, text="My Virtual Rig (.mvr) from BlenderDMX"
    )


def menu_func_import(self, context):
    self.layout.operator(
        DMX_OT_Import_MVR.bl_idname, text="My Virtual Rig (.mvr) into BlenderDMX"
    )


def register():
    bpy.utils.register_class(DMX_OT_SaveShared_MVR)
    bpy.utils.register_class(DMX_OT_LoadShare_MVR)
    bpy.utils.register_class(DMX_OT_Import_MVR)
    bpy.utils.register_class(DMX_OT_Export_MVR)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    if bpy.app.version >= (4, 1):
        bpy.utils.register_class(DMX_IO_FH_MVR)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    if bpy.app.version >= (4, 1):
        bpy.utils.unregister_class(DMX_IO_FH_MVR)
    bpy.utils.unregister_class(DMX_OT_Import_MVR)
    bpy.utils.unregister_class(DMX_OT_LoadShare_MVR)
    bpy.utils.unregister_class(DMX_OT_SaveShared_MVR)
    bpy.utils.unregister_class(DMX_OT_Export_MVR)
