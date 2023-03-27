import bpy
import os
import pathlib

from bpy.types import AddonPreferences
from bpy.props import StringProperty

from src.lang import DMX_Lang
_ = DMX_Lang._

# Module Data Structure

class DMX_Preferences(AddonPreferences):
    bl_idname = pathlib.Path(__file__).parent.parts[-3]

    share_api_key: StringProperty(
        default="",
        name=_("GDTF Share API key"),
        description=_("Private API key for GDTF Share"),
    )

    def draw(self, context):
        self.layout.use_property_split = True
        self.layout.prop(self, "share_api_key")


# Add-on Module Registering

classes = (
    DMX_Preferences,
)
