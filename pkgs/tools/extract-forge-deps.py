#!/usr/bin/env python3

"""Forge library dependency extractor.

This extracts the list of dependencies needed by the forge minecraft
mod loader. Typically this is done through an installer provided by
them, which then downloads all these dependencies at run time.

This is very impure, and therefore not really packageable for nix.

Note that this does not download forge itself. This is distributed
with the installer, and keeping with the upstream's wishes, will not
be automatically downloaded.
"""

import argparse
import itertools
import json
import os
import re
from pathlib import Path
from typing import Dict, Iterator, List, NamedTuple
from zipfile import ZipFile


def main():
    """Entrypoint."""
    parser = argparse.ArgumentParser()
    parser.add_argument("installer", type=Path)
    parser.add_argument("output", type=argparse.FileType("w"))
    args = parser.parse_args()

    json.dump(encode_libs(get_version_libs(args.installer)), args.output)


class Library(NamedTuple):
    """A representation of the data needed to download a library."""

    path: str
    sha1: str
    url: str


# This matches recent versions of the forge jars. Not tested on older
# versions (<= 1.16, much older versions have a separate -server jar,
# which will need to be handled completely differently anyway).
IS_FORGE = re.compile(r"forge-(\d+.)+\d+(-universal)?.jar")


def encode_libs(libs: Iterator[Library]) -> List[Dict]:
    """Encode an iterator of libraries as something `json.dumps` can deal with.

    Unfortunately NamedTuple rejects implementing any other base
    classes, so JSONEncoder can't be used.

    """
    return [
        {"path": lib.path, "sha1": lib.sha1, "url": lib.url}
        for lib in libs
        # Forge itself isn't downloaded, but distributed with the
        # installer, so it has an empty url
        if not re.match(IS_FORGE, os.path.basename(lib.path))
    ]


def get_version_libs(installer: Path) -> Iterator[Library]:
    """Get the library download handles from the installer."""
    with ZipFile(installer) as z:
        profile = json.load(z.open("install_profile.json"))
        version = json.load(z.open(profile["json"].lstrip("/")))
    return itertools.chain(get_libraries(profile), get_libraries(version))


def get_libraries(version: Dict) -> Iterator[Library]:
    """Extract a list of libraries as listed in a forge version json."""
    yield from (
        Library(path=lib["path"], sha1=lib["sha1"], url=lib["url"])
        for lib in (lib["downloads"]["artifact"] for lib in version["libraries"])
    )


if __name__ == "__main__":
    main()
