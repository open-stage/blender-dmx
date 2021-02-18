#
#   BlendexDMX > Model
#   Handles the creation of different models
#
#   http://www.github.com/hugoaboud/BlenderDMX
#

import os.path
import bpy

from dmx.material import getEmitterMaterial

class DMX_Model():

    @staticmethod
    def getModelsPath():
        ADDON_PATH = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(ADDON_PATH,'data','models')

    @staticmethod
    def getModelList(fixtureClass):
        # If models are defined on the fixture class (in case of parametric models such as tubes)
        # Just take the list from them
        if (fixtureClass.MODELS != None):
            return fixtureClass.MODELS

        # If not, List models in folder with the fixture class prefix
        models = []
        i = 0
        for file in os.listdir(DMX_Model.getModelsPath()):
            # Parse info from file name: Company@Model.gdtf
            info = file.split('@')
            if (info[0] == fixtureClass.PREFIX):
                info[2] = info[2][:-6]
                # Add to list (identifier, short name, full name)
                models.append((file, info[1], info[0]+" | "+info[1], info[2], i))
                i += 1

        return tuple(models)

    #   Return the fixture model collection by name
    #   If not imported, find the .blend file on dmx/data/models/
    #   and copy it's "Fixture" collection
    #   This collection is then deep-copied by the Fixture class
    #   to create a fixture collection.
    @staticmethod
    def getFixtureModelCollection(name):

        # If the fixture collection was already imported for this model
        # just return it
        if (name in bpy.data.collections):
            return bpy.data.collections[name]

        path = os.path.join(DMX_Model.getModelsPath(),name)

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
        data_to.collections[0].name = name

        return data_to.collections[0]
