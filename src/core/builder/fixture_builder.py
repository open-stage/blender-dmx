from typing import Optional, List

import bpy
from bpy.types import Collection, Object

from src.core.types import *
from src.core import util
from src.core import const
from .gdtf_builder import DMX_GDTF_ModelBuilder
from .material import DMX_Material

class DMX_FixtureBuilder:
    '''
    Builder that turns a GDTF Profile and a Model Collection
    into a Fixture Collection.
    '''

    # [ Fixture Helpers ]

    def _create_fixture(self) -> 'DMX_Fixture':
        '''
        Add a new DMX_Fixture to the Core.
        '''
        self.core.fixtures.add()
        self.core.fixtures[-1].id = self.patch.id
        self.core.fixtures[-1].name = self.patch.name
        return self.core.fixtures[-1]

    def _get_fixture(self) -> Optional['DMX_Fixture']:
        '''
        Get the patch DMX_Fixture from the Core, or None
        if it doesn't exist.
        '''
        for fixture in self.core.fixtures:
            if (fixture.id == self.patch.id):
                return fixture

    def _clear_old_fixture(self) -> None:
        '''
        Remove old data from a fixture when rebuilding it.
        '''
        self.fixture.name = self.patch.name
        self.fixture.roots.clear()
        self.fixture.channels.clear()
        if (self.fixture.collection):
            util.delete_collection(self.fixture.collection.name)

    # [ Build from Model ]

    def _load_model(self) -> Collection:
        '''
        Load a Model Collection, built by the GDTF Builder.
        '''
        return DMX_GDTF_ModelBuilder.get(self.profile.filename, self.patch.mode)

    def _build_tree(self, node: Object) -> Object:
        '''
        Recursively build the fixture object tree by copying
        the Model tree.
        '''

        if (not self.patch.create_lights):
            if (node['geometry_type'] == 'Light'):
                return None
        
        clone = node.copy()
        if (node.data):
            clone.data = node.data.copy()
        
        self.fixture.collection.objects.link(clone)
        self.objects.append(clone)

        # Build tree below this node
        for child in node.children:
            child_clone = self._build_tree(child)
            if (child_clone):
                child_clone.parent = clone
                child_clone.matrix_parent_inverse = clone.matrix_world.inverted()
        return clone

    def _build_trees_from_model(self, model_collection: Collection) -> None:
        '''
        Build all the object trees defined on the Model Collection.
        '''
        for obj in model_collection.objects:
            if (obj.parent == None):
                root = self._build_tree(obj)
                self.fixture.roots.add()
                self.fixture.roots[-1].object = root

    # [ Positional Permanence ]
 
    def _save_positional_data(self) -> object:
        '''
        Store the root location and rotation, so the fixture
        is rebuilt in place.
        '''
        pos_rot = {
            root.object['geometry_name']: (
                root.object.location.copy(),
                root.object.rotation_euler.copy()
            )
            for root in self.fixture.roots
        }
        return pos_rot

    def _load_positional_data(self, pos_rot: object) -> None:
        '''
        Load the roots location and rotation, to rebuild
        the fixture in place.
        If root names have changed (ex: different profile),
        it uses the first root as source.
        '''
        first_non_target = [p for p in pos_rot if not 'Target' in p][0]
        for root in self.fixture.roots:
            name = root.object['geometry_name']
            if not name in pos_rot:
                name = first_non_target
            root.object.location = pos_rot[name][0]
            root.object.rotation_mode = 'XYZ'
            root.object.rotation_euler = pos_rot[name][1]
            match = True

    # [ Constraints ]

    def _relink_constraints(self) -> None:
        '''
        Relink constraints to the targets.
        (The links break when copying from the collection)
        '''
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

    # [ Materials ]

    def _add_emitter_materials(self) -> None:
        '''
        Add emission node materials to the beam geometry,
        so it glows along with the light source.
        '''
        beams = [
            obj for obj in self.objects
            if obj['geometry_type'] == 'GeometryBeam'
        ]

        for obj in beams:
            geometry_name = obj['geometry_name']
            material = DMX_Material.reset_emitter_material(
                self.fixture,
                geometry_name
            )

            if obj.data.materials:
                obj.data.materials[0] = material
            else:
                obj.data.materials.append(material)
    
    # [ Shader Reference Cache ]
    #
    # Geometries are annotated with references to it's 
    # relevant children shaders.
    # This is used to speed up the rendering of DMX values
    # by avoiding to traverse child geometry every frame

    def _get_nodes_of_type(self, root: Object, geometry_type: str) -> List[Object]:
        '''
        Return all nodes of the tree of a given geometry_type.
        '''
        objs = []
        stack = [root]
        while len(stack):
            obj = stack.pop(0)
            if obj['geometry_type'] == geometry_type:
                objs.append(obj)
            stack += obj.children
        return objs    

    def _cache_emitter_shader_references(self) -> None:
        '''
        Annotate all geometry that has a Dimmer or Color
        function with references to it's children emitter
        shaders.
        '''
        emitter_fns = [const.Function.Dimmer] + \
                      const.Function.RGB + \
                      const.Function.HSV
        channels = [
            ch for ch in self.fixture.channels
            if ch.function in emitter_fns
        ]

        for ch in channels:
            geom = ch.geometry
            beams = self._get_nodes_of_type(geom, 'GeometryBeam')
            geom['emitter_shaders'] = [
                beam.data.materials[0].node_tree
                for beam in beams
            ]

    # [ Preview Options ]

    def _show_name(self):
        '''
        Show a floating label on the 3D View with the fixture name.
        '''
        first_non_target = [r.object for r in self.fixture.roots if r.object['geometry_type'] != 'Target'][0]
        first_non_target.name = self.fixture.name
        first_non_target.show_name = True

    # [ DMX Channels ]

    def _get_coords(self, universe: Universe, offset: Offset) -> BufferCoords:
        '''
        Return the 3D coordinates of a given universe+address
        on the DMX buffer.
        '''
        addresses = [
            (o - 1 + universe*512)
            for o in offset
            if o != 0
        ]
        coords = [(
            i & 31,
            (i >> 5) & 31,
            (i >> 10) & 31
        ) for i in addresses]
        return coords

    def _build_channel(self, obj: Object, channel: ChannelMetadata):
        '''
        Build a FixtureChannel for the Fixture from
        a ChannelMetadata, stored by GDTFBuilder at
        the geometry.
        '''
        self.fixture.channels.add()
        
        offset = channel['offset']
        dmx_break = self.patch.breaks[channel['dmx_break']-1]
        
        coords = None
        if (offset):
            # Add break address so offset has absolute dmx address
            offset = [
                offset[i] + dmx_break.address
                if i < len(offset) else 0
                for i in range(4)
            ]
            # Get 3D coords of the universe+channel on the dmx buffer
            coords = self._get_coords(dmx_break.universe, offset)
            coords = sum(coords, tuple())
            coords += (0,)*(12-len(coords))

        self.fixture.channels[-1].coords = coords or (0,)*12
        self.fixture.channels[-1].resolution = len(offset)
        self.fixture.channels[-1].function = channel['function']
        self.fixture.channels[-1].geometry = obj
        self.fixture.channels[-1].default = channel['default']['value']

    def _build_channels(self):
        '''
        Build FixtureChannels for each geometry annotated
        with channel definitions.
        '''
        for obj in self.objects:
            if 'dmx_channels' not in obj:
                continue
            for channel in obj['dmx_channels']:
                self._build_channel(obj, channel)

    # [ Constructor ]

    def __init__(self, patch: 'DMX_Patch_Fixture'):
        
        self.patch = patch
        self.core = bpy.context.scene.dmx.core
        
        # Load Profile
        self.profile = self.patch.get_profile(bpy.context)
        
        # Load Fixture
        self.fixture = self._get_fixture()
        self.old_pos_rot = None
        if self.fixture:
            # [Edit] Save positional data and clear fixture
            self.old_pos_rot = self._save_positional_data()
            self._clear_old_fixture()
        else:
            # [Create] Create a new fixture
            self.fixture = self._create_fixture()

    def build(self, mvr = None) -> None:
        '''
        Build a Fixture
        - Create a new DMX_Fixture inside DMX.fixtures
        - Create a new Fixture Collection and add it to the scene
        - If a fixture with the same ID already exists, rebuild
        it while keeping the positional data
        '''

        # Build empty fixture collection
        self.fixture.collection = util.new_collection(self.patch.name)

        # Build fixture from model collection
        self.objects = []
        model_collection = self._load_model()
        self._build_trees_from_model(model_collection)

        # Decorate fixture
        self._relink_constraints()
        self._add_emitter_materials()
        self._show_name()
        # self._hide_pigtails()

        # Build DMX channels
        self._build_channels()

        # Build caches of pointers to dynamic blender elements
        # such as material nodes and lights.
        # These allow updating fixture state in constant time.
        self._cache_emitter_shader_references()

        # Set position
        if mvr:
            # From MVR
            pass #self._load_positional_data_from_mvr(mvr, fixture)
        else:
            if (self.old_pos_rot):
                #[Edit] Reload old positions and rotations
                self._load_positional_data(self.old_pos_rot)

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
