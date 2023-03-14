import re

from .manager import DMX_Patch_Manager
from .callback import DMX_Patch_Callback

class DMX_Patch_Controller(
    DMX_Patch_Manager,
    DMX_Patch_Callback
):
    pass