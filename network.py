import bpy
from . import ifaddr


class DMX_Network:
    """This class is holding persisted data for the artnet_ipaddr enum. Persistently, because
    we cannot get the enum_items from this dynamically filled enum and we want to hold a cache, because
    this is called automatically when the panel is open, and we want to limit the amount
    of calls. So when artnet is enabled, we just return cached data."""

    instance = None
    data = None

    def __init__(self):
        super(DMX_Network, self).__init__()

    @staticmethod
    def cards(arg_a, arg_b):
        if DMX_Network.instance is None:
            DMX_Network.instance = DMX_Network()

        dmx = bpy.context.scene.dmx
        if dmx.artnet_enabled and DMX_Network.data is not None:
            # return cached data to prevent many fast refreshes
            return DMX_Network.data

        all_cards = [("0.0.0.0", "0.0.0.0", "All interfaces")]
        for adapter in ifaddr.get_adapters():
            for ip in adapter.ips:
                if type(ip.ip) is tuple:  # ipv6 addresses, skip
                    continue
                if ip.ip.startswith("169.254."):
                    continue  # local link addresses on Windows, skip
                all_cards.append((ip.ip, ip.ip, ip.nice_name))
        DMX_Network.data = all_cards
        return DMX_Network.data
