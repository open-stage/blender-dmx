import bpy

from src.core import util
from .fixture_builder import DMX_FixtureBuilder

class DMX_Builder:

    def _validate_unique_fixture_ids(self):
        ids = []
        for fixture in self.patch.fixtures:
            if fixture.id in ids:
                raise Exception(f'Fixture ID {fixture.id} used in more than one Fixture.')
            ids.append(fixture.id)
    
    def _validate_unique_fixture_names(self):
        names = []
        for fixture in self.patch.fixtures:
            if fixture.name in names:
                raise Exception(f'Fixture name "{fixture.name}" used in more than one Fixture.')
            names.append(fixture.name)


    def _validate_empty_universe_names(self):
        for universe in self.patch.universes:
            if len(universe.name) == 0:
                raise Exception(f'Universe {universe.name} has no name.')

    def _validate_empty_fixture_names(self):
        for fixture in self.patch.fixtures:
            if len(fixture.name) == 0:
                raise Exception(f'Fixture {fixture.id} has no name.')


    def _validate_maximum_lights(self):
        pass


    def _validate(self):
        self._validate_unique_fixture_ids()
        self._validate_unique_fixture_names()
        self._validate_empty_universe_names()
        self._validate_empty_fixture_names()
        self._validate_maximum_lights()

    def _clean_removed_fixtures(self):
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
        self._validate()
        self._clean_removed_fixtures()
        for fixture_patch in self.patch.fixtures:
            DMX_FixtureBuilder(fixture_patch)


    