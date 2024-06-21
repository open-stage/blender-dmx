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
import pypsn
from .logging import DMX_Log
from functools import partial


class DMX_PSN:
    _instances = {}
    _data = {}

    def __init__(self, callback, ip_address, port):
        super(DMX_PSN, self).__init__()
        self.data = None
        self.receiver = pypsn.receiver(callback, ip_address, port)
        self._dmx = bpy.context.scene.dmx

    def callback(psn_data, tracker):
        if isinstance(psn_data, pypsn.psn_data_packet):
            for idx, slot in enumerate(psn_data.trackers):
                position = slot.pos
                DMX_PSN.set_data(tracker.uuid, idx, position)
        if isinstance(psn_data, pypsn.psn_info_packet):
            DMX_Log.log.info(f"Tracker info server: {psn_data.name}")
            for tracker_info in psn_data.trackers:
                DMX_Log.log.info(f"Tracker info slot: {tracker_info.tracker_name}")

    @staticmethod
    def enable(tracker):
        uuid = tracker.uuid
        if uuid in DMX_PSN._instances:
            return
        DMX_Log.log.info("Enabling PSN")
        DMX_PSN._instances[uuid] = DMX_PSN(None, tracker.ip_address, tracker.ip_port)
        DMX_PSN._instances[uuid].receiver.callback = partial(DMX_PSN.callback, tracker=tracker)
        DMX_PSN._instances[uuid].receiver.start()
        DMX_PSN._data[uuid] = [
            [],
        ] * 10  # hardcoded to 10 slots
        if bpy.app.timers.is_registered(DMX_PSN.run_render):
            # we are already rendering
            pass
        else:
            bpy.app.timers.register(DMX_PSN.run_render)

    @staticmethod
    def disable(tracker):
        uuid = tracker.uuid
        if uuid in DMX_PSN._instances:
            try:
                DMX_Log.log.info(f"Disabling PSN {uuid}")
                DMX_PSN._instances[uuid].receiver.stop()  # Stop the default socket
            except Exception as e:
                DMX_Log.log.error(("Error", e))
            DMX_PSN._instances.pop(uuid, None)
            DMX_PSN._data.pop(uuid, None)
            DMX_Log.log.info(f"Disabled PSN {uuid}")
        if bpy.app.timers.is_registered(DMX_PSN.run_render):
            if len(DMX_PSN._instances) > 0:
                # we still need the render
                pass
            else:
                bpy.app.timers.unregister(DMX_PSN.run_render)

    @staticmethod
    def get_data(tracker_uuid):
        if tracker_uuid in DMX_PSN._data:
            return DMX_PSN._data[tracker_uuid]
        return []

    @staticmethod
    def set_data(tracker_uuid, slot, data):
        DMX_PSN._data[tracker_uuid][slot] = data

    @staticmethod
    def run_render():
        bpy.context.scene.dmx.render()
        return 1.0 / 60.0
