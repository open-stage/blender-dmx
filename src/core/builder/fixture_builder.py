import bpy
from bpy.types import Collection

from src.core import util
from .gdtf_builder import DMX_GDTFBuilder

class DMX_FixtureBuilder:

    def _get_fixture(self) -> 'DMX_Fixture' or None:
        for fixture in self.core.fixtures:
            if (fixture.id == self.patch.id):
                return fixture

    def _save_positional_data(self) -> (object(),object()):
        pos_rot = {
            root.object['geometry_name']: (
                root.object.location.copy(),
                root.object.rotation_euler.copy()
            )
            for root in self.fixture.roots
        }
        return pos_rot

    def _clear_old_fixture(self) -> None:
        self.fixture.name = self.patch.name
        self.fixture.roots.clear()
        # self.fixture.lights.clear()
        # self.fixture.emitters.clear()
        # self.fixture.targets.clear()
        self.fixture.channels.clear()
        if (self.fixture.collection):
            util.delete_collection(self.fixture.collection.name)

    def _create_fixture(self) -> 'DMX_Fixture':
        self.core.fixtures.add()
        self.core.fixtures[-1].id = self.patch.id
        self.core.fixtures[-1].name = self.patch.name
        return self.core.fixtures[-1]
    
    def _load_model(self):
        return DMX_GDTFBuilder.get(self.profile.filename, self.patch.mode)

    def _create_collection(self) -> Collection:
        return util.new_collection(self.patch.name)

    def _build_obj(self, obj):
        if (obj['geometry_type'] == 'Light'):
            if (not self.patch.create_lights):
                return None
        clone = obj.copy()
        self.fixture.collection.objects.link(clone)
        self.objects.append(clone)
        for child in obj.children:
            child_clone = self._build_obj(child)
            if (child_clone):
                child_clone.parent = clone
                child_clone.matrix_parent_inverse = clone.matrix_world.inverted()
        return clone

    def _build_from_model(self, model_collection):
        self.objects = []
        for obj in model_collection.objects:
            if (obj.parent == None):
                root = self._build_obj(obj)
                self.fixture.roots.add()
                self.fixture.roots[-1].object = root

    def _load_positional_data(self, pos_rot: object) -> None:
        first_non_target = [p for p in pos_rot if not 'Target' in p][0]
        for root in self.fixture.roots:
            name = root.object['geometry_name']
            if not name in pos_rot:
                name = first_non_target
            root.object.location = pos_rot[name][0]
            root.object.rotation_mode = 'XYZ'
            root.object.rotation_euler = pos_rot[name][1]
            match = True

    def _relink_mobiles(self):
        mobiles = [
            obj for obj in self.objects
            if obj['geometry_type'] == 'Mobile'
        ]
        targets = [
            obj for obj in self.objects
            if obj['geometry_type'] == 'Target'
        ]
        targets.sort(key=lambda t: t['index'])
        for mobile in mobiles:
            target_index = mobile['target_index']
            mobile.constraints[0].target = targets[target_index]

    def __init__(self, patch: 'DMX_Patch_Fixture', mvr = None):
        self.patch = patch
        self.core = bpy.context.scene.dmx.core
        self.profile = self.patch.get_profile(bpy.context)
        
        # [Edit]
        # Save positional data and clear fixture
        self.fixture = self._get_fixture()
        old_pos_rot = None
        if self.fixture:
            old_pos_rot = self._save_positional_data()
            self._clear_old_fixture()

        # [Create]
        # Create a new fixture
        else:
            self.fixture = self._create_fixture()

        self.fixture.collection = self._create_collection()

        model_collection = self._load_model()
        self._build_from_model(model_collection)

        self._relink_mobiles()

        # # Set position from MVR
        # if mvr:
        #     self._load_positional_data_from_mvr(mvr, fixture)
        # else:
        # [Edit] Reload old positions and rotations
        if (old_pos_rot):
            self._load_positional_data(old_pos_rot)

        # Link collection to DMX collection
        self.core.collection.children.link(self.fixture.collection)

        # # Set Pigtail visibility
        # if (not core.display_pigtails):
        #     self._hide_pigtails(fixture)
 
        # # Clear Fixture and Render
        # fixture.clear()
        # bpy.context.scene.dmx.render()
