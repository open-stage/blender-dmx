# Copyright (C) 2023 NRG Sille, Sebastian, vanous
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

import json
import os
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace
import traceback

import bpy
import pymvr
import uuid as py_uuid
from io_scene_3ds.import_3ds import load_3ds
from mathutils import Matrix

from .group import FixtureGroup
from .logging_setup import DMX_Log
from .util import create_unique_fixture_name
from .color_utils import xyY2rgbaa

auxData = {}
objectData = {}
direct_fixture_children = []
MVR_UNIT_SCALE = 0.001


def create_mvr_props(mvr_obj, cls, name="", uid=False, ref=None, classing=None):
    mvr_obj["MVR Class"] = cls
    if len(name):
        mvr_obj["MVR Name"] = name
    if ref:
        mvr_obj["Reference"] = ref
    if uid:
        mvr_obj["UUID"] = uid
    if classing:
        mvr_obj["classing"] = classing


def create_transform_property(obj):
    mtx_copy = obj.matrix_world.copy()
    translate = mtx_copy.to_translation()
    rotate = mtx_copy.transposed().to_3x3()
    trans_mtx = rotate[0][:] + rotate[1][:] + rotate[2][:] + translate[:]
    obj["Transform"] = trans_mtx


def create_local_transform_property(obj):
    mtx_copy = obj.matrix_world.copy()
    translate = mtx_copy.to_translation()
    rotate = mtx_copy.transposed().to_3x3()
    trans_mtx = rotate[0][:] + rotate[1][:] + rotate[2][:] + translate[:]
    obj["MVR Local Transform"] = trans_mtx


def get_matrix(obj, mtx):
    mtx_data = obj.matrix.matrix
    check_float = any(isinstance(i, float) for i in set().union(sum(mtx_data, [])))
    if check_float:
        scaled = [row[:] for row in mtx_data]
        if len(scaled) >= 4 and len(scaled[3]) >= 3:
            scaled[3][0] *= MVR_UNIT_SCALE
            scaled[3][1] *= MVR_UNIT_SCALE
            scaled[3][2] *= MVR_UNIT_SCALE
        obj_mtx = Matrix(scaled).transposed()
        global_matrix = obj_mtx @ mtx
    else:
        global_matrix = mtx
    return global_matrix


def trans_matrix(trans_mtx):
    mtx = list(trans_mtx)
    trans_matrix = Matrix(
        (mtx[:3] + [0], mtx[3:6] + [0], mtx[6:9] + [0], mtx[9:] + [1])
    ).transposed()
    return trans_matrix


def check_existing(node, collection, mscale):
    cls_name = node.__class__.__name__
    existing = any(col.get("UUID") == node.uuid for col in collection.children)
    if existing:
        node_mtx = get_matrix(node, mscale)
        for collect in collection.children:
            if collect.get("UUID") != node.uuid or collect.get("MVR Class") != cls_name:
                continue
            for obj in collect.all_objects:
                transform = obj.get("Transform")
                local_transform = obj.get("MVR Local Transform")
                if obj.parent is None and transform is not None:
                    obj.matrix_world = trans_matrix(transform)
                    continue
                if local_transform is not None:
                    obj.matrix_world = node_mtx @ trans_matrix(local_transform)
                    create_transform_property(obj)
        return True
    for collect in bpy.data.collections:
        if collect.get("UUID") == node.uuid:
            node_mtx = get_matrix(node, mscale)
            for obj in collect.all_objects:
                transform = obj.get("Transform")
                local_transform = obj.get("MVR Local Transform")
                if obj.parent is None and transform is not None:
                    obj.matrix_world = trans_matrix(transform)
                    continue
                if local_transform is not None:
                    obj.matrix_world = node_mtx @ trans_matrix(local_transform)
                    create_transform_property(obj)
            return True
    # Fallback: match existing objects by UUID even if collection is missing.
    for obj in collection.all_objects:
        if obj.get("UUID") == node.uuid:
            transform = obj.get("Transform")
            local_transform = obj.get("MVR Local Transform")
            if obj.parent is None and transform is not None:
                obj.matrix_world = trans_matrix(transform)
                return True
            if local_transform is not None:
                obj.matrix_world = get_matrix(node, mscale) @ trans_matrix(
                    local_transform
                )
                create_transform_property(obj)
            return True
    return False


def get_child_list(
    dmx,
    mscale,
    mvr_scene,
    child_list,
    layer_index,
    folder_path,
    import_globals,
    layer_collection,
    fixture_group=None,
    parent_object=None,
    parent_blender_object=None,
):
    context = bpy.context
    viewlayer = context.view_layer
    viewport = viewlayer.layer_collection.children.get(layer_collection.name)
    if viewport is not None:
        viewlayer.active_layer_collection = viewport

    if hasattr(child_list, "trusses") and child_list.trusses:
        for truss_idx, truss_obj in enumerate(child_list.trusses):
            existing = check_existing(truss_obj, layer_collection, mscale)

            if fixture_group is None:
                group_name = truss_obj.name or "Truss"
                fixture_group = FixtureGroup(group_name, truss_obj.uuid)

            if not existing and import_globals.import_trusses:
                process_mvr_object(
                    context,
                    mvr_scene,
                    truss_obj,
                    truss_idx,
                    mscale,
                    import_globals,
                    layer_collection,
                    parent_blender_object,
                )

            if hasattr(truss_obj, "child_list") and truss_obj.child_list:
                get_child_list(
                    dmx,
                    mscale,
                    mvr_scene,
                    truss_obj.child_list,
                    layer_index,
                    folder_path,
                    import_globals,
                    layer_collection,
                    fixture_group,
                    truss_obj,
                    parent_blender_object,
                )

    # TODO: reuse
    if hasattr(child_list, "projectors") and child_list.projectors:
        for projector_idx, projector_obj in enumerate(child_list.projectors):
            existing = check_existing(projector_obj, layer_collection, mscale)

            if not existing and import_globals.import_projectors:
                process_mvr_object(
                    context,
                    mvr_scene,
                    projector_obj,
                    projector_idx,
                    mscale,
                    import_globals,
                    layer_collection,
                    parent_blender_object,
                )

            if hasattr(projector_obj, "child_list") and projector_obj.child_list:
                get_child_list(
                    dmx,
                    mscale,
                    mvr_scene,
                    projector_obj.child_list,
                    layer_index,
                    folder_path,
                    import_globals,
                    layer_collection,
                    fixture_group,
                    projector_obj,
                    parent_blender_object,
                )
    if hasattr(child_list, "supports") and child_list.supports:
        for projector_idx, projector_obj in enumerate(child_list.supports):
            existing = check_existing(projector_obj, layer_collection, mscale)

            if not existing and import_globals.import_supports:
                process_mvr_object(
                    context,
                    mvr_scene,
                    projector_obj,
                    projector_idx,
                    mscale,
                    import_globals,
                    layer_collection,
                    parent_blender_object,
                )

            if hasattr(projector_obj, "child_list") and projector_obj.child_list:
                get_child_list(
                    dmx,
                    mscale,
                    mvr_scene,
                    projector_obj.child_list,
                    layer_index,
                    folder_path,
                    import_globals,
                    layer_collection,
                    fixture_group,
                    projector_obj,
                    parent_blender_object,
                )

    if hasattr(child_list, "video_screens") and child_list.video_screens:
        for projector_idx, projector_obj in enumerate(child_list.video_screens):
            existing = check_existing(projector_obj, layer_collection, mscale)

            if not existing and import_globals.import_video_screens:
                process_mvr_object(
                    context,
                    mvr_scene,
                    projector_obj,
                    projector_idx,
                    mscale,
                    import_globals,
                    layer_collection,
                    parent_blender_object,
                )

            if hasattr(projector_obj, "child_list") and projector_obj.child_list:
                get_child_list(
                    dmx,
                    mscale,
                    mvr_scene,
                    projector_obj.child_list,
                    layer_index,
                    folder_path,
                    import_globals,
                    layer_collection,
                    fixture_group,
                    projector_obj,
                    parent_blender_object,
                )

    if hasattr(child_list, "scene_objects") and child_list.scene_objects:
        for projector_idx, projector_obj in enumerate(child_list.scene_objects):
            existing = check_existing(projector_obj, layer_collection, mscale)

            if not existing and import_globals.import_scene_objects:
                process_mvr_object(
                    context,
                    mvr_scene,
                    projector_obj,
                    projector_idx,
                    mscale,
                    import_globals,
                    layer_collection,
                    parent_blender_object,
                )

            if hasattr(projector_obj, "child_list") and projector_obj.child_list:
                get_child_list(
                    dmx,
                    mscale,
                    mvr_scene,
                    projector_obj.child_list,
                    layer_index,
                    folder_path,
                    import_globals,
                    layer_collection,
                    fixture_group,
                    projector_obj,
                    parent_blender_object,
                )

    if hasattr(child_list, "fixtures") and child_list.fixtures:
        for fixture_idx, fixture in enumerate(child_list.fixtures):
            focus_points = []
            if fixture.focus is not None:
                focus_points.extend(
                    [fp for fp in child_list.focus_points if fp.uuid == fixture.focus]
                )
            if import_globals.import_fixtures:
                add_mvr_fixture(
                    dmx,
                    mscale,
                    mvr_scene,
                    folder_path,
                    fixture,
                    fixture_idx,
                    layer_index,
                    focus_points,
                    import_globals,
                    fixture_group,
                    parent_object,
                    layer_collection,
                )

            if hasattr(fixture, "child_list") and fixture.child_list:
                get_child_list(
                    dmx,
                    mscale,
                    mvr_scene,
                    fixture.child_list,
                    layer_index,
                    folder_path,
                    import_globals,
                    layer_collection,
                    fixture_group,
                    fixture,
                    parent_blender_object,
                )

    if hasattr(child_list, "group_objects") and child_list.group_objects:
        for group_idx, group in enumerate(child_list.group_objects):
            if hasattr(group, "child_list") and group.child_list:
                layergroup_idx = f"{layer_index}-{group_idx}"
                group_name = group.name or "Group"
                group_name = (
                    "%s %d" % (group_name, group_idx) if group_idx >= 1 else group_name
                )
                fixture_group = FixtureGroup(group_name, group.uuid)
                group_collection = bpy.data.collections.new(group_name)
                create_mvr_props(
                    group_collection,
                    "GroupObject",
                    name=group.name,
                    uid=group.uuid,
                    classing=group.classing if hasattr(group, "classing") else None,
                )
                layer_collection.children.link(group_collection)
                group_empty = bpy.data.objects.new(group_name, None)
                create_mvr_props(
                    group_empty,
                    "GroupObject",
                    name=group.name,
                    uid=group.uuid,
                    classing=group.classing if hasattr(group, "classing") else None,
                )
                group_empty.matrix_world = get_matrix(group, mscale)
                create_transform_property(group_empty)
                if parent_blender_object is not None:
                    group_empty.parent = parent_blender_object
                    group_empty.matrix_parent_inverse = (
                        parent_blender_object.matrix_world.inverted()
                    )
                group_collection.objects.link(group_empty)
                get_child_list(
                    dmx,
                    mscale,
                    mvr_scene,
                    group.child_list,
                    layergroup_idx,
                    folder_path,
                    import_globals,
                    group_collection,
                    fixture_group,
                    group,
                    group_empty,
                )

    for obj in viewlayer.active_layer_collection.collection.all_objects:
        obj.select_set(True)


def process_mvr_object(
    context,
    mvr_scene,
    mvr_object,
    mvr_idx,
    mscale,
    import_globals,
    group_collect,
    parent_blender_object=None,
):
    uid = mvr_object.uuid
    name = mvr_object.name
    viewlayer = context.view_layer
    object_data = bpy.data.objects
    data_collect = bpy.data.collections
    class_name = mvr_object.__class__.__name__
    layer_collect = viewlayer.layer_collection
    active_layer = viewlayer.active_layer_collection
    symdef_id = isinstance(mvr_object, pymvr.Symdef)
    focus_id = isinstance(mvr_object, pymvr.FocusPoint)
    classing = mvr_object.classing if hasattr(mvr_object, "classing") else None
    dmx = bpy.context.scene.dmx
    current_path = dmx.get_addon_path()
    folder = os.path.join(current_path, "assets", "models", "mvr")
    DMX_Log.log.info(f"creating {class_name}... {name}")

    def add_mvr_object(idx, node, mtx, collect, file=""):
        imported_objects = []
        item_name = Path(file).name
        mesh_name = Path(file).stem
        mesh_data = bpy.data.meshes
        node_type = node.__class__.__name__
        gltf = file.split(".")[-1] == "glb"
        scale_factor = 0.001 if file.split(".")[-1] == "3ds" else 1.0
        mesh_exist = next((msh for msh in mesh_data if msh.name == mesh_name), False)
        exist = any(ob.data and ob.data.name == mesh_name for ob in collect.objects)
        world_matrix = mtx @ Matrix.Scale(scale_factor, 4)
        DMX_Log.log.info(f"adding {node_type}... {mesh_name}")

        if not exist:
            if mesh_exist:
                mesh_id = mesh_exist.get("MVR Name", mesh_name)
                new_object = object_data.new(mesh_id, mesh_exist)
                imported_objects.append(new_object)
            else:
                file_name = os.path.join(folder, file)
                if os.path.isfile(file_name):
                    if gltf:
                        bpy.ops.import_scene.gltf(filepath=file_name)
                    else:
                        load_3ds(file_name, context, KEYFRAME=False, APPLY_MATRIX=False)
                    imported_objects.extend(list(viewlayer.objects.selected))
            for ob in imported_objects:
                ob.rotation_mode = "XYZ"
                obname = ob.name.split(".")[0]
                create_mvr_props(
                    ob,
                    class_name,
                    obname,
                    uid=uid,
                    ref=item_name,
                    classing=classing,
                )
                if ob.data:
                    ob.data.name = mesh_name
                    create_mvr_props(
                        ob.data,
                        node_type,
                        obname,
                        uid=uid,
                        ref=item_name,
                        classing=classing,
                    )
                if (
                    len(ob.users_collection)
                    and ob.name in ob.users_collection[0].objects
                ):
                    ob.users_collection[0].objects.unlink(ob)
                elif ob.name in layer_collect.collection.objects:
                    active_layer.collection.objects.unlink(ob)
                if ob.parent is None:  # only gltf files can be pre transformed
                    if gltf or ob.type != "MESH":
                        ob.matrix_world = world_matrix @ ob.matrix_world.copy()
                    else:
                        ob.matrix_world = world_matrix
                create_local_transform_property(ob)
                create_transform_property(ob)
                if ob.name not in collect.objects:
                    collect.objects.link(ob)
            objectData.setdefault(uid, collect)
            imported_objects.clear()
            viewlayer.update()
        return collect

    file = ""
    symbols = []
    geometrys = []
    active_collect = None
    context_matrix = mscale
    collection = group_collect
    dmx = bpy.context.scene.dmx
    previous_mvr_object = None
    for existing_mvr_object in dmx.mvr_objects:
        if existing_mvr_object.uuid == mvr_object.uuid:
            previous_mvr_object = existing_mvr_object
            DMX_Log.log.info("Updating existing mvr object")
            for child in existing_mvr_object.collection.children:
                for obj in child.objects:
                    bpy.data.objects.remove(obj)
            break

    if previous_mvr_object:
        dmx_mvr_object = previous_mvr_object
    else:
        dmx_mvr_object = dmx.mvr_objects.add()
        dmx_mvr_object.name = name
        dmx_mvr_object.uuid = mvr_object.uuid
        dmx_mvr_object.object_type = mvr_object.__class__.__name__
        dmx_mvr_object.collection = bpy.data.collections.new(mvr_object.uuid)

    if isinstance(mvr_object, pymvr.Symbol):
        symbols.append(mvr_object)
    elif isinstance(mvr_object, pymvr.Geometry3D):
        geometrys.append(mvr_object)
    elif symdef_id:
        symbols += mvr_object.child_list.symbol
        geometrys += mvr_object.child_list.geometry3d
    elif mvr_object.geometries:
        symbols += mvr_object.geometries.symbol
        geometrys += mvr_object.geometries.geometry3d
    else:
        DMX_Log.log.info(f"Handle this in the future")

    if focus_id:
        active_collect = group_collect
    elif symdef_id:
        create_mvr_props(
            group_collect, class_name, name=name, uid=uid, classing=classing
        )
        active_collect = next(
            (col for col in data_collect if col.get("Reference") == uid), False
        )
        if not active_collect:
            active_collect = data_collect.get(uid)
            if active_collect is None:
                active_collect = data_collect.new(uid)
        if active_collect.get("MVR Class") is None:
            create_mvr_props(active_collect, class_name, uid=uid, classing=classing)
        active_collect.hide_render = True
    elif not focus_id and (len(geometrys) + len(symbols)) > 1:
        if mvr_object.name is not None and len(mvr_object.name):
            obj_name = "%s - %s %d" % (class_name, mvr_object.name, mvr_idx)
        else:
            obj_name = "%s %d" % (class_name, mvr_idx) if mvr_idx >= 1 else class_name
        DMX_Log.log.info(f"creating extra collection {obj_name}")
        active_collect = bpy.data.collections.new(obj_name)
        create_mvr_props(
            active_collect, class_name, name=name, uid=uid, classing=classing
        )
        group_collect.children.link(active_collect)
        collection = active_collect

    if active_collect is None:
        active_collect = next(
            (col for col in data_collect if col.get("UUID") == uid), False
        )
        if not active_collect:
            reference = collection.get("UUID")
            active_collect = data_collect.new(name)
            create_mvr_props(
                active_collect,
                class_name,
                name=name,
                uid=uid,
                ref=reference,
                classing=classing,
            )
            if (
                collection is not None
                and active_collect != collection
                and active_collect.name not in collection.children
            ):
                collection.children.link(active_collect)

    for idx, geometry in enumerate(geometrys):
        file = geometry.file_name
        extract_mvr_object(file, mvr_scene, folder, import_globals)
        obj_mtx = (
            get_matrix(mvr_object, mscale) if focus_id else get_matrix(geometry, mscale)
        )
        object_collect = add_mvr_object(idx, geometry, obj_mtx, active_collect, file)
        if (
            object_collect
            and object_collect.name not in collection.children
            and object_collect != collection
        ):
            collection.children.link(object_collect)

    for idx, symbol in enumerate(symbols):
        symbol_type = symbol.__class__.__name__
        symbol_mtx = get_matrix(symbol, context_matrix)
        if not symdef_id:
            symbol_mtx = get_matrix(mvr_object, symbol_mtx)
        symbol_collect = data_collect.get(symbol.symdef)
        if symbol_collect:
            if not len(name):
                name = "%s %d" % (class_name, idx) if idx >= 1 else class_name
            symbol_object = object_data.new(name, None)
            symbol_target_collect = active_collect or collection
            if symbol_target_collect is not None:
                symbol_target_collect.objects.link(symbol_object)
            symbol_object.matrix_world = symbol_mtx
            create_transform_property(symbol_object)
            symbol_object.empty_display_size = 0.001
            symbol_object.empty_display_type = "ARROWS"
            symbol_object.instance_type = "COLLECTION"
            symbol_object.instance_collection = symbol_collect
            create_mvr_props(
                symbol_object,
                symbol_type,
                name=name,
                uid=uid,
                ref=symbol.symdef,
                classing=classing,
            )
            create_mvr_props(
                symbol_collect,
                symbol_type,
                name=name,
                uid=symbol.symdef,
                ref=symbol.uuid,
                classing=classing,
            )

    if parent_blender_object is not None and active_collect is not None:
        for obj in active_collect.all_objects:
            if obj.parent is None and obj != parent_blender_object:
                obj.parent = parent_blender_object
                obj.matrix_parent_inverse = (
                    parent_blender_object.matrix_world.inverted()
                )

    if focus_id:
        target = next(
            (
                ob
                for ob in group_collect.objects
                if ob.data is None and ob.get("Target ID") == mvr_object.uuid
            ),
            None,
        )
        if target:
            all_focus_points_geo_uuid = dmx.find_class_by_name("Focus Points")
            target_mtx = target.matrix_world.copy()
            for ob in group_collect.objects:
                if (
                    ob.parent is None
                    and ob.get("MVR Class") == "FocusPoint"
                    and ob.get("UUID") == mvr_object.uuid
                ):
                    ob["classing"] = all_focus_points_geo_uuid
                    ob.parent = target
                    ob.matrix_parent_inverse = target.matrix_world.inverted()


def transform_objects(layers, mscale):
    def transform_matrix(mvr, parent_mtx):
        obj_collect = objectData.get(mvr.uuid)
        if obj_collect is not None:
            global_mtx = get_matrix(mvr, parent_mtx)
            for obj in obj_collect.objects:
                if obj.parent is None:
                    obj.matrix_world = global_mtx @ obj.matrix_world.copy()
                create_transform_property(obj)

    def collect_objects(childlist, parent_mtx):
        for video_screen in childlist.video_screens:
            transform_matrix(video_screen, parent_mtx)
        for projector in childlist.projectors:
            transform_matrix(projector, parent_mtx)
        for support in childlist.supports:
            transform_matrix(support, parent_mtx)
        for truss in childlist.trusses:
            transform_matrix(truss, parent_mtx)
        for sceneobject in childlist.scene_objects:
            transform_matrix(sceneobject, parent_mtx)
        for fixture in childlist.fixtures:
            transform_matrix(fixture, parent_mtx)
        for group in childlist.group_objects:
            if hasattr(group, "child_list") and group.child_list:
                collect_objects(group.child_list, parent_mtx)

    for layer in layers:
        if hasattr(layer, "child_list") and layer.child_list:
            layer_mtx = get_matrix(layer, mscale)
            collect_objects(layer.child_list, layer_mtx)


def extract_mvr_object(file, mvr_scene, folder, import_globals):
    if f"{file}" in mvr_scene._package.namelist():
        if file not in import_globals.extracted.keys():
            mvr_scene._package.extract(file, folder)
            import_globals.extracted[file] = 0
        else:
            import_globals.extracted[file] += 1


def extract_mvr_textures(mvr_scene, folder):
    for name in mvr_scene._package.namelist():
        if name.endswith(".png"):
            mvr_scene._package.extract(name, folder)


def add_mvr_fixture(
    dmx,
    mscale,
    mvr_scene,
    folder_path,
    fixture,
    fixture_idx,
    layer_idx,
    focus_points,
    import_globals,
    fixture_group=None,
    parent_object=None,
    layer_collection=None,
):
    """Add fixture to the scene"""

    existing_fixture = None
    for _fixture in dmx.fixtures:
        if _fixture.uuid == fixture.uuid:
            existing_fixture = _fixture
            DMX_Log.log.info(f"Update existing fixture {fixture.uuid}")
            break

    if f"{fixture.gdtf_spec}" in mvr_scene._package.namelist():
        if fixture.gdtf_spec not in import_globals.extracted.keys():
            mvr_scene._package.extract(fixture.gdtf_spec, folder_path)
            import_globals.extracted[fixture.gdtf_spec] = 0
        else:
            import_globals.extracted[fixture.gdtf_spec] += 1
    else:
        # if the file is not in the MVR package, use an RGBW Par64
        DMX_Log.log.error(
            f"{fixture.gdtf_spec} not in mvr_scene._package.namelist, using a generic PAR"
        )
        fixture.gdtf_spec = "BlenderDMX@LED_PAR_64@ver6.gdtf"
    for address in fixture.addresses.addresses:
        dmx.ensureUniverseExists(address.universe)

    add_target = import_globals.import_focus_points

    addresses = [
        SimpleNamespace(
            dmx_break=address.dmx_break,
            address=address.address,
            universe=address.universe,
        )
        for address in fixture.addresses.addresses
        if address.address > 0
    ]
    null_matrix = pymvr.Matrix([[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]])
    # ensure that fixture is not scaled to 0
    if fixture.matrix == null_matrix:
        fixture.matrix = pymvr.Matrix(0)

    """Get Focuspoints."""
    focus_point = mscale
    if len(focus_points):
        focus_point = get_matrix(focus_points[0], mscale)
    fixture_matrix = get_matrix(fixture, mscale)

    if existing_fixture is not None:
        # TODO: we should not rename the fixture on import unless if the user wants it
        # but we must ensure that the name is unique in the collection
        unique_name = create_unique_fixture_name(fixture.name)
        if isinstance(fixture.color, str):
            fixture.color = pymvr.Color(str_repr=fixture.color)

        color_rgb = xyY2rgbaa(fixture.color)
        gel_color = [c / 255 for c in color_rgb] + [1]
        existing_fixture.build(
            unique_name,
            fixture.gdtf_spec,
            fixture.gdtf_mode or "",
            addresses,
            gel_color,
            True,
            add_target,
            mvr_position=fixture_matrix,
            focus_point=focus_point,
            uuid=fixture.uuid,
            fixture_id=fixture.fixture_id,
            custom_id=fixture.custom_id,
            fixture_id_numeric=fixture.fixture_id_numeric,
            unit_number=fixture.unit_number,
            classing=fixture.classing,
        )
    else:
        unique_name = f"{fixture.name} {layer_idx}-{fixture_idx}"
        unique_name = create_unique_fixture_name(unique_name)
        if isinstance(fixture.color, str):
            fixture.color = pymvr.Color(str_repr=fixture.color)
        color_rgb = xyY2rgbaa(fixture.color)
        gel_color = [c / 255 for c in color_rgb] + [1]
        dmx.addFixture(
            unique_name,
            fixture.gdtf_spec,
            fixture.gdtf_mode or "",
            addresses,
            gel_color,
            True,
            add_target,
            position=fixture_matrix,
            focus_point=focus_point,
            uuid=fixture.uuid,
            fixture_id=fixture.fixture_id,
            custom_id=fixture.custom_id,
            fixture_id_numeric=fixture.fixture_id_numeric,
            unit_number=fixture.unit_number,
            classing=fixture.classing,
        )

    if parent_object is not None:
        direct_fixture_children.append(
            SimpleNamespace(
                child_uuid=fixture.uuid,
                parent_uuid=parent_object.uuid,
            )
        )

    if fixture_group is not None:
        if fixture_group.name in dmx.groups:
            group = dmx.groups[fixture_group.name]
        else:
            group = dmx.groups.add()
            group.name = fixture_group.name
            group.uuid = fixture_group.uuid
        if group.dump:
            dump = json.loads(group.dump)
        else:
            dump = []
        dump.append(fixture.uuid)
        group.dump = json.dumps(dump)

        added_fixture = dmx.findFixtureByUUID(fixture.uuid)
        if added_fixture:
            added_fixture["layer_name"] = layer_collection.name
            added_fixture["layer_uuid"] = layer_collection.get("UUID", None)

    if len(focus_points) and focus_points[0].geometries:
        focus_fixture = dmx.findFixtureByUUID(fixture.uuid)
        if focus_fixture:
            DMX_Log.log.info(f"importing FocusPoint geometry... {fixture.name}")
            focus_target = next(
                (tg.object for tg in focus_fixture.objects if tg.name == "Target"), None
            )
            if focus_target:
                focus_target["Geometry Type"] = "Target"
                focus_target["Target ID"] = fixture.focus
            process_mvr_object(
                bpy.context,
                mvr_scene,
                focus_points[0],
                fixture_idx,
                mscale,
                import_globals,
                focus_fixture.collection,
            )


def perform_direct_parenting(dmx):
    for item in direct_fixture_children:
        child_object = None
        parent_object = None
        child_fixture = dmx.findFixtureByUUID(item.child_uuid)
        if child_fixture:
            try:
                child_object = child_fixture.objects["Root"].object
            except:
                ...
        parent_object = next(
            (
                obj
                for obj in bpy.data.objects
                if obj.get("UUID", "") == item.parent_uuid
            ),
            None,
        )
        if child_object is not None and parent_object is not None:
            child_object.parent = parent_object
            try:
                child_object.matrix_parent_inverse = (
                    parent_object.matrix_world.inverted()
                )
            except:
                ...


def load_mvr(
    dmx,
    file_name,
    import_focus_points,
    import_fixtures,
    import_trusses,
    import_scene_objects,
    import_projectors,
    import_supports,
    import_video_screens,
):
    import_globals = SimpleNamespace(
        extracted={},
        import_focus_points=import_focus_points,
        import_fixtures=import_fixtures,
        import_trusses=import_trusses,
        import_scene_objects=import_scene_objects,
        import_projectors=import_projectors,
        import_supports=import_supports,
        import_video_screens=import_video_screens,
    )

    bpy.ops.object.select_all(action="DESELECT")
    for obj in bpy.data.objects:
        obj.select_set(False)
    # clear possible existing selections in Blender

    imported_layers = []
    context = bpy.context
    start_time = time.time()
    mscale = Matrix.Identity(4)
    viewlayer = context.view_layer
    data_collect = bpy.data.collections
    scene_collect = context.scene.collection
    view_collect = viewlayer.layer_collection
    layer_collect = view_collect.collection
    mvr_scene = pymvr.GeneralSceneDescription(file_name)
    aux_dir = scene_collect.children.get("AUXData")
    dmx = bpy.context.scene.dmx
    current_path = dmx.get_addon_path()
    folder_path = os.path.join(current_path, "assets", "profiles")
    media_folder_path = os.path.join(current_path, "assets", "models", "mvr")
    extract_mvr_textures(mvr_scene, media_folder_path)
    if hasattr(mvr_scene, "scene") and mvr_scene.scene:
        auxdata = mvr_scene.scene.aux_data
        layers = mvr_scene.scene.layers
    else:
        auxdata = None
        layers = []

    if auxdata is not None:
        classes = auxdata.classes
        symdefs = auxdata.symdefs
    else:
        classes = []
        symdefs = []

    for ob in viewlayer.objects.selected:
        ob.select_set(False)

    for _class in classes:
        if _class.name not in dmx.classing:
            new_class = dmx.classing.add()
            new_class.name = _class.name
            new_class.uuid = _class.uuid

    if "Focus Points" not in dmx.classing:
        new_class = dmx.classing.add()
        new_class.name = "Focus Points"
        new_class.uuid = str(py_uuid.uuid4())

    for aux_idx, symdef in enumerate(symdefs):
        if aux_dir and symdef.name in aux_dir.children:
            aux_collection = aux_dir.children.get(symdef.name)
        elif symdef.name in data_collect:
            aux_collection = data_collect.get(symdef.name)
        else:
            aux_collection = data_collect.new(symdef.name)

        auxData.setdefault(symdef.uuid, aux_collection)
        process_mvr_object(
            context, mvr_scene, symdef, aux_idx, mscale, import_globals, aux_collection
        )

        if hasattr(symdef, "child_list") and symdef.child_list:
            get_child_list(
                dmx,
                mscale,
                mvr_scene,
                symdef.child_list,
                aux_idx,
                folder_path,
                import_globals,
                aux_collection,
            )

    for layer_idx, layer in enumerate(layers):
        layer_class = layer.__class__.__name__
        layer_collection = next(
            (col for col in data_collect if col.get("UUID") == layer.uuid), False
        )
        if not layer_collection:
            layer_collection = data_collect.new(layer.name)
            create_mvr_props(layer_collection, layer_class, layer.name, layer.uuid)
            layer_collect.children.link(layer_collection)

        group_name = layer.name or "Layer"
        fixture_group = FixtureGroup(group_name, layer.uuid)
        get_child_list(
            dmx,
            mscale,
            mvr_scene,
            layer.child_list,
            layer_idx,
            folder_path,
            import_globals,
            layer_collection,
            fixture_group,
            layer,
        )

        if (
            len(layer_collection.all_objects) == 0
            and layer_collection.name in layer_collect.children
        ):
            layer_collect.children.unlink(layer_collection)

    transform_objects(layers, mscale)
    perform_direct_parenting(dmx)

    if auxData.items():
        aux_type = auxdata.__class__.__name__
        if "AUXData" in data_collect:
            aux_directory = data_collect.get("AUXData")
        else:
            aux_directory = data_collect.new("AUXData")
            create_mvr_props(aux_directory, aux_type)
            layer_collect.children.link(aux_directory)
        for uid, auxcollect in auxData.items():
            try:
                if auxcollect and auxcollect.name not in aux_directory.children:
                    aux_directory.children.link(auxcollect)
            except Exception as e:
                traceback.print_exception(e)

            sym_collect = data_collect.get(uid)
            if sym_collect:
                sym_name = sym_collect.get("MVR Name", "")
                if sym_collect.name in layer_collect.children:
                    layer_collect.children.unlink(sym_collect)
                elif sym_collect.name not in auxcollect.children:
                    auxcollect.children.link(sym_collect)
                    if sym_name in (None, "None"):
                        sym_name = "None Layer"
                if sym_name:
                    # TODO: check if this is correct. Was added to prevent breakage of imports from Production Assist
                    sym_collect.name = sym_name

    for laycollect in layer_collect.children:
        if laycollect.get("MVR Class") is not None:
            imported_layers.append(laycollect)
            for cidx, collect in enumerate(laycollect.children):
                for col in collect.children:
                    col_name = col.get("MVR Name")
                    check_name = col.name[-3:].isdigit() and col.name[-4] == "."
                    if check_name and col_name in data_collect:
                        clean_name = col.name.split(".")[0]
                        col.name = "%s %d" % (clean_name, cidx)

    for idx, collect in enumerate(imported_layers):
        for obid, obj in enumerate(collect.all_objects):
            obj_name = obj.name.split(".")[0]
            if obj.is_instancer:
                transform = obj.get("Transform")
                if transform:
                    obj.matrix_world = trans_matrix(transform)
                insta_name = "%s %d" % (obj_name, idx) if idx >= 1 else obj_name
                obj.name = "%s_%d" % (insta_name.split("_")[0], obid)
            elif obj.name[-3:].isdigit() and obj.name[-4] == ".":
                obj.name = "%s %d" % (obj_name, obid)

    for view in view_collect.children:
        if view.name == "AUXData":
            for childs in view.children:
                for collect in childs.children:
                    collect.hide_viewport = True

    auxData.clear()
    objectData.clear()
    direct_fixture_children.clear()
    viewlayer.update()
    imported_layers.clear()
    if mvr_scene is not None:
        if hasattr(mvr_scene, "_package"):
            if mvr_scene._package is not None:
                mvr_scene._package.close()

    DMX_Log.log.info(f"MVR scene loaded in {time.time() - start_time}.4f sec.")


def export_mvr(
    dmx,
    file_name,
    export_focus_points=True,
    selected_fixtures_only=False,
    export_fixtures_only=False,
):
    start_time = time.time()
    bpy.context.window_manager.dmx.pause_render = (
        True  # this stops the render loop, to prevent slowness and crashes
    )
    # reset 3D cursor to eliminate offset issues
    bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
    bpy.context.scene.cursor.rotation_euler = (0.0, 0.0, 0.0)

    addon_path = dmx.get_addon_path()
    folder_path = os.path.join(addon_path, "assets", "profiles")
    universe_add = dmx.is_there_universe_zero()

    try:
        assets_list = []
        mvr_layers = pymvr.Layers()
        mvr = pymvr.GeneralSceneDescriptionWriter()
        mvr.serialize_user_data(pymvr.UserData())

        def matrix_world_to_mvr(matrix_world):
            matrix = [list(col) for col in matrix_world.col]
            if len(matrix) >= 4 and len(matrix[3]) >= 3:
                matrix[3][0] *= 1000.0
                matrix[3][1] *= 1000.0
                matrix[3][2] *= 1000.0
            return matrix

        def set_local_transform(obj):
            mtx_copy = obj.matrix_world.copy()
            translate = mtx_copy.to_translation()
            rotate = mtx_copy.transposed().to_3x3()
            trans_mtx = rotate[0][:] + rotate[1][:] + rotate[2][:] + translate[:]
            obj["MVR Local Transform"] = trans_mtx

        def export_glb_object(obj, file_path):
            if obj.type != "MESH":
                return
            context = bpy.context
            selected = list(context.selected_objects)
            active = context.view_layer.objects.active
            bpy.ops.object.select_all(action="DESELECT")
            obj.select_set(True)
            context.view_layer.objects.active = obj
            try:
                bpy.ops.export_scene.gltf(
                    filepath=file_path,
                    export_format="GLB",
                    export_selected=True,
                )
            except TypeError:
                bpy.ops.export_scene.gltf(
                    filepath=file_path,
                    export_format="GLB",
                    use_selection=True,
                )
            bpy.ops.object.select_all(action="DESELECT")
            for item in selected:
                item.select_set(True)
            context.view_layer.objects.active = active

        def resolve_geometry_file(obj, temp_dir, used_names):
            file_name = obj.get("Reference", None)
            if not file_name and obj.data is not None:
                file_name = obj.data.get("Reference", None)
            if file_name:
                base_name = Path(file_name).stem
            else:
                obj_uuid = obj.get("UUID", None)
                base_name = obj_uuid or obj.name
            safe_name = base_name.replace(" ", "_")
            file_name = f"{safe_name}.glb"
            if file_name in used_names:
                used_names[file_name] += 1
                file_name = f"{safe_name}_{used_names[file_name]}.glb"
            else:
                used_names[file_name] = 0
            file_path = os.path.join(temp_dir, file_name)
            export_glb_object(obj, file_path)
            return file_name, file_path

        def build_geometries(collection, files_list, temp_dir, used_names):
            geometries = pymvr.Geometries()
            geometry_objects = list({obj for obj in collection.all_objects})
            for obj in geometry_objects:
                if obj.get("MVR Class") == "GroupObject":
                    continue
                if obj.get("geometry_root") or obj.get("geometry_type"):
                    continue
                if obj.type == "EMPTY" and obj.data is None:
                    symdef_uuid = obj.get("Reference")
                    if not symdef_uuid and obj.instance_collection:
                        symdef_uuid = obj.instance_collection.get("UUID")
                    if symdef_uuid:
                        geometries.symbol.append(
                            pymvr.Symbol(
                                uuid=obj.get("UUID", str(py_uuid.uuid4())),
                                symdef=symdef_uuid,
                                matrix=pymvr.Matrix(
                                    matrix_world_to_mvr(obj.matrix_world)
                                ),
                            )
                        )
                        continue
                if obj.type == "MESH":
                    set_local_transform(obj)
                    file_name, file_path = resolve_geometry_file(
                        obj, temp_dir, used_names
                    )
                    if file_name:
                        geometries.geometry3d.append(
                            pymvr.Geometry3D(
                                file_name=file_name,
                                matrix=pymvr.Matrix(0),
                            )
                        )
                        files_list.append((file_path, file_name))
                elif obj.type == "EMPTY" and obj.get("MVR Class") == "Symbol":
                    symdef_uuid = obj.get("Reference", None)
                    if symdef_uuid:
                        geometries.symbol.append(
                            pymvr.Symbol(
                                uuid=obj.get("UUID", str(py_uuid.uuid4())),
                                symdef=symdef_uuid,
                                matrix=pymvr.Matrix(
                                    matrix_world_to_mvr(obj.matrix_world)
                                ),
                            )
                        )
            return geometries

        def extend_geometries_from_uuid(
            uuid_value, geometries, files_list, temp_dir, used_names
        ):
            if not uuid_value:
                return
            for obj in bpy.data.objects:
                if obj.get("UUID") != uuid_value:
                    continue
                if obj.get("MVR Class") == "GroupObject":
                    continue
                if obj.get("geometry_root") or obj.get("geometry_type"):
                    continue
                if obj.type == "EMPTY" and obj.data is None:
                    symdef_uuid = obj.get("Reference")
                    if not symdef_uuid and obj.instance_collection:
                        symdef_uuid = obj.instance_collection.get("UUID")
                    if symdef_uuid:
                        geometries.symbol.append(
                            pymvr.Symbol(
                                uuid=obj.get("UUID", str(py_uuid.uuid4())),
                                symdef=symdef_uuid,
                                matrix=pymvr.Matrix(
                                    matrix_world_to_mvr(obj.matrix_world)
                                ),
                            )
                        )
                    continue
                if obj.type == "MESH":
                    file_name, file_path = resolve_geometry_file(
                        obj, temp_dir, used_names
                    )
                    if file_name:
                        geometries.geometry3d.append(
                            pymvr.Geometry3D(
                                file_name=file_name,
                                matrix=pymvr.Matrix(0),
                            )
                        )
                        files_list.append((file_path, file_name))

        def build_symdef_child_list(collection, files_list, temp_dir, used_names):
            child_list = pymvr.SymdefChildList()
            symdef_objects = list({obj for obj in collection.all_objects})
            for obj in symdef_objects:
                if obj.get("MVR Class") == "GroupObject":
                    continue
                if obj.get("geometry_root") or obj.get("geometry_type"):
                    continue
                if obj.type == "MESH":
                    set_local_transform(obj)
                    file_name, file_path = resolve_geometry_file(
                        obj, temp_dir, used_names
                    )
                    if file_name:
                        child_list.geometry3d.append(
                            pymvr.Geometry3D(
                                file_name=file_name,
                                matrix=pymvr.Matrix(0),
                            )
                        )
                        files_list.append((file_path, file_name))
                elif obj.type == "EMPTY" and obj.get("MVR Class") == "Symbol":
                    symdef_uuid = obj.get("Reference", None)
                    if symdef_uuid:
                        child_list.symbol.append(
                            pymvr.Symbol(
                                uuid=obj.get("UUID", str(py_uuid.uuid4())),
                                symdef=symdef_uuid,
                                matrix=pymvr.Matrix(
                                    matrix_world_to_mvr(obj.matrix_world)
                                ),
                            )
                        )
            return child_list

        def get_or_create_layer(name, uuid_):
            for layer in mvr_layers:
                if uuid_ and layer.uuid == uuid_:
                    return layer
                if not uuid_ and layer.name == name:
                    return layer
            layer = pymvr.Layer(name=name, uuid=uuid_)
            layer.child_list = pymvr.ChildList()
            mvr_layers.append(layer)
            return layer

        def iter_layer_collections():
            for collection in bpy.context.scene.collection.children:
                if collection.get("MVR Class") == "Layer":
                    yield collection

        layer_collections = list(iter_layer_collections())
        if not layer_collections:
            root_collection = bpy.context.scene.collection
            if not root_collection.get("UUID"):
                root_collection["UUID"] = str(py_uuid.uuid4())
            if not root_collection.get("MVR Class"):
                root_collection["MVR Class"] = "Layer"
            if not root_collection.get("MVR Name"):
                root_collection["MVR Name"] = root_collection.name
            layer_collections = [root_collection]
        for collection in layer_collections:
            get_or_create_layer(
                collection.get("MVR Name", collection.name),
                collection.get("UUID", None),
            )

        for dmx_fixture in dmx.fixtures:
            if selected_fixtures_only and not dmx_fixture.is_selected():
                continue
            fixture_layer_name = dmx_fixture.get("layer_name", "DMX")
            fixture_layer_uuid = dmx_fixture.get("layer_uuid", None)
            if fixture_layer_uuid is not None:
                use_layer = next(
                    (l for l in mvr_layers if l.uuid == fixture_layer_uuid), None
                )
                if not use_layer:
                    use_layer = get_or_create_layer(
                        fixture_layer_name, fixture_layer_uuid
                    )
            else:  # no layer in fixture
                use_layer = next(
                    (l for l in mvr_layers if l.name == fixture_layer_name), None
                )  # we should get "DMX" layer if exists
                if not use_layer:  # create new DMX layer
                    use_layer = get_or_create_layer("DMX", str(py_uuid.uuid4()))

            child_list = use_layer.child_list

            fixture_object = dmx_fixture.to_mvr_fixture(universe_add=universe_add)
            focus_point = dmx_fixture.focus_to_mvr_focus_point()
            if export_focus_points and focus_point is not None:
                child_list.focus_points.append(focus_point)
            child_list.fixtures.append(fixture_object)
            if fixture_object.gdtf_spec:
                file_path = os.path.join(folder_path, fixture_object.gdtf_spec)
                assets_list.append((file_path, fixture_object.gdtf_spec))

        mvr_class_map = {
            "SceneObject": pymvr.SceneObject,
            "Truss": pymvr.Truss,
            "Support": pymvr.Support,
            "Projector": pymvr.Projector,
            "VideoScreen": pymvr.VideoScreen,
        }

        def is_fixture_collection(collection):
            if collection.get("Company"):
                return True
            return any(
                obj.get("geometry_root") or obj.get("geometry_type")
                for obj in collection.objects
            )

        def add_objects_from_collection(
            layer, collection, temp_dir, used_names, export_objects=True
        ):
            for child in collection.children:
                child_class = child.get("MVR Class")
                if child_class == "GroupObject":
                    group_matrix = pymvr.Matrix(0)
                    group_empty = next(
                        (
                            obj
                            for obj in child.objects
                            if obj.get("MVR Class") == "GroupObject"
                            and obj.type == "EMPTY"
                        ),
                        None,
                    )
                    if not child.get("UUID"):
                        child["UUID"] = str(py_uuid.uuid4())
                    if not child.get("MVR Class"):
                        child["MVR Class"] = "GroupObject"
                    if not child.get("MVR Name"):
                        child["MVR Name"] = child.name
                    if group_empty is not None:
                        if not group_empty.get("UUID"):
                            group_empty["UUID"] = child["UUID"]
                        if not group_empty.get("MVR Class"):
                            group_empty["MVR Class"] = "GroupObject"
                        if not group_empty.get("MVR Name"):
                            group_empty["MVR Name"] = child["MVR Name"]
                        group_matrix = pymvr.Matrix(
                            matrix_world_to_mvr(group_empty.matrix_world)
                        )
                    group = pymvr.GroupObject(
                        name=child["MVR Name"],
                        uuid=child["UUID"],
                        matrix=group_matrix,
                        classing=child.get("classing", None),
                    )
                    group.child_list = pymvr.ChildList()
                    layer.child_list.group_objects.append(group)
                    add_objects_from_collection(
                        group, child, temp_dir, used_names, export_objects=False
                    )
                    continue
                if child_class in mvr_class_map:
                    mvr_cls = mvr_class_map[child_class]
                    if not child.get("UUID"):
                        child["UUID"] = str(py_uuid.uuid4())
                    if not child.get("MVR Class"):
                        child["MVR Class"] = child_class
                    if not child.get("MVR Name"):
                        child["MVR Name"] = child.name
                    child_list = layer.child_list
                    geometries = build_geometries(
                        child, assets_list, temp_dir, used_names
                    )
                    if (
                        not geometries.geometry3d
                        and not geometries.symbol
                        and child.get("UUID")
                    ):
                        extend_geometries_from_uuid(
                            child.get("UUID"),
                            geometries,
                            assets_list,
                            temp_dir,
                            used_names,
                        )
                    mvr_object = mvr_cls(
                        name=child.get("MVR Name", child.name),
                        uuid=child.get("UUID", str(py_uuid.uuid4())),
                        matrix=pymvr.Matrix(0),
                        classing=child.get("classing", None),
                        geometries=geometries,
                    )
                    if child_class == "SceneObject":
                        child_list.scene_objects.append(mvr_object)
                    elif child_class == "Truss":
                        child_list.trusses.append(mvr_object)
                    elif child_class == "Support":
                        child_list.supports.append(mvr_object)
                    elif child_class == "Projector":
                        child_list.projectors.append(mvr_object)
                    elif child_class == "VideoScreen":
                        child_list.video_screens.append(mvr_object)

                    add_objects_from_collection(
                        layer, child, temp_dir, used_names, export_objects=False
                    )
                    continue

                if child_class is None and child.objects:
                    if is_fixture_collection(child):
                        add_objects_from_collection(layer, child, temp_dir, used_names)
                        continue
                    if not child.get("UUID"):
                        child["UUID"] = str(py_uuid.uuid4())
                    if not child.get("MVR Class"):
                        child["MVR Class"] = "SceneObject"
                    if not child.get("MVR Name"):
                        child["MVR Name"] = child.name
                    geometries = build_geometries(
                        child, assets_list, temp_dir, used_names
                    )
                    mvr_object = pymvr.SceneObject(
                        name=child["MVR Name"],
                        uuid=child["UUID"],
                        matrix=pymvr.Matrix(0),
                        geometries=geometries,
                    )
                    layer.child_list.scene_objects.append(mvr_object)

                    add_objects_from_collection(
                        layer, child, temp_dir, used_names, export_objects=False
                    )
                    continue

                add_objects_from_collection(
                    layer, child, temp_dir, used_names, export_objects=True
                )

            if not export_objects:
                return

            for obj in collection.objects:
                if obj.get("MVR Class") or obj.get("geometry_root"):
                    continue
                if obj.get("geometry_type"):
                    continue
                if obj.type == "EMPTY" and obj.get("MVR Class") == "GroupObject":
                    continue
                if obj.type != "MESH":
                    continue
                set_local_transform(obj)
                if not obj.get("UUID"):
                    obj["UUID"] = str(py_uuid.uuid4())
                if not obj.get("MVR Class"):
                    obj["MVR Class"] = "SceneObject"
                if not obj.get("MVR Name"):
                    obj["MVR Name"] = obj.name
                obj_uuid = obj["UUID"]
                obj_collection = next(
                    (
                        col
                        for col in bpy.data.collections
                        if col.get("UUID") == obj_uuid
                    ),
                    None,
                )
                if obj_collection is None:
                    obj_collection = bpy.data.collections.new(obj["MVR Name"])
                    obj_collection["UUID"] = obj_uuid
                    obj_collection["MVR Class"] = "SceneObject"
                    obj_collection["MVR Name"] = obj["MVR Name"]
                    if obj_collection.name not in collection.children:
                        collection.children.link(obj_collection)
                if obj.name not in obj_collection.objects:
                    obj_collection.objects.link(obj)
                file_name, file_path = resolve_geometry_file(obj, temp_dir, used_names)
                if file_name:
                    geometries = pymvr.Geometries(
                        geometry3d=[
                            pymvr.Geometry3D(
                                file_name=file_name,
                                matrix=pymvr.Matrix(0),
                            )
                        ]
                    )
                    assets_list.append((file_path, file_name))
                    mvr_object = pymvr.SceneObject(
                        name=obj["MVR Name"],
                        uuid=obj["UUID"],
                        matrix=pymvr.Matrix(0),
                        geometries=geometries,
                    )
                    layer.child_list.scene_objects.append(mvr_object)

        with tempfile.TemporaryDirectory(prefix="blenderdmx_mvr_") as temp_dir:
            used_geometry_names = {}
            if not export_fixtures_only:
                for collection in layer_collections:
                    layer = get_or_create_layer(
                        collection.get("MVR Name", collection.name),
                        collection.get("UUID", None),
                    )
                    add_objects_from_collection(
                        layer, collection, temp_dir, used_geometry_names
                    )

            aux_data = pymvr.AUXData()
            for class_item in dmx.classing:
                if class_item.uuid and class_item.name:
                    aux_data.classes.append(
                        pymvr.Class(uuid=class_item.uuid, name=class_item.name)
                    )

            aux_collection = bpy.data.collections.get("AUXData")
            if aux_collection:
                for sym_collection in aux_collection.children:
                    if sym_collection.get("MVR Class") == "Symdef":
                        symdef = pymvr.Symdef(
                            name=sym_collection.get("MVR Name", sym_collection.name),
                            uuid=sym_collection.get("UUID", str(py_uuid.uuid4())),
                            child_list=build_symdef_child_list(
                                sym_collection,
                                assets_list,
                                temp_dir,
                                used_geometry_names,
                            ),
                        )
                        aux_data.symdefs.append(symdef)

            scene = pymvr.Scene(layers=mvr_layers, aux_data=aux_data)
            mvr.serialize_scene(scene)
            mvr.files_list = list(set(assets_list))
            mvr.write_mvr(file_name)
            file_size = Path(file_name).stat().st_size

    except Exception as e:
        traceback.print_exception(e)
        return SimpleNamespace(ok=False, error=str(e))

    bpy.context.window_manager.dmx.pause_render = False  # re-enable render loop
    print("INFO", "MVR scene exported in %.4f sec." % (time.time() - start_time))
    return SimpleNamespace(ok=True, file_size=file_size)
