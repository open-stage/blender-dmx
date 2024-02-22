#
#   BlendexDMX > Panels > Fixtures
#
#   - Add/Edit/Remove Fixtures
#   - Select Fixtures by name for programming
#
#   http://www.github.com/open-stage/BlenderDMX
#

import bpy
import os
import shutil
import re

from dmx.gdtf import *
import dmx.panels.profiles as Profiles
from dmx.util import pad_number

from bpy.props import (IntProperty,
                       BoolProperty,
                       FloatVectorProperty,
                       StringProperty,
                       CollectionProperty)

from bpy.types import (Panel,
                       Menu,
                       Operator,
                       UIList,
                       )

from dmx.gdtf import DMX_GDTF

from dmx.i18n import DMX_Lang
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
        row.operator("dmx.add_fixture", text="Add", icon="ADD")

        selected = False
        for fixture in dmx.fixtures:
            for obj in fixture.collection.objects:
                if (obj in bpy.context.selected_objects):
                    selected = True
                    break
            if (selected): break

        # "Edit"
        row = layout.row()
        row.operator("dmx.edit_fixture", text = _("Edit"), icon="GREASEPENCIL")
        row.enabled = len(dmx.fixtures) and selected

        # "Remove"
        row = layout.row()
        row.operator("dmx.remove_fixture", text=_("Remove"), icon="REMOVE")
        row.enabled = len(dmx.fixtures) and selected

        # "Import GDTF Profile"
        row = layout.row()
        row.operator("dmx.import_gdtf_profile", text=_("Import GDTF Profile"), icon="IMPORT")

        # "Import MVR scene"
        row = layout.row()
        row.operator("dmx.import_mvr_scene", text=_("Import MVR scene"), icon="IMPORT")


class DMX_MT_Fixture_Manufacturers(Menu):
    bl_label = _("DMX > Fixture > Add > Manufacturers")
    bl_idname = "DMX_MT_Fixture_Manufacturers"

    def draw(self, context):
        layout = self.layout

        manufacturers  = bpy.context.window_manager.dmx.manufacturers
        for manufacturer in manufacturers:
            row = layout.row()
            row.context_pointer_set("add_edit_panel", context.add_edit_panel)
            row.context_pointer_set("manufacturer", manufacturer)
            row.menu(DMX_MT_Fixture_Profiles.bl_idname, text=manufacturer.name.replace("_"," "))

class DMX_MT_Fixture_Profiles(Menu):
    bl_label = _("DMX > Fixture > Add > Profiles")
    bl_idname = "DMX_MT_Fixture_Profiles"

    def draw(self, context):
        layout = self.layout
        manufacturer = context.manufacturer
        for profile in DMX_GDTF.getProfileList(manufacturer.name):
            row = layout.row()
            row.context_pointer_set("add_edit_panel", context.add_edit_panel)
            revision = f" ({profile[2]})" if profile[2] else ""
            row.operator(DMX_OT_Fixture_Profiles.bl_idname, text=f"{profile[1]}{revision}".replace('_',' ')).profile = profile[0]

class DMX_MT_Fixture_Mode(Menu):
    bl_label = _("DMX > Fixture > Add > Mode")
    bl_idname = "DMX_MT_Fixture_Mode"

    def draw(self, context):
        layout = self.layout
        profile = context.add_edit_panel.profile
        if (not profile): return
        for mode, channel_count in DMX_GDTF.getModes(profile).items():
            row = layout.row()
            row.context_pointer_set("add_edit_panel", context.add_edit_panel)
            row.operator(DMX_OT_Fixture_Mode.bl_idname, text=f"{mode}, {channel_count} channels").mode = mode

# Operators #

class DMX_OT_Fixture_Profiles(Operator):
    bl_label = _("DMX > Fixture > Add > Manufacturers > Profiles")
    bl_idname = "dmx.fixture_pick_profile"

    profile: StringProperty(
        name = _("Profile"),
        description = _("Fixture GDTF Profile"),
        default = ""
    )

    def execute(self, context):
        context.add_edit_panel.profile = self.profile
        return {'FINISHED'}

class DMX_OT_Fixture_Mode(Operator):
    bl_label = _("DMX > Fixture > Add > Mode")
    bl_idname = "dmx.fixture_pick_mode"

    mode: StringProperty(
        name = _("Mode"),
        description = _("Fixture GDTF Mode"),
        default = ""
    )

    def execute(self, context):
        context.add_edit_panel.mode = self.mode
        return {'FINISHED'}


class DMX_Fixture_AddEdit():

    def onProfile(self, context):
        if hasattr(context,'add_edit_panel'):
            mode, channel_count = list(DMX_GDTF.getModes(context.add_edit_panel.profile).items())[0]
            context.add_edit_panel.mode =f"{mode}"


    profile: StringProperty(
        name = _("Profile"),
        description = _("Fixture GDTF Profile"),
        default = "",
        update = onProfile
    )

    name: StringProperty(
        name=_("Name"),
        default="Fixture")

    universe: IntProperty(
        name = _("Universe"),
        description = _("DMX Universe"),
        default = 0,
        min = 0,
        max = 511)

    address: IntProperty(
        name = _("Address"),
        description = _("DMX Address"),
        default = 1,
        min = 1,
        max = 512)

    mode: StringProperty(
        name = _("Mode"),
        description = _("DMX Mode"),
        default = ""
    )

    gel_color: FloatVectorProperty(
        name = _("Gel Color"),
        subtype = "COLOR",
        size = 4,
        min = 0.0,
        max = 1.0,
        default = (1.0,1.0,1.0,1.0))

    display_beams: BoolProperty(
        name = _("Display beams"),
        description=_("Display beam projection and cone"),
        #update = onDisplayBeams,
        default = True)

    add_target: BoolProperty(
        name = _("Add Target"),
        description=_("Add target for beam to follow"),
        #update = onAddTarget,
        default = True)

    re_address_only: BoolProperty(
        name = "Re-address only",
        description="Do not rebuild the model structure",
        default = False)

    increment_address: BoolProperty(
        name = _("Increment DMX address"),
        description=_("Increment DMX address"),
        default = True)

    increment_fixture_id: BoolProperty(
        name = _("Increment Fixture ID"),
        description=_("Increment Fixture ID if numeric"),
        default = True)

    fixture_id: StringProperty(
        name = _("Fixture ID"),
        description = _("The Fixture ID is an identifier for the instance of this fixture that can be used to activate / select them for programming."),
        default = ""
            )

    units: IntProperty(
        name = _("Units"),
        description = _("How many units of this light to add"),
        default = 1,
        min = 0,
        max = 1024)

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        if not self.re_address_only:
            col.prop(self, "name")
        col.context_pointer_set("add_edit_panel", self)
        text_profile = _("GDTF Profile")
        if (self.profile != ""):
            text_profile = self.profile[:-5].replace('_',' ').split('@')
            if len(text_profile) > 1:
                text_profile = text_profile[0] + " > " + text_profile[1]
            else:
                text_profile = _("Unknown manufacturer") + " > " + text_profile[0]
        if not self.re_address_only:
            col.menu("DMX_MT_Fixture_Manufacturers", text = text_profile)
        text_mode = _("DMX Mode")
        if (self.mode != ""):
            text_mode = self.mode
        if not self.re_address_only:
            col.menu("DMX_MT_Fixture_Mode", text = text_mode)
        col.prop(self, "universe")
        col.prop(self, "address")
        col.prop(self, "fixture_id")
        if self.units == 0:                   # Edit fixtures:
            col.prop(self, "re_address_only") #     Be default, only change address, don't rebuild models (slow)
        else:                                 # Adding new fixtures:
            col.prop(self, "units")           #     Allow to define how many
        col.prop(self, "increment_address")
        col.prop(self, "increment_fixture_id")
        if not self.re_address_only:          # When adding and editing:
            col.prop(self, "display_beams")   #     Allow not to create and draw Beams (faster, only for emitter views)
            col.prop(self, "add_target")      #     Should a target be added to the fixture
            col.prop(self, "gel_color")       #     This works when both adding AND when editing

class DMX_OT_Fixture_Add(DMX_Fixture_AddEdit, Operator):
    bl_label = _("DMX: Add Fixture")
    bl_idname = "dmx.add_fixture"
    bl_description = _("Add fixtures to the show")
    bl_options = {'REGISTER','UNDO'}

    def execute(self, context):
        scene = context.scene
        dmx = scene.dmx
        if (self.name in bpy.data.collections):
            self.report({'ERROR'}, _("Fixture named {} already exists").format(self.name))
            return {'CANCELLED'}
        if (not len(self.profile)):
            self.report({'ERROR'}, _("No GDTF Profile selected."))
            return {'CANCELLED'}
        if (not len(self.mode)):
            self.report({'ERROR'}, _("No DMX Mode selected."))
            return {'CANCELLED'}
        address = self.address
        universe = self.universe
        fixture_id = self.fixture_id
        for i in range(self.units):
            DMX_Log.log.debug(f"Adding fixture {self.name}")
            dmx.addFixture(f"{self.name} {pad_number(i+1)}", self.profile, universe, address, self.mode,
                           self.gel_color, self.display_beams, self.add_target, fixture_id = fixture_id)
            fixture = dmx.fixtures[-1]
            DMX_Log.log.debug(f"Added fixture {fixture}")
            if not fixture:
                continue

            if self.increment_fixture_id:
                if fixture_id.isnumeric():
                    fixture_id = str(int(fixture_id)+1)
            if self.increment_address:
                if (address + len(fixture.channels)) > 512:
                    universe += 1
                    address = 1
                    dmx.ensureUniverseExists(universe)
                else:
                    address += len(fixture.channels)

        return {'FINISHED'}

    def invoke(self, context, event):
        fixtures_len = len(context.scene.dmx.fixtures)
        self.name = f"Fixture {pad_number(fixtures_len + 1)}"
        self.units = 1
        DMX_Fixture_AddEdit.profile_list_items = []
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

class DMX_OT_Fixture_Edit(Operator, DMX_Fixture_AddEdit):
    bl_label = _("DMX: Edit Fixture")
    bl_idname = "dmx.edit_fixture"
    bl_description = _("Edit selected fixtures")
    bl_options = {'UNDO'}

    def execute(self, context):
        scene = context.scene
        dmx = scene.dmx
        selected = scene.dmx.selectedFixtures()
        context.window_manager.dmx.pause_render = True # pause renderer as partially imported fixture can cause issues during updates
        # Single fixture
        if (len(selected) == 1):
            fixture = selected[0]
            if (self.name != fixture.name and self.name in bpy.data.collections):
                self.report({'ERROR'}, _("Fixture named {} already exists").format(self.name))
                return {'CANCELLED'}
            if not self.re_address_only:
                fixture.build(self.name, self.profile, self.mode, self.universe, self.address, self.gel_color, self.display_beams, self.add_target, uuid = fixture.uuid, fixture_id = fixture.fixture_id)
                context.window_manager.dmx.pause_render = False
            else:
                fixture.address = self.address
                fixture.universe = self.universe
                dmx.ensureUniverseExists(self.universe)
                fixture.fixture_id = self.fixture_id
        # Multiple fixtures
        else:
            address = self.address
            universe = self.universe
            fixture_id = self.fixture_id

            for i, fixture in enumerate(selected):
                name = f"{self.name} {pad_number(i+1)}"
                if (name != fixture.name and name in bpy.data.collections):
                    self.report({'ERROR'}, _("Fixture named {} already exists".format(self.name)))
                    return {'CANCELLED'}
            for i, fixture in enumerate(selected):
                name = f"{self.name} {pad_number(i+1)}" if (self.name != '*') else fixture.name
                #fixture_id = f"{self.fixture_id}{i+1}" if (self.name != '*') else fixture.name
                profile = self.profile if (self.profile != '') else fixture.profile
                mode = self.mode if (self.mode != '') else fixture.mode
                if not self.re_address_only:
                    fixture.build(name, profile, mode, self.universe, address, self.gel_color, self.display_beams, self.add_target, uuid = fixture.uuid, fixture_id = fixture_id)
                else:
                    fixture.address = address
                    fixture.universe = universe
                    fixture.fixture_id = fixture_id

                if self.increment_fixture_id:
                    if fixture_id.isnumeric():
                        fixture_id = str(int(fixture_id)+1)

                if self.increment_address:
                    if (address + len(fixture.channels)) > 512:
                        universe += 1
                        address = 1
                        dmx.ensureUniverseExists(universe)
                    else:
                        address += len(fixture.channels)

        context.window_manager.dmx.pause_render = False # re-enable renderer
        return {'FINISHED'}

    def invoke(self, context, event):
        scene = context.scene
        selected = scene.dmx.selectedFixtures()

        # Single fixture
        if (len(selected) == 1):
            fixture = selected[0]
            self.name = fixture.name
            self.profile = fixture.profile
            self.universe = fixture.universe
            self.address = fixture.address
            self.mode = fixture.mode
            self.gel_color = fixture.gel_color
            self.re_address_only = True
            self.display_beams = fixture.display_beams
            self.add_target = fixture.add_target
            self.units = 0
            self.fixture_id = fixture.fixture_id
        # Multiple fixtures
        else:
            self.name = '*'
            self.profile = ''
            self.universe = 0
            self.address = selected[0].address
            self.mode = ''
            self.gel_color = (255,255,255,255)
            self.units = 0
            self.display_beams = True
            self.add_target = True
            self.re_address_only = True
            self.fixture_id = selected[0].fixture_id

        wm = context.window_manager
        return wm.invoke_props_dialog(self)

class DMX_OT_Fixture_Remove(Operator):
    bl_label = _("DMX > Fixture > Remove")
    bl_idname = "dmx.remove_fixture"
    bl_description = _("Remove selected fixtures from Scene")
    bl_options = {'UNDO'}

    def execute(self, context):
        scene = context.scene
        dmx = scene.dmx
        selected = dmx.selectedFixtures()
        while len(selected):
            dmx.removeFixture(selected[0])
            # needed since removeFixture alters dmx.fixtures
            selected = dmx.selectedFixtures()
        return {'FINISHED'}

class DMX_OT_Fixture_Import_GDTF(Operator):
    bl_label = _("Import GDTF Profile")
    bl_idname = "dmx.import_gdtf_profile"
    bl_description = _("Import fixture from GDTF Profile")
    bl_options = {'UNDO'}

    filter_glob: StringProperty(default="*.gdtf", options={'HIDDEN'})

    directory: StringProperty(
        name=_("File Path"),
        maxlen= 1024,
        default= "" )

    files: CollectionProperty(
        name=_("Files"),
        type=bpy.types.OperatorFileListElement
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
        folder_path = os.path.join(folder_path, '..', 'assets', 'profiles')
        for file in self.files:
            file_path = os.path.join(self.directory, file.name)
            DMX_Log.log.info('Importing GDTF Profile: %s' % file_path)
            shutil.copy(file_path, folder_path)
        DMX_GDTF.getManufacturerList()
        Profiles.DMX_Fixtures_Local_Profile.loadLocal()
        return {'FINISHED'}


class DMX_OT_Fixture_Import_MVR(Operator):
    bl_label = _("Import MVR scene")
    bl_idname = "dmx.import_mvr_scene"
    bl_description = _("Import fixtures from MVR scene file. This may take a long time!")
    bl_options = {'UNDO'}

    filter_glob: StringProperty(default="*.mvr", options={'HIDDEN'})

    directory: StringProperty(
        name=_("File Path"),
        maxlen= 1024,
        default= "" )

    files: CollectionProperty(
        name=_("Files"),
        type=bpy.types.OperatorFileListElement
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
        folder_path = os.path.join(folder_path, '..', 'assets', 'profiles')
        for file in self.files:
            file_path = os.path.join(self.directory, file.name)
            print("INFO", f'Processing MVR file: {file_path}')
            dmx = context.scene.dmx
            dmx.addMVR(file_path)
            #shutil.copy(file_path, folder_path)
        # https://developer.blender.org/T86803
        #self.report({'WARNING'}, 'Restart Blender to load the profiles.')
        return {'FINISHED'}


# Panel #

class DMX_OT_Fixture_SelectPrevious(Operator):
    bl_label = " "
    bl_idname = "dmx.fixture_previous"
    bl_description = "Select Previous Fixture"
    bl_options = {'UNDO'}

    def execute(self, context):
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
                        idx = len(fixtures)-1
                    fixtures[idx].select()
                    break

        if not selected_all and fixtures:
            fixtures[-1].select()

        return {'FINISHED'}

class DMX_OT_Fixture_SelectNext(Operator):
    bl_label = " "
    bl_idname = "dmx.fixture_next"
    bl_description = "Select Next Fixture"
    bl_options = {'UNDO'}

    def execute(self, context):
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
                    if idx > len(fixtures)-1:
                        idx = 0
                    fixtures[idx].select()
                    break

        if not selected_all and fixtures:
            fixtures[0].select()

        return {'FINISHED'}

class DMX_OT_Fixture_Item(Operator):
    bl_label = _("DMX > Fixture > Item")
    bl_idname = "dmx.fixture_item"
    bl_description = _("Select Fixture")
    bl_options = {'UNDO'}

    def invoke(self, context, event):
        scene = context.scene
        dmx = scene.dmx

        if event.shift:
            from_fixture_index = dmx.selected_fixture_index
            from_fixture_fixture = dmx.get_fixture_by_index(from_fixture_index)
            context.fixture.toggleSelect()
            to_fixture_index = dmx.selected_fixture_index

            sorted_fixtures = dmx.sortedFixtures()

            start_selecting = False
            for sorted_fixture in sorted_fixtures:
                if start_selecting:
                    sorted_fixture.select()
                    if sorted_fixture == context.fixture or sorted_fixture == from_fixture_fixture:
                        break

                if sorted_fixture == from_fixture_fixture or sorted_fixture == context.fixture:
                    start_selecting = True
        else:
            context.fixture.toggleSelect()

        DMX_Log.log.info(dmx.selected_fixture_index)
        return {'FINISHED'}


class DMX_OT_Fixture_ForceRemove(Operator):
    bl_label = ""
    bl_idname = "dmx.force_remove_fixture"
    bl_description = _("Remove fixture")
    bl_options = {'UNDO'}

    def execute(self, context):
        dmx = context.scene.dmx
        dmx.removeFixture(context.fixture)
        return {'FINISHED'}


class DMX_PT_Fixtures(Panel):
    bl_label = _("Fixtures")
    #bl_parent_id = "DMX_PT_Profiles"
    bl_idname = "DMX_PT_FixturesNEW"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"
    # bl_parent_id = "DMX_PT_Patch"
    #bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        dmx = scene.dmx

        row = layout.row()
        c = row.column()
        c.label(text=_("Name"))
        c.ui_units_x = 8

        if dmx.column_fixture_id and not dmx.fixture_properties_editable:

            c = row.column()
            c.label(text="F ID")
            c.ui_units_x = 2

        if dmx.column_unit_number and not dmx.fixture_properties_editable:
            c = row.column()
            c.ui_units_x = 2
            c.label(text="Unit #")

        if dmx.column_fixture_id_numeric and not dmx.fixture_properties_editable:
            c = row.column()
            c.label(text="F ID #")
            c.ui_units_x = 2

        if dmx.column_custom_id and not dmx.fixture_properties_editable:
            c = row.column()
            c.label(text="Cst ID")
            c.ui_units_x = 2

        if dmx.column_dmx_address and not dmx.fixture_properties_editable:
            c = row.column()
            c.ui_units_x = 2
            if dmx.fixture_properties_editable:
                c.label(text="Uni")
                c = row.column()
                c.ui_units_x = 2
                c.label(text="Addr")
            else:
                c.label(text="Uni.Addr")

        layout.template_list(
            "DMX_UL_Fixtures",
            "",
            dmx,
            "fixtures",
            dmx,
            "selected_fixture_index",
            rows=4,
        )

        layout.menu('DMX_MT_Fixture', text=_("Fixtures"), icon="OUTLINER_DATA_LIGHT")

class DMX_UL_Fixtures(UIList):

    def str_to_digit(self, s):
        out = 0
        try:
            if len(s):
                digs=re.compile(r"(\d*)").findall
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
        row = row.row()
        col = row.column()
        col.prop(dmx, "column_fixture_id_numeric")
        col.prop(dmx, "column_unit_number")
        row = row.row()
        col = row.column()
        col.prop(dmx, "column_dmx_address")
        col.prop(dmx, "fixture_properties_editable")
        if dmx.fixture_properties_editable:
            col.prop(dmx, "column_fixture_position")
        row = layout.row()
        row.prop(dmx, "fixtures_sorting_order")

    def filter_items(self, context, data, propname):
        vgroups = getattr(data, propname)
        helper_funcs = bpy.types.UI_UL_list
        dmx = context.scene.dmx

        # Default return values.
        flt_flags = []
        flt_neworder = []

        flt_flags = helper_funcs.filter_items_by_name(self.filter_name, self.bitflag_filter_item, vgroups, "name")
        if not flt_flags:
            flt_flags = [self.bitflag_filter_item] * len(vgroups)
        dmx.set_fixtures_filter(flt_flags)

        sorting_order = dmx.fixtures_sorting_order

        if sorting_order == "ADDRESS":
            _sort = [(idx, vgroups[vg.name].universe*1000+vgroups[vg.name].address) for idx, vg in enumerate(vgroups)]
            flt_neworder = helper_funcs.sort_items_helper(_sort, lambda e: e[1], False)
        elif sorting_order == "NAME":
            flt_neworder = helper_funcs.sort_items_by_name(vgroups, "name")
        elif sorting_order == "FIXTURE_ID":
            _sort = [(idx, self.str_to_digit(vgroups[vg.name].fixture_id)) for idx, vg in enumerate(vgroups)]
            flt_neworder = helper_funcs.sort_items_helper(_sort, lambda e: e[1], False)
        elif sorting_order == "UNIT_NUMBER":
            _sort = [(idx, vgroups[vg.name].unit_number) for idx, vg in enumerate(vgroups)]
            flt_neworder = helper_funcs.sort_items_helper(_sort, lambda e: e[1], False)
        else:
            flt_neworder=[]
        return flt_flags, flt_neworder

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        self.use_filter_show = True
        scene = context.scene
        dmx = scene.dmx

        col = layout.column()
        col.context_pointer_set("fixture", item)
        col.operator('dmx.fixture_item', text=f"{item.name}", depress=item.is_selected(), icon="LOCKED" if item.ignore_movement_dmx else 'OUTLINER_DATA_LIGHT')
        col.ui_units_x = 6

        if dmx.column_fixture_id:
            c = layout.column()
            #c.label(text=f"{item.fixture_id}")
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
                c.prop(item, "universe", text="")
                c = layout.column()
                c.prop(item, "address", text="")
                c.ui_units_x = 2
            else:
                c.label(text=f"{item.universe}.{item.address}")

        if dmx.fixture_properties_editable and dmx.column_fixture_position:
            body = None
            for obj in item.collection.objects:
                if obj.get("geometry_root", False):
                    body = obj
                    break
            if body is not None:
                col = layout.column()
                col.prop(body, "location", index=0, text='')
                col.ui_units_x = 3
                col = layout.column()
                col.ui_units_x = 3
                col.prop(body, "location", index=1, text='')
                col = layout.column()
                col.prop(body, "location", index=2, text='')
                col.ui_units_x = 3

        if dmx.fixture_properties_editable:
            col = layout.column()
            col.context_pointer_set("fixture", item)
            col.operator("dmx.force_remove_fixture", text="", icon="CANCEL")
