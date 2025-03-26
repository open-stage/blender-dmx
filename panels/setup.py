#    Copyright Hugo Aboud, vanous
#
#    This file is part of BlenderDMX.
#
#    BlenderDMX is free software: you can redistribute it and/or modify it
#    under the terms of the GNU General Public License as published by the Free
#    Software Foundation, either version 3 of the License, or (at your option)
#    any later version.
#
#    BlenderDMX is distributed in the hope that it will be useful, but WITHOUT
#    ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
#    FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
#    more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program. If not, see <https://www.gnu.org/licenses/>.

import os
import shutil

import bpy
from bpy.props import CollectionProperty, StringProperty
from bpy.types import Operator, Panel

from .. import blender_utils as blender_utils
from ..gdtf import DMX_GDTF
from ..i18n import DMX_Lang
from ..in_gdtf import DMX_OT_Import_GDTF
from ..in_out_mvr import DMX_OT_Export_MVR, DMX_OT_Import_MVR
from ..logging import DMX_Log
from ..material import getVolumeScatterMaterial
from ..panels import profiles as Profiles
from ..util import getSceneRect, split_text_on_spaces

_ = DMX_Lang._
# Operators #


class DMX_OT_Setup_NewShow(Operator):
    bl_label = _("DMX > Setup > New Show")
    bl_description = _("Clear any existing DMX data and create a new show.")
    bl_idname = "dmx.new_show"
    bl_options = {"UNDO"}

    def execute(self, context):
        # DMX setup
        context.scene.dmx.new()
        dmx = context.scene.dmx
        dmx.fixtures.clear()

        return {"FINISHED"}


class DMX_OT_Setup_EnableSelectGeometries(Operator):
    bl_label = _("Do at your own risk. Manual edits or deletes can cause issues")
    bl_description = _(
        "Manually editing or deleting geometries of GDTF devices may cause issues."
    )
    bl_idname = "dmx.enabling_geometry_selection"
    bl_options = {"UNDO"}

    def draw(self, context):
        layout = self.layout
        col = layout.column()

    def execute(self, context):
        dmx = context.scene.dmx
        for fixture in dmx.fixtures:
            for obj in fixture.collection.objects:
                if obj.get("geometry_root", False):
                    continue
                if obj.get("2d_symbol", None):
                    continue
                if "Target" in obj.name:
                    continue
                obj.hide_select = not dmx.select_geometries

        return {"FINISHED"}

    def invoke(self, context, event):
        if context.scene.dmx.select_geometries:
            wm = context.window_manager
            return wm.invoke_props_dialog(self)
        else:
            return self.execute(context)

    def cancel(self, context):
        context.scene.dmx.select_geometries = False


class DMX_OT_Setup_RemoveDMX(Operator):
    bl_label = _("Really remove all fixtures and DMX from blend file?")
    bl_description = _("Try to remove DMX from the Blender showfile")
    bl_idname = "dmx.remove_show"
    bl_options = {"UNDO"}

    def draw(self, context):
        layout = self.layout
        col = layout.column()

    def execute(self, context):
        # DMX setup
        dmx = context.scene.dmx
        dmx.fixtures.clear()
        dmx.trackers.clear()
        if "DMX" in bpy.data.collections:
            bpy.data.collections.remove(bpy.data.collections["DMX"])

        return {"FINISHED"}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class DMX_OT_Fixture_Set_Cycles_Beams_Size_Small(Operator):
    bl_label = _("Beam diameter small")
    bl_idname = "dmx.fixture_set_cycles_beam_size_small"

    def execute(self, context):
        dmx = context.scene.dmx
        selected = dmx.selectedFixtures()
        for fixture in selected:
            for light in fixture.lights:
                light_obj = light.object
                light_obj.data["beam_radius_pin_sized_for_gobos"] = True
                fixture.dmx_cache_dirty = True
                fixture.render(skip_cache=True)
        return {"FINISHED"}


class DMX_OT_Fixture_Set_Cycles_Beams_Size_Normal(Operator):
    bl_label = _("Beam diameter normal")
    bl_idname = "dmx.fixture_set_cycles_beam_size_normal"

    def execute(self, context):
        dmx = context.scene.dmx
        selected = dmx.selectedFixtures()
        for fixture in selected:
            for light in fixture.lights:
                light_obj = light.object
                light_obj.data["beam_radius_pin_sized_for_gobos"] = False
                fixture.dmx_cache_dirty = True
                fixture.render(skip_cache=True)
        return {"FINISHED"}


class DMX_OT_Setup_Volume_Create(Operator):
    bl_label = _("DMX > Setup > Create/Update Volume Box")
    bl_description = _(
        "Create/Update a Box on the scene bounds with a Volume Scatter shader"
    )
    bl_idname = "dmx.create_volume"
    bl_options = {"UNDO"}

    def execute(self, context):
        dmx = context.scene.dmx
        # Get scene bounds
        min, max = getSceneRect()
        pos = [min[i] + (max[i] - min[i]) / 2 for i in range(3)]
        scale = [max[i] - min[i] for i in range(3)]
        # Remove old DMX collection if present
        if "DMX_Volume" not in bpy.data.objects:
            bpy.ops.mesh.primitive_cube_add(size=1.0)
            dmx.volume = bpy.context.selected_objects[0]
            dmx.volume.name = "DMX_Volume"
            dmx.volume.display_type = "WIRE"
            material = getVolumeScatterMaterial()
            dmx.volume.data.materials.append(material)
        else:
            dmx.volume = bpy.data.objects["DMX_Volume"]

        if not len(dmx.volume.data.materials):
            material = getVolumeScatterMaterial()
            dmx.volume.data.materials.append(material)
            # The previous code was assigning embedded ID to an IDProperty
            # https://projects.blender.org/blender/blender/issues/129393
            # but i think we do not need this at all, as the dmx.volume holds
            # all we need
            # dmx.volume_nodetree = dmx.volume.data.materials[0].node_tree

        old_collections = dmx.volume.users_collection
        if dmx.collection not in old_collections:
            dmx.collection.objects.link(dmx.volume)
            for collection in old_collections:
                collection.objects.unlink(dmx.volume)

        dmx.volume.location = pos
        dmx.volume.scale = scale

        return {"FINISHED"}


class DMX_PT_Setup_Volume(Panel):
    bl_label = _("Beam Volume")
    bl_idname = "DMX_PT_Setup_Volume"
    bl_parent_id = "DMX_PT_Setup"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        dmx = context.scene.dmx

        box = layout.column().box()
        box.prop(dmx, "volume_preview")
        box.prop(dmx, "disable_overlays")

        box = layout.column().box()
        box.operator(
            "dmx.create_volume",
            text=(_("Update Volume Box") if dmx.volume else _("Create Volume Box")),
            icon="MESH_CUBE",
        )

        row = box.row()
        row.prop(dmx, "volume_enabled")
        row.enabled = dmx.volume is not None

        row_den = box.row()
        row_den.prop(dmx, "volume_density")
        row_scale = box.row()
        row_scale.prop(dmx, "volume_noise_scale")
        row_den.enabled = row_scale.enabled = dmx.volume is not None

        selected = dmx.selectedFixtures()
        enabled = len(selected) > 0

        row = box.row()
        col1 = row.column()
        col1.prop(dmx, "beam_intensity_multiplier")

        box = layout.column().box()
        row = box.row()
        col1 = row.column()
        col1.prop(dmx, "reduced_beam_diameter_in_cycles")
        col2 = row.column()
        col2.operator(
            "wm.url_open", text="", icon="HELP"
        ).url = "https://blenderdmx.eu/docs/setup/#beam-lens-diameter-in-cycles"

        if bpy.context.scene.dmx.reduced_beam_diameter_in_cycles == "CUSTOM":
            row0 = box.row()
            row1 = box.row()
            row2 = box.row()
            row0.label(text=_("Set on selected fixtures"))
            row1.operator("dmx.fixture_set_cycles_beam_size_normal", icon="CONE")
            row2.operator("dmx.fixture_set_cycles_beam_size_small", icon="LIGHT_SPOT")
            row0.enabled = row1.enabled = row2.enabled = enabled
        box = layout.column().box()
        row = box.row()
        col1 = row.column()
        col1.prop(context.window_manager.dmx, "collections_list")
        col2 = row.column()
        col2.operator(
            "wm.url_open", text="", icon="HELP"
        ).url = "https://blenderdmx.eu/docs/laser/"


class DMX_PT_Setup_Viewport(Panel):
    bl_label = _("Viewport")
    bl_idname = "DMX_PT_Setup_Viewport"
    bl_parent_id = "DMX_PT_Setup"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        dmx = context.scene.dmx
        row = layout.row()
        row.label(text=_("Background Color"))
        row = layout.row()
        row.prop(dmx, "background_color", text="")
        row = layout.row()
        row.prop(context.window_manager.dmx, "pause_render")
        row = layout.row()
        row.prop(dmx, "display_2D")
        row = layout.row()
        row.prop(dmx, "enable_device_label")
        row = layout.row()
        row.prop(dmx, "display_device_label")
        row.enabled = dmx.display_2D or dmx.enable_device_label
        row = layout.row()
        row.prop(dmx, "display_pigtails")
        row = layout.row()
        row.prop(dmx, "select_geometries")


class DMX_PT_Setup_Extras(Panel):
    bl_label = _("Extras")
    bl_idname = "DMX_PT_Setup_Extras"
    bl_parent_id = "DMX_PT_Setup"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        dmx = context.scene.dmx
        old_data_exists = blender_utils.old_custom_data_exists()
        row = layout.row()
        row.operator_context = "INVOKE_DEFAULT"  #'INVOKE_AREA'
        row.operator(
            "dmx.clear_custom_data", text=_("Clear Project data"), icon="TRASH"
        )
        if old_data_exists:
            row = layout.row()
            row.operator(
                "dmx.copy_custom_data",
                text=_("Copy (import) old data from addon folder"),
                icon="DUPLICATE",
            )
        layout.operator(
            "dmx.remove_show", text=_("Remove DMX from blend file"), icon="BRUSH_DATA"
        )
        layout.operator(
            "wm.url_open", text="User Guide Online", icon="HELP"
        ).url = "https://blenderdmx.eu/docs/faq/"
        row = layout.row()
        row.prop(dmx, "mvrx_hostname_in_service")
        row = layout.row()
        row.prop(dmx, "mvrx_per_project_station_uuid")


class DMX_PT_Setup_Import(Panel):
    bl_label = _("Import")
    bl_idname = "DMX_PT_Setup_Import"
    bl_parent_id = "DMX_PT_Setup"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        dmx = context.scene.dmx
        # "Import GDTF Profile"
        row = layout.row()
        row.operator(
            "dmx.import_gdtf_into_scene", text=_("Import GDTF Profile"), icon="IMPORT"
        )

        # "Import MVR scene"
        row = layout.row()
        row.operator(
            "dmx.import_mvr_into_scene", text=_("Import MVR Scene"), icon="IMPORT"
        )

        # export project data
        row = layout.row()
        row.operator(
            "dmx.import_custom_data", text=_("Import Project data"), icon="IMPORT"
        )


class DMX_PT_Setup_Export(Panel):
    bl_label = _("Export")
    bl_idname = "DMX_PT_Setup_Export"
    bl_parent_id = "DMX_PT_Setup"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        dmx = context.scene.dmx

        # export project data
        row = layout.row()
        row.operator(
            "dmx.export_custom_data", text=_("Export Project data"), icon="EXPORT"
        )
        row = layout.row()
        row.operator("dmx.export_mvr_from_scene", text=_("Export MVR"), icon="EXPORT")


class DMX_OT_Setup_Open_LogFile(Operator):
    bl_label = _("Show logging directory")
    bl_description = _("Show logging directory")
    bl_idname = "dmx.print_logging_path"
    bl_options = {"UNDO"}

    def execute(self, context):
        # DMX setup
        dmx = context.scene.dmx
        current_path = dmx.get_addon_path()
        self.report({"INFO"}, f"Path with a log file: {current_path}")

        return {"FINISHED"}


class DMX_PT_Setup_Logging(Panel):
    bl_label = _("Logging")
    bl_idname = "DMX_PT_Setup_Logging"
    bl_parent_id = "DMX_PT_Setup"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        # DMX setup
        dmx = context.scene.dmx
        layout = self.layout
        row = layout.row()
        row.prop(dmx, "logging_level")
        row = layout.row()
        row.label(text=_("Log filter"))
        row = layout.row(align=True)
        row.prop(context.window_manager.dmx, "logging_filter_mvr_xchange", toggle=True)
        row.prop(context.window_manager.dmx, "logging_filter_dmx_in", toggle=True)
        row.prop(context.window_manager.dmx, "logging_filter_fixture", toggle=True)
        row = layout.row()
        layout.operator("dmx.print_logging_path")


# Panel #


class DMX_PT_Setup(Panel):
    bl_label = _("Setup")
    bl_idname = "DMX_PT_Setup"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        dmx = context.scene.dmx
        temp_data = bpy.context.window_manager.dmx
        message = temp_data.migration_message

        if len(message) > 0:
            row = layout.row()
            lines = split_text_on_spaces(message, 30)
            row.label(text="Important!", icon="ERROR")
            for line in lines:
                row = layout.row()
                row.label(text=line)

        if not dmx.collection:
            if not bpy.app.version >= (3, 4):
                layout.label(
                    text=_("Error! Blender 3.4 or higher required."), icon="ERROR"
                )
            layout.operator("dmx.new_show", text=_("Create New Show"), icon="LIGHT")
            layout.operator(
                "wm.url_open", text="User Guide Online", icon="HELP"
            ).url = "https://blenderdmx.eu/docs/faq/"


class DMX_OT_Import_Custom_Data(Operator):
    bl_label = _("Import Custom Data")
    bl_idname = "dmx.import_custom_data"
    bl_description = _(
        "Unzip previously exported custom data from a zip file. This will overwrite current data!"
    )
    bl_options = {"UNDO"}

    filter_glob: StringProperty(default="*.zip", options={"HIDDEN"})

    directory: StringProperty(name=_("File Path"), maxlen=1024, default="")

    files: CollectionProperty(name=_("Files"), type=bpy.types.OperatorFileListElement)

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, "files")

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        file_name = self.files[0].name
        if file_name != "" and len(file_name) > 1:
            result = blender_utils.import_custom_data(self.directory, file_name)
        else:
            self.report({"ERROR"}, _("Incorrect file name!"))
            return {"FINISHED"}

        DMX_GDTF.getManufacturerList()
        Profiles.DMX_Fixtures_Local_Profile.loadLocal()

        if result.ok:
            import_filename = os.path.join(self.directory, file_name)
            self.report({"INFO"}, _("Data imported from: {}").format(import_filename))
        else:
            self.report({"ERROR"}, result.error)

        return {"FINISHED"}


class DMX_OT_Export_Custom_Data(Operator):
    bl_label = _("Export Custom Data")
    bl_idname = "dmx.export_custom_data"
    bl_description = _("Zip and Export custom data from BlenderDMX addon directory.")
    bl_options = {"UNDO"}

    filter_glob: StringProperty(default="*.zip", options={"HIDDEN"})

    directory: StringProperty(name=_("File Path"), maxlen=1024, default="")

    files: CollectionProperty(name=_("Files"), type=bpy.types.OperatorFileListElement)

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, "files")

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        file_name = self.files[0].name
        if file_name[-4:].lower() == ".zip":
            file_name = file_name[:-4]
        if file_name != "" and len(file_name) > 1:
            result = blender_utils.export_custom_data(self.directory, file_name)
        else:
            self.report({"ERROR"}, _("Incorrect file name!"))
            return {"FINISHED"}

        if result.ok:
            export_filename = os.path.join(self.directory, f"{file_name}.zip")
            self.report({"INFO"}, _("Data exported to: {}").format(export_filename))
        else:
            self.report({"ERROR"}, result.error)

        return {"FINISHED"}


class DMX_OT_Clear_Custom_Data(Operator):
    bl_label = _("Really delete all custom data from the addon directory?")
    bl_idname = "dmx.clear_custom_data"
    bl_description = _("Clear custom data from BlenderDMX addon directory.")
    bl_options = {"UNDO"}

    def draw(self, context):
        layout = self.layout
        col = layout.column()

    def execute(self, context):
        result = blender_utils.clear_custom_data()

        DMX_GDTF.getManufacturerList()
        Profiles.DMX_Fixtures_Local_Profile.loadLocal()

        if result.ok:
            self.report({"INFO"}, _("Data cleared"))
        else:
            self.report({"ERROR"}, result.error)

        return {"FINISHED"}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class DMX_OT_Copy_Custom_Data(Operator):
    bl_label = _("Copy data from addon to user directory")
    bl_idname = "dmx.copy_custom_data"
    bl_description = _(
        "Copy custom data from BlenderDMX addon directory to BlenderDMX extension user directory."
    )
    bl_options = {"UNDO"}

    def draw(self, context):
        layout = self.layout
        col = layout.column()

    def execute(self, context):
        result = blender_utils.copy_custom_data()
        DMX_GDTF.getManufacturerList()
        Profiles.DMX_Fixtures_Local_Profile.loadLocal()

        if result.ok:
            self.report({"INFO"}, _("Data copied"))
        else:
            self.report({"ERROR"}, result.error)

        return {"FINISHED"}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class DMX_OT_Reload_Addon(Operator):
    bl_label = _("Reload BlenderDMX addon")
    bl_idname = "dmx.reload_addon"
    bl_description = _("Reload the addon, useful during development")
    bl_options = {"UNDO"}

    def draw(self, context):
        layout = self.layout
        col = layout.column()

    def execute(self, context):
        dmx = context.scene.dmx

        try:
            bpy.utils.unregister_class(DMX_OT_Import_GDTF)
            bpy.utils.unregister_class(DMX_OT_Import_MVR)
            bpy.utils.unregister_class(DMX_OT_Export_MVR)
        except:
            ...

        for cls in dmx.classes:
            try:
                bpy.utils.unregister_class(cls)
            except:
                ...

        for cls in dmx.classes_base:
            try:
                bpy.utils.unregister_class(cls)
            except:
                ...
        for cls in dmx.classes_setup:
            try:
                bpy.utils.unregister_class(cls)
            except:
                ...

        result = blender_utils.reload_addon()

        if result.ok:
            self.report({"INFO"}, _("Addon reloaded"))
        else:
            self.report({"ERROR"}, result.error)

        return {"FINISHED"}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)
