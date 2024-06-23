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


import uuid

from bpy.props import PointerProperty, StringProperty

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

