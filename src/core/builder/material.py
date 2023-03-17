import bpy

SHADER_NODE_BSDF = 'ShaderNodeBsdfPrincipled'
SHADER_NODE_OUTPUT = 'ShaderNodeOutputMaterial'
SHADER_NODE_EMISSION = 'ShaderNodeEmission'

class DMX_Material:
    '''
    Manager for the materials used by the Add-on.
    '''

    EMITTER_NODE_NAME = 'DMX_Emitter'

    @staticmethod
    def reset_emitter_material(fixture: 'DMX_Fixture', geometry_name: str):
        
        # Delete and create material
        name = f'{fixture.name}#{geometry_name}'
        if name in bpy.data.materials:
            bpy.data.materials.remove(bpy.data.materials[name])
        material = bpy.data.materials.new(name)

        material.use_nodes = True
        nodes = material.node_tree.nodes
        links = material.node_tree.links

        # Remove BSDF and get Output node
        output = None
        for node in nodes:
            if node.bl_idname == SHADER_NODE_BSDF:
                nodes.remove(node)
            elif node.bl_idname == SHADER_NODE_OUTPUT:
                output = node

        if not output:
            raise Exception(f'Output node not found while creating emitter material for fixture {fixture.name}')

        # Add a new emitter node and link it to output
        emission_node = nodes.new(SHADER_NODE_EMISSION)
        emission_node.name = DMX_Material.EMITTER_NODE_NAME
        links.new(emission_node.outputs[0], output.inputs[0])

        return material


# # Shader Nodes default labels
# # Blender API naming convention is inconsistent for internationalization
# # Every label used is listed here, so it's easier to fix it on new API updates
# PRINCIPLED_BSDF = 'Principled BSDF'
# MATERIAL_OUTPUT = 'Material Output'
# SHADER_NODE_EMISSION = 'ShaderNodeEmission'
# SHADER_NODE_VOLUMESCATTER = 'ShaderNodeVolumeScatter'
# VOLUME_SCATTER = bpy.app.translations.pgettext('Volume Scatter')
# EMISSION = bpy.app.translations.pgettext('Emission')

# # <get Emitter Material>
# #   Create an emissive material with given name, remove if already present
# def get_emitter_material(name):
#     if (name in bpy.data.materials):
#         bpy.data.materials.remove(bpy.data.materials[name])
#     material = bpy.data.materials.new(name)
#     material.use_nodes = True
#     # BUG: Internationalization
#     if PRINCIPLED_BSDF in material.node_tree.nodes:
#         material.node_tree.nodes.remove(material.node_tree.nodes[PRINCIPLED_BSDF])
#     else:
#         DMX_Log.log.error('''BSDF material could not be removed when adding new Emitter,
#                          this could cause issues. Set Logging level to Info to get more details.''')
#         if DMX_Log.log.isEnabledFor(logging.INFO):
#             print('Nodes in material tree nodes:')
#             for node in material.node_tree.nodes:
#                 print(node)
#     material.node_tree.nodes.new(SHADER_NODE_EMISSION)
#     material.node_tree.links.new(material.node_tree.nodes[MATERIAL_OUTPUT].inputs[0], material.node_tree.nodes[EMISSION].outputs[0])
#     return material

# def get_volume_scatter_material():
#     if ('DMX_Volume' in bpy.data.materials):
#         return bpy.data.materials['DMX_Volume']

#     material = bpy.data.materials.new('DMX_Volume')
#     material.use_nodes = True
#     # BUG: Internationalization
#     if PRINCIPLED_BSDF in material.node_tree.nodes:
#         material.node_tree.nodes.remove(material.node_tree.nodes[PRINCIPLED_BSDF])
#     else:
#         DMX_Log.log.error('''BSDF material could not be removed when adding creating Volume,
#                        this could cause issues. Set Logging level to Info to get more details.''')
#         if DMX_Log.log.isEnabledFor(logging.INFO):
#             print('Nodes in material tree nodes:')
#             for node in material.node_tree.nodes:
#                 print(node)

#     material.node_tree.nodes.new(SHADER_NODE_VOLUMESCATTER)
#     material.node_tree.links.new(material.node_tree.nodes[MATERIAL_OUTPUT].inputs[1], material.node_tree.nodes[VOLUME_SCATTER].outputs[0])
#     return material