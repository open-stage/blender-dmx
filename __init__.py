bl_info = {
    'name': 'DMX',
    'description': 'DMX visualization and programming, with GDTF/MVR and Network support',
    'author': 'open-stage',
    'version': (2, 0, 0),
    'blender': (3, 0, 0),
    "location": "3D View > DMX",
    "warning": "", # used for warning icon and text in addons panel
    "wiki_url": "https://github.com/open-stage/blender-dmx/wiki",
    "doc_url": "https://github.com/open-stage/blender-dmx/wiki",
    "tracker_url": "https://github.com/open-stage/blender-dmx/issues",
    'category': 'Lighting'
}

import os
import sys
sys.path.append(os.path.dirname(__file__))

from threading import Timer

import bpy
from bpy.types import PropertyGroup
from bpy.props import PointerProperty

from src import core as Core
from src import patch as Patch
from src import devices as Devices
from src import programmer as Programmer
from src import preferences as Preferences


class DMX(PropertyGroup):

    core: PointerProperty(
        name = 'Core',
        type = Core.DMX_Core
    )

    patch: PointerProperty(
        name = 'Patch',
        type = Patch.DMX_Patch
    )

    devices: PointerProperty(
        name = 'Devices',
        type = Devices.DMX_Devices
    )

    programmer: PointerProperty(
        name = 'Patch',
        type = Programmer.DMX_Programmer
    )

class DMX_Non_Persistent_Data(PropertyGroup):

    imports: PointerProperty(
            name = "Imports",
            type=Devices.DMX_Devices_Share_Imports
            )

# Blender Add-on Registering

def on_register():
    Patch.DMX_Patch_Profile.load()
    Devices.DMX_Devices_Import_Gdtf_Profile.load()

def clean_module_imports():
    modules = dict(sys.modules)
    for name in modules.keys():
        if (name == __name__):
            continue
        if name.startswith('src'):
            del sys.modules[name]
    return None 

def register():
    for cls in Patch.classes:
        bpy.utils.register_class(cls)
    for cls in Devices.classes:
        bpy.utils.register_class(cls)
    for cls in Core.classes:
        bpy.utils.register_class(cls)
    for cls in Programmer.classes:
        bpy.utils.register_class(cls)
    for cls in Preferences.classes:
        bpy.utils.register_class(cls)
    
    bpy.utils.register_class(DMX)
    bpy.utils.register_class(DMX_Non_Persistent_Data)
    bpy.types.Scene.dmx = PointerProperty(type=DMX)
    bpy.types.WindowManager.dmx = PointerProperty(type=DMX_Non_Persistent_Data)
    
    Timer(1, on_register, ()).start()

def unregister():
    for cls in Patch.classes:
        bpy.utils.unregister_class(cls)
    for cls in Devices.classes:
        bpy.utils.unregister_class(cls)
    for cls in Core.classes:
        bpy.utils.unregister_class(cls)
    for cls in Programmer.classes:
        bpy.utils.unregister_class(cls)
    for cls in Preferences.classes:
        bpy.utils.unregister_class(cls)
    
    bpy.utils.unregister_class(DMX_Non_Persistent_Data)
    bpy.utils.unregister_class(DMX)

    clean_module_imports()

if __name__ == '__main__':

    register()
