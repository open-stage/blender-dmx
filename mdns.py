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
from zeroconf import IPVersion, ServiceBrowser, ServiceStateChange, Zeroconf, ServiceInfo, get_all_addresses

from .logging import DMX_Log
from typing import cast
import uuid as pyuuid
import socket

# mdns (zeroconf) instances for discover and for mdns server


class DMX_Zeroconf:
    _instance = None

    def __init__(self):
        super(DMX_Zeroconf, self).__init__()
        self.data = None
        self.zeroconf = Zeroconf(ip_version=IPVersion.V4Only)
        self.browser = None
        self.info = None
        self._dmx = bpy.context.scene.dmx
        prefs = bpy.context.preferences.addons[__package__].preferences
        application_uuid = prefs.get("application_uuid", str(pyuuid.uuid4()))  # must never be 0
        self.application_uuid = application_uuid

    def callback(zeroconf: Zeroconf, service_type: str, name: str, state_change: ServiceStateChange) -> None:
        DMX_Log.log.debug(f"Service {name} of type {service_type} state changed: {state_change}")

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
                    station_uuid = info.properties[b"StationUUID"].decode("utf-8")
        station_name = f"{station_name} ({service_name})"
        DMX_Log.log.info(info)
        if state_change is ServiceStateChange.Added:
            DMX_Zeroconf._instance._dmx.createMVR_Client(station_name, station_uuid, service_name, ip_address, int(port))
        elif state_change is ServiceStateChange.Updated:
            DMX_Zeroconf._instance._dmx.updateMVR_Client(station_uuid, station_name, service_name, ip_address, int(port))
        else:  # removed
            DMX_Zeroconf._instance._dmx.removeMVR_Client(station_uuid, station_name, service_name, ip_address, int(port))

    @staticmethod
    def enable_discovery():
        if not DMX_Zeroconf._instance:
            DMX_Zeroconf._instance = DMX_Zeroconf()

        services = ["_mvrxchange._tcp.local."]
        DMX_Zeroconf._instance.browser = ServiceBrowser(DMX_Zeroconf._instance.zeroconf, services, handlers=[DMX_Zeroconf.callback])
        DMX_Log.log.info("Enabling Zeroconf")
        DMX_Log.log.info("starting mvrx discovery")

    @staticmethod
    def close():
        if DMX_Zeroconf._instance:
            if DMX_Zeroconf._instance.browser:
                DMX_Zeroconf._instance.browser.cancel()
                DMX_Log.log.info("closing mvrx discovery")
            if DMX_Zeroconf._instance.info:
                DMX_Zeroconf._instance.zeroconf.unregister_service(DMX_Zeroconf._instance.info)
            DMX_Zeroconf._instance.zeroconf.close()
            DMX_Zeroconf._instance = None

    @staticmethod
    def enable_server(server_name="test_mvr", port=9999):
        if server_name == "":
            DMX_Log.log.critical("server name missing, cannot start mdns service")
            return
        if not DMX_Zeroconf._instance:
            DMX_Zeroconf._instance = DMX_Zeroconf()
        host_name = f"{socket.gethostname()}-{pyuuid.uuid4().hex}"
        station_name = f"BlenderDMX station {socket.gethostname()}"
        desc = {"StationUUID": DMX_Zeroconf._instance.application_uuid, "StationName": station_name}
        addrs = [socket.inet_pton(socket.AF_INET, address) for address in get_all_addresses()]
        DMX_Zeroconf._instance.info = ServiceInfo(
            "_mvrxchange._tcp.local.",
            name=f"{server_name}._mvrxchange._tcp.local.",
            addresses=addrs,
            port=port,
            properties=desc,
            server=f"{host_name}.local.",
        )
        DMX_Log.log.debug(DMX_Zeroconf._instance.info)

        DMX_Zeroconf._instance.zeroconf.register_service(DMX_Zeroconf._instance.info, cooperating_responders=True)

    @staticmethod
    def disable_server():
        if DMX_Zeroconf._instance:
            if DMX_Zeroconf._instance.info:
                DMX_Zeroconf._instance.zeroconf.unregister_service(DMX_Zeroconf._instance.info)
