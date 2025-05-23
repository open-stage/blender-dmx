## Development

### Formatting

Use `ruff` to format the code, ideally by setting it up in your editor.
Formatting code with Blender RNA structures can be problematic as short lines
are typically better, so using \fmt: off , \#fmt: on can disable the formatter
for a block of code.

You can install ruff, isort, pip... by first installing
[uv](https://docs.astral.sh/uv/), then run `uv init` in this directory. Then
you can use for example ruff by running `uv run ruff format`.

### Pre-commit-hooks

There is a configuration for [pre-commit](https://pre-commit.com/). You can run
this manually by (ensure that `python -m pip install pre-commit` is installed)
running `pre-commit`. Note that it checks for print statements. Print
statements with "INFO" as first argument are skipped.  This runs on staged
files.

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
DMX_LOG.log.info("Logging info message here, level 20")
DMX_LOG.log.debug("Logging debug message here, level 10")
```

### Code Attribution

Add/update code license headers with  [hawkeye](https://github.com/korandoru/hawkeye):
 - `hawkeye format`

### Local development

Since the Extension store, developing locally is a bit harder but still
possible, with the git folder being the source of the data for Blender:

* Build or download the extension file
* Install the Extension from the local file
* Go to local user folder, for example this on linux:
  ./config/blender/4.4/extensions/user\_default, there will be a folder
  open\_stage\_blender\_dmx. Remove this folder and make a symlink of your
  local git folder to open\_stage\_blender\_dmx.
