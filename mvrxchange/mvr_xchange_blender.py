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
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    IntProperty,
    StringProperty,
)
from bpy.types import PropertyGroup

from ..network import DMX_Network

# MVR-xchange commit and client RNA structures


class DMX_MVR_Xchange_Commit(PropertyGroup):
    def onUpdate(self, context):
        # empty callback just for automatic UI updates
        return

    commit_uuid: StringProperty(name="File UUID", update=onUpdate)
    comment: StringProperty(name="Comment")
    file_name: StringProperty(name="File Name")
    station_uuid: StringProperty(name="Station UUID")
    file_size: IntProperty(name="File Size")
    timestamp: IntProperty(name="Time of info")
    timestamp_saved: IntProperty(name="Time of saving", default=0)
    subscribed: BoolProperty(name="Subscribed to")
    self_requested: BoolProperty(name="We requested latest file without UUID")


class DMX_MVR_Xchange_Client(PropertyGroup):
    def onUpdate(self, context):
        # empty callback just for automatic UI updates
        return

    ip_address: StringProperty(name="IP Address")
    port: IntProperty(name="Port")
    subscribed: BoolProperty(name="Subscribed to")
    last_seen: IntProperty(name="Last Seen Time", update=onUpdate)
    station_name: StringProperty(name="Station Name")
    station_uuid: StringProperty(name="Station UUID")
    service_name: StringProperty(name="MVR-xchange group")
    provider: StringProperty(name="Provider")
    commits: CollectionProperty(name="Commits", type=DMX_MVR_Xchange_Commit)

    def get_clients(self, context):
        clients = bpy.context.window_manager.dmx.mvr_xchange.mvr_xchange_clients
        dmx = bpy.context.scene.dmx
        data = []
        for index, client in enumerate(clients):
            icon = "DEFAULT_TEST"
            if any(
                "Production Assist" in x for x in [client.provider, client.station_name]
            ):
                icon = "PRODUCTION_ASSIST"
            elif any("gMA3" in x for x in [client.provider, client.station_name]):
                icon = "GMA3"
            elif any("GrandMA3" in x for x in [client.provider, client.station_name]):
                icon = "GMA3"
            elif any("BlenderDMX" in x for x in [client.provider, client.station_name]):
                icon = "BLENDER_DMX"
            if client.station_uuid and client.station_name and client.service_name:
                data.append(
                    (
                        client.station_uuid,
                        client.station_name,
                        client.station_uuid,
                        dmx.custom_icons[icon].icon_id,
                        index,
                    )
                )
        return data


class DMX_MVR_Xchange(PropertyGroup):
    selected_commit: IntProperty(default=0)
    selected_ws_commit: IntProperty(default=0)
    mvr_xchange_clients: CollectionProperty(
        name="MVR-xchange Clients", type=DMX_MVR_Xchange_Client
    )
    selected_mvr_client: EnumProperty(
        name="Client", description="", items=DMX_MVR_Xchange_Client.get_clients
    )
    shared_commits: CollectionProperty(name="Commits", type=DMX_MVR_Xchange_Commit)
    websocket_commits: CollectionProperty(
        name="Websocket Commits", type=DMX_MVR_Xchange_Commit
    )
    selected_shared_commit: IntProperty(default=0)
    selected_client: IntProperty(default=0)
    commit_message: StringProperty(name="Message", description="Message", default="")

    def get_addresses(self, context):
        addresses = DMX_Network.cards(None, None)
        if len(addresses):
            return addresses[1:]
        else:
            return addresses

    ip_address: EnumProperty(
        name="IPv4 Address for MVR-xchange",
        description="The network card/interface for MVR-xchange",
        items=get_addresses,
    )

    def edit_group(self, context):
        if "." in self.mvr_x_group:
            self.mvr_x_group = self.mvr_x_group.replace(".", "_")
        if not self.mvr_x_group:
            self.mvr_x_group = "WorkGroup"

    mvr_x_group: StringProperty(
        name="Group", description="Group", default="WorkGroup", update=edit_group
    )
