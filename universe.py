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


from bpy.props import EnumProperty, IntProperty, StringProperty
from bpy.types import PropertyGroup

network_options_list = (
    ("BLENDERDMX", "BlenderDMX", "Set DMX buffer from the Programmer"),
    ("ARTNET", "ArtNet", "Read DMX buffer from ArtNet"),
    ("sACN", "sACN", "Read DMX buffer from sACN"),
)


class DMX_Universe(PropertyGroup):
    id: IntProperty(name="ID", description="Number of the universe", default=0)

    name: StringProperty(
        name="Name", description="Name of the universe", default="Universe 0"
    )

    input: EnumProperty(
        name="Input",
        description="Input source of the universe",
        default="BLENDERDMX",
        items=network_options_list,
    )

    input_settings: StringProperty(default="Input Settings")

    @staticmethod
    def add(dmx, id, name):
        dmx.universes.add()
        universe = dmx.universes[-1]
        universe.id = id
        universe.name = name
        return universe

    @staticmethod
    def remove(dmx, i):
        if i >= 0 and i < len(dmx.universes):
            dmx.universes.remove(i)
