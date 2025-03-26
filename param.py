#    Copyright Hugo Aboud
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


from bpy.props import FloatProperty, IntProperty
from bpy.types import PropertyGroup


class DMX_Param(PropertyGroup):
    index: IntProperty(name="DMX: DMX Parameter Index", min=1, max=512)
    value: FloatProperty(name="DMX: DMX Parameter Value", default=1, min=0, max=1)
    default: FloatProperty(
        name="DMX: DMX Parameter Default Value", default=1, min=0, max=1
    )

    def toDefault(self):
        self.value = self.default


class DMX_Model_Param(PropertyGroup):
    value: FloatProperty(name="DMX: Model Parameter", default=0)
