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

bl_info = {
    "name": "DMX",
    "description": "DMX visualization and programming, with GDTF/MVR and Network support",
    "author": "open-stage",
    "version": (1, 7, 0),
    "blender": (3, 4, 0),
    "location": "3D View > DMX",
    "doc_url": "https://blenderdmx.eu/docs/faq/",
    "tracker_url": "https://github.com/open-stage/blender-dmx/issues",
    "category": "Lighting",
}

import sys
import bpy
from threading import Timer

from . import fixture as fixture
from .data import DMX_Data
from .artnet import DMX_ArtNet
from .acn import DMX_sACN

from .panels import profiles as Profiles

from .osc import DMX_OSC
from .mdns import DMX_Zeroconf

from .mvrx_protocol import DMX_MVR_X_Client, DMX_MVR_X_Server
from bpy.props import PointerProperty

from .i18n import DMX_Lang

_ = DMX_Lang._
from .dmx import DMX
from .dmx_temp_data import DMX_TempData
from . import in_out_mvr
from . import in_gdtf


@bpy.app.handlers.persistent
def onLoadFile(scene):
    if "Scene" in bpy.data.scenes:
        if "DMX" in bpy.data.scenes["Scene"].collection.children:
            print("INFO", "File contains DMX show, linking...")
            bpy.context.scene.dmx.linkFile()
        else:
            bpy.context.scene.dmx.unlinkFile()

    # Selection callback
    handle = object()
    subscribe_to = bpy.types.LayerObjects, "active"
    bpy.msgbus.subscribe_rna(
        key=subscribe_to,
        owner=handle,
        args=(None,),
        notify=onActiveChanged,
        options={
            "PERSISTENT",
        },
    )

    # Stop ArtNet
    DMX_ArtNet.disable()
    DMX_sACN.disable()
    DMX_OSC.disable()
    DMX_MVR_X_Client.disable()
    DMX_MVR_X_Server.disable()
    DMX_Zeroconf.close()

    # register a "bdmx" namespace to get current value of a DMX channel,
    # the syntax is #bdmx(universe, channel(s)), where the channel can be
    # multiple, to receive 8, 16, 24... bits of data:
    # for example: #bdmx(1,1) , #bdmx(1,1,2)
    bpy.app.driver_namespace["bdmx"] = DMX_Data.get_value


@bpy.app.handlers.persistent
def onUndo(scene):
    if not scene.dmx.collection and DMX.linkedToFile:
        scene.dmx.unlinkFile()


# Callbacks #

def onActiveChanged(*args):
    dmx = bpy.context.scene.dmx
    if dmx.volume_preview == "SELECTED":
        dmx.updatePreviewVolume()

    if dmx.display_2D:
        selected = False
        for fixture in dmx.fixtures:
            if bpy.context.active_object is not None and bpy.context.active_object.name in fixture.collection.objects:
                selected = True
                fixture.select()
            else:
                fixture.unselect()
        if selected:
            bpy.context.window_manager.dmx.pause_render = False
        else:
            bpy.context.window_manager.dmx.pause_render = True


#
# Hot-Reload
#


def clean_module_imports():
    modules = dict(sys.modules)
    for name in modules.keys():
        if name == __name__:
            continue
        if name.startswith(__name__):
            del sys.modules[name]
    return None


#
# Blender Add-On
#


def onRegister():
    onLoadFile(None)


def register():
    # Register Base Classes

    in_out_mvr.register()
    in_gdtf.register()

    for cls in DMX.classes_base:
        bpy.utils.register_class(cls)

    # Register addon main class
    bpy.utils.register_class(DMX)
    bpy.types.Scene.dmx = PointerProperty(type=DMX)


    for cls in Profiles.classes:
        bpy.utils.register_class(cls)

    bpy.utils.register_class(DMX_TempData)
    bpy.types.WindowManager.dmx = PointerProperty(type=DMX_TempData)

    # Append handlers
    bpy.app.handlers.load_post.append(onLoadFile)
    bpy.app.handlers.undo_post.append(onUndo)

    Timer(1, onRegister, ()).start()


def unregister():
    # Stop ArtNet
    DMX_ArtNet.disable()
    DMX_sACN.disable()
    DMX_OSC.disable()
    DMX_MVR_X_Client.disable()
    DMX_MVR_X_Server.disable()
    DMX_Zeroconf.close()

    try:
        in_out_mvr.unregister()
        in_gdtf.unregister()
    except Exception as e:
        print("INFO", e)


    for cls in Profiles.classes:
        try:
            bpy.utils.unregister_class(cls)
        except Exception as e:
            print("INFO", e)


    # Unregister Base Classes
    for cls in DMX.classes_base:
        try:
            bpy.utils.unregister_class(cls)
        except Exception as e:
            print("INFO", e)


    # Unregister addon main class
    bpy.utils.unregister_class(DMX_TempData)
    bpy.utils.unregister_class(DMX)


    # Append handlers
    bpy.app.handlers.load_post.clear()
    bpy.app.handlers.undo_post.clear()

    clean_module_imports()

if __name__ == "__main__":
    register()
