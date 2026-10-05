#!/usr/bin/env python3
# AUTO-GENERATED from scripts/release_notes.py by scripts/make_addon.py - DO NOT EDIT
"""Print the release-notes section for a version from an .rst file.

    python scripts/release_notes.py docs/release_notes.rst 6.2.0 [--output notes.md]

A section starts at a title line ``v<version>`` underlined with a single repeated character
(``-``, ``=``, ``~`` or ``^``) and runs until the next underlined title. Exits 1 if the
section is missing or empty, so a release cannot go out without notes.
"""
import argparse
import sys
from pathlib import Path
from typing import List, Optional, Sequence

_UNDERLINE_CHARS = "-=~^"


def _is_underline(line: str) -> bool:
    s = line.strip()
    return len(s) >= 3 and len(set(s)) == 1 and s[0] in _UNDERLINE_CHARS


def _is_title(lines: List[str], i: int) -> bool:
    return (i + 1 < len(lines) and bool(lines[i].strip())
            and not _is_underline(lines[i]) and _is_underline(lines[i + 1]))


def extract(text: str, version: str) -> Optional[str]:
    lines = text.splitlines()
    title = "v" + version
    start = None
    for i in range(len(lines)):
        if lines[i].strip() == title and _is_title(lines, i):
            start = i + 2
            break
    if start is None:
        return None
    end = len(lines)
    for j in range(start, len(lines)):
        if _is_title(lines, j):
            end = j
            break
    body = "\n".join(lines[start:end]).strip()
    return body or None


def main(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("rst_file")
    parser.add_argument("version")
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    body = extract(Path(args.rst_file).read_text(encoding="utf-8"), args.version)
    if body is None:
        print("no non-empty 'v{}' section in {}".format(args.version, args.rst_file), file=sys.stderr)
        return 1
    if args.output:
        Path(args.output).write_text(body + "\n", encoding="utf-8")
    else:
        print(body)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
