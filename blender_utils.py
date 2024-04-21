import threading
import requests
import shutil
import os
from types import SimpleNamespace

from dmx.i18n import DMX_Lang
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


def get_latest_release(callback, context):
    url = "https://api.github.com/repos/open-stage/blender-dmx/releases/latest"
    thread = threading.Thread(target=get_version_json, args=(url, callback, context))
    thread.start()
    thread.join()


def export_custom_data(directory_name, file_name):
    folder_path = os.path.dirname(os.path.realpath(__file__))
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
        shutil.copytree(models_path, os.path.join(export_dir,"models"))
        shutil.copytree(mvrs_path, os.path.join(export_dir,"mvrs"))
        shutil.copytree(profiles_path, os.path.join(export_dir,"profiles"), ignore=ignore)
        shutil.make_archive(export_filename, "zip", export_dir)
        shutil.rmtree(export_dir)
    except Exception as e:
        return SimpleNamespace(ok=False, error = str(e))
    return SimpleNamespace(ok=True, error = "")

def import_custom_data(directory_name, file_name):
    import_filename = os.path.join(directory_name, file_name)
    folder_path = os.path.dirname(os.path.realpath(__file__))
    import_dir = os.path.join(folder_path, "assets")
    if not os.path.exists(import_filename):
        return SimpleNamespace(ok=False, error = _("File doesn't exist"))

    try:
        shutil.unpack_archive(import_filename, import_dir)
    except Exception as e:
        return SimpleNamespace(ok=False, error = str(e))
    return SimpleNamespace(ok=True, error = "")