"""Contract tests for `core/tools/detach_watcher.sh` — the shared completion-watch home.

This is a **sourced bash library**, never run directly, so there is no launcher to invoke
here — that is each caller's own suite's job, over the six launchers that source this file
(named in `_LIBRARY_CALLERS` below, and measured there rather than recited). What is pinned here is the library's own contract, in its
own terms:

- **Required flags.** `detach_completion_watcher` dies naming any missing required flag —
  never a generic error. `--exclude-ids ""` is a legal *value* (the common case: no agents
  existed before the launch) and must not be confused with the flag never having been
  passed at all — the parser tracks *which flags were seen*, not whether their values are
  non-empty.
- **The happy path** — `[ -x notifier ] && [ -f watcher ]` — spawns the watcher with every
  value the caller handed in, `--artifact-path` included only when given.
- **The two-condition else branch** — the fix this library exists to carry from the start
  each half (`watcher`, `notifier`) is checked
  independently and named independently, so "no watcher" is never misreported as "no
  notifier" or vice-versa.
- **`--keep-awake`** starts one detached `caffeinate -i -s` on the happy path and releases
  it on the watcher's **identity** — the pid paired with the start time it had when this
  library spawned it, which a reissued pid number cannot forge — none on the else branch,
  where it prints the "needs a completion watcher" line instead.
- **The function never fails its caller** — exit 0 on every branch except the
  missing-required-flag case, which is the caller's own bug.
- **Sourcing alone has no side effect** — no function call, no output, no directory made.

Isolation: a tiny bash wrapper (`call_detach.sh`, written fresh per test into `tmp_path`)
sources the real library and calls `detach_completion_watcher "$@"` with whatever argv the
wrapper itself received — the same "source, then call" shape `companion-self-answer/launcher.sh`
uses, minus everything a launcher does around it. `watch_agent.py` and the notifier are
stubs. The keep-awake tests hand the library a fake hold starter (a shell function in the
wrapper, through `DETACH_WATCHER_KEEPAWAKE_STARTER`), so the hold exists and is known before the
call returns; they script `ps` and record `sleep` rather than waiting on a clock, and observe the
release as their own stand-in hold exiting. `caffeinate` is stubbed on `PATH` for the few tests
that run the library's real starter.
"""

from __future__ import annotations

import itertools
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

_LIB = Path(__file__).resolve().parent / "detach_watcher.sh"

# The tail of a DETACH_LIB assignment — the variable name and the file it names — matched
# without regard to the prefix expression that resolves the directory (`$CORE_DIR/tools/...`,
# derived from the launcher's own location, not a fixed number of parent steps). A launcher's
# reach mechanism is not part of what makes it a caller of this library; only the declaration is.
_DETACH_LIB_TAIL_RE = re.compile(r'DETACH_LIB="[^"]*/detach_watcher\.sh"')


def _declares_the_shared_detach_home(source: str) -> bool:
    """True when a launcher's source assigns `DETACH_LIB` naming `detach_watcher.sh` — matched
    on the assignment's tail, never on how the directory was resolved. A change to the
    resolution mechanism cannot make this predicate stop matching a launcher that still sources
    the same file."""
    return bool(_DETACH_LIB_TAIL_RE.search(source))


def _launchers_declaring_the_shared_detach_home(launchers_dir: Path) -> list[Path]:
    """Every `launcher.sh` under `launchers_dir` that declares the shared detach home — a
    positive control included: an empty result fails loudly here rather than letting a caller
    read silence as a fleet that complies."""
    found = sorted(
        p for p in launchers_dir.glob("*/launcher.sh") if _declares_the_shared_detach_home(p.read_text())
    )
    assert found, "no launcher declares the shared detach home — this sweep would pass vacuously"
    return found


def _core_dir_for(launcher_dir: Path) -> Path:
    """The `<CORE>` a launcher at `launcher_dir` resolves to — derived from its own location by
    the same shortest-suffix-at-`/launchers/` rule the bootstrap uses, never by counting a fixed
    number of parent steps. Pure string work: it needs no file on disk to exist."""
    text = str(launcher_dir)
    marker = "/launchers/"
    idx = text.rfind(marker)
    assert idx != -1, f"{launcher_dir} has no /launchers/ ancestor"
    return Path(text[:idx])


def _shared_detach_home_for(launcher_path: Path) -> Path:
    """The `detach_watcher.sh` a launcher at `launcher_path` should resolve to, derived from its
    own location rather than from a hard-coded number of parent steps."""
    return _core_dir_for(launcher_path.parent) / "tools" / "detach_watcher.sh"

CAPTURE_STUB = """#!/usr/bin/env bash
# Sources the library under test and calls the launch-output parser with this wrapper's own
# argv, printing whatever came back. A launcher that needs the id for something besides its
# watcher (the round lock, a hand-built watch_args) calls it exactly this way.
set -euo pipefail
source "{lib}"
capture_agent_id "$@"
"""

CALL_STUB = """#!/usr/bin/env bash
# Sources the library under test and calls detach_completion_watcher with this wrapper's
# own argv — a shim, not a launcher, so the library's contract is what is under test.
set -euo pipefail
source "{lib}"
# The layer-1 fake of the keep-awake's hold starter (`DETACH_WATCHER_KEEPAWAKE_STARTER`). A shell function, so it runs inside this bash and starts nothing: it
# records the argv it was handed and answers with the pid of the stand-in hold the test made and
# owns. The hold has therefore started, and is known, before the call returns. Switched on by
# `FAKE_STARTER_CALLS_LOG`; an empty `FAKE_HOLD_PID` is a starter that started nothing.
fake_keepawake_starter() {{
  echo "invoked" >> "$FAKE_STARTER_CALLS_LOG"
  printf '%s\\n' "$@" >> "$FAKE_STARTER_ARGV_LOG"
  printf '%s\\n' "$FAKE_HOLD_PID"
}}
if [ -n "${{FAKE_STARTER_CALLS_LOG:-}}" ]; then
  DETACH_WATCHER_KEEPAWAKE_STARTER=fake_keepawake_starter
fi
detach_completion_watcher "$@"
echo "DETACH_WATCHER_PID=$DETACH_WATCHER_PID"
echo "DETACH_WATCHER_START=$DETACH_WATCHER_START"
"""

TWO_CALLS_STUB = """#!/usr/bin/env bash
# Calls detach_completion_watcher twice in one sourcing session — the shape a fan-out
# caller uses — and reports the caller-visible variable after each call, so a test can
# prove the second call's value overwrites the first rather than the two colliding.
set -euo pipefail
source "{lib}"
detach_completion_watcher "$@" --log-stem call1
echo "FIRST=$DETACH_WATCHER_PID"
detach_completion_watcher "$@" --log-stem call2
echo "SECOND=$DETACH_WATCHER_PID"
"""

WATCHER_STUB = """import sys, os, time
# Stands in for watch_agent.py: records its OWN pid first (so --keep-awake's caffeinate
# can be checked against the pid of the process it is supposed to be waiting on), writes
# both stdout and stderr (the log-carries-both-streams behaviour is catchable), then
# records its own argv for assertions. WATCHER_STUB_START_DELAY stands in for a slow start
# under a loaded parallel run. Each record is written whole and then renamed into place, so a
# reader never sees one half-written.
time.sleep(float(os.environ.get("WATCHER_STUB_START_DELAY") or 0))
def _record(path, text):
    with open(path + ".part", "w") as fh:
        fh.write(text)
    os.replace(path + ".part", path)
# The library starts the watcher through the runner (`locked_python.sh`), and `uv run` keeps its own
# process as the watcher's parent for the watcher's whole life, so the pid the library records is that
# parent's: it lives exactly as long as the watcher, and a signal to it reaches the watcher. The stub
# records the pid it expects the library to have recorded.
_record(os.environ["WATCHER_PID_LOG"], str(os.getppid()))
print("watcher-stub: stdout line")
print("watcher-stub: stderr line", file=sys.stderr)
_record(os.environ["WATCHER_ARGV_LOG"], "\\n".join(sys.argv[1:]))
"""

NOTIFIER_STUB = """#!/usr/bin/env bash
printf '%s\\n' "$@" >> "$NOTIFIER_ARGV_LOG"
"""

CAFFEINATE_STUB = """#!/usr/bin/env bash
echo "invoked" >> "$CAFFEINATE_CALLS_LOG"
printf '%s\\n' "$@" >> "$CAFFEINATE_ARGV_LOG"
sleep 0.2
"""

# A watcher that stays alive for a short, bounded window before exiting — the start-time test
# needs a watcher that is genuinely still running when the library returns, so `ps` can be asked
# about it independently.
WATCHER_STUB_SLEEPY = """import os, sys, time
with open(os.environ["WATCHER_PID_LOG"], "w") as fh:
    fh.write(str(os.getppid()))  # the runner's uv, which is the pid the library records
with open(os.environ["WATCHER_ARGV_LOG"], "w") as fh:
    fh.write("\\n".join(sys.argv[1:]))
time.sleep(0.5)
"""

# Answers ONLY the `ps -o lstart= -p <pid>` shape the library's identity check uses, scripted
# via $PS_ANSWERS_FILE (one answer per line, consumed in call order). The literal answer "GONE"
# means no such process: exit 1 with no output, what real `ps -p` does for a pid nothing
# occupies. A line answering something other than what the first call answered is what a
# *reissued* pid looks like from outside — the same number, a different process.
#
# The first call is the library's own capture of the watcher's start time, taken before the
# keep-awake exists; every later call is the poller's. **Once the script is exhausted the stub
# answers GONE**, so every poller a test starts ends, and ends at a call the test can count: a
# release that came at the right answer and one that came only at exhaustion are two different
# call counts, never a test that hangs. Each call also records whether the stand-in hold was
# still alive at that moment ($PS_HOLD_PID), which is how "the hold stayed up while the watched
# process was itself" is read after the fact rather than sampled under a clock.
#
# There is no readiness gate any more. It existed because the hold was a `caffeinate` stub the
# library detached, whose pid file landed some unbounded time after the call returned; the hold
# is now handed in (`DETACH_WATCHER_KEEPAWAKE_STARTER`) and known before the poller starts.
PS_STUB = """#!/usr/bin/env bash
n=$(( $(cat "$PS_CALL_COUNT_FILE" 2>/dev/null || echo 0) + 1 ))
echo "$n" > "$PS_CALL_COUNT_FILE"
echo "$*" >> "$PS_ARGV_LOG"
if [ -n "${PS_HOLD_PID:-}" ]; then
  if kill -0 "$PS_HOLD_PID" 2>/dev/null; then echo alive; else echo dead; fi >> "$PS_HOLD_LOG"
fi
total=$(wc -l < "$PS_ANSWERS_FILE" | tr -d ' ')
ans=GONE
[ "$n" -le "$total" ] && ans="$(sed -n "${n}p" "$PS_ANSWERS_FILE")"
if [ "$ans" = "GONE" ]; then
  exit 1
fi
printf '%s\\n' "$ans"
"""

# Stands in for `sleep` on the poller's PATH: records the interval it was asked for and returns at
# once. The poll interval is then a value the test reads, not a length of time it waits out.
SLEEP_STUB = """#!/usr/bin/env bash
printf '%s\\n' "$*" >> "$SLEEP_ARGV_LOG"
"""

# The stand-in hold: a process the test starts and owns, which holds until a signal ends it — the
# role `caffeinate -i -s` plays for real. Being the test's own child is the point: `wait()` on it
# is the release, observed as an event, with no deadline of the test's own.
HOLD_STAND_IN = "import signal; signal.pause()"


def _wait_until(predicate, timeout=5.0, interval=0.05):
    """Poll `predicate` up to `timeout` seconds — the polling-with-timeout shape this suite
    already uses for detached background processes whose timing it does not control."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return predicate()


@pytest.fixture
def capture(tmp_path):
    """`capture(*args) -> stdout text`, sourcing the real library and calling
    `capture_agent_id`. Nothing is stubbed: the function is a pure text parse."""
    wrapper = tmp_path / "call_capture.sh"
    wrapper.write_text(CAPTURE_STUB.format(lib=_LIB))
    wrapper.chmod(0o755)

    def _capture(*args):
        result = subprocess.run(
            [str(wrapper), *args], cwd=str(tmp_path), capture_output=True, text=True
        )
        assert result.returncode == 0, result.stderr
        return result.stdout.strip()

    return _capture


@pytest.fixture
def call(tmp_path):
    """`call(*flags) -> CompletedProcess`, sourcing the real library in a tiny bash
    wrapper and invoking `detach_completion_watcher` with `flags`.

    `call.watcher` / `call.notifier` are stub paths honouring the happy-path branch;
    `call.watcher_argv()` / `call.logs()` read back what the stubs recorded;
    `call.install_caffeinate()` puts a `caffeinate` stub on `PATH` for the tests that run the
    library's real hold starter. `call.install_fake_starter()` hands the library a fake hold
    starter instead and returns the stand-in hold it answers with; `call.starter_calls()` /
    `call.starter_argv()` read what that fake was handed — synchronously, because the fake runs
    inside the call. `call.install_ps()` scripts the identity check the poller makes.
    """
    wrapper = tmp_path / "call_detach.sh"
    wrapper.write_text(CALL_STUB.format(lib=_LIB))
    wrapper.chmod(0o755)

    watcher_stub = tmp_path / "watch_agent_stub.py"
    watcher_stub.write_text(WATCHER_STUB)
    watcher_stub.chmod(0o755)

    notifier_stub = tmp_path / "notify_stub.sh"
    notifier_stub.write_text(NOTIFIER_STUB)
    notifier_stub.chmod(0o755)

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()

    argv_log = tmp_path / "watcher_argv.log"
    pid_log = tmp_path / "watcher_pid.log"
    notifier_log = tmp_path / "notifier_argv.log"
    caffeinate_calls_log = tmp_path / "caffeinate_calls.log"
    caffeinate_argv_log = tmp_path / "caffeinate_argv.log"
    starter_calls_log = tmp_path / "starter_calls.log"
    starter_argv_log = tmp_path / "starter_argv.log"
    ps_argv_log = tmp_path / "ps_argv.log"
    ps_hold_log = tmp_path / "ps_hold.log"
    sleep_argv_log = tmp_path / "sleep_argv.log"
    holds = []

    env = dict(os.environ)
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
    env["WATCHER_PID_LOG"] = str(pid_log)
    env["WATCHER_ARGV_LOG"] = str(argv_log)
    env["NOTIFIER_ARGV_LOG"] = str(notifier_log)
    env["CAFFEINATE_CALLS_LOG"] = str(caffeinate_calls_log)
    env["CAFFEINATE_ARGV_LOG"] = str(caffeinate_argv_log)

    def _call(*flags):
        return subprocess.run(
            [str(wrapper), *flags],
            cwd=str(tmp_path),
            capture_output=True,
            text=True,
            env=env,
        )

    # The library backgrounds the watcher (`&`), so it may still be starting when the wrapper
    # returns — past 2.5s inside a loaded `-n 32` run (2026-09-19). A presence read waits 10s.
    # The stub renames each record into place, so a file that exists is whole.
    def _watcher_argv(wait=10.0):
        for _ in range(int(wait / 0.05)):
            if argv_log.exists():
                return argv_log.read_text().splitlines()
            time.sleep(0.05)
        return []

    def _logs():
        # Nonzero size alone is not enough: the stub watcher's stdout is fully buffered
        # when redirected to a file (stderr isn't), so a poll can catch the log mid-write.
        # Two identical reads in a row means the process has exited and flushed.
        logs_dir = tmp_path / "system" / "logs"
        last_size = None
        stable_reads = 0
        for _ in range(100):
            if logs_dir.exists():
                matches = sorted(p for p in logs_dir.glob("watch-*.log") if p.stat().st_size)
                if matches:
                    size = matches[0].stat().st_size
                    if size == last_size:
                        stable_reads += 1
                        if stable_reads >= 2:
                            return matches
                    else:
                        stable_reads = 0
                    last_size = size
            time.sleep(0.05)
        return sorted(logs_dir.glob("watch-*.log")) if logs_dir.exists() else []

    def _slow_start(seconds):
        env["WATCHER_STUB_START_DELAY"] = str(seconds)

    def _watcher_pid(wait=10.0):
        for _ in range(int(wait / 0.05)):
            if pid_log.exists():
                text = pid_log.read_text().strip()
                if text:
                    return text
            time.sleep(0.05)
        return None

    def _install_caffeinate():
        stub = bin_dir / "caffeinate"
        stub.write_text(CAFFEINATE_STUB)
        stub.chmod(0o755)

    def _install_fake_starter():
        """Hand the library a fake hold starter (see CALL_STUB) and return the stand-in hold it
        answers with: a process this test started and owns, so its end is an event the test
        waits on rather than a state it samples. The plain `caffeinate` stub goes on `PATH` as
        well, so a library that ignored the port would still never start the machine's own."""
        _install_caffeinate()
        hold = subprocess.Popen([sys.executable, "-c", HOLD_STAND_IN])
        holds.append(hold)
        env["FAKE_HOLD_PID"] = str(hold.pid)
        env["FAKE_STARTER_CALLS_LOG"] = str(starter_calls_log)
        env["FAKE_STARTER_ARGV_LOG"] = str(starter_argv_log)
        return hold

    def _starter_calls():
        """How many holds the call started. Read once, with no wait: the fake runs inside the
        call, so its record is whole by the time the call has returned."""
        if not starter_calls_log.exists():
            return 0
        return len(starter_calls_log.read_text().splitlines())

    def _starter_argv():
        return starter_argv_log.read_text().splitlines() if starter_argv_log.exists() else []

    def _install_ps(answers, poll_seconds="0.1"):
        """A fake `ps` answering the identity check from `answers` (GONE once exhausted — see
        PS_STUB), and a fake `sleep` recording the poller's interval instead of waiting it out.
        `poll_seconds` is the env default the poller reads when no flag is passed."""
        for name, text in (("ps", PS_STUB), ("sleep", SLEEP_STUB)):
            stub = bin_dir / name
            stub.write_text(text)
            stub.chmod(0o755)
        answers_file = tmp_path / "ps_answers.txt"
        answers_file.write_text("".join(f"{a}\n" for a in answers))
        env["PS_ANSWERS_FILE"] = str(answers_file)
        env["PS_CALL_COUNT_FILE"] = str(tmp_path / "ps_call_count.txt")
        env["PS_ARGV_LOG"] = str(ps_argv_log)
        env["PS_HOLD_LOG"] = str(ps_hold_log)
        env["SLEEP_ARGV_LOG"] = str(sleep_argv_log)
        env["DETACH_WATCHER_KEEPAWAKE_POLL_SECONDS"] = poll_seconds
        if "FAKE_HOLD_PID" in env:
            env["PS_HOLD_PID"] = env["FAKE_HOLD_PID"]

    def _released(hold):
        """Wait for the poller to end the stand-in hold, and return how it ended. The wait is
        an event — the test's own child exiting — bounded by nothing of this test's own: a
        poller always ends, because the scripted `ps` answers GONE once exhausted, so a wrong
        release shows up as the wrong call count below rather than as a hang."""
        return hold.wait()

    def _read_lines(path):
        return path.read_text().splitlines() if path.exists() else []

    def _use_sleepy_watcher():
        """Swap the instantly-terminal watcher stub for one that lives ~0.5s, so "holding"
        and "released" are two observable states rather than one."""
        watcher_stub.write_text(WATCHER_STUB_SLEEPY)
        env["DETACH_WATCHER_KEEPAWAKE_POLL_SECONDS"] = "0.1"

    def _ps_argv():
        return _read_lines(ps_argv_log)

    def _ps_hold_states():
        return _read_lines(ps_hold_log)

    def _sleeps():
        return _read_lines(sleep_argv_log)

    _call.root = tmp_path
    _call.env = env
    _call.watcher = watcher_stub
    _call.notifier = notifier_stub
    _call.watcher_argv = _watcher_argv
    _call.watcher_pid = _watcher_pid
    _call.slow_start = _slow_start
    _call.logs = _logs
    _call.install_caffeinate = _install_caffeinate
    _call.install_fake_starter = _install_fake_starter
    _call.starter_calls = _starter_calls
    _call.starter_argv = _starter_argv
    _call.install_ps = _install_ps
    _call.released = _released
    _call.use_sleepy_watcher = _use_sleepy_watcher
    _call.ps_argv = _ps_argv
    _call.ps_hold_states = _ps_hold_states
    _call.sleeps = _sleeps
    yield _call

    # A stand-in hold outlives a test that failed before its release, so the fixture ends it
    # rather than leaving it behind. It is this test's own child, so ending and reaping it needs
    # no pid file and no wait for one.
    for hold in holds:
        if hold.poll() is None:
            hold.kill()
            hold.wait()


def _reported_pid(result):
    """The value `DETACH_WATCHER_PID` held after `detach_completion_watcher` returned, read
    back from the `CALL_STUB` wrapper's own echoed line — never `$!` from the test's own
    shell, which would name the wrong process."""
    for line in result.stdout.splitlines():
        if line.startswith("DETACH_WATCHER_PID="):
            return line.split("=", 1)[1]
    return None


def _reported_start(result):
    """The value `DETACH_WATCHER_START` held after the call returned — the other half of the
    identity a fan-out caller needs, read back the same way and for the same reason."""
    for line in result.stdout.splitlines():
        if line.startswith("DETACH_WATCHER_START="):
            return line.split("=", 1)[1]
    return None


# The required-flag set, and a legal default value for each — used both to build a full,
# valid call and to omit one flag at a time.
REQUIRED_FLAG_VALUES = {
    "--watcher": lambda c: str(c.watcher),
    "--notifier": lambda c: str(c.notifier),
    "--instance-root": lambda c: str(c.root),
    "--prompt": lambda c: "invoke the project-finish-line skill for the example-product project.",
    "--label": lambda c: "example-product",
    "--log-stem": lambda c: "example-product",
    "--reporter": lambda c: "generic",
    "--exclude-ids": lambda c: "",  # legal: no agents existed before this launch
}


def _flags(call, omit=None, **overrides):
    """The full set of required flags (as CLI args), each resolved via
    `REQUIRED_FLAG_VALUES` unless overridden by name (without the leading `--`), and with
    `omit` (a flag name, `--foo`) left out entirely — distinct from passing it an empty
    value.
    """
    out = []
    for name, default_fn in REQUIRED_FLAG_VALUES.items():
        if name == omit:
            continue
        value = overrides.get(name, default_fn(call))
        out += [name, value]
    return out


# --- missing required flags ---------------------------------------------------------


@pytest.mark.parametrize("omitted", list(REQUIRED_FLAG_VALUES))
def test_a_missing_required_flag_dies_naming_it(call, omitted):
    result = call(*_flags(call, omit=omitted))

    assert result.returncode != 0
    assert omitted in result.stderr
    assert call.watcher_argv(wait=2.5) == []


def test_an_empty_exclude_ids_value_is_not_treated_as_missing(call):
    """`--exclude-ids ""` is the ordinary first-launch case (no prior agents to exclude) —
    it must reach the happy path, not the missing-required-flag guard."""
    result = call(*_flags(call, **{"--exclude-ids": ""}))

    assert result.returncode == 0
    argv = call.watcher_argv()
    assert argv[argv.index("--exclude-ids") + 1] == ""


# --- the happy path -------------------------------------------------------------------


def test_happy_path_spawns_the_watcher_with_every_value_it_was_given(call):
    result = call(*_flags(call, **{"--exclude-ids": "pre1,pre2"}), "--artifact-path", "/some/artifact")

    assert result.returncode == 0
    argv = call.watcher_argv()
    assert argv[argv.index("--name") + 1] == "invoke the project-finish-line skill for the example-product project."
    assert argv[argv.index("--label") + 1] == "example-product"
    assert argv[argv.index("--cwd") + 1] == str(call.root)
    assert argv[argv.index("--reporter") + 1] == "generic"
    assert argv[argv.index("--artifact-path") + 1] == "/some/artifact"
    assert argv[argv.index("--exclude-ids") + 1] == "pre1,pre2"
    assert argv[argv.index("--notify") + 1] == str(call.notifier)


def test_artifact_path_absent_is_honoured_not_defaulted(call):
    call(*_flags(call))

    argv = call.watcher_argv()
    assert "--artifact-path" not in argv
    assert "--product-path" not in argv


# --- --product-path (an alias for --artifact-path, passed through under its own spelling) ---


def test_product_path_reaches_the_watcher_as_product_path(call):
    result = call(*_flags(call), "--product-path", "/some/product")

    assert result.returncode == 0
    argv = call.watcher_argv()
    assert argv[argv.index("--product-path") + 1] == "/some/product"
    assert "--artifact-path" not in argv


def test_giving_both_artifact_path_and_product_path_returns_1_naming_the_conflict(call):
    result = call(
        *_flags(call), "--artifact-path", "/some/artifact", "--product-path", "/some/product"
    )

    assert result.returncode != 0
    assert "--artifact-path" in result.stderr
    assert "--product-path" in result.stderr
    assert call.watcher_argv(wait=2.5) == []


def test_artifact_path_reaches_the_watcher_under_its_own_spelling_only(call):
    """The mirror of `test_product_path_reaches_the_watcher_as_product_path`: the home passes
    through *the one spelling it was given*, so `--artifact-path` must not also emit the
    `--product-path` alias. Without this the alias could be emitted under both spellings and
    only the product-path direction would notice (plan Task 1, behaviour 2)."""
    result = call(*_flags(call), "--artifact-path", "/some/artifact")

    assert result.returncode == 0
    argv = call.watcher_argv()
    assert argv[argv.index("--artifact-path") + 1] == "/some/artifact"
    assert "--product-path" not in argv


# --- --head-repo (pure pass-through, watch_agent.py's parse_args already declares it) ---


def test_head_repo_reaches_the_watcher_as_head_repo(call):
    result = call(*_flags(call), "--head-repo", "/some/repo")

    assert result.returncode == 0
    argv = call.watcher_argv()
    assert argv[argv.index("--head-repo") + 1] == "/some/repo"


def test_head_repo_absent_is_honoured_not_defaulted(call):
    call(*_flags(call))

    argv = call.watcher_argv()
    assert "--head-repo" not in argv


def test_head_repo_composes_with_artifact_path(call):
    result = call(*_flags(call), "--head-repo", "/some/repo", "--artifact-path", "/some/artifact")

    assert result.returncode == 0
    argv = call.watcher_argv()
    assert argv[argv.index("--head-repo") + 1] == "/some/repo"
    assert argv[argv.index("--artifact-path") + 1] == "/some/artifact"


def test_omitting_head_repo_never_trips_the_missing_required_flag_guard(call):
    result = call(*_flags(call))

    assert result.returncode == 0
    assert "missing required" not in result.stderr


# --- --agent-id (the exact handle, forwarded to watch_agent.py) -------------------------
#
# `watch_agent.py:155` declares this parameter as "the id `claude --bg` printed at launch. The
# exact handle: given this, the name is not consulted at all. Preferred over --name." The library
# is the only thing between a launcher that can capture that id and the watcher that wants it, so
# what is pinned here is that it carries the value through untouched — and, just as hard, that a
# caller passing nothing gets the argv it gets today.


def test_agent_id_reaches_the_watcher_as_agent_id(call):
    result = call(*_flags(call), "--agent-id", "acc210c01c43a9e6b")

    assert result.returncode == 0
    argv = call.watcher_argv()
    assert argv[argv.index("--agent-id") + 1] == "acc210c01c43a9e6b"


def test_agent_id_absent_appends_nothing(call):
    """The sixteen callers that pass no id inherit this flag by not using it, so the no-flag
    argv must stay exactly what it is today — not `--agent-id ""`, which watch_agent would read
    as a falsy id and which no test downstream would catch."""
    call(*_flags(call))

    argv = call.watcher_argv()
    assert "--agent-id" not in argv


def test_agent_id_does_not_displace_the_name(call):
    """--name stays on the line either way. watch_agent ignores it when an id is present
    (`watch_agent.py:268-271`), so keeping it makes every caller's argv a superset rather than a
    rewrite, and leaves the fallback chain intact for the callers that pass no id."""
    result = call(*_flags(call), "--agent-id", "acc210c01c43a9e6b")

    assert result.returncode == 0
    argv = call.watcher_argv()
    assert argv[argv.index("--name") + 1] == "invoke the project-finish-line skill for the example-product project."


def test_agent_id_composes_with_artifact_path_and_head_repo(call):
    result = call(
        *_flags(call),
        "--agent-id", "acc210c01c43a9e6b",
        "--artifact-path", "/some/artifact",
        "--head-repo", "/some/repo",
    )

    assert result.returncode == 0
    argv = call.watcher_argv()
    assert argv[argv.index("--agent-id") + 1] == "acc210c01c43a9e6b"
    assert argv[argv.index("--artifact-path") + 1] == "/some/artifact"
    assert argv[argv.index("--head-repo") + 1] == "/some/repo"


def test_omitting_agent_id_never_trips_the_missing_required_flag_guard(call):
    result = call(*_flags(call))

    assert result.returncode == 0
    assert "missing required" not in result.stderr


def test_an_empty_agent_id_value_appends_nothing(call):
    """A launcher whose capture found no id passes `--agent-id "$agent_id"` with an empty value
    rather than branching around the flag. That must land on the fallback path, not hand the
    watcher an empty handle."""
    result = call(*_flags(call), "--agent-id", "")

    assert result.returncode == 0
    argv = call.watcher_argv()
    assert "--agent-id" not in argv


# --- capture_agent_id (the one parse of `claude --bg`'s own launch line) ----------------
#
# This moved here from `launch-skill-evals/launcher.sh`, which had the only copy in the fleet and
# used it for its round lock. Seventeen launcher scripts need the same three lines, so the parse
# gets one home rather than seventeen — the same reason the detach block itself is in this file.
#
# `claude --bg` prints `backgrounded · <id>`, ANSI-wrapped even when stdout is not a TTY, which is
# why the escapes are stripped before the line is read at all.

_BACKGROUNDED = "\x1b[2m  ⎿  backgrounded · \x1b[0macc210c01c43a9e6b\x1b[0m"


def test_capture_agent_id_reads_the_id_off_the_backgrounded_line(capture):
    assert capture(_BACKGROUNDED) == "acc210c01c43a9e6b"


def test_capture_agent_id_strips_the_ansi_colour_claude_wraps_the_id_in(capture):
    """The id is the last field of the line *after* the escapes come off. Read without the
    strip, the trailing reset sequence rides along and the id never matches the agent list."""
    captured = capture(_BACKGROUNDED)

    assert "\x1b" not in captured
    assert captured == "acc210c01c43a9e6b"


def test_capture_agent_id_finds_the_line_among_the_rest_of_the_launch_output(capture):
    launch_out = "\n".join([
        "Launching cto run for 'example-product' (background)…",
        _BACKGROUNDED,
        "  Run `claude attach acc210c01c43a9e6b` to follow it.",
    ])

    assert capture(launch_out) == "acc210c01c43a9e6b"


def test_capture_agent_id_returns_nothing_when_no_backgrounded_line_is_present(capture):
    """A launcher that cannot capture an id still runs, on the fallback — so the parse's own
    empty answer is a supported outcome, not an error."""
    assert capture("Launching cto run for 'example-product' (background)…\nsomething went wrong") == ""


def test_capture_agent_id_returns_nothing_for_empty_output(capture):
    assert capture("") == ""


# --- --launch-output (the library does the parse for a caller that wants no copy of it) --


def test_launch_output_reaches_the_watcher_as_the_parsed_agent_id(call):
    result = call(*_flags(call), "--launch-output", _BACKGROUNDED)

    assert result.returncode == 0
    argv = call.watcher_argv()
    assert argv[argv.index("--agent-id") + 1] == "acc210c01c43a9e6b"


def test_an_explicit_agent_id_wins_over_launch_output(call):
    """A caller that already parsed the id — for a round lock, say — passes `--agent-id`, and
    that is authoritative: it is a value the caller decided on, not one this library inferred."""
    result = call(
        *_flags(call),
        "--launch-output", _BACKGROUNDED,
        "--agent-id", "1111111111111111",
    )

    assert result.returncode == 0
    argv = call.watcher_argv()
    assert argv[argv.index("--agent-id") + 1] == "1111111111111111"
    assert argv.count("--agent-id") == 1


def test_launch_output_with_no_backgrounded_line_appends_no_agent_id(call):
    """The whole of "a launcher that cannot capture one still runs": the parse comes back empty,
    nothing is appended, and the watcher falls back to --name and the candidate set."""
    result = call(*_flags(call), "--launch-output", "claude: command not found")

    assert result.returncode == 0
    argv = call.watcher_argv()
    assert "--agent-id" not in argv
    assert argv[argv.index("--name") + 1] == "invoke the project-finish-line skill for the example-product project."


def test_launch_output_absent_appends_no_agent_id(call):
    call(*_flags(call))

    argv = call.watcher_argv()
    assert "--agent-id" not in argv


def test_omitting_launch_output_never_trips_the_missing_required_flag_guard(call):
    result = call(*_flags(call))

    assert result.returncode == 0
    assert "missing required" not in result.stderr


# --- --multi-turn / --done-when-exists (pure pass-through to watch_agent.py) ------------
#
# The library does not re-implement `watch_agent.py`'s own rule that --multi-turn requires
# --done-when-exists — that refusal is the watcher's alone, and this library passes both
# through exactly as given, so it lands in the watcher log where the ending it protects
# would have been (§ THE CONTRACT).


def test_a_call_passing_neither_new_flag_is_byte_identical_to_before(call):
    result = call(*_flags(call, **{"--exclude-ids": "pre1,pre2"}), "--artifact-path", "/some/artifact")

    assert result.returncode == 0
    argv = call.watcher_argv()
    assert argv == [
        "--name", "invoke the project-finish-line skill for the example-product project.",
        "--label", "example-product",
        "--cwd", str(call.root),
        "--reporter", "generic",
        "--artifact-path", "/some/artifact",
        "--exclude-ids", "pre1,pre2",
        "--notify", str(call.notifier),
    ]


def test_multi_turn_reaches_the_watcher_with_no_value(call):
    result = call(*_flags(call), "--multi-turn", "--done-when-exists", "/some/done")

    assert result.returncode == 0
    argv = call.watcher_argv()
    idx = argv.index("--multi-turn")
    # A valueless flag: whatever follows it (if anything) is another flag, never a value
    # token belonging to --multi-turn.
    assert idx + 1 == len(argv) or argv[idx + 1].startswith("--")


def test_done_when_exists_reaches_the_watcher_as_done_when_exists(call):
    result = call(*_flags(call), "--done-when-exists", "/some/done")

    assert result.returncode == 0
    argv = call.watcher_argv()
    assert argv[argv.index("--done-when-exists") + 1] == "/some/done"


def test_an_empty_done_when_exists_value_appends_nothing(call):
    result = call(*_flags(call), "--done-when-exists", "")

    assert result.returncode == 0
    argv = call.watcher_argv()
    assert "--done-when-exists" not in argv


def test_multi_turn_and_done_when_exists_land_together_with_everything_else(call):
    result = call(
        *_flags(call),
        "--multi-turn",
        "--done-when-exists", "/some/done",
        "--artifact-path", "/some/artifact",
        "--head-repo", "/some/repo",
        "--agent-id", "acc210c01c43a9e6b",
    )

    assert result.returncode == 0
    argv = call.watcher_argv()
    assert "--multi-turn" in argv
    assert argv[argv.index("--done-when-exists") + 1] == "/some/done"
    assert argv[argv.index("--artifact-path") + 1] == "/some/artifact"
    assert argv[argv.index("--head-repo") + 1] == "/some/repo"
    assert argv[argv.index("--agent-id") + 1] == "acc210c01c43a9e6b"
    assert argv[argv.index("--name") + 1] == "invoke the project-finish-line skill for the example-product project."
    assert argv[argv.index("--label") + 1] == "example-product"
    assert argv[argv.index("--reporter") + 1] == "generic"


def test_multi_turn_alone_reaches_the_watcher_unmodified(call):
    """The library does not re-implement watch_agent.py's own --multi-turn-needs-a-marker
    rule — it passes what it was given, and the watcher's refusal (not this library's) is
    what a caller sees if it gets that wrong."""
    result = call(*_flags(call), "--multi-turn")

    assert result.returncode == 0
    argv = call.watcher_argv()
    assert "--multi-turn" in argv
    assert "--done-when-exists" not in argv


def test_omitting_multi_turn_and_done_when_exists_never_trips_the_missing_required_flag_guard(call):
    result = call(*_flags(call))

    assert result.returncode == 0
    assert "missing required" not in result.stderr


def test_the_required_flag_loop_is_unchanged_with_the_new_flags_present(call):
    result = call(
        *_flags(call, omit="--reporter"), "--multi-turn", "--done-when-exists", "/some/done"
    )

    assert result.returncode != 0
    assert "--reporter" in result.stderr
    assert call.watcher_argv(wait=2.5) == []


def test_detach_watcher_pid_and_start_publish_on_the_new_paths_exactly_as_before(call):
    result = call(*_flags(call), "--multi-turn", "--done-when-exists", "/some/done")

    assert result.returncode == 0
    assert _reported_pid(result) == call.watcher_pid()
    assert _reported_start(result) not in (None, "")


# --- --on-complete (sourced from DETACH_WATCHER_ON_COMPLETE, not a flag on this contract) --
#
# The one flag this library forwards without a flag of its own to carry it: no launcher is
# edited to relay it, so the caller sets the environment variable before invoking a
# launcher and this library reads it directly — the same shape
# DETACH_WATCHER_KEEPAWAKE_POLL_SECONDS already reads directly, rather than through a flag.


def test_on_complete_env_var_reaches_the_watcher_as_on_complete(call):
    call.env["DETACH_WATCHER_ON_COMPLETE"] = "/some/hook.sh"

    result = call(*_flags(call))

    assert result.returncode == 0
    argv = call.watcher_argv()
    assert argv[argv.index("--on-complete") + 1] == "/some/hook.sh"


def test_on_complete_env_var_absent_appends_nothing(call):
    result = call(*_flags(call))

    assert result.returncode == 0
    argv = call.watcher_argv()
    assert "--on-complete" not in argv


def test_an_empty_on_complete_env_var_appends_nothing(call):
    """A caller that resolved no hook exports the variable empty rather than branching
    around it. That must land on the no-flag argv, not hand the watcher `--on-complete ""`."""
    call.env["DETACH_WATCHER_ON_COMPLETE"] = ""

    result = call(*_flags(call))

    assert result.returncode == 0
    argv = call.watcher_argv()
    assert "--on-complete" not in argv


def test_on_complete_composes_with_agent_id_and_artifact_path(call):
    call.env["DETACH_WATCHER_ON_COMPLETE"] = "/some/hook.sh"

    result = call(
        *_flags(call),
        "--agent-id", "acc210c01c43a9e6b",
        "--artifact-path", "/some/artifact",
    )

    assert result.returncode == 0
    argv = call.watcher_argv()
    assert argv[argv.index("--on-complete") + 1] == "/some/hook.sh"
    assert argv[argv.index("--agent-id") + 1] == "acc210c01c43a9e6b"
    assert argv[argv.index("--artifact-path") + 1] == "/some/artifact"


def test_a_call_with_no_on_complete_env_var_is_byte_identical_to_before(call):
    """The regression this task must not cause: the eighteen callers that export nothing
    get exactly the argv they get today."""
    result = call(
        *_flags(call, **{"--exclude-ids": "pre1,pre2"}), "--artifact-path", "/some/artifact"
    )

    assert result.returncode == 0
    argv = call.watcher_argv()
    assert argv == [
        "--name", "invoke the project-finish-line skill for the example-product project.",
        "--label", "example-product",
        "--cwd", str(call.root),
        "--reporter", "generic",
        "--artifact-path", "/some/artifact",
        "--exclude-ids", "pre1,pre2",
        "--notify", str(call.notifier),
    ]


def test_omitting_the_on_complete_env_var_never_trips_the_missing_required_flag_guard(call):
    result = call(*_flags(call))

    assert result.returncode == 0
    assert "missing required" not in result.stderr


def test_the_hook_reaches_every_launcher_without_one_being_edited():
    """The leverage claim the passthrough exists for, proved rather than asserted.

    "No launcher is edited" is only worth anything if the launchers are reached anyway, so
    both halves are checked here and neither on its own is the claim: every `launcher.sh`
    that spawns a model run (`claude --bg`) — the only kind of run this library's watcher
    has anything to watch — names this file as its detach home (so the appended flag
    reaches it), and none of them mentions the hook at all (so none was edited to relay
    it). Discovered by the wiring rather than by a recited list, the same way the
    keep-awake inheritance test below discovers its callers — a launcher that merely
    mentions this library is not a caller.

    Scoped to `claude --bg` launchers, not every `launcher.sh` on disk: `product-docs` spawns no
    model and holds no prompt — it hands its walk to `core/tools/chain.py --start`, a synchronous
    Python entrypoint —
    so it is not a caller of this library at all, the same way a launcher that never
    sources this file today is not one. `claude --bg` is the discoverable trait that
    actually needs a completion watcher; "every `launcher.sh`" was true only because every
    launcher happened to share that trait until this one did not.
    """
    launchers_dir = _LIB.resolve().parents[1] / "launchers"

    def _spawns_a_model(path):
        """`claude --bg` OR the adapter's own `--shape background` (Task 19: every launcher that
        used to spell `claude --bg` in its own shell text now builds its argv through
        `agent_run.py`'s one adapter instead, `--shape background` in place of the literal verb —
        `core/tools/agent_run.py`'s `ClaudeAdapter` is what turns that shape into `claude --bg`)
        on an EXECUTABLE line, never in prose.

        Searching the whole file made a launcher's own comments decide what it does. Every
        launcher here carries a header block explaining itself, and `product-skeleton`'s says it
        spawns nothing *by contrast with* the siblings that do — naming `claude --bg` to do it. So
        the one launcher that must not be selected was selected, by the sentence saying so.
        `test_product_skeleton.py`'s `_bash_code_lines` had already met this locally, for the same
        reason and in the same words: "the header block is 75 lines of prose about `claude --bg`
        and would trip every rule below on its own."
        """
        for line in path.read_text().splitlines():
            stripped = line.lstrip()
            if not stripped or stripped.startswith("#"):
                continue
            code = line.split(" #", 1)[0]
            if "claude --bg" in code or "--shape background" in code:
                return True
        return False

    every_launcher = sorted(
        p for p in launchers_dir.glob("*/launcher.sh") if _spawns_a_model(p)
    )
    sourcing = [
        p for p in every_launcher if _declares_the_shared_detach_home(p.read_text())
    ]

    assert every_launcher, "no launcher found — this test would pass vacuously"
    unreached = sorted(p.parent.name for p in set(every_launcher) - set(sourcing))
    assert not unreached, (
        f"launchers the passthrough cannot reach, because they do not source the shared "
        f"home: {unreached}"
    )

    for path in sourcing:
        source = path.read_text()
        assert "--on-complete" not in source, (
            f"{path.parent.name} passes the flag itself — the passthrough was supposed to "
            "reach it unedited"
        )
        assert "DETACH_WATCHER_ON_COMPLETE" not in source, (
            f"{path.parent.name} relays the variable itself — the passthrough was supposed "
            "to reach it unedited"
        )


# --- the launcher-selection predicate itself (CP-7 — the reach change must not empty this) ----


def test_the_launcher_sweep_finds_every_launcher_that_sources_the_shared_home():
    """The predicate the sweeps above key on, exercised directly and named by path.

    Corrected from the plan's pinned count of 21: that figure is CP-1's broader retired-walk
    match (`core/launchers/test_core_resolution.py`'s `_RETIRED_TOOLS_WALK`), which also counts
    `product-card` — its WATCHER default reached through that expression while the launcher
    declares no `DETACH_LIB` of its own (its own header says so: "this is the one file with no
    DETACH_LIB beside it to anchor the comment on"). The set that actually declares the shared
    detach home was 21 the day this was corrected, was 23 on 2026-09-12, the day two launchers
    joined it — `core/launchers/shukuba-refine/` and `core/launchers/stations-from-seed/` — and
    was 24 on 2026-09-14, the day one more launcher joined, and is **25** on
    2026-09-15, the day `core/launchers/skill/` joined (`c769887a`) — which left this literal at 24
    until the next run of this suite found it — and is **22** on 2026-09-17, the day
    `shukuba-refine`, `shukuba-retire` and `stations-from-seed` were deleted, each now launched
    through `core/launchers/skill/` from its skill's `launcher.md` — and was **23** later that day, when
    `core/launchers/nemawashi-unpick/` joined, and is **22** again once it was deleted, un-pick
    launching through `core/launchers/skill/` too — and is **14** once the eight product document
    launchers (`launch-product-prd`, `project-finish-line`, `product-srs`, `product-uxd`,
    `product-design`, `product-content`, `product-fdr`, `product-architecture`) were deleted the same
    day, each of those skills launching through `core/launchers/skill/` from its `launcher.md` — and is **13**
    once `ad-hoc-flow` was retired on 2026-09-18 with the `ad-hoc-implementation` skill it ran — and is **12**
    on 2026-09-24, the day that launcher was deleted — and is **9** on 2026-09-25, the day `skill`,
    `companion-self-answer` and `product-sdd` moved their Claude run to a detached `--print` process
    and their `DETACH_LIB` to `detach_process_watcher.sh` — and is **8** later that day, when
    `core/launchers/seeds-from-product-docs/` was deleted, the skill launching through
    `core/launchers/skill/` from its `launcher.md` — and is **7** on 2026-09-30, when
    `core/launchers/kensaiapp-writing-bar/` was deleted the same way — and is **5** later that
    day, when `core/launchers/experience-visual/` and `core/launchers/experience-voice/` were too —
    and is **3** on 2026-10-24, when `core/launchers/seeds-from-idea/` was deleted, the skill having
    no launcher of its own. Each declares `DETACH_LIB` the same way every
    sibling in this set does, so all three join the sweep rather than breaking it. Verified by grepping every `launcher.sh` for the exact `DETACH_LIB=`
    assignment naming `detach_watcher.sh`.
    """
    launchers_dir = _LIB.resolve().parents[1] / "launchers"
    found = _launchers_declaring_the_shared_detach_home(launchers_dir)
    names = sorted(p.parent.name for p in found)

    assert len(names) == 3, f"expected 3 launchers declaring the shared home, found {len(names)}: {names}"
    assert "product-card" not in names, (
        "product-card reaches core/tools/ through its WATCHER default only — it declares no "
        "DETACH_LIB and must not be swept in as a caller of this library"
    )
    assert "cold-read" in names and "launch-eval-fix" in names, (
        "two known callers are missing from the sweep — the predicate is not matching real "
        "declarations"
    )


@pytest.fixture
def _empty_launchers_tree(tmp_path):
    launchers_dir = tmp_path / "launchers"
    non_caller = launchers_dir / "some-launcher"
    non_caller.mkdir(parents=True)
    (non_caller / "launcher.sh").write_text(
        "#!/usr/bin/env bash\nset -euo pipefail\necho no shared home declared here\n"
    )
    return launchers_dir


def test_the_launcher_sweep_fails_when_it_matches_nothing(_empty_launchers_tree):
    """The selection predicate applied to a tree with no launcher declaring the shared home
    fails the control rather than reporting compliance. A filter matching nothing is
    indistinguishable from a fleet that complies — so the sweep must refuse the empty result
    itself, not just happen to be given a non-empty tree today."""
    with pytest.raises(AssertionError, match="pass vacuously"):
        _launchers_declaring_the_shared_detach_home(_empty_launchers_tree)


def test_each_launcher_declared_library_path_is_the_real_shared_home():
    """For every launcher the sweep finds, the `detach_watcher.sh` it names resolves to the one
    real `core/tools/detach_watcher.sh`, derived from the launcher's own location rather than
    from a hard-coded number of parent steps."""
    launchers_dir = _LIB.resolve().parents[1] / "launchers"
    core_dir = _LIB.resolve().parents[1]

    for path in _launchers_declaring_the_shared_detach_home(launchers_dir):
        resolved = _shared_detach_home_for(path)
        assert resolved == _LIB.resolve(), (
            f"{path.parent.name}'s declared home does not resolve to the library under test"
        )
        assert resolved.exists(), f"{path.parent.name}'s declared home does not exist: {resolved}"

    # The resolution names no fixed depth: applied to a launcher one level deeper than any real
    # one, it still lands on the same <CORE> — proving the mechanism, not just today's flat tree.
    nested_dir = launchers_dir / "development" / "specs"
    assert _core_dir_for(nested_dir) == core_dir, (
        "the resolution counted a fixed number of parent steps instead of finding /launchers/"
    )


# --- an unrecognized argument (the library's own bug guard) -----------------------------


def test_an_unrecognized_argument_returns_1_naming_itself(call):
    result = call(*_flags(call), "--not-a-real-flag", "value")

    assert result.returncode != 0
    assert "--not-a-real-flag" in result.stderr
    assert call.watcher_argv(wait=2.5) == []


# --- the log file ----------------------------------------------------------------------


def test_log_file_is_created_named_from_log_stem_and_carries_both_streams(call):
    call(*_flags(call, **{"--log-stem": "example-product"}))

    # Wait for the content, not for the size to settle: a log whose size holds still can still
    # lack the line the watcher has not written yet. Each poll re-discovers the log and reads it
    # once, directly, so the one deadline covers the whole wait (call.logs() waits on its own).
    logs_dir = call.root / "system" / "logs"
    observed = {}

    def _log_has_both_streams():
        logs = [
            p
            for p in (logs_dir.glob("watch-*.log") if logs_dir.exists() else [])
            if p.name.startswith("watch-example-product-")
        ]
        if len(logs) != 1:
            return False
        body = logs[0].read_text()
        if "watcher-stub: stdout line" not in body or "watcher-stub: stderr line" not in body:
            return False
        observed["logs"], observed["body"] = logs, body
        return True

    assert _wait_until(_log_has_both_streams, timeout=10.0)
    logs, body = observed["logs"], observed["body"]
    assert len(logs) == 1
    assert "watcher-stub: stdout line" in body
    assert "watcher-stub: stderr line" in body      # 2>&1, not just stdout


# --- the two-condition else branch ------------------------------------------------------


def test_missing_watcher_names_only_the_watcher(call):
    result = call(*_flags(call, **{"--watcher": str(call.root / "no_such_watcher.py")}))

    assert result.returncode == 0
    assert "no watcher at" in result.stdout
    assert "no notifier at" not in result.stdout
    assert call.watcher_argv(wait=2.5) == []
    assert call.logs() == []


def test_missing_notifier_names_only_the_notifier(call):
    result = call(*_flags(call, **{"--notifier": str(call.root / "no_such_notifier.sh")}))

    assert result.returncode == 0
    assert "no notifier at" in result.stdout
    assert "no watcher at" not in result.stdout
    assert call.watcher_argv(wait=2.5) == []
    assert call.logs() == []


def test_a_present_but_non_executable_notifier_names_only_the_notifier(call):
    """The happy-path guard is `-x` on the notifier, not `-f` — a notifier that exists but
    cannot be run is as unusable as one that is absent, and it is the *notifier* half that
    is broken. A branch that reported the file's mere presence as good enough would spawn a
    watcher that can never deliver its ping.
    """
    dud = call.root / "present_but_not_executable.sh"
    dud.write_text("#!/usr/bin/env bash\ntrue\n")
    dud.chmod(0o644)

    result = call(*_flags(call, **{"--notifier": str(dud)}))

    assert result.returncode == 0
    assert "no notifier at" in result.stdout
    assert "no watcher at" not in result.stdout
    assert call.watcher_argv(wait=2.5) == []
    assert call.logs() == []


def test_both_missing_names_both(call):
    result = call(
        *_flags(
            call,
            **{
                "--watcher": str(call.root / "no_such_watcher.py"),
                "--notifier": str(call.root / "no_such_notifier.sh"),
            },
        )
    )

    assert result.returncode == 0
    assert "no watcher at" in result.stdout
    assert "no notifier at" in result.stdout
    assert call.watcher_argv(wait=2.5) == []
    assert call.logs() == []


# --- --keep-awake ------------------------------------------------------------------------


def test_keep_awake_starts_one_caffeinate_and_binds_it_to_no_pid_number(call):
    """One hold per call, and `caffeinate` itself waits on nothing: `-w` takes a pid NUMBER,
    which the kernel reissues, so the release is the poller's job (below) and not a flag's.
    The starter is handed in, so what it was asked to start is read the moment the call
    returns — there is no detached process whose record has to be waited for."""
    hold = call.install_fake_starter()
    call.install_ps(["START"])

    result = call(*_flags(call), "--keep-awake")

    assert result.returncode == 0
    assert call.starter_calls() == 1
    argv = call.starter_argv()
    assert "-i" in argv and "-s" in argv
    assert "-w" not in argv, f"a bare-pid wait survives in caffeinate's argv: {argv}"
    assert call.released(hold) == -signal.SIGTERM


def test_keep_awake_keys_its_release_on_the_watchers_own_pid_not_some_other_process(call):
    """`--keep-awake` must hold the Mac awake *for the run*, and the only handle on the
    run's lifetime is the detached watcher — so the identity the release keys on has to name
    the process that was just spawned. Keying on anything else (the calling shell's `$$`, a
    stale `$!` from an earlier job) still produces exactly one `caffeinate`, which is why the
    count assertion above cannot catch it: the keep-awake would simply end when the *wrong*
    process ends. Pinned against the pid the stub watcher records for itself.
    """
    hold = call.install_fake_starter()
    call.install_ps(["START", "GONE"])

    result = call(*_flags(call), "--keep-awake")

    assert result.returncode == 0
    assert call.starter_calls() == 1, "the keep-awake never started its hold"
    assert call.released(hold) == -signal.SIGTERM
    watcher_pid = call.watcher_pid()
    assert watcher_pid is not None, "the stub watcher never ran, so there is no pid to key on"
    checks = call.ps_argv()
    assert len(checks) == 2, f"expected the capture and one poller check, got: {checks}"
    assert all("-o lstart=" in line and "-p" in line for line in checks), (
        f"expected `ps -o lstart= -p <pid>` identity checks, got: {checks}"
    )
    assert all(line.split()[-1] == watcher_pid for line in checks), (
        f"the identity check named a pid other than the spawned watcher's: {checks}"
    )


def test_no_keep_awake_flag_means_zero_caffeinate_invocations(call):
    call.install_fake_starter()

    call(*_flags(call))

    assert call.starter_calls() == 0


def test_keep_awake_on_the_else_branch_binds_no_caffeinate_and_says_so(call):
    call.install_fake_starter()

    result = call(*_flags(call, **{"--watcher": str(call.root / "nope.py")}), "--keep-awake")

    assert result.returncode == 0
    assert call.starter_calls() == 0
    assert "keep-awake needs a completion watcher" in result.stdout


def test_a_starter_that_starts_no_hold_says_so_and_polls_nothing(call):
    """The "caffeinate not found" fallback, reached through the port rather than by masking the
    machine's own tool off `PATH`: a starter that answers with no pid has started nothing, so
    there is nothing to bind a poller to and the call says it skipped."""
    call.install_fake_starter()
    call.env["FAKE_HOLD_PID"] = ""
    call.install_ps(["START"])

    result = call(*_flags(call), "--keep-awake")

    assert result.returncode == 0
    assert call.starter_calls() == 1
    assert "(keep-awake: caffeinate not found — not macOS? — skipped)" in result.stdout
    assert "Keep-awake:" not in result.stdout


# --- --noun (the caller-supplied report noun, defaulting to "run") ----------------------


def test_no_noun_reads_exactly_as_v1_0_0(call):
    """The default (`--noun` omitted) must read identically to the pre-Task-3 wording — the
    25 pre-existing tests characterize this already; this test pins the exact strings so a
    regression here is caught even if none of the older tests happens to grep this text."""
    call.install_caffeinate()

    result = call(*_flags(call), "--keep-awake")

    assert "when the run stops" in result.stdout
    assert "held until the run stops" in result.stdout


def test_noun_pass_produces_when_the_pass_stops_and_held_until_the_pass_stops(call):
    call.install_caffeinate()

    result = call(*_flags(call), "--keep-awake", "--noun", "pass")

    assert "when the pass stops" in result.stdout
    assert "held until the pass stops" in result.stdout
    assert "when the run stops" not in result.stdout
    assert "held until the run stops" not in result.stdout


def test_else_branch_messages_are_unaffected_by_noun(call):
    result = call(
        *_flags(call, **{"--watcher": str(call.root / "nope.py")}), "--noun", "pass"
    )

    assert "no watcher at" in result.stdout
    assert "pass" not in result.stdout


def test_else_branch_keep_awake_message_stays_noun_free_with_noun_given(call):
    call.install_caffeinate()

    result = call(
        *_flags(call, **{"--watcher": str(call.root / "nope.py")}), "--keep-awake", "--noun", "pass"
    )

    assert "keep-awake needs a completion watcher" in result.stdout
    assert "pass" not in result.stdout


def test_else_branch_no_notifier_message_stays_noun_free_with_noun_given(call):
    """Plan Task 3 names all three else-branch messages as noun-free — `no watcher at …`,
    `no notifier at …` and the keep-awake line. The missing-watcher and keep-awake halves are
    covered above; this pins the missing-notifier half."""
    result = call(
        *_flags(call, **{"--notifier": str(call.root / "nope.sh")}), "--noun", "pass"
    )

    assert "no notifier at" in result.stdout
    assert "pass" not in result.stdout


def test_omitting_noun_never_trips_the_missing_required_flag_guard(call):
    result = call(*_flags(call))

    assert result.returncode == 0
    assert "missing required" not in result.stderr


# --- the function never fails its caller --------------------------------------------------


def test_exit_zero_on_the_happy_path(call):
    result = call(*_flags(call))
    assert result.returncode == 0


def test_exit_zero_on_the_else_branch(call):
    result = call(*_flags(call, **{"--watcher": str(call.root / "nope.py")}))
    assert result.returncode == 0


def test_exit_zero_with_keep_awake_on_either_branch(call):
    call.install_caffeinate()

    happy = call(*_flags(call), "--keep-awake")
    unhappy = call(*_flags(call, **{"--notifier": str(call.root / "nope.sh")}), "--keep-awake")

    assert happy.returncode == 0
    assert unhappy.returncode == 0


# --- a slow watcher start (a loaded parallel run) ------------------------------------------
#
# The library backgrounds the watcher and returns, so the read-back polls for what the stub
# records. On 2026-09-19 three read-backs failed in full `-n 32` runs of `core/tools/`, a
# different three each run, while the file alone passed: the stub had not started inside the
# read-back's window. The stub here starts 3s late, past the window those runs failed in.


def test_the_watchers_argv_is_read_back_after_a_slow_start(call):
    call.slow_start(3)
    result = call(*_flags(call, **{"--exclude-ids": ""}))

    assert result.returncode == 0
    argv = call.watcher_argv()
    assert argv[argv.index("--exclude-ids") + 1] == ""


def test_the_watchers_pid_is_read_back_after_a_slow_start(call):
    call.slow_start(3)
    result = call(*_flags(call))

    assert call.watcher_pid() == _reported_pid(result)


# --- DETACH_WATCHER_PID (the spawned watcher's PID, published for a fan-out caller) -----


def test_detach_watcher_pid_matches_the_spawned_watchers_own_pid(call):
    result = call(*_flags(call))

    watcher_pid = call.watcher_pid()
    assert watcher_pid is not None, "the stub watcher never ran, so there is no pid to compare"
    assert _reported_pid(result) == watcher_pid


def test_detach_watcher_pid_is_empty_on_the_else_branch_missing_watcher(call):
    result = call(*_flags(call, **{"--watcher": str(call.root / "nope.py")}))

    assert _reported_pid(result) == ""


def test_detach_watcher_pid_is_empty_on_the_else_branch_missing_notifier(call):
    result = call(*_flags(call, **{"--notifier": str(call.root / "nope.sh")}))

    assert _reported_pid(result) == ""


# --- DETACH_WATCHER_START — the other half of the identity, for a fan-out caller ---------
#
# The pid alone is not the handle this library releases on: its own poller keys on the pid
# PAIRED with the start time it had at spawn, because the kernel reissues pid numbers. A
# fan-out caller building the same poller over N watchers therefore needs both halves, and the
# start time is the half it cannot safely re-derive — a `ps` run after the call is exactly the
# window the pairing closes. So the library captures it at spawn and publishes it.


def test_detach_watcher_start_is_the_spawned_watchers_own_start_time(call):
    """Compared against `ps` for the same pid rather than against a literal: the format is
    the platform's (`ps -o lstart=`), and pinning a format here would test macOS, not this
    library. A sleepy watcher stub keeps the process alive long enough to be asked."""
    call.use_sleepy_watcher()

    result = call(*_flags(call))

    pid = _reported_pid(result)
    assert pid, "no pid was published, so there is no identity to pair"
    live = subprocess.run(
        ["ps", "-o", "lstart=", "-p", pid], capture_output=True, text=True
    ).stdout.strip()
    assert live, "the watcher was gone before its start time could be read independently"
    assert _reported_start(result).strip() == live, (
        f"published start {_reported_start(result)!r} is not the spawned watcher's own {live!r}"
    )


def test_detach_watcher_start_is_empty_on_the_else_branch_missing_watcher(call):
    """It travels with the pid: where there is no watcher to pair, there is no half-identity
    left behind for a caller to mistake for one."""
    result = call(*_flags(call, **{"--watcher": str(call.root / "nope.py")}))

    assert _reported_pid(result) == ""
    assert _reported_start(result) == ""


def test_detach_watcher_start_is_empty_on_the_else_branch_missing_notifier(call):
    result = call(*_flags(call, **{"--notifier": str(call.root / "nope.sh")}))

    assert _reported_pid(result) == ""
    assert _reported_start(result) == ""


def test_two_successive_calls_each_leave_their_own_pid(call):
    """The shape a fan-out caller uses: call the function once per reader in the same
    sourcing session, reading `DETACH_WATCHER_PID` after each call. The second call's
    value must overwrite the first, not collide with it — the two backgrounded watchers
    are distinct processes, so their pids are distinct too."""
    wrapper = call.root / "call_twice.sh"
    wrapper.write_text(TWO_CALLS_STUB.format(lib=_LIB))
    wrapper.chmod(0o755)

    result = subprocess.run(
        [str(wrapper), *_flags(call)],
        cwd=str(call.root),
        capture_output=True,
        text=True,
        env=call.env,
    )

    assert result.returncode == 0
    first = next(l.split("=", 1)[1] for l in result.stdout.splitlines() if l.startswith("FIRST="))
    second = next(l.split("=", 1)[1] for l in result.stdout.splitlines() if l.startswith("SECOND="))
    assert first and second
    assert first != second


def test_keep_awake_keys_its_release_on_the_pid_detach_watcher_pid_reports(call):
    """Nothing else about the function changes: `--keep-awake`'s release still keys on the
    same pid the function publishes as `DETACH_WATCHER_PID` — a fan-out caller reading that
    variable per call is reading the process this hold is tied to."""
    hold = call.install_fake_starter()
    call.install_ps(["START", "GONE"])

    result = call(*_flags(call), "--keep-awake")

    assert call.starter_calls() == 1, "the keep-awake never started its hold"
    assert call.released(hold) == -signal.SIGTERM
    reported = _reported_pid(result)
    checks = call.ps_argv()
    assert len(checks) == 2, f"expected the capture and one poller check, got: {checks}"
    assert all(line.split()[-1] == reported for line in checks), (
        f"the identity check named a pid other than the reported one ({reported}): {checks}"
    )


# --- all four values at once (the plan's headline: additively) --------------------------


def test_all_four_caller_values_land_together(call):
    """The plan's overall goal in one call — "the home takes the four caller values eleven
    launchers pass, additively". Each of the four must land without interfering with the
    others: the alias spelling survives into the argv, `--head-repo` rides alongside it, the
    caller's noun replaces "run" in both lines that name it, and the spawned pid is published
    and is the one `--keep-awake` binds."""
    hold = call.install_fake_starter()
    call.install_ps(["START"])

    result = call(
        *_flags(call),
        "--product-path", "/some/product",
        "--head-repo", "/some/repo",
        "--noun", "round",
        "--keep-awake",
    )

    assert result.returncode == 0

    argv = call.watcher_argv()
    assert argv[argv.index("--product-path") + 1] == "/some/product"
    assert argv[argv.index("--head-repo") + 1] == "/some/repo"
    assert "--artifact-path" not in argv

    assert "when the round stops" in result.stdout
    assert "held until the round stops" in result.stdout
    assert "when the run stops" not in result.stdout

    reported = _reported_pid(result)
    assert reported == call.watcher_pid()
    assert call.starter_calls() == 1
    assert "-w" not in call.starter_argv(), (
        f"a bare-pid wait survives in caffeinate's argv: {call.starter_argv()}"
    )
    assert call.released(hold) == -signal.SIGTERM


# --- sourcing alone --------------------------------------------------------------------


def test_sourcing_the_file_alone_has_no_side_effect(tmp_path):
    result = subprocess.run(
        ["bash", "-c", f'source "{_LIB}"'],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""
    assert not (tmp_path / "system").exists()


# --- executable-by-source, not by-run -----------------------------------------------------


def test_the_library_file_exists():
    assert _LIB.is_file()


# --- the keep-awake releases on identity, not on a pid number ---------------------------
#
# `caffeinate -i -s -w <pid>` waits on a pid NUMBER. When the watched process exits and the
# kernel reissues that number, the hold rides whatever unrelated process now answers to it —
# measured 2026-08-12 at 2h51m past its flow's end, killed by hand
# (`docs/proposals/archive/keep-awake-keys-on-identity/rationale.md`). Six launchers source
# this library and carry no caffeinate of their own, so this is the binding they all run.


def test_keep_awake_holds_while_the_watched_process_is_still_itself(call):
    """The under-live half, which a release test alone cannot see: while the watched pid is
    still answering as the same process, the hold must stay up. The scripted `ps` answers
    `START` — the identity captured at spawn — four times and then nothing, and records at
    each answer whether the hold was alive. So the test reads, after the release, that the hold
    was up at every check the watcher was still itself, and that it ended only after the last
    one: no moment is sampled, and no deadline decides anything."""
    hold = call.install_fake_starter()
    call.install_ps(["START", "START", "START", "START"])

    result = call(*_flags(call), "--keep-awake")

    assert result.returncode == 0
    assert call.starter_calls() == 1, "caffeinate never started"
    assert call.released(hold) == -signal.SIGTERM, (
        "the hold never released after the watched process was gone"
    )
    states = call.ps_hold_states()
    assert len(states) == 5, (
        "expected the capture, three re-checks that found the watcher still itself, and the "
        f"check that found it gone; the poller made {len(states) - 1} checks"
    )
    assert states[:4] == ["alive"] * 4, (
        f"the hold was released while the watcher was still itself: {states}"
    )


def test_a_recycled_pid_does_not_hold_the_machine_awake(call):
    """The defect this station exists to fix. The same pid number keeps answering — a live
    process is there — but it reports a different start time, which is exactly what a
    reissued pid looks like from outside. The hold must release on that, not ride it: the
    scripted `ps` keeps answering `OTHER` for three more checks, so a poller that rode it would
    release only at exhaustion, three calls later."""
    hold = call.install_fake_starter()
    call.install_ps(["START", "OTHER", "OTHER", "OTHER", "OTHER"])

    result = call(*_flags(call), "--keep-awake")

    assert result.returncode == 0
    assert call.starter_calls() == 1, "caffeinate never started"
    assert call.released(hold) == -signal.SIGTERM
    checks = call.ps_argv()
    assert len(checks) == 2, (
        "the keep-awake held on after the watched pid was answered by an unrelated process: "
        f"it released only after {len(checks)} identity checks"
    )
    assert "-o lstart=" in checks[0] and "-p" in checks[0], (
        f"expected a `ps -o lstart= -p <pid>` identity check, got: {checks[0]!r}"
    )


# --- the poll interval a migrating caller brings with it ---------------------------------
#
# Each launcher that hand-copied this block documents its own `LAUNCH_<X>_KEEPAWAKE_POLL_SECONDS`
# in its header, and two suites set it by that name (`test_ad_hoc_flow.py` and `test_product_srs.py`, both since retired).
# Migrating them onto this home must not rename their knob out from under them, so the caller may
# hand its already-resolved value in as a flag; the env default is what a caller that passes
# nothing still gets, unchanged for the six already here.


def test_keepawake_poll_seconds_flag_sets_the_pollers_interval(call):
    """The flag wins over the env var, proved by the interval the poller actually asked
    `sleep` for: the env says 30 and the flag 0.1. The `sleep` on the poller's `PATH` records
    its argument and returns at once, so the interval is read as a value rather than waited
    out as a length of time."""
    hold = call.install_fake_starter()
    call.install_ps(["START", "START", "START"], poll_seconds="30")

    result = call(*_flags(call), "--keep-awake", "--keepawake-poll-seconds", "0.1")

    assert result.returncode == 0
    assert call.starter_calls() == 1, "caffeinate never started"
    assert call.released(hold) == -signal.SIGTERM
    assert call.sleeps() == ["0.1", "0.1"], (
        f"the poller slept on something other than the flag's 0.1s: {call.sleeps()}"
    )


def test_omitting_keepawake_poll_seconds_leaves_the_env_default_in_force(call):
    """The other half, and the one that keeps the six callers already on this home unchanged:
    a call that passes no flag still polls on `DETACH_WATCHER_KEEPAWAKE_POLL_SECONDS`."""
    hold = call.install_fake_starter()
    call.install_ps(["START", "START", "START"], poll_seconds="0.7")

    result = call(*_flags(call), "--keep-awake")

    assert result.returncode == 0
    assert call.starter_calls() == 1, "caffeinate never started"
    assert call.released(hold) == -signal.SIGTERM
    assert call.sleeps() == ["0.7", "0.7"], (
        f"the env var no longer sets the poll interval for a caller that passes no flag: {call.sleeps()}"
    )


def test_keepawake_poll_seconds_never_trips_the_missing_required_flag_guard(call):
    """It is optional. A call that omits it is a normal call, not a caller bug."""
    result = call(*_flags(call))

    assert result.returncode == 0
    assert "missing required" not in result.stderr


def test_the_library_neither_uses_nor_documents_a_bare_pid_wait(call):
    """Read off the library's own source, in two halves. No caffeinate may be started with a
    `-w <pid>` wait — the binding that outlived its run — and the header must tell the next
    reader what the release keys on instead. A header still describing the old mechanism is a
    wrong answer to the only question a reader opens it with. Comment lines are excluded from
    the first half on purpose: the header EXPLAINS the binding it replaced, and a check that
    cannot tell an explanation from an invocation would forbid recording the reason."""
    source = _LIB.read_text()
    body = "\n".join(l for l in source.splitlines() if not l.lstrip().startswith("#"))

    # Two lines make the invocation: the real starter detaches `caffeinate` with the argv it is
    # handed, and the keep-awake hands it that argv through the starter port.
    caffeinate_calls = [l for l in body.splitlines() if "nohup caffeinate" in l]
    assert caffeinate_calls, "the library no longer invokes caffeinate at all"
    starter_calls = [l for l in body.splitlines() if '"$starter"' in l]
    assert starter_calls, "the keep-awake no longer starts its hold through the starter port"
    for line in caffeinate_calls + starter_calls:
        assert " -w " not in line, f"a bare-pid caffeinate wait survives: {line.strip()!r}"

    header = "\n".join(
        itertools.takewhile(
            lambda l: l.startswith("#") or not l.strip(), source.splitlines()
        )
    )
    assert "start time" in header.lower(), (
        "the header does not say what the keep-awake's release keys on now"
    )


# The launchers that source this library and bind the single-watcher keep-awake, re-measured
# 2026-09-30 by the declaration `_declares_the_shared_detach_home` reads, once the last three of
# the 2026-08-22 set (`kensaiapp-writing-bar`, `experience-visual`, `experience-voice`) were deleted
# that day, and once more on 2026-10-24, when `seeds-from-idea`'s was deleted; `cold-read` sources
# it too and is held below as the fan-out caller. Named rather than
# merely counted: the claim is that each of THESE inherits the fix, and a set that shrinks
# silently would still satisfy a count.
_LIBRARY_CALLERS = {
    "launch-eval-fix",
    "launch-skill-evals",
}


# The caller whose keep-awake spans a SET of watchers rather than one, so it runs its own
# poller over the identity pairs this library publishes and passes no `--keep-awake`. Named,
# because the difference is a decision about what a fan-out is — not something a pattern over
# launcher sources could tell from a copy that simply never migrated.
_FAN_OUT_CALLERS = {"cold-read"}


def test_the_launchers_that_source_this_library_inherit_its_keep_awake_binding():
    """The leverage claim, proved rather than asserted: these launchers get the identity-keyed
    release **without being edited**. Three links, all checked here — each names this exact
    file as its detach home, each carries no caffeinate of its own (so the library's is the
    only keep-awake they can run), and the binding they inherit is identity-keyed rather than
    a bare pid wait. Break any one link and the inheritance is not real.

    The known set is a floor, not a ceiling: a launcher migrating onto this home later joins
    it and is held to the same three links.

    One caller is held to a different third link, and it is named rather than pattern-matched.
    `cold-read` binds ONE keep-awake across N watchers, so it passes no `--keep-awake` to this
    library at all — it collects the identity pair each call publishes and runs its own poller
    over the set. It therefore carries a caffeinate of its own **by design**, and the
    no-caffeinate check would be asserting the opposite of what its migration was for. What it
    is held to instead is the same rule read at its own level: its poller keys on
    `ps -o lstart= -p`, the identity check, never on a bare pid — which is exactly what it
    would have inherited had it been able to pass `--keep-awake`.
    """
    launchers_dir = _LIB.resolve().parents[1] / "launchers"
    # Discovered by the wiring, not by the name: a launcher that merely MENTIONS this file —
    # every copy of the keep-awake block now cites it, so the reader knows where the shared one
    # lives — is not a caller, and reading a mention as one made this test fail against eight
    # launchers that had never sourced anything (measured 2026-08-22, after station 2's edit).
    callers = {
        p.parent.name: p
        for p in sorted(launchers_dir.glob("*/launcher.sh"))
        if _declares_the_shared_detach_home(p.read_text())
    }

    missing = _LIBRARY_CALLERS - set(callers)
    assert not missing, f"launchers that stopped sourcing the shared home: {sorted(missing)}"

    for name, path in callers.items():
        source = path.read_text()
        body = "\n".join(l for l in source.splitlines() if not l.lstrip().startswith("#"))

        assert _shared_detach_home_for(path) == _LIB.resolve(), (
            f"{name}'s detach home does not resolve to the library under test"
        )
        assert "detach_completion_watcher" in body, f"{name} sources the home but never calls it"
        if name in _FAN_OUT_CALLERS:
            assert "ps -o lstart= -p" in body, (
                f"{name} runs its own keep-awake over the set but does not key it on the "
                "watchers' identity — the one rule it cannot inherit, it has to carry"
            )
            for line in (l for l in body.splitlines() if "caffeinate" in l):
                assert " -w " not in line, (
                    f"{name}'s own keep-awake waits on a bare pid number: {line.strip()!r}"
                )
        else:
            assert "caffeinate" not in body, (
                f"{name} carries a keep-awake of its own, so it does not inherit the library's"
            )

    library_body = "\n".join(
        l for l in _LIB.read_text().splitlines() if not l.lstrip().startswith("#")
    )
    for line in (l for l in library_body.splitlines() if "caffeinate" in l):
        assert " -w " not in line, (
            f"every caller above inherits a bare-pid wait from the library: {line.strip()!r}"
        )


# --- code-integrity: plan behaviours with no test of their own -----------------------
#
# Derived from the ad-hoc plan
# `system/projects/tools/journey/nemawashi/2026-08-26_the-watcher-reads-a-run-between-turns-as-finished.md`
# § Plan, Task 5, never from the implementation.


def test_both_new_flags_land_without_displacing_cwd_exclude_ids_or_notify(call):
    """Task 5: "Both together → both appear, and `--name`, `--label`, `--cwd`,
    `--reporter`, `--exclude-ids`, `--notify` are all still there." The suite asserts
    --name / --label / --reporter; these three were left unasserted.
    """
    result = call(
        *_flags(call, **{"--exclude-ids": "pre1,pre2"}),
        "--multi-turn",
        "--done-when-exists", "/some/done",
    )

    assert result.returncode == 0
    argv = call.watcher_argv()
    assert "--multi-turn" in argv
    assert argv[argv.index("--done-when-exists") + 1] == "/some/done"
    assert argv[argv.index("--cwd") + 1] == str(call.root)
    assert argv[argv.index("--exclude-ids") + 1] == "pre1,pre2"
    assert argv[argv.index("--notify") + 1] == str(call.notifier)


# --- the id is the third field, not the last -----------------------------------------------
#   Regression, 2026-08-26. `capture_agent_id` read `$NF`, which was the id for as long as no
#   launcher passed `-n`. The first one that did made the line `backgrounded · <id> · <name>`,
#   so the parse returned the NAME; the watcher was handed a name where it expected an id,
#   matched nothing, and exited at its appear deadline reporting that the run may not have
#   started — while the run itself ran on, healthy and unwatched.


def test_capture_reads_the_id_when_a_name_follows_it(capture):
    """A launcher that passes `-n` puts the session name last on the launch line. The id is
    still the third field, and that is what must come back."""
    assert (
        capture("backgrounded · 6aec7cb2 · sdd-example-product-20260826-150147") == "6aec7cb2"
    )


def test_capture_still_reads_the_id_with_no_name(capture):
    """The shape the parse was originally written for keeps working — `$3` is the id whether or
    not a name follows, so this is not a trade between the two launcher shapes."""
    assert capture("backgrounded · 6aec7cb2") == "6aec7cb2"


def test_capture_reads_the_id_through_ansi_with_a_name(capture):
    """Both hazards at once: `claude --bg` colours its output even when stdout is not a TTY, and
    the name is now last. The escapes come off first, then the third field is taken."""
    line = ("backgrounded · \x1b[36mc823ebf2\x1b[39m · "
            "\x1b[2msdd-example-product-20260826-150147\x1b[22m")
    assert capture(line) == "c823ebf2"


def test_capture_never_returns_a_session_name(capture):
    """The failure this guards is silent: a name is a plausible-looking string, so a watcher
    handed one polls for something that will never appear and calls it a run that did not
    start. Nothing that looks like a name may come out of this parse."""
    got = capture("backgrounded · 6aec7cb2 · sdd-example-product-20260826-150147")

    assert not got.startswith("sdd-")
    assert got == "6aec7cb2"


def test_the_watcher_starts_and_its_pid_is_recorded_with_python3_stubbed_to_fail(call):
    stub = call.root / "bin" / "python3"
    stub.write_text(f'#!/bin/sh\necho called >> "{call.root / "python3-marker"}"\nexit 1\n')
    stub.chmod(0o755)

    result = call(*_flags(call))

    assert result.returncode == 0, result.stderr
    assert call.watcher_argv(), result.stderr
    assert _reported_pid(result)
    assert not (call.root / "python3-marker").exists()
