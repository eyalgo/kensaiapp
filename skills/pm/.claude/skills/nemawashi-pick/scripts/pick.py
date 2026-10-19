#!/usr/bin/env python3
"""pick.py — the validity half of `nemawashi-pick`.

The model chooses the seed (`prompts/thin.md`); this file decides whether that choice may be
made. Two commands:

    check  — the journey is in a state where a pick can happen at all; prints the pool.
    apply  — the selection record names one seed that may be picked; moves it to the root,
             appends it to the instance's PPM context (`record_in_ppm_context`), and prints
             the paths the commit must declare — the context's third, or a skip line when
             the instance has no such context.

Every refusal is printed and exits 1; nothing is moved on a refusal. The instance root and
the git runner are given, never derived, so the checks are testable at their seams.

Stdlib only.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Callable

__version__ = "1.3.0"

Git = Callable[[Path, list[str]], str]

_SEEDBED_FIXTURES = {"README.md", "unpicked", "trail", "drop"}
_SEED_LINE = re.compile(r"^Seed:\s*(.+?)\s*$", re.MULTILINE)
_CONDITION_LINE = re.compile(r"^Condition:\s*(.+?)\s*$", re.MULTILINE)
_TICKED = re.compile(r"^[ \t]*- \[x\]", re.MULTILINE)
_UNTICKED = re.compile(r"^[ \t]*- \[ \]", re.MULTILINE)
PPM_CONTEXT = Path("system") / "contexts" / "CONTEXT_PPM.md"
PICKED_HEADING = "## Picked seeds"


class Refused(Exception):
    """A pick that may not be made, with the reason."""


def run_git(root: Path, args: list[str]) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args], check=True, capture_output=True, text=True
    ).stdout


def _visible(folder: Path, fixtures: set[str]) -> list[Path]:
    if not folder.is_dir():
        return []
    return sorted(
        p for p in folder.iterdir() if not p.name.startswith(".") and p.name not in fixtures
    )


def _seed_name(item: Path) -> str:
    return item.name[:-3] if item.name.endswith(".md") else item.name


def journey(root: Path, project: str) -> Path:
    path = root / "system" / "projects" / project / "journey"
    if not (path / "nemawashi").is_dir():
        raise Refused(f"no seedbed at {path / 'nemawashi'}")
    return path


def check(root: Path, project: str, git: Git) -> list[str]:
    """Refuse unless a pick can happen now; return the pool's seed names."""
    j = journey(root, project)
    active = _visible(j / "nemawashi", _SEEDBED_FIXTURES)
    if active:
        raise Refused(f"a seed is already active: {active[0].name} — un-pick it first")
    station = _visible(j / "shukuba", {"README.md", "parked", "trail"})
    if station:
        raise Refused(f"a station is open with no active seed: {station[0].name}")
    unit = _visible(j / "tobiishi", {"trail", "drop"})
    if unit:
        raise Refused(f"a change unit is open: {unit[0].name}")
    pool = [_seed_name(p) for p in _visible(j / "nemawashi" / "unpicked", {"README.md"})]
    if not pool:
        raise Refused("the pool is empty — a cut is owed by the Principal PM")
    # Only the paths a pick writes: this project's journey and the PPM context. The instance's one
    # checkout is shared by every project's walk, so another project's edit in flight is not ours.
    own = [str(j.relative_to(root)), str(PPM_CONTEXT)]
    if git(root, ["status", "--porcelain", "--", *own]).strip():
        raise Refused("the working tree is not clean")
    return pool


def _resolve(unpicked: Path, name: str) -> Path:
    matches = [p for p in (unpicked / f"{name}.md", unpicked / name) if p.exists()]
    if len(matches) != 1:
        raise Refused(f"'{name}' is not exactly one seed in unpicked/")
    return matches[0]


def _seed_text(item: Path) -> str:
    return (item / "seed.md" if item.is_dir() else item).read_text(encoding="utf-8")


def apply(root: Path, project: str, record: str, git: Git) -> tuple[Path, Path]:
    """Validate the record, move the one seed to the root, return (old, new)."""
    check(root, project, git)
    seeds = _SEED_LINE.findall(record)
    if len(seeds) != 1:
        raise Refused(f"the record must name exactly one seed, found {len(seeds)}")
    name = _seed_name(Path(seeds[0].strip("`")))
    conditions = _CONDITION_LINE.findall(record)
    if len(conditions) != 1:
        raise Refused("the record must carry exactly one Condition: line")
    if conditions[0].strip().lower() != "none":
        raise Refused(f"the record states a condition that prevents starting: {conditions[0]}")

    nema = journey(root, project) / "nemawashi"
    item = _resolve(nema / "unpicked", name)
    for bin_ in ("trail", "drop"):
        if (nema / bin_ / item.name).exists():
            raise Refused(f"'{name}' is also in {bin_}/")
    text = _seed_text(item)
    if _TICKED.search(text) and not _UNTICKED.search(text):
        raise Refused(f"'{name}' is fully walked — it is a retire, not a pick")

    old = item.relative_to(root)
    new = (nema / item.name).relative_to(root)
    git(root, ["mv", str(old), str(new)])
    return old, new


def record_in_ppm_context(root: Path, project: str, seed: str, today: date) -> Path | None:
    """Append the pick to the PPM context's `## Picked seeds`; None when there is no such section.

    Several projects hold a picked seed at once, so a pick only appends — no other line is read or
    changed. The move that takes the seed off its root takes the line out.
    """
    path = root / PPM_CONTEXT
    if not path.is_file():
        return None
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    heading = next((i for i, line in enumerate(lines) if line.rstrip() == PICKED_HEADING), None)
    if heading is None:
        return None
    end = next((i for i in range(heading + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    last = max((i for i in range(heading + 1, end) if lines[i].strip()), default=heading)
    if not lines[last].endswith("\n"):
        lines[last] += "\n"
    entry = f"- `{project} · nemawashi · {seed}` — picked {today.isoformat()}\n"
    lines[last + 1:last + 1] = ["\n", entry] if last == heading else [entry]
    path.write_text("".join(lines), encoding="utf-8")
    return path.relative_to(root)


def main(argv: list[str] | None = None, git: Git = run_git, today: date | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--project", required=True)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check")
    apply_p = sub.add_parser("apply")
    apply_p.add_argument("--record", required=True, type=Path)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        if args.command == "check":
            print("\n".join(check(root, args.project, git)))
        else:
            old, new = apply(root, args.project, args.record.read_text(encoding="utf-8"), git)
            context = record_in_ppm_context(
                root, args.project, _seed_name(new), today or date.today()
            )
            print(f"{old}\n{new}\n{context or 'no PPM context — skipped'}")
    except Refused as refusal:
        print(f"REFUSED: {refusal}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
