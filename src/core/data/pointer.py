import bpy
from bpy.types import ( PropertyGroup,
                        Object,
                        Material )
from bpy.props import PointerProperty

from src.i18n import DMX_i18n

class DMX_Object(PropertyGroup):
    object: PointerProperty(type = Object)

class DMX_Material(PropertyGroup):
    material: PointerProperty(type = Material)