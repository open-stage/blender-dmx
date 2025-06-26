# Copyright (C) 2023 vanous
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

import os
import time

# from dmx import bl_info as application_info
import uuid as py_uuid

import bpy

from .logging_setup import DMX_Log
from .mvrxchange import mvrx_tcp_client as mvrx_client
from .mvrxchange import mvrx_tcp_server as mvrx_server
from .mvrxchange import mvrx_ws_client as mvrx_ws_client
from .mvrxchange.mvrx_message import mvrx_message

# Instances and callbacks for the MVR TCP client and servers


class DMX_MVR_X_Client:
    """This is a blender specific instance of the MVR-xchange client
    (mvrx_protocol-mvrxchange_client-client) TCP connection"""

    def __init__(self, client):
        # super(DMX_MVR_X_Client, self).__init__()
        self._dmx = bpy.context.scene.dmx
        self.client = client
        self.tcp_client = None

        prefs = bpy.context.preferences.addons[__package__].preferences
        application_uuid = prefs.get(
            "application_uuid", str(py_uuid.uuid4())
        )  # must never be 0
        if self._dmx.mvrx_per_project_station_uuid:
            application_uuid = self._dmx.project_application_uuid
        self.application_uuid = application_uuid.upper()
        # print("bl info", application_info) # TODO: use this in the future
        self.connect()

    def connect(self):
        try:
            DMX_Log.log.info(
                f"Connecting to MVR-xchange client {self.client.ip_address} {self.client.port}"
            )
            self.tcp_client = mvrx_client.client(
                self.client.ip_address,
                self.client.port,
                timeout=0,
                callback=self.tcp_client_callback,
                application_uuid=self.application_uuid,
            )

        except Exception as e:
            DMX_Log.log.error(f"Cannot connect to host {e}")
            return
        self.tcp_client.start()
        DMX_Log.log.debug("thread started")

    def tcp_client_callback(self, data):
        # in the callback, we do most of the "local" processing
        dmx = bpy.context.scene.dmx

        station_uuid = ""
        if "StationUUID" in data:
            station_uuid = data["StationUUID"]

        if "Commits" in data and station_uuid != "":
            dmx.createMVR_Commits(data["Commits"], station_uuid)

        if "Type" in data and station_uuid != "":
            if data["Type"] == "MVR_COMMIT":
                dmx.createMVR_Commits([data], station_uuid)

        if "FileUUID" in data and station_uuid != "":
            dmx.createMVR_Commits([data], station_uuid)

        if "Provider" in data and station_uuid != "":
            provider = data["Provider"]
            station_name = None

            if "StationName" in data:
                station_name = data["StationName"]
            dmx.updateMVR_Client(
                provider=provider, station_uuid=station_uuid, station_name=station_name
            )

        if "file_downloaded" in data:
            dmx.fetched_mvr_downloaded_file(data["file_downloaded"])

        msg_type = data.get("Type", "")
        msg_ok = data.get("OK", "")
        # msg_message = data.get("Message", "")
        if msg_type == "MVR_JOIN_RET" and msg_ok is False:
            DMX_Log.log.error("MVR-xchange client refused our connection")
            dmx.toggle_join_MVR_Client(station_uuid, False)

        if msg_type == "MVR_REQUEST_RET" and msg_ok is False:
            DMX_Log.log.error("MVR-xchange file request declined")
            commit = self.tcp_client.commit
            if commit:
                dmx.request_failed_mvr_downloaded_file(commit)

    def create_self_request_commit(self, mvr_commit):
        """used when requesting commit ourselves just by mvr_request"""
        dmx = bpy.context.scene.dmx
        uuid = mvr_commit["FileUUID"]
        station_uuid = mvr_commit["StationUUID"]
        dmx.createMVR_Commits([mvr_commit], station_uuid)
        clients = bpy.context.window_manager.dmx.mvr_xchange.mvr_xchange_clients

        for client in clients:
            if client.station_uuid == station_uuid:
                for mvr_commit in client.commits:
                    if mvr_commit.commit_uuid == uuid:
                        mvr_commit.self_requested = True
                        return mvr_commit

    def request_file(self, commit):
        dmx = bpy.context.scene.dmx
        ADDON_PATH = dmx.get_addon_path()
        path = os.path.join(
            ADDON_PATH, "assets", "mvrs", f"{commit.commit_uuid.upper()}.mvr"
        )
        DMX_Log.log.debug(f"path {path}")
        try:
            self.tcp_client.request_file(commit, path)
        except Exception as e:
            DMX_Log.log.debug(f"problem requesting file {e}")
            return
        DMX_Log.log.info("Requesting file")

    def send_commit(self, commit):
        try:
            self.tcp_client.send_commit(commit)

        except Exception as e:
            DMX_Log.log.debug(f"problem re_joining {e}")
            return

    def join(self):
        self.tcp_client.join_mvr()
        DMX_Log.log.info("Joining")

    def disable(self):
        self.tcp_client.stop()
        DMX_Log.log.info("Disabling MVR client")

    def leave(self):
        self.tcp_client.leave_mvr()
        DMX_Log.log.info("Disabling MVR")


class DMX_MVR_X_Server:
    """This is an instance of the blender specific mvr_xchange TCP server
    (mvrx_protocol-mvrxchange_server-server) for incoming connections"""

    _instance = None

    def __init__(self):
        super(DMX_MVR_X_Server, self).__init__()
        self._dmx = bpy.context.scene.dmx
        self.server = None

        prefs = bpy.context.preferences.addons[__package__].preferences
        application_uuid = prefs.get(
            "application_uuid", str(py_uuid.uuid4())
        )  # must never be 0
        if self._dmx.mvrx_per_project_station_uuid:
            application_uuid = self._dmx.project_application_uuid
        self.application_uuid = application_uuid.upper()
        # print("bl info", application_info) # TODO: use this in the future

    @staticmethod
    def tcp_server_callback(json_data, data):
        # TODO: rework this from a keyword based parsing to message Type based parsing
        DMX_Log.log.debug(("callback", json_data, data, type(json_data), type(data)))
        addr, port = data.addr
        # provider = ""
        # station_name = ""
        station_uuid = ""

        if "StationUUID" in json_data:
            station_uuid = json_data["StationUUID"]

        if "Commits" in json_data and station_uuid != "":
            DMX_MVR_X_Server._instance._dmx.createMVR_Commits(
                json_data["Commits"], station_uuid
            )

        if "FileUUID" in json_data and station_uuid != "":
            DMX_MVR_X_Server._instance._dmx.createMVR_Commits([json_data], station_uuid)

        if "Type" in json_data and station_uuid != "":
            if json_data["Type"] == "MVR_COMMIT":
                DMX_MVR_X_Server._instance._dmx.createMVR_Commits(
                    [json_data], station_uuid
                )

    @staticmethod
    def enable():
        if DMX_MVR_X_Server._instance:
            return
        DMX_MVR_X_Server._instance = DMX_MVR_X_Server()
        try:
            DMX_MVR_X_Server._instance.server = mvrx_server.server(
                callback=DMX_MVR_X_Server.tcp_server_callback,
                uuid=DMX_MVR_X_Server._instance.application_uuid,
            )

        except Exception as e:
            DMX_Log.log.error(f"Cannot connect to host {e}")
            return
        DMX_MVR_X_Server._instance.server.start()

    @staticmethod
    def get_port():
        if DMX_MVR_X_Server._instance:
            return DMX_MVR_X_Server._instance.server.get_port()

    @staticmethod
    def disable():
        if DMX_MVR_X_Server._instance:
            if DMX_MVR_X_Server._instance.server:
                DMX_MVR_X_Server._instance.server.stop()
            DMX_MVR_X_Server._instance = None
            DMX_Log.log.info("Disabling MVR")


class DMX_MVR_X_WS_Client:
    """Websocket client"""

    _instance = None

    def __init__(self):
        super(DMX_MVR_X_WS_Client, self).__init__()
        self._dmx = bpy.context.scene.dmx
        self.client = None
        self.server_url = None

        prefs = bpy.context.preferences.addons[__package__].preferences
        application_uuid = prefs.get(
            "application_uuid", str(py_uuid.uuid4())
        )  # must never be 0
        if self._dmx.mvrx_per_project_station_uuid:
            application_uuid = self._dmx.project_application_uuid
        self.application_uuid = application_uuid.upper()
        # print("bl info", application_info) # TODO: use this in the future

    @staticmethod
    def ws_client_callback(data):
        # TODO: rework this from a keyword based parsing to message Type based parsing
        DMX_Log.log.debug(("websocket data", data))
        station_uuid = ""

        if "StationUUID" in data:
            station_uuid = data["StationUUID"]
        if "Commits" in data and station_uuid != "":
            DMX_MVR_X_WS_Client._instance._dmx.createMVR_WS_Commits(
                data["Commits"], station_uuid
            )

        if "Type" in data and station_uuid != "":
            if data["Type"] == "MVR_COMMIT":
                DMX_MVR_X_WS_Client._instance._dmx.createMVR_WS_Commits(
                    [data], station_uuid
                )

        if "FileUUID" in data and station_uuid != "":
            DMX_MVR_X_WS_Client._instance._dmx.createMVR_WS_Commits(
                [data], station_uuid
            )

        if "Provider" in data and station_uuid != "":
            provider = data["Provider"]
            station_name = None

            if "StationName" in data:
                station_name = data["StationName"]
            DMX_MVR_X_WS_Client._instance._dmx.updateMVR_Client(
                provider=provider,
                station_uuid=station_uuid,
                station_name=station_name,
                service_name="",
                ip_address="0",
                port=0,
            )

        if "file_downloaded" in data:
            DMX_MVR_X_WS_Client._instance._dmx.fetched_mvr_downloaded_ws_file(
                data["file_downloaded"]
            )

        msg_type = data.get("Type", "")
        msg_ok = data.get("OK", "")
        # msg_message = data.get("Message", "")
        dmx = bpy.context.scene.dmx
        if msg_type == "MVR_JOIN_RET" and msg_ok is False:
            DMX_Log.log.error("MVR-xchange client refused our connection")
            # dmx.mvrx_enabled = False
            # TODO: needs testing

        if msg_type == "MVR_REQUEST_RET" and msg_ok is False:
            DMX_Log.log.error("MVR-xchange file request declined")

            commit = DMX_MVR_X_WS_Client._instance.client.commit
            if commit:
                dmx.request_failed_mvr_downloaded_ws_file(commit)

        if "Type" in data:
            if data["Type"] == "MVR_REQUEST":
                dmx = bpy.context.scene.dmx
                file_uuid = data["FileUUID"]
                if not file_uuid:
                    shared_commits = (
                        bpy.context.window_manager.dmx.mvr_xchange.shared_commits
                    )
                    if len(shared_commits):
                        last_commit = shared_commits[-1]
                        file_uuid = last_commit.commit_uuid
                        DMX_Log.log.debug("Sharing last version")

                ADDON_PATH = dmx.get_addon_path()
                file_path = os.path.join(
                    ADDON_PATH, "assets", "mvrs", f"{file_uuid.upper()}.mvr"
                )

                DMX_Log.log.debug("sending file")
                if not os.path.exists(file_path):
                    DMX_Log.log.error(
                        "MVR file for sending via MVR-xchange does not exist"
                    )

                    DMX_MVR_X_WS_Client._instance.client.send(
                        mvrx_message.create_message(
                            "MVR_REQUEST_RET",
                            ok=False,
                            nok_reason="Requested file does not exist",
                        )
                    )
                    return

                chunk_size = 8192
                with open(file_path, "br") as f:
                    buffer = f.read(chunk_size)
                    DMX_MVR_X_WS_Client._instance.client.send(buffer)
                    buffer = f.read(chunk_size)
                    while buffer:
                        DMX_MVR_X_WS_Client._instance.client.send(buffer)
                        buffer = f.read(chunk_size)

    @staticmethod
    def create_self_request_commit(mvr_commit):
        """used when requesting commit ourselves just by mvr_request"""
        uuid = mvr_commit["FileUUID"]
        station_uuid = mvr_commit["StationUUID"]
        DMX_MVR_X_Server._instance._dmx.createMVR_Commits([mvr_commit], station_uuid)
        clients = bpy.context.window_manager.dmx.mvr_xchange.mvr_xchange_clients

        for client in clients:
            if client.station_uuid == station_uuid:
                for mvr_commit in client.commits:
                    if mvr_commit.commit_uuid == uuid:
                        mvr_commit.self_requested = True
                        return mvr_commit

    @staticmethod
    def request_file(commit):
        if not DMX_MVR_X_WS_Client._instance:
            return
        if DMX_MVR_X_WS_Client._instance.client:
            dmx = bpy.context.scene.dmx
            ADDON_PATH = dmx.get_addon_path()
            path = os.path.join(
                ADDON_PATH, "assets", "mvrs", f"{commit.commit_uuid.upper()}.mvr"
            )
            DMX_Log.log.debug(f"path {path}")
            try:
                DMX_MVR_X_WS_Client._instance.client.request_file(commit, path)
            except Exception as e:
                DMX_Log.log.debug(f"problem requesting file {e}")
                return
            DMX_Log.log.info("Requesting file")

    @staticmethod
    def re_join():
        if not DMX_MVR_X_WS_Client._instance:
            return
        if DMX_MVR_X_WS_Client._instance.client:
            try:
                DMX_Log.log.debug("re-joining")
                DMX_MVR_X_WS_Client._instance.client.join_mvr()
            except Exception as e:
                DMX_Log.log.debug(f"problem re_joining {e}")
                return

    @staticmethod
    def connect():
        if not DMX_MVR_X_WS_Client._instance:
            return
        try:
            url = DMX_MVR_X_WS_Client._instance.server_url
            DMX_Log.log.info(f"Connecting to MVR-xchange client {url}")
            DMX_MVR_X_WS_Client._instance.client = mvrx_ws_client.WebSocketClient(
                url,
                callback=DMX_MVR_X_WS_Client.ws_client_callback,
                application_uuid=DMX_MVR_X_WS_Client._instance.application_uuid,
            )

        except Exception as e:
            DMX_Log.log.error(f"Cannot connect to host {e}")
            return
        DMX_MVR_X_WS_Client._instance.client.start()
        DMX_Log.log.debug("thread started")

    @staticmethod
    def join(server_url):
        DMX_MVR_X_WS_Client._instance = DMX_MVR_X_WS_Client()
        DMX_MVR_X_WS_Client._instance.server_url = server_url
        DMX_MVR_X_WS_Client.connect()
        # we send the mvr join automatically in the connected event

    @staticmethod
    def disable():
        if DMX_MVR_X_WS_Client._instance:
            if DMX_MVR_X_WS_Client._instance.client:
                DMX_MVR_X_WS_Client._instance.client.stop()
            DMX_MVR_X_WS_Client._instance = None
            DMX_Log.log.info("Disabling MVR")

    @staticmethod
    def leave():
        if DMX_MVR_X_WS_Client._instance:
            if DMX_MVR_X_WS_Client._instance.client:
                # DMX_MVR_X_WS_Client.connect()
                DMX_MVR_X_WS_Client._instance.client.leave_mvr()
                time.sleep(0.1)
                DMX_MVR_X_WS_Client._instance.client.stop()
            DMX_MVR_X_WS_Client._instance = None
            DMX_Log.log.info("Disabling MVR")
