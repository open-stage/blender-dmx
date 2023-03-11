import bpy
from bpy.types import PropertyGroup
from bpy.props import StringProperty

from src.i18n import DMX_i18n

class DMX_Patch_Profile(PropertyGroup):

    name: StringProperty(
        name = DMX_i18n.PROP_PATCH_PROFILE_NAME,
        description = DMX_i18n.PROP_PATCH_PROFILE_NAME_DESC
    )

    @staticmethod
    def load():
        patch = bpy.context.scene.dmx.patch
        patch.profiles.clear()
        for name in [
            'Fog/Haze @ Generic',
            'Fresnel @ Generic',
            'Ellipsoidal @ Generic',
            'PAR 64 Can @ Generic',
            'Pointe @ ROBE',
            'MAC Aura @ Martin'
        ]:
            patch.profiles.add()
            patch.profiles[-1].name = name