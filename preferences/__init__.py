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
from .. import rna_keymap_ui

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

        # https://blenderartists.org/t/keymap-for-addons/685544/28
        scene = context.scene
        dmx = scene.dmx
        box = layout.box()
        col = box.column()
        col.label(text="Keymap Settings:",icon="HAND")
        col.separator()
        wm = bpy.context.window_manager
        kc = wm.keyconfigs.user
        get_kmi_l = []
        for km_add, kmi_add in dmx._keymaps:
            for km_con in kc.keymaps:
                if km_add.name == km_con.name:
                    km = km_con
                    break

            for kmi_con in km.keymap_items:
                if kmi_add.idname == kmi_con.idname:
                    if kmi_add.name == kmi_con.name:
                        get_kmi_l.append((km,kmi_con))

        get_kmi_l = sorted(set(get_kmi_l), key=get_kmi_l.index)

        for km, kmi in get_kmi_l:
            col.context_pointer_set("keymap", km)
            rna_keymap_ui.draw_kmi([], kc, km, kmi, col, 0)
            col.separator()
