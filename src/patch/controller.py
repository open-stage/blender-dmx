import re

class DMX_Patch_Controller:

    @staticmethod
    def _get_next_fixture_index(fixtures, short_name: str) -> int:
        names = [f.name for f in fixtures if f.name.startswith(short_name)]
        if (len(names) == 0):
            return 1
        indexes = [re.findall(r'\d+', name) for name in names]
        indexes = [int(i[-1]) for i in indexes if len(i)]
        return max(indexes)+1

    @staticmethod
    def on_fixture_profile(fixture: 'DMX_Patch_Fixture', context):
        if (len(fixture.profile) == 0):
            return
        # If the name is not filled, suggest a name
        if (len(fixture.name) == 0):
            patch = context.scene.dmx.patch
            profile = patch.profiles[fixture.profile]
            index = DMX_Patch_Controller._get_next_fixture_index(patch.fixtures, profile.short_name)
            fixture.name = f'{profile.short_name} {index}'
        # Select default mode

    @staticmethod
    def on_select_mode(fixture: 'DMX_Patch_Fixture', context):
        mode = fixture.get_mode(context)
        fixture.breaks.clear()
        for mode_break in mode.breaks:
            fixture.breaks.add()
            fixture.breaks[-1].n_channels = mode_break.n_channels