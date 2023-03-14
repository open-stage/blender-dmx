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

    filename: StringProperty(
        name = DMX_i18n.PROP_PATCH_PROFILE_NAME,
        description = DMX_i18n.PROP_PATCH_PROFILE_NAME_DESC
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
                'filename': 'BlenderDMX@Source_Four_PAR@v0.2.gdtf',
                'modes': [{
                    'name': 'Default',
                    'breaks': (1,)
                }]
            },
            {
                'name': 'Fresnel @ Generic',
                'short_name': 'FRESN',
                'filename': 'BlenderDMX@Source_Four_PAR@v0.2.gdtf',
                'modes': [{
                    'name': 'Default',
                    'breaks': (1,)
                }]
            },
            {
                'name': 'Ellipsoidal @ Generic',
                'short_name': 'ELPS',
                'filename': 'BlenderDMX@Source_Four@v0.2.gdtf',
                'modes': [{
                    'name': 'Default',
                    'breaks': (1,)
                }]
            },
            {
                'name': 'PAR 64 Can @ Generic',
                'short_name': 'PAR64',
                'filename': 'BlenderDMX@PAR_64@v0.2.gdtf',
                'modes': [{
                    'name': 'Default',
                    'breaks': (1,)
                }]
            },
            {
                'name': 'Pointe @ ROBE',
                'short_name': 'POINTE',
                'filename': 'BlenderDMX@Moving_Beam@v0.3.gdtf',
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
                'filename': 'Martin_Professional@Mac_Aura@20230201NoMeas.gdtf',
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
                'filename': 'Marslite@4_x_Mini_LED_Moving_Head_RGBW_Bar@V.1.1_by_StefanoBigoloni.com_Multi_mode.gdtf',
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
            patch.profiles[-1].filename = profile['filename']

            for mode in profile['modes']:
                patch.profiles[-1].modes.add()
                patch.profiles[-1].modes[-1].name = mode['name']
                for n in mode['breaks']:
                    patch.profiles[-1].modes[-1].breaks.add()
                    patch.profiles[-1].modes[-1].breaks[-1].n_channels = n