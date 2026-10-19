"""Tests for `standing_rules_salience.py` — the injection that makes standing rules bind without
being consulted.

The task map is a pull: "where to look, **by what you're about to do**". A few rules do not work
that way — you do not decide to find a defect while walking, and failing to notice is the very thing
the rule exists to catch. Routing cannot deliver those, because consulting the index is the step
that never happens. Measured 2026-09-02: a satellite session carrying the trigger "find a defect
while walking" in context still could not name the rule when asked.

So these rows are injected as *binding* rather than as routes. This hook is that injection, and
these tests hold two things: that it names them, and that it does not restate them. The one block
carried whole, how to reply to the owner, is read from its own file and tested where it is rendered,
`core/tools/test_task_context.py`. The fixtures here hold no such file, so the naming block is
measured alone.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

_HOOK = Path(__file__).resolve().parent / "standing_rules_salience.py"

_MAP = """---
version: "1.0.0"
---

# Task map

| When you're about to… | Consult | Layer | Fires |
|---|---|---|---|
| Commit anything | `commit_format.md` | governance |  |
| Find a defect while walking — decide whether it is fixed here | `found_while_walking.md` | governance | unprompted |
| Harden a skill | `skills.md` | kaizen |  |
| Cite one of our own records — for a load-bearing claim | `single_source.md` | governance | unprompted |
"""


def _instance(tmp_path: Path, table: str | None = _MAP) -> Path:
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


def test_the_block_carries_its_own_probe_sentinel(tmp_path):
    assert "KENSAIAPP_STANDING_RULES" in _context(_run(_instance(tmp_path)))


def test_it_names_the_unprompted_rules(tmp_path):
    context = _context(_run(_instance(tmp_path)))
    assert "found_while_walking.md" in context
    assert "single_source.md" in context
    assert "Find a defect while walking" in context


def test_it_carries_only_the_marked_rows(tmp_path):
    """A routing row injected here would be a second copy of the map, and would drown the few rows
    that need to bind."""
    context = _context(_run(_instance(tmp_path)))
    assert "commit_format.md" not in context
    assert "skills.md" not in context


def test_it_is_framed_as_binding_not_as_routing(tmp_path):
    """The distinction is the whole point: these apply whether or not anything is consulted."""
    context = _context(_run(_instance(tmp_path))).lower()
    assert "already bound" in context


def test_it_denies_that_reading_the_doctrine_is_what_binds(tmp_path):
    """Measured 2026-09-02 in a cold example-8792fa session: given the previous wording, a fresh reader
    offered to "read the whole file" so the rule would be "actually in force" — treating the rule as
    pending its own reading. A standing rule that a session thinks it can defer by not opening a file
    is not standing. The block must close that reading explicitly."""
    context = _context(_run(_instance(tmp_path))).lower()
    assert "does not suspend" in context
    assert "not what puts it in force" in context


def test_it_names_the_rules_without_restating_them(tmp_path):
    """`task_map.md` owns the route and the doctrine body owns the rule. If this block starts
    carrying what found_while_walking.md *says*, it has taken ownership it does not hold."""
    context = _context(_run(_instance(tmp_path)))
    # The rule's actual content — its three clauses — must not appear here.
    for clause in ("fixed on the build branch", "cut as a seed", "before the merge"):
        assert clause not in context
    assert len(context) < 1200, "a naming block, not a restatement"


def test_it_is_derived_from_the_map_not_hardcoded(tmp_path):
    other = _MAP.replace("| Cite one of our own records — for a load-bearing claim | `single_source.md` | governance | unprompted |",
                         "| Do a newly marked thing | `a_new_doctrine.md` | governance | unprompted |")
    context = _context(_run(_instance(tmp_path, other)))
    assert "a_new_doctrine.md" in context
    assert "single_source.md" not in context


def test_it_reflects_the_incoming_event(tmp_path):
    repo = _instance(tmp_path)
    for event in ("SessionStart", "SubagentStart"):
        out = json.loads(_run(repo, event).stdout)
        assert out["hookSpecificOutput"]["hookEventName"] == event


def test_a_map_with_no_marked_rows_is_silent(tmp_path):
    """No standing rules and no reply rules is a real state, and it must inject nothing rather than
    an empty heading."""
    plain = _MAP.replace(" unprompted |", "  |")
    result = _run(_instance(tmp_path, plain))
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_a_missing_map_is_silent(tmp_path):
    result = _run(_instance(tmp_path, table=None))
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_an_unparseable_payload_never_breaks_the_session(tmp_path):
    result = _run(_instance(tmp_path), payload="not json")
    assert result.returncode == 0


def test_the_block_carries_a_rules_informal_name_when_it_has_one():
    """The owner asks for "the boy-scout rule"; a block naming only `found_while_walking.md` cannot
    be addressed in those words. Measured 2026-09-02: a cold session held the trigger and still could
    not match the name to it. Only this one of the five rules has an informal name."""
    repo = Path(__file__).resolve().parents[2]
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(repo))
    env.pop("CLAUDE_ENV_FILE", None)
    result = subprocess.run([sys.executable, str(_HOOK)], input="{}", capture_output=True,
                            text=True, env=env)
    assert "boy-scout" in _context(result)


def test_the_live_map_still_binds_the_boy_scout_rule():
    """The regression in the real instance, not a fixture."""
    repo = Path(__file__).resolve().parents[2]
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(repo))
    env.pop("CLAUDE_ENV_FILE", None)
    result = subprocess.run([sys.executable, str(_HOOK)], input="{}", capture_output=True,
                            text=True, env=env)
    assert "found_while_walking.md" in _context(result)
