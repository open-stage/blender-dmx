# Copyright (C) 2025 vanous
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
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    IntProperty,
    StringProperty,
)
from bpy.types import PropertyGroup
from ..network import DMX_Network
from ..i18n import DMX_Lang

_ = DMX_Lang._

# MVR-xchange commit and client RNA structures


class DMX_MVR_Xchange_Commit(PropertyGroup):
    def onUpdate(self, context):
        # empty callback just for automatic UI updates
        return

    commit_uuid: StringProperty(name=_("File UUID"), update=onUpdate)
    comment: StringProperty(name=_("Comment"))
    file_name: StringProperty(name=_("File Name"))
    station_uuid: StringProperty(name=_("Station UUID"))
    file_size: IntProperty(name=_("File Size"))
    timestamp: IntProperty(name=_("Time of info"))
    timestamp_saved: IntProperty(name=_("Time of saving"), default=0)
    subscribed: BoolProperty(name=_("Subscribed to"))
    self_requested: BoolProperty(name=_("We requested latest file without UUID"))


class DMX_MVR_Xchange_Client(PropertyGroup):
    def onUpdate(self, context):
        # empty callback just for automatic UI updates
        icon = "DEFAULT_TEST"
        if any("Production Assist" in x for x in [self.provider, self.station_name]):
            self.icon_id = "PRODUCTION_ASSIST"
        elif any("gMA3" in x for x in [self.provider, self.station_name]):
            self.icon_id = "GMA3"
        elif any("GrandMA3" in x for x in [self.provider, self.station_name]):
            self.icon_id = "GMA3"
        elif any("BlenderDMX" in x for x in [self.provider, self.station_name]):
            self.icon_id = "BLENDER_DMX"
        elif any("Vectorworks" in x for x in [self.provider, self.station_name]):
            self.icon_id = "VW"
        return

    def onSubscribe(self, context):
        dmx = bpy.context.scene.dmx
        dmx.onMVR_client_join(self, self.subscribed)

    ip_address: StringProperty(name=_("IP Address"))
    port: IntProperty(name=_("Port"))
    subscribed: BoolProperty(name=_("Connected"), default=False, update=onSubscribe)
    last_seen: IntProperty(name=_("Last Seen Time"), update=onUpdate)
    station_name: StringProperty(name=_("Station Name"))
    station_uuid: StringProperty(name=_("Station UUID"))
    service_name: StringProperty(name=_("MVR-xchange group"))
    provider: StringProperty(name=_("Provider"))
    commits: CollectionProperty(name=_("Commits"), type=DMX_MVR_Xchange_Commit)
    icon_id: StringProperty(name=_("Icon ID"), default="DEFAULT_TEST")

    def get_clients(self, context):
        clients = bpy.context.window_manager.dmx.mvr_xchange.mvr_xchange_clients
        dmx = bpy.context.scene.dmx
        data = []
        for index, client in enumerate(clients):
            if client.station_uuid and client.station_name and client.service_name:
                data.append(
                    (
                        client.station_uuid,
                        client.station_name,
                        client.station_uuid,
                        dmx.custom_icons[client.icon_id].icon_id,
                        index,
                    )
                )
        return data

    def get_groups(self, context):
        mvr_x = bpy.context.window_manager.dmx.mvr_xchange
        clients = bpy.context.window_manager.dmx.mvr_xchange.mvr_xchange_clients
        dmx = bpy.context.scene.dmx
        data = []
        services = [client.service_name for client in clients]

        for service_name in set(services):
            data.append(
                (
                    service_name,
                    service_name,
                    service_name,
                )
            )
        if data:
            mvr_x.existing_groups_exist = True
        else:
            mvr_x.existing_groups_exist = False
        return data


class DMX_MVR_Xchange(PropertyGroup):
    def updateGroup(self, context):
        if self.new_group_bool:
            self.mvr_x_group = self.new_mvr_x_group_string
        else:
            self.mvr_x_group = self.all_mvr_groups

    selected_commit: IntProperty(default=0)
    selected_group: IntProperty(default=0)
    selected_ws_commit: IntProperty(default=0)
    existing_groups_exist: BoolProperty(default=False)
    new_group_bool: BoolProperty(name=_("New Group:"), update=updateGroup)
    mvr_xchange_clients: CollectionProperty(
        name=_("MVR-xchange Clients"), type=DMX_MVR_Xchange_Client
    )
    all_mvr_groups: EnumProperty(
        name=_("Existing Groups"),
        description="",
        items=DMX_MVR_Xchange_Client.get_groups,
        update=updateGroup,
    )
    shared_commits: CollectionProperty(name=_("Commits"), type=DMX_MVR_Xchange_Commit)
    websocket_commits: CollectionProperty(
        name=_("Websocket Commits"), type=DMX_MVR_Xchange_Commit
    )
    selected_shared_commit: IntProperty(default=0)
    selected_client: IntProperty(default=0)
    commit_message: StringProperty(
        name=_("Message"), description=_("Message"), default=""
    )

    def get_addresses(self, context):
        addresses = DMX_Network.cards(None, None)
        if len(addresses):
            return addresses[1:]
        else:
            return addresses

    ip_address: EnumProperty(
        name=_("IPv4 Address for MVR-xchange"),
        description=_("The network card/interface for MVR-xchange"),
        items=get_addresses,
    )

    def edit_group(self, context):
        if "." in self.new_mvr_x_group_string:
            self.new_mvr_x_group_string = self.new_mvr_x_group_string.replace(".", "_")
        if not self.new_mvr_x_group_string:
            self.new_mvr_x_group_string = "WorkGroup"

    mvr_x_group: StringProperty(default="")

    new_mvr_x_group_string: StringProperty(
        name=_("Group"), description=_("Group"), default="WorkGroup", update=edit_group
    )

    export_focus_points: BoolProperty(
        name=_("Export Targets as MVR Focus Points"),
        description=_("Export Targets as MVR Focus Points"),
        default=True,
    )

    selected_fixtures_only: BoolProperty(
        name=_("Export only selected fixtures"),
        description=_(
            "Export only selected fixtures (does not filter non-fixture objects)"
        ),
        default=False,
    )

    export_fixtures_only: BoolProperty(
        name=_("Export fixtures only"),
        description=_("Export fixtures only (skip all non-fixture objects)"),
        default=False,
    )
