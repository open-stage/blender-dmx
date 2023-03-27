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
