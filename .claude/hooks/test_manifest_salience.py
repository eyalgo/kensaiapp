"""Tests for `manifest_salience.py` — the SessionStart / SubagentStart injection that makes the
instance manifest's *sections* reachable.

Measured over 584 real briefs: 111 name `kensaiapp_structure.md` and only 17 cite a line range, so
94 point an agent at 902 lines. The file has named sections; this hook puts their index in context so
a run can reach the right one without reading the whole thing.

Its sibling `task_map_salience.py` carries a `KENSAIAPP_TASK_MAP` sentinel described as a probe "lets
a test confirm propagation" and went untested until 2026-09-02, when deriving its block from the map
gave it `test_task_map_salience.py`. Both sentinels are now asserted on.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

_HOOK = Path(__file__).resolve().parent / "manifest_salience.py"

_MANIFEST = """---
version: "1.0.0"
---

# Structure

intro

## 1. Instance-level

body

### Root

body

## 2. Per-project

body
"""


def _instance(tmp_path: Path, manifest: str | None = _MANIFEST) -> Path:
    """A repo shaped like an instance, with no `.env` so `resolve_core._resolve` defaults to
    `<repo>/core` — the same fixture shape `test_written_forward_guard.py` uses."""
    repo = tmp_path / "instance"
    setup = repo / "core" / "doctrine" / "setup"
    setup.mkdir(parents=True)
    if manifest is not None:
        (setup / "kensaiapp_structure.md").write_text(manifest)
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
    assert "KENSAIAPP_STRUCTURE_MAP" in _context(_run(_instance(tmp_path)))


def test_it_lists_the_manifest_sections_with_their_lines(tmp_path):
    context = _context(_run(_instance(tmp_path)))
    assert "1. Instance-level" in context
    assert "2. Per-project" in context
    assert "Root" in context
    # Derived from the fixture, not counted by hand — the failure this whole guard exists to catch.
    expected = _MANIFEST.splitlines().index("## 1. Instance-level") + 1
    assert f":{expected}" in context, "a section is reachable by line, not just by name"


def test_the_index_is_derived_from_the_file_not_hardcoded(tmp_path):
    """The whole point is that it cannot drift. Change the manifest, and the block changes."""
    other = _MANIFEST.replace("## 2. Per-project", "## 2. Something Else Entirely")
    context = _context(_run(_instance(tmp_path, other)))
    assert "Something Else Entirely" in context
    assert "Per-project" not in context


def test_it_reflects_the_incoming_event(tmp_path):
    repo = _instance(tmp_path)
    for event in ("SessionStart", "SubagentStart"):
        out = json.loads(_run(repo, event).stdout)
        assert out["hookSpecificOutput"]["hookEventName"] == event


def test_a_missing_manifest_is_silent(tmp_path):
    result = _run(_instance(tmp_path, manifest=None))
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_an_unparseable_payload_never_breaks_the_session(tmp_path):
    result = _run(_instance(tmp_path), payload="not json")
    assert result.returncode == 0
