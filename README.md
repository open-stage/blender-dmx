# BlenderDMX
#### Blender addon to design DMX lighting.

*Click on the image below to watch the video!*

[![v0.2.5 video](https://img.youtube.com/vi/_Nh3hbscjJo/0.jpg)](https://www.youtube.com/watch?v=_Nh3hbscjJo)

*This addon will always be free and open source, if you can donate and help me keep developing this and other tools I'd be really grateful. [![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/donate?hosted_button_id=ZC6UQ8TKWZVZU)*

#### INTRODUCTION

Most commercial DMX 3D visualisers are focused on real-time rendering, so they can be used as a tool for designing the show's presets and animations.
However, when it comes to final render quality, it's hard to achieve true photorealistic results.
[Blender](https://www.blender.org/) is a phenomenal open source 3D software that supports both real time and photorealistic rendering, and this addon makes it easier to create and control common DMX fixtures.

#### INSTALL

1. Make sure you have installed [Blender 2.9](https://www.blender.org/download/) or higher;
2. Download the addon `.zip` file:
   * *Stable*: download the [latest release](https://github.com/hugoaboud/BlenderDMX/releases/tag/v0.2.5-alpha)
   * *Unstable*: download the zipped repository
3. Open Blender
4. `Edit > Preferences > Add-ons > Install`
5. Pick the addon `.zip` file

To enable the addon, go to `Edit > Preferences > Add-ons`, search for "DMX" and toggle the checkbox on.

![Install](https://i.imgur.com/Q1R0AzP.gif)

#### USAGE

First make sure you're on the 3D View and in Object Mode. Then, make sure you have an object in scene.
A "DMX" tab should appear on the right, and clicking it you can find the "Setup" toolbox. If it doesn't, select the object. (I'm looking for ways to improve this)
Click "Create Blank Show", and a "DMX" collection should appear on the scene inspector.

To add a fixture, go to the "Fixtures" toolbox and choose the fixture class. After setting the fixture properties, click "OK" and it should appear on the 3D View.
You can move the fixture body around and use the target object to set it's direction.

![Usage](https://i.imgur.com/VKgbTfD.gif)

Then, select the lights on the scene or the list and you can set their colors and intensity.
You can create and use groups for selecting multiple fixtures at once.

![Usage2](https://i.imgur.com/GhZnynf.gif)

The `DMX > Setup` panel allows setting the background color and creating a Volume Scatter box around the whole scene.
You can either use Eevee or Cycles.

![Usage3](https://i.imgur.com/SArYtIN.gif)


#### WHAT'S NEXT?

The alpha version offers no real DMX features. The main focus is to create the workflow of DMX softwares inside Blender.
A few features such as Pan/Tilt are missing, also a performance review is needed in order to optimize some parts of the code (mainly the DMX messaging system).

The beta version will mainly introduce Fixture Profiles, a "Channels" toolbox (so the 512 channels can be manually manipulated individually) and a Scene recorder.

Once this is done, the final step towards the vanilla release is the "ArtNet" panel, to allow the manipulation of such values by any ArtNet system.

Please feel free to make suggestions on the Issues section and to pull improvements to the code.
