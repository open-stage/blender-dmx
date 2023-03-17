# BlenderDMX

Architecture:

- Each module is a PropertyGroup (the M of MVC) which extends a Controller (the C of MVC)
- Controller itself is composed by scoped controllers and it also declares it's UI components, the V in MVC
- The addon itself is a composition of all modules into a PropertyGroup
