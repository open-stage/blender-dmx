* Update translations, commit and give some time for translations to be done
* To prevent weblate merge conflicts, in weblate:
* Push translations, merge them fast in GitHub, then reset weblate to upstream

* Add changes to CHANGELOG.md
* update blender_manifest.toml
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
