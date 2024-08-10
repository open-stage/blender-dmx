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

import os
from bpy.props import StringProperty
from bpy.types import Operator, Panel, UIList
from ...mvrx_protocol import DMX_MVR_X_Client
from ...logging import DMX_Log
import uuid as py_uuid
from datetime import datetime

from ...i18n import DMX_Lang

_ = DMX_Lang._


class DMX_OP_MVR_Refresh(Operator):
    bl_label = _("Refresh")
    bl_description = _("Refresh connection")
    bl_idname = "dmx.mvr_refresh"
    bl_options = {"UNDO"}

    def execute(self, context):
        DMX_MVR_X_Client.re_join()
        return {"FINISHED"}


class DMX_OP_MVR_Request(Operator):
    bl_label = _("Request latest version")
    bl_description = _("Sends the Request message")
    bl_idname = "dmx.mvr_request"
    bl_options = {"UNDO"}

    station_uuid: StringProperty()

    def execute(self, context):
        uuid = str(py_uuid.uuid4())
        mvr_commit = {"FileUUID": uuid, "StationUUID": self.station_uuid, "Comment": datetime.now().strftime("%H:%M:%S %B %d, %Y"), "FileSize": 0}

        last_commit = DMX_MVR_X_Client.create_self_request_commit(mvr_commit)
        if last_commit:
            DMX_MVR_X_Client.request_file(last_commit)

        return {"FINISHED"}


class DMX_OP_MVR_Import(Operator):
    bl_label = _("Import")
    bl_description = _("Import commit")
    bl_idname = "dmx.mvr_import"
    bl_options = {"UNDO"}

    uuid: StringProperty()

    def execute(self, context):
        scene = context.scene
        dmx = scene.dmx
        ADDON_PATH = dmx.get_addon_path()
        clients = context.window_manager.dmx.mvr_xchange
        all_clients = context.window_manager.dmx.mvr_xchange.mvr_xchange_clients
        selected = clients.selected_mvr_client
        for client in all_clients:
            if client.station_uuid == selected:
                break
        for commit in client.commits:
            if commit.commit_uuid == self.uuid:
                DMX_Log.log.info(f"import {commit}")
                path = os.path.join(ADDON_PATH, "assets", "mvrs", f"{commit.commit_uuid}.mvr")
                DMX_Log.log.info(path)
                dmx.addMVR(path)
                break
        return {"FINISHED"}


class DMX_OP_MVR_Download(Operator):
    bl_label = _("Download")
    bl_description = _("Download commit")
    bl_idname = "dmx.mvr_download"
    bl_options = {"UNDO"}

    uuid: StringProperty()

    def execute(self, context):
        DMX_Log.log.info("downloading")

        clients = context.window_manager.dmx.mvr_xchange
        all_clients = clients.mvr_xchange_clients
        selected = clients.selected_mvr_client
        for client in all_clients:
            if client.station_uuid == selected:
                break
        DMX_Log.log.info(f"got client {client.station_name}")
        for commit in client.commits:
            DMX_Log.log.info(commit.commit_uuid)
            if commit.commit_uuid == self.uuid:
                DMX_Log.log.info(f"downloading {commit}")
                DMX_MVR_X_Client.request_file(commit)
                break

        return {"FINISHED"}


class DMX_UL_MVR_Commit(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        scene = context.scene
        dmx = scene.dmx
        icon = "GROUP_VERTEX"
        # layout.context_pointer_set("mvr_xchange_clients", item)
        col = layout.column()
        col.label(text=f"{item.comment}", icon="CHECKBOX_HLT" if item.timestamp_saved else "CHECKBOX_DEHLT")
        col = layout.column()
        col.operator("dmx.mvr_download", text="", icon="IMPORT").uuid = item.commit_uuid
        col.enabled = dmx.mvrx_enabled
        col = layout.column()
        col.operator("dmx.mvr_import", text="", icon="CHECKBOX_HLT").uuid = item.commit_uuid
        col.enabled = item.timestamp_saved > 0


class DMX_PT_DMX_MVR_X(Panel):
    bl_label = _("MVR-xchange")
    bl_idname = "DMX_PT_DMX_MVR_Xchange"
    bl_parent_id = "DMX_PT_DMX"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DMX"
    bl_context = "objectmode"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        dmx = context.scene.dmx

        row = layout.row()
        row.prop(dmx, "zeroconf_enabled")
        row = layout.row()

        clients = context.window_manager.dmx.mvr_xchange
        all_clients = clients.mvr_xchange_clients
        if not all_clients:
            selected = None
        else:
            selected = clients.selected_mvr_client

        client = None
        for client in all_clients:
            if client.station_uuid == selected:
                break

        row.prop(clients, "selected_mvr_client", text="")
        row.enabled = not dmx.mvrx_enabled
        row = layout.row()
        col = row.column()
        row.prop(dmx, "mvrx_enabled")
        col1 = row.column()
        col1.operator("dmx.mvr_refresh", text="", icon="FILE_REFRESH")
        col2 = row.column()
        if client:
            col2.operator("dmx.mvr_request", text="", icon="IMPORT").station_uuid = client.station_uuid
        col1.enabled = col2.enabled = dmx.mvrx_enabled
        # row.operator("dmx.mvr_test", text="Test", icon="CANCEL")
        row.enabled = len(all_clients) > 0
        if not client:
            return
        row = layout.row()
        row.label(text=f"{client.station_name}", icon="LINKED" if dmx.mvrx_enabled else "UNLINKED")
        layout.template_list(
            "DMX_UL_MVR_Commit",
            "",
            client,
            "commits",
            clients,
            "selected_commit",
            rows=4,
        )
