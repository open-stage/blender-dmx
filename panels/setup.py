#
#   BlendexDMX > Panels > Setup
#
#   - Setup a DMX collection and data structure to store the DMX parameters
#   - Change background color
#   - Create/Update a Box that fits the whole scene with a Volume Scatter
#   shader, and control it's visibility and density (for simulating haze)
#
#   http://www.github.com/hugoaboud/BlenderDMX
#

import bpy
from bpy.props import PointerProperty
from bpy.types import (Panel, Operator)

from dmx.util import getSceneRect

# Operators #

class DMX_OT_Setup_NewShow(Operator):
    bl_label = "DMX: Create New Show"
    bl_description = "Clear any existing DMX data and create a new show."
    bl_idname = "dmx.new_show"
    bl_options = {'UNDO'}

    def execute(self, context):
        # DMX setup
        context.scene.dmx.new()
        return {'FINISHED'}

class DMX_OT_Setup_Volume_Create(Operator):
    bl_label = "DMX: Create Volume Box"
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

            material = bpy.data.materials.new("DMX_Volume")
            material.use_nodes = True
            material.node_tree.nodes.remove(material.node_tree.nodes[1])
            material.node_tree.nodes.new("ShaderNodeVolumeScatter")
            material.node_tree.links.new(material.node_tree.nodes[0].inputs[1], material.node_tree.nodes[1].outputs[0])

            dmx.volume_nodetree = material.node_tree
            dmx.volume.data.materials.append(material)

        else:
            dmx.volume = bpy.data.objects["DMX_Volume"]

        dmx.volume.location = pos
        dmx.volume.scale = scale

        bpy.ops.object.select_all(action='DESELECT')
        dmx.volume.select_set(True)
        bpy.ops.collection.objects_remove_all()
        bpy.context.scene.collection.objects.link(dmx.volume)

        return {'FINISHED'}

# Sub-panels #

class DMX_PT_Setup_Background(Panel):
    bl_label = "Background"
    bl_idname = "dmx.panel.setup.background"
    bl_parent_id = "dmx.panel.setup"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(self,context):
        return context.object is not None

    def draw(self, context):
        layout = self.layout
        dmx = context.scene.dmx
        layout.prop(context.scene.dmx,'background_color',text='')

class DMX_PT_Setup_Volume(Panel):
    bl_label = "Volume"
    bl_idname = "dmx.panel.setup.volume"
    bl_parent_id = "dmx.panel.setup"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(self,context):
        return context.object is not None

    def draw(self, context):
        layout = self.layout
        dmx = context.scene.dmx

        layout.prop(context.scene.dmx, 'volume_preview')

        layout.operator("dmx.create_volume", text = ('Update Volume Box' if dmx.volume else 'Create Volume Box'), icon='MESH_CUBE')

        row = layout.row()
        row.prop(context.scene.dmx, 'volume_enabled')
        row.enabled = (dmx.volume != None)

        row = layout.row()
        row.prop(context.scene.dmx, 'volume_density')
        row.enabled = (dmx.volume != None)

# Panel #

class DMX_PT_Setup(Panel):
    bl_label = "Setup"
    bl_idname = "dmx.panel.setup"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"

    @classmethod
    def poll(self,context):
        return context.object is not None

    def draw(self, context):
        layout = self.layout
        dmx = context.scene.dmx
        if (not dmx.collection): layout.operator("dmx.new_show", text="Create New Show", icon="LIGHT")
