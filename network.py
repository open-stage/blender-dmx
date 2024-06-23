#    Copyright Hugo Aboud, vanous
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
import ifaddr


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
