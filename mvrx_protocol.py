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


import bpy
from .mvrxchange import mvrxchange_client as mvrx_client
from .mvrxchange import mvrxchange_server as mvrx_server
from .mvrxchange import mvrxchange_ws_client as mvrx_ws_client
from .logging import DMX_Log
import os
import time

# from dmx import bl_info as application_info
import uuid as py_uuid

# Instances and callbacks for the MVR TCP client and servers


class DMX_MVR_X_Client:
    """This is a blender specific instance of the MVR-xchange client
    (mvrx_protocol-mvrxchange_client-client) TCP connection"""

    _instance = None

    def __init__(self):
        super(DMX_MVR_X_Client, self).__init__()
        self._dmx = bpy.context.scene.dmx
        self.client = None
        self.selected_client = None

        prefs = bpy.context.preferences.addons[__package__].preferences
        application_uuid = prefs.get("application_uuid", str(py_uuid.uuid4()))  # must never be 0
        self.application_uuid = application_uuid
        # print("bl info", application_info) # TODO: use this in the future

    @staticmethod
    def callback(data):
        station_uuid = ""
        if "StationUUID" in data:
            station_uuid = data["StationUUID"]

        if "Commits" in data and station_uuid != "":
            DMX_MVR_X_Client._instance._dmx.createMVR_Commits(data["Commits"], station_uuid)

        if "Type" in data and station_uuid != "":
            if data["Type"] == "MVR_COMMIT":
                DMX_MVR_X_Client._instance._dmx.createMVR_Commits([data], station_uuid)

        if "FileUUID" in data and station_uuid != "":
            DMX_MVR_X_Client._instance._dmx.createMVR_Commits([data], station_uuid)

        if "Provider" in data and station_uuid != "":
            provider = data["Provider"]
            station_name = None

            if "StationName" in data:
                station_name = data["StationName"]
            DMX_MVR_X_Client._instance._dmx.updateMVR_Client(provider=provider, station_uuid=station_uuid, station_name=station_name)

        if "file_downloaded" in data:
            DMX_MVR_X_Client._instance._dmx.fetched_mvr_downloaded_file(data["file_downloaded"])

        msg_type = data.get("Type", "")
        msg_ok = data.get("OK", "")
        if msg_type == "MVR_JOIN_RET" and msg_ok is False:
            DMX_Log.log.error("MVR-xchange client refused our connection")
            dmx = bpy.context.scene.dmx
            dmx.mvrx_enabled = False

    @staticmethod
    def create_self_request_commit(mvr_commit):
        """used when requesting commit ourselves just by mvr_request"""
        uuid = mvr_commit["FileUUID"]
        station_uuid = mvr_commit["StationUUID"]
        DMX_MVR_X_Client._instance._dmx.createMVR_Commits([mvr_commit], station_uuid)
        clients = bpy.context.window_manager.dmx.mvr_xchange.mvr_xchange_clients

        for client in clients:
            if client.station_uuid == station_uuid:
                for mvr_commit in client.commits:
                    if mvr_commit.commit_uuid == uuid:
                        mvr_commit.self_requested = True
                        return mvr_commit

    @staticmethod
    def request_file(commit):
        if not DMX_MVR_X_Client._instance:
            return
        if DMX_MVR_X_Client._instance.client:
            dmx = bpy.context.scene.dmx
            ADDON_PATH = dmx.get_addon_path()
            path = os.path.join(ADDON_PATH, "assets", "mvrs", f"{commit.commit_uuid}.mvr")
            DMX_Log.log.debug(f"path {path}")
            try:
                DMX_MVR_X_Client.connect()
                DMX_MVR_X_Client._instance.client.request_file(commit, path)
            except Exception as e:
                DMX_Log.log.debug(f"problem requesting file {e}")
                return
            DMX_Log.log.info("Requesting file")

    @staticmethod
    def re_join():
        if not DMX_MVR_X_Client._instance:
            return
        if DMX_MVR_X_Client._instance.client:
            try:
                DMX_Log.log.debug(f"re-joining")
                DMX_MVR_X_Client.connect()
                DMX_MVR_X_Client._instance.client.join_mvr()
            except Exception as e:
                DMX_Log.log.debug(f"problem re_joining {e}")
                return

    @staticmethod
    def connect():
        if not DMX_MVR_X_Client._instance:
            return
        try:
            client = DMX_MVR_X_Client._instance.selected_client
            DMX_Log.log.info(f"Connecting to MVR-xchange client {client.ip_address} {client.port}")
            DMX_MVR_X_Client._instance.client = mvrx_client.client(client.ip_address, client.port, timeout=0, callback=DMX_MVR_X_Client.callback, application_uuid=DMX_MVR_X_Client._instance.application_uuid)

        except Exception as e:
            DMX_Log.log.error(f"Cannot connect to host {e}")
            return
        DMX_MVR_X_Client._instance.client.start()
        DMX_Log.log.debug("thread started")

    @staticmethod
    def join(client):
        DMX_MVR_X_Client._instance = DMX_MVR_X_Client()
        DMX_MVR_X_Client._instance.selected_client = client
        DMX_MVR_X_Client.connect()
        DMX_MVR_X_Client._instance.client.join_mvr()
        # TODO do only if we get OK ret
        DMX_Log.log.info("Joining")

    @staticmethod
    def disable():
        if DMX_MVR_X_Client._instance:
            if DMX_MVR_X_Client._instance.client:
                DMX_MVR_X_Client._instance.client.stop()
            DMX_MVR_X_Client._instance = None
            DMX_Log.log.info("Disabling MVR")

    @staticmethod
    def leave():
        if DMX_MVR_X_Client._instance:
            if DMX_MVR_X_Client._instance.client:
                DMX_MVR_X_Client.connect()
                DMX_MVR_X_Client._instance.client.leave_mvr()
                time.sleep(0.3)
                DMX_MVR_X_Client._instance.client.stop()
            DMX_MVR_X_Client._instance = None
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
        application_uuid = prefs.get("application_uuid", str(py_uuid.uuid4()))  # must never be 0
        self.application_uuid = application_uuid
        # print("bl info", application_info) # TODO: use this in the future

    @staticmethod
    def callback(json_data, data):
        DMX_Log.log.debug(("callback", json_data, data))
        addr, port = data.addr
        provider = ""
        station_name = ""
        station_uuid = ""

        if "StationUUID" in json_data:
            station_uuid = json_data["StationUUID"]

        if "Commits" in json_data and station_uuid != "":
            DMX_MVR_X_Server._instance._dmx.createMVR_Commits(json_data["Commits"], station_uuid)

        if "FileUUID" in json_data and station_uuid != "":
            DMX_MVR_X_Server._instance._dmx.createMVR_Commits([json_data], station_uuid)

        if "Type" in json_data and station_uuid != "":
            if json_data["Type"] == "MVR_COMMIT":
                DMX_MVR_X_Server._instance._dmx.createMVR_Commits([data], station_uuid)

        # if "Provider" in json_data:
        #    provider = json_data["Provider"]

        # if "StationName" in json_data:
        #    station_name = json_data["StationName"]

        # if provider != "" and station_name != "" and uuid != "":
        #    DMX_MVR_X_Server._instance._dmx.updateMVR_Client(station_name=station_name, station_uuid=uuid, service_name="", ip_address=addr, port=port, provider=provider)

        # if "file_downloaded" in json_data:
        #    DMX_MVR_X_Server._instance._dmx.fetched_mvr_downloaded_file(json_data["file_downloaded"])

    @staticmethod
    def request_file(commit):
        if DMX_MVR_X_Server._instance:
            if DMX_MVR_X_Server._instance.DMX_MVR_X_Server:
                dmx = bpy.context.scene.dmx
                ADDON_PATH = dmx.get_addon_path()
                path = os.path.join(ADDON_PATH, "assets", "mvrs", f"{commit.commit_uuid}.mvr")
                try:
                    DMX_MVR_X_Server._instance.server.request_file(commit, path)
                except:
                    DMX_Log.log.error("problem requesting file")
                    return
                DMX_Log.log.info("Requesting file")

    @staticmethod
    def enable():
        if DMX_MVR_X_Server._instance:
            return
        DMX_MVR_X_Server._instance = DMX_MVR_X_Server()
        try:
            DMX_MVR_X_Server._instance.server = mvrx_server.server(callback=DMX_MVR_X_Server.callback, uuid=DMX_MVR_X_Server._instance.application_uuid)

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

    @staticmethod
    def post_data(data):
        if DMX_MVR_X_Server._instance:
            return DMX_MVR_X_Server._instance.server.post_data(data)


class DMX_MVR_X_WS_Client:
    """Websocket client"""

    _instance = None

    def __init__(self):
        super(DMX_MVR_X_WS_Client, self).__init__()
        self._dmx = bpy.context.scene.dmx
        self.client = None
        self.server_url = None

        prefs = bpy.context.preferences.addons[__package__].preferences
        application_uuid = prefs.get("application_uuid", str(py_uuid.uuid4()))  # must never be 0
        self.application_uuid = application_uuid
        # print("bl info", application_info) # TODO: use this in the future

    @staticmethod
    def callback(data):
        DMX_Log.log.debug(("websocket data", data))
        station_uuid = ""

        if "StationUUID" in data:
            station_uuid = data["StationUUID"]

        if "Commits" in data and station_uuid != "":
            DMX_MVR_X_WS_Client._instance._dmx.createMVR_WS_Commits(data["Commits"], station_uuid)

        if "Type" in data and station_uuid != "":
            if data["Type"] == "MVR_COMMIT":
                DMX_MVR_X_WS_Client._instance._dmx.createMVR_WS_Commits([data], station_uuid)

        if "FileUUID" in data and station_uuid != "":
            DMX_MVR_X_WS_Client._instance._dmx.createMVR_WS_Commits([data], station_uuid)

        if "Provider" in data and station_uuid != "":
            provider = data["Provider"]
            station_name = None

            if "StationName" in data:
                station_name = data["StationName"]
            DMX_MVR_X_WS_Client._instance._dmx.updateMVR_Client(provider=provider, station_uuid=station_uuid, station_name=station_name, service_name="", ip_address="0", port=0)

        if "file_downloaded" in data:
            DMX_MVR_X_WS_Client._instance._dmx.fetched_mvr_downloaded_ws_file(data["file_downloaded"])

        msg_type = data.get("Type", "")
        msg_ok = data.get("OK", "")
        if msg_type == "MVR_JOIN_RET" and msg_ok is False:
            DMX_Log.log.error("MVR-xchange client refused our connection")
            dmx = bpy.context.scene.dmx
            dmx.mvrx_enabled = False

        if "Type" in data:
            if data["Type"] == "MVR_REQUEST":
                dmx = bpy.context.scene.dmx
                local_path = dmx.get_addon_path()
                file_uuid = data["FileUUID"]
                if not file_uuid:
                    shared_commits = bpy.context.window_manager.dmx.mvr_xchange.shared_commits
                    if len(shared_commits):
                        last_commit = shared_commits[-1]
                        file_uuid = last_commit.commit_uuid
                        DMX_Log.log.debug("Sharing last version")

                ADDON_PATH = dmx.get_addon_path()
                file_path = os.path.join(ADDON_PATH, "assets", "mvrs", f"{file_uuid}.mvr")

                DMX_Log.log.debug("sending file")
                if not os.path.exists(file_path):
                    DMX_Log.log.error("MVR file for sending via MVR-xchange does not exist")

                with open(file_path, "br") as f:
                    buffer = f.read()
                DMX_MVR_X_WS_Client._instance.client.send(buffer)

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
            path = os.path.join(ADDON_PATH, "assets", "mvrs", f"{commit.commit_uuid}.mvr")
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
                DMX_Log.log.debug(f"re-joining")
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
            DMX_MVR_X_WS_Client._instance.client = mvrx_ws_client.socket_client(url, callback=DMX_MVR_X_WS_Client.callback, application_uuid=DMX_MVR_X_WS_Client._instance.application_uuid)

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
                time.sleep(0.3)
                DMX_MVR_X_WS_Client._instance.client.stop()
            DMX_MVR_X_WS_Client._instance = None
            DMX_Log.log.info("Disabling MVR")
