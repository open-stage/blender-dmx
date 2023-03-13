class DMX_i18n:

    # Patch

    # Patch > Menus

    MENU_PATCH_SELECT_UNIVERSE = 'DMX Universe'
    MENU_PATCH_SELECT_UNIVERSE_OP = 'Select DMX Universe'

    MENU_PATCH_SELECT_MODE = 'DMX Universe'
    MENU_PATCH_SELECT_MODE_OP = 'Select DMX Universe'
    
    # Patch > Operators

    OP_PATCH_SOURCE_CONFIGURE = 'Configure Source'
    OP_PATCH_SOURCE_CONFIGURE_DESC = 'Opens a dialog for configuring this Source.'

    OP_PATCH_UNIVERSE_ADD = 'Add Universe'
    OP_PATCH_UNIVERSE_ADD_DESC = 'Add a new Universe to the Patch.'

    OP_PATCH_FIXTURE_ADD = 'Add Single Fixture'
    OP_PATCH_FIXTURE_ADD_DESC = 'Add a single new Fixture to the Patch.'
    
    OP_PATCH_FIXTURE_ADDBATCH = 'Add Fixture Batch'
    OP_PATCH_FIXTURE_ADDBATCH_DESC = 'Add new Fixture Batch to the Patch.'
    
    OP_PATCH_FIXTURE_REMOVE = 'Remove Fixture'
    OP_PATCH_FIXTURE_REMOVE_DESC = 'Remove this Fixture from the Patch.'
    
    OP_PATCH_BUILD = 'Build Fixtures'
    OP_PATCH_BUILD_DESC = 'After completing the patch, you should click this button to build/update the fixture geometry.'

    # Patch > Panel

    PANEL_PATCH = 'DMX Patch'
    PANEL_PATCH_UNIVERSES = 'Universes'
    PANEL_PATCH_FIXTURES = 'Fixtures'

    # Patch > Properties > Fixture

    PROP_PATCH_FIXTURE_ID = 'ID'
    PROP_PATCH_FIXTURE_ID_DESC = 'A numeric unique identifier for the fixture.'

    PROP_PATCH_FIXTURE_NAME = 'Name'
    PROP_PATCH_FIXTURE_NAME_DESC = 'A unique name for the fixture.'

    PROP_PATCH_FIXTURE_PROFILE = 'GDTF Profile'
    PROP_PATCH_FIXTURE_PROFILE_DESC = 'The GDTF profile of the fixture.'

    PROP_PATCH_FIXTURE_MODE = 'GDTF Mode'
    PROP_PATCH_FIXTURE_MODE_DESC = 'The GDTF mode of the current profile.'

    PROP_PATCH_FIXTURE_NCHANNELS = 'Number of Channels'
    PROP_PATCH_FIXTURE_NCHANNELS_DESC = 'The number of channels of the current profile.'

    PROP_PATCH_FIXTURE_ADDRESS = 'DMX Address'
    PROP_PATCH_FIXTURE_ADDRESS_DESC = 'The DMX address of the fixture at the current universe.'

    PROP_PATCH_FIXTURE_UNIVERSE = 'DMX Universe'
    PROP_PATCH_FIXTURE_UNIVERSE_DESC = 'The DMX universe to which the fixture is currently addressed.'

    PROP_PATCH_FIXTURE_CREATELIGHTS = 'Create Lights'
    PROP_PATCH_FIXTURE_CREATELIGHTS_DESC = 'This fixture should have light sources. If false, the lights are created with emitter materials only. Keep in mind that Blender has a 128 light sources limitation.'

    PROP_PATCH_FIXTURE_GELCOLOR = 'Gel Color'
    PROP_PATCH_FIXTURE_GELCOLOR_DESC = 'Color of the gel applied to the fixture, in case the profile doesn\'t define color channels.'

    # Patch > Properties > Fixture Batch

    PROP_PATCH_FIXTUREBATCH_NAME = 'Name'
    PROP_PATCH_FIXTUREBATCH_NAME_DESC = 'A unique name for the fixture batch.'

    PROP_PATCH_FIXTUREBATCH_UNITS = 'Units'
    PROP_PATCH_FIXTUREBATCH_UNITS_DESC = 'The number of fixtures inside this batch.'

    PROP_PATCH_FIXTUREBATCH_SEQUENTIAL = 'Sequential'
    PROP_PATCH_FIXTUREBATCH_SEQUENTIAL_DESC = 'The fixtures in this batch are automatically addressed in a sequence.'

    PROP_PATCH_FIXTUREBATCH_FOOTPRINT = 'Footprint'
    PROP_PATCH_FIXTUREBATCH_FOOTPRINT_DESC = 'Overrides the footprint of each fixture.'

    # Patch > Properties > Profile

    PROP_PATCH_PROFILE_NAME = 'Name'
    PROP_PATCH_PROFILE_NAME_DESC = 'The name of the DMX profile.'

    PROP_PATCH_PROFILE_SHORT_NAME = 'Short Name'
    PROP_PATCH_PROFILE_SHORT_NAME_DESC = 'The short name of the DMX profile, all caps, used as suggestion for fixture names.'

    # Patch > Properties > Source

    PROP_PATCH_SOURCE_TYPE = 'Type'
    PROP_PATCH_SOURCE_TYPE_DESC = 'The type of DMX source.'

    # Patch > Properties > Universe

    PROP_PATCH_UNIVERSE_NAME = 'Name'
    PROP_PATCH_UNIVERSE_NAME_DESC = 'A unique name for the DMX universe.'

    PROP_PATCH_UNIVERSE_NUMBER = 'Number'
    PROP_PATCH_UNIVERSE_NUMBER_DESC = 'The number of the DMX universe.'

    PROP_PATCH_UNIVERSE_SOURCE = 'Source'
    PROP_PATCH_UNIVERSE_SOURCE_DESC = 'The type of DMX source of the universe.'

    # Programmer

    # Programmer > Panel

    PANEL_PROGRAMMER = 'Programmer'

    # Programmer > Operators

    OP_PROGRAMMER_SELECTALL = 'Select All'
    OP_PROGRAMMER_SELECTALL_DESC = 'Select every fixture in the scene.'

    OP_PROGRAMMER_SELECTINVERT = 'Invert Selection'
    OP_PROGRAMMER_SELECTINVERT_DESC = 'Invert the selection of fixtures.'

    OP_PROGRAMMER_SELECTEVERYOTHER = 'Select Every Other'
    OP_PROGRAMMER_SELECTEVERYOTHER_DESC = 'Select every other light.'

    OP_PROGRAMMER_DESELECTALL = 'Deselect All'
    OP_PROGRAMMER_DESELECTALL_DESC = 'Deselect every object in the scene.'

    OP_PROGRAMMER_SELECTBODIES = 'Bodies'
    OP_PROGRAMMER_SELECTBODIES_DESC = 'Select body from every fixture selected.'

    OP_PROGRAMMER_SELECTTARGETS = 'Targets'
    OP_PROGRAMMER_SELECTTARGETS_DESC = 'Select target from every fixture selected.'

    OP_PROGRAMMER_CLEAR = 'Clear'
    OP_PROGRAMMER_CLEAR_DESC = 'Clears the selected fixtures.'