# Copyright (C) 2026 vanous
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

import bpy

from sinette import SinetteReceiver

from .data import DMX_Data
from .logging_setup import DMX_Log


class DMX_Sinette:
    _instance = None
    scope = "local"

    def __init__(self):
        self.receiver = SinetteReceiver(scope=self.scope)
        self._dmx = bpy.context.scene.dmx

    @staticmethod
    def callback(packet):
        dmx = bpy.context.scene.dmx
        if packet.universe >= len(dmx.universes):
            DMX_Log.log.error(
                "Not enough DMX universes set in BlenderDMX for incoming Sinette data"
            )
            return
        if dmx.universes[packet.universe].input != "Sinette":
            DMX_Log.log.warning("This DMX universe is not set to accept Sinette data")
            return

        DMX_Data.set_universe(packet.universe, bytearray(packet.dmxData), "Sinette")
        if dmx.sinette_status != "online":
            dmx.sinette_status = "online"

    @staticmethod
    def enable():
        if DMX_Sinette._instance:
            return

        DMX_Sinette._instance = DMX_Sinette()
        dmx = bpy.context.scene.dmx
        DMX_Sinette._instance.receiver.start()
        DMX_Log.log.info("Enabling Sinette")

        for universe in range(1, len(dmx.universes)):
            if dmx.universes[universe].input != "Sinette":
                continue
            DMX_Sinette._instance.receiver.register_listener(
                "universe", DMX_Sinette.callback, universe=universe
            )
            DMX_Log.log.info(("Joining Sinette universe:", universe))
            DMX_Sinette._instance.receiver.join_multicast(universe)
        dmx.sinette_status = "listen"

    @staticmethod
    def disable():
        dmx = bpy.context.scene.dmx
        if DMX_Sinette._instance:
            for universe in range(1, len(dmx.universes)):
                if dmx.universes[universe].input == "Sinette":
                    DMX_Log.log.info(("Leaving Sinette universe:", universe))
                    DMX_Sinette._instance.receiver.leave_multicast(universe)
            DMX_Sinette._instance.receiver.remove_listener(DMX_Sinette.callback)
            DMX_Sinette._instance.receiver.stop()
            DMX_Sinette._instance = None
        dmx.sinette_status = "offline"
