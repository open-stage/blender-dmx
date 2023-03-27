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
            print("Setting up language:", locale)
            lang = gettext.translation(
                "messages", localedir=localedir, languages=[locale]
            )
        except:
            lang = gettext.translation(
                "messages", localedir=localedir, languages=["en_US"]
            )  # fallback
            print(
                f"Setting language did not work, locale {locale} probably not created yet"
            )
        finally:
            DMX_Lang._ = lang.gettext


DMX_Lang.enable()
