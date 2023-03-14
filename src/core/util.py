import bpy
from bpy.types import Collection

def delete_collection(name: str) -> None:
    if (name in bpy.data.collections):
        for obj in bpy.data.collections[name].objects:
            bpy.data.objects.remove(obj)
        bpy.data.collections.remove(bpy.data.collections[name])

def new_collection(name: str, unique: bool = True) -> Collection:
    if (unique and name in bpy.data.collections):
        return bpy.data.collections[name]
    return bpy.data.collections.new(
        name
    )

def reset_collection(name: str) -> Collection:
    delete_collection(name)
    return new_collection(name)

def activate_collection(collection: Collection) -> None:
    # Activates the collection so new objects are created inside it
    children = bpy.context.scene.collection.children
    if (not collection.name in children):
        children.link(collection)
    layer_collection = bpy.context.view_layer.layer_collection.children[collection.name]
    bpy.context.view_layer.active_layer_collection = layer_collection

def hide_collection(collection: Collection) -> None:
    bpy.context.scene.collection.children.unlink(collection)