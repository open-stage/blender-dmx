#
#   BlendexDMX > Model
#   Handles the creation of different models
#
#   http://www.github.com/hugoaboud/BlenderDMX
#

import os.path
import bpy

from dmx.util import getEmitterMaterial, getBodyMaterial, getSurfaceMaterial

MESH_PATH = 'C:\\Users\\Aboud\\Desktop\\LAB\\BlenderDMX\\mesh\\'

# <get Mesh>
# Load the mesh for a given model if it wasn't already loaded
# model is the .obj file name on the "models/" folder

def getMesh(model):
    mesh = {}
    if (model+"_emitter" not in bpy.data.meshes):
        path = MESH_PATH+model+'.obj'
        if (not os.path.exists(path) or not os.path.isfile(path)):
            return None
        imported_object = bpy.ops.import_scene.obj(filepath=path)
        for i in range(len(bpy.context.selected_objects)):
            obj = bpy.context.selected_objects[i]
            # delete materials
            for m in obj.data.materials:
                if (m): bpy.data.materials.remove(m)
            obj.data.materials.clear()
            # rename mesh
            if ("Body" in obj.name):
                obj.data.name = model+"_body"
                mesh['body'] = bpy.data.meshes[model+"_body"]
            elif ("Emitter" in obj.name):
                obj.data.name = model+"_emitter"
                mesh['emitter'] = bpy.data.meshes[model+"_emitter"]
            elif ("Surface" in obj.name):
                obj.data.name = model+"_surface"
                mesh['surface'] = bpy.data.meshes[model+"_surface"]
        bpy.ops.object.delete()
    else:
        if (model+"_body" in bpy.data.meshes): mesh['body'] = bpy.data.meshes[model+"_body"]
        if (model+"_emitter" in bpy.data.meshes): mesh['emitter'] = bpy.data.meshes[model+"_emitter"]
        if (model+"_surface" in bpy.data.meshes): mesh['surface'] = bpy.data.meshes[model+"_surface"]
    return mesh

def populateModel(collection, model):
    name = collection.name
    mesh = getMesh(model)
    if (not mesh):
        print("DMX", "No mesh named " + model)
        return
    if (not len(mesh)):
        print("DMX", "Invalid mesh")
        return

    components = {}

    # Emitter
    emitter = bpy.data.objects.new('Emitter', mesh['emitter'])
    collection.objects.link(emitter)
    components['emitter'] = emitter
    material = getEmitterMaterial(name)
    emitter.active_material = material
    emitter.material_slots[0].link = 'OBJECT'
    emitter.material_slots[0].material = material

    # Body (optional)
    if ('body' in mesh):
        body = bpy.data.objects.new('Body', mesh['body'])
        collection.objects.link(body)
        if (not len(body.data.materials)):
            body.data.materials.append(getBodyMaterial())
        components['body'] = body

    # Surface (optional)
    if ('surface' in mesh):
        surface = bpy.data.objects.new('Surface', mesh['surface'])
        collection.objects.link(surface)
        if (not len(surface.data.materials)):
            surface.data.materials.append(getSurfaceMaterial())
            components['surface'] = surface

    return components
