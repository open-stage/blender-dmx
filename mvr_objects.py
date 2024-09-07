#    Copyright vanous
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
import uuid

from bpy.props import PointerProperty, StringProperty, BoolProperty

from bpy.types import PropertyGroup, Collection


class DMX_MVR_Object(PropertyGroup):
    """Universal MVR object... in the future, make this specific
    SceneObject, Truss, Layer..."""

    name: StringProperty(
        name = "Name",
        description = "Name",
        default = ""
            )

    collection: PointerProperty(
        name = "Collection of objects",
        type = Collection)

    uuid: StringProperty(
        name = "UUID",
        description = "UUID",
        default = str(uuid.uuid4())
            )

    object_type: StringProperty(
        name = "Object type",
        description = "Simple object classification",
        default = "SceneObject" #Layer, Truss,
            )
    classing: StringProperty(
        name = "Classing",
        description = "Grouping/Layering",
        default = ""
            )

class DMX_MVR_Class(PropertyGroup):

    name: StringProperty(
        name = "Name",
        description = "Name",
        default = ""
            )

    uuid: StringProperty(
            name="UUID",
            description="Unique ID, used for MVR",
            default="")

    def onEnable(self, context):
        enabled = self.enabled
        for obj in bpy.context.scene.objects:
            if obj.get("classing", None) == self.uuid:
                obj.hide_set(not enabled)
                obj.hide_viewport = not enabled
                obj.hide_render = not enabled
        for fixture in bpy.context.scene.dmx.fixtures:
            if fixture.classing == self.uuid:
                #fixture.collection.hide_set(not enabled)
                fixture.collection.hide_viewport = not enabled
                fixture.collection.hide_render = not enabled

    enabled: BoolProperty(
            name = "Enabled",
            default = True,
            update = onEnable
            )
