import bpy
from bpy.props import BoolProperty, CollectionProperty, EnumProperty, IntProperty, StringProperty
from bpy.types import PropertyGroup


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
    timestamp_saved: IntProperty(name="Time of saving")
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
            if any("Production Assist" in x for x in [client.provider, client.station_name]):
                icon = "PRODUCTION_ASSIST"
            data.append((client.station_uuid, client.station_name, client.station_uuid, dmx.custom_icons[icon].icon_id, index))
        return data


class DMX_MVR_Xchange(PropertyGroup):
    selected_commit: IntProperty(default=0)
    mvr_xchange_clients: CollectionProperty(name="MVR-xchange Clients", type=DMX_MVR_Xchange_Client)

    selected_mvr_client: EnumProperty(name="Client", description="", items=DMX_MVR_Xchange_Client.get_clients)
