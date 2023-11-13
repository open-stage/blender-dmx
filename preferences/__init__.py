import pathlib

from bpy.types import AddonPreferences
from bpy.props import StringProperty


class DMX_Preferences(AddonPreferences):
    bl_idname = pathlib.Path(__file__).parent.parts[-2]

    share_api_username: StringProperty(
        default="",
        name="GDTF Share API username",
        description="Username for GDTF Share",
    )

    share_api_password: StringProperty(
        default="",
        name="GDTF Share API password",
        description="Password for GDTF Share",
    )

    def draw(self, context):
        self.layout.use_property_split = True
        self.layout.prop(self, "share_api_username")
        self.layout.prop(self, "share_api_password")

