#! /bin/env python3

import requests
import json
import os
from threading import Thread


class Result:
    status = None
    result = None

    def __init__(self, status, result):
        self.status = status
        self.result = result


class GdtfShareApi:
    base_url = "https://gdtf-share.com/apis/public"
    api_key = ""
    verbose = True
    dir_path = os.path.dirname(os.path.abspath(__file__))
    data_file = os.path.join(dir_path, "data.json")

    def __init__(self, api_key: str):
        saved_config = self.load_config()
        self.config = {}
        self.api_key = api_key
        self.config["hash"] = saved_config.get("hash", None)
        self.session = requests.Session()

    def load_config(self):
        dir_path = os.path.dirname(os.path.abspath(__file__))
        fname = os.path.join(dir_path, "config.json")
        if os.path.isfile(fname):
            with open(fname) as a:
                return json.load(a)
        return {
            "hash": None,
        }

    def store_config(self):
        dir_path = os.path.dirname(os.path.abspath(__file__))
        fname = os.path.join(dir_path, "config.json")
        with open(fname, "w") as a:
            json.dump(self.config, a)

    def save_json_file(self, data, fname):
        with open(fname, "w") as a:
            json.dump(data, a)

    def load_json_file(self, fname):
        try:
            with open(fname, "r") as a:
                return json.load(a)
        except:
            return None

    def make_call(self, slug=None, url_params="", method="GET"):
        url = "%s/%s?%s" % (self.base_url, slug, url_params)
        if self.verbose:
            print(url)
        if method == "GET":
            # res = self.session.get(url, verify=False)
            res = self.session.get(url)
        else:
            res = self.session.post(url)

        if res.status_code == 200:
            return Result(True, res)
        else:
            return Result(False, res)

    def start(self):
        result = self.make_call(method="GET", slug="getDiff.php", url_params=f"all")
        print("result status", result, result.status)
        if result.status:
            self.data = result.result.json()
            self.config["hash"] = self.data.get("hash", None)
            self.store_config()
            self.save_json_file(self.data.get("list", []), self.data_file)
            self.data = self.data.get("list", [])
            return result
        return result

    def update(self):
        if self.verbose:
            print(f"Updating since: {self.config['hash']}")
        result = self.make_call(
            method="GET", slug="getDiff.php", url_params=f"hash={self.config['hash']}"
        )
        print("result status", result.status)
        if result.status:
            self.data = result.result.json()
            self.config["hash"] = self.data.get("hash", None)
            if self.verbose:
                print(f"new hash: {self.config['hash']}")
            self.data = self.data.get("list", [])
            self.patch_data()
            return result
        else:
            # if update doesn't work (server error), retry from the beginning
            print("Update failed, try full reload")
            result = gs.start()
        return result

    def login(self):
        return self.make_call(
            method="GET", slug="login.php", url_params=f"seed={self.api_key}"
        )

    def get_gdtf_files(self, data, file_path):
        for fixture in data:
            if self.verbose:
                print(
                    fixture.get("fixture"),
                    fixture.get("manufacturer"),
                    fixture.get("rid"),
                )
            filename = f"{fixture.get('manufacturer').replace(' ','_')}@{fixture.get('fixture').replace(' ','_')}@{fixture.get('revision').replace(' ','_')}.gdtf"

            res = self.make_call(
                slug="downloadFile.php", url_params=f"rid={fixture.get('rid')}"
            )
            with open(os.path.join(file_path, filename), "wb") as out:
                out.write(res.result.content)
                print(f"saved {filename}")
        return res

    def patch_data(self):
        all_fixtures = self.load_json_file(self.data_file)
        updated_fixtures = self.data

        for updated_fixture in updated_fixtures:
            updated_status = updated_fixture.get("status", "")
            updated_rid = updated_fixture.get("rid", 0)
            updated_name = updated_fixture.get("fixture", "")
            original_fixture = next(
                (x for x in all_fixtures if x["rid"] == updated_rid), None
            )
            if updated_status == "deleted":
                print("removed", updated_name, updated_rid)
                if original_fixture in all_fixtures:
                    all_fixtures.remove(original_fixture)
                else:
                    print("not found")
            else:
                print("added/updated", updated_name, updated_rid)
                if original_fixture in all_fixtures:
                    all_fixtures.remove(original_fixture)
                else:
                    print("not found")
                all_fixtures.append(updated_fixture)

        self.save_json_file(all_fixtures, self.data_file)
        self.store_config()


def _update_data(api_key: str, update, function):
    """Updates data.json.
    When last timestamp of update exists, it updates from that date.
    If timestamp is missing, it requests full listing.
    If update since last timestamp fails, it requests full listing.
    """
    gs = GdtfShareApi(api_key)
    start = gs.load_json_file(gs.data_file)
    gs.login()
    if start is None or len(start) < 1:
        result = gs.start()
    elif gs.config["hash"] is None:
        result = gs.start()
    else:
        result = gs.update()
    update(function, result)


def update_data(api_key: str, update, function):
    thread = Thread(target=_update_data, args=(api_key, update, function))
    thread.start()

def _download_files(api_key: str, file_path: str, files, update, function):
    """Download GDTF files form GDTF Share.
    @files=[] is list of GDTF files as returned by the API itself,
    it must contain revision id (rid), name (fixture), manufacturer
    and revision (required to create file name).

      {
        "rid": int,
        "fixture": str,
        "manufacturer": str,
        "revision": str
      }
    """
    gs = GdtfShareApi(api_key)
    gs.login()
    result = gs.get_gdtf_files(files, file_path)
    update(function, result)


def download_files(api_key: str, file_path: str, files, update, function):
    thread = Thread(target=_download_files, args=(api_key, file_path, files, update, function))
    thread.start()
