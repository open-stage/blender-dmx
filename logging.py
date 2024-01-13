import logging
from logging.handlers import RotatingFileHandler

import bpy
import os


class DMX_Log:
    def __init__(self):
        super(DMX_Log, self).__init__()
        self.log = None

        dmx = bpy.context.window_manager.dmx
        self.logging_filter_dmx_in = dmx.logging_filter_dmx_in
        self.logging_filter_mvr_xchange = dmx.logging_filter_mvr_xchange
        self.logging_filter_fixture = dmx.logging_filter_fixture

    @staticmethod
    def enable(level):
        log = logging.getLogger("blenderDMX")
        log.setLevel(level)

        # file log

        # console log
        log_formatter = logging.Formatter(
            fmt="%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s %(lineno)d: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        if not log.handlers:  # logger is global, prevent duplicate registrations
            ADDON_PATH = os.path.dirname(os.path.abspath(__file__))
            path = os.path.join(ADDON_PATH, "blenderDMX.log")

            console_log_handler = logging.StreamHandler()
            console_log_handler.setFormatter(log_formatter)
            file_log_handler = RotatingFileHandler(path, backupCount=5, maxBytes=5000000, encoding="utf-8", mode="a")
            file_log_handler.setFormatter(log_formatter)
            log.addHandler(file_log_handler)
            log.addHandler(console_log_handler)
        DMX_Log.log = log
        DMX_Log.update_filters()

    @staticmethod
    def set_level(level):
        DMX_Log.log.critical(f"Update logging level {level}")
        DMX_Log.log.setLevel(level)

    @staticmethod
    def update_filters():
        DMX_Log.log.debug("Update logging filters")
        dmx = bpy.context.window_manager.dmx
        log = DMX_Log.log
        # cache these:
        DMX_Log.logging_filter_dmx_in = dmx.logging_filter_dmx_in
        DMX_Log.logging_filter_mvr_xchange = dmx.logging_filter_mvr_xchange
        DMX_Log.logging_filter_fixture = dmx.logging_filter_fixture
        for filter in log.filters:
            log.filters.remove(filter)

        def custom_filter(record):
            if DMX_Log.logging_filter_dmx_in:
                if any([x in record.filename for x in ["data", "artnet", "acn", "logging"]]):
                    return True

            if DMX_Log.logging_filter_mvr_xchange:
                if any([x in record.pathname for x in ["mdns", "mvr_xchange", "mvrx_protocol", "mvrxchange", "logging"]]):
                    return True

            if DMX_Log.logging_filter_fixture:
                if any([x in record.filename for x in ["gdtf", "fixture"]]):
                    return True

            return not (DMX_Log.logging_filter_dmx_in or DMX_Log.logging_filter_mvr_xchange or DMX_Log.logging_filter_fixture)

        log.addFilter(custom_filter)

        # not needed, leaving just in case
        # def mvx_filter(record):
        #    print("rec", record.filename)
        #    if any([x in record.filename for x in ["mdns", "mvr_xchange"]]):
        #        return True
        #    return False

        # def dmx_filter(record):
        #    if any([x in record.filename for x in ["data", "artnet", "acn"]]):
        #        return True
        #    return False

        # def debug_filter(record):
        #    print(record)
        #    return True

        # log.addFilter(debug_filter)

        # if dmx.logging_filter_mvr_xchange:
        #    log.addFilter(mvrx_filter)
        #    print("adding mvr filter")

        # if dmx.logging_filter_dmx_in:
        #    log.addFilter(dmx_filter)
        #    print("adding dmx filter")
