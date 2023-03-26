import bpy

from src.core import util
from src.core.builder import DMX_SceneBuilder

class DMX_Core_Controller:
    
    def build_patch(self) -> None:
        '''
        Rebuild all DMX fixtures from the Patch.
        '''
        self.collection = util.new_collection('DMX')
        util.activate_collection(self.collection)
        DMX_SceneBuilder().build()

