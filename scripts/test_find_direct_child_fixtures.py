# Copyright (C) 2025 vanous
#
# This file is part of BlenderDMX.
#
# BlenderDMX is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# BlenderDMX is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <https://www.gnu.org/licenses/>.

from pathlib import Path
import pymvr
import sys


def find_child_fixtures_recursive(parent, skip=False):
    """Recursively search for fixtures that are children of other fixtures."""
    child_fixtures = []
    child_list = parent.child_list

    if not skip:
        for fixture in child_list.fixtures:
            child_fixtures.append(fixture)
            print("INFO", parent.__class__.__name__)
            if fixture.child_list:
                child_fixtures.extend(find_child_fixtures_recursive(fixture))

    for group in child_list.group_objects:
        if group.child_list:
            child_fixtures.extend(find_child_fixtures_recursive(group, skip=True))

    for scene_object in child_list.scene_objects:
        if scene_object.child_list:
            child_fixtures.extend(find_child_fixtures_recursive(scene_object))

    for truss in child_list.trusses:
        if truss.child_list:
            child_fixtures.extend(find_child_fixtures_recursive(truss))

    for support in child_list.supports:
        if support.child_list:
            child_fixtures.extend(find_child_fixtures_recursive(support))

    for video_screen in child_list.video_screens:
        if video_screen.child_list:
            child_fixtures.extend(find_child_fixtures_recursive(video_screen))

    for projector in child_list.projectors:
        if projector.child_list:
            child_fixtures.extend(find_child_fixtures_recursive(projector))

    return child_fixtures


def test_find_child_fixtures():
    """
    To run, use: uv run test_find_child_fixtures.py <path_to_mvr_or_dir>
    """
    file_path_str = sys.argv[1]

    if file_path_str is None:
        print(
            "INFO",
            "File path not provided. Specify a directory of MVR files or a single MVR file.",
        )

    path = Path(file_path_str)
    if path.is_file() and path.suffix.lower() == ".mvr":
        files = [path]
    elif path.is_dir():
        files = sorted(list(path.glob("**/*.mvr")))
    else:
        print(
            "INFO",
            f"Invalid path: {file_path_str}. Must be an MVR file or a directory.",
        )

    found_any = False
    for file in files:
        try:
            with pymvr.GeneralSceneDescription(file) as f:
                child_fixtures_found = []
                if f.scene and f.scene.layers:
                    for layer in f.scene.layers:
                        if layer.child_list:
                            child_fixtures_found.extend(
                                find_child_fixtures_recursive(layer, skip=True)
                            )

                if child_fixtures_found:
                    print(
                        "INFO",
                        f"Found fixtures that are children of other objects in {file}: {len(child_fixtures_found)}:",
                    )
                    found_any = True

        except Exception as e:
            print("INFO", f"Could not process file {file}: {e}")

    if not found_any:
        print("INFO", "No MVR files with child fixtures found in the specified path.")


if __name__ == "__main__":
    if len(sys.argv):
        test_find_child_fixtures()
