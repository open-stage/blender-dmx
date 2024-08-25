#    Copyright Hugo Aboud, vanous
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


import bpy
from .logging import DMX_Log
import logging
import os
from .gdtf import DMX_GDTF

# Shader Nodes default labels
# Blender API naming convention is inconsistent for internationalization
# Every label used is listed here, so it's easier to fix it on new API updates
PRINCIPLED_BSDF = bpy.app.translations.pgettext("Principled BSDF")
MATERIAL_OUTPUT = bpy.app.translations.pgettext("Material Output")
SHADER_NODE_EMISSION = bpy.app.translations.pgettext("ShaderNodeEmission")
SHADER_NODE_VOLUMESCATTER = bpy.app.translations.pgettext("ShaderNodeVolumeScatter")
VOLUME_SCATTER = bpy.app.translations.pgettext("Volume Scatter")
EMISSION = bpy.app.translations.pgettext("Emission")
LIGHT_NODE = bpy.app.translations.pgettext("Light Output")
SHADER_NODE_MIX_SHADER = bpy.app.translations.pgettext("ShaderNodeMixShader")
SHADER_NODE_BSDF_TRANSPARENT = bpy.app.translations.pgettext("ShaderNodeBsdfTransparent")
SHADER_NODE_TEX_IMAGE = bpy.app.translations.pgettext("ShaderNodeTexImage")
SHADER_NODE_MIX = bpy.app.translations.pgettext("ShaderNodeMix")
SHADER_NODE_COLOR_RAMP = bpy.app.translations.pgettext("ShaderNodeValToRGB")
SHADER_NODE_NOISE_TEXTURE = bpy.app.translations.pgettext("ShaderNodeTexNoise")
SHADER_NODE_TEX_IES = bpy.app.translations.pgettext("ShaderNodeTexIES")


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
            print("INFO", "Nodes in material tree nodes:")
            for node in material.node_tree.nodes:
                print("INFO", node)
    node = material.node_tree.nodes.new(SHADER_NODE_EMISSION)
    material.node_tree.links.new(material.node_tree.nodes[MATERIAL_OUTPUT].inputs[0], node.outputs[0])
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
            print("INFO", "Nodes in material tree nodes:")
            for node in material.node_tree.nodes:
                print("INFO", node)

    volume_scatter = material.node_tree.nodes.new(SHADER_NODE_VOLUMESCATTER)
    volume_scatter.name = "Volume Scatter"
    color_ramp = material.node_tree.nodes.new(SHADER_NODE_COLOR_RAMP)
    color_ramp.name = "Color Ramp"
    noise_texture = material.node_tree.nodes.new(SHADER_NODE_NOISE_TEXTURE)
    noise_texture.name = "Noise Texture"
    material.node_tree.links.new(material.node_tree.nodes[MATERIAL_OUTPUT].inputs[1], volume_scatter.outputs[0])
    material.node_tree.links.new(noise_texture.outputs[0], color_ramp.inputs[0])
    material.node_tree.links.new(color_ramp.outputs[0], volume_scatter.inputs[0])
    volume_scatter.inputs["Density"].default_value = 0.1
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
    matout.location = (400, 500)
    # matout.target = "EEVEE"
    # mix = material.node_tree.nodes.new(SHADER_NODE_MIX_SHADER)
    # mix.inputs[0].default_value = 0.010
    # material.node_tree.links.new(matout.inputs[0], mix.outputs[0])
    bsdf = material.node_tree.nodes.new(SHADER_NODE_BSDF_TRANSPARENT)
    bsdf.location = (200, 500)
    # material.node_tree.links.new(bsdf.outputs[0], mix.inputs[1])
    material.node_tree.links.new(matout.inputs[0], bsdf.outputs[0])
    image = material.node_tree.nodes.new(SHADER_NODE_TEX_IMAGE)
    image.location = (0, 500)
    image.name = "Image Texture"
    # material.node_tree.links.new(image.outputs[1], mix.inputs[2])
    material.node_tree.links.new(image.outputs[0], bsdf.inputs[0])
    # material.node_tree.links.new(bsdf.outputs[0], mix.inputs[1])

    return material


def set_light_nodes(light):
    light_obj = light.object
    light_obj.data.use_nodes = True
    emission = light_obj.data.node_tree.nodes.get(EMISSION)
    light_node = light_obj.data.node_tree.nodes.get(LIGHT_NODE)

    # set gobo node

    gobo2_image_rotate = light_obj.data.node_tree.nodes.new("ShaderNodeVectorRotate")
    gobo2_image_rotate.name = "Gobo2Rotation"
    gobo2_image_rotate.rotation_type = "Z_AXIS"
    gobo2_image_rotate.invert = True
    gobo2_image_rotate.inputs[1].default_value[:2] = [0.5] * 2
    gobo2_image = light_obj.data.node_tree.nodes.new(SHADER_NODE_TEX_IMAGE)
    gobo2_image.name = "Gobo2Texture"

    gobo1_image_rotate = light_obj.data.node_tree.nodes.new("ShaderNodeVectorRotate")
    gobo1_image_rotate.name = "Gobo1Rotation"
    gobo1_image_rotate.rotation_type = "Z_AXIS"
    gobo1_image_rotate.invert = True
    gobo1_image_rotate.inputs[1].default_value[:2] = [0.5] * 2
    gobo1_image = light_obj.data.node_tree.nodes.new(SHADER_NODE_TEX_IMAGE)
    gobo1_image.name = "Gobo1Texture"
    gobo_geometry_node = light_obj.data.node_tree.nodes.new("ShaderNodeNewGeometry")

    gobo_geometry_node.location = (-694.17, 457.04)
    gobo1_image_rotate.location = (-405.22, 486.14)
    gobo2_image_rotate.location = (-406.19, 229.93)

    light_obj.data.node_tree.links.new(gobo_geometry_node.outputs[5], gobo1_image_rotate.inputs[0])
    light_obj.data.node_tree.links.new(gobo1_image_rotate.outputs[0], gobo1_image.inputs[0])
    light_obj.data.node_tree.links.new(gobo_geometry_node.outputs[5], gobo2_image_rotate.inputs[0])
    light_obj.data.node_tree.links.new(gobo2_image_rotate.outputs[0], gobo2_image.inputs[0])

    gobo1_mix = light_obj.data.node_tree.nodes.new(SHADER_NODE_MIX)
    gobo1_mix.data_type = "RGBA"
    gobo1_mix.blend_type = "MIX"
    gobo1_mix.name = "Gobo1Mix"
    gobo1_mix.inputs[0].default_value = 1

    gobo2_mix = light_obj.data.node_tree.nodes.new(SHADER_NODE_MIX)
    gobo2_mix.data_type = "RGBA"
    gobo2_mix.blend_type = "MIX"
    gobo2_mix.name = "Gobo2Mix"
    gobo2_mix.inputs[0].default_value = 1

    # gobo mix
    gobos_mix = light_obj.data.node_tree.nodes.new(SHADER_NODE_MIX)
    gobos_mix.data_type = "RGBA"
    gobos_mix.blend_type = "DARKEN"
    gobos_mix.name = "Mix"
    gobos_mix.inputs[0].default_value = 1

    light_obj.data.node_tree.links.new(gobo1_image.outputs[0], gobo1_mix.inputs["A"])
    light_obj.data.node_tree.links.new(gobo2_image.outputs[0], gobo2_mix.inputs["A"])

    light_obj.data.node_tree.links.new(gobo1_mix.outputs["Result"], gobos_mix.inputs["A"])
    light_obj.data.node_tree.links.new(gobo2_mix.outputs["Result"], gobos_mix.inputs["B"])

    mix = light_obj.data.node_tree.nodes.new(SHADER_NODE_MIX)
    mix.data_type = "RGBA"
    mix.blend_type = "DARKEN"
    mix.name = "IrisMix"
    mix.inputs[0].default_value = 1

    light_obj.data.node_tree.links.new(gobos_mix.outputs["Result"], mix.inputs["A"])
    light_obj.data.node_tree.links.new(mix.outputs["Result"], emission.inputs[0])

    gobo1_image.location = (-221.73, 486.83)
    gobo2_image.location = (-225.50, 280.40)
    gobos_mix.location = (82.07, 489.56)
    mix.location = (319.60, 489.01)
    emission.location = (529.09, 509.87)
    light_node.location = (733.60, 536.36)

    # set iris up
    iris_geometry_node = light_obj.data.node_tree.nodes.new("ShaderNodeNewGeometry")
    iris_texture = light_obj.data.node_tree.nodes.new("ShaderNodeTexImage")
    add_node = light_obj.data.node_tree.nodes.new("ShaderNodeVectorMath")
    iris_gobo = bpy.data.images.get("default_iris.png", None)

    if iris_gobo is None:
        iris_image_path = os.path.join(DMX_GDTF.getPrimitivesPath(), "default_iris.png")
        iris_gobo = bpy.data.images.load(iris_image_path)
        iris_gobo.alpha_mode = "CHANNEL_PACKED"

    scale_node = light_obj.data.node_tree.nodes.new("ShaderNodeVectorMath")
    center_node = light_obj.data.node_tree.nodes.new("ShaderNodeVectorMath")
    center_node.inputs[1].default_value[:2] = add_node.inputs[1].default_value[:2] = [0.5] * 2

    iris_geometry_node.location = (-257.48, 70.51)
    center_node.location = (-84.09, 76.15)
    scale_node.location = (93.27, 74.36)
    iris_texture.location = (458.52, 84.25)
    add_node.location = (271.07, 75.90)

    # inputnode.blend_type = 'DARKEN' if check_spot else 'MULTIPLY'
    scale_node.label = scale_node.name = "Iris Size"
    center_node.label = center_node.name = "Center"
    add_node.label = add_node.name = "Iris Vector"
    center_node.operation = "SUBTRACT"
    scale_node.operation = "SCALE"
    add_node.operation = "ADD"

    iris_texture.image = iris_gobo
    iris_texture.extension = "EXTEND"
    iris_texture.label = iris_texture.name = "Iris"

    light_obj.data.node_tree.links.new(iris_geometry_node.outputs[5], center_node.inputs[0])
    light_obj.data.node_tree.links.new(center_node.outputs[0], scale_node.inputs[0])
    light_obj.data.node_tree.links.new(scale_node.outputs[0], add_node.inputs[0])
    light_obj.data.node_tree.links.new(add_node.outputs[0], iris_texture.inputs[0])
    light_obj.data.node_tree.links.new(iris_texture.outputs[0], mix.inputs["B"])


def get_ies_node(light_obj):
    emission = light_obj.data.node_tree.nodes.get(EMISSION)
    ies = light_obj.data.node_tree.nodes.new(SHADER_NODE_TEX_IES)
    ies.name = "IES Texture"
    light_obj.data.node_tree.links.new(ies.outputs[0], emission.inputs[1])
    return ies


def getGeometryNodes(obj):
    name = obj.name
    beam_diameter = obj.get("beam_diameter", 0.005)  # m
    # initialize geometry_nodes node group
    geometry_nodes = bpy.data.node_groups.new(type="GeometryNodeTree", name=name)
    geometry_nodes.is_modifier = True
    # initialize geometry_nodes nodes
    # geometry_nodes interface
    # Socket Geometry
    geometry_socket = geometry_nodes.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    geometry_socket.attribute_domain = "POINT"

    # Socket Geometry
    geometry_socket_1 = geometry_nodes.interface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    geometry_socket_1.attribute_domain = "POINT"

    # Socket Material
    # material_socket = geometry_nodes.interface.new_socket(name = "Material", in_out='INPUT', socket_type = 'NodeSocketMaterial')
    # material_socket.attribute_domain = 'POINT'

    # node Realize Instances
    realize_instances = geometry_nodes.nodes.new("GeometryNodeRealizeInstances")
    realize_instances.name = "Realize Instances"

    # node Vector
    vector = geometry_nodes.nodes.new("FunctionNodeInputVector")
    vector.name = "Vector"
    vector.vector = (0, 0, -1)

    # node Set Position
    set_position = geometry_nodes.nodes.new("GeometryNodeSetPosition")
    set_position.name = "Set Position"
    # Offset
    set_position.inputs[3].default_value = (0.0, 0.0, 0.0)

    # node Collection Info
    collection_info = geometry_nodes.nodes.new("GeometryNodeCollectionInfo")
    collection_info.name = "Collection Info"
    collection_info.transform_space = "RELATIVE"
    collection = bpy.context.window_manager.dmx.collections_list
    if collection and collection.name in bpy.data.collections:
        collection_info.inputs[0].default_value = collection

    # Separate Children
    collection_info.inputs[1].default_value = False
    # Reset Children
    collection_info.inputs[2].default_value = False

    # node Transform Geometry
    transform_geometry = geometry_nodes.nodes.new("GeometryNodeTransform")
    transform_geometry.name = "Transform Geometry"
    # Translation
    transform_geometry.inputs[1].default_value = (0.0, 0.0, 0.0)
    # Scale
    transform_geometry.inputs[3].default_value = (1.0, 1.0, 1.0)

    # node Group Input
    group_input = geometry_nodes.nodes.new("NodeGroupInput")
    group_input.name = "Group Input"

    # node Curve Line
    curve_line = geometry_nodes.nodes.new("GeometryNodeCurvePrimitiveLine")
    curve_line.name = "Curve Line"
    curve_line.mode = "POINTS"
    # Start
    curve_line.inputs[0].default_value = (0.0, 0.0, 0)
    # End
    curve_line.inputs[1].default_value = (0.0, 0.0, 0)
    # Direction
    curve_line.inputs[2].default_value = (0.0, 0.0, 0)
    # Length
    curve_line.inputs[3].default_value = 0

    # node Group Output
    group_output = geometry_nodes.nodes.new("NodeGroupOutput")
    group_output.name = "Group Output"
    group_output.is_active_output = True

    # node Transform Geometry.001
    transform_geometry_001 = geometry_nodes.nodes.new("GeometryNodeTransform")
    transform_geometry_001.name = "Transform Geometry.001"
    # Translation
    transform_geometry_001.inputs[1].default_value = (0.0, 0.0, 0.0)
    # Scale
    transform_geometry_001.inputs[3].default_value = (1.0, 1.0, 1.0)

    # node Join Geometry
    join_geometry = geometry_nodes.nodes.new("GeometryNodeJoinGeometry")
    join_geometry.name = "Join Geometry"

    # node Raycast
    raycast = geometry_nodes.nodes.new("GeometryNodeRaycast")
    raycast.name = "Raycast"
    raycast.data_type = "FLOAT"
    raycast.mapping = "INTERPOLATED"
    # Attribute
    # raycast.inputs[1].default_value = 0.0
    # Source Position
    # raycast.inputs[2].default_value = (0.0, 0.0, 0.0)
    # Ray Length
    # raycast.inputs[4].default_value = 100.0

    # node Index
    index = geometry_nodes.nodes.new("GeometryNodeInputIndex")
    index.name = "Index"

    # node Compare
    compare = geometry_nodes.nodes.new("FunctionNodeCompare")
    compare.name = "Compare"
    compare.data_type = "FLOAT"
    compare.mode = "ELEMENT"
    compare.operation = "EQUAL"
    # B
    compare.inputs[1].default_value = 0.0
    # A_INT
    compare.inputs[2].default_value = 0
    # B_INT
    compare.inputs[3].default_value = 0
    # A_VEC3
    compare.inputs[4].default_value = (0.0, 0.0, 0.0)
    # B_VEC3
    compare.inputs[5].default_value = (0.0, 0.0, 0.0)
    # A_COL
    compare.inputs[6].default_value = (0.0, 0.0, 0.0, 0.0)
    # B_COL
    compare.inputs[7].default_value = (0.0, 0.0, 0.0, 0.0)
    # A_STR
    compare.inputs[8].default_value = ""
    # B_STR
    compare.inputs[9].default_value = ""
    # C
    compare.inputs[10].default_value = 0.8999999761581421
    # Angle
    compare.inputs[11].default_value = 0.08726649731397629
    # Epsilon
    compare.inputs[12].default_value = 0.0010000000474974513

    # node Align Euler to Vector
    align_euler_to_vector = geometry_nodes.nodes.new("FunctionNodeAlignEulerToVector")
    align_euler_to_vector.name = "Align Euler to Vector"
    align_euler_to_vector.axis = "Z"
    align_euler_to_vector.pivot_axis = "AUTO"
    # Rotation
    align_euler_to_vector.inputs[0].default_value = (0.0, 0.0, 0.0)
    # Factor
    align_euler_to_vector.inputs[1].default_value = 1.0

    # node Curve to Mesh
    curve_to_mesh = geometry_nodes.nodes.new("GeometryNodeCurveToMesh")
    curve_to_mesh.name = "Curve to Mesh"
    # Fill Caps
    curve_to_mesh.inputs[2].default_value = False

    # node Curve Circle
    curve_circle = geometry_nodes.nodes.new("GeometryNodeCurvePrimitiveCircle")
    curve_circle.name = "Curve Circle"
    curve_circle.mode = "RADIUS"
    # Resolution
    curve_circle.inputs[0].default_value = 32
    # Point 1
    curve_circle.inputs[1].default_value = (-1.0, 0.0, 0.0)
    # Point 2
    curve_circle.inputs[2].default_value = (0.0, 1.0, 0.0)
    # Point 3
    curve_circle.inputs[3].default_value = (1.0, 0.0, 0.0)
    # Radius
    curve_circle.inputs[4].default_value = beam_diameter

    # node Resample Curve
    resample_curve = geometry_nodes.nodes.new("GeometryNodeResampleCurve")
    resample_curve.name = "Resample Curve"
    resample_curve.mode = "LENGTH"
    # Selection
    resample_curve.inputs[1].default_value = True
    # Count
    resample_curve.inputs[2].default_value = 200
    # Length
    resample_curve.inputs[3].default_value = 0.020000000298023224

    # node Set Curve Radius
    set_curve_radius = geometry_nodes.nodes.new("GeometryNodeSetCurveRadius")
    set_curve_radius.name = "Set Curve Radius"
    # Selection
    set_curve_radius.inputs[1].default_value = True

    # node Random Value
    random_value = geometry_nodes.nodes.new("FunctionNodeRandomValue")
    random_value.name = "Random Value"
    random_value.data_type = "FLOAT"
    # Min
    random_value.inputs[0].default_value = (0.0, 0.0, 0.0)
    # Max
    random_value.inputs[1].default_value = (1.0, 1.0, 1.0)
    # Min_001
    random_value.inputs[2].default_value = 0.75
    # Max_001
    random_value.inputs[3].default_value = 1.0
    # Min_002
    random_value.inputs[4].default_value = 0
    # Max_002
    random_value.inputs[5].default_value = 100
    # Probability
    random_value.inputs[6].default_value = 0.5
    # ID
    random_value.inputs[7].default_value = 0

    # node Scene Time
    scene_time = geometry_nodes.nodes.new("GeometryNodeInputSceneTime")
    scene_time.name = "Scene Time"

    # node Set Material
    set_material = geometry_nodes.nodes.new("GeometryNodeSetMaterial")
    set_material.name = "Set Material"
    # Selection
    set_material.inputs[1].default_value = True
    # set_material.inputs[2].default_value = bpy.data.materials[name]
    # node Set Material.001
    set_material_001 = geometry_nodes.nodes.new("GeometryNodeSetMaterial")
    set_material_001.name = "Set Material.001"
    # Selection
    set_material_001.inputs[1].default_value = True
    set_material_001.inputs[2].default_value = bpy.data.materials[name]

    # Set locations
    realize_instances.location = (648.1306762695312, -248.14083862304688)
    vector.location = (-344.9915771484375, -388.932373046875)
    set_position.location = (342.9999694824219, 16.370197296142578)
    collection_info.location = (353.42681884765625, -255.13473510742188)
    transform_geometry.location = (123.29208374023438, -17.09014892578125)
    group_input.location = (-340.0, 0.0)
    curve_line.location = (-338.0681457519531, -99.52672576904297)
    group_output.location = (1638.52880859375, 127.81448364257812)
    transform_geometry_001.location = (114.59432983398438, 326.46453857421875)
    join_geometry.location = (1591.364501953125, 254.31729125976562)
    raycast.location = (1045.16796875, -45.3947868347168)
    index.location = (380.6321105957031, 357.8047180175781)
    compare.location = (609.8900756835938, 329.3902587890625)
    align_euler_to_vector.location = (-176.80389404296875, -246.462646484375)
    curve_to_mesh.location = (1025.011962890625, 78.24966430664062)
    curve_circle.location = (772.3076171875, -106.07250213623047)
    resample_curve.location = (584.7500610351562, 68.5484848022461)
    set_curve_radius.location = (805.0, 90.10665893554688)
    random_value.location = (979.1607055664062, 341.25897216796875)
    scene_time.location = (791.7000732421875, 443.5702819824219)
    set_material.location = (1252.5028076171875, 290.9101867675781)
    set_material_001.location = (1300.63720703125, 151.0940704345703)

    # Set dimensions
    realize_instances.width, realize_instances.height = 140.0, 100.0
    vector.width, vector.height = 140.0, 100.0
    set_position.width, set_position.height = 140.0, 100.0
    collection_info.width, collection_info.height = 140.0, 100.0
    transform_geometry.width, transform_geometry.height = 140.0, 100.0
    group_input.width, group_input.height = 140.0, 100.0
    curve_line.width, curve_line.height = 140.0, 100.0
    group_output.width, group_output.height = 140.0, 100.0
    transform_geometry_001.width, transform_geometry_001.height = 140.0, 100.0
    join_geometry.width, join_geometry.height = 140.0, 100.0
    raycast.width, raycast.height = 150.0, 100.0
    index.width, index.height = 140.0, 100.0
    compare.width, compare.height = 140.0, 100.0
    align_euler_to_vector.width, align_euler_to_vector.height = 140.0, 100.0
    curve_to_mesh.width, curve_to_mesh.height = 140.0, 100.0
    curve_circle.width, curve_circle.height = 140.0, 100.0
    resample_curve.width, resample_curve.height = 140.0, 100.0
    set_curve_radius.width, set_curve_radius.height = 140.0, 100.0
    random_value.width, random_value.height = 140.0, 100.0
    scene_time.width, scene_time.height = 140.0, 100.0
    set_material.width, set_material.height = 140.0, 100.0
    set_material_001.width, set_material_001.height = 140.0, 100.0

    # initialize geometry_nodes links
    # vector.Vector -> align_euler_to_vector.Vector
    geometry_nodes.links.new(vector.outputs[0], align_euler_to_vector.inputs[2])
    # align_euler_to_vector.Rotation -> transform_geometry.Rotation
    geometry_nodes.links.new(align_euler_to_vector.outputs[0], transform_geometry.inputs[2])
    # collection_info.Instances -> realize_instances.Geometry
    geometry_nodes.links.new(collection_info.outputs[0], realize_instances.inputs[0])
    # realize_instances.Geometry -> raycast.Target Geometry
    geometry_nodes.links.new(realize_instances.outputs[0], raycast.inputs[0])
    # vector.Vector -> raycast.Ray Direction
    geometry_nodes.links.new(vector.outputs[0], raycast.inputs[3])
    # transform_geometry.Geometry -> set_position.Geometry
    geometry_nodes.links.new(transform_geometry.outputs[0], set_position.inputs[0])
    # raycast.Hit Position -> set_position.Position
    geometry_nodes.links.new(raycast.outputs[1], set_position.inputs[2])
    # group_input.Geometry -> transform_geometry_001.Geometry
    geometry_nodes.links.new(group_input.outputs[0], transform_geometry_001.inputs[0])
    # curve_line.Curve -> transform_geometry.Geometry
    geometry_nodes.links.new(curve_line.outputs[0], transform_geometry.inputs[0])
    # set_material.Geometry -> join_geometry.Geometry
    geometry_nodes.links.new(set_material.outputs[0], join_geometry.inputs[0])
    # set_material_001.Geometry -> join_geometry.Geometry
    geometry_nodes.links.new(set_material_001.outputs[0], join_geometry.inputs[0])
    # index.Index -> compare.A
    geometry_nodes.links.new(index.outputs[0], compare.inputs[0])
    # compare.Result -> set_position.Selection
    geometry_nodes.links.new(compare.outputs[0], set_position.inputs[1])
    # align_euler_to_vector.Rotation -> transform_geometry_001.Rotation
    geometry_nodes.links.new(align_euler_to_vector.outputs[0], transform_geometry_001.inputs[2])
    # join_geometry.Geometry -> group_output.Geometry
    geometry_nodes.links.new(join_geometry.outputs[0], group_output.inputs[0])
    # set_curve_radius.Curve -> curve_to_mesh.Curve
    geometry_nodes.links.new(set_curve_radius.outputs[0], curve_to_mesh.inputs[0])
    # curve_circle.Curve -> curve_to_mesh.Profile Curve
    geometry_nodes.links.new(curve_circle.outputs[0], curve_to_mesh.inputs[1])
    # set_position.Geometry -> resample_curve.Curve
    geometry_nodes.links.new(set_position.outputs[0], resample_curve.inputs[0])
    # resample_curve.Curve -> set_curve_radius.Curve
    geometry_nodes.links.new(resample_curve.outputs[0], set_curve_radius.inputs[0])
    # random_value.Value -> set_curve_radius.Radius
    geometry_nodes.links.new(random_value.outputs[1], set_curve_radius.inputs[2])
    # scene_time.Frame -> random_value.Seed
    geometry_nodes.links.new(scene_time.outputs[1], random_value.inputs[8])
    # transform_geometry_001.Geometry -> set_material.Geometry
    geometry_nodes.links.new(transform_geometry_001.outputs[0], set_material.inputs[0])
    # group_input.Material -> set_material.Material
    # geometry_nodes.links.new(group_input.outputs[1], set_material.inputs[2])
    # curve_to_mesh.Mesh -> set_material_001.Geometry
    geometry_nodes.links.new(curve_to_mesh.outputs[0], set_material_001.inputs[0])
    # group_input.Material -> set_material_001.Material
    # geometry_nodes.links.new(group_input.outputs[1], set_material_001.inputs[2])
    return geometry_nodes
