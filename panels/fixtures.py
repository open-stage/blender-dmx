# Copyright (C) 2020 Hugo Aboud, Kaspars Jaudzems, vanous
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

import re

import bpy
from bpy.props import BoolProperty, FloatVectorProperty, IntProperty, StringProperty
from bpy.types import Menu, Operator, Panel, UIList
from bpy_extras.io_utils import ImportHelper
from itertools import zip_longest

from ..fixture import DMX_Break
from ..gdtf_file import DMX_GDTF_File
from ..i18n import DMX_Lang
from ..logging_setup import DMX_Log
from bpy.props import CollectionProperty

_ = DMX_Lang._

# Menus #


class DMX_MT_Fixture(Menu):
    bl_label = _("DMX > Fixture Menu")
    bl_idname = "DMX_MT_Fixture"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        dmx = scene.dmx

        # "Add"
        row = layout.row()
        row.operator("dmx.add_fixture", text=_("Add"), icon="ADD")

        selected = False
        for fixture in dmx.fixtures:
            for obj in fixture.collection.objects:
                if obj in bpy.context.selected_objects:
                    selected = True
                    break
            if selected:
                break

        # "Edit"
        row = layout.row()
        row.operator("dmx.edit_fixture", text=_("Edit"), icon="GREASEPENCIL")
        row.enabled = len(dmx.fixtures) and selected

        # "Remove"
        row = layout.row()
        row.operator("dmx.remove_fixture", text=_("Remove"), icon="REMOVE")
        row.enabled = len(dmx.fixtures) and selected


class DMX_MT_Fixture_Manufacturers(Menu):
    bl_label = _("DMX > Fixture > Add > Manufacturers")
    bl_idname = "DMX_MT_Fixture_Manufacturers"

    def draw(self, context):
        layout = self.layout

        manufacturers = bpy.context.window_manager.dmx.manufacturers
        for manufacturer in manufacturers:
            row = layout.row()
            row.context_pointer_set("add_edit_panel", context.add_edit_panel)
            row.context_pointer_set("manufacturer", manufacturer)
            row.menu(
                DMX_MT_Fixture_Profiles.bl_idname,
                text=manufacturer.name.replace("_", " "),
            )


class DMX_MT_Fixture_Profiles(Menu):
    bl_label = _("DMX > Fixture > Add > Profiles")
    bl_idname = "DMX_MT_Fixture_Profiles"

    def draw(self, context):
        layout = self.layout
        manufacturer = context.manufacturer
        for profile in DMX_GDTF_File.get_manufacturer_profiles_list(manufacturer.name):
            row = layout.row()
            row.context_pointer_set("add_edit_panel", context.add_edit_panel)
            revision_name = profile["revision"].replace("_", " ")
            op = row.operator(
                DMX_OT_Fixture_Profiles.bl_idname,
                text=f"{profile['name']} {'@' if revision_name else ''} {revision_name}",
            )
            op.profile = profile["filename"]
            op.short_name = profile["short_name"]


class DMX_MT_Fixture_Mode(Menu):
    bl_label = _("DMX > Fixture > Add > Mode")
    bl_idname = "DMX_MT_Fixture_Mode"

    def draw(self, context):
        layout = self.layout
        profile = context.add_edit_panel.profile
        if not profile:
            return
        for mode_info in DMX_GDTF_File.get_profile_dmx_modes_info(profile):
            breaks_text = (
                f" {mode_info['dmx_breaks_count']} Breaks,"
                if mode_info["dmx_breaks_count"] > 1
                else ""
            )

            row = layout.row()
            row.context_pointer_set("add_edit_panel", context.add_edit_panel)
            row.operator(
                DMX_OT_Fixture_Mode.bl_idname,
                text=f"{mode_info['mode_name']},{breaks_text} {mode_info['dmx_channels_count']} Channels",
            ).mode = mode_info["mode_name"]


# Operators #


class DMX_OT_Fixture_Profiles(Operator):
    bl_label = _("DMX > Fixture > Add > Manufacturers > Profiles")
    bl_idname = "dmx.fixture_pick_profile"

    profile: StringProperty(
        name=_("Profile"), description=_("Fixture GDTF Profile"), default=""
    )
    short_name: StringProperty()

    def execute(self, context):
        context.add_edit_panel.profile = self.profile
        context.add_edit_panel.name = self.short_name
        return {"FINISHED"}


class DMX_OT_Fixture_Mode(Operator):
    bl_label = _("DMX > Fixture > Add > Mode")
    bl_idname = "dmx.fixture_pick_mode"

    mode: StringProperty(name=_("Mode"), description=_("Fixture GDTF Mode"), default="")

    def execute(self, context):
        context.add_edit_panel.mode = self.mode
        return {"FINISHED"}


class DMX_Fixture_AddEdit:
    def onProfile(self, context):
        if hasattr(context, "add_edit_panel"):
            mode_name = DMX_GDTF_File.get_profile_dmx_modes_info(
                context.add_edit_panel.profile
            )[0]["mode_name"]
            context.add_edit_panel.mode = f"{mode_name}"

    profile: StringProperty(
        name=_("Profile"),
        description=_("Fixture GDTF Profile"),
        default="",
        update=onProfile,
    )

    name: StringProperty(name=_("Name"), default="Fixture")

    dmx_breaks: CollectionProperty(name="DMX Break", type=DMX_Break)

    mode: StringProperty(name=_("Mode"), description=_("DMX Mode"), default="")

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

    advanced_edit: BoolProperty(
        name=_("Advanced edit"),
        description="Re-build fixture structure during Advanced edit",
        default=False,
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
        min=0,
        max=1024,
    )

    use_fixtures_channel_functions: BoolProperty(
        name=_("Use Fixtures Physical Properties"),
        description=_("Use Channel Functions of this fixture"),
        default=True,
    )

    use_target: BoolProperty(
        name="Use Target", description="Follow the target", default=True
    )

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        if self.units == 1:
            self.advanced_edit = True
        if self.advanced_edit:
            col.prop(self, "name")
        else:
            if self.name != "*":
                col.label(text=f"{self.name}")

        col.context_pointer_set("add_edit_panel", self)
        text_profile = _("GDTF Profile")
        fixture_type = None
        if self.profile != "":
            fixture_type = DMX_GDTF_File.profiles_list.get(self.profile)

            if fixture_type is not None:
                text_profile = (
                    f"{fixture_type['manufacturer_name']} > {fixture_type['name']}"
                )

        if self.advanced_edit:
            col.menu("DMX_MT_Fixture_Manufacturers", text=text_profile)
        text_mode = _("DMX Mode")
        if self.mode != "":
            text_mode = self.mode
        if self.advanced_edit:
            col.menu("DMX_MT_Fixture_Mode", text=text_mode)

        if fixture_type is not None:
            dmx_breaks = [
                mode for mode in fixture_type["modes"] if mode["mode_name"] == self.mode
            ][0]["dmx_breaks"]

            for dmx_break in dmx_breaks:
                new_break = None
                for existing_break in self.dmx_breaks:
                    if existing_break.dmx_break == dmx_break["dmx_break"]:
                        new_break = existing_break
                if new_break is None:
                    new_break = self.dmx_breaks.add()
                    new_break.dmx_break = dmx_break["dmx_break"]
                new_break.channels_count = dmx_break["channels_count"]

            all_breaks = [dmx_break["dmx_break"] for dmx_break in dmx_breaks]
            for idx, dmx_break in enumerate(self.dmx_breaks):
                if dmx_break.dmx_break not in all_breaks:
                    self.dmx_breaks.remove(idx)

            for dmx_break in self.dmx_breaks:
                if len(self.dmx_breaks) > 1:
                    col.label(
                        text=f"DMX Break: {dmx_break.dmx_break}, {dmx_break.channels_count}ch:"
                    )
                col.prop(dmx_break, "universe")
                col.prop(dmx_break, "address")
        else:
            for dmx_break in self.dmx_breaks:
                if len(self.dmx_breaks) > 1:
                    col.label(
                        text=f"DMX Break: {dmx_break.dmx_break}, {dmx_break.channels_count}ch:"
                    )
                col.prop(dmx_break, "universe")
                col.prop(dmx_break, "address")

        col.prop(self, "fixture_id")
        if self.units == 0:  # Edit fixtures:
            col.prop(
                self, "advanced_edit"
            )  #     Be default, only change address, don't rebuild models (slow)
            if not self.advanced_edit:
                col.operator("dmx.import_ies_file")
                col.operator("dmx.remove_ies_files")
                col.prop(self, "use_fixtures_channel_functions")
                col.prop(self, "use_target")
        else:  # Adding new fixtures:
            col.prop(self, "units")  #     Allow to define how many
        col.prop(self, "increment_address")
        col.prop(self, "increment_fixture_id")
        if self.advanced_edit:  # When adding and editing:
            col.prop(
                self, "display_beams"
            )  #     Allow not to create and draw Beams (faster, only for emitter views)
            col.prop(self, "add_target")  #     Should a target be added to the fixture
            col.prop(
                self, "gel_color"
            )  #     This works when both adding AND when editing


class DMX_OT_Fixture_Add(DMX_Fixture_AddEdit, Operator):
    bl_label = _("DMX: Add Fixture")
    bl_idname = "dmx.add_fixture"
    bl_description = _("Add fixtures to the show")
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        dmx = scene.dmx
        context.window_manager.dmx.pause_render = True  # pause renderer as partially imported fixture can cause issues during updates
        if self.name in bpy.data.collections:
            self.report(
                {"ERROR"}, _("Fixture named {} already exists").format(self.name)
            )
            return {"CANCELLED"}
        if not len(self.profile):
            self.report({"ERROR"}, _("No GDTF Profile selected."))
            return {"CANCELLED"}
        if not len(self.mode):
            self.report({"ERROR"}, _("No DMX Mode selected."))
            return {"CANCELLED"}
        dmx_breaks = self.dmx_breaks
        fixture_id = self.fixture_id
        for i in range(self.units):
            DMX_Log.log.debug(f"Adding fixture {self.name}")
            new_name = generate_fixture_name(self.name, i + 1)
            dmx.addFixture(
                new_name,
                self.profile,
                self.mode,
                dmx_breaks,
                self.gel_color,
                self.display_beams,
                self.add_target,
                fixture_id=fixture_id,
            )
            fixture = dmx.fixtures[-1]
            DMX_Log.log.debug(f"Added fixture {fixture}")
            if not fixture:
                continue

            if self.increment_fixture_id:
                if fixture_id.isnumeric():
                    fixture_id = str(int(fixture_id) + 1)
            if self.increment_address:
                for dmx_break in dmx_breaks:
                    if (dmx_break.address + dmx_break.channels_count) > 512:
                        dmx_break.universe += 1
                        dmx_break.address = 1
                        dmx.ensureUniverseExists(dmx_break.universe)
                    else:
                        dmx_break.address += dmx_break.channels_count

        context.window_manager.dmx.pause_render = False
        return {"FINISHED"}

    def invoke(self, context, event):
        # fixtures_len = len(context.scene.dmx.fixtures)
        # self.name = generate_fixture_name("Fixture", fixtures_len + 1)
        self.name = "Fixture"
        self.units = 1
        DMX_Fixture_AddEdit.profile_list_items = []
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class DMX_OT_Fixture_Edit(Operator, DMX_Fixture_AddEdit):
    bl_label = _("DMX: Edit Fixture")
    bl_idname = "dmx.edit_fixture"
    bl_description = _("Edit selected fixtures")
    bl_options = {"UNDO"}

    def execute(self, context):
        scene = context.scene
        dmx = scene.dmx
        selected = scene.dmx.selectedFixtures()
        context.window_manager.dmx.pause_render = True  # pause renderer as partially imported fixture can cause issues during updates
        # Single fixture
        if len(selected) == 1:
            fixture = selected[0]
            if self.name != fixture.name and self.name in bpy.data.collections:
                self.report(
                    {"ERROR"}, _("Fixture named {} already exists").format(self.name)
                )
                return {"CANCELLED"}

            if self.advanced_edit:
                fixture.build(
                    self.name,
                    self.profile,
                    self.mode,
                    self.dmx_breaks,
                    self.gel_color,
                    self.display_beams,
                    self.add_target,
                    uuid=fixture.uuid,
                    fixture_id=fixture.fixture_id,
                )
                context.window_manager.dmx.pause_render = False
            else:
                for mode_dmx_break, provided_dmx_break in zip_longest(
                    fixture.dmx_breaks, self.dmx_breaks
                ):
                    if mode_dmx_break is None:
                        continue
                    if provided_dmx_break is None:
                        provided_dmx_break = SimpleNamespace(
                            dmx_break=0, address=0, universe=0
                        )
                    mode_dmx_break.universe = provided_dmx_break.universe
                    mode_dmx_break.address = provided_dmx_break.address
                    dmx.ensureUniverseExists(mode_dmx_break.universe)

                if not fixture.dmx_breaks:
                    new_break = fixture.dmx_breaks.add()
                    new_break.dmx_break = 0
                    new_break.universe = 0
                    new_break.address = 0
                    new_break.channels_count = 0
                    dmx.ensureUniverseExists(0)

                fixture.fixture_id = self.fixture_id
                fixture.use_fixtures_channel_functions = (
                    self.use_fixtures_channel_functions
                )
                fixture.use_target = self.use_target
        # Multiple fixtures
        else:
            dmx_breaks = self.dmx_breaks
            fixture_id = self.fixture_id

            for i, fixture in enumerate(selected):
                name = generate_fixture_name(self.name, i + 1)
                if name != fixture.name and name in bpy.data.collections:
                    self.report(
                        {"ERROR"},
                        _("Fixture named {} already exists".format(self.name)),
                    )
                    return {"CANCELLED"}
            for i, fixture in enumerate(selected):
                name = (
                    generate_fixture_name(self.name, i + 1)
                    if (self.name != "*")
                    else fixture.name
                )
                # fixture_id = f"{self.fixture_id}{i+1}" if (self.name != '*') else fixture.name
                profile = self.profile if (self.profile != "") else fixture.profile
                mode = self.mode if (self.mode != "") else fixture.mode
                if self.advanced_edit:
                    fixture.build(
                        name,
                        profile,
                        mode,
                        dmx_breaks,
                        self.gel_color,
                        self.display_beams,
                        self.add_target,
                        uuid=fixture.uuid,
                        fixture_id=fixture_id,
                    )

                for fixture_break, edit_break in zip(fixture.dmx_breaks, dmx_breaks):
                    if edit_break:
                        fixture_break.universe = edit_break.universe
                        fixture_break.address = edit_break.address

                fixture.fixture_id = fixture_id
                fixture.use_fixtures_channel_functions = (
                    self.use_fixtures_channel_functions
                )
                fixture.use_target = self.use_target

                if self.increment_fixture_id:
                    if fixture_id.isnumeric():
                        fixture_id = str(int(fixture_id) + 1)

                if self.increment_address:
                    for dmx_break in self.dmx_breaks:
                        if dmx_break.address + dmx_break.channels_count > 512:
                            dmx_break.universe += 1
                            dmx_break.address = 1
                            dmx.ensureUniverseExists(dmx_break.universe)
                        else:
                            dmx_break.address += dmx_break.channels_count

        context.window_manager.dmx.pause_render = False  # re-enable renderer
        return {"FINISHED"}

    def invoke(self, context, event):
        scene = context.scene
        selected = scene.dmx.selectedFixtures()

        # Single fixture edit
        if len(selected) == 1:
            fixture = selected[0]
            self.name = fixture.name
            self.profile = fixture.profile
            self.dmx_breaks.clear()
            for dmx_break in fixture.dmx_breaks:
                new_break = self.dmx_breaks.add()
                new_break.dmx_break = dmx_break.dmx_break
                new_break.universe = dmx_break.universe
                new_break.address = dmx_break.address
                new_break.channels_count = dmx_break.channels_count

            if not self.dmx_breaks:
                new_break = self.dmx_breaks.add()
                new_break.dmx_break = 0
                new_break.universe = 0
                new_break.address = 0
                new_break.channels_count = 0

            self.mode = fixture.mode
            self.gel_color = [c / 255 for c in fixture.gel_color_rgb] + [1]
            self.advanced_edit = False
            self.display_beams = fixture.display_beams
            self.add_target = fixture.add_target
            self.units = 0
            self.fixture_id = fixture.fixture_id
            self.use_fixtures_channel_functions = fixture.use_fixtures_channel_functions
            self.use_target = fixture.use_target
        # Multiple fixtures edit
        else:
            self.name = "*"
            self.profile = ""
            self.dmx_breaks.clear()
            for selected_dmx_break in selected[0].dmx_breaks:
                new_break = self.dmx_breaks.add()
                new_break.universe = selected_dmx_break.universe
                new_break.address = selected_dmx_break.address
                new_break.channels_count = selected_dmx_break.channels_count

            self.mode = ""
            self.gel_color = (1, 1, 1, 1)
            self.units = 0
            self.display_beams = True
            self.add_target = True
            self.advanced_edit = False
            self.fixture_id = selected[0].fixture_id
            self.use_fixtures_channel_functions = selected[
                0
            ].use_fixtures_channel_functions
            self.use_target = selected[0].use_target

        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class DMX_OT_Fixture_Remove(Operator):
    bl_label = _("DMX > Fixture > Remove")
    bl_idname = "dmx.remove_fixture"
    bl_description = _("Remove selected fixtures from Scene")
    bl_options = {"UNDO"}

    def execute(self, context):
        scene = context.scene
        dmx = scene.dmx
        selected = dmx.selectedFixtures()
        while len(selected):
            dmx.removeFixture(selected[0])
            # needed since removeFixture alters dmx.fixtures
            selected = dmx.selectedFixtures()
        return {"FINISHED"}


class DMX_OT_IES_Remove(Operator):
    """Remove IES"""

    bl_idname = "dmx.remove_ies_files"
    bl_label = _("Remove IES Files")

    def execute(self, context):
        selected = context.scene.dmx.selectedFixtures()
        for fixture in selected:
            fixture.remove_ies()
        return {"FINISHED"}


class DMX_OT_IES_Import(Operator, ImportHelper):
    """Import IES"""

    bl_idname = "dmx.import_ies_file"
    bl_label = _("Import IES File")

    # ImportHelper mixin class uses this
    filename_ext = ".ies"

    filter_glob: StringProperty(default="*.ies", options={"HIDDEN"}, maxlen=255)

    def execute(self, context):
        selected = context.scene.dmx.selectedFixtures()
        for fixture in selected:
            fixture.add_ies(self.filepath)
        return {"FINISHED"}


# Panel #


def select_previous(context, select_target=False):
    scene = context.scene
    dmx = scene.dmx
    selected_all = dmx.selectedFixtures()
    fixtures = dmx.sortedFixtures()

    for fixture in fixtures:
        fixture.unselect()

    for selected in selected_all:
        for idx, fixture in enumerate(fixtures):
            if fixture == selected:
                idx -= 1
                if idx < 0:
                    idx = len(fixtures) - 1
                fixtures[idx].select(select_target)
                break

    if not selected_all and fixtures:
        fixtures[-1].select(select_target)

    scene.dmx.syncProgrammer()


def select_next(context, select_target=False):
    scene = context.scene
    dmx = scene.dmx
    selected_all = dmx.selectedFixtures()
    fixtures = dmx.sortedFixtures()

    for fixture in fixtures:
        fixture.unselect()

    for selected in selected_all:
        for idx, fixture in enumerate(fixtures):
            if fixture == selected:
                idx += 1
                if idx > len(fixtures) - 1:
                    idx = 0
                fixtures[idx].select(select_target)
                break

    if not selected_all and fixtures:
        fixtures[0].select(select_target)

    scene.dmx.syncProgrammer()


class DMX_OT_Fixture_SelectPrevious(Operator):
    bl_label = _("Select Previous Fixture")
    bl_idname = "dmx.fixture_previous"
    bl_description = _("Select Previous Fixture")
    bl_options = {"UNDO"}

    def execute(self, context):
        select_previous(context)
        return {"FINISHED"}


class DMX_OT_Fixture_SelectNext(Operator):
    bl_label = _("Select Next Fixture")
    bl_idname = "dmx.fixture_next"
    bl_description = _("Select Next Fixture")
    bl_options = {"UNDO"}

    def execute(self, context):
        select_next(context)
        return {"FINISHED"}


class DMX_OT_Fixture_SelectPreviousTarget(Operator):
    bl_label = _("Select Previous Target")
    bl_idname = "dmx.fixture_previous_target"
    bl_description = _("Select Previous Target")
    bl_options = {"UNDO"}

    def execute(self, context):
        select_previous(context, select_target=True)
        return {"FINISHED"}


class DMX_OT_Fixture_SelectNextTarget(Operator):
    bl_label = _("Select Next Target")
    bl_idname = "dmx.fixture_next_target"
    bl_description = _("Select Next Target")
    bl_options = {"UNDO"}

    def execute(self, context):
        select_next(context, select_target=True)
        return {"FINISHED"}


class DMX_OT_Fixture_Item(Operator):
    bl_label = _("DMX > Fixture > Item")
    bl_idname = "dmx.fixture_item"
    bl_description = _("Select Fixture")
    bl_options = {"UNDO"}

    def invoke(self, context, event):
        scene = context.scene
        dmx = scene.dmx

        if event.shift:
            from_fixture_index = dmx.selected_fixture_index
            from_fixture_fixture = dmx.get_fixture_by_index(from_fixture_index)
            context.fixture.toggleSelect()
            sorted_fixtures = dmx.sortedFixtures()

            start_selecting = False
            for sorted_fixture in sorted_fixtures:
                if start_selecting:
                    sorted_fixture.select()
                    if (
                        sorted_fixture == context.fixture
                        or sorted_fixture == from_fixture_fixture
                    ):
                        break

                if (
                    sorted_fixture == from_fixture_fixture
                    or sorted_fixture == context.fixture
                ):
                    start_selecting = True
        else:
            context.fixture.toggleSelect()

        DMX_Log.log.info(dmx.selected_fixture_index)
        return {"FINISHED"}


class DMX_OT_Fixture_ForceRemove(Operator):
    bl_label = ""
    bl_idname = "dmx.force_remove_fixture"
    bl_description = _("Remove fixture")
    bl_options = {"UNDO"}

    def execute(self, context):
        dmx = context.scene.dmx
        dmx.removeFixture(context.fixture)
        return {"FINISHED"}


class DMX_PT_Fixtures(Panel):
    bl_label = _("Fixtures")
    # bl_parent_id = "DMX_PT_Profiles"
    bl_idname = "DMX_PT_FixturesNEW"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"
    # bl_parent_id = "DMX_PT_Patch"
    # bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        dmx = scene.dmx

        # LABELS

        row = layout.row()
        c = row.column()
        c.label(text=_("Name"))
        c.ui_units_x = 8

        if dmx.column_fixture_id and not dmx.fixture_properties_editable:
            c = row.column()
            c.label(text=_("F ID"))
            c.ui_units_x = 2

        if dmx.column_unit_number and not dmx.fixture_properties_editable:
            c = row.column()
            c.ui_units_x = 2
            c.label(text=_("Unit #"))

        if dmx.column_fixture_id_numeric and not dmx.fixture_properties_editable:
            c = row.column()
            c.label(text=_("F ID #"))
            c.ui_units_x = 2

        if dmx.column_custom_id and not dmx.fixture_properties_editable:
            c = row.column()
            c.label(text=_("Cst ID"))
            c.ui_units_x = 2

        if dmx.column_dmx_address and not dmx.fixture_properties_editable:
            c = row.column()
            c.ui_units_x = 2
            if dmx.fixture_properties_editable:
                c.label(text=_("Uni"))
                c = row.column()
                c.ui_units_x = 2
                c.label(text=_("Addr"))
            else:
                c.label(text=_("Uni.Addr"))

        if dmx.column_fixture_footprint and not dmx.fixture_properties_editable:
            c = row.column()
            c.label(text=_("Foot"))
            c.ui_units_x = 2

        layout.template_list(
            "DMX_UL_Fixtures",
            "",
            dmx,
            "fixtures",
            dmx,
            "selected_fixture_index",
            rows=4,
        )

        layout.menu("DMX_MT_Fixture", text=_("Fixtures"), icon="OUTLINER_DATA_LIGHT")


class DMX_UL_Fixtures(UIList):
    def str_to_digit(self, s):
        out = 0
        try:
            if len(s):
                digs = re.compile(r"(\d*)").findall
                out = int(digs(s)[-2]) or 0
        except Exception as e:
            DMX_Log.log.error(f"Error converting text to digit {e} {s}")
            DMX_Log.log.exception(e)
        return out

    def draw_filter(self, context, layout):
        dmx = context.scene.dmx

        row = layout.row()
        row.prop(self, "filter_name", text="")
        row = layout.row()
        col = row.column()
        col.prop(dmx, "column_fixture_id")
        col.prop(dmx, "column_custom_id")
        col.prop(dmx, "column_fixture_id_numeric")
        row = row.row()
        col = row.column()
        col.prop(dmx, "column_unit_number")
        col.prop(dmx, "column_dmx_address")
        col.prop(dmx, "column_fixture_footprint")
        col.prop(dmx, "fixture_properties_editable")
        row = row.row()
        col = row.column()
        col.prop(dmx, "column_fixture_position")
        col.prop(dmx, "column_fixture_rotation")
        col.prop(dmx, "column_fixture_physical_properties")
        col.enabled = dmx.fixture_properties_editable
        row = layout.row()
        row.prop(dmx, "fixtures_sorting_order")

    def filter_items(self, context, data, propname):
        vgroups = getattr(data, propname)
        helper_funcs = bpy.types.UI_UL_list
        dmx = context.scene.dmx

        # Default return values.
        flt_flags = []
        flt_neworder = []

        flt_flags = helper_funcs.filter_items_by_name(
            self.filter_name, self.bitflag_filter_item, vgroups, "name"
        )
        if not flt_flags:
            flt_flags = [self.bitflag_filter_item] * len(vgroups)
        dmx.set_fixtures_filter(flt_flags)

        sorting_order = dmx.fixtures_sorting_order

        if sorting_order == "ADDRESS":
            _sort = [
                (
                    idx,
                    vgroups[vg.name].dmx_breaks[0].universe * 1000
                    + vgroups[vg.name].dmx_breaks[0].address,
                )
                for idx, vg in enumerate(vgroups)
            ]
            flt_neworder = helper_funcs.sort_items_helper(_sort, lambda e: e[1], False)
        elif sorting_order == "NAME":
            flt_neworder = helper_funcs.sort_items_by_name(vgroups, "name")
        elif sorting_order == "FIXTURE_ID":
            _sort = [
                (idx, self.str_to_digit(vgroups[vg.name].fixture_id))
                for idx, vg in enumerate(vgroups)
            ]
            flt_neworder = helper_funcs.sort_items_helper(_sort, lambda e: e[1], False)
        elif sorting_order == "UNIT_NUMBER":
            _sort = [
                (idx, vgroups[vg.name].unit_number) for idx, vg in enumerate(vgroups)
            ]
            flt_neworder = helper_funcs.sort_items_helper(_sort, lambda e: e[1], False)
        else:
            flt_neworder = []
        return flt_flags, flt_neworder

    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        self.use_filter_show = True
        scene = context.scene
        dmx = scene.dmx

        has_ies = len(item.ies_data) > 0
        item_dmx_break = item.dmx_breaks[0]  # just get the first breake for now
        col = layout.column()
        col.context_pointer_set("fixture", item)
        col.operator(
            "dmx.fixture_item",
            text=f"{item.name}{' 📈' if has_ies else ''} {'*' if item.dmx_cache_dirty else ''}",
            depress=item.is_selected(),
            icon="LOCKED" if item.ignore_movement_dmx else "OUTLINER_DATA_LIGHT",
        )
        col.ui_units_x = 6

        if dmx.column_fixture_id:
            c = layout.column()
            # c.label(text=f"{item.fixture_id}")
            c.ui_units_x = 2
            c.prop(item, "fixture_id", text="")
            c.enabled = dmx.fixture_properties_editable

        if dmx.column_unit_number:
            c = layout.column()
            c.ui_units_x = 2
            c.prop(item, "unit_number", text="")
            c.enabled = dmx.fixture_properties_editable

        if dmx.column_fixture_id_numeric:
            c = layout.column()
            c.prop(item, "fixture_id_numeric", text="")
            c.ui_units_x = 2
            c.enabled = dmx.fixture_properties_editable

        if dmx.column_custom_id:
            c = layout.column()
            c.prop(item, "custom_id", text="")
            c.ui_units_x = 2
            c.enabled = dmx.fixture_properties_editable

        if dmx.column_dmx_address:
            c = layout.column()
            c.ui_units_x = 2
            if dmx.fixture_properties_editable:
                c.prop(item_dmx_break, "universe", text="")
                c = layout.column()
                c.prop(item_dmx_break, "address", text="")
                c.ui_units_x = 2
            else:
                c.label(text=f"{item_dmx_break.universe}.{item_dmx_break.address}")

        if dmx.column_fixture_footprint:
            overlapping = False
            item_channels = set(
                range(
                    item.dmx_breaks[0].address,
                    item.dmx_breaks[0].address + item.dmx_breaks[0].channels_count,
                )
            )
            for fixture in dmx.fixtures:
                fixture_dmx_break = fixture.dmx_breaks[
                    0
                ]  # just get the first break for now
                if overlapping:
                    break
                if fixture.name == item.name:
                    continue
                if fixture_dmx_break.universe == item_dmx_break.universe:
                    channels = set(
                        range(
                            fixture_dmx_break.address,
                            fixture_dmx_break.address
                            + fixture_dmx_break.channels_count,
                        )
                    )
                    if not item_channels.isdisjoint(
                        channels
                    ):  # should be fastest way of checking https://stackoverflow.com/a/17735466/2949947
                        overlapping = True
                        break

            c = layout.column()
            c.ui_units_x = 2
            c.label(
                text=f"{item_dmx_break.channels_count}{'!' if overlapping else ' '}"
            )

        if dmx.column_fixture_physical_properties:
            c = layout.column()
            c.prop(item, "use_fixtures_channel_functions", text="")
            c.ui_units_x = 2
            c.enabled = dmx.fixture_properties_editable

        if dmx.fixture_properties_editable and dmx.column_fixture_position:
            body = None
            for obj in item.collection.objects:
                if obj.get("geometry_root", False):
                    body = obj
                    break
            if body is not None:
                col = layout.column()
                col.prop(body, "location", index=0, text="")
                col.ui_units_x = 3
                col = layout.column()
                col.ui_units_x = 3
                col.prop(body, "location", index=1, text="")
                col = layout.column()
                col.prop(body, "location", index=2, text="")
                col.ui_units_x = 3

        if dmx.fixture_properties_editable and dmx.column_fixture_rotation:
            body = None
            for obj in item.collection.objects:
                if obj.get("geometry_root", False):
                    body = obj
                    break
            if body is not None:
                col = layout.column()
                col.prop(body, "rotation_euler", index=0, text="")
                col.ui_units_x = 3
                col = layout.column()
                col.ui_units_x = 3
                col.prop(body, "rotation_euler", index=1, text="")
                col = layout.column()
                col.prop(body, "rotation_euler", index=2, text="")
                col.ui_units_x = 3

        if dmx.fixture_properties_editable:
            col = layout.column()
            col.context_pointer_set("fixture", item)
            col.operator("dmx.force_remove_fixture", text="", icon="CANCEL")


def pad_number(number):
    """Pad fixture number with leading zeros,
    the amount of padding zeros depends on amount of fixtures."""
    dmx = bpy.context.scene.dmx
    padding_len = len(str(len(dmx.fixtures))) + 1
    return f"{number:>0{padding_len}}"


def generate_fixture_name(name, new_id):
    dmx = bpy.context.scene.dmx
    while True:
        new_name = f"{name} {new_id:>04}"
        if new_name in dmx.fixtures:
            new_id += 1
        else:
            break
    return new_name
