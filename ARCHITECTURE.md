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
        - get collection using DMX_GDTF_ModelBuilder.get(self.profile.filename, self.patch.mode)

#### core/builder/gdtf_builder → DMX_GDTF_ModelBuilder → get:

                - create pygdtf object
                - build gdtf fixture model using DMX_GDTF_ModelBuilder(gdtf, mode_name).build()

#### core/builder/gdtf_builder → DMX_GDTF_ModelBuilder(gdtf, mode_name) → __init__, build:
                
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







