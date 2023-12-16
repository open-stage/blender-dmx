#
#   BlendexDMX > MVR Objects
#
#   http://www.github.com/open-stage/BlenderDMX
#

import bpy
import math
import mathutils
import uuid

import json
from bpy.props import (IntProperty,
                       FloatProperty,
                       BoolProperty,
                       FloatVectorProperty,
                       PointerProperty,
                       StringProperty,
                       CollectionProperty)

from bpy.types import (PropertyGroup,
                       Collection,
                       Object,
                       Material)

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

