# Copyright (C) 2023 vanous
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

import json
import os
from threading import Thread

import requests


class Result:
    status = None
    result = None

    def __init__(self, status, result):
        self.status = status
        self.result = result


class GdtfShareApi:
    base_url = "https://gdtf-share.com/apis/public"
    api_username = ""
    api_password = ""
    verbose = True
    dir_path = os.path.dirname(os.path.abspath(__file__))
    data_file = os.path.join(dir_path, "data.json")

    def __init__(self, api_username, api_password: str, data_file=None):
        self.api_username = api_username
        self.api_password = api_password
        if data_file is not None:
            self.data_file = data_file
        self.session = requests.Session()

    def save_json_file(self, data, fname):
        with open(fname, "w") as a:
            json.dump(data, a)

    def load_json_file(self, fname):
        try:
            with open(fname, "r") as a:
                return json.load(a)
        except Exception:
            return None

    def make_call(self, slug=None, url_params="", method="GET", data={}):
        url = "%s/%s?%s" % (self.base_url, slug, url_params)
        if self.verbose:
            print("INFO", url)
        if method == "GET":
            # res = self.session.get(url, verify=False)
            res = self.session.get(url)
        else:
            res = self.session.post(url, data=data)

        if res.status_code == 200:
            return Result(True, res)
        else:
            return Result(False, res)

    def get_list(self):
        result = self.make_call(method="GET", slug="getList.php")
        print("INFO", "result status", result, result.status)
        if result.status:
            self.data = result.result.json()
            self.save_json_file(self.data.get("list", []), self.data_file)
            self.data = self.data.get("list", [])
            return result
        return result

    def login(self):
        data = {"user": self.api_username, "password": self.api_password}
        return self.make_call(method="POST", slug="login.php", data=data)

    def get_gdtf_files(self, data, file_path):
        for fixture in data:
            if self.verbose:
                print(
                    "INFO",
                    fixture.get("fixture"),
                    fixture.get("manufacturer"),
                    fixture.get("rid"),
                )
            filename = f"{fixture.get('manufacturer').replace(' ', '_').replace('/', '_')}@{fixture.get('fixture').replace(' ', '_').replace('/', '_')}@{fixture.get('revision').replace(' ', '_').replace('/', '_')}.gdtf"

            res = self.make_call(
                slug="downloadFile.php", url_params=f"rid={fixture.get('rid')}"
            )
            with open(os.path.join(file_path, filename), "wb") as out:
                out.write(res.result.content)
                print("INFO", f"saved {filename}")
        return res


def _update_data(api_username, api_password: str, update, function, data_file=None):
    """Updates data.json."""
    gs = GdtfShareApi(api_username, api_password, data_file)
    gs.login()
    result = gs.get_list()
    update(function, result)


def update_data(api_username, api_password: str, update, function, data_file):
    thread = Thread(
        target=_update_data,
        args=(api_username, api_password, update, function, data_file),
    )
    thread.start()


def _download_files(
    api_username, api_password: str, file_path: str, files, update, function, data_file
):
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
    gs = GdtfShareApi(api_username, api_password, data_file)
    gs.login()
    result = gs.get_gdtf_files(files, file_path)
    update(function, result)


def download_files(
    api_username, api_password: str, file_path: str, files, update, function, data_file
):
    thread = Thread(
        target=_download_files,
        args=(
            api_username,
            api_password,
            file_path,
            files,
            update,
            function,
            data_file,
        ),
    )
    thread.start()
