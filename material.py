#
#   BlendexDMX > Material
#   Methods to create special materials (such as the default light emitter)
#
#   http://www.github.com/open-stage/BlenderDMX
#

import bpy
from dmx.logging import DMX_Log
import logging

# Shader Nodes default labels
# Blender API naming convention is inconsistent for internationalization
# Every label used is listed here, so it's easier to fix it on new API updates
PRINCIPLED_BSDF = bpy.app.translations.pgettext("Principled BSDF")
MATERIAL_OUTPUT = bpy.app.translations.pgettext("Material Output")
SHADER_NODE_EMISSION = bpy.app.translations.pgettext("ShaderNodeEmission")
SHADER_NODE_VOLUMESCATTER = bpy.app.translations.pgettext("ShaderNodeVolumeScatter")
VOLUME_SCATTER = bpy.app.translations.pgettext("Volume Scatter")
EMISSION = bpy.app.translations.pgettext("Emission")
SHADER_NODE_MIX_SHADER = bpy.app.translations.pgettext("ShaderNodeMixShader")
SHADER_NODE_BSDF_TRANSPARENT = bpy.app.translations.pgettext("ShaderNodeBsdfTransparent")
SHADER_NODE_TEX_IMAGE = bpy.app.translations.pgettext("ShaderNodeTexImage")
SHADER_NODE_MIX = bpy.app.translations.pgettext("ShaderNodeMix")
SHADER_NODE_COLOR_RAMP = bpy.app.translations.pgettext("ShaderNodeValToRGB")
SHADER_NODE_NOISE_TEXTURE = bpy.app.translations.pgettext("ShaderNodeTexNoise")



# <get Emitter Material>
#   Create an emissive material with given name, remove if already present
def getEmitterMaterial(name):
    if name in bpy.data.materials:
        bpy.data.materials.remove(bpy.data.materials[name])
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    # BUG: Internationalization
    if PRINCIPLED_BSDF in material.node_tree.nodes:
        material.node_tree.nodes.remove(material.node_tree.nodes[PRINCIPLED_BSDF])
    else:
        DMX_Log.log.error("BSDF material could not be removed when adding new Emitter, this could cause issues. Set Logging level to Info to get more details.")
        if DMX_Log.log.isEnabledFor(logging.INFO):
            print("Nodes in material tree nodes:")
            for node in material.node_tree.nodes:
                print(node)
    material.node_tree.nodes.new(SHADER_NODE_EMISSION)
    material.node_tree.links.new(material.node_tree.nodes[MATERIAL_OUTPUT].inputs[0], material.node_tree.nodes[EMISSION].outputs[0])
    return material


# <get Volume Scatter Material>
#
def getVolumeScatterMaterial():
    if "DMX_Volume" in bpy.data.materials:
        return bpy.data.materials["DMX_Volume"]

    material = bpy.data.materials.new("DMX_Volume")
    material.use_nodes = True
    # BUG: Internationalization
    if PRINCIPLED_BSDF in material.node_tree.nodes:
        material.node_tree.nodes.remove(material.node_tree.nodes[PRINCIPLED_BSDF])
    else:
        DMX_Log.log.error("BSDF material could not be removed when adding creating Volume, this could cause issues. Set Logging level to Info to get more details")
        if DMX_Log.log.isEnabledFor(logging.INFO):
            print("Nodes in material tree nodes:")
            for node in material.node_tree.nodes:
                print(node)

    volume_scatter = material.node_tree.nodes.new(SHADER_NODE_VOLUMESCATTER)
    volume_scatter.name="Volume Scatter"
    color_ramp = material.node_tree.nodes.new(SHADER_NODE_COLOR_RAMP)
    color_ramp.name = "Color Ramp"
    noise_texture = material.node_tree.nodes.new(SHADER_NODE_NOISE_TEXTURE)
    noise_texture.name = "Noise Texture"
    material.node_tree.links.new(material.node_tree.nodes[MATERIAL_OUTPUT].inputs[1], volume_scatter.outputs[0])
    material.node_tree.links.new(noise_texture.outputs[0],color_ramp.inputs[0])
    material.node_tree.links.new(color_ramp.outputs[0], volume_scatter.inputs[0])
    volume_scatter.inputs['Density'].default_value = 0.1
    material.node_tree.nodes["Color Ramp"].color_ramp.elements[0].position = 0.444
    material.node_tree.nodes["Color Ramp"].color_ramp.elements[1].position = 1
    return material


def get_gobo_material(name):
    """Material for gobo projection.
    The commented out lines have originally been used
    but there doesn't seem to be difference without them
    keeping them here just in case."""

    if name in bpy.data.materials:
        bpy.data.materials.remove(bpy.data.materials[name])
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    material.node_tree.nodes.remove(material.node_tree.nodes[PRINCIPLED_BSDF])
    matout = material.node_tree.nodes.get(MATERIAL_OUTPUT)
    # matout.target = "EEVEE"
    # mix = material.node_tree.nodes.new(SHADER_NODE_MIX_SHADER)
    # mix.inputs[0].default_value = 0.010
    # material.node_tree.links.new(matout.inputs[0], mix.outputs[0])
    bsdf = material.node_tree.nodes.new(SHADER_NODE_BSDF_TRANSPARENT)
    # material.node_tree.links.new(bsdf.outputs[0], mix.inputs[1])
    material.node_tree.links.new(matout.inputs[0], bsdf.outputs[0])
    image = material.node_tree.nodes.new(SHADER_NODE_TEX_IMAGE)
    image.name = "Image Texture"
    # material.node_tree.links.new(image.outputs[1], mix.inputs[2])
    material.node_tree.links.new(image.outputs[0], bsdf.inputs[0])
    # material.node_tree.links.new(bsdf.outputs[0], mix.inputs[1])
    return material

def set_light_nodes(light):
    light_obj = light.object
    light_obj.data.use_nodes = True
    emission = light_obj.data.node_tree.nodes.get(EMISSION)
    image = light_obj.data.node_tree.nodes.new(SHADER_NODE_TEX_IMAGE)
    image.name = "Image Texture"
    mix = light_obj.data.node_tree.nodes.new(SHADER_NODE_MIX)
    mix.data_type="RGBA"
    mix.name = "Mix"
    mix.inputs[0].default_value = 1
    light_obj.data.node_tree.links.new(mix.outputs["Result"], emission.inputs[0])
    light_obj.data.node_tree.links.new(image.outputs[0], mix.inputs["A"])
