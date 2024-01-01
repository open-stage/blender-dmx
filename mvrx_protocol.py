import bpy
import dmx.mvrxchange_protocol as mvrx_protocol
from dmx.logging import DMX_Log
import os
import time
import pathlib
from dmx import bl_info as application_info
import uuid as py_uuid


class DMX_MVR_X_Protocol:
    _instance = None

    def __init__(self):
        super(DMX_MVR_X_Protocol, self).__init__()
        self._dmx = bpy.context.scene.dmx
        self.client = None

        addon_name = pathlib.Path(__file__).parent.parts[-1]
        prefs = bpy.context.preferences.addons[addon_name].preferences
        application_uuid = prefs.get("application_uuid", str(py_uuid.uuid4()))  # must never be 0
        self.application_uuid = application_uuid
        # print("bl info", application_info) # TODO: use this in the future

    @staticmethod
    def callback(data):
        if "StationUUID" not in data:
            print("Bad response", data)
            return
        uuid = data["StationUUID"]
        if "Files" in data:
            DMX_MVR_X_Protocol._instance._dmx.createMVR_Commits(data["Files"], uuid)
        if "FileUUID" in data:
            DMX_MVR_X_Protocol._instance._dmx.createMVR_Commits([data], uuid)
        if "Provider" in data:
            provider = data["Provider"]
            DMX_MVR_X_Protocol._instance._dmx.updateMVR_Client(provider = provider, station_uuid = uuid)
        if "file_downloaded" in data:
            DMX_MVR_X_Protocol._instance._dmx.fetched_mvr_downloaded_file(data["file_downloaded"])

    @staticmethod
    def request_file(commit):
        if DMX_MVR_X_Protocol._instance:
            if DMX_MVR_X_Protocol._instance.client:
                ADDON_PATH = os.path.dirname(os.path.abspath(__file__))
                path = os.path.join(ADDON_PATH, "assets", "mvrs", f"{commit.commit_uuid}.mvr")
                try:
                    DMX_MVR_X_Protocol._instance.client.request_file(commit, path)
                except:
                    print("problem requesting file")
                    return
                DMX_Log.log.info("Requesting file")

    @staticmethod
    def enable(client):
        if DMX_MVR_X_Protocol._instance:
            return
        DMX_MVR_X_Protocol._instance = DMX_MVR_X_Protocol()
        print("Connecting to MVR-xchange client", client.ip_address, client.port)
        try:
            DMX_MVR_X_Protocol._instance.client = mvrx_protocol.client(client.ip_address, client.port, timeout=0, callback=DMX_MVR_X_Protocol.callback, application_uuid=DMX_MVR_X_Protocol._instance.application_uuid)

        except Exception as e:
            print("Cannot connect to host", e)
            return
        DMX_MVR_X_Protocol._instance.client.start()
        DMX_MVR_X_Protocol._instance.client.join_mvr()
        DMX_Log.log.info("Joining")

    @staticmethod
    def disable():
        if DMX_MVR_X_Protocol._instance:
            if DMX_MVR_X_Protocol._instance.client:
                DMX_MVR_X_Protocol._instance.client.leave_mvr()
                time.sleep(0.3)
                DMX_MVR_X_Protocol._instance.client.stop()
            DMX_MVR_X_Protocol._instance = None
            DMX_Log.log.info("Disabling MVR")
