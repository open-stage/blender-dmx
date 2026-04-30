# Copyright (C) 2023 vanous
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

import uuid

import bpy
from bpy.props import BoolProperty, PointerProperty, StringProperty
from bpy.types import Collection, PropertyGroup


class DMX_MVR_Object(PropertyGroup):
    """Universal MVR object... in the future, make this specific
    SceneObject, Truss, Layer..."""

    name: StringProperty(name="Name", description="Name", default="")

    collection: PointerProperty(name="Collection of objects", type=Collection)

    uuid: StringProperty(name="UUID", description="UUID", default=str(uuid.uuid4()))

    object_type: StringProperty(
        name="Object type",
        description="Simple object classification",
        default="SceneObject",  # Layer, Truss,
    )
    classing: StringProperty(
        name="Classing", description="Grouping/Layering", default=""
    )


class DMX_MVR_Class(PropertyGroup):
    name: StringProperty(name="Name", description="Name", default="")

    uuid: StringProperty(name="UUID", description="Unique ID, used for MVR", default="")

    def onEnable(self, context):
        enabled = self.enabled
        for obj in bpy.context.scene.objects:
            if obj.get("classing", None) == self.uuid:
                obj.hide_set(not enabled)
                obj.hide_viewport = not enabled
                obj.hide_render = not enabled
        for fixture in bpy.context.scene.dmx.fixtures:
            if fixture.classing == self.uuid:
                # fixture.collection.hide_set(not enabled)
                fixture.collection.hide_viewport = not enabled
                fixture.collection.hide_render = not enabled

    enabled: BoolProperty(name="Enabled", default=True, update=onEnable)


class DMX_MVR_Layer(PropertyGroup):
    name: StringProperty(name="Name", description="Name", default="")

    collection: PointerProperty(name="Collection of objects", type=Collection)

    uuid: StringProperty(name="UUID", description="Unique ID, used for MVR", default="")

    def onEnable(self, context):
        enabled = self.enabled
        scene = bpy.context.scene
        dmx = scene.dmx

        def set_object_visibility(obj):
            if obj is None:
                return
            obj.hide_set(not enabled)
            obj.hide_viewport = not enabled
            obj.hide_render = not enabled

        def set_collection_visibility(collection):
            if collection is None:
                return
            collection.hide_viewport = not enabled
            collection.hide_render = not enabled

        if self.collection is not None:
            set_collection_visibility(self.collection)
            for obj in self.collection.all_objects:
                set_object_visibility(obj)

        for fixture in dmx.fixtures:
            fixture_layer_uuid = fixture.get("layer_uuid", None)
            fixture_layer_name = fixture.get("layer_name", "")
            if (self.uuid and fixture_layer_uuid == self.uuid) or (
                not fixture_layer_uuid and fixture_layer_name == self.name
            ):
                set_collection_visibility(getattr(fixture, "collection", None))

        fixture_objects = set()
        for fixture in dmx.fixtures:
            if getattr(fixture, "collection", None) is None:
                continue
            for obj in getattr(fixture.collection, "objects", []):
                fixture_objects.add(obj)

        for obj in scene.objects:
            if obj in fixture_objects:
                continue
            obj_layer_uuid = obj.get("layer_uuid", None)
            obj_layer_name = obj.get("layer_name", "")
            if (self.uuid and obj_layer_uuid == self.uuid) or (
                not obj_layer_uuid and obj_layer_name == self.name
            ):
                set_object_visibility(obj)

    enabled: BoolProperty(name="Enabled", default=True, update=onEnable)
