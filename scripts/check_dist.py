#!/usr/bin/env python3
# AUTO-GENERATED from scripts/check_dist.py by scripts/make_addon.py - DO NOT EDIT
"""Check built distributions before they are released.

    python scripts/check_dist.py DIST_DIR --name my-package --package my_package \
        --requires-python '>=3.7' [--min-version 6.2.0.dev0] [--expect-version 6.2.0] \
        [--sdist-allow 'src/*' ...]

Checks every wheel and sdist in DIST_DIR: project name, Requires-Python, version (at least
--min-version; exactly --expect-version, with no local part), wheel files limited to the
package and its own top-level <name>-<version>.dist-info, and - when --sdist-allow is given - sdist files limited to those
globs. Prints one "problem: ..." line per issue and exits 1 if there are any.
"""
import argparse
import fnmatch
import re
import sys
import tarfile
import zipfile
from email.parser import Parser
from pathlib import Path
from typing import List, NamedTuple, Optional, Sequence

from packaging.version import InvalidVersion, Version


class Options(NamedTuple):
    name: str
    package: str
    requires_python: str
    min_version: Optional[str]
    expect_version: Optional[str]
    sdist_allow: List[str]


def _normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "_", name).lower()


def _check_metadata(label: str, text: str, opts: Options) -> List[str]:
    meta = Parser().parsestr(text)
    problems = []
    if meta.get("Name") != opts.name:
        problems.append("{}: Name is {!r}, expected {!r}".format(label, meta.get("Name"), opts.name))
    if meta.get("Requires-Python") != opts.requires_python:
        problems.append("{}: Requires-Python is {!r}, expected {!r}".format(
            label, meta.get("Requires-Python"), opts.requires_python))
    raw_version = meta.get("Version")
    if raw_version is None:
        problems.append("{}: missing Version".format(label))
        return problems
    try:
        version = Version(raw_version)
    except InvalidVersion:
        problems.append("{}: invalid Version {!r}".format(label, raw_version))
        return problems
    if opts.min_version and version < Version(opts.min_version):
        problems.append("{}: version {} is below {}".format(label, version, opts.min_version))
    if opts.expect_version and (version != Version(opts.expect_version) or version.local):
        problems.append("{}: version {} is not exactly {}".format(label, version, opts.expect_version))
    return problems


def check_wheel(path: Path, opts: Options) -> List[str]:
    with zipfile.ZipFile(str(path)) as zf:
        names = zf.namelist()
        meta_names = [n for n in names
                      if n.endswith(".dist-info/METADATA") and n.count("/") == 1]
        if not meta_names:
            return ["{}: no top-level .dist-info/METADATA".format(path.name)]
        if len(meta_names) > 1:
            return ["{}: more than one top-level .dist-info/METADATA: {}".format(
                path.name, ", ".join(meta_names))]
        text = zf.read(meta_names[0]).decode("utf-8")
    problems = _check_metadata(path.name, text, opts)
    dist_info = meta_names[0].split("/", 1)[0]
    raw_version = Parser().parsestr(text).get("Version")
    try:
        version = Version(raw_version) if raw_version is not None else None
    except InvalidVersion:
        version = None
    if version is not None:
        accepted = {"{}-{}.dist-info".format(_normalize(opts.name), v)
                    for v in (raw_version, str(version))}
        if dist_info not in accepted:
            problems.append("{}: {} does not match {}-{}.dist-info".format(
                path.name, dist_info, _normalize(opts.name), version))
    for name in names:
        top = name.split("/", 1)[0]
        if top != opts.package and top != dist_info:
            problems.append("{}: unexpected file {}".format(path.name, name))
    return problems


def check_sdist(path: Path, opts: Options) -> List[str]:
    with tarfile.open(str(path), "r:gz") as tf:
        members = [m for m in tf.getmembers() if not m.isdir()]
        rel = {m.name: m.name.split("/", 1)[1] if "/" in m.name else m.name for m in members}
        pkg_info = [m for m in members if rel[m.name] == "PKG-INFO"]
        if not pkg_info:
            return ["{}: no PKG-INFO".format(path.name)]
        try:
            handle = tf.extractfile(pkg_info[0])
            if handle is None:
                raise ValueError("not a regular file")
            text = handle.read().decode("utf-8")
        except (KeyError, OSError, ValueError, tarfile.TarError):
            return ["{}: unreadable PKG-INFO".format(path.name)]
    problems = _check_metadata(path.name, text, opts)
    if opts.sdist_allow:
        for full, name in sorted(rel.items()):
            if not any(fnmatch.fnmatch(name, pattern) for pattern in opts.sdist_allow):
                problems.append("{}: file not allowed in sdist: {}".format(path.name, name))
    return problems


def main(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("dist_dir")
    parser.add_argument("--name", required=True)
    parser.add_argument("--package", required=True)
    parser.add_argument("--requires-python", required=True)
    parser.add_argument("--min-version")
    parser.add_argument("--expect-version")
    parser.add_argument("--sdist-allow", action="append", default=[])
    args = parser.parse_args(argv)
    opts = Options(args.name, args.package, args.requires_python,
                   args.min_version, args.expect_version, args.sdist_allow)
    dist = Path(args.dist_dir)
    wheels = sorted(dist.glob("*.whl"))
    sdists = sorted(dist.glob("*.tar.gz"))
    problems = []
    if not wheels:
        problems.append("no wheel in {}".format(dist))
    if not sdists:
        problems.append("no sdist in {}".format(dist))
    for w in wheels:
        problems += check_wheel(w, opts)
    for s in sdists:
        problems += check_sdist(s, opts)
    for p in problems:
        print("problem: " + p)
    if not problems:
        print("ok: {} wheel(s), {} sdist(s)".format(len(wheels), len(sdists)))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
