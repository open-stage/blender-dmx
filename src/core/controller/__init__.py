import bpy

from src.core import util
from src.core.builder import DMX_Builder

class DMX_Core_Controller:
    
    def build_patch(self):
        self.collection = util.new_collection('DMX')
        util.activate_collection(self.collection)
        DMX_Builder()

