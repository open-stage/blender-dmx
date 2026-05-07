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
import time
from types import SimpleNamespace
import uuid as py_uuid
from pathlib import Path
import json

import bpy
from bpy_extras.io_utils import ExportHelper, ImportHelper

from .logging_setup import DMX_Log

from bpy_extras.io_utils import poll_file_object_drop

from threading import Timer

from bpy.props import BoolProperty, CollectionProperty, StringProperty
from bpy.types import Operator

from .i18n import DMX_Lang
from .panels import profiles as Profiles
from .gdtf_file import DMX_GDTF_File
from .util import (
    clear_status_overlay,
    force_view3d_redraw,
    is_status_overlay_dismissible,
    is_status_overlay_visible,
    status_overlay_contains_window_point,
    show_status_overlay,
)

_ = DMX_Lang._


def createDMXcollection():
    dmx = bpy.context.scene.dmx
    if not dmx.collection:
        bpy.context.scene.dmx.new()


def _deserialize_mvr_filepaths(serialized):
    if not serialized:
        return []
    try:
        filepaths = json.loads(serialized)
    except json.JSONDecodeError:
        return []
    return [path for path in filepaths if path]


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
    bl_label = "Import MVR (.mvr) into BlenderDMX"
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

    import_fixtures: BoolProperty(
        name=_("Import Fixtures"),
        description=_("Import Fixtures"),
        default=True,
    )

    import_trusses: BoolProperty(
        name=_("Import Trusses"),
        description=_("Import Trusses"),
        default=True,
    )

    import_scene_objects: BoolProperty(
        name=_("Import Scene Objects"),
        description=_("Import Scene Objects"),
        default=True,
    )
    import_projectors: BoolProperty(
        name=_("Import Projectors"),
        description=_("Import Projectors"),
        default=True,
    )

    import_video_screens: BoolProperty(
        name=_("Import Video Screens"),
        description=_("Import Video Screens"),
        default=True,
    )

    import_supports: BoolProperty(
        name=_("Import Supports"),
        description=_("Import Supports"),
        default=True,
    )

    use_high_mesh: BoolProperty(
        name=_("Use GDTF High Quality Models"),
        description=_("Use high quality mesh files if present"),
        default=False,
    )

    def draw(self, context):
        dmx = context.scene.dmx
        if not dmx.collection:
            Timer(0.5, createDMXcollection, ()).start()
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        box = layout.column().box()
        row = box.row()
        row.template_icon_view(
            context.scene, "mvr_logo_enum", show_labels=False, scale=10
        )
        row.enabled = False
        box = layout.column().box()
        row1 = box.row()
        row1.prop(self, "import_fixtures")
        row7 = box.row()
        row7.prop(self, "use_high_mesh")
        row7.enabled = self.import_fixtures
        row2 = box.row()
        row2.prop(self, "import_focus_points")
        row2.enabled = self.import_fixtures
        row3 = box.row()
        row3.prop(self, "import_trusses")
        # box.prop(self, "import_scene_objects")
        row4 = box.row()
        row4.prop(self, "import_projectors")
        row5 = box.row()
        row5.prop(self, "import_video_screens")
        row6 = box.row()
        row6.prop(self, "import_supports")

    def execute(self, context):
        filepaths = []
        for file in self.files:
            if not file.name:
                continue
            filepaths.append(os.path.join(self.directory, file.name))

        if not filepaths and self.filepath:
            filepaths.append(self.filepath)
        if not filepaths:
            return {"CANCELLED"}

        return bpy.ops.dmx.import_mvr_modal(
            "INVOKE_DEFAULT",
            filepaths_json=json.dumps(filepaths),
            import_focus_points=self.import_focus_points,
            import_fixtures=self.import_fixtures,
            import_trusses=self.import_trusses,
            import_scene_objects=self.import_scene_objects,
            import_supports=self.import_supports,
            import_projectors=self.import_projectors,
            import_video_screens=self.import_video_screens,
            use_high_mesh=self.use_high_mesh,
        )

    def invoke(self, context, event):
        return self.invoke_popup(context)


class DMX_OT_Export_MVR(Operator, ExportHelper):
    """Export My Virtual Rig"""

    bl_idname = "dmx.export_mvr_from_scene"
    bl_label = "Export MVR (.mvr) from BlenderDMX"
    bl_options = {"PRESET", "UNDO"}

    filename_ext = ".mvr"

    export_focus_points: BoolProperty(
        name=_("Export Targets as MVR Focus Points"),
        description=_("Export Targets as MVR Focus Points"),
        default=True,
    )

    selected_fixtures_only: BoolProperty(
        name=_("Export only selected fixtures"),
        description=_(
            "Export only selected fixtures (does not filter non-fixture objects)"
        ),
        default=False,
    )

    export_fixtures_only: BoolProperty(
        name=_("Export fixtures only"),
        description=_("Export fixtures only (skip all non-fixture objects)"),
        default=False,
    )

    export_active_layer_only: BoolProperty(
        name=_("Export active MVR layer only"),
        description=_("Export only the currently selected MVR layer"),
        default=False,
    )

    def draw(self, context):
        dmx = context.scene.dmx
        if not dmx.collection:
            Timer(0.5, createDMXcollection, ()).start()
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        box = layout.column().box()
        row = box.row()
        row.template_icon_view(
            context.scene, "mvr_logo_enum", show_labels=False, scale=10
        )
        row.enabled = False
        box = layout.column().box()
        box.prop(self, "export_focus_points")
        box.prop(self, "selected_fixtures_only")
        box.prop(self, "export_fixtures_only")
        box.prop(self, "export_active_layer_only")

    def execute(self, context):
        dmx = context.scene.dmx
        DMX_Log.log.info(self.filepath)
        started_at = time.monotonic()
        show_status_overlay(
            "Exporting MVR package",
            progress=None,
            status="running",
            title="MVR Export In Progress!",
            hint="Please wait...",
        )
        force_view3d_redraw()
        result = dmx.export_mvr(
            self.filepath,
            export_focus_points=self.export_focus_points,
            selected_fixtures_only=self.selected_fixtures_only,
            export_fixtures_only=self.export_fixtures_only,
            export_active_layer_only=self.export_active_layer_only,
        )

        if result.ok:
            elapsed = max(0.0, time.monotonic() - started_at)
            show_status_overlay(
                f"Exported in {elapsed:.1f} sec",
                progress=1.0,
                status="complete",
                title="MVR Export Complete",
                hint="Click overlay to dismiss",
                auto_hide_after=10.0,
            )
            bpy.ops.dmx.dismiss_status_overlay_modal("INVOKE_DEFAULT")
            self.report({"INFO"}, "Data exported to: {}".format(self.filepath))
        else:
            show_status_overlay(
                result.error,
                progress=None,
                status="error",
                title="MVR Export Failed",
                hint="Click overlay to dismiss",
                auto_hide_after=10.0,
            )
            bpy.ops.dmx.dismiss_status_overlay_modal("INVOKE_DEFAULT")
            self.report({"ERROR"}, result.error)

        return {"FINISHED"}


class DMX_OT_Import_MVR_Modal(Operator):
    """Import My Virtual Rig using a modal staged importer"""

    bl_idname = "dmx.import_mvr_modal"
    bl_label = "Import MVR (Modal)"
    bl_options = {"UNDO"}

    filepaths_json: StringProperty(options={"HIDDEN"})

    import_focus_points: BoolProperty(default=True, options={"HIDDEN"})
    import_fixtures: BoolProperty(default=True, options={"HIDDEN"})
    import_trusses: BoolProperty(default=True, options={"HIDDEN"})
    import_scene_objects: BoolProperty(default=True, options={"HIDDEN"})
    import_projectors: BoolProperty(default=True, options={"HIDDEN"})
    import_video_screens: BoolProperty(default=True, options={"HIDDEN"})
    import_supports: BoolProperty(default=True, options={"HIDDEN"})
    use_high_mesh: BoolProperty(default=False, options={"HIDDEN"})

    _timer = None
    _filepaths = None
    _file_index = 0
    _import_iter = None
    _cancelled = False
    _last_message = ""
    _finished = False
    _started_at = 0.0

    def _progress_cb(self, progress, message):
        self._last_message = message
        show_status_overlay(
            message,
            progress=progress,
            status="running",
            hint="Press ESC to cancel the import",
        )

    def _should_stop(self):
        return self._cancelled

    def _start_next_import(self, context):
        if self._file_index >= len(self._filepaths):
            self._finished = True
            return False

        file_path = self._filepaths[self._file_index]
        print("INFO", f"Processing MVR file: {file_path}")
        self._last_message = f"Starting {Path(file_path).name}"
        self._import_iter = context.scene.dmx.addMVR_steps(
            file_path,
            import_focus_points=self.import_focus_points,
            import_fixtures=self.import_fixtures,
            import_trusses=self.import_trusses,
            import_scene_objects=self.import_scene_objects,
            import_supports=self.import_supports,
            import_projectors=self.import_projectors,
            import_video_screens=self.import_video_screens,
            use_high_mesh=self.use_high_mesh,
            progress_cb=self._progress_cb,
            should_stop=self._should_stop,
        )
        return True

    def _finish(self, context, cancelled=False, error=None):
        elapsed = max(0.0, time.monotonic() - self._started_at)
        if self._timer is not None:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None
        if self._import_iter is not None:
            try:
                self._import_iter.close()
            except RuntimeError:
                pass
            self._import_iter = None

        if cancelled:
            show_status_overlay(
                f"Canceled after {elapsed:.1f} sec",
                progress=None,
                status="cancelled",
                title="MVR Import Canceled",
                hint="Click overlay to dismiss",
                auto_hide_after=10.0,
            )
            bpy.ops.dmx.dismiss_status_overlay_modal("INVOKE_DEFAULT")
            self.report({"WARNING"}, "MVR import cancelled")
            return {"CANCELLED"}
        if error is not None:
            show_status_overlay(
                str(error),
                progress=None,
                status="error",
                title="MVR Import Failed",
                hint="Click overlay to dismiss",
                auto_hide_after=10.0,
            )
            bpy.ops.dmx.dismiss_status_overlay_modal("INVOKE_DEFAULT")
            self.report({"ERROR"}, f"MVR import failed: {error}")
            return {"CANCELLED"}

        Profiles.DMX_Fixtures_Local_Profile.loadLocal()
        DMX_GDTF_File.get_manufacturers_list()
        show_status_overlay(
            f"Completed in {elapsed:.1f} sec",
            progress=1.0,
            status="complete",
            title="MVR Import Complete",
            hint="Click overlay to dismiss",
            auto_hide_after=10.0,
        )
        bpy.ops.dmx.dismiss_status_overlay_modal("INVOKE_DEFAULT")
        self.report({"INFO"}, "MVR import complete")
        return {"FINISHED"}

    def invoke(self, context, event):
        self._filepaths = _deserialize_mvr_filepaths(self.filepaths_json)
        self._file_index = 0
        self._import_iter = None
        self._cancelled = False
        self._finished = False
        self._last_message = ""
        self._started_at = time.monotonic()

        if not self._filepaths:
            self.report({"ERROR"}, "No MVR file selected")
            return {"CANCELLED"}

        show_status_overlay(
            "Preparing import",
            progress=0.0,
            status="running",
            hint="Press ESC to cancel the import",
        )
        self._timer = context.window_manager.event_timer_add(
            0.05, window=context.window
        )
        context.window_manager.modal_handler_add(self)
        self._start_next_import(context)
        return {"RUNNING_MODAL"}

    def modal(self, context, event):
        if event.type in {"ESC", "RIGHTMOUSE"}:
            self._cancelled = True
            return self._finish(context, cancelled=True)

        if event.type != "TIMER":
            return {"PASS_THROUGH"}

        if self._finished:
            return self._finish(context)

        try:
            next(self._import_iter)
        except StopIteration:
            self._file_index += 1
            self._import_iter = None
            if not self._start_next_import(context):
                self._finished = True
        except Exception as exc:
            DMX_Log.log.exception("MVR modal import failed")
            return self._finish(context, error=exc)

        return {"RUNNING_MODAL"}


class DMX_IO_FH_MVR(bpy.types.FileHandler):
    bl_idname = "IO_FH_mvr"
    bl_label = "MVR"
    bl_import_operator = "dmx.import_mvr_into_scene"
    bl_export_operator = "dmx.export_mvr_from_scene"
    bl_file_extensions = ".mvr"

    @classmethod
    def poll_drop(cls, context):
        return poll_file_object_drop(context)


class DMX_OT_Dismiss_Status_Overlay_Modal(Operator):
    """Dismiss terminal status overlay by clicking it"""

    bl_idname = "dmx.dismiss_status_overlay_modal"
    bl_label = "Dismiss Status Overlay"

    _timer = None

    def invoke(self, context, event):
        if not is_status_overlay_dismissible():
            return {"CANCELLED"}
        self._timer = context.window_manager.event_timer_add(0.2, window=context.window)
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def modal(self, context, event):
        if not is_status_overlay_visible():
            if self._timer is not None:
                context.window_manager.event_timer_remove(self._timer)
                self._timer = None
            return {"FINISHED"}

        if event.type == "LEFTMOUSE" and event.value == "PRESS":
            if status_overlay_contains_window_point(event.mouse_x, event.mouse_y):
                clear_status_overlay()
                if self._timer is not None:
                    context.window_manager.event_timer_remove(self._timer)
                    self._timer = None
                return {"FINISHED"}

        if event.type == "TIMER" and not is_status_overlay_visible():
            if self._timer is not None:
                context.window_manager.event_timer_remove(self._timer)
                self._timer = None
            return {"FINISHED"}

        return {"PASS_THROUGH"}


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
    bpy.utils.register_class(DMX_OT_Import_MVR_Modal)
    bpy.utils.register_class(DMX_OT_Dismiss_Status_Overlay_Modal)
    bpy.utils.register_class(DMX_OT_Export_MVR)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    bpy.utils.register_class(DMX_IO_FH_MVR)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.utils.unregister_class(DMX_IO_FH_MVR)
    bpy.utils.unregister_class(DMX_OT_Dismiss_Status_Overlay_Modal)
    bpy.utils.unregister_class(DMX_OT_Import_MVR_Modal)
    bpy.utils.unregister_class(DMX_OT_Import_MVR)
    bpy.utils.unregister_class(DMX_OT_LoadShare_MVR)
    bpy.utils.unregister_class(DMX_OT_SaveShared_MVR)
    bpy.utils.unregister_class(DMX_OT_Export_MVR)
