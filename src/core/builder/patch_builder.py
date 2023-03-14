import bpy

from src.core import util
from .fixture_builder import DMX_FixtureBuilder

class DMX_PatchBuilder:


    def check_unique_fixture_ids(self):
        ids = []
        for fixture in self.patch.fixtures:
            if fixture.id in ids:
                raise Exception(f'Fixture ID {fixture.id} used in more than one Fixture.')
            ids.append(fixture.id)
    
    def check_unique_fixture_names(self):
        names = []
        for fixture in self.patch.fixtures:
            if fixture.name in names:
                raise Exception(f'Fixture name "{fixture.name}" used in more than one Fixture.')
            names.append(fixture.name)


    def check_empty_universe_names(self):
        for universe in self.patch.universes:
            if len(universe.name) == 0:
                raise Exception(f'Universe {universe.name} has no name.')

    def check_empty_fixture_names(self):
        for fixture in self.patch.fixtures:
            if len(fixture.name) == 0:
                raise Exception(f'Fixture {fixture.name} has no name.')


    def check_dmx_overlap(self):
        pass


    def check(self):
        self.check_unique_fixture_ids()
        self.check_unique_fixture_names()
        self.check_empty_universe_names()
        self.check_empty_fixture_names()
        self.check_dmx_overlap()

    def clean_removed_fixtures(self):
        new_ids = [f.id for f in self.patch.fixtures]
        fixtures = self.core.fixtures
        to_remove = []
        for fixture in fixtures:
            if fixture.id not in new_ids:
                to_remove.append(fixture)
        for fixture in to_remove:
            if (fixture.collection):
                util.delete_collection(fixture.collection.name)
            fixture_i = fixtures.find(fixture.name)
            fixtures.remove(fixture_i)

    def __init__(self):
        self.core = bpy.context.scene.dmx.core
        self.patch = bpy.context.scene.dmx.patch
        self.check()
        self.clean_removed_fixtures()
        for fixture_patch in self.patch.fixtures:
            DMX_FixtureBuilder(fixture_patch)


    