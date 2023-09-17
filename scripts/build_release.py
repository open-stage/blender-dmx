import re
import os
import shutil
from shutil import copytree, ignore_patterns
from pygit2 import Repository

BUILD_DIR = "build"

branch_name = Repository(".").head.shorthand
if branch_name == None:
    raise Exception("Run the script from the project root.")

branch_name = "release_v1.0.1"

release_name = branch_name
if re.match(r"^release_v\d+\.\d+\.\d+$", branch_name):
    print(
        'Warning: This is not a release branch. The branch should be named "release_vX.Y.Z".'
    )
    release_name = branch_name[8:]

zip_name = "blenderDMX_" + release_name

print("---------")
print("branch name: " + branch_name)
print("release name: " + release_name)
print("zip name: " + zip_name + ".zip")
print("---------")

print("Resetting build directory...")
if os.path.exists(BUILD_DIR):
    shutil.rmtree(BUILD_DIR)
os.mkdir(BUILD_DIR)
os.mkdir(BUILD_DIR + "/dmx")

# List of files/directories to skip during copy
ignore = ignore_patterns("*.pyc", "__pycache__", ".mypy_cache", ".pytest_cache")

print("Copying dependencies to build directory...")
copytree("assets", BUILD_DIR + "/dmx/assets", ignore=ignore)
copytree("io_scene_3ds", BUILD_DIR + "/dmx/io_scene_3ds", ignore=ignore)
copytree("panels", BUILD_DIR + "/dmx/panels", ignore=ignore)
copytree("pygdtf", BUILD_DIR + "/dmx/pygdtf", ignore=ignore)
copytree("pymvr", BUILD_DIR + "/dmx/pymvr", ignore=ignore)
copytree("sacn", BUILD_DIR + "/dmx/sacn", ignore=ignore)

print("Copying source to build directory...")
for filename in os.listdir("."):
    if filename.endswith(".py"):
        shutil.copy2(filename, BUILD_DIR + "/dmx")

print("Copying metadata to build directory...")
shutil.copy2("CHANGELOG.md", BUILD_DIR + "/dmx")
shutil.copy2("LICENSE", BUILD_DIR + "/dmx")

print("Zipping release...")
shutil.make_archive(zip_name, "zip", BUILD_DIR)

print("Clearing build directory...")
shutil.rmtree(BUILD_DIR)

print("Build successfull! Have a great release!")
