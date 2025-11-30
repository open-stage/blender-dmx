# Copyright (C) 2023 vanous
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

import socket
import uuid as pyuuid
from typing import cast

import bpy
from zeroconf import (
    IPVersion,
    ServiceBrowser,
    ServiceInfo,
    ServiceStateChange,
    Zeroconf,
    DNSOutgoing,
    DNSQuestion,
    const,
)

from .logging_setup import DMX_Log
from .mvrxchange.mvrx_message import defined_station_name

# mdns (zeroconf) instances for discover and for mdns server


class DMX_Zeroconf:
    _instance = None

    def __init__(self):
        super(DMX_Zeroconf, self).__init__()
        self.data = None
        self.zeroconf = Zeroconf(ip_version=IPVersion.V4Only)
        self.zeroconf.start()
        self.browser = None
        self.dns_out = None
        self.info = None
        self._dmx = bpy.context.scene.dmx
        prefs = bpy.context.preferences.addons[__package__].preferences
        application_uuid = prefs.application_uuid  # must never be 0
        if self._dmx.mvrx_per_project_station_uuid:
            application_uuid = self._dmx.project_application_uuid
        self.application_uuid = application_uuid.upper()

    @staticmethod
    def mdns_ping():
        DMX_Zeroconf._instance.zeroconf.send(DMX_Zeroconf._instance.dns_out)
        return 10

    @staticmethod
    def enable_periodic_checker(enable):
        if enable:
            if bpy.app.timers.is_registered(DMX_Zeroconf._instance.mdns_ping):
                return

            if not DMX_Zeroconf._instance:
                DMX_Zeroconf._instance = DMX_Zeroconf()

            service_type = "_mvrxchange._tcp.local."
            service_name = "Placeholder._mvrxchange._tcp.local."  # not used
            port = 70000  # not used
            properties = {}
            server_name = f"{socket.gethostname()}.{service_type}"
            addrs = [socket.inet_pton(socket.AF_INET, "127.0.0.1")]

            info = ServiceInfo(
                service_type,
                service_name,
                addresses=addrs,
                port=port,
                properties=properties,
                server=server_name,
            )

            query = DNSOutgoing(const._FLAGS_QR_QUERY | const._FLAGS_AA)
            query.add_question(DNSQuestion(info.type, const._TYPE_PTR, const._CLASS_IN))
            DMX_Zeroconf._instance.dns_out = query

            bpy.app.timers.register(DMX_Zeroconf._instance.mdns_ping)
        else:
            if bpy.app.timers.is_registered(DMX_Zeroconf._instance.mdns_ping):
                bpy.app.timers.unregister(DMX_Zeroconf._instance.mdns_ping)

    def callback(
        zeroconf: Zeroconf,
        service_type: str,
        name: str,
        state_change: ServiceStateChange,
    ) -> None:
        DMX_Log.log.debug(
            f"Service {name} of type {service_type} state changed: {state_change}"
        )

        info = zeroconf.get_service_info(service_type, name)
        service_name = name.replace(f".{service_type}", "").split(".")[-1]
        station_name = ""
        station_uuid = ""
        ip_address = ""
        port = 0

        if info:
            addresses = [
                "%s:%d" % (addr, cast(int, info.port))
                for addr in info.parsed_scoped_addresses()
            ]
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
        # TODO: we should perhaps check if the station really has StationName
        # and StationUUID before we add it into the list
        if state_change is ServiceStateChange.Added:
            DMX_Zeroconf._instance._dmx.createMVR_Client(
                station_uuid, station_name, service_name, ip_address, int(port)
            )
        elif state_change is ServiceStateChange.Updated:
            DMX_Zeroconf._instance._dmx.updateMVR_Client(
                station_uuid, station_name, service_name, ip_address, int(port)
            )
        elif state_change is ServiceStateChange.Removed:
            # TODO: this typically does NOT work, because the info is empty. mDNS does not
            # provide us with this info, but in some strange cases it actually works.
            DMX_Zeroconf._instance._dmx.removeMVR_Client(
                station_uuid, station_name, service_name, ip_address, int(port)
            )

    @staticmethod
    def enable_discovery():
        if not DMX_Zeroconf._instance:
            DMX_Zeroconf._instance = DMX_Zeroconf()

        services = ["_mvrxchange._tcp.local."]
        DMX_Zeroconf._instance.browser = ServiceBrowser(
            DMX_Zeroconf._instance.zeroconf, services, handlers=[DMX_Zeroconf.callback]
        )

        DMX_Zeroconf.enable_periodic_checker(True)
        DMX_Log.log.info("Enabling Zeroconf")
        DMX_Log.log.info("starting mvrx discovery")

    @staticmethod
    def close():
        if DMX_Zeroconf._instance:
            DMX_Zeroconf._instance.enable_periodic_checker(False)
            if DMX_Zeroconf._instance.browser:
                DMX_Zeroconf._instance.browser.cancel()
                DMX_Log.log.info("closing mvrx discovery")
            # if DMX_Zeroconf._instance.info:
            #    DMX_Zeroconf._instance.zeroconf.unregister_service(
            #        DMX_Zeroconf._instance.info
            #    )
            DMX_Zeroconf._instance.zeroconf.close()
            DMX_Zeroconf._instance = None

    @staticmethod
    def enable_server(group_name=None, port=9999):
        if not DMX_Zeroconf._instance:
            DMX_Zeroconf._instance = DMX_Zeroconf()

        dmx = bpy.context.scene.dmx
        service_type = "_mvrxchange._tcp.local."
        station_name = defined_station_name

        if group_name is None or group_name == "":
            group_name = station_name

        desc = {
            "StationUUID": DMX_Zeroconf._instance.application_uuid,
            "StationName": station_name,
        }

        ip_address = bpy.context.window_manager.dmx.mvr_xchange.ip_address
        addrs = [socket.inet_pton(socket.AF_INET, ip_address)]
        DMX_Log.log.debug(addrs)

        service_name = f"{group_name}.{service_type}"

        DMX_Zeroconf._instance.info = ServiceInfo(
            service_type,
            service_name,
            addresses=addrs,
            port=port,
            properties=desc,
            server=f"{station_name}.{group_name}.{service_type}",
        )
        DMX_Log.log.debug(DMX_Zeroconf._instance.info)

        DMX_Zeroconf._instance.zeroconf.register_service(
            DMX_Zeroconf._instance.info, cooperating_responders=True
        )

    @staticmethod
    def disable_server():
        if DMX_Zeroconf._instance:
            if DMX_Zeroconf._instance.info:
                DMX_Zeroconf._instance.zeroconf.unregister_service(
                    DMX_Zeroconf._instance.info
                )
