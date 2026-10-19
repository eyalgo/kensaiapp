"""Tests for `task_map_salience.py` — the SessionStart / SubagentStart injection that makes the
task→doctrine map salient.

Until 2026-09-02 this hook carried a hand-picked list of eight triggers out of the map's forty-nine
rows, and had no test. The list is why the boy-scout rule went unsurfaced: `task_map.md` polices
that every trigger the hook names resolves to a row, and nothing policed the other direction, so a
row nobody thought to add was invisible and looked identical to a row that did not exist. These
tests hold the list derived.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

_HOOK = Path(__file__).resolve().parent / "task_map_salience.py"

_MAP = """---
version: "1.0.0"
---

# Task map

preamble prose, not a row

| When you're about to… | Consult | Layer | Fires |
|---|---|---|---|
| Commit anything | `commit_format.md` | governance |  |
| Find a defect while walking — decide whether it is fixed here | `found_while_walking.md` | governance | unprompted |
| Harden a skill | `skills.md` | kaizen |  |
| Author a hook | `kensaiapp_structure.md` | setup |  |
"""


def _instance(tmp_path: Path, table: str | None = _MAP) -> Path:
    """A repo shaped like an instance, with no `.env` so `resolve_core._resolve` defaults to
    `<repo>/core` — the fixture shape `test_manifest_salience.py` uses."""
    repo = tmp_path / "instance"
    doctrine = repo / "core" / "doctrine"
    doctrine.mkdir(parents=True)
    if table is not None:
        (doctrine / "task_map.md").write_text(table, encoding="utf-8")
    return repo


def _run(repo: Path, event: str = "SubagentStart", payload: str | None = None):
    stdin = payload if payload is not None else json.dumps({"hook_event_name": event})
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(repo))
    env.pop("CLAUDE_ENV_FILE", None)
    return subprocess.run(
        [sys.executable, str(_HOOK)], input=stdin, capture_output=True, text=True, env=env
    )


def _context(result) -> str:
    assert result.returncode == 0
    assert result.stdout.strip(), "expected an injection, got silence"
    return json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]


def test_the_block_carries_a_probe_sentinel(tmp_path):
    assert "KENSAIAPP_TASK_MAP" in _context(_run(_instance(tmp_path)))


def test_it_names_every_row_not_a_chosen_few(tmp_path):
    """The selection defect, stated as a test: no row may be missing from the block."""
    context = _context(_run(_instance(tmp_path)))
    for consult in ("commit_format.md", "found_while_walking.md", "skills.md",
                    "kensaiapp_structure.md"):
        assert consult in context, f"{consult} is a row in the map and must be in the block"


def test_each_row_pairs_its_trigger_with_its_doctrine(tmp_path):
    context = _context(_run(_instance(tmp_path)))
    assert "Commit anything" in context
    # The short trigger, not the elaboration after the em-dash.
    assert "Find a defect while walking" in context
    assert "decide whether it is fixed here" not in context


def test_the_block_is_derived_from_the_map_not_hardcoded(tmp_path):
    """Change the map, and the block changes. A hardcoded list cannot pass this."""
    other = _MAP.replace("| Harden a skill | `skills.md` | kaizen |  |",
                         "| Do a brand new thing | `a_new_doctrine.md` | governance |  |")
    context = _context(_run(_instance(tmp_path, other)))
    assert "a_new_doctrine.md" in context
    assert "Do a brand new thing" in context
    assert "skills.md" not in context


def test_it_reflects_the_incoming_event(tmp_path):
    repo = _instance(tmp_path)
    for event in ("SessionStart", "SubagentStart"):
        out = json.loads(_run(repo, event).stdout)
        assert out["hookSpecificOutput"]["hookEventName"] == event


def test_a_missing_map_is_silent(tmp_path):
    result = _run(_instance(tmp_path, table=None))
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_a_map_with_no_table_is_silent(tmp_path):
    result = _run(_instance(tmp_path, "# Task map\n\nprose only\n"))
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_an_unparseable_payload_never_breaks_the_session(tmp_path):
    result = _run(_instance(tmp_path), payload="not json")
    assert result.returncode == 0


def test_no_hardcoded_trigger_list_survives_in_the_source():
    """The eight-trigger CONTEXT constant is what this change removes; its return would restore the
    defect silently, because a stale inline list still renders a plausible block."""
    source = _HOOK.read_text(encoding="utf-8")
    assert "CONTEXT = (" not in source
