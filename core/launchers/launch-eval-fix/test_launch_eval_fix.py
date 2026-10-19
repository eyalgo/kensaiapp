"""Contract tests for `launch-eval-fix/launcher.sh`.

Sibling of `launch-skill-evals`, and the two are two sides of one rule: that launcher writes the
round lock, this one reads it and stands down, because this pass EDITS skills and a skill edited
mid-benchmark makes that round's numbers describe a skill that never existed.

What is pinned here:

- **Round resolution takes the newest SETTLED iteration**, meaning the newest with a `benchmark.md`
  — not the newest directory. A killed or in-flight round leaves case folders and no numbers, and
  the fix-author pointed at one would be reading an absence. The fixtures deliberately put an
  unsettled iteration ABOVE the settled one, which is the only arrangement where the distinction
  shows.
- **The previous settled round is passed for comparison**, and skipped cleanly when there is none.
- **It stands down while a round holds the lock**, with `--force` and `--dry-run` as the exits.
- **The fixed-prompt guarantee** — a caller passes a skill name; the round is derived, never typed.
- **No `--agent`** — the workflow spawns the two postures itself (author with no Edit, fixer with no
  Write), so the driving session's model is not load-bearing and inherits.

Isolation: the real script runs with `tmp_path` as cwd (its instance root). A fake `claude` on PATH
records argv; the watcher and notifier are stubbed; the lock is driven through the real
`evals_round_lock.py` via `KENSAIAPP_EVALS_LOCK`, so these tests exercise the actual protocol rather
than a reimplementation of it.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

import pytest

from provenance_test_support import (
    assert_instrument_run_call_carries_provenance,
    assert_provenance_stamped,
)

_SCRIPT = Path(__file__).resolve().parent / "launcher.sh"
# The delivered provider file: the tracked template at the instance root, copied into the instance
# a case runs for. No suite leans on a live `.providers.toml`, which is untracked.
_PROVIDER_EXAMPLE = Path(__file__).resolve().parents[3] / ".providers.toml.example"

CLAUDE_STUB = """#!/usr/bin/env bash
if [ "${1:-}" = "agents" ]; then
  if [ -n "${AGENTS_JSON:-}" ] && [ -f "$AGENTS_JSON" ]; then cat "$AGENTS_JSON"; else echo '[]'; fi
  exit 0
fi
printf '%s\\n' "$@" > "$CLAUDE_ARGV_LOG"
printf 'backgrounded %s\\n' "${STUB_AGENT_ID:-newid00}"
"""

WATCHER_STUB = """import sys
if "--list-ids" in sys.argv:
    print("pre1,pre2")
else:
    print("watcher-stub: stdout line")
    print("watcher-stub: stderr line", file=sys.stderr)
    with open(__import__("os").environ["WATCHER_ARGV_LOG"], "w") as fh:
        fh.write("\\n".join(sys.argv[1:]))
"""

NOTIFIER_STUB = """#!/usr/bin/env bash
printf '%s\\n' "$@" >> "$NOTIFIER_ARGV_LOG"
"""


@pytest.fixture
def run(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    claude_stub = bin_dir / "claude"
    claude_stub.write_text(CLAUDE_STUB)
    claude_stub.chmod(0o755)

    watcher_stub = tmp_path / "watch_agent_stub.py"
    watcher_stub.write_text(WATCHER_STUB)
    notifier_stub = tmp_path / "notify_stub.sh"
    notifier_stub.write_text(NOTIFIER_STUB)
    notifier_stub.chmod(0o755)

    argv_log = tmp_path / "claude_argv.log"
    watcher_log = tmp_path / "watcher_argv.log"
    agents_json = tmp_path / "agents.json"
    lock_path = tmp_path / "round.lock.json"

    env = dict(os.environ)
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
    # Points at a path nothing occupies, so this fixture never reads this machine's real
    # published telemetry endpoint (`a-launcher-tags-its-own-run`) — a launcher's own suite
    # is isolated from real machine state exactly like the watcher and the notifier above.
    env["INSTRUMENT_RUN_ENDPOINT_FILE"] = str(tmp_path / "no-instrument-endpoint")
    env["CLAUDE_ARGV_LOG"] = str(argv_log)
    env["WATCHER_ARGV_LOG"] = str(watcher_log)
    env["AGENTS_JSON"] = str(agents_json)
    env["KENSAIAPP_EVALS_LOCK"] = str(lock_path)
    env["LAUNCH_EVAL_FIX_WATCHER"] = str(watcher_stub)
    env["LAUNCH_EVAL_FIX_NOTIFIER"] = str(notifier_stub)
    # The instance's own provider file: an unforced launch reads it at the instance root.
    (tmp_path / ".providers.toml").write_text(_PROVIDER_EXAMPLE.read_text(encoding="utf-8"))
    env["HOME"] = str(tmp_path / "home")
    (tmp_path / "home").mkdir()

    def _run(*cli_args, script=_SCRIPT):
        # `script` lets one test run an isolated COPY of the launcher from a tree that lacks
        # something the real one has — the only way to exercise a missing `$DETACH_LIB`, which
        # has no env override to unset.
        return subprocess.run([str(script), *cli_args], cwd=str(tmp_path),
                              capture_output=True, text=True, env=env)

    def _skill(name="demo-skill", settled=(), unsettled=()):
        """Create a skill whose workspace has `settled` iterations (with benchmark.md) and
        `unsettled` ones (case dirs only — a killed or in-flight round)."""
        ws = tmp_path / ".claude" / "skills" / name / "evals" / "workspace"
        ws.mkdir(parents=True)
        for n in settled:
            d = ws / f"iteration-{n}"
            d.mkdir()
            (d / "benchmark.md").write_text(f"# benchmark {n}\n")
        for n in unsettled:
            (ws / f"iteration-{n}").mkdir()
        return ws

    def _bare_skill(name="demo-skill"):
        (tmp_path / ".claude" / "skills" / name).mkdir(parents=True)

    def _grouped_skill(group="g", name="demo-skill", settled=(), unsettled=()):
        """Same as `_skill`, but built only under the grouped layout — no flat `.claude/skills/`
        at all."""
        ws = tmp_path / "skills" / group / ".claude" / "skills" / name / "evals" / "workspace"
        ws.mkdir(parents=True)
        for n in settled:
            d = ws / f"iteration-{n}"
            d.mkdir()
            (d / "benchmark.md").write_text(f"# benchmark {n}\n")
        for n in unsettled:
            (ws / f"iteration-{n}").mkdir()
        return ws

    def _bare_grouped_skill(group="g", name="demo-skill"):
        d = tmp_path / "skills" / group / ".claude" / "skills" / name
        d.mkdir(parents=True)
        return d

    def _hold(agent_id="held01", state="working"):
        lock_path.write_text(json.dumps(
            {"schema_version": 1, "agent_id": agent_id, "skill": "other", "cwd": "/x", "iteration": 1}))
        agents_json.write_text(json.dumps(
            [{"id": agent_id, "kind": "background", "cwd": "/x", "state": state}]))

    def _launched_argv():
        return argv_log.read_text().splitlines() if argv_log.exists() else []

    def _watcher_argv():
        for _ in range(50):
            if watcher_log.exists():
                return watcher_log.read_text().splitlines()
            time.sleep(0.05)
        return []

    def _default_watcher():
        """Drop the stub override so the launcher must resolve its own default path."""
        env.pop("LAUNCH_EVAL_FIX_WATCHER", None)

    _run.root = tmp_path
    _run.env = env
    _run.default_watcher = _default_watcher
    _run.skill = _skill
    _run.bare_skill = _bare_skill
    _run.grouped_skill = _grouped_skill
    _run.bare_grouped_skill = _bare_grouped_skill
    _run.hold = _hold
    _run.launched_argv = _launched_argv
    _run.watcher_argv = _watcher_argv
    return _run


# --- guards -------------------------------------------------------------------


def test_no_skill_arg_dies_with_usage(run):
    result = run()
    assert result.returncode != 0
    assert "usage: launch-eval-fix" in result.stderr


def test_unknown_skill_dies(run):
    result = run("nope")
    assert result.returncode != 0
    assert "no skill at" in result.stderr


def test_a_skill_with_no_workspace_dies(run):
    run.bare_skill("demo-skill")
    result = run("demo-skill")
    assert result.returncode != 0
    assert "no eval runs under" in result.stderr


def test_a_path_shaped_argument_is_rejected(run):
    run.skill("demo-skill", settled=(1,))
    result = run(".claude/skills/demo-skill")
    assert result.returncode != 0
    assert "is a skill NAME, not a path" in result.stderr


# --- round resolution ----------------------------------------------------------


def test_only_a_settled_round_is_acted_on(run):
    # iteration-9 exists but never produced a benchmark (killed mid-run). Acting on it would point
    # the fix-author at case folders with no numbers in them.
    run.skill("demo-skill", settled=(6,), unsettled=(9,))
    result = run("demo-skill", "--dry-run")
    assert "iteration-6" in result.stdout
    assert "iteration-9" not in result.stdout


def test_no_settled_round_at_all_dies_rather_than_guessing(run):
    run.skill("demo-skill", settled=(), unsettled=(4, 5))
    result = run("demo-skill")
    assert result.returncode != 0
    assert "no settled round" in result.stderr
    assert run.launched_argv() == []


def test_the_previous_settled_round_is_passed_for_comparison(run):
    run.skill("demo-skill", settled=(3, 6), unsettled=(7,))
    run("demo-skill")
    prompt = run.launched_argv()[1]
    assert "iteration-6" in prompt
    assert "previous" in prompt and "iteration-3" in prompt


def test_a_first_ever_round_carries_no_previous(run):
    run.skill("demo-skill", settled=(1,))
    result = run("demo-skill")
    assert "no earlier settled round" in result.stdout
    assert "previous" not in run.launched_argv()[1]


def test_the_previous_is_the_nearest_settled_one_below(run):
    # Not simply "the one before by number": iteration-5 is unsettled, so 3 is the comparison point.
    run.skill("demo-skill", settled=(2, 3, 6), unsettled=(5,))
    run("demo-skill")
    prompt = run.launched_argv()[1]
    assert "iteration-3" in prompt
    assert "iteration-2" not in prompt


# --- standing down while a round runs ------------------------------------------


def test_refuses_while_a_benchmark_round_holds_the_lock(run):
    run.skill("demo-skill", settled=(1,))
    run.hold(state="working")
    result = run("demo-skill")
    assert result.returncode != 0
    assert "an eval round is running" in result.stderr
    assert run.launched_argv() == []


def test_a_finished_round_does_not_hold_it_back(run):
    run.skill("demo-skill", settled=(1,))
    run.hold(state="stopped")
    result = run("demo-skill")
    assert result.returncode == 0, result.stderr
    assert run.launched_argv() != []


def test_force_overrides_the_stand_down(run):
    run.skill("demo-skill", settled=(1,))
    run.hold(state="working")
    result = run("demo-skill", "--force")
    assert result.returncode == 0, result.stderr


def test_dry_run_is_exempt(run):
    run.skill("demo-skill", settled=(1,))
    run.hold(state="working")
    result = run("demo-skill", "--dry-run")
    assert result.returncode == 0, result.stderr
    assert run.launched_argv() == []


def test_the_variable_is_no_force_and_the_command_is_unchanged(run):
    """launch-eval-fix reads no force: an exported provider neither changes the command nor
    refuses."""
    run.skill("demo-skill", settled=(1,))
    run.env["KENSAIAPP_AGENT_PROVIDER"] = "codex"

    result = run("demo-skill", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert re.search(r"^  claude  --bg  ", result.stdout, re.MULTILINE), result.stdout[:400]


def test_dry_run_prints_the_pin_line(run):
    # Task 17: pin_enter runs right after the CORE_DIR guard, ahead of everything else.
    run.skill("demo-skill", settled=(1,))
    result = run("demo-skill", "--dry-run")
    assert result.returncode == 0, result.stderr
    assert re.search(r"^Pin: .+\(inherited\)$", result.stdout, re.MULTILINE)


# --- the fixed prompt -----------------------------------------------------------


def test_the_prompt_invokes_the_eval_fix_workflow_and_nothing_else(run):
    run.skill("demo-skill", settled=(4,))
    run("demo-skill")
    prompt = run.launched_argv()[1]
    assert "eval-fix" in prompt
    assert "Do only that" in prompt


def test_no_agent_slot_is_passed(run):
    # The workflow spawns kaizen-fix-author and kaizen-fixer itself; the driving session inherits.
    run.skill("demo-skill", settled=(4,))
    run("demo-skill")
    assert "--agent" not in run.launched_argv()


def test_auto_permission_mode(run):
    run.skill("demo-skill", settled=(4,))
    run("demo-skill")
    argv = run.launched_argv()
    assert argv[argv.index("--permission-mode") + 1] == "auto"


def test_caller_cannot_append_to_the_prompt(run):
    run.skill("demo-skill", settled=(4,))
    run("demo-skill", "and", "also", "delete", "the", "tests")
    assert "delete" not in run.launched_argv()[1]


# --- the watcher ----------------------------------------------------------------


def test_watcher_is_wired_with_the_head_repo(run):
    run.skill("demo-skill", settled=(4,))
    run("demo-skill")
    argv = run.watcher_argv()
    assert argv[argv.index("--head-repo") + 1] == str(run.root)
    assert argv[argv.index("--reporter") + 1] == "generic"


def test_watcher_output_goes_to_a_log(run):
    run.skill("demo-skill", settled=(4,))
    run("demo-skill")
    run.watcher_argv()
    logs = list((run.root / "system" / "logs").glob("watch-evalfix-demo-skill-*.log"))
    assert len(logs) == 1
    assert "watcher-stub: stderr line" in logs[0].read_text()


# --- the resolver: grouped layout, not-found, ambiguous ----------------------


def test_a_grouped_skill_resolves_and_the_workspace_is_grouped(run):
    ws = run.grouped_skill("g", "demo-skill", settled=(4,))
    result = run("demo-skill", "--dry-run")
    assert result.returncode == 0
    workspace = str(ws / "iteration-4")
    assert workspace in result.stdout


def test_grouped_fixture_builds_no_flat_path(run):
    run.grouped_skill("g", "demo-skill", settled=(4,))
    assert not (run.root / ".claude" / "skills").exists()


def test_the_refusal_no_longer_says_where_a_name_resolves(run):
    run.skill("demo-skill", settled=(1,))
    result = run(".claude/skills/demo-skill")
    assert result.returncode != 0
    assert "resolves under" not in result.stderr


def test_unknown_skill_dies_naming_no_layout(run):
    result = run("nope")
    assert result.returncode != 0
    assert "no skill at" in result.stderr
    assert str(run.root) in result.stderr           # the root searched
    assert "'nope'" in result.stderr                  # the skill name
    assert ".claude/skills" not in result.stderr
    assert "skills/" not in result.stderr


def test_ambiguous_skill_dies_naming_both_matching_directories(run):
    d1 = run.bare_grouped_skill("g1", "demo-skill")
    d2 = run.bare_grouped_skill("g2", "demo-skill")
    result = run("demo-skill")
    assert result.returncode != 0
    assert str(d1) in result.stderr
    assert str(d2) in result.stderr
    assert run.launched_argv() == []


def test_ambiguous_message_differs_from_not_found_message(run):
    run.bare_grouped_skill("g1", "demo-skill")
    run.bare_grouped_skill("g2", "demo-skill")
    ambiguous = run("demo-skill")
    not_found = run("nope")
    assert ambiguous.stderr != not_found.stderr
    assert ambiguous.returncode != 0
    assert not_found.returncode != 0


def test_stderr_noise_on_a_clean_resolve_never_reaches_the_captured_path(run):
    """The resolver's own stderr is folded into the captured value today (2>&1), so any text a
    future resolver version prints on a successful exit would land INSIDE skill_dir. A stub
    resolver here — exit 0, a real directory on stdout, a line of noise on stderr — proves the
    fold does not happen: the launcher proceeds against the stdout path alone."""
    run.skill("demo-skill", settled=(1,))
    skill_dir = run.root / ".claude" / "skills" / "demo-skill"
    stub = run.root / "stub_resolver.py"
    stub.write_text(
        "import sys\n"
        f"print({str(skill_dir)!r})\n"
        "print('resolver: a future warning', file=sys.stderr)\n"
    )
    run.env["LAUNCH_EVAL_FIX_RESOLVER"] = str(stub)
    result = run("demo-skill", "--dry-run")
    assert result.returncode == 0, result.stderr
    assert "resolver: a future warning" not in result.stdout
def _wait_for_text(path, needle, timeout=5.0):
    """True once `needle` appears in `path`. The watcher is detached, so its first line lands
    after the launcher has already returned — polling is how a test observes a process whose
    timing it does not control."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.exists() and needle in path.read_text():
            return True
        time.sleep(0.05)
    return False


# --- the two core-relative paths, at their real depth ----------------------------
#
# This launcher sits at `<CORE>/launchers/launch-eval-fix/`, a sibling of `<CORE>/tools/`, so both
# of the things it reads under core resolve via CORE_DIR. Neither failure announces itself: a watcher
# it cannot find leaves the detach unrun while the launch still exits 0, and a library it cannot
# find skips the detach entirely the same way. Every other test in this suite stubs `$WATCHER` and
# would stay green against either.


def test_watcher_is_found_at_its_resolved_home_when_the_env_override_is_unset(run):
    """The only test here that unsets `$LAUNCH_EVAL_FIX_WATCHER`, because it is the only failure
    in this suite that is SILENT. Asserted through the outcome — the detach ran and wrote its log —
    rather than against a literal path, so it still pins the behaviour if the walk is ever
    expressed differently."""
    run.skill("demo-skill", settled=(4,))
    run.default_watcher()

    result = run("demo-skill")

    assert result.returncode == 0
    assert "completion watch skipped" not in result.stdout
    assert "Watcher log:" in result.stdout, (
        f"the detach did not run — the launcher failed to resolve watch_agent.py. stdout: "
        f"{result.stdout}"
    )
    logs = list((run.root / "system" / "logs").glob("watch-evalfix-demo-skill-*.log"))
    assert logs, "no watcher log was written, so no completion watch is running"
    # And it is the REAL watcher that started, not merely a file that happened to exist at the
    # path: `watch_agent.py` announces itself on stderr before doing anything else, flushed, and
    # that line is the log's own proof of which process wrote it. Polled, because the log is
    # created by the shell redirect the instant the detach happens and filled a moment later.
    assert _wait_for_text(logs[0], "watch_agent:"), (
        f"the log exists but no real watcher wrote to it: {logs[0].read_text()!r}"
    )


def test_detach_watcher_is_found_at_its_resolved_home_when_nothing_overrides_it(run):
    """`$DETACH_LIB` has no env override to unset — unlike `$WATCHER`, no test or caller ever
    wants a stub in its place. So every passing launch in this suite already runs against the
    real `core/tools/detach_watcher.sh` at its real relative depth, and this names that invariant
    on its own rather than leaving it as a side effect nothing asserts."""
    run.skill("demo-skill", settled=(4,))

    result = run("demo-skill")

    assert result.returncode == 0
    assert "no completion-watch library at" not in result.stdout
    assert run.watcher_argv() != []


def test_a_missing_detach_watcher_is_reported_distinctly_and_does_not_block_the_launch(
    run, tmp_path_factory
):
    """The negative case, built from an isolated copy of the launcher relocated into a tree with
    no `tools/detach_watcher.sh` beside it — never by disturbing the real one, which every other
    test in this suite depends on.

    `isolated/core` stands in for CORE_DIR, with `isolated/pin.json` marking `isolated` as its
    own pin — so pin_enter (rule 1) finds itself already a pin and neither re-execs nor copies
    anything: what this test builds is exactly what runs (Task 17). `tools/` holds only the
    machinery pin_enter and the adapter build unconditionally reach, plus the resolver — never
    detach_watcher.sh, which is what this test is about."""
    run.skill("demo-skill", settled=(4,))

    isolated = tmp_path_factory.mktemp("no_detach_lib")
    core_root = isolated / "core"
    launcher_dir = core_root / "launchers" / "launch-eval-fix"
    launcher_dir.mkdir(parents=True)
    copied = launcher_dir / "launcher.sh"
    copied.write_text(_SCRIPT.read_text())
    copied.chmod(0o755)
    tools_dir = core_root / "tools"
    tools_dir.mkdir()  # sibling of launchers/ — no detach_watcher.sh inside it
    # The resolver DOES go in. The launcher reaches for it before it reaches for the detach
    # library, so a tree missing both dies at the resolver and never gets far enough to report
    # the thing this test is about — one missing file, not two.
    shutil.copy2(
        _SCRIPT.resolve().parents[2] / "tools" / "skill_path.py",
        tools_dir / "skill_path.py",
    )
    # Task 17: pin_enter (sourced right after the CORE_DIR guard) and the adapter it shells out
    # to are reached before either the resolver or the detach library, so they go in too.
    # The one intelligence resolution and its reader are reached before the detach library too.
    for _tool in ("pin.py", "pin_run.sh", "agent_run.py", "model_assignment.py", "task_context.py",
                  "hook_wiring.py",
                  "env_file.py", "run_intelligence.py", "intelligence.py", "providers.py"):
        shutil.copy2(
            _SCRIPT.resolve().parents[2] / "tools" / _tool,
            tools_dir / _tool,
        )
    (isolated / "pin.json").write_text(
        json.dumps(
            {
                "id": "isolated",
                "source_host_root": str(isolated),
                "created": "1970-01-01T00:00:00+00:00",
            }
        )
        + "\n"
    )

    result = run("demo-skill", script=copied)

    assert result.returncode == 0
    assert run.launched_argv() != [], "the primary launch still happened"
    assert "no completion-watch library at" in result.stdout


def test_dry_run_states_the_arm_it_would_run_under(run, tmp_path):
    """`a-launcher-tags-its-own-run` — a dry run that hides the instrument is a dry run that
    lies. With a published endpoint file present, `instrument_run` prints the arm it derived
    (this launcher's own directory name) even though nothing is actually spawned."""
    endpoint_file = tmp_path / "real-instrument-endpoint"
    endpoint_file.write_text("http://127.0.0.1:9/v1\n")
    run.env["INSTRUMENT_RUN_ENDPOINT_FILE"] = str(endpoint_file)
    run.skill("demo-skill", settled=(1,))
    run.hold(state="working")
    result = run("demo-skill", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert "kensai.arm=launch-eval-fix" in result.stdout
    assert "--settings" in result.stdout, "a dry run that hides the settings hides what a backgrounded run needs"


# --- the run's provenance (CP-221, CP-227, CP-229, CP-230) -------------------------------------


def test_the_instrument_run_call_carries_the_four_provenance_keys():
    assert_instrument_run_call_carries_provenance(_SCRIPT)


def test_the_telemetry_line_stamps_provider_claude_and_source_default_with_no_model_or_effort(
    run, tmp_path
):
    """The eval-fix workflow run is handed no model and reads no intelligence, so the stamp says
    `default` and names none; the skill= pair it stamped before comes first, unchanged."""
    endpoint_file = tmp_path / "real-instrument-endpoint"
    endpoint_file.write_text("http://127.0.0.1:9/v1\n")
    run.env["INSTRUMENT_RUN_ENDPOINT_FILE"] = str(endpoint_file)
    run.skill("demo-skill", settled=(1,))
    run.hold(state="working")
    result = run("demo-skill", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert "kensai.skill=demo-skill" in result.stdout
    assert_provenance_stamped(result.stdout, provider="claude", source="default", after=("skill",))
    assert "--model" not in result.stdout and "--effort" not in result.stdout
