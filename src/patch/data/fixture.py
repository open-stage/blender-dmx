import bpy
from bpy.types import PropertyGroup
from bpy.props import ( BoolProperty,
                        FloatVectorProperty,
                        IntProperty,
                        StringProperty )

from src.i18n import DMX_i18n

class DMX_Patch_Fixture(PropertyGroup):

    # Identification

    id: IntProperty(
        name = DMX_i18n.PROP_PATCH_FIXTURE_ID,
        description = DMX_i18n.PROP_PATCH_FIXTURE_ID_DESC,
        min = 1,
        max = 9999
    )

    name: StringProperty(
        name = DMX_i18n.PROP_PATCH_FIXTURE_NAME,
        description = DMX_i18n.PROP_PATCH_FIXTURE_NAME_DESC
    )

    # GDTF

    profile: StringProperty(
        name = DMX_i18n.PROP_PATCH_FIXTURE_PROFILE,
        description = DMX_i18n.PROP_PATCH_FIXTURE_PROFILE_DESC
    )

    mode: StringProperty(
        name = DMX_i18n.PROP_PATCH_FIXTURE_MODE,
        description = DMX_i18n.PROP_PATCH_FIXTURE_MODE_DESC
    )

    n_channels: IntProperty(
        name = DMX_i18n.PROP_PATCH_FIXTURE_NCHANNELS,
        description = DMX_i18n.PROP_PATCH_FIXTURE_NCHANNELS_DESC,
        default = 0
    )

    # DMX Addressing

    address: IntProperty(
        name = DMX_i18n.PROP_PATCH_FIXTURE_ADDRESS,
        description = DMX_i18n.PROP_PATCH_FIXTURE_ADDRESS_DESC,
        default = 1,
        min = 1,
        max = 512
    )

    universe: IntProperty(
        name = DMX_i18n.PROP_PATCH_FIXTURE_UNIVERSE,
        description = DMX_i18n.PROP_PATCH_FIXTURE_UNIVERSE_DESC,
        default = 1,
        min = 1,
        max = 512
    )

    # Settings

    create_lights: BoolProperty(
        name = DMX_i18n.PROP_PATCH_FIXTURE_CREATELIGHTS,
        description = DMX_i18n.PROP_PATCH_FIXTURE_CREATELIGHTS_DESC,
        default = True
    )

    gel_color: FloatVectorProperty(
        name = DMX_i18n.PROP_PATCH_FIXTURE_GELCOLOR,
        description = DMX_i18n.PROP_PATCH_FIXTURE_GELCOLOR_DESC,
        subtype = "COLOR",
        size = 4,
        min = 0.0,
        max = 1.0,
        default = (1.0,1.0,1.0,1.0))

    # Fixture Batch Info

    batch: IntProperty(
        default = -1
    )
    batch_index: IntProperty(
        default = -1
    )

    # Getters

    def get_universe_str(self, context, mini=False):
        patch = context.scene.dmx.patch
        universe = patch.universes[self.universe-1]
        if (mini):
            return str(universe.number)
        else:
            return f'{universe.number}: {universe.name}'

    def get_mode_str(self, mini=False):
        if (mini):
            if (self.n_channels == 0):
                return ''
            return f'{self.n_channels} chs'
        else:
            return f'{self.mode} ({self.n_channels} chs)'

    def get_batch(self, context):
        if (self.batch == -1):
            return None
        return context.scene.dmx.patch.fixture_batches[self.batch]