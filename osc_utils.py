import bpy
import json
import os

from .osc import DMX_OSC
from .logging import DMX_Log


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
        template_path = os.path.join(ADDON_PATH, "assets", "osc_templates", template_name)

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
                DMX_OSC.send(fix_sel["key"].format(fixture=fixture), fix_sel["value"].format(fixture=fixture))

    @staticmethod
    def fixture_clear():
        if DMX_OSC_Templates.data is not None:
            temp = DMX_OSC_Templates.data
            fixture_clear = temp["fixture_clear"]
            for f_cl in fixture_clear:
                DMX_OSC.send(f_cl["key"], f_cl["value"])
