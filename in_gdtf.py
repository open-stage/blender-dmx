import bpy
import shutil
import os
import traceback
from bpy_extras.io_utils import (
    ImportHelper,
)
from bpy.props import (
    StringProperty,
    BoolProperty,
    FloatVectorProperty,
    IntProperty,
    CollectionProperty,
)
from .gdtf import DMX_GDTF
from .panels import profiles as Profiles
from . import pygdtf
from .util import create_unique_fixture_name

from .i18n import DMX_Lang

_ = DMX_Lang._

from .logging import DMX_Log


class DMX_OT_Import_GDTF(bpy.types.Operator, ImportHelper):
    """Import GDTF"""

    bl_idname = "dmx.import_gdtf_into_scene"
    bl_label = "Import GDTF (.gdtf)"
    bl_options = {"PRESET", "UNDO"}

    filename_ext = ".gdtf"
    filter_glob: StringProperty(default="*.gdtf", options={"HIDDEN"})
    files: CollectionProperty(type=bpy.types.OperatorFileListElement, options={"HIDDEN", "SKIP_SAVE"})
    directory: StringProperty(subtype="DIR_PATH")

    patch: BoolProperty(
        name="Patch into the scene",
        description="Patch fixture into the scene",
        default=False,
    )

    universe: IntProperty(name=_("Universe"), description=_("DMX Universe"), default=0, min=0, max=511)

    address: IntProperty(name=_("Address"), description=_("DMX Address"), default=1, min=1, max=512)

    gel_color: FloatVectorProperty(name=_("Gel Color"), subtype="COLOR", size=4, min=0.0, max=1.0, default=(1.0, 1.0, 1.0, 1.0))

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

    increment_address: BoolProperty(name=_("Increment DMX address"), description=_("Increment DMX address"), default=True)

    increment_fixture_id: BoolProperty(name=_("Increment Fixture ID"), description=_("Increment Fixture ID if numeric"), default=True)

    fixture_id: StringProperty(name=_("Fixture ID"), description=_("The Fixture ID is an identifier of this fixture that can be used to activate / select them for programming."), default="")

    units: IntProperty(name=_("Units"), description=_("How many units of this light to add"), default=1, min=1, max=1024)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
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
        folder_path = os.path.dirname(os.path.realpath(__file__))
        folder_path = os.path.join(folder_path, "assets", "profiles")
        dmx = context.scene.dmx
        if not dmx.collection:
            context.scene.dmx.new()

        address = self.address
        universe = self.universe
        fixture_id = self.fixture_id

        for file in self.files:
            if not file.name:
                continue
            file_path = os.path.join(self.directory, file.name)
            DMX_Log.log.info(f"Importing GDTF Profile: {file_path}")
            shutil.copy(file_path, folder_path)
            if self.patch:
                try:
                    file_name = os.path.join(folder_path, file.name)
                    profile = pygdtf.FixtureType(file_name)
                    mode, channel_count = list(DMX_GDTF.getModes(file_name).items())[0]
                    for count in range(1, 1 + self.units):
                        new_name = f"{profile.name} {count}"
                        new_name = create_unique_fixture_name(new_name)
                        dmx.addFixture(new_name, file_name, universe, address, mode, self.gel_color, self.display_beams, self.add_target, fixture_id=fixture_id)
                        fixture = dmx.fixtures[-1]
                        DMX_Log.log.debug(f"Added fixture {fixture}")
                        if not fixture:
                            continue

                        if self.increment_fixture_id:
                            if fixture_id.isnumeric():
                                fixture_id = str(int(fixture_id) + 1)
                        if self.increment_address:
                            if (address + len(fixture.channels)) > 512:
                                universe += 1
                                address = 1
                                dmx.ensureUniverseExists(universe)
                            else:
                                address += len(fixture.channels)

                except Exception as e:
                    traceback.print_exception(e)
        DMX_GDTF.getManufacturerList()
        Profiles.DMX_Fixtures_Local_Profile.loadLocal()
        return {"FINISHED"}


class DMX_IO_FH_GDTF(bpy.types.FileHandler):
    bl_idname = "IO_FH_gdtf"
    bl_label = "GDTF"
    bl_import_operator = "dmx.import_gdtf_into_scene"
    bl_file_extensions = ".gdtf"


def menu_func_import(self, context):
    self.layout.operator(DMX_OT_Import_GDTF.bl_idname, text="General Device Type Format (.gdtf) into BlenderDMX")


def register():
    bpy.utils.register_class(DMX_OT_Import_GDTF)
    bpy.utils.register_class(DMX_IO_FH_GDTF)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.utils.unregister_class(DMX_IO_FH_GDTF)
    bpy.utils.unregister_class(DMX_OT_Import_GDTF)
