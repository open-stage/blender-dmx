import threading
import requests


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
