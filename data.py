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
from dmx.thread import DMX_Lock

class DMX_Data():

    _universes = []

    @staticmethod
    def setup(universes):
        old_n = len(DMX_Data._universes)
        # shrinking (less universes then before)
        if (universes < old_n):
            print("DMX", "Universes Deallocated: ", universes, " to ", old_n)
            DMX_Data._universes = DMX_Data._universes[:universes]
        # growing (more universes then before)
        else:
            for u in range(old_n,universes):
                DMX_Data._universes.append(bytearray([0]*512))
                print("DMX", "Universe Allocated: ", u)


    @staticmethod
    def get(universe, addr, n):
        if (universe > len(DMX_Data._universes)): return bytearray([0]*n)
        if (addr + n > 512): return bytearray([0]*n)
        return DMX_Data._universes[universe-1][addr-1:addr+n-1]
    
    @staticmethod
    def set(universe, addr, val):
        if (universe > len(DMX_Data._universes)): return
        #DMX_Data._universes[universe-1] = DMX_Data._universes[universe-1][:addr-1] + ('%c' % val) + DMX_Data._universes[universe-1][addr:]
        DMX_Data._universes[universe-1][addr-1] = val

    @staticmethod
    def set_universe(universe, data):
        if (universe >= len(DMX_Data._universes)):
            return
        with DMX_Lock:
            DMX_Data._universes[universe] = data
