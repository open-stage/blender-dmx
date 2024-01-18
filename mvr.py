import os
import bpy
from dmx.util import xyY2rgbaa
from dmx.io_scene_3ds.import_3ds import load_3ds
from mathutils import Matrix
import time
import hashlib
import json
from dmx.group import FixtureGroup
from dmx.mvr_objects import DMX_MVR_Object
from dmx.logging import DMX_Log


# importing from dmx didn't work, had to duplicate this function
def onDepsgraph(scene):
    scene = bpy.context.scene
    depsgraph = bpy.context.evaluated_depsgraph_get()

    for update in depsgraph.updates:
        obj = update.id.evaluated_get(depsgraph)
        # Selection changed, sync programmer
        if obj.rna_type.name == "Scene":
            scene.dmx.syncProgrammer()
            continue
        # Fixture updated
        found = False
        for fixture in scene.dmx.fixtures:
            for f_obj in fixture.objects:
                if obj.name == f_obj.object.name:
                    fixture.onDepsgraphUpdate()
                    found = True
                    break
            if found:
                break


def process_mvr_child_list(dmx, child_list, layer_index, extract_to_folder_path, mvr_scene, already_extracted_files, layer_collection, fixture_group=None):
    if "MVR Trusses" in layer_collection.children:
        truss_collection = layer_collection.children["MVR Trusses"]
    else:
        truss_collection = bpy.data.collections.new("MVR Trusses")
        layer_collection.children.link(truss_collection)

    for truss_index, truss_object in enumerate(child_list.trusses):
        process_mvr_object(
            mvr_scene,
            truss_object,
            truss_index,
            layer_index,
            already_extracted_files,
            truss_collection,
        )
        if fixture_group is None:
            g_name = truss_object.name or "Truss"
            g_name = f"{g_name} {truss_index}"
            fixture_group = FixtureGroup(g_name, truss_object.uuid)

        if hasattr(truss_object, "child_list") and truss_object.child_list:
            process_mvr_child_list(
                dmx,
                truss_object.child_list,
                truss_index,
                extract_to_folder_path,
                mvr_scene,
                already_extracted_files,
                layer_collection,
                fixture_group,
            )

    if "MVR Scene objects" in layer_collection.children:
        scene_collection_top = layer_collection.children["MVR Scene objects"]
    else:
        scene_collection_top = bpy.data.collections.new("MVR Scene objects")
        layer_collection.children.link(scene_collection_top)

    for scene_index, scene_object in enumerate(child_list.scene_objects):
        collection = scene_collection_top

        geometry3ds = []
        symbols = []
        if scene_object.geometries:
            geometry3ds = scene_object.geometries.geometry3d
            symbols = scene_object.geometries.symbol

        if (len(geometry3ds) + len(symbols)) > 1:
            # create extra scene object collection if the scene object is composed of multiple models
            if scene_object.name is not None or scene_object.name != "":
                scene_name = f"Scene object - {scene_object.name}"
            else:
                scene_name = f"Scene object - {scene_object.uuid}"

            scene_collection = bpy.data.collections.new(scene_name)
            scene_collection_top.children.link(scene_collection)
            collection = scene_collection
            DMX_Log.log.info(("creating extra collection", scene_name))

        process_mvr_object(
            mvr_scene,
            scene_object,
            scene_index,
            layer_index,
            already_extracted_files,
            collection,
        )

        if hasattr(scene_object, "child_list") and scene_object.child_list:
            process_mvr_child_list(dmx, scene_object.child_list, scene_index, extract_to_folder_path, mvr_scene, already_extracted_files, layer_collection, fixture_group)

    for fixture_index, fixture in enumerate(child_list.fixtures):
        focus_point = None
        if fixture.focus is not None:
            focus_points = [fp for fp in child_list.focus_points if fp.uuid == fixture.focus]
            if len(focus_points):
                focus_point = focus_points[0].matrix.matrix

        add_mvr_fixture(
            dmx,
            mvr_scene,
            extract_to_folder_path,
            fixture,
            fixture_index,
            layer_index,
            focus_point,
            already_extracted_files,
            fixture_group,
        )

        if hasattr(fixture, "child_list") and fixture.child_list:
            process_mvr_child_list(dmx, fixture.child_list, fixture_index, extract_to_folder_path, mvr_scene, already_extracted_files, layer_collection, fixture_group)

    for group_index, group in enumerate(child_list.group_objects):
        if hasattr(group, "child_list") and group.child_list:
            # if group.child_list is not None:
            layer_group_index = f"{layer_index}-{group_index}"
            g_name = group.name or "Group"
            g_name = f"{g_name} {group_index}"
            fixture_group = FixtureGroup(g_name, group.uuid)
            process_mvr_child_list(
                dmx,
                group.child_list,
                layer_group_index,
                extract_to_folder_path,
                mvr_scene,
                already_extracted_files,
                layer_collection,
                fixture_group,
            )


def process_mvr_object(
    mvr_scene,
    mvr_object,
    mvr_object_index,
    layer_index,
    already_extracted_files,
    group_collection,
):
    geometry3ds = []
    symbols = []
    if mvr_object.geometries:
        geometry3ds = mvr_object.geometries.geometry3d
        symbols = mvr_object.geometries.symbol
    global_transform = mvr_object.matrix.matrix
    file = ""
    current_path = os.path.dirname(os.path.realpath(__file__))
    folder = os.path.join(current_path, "assets", "models", "mvr")
    name = mvr_object.name

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
        dmx_mvr_object.object_type = mvr_object.__class__.__name__
        dmx_mvr_object.uuid = mvr_object.uuid
        dmx_mvr_object.collection = bpy.data.collections.new(mvr_object.uuid)

    for geometry in geometry3ds:
        if geometry.file_name:
            file = geometry.file_name
            local_transform = geometry.matrix.matrix
            extract_mvr_object(file, mvr_scene, folder, already_extracted_files)
            coll = add_mvr_object(
                name,
                file,
                folder,
                global_transform,
                local_transform,
                mvr_object_index,
                layer_index,
                group_collection,
                mvr_object,
            )
            if coll:
                dmx_mvr_object.collection.children.link(coll)

    for symbol in symbols:
        symdefs = [sd for sd in mvr_scene.aux_data.symdefs if sd.uuid == symbol.symdef]
        for symdef in symdefs:
            for geometry in symdef.geometry3d:
                if geometry.file_name:
                    file = geometry.file_name
                    local_transform = geometry.matrix.matrix

                    extract_mvr_object(file, mvr_scene, folder, already_extracted_files)
                    coll = add_mvr_object(
                        name,
                        file,
                        folder,
                        global_transform,
                        local_transform,
                        mvr_object_index,
                        layer_index,
                        group_collection,
                        symbol,
                    )
                    if coll:
                        dmx_mvr_object.collection.children.link(coll)


def extract_mvr_object(file, mvr_scene, folder, already_extracted_files):
    if f"{file}" in mvr_scene._package.namelist():
        if file not in already_extracted_files.keys():
            mvr_scene._package.extract(file, folder)
            already_extracted_files[file] = 0
        else:
            already_extracted_files[file] += 1


def extract_mvr_textures(mvr_scene, folder):
    for name in mvr_scene._package.namelist():
        if name.endswith(".png"):
            mvr_scene._package.extract(name, folder)


def getCollectionName(string):
    name = hashlib.shake_256(string.encode()).hexdigest(5)
    return name


def loadModelAndPrepareMvrFileCollection(file, folder):
    object_collection = bpy.data.collections.new(getCollectionName(file))
    file_name = os.path.join(folder, file)
    file_3ds = False
    if file_name.split(".")[-1] == "glb":
        bpy.ops.import_scene.gltf(filepath=file_name)
    else:
        load_3ds(file_name, bpy.context)
        file_3ds = True
    objs = list(bpy.context.view_layer.objects.selected)

    for ob in objs:
        if file_3ds:
            ob.users_collection[0].objects.unlink(ob)
        else:
            bpy.context.scene.collection.objects.unlink(ob)
        object_collection.objects.link(ob)
    return object_collection


def add_mvr_object(
    # This is just a basic implementation, layers, grouping, management need to be added...
    name,
    file,
    folder,
    global_transform,
    local_transform,
    mvr_object_index,
    layer_index,
    group_collection,
    mvr_object,
):
    start_time = time.time()
    name = f"{name} {layer_index}-{mvr_object_index}"
    # bpy.app.handlers.depsgraph_update_post.clear()

    cached_collection_name = getCollectionName(file)
    if cached_collection_name in bpy.data.collections:
        mvr_file_collection = bpy.data.collections[cached_collection_name]
    else:
        mvr_file_collection = loadModelAndPrepareMvrFileCollection(file, folder)

    collection_name = name
    object_collection = bpy.data.collections.new(collection_name)

    local_scale = Matrix(local_transform).to_scale()
    global_scale = Matrix(global_transform).to_scale()

    file_3ds = False
    if file.split(".")[-1] != "glb":
        file_3ds = True

    for obj in mvr_file_collection.objects:
        ob = obj.copy()
        ob.location = Matrix(local_transform).to_translation()
        ob.rotation_mode = "XYZ"
        ob.rotation_euler = Matrix(local_transform).to_euler("XYZ")
        ob["file name"] = file

        ob.matrix_world = global_transform
        # ob.location = Matrix(global_transform).to_translation()
        # ob.rotation_mode = "XYZ"
        # ob.rotation_euler = Matrix(global_transform).to_euler('XYZ')

        ob.scale[0] *= local_scale[0] * global_scale[0]
        ob.scale[1] *= local_scale[1] * global_scale[1]
        ob.scale[2] *= local_scale[2] * global_scale[2]

        if file_3ds:
            # ob.scale = (0.001, 0.001, 0.001)
            ob.scale[0] *= 0.001
            ob.scale[1] *= 0.001
            ob.scale[2] *= 0.001

        object_collection.objects.link(ob)

    if len(object_collection.children) + len(object_collection.objects):
        group_collection.children.link(object_collection)
        print("MVR object loaded in %.4f sec." % (time.time() - start_time))
        return object_collection

    return None


def add_mvr_fixture(
    dmx,
    mvr_scene,
    extract_to_folder_path,
    fixture,
    fixture_index,
    layer_index,
    focus_point,
    already_extracted_files,
    fixture_group=None,
):
    """Add fixture to the scene"""

    existing_fixture = None
    for _fixture in dmx.fixtures:
        if _fixture.uuid == fixture.uuid:
            existing_fixture = _fixture
            DMX_Log.log.info(f"Update existing fixture {fixture.uuid}")
            break

    if f"{fixture.gdtf_spec}" in mvr_scene._package.namelist():
        if fixture.gdtf_spec not in already_extracted_files.keys():
            mvr_scene._package.extract(fixture.gdtf_spec, extract_to_folder_path)
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
