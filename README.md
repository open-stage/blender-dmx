# BlenderDMX
#### Blender addon to design and render DMX lighting.

*This project is in an early alpha stage. If you're willing to contribute, please check the issues.*

*This addon will always be free and open source, if you can donate and help me keep developing this and other tools I'd be really grateful. [![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](YOUR_EMAIL_CODE)*

#### INTRODUCTION

As a Lighting Designer I often find myself frustrated with the rendering results of the freely available DMX 3D visualisers. I mean, they are pretty good for designing the show, but once you need to take a screenshot to include in the final proposal that's going to the client, it's not as good as it could be.
[Blender](https://www.blender.org/) is a phenomenal open source 3D software that supports [Cycles](https://www.cycles-renderer.org/), an amazing (and also open source) photorealistic rendering engine.

This addon allows a smooth workflow for placing and programming DMX fixtures in Blender, so that you can take advantage of it's rendering power for professional screenshots.

#### INSTALL

While on early-alpha, this addon can only be installed manually. Fortunately, that should be pretty easy.

Just download the `dmx.py` file, then on Blender go to `Edit > Preferences > Add-ons > Install...` and select the file.
To enable the addon, search for "DMX" and toggle the checkbox on.

![Install](https://i.imgur.com/9w1QxzQ.gif)

#### USAGE

First make sure you're in Object Mode. Then, for some reason Blender won't show the toolbox until you actually create an object, so go ahead and make a plane.
A "DMX" tab should appear on the 3D View, where you can find the "Setup" toolbox. Click "Create Blank Show", and a "DMX" collection should appear on the scene inspector.

To add a fixture, go to the "Fixtures" toolbox and choose the fixture type (only Spots for now). After setting the fixture properties, click "OK" and it should appear on the 3D View.
You can move the fixture body around and use the target object to set it's direction.

Then, select the lights on the scene or the list and you can set their colors and intensity.

![Usage](https://i.imgur.com/egBnXSU.gif)

#### CONCEPT

Setting up stage scenes in Blender is quite painful, since each fixture must be composed by a Light Source, a 3D model of the fixture and a 3D model of the light surface, with an emissive color that should match the light color. All of that needs to stay aligned and be easily manipulated so that placing and tuning dozens of lights won't take way too long.
To solve this, the addon creates fixtures as Collections, which contains all of these components and a target object, to make tuning easy. Everything is constrained and only the body and the target are selectable, so there's no way you can mess with the alignments.

![Fixture](https://i.imgur.com/Zxo8K5E.gif)

Also, once everything is setup, changing colors of multiple lights would mean individually changing the color of each light source and light surface, and since you have to do it multiple times while programming, it's a very impractical method.

For that purpose, I've introduced the "Programmer" concept from most DMX systems. Once you select the fixtures (body or target, you can set their colors all at once with the color picker. Also, you can set the light intensity (dimmer).

A toolbox allows the creation of fixtures by type. All the fixtures are created inside the "DMX" collection.
This list also allows for easier selection of fixtures by name.

![Programmer](https://i.imgur.com/eWg3Cbk.gif)

#### WHAT'S NEXT?

The alpha version contains no real DMX features. The main focus is to create the DMX-like workflow inside Blender.
The foundation of fixtures and the programmer is there. Some features are missing such as the hability to edit a fixture settings, those should be solved soon.
The next step is adding more fixture types (Moving Fixtures, Tubular Fixtures, Panel Fixtures, etc) and improving their 3D model by importing instead of using primitives.
Also, it should include a "Groups" toolbox to allow easier selection of multiple fixtures.
The last feature to be implemented on the alpha version is the hability to save the DMX show within the Blender file and parse it back when loaded.

The beta version will mainly introduce Fixture Personalities and a "Channels" toolbox, so the 512 channels can be manually manipulated individually and modify the right parameters according to the fixture address.
Once this is done, the final beta step is the "ArtNet" toolbox, to allow the manipulation of such values by any DMX system.


