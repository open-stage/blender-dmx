### Changelog

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

