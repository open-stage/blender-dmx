#    Copyright vanous
#
#    This file is part of BlenderDMX.
#
#    BlenderDMX is free software: you can redistribute it and/or modify it
#    under the terms of the GNU General Public License as published by the Free
#    Software Foundation, either version 3 of the License, or (at your option)
#    any later version.
#
#    BlenderDMX is distributed in the hope that it will be useful, but WITHOUT
#    ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
#    FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
#    more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program. If not, see <https://www.gnu.org/licenses/>.


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
        class CustomStreamHandler(logging.StreamHandler):
            def emit(self, record):
                super().emit(record)
                # self.stream.write("\n")
                # this allow us to add a break between log lines, to make long logs more readable
                self.flush()

        # console log
        log_formatter = logging.Formatter(
            fmt="%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s %(lineno)d: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        if not log.handlers:  # logger is global, prevent duplicate registrations
            dmx = bpy.context.scene.dmx
            ADDON_PATH = dmx.get_addon_path()
            path = os.path.join(ADDON_PATH, "blenderDMX.log")

            console_log_handler = CustomStreamHandler()
            console_log_handler.setFormatter(log_formatter)
            file_log_handler = RotatingFileHandler(
                path, backupCount=5, maxBytes=8000000, encoding="utf-8", mode="a"
            )
            file_log_handler.setFormatter(log_formatter)
            log.addHandler(file_log_handler)
            log.addHandler(console_log_handler)
        DMX_Log.log = log
        DMX_Log.update_filters()

    @staticmethod
    def set_level(level):
        DMX_Log.log.critical(f"Update logging level to {level}")
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
                if any(
                    [x in record.filename for x in ["data", "artnet", "acn", "logging"]]
                ):
                    return True

            if DMX_Log.logging_filter_mvr_xchange:
                if any(
                    [
                        x in record.pathname
                        for x in [
                            "mdns",
                            "mvr_xchange",
                            "mvrx_protocol",
                            "mvrxchange",
                            "logging",
                        ]
                    ]
                ):
                    return True

            if DMX_Log.logging_filter_fixture:
                if any([x in record.filename for x in ["gdtf", "fixture"]]):
                    return True

            return not (
                DMX_Log.logging_filter_dmx_in
                or DMX_Log.logging_filter_mvr_xchange
                or DMX_Log.logging_filter_fixture
            )

        log.addFilter(custom_filter)
