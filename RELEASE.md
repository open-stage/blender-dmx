* Update translations, commit and give some time for translations to be done
* To prevent weblate merge conflicts, in weblate:
* Push translations, merge them fast in GitHub, then reset weblate to upstream

* Add changes to CHANGELOG.md
* update blender_manifest.toml
* update pyproject.toml
* Check that ./assets/* doesn't include extra GDTF files or folders
* Make sure that all used libraries are available via pypi.org

git clean -xdf .

* Generate a release for Extension website:

blender --command extension build

# Updating libraries, for example pygdtf

This will download the latest wheel locally:

python -m pip wheel pygdtf

* Tag and push

git tag vX.Y.Z
git push vX.Y.Z

On Github, create a release, add description and include the build zip
artifact.  On BlenderDMX.eu site, you must push some change, for example
release news blog post, but anything else is fine too, so the api/repo is
re-generated and pulls the Github releases.
