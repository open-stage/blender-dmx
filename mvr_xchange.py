import bpy
from bpy.props import BoolProperty, CollectionProperty, EnumProperty, IntProperty, StringProperty
from bpy.types import PropertyGroup


class DMX_MVR_Xchange_Commit(PropertyGroup):
    commit_uuid: StringProperty(name="File UUID")
    comment: StringProperty(name="Comment")
    file_name: StringProperty(name="File Name")
    station_uuid: StringProperty(name="Station UUID")
    file_size: IntProperty(name="File Size")
    timestamp: IntProperty(name="Time of info")
    timestamp_saved: IntProperty(name="Time of saving")
    subscribed: BoolProperty(name="Subscribed to")


class DMX_MVR_Xchange_Client(PropertyGroup):
    ip_address: StringProperty(name="IP Address")
    port: IntProperty(name="Port")
    subscribed: BoolProperty(name="Subscribed to")
    last_seen: IntProperty(name="Last Seen Time")
    station_name: StringProperty(name="Station Name")
    station_uuid: StringProperty(name="Station UUID")
    provider: StringProperty(name="Provider")
    commits: CollectionProperty(name="Commits", type=DMX_MVR_Xchange_Commit)

    def get_clients(self, context):
        #print(self, context)
        clients  = bpy.context.window_manager.dmx.mvr_xchange.mvr_xchange_clients
        data = []
        for client in clients:
            data.append((client.station_uuid, client.station_name, client.station_uuid))
        return data

class DMX_MVR_Xchange(PropertyGroup):
    selected_commit: IntProperty(default=0)
    mvr_xchange_clients: CollectionProperty(
            name = "MVR-xchange Clients",
            type=DMX_MVR_Xchange_Client
            )

    selected_mvr_client: EnumProperty(
        name = "Client",
        description="",
        items = DMX_MVR_Xchange_Client.get_clients
    )
