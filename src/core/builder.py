from bpy.types import Collection

from src.patch.data.fixture import DMX_Patch_Fixture
from .data.fixture import DMX_Fixture
from .gdtf import DMX_GDTF
from .model import DMX_Model

class DMX_FixtureBuilder:

    @classmethod
    def _get_fixture(self, id: int) -> DMX_Fixture or None:
        for fixture in core.fixtures:
            if (fixture.id == id):
                return fixture

    @classmethod
    def _save_positional_data(self, fixture: DMX_Fixture) -> (object(),object()):
        pos = {
            obj.name: obj.object.location.copy()
            for obj in self.objects
        }
        rot = {
            obj.name:obj.object.rotation_euler.copy()
            for obj in self.objects
        }
        return pos, rot
    
    @classmethod
    def _delete_fixture(self, core: 'DMX_Core', id: int) -> None:
        for fixture in core.fixtures:
            if (fixture.id == id):
                core.fixtures.remove(fixture)

    @classmethod
    def _create_fixture(self, core: 'DMX_Core', id: int) -> DMX_Fixture:
        self._delete_fixture(id)
        core.fixtures.add()
        core.fixtures[-1].id = id
        return core.fixtures[-1]
    
    @classmethod
    def _delete_collection(self, name: str) -> None:
        if (name in bpy.data.collections):
            for obj in bpy.data.collections[name].objects:
                bpy.data.objects.remove(obj)
            bpy.data.collections.remove(bpy.data.collections[name])

    @classmethod
    def _create_collection(self, name: str) -> Collection:
        self._delete_collection(name)

        bpy.ops.collection.create(name=name)
        collection = bpy.data.collections[name]

        # Blender creates collections with all selected
        # objects, so we unlink them to be safe.
        for c in self.collection.objects:
            self.collection.objects.unlink(c)
        for c in self.collection.children:
            self.collection.children.unlink(c)

        return collection

    @classmethod
    def _build_channels(self, gdtf, mode: str, fixture: DMX_Fixture) -> None:
        # Merge all DMX breaks together
        # TODO: Multiple start channels
        dmx_channels = pygdtf.utils.get_dmx_channels(gdtf, mode)
        dmx_channels_flattened = [channel for break_channels in dmx_channels for channel in break_channels]

        for ch in dmx_channels_flattened:
            fixture.channels.add()
            fixture.channels[-1].id = ch['id']
            fixture.channels[-1].geometry = ch['geometry']

            # Set shutter to 0, we don't want strobing by default
            # and are not reading real world values yet
            if "shutter" in ch['id'].lower():
                fixture.channels[-1].default = 0
            else:
                fixture.channels[-1].default = ch['default']

    @classmethod
    def _build_virtual_channels(self, gdtf, mode: str, fixture: DMX_Fixture) -> None:
        _virtual_channels = pygdtf.utils.get_virtual_channels(gdtf_profile, mode)
        for ch in _virtual_channels:
            fixture.virtual_channels.add()
            fixture.virtual_channels[-1].id = ch['id']
            fixture.virtual_channels[-1].geometry = ch['geometry']
            fixture.virtual_channels[-1].default = ch['default']

    @classmethod
    def _copy_model_objects(self, model: DMX_Model, create_lights: bool, fixture: DMX_Fixture) -> None:
        root = model.get_root()
        head = model.get_head()
        DMX_Log.log.info(f"Head: {head}, Root: {root}")

        links = {}
        for obj in model.collection.objects:
            # Copy object
            links[obj.name] = obj.copy()
            # If light, copy object data, 
            # Cache access to root (root) and head for faster rendering.
            # Fixtures with multiple pan/tilts will still have issues
            # but that would anyway require geometry → attribute approach
            if obj.type == 'LIGHT':
                if (not create_lights):
                    continue
                links[obj.name].data = obj.data.copy()
                fixture.lights.add()
                light_name=f'Light{len(fixture.lights)}'
                fixture.lights[-1].name = light_name
                fixture.lights[light_name].object = links[obj.name]
            elif 'Target' in obj.name:
                fixture.objects.add()
                fixture.objects[-1].name = 'Target'
                fixture.objects['Target'].object = links[obj.name]
            elif root.name == obj.name:
                fixture.objects.add()
                fixture.objects[-1].name = "Root"
                fixture.objects["Root"].object = links[obj.name]
            elif head is not None and head.name == obj.name:
                fixture.objects.add()
                fixture.objects[-1].name = "Head"
                fixture.objects["Head"].object = links[obj.name]

            # Link all other object to collection
            fixture.collection.objects.link(links[obj.name])

        # Relink constraints
        for obj in fixture.collection.objects:
            for constraint in obj.constraints:
                constraint.target = links[constraint.target.name]

    @classmethod
    def _load_positional_data(self, pos: object, rot: object, fixture: DMX_Fixture) -> None:
        bpy.context.view_layer.update()
        for obj in fixture.objects:
            if obj.name in pos:
                obj.object.location = pos[obj.name]

            if obj.object.get("geometry_root", False):
                if obj.name in rot:
                    obj.object.rotation_mode = 'XYZ'
                    obj.object.rotation_euler = rot[obj.name]

    @classmethod
    def _create_emitters(self, fixture: DMX_Fixture) -> None:
        for obj in fixture.collection.objects:
            if "beam" in obj.get("geometry_type", ""):
                emitter = obj
                fixture.emitters.add()
                fixture.emitters[-1].name = obj.name
                material = DMX_Material.get_emitter_material(obj.name)
                emitter.active_material = material
                emitter.material_slots[0].link = 'OBJECT'
                emitter.material_slots[0].material = material
                emitter.material_slots[0].material.shadow_method = 'NONE' # eevee
                fixture.emitters[-1].material = material

    @classmethod
    def _load_positional_data_from_mvr(self, mvr, fixture: DMX_Fixture):
        for obj in self.objects:
            if obj.object.get("geometry_root", False):
                obj.object.matrix_world=mvr_position

    @classmethod
    def _hide_pigtails(self, fixture: DMX_Fixture):
        for obj in fixture.collection.objects:
            if "pigtail" in obj.get("geometry_type", ""):
                obj.hide_set(not bpy.context.scene.dmx.display_pigtails)

    @classmethod
    def build(self, patch: DMX_Patch_Fixture, mvr = None):
        
        core = bpy.context.scene.dmx.core
        fixture = self._get_fixture(patch.id)

        # [Edit]
        # Save positional data and clear fixture
        if fixture:
            old_pos, old_rot = self._save_positional_data(fixture)
            fixture.lights.clear()
            fixture.objects.clear()
            fixture.channels.clear()
            fixture.virtual_channels.clear()
            fixture.emitter_materials.clear()

        # [Create]
        # Create a new fixture
        else:
            fixture = self._create_fixture(core, patch.id)

        # Build DMX channels
        gdtf = DMX_GDTF.load_fixture_type(patch.profile)
        self._build_channels(gdtf, patch.mode, fixture)
        self._build_virtual_channels(gdtf, patch.mode, fixture)

        # Prepare collection and model
        fixture.collection = self._create_collection()
        model = DMX_Model.get_fixture_model(patch)

        self._copy_model_objects(model, patch.create_lights, fixture)
        self._create_emitters(_create_emitters)
        
        # Set position from MVR
        if mvr:
            self._load_positional_data_from_mvr(mvr, fixture)
        else:
            # [Edit] Reload old positions and rotations
            if (old_pos and old_rot):
                self._load_positional_data(old_pos, old_rot, fixture)

        # Link collection to DMX collection
        core.collection.children.link(self.collection)

        # Set Pigtail visibility
        if (not core.display_pigtails):
            self._hide_pigtails(fixture)
 
        # Clear Fixture and Render
        fixture.clear()
        bpy.context.scene.dmx.render()