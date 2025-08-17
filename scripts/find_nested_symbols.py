#!/usr/bin/env python3

import argparse
import os
import sys
from pathlib import Path
import pymvr


def check_for_nested_symbols(mvr_file_path):
    """
    Parses an MVR file and checks if it contains nested symbols.
    A nested symbol is a Symdef that contains another Symbol instance.
    """
    try:
        mvr = pymvr.GeneralSceneDescription(str(mvr_file_path))
        if (
            not hasattr(mvr, "scene")
            or not mvr.scene
            or not hasattr(mvr.scene, "aux_data")
            or not mvr.scene.aux_data
        ):
            return False

        for symdef in mvr.scene.aux_data.symdefs:
            if hasattr(symdef, "symbol") and len(symdef.symbol) > 0:
                return True
    except Exception as e:
        print(f"Could not process file {mvr_file_path}: {e}", file=sys.stderr)
        return False
    return False


def main():
    """
    Main function to parse arguments and find MVR files with nested symbols.
    """
    parser = argparse.ArgumentParser(
        description="Find MVR files with nested symbols in a given directory."
    )
    parser.add_argument(
        "directory", type=str, help="The directory to search for .mvr files."
    )
    args = parser.parse_args()

    search_dir = Path(args.directory)

    if not search_dir.is_dir():
        print(f"Error: '{search_dir}' is not a valid directory.", file=sys.stderr)
        sys.exit(1)

    print(f"Searching for .mvr files in '{search_dir}'...")

    found_files = []
    for mvr_file in search_dir.rglob("*.mvr"):
        if check_for_nested_symbols(mvr_file):
            found_files.append(mvr_file)

    if found_files:
        print("\nFound MVR files with nested symbols:")
        for f in found_files:
            print(f"- {f}")
    else:
        print("\nNo MVR files with nested symbols were found.")


if __name__ == "__main__":
    main()
