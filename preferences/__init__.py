import pathlib

from bpy.types import AddonPreferences
from bpy.props import StringProperty


class DMX_Preferences(AddonPreferences):
    bl_idname = pathlib.Path(__file__).parent.parts[-2]

    share_api_username: StringProperty(
        default="",
        name="GDTF Share Username",
        description="Username for GDTF Share",
    )

    share_api_password: StringProperty(
        default="",
        name="GDTF Share Password",
        subtype='PASSWORD',
        description="Password for GDTF Share",
    )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.label(text="Username and Password for GDTF Share. Get a free account at gdtf-share.com")
        layout.prop(self, "share_api_username")
        layout.prop(self, "share_api_password")

