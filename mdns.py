from types import DynamicClassAttribute
import bpy
from dmx.zeroconf import (
    IPVersion,
    ServiceBrowser,
    ServiceStateChange,
    Zeroconf,
)
from dmx.logging import DMX_Log
from typing import cast


class DMX_Zeroconf:
    _instance = None

    def __init__(self):
        super(DMX_Zeroconf, self).__init__()
        self.data = None
        self.zeroconf = None
        self.browser = None
        self._dmx = bpy.context.scene.dmx

    def callback(zeroconf: Zeroconf, service_type: str, name: str, state_change: ServiceStateChange) -> None:
        # print(f"Service {name} of type {service_type} state changed: {state_change}")

        info = zeroconf.get_service_info(service_type, name)
        service_name = name.replace(f".{service_type}", "")
        station_name = ""
        station_uuid = ""
        ip_address = ""
        port = 0

        if info:
            addresses = ["%s:%d" % (addr, cast(int, info.port)) for addr in info.parsed_scoped_addresses()]
            for address in addresses:
                if "::" in address:
                    continue
                ip_a, ip_port = address.split(":")
                ip_address = ip_a
                port = ip_port

            if info.properties:
                if b"StationName" in info.properties:
                    station_name = info.properties[b"StationName"].decode("utf-8")
                if b"StationUUID" in info.properties:
                    station_uuid = info.properties[b"StationUUID"].decode("utf-")
        station_name = f"{station_name} ({service_name})"
        if state_change is ServiceStateChange.Added:
            DMX_Zeroconf._instance._dmx.createMVR_Client(station_name, station_uuid, ip_address, int(port))
        elif state_change is ServiceStateChange.Updated:
            DMX_Zeroconf._instance._dmx.updateMVR_Client(station_name, station_uuid, ip_address, int(port))
        else:  # removed
            DMX_Zeroconf._instance._dmx.removeMVR_Client(station_name, station_uuid, ip_address, int(port))

    @staticmethod
    def enable():
        if DMX_Zeroconf._instance:
            return
        DMX_Zeroconf._instance = DMX_Zeroconf()

        services = ["_mvrxchange._tcp.local."]
        DMX_Zeroconf._instance.zeroconf = Zeroconf(ip_version=IPVersion.V4Only)
        DMX_Zeroconf._instance.browser = ServiceBrowser(DMX_Zeroconf._instance.zeroconf, services, handlers=[DMX_Zeroconf.callback])
        DMX_Log.log.info("Enabling Zeroconf")
        print("starting mvrx discovery")

    @staticmethod
    def disable():
        if DMX_Zeroconf._instance:
            DMX_Zeroconf._instance.zeroconf.close()
            DMX_Zeroconf._instance = None
            print("closing mvrx discovery")
            DMX_Log.log.info("Disabling Zeroconf")
