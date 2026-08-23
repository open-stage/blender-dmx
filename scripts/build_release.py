# Copyright (C) 2023 Hugo Aboud, vanous
#
# This file is part of BlenderDMX.
#
# BlenderDMX is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# BlenderDMX is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <https://www.gnu.org/licenses/>.

import os
import re
import shutil
import sys
from shutil import copytree, ignore_patterns

from pygit2 import Repository

BUILD_DIR = "build"


def read_version():
    line = ""
    with open("__init__.py", "r") as f:
        while True:
            data_line = f.readline().rstrip()
            if data_line.startswith("#"):
                continue
            line += data_line
            if "}" in line:
                break
    version_string = line.replace("bl_info = ", "")
    bl_info = eval(version_string)
    x, y, z = bl_info["version"]
    return f"{x}.{y}.{z}"


branch_name = Repository(".").head.shorthand
if branch_name is None:
    raise Exception("Run the script from the project root.")

set_version = read_version()
# branch_name = "release_v1.0.3"
branch_version = branch_name[9:]
print("INFO", branch_name)

release_name = branch_name
if re.match(r"^release_v\d+\.\d+\.\d+$", branch_name):
    print(
        "INFO",
        'Warning: This is not a release branch. The branch should be named "release_vX.Y.Z".',
    )
    release_name = branch_name[8:]


if set_version != branch_version:
    if len(sys.argv) > 1:  # any command line argument will do to skip version check
        print("INFO", "Continue for local testing")
    else:
        print(
            "INFO",
            f"Branch version {branch_version} and add-on version {set_version} do not match. Exit!",
        )
        sys.exit()

zip_name = "blenderDMX_" + release_name

print("INFO", "---------")
print("INFO", "branch name: " + branch_name)
print("INFO", "release name: " + release_name)
print("INFO", "zip name: " + zip_name + ".zip")
print("INFO", "---------")

print("INFO", "Resetting build directory...")
if os.path.exists(BUILD_DIR):
    shutil.rmtree(BUILD_DIR)
os.mkdir(BUILD_DIR)
os.mkdir(BUILD_DIR + "/dmx")

# List of files/directories to skip during copy
ignore = ignore_patterns(
    "*.pyc", "__pycache__", ".mypy_cache", ".pytest_cache", "data.json"
)

print("INFO", "Copying dependencies to build directory...")
copytree("assets", BUILD_DIR + "/dmx/assets", ignore=ignore)
copytree("io_scene_3ds", BUILD_DIR + "/dmx/io_scene_3ds", ignore=ignore)
copytree("panels", BUILD_DIR + "/dmx/panels", ignore=ignore)
copytree("pygdtf", BUILD_DIR + "/dmx/pygdtf", ignore=ignore)
copytree("pypsn", BUILD_DIR + "/dmx/pypsn", ignore=ignore)
copytree("pymvr", BUILD_DIR + "/dmx/pymvr", ignore=ignore)
copytree("sacn", BUILD_DIR + "/dmx/sacn", ignore=ignore)
copytree("ifaddr", BUILD_DIR + "/dmx/ifaddr", ignore=ignore)
copytree("oscpy", BUILD_DIR + "/dmx/oscpy", ignore=ignore)
copytree("share_api_client", BUILD_DIR + "/dmx/share_api_client", ignore=ignore)
copytree("mvrxchange", BUILD_DIR + "/dmx/mvrxchange", ignore=ignore)
copytree("zeroconf", BUILD_DIR + "/dmx/zeroconf", ignore=ignore)
copytree("async_timeout", BUILD_DIR + "/dmx/async_timeout", ignore=ignore)
copytree("preferences", BUILD_DIR + "/dmx/preferences", ignore=ignore)
copytree("i18n", BUILD_DIR + "/dmx/i18n", ignore=ignore)

print("INFO", "Copying source to build directory...")
for filename in os.listdir("."):
    if filename.endswith(".py"):
        shutil.copy2(filename, BUILD_DIR + "/dmx")

print("INFO", "Copying metadata to build directory...")
shutil.copy2("CHANGELOG.md", BUILD_DIR + "/dmx")
shutil.copy2("LICENSE", BUILD_DIR + "/dmx")
shutil.copy2("README.md", BUILD_DIR + "/dmx")

print("INFO", "Zipping release...")
shutil.make_archive(zip_name, "zip", BUILD_DIR)

if len(sys.argv) > 1:  # any command line argument will do to skip version check
    if sys.argv[1] == "github":
        print("INFO", "Keeping the build directory")
        sys.exit()

print("INFO", "Clearing build directory...")
shutil.rmtree(BUILD_DIR)

print("INFO", "Build successfull! Have a great release!")
