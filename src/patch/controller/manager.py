import bpy
from i18n import DMX_Lang
import queue


execution_queue = queue.Queue()
_ = DMX_Lang._


class DMX_Patch_Manager:
    # Source Management

    def configure_source(self):
        print("Configuring source...")

    # Universe Management

    def add_universe(self):
        self.universes.add()
        self.universes[-1].name = f"Universe {len(self.universes)}"
        for i, universe in enumerate(self.universes):
            universe.number = i + 1

    def remove_universe(self, index: int):
        self.universes.remove(index)
        for i, universe in enumerate(self.universes):
            universe.number = i + 1

    # Fixture Management

    def new_fixture_id(self):
        if len(self.fixtures) == 0:
            return 1
        return max([f.id for f in self.fixtures]) + 1

    def add_fixture(self):
        self.fixtures.add()
        self.fixtures[-1].id = self.new_fixture_id()

    def add_fixture_batch(self):
        self.fixture_batches.add()
        self.fixtures.add()
        self.fixtures[-1].id = self.new_fixture_id()
        self.fixtures[-1].batch = len(self.fixture_batches)-1
        self.fixtures[-1].batch_index = 0

    def remove_fixture(self, index):
        self.fixtures.remove(index)
