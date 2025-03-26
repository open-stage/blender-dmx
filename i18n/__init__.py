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

import gettext
import os

import bpy


class DMX_Lang:
    _ = None

    @staticmethod
    def enable():
        locale = bpy.app.translations.locale
        gettext.gettext._translations = {}
        this_dir = os.path.dirname(os.path.abspath(__file__))
        localedir = os.path.join(this_dir, "translations")
        try:
            print("INFO", "Setting up language:", locale)
            lang = gettext.translation(
                "messages", localedir=localedir, languages=[locale]
            )
        except:
            lang = gettext.translation(
                "messages", localedir=localedir, languages=["en_US"]
            )  # fallback
            print(
                "INFO",
                f"Setting language did not work, locale {locale} probably not created yet",
            )
        finally:
            DMX_Lang._ = lang.gettext


DMX_Lang.enable()
