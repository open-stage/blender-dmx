### Changelog

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

