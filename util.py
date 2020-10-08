#
#   BlendexDMX > Utilities
#   General utility functions
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
    material.node_tree.nodes.remove(material.node_tree.nodes[1])
    material.node_tree.nodes.new("ShaderNodeEmission")
    material.node_tree.links.new(material.node_tree.nodes[0].inputs[0], material.node_tree.nodes[1].outputs[0])
    return material

# <get Body Material>
#   Create a diffuse material with dark gray color if it doesn't exist
# and return it

def getBodyMaterial():
    if ('FixtureBody' not in bpy.data.materials):
        material = bpy.data.materials.new("FixtureBody")
        material.diffuse_color = (0.1,0.1,0.1,1.0)
    else:
        material = bpy.data.materials['FixtureBody']
    return material

# <get Surface Material>
#   Create a diffuse material with less darker gray color if it doesn't exist
# and return it

def getSurfaceMaterial():
    if ('FixtureSurface' not in bpy.data.materials):
        material = bpy.data.materials.new("FixtureSurface")
        material.diffuse_color = (0.2,0.2,0.2,1.0)
    else:
        material = bpy.data.materials['FixtureSurface']
    return material



# <get Scene Rect>
# Calculate the minimum and maximum coordinate of the scene objects

def getSceneRect():
    min = [float("inf"),float("inf"),float("inf")]
    max = [-float("inf"),-float("inf"),-float("inf")]

    for obj in bpy.context.scene.objects:
        if (obj.data and hasattr(obj.data, 'vertices')):
            for vertex in obj.data.vertices:
                vtx = obj.matrix_world @ vertex.co
                for i in range(3):
                    if (vtx[i] < min[i]): min[i] = vtx[i]
                    if (vtx[i] > max[i]): max[i] = vtx[i]
        else:
            for i in range(3):
                if (obj.location[i] < min[i]): min[i] = obj.location[i]
                if (obj.location[i] > max[i]): max[i] = obj.location[i]

    return (min, max)
