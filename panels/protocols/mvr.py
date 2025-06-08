# Copyright (C) 2024 vanous
#
# This file is part of BlenderDMX.
#
# BlenderDMX is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# BlenderDMX is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <https://www.gnu.org/licenses/>.

import logging
import os
import uuid as py_uuid
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import bpy
from bpy.props import StringProperty
from bpy.types import Operator, Panel, UIList

from ...i18n import DMX_Lang
from ...logging_setup import DMX_Log
from ...mvrx_protocol import DMX_MVR_X_Client, DMX_MVR_X_WS_Client
from ...util import sizeof_fmt
from ...mvrxchange.mvrx_message import defined_station_name

_ = DMX_Lang._


class DMX_OP_MVR_Refresh(Operator):
    bl_label = _("Refresh")
    bl_description = _("Refresh connection")
    bl_idname = "dmx.mvr_refresh"
    bl_options = {"UNDO"}

    def execute(self, context):
        DMX_MVR_X_Client.re_join()
        return {"FINISHED"}


class DMX_OP_MVR_WS_Refresh(Operator):
    bl_label = _("Refresh")
    bl_description = _("Refresh connection")
    bl_idname = "dmx.mvr_ws_refresh"
    bl_options = {"UNDO"}

    def execute(self, context):
        DMX_MVR_X_WS_Client.re_join()
        return {"FINISHED"}


class DMX_OP_MVR_Request(Operator):
    bl_label = _("Request latest version")
    bl_description = _("Sends the Request message")
    bl_idname = "dmx.mvr_request"
    bl_options = {"UNDO"}

    def execute(self, context):
        mvr_x = context.window_manager.dmx.mvr_xchange
        all_clients = mvr_x.mvr_xchange_clients
        client = None
        if all_clients:
            client = all_clients[mvr_x.selected_client]
        uuid = str(py_uuid.uuid4()).upper()
        mvr_commit = {
            "FileUUID": uuid,
            "StationUUID": client.station_uuid,
            "Comment": datetime.now().strftime("%H:%M:%S %B %d, %Y"),
            "FileSize": 0,
        }

        last_commit = DMX_MVR_X_Client.create_self_request_commit(client, mvr_commit)
        if last_commit:
            DMX_MVR_X_Client.request_file(client, last_commit)

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
        mvr_x = context.window_manager.dmx.mvr_xchange
        all_clients = mvr_x.mvr_xchange_clients
        client = None
        if all_clients:
            client = all_clients[mvr_x.selected_client]

        for commit in client.commits:
            if commit.commit_uuid == self.uuid:
                DMX_Log.log.info(f"import {commit}")
                path = os.path.join(
                    ADDON_PATH, "assets", "mvrs", f"{commit.commit_uuid.upper()}.mvr"
                )
                DMX_Log.log.info(path)
                dmx.addMVR(path)
                break
        return {"FINISHED"}


class DMX_OP_MVR_WS_Import(Operator):
    bl_label = _("Import")
    bl_description = _("Import commit")
    bl_idname = "dmx.mvr_ws_import"
    bl_options = {"UNDO"}

    uuid: StringProperty()

    def execute(self, context):
        scene = context.scene
        dmx = scene.dmx
        ADDON_PATH = dmx.get_addon_path()
        websocket_commits = context.window_manager.dmx.mvr_xchange.websocket_commits
        for commit in websocket_commits:
            if commit.commit_uuid == self.uuid:
                DMX_Log.log.info(f"import {commit}")
                path = os.path.join(
                    ADDON_PATH, "assets", "mvrs", f"{commit.commit_uuid}.mvr"
                )
                DMX_Log.log.info(path)
                dmx.addMVR(path)
                break
        return {"FINISHED"}


class DMX_OP_MVR_X_Export(Operator):
    bl_label = _("Export")
    bl_description = _("Export MVR to MVR-xchange")
    bl_idname = "dmx.mvr_x_export"
    bl_options = {"UNDO"}

    def execute(self, context):
        scene = context.scene
        dmx = scene.dmx
        mvr_x = context.window_manager.dmx.mvr_xchange
        comment = mvr_x.commit_message
        if comment == "":
            comment = "File shared"
        current_file_path = bpy.data.filepath
        file_stem = Path(current_file_path).stem
        if not file_stem:
            file_stem = "untitled"
        ADDON_PATH = dmx.get_addon_path()
        uuid = str(py_uuid.uuid4()).upper()
        path = os.path.join(ADDON_PATH, "assets", "mvrs", f"{uuid}.mvr")
        result = dmx.export_mvr(path)
        DMX_Log.log.info(path)
        if result.ok:
            commit = SimpleNamespace(
                file_size=result.file_size,
                file_uuid=uuid,
                file_name=file_stem,
                comment=comment,
            )
            dmx.createMVR_Shared_Commit(commit)
        return {"FINISHED"}


class DMX_OP_MVR_Download(Operator):
    bl_label = _("Download")
    bl_description = _("Download commit")
    bl_idname = "dmx.mvr_download"
    bl_options = {"UNDO"}

    uuid: StringProperty()

    def execute(self, context):
        DMX_Log.log.info("downloading")

        mvr_x = context.window_manager.dmx.mvr_xchange
        all_clients = mvr_x.mvr_xchange_clients
        client = None
        if all_clients:
            client = all_clients[mvr_x.selected_client]

        DMX_Log.log.info(f"got client {client.station_name}")
        for commit in client.commits:
            DMX_Log.log.info(commit.commit_uuid)
            if commit.commit_uuid == self.uuid:
                DMX_Log.log.info(f"downloading {commit}")
                DMX_MVR_X_Client.request_file(client, commit)
                break

        return {"FINISHED"}


class DMX_OP_MVR_WS_Download(Operator):
    bl_label = _("Websocket Download")
    bl_description = _("Download commit")
    bl_idname = "dmx.mvr_ws_download"
    bl_options = {"UNDO"}

    uuid: StringProperty()

    def execute(self, context):
        # TODO: implement WS download

        DMX_Log.log.info(("downloading", self.uuid))

        websocket_commits = context.window_manager.dmx.mvr_xchange.websocket_commits
        for commit in websocket_commits:
            if commit.commit_uuid == self.uuid:
                DMX_Log.log.info(f"downloading {commit.commit_uuid}")
                DMX_MVR_X_WS_Client.request_file(commit)
                break

        return {"FINISHED"}


class DMX_OP_MVR_RemoveSharedCommit(Operator):
    bl_label = _("Delete")
    bl_description = _("Remove Shared Commit")
    bl_idname = "dmx.mvr_remove_shared_commit"
    bl_options = {"UNDO"}

    uuid: StringProperty()

    def execute(self, context):
        DMX_Log.log.info(("removing", self.uuid))

        commits = context.window_manager.dmx.mvr_xchange.shared_commits
        for idx, commit in enumerate(commits):
            if commit.commit_uuid == self.uuid:
                commits.remove(idx)
                break

        return {"FINISHED"}


class DMX_UL_MVR_Commit(UIList):
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        scene = context.scene
        dmx = scene.dmx
        icon = "GROUP_VERTEX"
        # layout.context_pointer_set("mvr_xchange_clients", item)
        col = layout.column()

        if item.timestamp_saved < 0:
            icon = "ERROR"
        elif item.timestamp_saved == 0:
            icon = "CHECKBOX_DEHLT"
        else:
            icon = "CHECKBOX_HLT"

        col.label(
            text=f"{item.comment}",
            icon=icon,
        )
        col = layout.column()
        timestamp = datetime.fromtimestamp(item.timestamp).strftime("%H:%M:%S %b %d")
        col.label(text=f"{timestamp}")
        col = layout.column()
        file_size = sizeof_fmt(item.file_size)
        col.label(text=f"{file_size}")
        col = layout.column()
        col.operator("dmx.mvr_download", text="", icon="IMPORT").uuid = item.commit_uuid
        col.enabled = dmx.mvrx_enabled
        col = layout.column()
        col.operator(
            "dmx.mvr_import", text="", icon="CHECKBOX_HLT"
        ).uuid = item.commit_uuid
        col.enabled = item.timestamp_saved > 0

    def filter_items(self, context, data, property):
        # Filter the items in the UIList
        flt_flags = []
        flt_name = self.filter_name.lower()  # Get the search string from the UIList

        for item in data.commits:
            if flt_name in item.comment.lower():
                flt_flags.append(self.bitflag_filter_item)
            else:
                flt_flags.append(0)

        return flt_flags, []


class DMX_UL_MVR_WS_Commit(UIList):
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        scene = context.scene
        dmx = scene.dmx
        icon = "GROUP_VERTEX"
        # layout.context_pointer_set("mvr_xchange_clients", item)
        col = layout.column()

        if item.timestamp_saved < 0:
            icon = "ERROR"
        elif item.timestamp_saved == 0:
            icon = "CHECKBOX_DEHLT"
        else:
            icon = "CHECKBOX_HLT"

        col.label(
            text=f"{item.comment}",
            icon=icon,
        )
        col = layout.column()
        timestamp = datetime.fromtimestamp(item.timestamp).strftime("%H:%M:%S %b %d")
        col.label(text=f"{timestamp}")
        col = layout.column()
        file_size = sizeof_fmt(item.file_size)
        col.label(text=f"{file_size}")
        col = layout.column()
        col.operator(
            "dmx.mvr_ws_download", text="", icon="IMPORT"
        ).uuid = item.commit_uuid
        col.enabled = dmx.mvrx_socket_client_enabled
        col = layout.column()
        col.operator(
            "dmx.mvr_ws_import", text="", icon="CHECKBOX_HLT"
        ).uuid = item.commit_uuid
        col.enabled = item.timestamp_saved > 0

    def filter_items(self, context, data, property):
        # Filter the items in the UIList
        flt_flags = []
        flt_name = self.filter_name.lower()  # Get the search string from the UIList

        for item in data.websocket_commits:
            if flt_name in item.comment.lower():
                flt_flags.append(self.bitflag_filter_item)
            else:
                flt_flags.append(0)

        return flt_flags, []


class DMX_UL_MVR_Shared_Commit(UIList):
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        # layout.context_pointer_set("mvr_xchange_clients", item)
        col = layout.column()
        col.label(text=f"{item.comment}")
        col = layout.column()
        timestamp = datetime.fromtimestamp(item.timestamp).strftime("%H:%M:%S %b %d")
        col.label(text=f"{timestamp}")
        col = layout.column()
        file_size = sizeof_fmt(item.file_size)
        col.label(text=f"{file_size}")
        col = layout.column()
        col.operator(
            "dmx.mvr_remove_shared_commit", text="", icon="TRASH"
        ).uuid = item.commit_uuid

    def filter_items(self, context, data, property):
        # Filter the items in the UIList
        flt_flags = []
        flt_name = self.filter_name.lower()  # Get the search string from the UIList

        for item in data.shared_commits:
            if flt_name in item.comment.lower():
                flt_flags.append(self.bitflag_filter_item)
            else:
                flt_flags.append(0)

        return flt_flags, []


class DMX_UL_MVR_Stations(UIList):
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        dmx = context.scene.dmx
        icon = dmx.custom_icons[item.icon_id].icon_id
        # layout.context_pointer_set("mvr_xchange_clients", item)
        col = layout.column()
        col.label(text=f"{item.station_name}", icon_value=icon)
        col1 = layout.column()
        col1.prop(item, "subscribed", text="")
        col2 = layout.column()
        col2.operator("dmx.mvr_request", text="", icon="IMPORT")
        col1.enabled = col2.enabled = dmx.mvrx_enabled

    def filter_items(self, context, data, property):
        # Filter the items in the UIList
        flt_flags = []
        flt_name = self.filter_name.lower()  # Get the search string from the UIList
        mvr_x = context.window_manager.dmx.mvr_xchange

        for item in data.mvr_xchange_clients:
            if item.service_name != mvr_x.mvr_x_group:
                flt_flags.append(0)
                continue
            if flt_name in item.station_name.lower():
                flt_flags.append(self.bitflag_filter_item)
            else:
                flt_flags.append(0)

        return flt_flags, []


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
        mvr_x = context.window_manager.dmx.mvr_xchange

        if not bpy.app.online_access:
            row = layout.row()
            row.label(text=_("You must Allow Online access for this to work:"))
            prefs = context.preferences
            system = prefs.system
            row = layout.row()
            row.prop(system, "use_online_access", text="Allow Online Access")

        row = layout.row()
        row.prop(dmx, "mvrx_socket_client_enabled")
        url_exists = len(dmx.mvr_x_ws_url) > 1
        row.enabled = bpy.app.online_access and url_exists

        row = layout.row()
        row.prop(dmx, "mvr_x_ws_url")
        row.enabled = bpy.app.online_access

        row = layout.row()
        row.prop(dmx, "zeroconf_enabled")
        if not dmx.zeroconf_enabled:
            return

        row = layout.row()
        row.prop(mvr_x, "ip_address")
        row.enabled = not dmx.mvrx_enabled

        row = layout.row()
        row.prop(dmx, "mvrx_enabled", text=f"Enable Group: {mvr_x.mvr_x_group}")

        if not dmx.mvrx_enabled:
            row.enabled = mvr_x.existing_groups_exist or mvr_x.new_group_bool
            if (
                mvr_x.existing_groups_exist
                and not mvr_x.mvr_x_group
                and not mvr_x.new_group_bool
            ):
                mvr_x.mvr_x_group = mvr_x.all_mvr_groups

            row = layout.row()

            col1 = row.column()
            col2 = row.column()
            col1.prop(mvr_x, "new_group_bool", text="New group:")
            col2.prop(mvr_x, "new_mvr_x_group_string", text="")
            col1.enabled = not dmx.mvrx_enabled
            col2.enabled = not dmx.mvrx_enabled and mvr_x.new_group_bool
            row = layout.row()
            row.prop(mvr_x, "all_mvr_groups")
            row.enabled = not dmx.mvrx_enabled and not mvr_x.new_group_bool

        # if not dmx.zeroconf_enabled:
        #    return

        row = layout.row()
        row.operator("dmx.mvr_x_export", text="Share current version", icon="EXPORT")
        # row.enabled = dmx.zeroconf_enabled

        row = layout.row()
        row.prop(mvr_x, "commit_message")
        # row.enabled = dmx.zeroconf_enabled

        row = layout.row()
        # row.enabled = dmx.zeroconf_enabled

        row = layout.row()
        row.label(
            text=_("Shared by me ({defined_station_name}):").format(
                defined_station_name=defined_station_name
            )
        )

        row = layout.row()
        row.template_list(
            "DMX_UL_MVR_Shared_Commit",
            "",
            mvr_x,
            "shared_commits",
            mvr_x,
            "selected_shared_commit",
            rows=4,
        )
        if dmx.zeroconf_enabled:
            row = layout.row()
            row.label(text=_("Stations in the group:"))

            row = layout.row()
            row.template_list(
                "DMX_UL_MVR_Stations",
                "",
                mvr_x,
                "mvr_xchange_clients",
                mvr_x,
                "selected_client",
                rows=4,
            )
            all_clients = mvr_x.mvr_xchange_clients
            client = None
            if len(all_clients) > mvr_x.selected_client:
                client = all_clients[mvr_x.selected_client]

            if client:
                row = layout.row()
                row.label(text=_("Shared to me:"))
                row = layout.row()
                row.label(text=f"{client.ip_address}:{client.port}")
                row = layout.row()

                row.template_list(
                    "DMX_UL_MVR_Commit",
                    "",
                    client,
                    "commits",
                    mvr_x,
                    "selected_commit",
                    rows=4,
                )

        if dmx.mvrx_socket_client_enabled:
            row = layout.row()
            ws_group = (
                dmx.mvr_x_ws_url.split(".")[0]
                .replace("wss://", "")
                .replace("ws://", "")
            )
            row.label(text=f"{ws_group}", icon="WORLD")
            col1 = row.column()
            col1.operator("dmx.mvr_ws_refresh", text="", icon="FILE_REFRESH")
            row = layout.row()
            row.label(text=_("Shared to me:"))
            row = layout.row()

            row.template_list(
                "DMX_UL_MVR_WS_Commit",
                "",
                mvr_x,
                "websocket_commits",
                mvr_x,
                "selected_ws_commit",
                rows=4,
            )
