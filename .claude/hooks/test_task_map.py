"""Tests for `_task_map.py` — the one reader of `task_map.md`'s routing table.

Both salience hooks parse that table. A second parser would be a second definition of what a row
means, free to drift from the first, so there is one and these tests hold it.

The seam is the **path argument**: `routes()` is handed the file to read rather than reaching for
one, so a fixture is a real file in `tmp_path` and nothing monkeypatches the module under test —
`testing_python.md` § Rules.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _task_map  # noqa: E402

_TABLE = """---
version: "1.0.0"
---

# Task map

preamble prose that is not a row

| When you're about to… | Consult | Layer | Fires |
|---|---|---|---|
| Commit anything | `commit_format.md` | governance |  |
| Find a defect while walking — decide whether it is fixed here or cut as a seed | `found_while_walking.md` | governance | unprompted |
| Harden a skill | `skills.md` | kaizen |  |

closing note, also not a row
"""


def _map(tmp_path: Path, text: str | None = _TABLE) -> Path:
    path = tmp_path / "task_map.md"
    if text is not None:
        path.write_text(text, encoding="utf-8")
    return path


def test_it_reads_each_row_into_its_four_cells(tmp_path):
    rows = _task_map.routes(str(_map(tmp_path)))
    assert len(rows) == 3, "the header, the separator and the prose are not rows"
    first = rows[0]
    assert first.trigger == "Commit anything"
    assert first.consult == "commit_format.md", "backticks are stripped"
    assert first.layer == "governance"
    assert first.fires == ""


def test_the_short_trigger_stops_at_the_em_dash(tmp_path):
    rows = _task_map.routes(str(_map(tmp_path)))
    walking = [r for r in rows if r.consult == "found_while_walking.md"][0]
    assert walking.short == "Find a defect while walking"
    assert "cut as a seed" not in walking.short
    # A trigger with no em-dash is its own short form, unchanged.
    assert rows[0].short == "Commit anything"


def test_unprompted_selects_only_the_marked_rows(tmp_path):
    rows = _task_map.routes(str(_map(tmp_path)))
    marked = _task_map.unprompted(rows)
    assert [r.consult for r in marked] == ["found_while_walking.md"]


def test_a_missing_file_is_empty_never_an_exception(tmp_path):
    assert _task_map.routes(str(_map(tmp_path, text=None))) == []


def test_a_file_with_no_table_is_empty(tmp_path):
    assert _task_map.routes(str(_map(tmp_path, "# Nothing here\n\njust prose\n"))) == []


def test_a_row_missing_its_cells_is_skipped_not_raised(tmp_path):
    broken = _TABLE.replace("| Harden a skill | `skills.md` | kaizen |  |", "| Harden a skill |")
    rows = _task_map.routes(str(_map(tmp_path, broken)))
    assert [r.consult for r in rows] == ["commit_format.md", "found_while_walking.md"]


def test_the_map_path_resolves_through_the_instances_own_core(tmp_path):
    """`.env` declares CORE; the path is derived from it, not from this file's location."""
    repo = tmp_path / "instance"
    (repo / "core" / "doctrine").mkdir(parents=True)
    (repo / ".env").write_text("CORE=core/\n", encoding="utf-8")
    assert _task_map.map_path(str(repo)) == str(repo / "core" / "doctrine" / "task_map.md")


def test_the_real_map_parses_and_still_marks_the_boy_scout_rule():
    """The live table, not a fixture — the regression this whole change exists to prevent.

    Deliberately no row count: a count breaks the day a route is added, which is not a defect.
    """
    repo = Path(__file__).resolve().parents[2]
    rows = _task_map.routes(_task_map.map_path(str(repo)))
    assert len(rows) > 40, "the real table should parse to its many rows"
    assert "found_while_walking.md" in [r.consult for r in _task_map.unprompted(rows)]
