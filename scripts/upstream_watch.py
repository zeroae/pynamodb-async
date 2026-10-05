#!/usr/bin/env python3
# AUTO-GENERATED from scripts/upstream_watch.py by scripts/make_addon.py - DO NOT EDIT
"""Check whether the latest official pynamodb release is inside the add-on's supported range.

    python scripts/upstream_watch.py --spec '>=6.1,<6.2'

Prints the latest version. Exit 0 when it is supported, 2 when it is outside the range (the
weekly workflow then opens an issue to port the change and widen the range), 1 on errors.
"""
import argparse
import json
import sys
from typing import Callable, Sequence
from urllib.request import urlopen

from packaging.specifiers import SpecifierSet
from packaging.version import Version

PYPI_URL = "https://pypi.org/pypi/pynamodb/json"


def is_supported(version: str, spec: str) -> bool:
    return Version(version) in SpecifierSet(spec)


def latest_release() -> str:
    with urlopen(PYPI_URL, timeout=30) as response:
        return json.load(response)["info"]["version"]


def main(argv: Sequence[str], latest: Callable[[], str] = latest_release) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--spec", required=True)
    args = parser.parse_args(argv)
    try:
        version = latest()
    except Exception as e:
        print("error: could not read the latest pynamodb release: {}".format(e), file=sys.stderr)
        return 1
    print(version)
    return 0 if is_supported(version, args.spec) else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
