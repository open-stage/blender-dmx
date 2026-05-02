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
import time

import bpy
import blf

_status_overlay_handler = None
_status_overlay_hide_timer_registered = False
_status_overlay_state = {
    "visible": False,
    "title": "MVR Import",
    "message": "",
    "hint": "",
    "progress": None,
    "status": "info",
    "hide_at": None,
    "bounds": None,
}

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


def _tag_view3d_redraw():
    screen = getattr(bpy.context, "screen", None)
    if screen is None:
        return
    for area in screen.areas:
        if area.type == "VIEW_3D":
            area.tag_redraw()


def force_view3d_redraw():
    _tag_view3d_redraw()
    try:
        bpy.ops.wm.redraw_timer(type="DRAW_WIN_SWAP", iterations=1)
    except RuntimeError:
        pass


def _status_overlay_draw():
    state = _status_overlay_state
    if not state["visible"]:
        return

    font_id = 0
    region = bpy.context.region
    if region is None:
        return

    x = 24
    y = 72
    progress = state["progress"]
    title = state["title"]
    if progress is None:
        headline = title
    else:
        headline = f"{title}: {int(progress * 100)}%"
    hint = state["hint"]

    color_map = {
        "running": (1.0, 0.75, 0.2, 1.0),
        "complete": (0.45, 1.0, 0.45, 1.0),
        "cancelled": (1.0, 0.45, 0.45, 1.0),
        "error": (1.0, 0.35, 0.35, 1.0),
        "info": (1.0, 1.0, 1.0, 1.0),
    }
    headline_color = color_map.get(state["status"], color_map["info"])

    blf.size(font_id, 18)
    blf.color(font_id, *headline_color)
    blf.position(font_id, x, y, 0)
    blf.draw(font_id, headline)
    headline_width, headline_height = blf.dimensions(font_id, headline)

    message = state["message"]
    message_width = 0.0
    if message:
        blf.size(font_id, 13)
        blf.color(font_id, 0.92, 0.92, 0.92, 1.0)
        blf.position(font_id, x, y - 20, 0)
        blf.draw(font_id, message)
        message_width, _ = blf.dimensions(font_id, message)

    hint_width = 0.0
    if hint:
        blf.size(font_id, 11)
        blf.color(font_id, 0.7, 0.7, 0.7, 1.0)
        blf.position(font_id, x, y - 38, 0)
        blf.draw(font_id, hint)
        hint_width, _ = blf.dimensions(font_id, hint)

    state["bounds"] = {
        "x": x - 8,
        "y": y - 48,
        "width": max(headline_width, message_width, hint_width) + 16,
        "height": 60,
    }


def _status_overlay_hide_timer():
    global _status_overlay_hide_timer_registered

    hide_at = _status_overlay_state["hide_at"]
    if (
        not _status_overlay_state["visible"]
        or hide_at is None
        or time.monotonic() >= hide_at
    ):
        clear_status_overlay()
        _status_overlay_hide_timer_registered = False
        return None
    return 0.25


def ensure_status_overlay():
    global _status_overlay_handler
    if _status_overlay_handler is None:
        _status_overlay_handler = bpy.types.SpaceView3D.draw_handler_add(
            _status_overlay_draw, (), "WINDOW", "POST_PIXEL"
        )


def show_status_overlay(
    message="",
    *,
    progress=None,
    status="running",
    title="MVR Import In Progress!",
    hint="",
    auto_hide_after=None,
):
    global _status_overlay_hide_timer_registered

    ensure_status_overlay()
    _status_overlay_state["visible"] = True
    _status_overlay_state["title"] = title
    _status_overlay_state["message"] = message
    _status_overlay_state["hint"] = hint
    _status_overlay_state["progress"] = progress
    _status_overlay_state["status"] = status
    _status_overlay_state["hide_at"] = (
        time.monotonic() + auto_hide_after if auto_hide_after else None
    )
    _tag_view3d_redraw()

    if auto_hide_after and not _status_overlay_hide_timer_registered:
        bpy.app.timers.register(_status_overlay_hide_timer)
        _status_overlay_hide_timer_registered = True


def clear_status_overlay():
    _status_overlay_state["visible"] = False
    _status_overlay_state["message"] = ""
    _status_overlay_state["hint"] = ""
    _status_overlay_state["progress"] = None
    _status_overlay_state["status"] = "info"
    _status_overlay_state["hide_at"] = None
    _status_overlay_state["bounds"] = None
    _tag_view3d_redraw()


def is_status_overlay_visible():
    return _status_overlay_state["visible"]


def is_status_overlay_dismissible():
    return _status_overlay_state["visible"] and _status_overlay_state["status"] in {
        "complete",
        "cancelled",
        "error",
    }


def status_overlay_contains_window_point(window_x, window_y):
    bounds = _status_overlay_state.get("bounds")
    if not bounds:
        return False

    screen = getattr(bpy.context, "screen", None)
    if screen is None:
        return False

    for area in screen.areas:
        if area.type != "VIEW_3D":
            continue
        for region in area.regions:
            if region.type != "WINDOW":
                continue
            region_x0 = region.x
            region_y0 = region.y
            region_x1 = region_x0 + region.width
            region_y1 = region_y0 + region.height
            if not (
                region_x0 <= window_x <= region_x1
                and region_y0 <= window_y <= region_y1
            ):
                continue

            region_x = window_x - region_x0
            region_y = window_y - region_y0
            return (
                bounds["x"] <= region_x <= bounds["x"] + bounds["width"]
                and bounds["y"] <= region_y <= bounds["y"] + bounds["height"]
            )
    return False


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


def generate_fixture_name(name):
    dmx = bpy.context.scene.dmx
    new_id = 1
    while True:
        new_name = f"{name} {new_id:>04}"
        if new_name in dmx.fixtures:
            new_id += 1
        else:
            break
    return new_name


def sizeof_fmt(num, suffix="B"):
    for unit in ("", "K", "M", "G", "T", "P", "E", "Z"):
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"


def one_float_to_u16(f: float) -> int:
    f = max(-1.0, min(1.0, f))
    return int((f * 0.5 + 0.5) * 65535 + 0.5)
