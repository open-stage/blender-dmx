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

import glob
import importlib
import os
import shutil
import sys
import threading
from types import SimpleNamespace

import bpy
import requests

from .i18n import DMX_Lang

_ = DMX_Lang._


def get_version_json(url, callback, context):
    try:
        response = requests.get(url)
    except Exception as e:
        callback({"error": f"{e.__class__.__name__} {e}"}, context)
        return

    if response.ok:
        callback(response.json(), context)
    else:
        callback({"error": response.reason}, context)


def version_compare(current_version, new_version):
    cur_ver = current_version
    new_ver = new_version.split(".")
    n = max(len(cur_ver), len(new_ver))
    for i in range(n):
        cur_ver_num = int(cur_ver[i]) if i < len(cur_ver) else 0
        new_ver_num = int(new_ver[i]) if i < len(new_ver) else 0
        if cur_ver_num > new_ver_num:
            return 1
        elif cur_ver_num < new_ver_num:
            return -1
    return 0


def export_custom_data(directory_name, file_name):
    dmx = bpy.context.scene.dmx
    folder_path = dmx.get_addon_path()
    export_dir = os.path.join(folder_path, "export")
    export_filename = os.path.join(directory_name, file_name)

    if os.path.exists(export_dir):
        shutil.rmtree(export_dir)
    os.mkdir(export_dir)

    models_path = os.path.join(folder_path, "assets", "models")
    mvrs_path = os.path.join(folder_path, "assets", "mvrs")
    profiles_path = os.path.join(folder_path, "assets", "profiles")

    # do not export (and import) BlenderDMX profiles as they might be improved in the future
    # and this would prevent that
    ignore = shutil.ignore_patterns("BlenderDMX*")

    try:
        shutil.copytree(models_path, os.path.join(export_dir, "models"))
        if os.path.exists(mvrs_path):
            shutil.copytree(mvrs_path, os.path.join(export_dir, "mvrs"))
        shutil.copytree(
            profiles_path, os.path.join(export_dir, "profiles"), ignore=ignore
        )
        shutil.make_archive(export_filename, "zip", export_dir)
        shutil.rmtree(export_dir)
    except Exception as e:
        return SimpleNamespace(ok=False, error=str(e))
    return SimpleNamespace(ok=True, error="")


def import_custom_data(directory_name, file_name):
    import_filename = os.path.join(directory_name, file_name)
    dmx = bpy.context.scene.dmx
    folder_path = dmx.get_addon_path()
    import_dir = os.path.join(folder_path, "assets")
    if not os.path.exists(import_filename):
        return SimpleNamespace(ok=False, error=_("File doesn't exist"))

    try:
        shutil.unpack_archive(import_filename, import_dir)
    except Exception as e:
        return SimpleNamespace(ok=False, error=str(e))
    return SimpleNamespace(ok=True, error="")


def clear_custom_data():
    dmx = bpy.context.scene.dmx
    folder_path = dmx.get_addon_path()

    models_path = os.path.join(folder_path, "assets", "models", "*")
    mvrs_path = os.path.join(folder_path, "assets", "mvrs", "*")
    profiles_path = os.path.join(folder_path, "assets", "profiles", "*")

    rm_dirs = [
        (models_path, "models"),
        (mvrs_path, "mvrs"),
        (profiles_path, "profiles"),
    ]

    try:
        for rm_dir, name in rm_dirs:
            for file in glob.glob(rm_dir):
                if name == "profiles":
                    if "BlenderDMX" in file and file.endswith(".gdtf"):
                        continue
                if os.path.isdir(file):
                    shutil.rmtree(file)
                    continue
                if os.path.isfile(file):
                    os.remove(file)
    except Exception as e:
        return SimpleNamespace(ok=False, error=str(e))
    return SimpleNamespace(ok=True, error="")


def copy_custom_data():
    dmx = bpy.context.scene.dmx
    folder_path = dmx.get_addon_path()
    addon_path = os.path.dirname(os.path.realpath(__file__))

    models_path_new = os.path.join(folder_path, "assets", "models")
    mvrs_path_new = os.path.join(folder_path, "assets", "mvrs")
    profiles_path_new = os.path.join(folder_path, "assets", "profiles")

    models_path_old = os.path.join(addon_path, "assets", "models")
    mvrs_path_old = os.path.join(addon_path, "assets", "mvrs")
    profiles_path_old = os.path.join(addon_path, "assets", "profiles")

    try:
        if os.path.exists(models_path_old):
            shutil.copytree(models_path_old, models_path_new, dirs_exist_ok=True)
        if os.path.exists(mvrs_path_old):
            shutil.copytree(mvrs_path_old, mvrs_path_new, dirs_exist_ok=True)
        if os.path.exists(profiles_path_old):
            shutil.copytree(profiles_path_old, profiles_path_new, dirs_exist_ok=True)
    except Exception as e:
        return SimpleNamespace(ok=False, error=str(e))
    return SimpleNamespace(ok=True, error="")


def old_custom_data_exists():
    addon_path = os.path.dirname(os.path.realpath(__file__))

    models_path_old = os.path.join(addon_path, "assets", "models")
    if os.path.exists(models_path_old):
        return len(glob.glob(os.path.join(models_path_old, "*"))) > 0

    return False


def copy_blender_profiles():
    dmx = bpy.context.scene.dmx
    folder_path = dmx.get_addon_path()
    addon_path = os.path.dirname(os.path.realpath(__file__))

    profiles_path_user = os.path.join(folder_path, "assets", "profiles")
    profiles_path_addon = os.path.join(addon_path, "assets", "profiles", "*")

    for file in glob.glob(profiles_path_addon):
        if os.path.isfile(file):
            if "BlenderDMX" in file and file.endswith(".gdtf"):
                dest_path = os.path.join(profiles_path_user, os.path.basename(file))
                if not os.path.exists(dest_path):
                    shutil.copy(file, profiles_path_user)


def reload_addon():
    try:
        module = sys.modules.get(__package__)
        if not module:
            raise Exception("DMX module could not be loaded")
        module.unregister()
        importlib.reload(module)
        module.register()
    except Exception as e:
        return SimpleNamespace(ok=False, error=str(e))
    return SimpleNamespace(ok=True, error="")


def get_extension_manifest():
    import toml

    folder_path = os.path.dirname(os.path.realpath(__file__))
    toml_path = os.path.join(folder_path, "blender_manifest.toml")
    data = toml.load(toml_path)
    return data


def get_application_version():
    if bpy.app.version >= (4, 2):
        data = get_extension_manifest()
        version = data["version"]
        return tuple(version.split("."))
    else:
        from . import bl_info as application_info

        return application_info["version"]
