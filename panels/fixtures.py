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
import uuid
import re

from dmx import pygdtf
from dmx.gdtf import *
import dmx.panels.profiles as Profiles

from bpy.props import (IntProperty,
                       FloatProperty,
                       BoolProperty,
                       FloatVectorProperty,
                       EnumProperty,
                       StringProperty,
                       CollectionProperty)

from bpy.types import (Panel,
                       Menu,
                       Operator,
                       UIList,
                       PropertyGroup)

from dmx.model import DMX_Model
from dmx.gdtf import DMX_GDTF

# Menus #

class DMX_MT_Fixture(Menu):
    bl_label = "DMX > Fixture Menu"
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
        row.operator("dmx.edit_fixture", text = "Edit", icon="GREASEPENCIL")
        row.enabled = len(dmx.fixtures) and selected

        # "Remove"
        row = layout.row()
        row.operator("dmx.remove_fixture", text="Remove", icon="REMOVE")
        row.enabled = len(dmx.fixtures) and selected
        
        # "Import GDTF Profile"
        row = layout.row()
        row.operator("dmx.import_gdtf_profile", text="Import GDTF Profile", icon="IMPORT")
        
        # "Import MVR scene"
        row = layout.row()
        row.operator("dmx.import_mvr_scene", text="Import MVR scene", icon="IMPORT")


class DMX_MT_Fixture_Manufacturers(Menu):
    bl_label = "DMX > Fixture > Add > Manufacturers"
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
    bl_label = "DMX > Fixture > Add > Profiles"
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
    bl_label = "DMX > Fixture > Add > Mode"
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
    bl_label = "DMX > Fixture > Add > Manufacturers > Profiles"
    bl_idname = "dmx.fixture_pick_profile"

    profile: StringProperty(
        name = "Profile",
        description = "Fixture GDTF Profile",
        default = ""
    )

    def execute(self, context):
        context.add_edit_panel.profile = self.profile
        return {'FINISHED'}

class DMX_OT_Fixture_Mode(Operator):
    bl_label = "DMX > Fixture > Add > Mode"
    bl_idname = "dmx.fixture_pick_mode"

    mode: StringProperty(
        name = "Mode",
        description = "Fixture GDTF Mode",
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
        name = "Profile",
        description = "Fixture GDTF Profile",
        default = "",
        update = onProfile
    )

    name: StringProperty(
        name="Name",
        default="Fixture")

    universe: IntProperty(
        name = "Universe",
        description = "DMX Universe",
        default = 0,
        min = 0,
        max = 511)

    address: IntProperty(
        name = "Address",
        description = "DMX Address",
        default = 1,
        min = 1,
        max = 512)

    mode: StringProperty(
        name = "Mode",
        description = "DMX Mode",
        default = ""
    )

    gel_color: FloatVectorProperty(
        name = "Gel Color",
        subtype = "COLOR",
        size = 4,
        min = 0.0,
        max = 1.0,
        default = (1.0,1.0,1.0,1.0))

    display_beams: BoolProperty(
        name = "Display beams",
        description="Display beam projection and cone",
        #update = onDisplayBeams,
        default = True)

    add_target: BoolProperty(
        name = "Add Target",
        description="Add target for beam to follow",
        #update = onAddTarget,
        default = True)

    uuid: StringProperty(
        name = "UUID",
        description = "Unique ID, used for MVR",
        default = str(uuid.uuid4())
            )
    re_address_only: BoolProperty(
        name = "Re-address only",
        description="Do not rebuild the model structure",
        default = False)

    fixture_id: StringProperty(
        name = "Fixture ID",
        description = "The Fixture ID is an identifier for the instance of this fixture that can be used to activate / select them for programming.",
        default = ""
            )

    units: IntProperty(
        name = "Units",
        description = "How many units of this light to add",
        default = 1,
        min = 0,
        max = 1024)

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, "name")
        col.context_pointer_set("add_edit_panel", self)
        text_profile = "GDTF Profile"
        if (self.profile != ""):
            text_profile = self.profile[:-5].replace('_',' ').split('@')
            if len(text_profile) > 1:
                text_profile = text_profile[0] + " > " + text_profile[1]
            else:
                text_profile = "Unknown manufacturer" + " > " + text_profile[0]
        col.menu("DMX_MT_Fixture_Manufacturers", text = text_profile)
        text_mode = "DMX Mode"
        if (self.mode != ""):
            text_mode = self.mode
        col.menu("DMX_MT_Fixture_Mode", text = text_mode)
        col.prop(self, "universe")
        col.prop(self, "address")
        col.prop(self, "fixture_id")
        if self.units == 0:                   # Edit fixtures:
            col.prop(self, "re_address_only") #     Be default, only change address, don't rebuild models (slow)
        else:                                 # Adding new fixtures:
            col.prop(self, "units")           #     Allow to define how many
        if not self.re_address_only:          # When adding and editing:
            col.prop(self, "display_beams")   #     Allow not to create and draw Beams (faster, only for emitter views)
            col.prop(self, "add_target")      #     Should a target be added to the fixture
            col.prop(self, "gel_color")       #     This works when both adding AND when editing

class DMX_OT_Fixture_Add(DMX_Fixture_AddEdit, Operator):
    bl_label = "DMX: Add Fixture"
    bl_idname = "dmx.add_fixture"
    bl_description = "Add fixtures to the show"
    bl_options = {'REGISTER','UNDO'}

    def execute(self, context):
        scene = context.scene
        dmx = scene.dmx
        if (self.name in bpy.data.collections):
            self.report({'ERROR'}, "Fixture named " + self.name + " already exists")
            return {'CANCELLED'}
        if (not len(self.profile)):
            self.report({'ERROR'}, "No GDTF Profile selected.")
            return {'CANCELLED'}
        if (not len(self.mode)):
            self.report({'ERROR'}, "No DMX Mode selected.")
            return {'CANCELLED'}
        for i in range(self.units):
            dmx.addFixture(self.name+" "+str(i+1), self.profile, self.universe, self.address, self.mode, self.gel_color, self.display_beams, self.add_target, fixture_id = self.fixture_id)
        return {'FINISHED'}

    def invoke(self, context, event):
        self.name = "Fixture "+str(len(context.scene.dmx.fixtures)+1)
        self.units = 1
        DMX_Fixture_AddEdit.profile_list_items = []
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

class DMX_OT_Fixture_Edit(Operator, DMX_Fixture_AddEdit):
    bl_label = "DMX: Edit Fixture"
    bl_idname = "dmx.edit_fixture"
    bl_description = "Edit selected fixtures"
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
                return {'CANCELLED'}
            if not self.re_address_only:
                fixture.build(self.name, self.profile, self.mode, self.universe, self.address, self.gel_color, self.display_beams, self.add_target, uuid = self.uuid, fixture_id = self.fixture_id)
                context.window_manager.dmx.pause_render = False
            else:
                fixture.address = self.address
                fixture.universe = self.universe
                fixture.fixture_id = self.fixture_id
        # Multiple fixtures
        else:
            address = self.address
            universe = self.universe
            for i, fixture in enumerate(selected):
                name = self.name + ' ' + str(i+1)
                if (name != fixture.name and name in bpy.data.collections):
                    return {'CANCELLED'}
            for i, fixture in enumerate(selected):
                name = (self.name + ' ' + str(i+1)) if (self.name != '*') else fixture.name
                fixture_id = f"{self.fixture_id}{i+1}" if (self.name != '*') else fixture.name
                profile = self.profile if (self.profile != '') else fixture.profile
                mode = self.mode if (self.mode != '') else fixture.mode
                if not self.re_address_only:
                    fixture.build(name, profile, mode, self.universe, address, self.gel_color, self.display_beams, self.add_target, uuid = self.uuid, fixture_id = fixture_id)
                else:
                    fixture.address = address
                    fixture.universe = universe
                if (address + len(fixture.channels)) > 512:
                    universe += 1
                    address = 1
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
            self.fixture_id = "*"

        wm = context.window_manager
        return wm.invoke_props_dialog(self)

class DMX_OT_Fixture_Remove(Operator):
    bl_label = "DMX > Fixture > Remove"
    bl_idname = "dmx.remove_fixture"
    bl_description = "Remove selected fixtures from Scene"
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
    bl_label = "Import GDTF Profile"
    bl_idname = "dmx.import_gdtf_profile"
    bl_description = "Import fixture from GDTF Profile"
    bl_options = {'UNDO'}

    filter_glob: StringProperty(default="*.gdtf", options={'HIDDEN'})

    directory: StringProperty(
        name="File Path",
        maxlen= 1024,
        default= "" )

    files: CollectionProperty(
        name="Files",
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
            print('Importing GDTF Profile: %s' % file_path)
            shutil.copy(file_path, folder_path)
        DMX_GDTF.getManufacturerList()
        Profiles.DMX_Fixtures_Local_Profile.loadLocal()
        return {'FINISHED'}


class DMX_OT_Fixture_Import_MVR(Operator):
    bl_label = "Import MVR scene"
    bl_idname = "dmx.import_mvr_scene"
    bl_description = "Import fixtures from MVR scene file. This may take a long time!"
    bl_options = {'UNDO'}

    filter_glob: StringProperty(default="*.mvr", options={'HIDDEN'})

    directory: StringProperty(
        name="File Path",
        maxlen= 1024,
        default= "" )

    files: CollectionProperty(
        name="Files",
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
            print(f'Processing MVR file: {file_path}')
            dmx = context.scene.dmx
            dmx.addMVR(file_path)
            #shutil.copy(file_path, folder_path)
        # https://developer.blender.org/T86803
        #self.report({'WARNING'}, 'Restart Blender to load the profiles.')
        return {'FINISHED'}


# Panel #

class DMX_OT_Fixture_Item(Operator):
    bl_label = "DMX > Fixture > Item"
    bl_idname = "dmx.fixture_item"
    bl_description = "Select Fixture"
    bl_options = {'UNDO'}

    def execute(self, context):
        context.fixture.toggleSelect()
        return {'FINISHED'}



class DMX_PT_Fixture_Columns_Setup(Panel):
    bl_label = "Display Columns"
    bl_idname = "DMX_PT_Fixture_Columns_Setup"
    bl_parent_id = "DMX_PT_Fixtures"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        dmx = context.scene.dmx

        row = layout.row()
        row.prop(dmx, "column_fixture_id")
        row = layout.row()
        row.prop(dmx, "column_custom_id")
        row = layout.row()
        row.prop(dmx, "column_fixture_id_numeric")
        row = layout.row()
        row.prop(dmx, "column_unit_number")
        row = layout.row()
        row.prop(dmx, "column_dmx_address")
        row = layout.row()
        row.prop(dmx, "fixtures_sorting_order")



class DMX_PT_Fixtures(Panel):
    bl_label = "Fixtures"
    bl_idname = "DMX_PT_Fixtures"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"

    def draw(self, context):
        def string_to_pairs(s, pairs=re.compile(r"(\D*)(\d*)").findall):
            return [(text.lower(), int(digits or 0)) for (text, digits) in pairs(s)[:-1]]

        layout = self.layout
        scene = context.scene
        dmx = scene.dmx

        if (len(scene.dmx.fixtures)):
            box = layout.box()
            col = box.column()
            sorting_order = dmx.fixtures_sorting_order

            if sorting_order == "ADDRESS":
                fixtures = sorted(dmx.fixtures, key=lambda c: string_to_pairs(str(c.universe*1000+c.address)))
            elif sorting_order == "NAME":
                fixtures = sorted(dmx.fixtures, key=lambda c: string_to_pairs(c.name))
            elif sorting_order == "FIXTURE_ID":
                fixtures = sorted(dmx.fixtures, key=lambda c: string_to_pairs(str(c.fixture_id)))
            elif sorting_order == "UNIT_NUMBER":
                fixtures = sorted(dmx.fixtures, key=lambda c: string_to_pairs(str(c.unit_number)))
            else:
                fixtures = dmx.fixtures

            for fixture in fixtures:
                selected = False
                for obj in fixture.collection.objects:
                    if (obj in bpy.context.selected_objects):
                        selected = True
                        break

                row = col.row()
                row.context_pointer_set("fixture", fixture)
                row.operator('dmx.fixture_item', text=fixture.name, depress=selected, icon="LOCKED" if fixture.ignore_movement_dmx else 'OUTLINER_DATA_LIGHT')

                if dmx.column_fixture_id and fixture.fixture_id:
                    c = row.column()
                    c.label(text=f"{fixture.fixture_id}")
                    c.ui_units_x = 2

                if dmx.column_unit_number:
                    c = row.column()
                    c.label(text=f"{fixture.unit_number}")
                    c.ui_units_x = 2

                if dmx.column_fixture_id_numeric:
                    c = row.column()
                    c.label(text=f"{fixture.fixture_id_numeric}")
                    c.ui_units_x = 2

                if dmx.column_custom_id:
                    c = row.column()
                    c.label(text=f"{fixture.custom_id}")
                    c.ui_units_x = 2

                if dmx.column_dmx_address:
                    c = row.column()
                    c.label(text=f"{fixture.universe}.{fixture.address}")
                    c.ui_units_x = 2
            
        layout.menu('DMX_MT_Fixture', text="Fixtures", icon="OUTLINER_DATA_LIGHT")
