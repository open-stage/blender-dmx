import bpy
from bpy.types import PropertyGroup
from bpy.props import (
    BoolProperty,
    FloatVectorProperty,
    IntProperty,
    CollectionProperty,
    StringProperty,
)

from i18n import DMX_Lang

_ = DMX_Lang._

from src.patch.controller import DMX_Patch_Controller


class DMX_Patch_FixtureBreak(PropertyGroup):
    n_channels: IntProperty(
        name=_("Number of Channels"),
        description=_("The number of channels of the current profile."),
        default=0,
    )

    address: IntProperty(
        name=_("DMX Address"),
        description=_("The DMX address of the fixture at the current universe."),
        default=1,
        min=1,
        max=512,
    )

    universe: IntProperty(
        name=_("DMX Universe"),
        description=_("The DMX universe to which the fixture is currently addressed."),
        default=1,
        min=1,
        max=512,
    )


class DMX_Patch_Fixture(PropertyGroup):
    # Identification

    id: IntProperty(
        name=_("ID"),
        description=_("A numeric unique identifier for the fixture."),
        min=1,
        max=9999,
    )

    name: StringProperty(
        name=_("Name"),
        description=_("A unique name for the fixture."),
    )

    # GDTF

    profile: StringProperty(
        name=_("GDTF Profile"),
        description=_("The GDTF profile of the fixture."),
        update=DMX_Patch_Controller.on_fixture_profile,
    )

    mode: StringProperty(
        name=_("GDTF Mode"),
        description=_("The GDTF mode of the current profile."),
    )

    # DMX Addressing

    breaks: CollectionProperty(
        name=_("Number of Channels"),
        description=_("The number of channels of the current profile."),
        type=DMX_Patch_FixtureBreak,
    )

    # Settings

    create_lights: BoolProperty(
        name=_("Create Lights"),
        description=_(
            "This fixture should have light sources. If false, the lights are created with emitter materials only. Keep in mind that Blender has a 128 light sources limitation."
        ),
        default=True,
    )

    gel_color: FloatVectorProperty(
        name=_("Gel Color"),
        description=_(
            "Color of the gel applied to the fixture, in case the profile doesn't define color channels."
        ),
        subtype="COLOR",
        size=4,
        min=0.0,
        max=1.0,
        default=(1.0, 1.0, 1.0, 1.0),
    )

    # Fixture Batch Info

    batch: IntProperty(default=-1)
    batch_index: IntProperty(default=-1)

    # Getters

    def get_profile(self, context) -> 'DMX_Patch_Profile':
        return context.scene.dmx.patch.profiles.get(self.profile, None)

    def get_mode(self, context) -> 'DMX_Patch_ProfileMode':
        profile = self.get_profile(context)
        return profile.modes.get(self.mode, None)

    def get_address_str(self, context, break_i: int) -> str:
        if break_i >= len(self.breaks):
            return None

        patch = context.scene.dmx.patch
        address = self.breaks[break_i].address

        return str(address)

    def get_universe_str(self, context, break_i: int, mini=False) -> str:
        if break_i >= len(self.breaks):
            return None

        patch = context.scene.dmx.patch
        universe_i = self.breaks[break_i].universe
        if universe_i > len(patch.universes):
            return None

        universe = patch.universes[universe_i - 1]
        if mini:
            return str(universe.number)
        else:
            return f"{universe.number}: {universe.name}"

    def get_mode_str(self, mini=False) -> str:
        if len(self.breaks) == 0:
            return None
        breaks = [b.n_channels for b in self.breaks]
        if len(breaks) == 1:
            n_channels = str(breaks[0])
        else:
            n_channels = "+".join(str(b) for b in breaks)
        if mini:
            return f"{n_channels} chs"
        else:
            return f"{self.mode}, {n_channels} chs"

    def get_batch(self, context) -> 'DMX_Patch_FixtureBatch':
        if self.batch == -1:
            return None
        return context.scene.dmx.patch.fixture_batches[self.batch]
