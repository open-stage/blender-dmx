### Changelog

### 1.4.1

    * Handle XML files with null byte at the end
    * Add support for Color Wheels (Color1, Color2, and ColorMacro1 GDTF attributes)

### 1.4.0

    *  Add initial support for laser projection
    *  Add Import of GDTF and MVR to Setup panel
    *  Set materials for models of default fixture files
    *  Add gMA3 icon to MVR-exchange stations list

### 1.3.3

    * Add support for ColorRGB_Red/Green/Blue color attributes
    * Bug fix pan/tilt lock

### 1.3.2

    * Improve pan/tilt controlling and animating:
        * Support multiple pan/tilt geometries for fixtures without Target
        * Set Ignore pan/tilt DMX (lock target) after using Target to set
          position, to allow programming keyframes by Target
        * Indicate pan/tilt lock and provide quick unlock in programmer
        * Ensure that keyframes are saved when programming position by Target
    * Provide shortcut to select prev/next Target (Ctrl-Shift-Left/Right)
    * Improve logging during addon initialization
    * Fix fixture addressing procedure
    * Add minimal required Blender version message to Setup panel
    * Add links to documentation
    * Add Rotation to the list of editable fixture's columns
    * Indicate IES by an icon in fixture's name

### 1.3.1

    * Add support to import IES photometrics and apply them to beams in Cycles
    * Allow changing beam lens diameter for Cycles, based on global or per fixture settings
    * Set hidden objects as hidden also for renderer
    * Make more items translatable, disable automatic translation for Fixture controls
    * Add version checks on start for Python, Blender, and for the BlenderDMX addon

### 1.3.0

    * Add support for gobos in Cycles
    * Add translation of UI
    * Add Noise Scatter to Volume box
    * Enable programmer only if any fixture is selected
    * Small improvements:
        * GDTF download: Better sanitizing of GDTF download file name
        * Handle ArtNet status setting error
        * MVR import: check if file exists before loading it
        * Handle fixtures without dimmer
        * Handle fixtures with gobo but without zoom

### 1.2.0

    * Initial keyframing support with Auto Keying and Manual Keyframe insert
    * Add new default 2D symbol based on BlenderDMX logo
    * Use BlenderDMX's own Art-Net OEM code into ArtPollReply
    * Select multiple fixtures in Fixture list with Shift
    * Add button to request latest version of an MVR scene from MVR-xchange

### 1.1.0

* MVR-xchange:
    * Add proper listener and sender (client and server) to MVR-xchange, to match the Spec
    * Many other improvements to MVR-xchange
* Logging:
    * Ensure that logger is not initialized multiple times
    * Add logging to file
    * Add filters to allow logging only specific parts of the app
    * Convert most prints() to log
* UI:
    * Speed up LiveDMX view refresh
    * When adding/editing fixtures, allow to (not)increment address/id
    * Set 2D view to Material rather then Solid
    * Reorganize Setup panels
    * Ensure automatic UI refresh for several panels
* GDTF/MVR/Fixtures:
    * Speed up DMX values caching for render loop bypass
    * Scale gobo planes during fixture creation
    * Unzip correctly files with non latin encoding in file names

### 1.0.8

* Initial GOBO from GDTF support with indexing and rotation
* Programmer improvements (name/count of selection, fixture specific control)
* Add on-line version check into Extras
* If no fixture is selected, select first/last on Ctrl-Right/Left
* MVR-xchange improvements and custom icons
* Hide/show positions in Fixtures edit list
* Updating bdmx driver syntax to #bdmx

### 1.0.7

* New Fixture UI List:
    * Better scrolling and filtering
    * In-place editing of some attributes
    * New editing of XYZ position transforms
* Indicate that Blender 3.4 and higher is required
* Improvements to MVR-xchange:
    * Support for MVR_COMMIT message
    * Rewrite of the protocol code
* Add custom namespace driver for Blender, to use DMX for general animations of
  any 3D objects in Blender
* Improved Network DMX protocols:
    * Separate sACN from Art-Net
    * Improve Art-Net handling (ArtPoll, error messages, timeout)
    * Universe setting made clearer

### 1.0.6

* Initial support for MVR-xchange protocol added
* Added ArtPoll reply

### 1.0.5

* Set beam type based on Spot/Wash/None beam types as defined in GDTF
* Allow MVR reimport:
    * existing objects/fixtures/trusses... (by UUIDs) will be updated by data
      in MVR
    * new objects... will be added to the scene
    * there is a new internal structure for scene objects, not visible to the
      user at this point
* Add OpenSoundControl (OSC):
    * send fixture selection to consoles
    * allow multiple commands to be sent
    * definition in json
* Network improvements:
    * list of IPs is now dynamic
    * add 0.0.0.0 to the IP list
* Device and group listing and editing:
    * Show number of fixtures in a group
    * Allow to soft fixtures differently
    * Allow incremental Fixture IDs
    * Use original fixture's UUID during fixture edit
    * Improve 'Re-address only' dialog
* Handle errors during fixture adding more gracefully:
    * do not add the fixture to the fixture list
    * remove bad collection
    * show error message
    * allow to remove non-selectable fixtures
* Fix group creation during MVR import
* Apply stored position and rotation only on root geometry
* Use fixture UUIDs instead of names in groups (ensures group validity on fixture
  rename):
    * ensure unique UUIDs in fixtures
    * ensure unique UUIDs in groups
* Add DMX data caching to shortcut render loop to prevent flicker a bit

### 1.0.4
* Fixing a color control bug with pixel devices like Spiider
* Fix tilt movement when fixture is on the floor
* More attributes are now applied (only) for correct geometries (RGB, XYZ
  position and rotation, dimmer)
* Extending Volume preview settings to now have the possibility to see the fake
  beam cone for None, Selected fixtures or All fixtures
* Adding RGB based color picker to the existing color picker in Programmer
* Support for movement control of fixtures with pan only (without tilt)
* Initial support for 16bit channels for smoother behavior: pan, tilt, dimmer
* Group selection can now be additive (as before) or exclusive (only selected
  group)
* Allow freezing of pan/tilt movement to current position (for example after
  Target adjustment). Indicated by LOCK icon in Fixture list
* GDTF Share Password in Preferences now masked with \*\*\*\*\*
* Fixture ID in Fixture list is now displayed only if not empty

### 1.0.3
* MVR Improvements:
  * Add FixtureID, CustomId... from MVR to Fixture
  * Create groups from MVR, migrate groups from str([]) to json
  * Clean up unused MVR collections after MVR import
  * Add UUID to fixtures and groups

* GDTF Improvements:
  * Handle models composed of multiple parts

* App improvements:
  * Add initial support for 2D symbols and 2D TOP planning view
  * Speed up MVR import - fix GDTF collection caching, cache also MVR imported objects
  * Converted Primitives to glb to ensure compatibility with Blender 4.x
  * Increment data version and provide migration
  * Remove fixture from groups when deleting fixture
  * Display revision in fixture listing
  * Create new World in case it is missing
  * Allow centering selected fixture's Targets
  * Handle time during fixture edit processing (prevent errors)
  * Check for existence of Dimmer for fixtures without dimmer (prevent errors)
  * Add possibility to make fixture geometries selectable
  * Display Volume cone on all lights when enabled
  * Add generix XYZ fixture to BlenderDMX
  * Add support for XYZ Z,Y,Z a nd Rot X,Y,Z attributes and for devices without target

### 1.0.2
* MVR improvements:
  * Add collections for GroupObjects and Layers
  * Support group object list
  * Process child lists of MVR objects
  * Apply scaling of 3D objects in correct order
  * Load textures for 3D models
* Fixture profiles management:
  * Backport local and GDTF Share file management and import from development branch
  * Add GDTF Share integration (can be used with username/password from gdtf-share.com)
  * Improve local profiles handling
  * Do not require Blender restart after GDTF profiles import
* Improve GDTF parsing
* Fix issue with localize structures by requesting localized versions of strings

#### 1.0.1
* Improved MVR import:
  * Import Focus Points and Fixture Color
  * Import Scene Objects
  * Import Trusses
  * Handle incomplete MVR files
* Fix issues due to empty material
* Enable camera selection
* Improve logging
* Fix Live DMX logic
* Ignore packets with dmxStartCode set
* Add support for migrations of older BlenderDMX file versions
* Process deeper GeometryReference trees

#### 1.0.0
* Add support for sACN protocol
* Fix receiving higher ArtNet universes
* Add import of fixtures from MVR
* Support multipixel devices and color control per geometry
* Show DMX Channel count in list of DMX Modes
* Add Live DMX - a table with current DMX values
* Add logging

