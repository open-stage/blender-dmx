import os
import bpy
from dmx.util import xyY2rgbaa
from dmx.io_scene_3ds.import_3ds import load_3ds
from mathutils import Matrix
import time


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


def process_mvr_child_list(
    dmx,
    child_list,
    layer_index,
    extract_to_folder_path,
    mvr_scene,
    already_extracted_files,
    layer_collection,
):
    if "MVR Trusses" in layer_collection:
        truss_collection = layer_collection["MVR Trusses"]
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

        if hasattr(truss_object, "child_list") and truss_object.child_list:
            process_mvr_child_list(
                dmx,
                truss_object.child_list,
                truss_index,
                extract_to_folder_path,
                mvr_scene,
                already_extracted_files,
                layer_collection,
            )

    if "MVR Scene objects" in layer_collection:
        scene_collection_top = layer_collection["MVR Scene objects"]
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

        process_mvr_object(
            mvr_scene,
            scene_object,
            scene_index,
            layer_index,
            already_extracted_files,
            collection,
        )

        if hasattr(scene_object, "child_list") and scene_object.child_list:
            process_mvr_child_list(
                dmx,
                scene_object.child_list,
                scene_index,
                extract_to_folder_path,
                mvr_scene,
                already_extracted_files,
                layer_collection,
            )

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
        )

        if hasattr(fixture, "child_list") and fixture.child_list:
            process_mvr_child_list(
                dmx,
                fixture.child_list,
                fixture_index,
                extract_to_folder_path,
                mvr_scene,
                already_extracted_files,
                layer_collection,
            )

    for group_index, group in enumerate(child_list.group_objects):
        if hasattr(group, "child_list") and group.child_list:
            # if group.child_list is not None:
            layer_group_index = f"{layer_index}-{group_index}"
            process_mvr_child_list(
                dmx,
                group.child_list,
                layer_group_index,
                extract_to_folder_path,
                mvr_scene,
                already_extracted_files,
                layer_collection,
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

    for geometry in geometry3ds:
        if geometry.file_name:
            file = geometry.file_name
            local_transform = geometry.matrix.matrix
            extract_mvr_object(file, mvr_scene, folder, already_extracted_files)
            add_mvr_object(
                name,
                file,
                folder,
                global_transform,
                local_transform,
                mvr_object_index,
                layer_index,
                group_collection,
            )

    for symbol in symbols:
        symdefs = [sd for sd in mvr_scene.aux_data.symdefs if sd.uuid == symbol.symdef]
        for symdef in symdefs:
            for geometry in symdef.geometry3d:
                if geometry.file_name:
                    file = geometry.file_name
                    local_transform = geometry.matrix.matrix

                    extract_mvr_object(file, mvr_scene, folder, already_extracted_files)
                    add_mvr_object(
                        name,
                        file,
                        folder,
                        global_transform,
                        local_transform,
                        mvr_object_index,
                        layer_index,
                        group_collection,
                    )


def extract_mvr_object(file, mvr_scene, folder, already_extracted_files):
    if f"{file}" in mvr_scene._package.namelist():
        if file not in already_extracted_files.keys():
            mvr_scene._package.extract(file, folder)
            already_extracted_files[file] = 0
        else:
            already_extracted_files[file] += 1


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
):
    time1 = time.time()
    name = f"{name} {layer_index}-{mvr_object_index}"
    # bpy.app.handlers.depsgraph_update_post.clear()

    collection_name = name

    file_name = os.path.join(folder, file)
    file_3ds = False
    if file_name.split(".")[-1] == "glb":
        bpy.ops.import_scene.gltf(filepath=file_name)
    else:
        load_3ds(file_name, bpy.context)
        file_3ds = True

    object_collection = bpy.data.collections.new(collection_name)

    objs = list(bpy.context.view_layer.objects.selected)

    local_scale = Matrix(local_transform).to_scale()
    global_scale = Matrix(global_transform).to_scale()

    for ob in objs:
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
            ob.users_collection[0].objects.unlink(ob)
        else:
            bpy.context.scene.collection.objects.unlink(ob)

        object_collection.objects.link(ob)
    group_collection.children.link(object_collection)
    # bpy.app.handlers.depsgraph_update_post.append(onDepsgraph)
    print("MVR object loaded in %.4f sec." % (time.time() - time1))


def add_mvr_fixture(
    dmx,
    mvr_scene,
    extract_to_folder_path,
    fixture,
    fixture_index,
    layer_index,
    focus_point,
    already_extracted_files,
):
    """Add fixture to the scene"""
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
    dmx.addFixture(
        f"{fixture.name} {layer_index}-{fixture_index}",
        fixture.gdtf_spec,
        fixture.addresses[0].universe,
        fixture.addresses[0].address,
        fixture.gdtf_mode,
        xyY2rgbaa(fixture.color),
        True,
        position=fixture.matrix.matrix,
        focus_point=focus_point,
    )
