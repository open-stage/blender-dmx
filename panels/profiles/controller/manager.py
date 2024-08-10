#    Copyright vanous
#
#    This file is part of BlenderDMX.
#
#    BlenderDMX is free software: you can redistribute it and/or modify it
#    under the terms of the GNU General Public License as published by the Free
#    Software Foundation, either version 3 of the License, or (at your option)
#    any later version.
#
#    BlenderDMX is distributed in the hope that it will be useful, but WITHOUT
#    ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
#    FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
#    more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program. If not, see <https://www.gnu.org/licenses/>.

from .... import share_api_client as share_api_client
from ....gdtf import DMX_GDTF
import bpy
import os
import queue

from ....panels import profiles as Profiles
from .... import __package__ as base_package

execution_queue = queue.Queue()

from ....i18n import DMX_Lang

_ = DMX_Lang._


class DMX_Fixtures_Manager:
    # Source Management

    # Fixture delete

    def delete_local_fixture(self, index: int):
        dmx = bpy.context.scene.dmx
        dir_path = dmx.get_addon_path()
        profiles = bpy.context.window_manager.dmx.imports.local_profiles
        profile = profiles[index]
        filename = profile.filename
        file_path = os.path.join(dir_path, "assets", "profiles", filename)
        os.remove(file_path)
        DMX_GDTF.getManufacturerList()
        Profiles.DMX_Fixtures_Local_Profile.loadLocal()

    # Fixture Import

    def import_from_share(self, index: int):
        prefs = bpy.context.preferences.addons[base_package].preferences
        api_username = prefs.get("share_api_username", None)
        api_password = prefs.get("share_api_password", None)
        imports = bpy.context.window_manager.dmx.imports
        dmx = bpy.context.scene.dmx
        ADDON_PATH = dmx.get_addon_path()
        data_file = os.path.join(ADDON_PATH, "data.json")

        if api_username is None or len(api_username) < 2 or api_password is None or len(api_password) < 2:
            ShowMessageBox(
                _("Get GDTF Share account and fill it into BlenderDMX addon preferences."),
                _("GDTF Share API credentials missing"),
                "ERROR",
            )
            return
        dmx = bpy.context.scene.dmx
        dir_path = dmx.get_addon_path()
        file_path = os.path.join(dir_path, "assets", "profiles")

        if not bpy.app.timers.is_registered(execute_queued_functions):
            bpy.app.timers.register(execute_queued_functions)

        timer_subscribers.append("download file")

        share_api_client.download_files(
            api_username,
            api_password,
            file_path,
            [imports.share_profiles[index]],
            queue_up,
            reload_local_profiles,
            data_file,
        )

        ShowMessageBox(
            _("Downloading {}").format(imports.share_profiles[index]["fixture"]),
            _("GDTF Share Download"),
            "INFO",
        )

    def update_share_index(self):
        prefs = bpy.context.preferences.addons[base_package].preferences
        api_username = prefs.get("share_api_username", None)
        api_password = prefs.get("share_api_password", None)
        dmx = bpy.context.scene.dmx
        ADDON_PATH = dmx.get_addon_path()
        data_file = os.path.join(ADDON_PATH, "data.json")
        if api_username is None or len(api_username) < 2 or api_password is None or len(api_password) < 2:
            ShowMessageBox(
                _("Get GDTF Share account and fill it into BlenderDMX addon preferences."),
                _("GDTF Share API credentials missing"),
                "ERROR",
            )
            return

        if not bpy.app.timers.is_registered(execute_queued_functions):
            bpy.app.timers.register(execute_queued_functions)
        timer_subscribers.append("update index")
        share_api_client.update_data(api_username, api_password, queue_up, reload_share_profiles, data_file)


timer_subscribers = []


def queue_up(function, arg):
    execution_queue.put((function, arg))


def execute_queued_functions():
    print("INFO", "check")
    while not execution_queue.empty():
        items = execution_queue.get()
        execute = items[0]
        arg = items[1]
        execute(arg)
        if len(timer_subscribers) > 0:
            timer_subscribers.pop()
        if len(timer_subscribers) < 1 and execution_queue.empty() and bpy.app.timers.is_registered(execute_queued_functions):
            bpy.app.timers.unregister(execute_queued_functions)

    return 1.0


def reload_share_profiles(result):
    if result.status:
        ShowMessageBox(
            _("Share index updated. Status code was: {}").format(result.result.status_code),
            _("GDTF Share updated"),
            "INFO",
        )
    else:
        ShowMessageBox(
            _("Error while updating Share index. Error code was: {}").format(result.result.status_code),
            _("GDTF Share update error"),
            "ERROR",
        )
    Profiles.DMX_Fixtures_Import_Gdtf_Profile.loadShare()


def reload_local_profiles(result):
    DMX_GDTF.getManufacturerList()
    Profiles.DMX_Fixtures_Local_Profile.loadLocal()
    if result.status:
        ShowMessageBox(
            _("File downloaded correctly. Status code was: {}").format(result.result.status_code),
            _("GDTF file downloaded"),
            "INFO",
        )
    else:
        ShowMessageBox(
            _("Error downloading GDTF file. Error code was: {}").format(result.result.status_code),
            _("GDTF Share download error"),
            "ERROR",
        )


def ShowMessageBox(message="", title="Message Box", icon="INFO"):
    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)
