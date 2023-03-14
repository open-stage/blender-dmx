from src.core.builder.patch_builder import DMX_PatchBuilder
from src.core import util

class DMX_Core_Controller:
    
    def build_patch(self):
        self.collection = util.new_collection('DMX')
        util.activate_collection(self.collection)
        DMX_PatchBuilder()