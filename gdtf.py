#
#   BlendexDMX > GDTF
#   Handles GDTF profiles
#
#   http://www.github.com/hugoaboud/BlenderDMX
#

import os
import bpy

from mathutils import Euler

from dmx import pygdtf

from dmx.io_scene_3ds.import_3ds import load_3ds

class DMX_GDTF():

    @staticmethod
    def getProfilesPath():
        ADDON_PATH = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(ADDON_PATH,'data','profiles')

    @staticmethod
    def getPrimitivesPath():
        ADDON_PATH = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(ADDON_PATH,'data','primitives')

    @staticmethod
    def getProfileList():
        # List profiles in folder
        profiles = []
        for file in os.listdir(DMX_GDTF.getProfilesPath()):
            # Parse info from file name: Company@Model.gdtf
            info = file.split('@')
            if (len(info) == 2): info[1] = info[1][:-5]
            if (len(info) == 3): info[2] = info[2][:-5]
            # Add to list (identifier, short name, full name)
            profiles.append((file, info[1], info[0]+" | "+info[1]))

        return tuple(profiles)

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
        return obj

    @staticmethod
    def load3ds(profile, model):
        filename = 'models/3ds/'+model.file.name+'.3ds'
        file_3ds = profile._package.open(filename)
        load_3ds(file_3ds, bpy.context)
        obj = bpy.context.view_layer.objects.selected[0]
        obj.users_collection[0].objects.unlink(obj)
        return obj

    @staticmethod
    def buildCollection(profile):

        # Create model collection
        collection = bpy.data.collections.new(DMX_GDTF.getName(profile))

        # Load 3ds objects from the GDTF profile
        objs = {}
        for model in profile.models:
            obj = None
            # Normalize 1.1 PrimitiveTypes
            primitive = str(model.primitive_type)
            if (primitive[-3:] == '1_1'):
                primitive = primitive[:-3]
                model.primitive_type = pygdtf.PrimitiveType(primitive)
            # Blender primitives
            if (str(model.primitive_type) == 'Conventional'):
                obj = DMX_GDTF.loadPrimitive(model)
            elif (str(model.primitive_type) == 'Cylinder'):
                obj = DMX_GDTF.loadBlenderPrimitive(model)
            # No primitives: load from 3ds
            elif (str(model.primitive_type) == 'Undefined'):
                obj = DMX_GDTF.load3ds(profile, model)
            # If object was created
            if (obj != None):
                obj.name = model.name
                objs[model.name] = obj
                obj.hide_select = True

        # Recursively update object position, rotation and scale
        def updateGeom(geom, d=0):
            print("geom " + str(geom))
            if (len(geom.geometries) > 0):
                for child_geom in geom.geometries:
                    if (d > 0):
                        # Constrain child to parent
                        obj_child = objs[child_geom.name]
                        print(obj_child)
                        constraint = obj_child.constraints.new('CHILD_OF')
                        constraint.target = objs[geom.name]
                        # Add parent position
                        position = [geom.position.matrix[c][3] for c in range(3)]
                        obj_child.location[0] += position[0]
                        obj_child.location[1] += position[1]
                        obj_child.location[2] += position[2]
                    updateGeom(child_geom, d+1)
            if (d > 0):
                # Add child position
                position = [geom.position.matrix[c][3] for c in range(3)]
                obj_child = objs[geom.name]
                obj_child.location[0] += position[0]
                obj_child.location[1] += position[1]
                obj_child.location[2] += position[2]

                # Beam geometry: add light source and emitter material
                if (isinstance(geom, pygdtf.GeometryBeam)):
                    light_data = bpy.data.lights.new(name="Spot", type='SPOT')
                    light_data.energy = geom.power_consumption
                    light_data.spot_size = geom.beam_angle*3.1415/180.0
                    light_data.shadow_soft_size = geom.beam_radius
                    light_object = bpy.data.objects.new(name="Spot", object_data=light_data)
                    light_object.location = obj_child.location
                    light_object.hide_select = True
                    constraint = light_object.constraints.new('CHILD_OF')
                    constraint.target = obj_child
                    collection.objects.link(light_object)

        updateGeom(profile)

        # Add target for manipulating fixture
        target = bpy.data.objects.new(name="Target", object_data=None)
        collection.objects.link(target)
        target.empty_display_size = 0.5
        target.empty_display_type = 'PLAIN_AXES'
        target.location = (0,0,-2)

        # If there's no Head, this is a conventional fixture
        if ('Head' not in objs):
            # If body has a Yoke child, set Z rotation constraint
            # This should be reviewed for other conventional fixtures
            for name, obj in objs.items():
                if (name == 'Yoke' and len(obj.constraints)):
                    print(obj)
                    print(obj.constraints)
                    constraint = obj.constraints[0]
                    if (constraint.target == objs['Body']):
                        constraint.use_rotation_x = False
                        constraint.use_rotation_y = False

            # Track body to the target
            constraint = objs['Body'].constraints.new('TRACK_TO')
            constraint.target = target

            # Make body selectable
            objs['Body'].hide_select = False

            print("CONVENTIONAL!")

        # Link objects to collection
        for name, obj in objs.items():
            collection.objects.link(obj)

        return collection

    @staticmethod
    def getName(profile):
        return profile.manufacturer + ", " + profile.name + ", " + (profile.revisions[-1].text if len(profile.revisions) else '')

    @staticmethod
    def TESTE():
        handle = object()

        # all branches below work
        if 1:
            # To get some properties we need to prevent them being coerced into native Py types.
            subscribe_to = bpy.context.object.path_resolve("name", False)
        elif 0:
            subscribe_to = bpy.context.object.location
        else:
            # all object locations
            subscribe_to = bpy.types.Object, "location"

        def notify_test(*args):
            print("Notify changed!", args)

        bpy.msgbus.subscribe_rna(
            key=subscribe_to,
            owner=handle,
            args=(1, 2, 3),
            notify=notify_test,
        )

        # In general we won't need to explicitly publish, nevertheless - support it.
        bpy.msgbus.publish_rna(key=subscribe_to)
