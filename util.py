#
#   BlendexDMX > Utilities
#   General utility functions
#
#   http://www.github.com/open-stage/BlenderDMX
#

import bpy
import bmesh
import math

# <get Scene Rect>
# Calculate the minimum and maximum coordinate of the scene objects


def getSceneRect():
    min = [float("inf"), float("inf"), float("inf")]
    max = [-float("inf"), -float("inf"), -float("inf")]

    for obj in bpy.context.scene.objects:
        if obj.data and hasattr(obj.data, "vertices"):
            for vertex in obj.data.vertices:
                vtx = obj.matrix_world @ vertex.co
                for i in range(3):
                    if vtx[i] < min[i]:
                        min[i] = vtx[i]
                    if vtx[i] > max[i]:
                        max[i] = vtx[i]
        else:
            for i in range(3):
                if obj.location[i] < min[i]:
                    min[i] = obj.location[i]
                if obj.location[i] > max[i]:
                    max[i] = obj.location[i]

    return (min, max)


def rgb_to_cmy(rgb):
    if (rgb) == [0, 0, 0]:
        return [255, 255, 255]

    c = 1 - rgb[0] / 255
    m = 1 - rgb[1] / 255
    y = 1 - rgb[2] / 255

    min_cmy = min(c, m, y)
    if min_cmy == 1:
        return [0, 0, 0]

    c = (c - min_cmy) / (1 - min_cmy)
    m = (m - min_cmy) / (1 - min_cmy)
    y = (y - min_cmy) / (1 - min_cmy)

    return [int(c * 255), int(m * 255), int(y * 255)]


def cmy_to_rgb(cmy):
    rgb = [0, 0, 0]
    rgb[0] = int(255 * (1.0 - cmy[0] / 255))
    rgb[1] = int(255 * (1.0 - cmy[1] / 255))
    rgb[2] = int(255 * (1.0 - cmy[2] / 255))
    return rgb


def sanitize_obj_name(geometry):
    name = geometry.name.replace(" ", "_")
    root_name = ""
    if hasattr(geometry, "reference_root"):
        root_name = f"{geometry.reference_root.replace(' ', '_')}_"
    return f"{root_name}{name}"


# https://stackoverflow.com/questions/6629798/whats-wrong-with-this-rgb-to-xyz-color-space-conversion-algorithm
# http://www.easyrgb.com/en/math.php
def xyY2rgbaa(xyY):
    """As blender needs RGBA, which we later strip anyways, we just add 100 for Alpha"""
    x = xyY.x
    y = xyY.y
    Y = xyY.Y

    if not x or not y or not Y:
        return [0, 0, 0]

    # convert to XYZ

    X = x * (Y / y)
    Z = (1 - x - y) * (Y / y)

    var_X = X / 100
    var_Y = Y / 100
    var_Z = Z / 100

    # XYZ to RGB
    var_R = var_X * 3.2406 + var_Y * -1.5372 + var_Z * -0.4986
    var_G = var_X * -0.9689 + var_Y * 1.8758 + var_Z * 0.0415
    var_B = var_X * 0.0557 + var_Y * -0.204 + var_Z * 1.057

    if var_R > 0.0031308:
        var_R = 1.055 * math.pow(var_R, 1 / 2.4) - 0.055
    else:
        var_R = 12.92 * var_R

    if var_G > 0.0031308:
        var_G = 1.055 * math.pow(var_G, 1 / 2.4) - 0.055
    else:
        var_G = 12.92 * var_G

    if var_B > 0.0031308:
        var_B = 1.055 * math.pow(var_B, 1 / 2.4) - 0.055
    else:
        var_B = 12.92 * var_B

    return (int(var_R * 100), int(var_G * 100), int(var_B * 100), 0)


def xyY2rgba(xyz):
    """Unused for now"""
    rgb = xyY2rgb(xyz)
    lowest = min(rgb)
    alpha = (255 - lowest) / 255
    red = (rgb[0] - lowest) / alpha
    green = (rgb[1] - lowest) / alpha
    blue = (rgb[2] - lowest) / alpha
    return (int(red), int(green), int(blue), int(alpha * 100))


def ShowMessageBox(message="", title="Message Box", icon="INFO"):
    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)


def pad_number(number):
    """Pad fixture number with leading zeros,
    the amount of padding zeros depends on amount of fixtures."""
    dmx = bpy.context.scene.dmx
    padding_len = len(str(len(dmx.fixtures))) + 1
    return f"{number:>0{padding_len}}"


def clamp(n, small=0, large=255):
    return max(small, min(n, large))


def add_rgb(color1, color2):
    if all(255 == i for i in color1):
        return color2
    r = clamp(int((1 - (1 - color1[0] / 255) + (1 - color2[0] / 255))) * 255)
    g = clamp(int((1 - (1 - color1[1] / 255) + (1 - color2[1] / 255))) * 255)
    b = clamp(int((1 - (1 - color1[2] / 255) + (1 - color2[2] / 255))) * 255)
    return [r, g, b]
