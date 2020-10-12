# BlenderDMX
#### Blender addon to design and render DMX lighting.

*This addon will always be free and open source, if you can donate and help me keep developing this and other tools I'd be really grateful. [![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/donate/?cmd=_s-xclick&hosted_button_id=ZC6UQ8TKWZVZU)*

*This project is in alpha stage. If you're willing to contribute, please check the issues.*

#### INTRODUCTION

Most commercial DMX 3D visualisers are focused on real-time rendering, so they can be used as a tool for designing the show's presets and animations.
However, when it comes to final render quality, it's hard to achieve true photorealistic results.
[Blender](https://www.blender.org/) is a phenomenal open source 3D software that supports both real time and photorealistic rendering, and this addon makes it easier to create and control common DMX fixtures.

#### INSTALL

While on alpha, this addon can only be installed manually.
Download the repository and place the whole folder on your [Blender Addons Directory](https://docs.blender.org/manual/en/latest/advanced/blender_directory_layout.html).

To enable the addon, go to `Edit > Preferences > Add-ons`, search for "DMX" and toggle the checkbox on.

![Install](https://i.imgur.com/Q1R0AzP.gif)

#### USAGE

First make sure you're on the 3D View and in Object Mode. Then, make sure you have an object in scene.
A "DMX" tab should appear on the right, and clicking it you can find the "Setup" toolbox. If it doesn't, select the object. (I'm looking for ways to fix this)
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

The alpha version contains no real DMX features. The main focus is to create the DMX-like workflow inside Blender.
After a final check, I'll upload the 0.1.0 alpha version to a repository and reach out for contributors and donations.

The beta version will mainly introduce Fixture Profiles and a "Channels" toolbox, so the 512 channels can be manually manipulated individually and modify the right parameters according to the fixture address.

Once this is done, the final step towards the first release version is the "ArtNet" panel, to allow the manipulation of such values by any DMX system.
