"""Fleet-wide guard: every launcher that starts a `claude --bg` run hands its watcher the id.

`watch_agent.py:155` calls `--agent-id` "the exact handle: given this, the name is not consulted
at all. Preferred over --name." The name is the one thing Claude Code rewrites — now inside the
90-second appear window, on a run that has barely begun (`watch_agent.py` § THE NAME IS NOT A
HANDLE) — so a watcher running on the name is watching a guess.

The id is knowable exactly once: `claude --bg` prints `backgrounded · <id>` at launch, and the
launcher is the only thing in the room when it does. Measured 2026-08-23, before this guard, that
id reached `watch_agent` from **zero** of the seventeen files below.

**Why this is enumerated from disk rather than listed.** Seventeen is a list that goes stale the
first time an eighteenth launcher is written by copying a seventeenth — the reasoning
`test_keep_awake_binding.py` states for the same tree, and this file follows its shape
deliberately.

The rule is one line: **a file that invokes `claude --bg` names an id-feeding flag.** Either
`--agent-id` (it parsed the id itself, because it needs the value for something besides the watch)
or `--launch-output` (it hands the raw launch output to `detach_watcher.sh` and never parses
anything). There is no exemption: a launcher that starts a run it cannot name has no business
reporting on one.

The second rule guards the first: **the parse has one home.** `capture_agent_id` in
`core/tools/detach_watcher.sh` is the only place a `backgrounded` line is read. A launcher growing
its own `awk '/backgrounded/` is the duplication this replaced, coming back.
"""

from __future__ import annotations

from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]

# The shell layer. `.worktrees/` is another checkout of this same repo — its files belong to some
# other branch, and holding them to this tree's rules reports findings nobody here can fix.
_ROOT = _REPO / "core"

_LIBRARY = Path("core/tools/detach_watcher.sh")


def _non_comment_lines(path: Path):
    return [l for l in path.read_text().splitlines() if not l.lstrip().startswith("#")]


def _launcher_files():
    """Every `.sh` under `core/` that actually *invokes* `claude --bg`, mapped to its non-comment
    lines. Comment lines are excluded throughout: nearly every launcher header explains what
    `claude --bg` does and why, and a check that cannot tell an explanation from an invocation
    would forbid recording the reason."""
    found = {}
    for path in sorted(_ROOT.rglob("*.sh")):
        lines = _non_comment_lines(path)
        if any("claude --bg" in l for l in lines):
            found[path.relative_to(_REPO)] = lines
    return found


# `test_the_sweep_finds_the_launchers_it_is_meant_to_check` (a `_launcher_files()` sweep for a
# literal `claude --bg` invocation, asserting the sweep still finds something) is retired here,
# per its own comment's prediction: Task 19 moved the last two launchers that still spelled
# `claude --bg` in their own shell text (companion-self-answer, product-sdd) onto the one adapter
# (`core/tools/agent_run.py --print-argv`), so every launcher now drops out of this literal-text
# sweep by construction — `_launcher_files()` is permanently empty, and the assertion it existed
# to make ("the sweep still finds something") can never again distinguish a broken filter from a
# compliant fleet. `core/launchers/test_core_resolution.py` (Task 21, fleet checks over the
# launcher folders directly rather than over this literal text) is the sweep that replaces it.
# `test_every_launcher_feeds_its_watcher_an_id` below is left in place — it is vacuously
# true now (`_launcher_files()` is empty) but asserts nothing false, and Task 21's own sweep is
# what governs the fleet going forward.


def test_every_launcher_feeds_its_watcher_an_id():
    """The rule. Either the launcher parsed the id (`--agent-id`) or it handed the launch output
    over for the library to parse (`--launch-output`). Naming neither means its watcher is still
    running on a name Claude Code is free to rewrite."""
    offenders = [
        str(path)
        for path, lines in _launcher_files().items()
        if not any("--agent-id" in l or "--launch-output" in l for l in lines)
    ]

    assert not offenders, (
        "these launchers start a `claude --bg` run and never tell their watcher which run it is, "
        "so the watch falls back to a name Claude Code rewrites:\n  " + "\n  ".join(sorted(offenders))
    )


def test_the_backgrounded_line_is_parsed_in_exactly_one_place():
    """The parse has one home — `capture_agent_id` in the shared library. A launcher with its own
    `awk '/backgrounded/` has reintroduced the copy this replaced."""
    parsers = sorted(
        str(path.relative_to(_REPO))
        for path in _ROOT.rglob("*.sh")
        if any("backgrounded" in l for l in _non_comment_lines(path))
    )

    assert parsers == [str(_LIBRARY)], (
        "the `backgrounded` launch line is read in more than one place (or in none):\n  "
        + "\n  ".join(parsers)
    )


def test_the_library_exposes_the_parse_as_a_function():
    """`capture_agent_id` is public on purpose: the two launchers that need the id for something
    besides the watch — `launch-skill-evals` for its round lock, `launch-audit` for its hand-built
    `watch_args` — call it rather than keeping a second copy."""
    body = (_REPO / _LIBRARY).read_text()

    assert "capture_agent_id()" in body
