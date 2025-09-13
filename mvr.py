# Copyright (C) 2023 Sebastian, vanous
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
import time
from pathlib import Path
from types import SimpleNamespace
import traceback

import bpy
import pymvr
from io_scene_3ds.import_3ds import load_3ds
from mathutils import Matrix

from .group import FixtureGroup
from .logging_setup import DMX_Log
from .util import create_unique_fixture_name
from .color_utils import xyY2rgbaa

auxData = {}
objectData = {}
direct_fixture_children = []


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


def get_matrix(obj, mtx):
    mtx_data = obj.matrix.matrix
    obj_mtx = Matrix(mtx_data).transposed()
    check_float = any(isinstance(i, float) for i in set().union(sum(mtx_data, [])))
    global_matrix = obj_mtx @ mtx if check_float else mtx
    return global_matrix


def trans_matrix(trans_mtx):
    mtx = list(trans_mtx)
    trans_matrix = Matrix(
        (mtx[:3] + [0], mtx[3:6] + [0], mtx[6:9] + [0], mtx[9:] + [1])
    ).transposed()
    return trans_matrix


def check_existing(node, collection):
    cls_name = node.__class__.__name__
    existing = any(col.get("UUID") == node.uuid for col in collection.children)
    if existing:
        for collect in collection.children:
            if collect.get("MVR Class") == cls_name:
                for obj in collect.all_objects:
                    transform = obj.get("Transform")
                    if transform is not None:
                        obj.matrix_world = trans_matrix(transform)
    return existing


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
):
    context = bpy.context
    viewlayer = context.view_layer
    viewport = viewlayer.layer_collection.children.get(layer_collection.name)
    if viewport is not None:
        viewlayer.active_layer_collection = viewport

    if hasattr(child_list, "trusses") and child_list.trusses:
        for truss_idx, truss_obj in enumerate(child_list.trusses):
            existing = check_existing(truss_obj, layer_collection)

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
                )

    # TODO: reuse
    if hasattr(child_list, "projectors") and child_list.projectors:
        for projector_idx, projector_obj in enumerate(child_list.projectors):
            existing = check_existing(projector_obj, layer_collection)

            if not existing and import_globals.import_projectors:
                process_mvr_object(
                    context,
                    mvr_scene,
                    projector_obj,
                    projector_idx,
                    mscale,
                    import_globals,
                    layer_collection,
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
                )
    if hasattr(child_list, "supports") and child_list.supports:
        for projector_idx, projector_obj in enumerate(child_list.supports):
            existing = check_existing(projector_obj, layer_collection)

            if not existing and import_globals.import_supports:
                process_mvr_object(
                    context,
                    mvr_scene,
                    projector_obj,
                    projector_idx,
                    mscale,
                    import_globals,
                    layer_collection,
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
                )

    if hasattr(child_list, "video_screens") and child_list.video_screens:
        for projector_idx, projector_obj in enumerate(child_list.video_screens):
            existing = check_existing(projector_obj, layer_collection)

            if not existing and import_globals.import_video_screens:
                process_mvr_object(
                    context,
                    mvr_scene,
                    projector_obj,
                    projector_idx,
                    mscale,
                    import_globals,
                    layer_collection,
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
                )

    if hasattr(child_list, "scene_objects") and child_list.scene_objects:
        for projector_idx, projector_obj in enumerate(child_list.scene_objects):
            existing = check_existing(projector_obj, layer_collection)

            if not existing and import_globals.import_scene_objects:
                process_mvr_object(
                    context,
                    mvr_scene,
                    projector_obj,
                    projector_idx,
                    mscale,
                    import_globals,
                    layer_collection,
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
                get_child_list(
                    dmx,
                    mscale,
                    mvr_scene,
                    group.child_list,
                    layergroup_idx,
                    folder_path,
                    import_globals,
                    layer_collection,
                    fixture_group,
                    group,
                )

    for obj in viewlayer.active_layer_collection.collection.all_objects:
        obj.select_set(True)


def process_mvr_object(
    context, mvr_scene, mvr_object, mvr_idx, mscale, import_globals, group_collect
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
                create_mvr_props(ob, class_name, obname, uid=uid, classing=classing)
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
    elif not symdef_id and mvr_object.geometries:
        symbols += mvr_object.geometries.symbol
        geometrys += mvr_object.geometries.geometry3d
    elif isinstance(mvr_object, pymvr.Symdef):
        symbols += mvr_object.child_list.symbol
        geometrys += mvr_object.child_list.geometry3d
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
        if not active_collect and not len(symbols):
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
            collection.objects.link(symbol_object)
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
                ref=symbol.uuid,
                classing=classing,
            )
            create_mvr_props(
                symbol_collect,
                symbol_type,
                name=name,
                uid=symbol.uuid,
                ref=symbol.symdef,
                classing=classing,
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
            target_mtx = target.matrix_world.copy()
            for ob in group_collect.objects:
                if (
                    ob.parent is None
                    and ob.get("MVR Class") == "FocusPoint"
                    and ob.get("UUID") == mvr_object.uuid
                ):
                    ob.parent = target
                    ob.matrix_parent_inverse = target.matrix_world.inverted()


def transform_objects(layers, mscale):
    def transform_matrix(mvr):
        obj_collect = objectData.get(mvr.uuid)
        if obj_collect is not None:
            global_mtx = get_matrix(mvr, mscale)
            for obj in obj_collect.objects:
                if obj.parent is None:
                    obj.matrix_world = global_mtx @ obj.matrix_world.copy()
                create_transform_property(obj)

    def collect_objects(childlist):
        for video_screen in childlist.video_screens:
            transform_matrix(video_screen)
        for projector in childlist.projectors:
            transform_matrix(projector)
        for support in childlist.supports:
            transform_matrix(support)
        for truss in childlist.trusses:
            transform_matrix(truss)
        for sceneobject in childlist.scene_objects:
            transform_matrix(sceneobject)
        for fixture in childlist.fixtures:
            transform_matrix(fixture)
        for group in childlist.group_objects:
            if hasattr(group, "child_list") and group.child_list:
                collect_objects(group.child_list)

    for layer in layers:
        if hasattr(layer, "child_list") and layer.child_list:
            collect_objects(layer.child_list)


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
        fixture.gdtf_spec = "BlenderDMX@LED_PAR_64@ver5.gdtf"
    for address in fixture.addresses.address:
        dmx.ensureUniverseExists(address.universe)

    add_target = import_globals.import_focus_points

    addresses = [
        SimpleNamespace(
            dmx_break=address.dmx_break,
            address=address.address,
            universe=address.universe,
        )
        for address in fixture.addresses.address
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
            mvr_position=fixture.matrix.matrix,
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
            position=fixture.matrix.matrix,
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
