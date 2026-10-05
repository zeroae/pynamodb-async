#!/usr/bin/env python3
# AUTO-GENERATED from scripts/release_notes.py by scripts/make_addon.py - DO NOT EDIT
"""Print the release-notes section for a version from an .rst file.

    python scripts/release_notes.py docs/release_notes.rst 6.2.0 [--unwrap] [--output notes.md]

A section starts at a title line ``v<version>`` underlined with a single repeated character
(``-``, ``=``, ``~`` or ``^``) and runs until the next underlined title. Exits 1 if the
section is missing or empty, so a release cannot go out without notes.

``--unwrap`` joins the wrapped lines of each paragraph and list item into one line. GitHub
Release bodies turn every newline into a line break, so hard-wrapped text would break
mid-sentence there.
"""
import argparse
import re
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


_BLOCK_START = re.compile(r"^\s*(?:[*+\-\u2022]\s|(?:\d+|#)[.)]\s|\.\.\s|\|\s|:\w[^:]*:\s)")


def unwrap(body: str) -> str:
    """Join wrapped continuation lines inside paragraphs and list items.

    Blank lines, list-item starts (including indented sub-items), directives and
    literal blocks (after a paragraph ending in ``::``) are left as they are.
    """
    out: List[str] = []
    literal_base: Optional[int] = None  # indent of the paragraph that introduced a literal block
    in_literal = False
    for line in body.splitlines():
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())
        if not stripped:
            if out and out[-1] and not in_literal and out[-1].rstrip().endswith("::"):
                literal_base = len(out[-1]) - len(out[-1].lstrip())
                in_literal = True
            out.append("")
            continue
        if in_literal:
            assert literal_base is not None
            if indent > literal_base:
                out.append(line.rstrip())
                continue
            in_literal = False
            literal_base = None
        previous = out[-1] if out else ""
        joinable = (
            bool(previous)
            and not _BLOCK_START.match(line)
            and not _is_underline(line)
            and not _is_underline(previous)
            and not previous.lstrip().startswith(".. ")
        )
        if joinable:
            out[-1] = previous.rstrip() + " " + stripped
        else:
            out.append(line.rstrip())
    return "\n".join(out)


def main(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("rst_file")
    parser.add_argument("version")
    parser.add_argument("--output")
    parser.add_argument("--unwrap", action="store_true",
                        help="join wrapped lines of paragraphs and list items (for GitHub Release bodies)")
    args = parser.parse_args(argv)
    body = extract(Path(args.rst_file).read_text(encoding="utf-8"), args.version)
    if body is None:
        print("no non-empty 'v{}' section in {}".format(args.version, args.rst_file), file=sys.stderr)
        return 1
    if args.unwrap:
        body = unwrap(body)
    if args.output:
        Path(args.output).write_text(body + "\n", encoding="utf-8")
    else:
        print(body)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
