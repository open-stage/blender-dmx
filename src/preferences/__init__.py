import bpy
import os
import pathlib

from bpy.types import AddonPreferences
from bpy.props import StringProperty

from i18n import DMX_Lang

_ = DMX_Lang._

# Module Data Structure


class DMX_Preferences(AddonPreferences):
    bl_idname = pathlib.Path(__file__).parent.parts[-3]

    share_api_username: StringProperty(
        default="",
        name=_("GDTF Share API username"),
        description=_("Username for GDTF Share"),
    )

    share_api_password: StringProperty(
        default="",
        name=_("GDTF Share API password"),
        description=_("Password for GDTF Share"),
    )

    def draw(self, context):
        self.layout.use_property_split = True
        self.layout.prop(self, "share_api_username")
        self.layout.prop(self, "share_api_password")


# Add-on Module Registering

classes = (DMX_Preferences,)
