import bpy
from .mvrxchange import mvrxchange_client as mvrx_client
from .mvrxchange import mvrxchange_server as mvrx_server
from .logging import DMX_Log
import os
import time
import pathlib
#from dmx import bl_info as application_info
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
        if "StationUUID" not in data:
            DMX_Log.log.debug(f"Bad response {data}")
            return
        uuid = data["StationUUID"]
        if "Commits" in data:
            DMX_MVR_X_Client._instance._dmx.createMVR_Commits(data["Commits"], uuid)
        if "FileUUID" in data:
            DMX_MVR_X_Client._instance._dmx.createMVR_Commits([data], uuid)
        if "Provider" in data:
            provider = data["Provider"]
            DMX_MVR_X_Client._instance._dmx.updateMVR_Client(provider=provider, station_uuid=uuid)
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
        if not DMX_MVR_X_Client._instance:
            return
        if DMX_MVR_X_Client._instance.client:
            ADDON_PATH = os.path.dirname(os.path.abspath(__file__))
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

        if "StationUUID" not in json_data:
            DMX_Log.log.error(f"Bad response {json_data}")
            return
        uuid = json_data["StationUUID"]
        if "Commits" in json_data:
            DMX_MVR_X_Server._instance._dmx.createMVR_Commits(json_data["Commits"], uuid)
        if "FileUUID" in json_data:
            DMX_MVR_X_Server._instance._dmx.createMVR_Commits([json_data], uuid)
        if "Provider" in json_data:
            provider = json_data["Provider"]
            station_name = ""
            if "StationName" in json_data:
                station_name = json_data["StationName"]
            DMX_MVR_X_Server._instance._dmx.createMVR_Client(station_name=station_name, station_uuid=uuid, service_name=None, ip_address=addr, port=port, provider=provider)
        if "file_downloaded" in json_data:
            DMX_MVR_X_Server._instance._dmx.fetched_mvr_downloaded_file(json_data["file_downloaded"])

    @staticmethod
    def request_file(commit):
        if DMX_MVR_X_Server._instance:
            if DMX_MVR_X_Server._instance.DMX_MVR_X_Server:
                ADDON_PATH = os.path.dirname(os.path.abspath(__file__))
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
