import os

import bpy
from bpy_extras.io_utils import ExportHelper, ImportHelper

from .logging import DMX_Log

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
    bpy.utils.unregister_class(DMX_OT_Export_MVR)
