#
#   BlendexDMX > Model
#   Handles the creation of different models
#
#   http://www.github.com/hugoaboud/BlenderDMX
#

import os.path
import bpy

from dmx.material import getEmitterMaterial

def getModelPath():
    ADDON_PATH = os.path.dirname(os.path.abspath(__file__))
    # BUG: cross-platform directory names (won't work outside Windows)
    return ADDON_PATH+'\\data\\models\\'

#   Return the fixture model collection by name
#   If not imported, find the .blend file on dmx/data/models/
#   and copy it's "Fixture" collection

#   This collection is then deep-copied by the Fixture class
#   to create a fixture collection.

def getFixtureModelCollection(model):

    # If the fixture collection was already imported for this model
    # just return it
    if (model in bpy.data.collections):
        return bpy.data.collections[model]

    path = getModelPath()+model+'.blend'

    # Make sure the file exists, otherwise return None
    if (not os.path.exists(path) or not os.path.isfile(path)):
        raise OSError("Model not found: " + path)

    # Load fixture collection from .blend model file
    with bpy.data.libraries.load(path) as (data_from, data_to):
        for coll in data_from.collections:
            if (coll == "Fixture"):
                data_to.collections = ["Fixture"]

    # Make sure a fixture collection was found
    if (len(data_to.collections) == 0):
        raise SyntaxError("No 'Fixture' collection found on model: " + path)

    # Rename collection
    data_to.collections[0].name = model

    return data_to.collections[0]
