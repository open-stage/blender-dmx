# Copyright (C) 2020 Hugo Aboud, Kaspars Jaudzems, vanous
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

import bpy

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


def sanitize_obj_name(geometry):
    name = geometry.name.replace(" ", "_")
    root_name = ""
    if hasattr(geometry, "reference_root"):
        root_name = f"{geometry.reference_root.replace(' ', '_')}_"
    return f"{root_name}{name}"


def ShowMessageBox(message="", title="Message Box", icon="INFO"):
    def draw(self, context):
        lines = split_text_on_spaces(message, 30)
        for line in lines:
            self.layout.label(text=line)

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)


def draw_top_message(self, context):
    self.layout.label(text="READ Important Message in BlenderDMX Setup Panel!")


def split_text_on_spaces(text, max_line_length):
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        if len(current_line) + len(word) + 1 <= max_line_length:
            if current_line:
                current_line += " "
            current_line += word
        else:
            lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return lines


def create_unique_fixture_name(name):
    dmx = bpy.context.scene.dmx
    while True:
        if name in dmx.fixtures:
            rand = random.randint(1000, 9999)
            name = f"{name}-{rand}"
        else:
            return name


def sizeof_fmt(num, suffix="B"):
    for unit in ("", "K", "M", "G", "T", "P", "E", "Z"):
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"
