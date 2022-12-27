import bpy
from dmx.sacn import sACNreceiver
from dmx.data import DMX_Data


class DMX_ACN:

    _instance = None

    def __init__(self):
        super(DMX_ACN, self).__init__()
        self.data = None
        self.receiver = sACNreceiver()
        self._dmx = bpy.context.scene.dmx

    def callback(packet):  # packet type: sacn.DataPacket
        dmx = bpy.context.scene.dmx
        if packet.universe >= len(dmx.universes):
            print("Not enough DMX universes set in BlenderDMX")
            return
        if not dmx.universes[packet.universe]:
            print("sACN universe doesn't exist in BlenderDMX")
            return
        if dmx.universes[packet.universe].input != "sACN":
            print("This DMX universe is not set to accept sACN data")
            return
        DMX_Data.set_universe(packet.universe, bytearray(packet.dmxData))
        dmx.artnet_status = "online"

    @staticmethod
    def enable():
        DMX_ACN._instance = DMX_ACN()
        dmx = bpy.context.scene.dmx
        DMX_ACN._instance.receiver.start()  # start the receiving thread

        for universe in range(1, len(dmx.universes) + 1):
            DMX_ACN._instance.receiver.register_listener(
                "universe", DMX_ACN.callback, universe=universe
            )
        DMX_ACN._instance.receiver.join_multicast(1)
        bpy.app.timers.register(DMX_ACN.run_render)
        dmx.artnet_status = "listen"

    @staticmethod
    def disable():
        dmx = bpy.context.scene.dmx
        if DMX_ACN._instance:
            DMX_ACN._instance.receiver.leave_multicast(1)
            DMX_ACN._instance.receiver.remove_listener(DMX_ACN.callback)
            DMX_ACN._instance.receiver.stop()
            DMX_ACN._instance.data = None
            dmx.artnet_status = "offline"

        if bpy.app.timers.is_registered(DMX_ACN.run_render):
            bpy.app.timers.unregister(DMX_ACN.run_render)

    @staticmethod
    def run_render():
        bpy.context.scene.dmx.render()
        return 1.0 / 60.0
