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
from bpy.types import Operator, Panel
from dmx.material import getVolumeScatterMaterial
from dmx.util import getSceneRect
import dmx.version as version
from dmx import bl_info as application_info

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
        row.prop(context.window_manager.dmx, 'pause_render')
        row = layout.row()
        row.prop(context.scene.dmx,'display_2D')
        row = layout.row()
        row.prop(context.scene.dmx,'display_pigtails')
        row = layout.row()
        row.prop(context.scene.dmx,'select_geometries')
        row = layout.row()
        row.prop(context.scene.dmx, 'logging_level')
        row = layout.row()
        layout.operator("dmx.check_version", text="Check for BlenderDMX updates")
        row = layout.row()
        row.label(text = f"Status: {context.window_manager.dmx.release_version_status}")

class DMX_PT_Setup_Experimental(Panel):
    bl_label = "Experimental"
    bl_idname = "DMX_PT_Setup_Experimental"
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
        row.prop(dmx, 'gobo_support')

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

class DMX_OT_VersionCheck(Operator):
    bl_label = "Check version"
    bl_description = "Check if there is new release of BlenderDMX"
    bl_idname = "dmx.check_version"
    bl_options = {'UNDO'}

    def callback(self, data, context):
        temp_data = context.window_manager.dmx
        text = "Unknown version error"
        if "error" in data:
            text = data["error"]
        else:
            try:
                current_version = application_info["version"]
                new_version = data["name"]
                res = version.version_compare(current_version, new_version)
            except Exception as e:
                text = f"{e.__class__.__name__} {e}"
            else:
                if res < 0:
                    text = f"New version {new_version} available"
                elif res > 0:
                    text = "You are using pre-release version"
                else:
                    text = "You are using latest version of BlenderDMX"

        self.report({"INFO"}, f"{text}")
        temp_data.release_version_status = text

    def execute(self, context):
        temp_data = context.window_manager.dmx
        temp_data.release_version_status = "Checking..."
        version.get_latest_release(self.callback, context)
        return {'FINISHED'}
