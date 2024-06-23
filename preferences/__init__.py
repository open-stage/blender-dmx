#    Copyright vanous
#
#    This file is part of BlenderDMX.
#
#    BlenderDMX is free software: you can redistribute it and/or modify it
#    under the terms of the GNU General Public License as published by the Free
#    Software Foundation, either version 3 of the License, or (at your option)
#    any later version.
#
#    BlenderDMX is distributed in the hope that it will be useful, but WITHOUT
#    ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
#    FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
#    more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program. If not, see <https://www.gnu.org/licenses/>.

import uuid as py_uuid

import bpy
from bpy.props import StringProperty
from bpy.types import AddonPreferences, Operator
from .. import __package__ as base_package


class DMX_Regenrate_UUID(Operator):
    bl_label = "Regenerate UUID"
    bl_idname = "dmx.regenerate_uuid"
    bl_options = {"UNDO"}

    def execute(self, context):
        prefs = bpy.context.preferences.addons[base_package].preferences
        uuid = str(py_uuid.uuid4())
        prefs["application_uuid"] = uuid
        return {"FINISHED"}


class DMX_Preferences(AddonPreferences):
    bl_idname = base_package

    share_api_username: StringProperty(
        default="",
        name="GDTF Share Username",
        description="Username for GDTF Share",
    )

    share_api_password: StringProperty(
        default="",
        name="GDTF Share Password",
        subtype="PASSWORD",
        description="Password for GDTF Share",
    )

    application_uuid: StringProperty(
        default=str(py_uuid.uuid4()),
        name="Application UUID",
        description="Used for example for MVR xchange",
    )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.label(text="Username and Password for GDTF Share. Get a free account at gdtf-share.com")
        layout.prop(self, "share_api_username")
        layout.prop(self, "share_api_password")
        layout.separator()
        layout.label(text="Application settings")
        row = layout.row()
        col = row.column()
        col.prop(self, "application_uuid")
        col.enabled = False
        col = row.column()
        col.operator("dmx.regenerate_uuid", text="", icon="FILE_REFRESH")
        layout.separator()
        layout.label(text="Make sure to save the preferences after editing.")
