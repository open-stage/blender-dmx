#    Copyright Hugo Aboud, vanous
#
#    This file is part of BlenderDMX.
#
#    BlenderDMX is free software: you can redistribute it and/or modify it
#    under the terms of the GNU General Public License as published by the Free
#    Software Foundation, either version 3 of the License, or (at your option)
#    any later version.
#
#    BlenderDMX is distributed in the hope that it will be useful, but WITHOUT
#    ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
#    FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
#    more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program. If not, see <https://www.gnu.org/licenses/>.


import bpy
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


def flatten_color(colors):
    """Remove precision to prevent color picker drifting"""
    color_list = []
    for color in colors:
        color_list.append(round(1 / 256 * color, 2))
    return color_list


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
        return (0, 0, 0, 0)

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

def rgb2xyY(sR, sG, sB):
    # Convert RGB values to the 0-1 range
    var_R = sR / 255
    var_G = sG / 255
    var_B = sB / 255

    # Apply the gamma correction
    if var_R > 0.04045:
        var_R = ((var_R + 0.055) / 1.055) ** 2.4
    else:
        var_R = var_R / 12.92

    if var_G > 0.04045:
        var_G = ((var_G + 0.055) / 1.055) ** 2.4
    else:
        var_G = var_G / 12.92

    if var_B > 0.04045:
        var_B = ((var_B + 0.055) / 1.055) ** 2.4
    else:
        var_B = var_B / 12.92

    # Convert to the 0-100 range
    var_R = var_R * 100
    var_G = var_G * 100
    var_B = var_B * 100

    # Convert to XYZ color space
    X = var_R * 0.4124 + var_G * 0.3576 + var_B * 0.1805
    Y = var_R * 0.2126 + var_G * 0.7152 + var_B * 0.0722
    Z = var_R * 0.0193 + var_G * 0.1192 + var_B * 0.9505

    # convert to xyY
    Y = Y
    x = X / ( X + Y + Z )
    y = Y / ( X + Y + Z )
    return x, y, Y

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


def clamp(n, small=0, large=255):
    return max(small, min(n, large))


def add_rgb(color1, color2):
    if all(255 == i for i in color1):
        return color2
    if all(255 == i for i in color2):
        return color1
    r = max(color1[0], color2[0])
    g = max(color1[1], color2[1])
    b = max(color1[2], color2[2])
    return [r, g, b]


def color_to_rgb(base_color, colors, index):
    if colors[index] is None:
        return [0, 0, 0]
    else:
        color_float = colors[index] / 255.0
        return [int(c * color_float) for c in base_color]


def colors_to_rgb(colors):
    # 0  1  2    3     4   5     6     7     8    9     10      11
    # R, G, B, White, WW, CW, Amber, Lime, UV, Cyan, Magenta, Yellow
    # color definitions below, these have been tuned to look OK in Blender

    white_rgb = color_to_rgb([128, 128, 128], colors, 3)
    wwhite_rgb = color_to_rgb([253, 244, 220], colors, 4)
    cwhite_rgb = color_to_rgb([227, 228, 237], colors, 5)
    amber_rgb = color_to_rgb([255, 68, 0], colors, 6)
    lime_rgb = color_to_rgb([68, 255, 0], colors, 7)
    uv_rgb = color_to_rgb([5, 0, 255], colors, 8)
    cyan_rgb = color_to_rgb([0, 255, 255], colors, 9)
    magenta_rgb = color_to_rgb([255, 0, 255], colors, 10)
    yellow_rgb = color_to_rgb([255, 255, 0], colors, 11)

    red = max(amber_rgb[0], lime_rgb[0], colors[0], white_rgb[0], wwhite_rgb[0], cwhite_rgb[0], uv_rgb[0], cyan_rgb[0], magenta_rgb[0], yellow_rgb[0])
    green = max(amber_rgb[1], lime_rgb[1], colors[1], white_rgb[1], wwhite_rgb[1], cwhite_rgb[1], uv_rgb[1], cyan_rgb[1], magenta_rgb[1], yellow_rgb[1])
    blue = max(amber_rgb[2], lime_rgb[2], colors[2], white_rgb[2], wwhite_rgb[2], cwhite_rgb[2], uv_rgb[2], cyan_rgb[2], magenta_rgb[2], yellow_rgb[2])

    return [red, green, blue]
