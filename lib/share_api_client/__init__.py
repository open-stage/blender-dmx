#! /bin/env python3

import requests
import json
import os
import argparse

class Result:
    status = None
    result = None

    def __init__(self, status, result):
        self.status = status
        self.result = result


class GS:
    base_url = ""
    api_key = ""
    verbose = True

    dir_path = os.path.dirname(os.path.abspath(__file__))
    data_file = os.path.join(dir_path, "data.json")

    def __init__(self):
        saved_config = self.load_config()
        self.config = {}
        self.config["api_key"] = saved_config["api_key"]
        self.config["base_url"] = saved_config.get("base_url")
        self.config["hash"] = saved_config.get("hash", None)
        self.session = requests.Session()

    def load_config(self):
        dir_path = os.path.dirname(os.path.abspath(__file__))
        fname = os.path.join(dir_path, "config.json")
        if os.path.isfile(fname):
            with open(fname) as a:
                return json.load(a)
        return {
            "api_key": "",
            "base_url": "https://gdtf-share.com/apis/public",
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
        url = "%s/%s?%s" % (self.config["base_url"], slug, url_params)
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
        return result

    def login(self):
        return self.make_call(
            method="GET", slug="login.php", url_params=f"seed={self.config['api_key']}"
        )

    def get_gdtf_files(self, data):
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
            dir_path = os.path.dirname(os.path.abspath(__file__))
            full_path = os.path.join(dir_path,'..','..','assets','profiles')
            with open(os.path.join(full_path, filename), "wb") as out:
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

    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Work with GDTF Share API")
    parser.add_argument("-s", "--start", action="store_true", help="Resync from 0")
    parser.add_argument("-H", "--hash", dest="hash", help="Resync from a hash")
    parser.add_argument(
        "-t", "--timestamp", dest="timestamp", help="Resync from a timestamp"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_false", help="Print debug information"
    )
    args = parser.parse_args()
    gs = GS()
    gs.verbose = args.verbose
    start = gs.load_json_file(gs.data_file)
    gs.login()
    if args.start or start is None or len(start) < 1:
        ret = gs.start()
    elif gs.config["hash"] is None:
        ret = gs.start()
    else:
        ret = gs.update()

def update_data():
    gs = GS()
    start = gs.load_json_file(gs.data_file)
    gs.login()
    if start is None or len(start) < 1:
        ret = gs.start()
    elif gs.config["hash"] is None:
        ret = gs.start()
    else:
        ret = gs.update()
    return ret

def download_files(files = []):
    gs = GS()
    gs.login()
    res = gs.get_gdtf_files(files)
    return res
