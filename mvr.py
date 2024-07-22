#    Copyright vanous, NRG Sille
#
#    This file is part of BlenderDMX.
#
#    BlenderDMX is free software: you can redistribute it and/or modify it
#    under the terms of the GNU General Public License as published by the Free
#    Software Foundation, either version 3 of the License, or (at your option)
#    any later version.
#
#    BlenderDMX is distributed in the hope that it will be useful, but WITHOUT
#    ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
#    FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
#    more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program. If not, see <https://www.gnu.org/licenses/>.


import os
import bpy
import time
import json
from . import pymvr
from pathlib import Path
from mathutils import Matrix
from .logging import DMX_Log
from .group import FixtureGroup
from .io_scene_3ds.import_3ds import load_3ds
from .util import xyY2rgbaa, create_unique_fixture_name


auxData = {}
objectData = {}

def create_mvr_props(mvr_obj, cls, name="", uid=False, ref=None):
    mvr_obj['MVR Class'] = cls
    if len(name):
        mvr_obj['MVR Name'] = name
    if ref:
        mvr_obj['Reference'] = ref
    if uid:
        mvr_obj['UUID'] = uid


def get_matrix(obj, mtx):
    mtx_data = obj.matrix.matrix
    obj_mtx = Matrix(mtx_data).transposed()
    check_float = any(isinstance(i, float) for i in set().union(sum(mtx_data, [])))
    global_matrix = obj_mtx @ mtx if check_float else mtx
    return global_matrix


def get_child_list(dmx, mscale, mvr_scene, child_list, layer_index, folder_path,
                   extracted, layer_collection, fixture_group=None):

    context = bpy.context
    viewlayer = context.view_layer
    viewport = viewlayer.layer_collection.children.get(layer_collection.name)
    if viewport is not None:
        viewlayer.active_layer_collection = viewport

    for truss_idx, truss_obj in enumerate(child_list.trusses):
        print("creating Truss... %s" % truss_obj.name)

        if fixture_group is None:
            group_name = truss_obj.name or "Truss"
            group_name =  '%s %d' % (group_name, truss_idx) if scene_idx >= 1 else group_name
            fixture_group = FixtureGroup(group_name, truss_obj.uuid)

        process_mvr_object(context, mvr_scene, truss_obj, truss_idx,
                           mscale, extracted, layer_collection)

        if hasattr(truss_obj, "child_list") and truss_obj.child_list:
            get_child_list(dmx, mscale, mvr_scene, truss_obj.child_list, layer_index,
                           folder_path, extracted, layer_collection, fixture_group)

    for scene_idx, scene_obj in enumerate(child_list.scene_objects):

        process_mvr_object(context, mvr_scene, scene_obj, scene_idx,
                           mscale, extracted, layer_collection)

        if hasattr(scene_obj, "child_list") and scene_obj.child_list:
            get_child_list(dmx, mscale, mvr_scene, scene_obj.child_list, layer_index,
                           folder_path, extracted, layer_collection, fixture_group)

    for fixture_idx, fixture in enumerate(child_list.fixtures):
        focus_point = mscale
        if fixture.focus is not None:
            focus_points = [fp for fp in child_list.focus_points if fp.uuid == fixture.focus]
            if len(focus_points):
                focus_point = get_matrix(focus_points[0], mscale)

        add_mvr_fixture(dmx, mvr_scene, folder_path, fixture, fixture_idx,
                        layer_index, focus_point, extracted, fixture_group)

        if hasattr(fixture, "child_list") and fixture.child_list:
            get_child_list(dmx, mscale, mvr_scene, fixture.child_list, layer_index,
                           folder_path, extracted, layer_collection, fixture_group)

    for group_idx, group in enumerate(child_list.group_objects):
        if hasattr(group, "child_list") and group.child_list:
            layergroup_idx = f"{layer_index}-{group_idx}"
            group_name = group.name or "Group"
            group_name =  '%s %d' % (group_name, group_idx) if group_idx >= 1 else group_name
            fixture_group = FixtureGroup(group_name, group.uuid)
            get_child_list(dmx, mscale, mvr_scene, group.child_list, layergroup_idx,
                           folder_path, extracted, layer_collection, fixture_group)

    for obj in viewlayer.active_layer_collection.collection.all_objects:
        obj.select_set(True)


def process_mvr_object(context, mvr_scene, mvr_object, mvr_idx, mscale, extracted, group_collect):

    uid = mvr_object.uuid
    name = mvr_object.name
    viewlayer = context.view_layer
    object_data = bpy.data.objects
    data_collect = bpy.data.collections
    scene_collect = context.scene.collection
    class_name = mvr_object.__class__.__name__
    layer_collect = viewlayer.layer_collection
    active_layer = viewlayer.active_layer_collection
    symdef_id = isinstance(mvr_object, pymvr.Symdef)
    current_path = os.path.dirname(os.path.realpath(__file__))
    folder = os.path.join(current_path, "assets", "models", "mvr")
    print("creating %s... %s" % (class_name, name))  

    def add_mvr_object(idx, node, mtx, collect, file=""):
        node_type = node.__class__.__name__
        item_name = Path(file).name
        mesh_name = Path(file).stem
        mesh_data = bpy.data.meshes
        imported_objects = []
        if not symdef_id:
            collect['Reference'] = mesh_name
        reference = collect.get('Reference')
        scale_factor = 0.001 if file.split('.')[-1] == '3ds' else 1.0
        mesh_exist = next((msh for msh in mesh_data if msh.name == mesh_name), False)
        exist = any(ob for ob in object_data if ob.get('Reference') and reference == uid)
        world_matrix = mtx @ Matrix.Scale(scale_factor, 4)
        print("adding %s... %s" % (node_type, mesh_name))

        if mesh_exist:
            if not exist:
                new_obj = next((ob for ob in object_data if ob.get('UUID') == reference), False)
                if not new_obj:
                    mesh_id = mesh_exist.get('MVR Name')
                    new_obj = object_data.new(mesh_id, mesh_exist)
                imported_objects.append(new_obj)
        elif not exist:
            file_name = os.path.join(folder, file)
            if os.path.isfile(file_name):
                if file.split('.')[-1] == 'glb':
                    bpy.ops.import_scene.gltf(filepath=file_name)
                else:
                    load_3ds(file_name, bpy.context, KEYFRAME=False, APPLY_MATRIX=False)
                imported_objects.extend(list(viewlayer.objects.selected))
        for ob in imported_objects:
            ob.rotation_mode = 'XYZ'
            obname = ob.name.split('.')[0]
            create_mvr_props(ob, class_name, obname, mesh_name, uid)
            if ob.data:
                ob.data.name = mesh_name
                create_mvr_props(ob.data, node_type, obname, uid, item_name) 
            if ob.name in ob.users_collection[0].objects:
                ob.users_collection[0].objects.unlink(ob)
            elif ob.name in layer_collect.collection.objects:
                active_layer.collection.objects.unlink(ob)
            if ob.parent is None:
                ob.matrix_world = world_matrix
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

    if isinstance(mvr_object, pymvr.Symbol):
        symbols.append(mvr_object)
    elif isinstance(mvr_object, pymvr.Geometry3D):
        geometrys.append(mvr_object)
    elif not symdef_id and mvr_object.geometries:
        symbols += mvr_object.geometries.symbol
        geometrys += mvr_object.geometries.geometry3d
    else:
        symbols += mvr_object.symbol
        geometrys += mvr_object.geometry3d

    if symdef_id:
        create_mvr_props(group_collect, class_name, name, uid)
        active_collect = next((col for col in data_collect if col.get('Reference') == uid), False)
        if not active_collect:
            active_collect = data_collect.get(uid)
            if active_collect is None:
                active_collect = data_collect.new(uid)
        if active_collect.get('MVR Class') is None:
            create_mvr_props(active_collect, class_name, uid)
        active_collect.hide_render = True
    elif (len(geometrys) + len(symbols)) > 1:
        if mvr_object.name is not None and len(mvr_object.name):
            obj_name = '%s - %s %d' % (class_name, mvr_object.name, mvr_idx)
        else:
            obj_name = '%s %d' % (class_name, mvr_idx) if mvr_idx >= 1 else class_name
        print("creating extra collection", obj_name)
        active_collect = bpy.data.collections.new(obj_name)
        create_mvr_props(active_collect, class_name, name, uid)
        group_collect.children.link(active_collect)

    if active_collect is None:
        active_collect = next((col for col in data_collect if col.get('UUID') == uid), False)
        if not active_collect and not len(symbols):
            active_collect = data_collect.new(name)
            create_mvr_props(active_collect, class_name, name, uid)

    for idx, geometry in enumerate(geometrys):
        file = geometry.file_name
        obj_mtx = get_matrix(geometry, mscale)
        extract_mvr_object(file, mvr_scene, folder, extracted)
        object_collect = add_mvr_object(idx, geometry, obj_mtx, active_collect, file)
        if object_collect and object_collect.name not in group_collect.children: 
            group_collect.children.link(object_collect)

    for idx, symbol in enumerate(symbols):
        symbol_type = symbol.__class__.__name__
        symbol_mtx = get_matrix(symbol, context_matrix)
        if not symdef_id:
            symbol_mtx = get_matrix(mvr_object, symbol_mtx)
        symbol_collect = data_collect.get(symbol.symdef)
        if symbol_collect:
            if not len(name):
                name = '%s %d' % (class_name, idx) if idx >= 1 else class_name
            symbol_object = object_data.new(name, None)
            group_collect.objects.link(symbol_object)
            symbol_object.matrix_world = symbol_mtx
            symbol_object.empty_display_size = 0.01
            symbol_object.empty_display_type = 'ARROWS'
            symbol_object.instance_type = 'COLLECTION'
            symbol_object.instance_collection = symbol_collect
            create_mvr_props(symbol_object, symbol_type, name, uid, symbol.uuid)
            create_mvr_props(symbol_collect, symbol_type, name, symbol.uuid, symbol.symdef)


def transform_objects(layers, mscale):

    def transform_matrix(mvr):
        obj_collect = objectData.get(mvr.uuid)
        if obj_collect is not None:
            global_mtx = get_matrix(mvr, mscale)
            for obj in obj_collect.objects:
                obj.matrix_world = global_mtx @ obj.matrix_world.copy()

    def collect_objects(childlist):
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


def extract_mvr_object(file, mvr_scene, folder, extracted):
    if f"{file}" in mvr_scene._package.namelist():
        if file not in extracted.keys():
            mvr_scene._package.extract(file, folder)
            extracted[file] = 0
        else:
            extracted[file] += 1


def extract_mvr_textures(mvr_scene, folder):
    for name in mvr_scene._package.namelist():
        if name.endswith(".png"):
            mvr_scene._package.extract(name, folder)


def add_mvr_fixture(dmx, mvr_scene, folder_path, fixture, fixture_index, layer_index, focus_point, already_extracted_files, fixture_group=None):
    """Add fixture to the scene"""

    existing_fixture = None
    for _fixture in dmx.fixtures:
        if _fixture.uuid == fixture.uuid:
            existing_fixture = _fixture
            DMX_Log.log.info(f"Update existing fixture {fixture.uuid}")
            break

    if f"{fixture.gdtf_spec}" in mvr_scene._package.namelist():
        if fixture.gdtf_spec not in already_extracted_files.keys():
            mvr_scene._package.extract(fixture.gdtf_spec, folder_path)
            already_extracted_files[fixture.gdtf_spec] = 0
        else:
            already_extracted_files[fixture.gdtf_spec] += 1
    else:
        # if the file is not in the MVR package, use an RGBW Par64
        fixture.gdtf_spec = "BlenderDMX@LED_PAR_64_RGBW@v0.3.gdtf"

    dmx.ensureUniverseExists(fixture.addresses[0].universe)

    if existing_fixture is not None:
        existing_fixture.build(
            f"{fixture.name} {layer_index}-{fixture_index}",
            fixture.gdtf_spec,
            fixture.gdtf_mode,
            fixture.addresses[0].universe,
            fixture.addresses[0].address,
            xyY2rgbaa(fixture.color),
            True,
            True,
            mvr_position=fixture.matrix.matrix,
            focus_point=focus_point,
            uuid=fixture.uuid,
            fixture_id=fixture.fixture_id,
            custom_id=fixture.custom_id,
            fixture_id_numeric=fixture.fixture_id_numeric,
            unit_number=fixture.unit_number,
        )
    else:
        dmx.addFixture(
            f"{fixture.name} {layer_index}-{fixture_index}",
            fixture.gdtf_spec,
            fixture.addresses[0].universe,
            fixture.addresses[0].address,
            fixture.gdtf_mode,
            xyY2rgbaa(fixture.color),
            True,
            True,
            position=fixture.matrix.matrix,
            focus_point=focus_point,
            uuid=fixture.uuid,
            fixture_id=fixture.fixture_id,
            custom_id=fixture.custom_id,
            fixture_id_numeric=fixture.fixture_id_numeric,
            unit_number=fixture.unit_number,
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


def load_mvr(dmx, file_name):

    extracted = {}
    imported_layers = []
    context = bpy.context
    start_time = time.time()
    mscale = Matrix.Identity(4)
    viewlayer = context.view_layer
    data_collect = bpy.data.collections
    scene_collect = context.scene.collection
    view_collect = viewlayer.layer_collection
    layer_collect = view_collect.collection
    active_layer = viewlayer.active_layer_collection
    mvr_scene = pymvr.GeneralSceneDescription(file_name)
    aux_dir = scene_collect.children.get('AUXData')
    current_path = os.path.dirname(os.path.realpath(__file__))
    folder_path = os.path.join(current_path, "assets", "profiles")
    media_folder_path = os.path.join(current_path, "assets", "models", "mvr")
    extract_mvr_textures(mvr_scene, media_folder_path)
    mvr_layer = mvr_scene.layers
    auxdata = mvr_scene.aux_data
    classes = auxdata.classes
    symdefs = auxdata.symdefs

    for aux_idx, symdef in enumerate(symdefs):
        if aux_dir and symdef.name in aux_dir.children:
            aux_collection = aux_dir.children.get(symdef.name)
        elif symdef.name in data_collect:
            aux_collection = data_collect.get(symdef.name)
        else:
            aux_collection = data_collect.new(symdef.name)

        auxData.setdefault(symdef.uuid, aux_collection)
        process_mvr_object(context, mvr_scene, symdef, aux_idx,
                           mscale, extracted, aux_collection)

        if hasattr(symdef, "child_list") and symdef.child_list:
            get_child_list(dmx, mscale, mvr_scene, symdef.child_list,
                           aux_idx, folder_path, extracted, aux_collection)

    for layer_idx, layer in enumerate(mvr_scene.layers):
        layer_class = layer.__class__.__name__
        layer_collection = next((col for col in data_collect if col.get('UUID') == layer.uuid), False)
        if not layer_collection:
            layer_collection = data_collect.new(layer.name)
            create_mvr_props(layer_collection, layer_class, layer.name, layer.uuid)
            layer_collect.children.link(layer_collection)

        group_name = layer.name or "Layer"
        fixture_group = FixtureGroup(group_name, layer.uuid)
        get_child_list(dmx, mscale, mvr_scene, layer.child_list, layer_idx,
                       folder_path, extracted, layer_collection, fixture_group)

        if len(layer_collection.all_objects) == 0 and layer_collection.name in layer_collect.children:
            layer_collect.children.unlink(layer_collection)

    transform_objects(mvr_scene.layers, mscale)

    if auxData.items():
        aux_type = auxdata.__class__.__name__
        if 'AUXData' in data_collect:
            aux_directory = data_collect.get('AUXData')
        else:
            aux_directory = data_collect.new('AUXData')
            create_mvr_props(aux_directory, aux_type)
            layer_collect.children.link(aux_directory)
        for uid, auxcollect in auxData.items():
            aux = data_collect.get(auxcollect.name)
            if aux and aux.name not in aux_directory.children:
                aux_directory.children.link(aux)
            sym_collect = data_collect.get(uid)
            if sym_collect:
                if sym_collect.name in layer_collect.children:
                    layer_collect.children.unlink(sym_collect)
                elif sym_collect.name not in auxcollect.children:
                    if sym_name in (None, 'None'):
                        sym_name = 'None Layer'
                    auxcollect.children.link(sym_collect)
                sym_collect.name = sym_collect.get('MVR Name')  

    for laycollect in layer_collect.children:
        if laycollect.get('MVR Class') is not None:
            imported_layers.append(laycollect)
            for cidx, collect in enumerate(laycollect.children):
                for col in collect.children:
                    col_name = col.get('MVR Name')
                    check_name = col.name[-3:].isdigit() and col.name[-4] == '.'
                    if check_name and col_name in data_collect:
                        clean_name = col.name.split('.')[0]
                        col.name = '%s %d' % (clean_name, cidx)

    for idx, collect in enumerate(imported_layers):
        for obid, obj in enumerate(collect.all_objects):
            obj_name = obj.name.split('.')[0]
            if obj.is_instancer:
                insta_name = '%s %d' % (obj_name, idx) if idx >= 1 else obj_name
                obj.name = '%s_%d' % (insta_name.split('_')[0], obid)
            elif obj.name[-3:].isdigit() and obj.name[-4] == '.':
                obj.name = '%s %d' % (obj_name, obid)

    for view in view_collect.children:
        if view.name == 'AUXData':
            for childs in view.children:
                for collect in childs.children:
                    collect.hide_viewport = True

    auxData.clear()
    objectData.clear()
    viewlayer.update()
    imported_layers.clear()
    print("INFO", "MVR scene loaded in %.4f sec." % (time.time() - start_time))
