#
#   BlendexDMX > Panels > Fixtures
#
#   - Add/Edit/Remove Fixtures
#   - Select Fixtures by name for programming
#
#   http://www.github.com/hugoaboud/BlenderDMX
#

import bpy
import os
import shutil

from bpy.props import (IntProperty,
                       FloatProperty,
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


class DMX_MT_Fixture_Manufacturers(Menu):
    bl_label = "DMX > Fixture > Add > Manufacturers"
    bl_idname = "DMX_MT_Fixture_Manufacturers"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        dmx = scene.dmx

        for manufacturer in context.add_edit_panel.rna_type.properties['manufacturers'].enum_items:
            row = layout.row()
            row.context_pointer_set("add_edit_panel", context.add_edit_panel)
            row.context_pointer_set("manufacturer", manufacturer)
            row.menu(DMX_MT_Fixture_Profiles.bl_idname, text=manufacturer.identifier.replace("_"," "))

class DMX_MT_Fixture_Profiles(Menu):
    bl_label = "DMX > Fixture > Add > Profiles"
    bl_idname = "DMX_MT_Fixture_Profiles"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        dmx = scene.dmx
        manufacturer = context.manufacturer.identifier
        print('oy')
        for profile in DMX_GDTF.getProfileList(manufacturer):
            row = layout.row()
            row.context_pointer_set("add_edit_panel", context.add_edit_panel)
            row.operator(DMX_OT_Fixture_Profiles.bl_idname, text=profile[1].replace("_"," ")).profile = profile[0]

class DMX_MT_Fixture_Mode(Menu):
    bl_label = "DMX > Fixture > Add > Mode"
    bl_idname = "DMX_MT_Fixture_Mode"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        dmx = scene.dmx
        profile = context.add_edit_panel.profile
        if (not profile): return
        for mode in DMX_GDTF.getModes(profile):
            row = layout.row()
            row.context_pointer_set("add_edit_panel", context.add_edit_panel)
            row.operator(DMX_OT_Fixture_Mode.bl_idname, text=mode).mode = mode

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

    manufacturer_list_items = DMX_GDTF.getManufacturerList()

    manufacturers: EnumProperty(
        name = "Manufacturers",
        description = "Fixture GDTF Manufacturers",
        items=manufacturer_list_items
    )

    def onProfile(self, context):
        if hasattr(context,'add_edit_panel'):
            context.add_edit_panel.mode = DMX_GDTF.getModes(context.add_edit_panel.profile)[0]

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

    units: IntProperty(
        name = "Units",
        description = "How many units of this light to add",
        default = 1,
        min = 1,
        max = 1024)

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, "name")
        col.context_pointer_set("add_edit_panel", self)
        text_profile = "GDTF Profile"
        if (self.profile != ""):
            text_profile = self.profile[:-5].replace('_',' ').split('@')
            text_profile = text_profile[0] + " > " + text_profile[1]
        col.menu("DMX_MT_Fixture_Manufacturers", text = text_profile)
        text_mode = "DMX Mode"
        if (self.mode != ""):
            text_mode = self.mode
        col.menu("DMX_MT_Fixture_Mode", text = text_mode)
        col.prop(self, "universe")
        col.prop(self, "address")
        col.prop(self, "gel_color")
        if (self.units > 0):
            col.prop(self, "units")

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
            dmx.addFixture(self.name+" "+str(i+1), self.profile, self.universe, self.address, self.mode, self.gel_color)
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
        # Single fixture
        if (len(selected) == 1):
            fixture = selected[0]
            if (self.name != fixture.name and self.name in bpy.data.collections):
                return {'CANCELLED'}
            fixture.build(self.name, self.profile, self.mode, self.universe, self.address, self.gel_color)
        # Multiple fixtures
        else:
            address = self.address
            for i, fixture in enumerate(selected):
                name = self.name + ' ' + str(i+1)
                if (name != fixture.name and name in bpy.data.collections):
                    return {'CANCELLED'}
            for i, fixture in enumerate(selected):
                name = (self.name + ' ' + str(i+1)) if (self.name != '*') else fixture.name
                profile = self.profile if (self.profile != '') else fixture.profile
                mode = self.mode if (self.mode != '') else fixture.mode
                fixture.build(name, profile, mode, self.universe, address, self.gel_color)
                address += len(fixture.channels)
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
            self.units = 0
        # Multiple fixtures
        else:
            self.name = '*'
            self.profile = ''
            self.universe = 0
            self.address = selected[0].address
            self.mode = ''
            self.gel_color = (255,255,255,255)
            self.units = 0

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
        # https://developer.blender.org/T86803
        self.report({'WARNING'}, 'Restart Blender to load the profiles.')
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

class DMX_PT_Fixtures(Panel):
    bl_label = "Fixtures"
    bl_idname = "DMX_PT_Fixtures"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        dmx = scene.dmx

        if (len(scene.dmx.fixtures)):
            box = layout.box()
            col = box.column()
            for fixture in scene.dmx.fixtures:
                selected = False
                for obj in fixture.collection.objects:
                    if (obj in bpy.context.selected_objects):
                        selected = True
                        break

                row = col.row()
                row.context_pointer_set("fixture", fixture)
                row.operator('dmx.fixture_item', text=fixture.name, depress=selected, icon='OUTLINER_DATA_LIGHT')
                c = row.column()
                c.label(text=str(fixture.universe)+'.'+str(fixture.address))
                c.ui_units_x = 2  
            
        layout.menu('DMX_MT_Fixture', text="Fixtures", icon="OUTLINER_DATA_LIGHT")
