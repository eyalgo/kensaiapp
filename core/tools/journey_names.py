"""journey_names.py — what a station's slug and dated stem look like, stated once.

WHY THIS EXISTS
    `shukuba-open` cuts a station's file name from a route item's slug, `build_idea` checks the
    stem a close row names, and `shukuba-retire` resolves the stem it is handed. Each held its own
    copy of the slug's characters until 2026-10-13, so a change to one would have left the others
    refusing names the first one writes. The skill scripts reach this file through their own path
    (`<CORE>/../skills/…` sits beside `<CORE>`), as `.claude/hooks/_task_map.py` reaches
    `core/tools/`.

Stdlib only.
"""

from __future__ import annotations

import re

__version__ = "1.0.0"

# A station's slug: lowercase letters and digits, joined by `-`, never opening with one.
SLUG = r"[a-z0-9][a-z0-9-]*"
# A station's dated stem: its file name at the shukuba root, without `.md`.
STATION_STEM = re.compile(rf"\d{{4}}-\d{{2}}-\d{{2}}_{SLUG}")


def station_stem(written: str) -> str | None:
    """The dated stem `written` names, with or without its `.md` suffix, or `None` when it is not
    one."""
    stem = written.removesuffix(".md")
    return stem if STATION_STEM.fullmatch(stem) else None
