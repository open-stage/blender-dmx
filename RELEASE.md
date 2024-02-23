* Update translations, commit and give some time for translations to be done

cd i18n/
pybabel extract -F babel.cfg -o messages.pot ../

* Checkout a new branch `release_v_X.Y.Z`
* Add changes to CHANGELOG.md
* Update versions (in text and in links) in README.md
* Update __init__.py → bl_info → version
* Check that ./assets/* doesn't include extra GDTF files or folders
* Generate a release:
 * (ensure to have pygit) python -m pip install pygit2
 * Edit scripts/build_release.py
   * branch_name = "release_v1.0.2"
   * if you added new directories, make sure to add them
   * python scripts/build_release.py
   * test the release
* Draft a release, attach the zip file
* Make PR, add details, merge
* Pull latest main
* git tag v1.0.2
* git push origin v1.0.2
* Edit release on GH, make public


