# run this way:
# blender --background --python ./test_fixture_patching.py

import os
from types import SimpleNamespace as SN

import bpy
from mathutils import Vector

addon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
os.chdir(addon_path)
profiles_path = os.path.join(addon_path, "assets", "profiles")

bpy.context.scene.dmx.new()
# from dmx.gdtf import DMX_GDTF
from dmx.scripts.get_testing_gdtfs import fixture_files

# fixture_files = [SN(name="")]

test_only = [
    "Cameo@Evos_W7@Firmware-1.4_GDTF-1.2.gdtf",
    "Ayrton@Argo_6_FX@V1.1_First_Release.gdtf",
]
test_only = []


def process_children(o):
    for obj in o:
        print(obj.name, obj.dimensions)
        process_children(obj.children)


for fixture_file in fixture_files:
    print("Adding", fixture_file.name)
    f = bpy.context.scene.dmx.fixtures.add()
    f.build(f"test", fixture_file.name, "default", 1, 1, (0, 0, 0), True, True)
    for obj in f.objects:
        print(obj.name, obj.object.dimensions)
        process_children(obj.object.children)

        # if "dimensions" in list(fixture_file.__dict__):
        #    assert obj.object.dimensions == Vector(fixture_file.dimensions), "Dimensions not matching"
