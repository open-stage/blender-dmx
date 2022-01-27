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
        return os.path.join(ADDON_PATH,'assets','profiles')

    @staticmethod
    def getPrimitivesPath():
        ADDON_PATH = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(ADDON_PATH,'assets','primitives')

    @staticmethod
    def getManufacturerList():
        # List profiles in folder
        manufacturers = set([])
        for file in os.listdir(DMX_GDTF.getProfilesPath()):
            # Parse info from file name: Company@Model.gdtf
            info = file.split('@')
            # Remove ".gdtf" from the end of the string
            info[-1] = info[-1][:-5]
            # Add to list (identifier, short name, full name)
            manufacturers.add((info[0], info[0], ''))

        return tuple(sorted(manufacturers))

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
        gdtf_profile = DMX_GDTF.loadProfile(profile)
        return tuple([mode.name for mode in gdtf_profile.dmx_modes])

    @staticmethod
    def getValue(dmx_value, fine=False):
        if (dmx_value.byte_count == 1): return dmx_value.value
        f = dmx_value.value/255.0
        msb = int(f)
        if (not fine): return msb
        lsb = int((f-msb)*255)
        return lsb

    @staticmethod
    def getChannels(gdtf_profile, mode):
        dmx_mode = None
        for m in gdtf_profile.dmx_modes:
            if (m.name == mode):
                dmx_mode = m
                break
        if (not dmx_mode): return []
        
        channels = dmx_mode.dmx_channels
        footprint = max([max([o for o in ch.offset]) for ch in channels])
        dmx_channels = [{'id':'', 'default':0}]*footprint
        for ch in channels:
            dmx_channels[ch.offset[0]-1] = {
                'id':str(ch.logical_channels[0].channel_functions[0].attribute),
                'default':DMX_GDTF.getValue(ch.logical_channels[0].channel_functions[0].default)
            }
            if (len(ch.offset) > 1):
                dmx_channels[ch.offset[1]-1] = {
                    'id':'+'+str(ch.logical_channels[0].channel_functions[0].attribute),
                    'default':DMX_GDTF.getValue(ch.logical_channels[0].channel_functions[0].default, True)
                }
        
        for i, ch in enumerate(dmx_channels):
            if ('ColorAdd_' in ch['id']):
                dmx_channels[i]['id'] = ch['id'][9:]

        return dmx_channels
        
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
        obj.scale = (model.length/obj.dimensions.x,model.width/obj.dimensions.y,model.height/obj.dimensions.z)
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
            primitive = str(model.primitive_type)
            # Normalize 1.1 PrimitiveTypes
            # (From GDTF v1.1 on, the 1_1 was added to the end of primitive names, we just ignore them and use the same primitives)
            if (primitive[-3:] == '1_1'):
                primitive = primitive[:-3]
                model.primitive_type = pygdtf.PrimitiveType(primitive)
            # BlenderDMX primitives
            if (str(model.primitive_type) in ['Base','Conventional','Head','Yoke']):
                obj = DMX_GDTF.loadPrimitive(model)
            # 'Undefined': load from 3ds
            elif (str(model.primitive_type) == 'Undefined'):
                obj = DMX_GDTF.load3ds(profile, model)
            # Blender primitives
            else:
                obj = DMX_GDTF.loadBlenderPrimitive(model)
            # If object was created
            if (obj != None):
                obj.name = model.name
                objs[model.name] = obj
                obj.hide_select = True

        # Recursively update object position, rotation and scale
        def updateGeom(geom, d=0):
            if (d > 0):
                # Add child position
                position = [geom.position.matrix[c][3] for c in range(3)]
                obj_child = objs[geom.name]
                obj_child.location[0] += position[0]
                obj_child.location[1] += position[1]
                obj_child.location[2] += position[2]

                # Beam geometry: add light source and emitter material
                if (isinstance(geom, pygdtf.GeometryBeam)):
                    obj_child.visible_shadow = False
                    light_data = bpy.data.lights.new(name="Spot", type='SPOT')
                    light_data['flux'] = geom.luminous_flux
                    light_data.energy = 0
                    light_data.spot_size = geom.beam_angle*3.1415/180.0
                    light_data.shadow_soft_size = geom.beam_radius
                    light_object = bpy.data.objects.new(name="Spot", object_data=light_data)
                    light_object.location = obj_child.location
                    light_object.hide_select = True
                    constraint = light_object.constraints.new('CHILD_OF')
                    constraint.target = obj_child
                    collection.objects.link(light_object)

            if (len(geom.geometries) > 0):
                for child_geom in geom.geometries:
                    if (d > 0):
                        # Constrain child to parent
                        obj_parent = objs[geom.name]
                        obj_child = objs[child_geom.name]
                        constraint = obj_child.constraints.new('CHILD_OF')
                        constraint.target = obj_parent
                        constraint.use_scale_x = False
                        constraint.use_scale_y = False
                        constraint.use_scale_z = False
                        # Add parent position
                        position = [geom.position.matrix[c][3] for c in range(3)]
                        obj_child.location[0] += obj_parent.location[0]
                        obj_child.location[1] += obj_parent.location[1]
                        obj_child.location[2] += obj_parent.location[2]
                    updateGeom(child_geom, d+1)

        updateGeom(profile)

        # Add target for manipulating fixture
        target = bpy.data.objects.new(name="Target", object_data=None)
        collection.objects.link(target)
        target.empty_display_size = 0.5
        target.empty_display_type = 'PLAIN_AXES'
        target.location = (0,0,-2)

        # If there's no Head, this is a static fixture
        if ('Head' not in objs):
            # If body has a Yoke child, set Z rotation constraint
            for name, obj in objs.items():
                if (name == 'Yoke' and len(obj.constraints)):
                    constraint = obj.constraints[0]
                    if (constraint.target == objs['Body']):
                        constraint.use_rotation_x = False
                        constraint.use_rotation_y = False
                    break

            # Track body to the target
            constraint = objs['Body'].constraints.new('TRACK_TO')
            constraint.target = target

            # Make body selectable
            objs['Body'].hide_select = False

        # There's a Head! This is a moving fixture
        else:
            # If base has a Yoke child, create Z rotation constraint
            for name, obj in objs.items():
                if (name == 'Yoke' and len(obj.constraints)):
                    constraint = obj.constraints[0]
                    if (constraint.target == objs['Base']):
                        constraint = obj.constraints.new('LOCKED_TRACK')
                        constraint.target = target
                        constraint.lock_axis = "LOCK_Z"
                    break

            # Track body to the target
            constraint = objs['Head'].constraints.new('TRACK_TO')
            constraint.target = target

            # Make body selectable
            objs['Base'].hide_select = False

        # Link objects to collection
        for name, obj in objs.items():
            collection.objects.link(obj)

        return collection

    @staticmethod
    def getName(profile):
        return profile.manufacturer + ", " + profile.name + ", " + (profile.revisions[-1].text if len(profile.revisions) else '')
