# Development Guide

Hi! It's good to have you here.
This document is an attempt to guide contributors at understanding and working on the add-on. Have fun!

## Architecture

The add-on is a modular system, where modules are composited into the `DMX` object and expose useful methods.

The modules follow a variation of the MVC (Model-View-Controller) architecture, with a "fat controller".

- module
    - **data**: the "model" layer, where data structures are defined. such structs have no functional methods, only getters.
    - **ui**: the "view" layer, responsible for defining how the UI looks like, and which operators are available. operators are slim, and should not implement logic inside them. instead, they should use the controller layer
    - **controller**: a fat controller, built by composing scoped controllers into a class

Each module is packed into a struct, such as `DMX_Patch`, which packs the data structure and controller into a dynamic object.

After composed into the `DMX` class, such method can be accessed through the context, like `bpy.context.scene.dmx.core.render()`.

### Core Module

The core module has two extra sub-modules:

- `builder`: Builds dynamic fixture objects from GDTF profiles
- `engine`: Handles DMX data and fixture rendering

## GDTF Parsing principles:

- do not presume that plain layout of DMX Channels in a DMX Mode is defining
  the DMX footprint of the device. Geometry references are (frequently) used to
  re-use parts of the device. This means that a channel(s) defined once can be
  multiplied, over several times duplicated geometry (tree).

- do not use geometry names for anything related to function of the geometry
  (yoke, pan, tilt, head), use attached GDTF attributes ("Pan", "Tilt")

- only Beam or Camera geometry types are currently used special types of
  geometry. Other types (Axis...) are not really relevant as even Normal
  geometry can have for example "Pan" GDTF attribute attached, to indicate
  movement.

## Fixture building and parsing in BlenderDMX

### Patching 

    - creates patch data → populates data in dmx.patch.fixtures

### Building fixtures

### core/controller/__init__ → DMX_Core_Controller → build_patch:

    - creates new collection (dmx) if not exists
    - activates this collection to hold all data
    - run DMX_SceneBuilder().build()

### core/builder/__init__ → DMX_SceneBuilder → __init__, build:

    - runs checks in DMX_Builder (__init__)
    - deletes removed fixtures - clears them from dmx.core.fixtures
    - loops through fixtures in dmx.patch.fixtures and rebuilds them using DMX_FixtureBuilder(fixture_patch).build()

### core/builder/fixture_builder → DMX_FixtureBuilder(fixture_patch) → build:

    - create a new DMX_Fixture inside DMX.fixtures:
    - creates new collection and add it to the scene
    - create model collection via _load_model:
        - get collection using DMX_GDTF_ModelBuilder.get(self.profile.filename, self.patch.mode)

#### core/builder/gdtf_builder → DMX_GDTF_ModelBuilder → get:

                - create pygdtf object
                - build gdtf fixture model using DMX_GDTF_ModelBuilder(gdtf, mode_name).build()

#### core/builder/gdtf_builder → DMX_GDTF_ModelBuilder(gdtf, mode_name) → __init__, build:
                
                - create channel metadata (__init__)
                - create collection in data.collections (name is fixture + mode name, revision is in props)
                - build models → loads models from glb/3ds files
                - build blender object trees
                - build targets, lights, cameras...
                - delete collection and delete model directory

    - build object trees from model collection, relink constraints, add emitters, add floating name, build channels
    - restore positions if exist or from mvr
    - annotate channels per geometry
    - render



## Rendering

Each fixture first root is annotated with the "renderables metadata".
It looks like this:

```
{
  'Dimmer': {
    'geoms': [<Object1>, <Object2>],
    'coords': [[[1,0,0,0,0]],[[1,8,0,0,0]]]
  },
  'ColorAdd': {
    'geoms': [<Object1>, <Object2>],
    'coords': [[[1,1,0,0,0],[1,2,0,0,0],[1,3,0,0,0],[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0]],[[1,9,0,0,0],[1,10,0,0,0],[1,11,0,0,0],[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0]]]
  }
}
```

The `coords` values follow the structure defined at `const.Functions`.

Each coordinate is composed of (resolution, coarse, fine, ultra, uber). All addresses are absolute on the buffer.
The render method reads the data for each valid coordinate (resolution > 0), then zips it with the geom, so each render method receives the following for each fixture:

```
# render_dimmer(data)
data = [
  (<Object1>, [1.0]),
  (<Object2>, [1.0])
]
# render_color(data)
data = [
  (<Object1>, [1.0,1.0,1.0,None,None,None]),
  (<Object2>, [1.0,1.0,1.0,None,None,None])
]
```










## Logging

Use [predefined python logging module](https://docs.python.org/3/library/logging.html?highlight=logging#module-logging) instead of print. If not imported yet, import it into your class:

```python
from dmx.logging import DMX_LOG
```

Then use it. Choose appropriate level. Default level is `Error`, which means `Error` and `Critical` messages will be displayed. Following logging levels are available:

```python
DMX_LOG.log.critical("Logging critical message here, level 50")
DMX_LOG.log.error("Logging error message here, level 40")
DMX_LOG.log.warning("Logging warning message here, level 30")
DMX_LOG.log.debug("Logging debug message here, level 20")
DMX_LOG.log.info("Logging info message here, level 10")
```
