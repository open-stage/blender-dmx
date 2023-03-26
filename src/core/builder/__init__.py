import bpy

from src.core import util
from .fixture_builder import DMX_FixtureBuilder

class DMX_SceneBuilder:
    '''
    Builder that turns a DMX Patch into a Blender scene.
    '''

    # [ Validation ]

    def _validate_unique_fixture_ids(self) -> None:
        '''
        Check if all fixture ids are unique.
        '''
        ids = []
        for fixture in self.patch.fixtures:
            if fixture.id in ids:
                raise Exception(f'Fixture ID {fixture.id} used in more than one Fixture.')
            ids.append(fixture.id)
    
    def _validate_unique_fixture_names(self) -> None:
        '''
        Check if all fixture names are unique.
        '''
        names = []
        for fixture in self.patch.fixtures:
            if fixture.name in names:
                raise Exception(f'Fixture name "{fixture.name}" used in more than one Fixture.')
            names.append(fixture.name)

    def _validate_empty_universe_names(self) -> None:
        '''
        Check if all universes have a name.
        '''
        for universe in self.patch.universes:
            if len(universe.name) == 0:
                raise Exception(f'Universe {universe.name} has no name.')

    def _validate_empty_fixture_names(self) -> None:
        '''
        Check if all fixtures have a name.
        '''
        for fixture in self.patch.fixtures:
            if len(fixture.name) == 0:
                raise Exception(f'Fixture {fixture.id} has no name.')

    def _validate_maximum_lights(self) -> None:
        '''
        Check if the patch contains at most 128 light sources.
        '''
        pass

    def _validate(self) -> None:
        '''
        Validate patch user input.
        '''
        self._validate_unique_fixture_ids()
        self._validate_unique_fixture_names()
        self._validate_empty_universe_names()
        self._validate_empty_fixture_names()
        self._validate_maximum_lights()

    # [ Cleanup ]

    def _delete_removed_fixtures(self) -> None:
        '''
        Delete fixtures whose ids were present on the 
        last patch but have been deleted on the new one.
        '''
        fixtures = self.core.fixtures
        new_ids = [f.id for f in self.patch.fixtures]
        to_remove = []
        for fixture in fixtures:
            if fixture.id not in new_ids:
                to_remove.append(fixture)
        
        for fixture in to_remove:
            if (fixture.collection):
                util.delete_collection(fixture.collection.name)
            fixture_i = fixtures.find(fixture.name)
            fixtures.remove(fixture_i)

    # [ Building ]

    def __init__(self):
        self.core = bpy.context.scene.dmx.core
        self.patch = bpy.context.scene.dmx.patch
        self._validate()

    def build(self) -> None:
        '''
        (Re-)build all the Fixtures on the Patch.
        '''
        self._delete_removed_fixtures()
        for fixture_patch in self.patch.fixtures:
            DMX_FixtureBuilder(fixture_patch).build()


    
