#
#   BlendexDMX > Utilities
#   General utility functions
#
#   http://www.github.com/open-stage/BlenderDMX
#

import bpy
import bmesh

# <get Scene Rect>
# Calculate the minimum and maximum coordinate of the scene objects

def get_scene_rect():
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

def rgb_to_cmy(rgb):
    if (rgb) == [0,0,0]:
        return [255,255,255]

    c = 1 - rgb[0] / 255
    m = 1 - rgb[1] / 255
    y = 1 - rgb[2] / 255

    min_cmy = min(c, m, y)
    if min_cmy == 1:
        return [0,0,0]

    c = (c - min_cmy) / (1 - min_cmy)
    m = (m - min_cmy) / (1 - min_cmy)
    y = (y - min_cmy) / (1 - min_cmy)

    return [int(c * 255), int(m * 255), int(y * 255)]

def cmy_to_rgb(cmy):
    rgb=[0,0,0]
    rgb[0] = int(255 * (1.0 - cmy[0] / 255))
    rgb[1] = int(255 * (1.0 - cmy[1] / 255))
    rgb[2] = int(255 * (1.0 - cmy[2] / 255))
    return rgb

def sanitize_obj_name(name):
    return name.replace(" ", "_")
