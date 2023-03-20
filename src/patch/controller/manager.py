from lib import share_api_client
from src import patch as Patch
import bpy
from src.lang import DMX_Lang
_ = DMX_Lang._

class DMX_Patch_Manager:

    # Source Management

    def configure_source(self):
        print('Configuring source...')

    # Universe Management

    def add_universe(self):
        self.universes.add()
        self.universes[-1].name = f'Universe {len(self.universes)}'
        for i, universe in enumerate(self.universes):
            universe.number = i+1

    def remove_universe(self, index: int):
        self.universes.remove(index)
        for i, universe in enumerate(self.universes):
            universe.number = i+1

    # Fixture Management

    def new_fixture_id(self):
        if (len(self.fixtures) == 0):
            return 1
        return max([f.id for f in self.fixtures]) + 1

    def add_fixture(self):
        fixtures = self.fixtures
        fixtures.add()
        fixtures[-1].id = self.new_fixture_id()

    def add_fixture_batch(self):
        pass

    def remove_fixture(self, index):
        self.fixtures.remove(index)

    # Fixture Import

    def import_from_share(self, index: int):
        result = share_api_client.download_files([self.share_profiles[index]])
        print(result)
        Patch.DMX_Patch_Profile.load()
        if result.status:
            ShowMessageBox(_("File downloaded correctly. Status code was: {}").format(result.result.status_code), _("GDTF file downloaded"), 'INFO')
        else:
            ShowMessageBox(_("Error downloading GDTF file. Error code was: {}").format(result.result.status_code), _("GDTF Share download error"), 'ERROR')

    def update_share_index(self):
        result = share_api_client.update_data()
        print(result)
        if result.status:
            ShowMessageBox(_("Share index updated. Status code was: {}").format(result.result.status_code), _("GDTF Share updated"), 'INFO')
        else:
            ShowMessageBox(_("Error while updating Share index. Error code was: {}").format(result.result.status_code), _("GDTF Share update error"), 'ERROR')
        Patch.DMX_Patch_Import_Gdtf_Profile.load()

    def save_api_key(self):
        config = share_api_client.get_config()
        key = bpy.context.window_manager.dmx.get("share_api_key", None)
        if key is not None:
            config["api_key"] = key
        share_api_client.set_config(config)

    def load_api_key(self):
        config = share_api_client.get_config()
        key = config["api_key"]
        if key is not None:
            bpy.context.window_manager.dmx.share_api_key = key
        
def ShowMessageBox(message = "", title = _("Message Box"), icon = 'INFO'):

    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

