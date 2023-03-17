import bpy
from bpy.types import ( PropertyGroup,
                        Object )
from bpy.props import PointerProperty

class DMX_Object(PropertyGroup):
    '''
    A pointer to a Blender Object, used to build custom
    collections of Objects.
    '''
    
    object: PointerProperty(type = Object)
