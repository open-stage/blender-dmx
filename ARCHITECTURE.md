## BlenderDMX Modules

- Each module is a PropertyGroup (the M of MVC) which extends a Controller (the C of MVC)
- Controller itself is composed by scoped controllers and it also declares it's UI components, the V in MVC
- The addon itself is a composition of all modules into a PropertyGroup

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
        - get collection using DMX_ModelBuilder.get(self.profile.filename, self.patch.mode)

#### core/builder/model_builder → DMX_ModelBuilder → get:

                - create pygdtf object
                - build gdtf fixture model using DMX_ModelBuilder(gdtf, mode_name).build()

#### core/builder/model_builder → DMX_ModelBuilder(gdtf, mode_name) → __init__, build:
                
                - create channel metadata (__init__)
                - create collection in data.collections (name is fixture + mode name, revision is in props)
                - build models → loads models from glb/3ds files
                - build trees
                - build targets, lights, cameras...
                - delete collection and delete model directory

    - build trees from model, relink constraints, add emitters, add floating name, build channels
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





