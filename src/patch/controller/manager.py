from lib import share_api_client
from src import patch as Patch
import bpy

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
        ShowMessageBox(f"File downloaded with status code {result.result.status_code}", "GDTF Share download status", 'INFO')

    def update_share_index(self):
        result = share_api_client.update_data()
        print(result)
        ShowMessageBox(f"Share index updated with status code {result.result.status_code}", "GDTF Share update status", 'INFO')
        Patch.DMX_Patch_Import_Gdtf_Profile.load()


def ShowMessageBox(message = "", title = "Message Box", icon = 'INFO'):

    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

