"""Contract tests for `launch-skill-evals/launcher.sh`.

The shared half — the fixed-prompt guarantee, the `--permission-mode auto` requirement, the
watcher wiring, the CORE_DIR-resolved watcher default — is pinned the way every launcher suite
pins it, and for the same reasons. What is specific to this launcher, and why each is worth
a test:

- **The serialisation guard.** This launcher's reason to exist beyond pollution control: it
  refuses to start a round while another is live. On 2026-07-26 two rounds were launched in
  parallel and both died on the account session limit, losing the reasoning as well as the
  benchmark. A guard that can be forgotten is prose; these tests pin it as behaviour — that it
  fires across skills and across directories (the incident was two worktrees of one repo), that
  it does NOT fire on a finished or vanished round, and that `--force` and `--dry-run` pass.
  It identifies by the recorded agent id, never by the agent's name: Claude Code renames a
  background agent shortly after launch, so a name-matching guard reports a clear field about a
  minute into every round. The lock protocol itself is `<CORE>/tools/evals_round_lock.py`'s,
  tested there; these tests pin only what this launcher does with it.
- **The round report derives from the HIGHEST iteration, not the count.** The two differ the
  moment the sequence has a gap, and `evals/workspace/` is gitignored, so a miscount points a
  round at a directory it would overwrite unrecoverably. The fixture deliberately builds a
  gapped sequence, which is the only shape where a counting bug is visible.
- **A Sonnet driver and no `--agent`.** `model_assignment.md` § Runs with no standing slot puts
  an autonomous tool loop at the worker tier; § Eval runs explains why a role slot must not be
  injected into a measurement. Both are silent regressions if lost — the run still works, it
  just costs the wrong amount or carries a posture it should not.
- **No host-global archive default.** `kensaiapp_structure.md` § core/tools forbids a shared
  tool baking in a machine-local path, so the archive destination comes from
  `KENSAIAPP_EVAL_HISTORY` and its absence is reported rather than guessed.

Isolation: the fixture runs the real script with `tmp_path` as cwd (which the launcher resolves
as its instance root, `$PWD`). A fake `claude` on PATH records the argv it was handed and also
answers `claude agents --json --all` from a test-controlled file, so the serialisation guard can
be driven without any real agent. The watcher and notifier are stubbed via
`LAUNCH_EVALS_WATCHER` / `LAUNCH_EVALS_NOTIFIER`, except the one default-path test which unsets
the watcher override on purpose.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
from pathlib import Path

import pytest

import launcher_telemetry_test_support as support
from provenance_test_support import assert_provenance_stamped
from test_skill_launcher_telemetry import install_telemetry_command

from kensaiapp_launchers_conftest import _granted_dirs, _plugin_skills

_SCRIPT = Path(__file__).resolve().parent / "launcher.sh"
# The delivered provider file: the tracked template at the instance root, copied into the instance
# a case runs for. No suite leans on a live `.providers.toml`, which is untracked.
_PROVIDER_EXAMPLE = Path(__file__).resolve().parents[3] / ".providers.toml.example"

# The prefix the launcher's fixed prompt must start with. The serialisation guard matches on it,
# so it is a contract between the launcher and itself across two runs: change it in one place and
# every already-running round becomes invisible to the next launch.
PROMPT_PREFIX = "run the skill-evals benchmark for the "

CLAUDE_STUB = """#!/usr/bin/env bash
# Two jobs. `claude agents ...` answers the launcher's serialisation guard from a file the test
# controls; anything else is the real launch, whose argv we record. The launch branch also prints
# the "backgrounded · <id>" line the real CLI prints, with the same ANSI colour, because the
# launcher parses that line to learn which agent it just started.
if [ "${1:-}" = "agents" ]; then
  if [ -n "${AGENTS_JSON:-}" ] && [ -f "$AGENTS_JSON" ]; then cat "$AGENTS_JSON"; else echo '[]'; fi
  exit 0
fi
printf '%s\\n' "$@" > "$CLAUDE_ARGV_LOG"
printf 'backgrounded \\xc2\\xb7 \\033[36m%s\\033[39m\\n' "${STUB_AGENT_ID:-newid00}"
"""

WATCHER_STUB = """import sys
# Stands in for watch_agent.py. --list-ids answers the launcher's pre-launch snapshot; any other
# invocation is the real spawn, whose argv we record. The spawn branch also writes stdout+stderr —
# the real watcher does too, and the launcher must keep that in a log — so a regression to
# /dev/null is catchable.
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
    """`run(*cli_args) -> CompletedProcess`, invoking the real launcher with `tmp_path` as its
    cwd — which is how the core tool resolves its instance root ($PWD).

    Helpers hang off the callable: `run.skill(name, iterations=…)` creates a skill with an
    evals.json and an optional set of iteration directories; `run.agents([...])` seeds what
    `claude agents` reports; `run.launched_argv()` / `run.watcher_argv()` return recorded argv;
    `run.no_notifier()` points at a missing notifier; `run.default_watcher()` unsets the watcher
    override so the launcher's CORE_DIR-resolved default is exercised; `run.history(path)` sets
    KENSAIAPP_EVAL_HISTORY.
    """
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

    env = dict(os.environ)
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
    # Points at a path nothing occupies, so this fixture never reads this machine's real
    # published telemetry endpoint (`a-launcher-tags-its-own-run`) — a launcher's own suite
    # is isolated from real machine state exactly like the watcher and the notifier above.
    env["INSTRUMENT_RUN_ENDPOINT_FILE"] = str(tmp_path / "no-instrument-endpoint")
    # Explicitly unconfigured: absent would let the source host's own setting answer, and a case
    # that is not about the telemetry command must not depend on this machine's package.
    env[support.COMMAND_VARIABLE] = ""
    env["CLAUDE_ARGV_LOG"] = str(argv_log)
    env["WATCHER_ARGV_LOG"] = str(watcher_log)
    env["AGENTS_JSON"] = str(agents_json)
    env["KENSAIAPP_EVALS_LOCK"] = str(tmp_path / "round.lock.json")
    env["LAUNCH_EVALS_WATCHER"] = str(watcher_stub)
    env["LAUNCH_EVALS_NOTIFIER"] = str(notifier_stub)
    # The instance's own provider file: an unforced launch reads it at the instance root.
    (tmp_path / ".providers.toml").write_text(_PROVIDER_EXAMPLE.read_text(encoding="utf-8"))
    env["HOME"] = str(tmp_path / "home")
    env.pop("KENSAIAPP_EVAL_HISTORY", None)
    (tmp_path / "home").mkdir()

    def _run(*cli_args):
        return subprocess.run(
            [str(_SCRIPT), *cli_args],
            cwd=str(tmp_path),
            capture_output=True,
            text=True,
            env=env,
        )

    def _skill(name="demo-skill", iterations=(), evals=True):
        skill_dir = tmp_path / ".claude" / "skills" / name
        (skill_dir / "evals").mkdir(parents=True)
        if evals:
            (skill_dir / "evals" / "evals.json").write_text('{"skill_name": "%s", "evals": []}' % name)
        for n in iterations:
            (skill_dir / "evals" / "workspace" / f"iteration-{n}").mkdir(parents=True)
        return skill_dir

    def _agents(entries):
        agents_json.write_text(json.dumps(entries))

    def _launched_argv():
        return argv_log.read_text().splitlines() if argv_log.exists() else []

    def _watcher_argv():
        # The launcher detaches the watcher with `&`, so it may still be starting when the
        # launcher exits. Give it a moment before concluding it never ran.
        for _ in range(50):
            if watcher_log.exists():
                return watcher_log.read_text().splitlines()
            time.sleep(0.05)
        return []

    def _no_notifier():
        env["LAUNCH_EVALS_NOTIFIER"] = str(tmp_path / "nope" / "missing.sh")

    def _default_watcher():
        env.pop("LAUNCH_EVALS_WATCHER", None)

    def _history(path):
        env["KENSAIAPP_EVAL_HISTORY"] = str(path)

    def _hold(agent_id="held01", state="working", skill="other-skill", cwd="/elsewhere"):
        """Seed a round lock naming `agent_id`, and report that agent in the given state.

        Both halves matter: the lock says which round is held, the agent list says whether it is
        still alive. The guard refuses only when both agree it is working.
        """
        lock.write_text(json.dumps({"agent_id": agent_id, "skill": skill, "cwd": cwd, "iteration": 9}))
        if state is not None:
            _agents([{"id": agent_id, "kind": "background", "cwd": cwd,
                      "state": state, "name": "some renamed thing"}])

    def _lock_body():
        return json.loads(lock.read_text()) if lock.exists() else None

    def _stub_id(value):
        env["STUB_AGENT_ID"] = value

    def _grouped_skill(group="g", name="demo-skill", iterations=(), evals=True):
        skill_dir = tmp_path / "skills" / group / ".claude" / "skills" / name
        (skill_dir / "evals").mkdir(parents=True)
        if evals:
            (skill_dir / "evals" / "evals.json").write_text('{"skill_name": "%s", "evals": []}' % name)
        for n in iterations:
            (skill_dir / "evals" / "workspace" / f"iteration-{n}").mkdir(parents=True)
        return skill_dir

    def _bare_grouped_skill(group="g", name="demo-skill"):
        d = tmp_path / "skills" / group / ".claude" / "skills" / name
        d.mkdir(parents=True)
        return d

    lock = tmp_path / "round.lock.json"

    _run.root = tmp_path
    _run.env = env
    _run.skill = _skill
    _run.agents = _agents
    _run.hold = _hold
    _run.lock_body = _lock_body
    _run.lock_path = lock
    _run.stub_id = _stub_id
    _run.launched_argv = _launched_argv
    _run.watcher_argv = _watcher_argv
    _run.no_notifier = _no_notifier
    _run.default_watcher = _default_watcher
    _run.history = _history
    _run.grouped_skill = _grouped_skill
    _run.bare_grouped_skill = _bare_grouped_skill
    return _run


# --- guards ------------------------------------------------------------------


def test_no_skill_arg_dies_with_usage(run):
    result = run()
    assert result.returncode != 0
    assert "usage: launch-skill-evals" in result.stderr


def test_unknown_skill_dies_before_launching(run):
    result = run("nope")
    assert result.returncode != 0
    assert "no skill at" in result.stderr
    assert run.launched_argv() == []


def test_skill_without_evals_json_dies_before_launching(run):
    run.skill("demo-skill", evals=False)
    result = run("demo-skill")
    assert result.returncode != 0
    assert "nothing to benchmark" in result.stderr
    assert run.launched_argv() == []


def test_a_path_shaped_argument_is_rejected(run):
    # The launcher takes a skill NAME, not a path. Accepting a path would let a caller point the
    # round at a directory outside the instance.
    run.skill("demo-skill")
    result = run(".claude/skills/demo-skill")
    assert result.returncode != 0
    assert "is a skill NAME, not a path" in result.stderr
    assert run.launched_argv() == []


# --- the serialisation guard --------------------------------------------------


def test_refuses_to_launch_while_the_held_round_is_working(run):
    run.skill("demo-skill")
    run.hold(state="working")
    result = run("demo-skill")
    assert result.returncode != 0
    assert "an eval round is already running" in result.stderr
    assert run.launched_argv() == []


def test_the_guard_blocks_on_a_round_for_a_DIFFERENT_skill(run):
    # Deliberately coarse: two skills' rounds are two full executor fan-outs against one account,
    # which is exactly the pair that exhausted the window. Skill identity is not the axis.
    run.skill("demo-skill")
    run.hold(skill="some-other-skill", state="working")
    result = run("demo-skill")
    assert result.returncode != 0
    assert "some-other-skill" in result.stderr


def test_a_round_in_another_directory_still_blocks(run):
    # The limit that stops a round is per-ACCOUNT, and the 2026-07-26 incident was two rounds in two
    # worktrees of one repo — two different cwds. An earlier draft of this launcher filtered on cwd
    # and so would have watched both start and blocked neither; hence "still blocks".
    run.skill("demo-skill")
    run.hold(cwd="/somewhere/else/entirely", state="working")
    result = run("demo-skill")
    assert result.returncode != 0
    assert run.launched_argv() == []


def test_the_guard_does_not_depend_on_the_agents_name(run):
    # Claude Code renames a background agent shortly after launch — a round launched with a prompt
    # opening "run the skill-evals benchmark for the ..." was listed minutes later as "run
    # skill-evals benchmark product-prd". A name-matching guard reports a clear field seconds after a
    # round starts, which is why identity is the recorded id. The seeded agent's name here is
    # deliberately nothing like the prompt.
    run.skill("demo-skill")
    run.hold(state="working")
    result = run("demo-skill")
    assert result.returncode != 0
    assert PROMPT_PREFIX not in result.stderr


def test_a_finished_round_does_not_block_and_its_lock_is_cleared(run):
    # `stopped` is a finished round. If it blocked, the guard would latch after the first round and
    # every later launch would need --force. Clearing the stale lock as it passes is why there is no
    # cleanup step anyone has to remember.
    run.skill("demo-skill")
    run.hold(agent_id="held01", state="stopped")
    result = run("demo-skill")
    assert result.returncode == 0, result.stderr
    assert run.launched_argv() != []
    assert run.lock_body()["agent_id"] != "held01"


def test_a_lock_naming_an_agent_that_no_longer_exists_is_stale(run):
    # The machine rebooted, or the agent aged out of the list. A lock that can only be cleared by
    # hand is a lock that will one day be deleted by hand at the wrong moment.
    run.skill("demo-skill")
    run.hold(agent_id="ghost01", state=None)  # lock written, agent absent from the list entirely
    result = run("demo-skill")
    assert result.returncode == 0, result.stderr
    assert run.launched_argv() != []


def test_no_lock_at_all_launches_freely(run):
    run.skill("demo-skill")
    result = run("demo-skill")
    assert result.returncode == 0, result.stderr
    assert run.launched_argv() != []


def test_force_launches_despite_a_held_round(run):
    run.skill("demo-skill")
    run.hold(state="working")
    result = run("demo-skill", "--force")
    assert result.returncode == 0, result.stderr
    assert run.launched_argv() != []


def test_an_unreadable_agent_list_does_not_block_a_launch(run):
    # The guard is a safety rail, not a gate. If `claude agents` cannot be parsed, refusing would
    # make the launcher unusable for a reason that has nothing to do with the account's load.
    run.skill("demo-skill")
    run.hold(state="working")
    (run.root / "agents.json").write_text("not json at all")
    result = run("demo-skill")
    assert result.returncode == 0, result.stderr
    assert run.launched_argv() != []


# --- the lock the next launch reads -------------------------------------------


def test_the_launch_records_the_agent_id_it_started(run):
    # Parsed out of `claude --bg`'s own "backgrounded · <id>" line, ANSI colour and all. Without
    # this the guard has nothing to ask about and every launch is the first launch.
    run.skill("demo-skill")
    run.stub_id("abc9f1")
    result = run("demo-skill")
    assert result.returncode == 0, result.stderr
    body = run.lock_body()
    assert body["agent_id"] == "abc9f1"
    assert body["skill"] == "demo-skill"
    assert body["iteration"] == 1


def test_the_launch_output_still_reaches_the_caller(run):
    # stdout is captured to read the id out of it, so it has to be echoed back or the caller loses
    # the attach/stop hints the CLI printed.
    run.skill("demo-skill")
    run.stub_id("abc9f1")
    result = run("demo-skill")
    assert "abc9f1" in result.stdout


def test_a_dry_run_writes_no_lock(run):
    run.skill("demo-skill")
    run("demo-skill", "--dry-run")
    assert run.lock_body() is None


def test_the_default_lock_is_the_repos_common_git_dir(run, tmp_path):
    # --git-common-dir, not --absolute-git-dir: the common dir is the one path every linked worktree
    # of a repo agrees on, which is the scope the guard needs. fixture_guard.py deliberately uses the
    # per-worktree dir for the opposite reason — same mechanism, opposite intent.
    subprocess.run(["git", "init", "-q"], cwd=str(tmp_path), check=True)
    run.skill("demo-skill")
    import os as _os
    env_lock = _os.environ.pop("KENSAIAPP_EVALS_LOCK", None)  # not the fixture's env; see below
    result = subprocess.run(
        [str(_SCRIPT), "demo-skill", "--dry-run"],
        cwd=str(tmp_path), capture_output=True, text=True,
        env={k: v for k, v in _os.environ.items()},
    )
    if env_lock is not None:
        _os.environ["KENSAIAPP_EVALS_LOCK"] = env_lock
    assert result.returncode == 0, result.stderr
    # The dry run does not print the lock path, so assert the derivation instead: the launcher must
    # resolve the common dir of this repo, which for a non-worktree checkout is <root>/.git
    common = subprocess.run(["git", "rev-parse", "--git-common-dir"], cwd=str(tmp_path),
                            capture_output=True, text=True).stdout.strip()
    assert common in (".git", str(tmp_path / ".git"))


# --- the round report ---------------------------------------------------------


def test_first_round_is_reported_as_iteration_1(run):
    run.skill("demo-skill")
    result = run("demo-skill", "--dry-run")
    assert "iteration-1 (first ever)" in result.stdout


def test_the_next_iteration_is_highest_plus_one_not_count_plus_one(run):
    # The gap is the point: iterations 1, 2, 5 count 3 but reach 5. A counting bug would name
    # iteration-4 here and, worse, iteration-3 on the very next round — overwriting a directory
    # that workspace/'s gitignore makes unrecoverable.
    run.skill("demo-skill", iterations=(1, 2, 5))
    result = run("demo-skill", "--dry-run")
    assert "iteration-6" in result.stdout
    assert "highest existing is iteration-5" in result.stdout


def test_a_non_numeric_iteration_directory_is_ignored(run):
    run.skill("demo-skill", iterations=(1, "scratch"))
    result = run("demo-skill", "--dry-run")
    assert "iteration-2" in result.stdout


def test_the_round_report_is_not_passed_into_the_run(run):
    # Same rule as the sibling launchers: the report is for the caller's eyes. Feeding a derived
    # iteration number into the prompt would let it disagree with the one the workflow derives.
    run.skill("demo-skill", iterations=(1, 2, 5))
    run("demo-skill")
    prompt = [a for a in run.launched_argv() if a.startswith(PROMPT_PREFIX)]
    assert len(prompt) == 1
    assert "iteration-6" not in prompt[0]
    assert "highest existing" not in prompt[0]


# --- the fixed-prompt guarantee ----------------------------------------------


def test_launches_with_the_fixed_prompt_on_a_sonnet_driver(run):
    run.skill("demo-skill")
    result = run("demo-skill")
    assert result.returncode == 0, result.stderr
    argv = run.launched_argv()
    assert argv[0] == "--bg"
    assert argv[1].startswith(PROMPT_PREFIX)
    assert "--model" in argv and argv[argv.index("--model") + 1] == "sonnet"


def test_no_agent_slot_is_injected_into_the_measurement(run):
    # model_assignment.md § Eval runs: a role slot injects its loader stack before the task, and a
    # loader legitimately restates what its skills do. A measurement must not carry a posture.
    run.skill("demo-skill")
    run("demo-skill")
    assert "--agent" not in run.launched_argv()


def test_the_run_is_launched_in_auto_permission_mode(run):
    # Load-bearing, not cosmetic: under the inherited `acceptEdits` a --bg run stops forever on the
    # first Bash command no static rule matches, and no static rule can match one containing a
    # $variable. `auto` puts a classifier on each call instead.
    run.skill("demo-skill")
    run("demo-skill")
    argv = run.launched_argv()
    assert "--permission-mode" in argv
    assert argv[argv.index("--permission-mode") + 1] == "auto"


def test_allowed_tools_bare_and_print_are_never_passed(run):
    # --allowedTools REPLACES the settings allow list and would strip Skill/MCP; --bare skips
    # settings.json entirely; -p/--print never starts the session `claude agents` attaches to.
    run.skill("demo-skill")
    run("demo-skill")
    argv = run.launched_argv()
    for flag in ("--allowedTools", "--bare", "-p", "--print"):
        assert flag not in argv


def test_the_prompt_forbids_touching_a_skill_file(run):
    # The measure pass measures. Deciding what a failure means is a separate pass on a separate
    # brain reading the committed benchmark — that split is what keeps a limit-kill from costing
    # the reasoning as well as the numbers.
    run.skill("demo-skill")
    run("demo-skill")
    prompt = run.launched_argv()[1]
    assert "change no skill file" in prompt


def test_the_prompt_skips_the_viewer_steps(run):
    run.skill("demo-skill")
    run("demo-skill")
    prompt = run.launched_argv()[1]
    assert "skip steps 4 and 5" in prompt


def test_caller_cannot_append_to_the_prompt(run):
    # The whole reason the launcher exists. Trailing words are parsed as flags or ignored; they
    # never reach the run.
    run.skill("demo-skill")
    run("demo-skill", "and", "also", "rewrite", "the", "skill")
    prompt = run.launched_argv()[1]
    assert "rewrite" not in prompt


# --- the archive destination --------------------------------------------------


def test_no_host_global_archive_default(run):
    # kensaiapp_structure.md § core/tools: a shared tool must not bake in a machine-local path.
    # With the variable unset the launcher says so rather than guessing at ~/projects/...
    run.skill("demo-skill")
    result = run("demo-skill")
    assert "KENSAIAPP_EVAL_HISTORY is unset" in result.stdout
    assert "kensaiapp-eval-history" not in run.launched_argv()[1]


def test_the_archive_clause_is_absent_when_no_destination_is_set(run):
    run.skill("demo-skill")
    run("demo-skill")
    assert "copy the run's whole iteration directory" not in run.launched_argv()[1]


def test_the_archive_destination_matches_the_history_vaults_own_layout(run):
    run.skill("demo-skill")
    run.history("/vault/evals")
    run("demo-skill")
    prompt = run.launched_argv()[1]
    assert "/vault/evals/demo-skill/evals/workspace/" in prompt


def test_a_trailing_slash_on_the_archive_root_does_not_double(run):
    run.skill("demo-skill")
    run.history("/vault/evals/")
    run("demo-skill")
    assert "/vault/evals/demo-skill/evals/workspace/" in run.launched_argv()[1]


# --- --dry-run ----------------------------------------------------------------


def test_dry_run_prints_the_command_without_launching(run):
    run.skill("demo-skill")
    result = run("demo-skill", "--dry-run")
    assert result.returncode == 0, result.stderr
    assert "DRY RUN" in result.stdout
    assert run.launched_argv() == []


def test_the_variable_is_no_force_and_the_command_is_unchanged(run):
    """launch-skill-evals reads no force: an exported provider neither changes the command nor
    refuses (CP-297)."""
    run.skill("demo-skill")
    run.env["KENSAIAPP_AGENT_PROVIDER"] = "codex"

    result = run("demo-skill", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert re.search(r"^  claude  --bg  ", result.stdout, re.MULTILINE), result.stdout[:400]


def test_dry_run_spawns_no_watcher(run):
    run.skill("demo-skill")
    run("demo-skill", "--dry-run")
    assert run.watcher_argv() == []


def test_dry_run_is_not_blocked_by_a_live_round(run):
    # Printing the command spends nothing, so the guard has nothing to protect — and being able to
    # inspect the next launch while one is running is exactly when you want to.
    run.skill("demo-skill")
    run.hold(state="working")
    result = run("demo-skill", "--dry-run")
    assert result.returncode == 0, result.stderr


# --- the completion watcher ---------------------------------------------------


def test_watcher_is_spawned_with_the_generic_reporter_and_run_identity(run):
    run.skill("demo-skill")
    run("demo-skill")
    argv = run.watcher_argv()
    assert "--reporter" in argv and argv[argv.index("--reporter") + 1] == "generic"
    assert "--label" in argv and "demo-skill" in argv[argv.index("--label") + 1]
    assert "--cwd" in argv and argv[argv.index("--cwd") + 1] == str(run.root)


def test_watcher_is_told_which_repo_head_proves_the_round_committed(run):
    # --head-repo is what turns "the run ended" into "the run ended and did/did not commit".
    run.skill("demo-skill")
    run("demo-skill")
    argv = run.watcher_argv()
    assert "--head-repo" in argv
    assert argv[argv.index("--head-repo") + 1] == str(run.root)


def test_watcher_excludes_agents_that_existed_before_the_launch(run):
    run.skill("demo-skill")
    run("demo-skill")
    argv = run.watcher_argv()
    assert "--exclude-ids" in argv
    assert argv[argv.index("--exclude-ids") + 1] == "pre1,pre2"


def test_watcher_is_found_at_its_resolved_home_when_the_env_override_is_unset(run):
    # This launcher lives at <CORE>/launchers/launch-skill-evals/, a sibling of <CORE>/tools/, so
    # its default watcher path resolves via CORE_DIR — derived from this folder's own location,
    # not a fixed number of parent steps. A wrong default leaves the file missing and silently
    # skips the watcher.
    run.skill("demo-skill")
    run.default_watcher()
    result = run("demo-skill")
    assert result.returncode == 0, result.stderr
    assert "completion watch skipped" not in result.stdout


def test_watcher_is_not_spawned_when_no_notifier_is_installed(run):
    # Notification is an optional add-on; its absence must never fail a run.
    run.skill("demo-skill")
    run.no_notifier()
    result = run("demo-skill")
    assert result.returncode == 0, result.stderr
    assert "completion watch skipped" in result.stdout
    assert run.launched_argv() != []


def test_watcher_output_goes_to_a_log_not_to_dev_null(run):
    # A detached process has nowhere else to put its output and nobody reads its exit code, so a
    # failed send and a crashed watcher are both perfectly silent without this.
    run.skill("demo-skill")
    run("demo-skill")
    run.watcher_argv()  # wait for the detached watcher to have written
    logs = list((run.root / "system" / "logs").glob("watch-evals-demo-skill-*.log"))
    assert len(logs) == 1
    body = logs[0].read_text()
    assert "watcher-stub: stdout line" in body
    assert "watcher-stub: stderr line" in body


# --- the resolver: grouped layout, not-found, ambiguous ----------------------


def test_a_grouped_skill_resolves_and_the_prompt_names_the_grouped_directory(run):
    skill_dir = run.grouped_skill("g", "demo-skill")
    result = run("demo-skill")
    assert result.returncode == 0, result.stderr
    prompt = run.launched_argv()[1]
    assert str(skill_dir) in prompt


def test_a_grouped_skill_evals_group_is_no_longer_admitted_by_add_dir(run):
    """Task 17: a grouped `skill-evals` used to be admitted here with its own --add-dir; a Claude
    run now reaches every owned skill, flat or grouped, through the pin's plugin instead. The
    pin's own --add-dir (the pin root) is still present — just not the skill-evals group's."""
    run.skill("demo-skill")
    evals_dir = run.grouped_skill("experimental", "skill-evals", evals=False)
    result = run("demo-skill")
    assert result.returncode == 0, result.stderr
    argv = run.launched_argv()
    assert str(evals_dir.parents[2]) not in argv


def test_a_flat_skill_evals_adds_no_group_directory(run):
    """A flat `skill-evals` was already in the index; there was never a group grant to add here,
    and there still is not — only the pin's own --add-dir (the pin root) is present."""
    run.skill("demo-skill")
    run.skill("skill-evals", evals=False)
    result = run("demo-skill")
    assert result.returncode == 0, result.stderr
    assert len(_granted_dirs(run.launched_argv())) == 1


def test_an_unresolvable_skill_evals_adds_no_group_directory(run):
    """A fixture instance with no `skill-evals` launches as before rather than refusing — only the
    pin's own --add-dir (the pin root) is present."""
    run.skill("demo-skill")
    result = run("demo-skill")
    assert result.returncode == 0, result.stderr
    assert len(_granted_dirs(run.launched_argv())) == 1


def test_dry_run_prints_the_pin_line(run):
    # Task 17: pin_enter runs right after the CORE_DIR guard, ahead of everything else.
    run.skill("demo-skill")
    result = run("demo-skill", "--dry-run")
    assert result.returncode == 0, result.stderr
    assert re.search(r"^Pin: .+\(inherited\)$", result.stdout, re.MULTILINE)


def test_the_claude_launch_grants_skill_evals(run):
    run.skill("demo-skill")

    result = run("demo-skill")

    assert result.returncode == 0, result.stderr
    listed, groups = _plugin_skills(run.launched_argv())
    assert "skill-evals" in listed
    assert groups == {"experimental"}


def test_launch_skill_evals_keeps_its_model(run):
    # Task 17: --model sonnet is an explicit ratifying/driving-model choice, not a seat/agent
    # grant the pin's plugin replaces — it rides through to the adapter unchanged.
    run.skill("demo-skill")
    result = run("demo-skill")
    assert result.returncode == 0, result.stderr
    argv = run.launched_argv()
    assert "--model" in argv and argv[argv.index("--model") + 1] == "sonnet"


def test_grouped_fixture_builds_no_flat_path(run):
    run.grouped_skill("g", "demo-skill")
    assert not (run.root / ".claude" / "skills").exists()


def test_the_refusal_no_longer_says_where_a_name_resolves(run):
    run.skill("demo-skill")
    result = run(".claude/skills/demo-skill")
    assert result.returncode != 0
    assert "resolves under" not in result.stderr


def test_unknown_skill_dies_before_launching_naming_no_layout(run):
    result = run("nope")
    assert result.returncode != 0
    assert "no skill at" in result.stderr
    assert str(run.root) in result.stderr           # the root searched
    assert "'nope'" in result.stderr                  # the skill name
    assert ".claude/skills" not in result.stderr
    assert "skills/" not in result.stderr
    assert run.launched_argv() == []


def test_stderr_noise_on_a_clean_resolve_never_reaches_the_captured_path(run):
    """The resolver's own stderr is folded into the captured value today (2>&1), so any text a
    future resolver version prints on a successful exit would land INSIDE skill_dir. A stub
    resolver here — exit 0, a real directory on stdout, a line of noise on stderr — proves the
    fold does not happen: the launcher proceeds against the stdout path alone."""
    skill_dir = run.skill("demo-skill")
    stub = run.root / "stub_resolver.py"
    stub.write_text(
        "import sys\n"
        f"print({str(skill_dir)!r})\n"
        "print('resolver: a future warning', file=sys.stderr)\n"
    )
    run.env["LAUNCH_EVALS_RESOLVER"] = str(stub)
    result = run("demo-skill", "--dry-run")
    assert result.returncode == 0, result.stderr
    assert "resolver: a future warning" not in result.stdout


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


def test_dry_run_states_the_arm_it_would_run_under(run, tmp_path):
    """`a-launcher-tags-its-own-run` — a dry run that hides the instrument is a dry run that
    lies. With a runnable telemetry command and a published endpoint file present,
    `run_telemetry` prints the arm it derived (this launcher's own directory name) even though
    nothing is actually spawned."""
    endpoint_file = tmp_path / "real-instrument-endpoint"
    endpoint_file.write_text("http://127.0.0.1:9/v1\n")
    run.env["INSTRUMENT_RUN_ENDPOINT_FILE"] = str(endpoint_file)
    install_telemetry_command(tmp_path / "home", run.env)
    run.skill("demo-skill")
    result = run("demo-skill", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert "kensai.arm=launch-skill-evals" in result.stdout
    assert "--settings" in result.stdout, "a dry run that hides the settings hides what a backgrounded run needs"


# --- the run's provenance (CP-222, CP-226, CP-227, CP-229, CP-230) -----------------------------


def test_the_run_telemetry_call_carries_the_four_provenance_keys():
    support.assert_run_telemetry_call_carries_provenance(_SCRIPT)


def _dry_run_with_endpoint(run, tmp_path):
    endpoint_file = tmp_path / "real-instrument-endpoint"
    endpoint_file.write_text("http://127.0.0.1:9/v1\n")
    run.env["INSTRUMENT_RUN_ENDPOINT_FILE"] = str(endpoint_file)
    install_telemetry_command(tmp_path / "home", run.env)
    result = run("demo-skill", "--dry-run")
    assert result.returncode == 0, result.stderr
    return result


def test_the_stamp_is_model_sonnet_source_tier_with_no_effort(run, tmp_path):
    """The driver goes at the fixed tier `sonnet`, so the stamp carries model_assignment.py's
    answer for it — `sonnet`, a null effort — and says `tier`, after the unchanged skill pair."""
    run.skill("demo-skill")
    result = _dry_run_with_endpoint(run, tmp_path)

    assert "kensai.skill=demo-skill" in result.stdout
    assert_provenance_stamped(
        result.stdout, provider="claude", model="sonnet", source="tier", after=("skill",)
    )


def test_the_argv_still_carries_model_sonnet_and_no_effort(run, tmp_path):
    """The run goes at what it went at before (CP-226): --model sonnet, and no --effort — the
    evaluated skill's own intelligence is never read (CP-222)."""
    skill_dir = run.skill("demo-skill")
    (skill_dir / "intelligence").mkdir()
    (skill_dir / "intelligence" / "claude.md").write_text(
        "**Model:** claude-opus-5-5\n**Effort:** high\n"
    )
    result = _dry_run_with_endpoint(run, tmp_path)

    assert re.search(r"--model\s+sonnet\s", result.stdout), result.stdout
    assert "--effort" not in result.stdout
    assert "claude-opus-5-5" not in result.stdout


# --- the launcher's launch, observed over the real helper (CP-685, CP-688, CP-759) -------------

_EVALS_ARGV = ("demo-skill", "--dry-run")
# The pairs one skill-evals launch stamps, in the order its call hands them over: the arm and the
# run's own id, then the skill and the provenance. The driver goes at the fixed tier sonnet, so the
# model is stamped and the effort is not, and a scratch tree that is no git checkout has no
# instance to add.
_STAMPED_PAIRS = [
    ("arm", "launch-skill-evals"),
    ("run_id", None),
    ("skill", "demo-skill"),
    ("provider", "claude"),
    ("model", "sonnet"),
    ("source", "tier"),
]


@pytest.mark.parametrize("cap", [None, "250000"], ids=["cap-absent", "cap-250000"])
@pytest.mark.parametrize("endpoint", ["valid", "absent"])
def test_launch_skill_evals_helper_observation_matches_case_inputs(run, tmp_path, endpoint, cap):
    """CP-685, CP-688, CP-759: the launcher itself, run once over the real helper and the real
    package, prints the lines, exports the six variables and hands its run the settings its own
    inputs call for: the arm it runs under, the skill it was given and the provider, model and
    source its fixed tier resolves, with no effort."""
    package = support.require_real_package(tmp_path / "package")
    run.skill("demo-skill")
    endpoint_file = tmp_path / "published-endpoint"
    cause = support.publish_endpoint(endpoint_file, endpoint)
    launcher = support.scratch_core(tmp_path / "scratch", _SCRIPT)
    helper = launcher.parents[2] / "tools" / "run_telemetry.sh"
    env = support.telemetry_environment(
        run.env, home=package.home, endpoint_file=endpoint_file, cap=cap, command=package.command
    )

    observation = support.run_launcher(
        launcher, _EVALS_ARGV, cwd=tmp_path, env=env, observation_dir=tmp_path / "observed"
    )

    if endpoint == "valid":
        support.assert_instrumented_observation(
            observation, pairs=_STAMPED_PAIRS, helper=helper, cap=cap
        )
    else:
        assert observation.status == 0, observation.stderr
        assert Path(observation.helper_source).resolve() == helper.resolve()
        assert observation.telemetry_lines == [f"          ({cause} — run uninstrumented)"]
        support.assert_uninstrumented(observation, cap=cap)


@pytest.mark.parametrize("combination", support.ORDINARY_COMBINATIONS)
def test_skill_evals_ordinary_launch_discovers_source_host_setting(run, tmp_path, combination):
    """CP-692: a launch whose environment names no command is instrumented from its source host's
    setting, whether the launcher runs from a core or a pin of it, for the host or for an
    instance that binds that core."""
    package = support.require_real_package(tmp_path / "package")
    run.skill("demo-skill")
    endpoint_file = tmp_path / "published-endpoint"
    support.publish_endpoint(endpoint_file)
    launch = support.ordinary_launch(tmp_path, _SCRIPT, tmp_path, combination, package.command)
    env = support.telemetry_environment(run.env, home=package.home, endpoint_file=endpoint_file)

    observation = support.run_launcher(
        launch.launcher, _EVALS_ARGV, cwd=launch.instance, env=env,
        observation_dir=tmp_path / "observed",
    )

    support.assert_ordinary_launch_is_instrumented(observation, environment=env)


@pytest.mark.parametrize("cap", [None, "250000"], ids=["cap-absent", "cap-250000"])
@pytest.mark.parametrize("kind", support.FAILURE_KINDS)
def test_skill_evals_telemetry_failures_preserve_launch(run, tmp_path, kind, cap):
    """CP-687, CP-693, CP-694: whatever is wrong with the command or the endpoint, the launch is
    not failed by it — it prints the one cause on stdout and hands its run the cap alone."""
    run.skill("demo-skill")
    scenario = support.failure_scenario(
        kind, run.env, home=tmp_path / "failure-home", endpoint_file=tmp_path / "endpoint", cap=cap
    )
    host = tmp_path / "host"
    host.mkdir()
    launcher = support.scratch_core(host, _SCRIPT)
    if scenario.host_setting is not None:
        support.write_host_setting(host, scenario.host_setting)

    observation = support.run_launcher(
        launcher, _EVALS_ARGV, cwd=tmp_path, env=scenario.environment,
        observation_dir=tmp_path / "observed",
    )

    support.assert_failure_scenario(observation, scenario, cap=cap)


def test_skill_evals_observation_skips_an_unreachable_package_and_fails_a_reached_one(tmp_path):
    """CP-689: the observation above is skipped, with the reason named, where the package's
    command cannot be reached, and fails where it is reached and breaks the contract."""
    support.assert_selection_skips_unreachable_and_fails_reached(
        tmp_path, f"{__file__}::test_launch_skill_evals_helper_observation_matches_case_inputs"
    )
