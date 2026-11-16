#!/usr/bin/env python3
"""skill_path.py — the one resolver: a skill name in, its directory out, under either layout.

A kensaiapp instance holds a skill's files at one of two roots: the flat layout,
`<instance root>/.claude/skills/<name>`, or the grouped layout,
`<instance root>/skills/<group>/.claude/skills/<name>`, for some `<group>` — see
`core/doctrine/setup/kensaiapp_structure.md` for what a group is and when one exists. Every
tools-owned caller that needs a skill's directory from its name goes through
`resolve_skill_dir`, so the answer agrees with the harness (which always indexes the flat path
first) and so a skill moving from flat to grouped does not leave a caller quietly resolving
nothing.

Two inputs, always: the instance root (passed in by the caller — never derived from this
module's own location, the same posture `written_forward.py` and `watch_agent.py` hold) and a
skill name. One output: the skill's absolute directory, wrapped in a `Resolution` so the three
outcomes — found, not found, ambiguous — are never conflated. Flat wins whenever the flat
directory exists, with one exception: a flat entry that is itself a link into the same name's
grouped directory under the same root answers as that group, so the host's flat links into its
own groups change no answer. A flat link to anywhere else answers flat. Otherwise exactly one
grouped match resolves, zero is not-found, and two or more is ambiguous (and never guesses). A name containing `/` or starting with `.` is a path, not
a name, and is refused as `invalid_name` — never a not-found.

`resolve_skill_dir` never raises, on any input.

Never canonicalizes a returned path — only `os.path.abspath`, which normalizes and joins with the
cwd but does not follow a symlink to its target; never the stdlib calls that do (`os.path` and
`pathlib` each carry one). A satellite's `.claude/skills` may be a directory symlink into its
host — every consumer carried one until every host skill was grouped, and
`core/tools/link_satellite.py` leaves such a link in place; following it to its target would
silently hand back the host's directory for a satellite's skill. The resolver finds a
skill *through* a symlink (existence checks follow symlinks, which `os.path.isdir` does by
default) without canonicalizing the answer.

Stdlib only, like every other tool in this folder.
"""

from __future__ import annotations

import argparse
import glob
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

__version__ = "1.1.0"

FOUND = "found"
NOT_FOUND = "not_found"
AMBIGUOUS = "ambiguous"
INVALID_NAME = "invalid_name"

EXIT_OK = 0
EXIT_NOT_FOUND = 3
EXIT_AMBIGUOUS = 4


@dataclass(frozen=True)
class Resolution:
    """The result of resolving a skill name to a directory. `path` is set only when `status` is
    `FOUND`; `matches` holds every grouped candidate considered, populated (2+, sorted) only when
    `status` is `AMBIGUOUS`."""

    status: str
    path: Path | None = None
    matches: tuple[Path, ...] = field(default_factory=tuple)


def _is_invalid_name(name: str) -> bool:
    """A name containing '/' or starting with '.' is a path, not a name — refused the way
    `core/launchers/cold-read/launcher.sh` already refuses one for its own skill argument. An
    empty name is refused too — it names nothing."""
    if not name:
        return True
    if "/" in name or "\\" in name:
        return True
    if name.startswith("."):
        return True
    return False


def _grouped_candidates(root_abs: str, name: str) -> list[Path]:
    """Every grouped directory for `name` under `root_abs`, sorted. Only the group segment is a
    wildcard. The root and the name are literals the caller handed in, so both are escaped — an
    unescaped name holding a glob metacharacter would match some *other* skill's directory (the
    flat branch, being an `isdir` check, already answers such a name literally), and an
    unescaped root would fail to find a skill under a directory legitimately named `inst[1]`."""
    pattern = os.path.join(
        glob.escape(root_abs), "skills", "*", ".claude", "skills", glob.escape(name)
    )
    return sorted(Path(p) for p in glob.glob(pattern) if os.path.isdir(p))


def _group_the_flat_link_points_at(flat: str, candidates: list[Path]) -> Path | None:
    """The grouped candidate a flat entry is a link to, or `None`. Only the flat entry itself
    being a link counts: a root whose whole `.claude/skills` is a link has a real entry in it,
    and that entry keeps its flat answer. Both sides are compared by real path; the returned
    path is the candidate as the caller's root spells it."""
    if not os.path.islink(flat):
        return None
    target = os.path.realpath(flat)
    for candidate in candidates:
        if os.path.realpath(candidate) == target:
            return candidate
    return None


def resolve_skill_dir(root: str | os.PathLike, name: str) -> Resolution:
    """Resolve `name` to its directory under `root` — flat first, except that a flat link into
    the same name's grouped directory answers as that group, then the single grouped match.
    Never raises."""
    if _is_invalid_name(name):
        return Resolution(status=INVALID_NAME)

    try:
        root_abs = os.path.abspath(os.fspath(root))

        flat = os.path.join(root_abs, ".claude", "skills", name)
        candidates = _grouped_candidates(root_abs, name)
        if os.path.isdir(flat):
            group = _group_the_flat_link_points_at(flat, candidates)
            return Resolution(status=FOUND, path=group if group is not None else Path(flat))
    except OSError:
        return Resolution(status=NOT_FOUND)

    if len(candidates) == 1:
        return Resolution(status=FOUND, path=candidates[0])
    if len(candidates) == 0:
        return Resolution(status=NOT_FOUND)
    return Resolution(status=AMBIGUOUS, matches=tuple(candidates))


def instance_root(skill_dir: str | os.PathLike) -> Path:
    """The inverse of `resolve_skill_dir`: given a skill's directory, the instance root it
    belongs to — recognising both layouts. A directory is read as grouped when its four parents
    spell `skills/<group>/.claude/skills`; otherwise it is read as flat and the root is three
    levels up (today's `coldread/manifest.py:_derive_root` behaviour, unchanged). Path
    arithmetic only — no filesystem probing, and no canonicalization, so a satellite's
    symlinked layer keeps the caller's own root rather than resolving to the host's. Never
    raises."""
    p = Path(os.path.abspath(os.fspath(skill_dir)))
    parents = p.parents

    # Grouped shape: <root>/skills/<group>/.claude/skills/<name>
    #   parents[0] = <root>/skills/<group>/.claude/skills
    #   parents[1] = <root>/skills/<group>/.claude
    #   parents[2] = <root>/skills/<group>
    #   parents[3] = <root>/skills
    #   parents[4] = <root>
    if (
        len(parents) >= 5
        and parents[0].name == "skills"
        and parents[1].name == ".claude"
        and parents[3].name == "skills"
    ):
        return parents[4]

    # Flat shape (or anything else): three levels up — today's unconditional behaviour.
    if len(parents) >= 3:
        return parents[2]
    return parents[-1] if parents else p


# --- command-line form -------------------------------------------------------------------------
# The surface the bash launchers branch on. 0 prints the directory; 3 is not-found; 4 is
# ambiguous, every match on stderr. 2 is left to argparse's own usage error — the name argument's
# shape is validated by a `type=` callable, so a refused name *is* that usage error rather than a
# fourth invented code.


def _name_arg(value: str) -> str:
    """argparse `type=` validator for the positional name — refuses a path-shaped value by
    raising `ArgumentTypeError`, which argparse turns into its own usage error (exit 2)."""
    if _is_invalid_name(value):
        raise argparse.ArgumentTypeError(
            f"{value!r} is a skill name, not a path — it must not contain '/' and must not "
            f"start with '.'"
        )
    return value


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Resolve a skill name to its directory under either instance layout."
    )
    parser.add_argument("name", type=_name_arg, help="the skill name to resolve")
    parser.add_argument("--root", default=None, help="instance root (default: the cwd)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = args.root if args.root is not None else os.getcwd()
    result = resolve_skill_dir(root, args.name)

    if result.status == FOUND:
        print(result.path)
        return EXIT_OK

    if result.status == NOT_FOUND:
        print(f"skill_path: no skill named {args.name!r} found under {root}", file=sys.stderr)
        return EXIT_NOT_FOUND

    # AMBIGUOUS — the name argument's own type= validator already refused an INVALID_NAME
    # before resolve_skill_dir was ever called, so this is the only remaining status.
    print(f"skill_path: {args.name!r} is ambiguous under {root} — matches:", file=sys.stderr)
    for match in result.matches:
        print(match, file=sys.stderr)
    return EXIT_AMBIGUOUS


if __name__ == "__main__":
    sys.exit(main())
