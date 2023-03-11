import bpy
from bpy.types import PropertyGroup
from bpy.props import ( CollectionProperty,
                        FloatVectorProperty,
                        IntProperty,
                        FloatProperty )

from .ui.operator import *
from .ui.panel import *

# Module Data Structure

class DMX_Programmer(PropertyGroup):

    def _on_color(self, context):
        pass

    color: FloatVectorProperty(
        subtype = "COLOR",
        size = 4,
        min = 0.0,
        max = 1.0,
        default = (1.0,1.0,1.0,1.0),
        update = _on_color
    )

    def _on_dimmer(self, context):
        pass

    dimmer: FloatProperty(
        default = 0,
        min = 0,
        max = 1,
        update = _on_dimmer)

    def _on_pan(self, context):
        pass

    pan: FloatProperty(
        min = -1.0,
        max = 1.0,
        default = 0.0,
        update = _on_pan)

    def _on_tilt(self, context):
        pass

    tilt: FloatProperty(
        min = -1.0,
        max = 1.0,
        default = 0.0,
        update = _on_tilt)

    def _on_zoom(self, context):
        pass

    zoom: IntProperty(
        min = 1,
        max = 180,
        default = 25,
        update = _on_zoom)

    def _on_shutter(self, context):
        pass

    shutter: IntProperty(
        min = 0,
        max = 255,
        default = 0,
        update = _on_shutter)

# Add-on Module Registering

classes = (

    # Data Structures
    DMX_Programmer,
        
    # Operators
    DMX_OP_Programmer_SelectAll,
    DMX_OP_Programmer_SelectInvert,
    DMX_OP_Programmer_SelectEveryOther,
    DMX_OP_Programmer_DeselectAll,
    DMX_OP_Programmer_SelectBodies,
    DMX_OP_Programmer_SelectTargets,
    DMX_OP_Programmer_Clear,

    # Panel
    DMX_PT_Programmer
    
)