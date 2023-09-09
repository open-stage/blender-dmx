#
#   BlendexDMX > Panels > Setup
#
#   - Setup a DMX collection and data structure to store the DMX parameters
#   - Change background color
#   - Create/Update a Box that fits the whole scene with a Volume Scatter
#   shader, and control it's visibility and density (for simulating haze)
#
#   http://www.github.com/open-stage/BlenderDMX
#

import bpy
from bpy.props import PointerProperty
from bpy.types import (Panel, Operator)

from dmx.material import getVolumeScatterMaterial
from dmx.util import getSceneRect

# Operators #

class DMX_OT_Setup_NewShow(Operator):
    bl_label = "DMX > Setup > New Show"
    bl_description = "Clear any existing DMX data and create a new show."
    bl_idname = "dmx.new_show"
    bl_options = {'UNDO'}

    def execute(self, context):
        # DMX setup
        context.scene.dmx.new()
        return {'FINISHED'}

class DMX_OT_Setup_Volume_Create(Operator):
    bl_label = "DMX > Setup > Create/Update Volume Box"
    bl_description = "Create/Update a Box on the scene bounds with a Volume Scatter shader"
    bl_idname = "dmx.create_volume"
    bl_options = {'UNDO'}

    def execute(self, context):
        dmx = context.scene.dmx
        # Get scene bounds
        min, max = getSceneRect()
        pos = [min[i]+(max[i]-min[i])/2 for i in range(3)]
        scale = [max[i]-min[i] for i in range(3)]
        # Remove old DMX collection if present
        if ("DMX_Volume" not in bpy.data.objects):
            bpy.ops.mesh.primitive_cube_add(size=1.0)
            dmx.volume = bpy.context.selected_objects[0]
            dmx.volume.name = "DMX_Volume"
            dmx.volume.display_type = 'WIRE'
            material = getVolumeScatterMaterial()
            dmx.volume.data.materials.append(material)
        else:
            dmx.volume = bpy.data.objects["DMX_Volume"]

        if len(dmx.volume.data.materials):
            dmx.volume_nodetree = dmx.volume.data.materials[0].node_tree
        else:
            material = getVolumeScatterMaterial()
            dmx.volume.data.materials.append(material)
            dmx.volume_nodetree = dmx.volume.data.materials[0].node_tree
        
        old_collections = dmx.volume.users_collection
        if (dmx.collection not in old_collections):
            dmx.collection.objects.link(dmx.volume)
            for collection in old_collections:
                collection.objects.unlink(dmx.volume)

        dmx.volume.location = pos
        dmx.volume.scale = scale

        return {'FINISHED'}

# Sub-panels #

class DMX_PT_Setup_Background(Panel):
    bl_label = "Background"
    bl_idname = "DMX_PT_Setup_Background"
    bl_parent_id = "DMX_PT_Setup"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        dmx = context.scene.dmx
        layout.prop(context.scene.dmx,'background_color',text='')

class DMX_PT_Setup_Volume(Panel):
    bl_label = "Volume"
    bl_idname = "DMX_PT_Setup_Volume"
    bl_parent_id = "DMX_PT_Setup"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        dmx = context.scene.dmx

        layout.prop(context.scene.dmx, 'volume_preview')
        layout.prop(context.scene.dmx, 'disable_overlays')

        layout.operator("dmx.create_volume", text = ('Update Volume Box' if dmx.volume else 'Create Volume Box'), icon='MESH_CUBE')

        row = layout.row()
        row.prop(context.scene.dmx, 'volume_enabled')
        row.enabled = (dmx.volume != None)

        row = layout.row()
        row.prop(context.scene.dmx, 'volume_density')
        row.enabled = (dmx.volume != None)

class DMX_PT_Setup_Debug(Panel):
    bl_label = "Extras"
    bl_idname = "DMX_PT_Setup_Debug"
    bl_parent_id = "DMX_PT_Setup"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        dmx = context.scene.dmx
        row = layout.row()
        row.prop(context.scene.dmx, 'mvr_import_in_progress')
        row = layout.row()
        row.prop(context.scene.dmx,'display_pigtails')
        row = layout.row()
        row.prop(context.scene.dmx, 'logging_level')

# Panel #

class DMX_PT_Setup(Panel):
    bl_label = "Setup"
    bl_idname = "DMX_PT_Setup"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        dmx = context.scene.dmx
        if (not dmx.collection):
            layout.operator("dmx.new_show", text="Create New Show", icon="LIGHT")
