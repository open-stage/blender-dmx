from pathlib import Path
import hashlib
import requests
import re
import json
import sys
import os

failed = []


def canonicalize(name):
    return name.replace("_", "-").lower()


def md5_of_file(path, chunk_size=8192):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def version_from_wheel_filename(stem):
    m = re.match(r"^(.+)-([0-9][^-]*)-([^-]+)-([^-]+)-([^-]+)$", stem)
    return m.group(2) if m else None


with open("changed.txt") as f:
    files = [line.strip() for line in f if line.strip()]
for file in files:
    p = Path(file)
    directory = str(p.parent)
    filename = p.name
    stem = p.stem
    suffix = p.suffix
    if directory != "wheels" or suffix != ".whl":
        continue
    dist = p.stem.split("-", 1)[0]  # 'my_project'
    project = canonicalize(dist)  # 'my-project'
    if not p.exists():
        continue
    local_md5 = md5_of_file(Path(file))
    r = requests.get(f"https://pypi.org/pypi/{project}/json")
    r.raise_for_status()
    meta = r.json()
    releases = meta.get("releases", {})
    version = version_from_wheel_filename(stem)
    release = releases.get(version, None)
    remote_md5 = None
    result = False
    if release:
        asset = next((a for a in release if a.get("filename") == filename), None)
        if asset:
            remote_md5 = asset["digests"].get("md5", None)
    if remote_md5 is not None:
        result = remote_md5 == local_md5
    if result is False:
        failed.append(f"{filename}: Local hash: {local_md5}, Remote hash: {remote_md5}")
if failed:
    print("Local and remote hash do not match:\n", "\n".join(failed))
    sys.exit(1)  # non-zero -> CI fails
else:
    print("All checks passed")
    sys.exit(0)
