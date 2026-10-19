#!/usr/bin/env python3
"""pin_host_changed.py — has the host a pin was made from changed since the pin was made?

WHAT "CHANGED" MEANS

A pin's source host has changed when its `core/`, `.claude/` or `skills/` tree differs from the
pin's own copy of that tree. An edit still uncommitted counts, because a pin is a copy of the
working tree as it stood and not of a commit. A file the host's git ignore rules match is never
considered, on either side: pinned runs write `__pycache__/` into a pin, and an ignored file was
never copied.
The host's journey, its product files and everything else outside the three trees are not
considered at all, so a commit that touches only those does not make the pin stale. Where the
host is not a git work tree there are no ignore rules to apply, so every file under the three
trees is considered on both sides.

"Differ" means one of three things: a file on one side only, a content difference, or a difference
in the executable bits. `pin.host_files` is the host side, the very listing `pin.make` copies from,
so what this file compares and what a pin holds cannot drift apart.

WHY THIS EXISTS

A `build-idea` start is the one launch that begins a long unattended chain. Started inside a pin
that predates the owner's latest edits, it would run the whole chain on a tree the owner has already
changed. `pin_run.sh`'s `pin_enter_renewing` asks this file first, and takes a new pin of the host
when the answer is `changed`.

THE CLI

    python3 -B core/tools/pin_host_changed.py --pin <pin root>

prints exactly two lines and exits 0: `verdict=<changed|unchanged|host-gone>` and `host=<source
host root>`. Any non-zero exit means the comparison itself failed, the reason on stderr. It writes
nothing, and `-B` keeps it from writing bytecode into the pin, whose `core/tools/` it imports from
— a bytecode file there would change the pin in force.
"""

from __future__ import annotations

import argparse
import filecmp
import stat
import subprocess
import sys
from enum import Enum
from pathlib import Path

import pin

__version__ = "1.0.0"

_EXECUTE_BITS = 0o111


class HostComparisonError(Exception):
    """The comparison itself could not be made — `git` failed on a host that exists. The entry
    point turns it into a message on stderr and a non-zero exit."""


class Verdict(str, Enum):
    """The three answers. The value is what the CLI prints."""

    CHANGED = "changed"
    UNCHANGED = "unchanged"
    HOST_GONE = "host-gone"


def _ignored_by_host(host_root: Path, relpaths: list[str]) -> set[str]:
    """The subset of `relpaths` the host's git ignore rules match. `git check-ignore` exits 1
    when nothing matched, which is an answer and not a failure."""
    if not relpaths:
        return set()
    result = subprocess.run(
        ["git", "-C", str(host_root), "check-ignore", "--stdin", "-z"],
        input="\0".join(relpaths) + "\0",
        capture_output=True,
        text=True,
    )
    if result.returncode not in (0, 1):
        raise HostComparisonError(
            f"git check-ignore failed in {host_root}: {result.stderr.strip()}"
        )
    return {relpath for relpath in result.stdout.split("\0") if relpath}


def _same_file(host_file: Path, pinned_file: Path) -> bool:
    """Equal when both sides are one file on disk, or agree in size and executable bits and bytes.
    Symlinks are followed on both sides, as `pin.make`'s copy follows them."""
    if host_file.samefile(pinned_file):
        return True
    host_stat = host_file.stat()
    pinned_stat = pinned_file.stat()
    if host_stat.st_size != pinned_stat.st_size:
        return False
    if (stat.S_IMODE(host_stat.st_mode) & _EXECUTE_BITS) != (
        stat.S_IMODE(pinned_stat.st_mode) & _EXECUTE_BITS
    ):
        return False
    return filecmp.cmp(host_file, pinned_file, shallow=False)


def compare(source_pin: pin.Pin) -> Verdict:
    """Whether `source_pin`'s source host differs from the pin across the three trees. Writes
    nothing."""
    host_root = source_pin.source_host_root
    if not host_root.is_dir():
        return Verdict.HOST_GONE

    # A path the listing still names but the working tree no longer holds is absent from the host
    # side, exactly as `pin.make` skips it when the copy finds it gone.
    host_side = {relpath for relpath in pin.host_files(host_root) if (host_root / relpath).exists()}
    pin_side = set(pin.tree_files(source_pin.root))
    pin_only = pin_side - host_side

    if host_side - pin_side:
        return Verdict.CHANGED
    if pin.is_git_work_tree(host_root):
        pin_only -= _ignored_by_host(host_root, sorted(pin_only))
    if pin_only:
        return Verdict.CHANGED

    for relpath in sorted(host_side):
        if not _same_file(host_root / relpath, source_pin.root / relpath):
            return Verdict.CHANGED
    return Verdict.UNCHANGED


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Say whether a pin's source host has changed since the pin was made."
    )
    parser.add_argument("--pin", required=True, type=Path, help="the pin's root directory")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    try:
        source_pin = pin.of_core(args.pin / "core")
        if source_pin is None:
            print(f"pin_host_changed: {args.pin} is not a pin — no pin.json", file=sys.stderr)
            return 2
        verdict = compare(source_pin)
    except (HostComparisonError, OSError, ValueError, KeyError) as exc:
        print(f"pin_host_changed: {exc}", file=sys.stderr)
        return 2
    print(f"verdict={verdict.value}")
    print(f"host={source_pin.source_host_root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
