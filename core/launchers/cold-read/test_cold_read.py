"""Contract tests for the `cold-read` launcher (`<CORE>/launchers/cold-read/launcher.sh`).

One command opens the blind cold reads over a skill's producing stack, then stops: N+1 concurrent
`kensaiapp-auditor` runs (one per substance file in the skill's `stack.json`, plus one seam reader
when there is more than one file), each writing and committing its own report. No fixing, no loop —
see `docs/proposals/cold-read-launcher/ad_hoc_plan.md` for the full design.

Sections mirror the plan's tasks:
  - Task 1 — argument surface, derivations, guards, `--dry-run`
  - Task 2 — the three fixed prompts (per-file scope adaptation, seam narrowness, commit + retry)
  - Task 3 — launch, per-reader watchers, `--keep-awake`
  - Task 4 — the concurrent-commit hazard, proven against the real `commit_builder.py`

Isolation, as in the sibling launcher suites: the real script runs with `tmp_path` as its
cwd (the launcher resolves that as `$PWD`, its instance root). A fake `claude` on `PATH` records the
argv of EACH invocation to its own file (the launcher fires N+1 sequential `claude --bg` calls, so a
single overwrite-log like the single-command launchers use would lose all but the last); the watcher
and notifier are stubbed via `LAUNCH_COLD_READ_WATCHER` / `LAUNCH_COLD_READ_NOTIFIER`, except the one
default-path test which unsets the watcher override on purpose. Task 4's tests need no launcher at
all — they invoke the real `commit_builder.py` against a throwaway git repo.
"""

from __future__ import annotations

import itertools
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import pytest

from path_test_support import path_without_caffeinate as _path_without_caffeinate
from provenance_test_support import (
    assert_instrument_run_call_carries_provenance,
    assert_provenance_stamped,
)

_SCRIPT = Path(__file__).resolve().parent / "launcher.sh"
# The delivered provider file: the tracked template at the instance root, copied into the instance
# a case runs for. No suite leans on a live `.providers.toml`, which is untracked.
_PROVIDER_EXAMPLE = Path(__file__).resolve().parents[3] / ".providers.toml.example"
_COMMIT_BUILDER = Path(__file__).resolve().parents[2] / "tools" / "commit_builder.py"

CLAUDE_STUB = """#!/usr/bin/env bash
# Records the argv of EACH invocation to its own file under $CLAUDE_ARGV_DIR (the launcher fires
# several sequential `claude --bg` calls, one per reader) and forks a detached sleeper before
# returning — the way the real CLI returns fast under --bg while the actual agent keeps running —
# so a test can prove the launcher does not block waiting on it. Each invocation's argv is written
# NUL-separated (not newline-separated) — a prompt argument is a multi-paragraph string carrying its
# own embedded newlines, so a newline-joined log would be ambiguous about where one argv token ends
# and the next begins.
n=$(ls "$CLAUDE_ARGV_DIR" 2>/dev/null | wc -l | tr -d ' ')
printf '%s\\0' "$@" > "$CLAUDE_ARGV_DIR/call-$n.argv"
[ -n "${SEQ_LOG:-}" ] && echo "claude" >> "$SEQ_LOG"
# The launch line the real CLI prints, ANSI-wrapped exactly as it wraps it even when stdout is
# not a TTY, and carrying a DISTINCT id per call — this launcher fans out, and an id that were
# the same for every reader would let a broken handover pass.
printf '\\033[2m  \\342\\216\\277  backgrounded \\302\\267 \\033[0mbg-id-%s\\033[0m\\n' "$n"
# The run it leaves behind lasts 2s — or, when $CLAUDE_RUN_RELEASE names a file, until that file
# exists (capped at 60s so a test that never releases leaves nothing behind for long). The release
# form lets a test prove the launcher does not wait on a run without timing it.
if [ -n "${CLAUDE_RUN_RELEASE:-}" ]; then
  ( i=0; while [ ! -e "$CLAUDE_RUN_RELEASE" ] && [ "$i" -lt 1200 ]; do sleep 0.05; i=$((i + 1)); done ) &
else
  ( sleep 2 ) &
fi
exit 0
"""

WATCHER_STUB = """import sys, os
# Stands in for watch_agent.py. Every invocation's argv is logged to its own NUL-separated file (the
# --list-ids pre-launch snapshot AND each of the N+1 per-reader spawns) so a test can both count and
# distinguish them; --list-ids also prints the fixed pre-launch id set the launcher's snapshot reads.
log_dir = os.environ["WATCHER_ARGV_DIR"]
# Claim the filename ATOMICALLY. The launcher spawns these concurrently, so counting the directory
# and then opening `call-{n}` lets every concurrent spawn read the same n and write the same path —
# the later ones silently overwrite the earlier, and the recorded count comes up short by however
# many collided. That is not a slow write a reader can wait out; the file never existed separately.
# O_CREAT|O_EXCL makes the claim indivisible: exactly one process wins each n, the losers retry.
n = 0
while True:
    try:
        fd = os.open(os.path.join(log_dir, f"call-{n}.argv"), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        break
    except FileExistsError:
        n += 1
with os.fdopen(fd, "wb") as fh:
    fh.write(b"\\0".join(a.encode("utf-8") for a in sys.argv[1:]))
seq = os.environ.get("SEQ_LOG")
if seq:
    with open(seq, "a") as fh:
        fh.write("watcher-list-ids\\n" if "--list-ids" in sys.argv else "watcher-spawn\\n")
if "--list-ids" in sys.argv:
    print("pre1,pre2")
else:
    print("watcher-stub: stdout line")
    print("watcher-stub: stderr line", file=sys.stderr)
    # Opt-in, bounded delay before this stub exits — unset (the default) preserves every existing
    # test's instantly-terminal watcher; the keep-awake timing tests set it to get a real, short
    # window during which a real caffeinate stub can be observed still holding.
    # Opt-in hold for a case that asserts keep-awake PRESENCE with no timed window: the watcher's
    # exit is what releases caffeinate, so it must not exit before the caffeinate stub has recorded.
    # It holds until that record exists or the case's teardown creates WATCHER_STUB_RELEASE — no
    # clock ends it, so a caffeinate that starts late cannot outlast it.
    hold_until = os.environ.get("WATCHER_STUB_HOLD_UNTIL")
    release = os.environ.get("WATCHER_STUB_RELEASE")
    if hold_until and release:
        import time
        while not os.path.exists(release):
            if os.path.exists(hold_until) and open(hold_until).read().strip():
                break
            time.sleep(0.05)
    delay = os.environ.get("WATCHER_STUB_SLEEP_SECONDS")
    if delay:
        import time
        # Opt-in readiness gate: hold until caffeinate has written its pid, so the window opens on
        # that event, not on a clock. A caffeinate stub can start after a fixed delay has already
        # run out — under load its first exec queues behind every other first exec on the machine
        # (see `warm_executables` in `core/launchers/conftest.py`) — and the poller then kills it
        # before it is ever seen.
        hold_until = os.environ.get("WATCHER_STUB_HOLD_UNTIL")
        if hold_until:
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline and not (
                os.path.exists(hold_until) and open(hold_until).read().strip()
            ):
                time.sleep(0.05)
        time.sleep(float(delay))
"""

NOTIFIER_STUB = """#!/usr/bin/env bash
printf '%s\\n' "$@" >> "$NOTIFIER_ARGV_LOG"
"""

# Records its own pid (so a test can check whether THAT pid is still alive later) and then holds
# forever until killed — standing in for `caffeinate -i -s`, which does the same until released.
CAFFEINATE_HOLDING_STUB = """#!/usr/bin/env bash
echo "$$" > "$CAFFEINATE_PID_LOG"
printf '%s\\n' "$@" >> "$CAFFEINATE_ARGV_LOG"
exec sleep 999999
"""

# Answers ONLY the `-o lstart= -p <pid>` shape the launcher's keep-awake identity check uses.
# Scripted via $PS_ANSWERS_FILE (one answer per line, consumed in call order — the last line
# repeats once exhausted). "GONE" means "no such process": exit 1, no output. Every entry in the
# fan-out shares this one global answer sequence — the recycled-pid test does not need per-reader
# timing, only that every pid in the set stops matching its captured start time.
# Records the argv of each invocation to $CAFFEINATE_ARGV_LOG and exits — one fixed body, so the
# same warm file serves every case; each case points the variable at its own log.
CAFFEINATE_RECORDING_STUB = """#!/usr/bin/env bash
echo "$@" >> "$CAFFEINATE_ARGV_LOG"
exit 0
"""

PS_STUB = """#!/usr/bin/env bash
# The scripted sequence does not begin until $PS_READY_FILE has content. Every call before
# that answers $PS_PRE_READY_ANSWER ("START" — the watched process is itself) and does not
# advance the counter, so the capture the launcher takes before caffeinate exists is served
# without consuming a line of the poll sequence.
#
# It is a readiness gate, not a widened window, and the difference is the whole point. This
# sequence exists to script the moment a watched pid stops matching — which is the moment the
# poller kills caffeinate. Scheduling that by call ordinal races caffeinate's OWN fork+exec:
# under load the kill can land before the stub has written its pid, and the test then fails as
# "caffeinate never started", having proved nothing about identity. Widening the ordinal was
# tried (2d352d00, one confirmed-alive cycle at 0.05s -> two at 0.3s) and still lost 10 runs
# out of 10 at ten-way concurrency. A fork+exec under load has no upper bound to widen past;
# gating on the event removes the clock from the question instead.
if [ -n "${PS_READY_FILE:-}" ] && [ ! -s "$PS_READY_FILE" ]; then
  echo "$*" >> "$PS_ARGV_LOG"
  printf '%s\n' "${PS_PRE_READY_ANSWER:-START}"
  exit 0
fi
n=$(( $(cat "$PS_CALL_COUNT_FILE" 2>/dev/null || echo 0) + 1 ))
echo "$n" > "$PS_CALL_COUNT_FILE"
echo "$*" >> "$PS_ARGV_LOG"
total=$(wc -l < "$PS_ANSWERS_FILE" | tr -d ' ')
idx="$n"
[ "$idx" -gt "$total" ] && idx="$total"
ans="$(sed -n "${idx}p" "$PS_ANSWERS_FILE")"
if [ "$ans" = "GONE" ]; then
  exit 1
fi
printf '%s\\n' "$ans"
"""


def _pid_alive(pid_text):
    try:
        os.kill(int(pid_text), 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _wait_until(predicate, timeout=5.0, interval=0.05):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return predicate()


def _header_version(text):
    """The launcher's live version, as a tuple. A launcher header carries its versions newest-first,
    so the topmost `# Version:` line is the current one."""
    match = re.search(r"^# Version: (\d+)\.(\d+)\.(\d+)", text, re.M)
    assert match, "the launcher header carries no `# Version:` line"
    return tuple(int(group) for group in match.groups())


def _counted_calls(path):
    """The stub `ps`'s running call count, read tolerantly — the stub rewrites the file on every
    call, so a read can land mid-write and see a partial or empty value."""
    try:
        return int(path.read_text().strip())
    except (OSError, ValueError):
        return 0


def _read_when_present(path, timeout=5.0, interval=0.05):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.exists():
            text = path.read_text().strip()
            if text:
                return text
        time.sleep(interval)
    return None


@pytest.fixture
def run(tmp_path, warm_executables):
    """`run(*cli_args) -> CompletedProcess`, invoking the real launcher with `tmp_path` as cwd.

    Helpers hang off the callable — see each one's docstring below. The tree starts empty; each
    test builds only the pieces its case needs via `run.skill(...)` / `run.project(...)`.
    """
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    warm_executables.link(bin_dir / "claude", CLAUDE_STUB)

    watcher_stub = tmp_path / "watch_agent_stub.py"
    watcher_stub.write_text(WATCHER_STUB)

    notifier_stub = warm_executables.link(tmp_path / "notify_stub.sh", NOTIFIER_STUB)
    watcher_release = tmp_path / "watcher_release"

    claude_argv_dir = tmp_path / "claude_argv"
    claude_argv_dir.mkdir()
    watcher_argv_dir = tmp_path / "watcher_argv"
    watcher_argv_dir.mkdir()
    notifier_log = tmp_path / "notifier_argv.log"
    seq_log = tmp_path / "call_sequence.log"

    env = dict(os.environ)
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
    # Points at a path nothing occupies, so this fixture never reads this machine's real
    # published telemetry endpoint (`a-launcher-tags-its-own-run`) — a launcher's own suite
    # is isolated from real machine state exactly like the watcher and the notifier above.
    env["INSTRUMENT_RUN_ENDPOINT_FILE"] = str(tmp_path / "no-instrument-endpoint")
    env["CLAUDE_ARGV_DIR"] = str(claude_argv_dir)
    env["WATCHER_ARGV_DIR"] = str(watcher_argv_dir)
    env["NOTIFIER_ARGV_LOG"] = str(notifier_log)
    env["SEQ_LOG"] = str(seq_log)
    env["WATCHER_STUB_RELEASE"] = str(watcher_release)
    env["LAUNCH_COLD_READ_WATCHER"] = str(watcher_stub)
    env["LAUNCH_COLD_READ_NOTIFIER"] = str(notifier_stub)
    # Pinned to the instance root by default, so every case that never calls `run.skills_root(...)`
    # keeps today's meaning: the skills root and the instance are the same directory, exactly as
    # they were before the skills root existed as a separate concept.
    env["LAUNCH_COLD_READ_SKILLS_ROOT"] = str(tmp_path)
    env.pop("KENSAIAPP_NOTIFIER", None)
    # The instance's own provider file: an unforced launch reads it at the instance root.
    (tmp_path / ".providers.toml").write_text(_PROVIDER_EXAMPLE.read_text(encoding="utf-8"))
    env["HOME"] = str(tmp_path / "home")
    (tmp_path / "home").mkdir()

    def _run(*cli_args, timeout=30):
        return subprocess.run(
            [str(_SCRIPT), *cli_args],
            cwd=str(tmp_path),
            capture_output=True,
            text=True,
            env=env,
            timeout=timeout,
        )

    def _skill(name, substance=None, manifest=True, version_lines=None, root=None):
        """Write `.claude/skills/<name>/` under `root` (default: `tmp_path`, the instance).
        `substance` is a list of repo-relative paths for `stack.json` (default: just the skill's
        own SKILL.md — a single-entry manifest). `version_lines` maps a substance path to the
        `version:` string its frontmatter should carry (default: "1.0.0" for every entry not
        named). `root` lets a case build the skill under a skills root apart from the instance."""
        base = root if root is not None else tmp_path
        skill_dir = base / ".claude" / "skills" / name
        skill_dir.mkdir(parents=True, exist_ok=True)
        version_lines = version_lines or {}
        skill_md = skill_dir / "SKILL.md"
        skill_ver = version_lines.get(f".claude/skills/{name}/SKILL.md", "1.0.0")
        skill_md.write_text(f"---\nname: {name}\nmetadata:\n  version: \"{skill_ver}\"\n---\n# skill\n")
        substance = substance if substance is not None else [f".claude/skills/{name}/SKILL.md"]
        for path in substance:
            if path == f".claude/skills/{name}/SKILL.md":
                continue
            p = base / path
            p.parent.mkdir(parents=True, exist_ok=True)
            ver = version_lines.get(path, "1.0.0")
            p.write_text(f'version: "{ver}"\n\n# prompt\n')
        if manifest:
            (skill_dir / "stack.json").write_text(
                json.dumps({"version": 1, "substance": substance})
            )
        return skill_dir

    def _grouped_skill(name, group="g", substance=None, manifest=True, version_lines=None, root=None):
        """Same as `_skill`, but built only under the grouped layout —
        `skills/<group>/.claude/skills/<name>` — with no flat `.claude/skills/` at all. Substance
        entries default to the skill's own grouped-repo-relative SKILL.md, matching manifest.py's
        literal-path containment check (a substance path is repo-relative to `root` regardless of
        which layout the skill physically sits under). `root` lets a case build the skill under a
        skills root apart from the instance (default: `tmp_path`)."""
        base = root if root is not None else tmp_path
        skill_dir = base / "skills" / group / ".claude" / "skills" / name
        skill_dir.mkdir(parents=True, exist_ok=True)
        version_lines = version_lines or {}
        skill_rel = f"skills/{group}/.claude/skills/{name}/SKILL.md"
        skill_md = skill_dir / "SKILL.md"
        skill_ver = version_lines.get(skill_rel, "1.0.0")
        skill_md.write_text(f"---\nname: {name}\nmetadata:\n  version: \"{skill_ver}\"\n---\n# skill\n")
        substance = substance if substance is not None else [skill_rel]
        for path in substance:
            if path == skill_rel:
                continue
            p = base / path
            p.parent.mkdir(parents=True, exist_ok=True)
            ver = version_lines.get(path, "1.0.0")
            p.write_text(f'version: "{ver}"\n\n# prompt\n')
        if manifest:
            (skill_dir / "stack.json").write_text(
                json.dumps({"version": 1, "substance": substance})
            )
        return skill_dir

    def _bare_grouped_skill(name, group="g"):
        d = tmp_path / "skills" / group / ".claude" / "skills" / name
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _project(name, stations=None):
        """Write `system/projects/<name>/project.md` + its shukuba folder. `stations` is a list of
        station-file basenames (e.g. `["2026-08-01_uxd-prompt-and-skill.md"]`); default: one."""
        project_dir = tmp_path / "system" / "projects" / name
        project_dir.mkdir(parents=True, exist_ok=True)
        (project_dir / "project.md").write_text(f"# {name}\n\n**Product path:** .\n")
        shukuba = project_dir / "journey" / "shukuba"
        shukuba.mkdir(parents=True, exist_ok=True)
        (shukuba / "README.md").write_text("# readme\n")
        if stations is None:
            stations = ["2026-08-01_a-station.md"]
        for s in stations:
            (shukuba / s).write_text(f"# station\n\nSlug: {s}\n")
        (shukuba / "trail").mkdir(exist_ok=True)
        (shukuba / "parked").mkdir(exist_ok=True)
        return project_dir

    def _argv_from_nul_file(path):
        """One call's argv, decoded from the stub's NUL-separated log (never `.splitlines()` — a
        prompt argv token carries its own embedded newlines, so only a NUL delimiter is unambiguous)."""
        raw = path.read_bytes()
        parts = raw.split(b"\0")
        if parts and parts[-1] == b"":
            parts = parts[:-1]
        return [p.decode("utf-8") for p in parts]

    def _claude_calls():
        """Each `claude` invocation's argv, in call order."""
        files = sorted(claude_argv_dir.glob("call-*.argv"), key=lambda p: int(p.stem.split("-")[1]))
        return [_argv_from_nul_file(f) for f in files]

    def _watcher_calls(expected=None):
        """Each `watch_agent.py` invocation's argv, in call order.

        `expected` is the TOTAL number of recorded calls to wait for — the one synchronous
        `--list-ids` snapshot plus one file per detached spawn. So a three-reader run expects 4.

        It matters because the launcher detaches its watchers and deliberately never waits for
        them (pinned by `test_all_n_plus_one_runs_are_launched_and_none_blocks_another`). A poll
        that stops at the first file hands back a set that is still filling, and a caller
        asserting on three of them fails whenever the machine is loaded enough for the other two
        to lag — which is most of a full-suite run and almost none of a single-test run.

        Left as `None`, it keeps the wait-for-any behaviour, which is what a caller asserting the
        list is EMPTY wants: absence cannot be observed early, so those callers wait out the full
        timeout. On timeout the partial list is returned rather than `[]`, so a failure reports
        what actually landed.
        """
        # Two budgets, because the two modes pay for them differently. Waiting for a COUNT returns
        # the instant the count is met, so a generous budget is free on the happy path and only
        # lengthens a genuine failure — and it has to cover N detached python interpreters starting
        # under load, which 3s does not (measured: under four concurrent runs of this file, 2 of 3
        # spawns landed inside 3s and the assertion saw `2 == 3`). Waiting for ABSENCE can never
        # return early, so its budget is paid in full on every one of those calls and stays short.
        attempts = 400 if expected is not None else 60   # 20s vs 3s, at 0.05s each
        files = []
        for _ in range(attempts):
            files = sorted(watcher_argv_dir.glob("call-*.argv"), key=lambda p: int(p.stem.split("-")[1]))
            enough = len(files) >= expected if expected is not None else bool(files)
            if enough:
                return [_argv_from_nul_file(f) for f in files]
            time.sleep(0.05)
        return [_argv_from_nul_file(f) for f in files]

    def _stub(name, body):
        """Put the warm stub for `body` in this case's `bin/` as `name`, replacing what is there
        (the fixture's own `claude`) rather than writing through it into the shared file."""
        destination = bin_dir / name
        destination.unlink(missing_ok=True)
        return warm_executables.link(destination, body)

    def _hold_watcher_until(record):
        """Keep every watcher stub alive until `record` has content, or this case ends."""
        env["WATCHER_STUB_HOLD_UNTIL"] = str(record)

    def _no_notifier():
        env["LAUNCH_COLD_READ_NOTIFIER"] = str(tmp_path / "nope" / "missing.sh")

    def _default_watcher():
        env.pop("LAUNCH_COLD_READ_WATCHER", None)

    def _other_root():
        """A directory apart from `tmp_path`'s own `.claude/skills` / `skills/` layout — for a
        case that builds a skill under a skills root distinct from the instance. Nested under
        `tmp_path` for cleanup, but never a path the launcher's own instance-relative resolution
        (`.claude/skills`, `skills/*`) would ever reach on its own."""
        d = tmp_path / "elsewhere"
        d.mkdir(exist_ok=True)
        return d

    def _skills_root(path):
        env["LAUNCH_COLD_READ_SKILLS_ROOT"] = str(path)

    def _default_skills_root():
        env.pop("LAUNCH_COLD_READ_SKILLS_ROOT", None)

    def _call_sequence():
        """Both stubs append one token per invocation to a single shared log, so a test can assert
        the ORDER of events across them (the per-stub argv dirs cannot: they are separate files)."""
        return seq_log.read_text().splitlines() if seq_log.exists() else []

    _run.root = tmp_path
    _run.call_sequence = _call_sequence
    _run.skill = _skill
    _run.grouped_skill = _grouped_skill
    _run.bare_grouped_skill = _bare_grouped_skill
    _run.project = _project
    _run.claude_calls = _claude_calls
    _run.watcher_calls = _watcher_calls
    _run.no_notifier = _no_notifier
    _run.default_watcher = _default_watcher
    _run.other_root = _other_root
    _run.skills_root = _skills_root
    _run.default_skills_root = _default_skills_root
    _run.env = env
    _run.stub = _stub
    _run.hold_watcher_until = _hold_watcher_until
    yield _run
    watcher_release.touch()


# =====================================================================================
# Task 1 — the launcher's argument surface, derivations and guards
# =====================================================================================


def test_no_skill_arg_dies_with_usage(run):
    result = run()
    assert result.returncode == 1
    assert "usage:" in result.stderr and "<skill>" in result.stderr and "--project" in result.stderr
    assert run.claude_calls() == []


def test_missing_project_flag_dies_with_usage(run):
    run.skill("product-uxd")
    result = run("product-uxd")
    assert result.returncode == 1
    assert "usage:" in result.stderr
    assert run.claude_calls() == []


def test_project_flag_with_no_value_dies(run):
    run.skill("product-uxd")
    result = run("product-uxd", "--project")
    assert result.returncode == 1
    assert "usage:" in result.stderr


def test_skill_argument_containing_slash_is_refused_as_a_path(run):
    result = run("some/skill", "--project", "p")
    assert result.returncode == 1
    assert "path" in result.stderr
    assert run.claude_calls() == []


def test_skill_argument_starting_with_dot_is_refused_as_a_path(run):
    result = run(".hidden", "--project", "p")
    assert result.returncode == 1
    assert "path" in result.stderr


def test_unknown_flag_is_refused_not_ignored(run):
    run.skill("product-uxd")
    run.project("product-definition")
    result = run("product-uxd", "--project", "product-definition", "--dryrun")
    assert result.returncode == 1
    assert "--dryrun" in result.stderr
    assert run.claude_calls() == []


def test_unknown_second_positional_is_refused(run):
    run.skill("product-uxd")
    run.project("product-definition")
    result = run("product-uxd", "extra-positional", "--project", "product-definition")
    assert result.returncode == 1
    assert "extra-positional" in result.stderr


def test_missing_skill_dies_before_launching(run):
    run.project("product-definition")
    result = run("ghost-skill", "--project", "product-definition")
    assert result.returncode == 1
    assert "ghost-skill" in result.stderr
    assert run.claude_calls() == []


def test_missing_manifest_names_the_one_entry_fix(run):
    run.skill("product-uxd", manifest=False)
    run.project("product-definition")
    result = run("product-uxd", "--project", "product-definition")
    assert result.returncode == 1
    assert "stack.json" in result.stderr
    assert "one-entry manifest" in result.stderr
    assert run.claude_calls() == []


def test_malformed_manifest_fails_loudly_with_manifest_pys_own_message(run):
    skill_dir = run.skill("product-uxd")
    (skill_dir / "stack.json").write_text(json.dumps({"version": 2, "substance": ["x"]}))
    run.project("product-definition")
    result = run("product-uxd", "--project", "product-definition")
    assert result.returncode == 1
    assert "version" in result.stderr
    assert run.claude_calls() == []


def test_manifest_with_empty_substance_array_fails(run):
    skill_dir = run.skill("product-uxd")
    (skill_dir / "stack.json").write_text(json.dumps({"version": 1, "substance": []}))
    run.project("product-definition")
    result = run("product-uxd", "--project", "product-definition")
    assert result.returncode == 1
    assert "substance" in result.stderr


def test_manifest_naming_an_absolute_path_fails(run):
    skill_dir = run.skill("product-uxd")
    (skill_dir / "stack.json").write_text(
        json.dumps({"version": 1, "substance": ["/etc/passwd"]})
    )
    run.project("product-definition")
    result = run("product-uxd", "--project", "product-definition")
    assert result.returncode == 1
    assert "absolute" in result.stderr


def test_manifest_naming_a_nonexistent_file_fails(run):
    skill_dir = run.skill("product-uxd")
    (skill_dir / "stack.json").write_text(
        json.dumps({"version": 1, "substance": ["core/prompts/does_not_exist.md"]})
    )
    run.project("product-definition")
    result = run("product-uxd", "--project", "product-definition")
    assert result.returncode == 1
    assert "does_not_exist.md" in result.stderr


def test_missing_project_dies_before_launching(run):
    run.skill("product-uxd")
    result = run("product-uxd", "--project", "ghost-project")
    assert result.returncode == 1
    assert "ghost-project" in result.stderr
    assert run.claude_calls() == []


def test_no_open_station_dies(run):
    run.skill("product-uxd")
    run.project("product-definition", stations=[])
    result = run("product-uxd", "--project", "product-definition")
    assert result.returncode == 1
    assert "station" in result.stderr
    assert run.claude_calls() == []


def test_two_open_stations_dies_and_lists_them(run):
    run.skill("product-uxd")
    run.project(
        "product-definition",
        stations=["2026-08-01_first.md", "2026-08-02_second.md"],
    )
    result = run("product-uxd", "--project", "product-definition")
    assert result.returncode == 1
    assert "2026-08-01_first.md" in result.stderr
    assert "2026-08-02_second.md" in result.stderr
    assert run.claude_calls() == []


def test_station_slug_is_the_dated_stem_without_the_extension(run):
    """commit_format.md names a station by its dated stem: one project may hold two stations under
    one bare slug on different dates."""
    run.skill("product-uxd")
    run.project("product-definition", stations=["2026-08-01_uxd-prompt-and-skill.md"])
    result = run("product-uxd", "--project", "product-definition", "--dry-run")
    assert result.returncode == 0
    assert "station '2026-08-01_uxd-prompt-and-skill'" in result.stdout


def test_station_slug_with_no_date_prefix_is_the_whole_basename(run):
    run.skill("product-uxd")
    run.project("product-definition", stations=["no-date-here.md"])
    result = run("product-uxd", "--project", "product-definition", "--dry-run")
    assert result.returncode == 0
    assert "no-date-here" in result.stdout


# --- output dir + report filenames ----------------------------------------------------


def test_report_filenames_are_indexed_ordered_and_lowercased(run):
    run.skill(
        "product-uxd",
        substance=[
            ".claude/skills/product-uxd/SKILL.md",
            "skills/cdo/.claude/skills/product-uxd/prompts/rich.md",
        ],
    )
    run.project("product-definition")
    result = run("product-uxd", "--project", "product-definition", "--dry-run")
    assert result.returncode == 0
    assert "01_skill.md" in result.stdout
    assert "02_rich.md" in result.stdout


def test_two_substance_files_sharing_a_basename_still_get_distinct_report_names(run):
    run.skill(
        "twofile",
        substance=[
            ".claude/skills/twofile/SKILL.md",
            "core/prompts/skill.md",
        ],
    )
    run.project("product-definition")
    result = run("twofile", "--project", "product-definition", "--dry-run")
    assert result.returncode == 0
    assert "01_skill.md" in result.stdout
    assert "02_skill.md" in result.stdout


def test_output_directory_is_derived_from_project_and_skill(run):
    run.skill("product-uxd")
    run.project("product-definition")
    result = run("product-uxd", "--project", "product-definition", "--dry-run")
    assert result.returncode == 0
    assert "system/projects/product-definition/docs/product-uxd-coldread" in result.stdout


# --- rounds: a re-read never writes over the round before it ------------------
#
# A cold-read is re-run after every fix pass, so the second run's reports and the first
# run's are different evidence about different text. Writing them to one path makes the
# comparison — did the fix land? — impossible to make, and destroys the prior round with
# no trace. Rounds are numbered folders, resolved from the HIGHEST that exists rather
# than the count: `auditrun/rounds.py` refuses to overwrite a round that already holds a
# report, and `launch-skill-evals` numbers from the highest existing iteration, both for
# this reason. A removed round must never let a new one collide with a real one.


def test_first_ever_read_writes_into_round_1(run):
    run.skill("product-uxd")
    run.project("product-definition")
    result = run("product-uxd", "--project", "product-definition", "--dry-run")
    assert result.returncode == 0
    assert "product-uxd-coldread/round-1/" in result.stdout


def test_a_second_read_writes_into_round_2_leaving_round_1_alone(run):
    run.skill("product-uxd")
    run.project("product-definition")
    round_1 = (run.root / "system/projects/product-definition/docs"
               / "product-uxd-coldread" / "round-1")
    round_1.mkdir(parents=True)
    (round_1 / "01_skill.md").write_text("# an earlier round's report\n")

    result = run("product-uxd", "--project", "product-definition", "--dry-run")

    assert result.returncode == 0
    assert "product-uxd-coldread/round-2/" in result.stdout
    assert "round-1/" not in result.stdout
    assert (round_1 / "01_skill.md").read_text() == "# an earlier round's report\n"


def test_the_next_round_comes_off_the_highest_not_the_count(run):
    """round-2 deleted by hand must not let this run reuse round-3's number."""
    run.skill("product-uxd")
    run.project("product-definition")
    coldread = (run.root / "system/projects/product-definition/docs"
                / "product-uxd-coldread")
    for n in (1, 3):
        (coldread / f"round-{n}").mkdir(parents=True)

    result = run("product-uxd", "--project", "product-definition", "--dry-run")

    assert result.returncode == 0
    assert "product-uxd-coldread/round-4/" in result.stdout


def test_a_non_numeric_round_folder_is_ignored_not_fatal(run):
    """An owner's own folder beside the rounds is not a round and must not break numbering."""
    run.skill("product-uxd")
    run.project("product-definition")
    coldread = (run.root / "system/projects/product-definition/docs"
                / "product-uxd-coldread")
    (coldread / "round-1").mkdir(parents=True)
    (coldread / "round-notes").mkdir()
    (coldread / "notes.md").write_text("# mine\n")

    result = run("product-uxd", "--project", "product-definition", "--dry-run")

    assert result.returncode == 0
    assert "product-uxd-coldread/round-2/" in result.stdout


def test_the_round_is_reported_before_anything_launches(run):
    """The round number is the one thing a caller cannot derive; say it in the header."""
    run.skill("product-uxd")
    run.project("product-definition")
    result = run("product-uxd", "--project", "product-definition", "--dry-run")
    assert result.returncode == 0
    assert "round 1" in result.stdout


def test_project_path_escaping_the_instance_root_is_refused(run):
    outside = run.root.parent / "outside-project"
    outside.mkdir()
    (outside / "project.md").write_text("# outside\n\n**Product path:** .\n")
    run.skill("product-uxd")
    project_dir = run.root / "system" / "projects" / "product-definition"
    project_dir.parent.mkdir(parents=True, exist_ok=True)
    os.symlink(outside, project_dir)
    result = run("product-uxd", "--project", "product-definition")
    assert result.returncode == 1
    assert "outside" in result.stderr or "refus" in result.stderr


# --- --dry-run ---------------------------------------------------------------------


def test_dry_run_launches_nothing(run):
    run.skill("product-uxd")
    run.project("product-definition")
    result = run("product-uxd", "--project", "product-definition", "--dry-run")
    assert result.returncode == 0
    assert run.claude_calls() == []
    assert run.watcher_calls() == []


def test_dry_run_prints_one_command_per_planned_run(run):
    run.skill(
        "product-uxd",
        substance=[
            ".claude/skills/product-uxd/SKILL.md",
            "skills/cdo/.claude/skills/product-uxd/prompts/rich.md",
        ],
    )
    run.project("product-definition")
    result = run("product-uxd", "--project", "product-definition", "--dry-run")
    assert result.returncode == 0
    # two substance files -> two per-file readers + one seam reader = three claude commands
    assert result.stdout.count("claude --bg") == 3


def test_the_variable_is_no_force_and_the_command_is_unchanged(run):
    """cold-read reads no force: an exported provider neither changes the command nor refuses."""
    run.skill("product-uxd")
    run.project("product-definition")
    run.env["KENSAIAPP_AGENT_PROVIDER"] = "codex"

    result = run("product-uxd", "--project", "product-definition", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert "claude --bg" in result.stdout


def test_dry_run_still_runs_every_guard(run):
    """A dry run that reports a command it would refuse to run is a dry run that lies —
    every guard above still runs under --dry-run."""
    result = run("--project", "product-definition", "--dry-run")
    assert result.returncode == 1
    assert run.claude_calls() == []


def test_starting_version_is_reported_but_never_launched(run):
    run.skill("product-uxd", version_lines={".claude/skills/product-uxd/SKILL.md": "9.9.9"})
    run.project("product-definition")
    result = run("product-uxd", "--project", "product-definition", "--dry-run")
    assert result.returncode == 0
    assert "9.9.9" in result.stdout
    assert "9.9.9" not in result.stdout.split("DRY RUN")[-1] if "DRY RUN" in result.stdout else True


def test_dry_run_prints_the_pin_line(run):
    # Task 17: pin_enter runs right after the CORE_DIR guard, ahead of everything else — the
    # fixture's own session-scoped pin (core/launchers/conftest.py) is what this launcher inherits.
    run.skill("product-uxd")
    run.project("product-definition")
    result = run("product-uxd", "--project", "product-definition", "--dry-run")
    assert result.returncode == 0, result.stderr
    assert re.search(r"^Pin: .+\(inherited\)$", result.stdout, re.MULTILINE)


def test_no_literal_core_path_in_the_script():
    text = _SCRIPT.read_text()
    offenders = [
        line for line in text.splitlines()
        if "core/" in line and not line.strip().startswith("#")
    ]
    assert offenders == [], f"literal core/ path(s) outside comments: {offenders}"


# =====================================================================================
# The resolver: grouped layout, not-found, ambiguous
# =====================================================================================


def test_a_grouped_skill_resolves_and_its_readers_launch(run):
    run.grouped_skill("thing")
    run.project("product-definition")
    result = run("thing", "--project", "product-definition", "--dry-run")
    assert result.returncode == 0, result.stderr
    assert result.stdout.count("----- [") == 1


def test_grouped_fixture_builds_no_flat_path(run):
    run.grouped_skill("thing")
    assert not (run.root / ".claude" / "skills").exists()


def test_the_prompts_manifest_sentence_names_the_grouped_path(run):
    run.grouped_skill("thing")
    run.project("product-definition")
    result = run("thing", "--project", "product-definition", "--dry-run")
    assert result.returncode == 0, result.stderr
    assert "skills/g/.claude/skills/thing/stack.json" in result.stdout
    # The bare flat form must never appear ON ITS OWN — only as a suffix of the grouped path
    # above, which legitimately contains it.
    assert "in .claude/skills/thing/stack.json" not in result.stdout


def test_the_no_manifest_die_message_shows_a_usable_grouped_example(run):
    run.grouped_skill("thing", manifest=False)
    run.project("product-definition")
    result = run("thing", "--project", "product-definition")
    assert result.returncode == 1
    assert "skills/g/.claude/skills/thing/SKILL.md" in result.stderr
    assert '".claude/skills/thing/SKILL.md"' not in result.stderr


def test_the_refusal_still_fires_appends_usage_and_no_longer_says_where_it_resolves(run):
    result = run("some/skill", "--project", "p")
    assert result.returncode == 1
    assert "path" in result.stderr
    assert "usage:" in result.stderr
    assert "resolves under" not in result.stderr


def test_unknown_skill_dies_naming_no_layout(run):
    run.project("product-definition")
    result = run("ghost-skill", "--project", "product-definition")
    assert result.returncode == 1
    assert "no skill at" in result.stderr
    assert str(run.root) in result.stderr           # the root searched
    assert "'ghost-skill'" in result.stderr           # the skill name
    assert ".claude/skills" not in result.stderr
    assert "skills/" not in result.stderr
    assert run.claude_calls() == []


def test_ambiguous_skill_dies_naming_both_matching_directories(run):
    d1 = run.bare_grouped_skill("thing", "g1")
    d2 = run.bare_grouped_skill("thing", "g2")
    run.project("product-definition")
    result = run("thing", "--project", "product-definition")
    assert result.returncode == 1
    assert str(d1) in result.stderr
    assert str(d2) in result.stderr
    assert run.claude_calls() == []


def test_ambiguous_message_differs_from_not_found_message(run):
    run.bare_grouped_skill("thing", "g1")
    run.bare_grouped_skill("thing", "g2")
    run.project("product-definition")
    ambiguous = run("thing", "--project", "product-definition")
    not_found = run("ghost-skill", "--project", "product-definition")
    assert ambiguous.stderr != not_found.stderr
    assert ambiguous.returncode == 1
    assert not_found.returncode == 1


def test_stderr_noise_on_a_clean_resolve_never_reaches_the_captured_path(run):
    """The resolver's own stderr is folded into the captured value today (2>&1), so any text a
    future resolver version prints on a successful exit would land INSIDE skill_dir. A stub
    resolver here — exit 0, a real directory on stdout, a line of noise on stderr — proves the
    fold does not happen: the launcher proceeds against the stdout path alone."""
    skill_dir = run.skill("thing")
    run.project("product-definition")
    stub = run.root / "stub_resolver.py"
    stub.write_text(
        "import sys\n"
        f"print({str(skill_dir)!r})\n"
        "print('resolver: a future warning', file=sys.stderr)\n"
    )
    run.env["LAUNCH_COLD_READ_RESOLVER"] = str(stub)
    result = run("thing", "--project", "product-definition", "--dry-run")
    assert result.returncode == 0, result.stderr
    assert "resolver: a future warning" not in result.stdout


# =====================================================================================
# Task 1 (CP-115, CP-116) — the stack is resolved and validated against the skills root
#
# The skills root is the directory above the running <CORE> — under a pin, the pin root; from a
# satellite, the host — never the instance root, and the two can differ. `run.skills_root(...)`
# points `LAUNCH_COLD_READ_SKILLS_ROOT` somewhere apart from `run.root` (the instance); with no
# call, the fixture's own default pins it to `run.root`, so every case above this section keeps
# its meaning unchanged.
# =====================================================================================


def test_a_skill_held_only_by_the_skills_root_resolves(run):
    skills_root = run.other_root()
    run.skills_root(skills_root)
    run.grouped_skill("thing", root=skills_root)
    run.project("product-definition")
    result = run("thing", "--project", "product-definition", "--dry-run")
    assert result.returncode == 0, result.stderr


def test_a_skill_held_only_by_the_instance_is_not_found(run):
    skills_root = run.other_root()
    run.skills_root(skills_root)
    run.grouped_skill("thing")   # built under `run.root` (the instance), not the skills root
    run.project("product-definition")
    result = run("thing", "--project", "product-definition")
    assert result.returncode == 1
    assert f"cold-read: no skill at {skills_root} (is 'thing' a real skill?)" in result.stderr


def test_a_substance_entry_only_the_skills_root_holds_passes(run):
    skills_root = run.other_root()
    run.skills_root(skills_root)
    run.grouped_skill(
        "thing", root=skills_root,
        substance=[
            "skills/g/.claude/skills/thing/SKILL.md",
            "skills/g/.claude/skills/thing/second.md",
        ],
    )
    run.project("product-definition")
    result = run("thing", "--project", "product-definition", "--dry-run")
    assert result.returncode == 0, result.stderr


def test_a_substance_entry_only_the_instance_holds_is_refused(run):
    skills_root = run.other_root()
    run.skills_root(skills_root)
    extra_rel = "skills/g/.claude/skills/thing/second.md"
    run.grouped_skill(
        "thing", root=skills_root,
        substance=["skills/g/.claude/skills/thing/SKILL.md", extra_rel],
    )
    (skills_root / extra_rel).unlink()   # the skills root does NOT hold this entry
    instance_copy = run.root / extra_rel
    instance_copy.parent.mkdir(parents=True, exist_ok=True)
    instance_copy.write_text('version: "1.0.0"\n\n# prompt\n')   # only the instance does
    run.project("product-definition")
    result = run("thing", "--project", "product-definition")
    assert result.returncode == 1
    assert "does not exist" in result.stderr


def test_a_skills_root_whose_path_carries_a_quote_still_validates(run):
    """CP-116 holds for any skills root, and the shell packet's toolchain rule — values cross to
    python3 as argv, never interpolated into its source — is what makes it hold here: a skills
    root (the pin's or a host's) is a path the launcher did not choose, and one carrying a `'`
    must reach `load_stack` as data, not as Python syntax."""
    skills_root = run.root / "it's elsewhere"
    skills_root.mkdir()
    run.skills_root(skills_root)
    run.grouped_skill("thing", root=skills_root)
    run.project("product-definition")
    result = run("thing", "--project", "product-definition", "--dry-run")
    assert result.returncode == 0, result.stderr
    assert f"{skills_root}/skills/g/.claude/skills/thing/SKILL.md" in result.stdout


def test_the_default_skills_root_is_the_inherited_pin(run, _session_pin):
    """With `LAUNCH_COLD_READ_SKILLS_ROOT` unset, the default is `${CORE_DIR%/core}` — the
    pin `core/launchers/conftest.py`'s own session fixture already inherited (Task 17). The
    instance (`tmp_path`) holds no `product-uxd` at all, so only the inherited pin's own copy
    (a real skill in this worktree, under `skills/cdo/.claude/skills/product-uxd`) can have
    resolved it."""
    run.default_skills_root()
    run.project("product-definition")
    result = run("product-uxd", "--project", "product-definition", "--dry-run")
    assert result.returncode == 0, result.stderr
    # CP-115 says the pin root, not merely "not the instance": the subject each reader is handed
    # is the inherited pin's own copy, never the live worktree's.
    pin_root = _session_pin.root
    assert f"{pin_root}/skills/cdo/.claude/skills/product-uxd/SKILL.md" in result.stdout
    assert f"{pin_root}/skills/cdo/.claude/skills/product-uxd/prompts/rich.md" in result.stdout


# =====================================================================================
# Task 2 (CP-117, CP-118, CP-119) — the substance is named and read against the skills root
#
# `skill_rel`, the version read, each per-file subject and the seam subject set derive from
# `SKILLS_ROOT` now, not `INSTANCE_ROOT` — the report paths, the project/station/round derivation
# and the commit's `--repo` stay on `INSTANCE_ROOT` (Task 1's section above already proved
# resolution + validation; this section proves naming + reading).
# =====================================================================================


def _skills_root_two_file_dry_run(run, skill="thing", group="g"):
    skills_root = run.other_root()
    run.skills_root(skills_root)
    run.grouped_skill(
        skill, group=group, root=skills_root,
        substance=[
            f"skills/{group}/.claude/skills/{skill}/SKILL.md",
            f"skills/{group}/.claude/skills/{skill}/second.md",
        ],
    )
    run.project("product-definition")
    result = run(skill, "--project", "product-definition", "--dry-run")
    assert result.returncode == 0, result.stderr
    return skills_root, result, _dry_run_blocks(result.stdout)


def test_each_subject_is_the_skills_roots_copy(run):
    skills_root, _, blocks = _skills_root_two_file_dry_run(run)
    assert f"{skills_root}/skills/g/.claude/skills/thing/SKILL.md" in blocks[0]
    assert f"{skills_root}/skills/g/.claude/skills/thing/second.md" in blocks[1]


def test_the_seam_set_is_the_skills_roots_copies(run):
    skills_root, _, blocks = _skills_root_two_file_dry_run(run)
    seam_block = blocks[-1]
    assert f"{skills_root}/skills/g/.claude/skills/thing/SKILL.md" in seam_block
    assert f"{skills_root}/skills/g/.claude/skills/thing/second.md" in seam_block


def test_the_starting_version_is_read_from_the_skills_root(run):
    skills_root = run.other_root()
    run.skills_root(skills_root)
    run.grouped_skill(
        "thing", root=skills_root,
        version_lines={"skills/g/.claude/skills/thing/SKILL.md": "9.9.9"},
    )
    # A differently-versioned copy sits at the same repo-relative path under the instance —
    # never resolved (the resolver's --root is SKILLS_ROOT), so its version must never surface.
    instance_copy = run.root / "skills" / "g" / ".claude" / "skills" / "thing" / "SKILL.md"
    instance_copy.parent.mkdir(parents=True, exist_ok=True)
    instance_copy.write_text('---\nname: thing\nmetadata:\n  version: "1.0.0"\n---\n# skill\n')
    run.project("product-definition")
    result = run("thing", "--project", "product-definition", "--dry-run")
    assert result.returncode == 0, result.stderr
    assert "9.9.9" in result.stdout
    assert "1.0.0" not in result.stdout


def test_the_manifest_sentence_names_the_skill_relative_to_the_skills_root(run):
    skills_root = run.other_root()
    run.skills_root(skills_root)
    run.grouped_skill("thing", root=skills_root)
    run.project("product-definition")
    result = run("thing", "--project", "product-definition", "--dry-run")
    assert result.returncode == 0, result.stderr
    assert "in skills/g/.claude/skills/thing/stack.json" in result.stdout
    assert f"in {skills_root}" not in result.stdout


def test_the_no_manifest_example_names_the_skill_relative_to_the_skills_root(run):
    skills_root = run.other_root()
    run.skills_root(skills_root)
    run.grouped_skill("thing", root=skills_root, manifest=False)
    run.project("product-definition")
    result = run("thing", "--project", "product-definition")
    assert result.returncode == 1
    assert '"skills/g/.claude/skills/thing/SKILL.md"' in result.stderr
    assert f'"{skills_root}/skills/g/.claude/skills/thing/SKILL.md"' not in result.stderr


def test_reports_and_commit_stay_in_the_instance(run):
    skills_root, _, blocks = _skills_root_two_file_dry_run(run)
    round_dir = "system/projects/product-definition/docs/thing-coldread/round-1"
    for block in blocks:
        assert f"{run.root}/{round_dir}/" in block
        assert f"{skills_root}/{round_dir}/" not in block
        repo_values = re.findall(r'--repo "([^"]*)"', block)
        assert repo_values, "every prompt's commit instruction must interpolate --repo"
        for value in repo_values:
            assert Path(value).resolve() == run.root.resolve()


# =====================================================================================
# Task 2 — the three fixed prompts
#
# Content assertions read --dry-run's stdout, which prints each prompt's text RAW (not shell-`%q`
# escaped, unlike the single-line prompts of sibling launchers) — these prompts are long structured
# documents, not a copy-paste one-liner, so raw display is what "prints every command in full" means
# here and is what makes a plain substring assertion meaningful. Each test isolates one reader's
# block by splitting on the "----- [" markers the dry-run output uses between runs.
# =====================================================================================


def _dry_run_blocks(stdout):
    """dry-run stdout, split into one block of text per planned run (in order)."""
    parts = stdout.split("----- [")[1:]
    return ["----- [" + p for p in parts]


def _two_file_dry_run(run, skill="product-uxd"):
    run.skill(
        skill,
        substance=[
            f".claude/skills/{skill}/SKILL.md",
            "skills/cdo/.claude/skills/product-uxd/prompts/rich.md",
        ],
    )
    run.project("product-definition", stations=["2026-08-01_uxd-prompt-and-skill.md"])
    result = run(skill, "--project", "product-definition", "--dry-run")
    assert result.returncode == 0, result.stderr
    return result, _dry_run_blocks(result.stdout)


def test_two_entry_manifest_yields_three_runs_no_seam_at_one_entry(run):
    _, blocks = _two_file_dry_run(run)
    assert len(blocks) == 3

    run.skill("single", substance=[".claude/skills/single/SKILL.md"])
    run.project("solo-project", stations=["2026-08-01_a-station.md"])
    result = run("single", "--project", "solo-project", "--dry-run")
    assert result.returncode == 0
    assert len(_dry_run_blocks(result.stdout)) == 1
    assert "seam" not in result.stdout.lower()


def test_three_entry_manifest_yields_four_runs(run):
    run.skill(
        "threefile",
        substance=[
            ".claude/skills/threefile/SKILL.md",
            "core/prompts/a.md",
            "core/prompts/b.md",
        ],
    )
    run.project("product-definition")
    result = run("threefile", "--project", "product-definition", "--dry-run")
    assert result.returncode == 0
    assert len(_dry_run_blocks(result.stdout)) == 4


def test_every_command_has_the_fixed_flags_and_no_model_or_allowed_tools(run):
    _, blocks = _two_file_dry_run(run)
    for block in blocks:
        assert "claude --bg" in block
        assert "--agent kensaiapp-auditor" in block
        assert "--permission-mode auto" in block
        assert "--model" not in block
        assert "--allowedTools" not in block
        assert "--print" not in block and " -p " not in block


def test_per_file_prompt_names_its_own_file_and_no_other(run):
    _, blocks = _two_file_dry_run(run)
    skill_block, prompt_block = blocks[0], blocks[1]
    assert ".claude/skills/product-uxd/SKILL.md" in skill_block
    assert "skills/cdo/.claude/skills/product-uxd/prompts/rich.md" not in skill_block
    assert "skills/cdo/.claude/skills/product-uxd/prompts/rich.md" in prompt_block
    # the whole block, not a prefix of it: "hand it the skill, and only the skill" is not a rule
    # that stops applying below the commit instruction
    assert ".claude/skills/product-uxd/SKILL.md" not in prompt_block


def test_every_prompt_draws_the_reading_scope_line_in_all_parts(run):
    """The five-part reading-scope line, in the PER-FILE readers' own terms (one file under
    judgment, evidence-reading allowed, no other subject/ruler, counterpart closed, no sibling
    comparison) plus the resolution-table ask. The seam reader draws its own, differently-worded
    version of the no-subject and no-sibling-comparison parts (its whole subject is the relationship
    between files, so "under judgment" and "counterpart closed" do not apply to it as written) —
    covered separately by test_seam_prompts_counterpart_clause_is_inverted_not_copied."""
    _, blocks = _two_file_dry_run(run)
    for block in blocks[:2]:   # the two per-file readers; blocks[2] is the seam reader
        assert "under judgment" in block
        assert "name the owner" in block.lower()
        assert "not treat it as the ruler" in block or "not a subject" in block
        assert "sibling comparison" in block
        assert "resolution table" in block


def test_seam_prompts_counterpart_clause_is_inverted_not_copied(run):
    _, blocks = _two_file_dry_run(run)
    seam_block = blocks[2]
    per_file_block = blocks[0]
    assert "not read for content at all" in per_file_block
    assert "not read for content at all" not in seam_block
    assert "sibling comparison" in seam_block
    assert "not a subject" in seam_block or "not treat either file as a subject" in seam_block


def test_seam_prompt_names_every_substance_file(run):
    run.skill(
        "threefile",
        substance=[
            ".claude/skills/threefile/SKILL.md",
            "core/prompts/a.md",
            "core/prompts/b.md",
        ],
    )
    run.project("product-definition")
    result = run("threefile", "--project", "product-definition", "--dry-run")
    blocks = _dry_run_blocks(result.stdout)
    seam_block = blocks[-1]
    assert ".claude/skills/threefile/SKILL.md" in seam_block
    assert "core/prompts/a.md" in seam_block
    assert "core/prompts/b.md" in seam_block


def test_seam_prompt_is_a_different_instruction_set_not_a_superset(run):
    _, blocks = _two_file_dry_run(run)
    seam_block = blocks[2]
    assert "does not need BOTH files" in seam_block or "does NOT need BOTH files" in seam_block
    per_file_prompt = blocks[0].split("claude --bg", 1)[1]
    seam_prompt = seam_block.split("claude --bg", 1)[1]
    assert per_file_prompt != seam_prompt
    assert per_file_prompt not in seam_prompt
    assert seam_prompt not in per_file_prompt


def test_no_prompt_asks_for_a_fix(run):
    _, blocks = _two_file_dry_run(run)
    for block in blocks:
        assert "do not fix" in block.lower()
        for word in ("kaizen-fix-author", "kaizen-fixer"):
            assert word not in block
        # none of these appear as an instruction verb directed at the reader
        assert "please fix" not in block.lower()
        assert "repair the" not in block.lower()


def test_no_prompt_restates_the_lens_grammar(run):
    _, blocks = _two_file_dry_run(run)
    for block in blocks:
        assert "BREAK" not in block
        assert "DEGRADE" not in block
        assert "skill-general" not in block
        assert "change-local" not in block


def test_each_prompt_names_only_its_own_report_path(run):
    _, blocks = _two_file_dry_run(run)
    round_dir = "system/projects/product-definition/docs/product-uxd-coldread/round-1"
    targets = [
        f"{round_dir}/01_skill.md",
        f"{round_dir}/02_rich.md",
        f"{round_dir}/seam.md",
    ]
    assert len(set(targets)) == len(targets)   # pairwise distinct
    for i, block in enumerate(blocks):
        assert targets[i] in block
        for j, other in enumerate(targets):
            if j != i:
                assert other not in block, f"block {i} names report path {j}"


def test_commit_instruction_is_complete_and_correct(run):
    _, blocks = _two_file_dry_run(run)
    for block in blocks:
        assert "commit_builder.py" in block
        assert '--repo "' in block
        assert "--add " in block
        assert "--actor kensaiapp-auditor" in block
        assert "--directional" in block
        assert "Shukuba: 2026-08-01_uxd-prompt-and-skill" in block
        assert "progress:" in block
        assert "--skill" not in block


def test_retry_rule_is_present_bounded_and_names_the_waiver(run):
    _, blocks = _two_file_dry_run(run)
    for block in blocks:
        assert "5" in block and "retry" in block.lower()
        assert "different number of seconds" in block
        assert "--take-index" in block
        assert "do not pass it" in block.lower() or "never" in block.lower()


def test_only_validated_values_are_interpolated(run):
    """Each interpolated slot — substance path, report path, instance root, station slug — carries
    exactly the value the launcher derived from disk, and nothing else does."""
    _, blocks = _two_file_dry_run(run)
    expected_substance = [
        ".claude/skills/product-uxd/SKILL.md",
        "skills/cdo/.claude/skills/product-uxd/prompts/rich.md",
    ]
    for i, block in enumerate(blocks[:2]):
        assert f"{run.root}/{expected_substance[i]}" in block   # absolute, root-anchored
        assert (
            f"{run.root}/system/projects/product-definition/docs/product-uxd-coldread/"
            in block
        )
    for block in blocks:
        repo_values = re.findall(r'--repo "([^"]*)"', block)
        assert repo_values, "every prompt's commit instruction must interpolate --repo"
        for value in repo_values:
            assert Path(value).is_absolute()
            assert Path(value).resolve() == run.root.resolve()
        # the station slug is the one the station FILE on disk yields, not anything the caller typed
        assert "Shukuba: 2026-08-01_uxd-prompt-and-skill —" in block


def test_seam_prompt_allows_evidence_reading_and_naming_an_owner(run):
    """The reading-scope line is drawn in EVERY prompt, not only the per-file ones. Two of its
    parts are inverted for the seam reader (one file under judgment; the counterpart closed for
    content) because its subject is the relationship, not a file — but the evidence-reading
    allowance is not one of them. The lens's "name the owner, or you have no finding" binds every
    kensaiapp-auditor finding, and a seam finding ("this file assumes a rule only that file
    states") IS an ownership claim: unstated, the seam reader either cannot file it or has to
    guess whether opening the owner is allowed."""
    _, blocks = _two_file_dry_run(run)
    seam_block = blocks[2]
    assert "as evidence" in seam_block.lower()
    assert "name the owner" in seam_block.lower()


def test_seam_prompt_asks_for_the_resolution_table(run):
    """"Report what you opened" is what makes the reading-scope line auditable rather than
    assumed — and the seam reader, holding the whole substance set, is the one most able to drift
    into simply reading everything. Every prompt asks for the table."""
    _, blocks = _two_file_dry_run(run)
    assert "resolution table" in blocks[2]


def test_seam_prompt_carries_all_three_prohibitions(run):
    """The narrowness is the load-bearing part: no inventory, no re-ranking of what a single-file
    reader would have found alone, and the both-files test."""
    _, blocks = _two_file_dry_run(run)
    seam_block = blocks[2]
    assert "not inventory" in seam_block.lower()
    assert "re-rank" in seam_block.lower()
    assert "BOTH files" in seam_block


def test_retry_rule_says_what_to_do_after_the_last_attempt(run):
    """A bounded retry with no stated terminal action is unbounded in practice — the reader
    invents one. Report the last refusal verbatim, and stop."""
    _, blocks = _two_file_dry_run(run)
    for block in blocks:
        assert "verbatim" in block.lower()
        assert "identical" in block.lower()


# =====================================================================================
# Task 3 — launch, the per-reader watchers, and keep-awake
# =====================================================================================


def _launch_two_file(run, skill="product-uxd", extra_args=()):
    run.skill(
        skill,
        substance=[
            f".claude/skills/{skill}/SKILL.md",
            "skills/cdo/.claude/skills/product-uxd/prompts/rich.md",
        ],
    )
    run.project("product-definition", stations=["2026-08-01_uxd-prompt-and-skill.md"])
    result = run(skill, "--project", "product-definition", *extra_args)
    return result


def test_all_n_plus_one_runs_are_launched_and_none_blocks_another(run):
    # Every run the fake claude leaves behind holds until this test releases it, so a launcher that
    # waited on one would never return: the fixture's own timeout fails the test. Nothing here is
    # timed, so a loaded machine cannot fail a launcher that does not block.
    release = run.root / "claude_run_release"
    run.env["CLAUDE_RUN_RELEASE"] = str(release)
    try:
        result = _launch_two_file(run)
    finally:
        release.touch()

    assert result.returncode == 0, result.stderr
    calls = run.claude_calls()
    assert len(calls) == 3   # 2 per-file + 1 seam
    for argv in calls:
        assert "--bg" in argv
        assert "--agent" in argv and argv[argv.index("--agent") + 1] == "kensaiapp-auditor"
        assert "--permission-mode" in argv and argv[argv.index("--permission-mode") + 1] == "auto"


def test_cold_read_every_reader_carries_the_delivery(run):
    """Task 17: each reader's claude argv is built through the one adapter, inside the loop —
    every one of the N+1 readers carries the pin's six delivery flags, not just the first."""
    result = _launch_two_file(run)
    assert result.returncode == 0, result.stderr
    calls = run.claude_calls()
    assert len(calls) == 3   # 2 per-file readers + 1 seam reader
    for argv in calls:
        assert argv[argv.index("--agent") + 1] == "kensaiapp-auditor"
        assert argv[argv.index("--setting-sources") + 1] == "user"
        assert "--plugin-dir" in argv
        assert "--agents" in argv
        assert "--model" not in argv


def test_agent_ids_are_snapshotted_once_before_the_first_launch(run):
    result = _launch_two_file(run)
    assert result.returncode == 0
    watcher_calls = run.watcher_calls(expected=4)   # 1 --list-ids + 3 detached spawns
    list_id_calls = [c for c in watcher_calls if "--list-ids" in c]
    # the stub answers --list-ids the same way every time it is asked; the launcher must ask ONCE,
    # before any claude invocation, and hand every watcher the same exclusion set
    assert len(list_id_calls) == 1


def test_one_watcher_per_run_each_with_its_own_name_label_and_log(run):
    result = _launch_two_file(run)
    assert result.returncode == 0
    spawns = [c for c in run.watcher_calls(expected=4) if "--list-ids" not in c]
    assert len(spawns) == 3

    names = {c[c.index("--name") + 1] for c in spawns}
    assert len(names) == 3   # each --name equals its own (distinct) prompt

    labels = [c[c.index("--label") + 1] for c in spawns]
    assert len(set(labels)) == 3
    assert any("skill.md" in label.lower() or "SKILL.md" in label for label in labels)
    assert any("rich.md" in label for label in labels)
    assert any("seam" in label.lower() for label in labels)

    logs = sorted((run.root / "system" / "logs").glob("watch-cold-read-product-uxd-*.log"))
    assert len(logs) == 3
    for log in logs:
        assert "product-uxd" in log.name


def test_each_readers_watcher_gets_its_own_readers_id(run):
    """The case the whole handover turns on. Every reader launches under one `--cwd` and shares
    one pre-launch `--exclude-ids` snapshot, so nothing but the id tells them apart — and a
    handover that gave all three watchers the first reader's id would be worse than none: two
    watchers would then report on, and `claude stop`, somebody else's run."""
    result = _launch_two_file(run)
    assert result.returncode == 0
    spawns = [c for c in run.watcher_calls(expected=4) if "--list-ids" not in c]
    assert len(spawns) == 3

    ids = [c[c.index("--agent-id") + 1] for c in spawns]
    assert sorted(ids) == ["bg-id-0", "bg-id-1", "bg-id-2"], (
        f"the three watchers were not handed the three launched ids: {ids}"
    )

    # ...and each id sits on the watcher whose reader printed it. The stub emits `bg-id-<n>` on
    # its n-th call and the launcher launches in prompt order, so the id must track the label.
    labels = [c[c.index("--label") + 1] for c in spawns]
    paired = dict(zip(ids, labels))
    assert len(set(paired.values())) == 3, f"two watchers share a subject: {paired}"


def test_a_launch_that_prints_no_id_still_runs_every_watcher(run):
    """The fallback, at the fan-out. A `claude` whose launch line cannot be read leaves every
    watcher on `--name` plus the candidate set — exactly today's behaviour — and the launcher
    must not fail, warn, or skip a watcher over it."""
    run.stub(
        "claude",
        "#!/usr/bin/env bash\n"
        'n=$(ls "$CLAUDE_ARGV_DIR" 2>/dev/null | wc -l | tr -d " ")\n'
        "printf '%s\\0' \"$@\" > \"$CLAUDE_ARGV_DIR/call-$n.argv\"\n"
        "( sleep 2 ) &\nexit 0\n",
    )
    result = _launch_two_file(run)

    assert result.returncode == 0
    spawns = [c for c in run.watcher_calls(expected=4) if "--list-ids" not in c]
    assert len(spawns) == 3
    for argv in spawns:
        assert "--agent-id" not in argv
        assert "--name" in argv


def test_the_launch_output_is_still_echoed_through_to_the_caller(run):
    """Capturing the launch output must not swallow it. `claude --bg` prints the attach and stop
    hints the caller needs, and a launcher that reads the id off them and keeps them is a
    launcher whose output silently got shorter."""
    result = _launch_two_file(run)

    assert result.returncode == 0
    assert result.stdout.count("backgrounded") == 3, result.stdout


def test_every_watcher_uses_the_generic_reporter_never_coldread(run):
    result = _launch_two_file(run)
    assert result.returncode == 0
    spawns = [c for c in run.watcher_calls(expected=4) if "--list-ids" not in c]
    for argv in spawns:
        assert "--reporter" in argv
        assert argv[argv.index("--reporter") + 1] == "generic"
        assert "--artifact-path" not in argv
        assert "--product-path" not in argv
        assert "--outcome" not in argv


def test_no_notifier_means_no_watcher_but_the_launch_still_succeeds(run):
    run.no_notifier()
    result = _launch_two_file(run)
    assert result.returncode == 0
    assert len(run.claude_calls()) == 3
    # the pre-launch --list-ids snapshot still fires (every sibling launcher takes it
    # unconditionally); what must be absent is any actual per-reader watcher SPAWN
    spawns = [c for c in run.watcher_calls(expected=1) if "--list-ids" not in c]
    assert spawns == []
    assert "completion watch skipped" in result.stdout


def test_a_non_executable_notifier_is_treated_as_absent(run):
    non_exec = run.root / "not_executable.sh"
    non_exec.write_text("#!/usr/bin/env bash\nexit 0\n")   # deliberately NOT chmod +x
    run.env["LAUNCH_COLD_READ_NOTIFIER"] = str(non_exec)
    result = _launch_two_file(run)
    assert result.returncode == 0
    spawns = [c for c in run.watcher_calls(expected=1) if "--list-ids" not in c]
    assert spawns == []
    assert "completion watch skipped" in result.stdout


def _wait_for_lines(path, count, timeout=5.0):
    """True once `path` holds at least `count` lines.

    The keep-awake bind is **detached**, so it lands after the launcher has already returned.
    Polling is how a test observes a process whose timing it does not control — the shape
    `core/launchers/launch-eval-fix/test_launch_eval_fix.py` already uses for the watcher's first
    line. A flat `time.sleep` here passed when this file ran alone and lost inside a loaded
    `core/launchers` run: there the stub's first exec queues behind every other first exec on the
    machine, which `warm_executables` (`core/launchers/conftest.py`) takes out of the window, and
    the wait that is left is only for the detach itself.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.exists() and len(path.read_text().splitlines()) >= count:
            return True
        time.sleep(0.05)
    return False


def test_keep_awake_binds_exactly_one_caffeinate_to_the_whole_fan_out(run, tmp_path):
    caffeinate_log = tmp_path / "caffeinate_calls.log"
    run.stub("caffeinate", CAFFEINATE_RECORDING_STUB)
    run.env["CAFFEINATE_ARGV_LOG"] = str(caffeinate_log)
    run.hold_watcher_until(caffeinate_log)

    result = _launch_two_file(run, extra_args=("--keep-awake",))
    assert result.returncode == 0
    assert _wait_for_lines(caffeinate_log, 1), (
        "keep-awake was asked for and caffeinate was never invoked within the wait"
    )
    # Then settle, so a SECOND bind would have landed by the time the count is read — the
    # "exactly one" half of this assertion is what the whole fan-out sharing one hold means.
    time.sleep(0.3)
    lines = caffeinate_log.read_text().splitlines()
    assert len(lines) == 1, f"expected exactly one caffeinate invocation, got: {lines}"


def test_no_keep_awake_means_no_caffeinate(run, tmp_path):
    caffeinate_log = tmp_path / "caffeinate_calls.log"
    run.stub("caffeinate", CAFFEINATE_RECORDING_STUB)
    run.env["CAFFEINATE_ARGV_LOG"] = str(caffeinate_log)

    result = _launch_two_file(run)
    assert result.returncode == 0
    time.sleep(0.3)
    assert not caffeinate_log.exists()


def test_keep_awake_without_a_notifier_notes_it_and_exits_zero(run):
    run.no_notifier()
    result = _launch_two_file(run, extra_args=("--keep-awake",))
    assert result.returncode == 0
    assert "keep-awake needs a completion watcher" in result.stdout


def test_keep_awake_releases_once_every_reader_actually_ends(run):
    """Behaviours 2 and 4: the fan-out's one caffeinate holds while any reader is genuinely still
    running, and releases once every one of them has actually exited — proven against real
    processes (all three readers' watchers held briefly by WATCHER_STUB_SLEEP_SECONDS, and a
    caffeinate stub that holds until killed), no faked `ps`."""
    # The launcher does real work (git, three python3 watcher startups, prompt-building) before it
    # ever reaches the keep-awake block, and that overhead varies with machine load — measured up
    # to ~0.8s on this machine. The watcher's own held-alive window has to outlast it comfortably,
    # or caffeinate can start after every watcher has already exited and never be observed holding.
    run.env["WATCHER_STUB_SLEEP_SECONDS"] = "2.0"
    run.env["LAUNCH_COLD_READ_KEEPAWAKE_POLL_SECONDS"] = "0.3"

    caffeinate_pid_log = run.root / "caffeinate_pid.log"
    caffeinate_argv_log = run.root / "caffeinate_argv.log"
    run.stub("caffeinate", CAFFEINATE_HOLDING_STUB)
    run.env["CAFFEINATE_PID_LOG"] = str(caffeinate_pid_log)
    run.env["CAFFEINATE_ARGV_LOG"] = str(caffeinate_argv_log)
    run.env["WATCHER_STUB_HOLD_UNTIL"] = str(caffeinate_pid_log)

    result = _launch_two_file(run, extra_args=("--keep-awake",))
    assert result.returncode == 0, result.stderr

    caff_pid = _read_when_present(caffeinate_pid_log)
    assert caff_pid, "caffeinate never started"
    assert _pid_alive(caff_pid), "caffeinate should still be holding while readers are running"

    argv = caffeinate_argv_log.read_text() if caffeinate_argv_log.exists() else ""
    assert "-w" not in argv.split(), (
        f"caffeinate should no longer be bound with a bare -w <pid>; argv was: {argv!r}"
    )

    assert _wait_until(lambda: not _pid_alive(caff_pid), timeout=15.0), (
        "keep-awake never released after every reader actually ended"
    )


def test_a_recycled_watcher_pid_does_not_keep_the_fan_out_awake(run):
    """Behaviour 3, the defect this plan exists to fix: a `kill -0`-style check can't tell a
    genuinely-running reader from an unrelated process that inherited its exited watcher's pid
    number — it just answers true either way. Script every pid in the fan-out to look exactly
    like that (same number, a different start time) and prove the fan-out's keep-awake releases
    rather than looping forever the way a bare `kill -0` poll would."""
    run.env["LAUNCH_COLD_READ_KEEPAWAKE_POLL_SECONDS"] = "0.3"

    caffeinate_pid_log = run.root / "caffeinate_pid.log"
    run.stub("caffeinate", CAFFEINATE_HOLDING_STUB)
    run.env["CAFFEINATE_PID_LOG"] = str(caffeinate_pid_log)
    run.env["CAFFEINATE_ARGV_LOG"] = str(run.root / "caffeinate_argv.log")

    run.stub("ps", PS_STUB)
    # The three captures are served by the readiness gate and consume no line here, so this
    # sequence is the POLLS alone, three per round (one per reader, in a fixed order). Round 1
    # answers "START" for all three — every watcher still itself — and round 2 answers "OTHER"
    # for all three: a live process at each number, with a different start time. The gate holds
    # the sequence until caffeinate has written its pid (see PS_STUB).
    (run.root / "ps_answers.txt").write_text("START\nSTART\nSTART\nOTHER\nOTHER\nOTHER\n")
    run.env["PS_READY_FILE"] = str(caffeinate_pid_log)
    run.env["PS_ANSWERS_FILE"] = str(run.root / "ps_answers.txt")
    run.env["PS_CALL_COUNT_FILE"] = str(run.root / "ps_call_count.txt")
    run.env["PS_ARGV_LOG"] = str(run.root / "ps_argv.log")

    result = _launch_two_file(run, extra_args=("--keep-awake",))
    assert result.returncode == 0, result.stderr

    caff_pid = _read_when_present(caffeinate_pid_log)
    assert caff_pid, "caffeinate never started"

    assert _wait_until(lambda: not _pid_alive(caff_pid), timeout=8.0), (
        "the fan-out's keep-awake is still holding after every watched pid was answered by an "
        "unrelated process"
    )

    ps_argv_log = run.root / "ps_argv.log"
    assert _read_when_present(ps_argv_log) is not None, "the identity check never consulted ps"
    first_call = ps_argv_log.read_text().splitlines()[0].split()
    assert "-o" in first_call and "lstart=" in first_call and "-p" in first_call, (
        f"expected a `ps -o lstart= -p <pid>` identity check, got: {first_call}"
    )


def test_one_reader_still_running_keeps_the_whole_fan_out_awake(run):
    """Behaviour 2, at the case that discriminates: the hold is for the fan-out, so ANY single
    reader still running has to keep it. A poller that released on the first finished reader would
    pass `test_keep_awake_releases_once_every_reader_actually_ends` (they all end there) and strand
    the last reader on a sleeping Mac — the exact failure --keep-awake exists to prevent.

    The fan-out spawns three watchers and the poller walks them in a fixed order, so a call-order
    `ps` can script "the first two are gone, the third is still itself" and hold it for five rounds
    before letting the third go too."""
    run.env["LAUNCH_COLD_READ_KEEPAWAKE_POLL_SECONDS"] = "0.5"

    caffeinate_pid_log = run.root / "caffeinate_pid.log"
    run.stub("caffeinate", CAFFEINATE_HOLDING_STUB)
    run.env["CAFFEINATE_PID_LOG"] = str(caffeinate_pid_log)
    run.env["CAFFEINATE_ARGV_LOG"] = str(run.root / "caffeinate_argv.log")

    run.stub("ps", PS_STUB)
    # The three captures are served by the readiness gate and consume no line here, so this is the
    # POLLS alone: five rounds in which the first two readers' pids are gone and only the third
    # still answers as itself, then one round where none does — the last line repeats once
    # exhausted, so "gone" is where this settles.
    answers = ["GONE", "GONE", "START"] * 5 + ["GONE", "GONE", "GONE"]
    (run.root / "ps_answers.txt").write_text("\n".join(answers) + "\n")
    call_count = run.root / "ps_call_count.txt"
    run.env["PS_READY_FILE"] = str(caffeinate_pid_log)
    run.env["PS_ANSWERS_FILE"] = str(run.root / "ps_answers.txt")
    run.env["PS_CALL_COUNT_FILE"] = str(call_count)
    run.env["PS_ARGV_LOG"] = str(run.root / "ps_argv.log")

    result = _launch_two_file(run, extra_args=("--keep-awake",))
    assert result.returncode == 0, result.stderr

    caff_pid = _read_when_present(caffeinate_pid_log)
    assert caff_pid, "caffeinate never started"

    # three full poll rounds: two readers observed gone, three times over, while the third ran on
    assert _wait_until(lambda: _counted_calls(call_count) >= 9, timeout=10.0), (
        "the poller never completed three rounds over the fan-out"
    )
    assert _pid_alive(caff_pid), (
        "the keep-awake released while a reader was still running — two finished readers ended the "
        "hold for all three"
    )

    assert _wait_until(lambda: not _pid_alive(caff_pid), timeout=10.0), (
        "the keep-awake never released once the last reader ended too"
    )


def test_without_caffeinate_on_path_the_fan_out_still_launches_and_says_it_skipped(run):
    """Behaviour 5: caffeinate is macOS-only. On a machine without it the launcher must still fan
    the readers out and report the skip — the identity-keyed liveness test must not have made the
    keep-awake a precondition of launching."""
    run.env["PATH"] = _path_without_caffeinate(run.env, run.root / "path-without-caffeinate")

    result = _launch_two_file(run, extra_args=("--keep-awake",))

    assert result.returncode == 0, result.stderr
    assert "caffeinate not found" in result.stdout and "skipped" in result.stdout, (
        f"the skip was not reported. stdout: {result.stdout!r}"
    )
    assert "Keep-awake:" not in result.stdout, "claimed a hold it could not take"


def test_the_launcher_neither_uses_nor_documents_a_pid_blind_liveness_test(run):
    """Behaviour 6, read off the launcher's own source. `kill -0` and a bare `caffeinate -w <pid>`
    are the same blindness at two depths, and both had to go; the header has to tell the next reader
    what liveness keys on now, because a header still describing the old poll is a wrong answer to
    the only question a reader opens it with."""
    source = _SCRIPT.read_text()
    # comment lines are excluded on purpose: the header EXPLAINS the `kill -0` it replaced, and a
    # check that cannot tell an explanation from an invocation would forbid recording the reason.
    body = "\n".join(
        line for line in source.splitlines() if not line.lstrip().startswith("#")
    )

    assert "kill -0" not in body, (
        "the fan-out's liveness test still uses `kill -0`, which answers true for a reissued pid"
    )
    caffeinate_calls = [line for line in body.splitlines() if "caffeinate -i -s" in line]
    assert caffeinate_calls, "the launcher no longer invokes caffeinate at all"
    for line in caffeinate_calls:
        assert " -w " not in line, f"a bare-pid caffeinate wait survives: {line.strip()!r}"

    header = "\n".join(
        line for line in itertools.takewhile(
            lambda l: l.startswith("#") or not l.strip(), source.splitlines()
        )
    )
    assert "start time" in header.lower(), (
        "the header does not say what the fan-out's liveness test keys on now"
    )
    assert _header_version(source) > (1, 1, 2), (
        "the pid-blind poll shipped at 1.1.2 — the identity-keyed liveness test has to ship past it"
    )


def test_nothing_is_created_before_the_guards_pass(run):
    run.skill("product-uxd")
    result = run("product-uxd", "--project", "ghost-project")
    assert result.returncode == 1
    assert not (run.root / "system" / "projects" / "ghost-project").exists()
    assert run.claude_calls() == []
    assert run.watcher_calls() == []
    assert not (run.root / "system" / "logs").exists()


def test_launch_exits_zero_and_names_where_to_watch(run):
    result = _launch_two_file(run)
    assert result.returncode == 0
    assert "claude agents" in result.stdout
    assert "claude agents --json --all" in result.stdout


def test_the_id_snapshot_happens_before_the_first_claude_launch(run):
    """Not just "once" — once BEFORE any launch. Taken after, the newest run sits inside its own
    exclusion set and its watcher matches a stale one instead. Only a shared, ordered log across
    both stubs can prove the ordering; the per-stub argv dirs cannot."""
    result = _launch_two_file(run)
    assert result.returncode == 0
    sequence = run.call_sequence()
    assert "watcher-list-ids" in sequence
    assert sequence.count("watcher-list-ids") == 1
    assert sequence.index("watcher-list-ids") < sequence.index("claude")


def test_each_watcher_name_is_its_own_readers_prompt(run):
    """A --name that is not verbatim the prompt its reader was launched with matches nothing and
    pings never. Distinctness alone does not catch that; equality does.

    Since watch_agent 1.8.0 the name is a PREFERENCE rather than the handle — but the fallback it
    was demoted in favour of is "exactly one candidate under this --cwd that was not in the
    pre-launch snapshot", and a fan-out puts three there at once. So the demotion does not reach
    this launcher: for a cold-read reader the name is still the only thing that can identify it,
    and this equality is what the identification rests on."""
    result = _launch_two_file(run)
    assert result.returncode == 0
    launched_prompts = {argv[argv.index("--bg") + 1] for argv in run.claude_calls()}
    spawns = [c for c in run.watcher_calls(expected=4) if "--list-ids" not in c]
    watcher_names = {c[c.index("--name") + 1] for c in spawns}
    assert watcher_names == launched_prompts


def test_the_starting_version_never_reaches_a_launched_command(run):
    """Reported to the terminal, never passed into a run — a version handed to a reader is a
    suspicion handed to a reader."""
    run.skill(
        "product-uxd",
        substance=[
            ".claude/skills/product-uxd/SKILL.md",
            "skills/cdo/.claude/skills/product-uxd/prompts/rich.md",
        ],
        version_lines={".claude/skills/product-uxd/SKILL.md": "9.9.9"},
    )
    run.project("product-definition", stations=["2026-08-01_uxd-prompt-and-skill.md"])
    result = run("product-uxd", "--project", "product-definition")
    assert result.returncode == 0
    assert "9.9.9" in result.stdout
    for argv in run.claude_calls():
        for token in argv:
            assert "9.9.9" not in token


def test_a_real_launch_creates_the_output_directory(run):
    """The readers are told to write into it; nothing else creates it."""
    result = _launch_two_file(run)
    assert result.returncode == 0
    out = run.root / "system" / "projects" / "product-definition" / "docs" / "product-uxd-coldread"
    assert out.is_dir()


def test_a_dry_run_creates_no_output_directory(run):
    """A dry run that materializes a directory has a side effect, which is the one thing "dry"
    promises not to have."""
    run.skill("product-uxd")
    run.project("product-definition")
    result = run("product-uxd", "--project", "product-definition", "--dry-run")
    assert result.returncode == 0
    out = run.root / "system" / "projects" / "product-definition" / "docs" / "product-uxd-coldread"
    assert not out.exists()


def test_keep_awake_without_a_notifier_spawns_no_caffeinate(run, tmp_path):
    caffeinate_log = tmp_path / "caffeinate_calls.log"
    run.stub("caffeinate", CAFFEINATE_RECORDING_STUB)
    run.env["CAFFEINATE_ARGV_LOG"] = str(caffeinate_log)
    run.no_notifier()

    result = _launch_two_file(run, extra_args=("--keep-awake",))
    assert result.returncode == 0
    time.sleep(0.3)
    assert not caffeinate_log.exists()


def test_watcher_is_found_at_its_resolved_home_when_the_env_override_is_unset(run):
    """The relocation test every sibling suite carries: this launcher sits at
    `<CORE>/launchers/cold-read/`, a sibling of `<CORE>/tools/`, so its default watcher path must be
    `$CORE_DIR/tools/watch_agent.py` — the real one, resolved from this folder's own location, not a fixed number of parent steps. With `LAUNCH_COLD_READ_WATCHER` unset
    and a real notifier present, the launcher must still find and spawn every watcher."""
    run.default_watcher()
    # a real watch_agent.py must exist at the real CORE_DIR-resolved path for this test to prove
    # the walk against a real file, not just against another stub
    real_watcher = Path(__file__).resolve().parents[2] / "tools" / "watch_agent.py"
    assert real_watcher.is_file()

    result = _launch_two_file(run)
    assert result.returncode == 0
    assert "completion watch skipped" not in result.stdout
    logs = list((run.root / "system" / "logs").glob("watch-cold-read-product-uxd-*.log"))
    assert len(logs) == 3


# =====================================================================================
# Task 4 — the concurrent-commit hazard, proven and pinned
#
# No launcher involved: these tests invoke the real commit_builder.py against a throwaway git repo,
# proving the collision the retry rule (Task 2) exists to answer and pinning why retrying is the
# correct response and --take-index is never one.
# =====================================================================================


def _no_pin_git_env():
    """`os.environ`, minus every `GIT_CONFIG_*` variable.

    A pinned session (`pin_run.sh`'s `pin_enter`) exports `GIT_CONFIG_COUNT` /
    `GIT_CONFIG_KEY_n=core.hooksPath`, pointed at the PIN's own githooks — which outranks this
    throwaway repo's own permissive `commit-msg` hook when the test process ITSELF runs inside a
    pin (this suite's own process does, whenever it is launched from a pinned session). Task 4's
    git subprocesses need the repo's own hook, set up by the `repo` fixture below, never the
    pin's — so every `GIT_CONFIG_*` variable is stripped from their environment. Measured
    2026-09-23: `test_a_retry_succeeds_once_the_other_writer_commits` fails, in a pinned session,
    on its plain `git commit -m 'b lands'` (`commit-msg: missing required trailer(s): Role:,
    Surface:` — the PIN's own hook, not this fixture's `exit 0` one) and passes once these
    variables are cleared."""
    return {k: v for k, v in os.environ.items() if not k.startswith("GIT_CONFIG")}


@pytest.fixture
def repo(tmp_path):
    """A throwaway git repo with a commit-msg hook that accepts any message (this pins the
    STAGED-SET collision, not the trailer format the real repo's hook separately enforces)."""
    r = tmp_path / "repo"
    r.mkdir()
    env = _no_pin_git_env()
    subprocess.run(["git", "init", "-q"], cwd=r, check=True, env=env)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=r, check=True, env=env)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=r, check=True, env=env)
    hooks = r / ".git" / "hooks"
    hook = hooks / "commit-msg"
    hook.write_text("#!/usr/bin/env bash\nexit 0\n")
    hook.chmod(0o755)
    return r


def _builder(repo, *args):
    return subprocess.run(
        [
            "python3", str(_COMMIT_BUILDER), "--repo", str(repo), "commit",
            "--actor", "kensaiapp-auditor",
            "--directional", "Shukuba: test-station — progress: pinning the collision",
            "--subject", "test commit",
            "--surface", "Claude Code",
            "--co-authored-by", "Claude <noreply@anthropic.com>",
            *args,
        ],
        cwd=str(repo), capture_output=True, text=True,
    )


def _tree_files(repo, ref="HEAD"):
    result = subprocess.run(
        ["git", "show", "--stat", "--format=", ref], cwd=str(repo),
        capture_output=True, text=True, check=True, env=_no_pin_git_env(),
    )
    return result.stdout


def test_the_collision_is_real(repo):
    (repo / "a.md").write_text("a\n")
    (repo / "b.md").write_text("b\n")
    subprocess.run(["git", "add", "b.md"], cwd=str(repo), check=True, env=_no_pin_git_env())   # staged OUTSIDE the builder

    result = _builder(repo, "--add", "a.md")

    assert result.returncode == 1
    assert "refusing to commit" in result.stderr
    assert "b.md" in result.stderr


def test_the_refusal_is_identifiable_by_the_reader(repo):
    (repo / "a.md").write_text("a\n")
    (repo / "b.md").write_text("b\n")
    subprocess.run(["git", "add", "b.md"], cwd=str(repo), check=True, env=_no_pin_git_env())

    result = _builder(repo, "--add", "a.md")

    assert "another session" in result.stderr


def test_a_retry_succeeds_once_the_other_writer_commits(repo):
    """The retry rule's core claim: once whatever was staged-and-undeclared clears, the IDENTICAL
    original command — unmodified — succeeds.

    Divergence from the plan's literal construction, logged here because it surfaces a real
    property of `commit_builder.py`: `_run_git_add` runs BEFORE the staged-set guard
    (`commit_builder.py:673-680`), so A's own refused `--add a.md` leaves a.md staged too — not
    just b.md. `_run_git_commit` carries no pathspec, so any commit that follows takes the WHOLE
    index. Concretely, a naive "the other writer commits through the builder with --add b.md" (as
    literally written in the plan) is ALSO refused here, empirically — a.md is now undeclared from
    B's side exactly as b.md was from A's, symmetrically, and neither side's identical retry ever
    breaks that tie on its own. So "the other writer's commit lands" is modelled directly, as a
    partial `git commit -- b.md` (git's own --only-equivalent form) — leaving a.md staged exactly
    as A's failed attempt left it, and clearing only the undeclared path that was blocking A. What
    this proves is unchanged from the plan's intent: once the blocking path is gone, A's identical
    original command succeeds. What it additionally surfaces, worth flagging to the owner as a
    possible hardening item for `commit_builder.py` itself (out of this plan's scope, which reads
    and reuses shared machinery but does not modify it): two readers who each retry only their own
    single file, with each other's residue mutually undeclared, do not resolve each other.
    """
    (repo / "a.md").write_text("a\n")
    (repo / "b.md").write_text("b\n")
    subprocess.run(["git", "add", "b.md"], cwd=str(repo), check=True, env=_no_pin_git_env())   # "another session" mid-write

    first = _builder(repo, "--add", "a.md")
    assert first.returncode == 1   # refused: b.md staged and undeclared (a.md now staged too)

    # the other writer's own commit lands, clearing b.md — modelled as a partial commit so a.md
    # (this test's own reader's prior staging) is left exactly where the refusal left it
    subprocess.run(
        ["git", "commit", "-m", "b lands", "--", "b.md"], cwd=str(repo), check=True,
        env=_no_pin_git_env(),
    )

    # the IDENTICAL original command, re-run unchanged
    retry = _builder(repo, "--add", "a.md")
    assert retry.returncode == 0, retry.stderr
    tree = _tree_files(repo)
    assert "a.md" in tree
    assert "b.md" not in tree


def test_disjoint_declared_sets_never_contaminate_a_commit(repo):
    (repo / "a.md").write_text("a\n")
    first = _builder(repo, "--add", "a.md")
    assert first.returncode == 0
    first_tree = _tree_files(repo)
    assert "a.md" in first_tree

    (repo / "b.md").write_text("b\n")
    second = _builder(repo, "--add", "b.md")
    assert second.returncode == 0
    second_tree = _tree_files(repo)
    assert "b.md" in second_tree
    assert "a.md" not in second_tree


def test_take_index_would_have_contaminated_it_forbidden_path_pinned(repo):
    """Pins a FORBIDDEN path as an executable fact, not a sanctioned usage: --take-index sweeps
    another session's staged report into this commit, which is exactly why the fixed prompt (Task 2)
    never passes it."""
    (repo / "a.md").write_text("a\n")
    (repo / "b.md").write_text("b\n")
    subprocess.run(["git", "add", "b.md"], cwd=str(repo), check=True, env=_no_pin_git_env())

    result = _builder(repo, "--add", "a.md", "--take-index")

    assert result.returncode == 0
    tree = _tree_files(repo)
    assert "a.md" in tree
    assert "b.md" in tree   # the contamination --take-index exists to demonstrate, never to use


# =====================================================================================
# The seam: the fan-out's identity check and the watchers' own identification
#
# The keep-awake tests above prove the fan-out poller releases on IDENTITY rather than on a pid
# number, against a stub watcher. They therefore say nothing about the processes whose lifetimes
# the whole mechanism is keyed to: the real `watch_agent.py`, one per reader, which is what every
# entry in `watcher_pids` is.
#
# Those processes have their own way of ending early. Each identifies the run it watches, gives up
# after `--appear-seconds` if it cannot, and exits — and a keep-awake keyed to them exactly, as
# the tests above now make it, follows them down. So the plan's overall goal ("neither launcher's
# --keep-awake can outlive the run it was started for") has a second half no test above reaches:
# it must not UNDER-live it either. `system/projects/tools/journey/nemawashi/
# 2026-08-22_the-watcher-cannot-find-its-own-agent.md` measured that half at ~90 seconds and asked
# for exactly this check: "whichever lands second should re-check the first's claim end to end."
#
# The fan-out is where that question has a different answer from the retired ad-hoc-flow's, and the reason is
# structural rather than incidental: every reader is launched under the SAME `--cwd` and handed
# the SAME `--exclude-ids` snapshot, so the three of them are indistinguishable to any rule that
# does not use the name. See `test_a_retitled_fan_out_...` below.
#
# These run the REAL watcher against a fake `claude`, with the watcher's own time knobs scaled
# down. What is faked is Claude Code; what is under test is everything this instance wrote.
# =====================================================================================


_REAL_WATCHER = Path(__file__).resolve().parents[2] / "tools" / "watch_agent.py"

# Runs the REAL watch_agent.py, with two of its own flags appended. Both only scale TIME — the
# 90-second appear window and the 30-second watch poll become fractions of a second, so the
# give-up path this seam is about can be reached inside a test instead of a minute and a half.
# Nothing about how a run is IDENTIFIED is touched, which is the only thing being measured here.
# `execv` keeps the pid the launcher captured, and with it the start time the keep-awake's
# identity check pairs against — a subprocess would not.
SEAM_WATCHER_WRAPPER = """import os, sys
os.execv(sys.executable, [
    sys.executable, os.environ["SEAM_REAL_WATCHER"], *sys.argv[1:],
    "--appear-seconds", os.environ["SEAM_APPEAR_SECONDS"],
    "--poll-seconds", os.environ["SEAM_POLL_SECONDS"],
])
"""

# A fake `claude` modelling the one Claude Code behaviour this seam turns on: a background agent
# listed under an AI-generated title the launcher never passed, from the first moment it appears.
# `$SEAM_AGENT_NAME` is what the list reports every agent as — an AI title for the retitle case,
# or the literal "PROMPT", which echoes each launch's own prompt back and is the control where the
# name still matches. `$SEAM_STATE_FILE` holds their state, so the TEST decides when the runs end
# rather than a clock the machine's load can outrun.
SEAM_CLAUDE_STUB = r"""#!/usr/bin/env bash
case "$1" in
  --bg)
    n=$(( $(cat "$SEAM_AGENT_COUNT_FILE" 2>/dev/null || echo 0) + 1 ))
    echo "$n" > "$SEAM_AGENT_COUNT_FILE"
    printf '%s\0' "$@" > "$CLAUDE_ARGV_DIR/call-$(( n - 1 )).argv"
    if [ "${SEAM_AGENT_NAME:-}" = "PROMPT" ]; then
      printf '%s\0' "$2" >> "$SEAM_AGENT_NAMES_FILE"
    else
      printf '%s\0' "${SEAM_AGENT_NAME:-user intent extraction task}" >> "$SEAM_AGENT_NAMES_FILE"
    fi
    # Whether the launch line is READABLE is the knob, not whether the CLI prints one. Off is
    # the fallback's own precondition — the launcher's capture came back empty, so its watchers
    # run on the name and the candidate set, which is what every seam test below was written
    # against. On, the launcher captures `seam-<n>` and hands each watcher its own reader.
    [ -n "${SEAM_EMIT_ID:-}" ] && printf '\033[2m  backgrounded \302\267 \033[0mseam-%s\033[0m\n' "$n"
    ;;
  agents)
    # The names file is NUL-separated, not newline-separated: a cold-read prompt is a
    # multi-paragraph string carrying its own newlines, so only NUL can say where one ends.
    # python builds the whole list — it is the only thing here that can be trusted to JSON-escape
    # such a string.
    python3 -c '
import json, os, sys
count = int(open(os.environ["SEAM_AGENT_COUNT_FILE"]).read().strip() or 0) if os.path.exists(os.environ["SEAM_AGENT_COUNT_FILE"]) else 0
state = open(os.environ["SEAM_STATE_FILE"]).read().strip() if os.path.exists(os.environ["SEAM_STATE_FILE"]) else "running"
names = []
if os.path.exists(os.environ["SEAM_AGENT_NAMES_FILE"]):
    raw = open(os.environ["SEAM_AGENT_NAMES_FILE"], "rb").read().split(b"\0")
    names = [p.decode("utf-8") for p in raw if p != b""]
out = [
    {"id": f"seam-{i+1}", "kind": "background", "cwd": os.environ["SEAM_AGENT_CWD"],
     "state": state or "running", "startedAt": i + 1,
     "sessionId": f"sess-seam-{i+1}", "name": names[i] if i < len(names) else "?"}
    for i in range(count)
]
sys.stdout.write(json.dumps(out))
'
    ;;
  stop)
    echo "$2" >> "$SEAM_STOP_LOG"
    ;;
esac
exit 0
"""


def _seam_setup(run, *, agent_name="user intent extraction task",
                appear_seconds="2.0", poll_seconds="0.25", keepawake_poll="0.3",
                emit_id=False):
    """Wire the launcher to the REAL watcher and a fake `claude`, and hand back the state file.

    `agent_name` is what Claude Code reports every launched agent as: an AI title (the default —
    the retitle this seam is about) or the literal "PROMPT", the control where the name matches.

    `emit_id` is whether the fake CLI's launch line is readable. Off — the default every test
    below this was written against — models a launcher whose capture came back empty, which is
    the fallback's own precondition and the state the whole fleet was in before the id was handed
    over. On, each reader prints its own `seam-<n>` and the launcher captures it.
    """
    root = run.root

    wrapper = root / "seam_watcher.py"
    wrapper.write_text(SEAM_WATCHER_WRAPPER)
    run.env["LAUNCH_COLD_READ_WATCHER"] = str(wrapper)
    run.env["SEAM_REAL_WATCHER"] = str(_REAL_WATCHER)
    run.env["SEAM_APPEAR_SECONDS"] = appear_seconds
    run.env["SEAM_POLL_SECONDS"] = poll_seconds
    run.env["LAUNCH_COLD_READ_KEEPAWAKE_POLL_SECONDS"] = keepawake_poll

    run.stub("claude", SEAM_CLAUDE_STUB)
    run.env["SEAM_AGENT_NAME"] = agent_name
    run.env["SEAM_AGENT_CWD"] = str(root)
    run.env["SEAM_AGENT_COUNT_FILE"] = str(root / "seam_agent_count")
    run.env["SEAM_AGENT_NAMES_FILE"] = str(root / "seam_agent_names")
    run.env["SEAM_STATE_FILE"] = str(root / "seam_agent_state")
    run.env["SEAM_STOP_LOG"] = str(root / "seam_stops.log")
    if emit_id:
        run.env["SEAM_EMIT_ID"] = "1"
    else:
        run.env.pop("SEAM_EMIT_ID", None)

    run.stub("caffeinate", CAFFEINATE_HOLDING_STUB)
    run.env["CAFFEINATE_PID_LOG"] = str(root / "seam_caffeinate_pid.log")
    run.env["CAFFEINATE_ARGV_LOG"] = str(root / "seam_caffeinate_argv.log")

    return root / "seam_agent_state"


def _seam_notifications(run):
    log = Path(run.env["NOTIFIER_ARGV_LOG"])
    return log.read_text() if log.exists() else ""


# This test carried `@pytest.mark.xfail(strict=True)` from 2026-08-22 until the same day, when the
# shukuba `the-keep-awake-outlives-a-blind-watcher` landed the fix it was waiting for. The marker's
# own reason said `strict=True` was there so that the day the fix arrived, pytest would turn the
# unexpected pass into a failure and force the marker out rather than let it outlive its cause. It
# did exactly that — the run reported `XPASS(strict)` — and this is the removal it was asking for.
#
# What changed is not in this file. `watch_agent.py` no longer exits at the appear window when it
# cannot identify its run: with candidates present it holds, watches the set, and reports at the
# real end. All three readers here are still unidentifiable — they share one `--cwd` and one
# `--exclude-ids` snapshot, and that is untouched — so this is the blind path passing, not the
# blindness going away.
def test_a_retitled_fan_out_does_not_release_the_keep_awake_at_the_appear_window(run):
    """The under-live half of the plan's overall goal, at the case the fan-out produces.

    Every reader is listed under an AI title from the moment it appears — what Claude Code now
    does inside the appear window. If the readers' watchers cannot identify their runs they all
    exit there, and the one caffeinate keyed to the whole set of them goes down with them, ~90s
    into a fan-out of any length. So: past the appear deadline, with every reader still going,
    caffeinate must still be holding, and nothing may have claimed a run "may not have started".

    This is the fan-out's own case, not a re-run of the retired ad-hoc-flow's: all three readers launch under
    ONE `--cwd` and share ONE pre-launch `--exclude-ids` snapshot, so they are three candidates
    that only a name can tell apart."""
    state_file = _seam_setup(run, appear_seconds="2.0")

    result = _launch_two_file(run, extra_args=("--keep-awake",))
    assert result.returncode == 0, result.stderr

    caff_pid = _read_when_present(run.root / "seam_caffeinate_pid.log")
    assert caff_pid, "caffeinate never started"

    # Every watcher is spawned before the launcher returns, so their appear deadlines have
    # certainly passed by now — and a watcher that gave up exited one keep-awake poll ago.
    time.sleep(float(run.env["SEAM_APPEAR_SECONDS"]) + 1.5)

    assert "may not have started" not in _seam_notifications(run), (
        f"a watcher abandoned a reader that was working. sent: {_seam_notifications(run)!r}"
    )
    assert _pid_alive(caff_pid), (
        "the fan-out's keep-awake released while every reader was still going — the watchers it "
        "is keyed to gave up on retitled agents and took the hold down with them"
    )

    state_file.write_text("done")
    assert _wait_until(lambda: not _pid_alive(caff_pid), timeout=15.0), (
        "the keep-awake never released once every reader reached a terminal state"
    )


def test_the_fan_out_keep_awake_holds_past_the_appear_window_while_the_names_still_match(run):
    """The control for the test above, and the thing that makes its failure attributable.

    Same wiring, same timings, one difference: every reader is listed under the prompt it was
    launched with, so `--name` still identifies it. If THIS holds and the retitled case does not,
    the difference is the retitle and nothing about the harness."""
    state_file = _seam_setup(run, agent_name="PROMPT", appear_seconds="2.0")

    result = _launch_two_file(run, extra_args=("--keep-awake",))
    assert result.returncode == 0, result.stderr

    caff_pid = _read_when_present(run.root / "seam_caffeinate_pid.log")
    assert caff_pid, "caffeinate never started"

    time.sleep(float(run.env["SEAM_APPEAR_SECONDS"]) + 1.5)

    assert "may not have started" not in _seam_notifications(run), (
        f"a watcher abandoned a name-matching reader. sent: {_seam_notifications(run)!r}"
    )
    assert _pid_alive(caff_pid), (
        "the fan-out's keep-awake released past the appear window even though every reader was "
        "still name-matchable and still running"
    )

    state_file.write_text("done")
    assert _wait_until(lambda: not _pid_alive(caff_pid), timeout=15.0), (
        "the keep-awake never released once every reader reached a terminal state"
    )


def test_a_retitled_fan_out_that_hands_its_ids_over_identifies_every_reader(run):
    """The blindness itself, gone — not survived.

    The two tests above prove the fan-out SURVIVES being unidentifiable: the keep-awake holds and
    nothing claims a run never started. This one asks the question they cannot. With the launch
    line readable, each reader's watcher is handed that reader's own id, so `find_agent_id`'s
    first rule answers and the name — the thing Claude Code rewrote here — is never consulted.

    `claude stop` is the observable difference, and it is the right one: a watcher that
    identified its run stops it, and a blind watch deliberately stops nothing ("a watcher with no
    id it is entitled to is not entitled to stop anything either", `watch_agent.py` § THE BLIND
    WATCH). So three distinct ids in the stop log is three watchers that each knew which run was
    theirs — a handover that gave them all one id could not produce it."""
    state_file = _seam_setup(run, appear_seconds="2.0", emit_id=True)

    result = _launch_two_file(run, extra_args=("--keep-awake",))
    assert result.returncode == 0, result.stderr

    caff_pid = _read_when_present(run.root / "seam_caffeinate_pid.log")
    assert caff_pid, "caffeinate never started"

    state_file.write_text("done")
    assert _wait_until(lambda: not _pid_alive(caff_pid), timeout=20.0), (
        "the keep-awake never released once every reader reached a terminal state"
    )

    stops = Path(run.env["SEAM_STOP_LOG"])
    assert _wait_until(
        lambda: stops.exists() and len(set(stops.read_text().split())) == 3, timeout=20.0
    ), (
        "the three watchers did not each stop their own reader; stop log: "
        f"{stops.read_text() if stops.exists() else '(absent)'!r}"
    )
    assert set(stops.read_text().split()) == {"seam-1", "seam-2", "seam-3"}
    assert "may not have started" not in _seam_notifications(run), (
        f"a watcher abandoned a reader it had been handed the id for: {_seam_notifications(run)!r}"
    )


def test_dry_run_states_the_arm_it_would_run_under(run, tmp_path):
    """`a-launcher-tags-its-own-run` — a dry run that hides the instrument is a dry run that
    lies. With a published endpoint file present, `instrument_run` prints the arm it derived
    (this launcher's own directory name) once, before the per-reader dry-run loop, even though
    nothing is actually spawned."""
    endpoint_file = tmp_path / "real-instrument-endpoint"
    endpoint_file.write_text("http://127.0.0.1:9/v1\n")
    run.env["INSTRUMENT_RUN_ENDPOINT_FILE"] = str(endpoint_file)
    run.skill("product-uxd")
    run.project("product-definition")

    result = run("product-uxd", "--project", "product-definition", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert "kensai.arm=cold-read" in result.stdout
    assert "--settings" in result.stdout, "a dry run that hides the settings hides what a backgrounded run needs"


# --- the run's provenance (CP-221, CP-227, CP-229, CP-230) -------------------------------------


def test_the_instrument_run_call_carries_the_four_provenance_keys():
    assert_instrument_run_call_carries_provenance(_SCRIPT)


def _dry_run_with_endpoint(run, tmp_path):
    endpoint_file = tmp_path / "real-instrument-endpoint"
    endpoint_file.write_text("http://127.0.0.1:9/v1\n")
    run.env["INSTRUMENT_RUN_ENDPOINT_FILE"] = str(endpoint_file)
    run.project("product-definition")
    result = run("product-uxd", "--project", "product-definition", "--dry-run")
    assert result.returncode == 0, result.stderr
    return result


def test_the_telemetry_line_stamps_provider_claude_and_source_default_with_no_model_or_effort(
    run, tmp_path
):
    """cold-read hands its readers no model, so the stamp says `default` and names none; the pairs
    it stamped before this change come first and keep their values (CP-227)."""
    run.skill("product-uxd")
    result = _dry_run_with_endpoint(run, tmp_path)
    assert "kensai.skill=product-uxd,kensai.project=product-definition" in result.stdout
    assert_provenance_stamped(
        result.stdout, provider="claude", source="default", after=("skill", "project")
    )


def test_a_skill_with_an_intelligence_folder_is_still_default_and_the_argv_carries_no_model(
    run, tmp_path
):
    """The audited skill is the run's subject, not its seat: its own intelligence is never read,
    so a declared model and effort reach neither the readers' argv nor the stamp (CP-221)."""
    skill_dir = run.skill("product-uxd")
    (skill_dir / "intelligence").mkdir()
    (skill_dir / "intelligence" / "claude.md").write_text(
        "**Model:** claude-opus-5-5\n**Effort:** high\n"
    )
    result = _dry_run_with_endpoint(run, tmp_path)
    assert_provenance_stamped(result.stdout, provider="claude", source="default")
    assert "claude-opus-5-5" not in result.stdout
    assert "--model" not in result.stdout and "--effort" not in result.stdout
