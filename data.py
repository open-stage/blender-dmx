#
#   BlendexDMX > Data
#   Allocates memory for DMX universes, which can be set from the Programmer
#   Future:
#       - Set from artnet
#       -
#
#   http://www.github.com/hugoaboud/BlenderDMX
#

import bpy

class DMX_Data():

    _data = []

    @staticmethod
    def setup(universes):
        old_n = len(DMX_Data._data)
        # shrinking (less universes then before)
        if (universes < old_n):
            print("DMX", "Universes Deallocated: ", universes, " to ", old_n)
            DMX_Data._data = DMX_Data._data[:universes]
        # growing (more universes then before)
        else:
            for u in range(old_n,universes):
                print("DMX", "Universe Allocated: ", u)
                DMX_Data._data.append("".join(['%c'%0]*512))

    @staticmethod
    def get(universe, addr, n):
        if (universe > len(DMX_Data._data)): return [0]*n
        if (addr + n > 512): return [0]*n
        return [ord(c) for c in DMX_Data._data[universe-1][addr-1:addr+n-1]]
    
    @staticmethod
    def set(universe, addr, val):
        if (universe > len(DMX_Data._data)): return
        DMX_Data._data[universe-1] = DMX_Data._data[universe-1][:addr-1] + ('%c' % val) + DMX_Data._data[universe-1][addr:]

    @staticmethod
    def set_string(universe, string):
        _data[universe] = string
