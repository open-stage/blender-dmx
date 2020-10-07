#
#   BlendexDMX > Param
#   A DMX parameter (Dimmer, Color, etc)
#
#   http://www.github.com/hugoaboud/BlenderDMX
#

import bpy

from bpy.props import FloatProperty
from bpy.types import PropertyGroup

class DMX_Param(PropertyGroup):
    value: FloatProperty(
        name = "DMX: DMX Parameter",
        default = 0,
        min = 0,
        max = 1
    )

class DMX_Model_Param(PropertyGroup):
    value: FloatProperty(
        name = "DMX: Model Parameter",
        default = 0
    )
