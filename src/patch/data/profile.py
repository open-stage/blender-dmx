import bpy
from bpy.types import PropertyGroup
from bpy.props import ( StringProperty,
                        CollectionProperty,
                        IntProperty )

from src.i18n import DMX_i18n


class DMX_Patch_ProfileBreak(PropertyGroup):

    n_channels: IntProperty(
        name = DMX_i18n.PROP_PATCH_PROFILE_NAME,
        description = DMX_i18n.PROP_PATCH_PROFILE_NAME_DESC
    )

class DMX_Patch_ProfileMode(PropertyGroup):

    name: StringProperty(
        name = DMX_i18n.PROP_PATCH_PROFILE_NAME,
        description = DMX_i18n.PROP_PATCH_PROFILE_NAME_DESC
    )

    breaks: CollectionProperty(
        name = DMX_i18n.PROP_PATCH_PROFILE_NAME,
        description = DMX_i18n.PROP_PATCH_PROFILE_NAME_DESC,
        type = DMX_Patch_ProfileBreak
    )


class DMX_Patch_Profile(PropertyGroup):

    name: StringProperty(
        name = DMX_i18n.PROP_PATCH_PROFILE_NAME,
        description = DMX_i18n.PROP_PATCH_PROFILE_NAME_DESC
    )

    short_name: StringProperty(
        name = DMX_i18n.PROP_PATCH_PROFILE_SHORT_NAME,
        description = DMX_i18n.PROP_PATCH_PROFILE_SHORT_NAME_DESC
    )

    modes: CollectionProperty(
        type = DMX_Patch_ProfileMode
    )

    @staticmethod
    def load():
        patch = bpy.context.scene.dmx.patch
        patch.profiles.clear()

        profiles = [
            {
                'name': 'Fog/Haze @ Generic',
                'short_name': 'FOG',
                'modes': [{
                    'name': 'Default',
                    'breaks': (1,)
                }]
            },
            {
                'name': 'Fresnel @ Generic',
                'short_name': 'FRESN',
                'modes': [{
                    'name': 'Default',
                    'breaks': (1,)
                }]
            },
            {
                'name': 'Ellipsoidal @ Generic',
                'short_name': 'ELPS',
                'modes': [{
                    'name': 'Default',
                    'breaks': (1,)
                }]
            },
            {
                'name': 'PAR 64 Can @ Generic',
                'short_name': 'PAR64',
                'modes': [{
                    'name': 'Default',
                    'breaks': (1,)
                }]
            },
            {
                'name': 'Pointe @ ROBE',
                'short_name': 'POINTE',
                'modes': [{
                    'name': 'Standard',
                    'breaks': (14,)
                },{
                    'name': 'Extended',
                    'breaks': (23,)
                }]
            },
            {
                'name': 'MAC Aura @ Martin',
                'short_name': 'MACAUR',
                'modes': [{
                    'name': 'Standard',
                    'breaks': (14,)
                },{
                    'name': 'Extended',
                    'breaks': (25,)
                }]
            },
            {
                'name': 'Multi-Break @ Test',
                'short_name': 'MBREAK',
                'modes': [{
                    'name': 'One Break',
                    'breaks': (12,)
                },{
                    'name': 'Two Breaks',
                    'breaks': (15, 13)
                },{
                    'name': 'Three Breaks',
                    'breaks': (14, 17, 3)
                }]
            }
        ]

        for profile in profiles:
            patch.profiles.add()
            patch.profiles[-1].name = profile['name']
            patch.profiles[-1].short_name = profile['short_name']

            for mode in profile['modes']:
                patch.profiles[-1].modes.add()
                patch.profiles[-1].modes[-1].name = mode['name']
                for n in mode['breaks']:
                    patch.profiles[-1].modes[-1].breaks.add()
                    patch.profiles[-1].modes[-1].breaks[-1].n_channels = n