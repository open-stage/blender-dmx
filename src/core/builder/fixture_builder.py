from typing import Optional

import bpy
from bpy.types import Collection, Object

from src.core import util
from .gdtf_builder import DMX_GDTFBuilder

class DMX_FixtureBuilder:

    # Fixture Object management

    def _get_fixture(self) -> Optional['DMX_Fixture']:
        for fixture in self.core.fixtures:
            if (fixture.id == self.patch.id):
                return fixture

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
    
    # Build from Model

    def _load_model(self) -> Collection:
        return DMX_GDTFBuilder.get(self.profile.filename, self.patch.mode)

    def _build_obj(self, obj: Object) -> Object:
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

    def _build_from_model(self, model_collection: Collection) -> None:
        for obj in model_collection.objects:
            if (obj.parent == None):
                root = self._build_obj(obj)
                self.fixture.roots.add()
                self.fixture.roots[-1].object = root

    # Positional Permanence
 
    def _save_positional_data(self) -> object:
        pos_rot = {
            root.object['geometry_name']: (
                root.object.location.copy(),
                root.object.rotation_euler.copy()
            )
            for root in self.fixture.roots
        }
        return pos_rot

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

    # Decorators

    def _relink_mobiles(self) -> None:
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

    def _show_name(self):
        first_non_target = [r.object for r in self.fixture.roots if r.object['geometry_type'] != 'Target'][0]
        first_non_target.name = self.fixture.name
        first_non_target.show_name = True

    # DMX Channels

    def _build_channel(self, obj: Object, channel: object):
        self.fixture.channels.add()
        
        patch_offset = channel['offset']
        dmx_break = self.patch.breaks[channel['dmx_break']-1]
        
        offset = None
        if (patch_offset):
            offset = [
                patch_offset[i] + dmx_break.address
                if i < len(patch_offset) else 0
                for i in range(4)
            ]

        self.fixture.channels[-1].offset = offset
        self.fixture.channels[-1].universe = dmx_break.universe
        self.fixture.channels[-1].function = channel['function']
        self.fixture.channels[-1].geometry = obj
        self.fixture.channels[-1].default = channel['default']['value']

    def _build_channels(self):
        for obj in self.objects:
            if 'dmx_channels' not in obj:
                continue
            for channel in obj['dmx_channels']:
                self._build_channel(obj, channel)
            a = 2

    def __init__(self, patch: 'DMX_Patch_Fixture', mvr = None) -> None:
        
        self.patch = patch
        self.core = bpy.context.scene.dmx.core
        
        # Load Profile
        self.profile = self.patch.get_profile(bpy.context)
        
        # Load Fixture
        self.fixture = self._get_fixture()
        old_pos_rot = None
        if self.fixture:
            # [Edit] Save positional data and clear fixture
            old_pos_rot = self._save_positional_data()
            self._clear_old_fixture()
        else:
            # [Create] Create a new fixture
            self.fixture = self._create_fixture()

        # Build empty fixture collection
        self.fixture.collection = util.new_collection(self.patch.name)

        # Build fixture from model collection
        self.objects = []
        model_collection = self._load_model()
        self._build_from_model(model_collection)

        # Decorate fixture
        self._relink_mobiles()
        # self._add_emitter_materials()
        self._show_name()
        # self._hide_pigtails()

        # Build DMX channels
        self._build_channels()

        # Set position
        if mvr:
            # From MVR
            pass #self._load_positional_data_from_mvr(mvr, fixture)
        else:
            if (old_pos_rot):
                #[Edit] Reload old positions and rotations
                self._load_positional_data(old_pos_rot)

        # Link collection to DMX collection
        self.core.collection.children.link(self.fixture.collection)

        # Debug: Program
        self.core.engine.program([self.fixture], {
            'Dimmer': 0.3,
            'Pan': 0.1,
            'Tilt': 0.8
        })

        # Render
        self.core.engine.render(self.core)
