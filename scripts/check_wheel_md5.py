#!/usr/bin/env python3
import asyncio
from pathlib import Path
import hashlib
import re
import json
import sys
import os
from concurrent.futures import ThreadPoolExecutor
import aiohttp

# config
CHANGED_TXT = Path("changed.txt")
MAX_CONCURRENT_HTTP = 10
MAX_WORKERS = 4  # for file hashing


def canonicalize(name):
    return name.replace("_", "-").lower()


def version_from_wheel_filename(stem):
    m = re.match(r"^(.+)-([0-9][^-]*)-([^-]+)-([^-]+)-([^-]+)$", stem)
    return m.group(2) if m else None


def md5_of_file_sync(path, chunk_size=8192):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


async def md5_of_file(path, loop, executor):
    return await loop.run_in_executor(executor, md5_of_file_sync, path)


async def fetch_pypi_json(session, project):
    url = f"https://pypi.org/pypi/{project}/json"
    async with session.get(url, timeout=30) as r:
        r.raise_for_status()
        return await r.json()


async def check_wheel(session, loop, executor, file):
    p = Path(file)
    directory = str(p.parent)
    filename = p.name
    stem = p.stem
    suffix = p.suffix
    if directory != "wheels" or suffix != ".whl":
        return None

    dist = stem.split("-", 1)[0]
    project = canonicalize(dist)

    # fetch metadata
    try:
        meta = await fetch_pypi_json(session, project)
    except aiohttp.ClientResponseError as e:
        return {"file": filename, "reason": "pypi-request-failed", "detail": str(e)}
    except Exception as e:
        return {"file": filename, "reason": "pypi-request-failed", "detail": str(e)}

    local_path = Path(file)
    if not local_path.is_file():
        return {"file": filename, "reason": f"local-file-missing: {local_path}"}

    try:
        local_md5 = await md5_of_file(local_path, loop, executor)
    except Exception as e:
        return {"file": filename, "reason": "md5-read-failed", "detail": str(e)}

    releases = meta.get("releases", {})
    version = version_from_wheel_filename(stem)
    published_md5 = None
    if version:
        release = releases.get(version)
        if release:
            asset = next((a for a in release if a.get("filename") == filename), None)
            if asset:
                published_md5 = asset.get("digests", {}).get("md5") or asset.get(
                    "md5_digest"
                )

    # fallback: search all releases
    if published_md5 is None:
        for ver, assets in releases.items():
            for asset in assets:
                if asset.get("filename") == filename:
                    published_md5 = asset.get("digests", {}).get("md5") or asset.get(
                        "md5_digest"
                    )
                    version = ver
                    break
            if published_md5 is not None:
                break

    if published_md5 is None:
        return {"file": filename, "reason": "not-found-on-pypi", "version": version}

    if published_md5 != local_md5:
        return {
            "file": filename,
            "reason": "md5-mismatch",
            "local": local_md5,
            "pypi": published_md5,
            "version": version,
        }

    return None


async def main():
    if not CHANGED_TXT.exists():
        print(f"{CHANGED_TXT} not found", file=sys.stderr)
        sys.exit(2)

    with CHANGED_TXT.open() as f:
        files = [line.strip() for line in f if line.strip()]

    candidates = [
        f
        for f in files
        if Path(f).parent.as_posix() == "wheels" and Path(f).suffix == ".whl"
    ]
    if not candidates:
        print("No wheel files to check.")
        return 0

    loop = asyncio.get_event_loop()
    executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

    connector = aiohttp.TCPConnector(limit=MAX_CONCURRENT_HTTP)
    timeout = aiohttp.ClientTimeout(total=60)
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        tasks = [
            asyncio.create_task(check_wheel(session, loop, executor, f))
            for f in candidates
        ]
        results = []
        for coro in asyncio.as_completed(tasks):
            res = await coro
            if res:
                results.append(res)

    if results:
        print("Failed items:", json.dumps(results, indent=2))
        if os.environ.get("GITHUB_ACTIONS") == "true":
            out_path = os.environ.get("GITHUB_OUTPUT")
            if out_path:
                with open(out_path, "a") as out:
                    out.write("failed_items<<EOF\n")
                    out.write(json.dumps(results))
                    out.write("\nEOF\n")
        else:
            with open("failed_items.json", "w") as f:
                json.dump(results, f, indent=2)
        return 1

    print("All checks passed")
    return 0


if __name__ == "__main__":
    code = asyncio.run(main())
    sys.exit(code)
