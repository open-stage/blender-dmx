import os
import bpy
from dmx.util import xyY2rgbaa
from dmx.io_scene_3ds.import_3ds import load_3ds


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
):
    if "MVR Trusses" in bpy.data.collections:
        truss_collection = bpy.data.collections["MVR Trusses"]
    else:
        truss_collection = bpy.data.collections.new("MVR Trusses")
        bpy.context.scene.collection.children.link(truss_collection)

    for truss_index, truss_object in enumerate(child_list.trusses):
        process_mvr_object(
            mvr_scene,
            truss_object,
            truss_index,
            layer_index,
            already_extracted_files,
            truss_collection,
        )

    if "MVR Scene objects" in bpy.data.collections:
        scene_collection = bpy.data.collections["MVR Scene objects"]
    else:
        scene_collection = bpy.data.collections.new("MVR Scene objects")
        bpy.context.scene.collection.children.link(scene_collection)

    for scene_index, scene_object in enumerate(child_list.scene_objects):
        process_mvr_object(
            mvr_scene,
            scene_object,
            scene_index,
            layer_index,
            already_extracted_files,
            scene_collection,
        )

    for fixture_index, fixture in enumerate(child_list.fixtures):
        focus_point = None
        if fixture.focus is not None:
            focus_points = [
                fp for fp in child_list.focus_points if fp.uuid == fixture.focus
            ]
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

    for group in child_list.group_objects:
        if group.child_list is not None:
            process_mvr_child_list(
                dmx,
                group.child_list,
                layer_index,
                extract_to_folder_path,
                mvr_scene,
                already_extracted_files,
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
    position = mvr_object.matrix.matrix
    file = ""
    current_path = os.path.dirname(os.path.realpath(__file__))
    folder = os.path.join(current_path, "assets", "models", "mvr")
    name = mvr_object.name

    for geometry in geometry3ds:
        if geometry.file_name:
            file = geometry.file_name
            extract_mvr_object(file, mvr_scene, folder, already_extracted_files)
            add_mvr_object(
                name,
                file,
                folder,
                position,
                mvr_object_index,
                layer_index,
                group_collection,
            )

    for symbol in symbols:
        symdefs = [sd for sd in mvr_scene.symdefs if sd.uuid == symbol.symdef]
        for symdef in symdefs:
            for geometry in symdef.geometry3d:
                if geometry.file_name:
                    file = geometry.file_name

                    extract_mvr_object(file, mvr_scene, folder, already_extracted_files)
                    add_mvr_object(
                        name,
                        file,
                        folder,
                        position,
                        mvr_object_index,
                        layer_index,
                        group_collection,
                    )


def extract_mvr_object(file, mvr_scene, folder, already_extracted_files):
    if f"{file}" in mvr_scene._package.namelist():
        if file not in already_extracted_files:
            mvr_scene._package.extract(file, folder)
            already_extracted_files.append(file)


def add_mvr_object(
    # This is just a basic implementation, layers, grouping, management need to be added...
    name,
    file,
    folder,
    position,
    mvr_object_index,
    layer_index,
    group_collection,
):
    name = f"{name} {layer_index}-{mvr_object_index}"
    bpy.app.handlers.depsgraph_update_post.clear()

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
    for ob in objs:
        ob.matrix_world = position

        if file_3ds:
            ob.scale = (0.001, 0.001, 0.001)
            ob.users_collection[0].objects.unlink(ob)
        else:
            bpy.context.scene.collection.objects.unlink(ob)

        object_collection.objects.link(ob)

    group_collection.children.link(object_collection)
    bpy.app.handlers.depsgraph_update_post.append(onDepsgraph)


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
        if fixture.gdtf_spec not in already_extracted_files:
            mvr_scene._package.extract(fixture.gdtf_spec, extract_to_folder_path)
            already_extracted_files.append(fixture.gdtf_spec)
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
