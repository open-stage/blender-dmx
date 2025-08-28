# Copyright (C) 2020 Hugo Aboud, Kaspars Jaudzems, Lily Hopkins, Sebastian, vanous
#
# This file is part of BlenderDMX.
#
# BlenderDMX is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# BlenderDMX is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <https://www.gnu.org/licenses/>.

import copy
import hashlib
import math
import os
import pathlib
import traceback
from types import SimpleNamespace

import bpy
import pygdtf
from io_scene_3ds.import_3ds import load_3ds
from mathutils import Matrix, Vector

from .logging_setup import DMX_Log
from .util import sanitize_obj_name
from .color_utils import xyY2rgbaa


class DMX_GDTF:
    @staticmethod
    def getPrimitivesPath():
        ADDON_PATH = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(ADDON_PATH, "assets", "primitives")

    @staticmethod
    def load_blender_primitive(model):
        primitive = model.primitive_type.value

        if primitive == "Cube":
            bpy.ops.mesh.primitive_cube_add(size=1.0)
        elif primitive == "Pigtail":
            bpy.ops.mesh.primitive_cube_add(size=1.0)
        elif primitive == "Plane":
            bpy.ops.mesh.primitive_plane_add(size=1.0)
        elif primitive == "Cylinder":
            bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.5, depth=1.0)
        elif primitive == "Sphere":
            bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=16, radius=0.5)

        obj = bpy.context.view_layer.objects.selected[0]
        obj.users_collection[0].objects.unlink(obj)
        obj.data.transform(
            Matrix.Diagonal((model.length, model.width, model.height)).to_4x4()
        )
        return obj

    @staticmethod
    def load_gdtf_primitive(model):
        primitive = model.primitive_type.value
        path = os.path.join(DMX_GDTF.getPrimitivesPath(), f"{primitive}.glb")
        bpy.ops.import_scene.gltf(filepath=path)
        obj = bpy.context.view_layer.objects.selected[0]
        obj.users_collection[0].objects.unlink(obj)
        obj.data.transform(
            Matrix.Diagonal(
                (
                    model.length / obj.dimensions.x,
                    model.width / obj.dimensions.y,
                    model.height / obj.dimensions.z,
                )
            ).to_4x4()
        )
        return obj

    @staticmethod
    def get_wheel_slot_colors(profile, attr_names_color_wheels_names):
        result = {}

        attr_color_wheels = [
            (attr_name, wheel)
            for attr_name, color_wheel_name in attr_names_color_wheels_names
            for wheel in profile.wheels
            if wheel.name == color_wheel_name
        ]

        if not attr_color_wheels:
            return result

        for index, (attribute_name, wheel) in enumerate(attr_color_wheels):
            colors = []
            for slot in wheel.wheel_slots:
                try:
                    color = xyY2rgbaa(slot.color)
                except Exception as e:
                    color = (0, 0, 0, 1)
                colors.append(color)
            result[attribute_name] = colors

        return result

    @staticmethod
    def extract_gobos_as_sequence(profile, attr_names_gobo_wheels_names):
        dmx = bpy.context.scene.dmx
        current_path = dmx.get_addon_path()
        result = []
        gdtf_path = os.path.join(
            current_path, "assets", "models", profile.fixture_type_id
        )

        attr_gobo_wheels = [
            (attr_name, wheel)  # (gobo_wheel_name, attribute_name)
            for attr_name, gobo_wheel_name in attr_names_gobo_wheels_names
            for wheel in profile.wheels
            if wheel.name == gobo_wheel_name
        ]

        if not attr_gobo_wheels:
            return result

        for image_name in profile._package.namelist():
            if image_name.startswith("wheels"):
                profile._package.extract(image_name, gdtf_path)

        images_path = os.path.join(gdtf_path, "wheels")

        images_paths = list(pathlib.Path(images_path).rglob("*"))

        for index, (attribute_name, wheel) in enumerate(attr_gobo_wheels):
            sequence_path = os.path.join(gdtf_path, attribute_name.lower())

            if not os.path.isdir(sequence_path):
                os.makedirs(sequence_path)
            idx = 1
            first = None
            for slot in wheel.wheel_slots:
                if not slot.media_file_name.name:
                    continue

                for image in images_paths:
                    if slot.media_file_name.name == image.stem:
                        destination = pathlib.Path(sequence_path, f"image_{idx:04}.png")
                        destination.write_bytes(image.read_bytes())
                        if first is None:
                            first = str(destination.resolve())
                        break

                if idx == 256:  # more gobos then values on a channel, must stop
                    DMX_Log.log.info("Only 255 gobos are supported at the moment")
                    break
                count = idx
                idx += 1

            if first:
                sequence = bpy.data.images.load(first)
                sequence["count"] = count
                sequence["attribute"] = attribute_name
                sequence["wheel"] = wheel.name
                result.append(sequence)

        return result

    @staticmethod
    def load2D(profile):
        dmx = bpy.context.scene.dmx
        current_path = dmx.get_addon_path()
        extract_to_folder_path = os.path.join(
            current_path, "assets", "models", profile.fixture_type_id
        )
        filename = f"{profile.thumbnail}.svg"
        obj = None
        if filename in profile._package.namelist():
            profile._package.extract(filename, extract_to_folder_path)
        else:
            # default 2D
            extract_to_folder_path = DMX_GDTF.getPrimitivesPath()
            filename = "thumbnail.svg"

        filepath = os.path.join(extract_to_folder_path, filename)
        try:
            bpy.ops.wm.grease_pencil_import_svg(filepath=filepath, scale=1)
        except Exception as e:
            print("INFO", e)
        try:
            bpy.ops.wm.gpencil_import_svg(filepath=filepath, scale=1)
        except Exception as e:
            print("INFO", e)

        if len(bpy.context.view_layer.objects.selected):
            obj = bpy.context.view_layer.objects.selected[0]
        if obj is not None:
            obj.name = "2D symbol"
            obj.users_collection[0].objects.unlink(obj)
            obj.rotation_euler[0] = -90 * (math.pi / 180)
        return obj

    @staticmethod
    def loadModel(profile, model):
        dmx = bpy.context.scene.dmx
        current_path = dmx.get_addon_path()
        extract_to_folder_path = os.path.join(
            current_path, "assets", "models", profile.fixture_type_id
        )
        obj_dimension = Vector((model.length, model.width, model.height))

        if model.file.extension.lower() == "3ds":
            inside_zip_path = f"models/3ds/{model.file.name}.{model.file.extension}"
            profile._package.extract(inside_zip_path, extract_to_folder_path)
            file_name = os.path.join(extract_to_folder_path, inside_zip_path)
            try:
                load_3ds(
                    file_name,
                    bpy.context,
                    FILTER={"MESH"},
                    KEYFRAME=False,
                    APPLY_MATRIX=False,
                )
            except Exception as e:
                DMX_Log.log.error(f"Error loading a 3DS file {profile.name} {e}")
                traceback.print_exception(e)
                bpy.ops.mesh.primitive_cube_add(size=0.1)
        else:
            inside_zip_path = f"models/gltf/{model.file.name}.{model.file.extension}"
            profile._package.extract(inside_zip_path, extract_to_folder_path)
            file_name = os.path.join(extract_to_folder_path, inside_zip_path)
            bpy.ops.import_scene.gltf(filepath=file_name)

        objs = list(bpy.context.selected_objects)

        # if the model is made up of multiple parts we must join them
        obj = DMX_GDTF.join_parts_apply_transforms(objs)

        # we should not set rotation to 0, models might be pre-rotated
        # obj.rotation_euler = Euler((0, 0, 0), 'XYZ')

        if obj.dimensions.x <= 0:
            DMX_Log.log.error(
                f"Model {obj.name} X size {obj.dimensions.x} <= 0. It will likely not work correctly."
            )
        if obj.dimensions.y <= 0:
            DMX_Log.log.error(
                f"Model {obj.name} Y size {obj.dimensions.y} <= 0. It will likely not work correctly."
            )
        if obj.dimensions.z <= 0:
            DMX_Log.log.error(
                f"Model {obj.name} Z size {obj.dimensions.z} <= 0. It will likely not work correctly."
            )

        scale_vector = obj.scale * obj_dimension
        factor = Vector(
            [scale_vector[val] / max(obj.dimensions[val], 1e-09) for val in range(3)]
        )
        if model.file.extension.lower() == "3ds":
            obj.data.transform(Matrix.Diagonal(factor).to_4x4())
        else:
            obj.scale = factor
        return obj

    @staticmethod
    def join_parts_apply_transforms(objs):
        """This ensures that glbs made of multiple parts are used as a single object.
        It feels convoluted but without this and all particular steps, some fixture files
        do not load correctly. Surely there is better way.
        Can be tested on files as per this issue: https://github.com/open-stage/blender-dmx/issues/67
        """

        # this first extra pass helps with Harmann fixture models but breaks other fixture.
        # meshes = [ob for ob in objs if ob.type=="MESH" and ob.data.vertices.items()]
        # if len(meshes)>1:
        #    bpy.context.view_layer.objects.active = meshes[0]
        #    bpy.ops.object.join()
        #    objs = list(bpy.context.selected_objects)

        join = 0
        single = None
        for ob in objs:
            mb = ob.matrix_basis  # apply some transforms
            if ob.type == "MESH" and ob.data.vertices.items():
                ob.select_set(True)  # objects for merging must be selected
                join += 1
                bpy.context.view_layer.objects.active = ob
                single = ob
                if hasattr(ob.data, "transform"):  # glb files
                    ob.data.transform(mb)
            ob.matrix_basis.identity()

        if join > 0:
            bpy.ops.object.join()  # join them together
            objs = list(bpy.context.view_layer.objects.selected)

        for obj in objs:
            obj.users_collection[0].objects.unlink(obj)

        if join == 1:
            objs = [single]  # if there was only a single object for merging

        for ob in objs:
            if ob.type == "MESH":
                obj = ob
                break

        return obj

    @staticmethod
    def buildCollection(profile, mode, display_beams, add_target):
        # Create model collection
        collection = bpy.data.collections.new(
            DMX_GDTF.getName(profile, mode, display_beams, add_target)
        )
        objs = {}
        # Get root geometry reference from the selected DMX Mode
        dmx_mode = profile.dmx_modes.get_mode_by_name(mode)

        # Handle if dmx mode doesn't exist (maybe this is MVR import and GDTF files were replaced)
        # use mode[0] as default
        if dmx_mode is None:
            dmx_mode = profile.dmx_modes[0]
            mode = dmx_mode.name

        root_geometry = profile.geometries.get_geometry_by_name(dmx_mode.geometry)
        has_gobos = False
        has_zoom = False

        dmx_channels_flattened = dmx_mode.dmx_channels
        virtual_channels = dmx_mode.virtual_channels

        for ch in dmx_channels_flattened:
            if "Gobo" in ch.attribute.str_link:
                has_gobos = True
            if "Zoom" in ch.attribute.str_link:
                has_zoom = True

        def load_geometries(geometry):
            """Load 3d models, primitives and shapes"""
            if geometry is None:
                return
            DMX_Log.log.info(f"loading geometry {geometry.name}")

            if isinstance(geometry, pygdtf.GeometryReference):
                reference = profile.geometries.get_geometry_by_name(geometry.geometry)
                geometry.model = geometry.model or reference.model
                # based on priority in the builder

                if hasattr(reference, "geometries"):
                    for sub_geometry in reference.geometries:
                        setattr(sub_geometry, "reference_root", str(geometry.name))
                        load_geometries(sub_geometry)

            if geometry.model is None:
                # Empty geometries are allowed as of GDTF 1.2
                # If the size is 0, Blender will discard it, set it to something tiny
                model = pygdtf.Model(
                    name=f"{sanitize_obj_name(geometry)}",
                    length=0.0001,
                    width=0.0001,
                    height=0.0001,
                    primitive_type=pygdtf.PrimitiveType("Cube"),
                )
            else:
                # Deepcopy the model because GeometryReference will modify the name
                # Perhaps this could be done conditionally
                # Also, we could maybe make a copy of the beam instance, if Blender supports it...
                model = copy.deepcopy(profile.models.get_model_by_name(geometry.model))

            if isinstance(geometry, pygdtf.GeometryReference):
                model.name = f"{sanitize_obj_name(geometry)}"

            obj = None
            primitive = model.primitive_type.value
            # Normalize 1.1 PrimitiveTypes
            # (From GDTF v1.1 on, the 1_1 was added to the end of primitive names, we just ignore them and use the same primitives)
            if primitive[-3:] == "1_1":
                primitive = primitive[:-3]
                model.primitive_type = pygdtf.PrimitiveType(primitive)

            if (model.primitive_type.value == "Undefined") or (
                model.file is not None
                and model.file.name != ""
                and model.primitive_type.value != "Pigtail"
            ):
                try:
                    obj = DMX_GDTF.loadModel(profile, model)
                except Exception as e:
                    DMX_Log.log.error(f"Error importing 3D model: {profile.name} {e}")
                    DMX_Log.log.exception(e)
                    if model.primitive_type.value == "Undefined":
                        model.primitive_type.value = "Cube"
                    if model.primitive_type.value in [
                        "Base",
                        "Conventional",
                        "Head",
                        "Yoke",
                    ]:
                        obj = DMX_GDTF.load_gdtf_primitive(model)
                    else:
                        obj = DMX_GDTF.load_blender_primitive(model)

            # BlenderDMX primitives
            elif model.primitive_type.value in ["Base", "Conventional", "Head", "Yoke"]:
                obj = DMX_GDTF.load_gdtf_primitive(model)
            # Blender primitives and a Pigtail
            else:
                obj = DMX_GDTF.load_blender_primitive(model)

            # If object was created
            if obj is not None:
                if sanitize_obj_name(geometry) == sanitize_obj_name(root_geometry):
                    obj["geometry_root"] = True
                    obj.hide_select = False
                else:
                    obj.hide_select = True
                obj.name = sanitize_obj_name(geometry)
                obj["geometry_type"] = get_geometry_type_as_string(geometry)
                obj["original_name"] = geometry.name
                if isinstance(geometry, pygdtf.GeometryReference):
                    obj["referenced_geometry"] = str(geometry.geometry)
                if model.primitive_type.value == "Pigtail":
                    obj["geometry_type"] = "pigtail"
                objs[sanitize_obj_name(geometry)] = obj

                # Apply transforms to ensure that models are correctly rendered
                # even if their transformations have not been applied prior to saving
                # without this, MVR fixtures are not loading correctly

                mb = obj.matrix_basis
                if hasattr(obj.data, "transform"):
                    obj.data.transform(mb)
                for c in obj.children:
                    c.matrix_local = mb @ c.matrix_local
                obj.matrix_basis.identity()

            if hasattr(geometry, "geometries"):
                for sub_geometry in geometry.geometries:
                    if hasattr(geometry, "reference_root"):
                        root_reference = getattr(geometry, "reference_root")
                        setattr(sub_geometry, "reference_root", root_reference)
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
            if isinstance(geometry, pygdtf.GeometryLaser):
                return "laser"
            if isinstance(geometry, pygdtf.GeometryAxis):
                return "axis"
            if isinstance(geometry, pygdtf.GeometryReference):
                geometry = profile.geometries.get_geometry_by_name(geometry.geometry)
                return get_geometry_type_as_string(geometry)
            return "normal"

        def create_camera(geometry):
            if sanitize_obj_name(geometry) not in objs:
                return
            obj_child = objs[sanitize_obj_name(geometry)]
            camera_data = bpy.data.cameras.new(name=f"{obj_child.name}")
            camera_object = bpy.data.objects.new("MediaCamera", camera_data)
            camera_object.hide_select = True
            camera_object.parent = obj_child
            camera_object.matrix_parent_inverse = obj_child.matrix_world.inverted()
            camera_object.rotation_euler[0] += math.radians(
                90
            )  # The media server camera-view points into the positive Y-direction (and Z-up).
            collection.objects.link(camera_object)

        def add_beam_controlling_parent_geometries(geometry):
            # create a list of parenting geometries with beam affecting attributes
            # this is a list with duplicate entries, we make unique list later
            # when adding it to the fixture

            if sanitize_obj_name(geometry) not in objs:
                return
            obj_child = objs[sanitize_obj_name(geometry)]
            if hasattr(geometry, "parent_name"):
                used_attributes = [
                    "Dimmer",
                    "ColorAdd_R",
                    "ColorAdd_G",
                    "ColorAdd_B",
                    "ColorSub_C",
                    "ColorSub_M",
                    "ColorAdd_Y",
                    "ColorAdd_W",
                    "ColorAdd_WW",
                    "ColorAdd_CW",
                    "ColorAdd_RY",
                    "ColorAdd_GY",
                    "ColorAdd_UV",
                    "ColorRGB_Red",
                    "ColorRGB_Blue",
                    "ColorRGB_Green",
                ]
                for ch in dmx_channels_flattened:
                    if ch.geometry == obj_child["original_name"]:
                        if any(
                            used_attr in ch.attribute.str_link
                            for used_attr in used_attributes
                        ):
                            obj_child["parent_geometries"] = []
                            return

                obj_child["parent_geometries"] = find_parent_geometries(
                    geometry, used_attributes
                )

        def find_parent_geometries(geometry, used_attributes):
            """this finds parent geometry of a beam type of geometry
            which does not have any color mixing/dimmig attributes attached"""

            if not hasattr(geometry, "parent_name"):
                return []
            parent_geometries = []

            for ch in dmx_channels_flattened:
                if ch.geometry == geometry.parent_name:
                    if any(
                        used_attr in ch.attribute.str_link
                        for used_attr in used_attributes
                    ):
                        parent_geometries.append(ch.geometry.replace(" ", "_"))

            if not parent_geometries and geometry.parent_name is not None:
                new_obj_name = geometry.parent_name.replace(" ", "_")
                if new_obj_name not in objs:
                    return []
                obj_child = objs[new_obj_name]

                geo = profile.geometries.get_geometry_by_name(
                    obj_child["original_name"]
                )
                return find_parent_geometries(geo, used_attributes)

            return parent_geometries

        def create_beam(geometry):
            if sanitize_obj_name(geometry) not in objs:
                return
            obj_child = objs[sanitize_obj_name(geometry)]
            if "beam" not in obj_child.name.lower():
                obj_child.name = f"Beam {obj_child.name}"

            if not display_beams:  # Don't even create beam objects to save resources
                return
            if any(geometry.beam_type.value == x for x in ["None", "Glow"]):
                return

            obj_child.visible_shadow = False
            light_data = bpy.data.lights.new(name=f"Spot {obj_child.name}", type="SPOT")

            light_data["parent_geometries"] = list(
                set(obj_child.get("parent_geometries", []))
            )

            light_data["flux"] = geometry.luminous_flux
            light_data.energy = light_data[
                "flux"
            ]  # set by default to full brightness for devices without dimmer
            light_data.use_custom_distance = True
            light_data.cutoff_distance = 23

            light_data.spot_blend = calculate_spot_blend(geometry)
            light_data.spot_size = math.radians(geometry.beam_angle)
            light_data.shadow_soft_size = geometry.beam_radius
            light_data["beam_radius"] = geometry.beam_radius  # save original beam size
            light_data["beam_radius_pin_sized_for_gobos"] = True
            # This allows the user to set this if wanted to prevent beam rendering differences
            light_data.shadow_buffer_clip_start = 0.0001
            if hasattr(
                light_data, "use_soft_falloff"
            ):  # ensure that beam has full diameter at the lense in Cycles for Blender 4.1 and up
                light_data.use_soft_falloff = False

            light_object = bpy.data.objects.new(name="Spot", object_data=light_data)
            light_object.hide_select = True
            light_object.parent = obj_child
            obj_child.matrix_parent_inverse = light_object.matrix_world.inverted()
            collection.objects.link(light_object)

            gobo_radius = 2.2 * 0.01 * math.tan(math.radians(geometry.beam_angle / 2))
            primitive_type = pygdtf.PrimitiveType("")
            primitive_type.value = "Plane"  # a small hack here
            goboGeometry = SimpleNamespace(
                name=f"gobo {sanitize_obj_name(geometry)}",
                length=gobo_radius,
                width=gobo_radius,
                height=0,
                primitive_type=primitive_type,
                beam_radius=geometry.beam_radius,
            )
            if has_gobos:
                create_gobo(geometry, goboGeometry)

        def create_bulb(geometry):
            if sanitize_obj_name(geometry) not in objs:
                return
            obj_child = objs[sanitize_obj_name(geometry)]
            if "beam" not in obj_child.name.lower():
                obj_child.name = f"Beam {obj_child.name}"

            if not display_beams:  # Don't even create beam objects to save resources
                return
            if any(geometry.beam_type.value == x for x in ["None", "Glow"]):
                return

            obj_child.visible_shadow = False
            light_data = bpy.data.lights.new(
                name=f"Spot {obj_child.name}", type="POINT"
            )

            light_data["parent_geometries"] = list(
                set(obj_child.get("parent_geometries", []))
            )

            light_data["flux"] = geometry.luminous_flux
            light_data.energy = light_data[
                "flux"
            ]  # set by default to full brightness for devices without dimmer

            light_data.shadow_soft_size = geometry.beam_radius
            light_data["beam_radius"] = geometry.beam_radius  # save original beam size
            light_data["beam_radius_pin_sized_for_gobos"] = True
            # This allows the user to set this if wanted to prevent beam rendering differences
            light_data.shadow_buffer_clip_start = 0.0001
            if hasattr(
                light_data, "use_soft_falloff"
            ):  # ensure that beam has full diameter at the lense in Cycles for Blender 4.1 and up
                light_data.use_soft_falloff = False

            light_object = bpy.data.objects.new(name="Spot", object_data=light_data)
            light_object.hide_select = True
            light_object.parent = obj_child
            obj_child.matrix_parent_inverse = light_object.matrix_world.inverted()
            collection.objects.link(light_object)

        def create_laser(geometry):
            if sanitize_obj_name(geometry) not in objs:
                return
            obj_child = objs[sanitize_obj_name(geometry)]
            if "laser" not in obj_child.name.lower():
                obj_child.name = f"Laser {obj_child.name}"
            obj_child.visible_shadow = False
            obj_child.rotation_mode = "XYZ"
            obj_child["beam_diameter"] = geometry.beam_diameter
            obj_child["rot_x"] = obj_child.rotation_euler[0]
            obj_child["rot_y"] = obj_child.rotation_euler[1]
            obj_child["rot_z"] = obj_child.rotation_euler[2]

        def create_gobo(geometry, goboGeometry):
            obj = DMX_GDTF.load_blender_primitive(goboGeometry)
            obj["geometry_type"] = "gobo"
            obj["beam_radius"] = goboGeometry.beam_radius
            obj["gobo_radius"] = goboGeometry.length
            obj.dimensions = (goboGeometry.length, goboGeometry.width, 0)
            obj.name = goboGeometry.name
            objs[sanitize_obj_name(goboGeometry)] = obj
            obj.location[2] += -0.01
            constraint_child_to_parent(geometry, goboGeometry)

        def calculate_spot_blend(geometry):
            """Return spot_blend value based on beam_type, maybe in the future
            we can calculate different value based on beam/field angle...?"""

            beam_type = geometry.beam_type.value
            if any(beam_type == x for x in ["Wash", "Fresnel", "PC"]):
                return 1.0
            return 0.0

        def add_child_position(geometry):
            """Add a child position"""

            # if (not sanitize_obj_name(geometry) in objs): return
            obj_child = objs[sanitize_obj_name(geometry)]
            geometry_mtx = Matrix(geometry.position.matrix)
            translate = geometry_mtx.to_translation()
            rotation = geometry_mtx.to_3x3().inverted()
            scale = geometry_mtx.to_scale()
            obj_child.matrix_local = Matrix.LocRotScale(translate, rotation, scale)
            obj_child.rotation_mode = "XYZ"
            obj_child["applied_rotation"] = obj_child.rotation_euler
            # baking into the object did not work, we store the rotation and re-apply it on pan/tilt in render()

        def constraint_child_to_parent(parent_geometry, child_geometry):
            if sanitize_obj_name(parent_geometry) not in objs:
                return
            obj_parent = objs[sanitize_obj_name(parent_geometry)]
            if sanitize_obj_name(child_geometry) not in objs:
                return
            obj_child = objs[sanitize_obj_name(child_geometry)]
            obj_child.parent = obj_parent
            obj_child.matrix_parent_inverse = obj_parent.matrix_world.inverted()

        def update_geometry(geometry):
            """Recursively update objects position, rotation and scale
            and define parent/child constraints. References are new
            sub-trees that must be processed and their root marked."""

            if geometry is None:
                return

            if not isinstance(geometry, pygdtf.GeometryReference):
                # geometry reference will have different geometry
                add_child_position(geometry)

            if isinstance(geometry, pygdtf.GeometryBeam):
                geometry.original_name = geometry.name
                add_beam_controlling_parent_geometries(geometry)

                if geometry.beam_angle == 360:
                    create_bulb(geometry)
                elif geometry.beam_angle > 180 and not has_zoom:
                    create_bulb(geometry)
                else:
                    create_beam(geometry)

            if isinstance(geometry, pygdtf.GeometryLaser):
                create_laser(geometry)
            elif isinstance(geometry, (pygdtf.GeometryMediaServerCamera)):
                create_camera(geometry)

            elif isinstance(geometry, pygdtf.GeometryReference):
                reference = copy.deepcopy(
                    profile.geometries.get_geometry_by_name(geometry.geometry)
                )
                reference.original_name = geometry.name
                if hasattr(geometry, "parent_name"):
                    reference.parent_name = geometry.parent_name
                reference.name = sanitize_obj_name(geometry)

                # apply position of the reference
                add_child_position(reference)

                # apply position of the referring geometry
                reference.position = geometry.position
                add_child_position(reference)

                if isinstance(reference, pygdtf.GeometryBeam):
                    add_beam_controlling_parent_geometries(geometry)
                    if reference.beam_angle == 360:
                        create_bulb(reference)
                    elif reference.beam_angle > 180 and not has_zoom:
                        create_bulb(reference)
                    else:
                        create_beam(reference)

                if isinstance(reference, pygdtf.GeometryLaser):
                    create_laser(reference)
                elif isinstance(reference, (pygdtf.GeometryMediaServerCamera)):
                    create_camera(reference)

                if hasattr(reference, "geometries"):
                    if len(reference.geometries) > 0:
                        for child_geometry in reference.geometries:
                            setattr(
                                child_geometry, "reference_root", str(reference.name)
                            )
                            constraint_child_to_parent(
                                reference, child_geometry
                            )  # parent, child
                            update_geometry(child_geometry)
                return

            if hasattr(geometry, "geometries"):
                if len(geometry.geometries) > 0:
                    for child_geometry in geometry.geometries:
                        if hasattr(geometry, "reference_root"):
                            root_reference = getattr(geometry, "reference_root")
                            setattr(child_geometry, "reference_root", root_reference)
                        constraint_child_to_parent(
                            geometry, child_geometry
                        )  # parent, child
                        update_geometry(child_geometry)

        # Load 3d objects from the GDTF profile
        # Also, we mostly omit links between geometry and channel function's geometry linking
        # For places, where for example multiple yokes would exist...
        load_geometries(root_geometry)
        update_geometry(root_geometry)

        def get_axis(attribute):
            axis_objects = []
            for obj in objs.values():
                for channel in dmx_channels_flattened:
                    if (
                        attribute == channel.attribute.str_link
                        and channel.geometry == obj.get("original_name", "None")
                    ):
                        obj["mobile_type"] = "head" if attribute == "Tilt" else "yoke"
                        obj["geometry_type"] = "axis"
                        axis_objects.append(obj)
                for channel in virtual_channels:
                    if attribute == channel.attribute and channel.geometry == obj.get(
                        "original_name", "None"
                    ):
                        obj["mobile_type"] = "head" if attribute == "Tilt" else "yoke"
                        obj["geometry_type"] = "axis"
                        axis_objects.append(obj)
            return axis_objects

        yokes = get_axis("Pan")
        heads = get_axis("Tilt")
        base = None
        if len(objs):
            base = next(ob for ob in objs.values() if ob.get("geometry_root", False))

        moving_parts = [ob for ob in objs.values() if ob.get("geometry_type") == "axis"]
        DMX_Log.log.info(f"Heads: {heads}, Yokes: {yokes}, Base: {base}")

        # Add target for manipulating fixture
        if add_target:
            target = bpy.data.objects.new("Target", None)
            collection.objects.link(target)
            target.empty_display_size = 0.5
            target.empty_display_type = "PLAIN_AXES"
            target.location = (0, 0, -2)

            for part in moving_parts:
                check_parent = part.parent and part.parent.get("mobile_type") == "head"
                check_pan = part.get("mobile_type") == "yoke"
                check_tilt = part.get("mobile_type") == "head"
                if not len(base.constraints) and (
                    check_pan
                    and not len(part.children)
                    or (not check_pan and not check_tilt)
                ):
                    constraint = base.constraints.new("TRACK_TO")
                    constraint.target = target
                    constraint.name = "FollowTarget"
                    continue
                else:
                    constraint = part.constraints.new("LOCKED_TRACK")
                    constraint.name = "FollowTarget"
                if check_tilt or (
                    check_parent
                    and part.parent.parent
                    and part.parent.parent.get("mobile_type") == "yoke"
                ):
                    constraint.track_axis = "TRACK_NEGATIVE_Z"
                else:
                    constraint.track_axis = "TRACK_NEGATIVE_Y"
                constraint.lock_axis = "LOCK_X" if check_tilt else "LOCK_Z"
                constraint.target = target

            if (
                not yokes
                and not heads
                and base is not None
                and not len(base.constraints)
            ):
                constraint = base.constraints.new("TRACK_TO")
                constraint.name = "FollowTarget"
                constraint.target = target

        # 2D thumbnail planning symbol
        obj = DMX_GDTF.load2D(profile)
        if obj is not None:
            # should probably always show it "on top"
            obj["2d_symbol"] = "all"
            objs["2d_symbol"] = obj
            obj.show_in_front = True
            obj.active_material.grease_pencil.show_stroke = True

            # svg.data.layers[...].frames[0].strokes[0]
            # add constraints
            constraint_copyLocation = obj.constraints.new(type="COPY_LOCATION")
            constraint_copyRotation = obj.constraints.new(type="COPY_ROTATION")
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
        revision = profile.revisions[-1].text if len(profile.revisions) else ""
        name = f"{profile.manufacturer}, {profile.name}, {dmx_mode}, {revision}, {'with_beams' if display_beams else 'without_beams'}, {'with_target' if add_target else 'without_target'}"
        # base64 encode the name as collections seems to have length limit
        # which causes collections not to be cached, thus slowing imports down
        name = hashlib.shake_256(name.encode()).hexdigest(5)
        return name
