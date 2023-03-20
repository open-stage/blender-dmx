bl_info = {
    'name': 'DMX',
    'description': 'DMX visualization and programming, with Network support',
    'author': 'open-stage',
    'version': (1, 5, 0),
    'blender': (3, 0, 0),
    'location': '',
    'warning': '', # used for warning icon and text in addons panel
    'wiki_url': 'http://www.github.com/open-stage/blenderDMX/wiki',
    'tracker_url': '',
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
from src import programmer as Programmer

# Main Data Structure

class DMX(PropertyGroup):

    core: PointerProperty(
        name = 'Core',
        type = Core.DMX_Core
    )

    patch: PointerProperty(
        name = 'Patch',
        type = Patch.DMX_Patch
    )

    programmer: PointerProperty(
        name = 'Patch',
        type = Programmer.DMX_Programmer
    )


# Add-on Registering

def on_register():
    Patch.DMX_Patch_Profile.load()
    Patch.DMX_Patch_Import_Gdtf_Profile.load()
    # load the Share API key
    bpy.context.scene.dmx.patch.load_api_key()

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
    for cls in Core.classes:
        bpy.utils.register_class(cls)
    for cls in Programmer.classes:
        bpy.utils.register_class(cls)
    
    bpy.utils.register_class(DMX)
    bpy.types.Scene.dmx = PointerProperty(type=DMX)
    # private data, not to be saved to the blender file:
    bpy.types.WindowManager.dmx = PointerProperty(type=Patch.DMX_PatchPrivateData)
    
    Timer(1, on_register, ()).start()

def unregister():
    for cls in Patch.classes:
        bpy.utils.unregister_class(cls)
    for cls in Core.classes:
        bpy.utils.unregister_class(cls)
    for cls in Programmer.classes:
        bpy.utils.unregister_class(cls)
    
    bpy.utils.unregister_class(DMX)

    clean_module_imports()

if __name__ == '__main__':
    register()
