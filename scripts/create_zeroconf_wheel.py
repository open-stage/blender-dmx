# Copyright (C) 2024 vanous
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
import pathlib
import shutil

import pygit2
from pip._internal.cli.main import main as pip_main

try:
    pygit2.clone_repository(
        "https://github.com/python-zeroconf/python-zeroconf.git", "zeroconf"
    )
except Exception as e:
    print("INFO", e)

for p in pathlib.Path("./zeroconf").rglob("**/*"):
    if p.suffix in {".c", ".pxd"}:
        p.unlink()

shutil.copyfile("zeroconf-README.rst", "zeroconf/README.rst")
shutil.copyfile("zeroconf-pyproject.toml", "zeroconf/pyproject.toml")

folder_path = os.path.dirname(os.path.realpath(__file__))
zeroconf_dir = os.path.join(folder_path, "zeroconf")
os.chdir(zeroconf_dir)

pip_main(["wheel", "."])
