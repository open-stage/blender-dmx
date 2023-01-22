<p align="center">
  <img src="https://i.ibb.co/Wn9wkH1/banner.png" />
</p>

# BlenderDMX

A DMX visualization tool inside `Blender`, designed to offer a free, easy and fully packed solution for Lighting Designers.

![](https://i.ibb.co/rvpKYxB/render-eevee-7.png)

## Download & Install

First of all, make sure you have installed [Blender 3.0](https://www.blender.org/download/) or higher;
Then, download the `zip` file:

- **LATEST RELEASE (STABLE): v0.5.0 Beta**

   1. Download the [latest release](https://github.com/hugoaboud/BlenderDMX/releases/tag/v0.5.0-beta) `dmx.zip` file

- **ROLLING RELEASE (UNSTABLE)**

   1. Download the [repository ZIP](https://github.com/hugoaboud/BlenderDMX/archive/main.zip) `BlenderDMX-main.zip` file
   2. Unzip it
   3. Rename the folder `BlenderDMX-main` inside it to `dmx`
   4. Zip it back, so you have: `dmx.zip/dmx/<contents>`

Finally:
   1. Open Blender
   2. `Edit > Preferences > Add-ons > Install`
   3. Pick the addon `zip` file

To enable the addon, go to `Edit > Preferences > Add-ons`, search for "DMX" and toggle the checkbox on.

![Install](https://i.imgur.com/Q1R0AzP.gif)

## How to Use

For details on how to use the Addon, check our [Wiki](https://github.com/hugoaboud/BlenderDMX/wiki).

Check the demonstration video:
[demonstration video](https://www.youtube.com/watch?v=uzZQhcqSjS4)

We also have a `Discord` server for sharing knowledge: [discord server link](https://discord.gg/FQVVyc45T9)

## Donate

*This addon will always be free and open source, if you can donate and help me keep developing tools for artists I'd be really grateful.*
- [![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/donate/?hosted_button_id=K2DRRKRFE583J)
- Bitcon (BTC only): 1BApp5s16pEPk5oECtJJ7G8iYmbj7r2YrG

## Development

### Logging

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




