Modules
- Each module is a PropertyGroup (the M of MVC) which extends a Controller (the C of MVC)
- Controller itself is composed by scoped controllers and it also declares it's UI components, the V in MVC
- The addon itself is a composition of all modules into a PropertyGroup


Parsing upon "Build fixtures":

Create patch data → populates data in dmx.patch.fixtures
Build:
- run build in core controller, core/controller/__init__: 
    - creates new collection (dmx) if not exists
    - activates this collection to hold all data
    - run build in dmx builder, core/builder/__init__:
        - runs checks in DMX_Builder (in constructor)
        - deletes removed fixtures - clears them from dmx.core.fixtures
        - loops through fixtures in dmx.patch.fixtures and rebuilds them using dmxfixturebuilder.build, core/builder/fixture_builder:
        - create a new DMX_Fixture inside DMX.fixtures:
        - creates new collection and add it to the scene
        - create model collection via load model, core/builder/gdtf_builder:
            - create pygdtf object (gdtf_builder)
            - build gdtf fixture model, core/builder/gdtf_builder: 
                - create collection in data.collections (name is fixture + mode name, revision is in props)
                - models, trees, targets..
                - delete collection and delete model directory
            - build trees from model, relink constraints, add emitters, add floating name, build channels, (fixture builder)
            - restore positions if exist
            - annotate channels per geometry
            - render







