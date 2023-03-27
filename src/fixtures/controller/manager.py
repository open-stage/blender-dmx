from lib import share_api_client
from src import patch as Patch
from src import fixtures as Fixtures
import bpy
import os
import pathlib
from src.lang import DMX_Lang
import queue


execution_queue = queue.Queue()
_ = DMX_Lang._


class DMX_Fixtures_Manager:
    # Source Management

    # Fixture delete

    def delete_local_fixture(self, index: int):
        dir_path = os.path.dirname(os.path.abspath(__file__))
        profiles = bpy.context.scene.dmx.patch.profiles
        profile = profiles[index]
        filename = profile.filename
        file_path = os.path.join(
            dir_path, "..", "..", "..", "assets", "profiles", filename
        )
        os.remove(file_path)
        Patch.DMX_Patch_Profile.load()

    # Fixture Import

    def import_from_share(self, index: int):
        addon_name = pathlib.Path(__file__).parent.parts[-4]
        prefs = bpy.context.preferences.addons[addon_name].preferences
        api_key = prefs.get("share_api_key", None)
        imports = bpy.context.window_manager.dmx.imports

        if api_key is None or len(api_key) < 2:
            ShowMessageBox(
                _(
                    "Get API key from GDTF Share account and fill it into BlenderDMX addon preferences."
                ),
                _("GDTF Share API key missing"),
                "ERROR",
            )
            return
        dir_path = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(dir_path, "..", "..", "..", "assets", "profiles")

        if not bpy.app.timers.is_registered(execute_queued_functions):
            bpy.app.timers.register(execute_queued_functions)

        timer_subscribers.append("download file")

        share_api_client.download_files(
            api_key,
            file_path,
            [imports.share_profiles[index]],
            queue_up,
            reload_local_profiles,
        )

    def update_share_index(self):
        addon_name = pathlib.Path(__file__).parent.parts[-4]
        prefs = bpy.context.preferences.addons[addon_name].preferences
        api_key = prefs.get("share_api_key", None)
        if api_key is None or len(api_key) < 2:
            ShowMessageBox(
                _(
                    "Get API key from GDTF Share account and fill it into BlenderDMX addon preferences."
                ),
                _("GDTF Share API key missing"),
                "ERROR",
            )
            return

        if not bpy.app.timers.is_registered(execute_queued_functions):
            bpy.app.timers.register(execute_queued_functions)
        timer_subscribers.append("update index")
        share_api_client.update_data(api_key, queue_up, reload_share_profiles)


timer_subscribers = []


def queue_up(function, arg):
    execution_queue.put((function, arg))


def execute_queued_functions():
    print("check")
    while not execution_queue.empty():
        items = execution_queue.get()
        execute = items[0]
        arg = items[1]
        execute(arg)
        if len(timer_subscribers) > 0:
            timer_subscribers.pop()
        if (
            len(timer_subscribers) < 1
            and execution_queue.empty()
            and bpy.app.timers.is_registered(execute_queued_functions)
        ):
            bpy.app.timers.unregister(execute_queued_functions)

    return 1.0


def reload_share_profiles(result):
    print("loading profiles")
    print(result)
    if result.status:
        ShowMessageBox(
            _("Share index updated. Status code was: {}").format(
                result.result.status_code
            ),
            _("GDTF Share updated"),
            "INFO",
        )
    else:
        ShowMessageBox(
            _("Error while updating Share index. Error code was: {}").format(
                result.result.status_code
            ),
            _("GDTF Share update error"),
            "ERROR",
        )
    Fixtures.DMX_Fixtures_Import_Gdtf_Profile.load()


def reload_local_profiles(result):
    print(result)
    Patch.DMX_Patch_Profile.load()
    if result.status:
        ShowMessageBox(
            _("File downloaded correctly. Status code was: {}").format(
                result.result.status_code
            ),
            _("GDTF file downloaded"),
            "INFO",
        )
    else:
        ShowMessageBox(
            _("Error downloading GDTF file. Error code was: {}").format(
                result.result.status_code
            ),
            _("GDTF Share download error"),
            "ERROR",
        )


def ShowMessageBox(message="", title=_("Message Box"), icon="INFO"):
    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)
