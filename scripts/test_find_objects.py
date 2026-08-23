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


def find_child_fixtures_recursive(parent):
    """Recursively search for fixtures that are children of other fixtures."""
    found_objects = []
    child_list = parent.child_list

    for item in child_list.fixtures:
        found_objects.append(item.__class__.__name__)
        if item.child_list:
            found_objects.extend(find_child_fixtures_recursive(item))

    for item in child_list.group_objects:
        found_objects.append(item.__class__.__name__)
        if item.child_list:
            found_objects.extend(find_child_fixtures_recursive(item))

    for item in child_list.scene_objects:
        found_objects.append(item.__class__.__name__)
        if item.child_list:
            found_objects.extend(find_child_fixtures_recursive(item))

    for item in child_list.trusses:
        found_objects.append(item.__class__.__name__)
        if item.child_list:
            found_objects.extend(find_child_fixtures_recursive(item))

    for item in child_list.supports:
        found_objects.append(item.__class__.__name__)
        if item.child_list:
            found_objects.extend(find_child_fixtures_recursive(item))

    for item in child_list.video_screens:
        found_objects.append(item.__class__.__name__)
        if item.child_list:
            found_objects.extend(find_child_fixtures_recursive(item))

    for item in child_list.projectors:
        found_objects.append(item.__class__.__name__)
        if item.child_list:
            found_objects.extend(find_child_fixtures_recursive(item))

    return found_objects


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

    for file in files:
        try:
            with pymvr.GeneralSceneDescription(file) as f:
                objects_found = []
                if f.scene and f.scene.layers:
                    for layer in f.scene.layers:
                        if layer.child_list:
                            objects_found.extend(find_child_fixtures_recursive(layer))

            print(file, set(objects_found))

        except Exception as e:
            print("INFO", f"Could not process file {file}: {e}")


if __name__ == "__main__":
    if len(sys.argv):
        test_find_child_fixtures()
