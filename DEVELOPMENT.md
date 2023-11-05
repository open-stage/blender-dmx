## Development

### Formatting

Use `ruff` to format the code.

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
DMX_LOG.log.debug("Logging debug message here, level 20")
DMX_LOG.log.info("Logging info message here, level 10")
```
