#!/usr/bin/env python3
"""open.py — the validity half of `shukuba-open`.

The model writes the station from the shukuba template; this file decides whether a station may
be opened, and whether the one written may land. Three commands:

    check    — the journey is in a state where a station can open; prints the active seed, the
               next unticked item on its route, and a parked station of that seed that already
               carries it.
    apply    — the station written outside the repository names that item and carries the
               template's three parts; writes it to the shukuba root and prints its path.
    take-up  — a parked station carries the item; moves it whole back to the root and prints
               the two paths the commit must declare.

Every refusal is printed and exits 1; nothing is written or moved on a refusal. The instance
root, the git runner and today's date are given, never derived, so the checks are testable at
their seams.

Stdlib only, plus `<CORE>/tools/journey_names.py`, which owns a station slug's characters and is
reached through this file's own path.
"""

from __future__ import annotations

import argparse
import datetime
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

# <root>/skills/pm/.claude/skills/shukuba-open/scripts/open.py → <root>/core/tools
sys.path.insert(0, str(Path(__file__).resolve().parents[6] / "core" / "tools"))
import journey_names  # noqa: E402

__version__ = "1.3.0"

Git = Callable[[Path, list[str]], str]
Today = Callable[[], datetime.date]

_SEEDBED_FIXTURES = {"README.md", "unpicked", "trail", "drop"}
_SHUKUBA_FIXTURES = {"README.md", "parked", "trail"}
_ITEM = re.compile(r"^[ \t]*- \[([ x])\][ \t]+(.*?)\s*$")
_SLUG = re.compile(rf"^`?({journey_names.SLUG})`?(?:\s+—\s+.*)?$")
_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
_PLACEHOLDER = re.compile(r"^<[^>]*>$", re.DOTALL)
_PARTS = ("What it is", "Reached when", "Guardrail")


class Refused(Exception):
    """A station that may not be opened, with the reason."""


@dataclass(frozen=True)
class Next:
    """The item a station opens from, and the parked station that already carries it, if any."""

    project: str
    seed: str
    number: int
    slug: str
    line: str
    parked: Path | None


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


def _seed_text(item: Path) -> str:
    return (item / "seed.md" if item.is_dir() else item).read_text(encoding="utf-8")


def _names(text: str, name: str) -> bool:
    """`name` appears whole — not as the front of a longer name."""
    return re.search(rf"(?<![\w-]){re.escape(name)}(?![\w-])", text) is not None


def journey(root: Path, project: str) -> Path:
    path = root / "system" / "projects" / project / "journey"
    if not (path / "shukuba").is_dir():
        raise Refused(f"no shukuba at {path / 'shukuba'}")
    return path


def _route(text: str) -> list[tuple[bool, str]]:
    """The items of the route — the section whose heading begins `## Stations`."""
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines) if line.startswith("## Stations")), None)
    if start is None:
        raise Refused("the active seed has no route section — stations-from-seed first")
    items = []
    for line in lines[start + 1:]:
        if line.startswith("## "):
            break
        match = _ITEM.match(line)
        if match:
            items.append((match.group(1) == "x", match.group(2)))
    return items


def _item_paragraph(lines: list[str]) -> str:
    start = next((i for i, line in enumerate(lines) if line.startswith("*Item ")), None)
    if start is None:
        return ""
    paragraph = []
    for line in lines[start:]:
        if not line.strip():
            break
        paragraph.append(line.strip())
    return " ".join(paragraph)


def _parked_for(folder: Path, slug: str, seed: str) -> list[Path]:
    """Parked stations under this slug that were opened from this seed. A slug names a station
    only within its seed, so a parked station of another seed is not this item's."""
    stem = re.compile(rf"^\d{{4}}-\d{{2}}-\d{{2}}_{re.escape(slug)}\.md$")
    return sorted(
        p for p in _visible(folder, set())
        if stem.match(p.name)
        and _names(_item_paragraph(p.read_text(encoding="utf-8").splitlines()), seed)
    )


def check(root: Path, project: str, git: Git) -> Next:
    """Refuse unless a station can open now; return the item it opens from."""
    j = journey(root, project)
    seeds = _visible(j / "nemawashi", _SEEDBED_FIXTURES)
    if not seeds:
        raise Refused("no seed is active — nemawashi-pick first")
    if len(seeds) > 1:
        raise Refused(f"more than one seed at the seedbed root: {', '.join(p.name for p in seeds)}")
    station = _visible(j / "shukuba", _SHUKUBA_FIXTURES)
    if station:
        raise Refused(f"a station is already open: {station[0].name}")
    unit = _visible(j / "tobiishi", {"trail", "drop"})
    if unit:
        raise Refused(f"a change unit is open: {unit[0].name}")

    seed = _seed_name(seeds[0])
    items = _route(_seed_text(seeds[0]))
    if not items:
        raise Refused("the route section lists no station — stations-from-seed first")
    unticked = [(n, line) for n, (ticked, line) in enumerate(items, 1) if not ticked]
    if not unticked:
        raise Refused("every item on the route is ticked — the seed's retire is owed to the Scrum Master (nemawashi-retire)")
    number, line = unticked[0]
    match = _SLUG.match(line)
    if not match:
        raise Refused(f"item {number} names no station slug — stations-from-seed first: {line}")
    slug = match.group(1)

    parked = _parked_for(j / "shukuba" / "parked", slug, seed)
    if len(parked) > 1:
        raise Refused(f"more than one parked station carries '{slug}': {', '.join(p.name for p in parked)}")
    # Only the journey an open writes. The instance's one checkout is shared by every project's
    # walk, so another project's edit in flight is not ours to refuse on.
    if git(root, ["status", "--porcelain", "--", str(j.relative_to(root))]).strip():
        raise Refused("the working tree is not clean")
    return Next(project, seed, number, slug, line, parked[0] if parked else None)


def _validate(station: str, nxt: Next) -> None:
    lines = station.splitlines()
    item = _item_paragraph(lines)
    if not re.match(rf"^\*Item {nxt.number} ", item):
        raise Refused(f"the station must open its Item line with item {nxt.number}")
    triple = f"{nxt.project} · nemawashi · {nxt.seed}"
    if not _names(item, triple):
        raise Refused(f"the Item line must name the seed as `{triple}`")
    if f"Slug: `{nxt.slug}`" not in item:
        raise Refused(f"the Item line must name the slug `{nxt.slug}`")
    for part in _PARTS:
        heads = [i for i, line in enumerate(lines) if line.strip() == f"## {part}"]
        if len(heads) != 1:
            raise Refused(f"the station must carry `## {part}` exactly once")
        body = []
        for line in lines[heads[0] + 1:]:
            if line.startswith("## "):
                break
            body.append(line)
        text = _COMMENT.sub("", "\n".join(body)).strip()
        if not text or _PLACEHOLDER.match(text):
            raise Refused(f"`## {part}` is empty or still the template's placeholder")


def apply(root: Path, project: str, station: str, git: Git, today: Today) -> Path:
    """Validate the written station, land it at the shukuba root, return its path."""
    nxt = check(root, project, git)
    if nxt.parked is not None:
        raise Refused(f"a parked station carries item {nxt.number}: {nxt.parked.name} — take it up")
    _validate(station, nxt)
    target = journey(root, project) / "shukuba" / f"{today().isoformat()}_{nxt.slug}.md"
    target.write_text(station if station.endswith("\n") else station + "\n", encoding="utf-8")
    return target.relative_to(root)


def take_up(root: Path, project: str, git: Git) -> tuple[Path, Path]:
    """Move the parked station for the next item back to the root, return (old, new)."""
    nxt = check(root, project, git)
    if nxt.parked is None:
        raise Refused(f"no parked station carries item {nxt.number} — write one")
    old = nxt.parked.relative_to(root)
    new = (nxt.parked.parent.parent / nxt.parked.name).relative_to(root)
    git(root, ["mv", str(old), str(new)])
    return old, new


def main(argv: list[str] | None = None, git: Git = run_git, today: Today = datetime.date.today) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--project", required=True)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check")
    apply_p = sub.add_parser("apply")
    apply_p.add_argument("--station", required=True, type=Path)
    sub.add_parser("take-up")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        if args.command == "check":
            nxt = check(root, args.project, git)
            print(f"Seed: {nxt.seed}\nItem: {nxt.number}\nSlug: {nxt.slug}\nLine: {nxt.line}")
            if nxt.parked is not None:
                print(f"Parked: {nxt.parked.relative_to(root)}")
        elif args.command == "apply":
            station = args.station.read_text(encoding="utf-8")
            print(apply(root, args.project, station, git, today))
        else:
            old, new = take_up(root, args.project, git)
            print(f"{old}\n{new}")
    except Refused as refusal:
        print(f"REFUSED: {refusal}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
