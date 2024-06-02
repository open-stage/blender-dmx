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
from oscpy.server import OSCThreadServer
from .logging import DMX_Log


class DMX_OSC:
    _instance = None

    def __init__(self):
        super(DMX_OSC, self).__init__()
        self.data = None
        self.server = OSCThreadServer()
        self._dmx = bpy.context.scene.dmx

    def callback(*values):
        DMX_Log.log.debug("Got OSC message, values: {}".format(values))

    @staticmethod
    def send(data_path: str, data_value: str):
        if not DMX_OSC._instance:
            DMX_Log.log.debug("no OSC instance...")
            return
        data_path = bytes(data_path, "utf-8")
        data_value = bytes(data_value, "utf-8")
        DMX_Log.log.debug(("OSC sending:", data_path, data_value))
        dmx = bpy.context.scene.dmx
        DMX_OSC._instance.server.send_message(data_path, [data_value], dmx.osc_target_address, dmx.osc_target_port)

    @staticmethod
    def enable():
        if DMX_OSC._instance:
            return
        DMX_OSC._instance = DMX_OSC()
        # If we have for OSC input in the future, we should make port and root path configurable
        DMX_OSC._instance.server.listen(address="0.0.0.0", port=8000, default=True)  # right now we map to 0.0.0, input is not used
        DMX_OSC._instance.server.bind(b"/blenderdmx", DMX_OSC.callback)  # this is our address, unused at the moment
        DMX_Log.log.info("Enabling OSC")

    @staticmethod
    def disable():
        if DMX_OSC._instance:
            try:
                DMX_OSC._instance.server.stop()  # Stop the default socket
            except Exception as e:
                ...
            DMX_OSC._instance.server.terminate_server()
            DMX_OSC._instance.server.join_server()
            DMX_OSC._instance = None
            DMX_Log.log.info("Disabling OSC")
