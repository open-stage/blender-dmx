import os
import pygit2
import pathlib
import shutil
from pip._internal.cli.main import main as pip_main

try:
    pygit2.clone_repository("https://github.com/python-zeroconf/python-zeroconf.git", "zeroconf")
except Exception as e:
    print(e)

for p in pathlib.Path("./zeroconf").rglob("**/*"):
    if p.suffix in {".c", ".pxd"}:
        p.unlink()

shutil.copyfile("zeroconf-README.rst", "zeroconf/README.rst")
shutil.copyfile("zeroconf-pyproject.toml", "zeroconf/pyproject.toml")

folder_path = os.path.dirname(os.path.realpath(__file__))
zeroconf_dir = os.path.join(folder_path, "zeroconf")
os.chdir(zeroconf_dir)

pip_main(["wheel", "."])
