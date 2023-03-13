from mathutils import Euler, Matrix

import bpy
from bpy.types import Object

from lib import pygdtf
from lib import io_scene_3ds

from .gdtf import DMX_GDTF

class DMX_GDTFBuilder:

    # Load Geometries

    def _get_created_obj(self):
        objs = list(bpy.context.view_layer.objects.selected)
        for obj in objs:
            # gltf files sometimes include this mysterious object
            # so we delete it. there maybe others.
            if (obj.name == '_display_d'):
                bpy.data.objects.remove(obj)
                objs.remove(obj)
        return objs[0]

    def _create_obj_from_file(self, model: pygdtf.Model) -> Object:
        filepath, extension = DMX_GDTF.extract_model_file(self.gdtf, model.file)
        try:
            if extension == "3ds":
                io_scene_3ds.import_3ds.load_3ds(filepath, bpy.context)
            else:
                bpy.ops.import_scene.gltf(filepath=filepath)
        except Exception as e:
            print(e)

        obj = self._get_created_obj()
        obj.name = model.name
        obj.data.name = model.name
        obj.rotation_euler = Euler((0, 0, 0), 'XYZ')

        # If the imported model has a 0 size in any dimension, warn the user.
        # This can cause conflicts while rotating.
        if obj.dimensions.x <= 0:
            DMX_Log.log.error(f"Model {obj.name} X size {obj.dimensions.x} <= 0. It will likely not work correctly.")
        if obj.dimensions.y <= 0:
            DMX_Log.log.error(f"Model {obj.name} Y size {obj.dimensions.y} <= 0. It will likely not work correctly.")
        if obj.dimensions.z <= 0:
            DMX_Log.log.error(f"Model {obj.name} Z size {obj.dimensions.z} <= 0. It will likely not work correctly.")
        dim_x = obj.dimensions.x or 1
        dim_y = obj.dimensions.y or 1
        dim_z = obj.dimensions.z or 1

        obj.scale = (
            obj.scale.x*model.length/dim_x,
            obj.scale.y*model.width/dim_y,
            obj.scale.z*model.height/dim_z
        )
        return obj

    def _create_obj_from_gdtf_primitive(self, model: pygdtf.Model, primitive: str) -> Object:
        filepath = DMX_GDTF._get_primitive_path(primitive)
        bpy.ops.import_scene.obj(filepath=filepath)

        obj = self._get_created_obj()
        obj.name = model.name
        obj.data.name = model.name

        obj.rotation_euler = Euler((0, 0, 0), 'XYZ')
        obj.scale = (
            model.length/obj.dimensions.x,
            model.width/obj.dimensions.y,
            model.height/obj.dimensions.z
        )
        return obj

    def _create_obj_from_primitive(self, model: pygdtf.Model, primitive: str) -> Object:
        if (primitive == 'Cube'):
            bpy.ops.mesh.primitive_cube_add(size=1.0)
        elif (primitive == 'Pigtail'):
            bpy.ops.mesh.primitive_cube_add(size=1.0)
        elif (primitive == 'Cylinder'):
            bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.5, depth=1.0)
        elif (primitive == 'Sphere'):
            bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=16, radius=0.5)

        obj = self._get_created_obj()
        obj.name = model.name
        obj.data.name = model.name

        obj.scale = (
            model.length,
            model.width,
            model.height
        )
        return obj

    # Collections Management

    def _delete_collection(self, name: str) -> None:
        if (name in bpy.data.collections):
            for obj in bpy.data.collections[name].objects:
                bpy.data.objects.remove(obj)
            bpy.data.collections.remove(bpy.data.collections[name])

    def _delete_collections(self) -> None:
        self._delete_collection(f'{self.gdtf.fixture_type_id}-{self.mode}-MODELS')
        self._delete_collection(f'{self.gdtf.fixture_type_id}-{self.mode}')

    def _activate_collection(self, collection: 'Collection'):
        # Activates the collection so new objects are created inside it
        bpy.context.scene.collection.children.link(collection)
        layer_collection = bpy.context.view_layer.layer_collection.children[collection.name]
        bpy.context.view_layer.active_layer_collection = layer_collection

    def _hide_collection(self, collection: 'Collection'):
        bpy.context.scene.collection.children.unlink(collection)

    # Model Build

    def _new_model_collection(self) -> 'Collection':
        name = f'{self.gdtf.fixture_type_id}-{self.mode}-MODELS'
        return bpy.data.collections.new(name)

    def _build_models(self):
        models = {}
        collection = self._new_model_collection()
        self._activate_collection(collection)

        for model in self.gdtf.models:
            model_type, primitive = DMX_GDTF.get_model_primitive_type(model)
            
            if model_type == 'file':
                models[model.name] = self._create_obj_from_file(model)
            elif model_type == 'gdtf':
                models[model.name] = self._create_obj_from_gdtf_primitive(model, primitive)
            elif model_type == 'primitive':
                models[model.name] = self._create_obj_from_primitive(model, primitive)

        self._hide_collection(collection)
        return models

    # Geometry Build

    def _new_geom_collection(self) -> 'Collection':
        name = f'{self.gdtf.fixture_type_id}-{self.mode}'
        return bpy.data.collections.new(name)

    def _build_empty_obj(self, name):
        if not name in self.models:
            self.models[name] = bpy.data.objects.new(name, None)
            self.models[name].empty_display_size = 0
        return self.models[name]

    def _apply_matrix(self, obj: 'Object', matrix: Matrix):
        obj.location = Matrix(matrix).to_translation()
        obj.rotation_mode = "XYZ"
        obj.rotation_euler = Matrix(matrix).to_euler('XYZ')
        
        scale = Matrix(matrix).to_scale()
        obj.scale[0] *= scale[0]
        obj.scale[1] *= scale[1]
        obj.scale[2] *= scale[2]
    
    def _tag_obj(self, geometry: pygdtf.Geometry, obj: 'Object'):
        if 'yoke' in geometry.name.lower():
            self.yoke_objects.append(obj)
        if 'head' in geometry.name.lower():
            self.head_objects.append(obj)
        if isinstance(geometry, pygdtf.GeometryBeam):
            self.beam_objects.append(obj)

    def _build_geometry(self, geometry: pygdtf.Geometry):
        # Build Geometry object
        if (geometry.model == None):
            obj = self._build_empty_obj(geometry.name)
        else:
            if not geometry.model in self.models:
                raise Exception(f'Malformed GDTF file. The "{geometry.model}" model refered by "{geometry.name}" geometry doesn\'t exist.')
            obj = self.models[geometry.model].copy()
        self.collection.objects.link(obj)

        # Apply geometry position/rotation/scale
        self._apply_matrix(obj, geometry.position.matrix)

        # Tag Geometry (Yokes, Heads and Beams)
        self._tag_obj(geometry, obj)
        obj['geometry_name'] = geometry.name

        # Add geometry channel metadata as custom properties
        # These are used later to build the fixture controls
        if (geometry.name in self.channels):
            obj['dmx_channels'] = self.channels[geometry.name]
        if (geometry.name in self.virtual_channels):
            obj['dmx_virtual_channels'] = self.virtual_channels[geometry.name]
        
        # Build children
        for child_geometry in geometry.geometries:
            child_obj = self._build_geometry(child_geometry)
            child_obj.parent = obj
            child_obj.matrix_parent_inverse = obj.matrix_world.inverted()
            # Make children unselectable, so the user won't accidentaly misalign them on the 3D view.
            child_obj.hide_select = True

        return obj

    def _build_geometries(self):
        geometries = []
        self._activate_collection(self.collection)

        for geometry in self.gdtf.geometries:
            geometries.append(self._build_geometry(geometry))            

        return geometries

    # Target Build

    def _get_dynamic_objects(self): 
        # Returns which objects should be tracked to a target
        # as a list of tuples. Objects inside the same tuple
        # should be tracked to the same target.
        
        # - Static Fixtures: track root geometry
        if (
            len(self.head_objects) == 0 and
            len(self.yoke_objects) == 0
        ):
            return [(root,) for root in self.roots]

        # - Yokes with a single direct Head child: track Yoke and Head to same target
        yoke_head_pairs = []
        for yoke in self.yoke_objects:
            child_heads = [obj for obj in yoke.children if obj in self.head_objects]
            if len(child_heads) == 1:
                yoke_head_pairs.append((yoke, child_heads[0]))

        # - Yoke without Head
        yokes = []
        for yoke in self.yoke_objects:
            if yoke not in [pair[0] for pair in yoke_head_pairs]:
                yokes.append((yoke,))

        # - Head without Yoke
        heads = []
        for head in self.head_objects:
            if head not in [pair[1] for pair in yoke_head_pairs]:
                heads.append((yoke,))

        return yokes + heads + yoke_head_pairs

    def _obj_has_channel(self, obj: 'Object', channel_attribute: str):
        if 'dmx_channels' in obj:
            for ch in obj['dmx_channels']:
                if (ch['attribute'] == channel_attribute):
                    return True
        if 'dmx_virtual_channels' in obj:
            for ch in obj['dmx_virtual_channels']:
                if (ch['attribute'] == channel_attribute):
                    return True
        return False

    def _build_targets(self):
        dynamic_objects = self._get_dynamic_objects()

        for pair in dynamic_objects:
            
            name = pair[0]['geometry_name']
            if (len(pair) > 1):
                name += '|' + pair[1]['geometry_name']
            target = bpy.data.objects.new(f'Target.{name}', None)

            target.empty_display_size = 0.1
            target.location = pair[0].location
            target.location.z = -1
            self.collection.objects.link(target)
            
            for obj in pair:
                has_pan = self._obj_has_channel(obj, 'Pan')
                has_tilt = self._obj_has_channel(obj, 'Tilt')

                if (has_pan or has_tilt):
                    constraint = obj.constraints.new(type='LOCKED_TRACK')
                    constraint.target = target
                    if has_tilt:
                        constraint.lock_axis = 'LOCK_X'
                        constraint.track_axis = 'TRACK_NEGATIVE_Z'
                else:
                    constraint = obj.constraints.new(type='TRACK_TO')
                    constraint.target = target

        a = 2
    # 

    def __init__(self, gdtf: pygdtf.FixtureType, mode: str):
        self.gdtf = gdtf
        self.mode = mode

        self.channels, self.virtual_channels = DMX_GDTF.get_geometry_channel_metadata(gdtf, mode)
        
        self._delete_collections()
        self.models = self._build_models()

        self.collection = self._new_geom_collection()
        self.yoke_objects = []
        self.head_objects = []
        self.beam_objects = []
        self.roots = self._build_geometries()

        self._build_targets()
        # self._hide_collection(self.collection)

        a = 2
