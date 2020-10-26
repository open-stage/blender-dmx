#
#   BlendexDMX > Param
#   A DMX parameter (Dimmer, Color, etc)
#
#   http://www.github.com/hugoaboud/BlenderDMX
#

import bpy

from bpy.props import (FloatProperty,
                       IntProperty)

from bpy.types import PropertyGroup

class DMX_Param(PropertyGroup):
    index: IntProperty(
        name = "DMX: DMX Parameter Index",
        min = 1,
        max = 512
    )
    value: FloatProperty(
        name = "DMX: DMX Parameter Value",
        default = 1,
        min = 0,
        max = 1
    )
    default: FloatProperty(
        name = "DMX: DMX Parameter Default Value",
        default = 1,
        min = 0,
        max = 1
    )
    def toDefault(self):
        self.value = self.default


class DMX_Model_Param(PropertyGroup):
    value: FloatProperty(
        name = "DMX: Model Parameter",
        default = 0
    )
