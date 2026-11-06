#!/usr/bin/env python3
"""open.py — the validity half of `shukuba-open`.

The model writes the station from the shukuba template; this file decides whether a station may
be opened, and whether the one written may land. Three commands:

    check    — the journey is in a state where a station can open, and, when the product the
               project's card names has a `docs/SDD.md`, the SDD's companion
               `docs/SDD_open_issues.md` holds no open Raised from downstream item tracked by the
               active seed; prints the active seed, the next unticked item on its route, and a
               parked station of that seed that already carries it.
    apply    — the station written outside the repository names that item and carries the
               template's three parts; writes it to the shukuba root and prints its path.
    take-up  — a parked station carries the item; moves it whole back to the root and prints
               the two paths the commit must declare.

Every refusal is printed and exits 1; nothing is written or moved on a refusal. The instance
root, the git runner and today's date are given, never derived, so the checks are testable at
their seams.

Stdlib only, plus `<CORE>/tools/journey_names.py`, which owns a station slug's characters, and
`<CORE>/tools/development_path.py`, which owns how a project card's `Product path:` line is read.
Both are reached through this file's own path.
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
import development_path  # noqa: E402
import journey_names  # noqa: E402

__version__ = "1.4.0"

Git = Callable[[Path, list[str]], str]
Today = Callable[[], datetime.date]

_SEEDBED_FIXTURES = {"README.md", "unpicked", "trail", "drop"}
_SHUKUBA_FIXTURES = {"README.md", "parked", "trail"}
_ITEM = re.compile(r"^[ \t]*- \[([ x])\][ \t]+(.*?)\s*$")
_SLUG = re.compile(rf"^`?({journey_names.SLUG})`?(?:\s+—\s+.*)?$")
_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
_PLACEHOLDER = re.compile(r"^<[^>]*>$", re.DOTALL)
_PARTS = ("What it is", "Reached when", "Guardrail")
_RAISED_SECTION = "Raised from downstream"
_TRACKED_BY = "**Tracked by:**"


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


class Files:
    """The product's records as `hold` reads them — the one place the hold touches a file."""

    def read_text(self, path: Path) -> str | None:
        """The file's text, or `None` when no readable file is there."""
        try:
            return path.read_text(encoding="utf-8")
        except OSError:
            return None

    def is_file(self, path: Path) -> bool:
        return path.is_file()


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
    """Refuse unless the journey lets a station open now; return the item it opens from.

    It answers the journey alone. Whether the SDD's companion holds the seed back is `hold()`'s."""
    j = journey(root, project)
    seeds = _visible(j / "nemawashi", _SEEDBED_FIXTURES)
    if not seeds:
        raise Refused("no seed is active — seed-pick first")
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


def _sdd_docs(root: Path, project: str, *, files: Files, home: str) -> Path | None:
    """The `docs/` folder of the product the project's card names, when it holds a `docs/SDD.md`.
    No card, no `Product path:` the parser accepts, or no SDD there, name no product."""
    card = files.read_text(root / "system" / "projects" / project / "project.md")
    if card is None:
        return None
    try:
        _, value = development_path.parse_product_path(card, home)
    except development_path.ToolError:
        return None
    docs = root / value / "docs"
    return docs if files.is_file(docs / "SDD.md") else None


def _tracked_by(item: list[str], triple: str) -> bool:
    """The item's `**Tracked by:**` value names `triple` whole, and is not a `<…>` placeholder."""
    for line in item:
        if _TRACKED_BY not in line:
            continue
        value = line.split(_TRACKED_BY, 1)[1].strip()
        if not (value.startswith("<") and value.endswith(">")) and _names(value, triple):
            return True
    return False


def _open_items(companion: str, triple: str) -> list[str]:
    """The `### ` headings, in file order, of the items in the companion's Raised from downstream
    section that `triple` tracks. Only text outside HTML comments is read."""
    lines = _COMMENT.sub("", companion).splitlines()
    start = next((i for i, line in enumerate(lines)
                  if line.startswith("## ") and _RAISED_SECTION in line), None)
    if start is None:
        return []
    items: list[tuple[str, list[str]]] = []
    for line in lines[start + 1:]:
        if line.startswith("## "):
            break
        if line.startswith("### "):
            items.append((line[len("### "):].strip(), []))
        elif items:
            items[-1][1].append(line)
    return [heading for heading, body in items if _tracked_by(body, triple)]


def hold(root: Path, nxt: Next, *, files: Files, home: str) -> None:
    """Refuse while the SDD's companion holds an open Raised from downstream item that the active
    seed tracks. The product is the one the project's card names, and only a product with a
    `docs/SDD.md` is held. Reads through `files`, writes nothing, returns when nothing is held."""
    docs = _sdd_docs(root, nxt.project, files=files, home=home)
    companion = files.read_text(docs / "SDD_open_issues.md") if docs is not None else None
    if companion is None:
        return
    triple = f"{nxt.project} · nemawashi · {nxt.seed}"
    headings = _open_items(companion, triple)
    if not headings:
        return
    listed = "; ".join(headings)
    if len(headings) == 1:
        raise Refused(
            f"records-owed — SDD_open_issues.md holds an open Raised from downstream item tracked "
            f"by {triple}, and no station of that seed opens until it has folded: {listed}")
    raise Refused(
        f"records-owed — SDD_open_issues.md holds open Raised from downstream items tracked "
        f"by {triple}, and no station of that seed opens until they have folded: {listed}")


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
    files, home = Files(), str(Path.home())  # the composition root: the one place they are built
    try:
        nxt = check(root, args.project, git)
        hold(root, nxt, files=files, home=home)
        if args.command == "check":
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
