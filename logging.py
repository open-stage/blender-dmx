import logging


class DMX_LOG:
    log = None

    def __init__(self):
        super(DMX_LOG, self).__init__()

    @staticmethod
    def enable(level):
        # DMX_LOG._instance = DMX_LOG()
        log = logging.getLogger("blenderDMX")
        log.setLevel(level)

        # file log
        # log_handler = logging.FileHandler(filename="blenderDMX.log", encoding="utf-8", mode="a")
        # log_handler.setFormatter(
        #    logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
        # )

        # console log
        log_formatter = logging.Formatter(
            fmt="%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s %(lineno)d: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        log_handler2 = logging.StreamHandler()
        log_handler2.setFormatter(log_formatter)
        # log.addHandler(log_handler)
        log.addHandler(log_handler2)
        DMX_LOG.log = log
