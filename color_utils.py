# Copyright (C) 2025 vanous
#
# This file is part of BlenderDMX.
#
# BlenderDMX is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# BlenderDMX is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <https://www.gnu.org/licenses/>.

import math
import random


def rgb_to_cmy(rgb):
    """
    Convert RGB to CMY.
    Input: rgb - list or tuple of 3 integers [R, G, B] in 0-255
    Output: list of 3 integers [C, M, Y] in 0-255
    """
    c = 255 - rgb[0]
    m = 255 - rgb[1]
    y = 255 - rgb[2]
    return [c, m, y]


def cmy_to_rgb(cmy):
    """
    Convert CMY to RGB.
    Input: cmy - list or tuple of 3 integers [C, M, Y] in 0-255
    Output: list of 3 integers [R, G, B] in 0-255
    """
    r = 255 - cmy[0]
    g = 255 - cmy[1]
    b = 255 - cmy[2]
    return [r, g, b]


def calculate_automatic_white(rgb):
    if rgb[0] == rgb[1] == rgb[2]:
        return rgb[0]
    min_rgb = min(rgb)
    if min_rgb == 0:
        return 0
    average_rgb = sum(rgb) / len(rgb)
    automatic_white = int(average_rgb * (1 - (min_rgb / 255)))

    return automatic_white


# https://stackoverflow.com/questions/6629798/whats-wrong-with-this-rgb-to-xyz-color-space-conversion-algorithm
# http://www.easyrgb.com/en/math.php


def is_default_x(x):
    return math.isclose(x, 0.3127, rel_tol=0.0001)


def is_default_y(y):
    return math.isclose(y, 0.3290, rel_tol=0.0001)


def is_default_Y(Y):
    return math.isclose(Y, 100.0, rel_tol=0.0001)


def xyY2rgbaa(xyY):
    """As blender needs RGBA, which we later strip anyways, we just add 100 for Alpha"""
    x = xyY.x
    y = xyY.y
    Y = xyY.Y
    if y == 0:
        return (0, 0, 0, 1)

    if is_default_x(x) and is_default_y(y) and is_default_Y(Y):
        # if color is the GDTF defined default white or very close
        return (255, 255, 255, 1)

    # Convert to XYZ
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
        var_R = 1.055 * (var_R ** (1 / 2.4)) - 0.055
    else:
        var_R = 12.92 * var_R

    if var_G > 0.0031308:
        var_G = 1.055 * (var_G ** (1 / 2.4)) - 0.055
    else:
        var_G = 12.92 * var_G

    if var_B > 0.0031308:
        var_B = 1.055 * (var_B ** (1 / 2.4)) - 0.055
    else:
        var_B = 12.92 * var_B

    R = max(0, min(1, var_R)) * 255
    G = max(0, min(1, var_G)) * 255
    B = max(0, min(1, var_B)) * 255
    return (R, G, B, 1)


def rgb2xyY(R, G, B):
    # Normalize RGB to 0-1
    r = R / 255.0
    g = G / 255.0
    b = B / 255.0

    # Inverse gamma correction (sRGB)
    def inv_gamma(c):
        if c > 0.04045:
            return ((c + 0.055) / 1.055) ** 2.4
        else:
            return c / 12.92

    r_lin = inv_gamma(r)
    g_lin = inv_gamma(g)
    b_lin = inv_gamma(b)

    # Scale linear RGB by 100 to match XYZ scale in xyY2rgbaa function
    r_lin *= 100
    g_lin *= 100
    b_lin *= 100

    # Convert linear RGB to XYZ (D65)
    X = r_lin * 0.4124 + g_lin * 0.3576 + b_lin * 0.1805
    Y = r_lin * 0.2126 + g_lin * 0.7152 + b_lin * 0.0722
    Z = r_lin * 0.0193 + g_lin * 0.1192 + b_lin * 0.9505

    denom = X + Y + Z
    if denom == 0:
        x = 0
        y = 0
    else:
        x = X / denom
        y = Y / denom
    return (x, y, Y)


def xyY2rgba(xyz):
    """Unused for now"""
    rgb = xyY2rgbaa(xyz)
    lowest = min(rgb)
    alpha = (255 - lowest) / 255
    red = (rgb[0] - lowest) / alpha
    green = (rgb[1] - lowest) / alpha
    blue = (rgb[2] - lowest) / alpha
    return (int(red), int(green), int(blue), int(alpha * 100))


# def clamp(n, small=0, large=255):
#    return max(small, min(n, large))


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

    red = max(
        amber_rgb[0],
        lime_rgb[0],
        colors[0],
        white_rgb[0],
        wwhite_rgb[0],
        cwhite_rgb[0],
        uv_rgb[0],
        cyan_rgb[0],
        magenta_rgb[0],
        yellow_rgb[0],
    )
    green = max(
        amber_rgb[1],
        lime_rgb[1],
        colors[1],
        white_rgb[1],
        wwhite_rgb[1],
        cwhite_rgb[1],
        uv_rgb[1],
        cyan_rgb[1],
        magenta_rgb[1],
        yellow_rgb[1],
    )
    blue = max(
        amber_rgb[2],
        lime_rgb[2],
        colors[2],
        white_rgb[2],
        wwhite_rgb[2],
        cwhite_rgb[2],
        uv_rgb[2],
        cyan_rgb[2],
        magenta_rgb[2],
        yellow_rgb[2],
    )

    return [red, green, blue]


# https://andi-siess.de/rgb-to-color-temperature/
kelvin_table = {
    1000: (255, 56, 0),
    1100: (255, 71, 0),
    1200: (255, 83, 0),
    1300: (255, 93, 0),
    1400: (255, 101, 0),
    1500: (255, 109, 0),
    1600: (255, 115, 0),
    1700: (255, 121, 0),
    1800: (255, 126, 0),
    1900: (255, 131, 0),
    2000: (255, 138, 18),
    2100: (255, 142, 33),
    2200: (255, 147, 44),
    2300: (255, 152, 54),
    2400: (255, 157, 63),
    2500: (255, 161, 72),
    2600: (255, 165, 79),
    2700: (255, 169, 87),
    2800: (255, 173, 94),
    2900: (255, 177, 101),
    3000: (255, 180, 107),
    3100: (255, 184, 114),
    3200: (255, 187, 120),
    3300: (255, 190, 126),
    3400: (255, 193, 132),
    3500: (255, 196, 137),
    3600: (255, 199, 143),
    3700: (255, 201, 148),
    3800: (255, 204, 153),
    3900: (255, 206, 159),
    4000: (255, 209, 163),
    4100: (255, 211, 168),
    4200: (255, 213, 173),
    4300: (255, 215, 177),
    4400: (255, 217, 182),
    4500: (255, 219, 186),
    4600: (255, 221, 190),
    4700: (255, 223, 194),
    4800: (255, 225, 198),
    4900: (255, 227, 202),
    5000: (255, 228, 206),
    5100: (255, 230, 210),
    5200: (255, 232, 213),
    5300: (255, 233, 217),
    5400: (255, 235, 220),
    5500: (255, 236, 224),
    5600: (255, 238, 227),
    5700: (255, 239, 230),
    5800: (255, 240, 233),
    5900: (255, 242, 236),
    6000: (255, 243, 239),
    6100: (255, 244, 242),
    6200: (255, 245, 245),
    6300: (255, 246, 247),
    6400: (255, 248, 251),
    6500: (255, 249, 253),
    6600: (254, 249, 255),
    6700: (252, 247, 255),
    6800: (249, 246, 255),
    6900: (247, 245, 255),
    7000: (245, 243, 255),
    7100: (243, 242, 255),
    7200: (240, 241, 255),
    7300: (239, 240, 255),
    7400: (237, 239, 255),
    7500: (235, 238, 255),
    7600: (233, 237, 255),
    7700: (231, 236, 255),
    7800: (230, 235, 255),
    7900: (228, 234, 255),
    8000: (227, 233, 255),
    8100: (225, 232, 255),
    8200: (224, 231, 255),
    8300: (222, 230, 255),
    8400: (221, 230, 255),
    8500: (220, 229, 255),
    8600: (218, 229, 255),
    8700: (217, 227, 255),
    8800: (216, 227, 255),
    8900: (215, 226, 255),
    9000: (214, 225, 255),
    9100: (212, 225, 255),
    9200: (211, 224, 255),
    9300: (210, 223, 255),
    9400: (209, 223, 255),
    9500: (208, 222, 255),
    9600: (207, 221, 255),
    9700: (207, 221, 255),
    9800: (206, 220, 255),
    9900: (205, 220, 255),
    10000: (207, 218, 255),
    10100: (207, 218, 255),
    10200: (206, 217, 255),
    10300: (205, 217, 255),
    10400: (204, 216, 255),
    10500: (204, 216, 255),
    10600: (203, 215, 255),
    10700: (202, 215, 255),
    10800: (202, 214, 255),
    10900: (201, 214, 255),
    11000: (200, 213, 255),
    11100: (200, 213, 255),
    11200: (199, 212, 255),
    11300: (198, 212, 255),
    11400: (198, 212, 255),
    11500: (197, 211, 255),
    11600: (197, 211, 255),
    11700: (197, 210, 255),
    11800: (196, 210, 255),
    11900: (195, 210, 255),
    12000: (195, 209, 255),
    12100: (194, 209, 255),
    12200: (194, 208, 255),
    12300: (193, 208, 255),
    12400: (193, 207, 255),
    12500: (192, 207, 255),
    12600: (192, 206, 255),
    12700: (191, 206, 255),
    12800: (191, 205, 255),
    12900: (190, 205, 255),
    13000: (190, 204, 255),
    13100: (189, 204, 255),
    13200: (189, 203, 255),
    13300: (188, 203, 255),
    13400: (188, 202, 255),
    13500: (187, 202, 255),
    13600: (187, 201, 255),
    13700: (186, 201, 255),
    13800: (186, 200, 255),
    13900: (185, 200, 255),
    14000: (185, 199, 255),
    14100: (184, 199, 255),
    14200: (184, 198, 255),
    14300: (183, 198, 255),
    14400: (183, 197, 255),
    14500: (182, 197, 255),
    14600: (182, 196, 255),
    14700: (181, 196, 255),
    14800: (181, 195, 255),
    14900: (180, 195, 255),
    15000: (180, 194, 255),
    15100: (179, 193, 255),
    15200: (179, 193, 255),
    15300: (178, 192, 255),
    15400: (178, 192, 255),
    15500: (177, 191, 255),
    15600: (177, 191, 255),
    15700: (176, 190, 255),
    15800: (176, 190, 255),
    15900: (175, 189, 255),
    16000: (175, 189, 255),
    16100: (174, 188, 255),
    16200: (174, 188, 255),
    16300: (173, 187, 255),
    16400: (173, 187, 255),
    16500: (172, 186, 255),
    16600: (172, 186, 255),
    16700: (171, 185, 255),
    16800: (171, 185, 255),
    16900: (170, 184, 255),
    17000: (170, 184, 255),
    17100: (169, 183, 255),
    17200: (169, 183, 255),
    17300: (168, 182, 255),
    17400: (168, 182, 255),
    17500: (167, 181, 255),
    17600: (167, 181, 255),
    17700: (166, 180, 255),
    17800: (166, 180, 255),
    17900: (165, 179, 255),
    18000: (165, 179, 255),
    18100: (164, 178, 255),
    18200: (164, 178, 255),
    18300: (163, 177, 255),
    18400: (163, 177, 255),
    18500: (162, 176, 255),
    18600: (162, 176, 255),
    18700: (161, 175, 255),
    18800: (161, 175, 255),
    18900: (160, 174, 255),
    19000: (160, 174, 255),
    19100: (159, 173, 255),
    19200: (159, 173, 255),
    19300: (158, 172, 255),
    19400: (158, 172, 255),
    19500: (157, 171, 255),
    19600: (157, 171, 255),
    19700: (156, 170, 255),
    19800: (156, 170, 255),
    19900: (155, 169, 255),
    20000: (155, 169, 255),
}


def kelvin_to_rgb(kelvin):
    kelvin = max(1000, min(20000, kelvin))

    # Calculate the RGB values using the Planckian locus formula
    # the problem is that the 4000K split makes a jump in the result

    if kelvin <= 4000:
        r = 255
        g = 99.4708025861 * pow(kelvin, -0.1332047592)
        b = 138.5177312231 * pow(kelvin, -0.0755148492)
    else:
        r = 351.97690566805693 * pow(kelvin, -0.114)
        g = 325.4494125711974 * pow(kelvin, -0.0291)
        b = 255

    # Ensure RGB values are in the range 0-255
    r = max(0, min(255, r))
    g = max(0, min(255, g))
    b = max(0, min(255, b))

    return (int(r), int(g), int(b))
