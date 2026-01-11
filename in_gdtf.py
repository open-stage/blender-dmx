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
import traceback
from threading import Timer

import bpy
from bpy_extras.io_utils import ImportHelper

from bpy_extras.io_utils import poll_file_object_drop

from bpy.props import (
    BoolProperty,
    CollectionProperty,
    FloatVectorProperty,
    IntProperty,
    StringProperty,
)
from bpy.types import PropertyGroup

from .i18n import DMX_Lang
from .panels import profiles as Profiles
from .gdtf_file import DMX_GDTF_File
from .logging_setup import DMX_Log

_ = DMX_Lang._


def createDMXcollection():
    dmx = bpy.context.scene.dmx
    if not dmx.collection:
        bpy.context.scene.dmx.new()


class DMX_Break_Import(PropertyGroup):
    def ensure_universe_exists(self, context):
        dmx = bpy.context.scene.dmx
        dmx.ensureUniverseExists(self.universe)

    dmx_break: IntProperty(
        name="DMX Break",
        description="DMX entry point",
        default=0,
        min=0,
        max=511,
    )
    universe: IntProperty(
        name="Fixture > Universe",
        description="Fixture DMX Universe",
        default=0,
        min=0,
        max=511,
        update=ensure_universe_exists,
    )

    address: IntProperty(
        name="Fixture > Address", description="Fixture DMX Address", default=1, min=1
    )  # no max for now

    channels_count: IntProperty(
        name="Number of channels",
        description="Number of DMX channels",
        default=0,
        min=0,
    )  # no max for now


class DMX_OT_Import_GDTF(bpy.types.Operator, ImportHelper):
    """Import GDTF"""

    bl_idname = "dmx.import_gdtf_into_scene"
    bl_label = "Import GDTF (.gdtf) into BlenderDMX"
    bl_options = {"PRESET", "UNDO"}

    filename_ext = ".gdtf"
    filter_glob: StringProperty(default="*.gdtf", options={"HIDDEN"})
    files: CollectionProperty(
        type=bpy.types.OperatorFileListElement, options={"HIDDEN", "SKIP_SAVE"}
    )
    directory: StringProperty(subtype="DIR_PATH")

    patch: BoolProperty(
        name="Patch into the scene",
        description="Patch fixture into the scene",
        default=False,
    )

    universe: IntProperty(
        name=_("Universe"), description=_("DMX Universe"), default=0, min=0, max=511
    )

    address: IntProperty(
        name=_("Address"), description=_("DMX Address"), default=1, min=1, max=512
    )

    dmx_breaks: CollectionProperty(name="DMX Break", type=DMX_Break_Import)

    gel_color: FloatVectorProperty(
        name=_("Gel Color"),
        subtype="COLOR",
        size=4,
        min=0.0,
        max=1.0,
        default=(1.0, 1.0, 1.0, 1.0),
    )

    display_beams: BoolProperty(
        name=_("Display beams"),
        description=_("Display beam projection and cone"),
        # update = onDisplayBeams,
        default=True,
    )

    add_target: BoolProperty(
        name=_("Add Target"),
        description=_("Add target for beam to follow"),
        # update = onAddTarget,
        default=True,
    )

    increment_address: BoolProperty(
        name=_("Increment DMX address"),
        description=_("Increment DMX address"),
        default=True,
    )

    increment_fixture_id: BoolProperty(
        name=_("Increment Fixture ID"),
        description=_("Increment Fixture ID if numeric"),
        default=True,
    )

    fixture_id: StringProperty(
        name=_("Fixture ID"),
        description=_(
            "The Fixture ID is an identifier of this fixture that can be used to activate / select them for programming."
        ),
        default="",
    )

    units: IntProperty(
        name=_("Units"),
        description=_("How many units of this light to add"),
        default=1,
        min=1,
        max=1024,
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
            context.scene, "gdtf_logo_enum", show_labels=False, scale=10
        )
        row.enabled = False
        layout.prop(self, "patch")
        box = layout.column().box()
        box.enabled = self.patch
        box.prop(self, "units")
        box.prop(self, "universe")
        box.prop(self, "address")
        box.prop(self, "fixture_id")
        box.prop(self, "gel_color")
        box.prop(self, "display_beams")
        box.prop(self, "add_target")
        box.prop(self, "increment_address")
        box.prop(self, "increment_fixture_id")

    def execute(self, context):
        dmx = bpy.context.scene.dmx
        folder_path = dmx.get_addon_path()
        folder_path = os.path.join(folder_path, "assets", "profiles")
        dmx = context.scene.dmx

        address = self.address
        universe = self.universe
        fixture_id = self.fixture_id

        for file in self.files:
            if not file.name:
                continue
            file_path = os.path.join(self.directory, file.name)
            DMX_Log.log.info(f"Importing GDTF Profile: {file_path}")
            try:
                shutil.copy(file_path, folder_path)
                DMX_GDTF_File.add_to_data(file.name)
            except shutil.SameFileError:
                DMX_Log.log.debug(
                    "Importing file which already existed in the profiles folder"
                )

            if self.patch:
                try:
                    profile = DMX_GDTF_File.load_gdtf_profile(file.name)
                    dmx_mode = profile.dmx_modes[0]
                    self.dmx_breaks.clear()
                    for idx, dmx_break in enumerate(dmx_mode.dmx_breaks):
                        new_break = self.dmx_breaks.add()
                        new_break.dmx_break = dmx_break.dmx_break
                        new_break.address = address
                        new_break.universe = universe
                        new_break.channels_count = dmx_break.channels_count

                    if not self.dmx_breaks:
                        new_break = self.dmx_breaks.add()
                        new_break.dmx_break = 1
                        new_break.universe = universe
                        new_break.address = address
                        new_break.channels_count = 0

                    for count in range(1, 1 + self.units):
                        dmx.addFixture(
                            file.name,
                            dmx_mode.name,
                            self.dmx_breaks,
                            self.gel_color,
                            self.display_beams,
                            self.add_target,
                            fixture_id=fixture_id,
                            user_fixture_name=None,
                        )
                        fixture = dmx.fixtures[-1]
                        DMX_Log.log.debug(f"Added fixture {fixture}")
                        if not fixture:
                            continue

                        if self.increment_fixture_id:
                            if fixture_id.isnumeric():
                                fixture_id = str(int(fixture_id) + 1)
                        if self.increment_address:
                            # This will only increment correctly the address of the first break
                            # Other breaks will have to be adjusted in the Fixtures list after import
                            if (address + self.dmx_breaks[0].channels_count) > 512:
                                universe += 1
                                address = 1
                                dmx.ensureUniverseExists(universe)
                            else:
                                address += self.dmx_breaks[0].channels_count

                except Exception as e:
                    traceback.print_exception(e)
        Profiles.DMX_Fixtures_Local_Profile.loadLocal()
        DMX_GDTF_File.get_manufacturers_list()
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.invoke_popup(context)


class DMX_IO_FH_GDTF(bpy.types.FileHandler):
    bl_idname = "IO_FH_gdtf"
    bl_label = "GDTF"
    bl_import_operator = "dmx.import_gdtf_into_scene"
    bl_file_extensions = ".gdtf"

    @classmethod
    def poll_drop(cls, context):
        return poll_file_object_drop(context)


def menu_func_import(self, context):
    self.layout.operator(
        DMX_OT_Import_GDTF.bl_idname,
        text="General Device Type Format (.gdtf) into BlenderDMX",
    )


def register():
    bpy.utils.register_class(DMX_Break_Import)
    bpy.utils.register_class(DMX_OT_Import_GDTF)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.utils.register_class(DMX_IO_FH_GDTF)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.utils.unregister_class(DMX_IO_FH_GDTF)
    bpy.utils.unregister_class(DMX_OT_Import_GDTF)
    bpy.utils.unregister_class(DMX_Break_Import)
