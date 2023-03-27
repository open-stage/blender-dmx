pybabel extract -F babel.cfg -o messages.pot ../ # extract strings to messages.pot (for weblate, crowdin...)
pybabel init -i messages.pot -d translations -l po_BR # run only once, will erase existing translation!
pybabel update -i messages.pot -d translations # update all languages
pybabel compile -d translations # make translations usable for app/addon


