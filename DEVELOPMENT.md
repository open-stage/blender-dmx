## Development

### Formatting

Use `ruff` to format the code. Formatting code with Blender RNA structures can be problematic as short lines are typically better.

### Pre-commit-hooks

There is a configuration for [pre-commit](https://pre-commit.com/) which is not
enabled by default. You can run this manually by (ensure that `python -m pip
install pre-commit` is installed) running `pre-commit`. Note that it checks for
print statements. Print statements with "INFO" as first argument are skipped.
This runs on staged files.

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
