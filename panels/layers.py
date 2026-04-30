# Copyright (C) 2026 vanous
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

import uuid as py_uuid

import bpy
from bpy.props import StringProperty
from bpy.types import Operator, Panel, UIList

from ..i18n import DMX_Lang

_ = DMX_Lang._


def _active_layer(dmx):
    if 0 <= dmx.mvr_layer_list_i < len(dmx.mvr_layers):
        return dmx.mvr_layers[dmx.mvr_layer_list_i]
    return None


def _layer_matches(item, uuid_value, name):
    if uuid_value and item.uuid == uuid_value:
        return True
    if not uuid_value and name and item.name == name:
        return True
    return False


def _selected_fixture_objects(dmx):
    fixture_objects = set()
    for fixture in dmx.fixtures:
        if not getattr(fixture, "collection", None):
            continue
        for obj in getattr(fixture.collection, "objects", []):
            fixture_objects.add(obj)
    return fixture_objects


def _mvr_layer_collections(dmx):
    collections = []
    for layer in dmx.mvr_layers:
        if layer.collection is not None:
            collections.append(layer.collection)
    return collections


def _fixture_members(layer_item, dmx):
    fixtures = []
    for fixture in dmx.fixtures:
        if _layer_matches(
            layer_item,
            fixture.get("layer_uuid", None),
            fixture.get("layer_name", ""),
        ):
            fixtures.append(fixture)
    return fixtures


def _object_members(layer_item, dmx):
    return [obj.name for obj in _object_member_objects(layer_item, dmx)]


def _object_member_objects(layer_item, dmx):
    fixture_objects = _selected_fixture_objects(dmx)
    seen_keys = set()
    members = []

    def add_member(obj):
        obj_uuid = obj.get("UUID", None)
        if obj_uuid:
            member_key = ("uuid", obj_uuid, obj.name)
        else:
            member_key = ("object", obj.as_pointer())
        if member_key in seen_keys:
            return
        seen_keys.add(member_key)
        members.append(obj)

    if layer_item.collection is not None:
        for child in layer_item.collection.children:
            child_class = child.get("MVR Class")
            if child_class in {
                "SceneObject",
                "Truss",
                "Support",
                "Projector",
                "VideoScreen",
                "GroupObject",
            }:
                for obj in child.all_objects:
                    if obj in fixture_objects:
                        continue
                    add_member(obj)
        for obj in layer_item.collection.all_objects:
            if obj in fixture_objects:
                continue
            if obj.type not in {"MESH", "EMPTY"}:
                continue
            add_member(obj)

    for obj in bpy.context.scene.objects:
        if obj in fixture_objects:
            continue
        if not _layer_matches(
            layer_item,
            obj.get("layer_uuid", None),
            obj.get("layer_name", ""),
        ):
            continue
        add_member(obj)

    return members


class DMX_UL_MVR_Layer(UIList):
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        dmx = context.scene.dmx
        fixtures = _fixture_members(item, dmx)
        objects = _object_members(item, dmx)
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            row = layout.row(align=True)
            row.label(text=item.name or _("Layer"))
            row.label(text=f"F:{len(fixtures)} O:{len(objects)}")
            row.prop(item, "enabled", text="")
        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.label(text="")


class DMX_OT_MVR_Layer_Create(Operator):
    bl_label = _("Create Layer")
    bl_idname = "dmx.create_mvr_layer"
    bl_description = _("Create MVR layer")
    bl_options = {"UNDO"}

    name: StringProperty(
        name=_("Name"), description=_("MVR Layer Name"), default="Layer"
    )

    def draw(self, context):
        self.layout.prop(self, "name")

    def execute(self, context):
        dmx = context.scene.dmx
        if dmx.find_mvr_layer_by_name(self.name):
            return {"CANCELLED"}
        collection = bpy.data.collections.new(self.name)
        context.scene.collection.children.link(collection)
        layer = dmx.ensure_mvr_layer(self.name, str(py_uuid.uuid4()), collection)
        dmx.mvr_layer_list_i = max(0, len(dmx.mvr_layers) - 1)
        layer.collection = collection
        return {"FINISHED"}

    def invoke(self, context, event):
        self.name = f"Layer {len(context.scene.dmx.mvr_layers) + 1}"
        return context.window_manager.invoke_props_dialog(self)


class DMX_OT_MVR_Layer_Remove(Operator):
    bl_label = _("Remove Layer")
    bl_idname = "dmx.remove_mvr_layer"
    bl_description = _("Remove selected MVR layer")
    bl_options = {"UNDO"}

    def execute(self, context):
        dmx = context.scene.dmx
        layer = _active_layer(dmx)
        if layer is None:
            return {"CANCELLED"}

        layer_uuid = layer.uuid
        layer_name = layer.name
        collection = layer.collection

        for fixture in dmx.fixtures:
            if _layer_matches(
                layer,
                fixture.get("layer_uuid", None),
                fixture.get("layer_name", ""),
            ):
                fixture["layer_name"] = None
                fixture["layer_uuid"] = None

        for obj in context.scene.objects:
            if _layer_matches(
                layer, obj.get("layer_uuid", None), obj.get("layer_name", "")
            ):
                obj["layer_name"] = None
                obj["layer_uuid"] = None

        if collection is not None:
            if collection.get("MVR Class") == "Layer":
                del collection["MVR Class"]
            if collection.get("MVR Name") == layer_name:
                del collection["MVR Name"]

        dmx.mvr_layers.remove(dmx.mvr_layer_list_i)
        dmx.mvr_layer_list_i = min(dmx.mvr_layer_list_i, len(dmx.mvr_layers) - 1)
        return {"FINISHED"}


class DMX_OT_MVR_Layer_Rename(Operator):
    bl_label = _("Rename Layer")
    bl_idname = "dmx.rename_mvr_layer"
    bl_description = _("Rename selected MVR layer")
    bl_options = {"UNDO"}

    name: StringProperty(
        name=_("Name"), description=_("MVR Layer Name"), default="Layer"
    )

    def draw(self, context):
        self.layout.prop(self, "name")

    def execute(self, context):
        dmx = context.scene.dmx
        layer = _active_layer(dmx)
        if layer is None or not self.name:
            return {"CANCELLED"}

        old_name = layer.name
        layer.name = self.name
        if layer.collection is not None:
            layer.collection.name = self.name
            layer.collection["MVR Class"] = "Layer"
            layer.collection["MVR Name"] = self.name
            if not layer.collection.get("UUID"):
                layer.collection["UUID"] = layer.uuid

        for fixture in dmx.fixtures:
            if _layer_matches(layer, fixture.get("layer_uuid", None), old_name):
                fixture["layer_name"] = self.name
                if not fixture.get("layer_uuid", None):
                    fixture["layer_uuid"] = layer.uuid

        for obj in context.scene.objects:
            if _layer_matches(layer, obj.get("layer_uuid", None), old_name):
                obj["layer_name"] = self.name
                if not obj.get("layer_uuid", None):
                    obj["layer_uuid"] = layer.uuid

        return {"FINISHED"}

    def invoke(self, context, event):
        layer = _active_layer(context.scene.dmx)
        if layer is None:
            return {"CANCELLED"}
        self.name = layer.name
        return context.window_manager.invoke_props_dialog(self)


class DMX_OT_MVR_Layer_Select(Operator):
    bl_label = _("Select Layer")
    bl_idname = "dmx.select_mvr_layer_members"
    bl_description = _("Select fixtures and objects in the selected MVR layer")
    bl_options = {"UNDO"}

    def execute(self, context):
        dmx = context.scene.dmx
        layer = _active_layer(dmx)
        if layer is None:
            return {"CANCELLED"}

        bpy.ops.object.select_all(action="DESELECT")

        for fixture in _fixture_members(layer, dmx):
            fixture.select()

        object_members = _object_member_objects(layer, dmx)
        for obj in object_members:
            try:
                obj.select_set(True)
            except RuntimeError:
                continue

        if object_members:
            context.view_layer.objects.active = object_members[0]

        return {"FINISHED"}


class DMX_OT_MVR_Layer_Assign_Selected(Operator):
    bl_label = _("Assign Selected")
    bl_idname = "dmx.assign_selected_to_mvr_layer"
    bl_description = _("Assign selected fixtures and objects to the selected MVR layer")
    bl_options = {"UNDO"}

    def execute(self, context):
        dmx = context.scene.dmx
        layer = _active_layer(dmx)
        if layer is None:
            return {"CANCELLED"}

        layer_collection = layer.collection
        fixture_objects = _selected_fixture_objects(dmx)
        mvr_layer_collections = _mvr_layer_collections(dmx)

        for fixture in dmx.fixtures:
            if fixture.is_selected():
                fixture["layer_name"] = layer.name
                fixture["layer_uuid"] = layer.uuid

        for obj in context.selected_objects:
            if obj in fixture_objects:
                continue
            obj["layer_name"] = layer.name
            obj["layer_uuid"] = layer.uuid
            if layer_collection is not None and not any(
                existing == obj for existing in layer_collection.objects
            ):
                layer_collection.objects.link(obj)
            for old_layer_collection in mvr_layer_collections:
                if old_layer_collection == layer_collection:
                    continue
                if any(existing == obj for existing in old_layer_collection.objects):
                    old_layer_collection.objects.unlink(obj)

        return {"FINISHED"}


class DMX_OT_MVR_Layer_Unassign_Selected(Operator):
    bl_label = _("Unassign Selected")
    bl_idname = "dmx.unassign_selected_from_mvr_layer"
    bl_description = _(
        "Remove selected fixtures and objects from the selected MVR layer"
    )
    bl_options = {"UNDO"}

    def execute(self, context):
        dmx = context.scene.dmx
        layer = _active_layer(dmx)
        if layer is None:
            return {"CANCELLED"}

        layer_collection = layer.collection
        fixture_objects = _selected_fixture_objects(dmx)

        for fixture in dmx.fixtures:
            if fixture.is_selected() and _layer_matches(
                layer,
                fixture.get("layer_uuid", None),
                fixture.get("layer_name", ""),
            ):
                fixture["layer_name"] = None
                fixture["layer_uuid"] = None

        for obj in context.selected_objects:
            if obj in fixture_objects:
                continue
            if _layer_matches(
                layer, obj.get("layer_uuid", None), obj.get("layer_name", "")
            ):
                obj["layer_name"] = None
                obj["layer_uuid"] = None
            if layer_collection is not None and any(
                existing == obj for existing in layer_collection.objects
            ):
                if len(obj.users_collection) == 1:
                    context.scene.collection.objects.link(obj)
                layer_collection.objects.unlink(obj)

        return {"FINISHED"}


class DMX_PT_MVR_Layers(Panel):
    bl_label = _("Layers")
    bl_idname = "DMX_PT_MVR_Layers"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        dmx = context.scene.dmx

        row = layout.row()
        row.template_list(
            "DMX_UL_MVR_Layer",
            "",
            dmx,
            "mvr_layers",
            dmx,
            "mvr_layer_list_i",
            rows=4,
        )

        col = row.column(align=True)
        col.operator("dmx.create_mvr_layer", text="", icon="ADD")
        col.operator("dmx.remove_mvr_layer", text="", icon="REMOVE")
        col.operator("dmx.rename_mvr_layer", text="", icon="SYNTAX_OFF")
        col.operator(
            "dmx.select_mvr_layer_members", text="", icon="RESTRICT_SELECT_OFF"
        )

        layer = _active_layer(dmx)
        if layer is None:
            return
        row = layout.row()
        row.operator("dmx.assign_selected_to_mvr_layer", icon="ADD")
        row.operator("dmx.unassign_selected_from_mvr_layer", icon="REMOVE")
