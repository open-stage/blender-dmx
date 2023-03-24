from mathutils import Euler, Matrix
from typing import List

import bpy
from bpy.types import Object, Collection

from lib import io_scene_3ds

from src.core import util
from .gdtf import DMX_GDTF

class DMX_GDTFBuilder:
    '''
    Builder that parses a GDTF Profile and builds a
    Model Collection from it.
    '''

     # [ Collections ]

    def _new_model_collection(self) -> Collection:        
        '''
        Create a new collection collection to store the Model of the Fixture being built.
        '''
        return util.new_collection(
            self.gdtf.get_model_collection_name(self.mode_name)
        )

    def _delete_model_collection(self) -> None:
        '''
        Delete the Model collection of the Fixture being built.
        '''
        util.delete_collection(
            self.gdtf.get_model_collection_name(self.mode_name)
        )

    def _new_fixture_collection(self) -> Collection:
        '''
        Create a new collection collection to store the Fixture being built.
        '''
        return util.new_collection(
            self.gdtf.get_collection_name(self.mode_name)
        )

    def _delete_fixture_collection(self) -> None:
        '''
        Delete the collection of the Fixture being built.
        '''
        util.delete_collection(
            self.gdtf.get_collection_name(self.mode_name)
        )

    # [ Objects ]
    #
    # When building models, 3 types of objects can be used:
    # - File: object imported from a .3ds of .gltf file
    # - GDTF Primitive: GDTF offers a few standards primitives
    # - Primitive: a simple Blender primitive (ex. Cube, Sphere, etc)

    def _get_created_obj(self, unlink = False) -> Object:
        '''
        Return the object that was just created by one of the 3 methods.
        '''
        objs = list(bpy.context.view_layer.objects.selected)
        for obj in objs:
            # gltf files sometimes include this mysterious object
            # so we delete it. there maybe others.
            # this is actually against GDTF spec, the glb should
            # contain only a single object
            # maybe we should check if len(obj) is > 1
            if (obj.name == '_display_d'):
                bpy.data.objects.remove(obj)
                objs.remove(obj)
            if unlink:
                obj.users_collection[0].objects.unlink(obj)
        return objs[0]

    def _create_obj_from_file(self, model: 'pygdtf.Model') -> Object:
        '''
        Import a geometry file (.3ds or .gltf) to Blender and return it.
        '''
        filepath, extension = self.gdtf.extract_model_file(model.file)
        try:
            if extension == "3ds":
                io_scene_3ds.import_3ds.load_3ds(filepath, bpy.context)
            else:
                bpy.ops.import_scene.gltf(filepath=filepath)
        except Exception as e:
            print(e)

        obj = self._get_created_obj(unlink = extension!="3ds")
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

    def _create_obj_from_gdtf_primitive(self, model: 'pygdtf.Model', primitive: str) -> Object:
        '''
        Import a geometry from BlenderDMX gdtf primitives to Blender and return it.
        '''
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

    def _create_obj_from_primitive(self, model: 'pygdtf.Model', primitive: str) -> Object:
        '''
        Create a primitive geometry and return it.
        '''
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

    # [ Model ]

    def _build_models(self):
        '''
        Build a Model collection and populate it with the models used
        on the GDTF profile.

        Before building Geometries, we build a collection with all the
        model objects used on this fixture.
        This collection is destroyed at the end of the build.
        During this process, 3D files are extracted from the zip file
        to a temporary folder inside assets/models, that's also deleted.
        '''
        collection = self._new_model_collection()
        util.activate_collection(collection)

        for model in self.gdtf.fixture_type.models:
            model_type, primitive = self.gdtf.get_model_primitive_type(model)
            
            if model_type == 'file':
                self.models[model.name] = self._create_obj_from_file(model)
            elif model_type == 'gdtf':
                self.models[model.name] = self._create_obj_from_gdtf_primitive(model, primitive)
            elif model_type == 'primitive':
                self.models[model.name] = self._create_obj_from_primitive(model, primitive)

        util.hide_collection(collection)

    # [Geometry Building]
    #
    # The profile geometry is a list of pygdtfGeometry Trees, that's
    # traversed recursively to create a list of Object Trees
    # inside a Collection.
    # The objects are tagged with geometry metadada.
    
    def _build_empty_model(self, name: str) -> Object:
        '''
        Create empty object for geometry without a geometry assigned.
        '''
        if not name in self.models:
            self.models[name] = bpy.data.objects.new(name, None)
            self.models[name].empty_display_size = 0
        return self.models[name]

    def _apply_matrix(self, obj: Object, matrix: Matrix):
        '''
        Apply a transform matrix to the object, altering it's
        location, rotation and scale.
        '''
        obj.location = Matrix(matrix).to_translation()
        obj.rotation_mode = "XYZ"
        obj.rotation_euler = Matrix(matrix).to_euler('XYZ')
        
        scale = Matrix(matrix).to_scale()
        obj.scale[0] *= scale[0]
        obj.scale[1] *= scale[1]
        obj.scale[2] *= scale[2]
    
    def _add_obj_metadata(self, geometry: 'pygdtf.Geometry', obj: Object):
        '''
        Add metadata to the Object as Custom Properties.
        These are used in later stages of the build.
        '''
        self.objects[geometry.name] = obj
        self.geometries[geometry.name] = geometry

        obj['geometry_name'] = geometry.name
        obj['geometry_type'] = type(geometry).__name__
        if 'yoke' in geometry.name.lower():
            obj['mobile_type'] = 'yoke'
        if 'head' in geometry.name.lower():
            obj['mobile_type'] = 'head'

        if (geometry.name in self.geom_channels):
            obj['dmx_channels'] = self.geom_channels[geometry.name]
        
    def _build_geometry(self, geometry: 'pygdtf.Geometry') -> Object:
        '''
        Build the base GDTF geometry tree as a Blender Object.
        Special geometries (such as Light, GeometryReference, MediaCamera)
        are added later, by targeting objects through geometry_name
        and populating them.
        '''
        # Copy model object for this geometry
        if (geometry.model == None):
            obj = self._build_empty_model(geometry.name)
        else:
            if not geometry.model in self.models:
                raise Exception(f'Malformed GDTF file. The "{geometry.model}" model refered by "{geometry.name}" geometry doesn\'t exist.')
            obj = self.models[geometry.model].copy()
        self.collection.objects.link(obj)

        # Apply geometry position/rotation/scale
        self._apply_matrix(obj, geometry.position.matrix)

        # Tag Geometry (Geometry Name, Yokes, Heads and Type)
        self._add_obj_metadata(geometry, obj)
        
        # Build children
        for child_geometry in geometry.geometries:
            child_obj = self._build_geometry(child_geometry)
            child_obj.parent = obj
            child_obj.matrix_parent_inverse = obj.matrix_world.inverted()
            # Make children unselectable, so the user won't accidentaly misalign them on the 3D view.
            child_obj.hide_select = True

        return obj

    def _build_trees(self) -> None:
        '''
        Build all trees defined on the GDTF geometry as
        Blender Object Trees.
        '''
        util.activate_collection(self.collection)
        for geometry in self.gdtf.fixture_type.geometries:
            self.roots.append(self._build_geometry(geometry))

    # [ Special Geometry Helpers ]

    def _obj_has_function(self, obj: Object, function: str) -> bool:
        '''
        Return true if the Object declares any dmx channel with the given function.
        '''
        if 'dmx_channels' in obj:
            for ch in obj['dmx_channels']:
                if (ch['function'] == function):
                    return True
        return False

    def _merge_special_obj(self, parent: Object, child: Object, special_geometry_type: str) -> None:
        '''
        Merge a special geometry Object into a node of the Tree.

        The geometry tree is built at a single pass, assuming all
        nodes are Normal Geometry.
        Then, separate build stages populate the tree, by adding
        children to the geometry created at the first pass.
        This makes it easier to integrate new features without modifying
        the tree traversal code.
        '''
        name = f'{parent["geometry_name"]}-{len(parent.children)}'
        child['geometry_name'] = name
        child['geometry_type'] = special_geometry_type
        child.parent = parent
        child.matrix_parent_inverse = child.parent.matrix_world.inverted()
        self.objects[name] = child
        self.collection.objects.link(child)

    # [ Special Geometry: Targets ]

    def _get_mobile_objects(self) -> List[Object]: 
        '''
        Return which objects should be tracked to a target
        as a list of tuples. Objects inside the same tuple
        should be tracked to the same target.
        '''
        yoke_objects = [obj for obj in self.objects.values()
            if obj.get('mobile_type',None) == 'yoke'
        ]
        head_objects = [obj for obj in self.objects.values()
            if obj.get('mobile_type',None) == 'head'
        ]

        # - Static Fixtures: track root geometry
        if (
            len(yoke_objects) == 0 and
            len(head_objects) == 0
        ):
            return [(root,) for root in self.roots]

        # - Yokes with a single direct Head child: track Yoke and Head to same target
        yoke_head_pairs = []
        for yoke in yoke_objects:
            child_heads = [obj for obj in yoke.children if obj in head_objects]
            if len(child_heads) == 1:
                yoke_head_pairs.append((yoke, child_heads[0]))

        # - Yoke without Head
        yokes = []
        for yoke in yoke_objects:
            if yoke not in [pair[0] for pair in yoke_head_pairs]:
                yokes.append((yoke,))

        # - Head without Yoke
        heads = []
        for head in head_objects:
            if head not in [pair[1] for pair in yoke_head_pairs]:
                heads.append((yoke,))

        return yokes + heads + yoke_head_pairs

    def _build_targets(self) -> None:
        '''
        Build the targets used to control fixture orientation.
        '''
        mobile_objects = self._get_mobile_objects()

        for index, pair in enumerate(mobile_objects):
            
            name = pair[0]['geometry_name']
            if (len(pair) > 1):
                name += '|' + pair[1]['geometry_name']
            target = bpy.data.objects.new(f'Target.{name}', None)
            target['geometry_name'] = f'Target{index}'
            target['geometry_type'] = 'Target'
            target['index'] = index

            target.empty_display_size = 0.1
            target.location = pair[0].location
            target.location.z = -1
            self.collection.objects.link(target)
            
            for obj in pair:
                has_pan = self._obj_has_function(obj, 'Pan')
                has_tilt = self._obj_has_function(obj, 'Tilt')
                obj['geometry_type'] = 'Mobile'
                obj['target_index'] = index

                if (has_pan or has_tilt):
                    constraint = obj.constraints.new(type='LOCKED_TRACK')
                    constraint.target = target
                    if has_tilt:
                        constraint.lock_axis = 'LOCK_X'
                        constraint.track_axis = 'TRACK_NEGATIVE_Z'
                else:
                    constraint = obj.constraints.new(type='TRACK_TO')
                    constraint.target = target
    
    # [ Special Geometry: Light ]

    def _build_light(self, obj: Object, geometry: 'pygdtf.GeometryBeam') -> None:
        '''
        Build a SpotLight for a given Object and GDTF Geometry.
        '''
        obj.visible_shadow = False

        data = bpy.data.lights.new(name=geometry.name, type='SPOT')
        data['flux'] = geometry.luminous_flux
        data['shutter_value'] = 0 # Here we will store values required for strobing
        data['shutter_dimmer_value'] = 0
        data['shutter_counter'] = 0
        data.energy = data['flux'] # set by default to full brightness for devices without dimmer
        data.spot_size = geometry.beam_angle
        data.spot_size = geometry.beam_angle*3.1415/180.0
        data.shadow_soft_size = geometry.beam_radius

        light = bpy.data.objects.new(name=f"Spot", object_data=data)
        light.hide_select = True

        self._merge_special_obj(obj, light, 'Light')

    def _build_lights(self) -> None:
        '''
        Build the children SpotLights of each GeometryBeam.
        '''
        beams = [obj for obj in self.objects.values()
            if obj['geometry_type'] == 'GeometryBeam'
        ]
        for obj in beams:
            name = obj['geometry_name']
            geometry = self.geometries[name]
            self._build_light(obj, geometry)
    
    # [ Special Geometry: Camera ]

    def _build_camera(self, obj: Object, geometry: 'pygdtf.GeometryBeam') -> None:
        '''
        Build a Camera for a given Object and GDTF Geometry.
        '''
        data = bpy.data.cameras.new(name=geometry.name)
        camera = bpy.data.objects.new(geometry.name, data)
        camera.hide_select = True

        self._merge_special_obj(obj, camera, 'Camera')

    def _build_cameras(self) -> None:
        '''
        Build the Cameras of each GeometryMediaServerCamera.
        '''
        cameras = [obj for obj in self.objects.values()
            if obj['geometry_type'] == 'GeometryMediaServerCamera'
        ]
        for obj in cameras:
            name = obj['geometry_name']
            geometry = self.geometries[name]
            self._build_camera(obj, geometry)
    
    # [ Constructor ]

    def __init__(self, gdtf: 'DMX_GDTF', mode_name: str) -> None:
        self.gdtf = gdtf
        self.mode_name = mode_name
       
        self.geometries = {}
        self.models = {}
        self.objects = {}
        self.roots = []

        self.geom_channels = gdtf.build_geometry_channel_metadata(mode_name)

    def build(self):
        '''
        Build a GDTF Fixture Model.
        '''
        self._delete_fixture_collection()
        self._delete_model_collection()
        self.collection = self._new_fixture_collection()
        
        self._build_models()
        self._build_trees()
        self._build_targets()
        self._build_lights()
        self._build_cameras()

        util.hide_collection(self.collection)
        self._delete_model_collection()
        self.gdtf.delete_fixture_model_folder()
        return self

    @staticmethod
    def get(filename: str, mode_name: str):
        gdtf = DMX_GDTF(filename)
        
        collection_name = gdtf.get_collection_name(mode_name)
        if (collection_name in bpy.data.collections):
            # TODO: Check collection metadata to match revision
            # Name lengths are limited, and there's no standard to the revision string,
            # so it better be stored as a Custom Property.
            collection = bpy.data.collections[collection_name]
            # objects = DMX_GDTFBuilder.get_objects(collection)
            return collection

        builder = DMX_GDTFBuilder(gdtf, mode_name).build()
        return builder.collection
