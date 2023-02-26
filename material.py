#
#   BlendexDMX > Material
#   Methods to create special materials (such as the default light emitter)
#
#   http://www.github.com/hugoaboud/BlenderDMX
#

import bpy
import bmesh
from dmx.logging import DMX_Log
import logging

# Shader Nodes default labels
# Blender API naming convention is inconsistent for internationalization
# Every label used is listed here, so it's easier to fix it on new API updates
PRINCIPLED_BSDF = "Principled BSDF"
MATERIAL_OUTPUT = "Material Output"
SHADER_NODE_EMISSION = "ShaderNodeEmission"
SHADER_NODE_VOLUMESCATTER = "ShaderNodeVolumeScatter"
VOLUME_SCATTER = bpy.app.translations.pgettext("Volume Scatter")
EMISSION = bpy.app.translations.pgettext("Emission")

# <get Emitter Material>
#   Create an emissive material with given name, remove if already present
def getEmitterMaterial(name):
    if (name in bpy.data.materials):
        bpy.data.materials.remove(bpy.data.materials[name])
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    # BUG: Internationalization
    if PRINCIPLED_BSDF in material.node_tree.nodes:
        material.node_tree.nodes.remove(material.node_tree.nodes[PRINCIPLED_BSDF])
    else:
        DMX_Log.log.error("""BSDF material could not be removed when adding new Emitter,
                         this could cause issues. Set Logging level to Info to get more details.""")
        if DMX_Log.log.isEnabledFor(logging.INFO):
            print("Nodes in material tree nodes:")
            for node in material.node_tree.nodes:
                print(node)
    material.node_tree.nodes.new(SHADER_NODE_EMISSION)
    material.node_tree.links.new(material.node_tree.nodes[MATERIAL_OUTPUT].inputs[0], material.node_tree.nodes[EMISSION].outputs[0])
    return material

# <get Volume Scatter Material>
#
def getVolumeScatterMaterial():
    if ("DMX_Volume" in bpy.data.materials):
        return bpy.data.materials["DMX_Volume"]

    material = bpy.data.materials.new("DMX_Volume")
    material.use_nodes = True
    # BUG: Internationalization
    if PRINCIPLED_BSDF in material.node_tree.nodes:
        material.node_tree.nodes.remove(material.node_tree.nodes[PRINCIPLED_BSDF])
    else:
        DMX_Log.log.error("""BSDF material could not be removed when adding creating Volume,
                       this could cause issues. Set Logging level to Info to get more details.""")
        if DMX_Log.log.isEnabledFor(logging.INFO):
            print("Nodes in material tree nodes:")
            for node in material.node_tree.nodes:
                print(node)

    material.node_tree.nodes.remove(material.node_tree.nodes[PRINCIPLED_BSDF])
    material.node_tree.nodes.new(SHADER_NODE_VOLUMESCATTER)
    material.node_tree.links.new(material.node_tree.nodes[MATERIAL_OUTPUT].inputs[1], material.node_tree.nodes[VOLUME_SCATTER].outputs[0])
    return material
