#!/bin/sh
#
#
pybabel extract -F babel.cfg --no-location -o messages.pot ../
pybabel update -i messages.pot -d translations
# pybabel compile -d translations # DO NOT RUN, creates binary merge weblate conflicts
