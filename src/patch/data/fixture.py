import bpy
from bpy.types import PropertyGroup
from bpy.props import ( BoolProperty,
                        FloatVectorProperty,
                        IntProperty,
                        CollectionProperty,
                        StringProperty )

from src.i18n import DMX_i18n
from ..controller import DMX_Patch_Controller

class DMX_Patch_FixtureBreak(PropertyGroup):

    n_channels: IntProperty(
        name = DMX_i18n.PROP_PATCH_FIXTURE_NCHANNELS,
        description = DMX_i18n.PROP_PATCH_FIXTURE_NCHANNELS_DESC,
        default = 0
    )

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
        description = DMX_i18n.PROP_PATCH_FIXTURE_PROFILE_DESC,
        update = DMX_Patch_Controller.on_fixture_profile
    )

    mode: StringProperty(
        name = DMX_i18n.PROP_PATCH_FIXTURE_MODE,
        description = DMX_i18n.PROP_PATCH_FIXTURE_MODE_DESC
    )

    # DMX Addressing

    breaks: CollectionProperty(
        name = DMX_i18n.PROP_PATCH_FIXTURE_NCHANNELS,
        description = DMX_i18n.PROP_PATCH_FIXTURE_NCHANNELS_DESC,
        type = DMX_Patch_FixtureBreak
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

    def get_profile(self, context):
        return context.scene.dmx.patch.profiles.get(self.profile, None)

    def get_mode(self, context):
        profile = self.get_profile(context)
        return profile.modes.get(self.mode, None)

    def get_address_str(self, context, break_i):
        if (break_i >= len(self.breaks)):
            return None

        patch = context.scene.dmx.patch
        address = self.breaks[break_i].address
        
        return str(address)
        
    def get_universe_str(self, context, break_i, mini=False):
        if (break_i >= len(self.breaks)):
            return None

        patch = context.scene.dmx.patch
        universe_i = self.breaks[break_i].universe
        if universe_i > len(patch.universes):
            return None

        universe = patch.universes[universe_i-1]
        if (mini):
            return str(universe.number)
        else:
            return f'{universe.number}: {universe.name}'

    def get_mode_str(self, mini=False):
        if (len(self.breaks) == 0):
            return None
        breaks = [b.n_channels for b in self.breaks]
        if (len(breaks) == 1):
            n_channels = str(breaks[0])
        else:
            n_channels = '+'.join(str(b) for b in breaks)
        if (mini):
            return f'{n_channels} chs'
        else:
            return f'{self.mode}, {n_channels} chs'

    def get_batch(self, context):
        if (self.batch == -1):
            return None
        return context.scene.dmx.patch.fixture_batches[self.batch]