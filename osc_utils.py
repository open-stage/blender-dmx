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

import json
import os

from .logging import DMX_Log
from .osc import DMX_OSC


class DMX_OSC_Templates:
    """This class is persisting the template data, the data
    is re-read each time OSC is enabled to allow refresh"""

    instance = None
    data = None

    def __init__(self):
        super(DMX_OSC_Templates, self).__init__()

    @staticmethod
    def read(template_name="default.json"):
        if DMX_OSC_Templates.instance is None:
            DMX_OSC_Templates.instance = DMX_OSC_Templates()

        DMX_Log.log.debug("reading data")
        ADDON_PATH = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(
            ADDON_PATH, "assets", "osc_templates", template_name
        )

        with open(template_path, "r") as f:
            _data = json.loads(f.read())
        DMX_OSC_Templates.data = _data
        return DMX_OSC_Templates.data


class DMX_OSC_Handlers:
    """Only grouping class, centralizing all OSC handlers into single place.
    Method arguments are then variables for the template"""

    @staticmethod
    def fixture_selection(fixture):
        if DMX_OSC_Templates.data is not None:
            template = DMX_OSC_Templates.data
            fixture_selection = template["fixture_selection"]
            for fix_sel in fixture_selection:
                DMX_OSC.send(
                    fix_sel["key"].format(fixture=fixture),
                    fix_sel["value"].format(fixture=fixture),
                )

    @staticmethod
    def fixture_clear():
        if DMX_OSC_Templates.data is not None:
            temp = DMX_OSC_Templates.data
            fixture_clear = temp["fixture_clear"]
            for f_cl in fixture_clear:
                DMX_OSC.send(f_cl["key"], f_cl["value"])
