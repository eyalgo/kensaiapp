#!/usr/bin/env python3
"""retire.py — the resolve half of `shukuba-retire`.

The model verifies the reached-when, moves, ticks and commits; this file decides which station
the close acts on. One command:

    resolve  — prints the station's path from the instance root: the one station at the project's
               shukuba root, or, when `--station` names one, that station, which must be there.

WHY THIS EXISTS
    The close used to find its station with whatever listing the run chose, and nothing checked
    the answer. On 2026-10-13 a run read a listing cut off by `| head -50` as an empty root and
    stopped on a station that was there. Only one station sits at a shukuba root, so a script
    can find it from the project alone, and `shukuba-open`'s `scripts/open.py check` already
    answers its own skill the same way.

Every refusal is printed and exits 1; nothing is written or moved.

Stdlib only, plus `<CORE>/tools/journey_names.py`, which owns what a station's dated stem looks
like and is reached through this file's own path.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# <root>/skills/scrum-master/.claude/skills/shukuba-retire/scripts/retire.py → <root>/core/tools
sys.path.insert(0, str(Path(__file__).resolve().parents[6] / "core" / "tools"))
import journey_names  # noqa: E402

__version__ = "1.0.0"

_SHUKUBA_FIXTURES = {"README.md", "parked", "trail"}


class Refused(Exception):
    """A station the close may not act on, with the reason."""


def _shukuba(root: Path, project: str) -> Path:
    path = root / "system" / "projects" / project / "journey" / "shukuba"
    if not path.is_dir():
        raise Refused(f"no shukuba at {path}")
    return path


def _open_stations(shukuba: Path) -> list[Path]:
    return sorted(
        p for p in shukuba.iterdir()
        if p.is_file() and p.name.endswith(".md") and not p.name.startswith(".")
        and p.name not in _SHUKUBA_FIXTURES
    )


def resolve(root: Path, project: str, station: str = "") -> Path:
    """The station the close acts on. Unnamed: the one station at the root. Named by its dated
    stem (with or without `.md`): that station, at the root. A root holding more than one station
    refuses either way — no close picks one of two."""
    shukuba = _shukuba(root, project)
    stations = _open_stations(shukuba)
    if len(stations) > 1:
        raise Refused(f"more than one station at the shukuba root: "
                      f"{', '.join(p.name for p in stations)} — a root holds one, so none is "
                      f"closed until the others are parked or closed by hand")
    if not station:
        if not stations:
            raise Refused(f"no station is open at {shukuba} — nothing to close")
        return stations[0]
    stem = journey_names.station_stem(station)
    if stem is None:
        raise Refused(f"'{station}' is not a station's dated stem — name it as "
                      f"<YYYY-MM-DD>_<slug>")
    name = f"{stem}.md"
    target = shukuba / name
    if target in stations:
        return target
    if (shukuba / "trail" / name).is_file():
        raise Refused(f"{name} is already closed: it is in {shukuba / 'trail'}")
    if (shukuba / "parked" / name).is_file():
        raise Refused(f"{name} is parked in {shukuba / 'parked'}, not open at the root")
    holds = ", ".join(p.name for p in stations) or "nothing"
    raise Refused(f"no station {name.removesuffix('.md')} at {shukuba} — the root holds {holds}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--project", required=True)
    sub = parser.add_subparsers(dest="command", required=True)
    resolve_p = sub.add_parser("resolve")
    resolve_p.add_argument("--station", default="")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        print(resolve(root, args.project, args.station).relative_to(root))
    except Refused as refusal:
        print(f"REFUSED: {refusal}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
