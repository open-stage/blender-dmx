### Dependencies

As we must vendor some libraries in due to how Blender dependencies work, here
is a list of included libraries.

* python-gdtf: https://github.com/open-stage/python-gdtf
* python-mvr: https://github.com/open-stage/python-mvr
* sACN / E1.31 module: https://github.com/Hundemeier/sacn
* 3DS Importer: https://projects.blender.org/extensions/io_scene_3ds
* ifaddr: https://github.com/pydron/ifaddr
* oscpy: https://github.com/kivy/oscpy
* async_timeout: https://github.com/aio-libs/async-timeout/
* zeroconf: https://github.com/python-zeroconf/python-zeroconf
    - build non-optimized, non-platform specific wheel without cython: export SKIP_CYTHON=1; pip wheel --no-binary=zeroconf zeroconf
