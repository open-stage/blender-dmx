import bpy
from dmx.sacn import sACNreceiver
from dmx.data import DMX_Data
from dmx.logging import DMX_Log
import os


class DMX_sACN:
    _instance = None

    def __init__(self):
        super(DMX_sACN, self).__init__()
        self.data = None
        self.receiver = sACNreceiver()
        self._dmx = bpy.context.scene.dmx

    def callback(packet):  # packet type: sacn.DataPacket
        if packet.dmxStartCode > 0:
            # See https://tsp.esta.org/tsp/working_groups/CP/DMXAlternateCodes.php
            DMX_Log.log.debug("Ignoring packet with start code %s", packet.dmxStartCode)
            return
        dmx = bpy.context.scene.dmx
        if packet.universe >= len(dmx.universes):
            DMX_Log.log.error("Not enough DMX universes set in BlenderDMX for incoming sACN data")
            return
        if dmx.universes[packet.universe].input != "sACN":
            DMX_Log.log.warning("This DMX universe is not set to accept sACN data")
            return
        DMX_Data.set_universe(packet.universe, bytearray(packet.dmxData), "sACN")
        try:
            if dmx.sacn_status != "online":
                dmx.sacn_status = "online"
        except Exception as e:
            DMX_Log.log.error(f"Error when setting status {e}")

    @staticmethod
    def enable():
        if DMX_sACN._instance:
            return
        DMX_sACN._instance = DMX_sACN()
        dmx = bpy.context.scene.dmx
        DMX_sACN._instance.receiver.start()  # start the receiving thread
        DMX_Log.log.info("enabling ACN")

        for universe in range(0, len(dmx.universes)):
            if dmx.universes[universe].input != "sACN":
                continue
            if universe == 0:  # invalid for sACN
                continue
            DMX_sACN._instance.receiver.register_listener("universe", DMX_sACN.callback, universe=universe)
            DMX_Log.log.info(("Joining sACN universe:", universe))
            DMX_sACN._instance.receiver.join_multicast(universe)
        bpy.app.timers.register(DMX_sACN.run_render)
        dmx.sacn_status = "listen"

    @staticmethod
    def disable():
        dmx = bpy.context.scene.dmx
        if DMX_sACN._instance:
            for universe in range(1, len(dmx.universes) + 1):
                DMX_Log.log.info(("Leaving sACN universe:", universe))
                DMX_sACN._instance.receiver.leave_multicast(universe)
            DMX_sACN._instance.receiver.remove_listener(DMX_sACN.callback)
            DMX_sACN._instance.receiver.stop()
            DMX_sACN._instance.data = None
            DMX_sACN._instance = None
        dmx.set_acn_status = "offline"

        if bpy.app.timers.is_registered(DMX_sACN.run_render):
            bpy.app.timers.unregister(DMX_sACN.run_render)

    @staticmethod
    def run_render():
        bpy.context.scene.dmx.render()
        return 1.0 / 60.0
