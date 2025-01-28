#    Copyright Hugo Aboud, Kaspars Jaudzems, Mark Steward, vanous
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

from .logging import DMX_Log
from bpy.types import PropertyGroup
from bpy.props import IntProperty


def update_callback(self, context):
    # https://blender.stackexchange.com/questions/238441/force-redraw-add-on-custom-propery-in-n-panel-from-a-separate-thread
    # The above (tag_redraw()) doesn't work, but it seems that even if this method is empty
    # just the fact that there is an update callback on the DMX_Value.channel
    # causes the UI to be refreshed periodically even when not in focus
    return None


class DMX_Value(PropertyGroup):
    channel: IntProperty(name="DMX Value", update=update_callback, default=0)


class DMX_Data:
    _universes = []
    _virtuals = {}  # Virtual channels. These are per fixture and have an attribute and a value
    _dmx = None  # Cache access to the context.scene
    _live_view_data = [0] * 512

    @staticmethod
    def prepare_empty_buffer():
        # Prepare structure in the dmx_values collection, this is then used for the LiveDMX table
        if DMX_Data._dmx is not None:
            dmx = DMX_Data._dmx
            dmx.dmx_values.clear()
            buffer = [0] * 512
            for i in buffer:
                dmx.dmx_values.add()
                dmx.dmx_values[-1].channel = i

    @staticmethod
    def setup(universes):
        try:
            DMX_Data._dmx = bpy.context.scene.dmx
        except:
            pass
        DMX_Data.prepare_empty_buffer()
        old_n = len(DMX_Data._universes)
        # shrinking (less universes then before)
        if universes < old_n:
            DMX_Log.log.info(f"DMX Universes Deallocated: {universes}, to {old_n}")
            DMX_Data._universes = DMX_Data._universes[:universes]
        # growing (more universes then before)
        else:
            for u in range(old_n, universes):
                DMX_Data._universes.append(bytearray([0] * 512))
                DMX_Log.log.debug(f"DMX Universe Allocated: {u}")

    @staticmethod
    def get_value(universe, *channels):
        """Used for the namespace bdmx function
        Returns value of the given channels"""
        sum = 0
        for idx, channel in enumerate(reversed(channels)):
            val = DMX_Data.get(universe, channel, 1)[0]
            sum |= val << (idx << 3)
        return sum

    @staticmethod
    def get(universe, addr, n):
        if universe >= len(DMX_Data._universes):
            return bytearray([0] * n)
        if addr + n > 512:
            return bytearray([0] * n)
        return DMX_Data._universes[universe][addr - 1 : addr + n - 1]

    @staticmethod
    def set(universe, addr, val):
        DMX_Log.log.debug((universe, addr, val))
        if universe >= len(DMX_Data._universes):
            return
        if not bpy.context.scene.dmx.universes[universe]:
            return
        if bpy.context.scene.dmx.universes[universe].input != "BLENDERDMX":
            return
        if val > 255:
            return
        # This happened when importing one MVR file
        if addr > 511:
            return

        if DMX_Data._dmx is not None:
            dmx = (
                bpy.context.scene.dmx
            )  # hmm, here we use non cached dmx, probably this was safer...
            if dmx.get_selected_live_dmx_universe().input == "BLENDERDMX":
                dmx = bpy.context.scene.dmx
                dmx.dmx_values[addr - 1].channel = val

        DMX_Data._universes[universe][addr - 1] = val

        # LiveDMX view
        if DMX_Data._dmx is not None:
            dmx = (
                bpy.context.scene.dmx
            )  # ...or maybe it prevents using this call before the class is ready?
            selected_live_dmx_universe = dmx.get_selected_live_dmx_universe()
            if selected_live_dmx_universe is None:  # this should not happen
                raise ValueError(
                    "Missing selected universe, as if DMX base class is empty..."
                )
            if (
                selected_live_dmx_universe.input == "BLENDERDMX"
                and selected_live_dmx_universe.id == universe
            ):
                DMX_Data._live_view_data = DMX_Data._universes[universe]

    @staticmethod
    def set_virtual(fixture, attribute, geometry, value):
        """Set value of virtual channel for given fixture"""
        DMX_Log.log.debug((fixture, attribute, value))
        if value > 255:
            return
        if fixture not in DMX_Data._virtuals:
            DMX_Data._virtuals[fixture] = {}
        if attribute not in DMX_Data._virtuals[fixture]:
            DMX_Data._virtuals[fixture][attribute] = {}
        DMX_Data._virtuals[fixture][attribute]["value"] = value
        DMX_Data._virtuals[fixture][attribute]["geometry"] = geometry

    @staticmethod
    def get_virtual(fixture):
        """Get virtual channels for a given fixture"""
        if fixture in DMX_Data._virtuals:
            return DMX_Data._virtuals[fixture]
        return {}

    @staticmethod
    def set_universe(universe, data, source):
        DMX_Log.log.debug((universe, data))
        if universe >= len(DMX_Data._universes):
            return

        dmx_changed = DMX_Data._universes[universe] != data
        if dmx_changed:
            DMX_Data._universes[universe] = data

        if DMX_Data._dmx is not None:
            dmx = bpy.context.scene.dmx
            selected_live_dmx_universe = dmx.get_selected_live_dmx_universe()
            if selected_live_dmx_universe is None:  # this should not happen
                raise ValueError(
                    "Missing selected universe, as if DMX base class is empty..."
                )
            if (
                selected_live_dmx_universe.input == source
                and selected_live_dmx_universe.id == universe
            ):
                if dmx_changed:
                    DMX_Data._live_view_data = data
