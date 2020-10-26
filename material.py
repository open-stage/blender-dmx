#
#   BlendexDMX > Material
#   Methods to create special materials (such as the default light emitter)
#
#   http://www.github.com/hugoaboud/BlenderDMX
#

import bpy
import bmesh

# <get Emitter Material>
#   Create an emissive material with given name, remove if already present
def getEmitterMaterial(name):
    if (name in bpy.data.materials):
        bpy.data.materials.remove(bpy.data.materials[name])
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    material.node_tree.nodes.remove(material.node_tree.nodes['Principled BSDF'])
    material.node_tree.nodes.new("ShaderNodeEmission")
    material.node_tree.links.new(material.node_tree.nodes['Material Output'].inputs[0], material.node_tree.nodes['Emission'].outputs[0])
    return material

# <get Volume Scatter Material>
#
def getVolumeScatterMaterial():
    if ("DMX_Volume" in bpy.data.materials):
        return bpy.data.materials["DMX_Volume"]

    material = bpy.data.materials.new("DMX_Volume")
    material.use_nodes = True
    material.node_tree.nodes.remove(material.node_tree.nodes['Principled BSDF'])
    material.node_tree.nodes.new("ShaderNodeVolumeScatter")
    material.node_tree.links.new(material.node_tree.nodes['Material Output'].inputs[1], material.node_tree.nodes['Volume Scatter'].outputs[0])
    return material
