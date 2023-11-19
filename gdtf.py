#
#   BlendexDMX > GDTF
#   Handles GDTF profiles
#
#   http://www.github.com/open-stage/BlenderDMX
#

import os
import bpy
import copy
import math
import hashlib

from mathutils import Euler, Matrix

from dmx import pygdtf
from dmx.logging import DMX_Log
from dmx.io_scene_3ds.import_3ds import load_3ds
from dmx.util import sanitize_obj_name


class DMX_GDTF():

    @staticmethod
    def getProfilesPath():
        ADDON_PATH = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(ADDON_PATH,'assets','profiles')

    @staticmethod
    def getPrimitivesPath():
        ADDON_PATH = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(ADDON_PATH,'assets','primitives')

    @staticmethod
    def getManufacturerList():
        # List profiles in folder
        manufacturers_names = set()
        for file in os.listdir(DMX_GDTF.getProfilesPath()):
            # Parse info from file name: Manufacturer@Device@Revision.gdtf
            if "@" not in file:
                continue
            name = file.split('@')[0]
            manufacturers_names.add(name)
        manufacturers  = bpy.context.window_manager.dmx.manufacturers
        manufacturers.clear()
        for name in sorted(manufacturers_names):
            manufacturers.add().name = name

    @staticmethod
    def getProfileList(manufacturer):
        # List profiles in folder
        profiles = []
        for file in os.listdir(DMX_GDTF.getProfilesPath()):
            # Parse info from file name: Company@Model.gdtf
            info = file.split('@')
            if (info[0] == manufacturer):
                # Remove ".gdtf" from the end of the string
                info[-1] = info[-1][:-5]
                # Add to list (identifier, short name, full name)
                profiles.append((file, info[1], (info[2] if len(info) > 2 else '')))

        return tuple(profiles)

    @staticmethod
    def getModes(profile):
        """Returns an array, keys are mode names, value is channel count"""
        gdtf_profile = DMX_GDTF.loadProfile(profile)
        modes = {}
        for mode in gdtf_profile.dmx_modes:
            dmx_channels = pygdtf.utils.get_dmx_channels(gdtf_profile, mode.name)
            dmx_channels_flattened = [channel for break_channels in dmx_channels for channel in break_channels]
            modes[mode.name] = len(dmx_channels_flattened)
        return modes
 
    @staticmethod
    def loadProfile(filename):
        path = os.path.join(DMX_GDTF.getProfilesPath(), filename)
        profile = pygdtf.FixtureType(path)
        return profile

    @staticmethod
    def loadBlenderPrimitive(model):
        primitive = str(model.primitive_type)

        if (primitive == 'Cube'):
            bpy.ops.mesh.primitive_cube_add(size=1.0)
        elif (primitive == 'Pigtail'):
            bpy.ops.mesh.primitive_cube_add(size=1.0)
        elif (primitive == 'Cylinder'):
            bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.5, depth=1.0)
        elif (primitive == 'Sphere'):
            bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=16, radius=0.5)

        obj = bpy.context.view_layer.objects.selected[0]
        obj.users_collection[0].objects.unlink(obj)
        obj.scale = (model.length, model.width, model.height)
        return obj

    @staticmethod
    def loadPrimitive(model):
        primitive = str(model.primitive_type)
        path = os.path.join(DMX_GDTF.getPrimitivesPath(), primitive+'.obj')
        bpy.ops.import_scene.obj(filepath=path)
        obj = bpy.context.view_layer.objects.selected[0]
        obj.users_collection[0].objects.unlink(obj)
        obj.rotation_euler = Euler((0, 0, 0), 'XYZ')
        obj.scale = (model.length/obj.dimensions.x,model.width/obj.dimensions.y,model.height/obj.dimensions.z)
        return obj

    @staticmethod
    def load2D(profile):
        current_path = os.path.dirname(os.path.realpath(__file__))
        extract_to_folder_path = os.path.join(current_path, 'assets', 'models', profile.fixture_type_id)
        filename = f"{profile.thumbnail}.svg"
        obj = None
        if filename in profile._package.namelist():
            profile._package.extract(filename, extract_to_folder_path)
            bpy.ops.wm.gpencil_import_svg(filepath="", directory=extract_to_folder_path, files=[{"name":filename}], scale=1)
            if len(bpy.context.view_layer.objects.selected):
                obj = bpy.context.view_layer.objects.selected[0]
            if obj is not None:
                obj.users_collection[0].objects.unlink(obj)
                obj.rotation_euler[0]=-90*(math.pi/180)
        return obj

    @staticmethod
    def loadModel(profile, model):
        current_path = os.path.dirname(os.path.realpath(__file__))
        extract_to_folder_path = os.path.join(current_path, 'assets', 'models', profile.fixture_type_id)
        
        if model.file.extension.lower() == "3ds":
            inside_zip_path =f"models/3ds/{model.file.name}.{model.file.extension}"
            profile._package.extract(inside_zip_path, extract_to_folder_path)
            file_name=os.path.join(extract_to_folder_path, inside_zip_path)
            load_3ds(file_name, bpy.context)
        else:
            inside_zip_path = f"models/gltf/{model.file.name}.{model.file.extension}"
            profile._package.extract(inside_zip_path, extract_to_folder_path)
            file_name=os.path.join(extract_to_folder_path, inside_zip_path)
            bpy.ops.import_scene.gltf(filepath=file_name)

        obj = bpy.context.view_layer.objects.selected[0]
        obj.users_collection[0].objects.unlink(obj)
        obj.rotation_euler = Euler((0, 0, 0), 'XYZ')
        z=obj.dimensions.z or 1
        if obj.dimensions.z <= 0:
            DMX_Log.log.error(f"Model {obj.name} has no Z height, it will likely not work correctly.")
        obj.scale = (
            obj.scale.x*model.length/obj.dimensions.x,
            obj.scale.y*model.width/obj.dimensions.y,
            obj.scale.z*model.height/z)
        return obj

    @staticmethod
    def buildCollection(profile, mode, display_beams, add_target):

        # Create model collection
        collection = bpy.data.collections.new(DMX_GDTF.getName(profile, mode, display_beams, add_target))
        objs = {}
        # Get root geometry reference from the selected DMX Mode
        dmx_mode = pygdtf.utils.get_dmx_mode_by_name(profile, mode)

        # Handle if dmx mode doesn't exist (maybe this is MVR import and GDTF files were replaced)
        # use mode[0] as default
        if dmx_mode is None:
            dmx_mode = profile.dmx_modes[0]
            mode = dmx_mode.name

        root_geometry = pygdtf.utils.get_geometry_by_name(profile, dmx_mode.geometry)
        def load_geometries(geometry):
            """Load 3d models, primitives and shapes"""
            DMX_Log.log.info(f"loading geometry {geometry.name}")
            
            if isinstance(geometry, pygdtf.GeometryReference):
                reference = pygdtf.utils.get_geometry_by_name(profile, geometry.geometry)
                geometry.model = reference.model

                if hasattr(reference, "geometries"):
                    for sub_geometry in reference.geometries:
                        setattr(sub_geometry, "reference_root", str(geometry.name))
                        load_geometries(sub_geometry)

            if geometry.model is None:
                # Empty geometries are allowed as of GDTF 1.2
                # If the size is 0, Blender will discard it, set it to something tiny
                model=pygdtf.Model(name=f"{sanitize_obj_name(geometry)}",
                                   length=0.0001, width=0.0001, height=0.0001, primitive_type="Cube")
                geometry.model = ""
            else:
                # Deepcopy the model because GeometryReference will modify the name
                # Perhaps this could be done conditionally
                # Also, we could maybe make a copy of the beam instance, if Blender supports it...
                model = copy.deepcopy(pygdtf.utils.get_model_by_name(profile, geometry.model))

            if isinstance(geometry, pygdtf.GeometryReference):
                model.name=f"{sanitize_obj_name(geometry)}"

            obj = None
            primitive = str(model.primitive_type)
            # Normalize 1.1 PrimitiveTypes
            # (From GDTF v1.1 on, the 1_1 was added to the end of primitive names, we just ignore them and use the same primitives)
            if (primitive[-3:] == '1_1'):
                primitive = primitive[:-3]
                model.primitive_type = pygdtf.PrimitiveType(primitive)

            # 'Undefined' of 'File': load from file
            # Prefer File first, as some GDTFs have both File and PrimitiveType
            if (str(model.primitive_type) == 'Undefined') or (model.file is not None and model.file.name != "" and (str(model.primitive_type) != 'Pigtail')):
                try:
                    obj = DMX_GDTF.loadModel(profile, model)
                except Exception as e:
                    print("Error importing 3D model:", e)
                    model.primitive_type="Cube"
                    obj = DMX_GDTF.loadBlenderPrimitive(model)
            # BlenderDMX primitives
            elif (str(model.primitive_type) in ['Base','Conventional','Head','Yoke']):
                obj = DMX_GDTF.loadPrimitive(model)
            # Blender primitives
            else:
                obj = DMX_GDTF.loadBlenderPrimitive(model)
                
            # If object was created
            if (obj != None):
                if sanitize_obj_name(geometry) == sanitize_obj_name(root_geometry):
                    obj["geometry_root"]=True
                    obj.hide_select = False
                else:
                    obj.hide_select = True
                obj.name = sanitize_obj_name(geometry)
                obj["geometry_type"]=get_geometry_type_as_string(geometry)
                obj["original_name"]=geometry.name
                if isinstance(geometry, pygdtf.GeometryReference):
                    obj["referenced_geometry"]=str(geometry.geometry)
                if str(model.primitive_type) == 'Pigtail':
                    # This is a bit ugly because of PrimitiveType (in model) and not Geometry type (in geometry)
                    obj["geometry_type"]="pigtail"
                objs[sanitize_obj_name(geometry)] = obj

                # Apply transforms to ensure that models are correctly rendered
                # even if their transformations have not been applied prior to saving
                # This solves 99% of known issues when loading glbs
                # TODO: if the model is made of multiple smaller objects, we need to process them.

                mb = obj.matrix_basis
                if hasattr(obj.data, "transform"):
                    obj.data.transform(mb)
                for c in obj.children:
                    c.matrix_local = mb @ c.matrix_local
                obj.matrix_basis.identity()

            if hasattr(geometry, "geometries"):
                for sub_geometry in geometry.geometries:
                    load_geometries(sub_geometry)

        def get_geometry_type_as_string(geometry):
            # From these, we end up using "beam" and "pigtail".
            # The Pigtail is a special primitive type and we don't have access to
            # get to know this here
            # Even axis is not needed, as we rotate the geometry based on attributes during controlling

            if isinstance(geometry, pygdtf.GeometryMediaServerCamera):
                return "camera"
            if isinstance(geometry, pygdtf.GeometryBeam):
                return "beam"
            if isinstance(geometry, pygdtf.GeometryAxis):
                return "axis"
            if isinstance(geometry, pygdtf.GeometryReference):
                geometry = pygdtf.utils.get_geometry_by_name(profile, geometry.geometry)
                return get_geometry_type_as_string(geometry)
            return "normal"

        def create_camera(geometry):
            if (not sanitize_obj_name(geometry) in objs): return
            obj_child = objs[sanitize_obj_name(geometry)]
            camera_data = bpy.data.cameras.new(name=f"{obj_child.name}")
            camera_object = bpy.data.objects.new('MediaCamera', camera_data)
            camera_object.location = obj_child.location
            #camera_object.location.z-=0.1
            camera_object.hide_select = True
            constraint = camera_object.constraints.new('CHILD_OF')
            constraint.target = obj_child
            collection.objects.link(camera_object)

        def create_beam(geometry):
            if (not sanitize_obj_name(geometry) in objs): return
            obj_child = objs[sanitize_obj_name(geometry)]
            if "beam" not in obj_child.name.lower():
                obj_child.name=f"Beam {obj_child.name}"

            if not display_beams: # Don't even create beam objects to save resources
                return

            obj_child.visible_shadow = False
            light_data = bpy.data.lights.new(name=f"Spot {obj_child.name}", type='SPOT')
            light_data['flux'] = geometry.luminous_flux
            light_data['shutter_value'] = 0 # Here we will store values required for strobing
            light_data['shutter_dimmer_value'] = 0
            light_data['shutter_counter'] = 0
            light_data.energy = light_data['flux'] #set by default to full brightness for devices without dimmer
            light_data.spot_size = geometry.beam_angle
            light_data.spot_size = geometry.beam_angle*3.1415/180.0
            light_data.shadow_soft_size = geometry.beam_radius
            light_object = bpy.data.objects.new(name=f"Spot", object_data=light_data)
            light_object.location = obj_child.location
            light_object.hide_select = True
            constraint = light_object.constraints.new('CHILD_OF')
            constraint.target = obj_child
            collection.objects.link(light_object)
        
        def add_child_position(geometry):
            """Add a child, create a light source and emitter material for beams"""

            #if (not sanitize_obj_name(geometry) in objs): return
            obj_child = objs[sanitize_obj_name(geometry)]

            position = Matrix(geometry.position.matrix).to_translation()
            obj_child.location[0] += (position[0]*-1) # a bug due to rotations of parents not being applied
            obj_child.location[1] += position[1]
            obj_child.location[2] += position[2]

            obj_child.rotation_mode = "XYZ"
            obj_child.rotation_euler = Matrix(geometry.position.matrix).to_euler('XYZ')

            scale=Matrix(geometry.position.matrix).to_scale()
            obj_child.scale[0] *= scale[0]
            obj_child.scale[1] *= scale[1]
            obj_child.scale[2] *= scale[2]

        def constraint_child_to_parent(parent_geometry, child_geometry):
            if (not sanitize_obj_name(parent_geometry) in objs): return
            obj_parent = objs[sanitize_obj_name(parent_geometry)]
            if (not sanitize_obj_name(child_geometry) in objs): return
            obj_child = objs[sanitize_obj_name(child_geometry)]

            constraint = obj_child.constraints.new('CHILD_OF')
            constraint.target = obj_parent
            constraint.use_scale_x = False
            constraint.use_scale_y = False
            constraint.use_scale_z = False
            # Add parent position
            obj_child.location[0] += obj_parent.location[0]
            obj_child.location[1] += obj_parent.location[1]
            obj_child.location[2] += obj_parent.location[2]

        def update_geometry(geometry):
            """Recursively update objects position, rotation and scale
               and define parent/child constraints. References are new
               sub-trees that must be processed and their root marked."""

            if not isinstance(geometry, pygdtf.GeometryReference):
                # geometry reference will have different geometry
                add_child_position(geometry)

            if isinstance(geometry, pygdtf.GeometryBeam):
                create_beam(geometry)
            elif isinstance(geometry, (pygdtf.GeometryMediaServerCamera)):
                create_camera(geometry)

            elif isinstance(geometry, pygdtf.GeometryReference):
                reference = copy.deepcopy(pygdtf.utils.get_geometry_by_name(profile, geometry.geometry))
                reference.name=sanitize_obj_name(geometry)
                reference.position = geometry.position

                add_child_position(reference)

                if isinstance(reference, pygdtf.GeometryBeam):
                    create_beam(reference)
                elif isinstance(reference, (pygdtf.GeometryMediaServerCamera)):
                    create_camera(reference)

                if hasattr(reference, "geometries"):
                    if len(reference.geometries) > 0:
                        for child_geometry in reference.geometries:
                            setattr(child_geometry, "reference_root", str(reference.name))
                            constraint_child_to_parent(reference, child_geometry) # parent, child
                            update_geometry(child_geometry)
                return

            if hasattr(geometry, "geometries"):
                if len(geometry.geometries) > 0:
                    for child_geometry in geometry.geometries:
                        constraint_child_to_parent(geometry, child_geometry) # parent, child
                        update_geometry(child_geometry)

        # Load 3d objects from the GDTF profile
        # The whole procedure is still quite simplified
        # We could use more hierarchical approach inside Blender
        # To represent the geometries in a kinematic chain rather then flat structure
        # Also, we mostly omit links between geometry and channel function's geometry linking
        # For places, where for example multiple yokes would exist...
        load_geometries(root_geometry)
        update_geometry(root_geometry)

        # Add target for manipulating fixture
        if add_target:
            target = bpy.data.objects.new(name="Target", object_data=None)
            collection.objects.link(target)
            target.empty_display_size = 0.5
            target.empty_display_type = 'PLAIN_AXES'
            target.location = (0,0,-2)

        dmx_channels = pygdtf.utils.get_dmx_channels(profile, mode)
        virtual_channels = pygdtf.utils.get_virtual_channels(profile, mode)
        # Merge all DMX breaks together
        dmx_channels_flattened = [channel for break_channels in dmx_channels for channel in break_channels]
        # dmx_channels_flattened contain list of channel with id, geometry

        def get_root():
            for obj in objs.values():
                if obj.get("geometry_root", False):
                    return obj

        def get_axis(attribute):
            for obj in objs.values():
                for channel in dmx_channels_flattened:
                    if attribute == channel["id"] and channel["geometry"] == obj.get("original_name", "None"):
                        return obj
                for channel in virtual_channels:
                    if attribute == channel["id"] and channel["geometry"] == obj.get("original_name", "None"):
                        return obj


        # This could be moved to the processing up higher,but for now, it's easier here
        head = get_axis("Tilt")
        if head:
            head["mobile_type"]="head"
        yoke = get_axis("Pan")
        if yoke:
            yoke["mobile_type"]="yoke"
        base = get_root()
        DMX_Log.log.info(f"Head: {head}, Yoke: {yoke}, Base: {base}")


        # If the root has a child with Pan, create Z rotation constraint
        if add_target:
            if yoke is not None:
                for name, obj in objs.items():
                    if yoke.name == obj.name and len(obj.constraints):
                        constraint = obj.constraints[0]
                        if constraint.target == base:
                            if add_target:
                                constraint = obj.constraints.new('LOCKED_TRACK')
                                constraint.target = target
                                constraint.lock_axis = "LOCK_Z"
                        break

        # Track head to the target
        if add_target:
            if head is not None:
                constraint = head.constraints.new('TRACK_TO')
                constraint.target = target
            else:
                # make sure simple par fixtures can be controlled via Target
                constraint = base.constraints.new('TRACK_TO')
                constraint.target = target

        # 2D thumbnail planning symbol
        obj = DMX_GDTF.load2D(profile)
        if obj is not None:
            # should probably always show it "on top"
            obj["2d_symbol"] = "all"
            objs["2d_symbol"] = obj
            obj.show_in_front = True
            obj.active_material.grease_pencil.show_stroke = True
            #svg.data.layers[...].frames[0].strokes[0]
            # add constraints
            constraint_copyLocation = obj.constraints.new(
                type="COPY_LOCATION"
            )
            constraint_copyRotation = obj.constraints.new(
                type="COPY_ROTATION"
            )
            constraint_copyLocation.target = base
            constraint_copyRotation.target = base
            constraint_copyRotation.use_z = True
            constraint_copyRotation.use_x = False
            constraint_copyRotation.use_y = False



        # Link objects to collection
        for name, obj in objs.items():
            collection.objects.link(obj)

        return collection

    @staticmethod
    def getName(profile, dmx_mode, display_beams, add_target):
        revision = profile.revisions[-1].text if len(profile.revisions) else ''
        name = f"{profile.manufacturer}, {profile.name}, {dmx_mode}, {revision}, {'with_beams' if display_beams else 'without_beams'}, {'with_target' if add_target else 'without_target'}"
        # base64 encode the name as collections seems to have lenght limit 
        # which causes collections not to be cached, thus slowing imports down
        name = hashlib.shake_256(name.encode()).hexdigest(5)
        return name
