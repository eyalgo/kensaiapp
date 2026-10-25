"""Tests for walk_stop.py — the one owner of a launch's process identity and of stopping it.

Two kinds of case. The real-process ones start a `sleep` in its own session, the way every launcher
starts a run, and prove a stop reaches it only while its pid still has the recorded start time. The
fakes are one per port the module is given: a recording `ProcessTable` and a dict-backed `files`.
"""

from __future__ import annotations

import contextlib
import json
import os
import signal
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

import walk_stop
import watch_process

TOOLS = Path(__file__).resolve().parent
SOME_START = "Fri Oct  2 15:24:58 2026"
IDENTITY_FILE = "/logs/chain-x-walk-1.identity.json"


class FakeFiles:
    """A dict-backed `files`: a missing path raises `FileNotFoundError`, as the real one does."""

    def __init__(self, contents: dict[str, str] | None = None) -> None:
        self.contents = dict(contents or {})

    def read_text(self, path: str) -> str:
        if path not in self.contents:
            raise FileNotFoundError(path)
        return self.contents[path]

    def write_text(self, path: str, text: str) -> None:
        self.contents[path] = text


class FakeTable:
    """A recording `ProcessTable`: pid → start, pid → `started_at`, and every `stop_group` call in
    order."""

    def __init__(self, starts: dict[int, str | None] | None = None,
                 started: dict[int, str] | None = None) -> None:
        self.starts = dict(starts or {})
        self.started = dict(started or {})
        self.stopped: list[int] = []

    def start_time(self, pid: int) -> str | None:
        return self.starts.get(pid)

    def started_at(self, pid: int) -> str | None:
        return self.started.get(pid)

    def stop_group(self, pid: int) -> None:
        self.stopped.append(pid)
        self.starts.pop(pid, None)


def identity_json(run: tuple[int, str | None] | None,
                  watcher: tuple[int, str | None] | None) -> str:
    def part(entry):
        return None if entry is None else {"pid": entry[0], "start": entry[1]}

    return json.dumps({"run": part(run), "watcher": part(watcher)})


def files_holding(run=None, watcher=None) -> FakeFiles:
    return FakeFiles({IDENTITY_FILE: identity_json(run, watcher)})


@contextlib.contextmanager
def sleeping_process():
    """A `sleep` that leads its own session, reaped on the way out."""
    process = subprocess.Popen(["sleep", "60"], start_new_session=True)
    try:
        yield process
    finally:
        if process.poll() is None:
            process.kill()
        process.wait()


# --- real processes ----------------------------------------------------------


def test_a_recorded_live_run_is_stopped_with_its_group():
    table = walk_stop.ProcessTable()
    with sleeping_process() as process:
        files = FakeFiles({IDENTITY_FILE: walk_stop.identity_text(table, process.pid, None)})

        stop = walk_stop.stop_launch(files, table, IDENTITY_FILE, "audit 1")

        assert stop.run == walk_stop.Outcome.STOPPED
        assert process.wait(timeout=10) is not None


def test_a_stop_reaches_a_child_in_the_recorded_runs_process_group():
    """Task 1 requires stopping the group, including the provider under the run wrapper."""
    wrapper = (
        "import signal, subprocess\n"
        "signal.signal(signal.SIGINT, lambda *_: None)\n"
        "child = subprocess.Popen(['sleep', '60'])\n"
        "print(child.pid, flush=True)\n"
        "print(child.wait(), flush=True)\n"
    )
    process = subprocess.Popen([sys.executable, "-c", wrapper], start_new_session=True,
                               stdout=subprocess.PIPE, text=True)
    try:
        assert int(process.stdout.readline()) > 0
        table = walk_stop.ProcessTable()
        files = FakeFiles({IDENTITY_FILE: walk_stop.identity_text(table, process.pid, None)})

        stop = walk_stop.stop_launch(files, table, IDENTITY_FILE, "wrapped run")

        assert stop.run == walk_stop.Outcome.STOPPED
        assert process.wait(timeout=10) == 0
        assert int(process.stdout.readline()) == -signal.SIGINT
    finally:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
        process.wait()
        process.stdout.close()


def test_a_pid_whose_start_time_differs_is_never_signalled():
    table = walk_stop.ProcessTable()
    with sleeping_process() as process:
        files = files_holding(run=(process.pid, "Mon Jan  1 00:00:00 1990"))

        stop = walk_stop.stop_launch(files, table, IDENTITY_FILE, "audit 1")

        assert stop.run == walk_stop.Outcome.GONE
        assert stop.run.value == "already gone"
        assert process.poll() is None


def test_the_record_cli_round_trips_through_read_identity(tmp_path):
    table = walk_stop.ProcessTable()
    target = tmp_path / "launch.identity.json"
    with sleeping_process() as run, sleeping_process() as watcher:
        result = subprocess.run(
            [sys.executable, str(TOOLS / "walk_stop.py"), "record", str(target),
             "--run-pid", str(run.pid), "--watcher-pid", str(watcher.pid)],
            capture_output=True, text=True)

        identity = walk_stop.read_identity(walk_stop.DiskFiles(), str(target))

        assert result.returncode == 0, result.stderr
        assert identity == walk_stop.LaunchIdentity(
            run=walk_stop.ProcessIdentity(run.pid, table.start_time(run.pid), table.started_at(run.pid)),
            watcher=walk_stop.ProcessIdentity(watcher.pid, table.start_time(watcher.pid),
                                              table.started_at(watcher.pid)))
        assert identity.run.start is not None
        assert identity.watcher.start is not None
        assert identity.run.started_at is not None and identity.watcher.started_at is not None


def test_record_names_a_pid_with_no_process_with_a_null_start(tmp_path):
    process = subprocess.Popen(["true"])
    process.wait()
    target = tmp_path / "launch.identity.json"
    bare = tmp_path / "bare.identity.json"

    first = subprocess.run(
        [sys.executable, str(TOOLS / "walk_stop.py"), "record", str(target),
         "--run-pid", str(process.pid)], capture_output=True, text=True)
    second = subprocess.run(
        [sys.executable, str(TOOLS / "walk_stop.py"), "record", str(bare)],
        capture_output=True, text=True)

    assert first.returncode == 0 and second.returncode == 0
    assert json.loads(target.read_text()) == {
        "run": {"pid": process.pid, "start": None, "started_at": None}, "watcher": None}
    assert json.loads(bare.read_text()) == {"run": None, "watcher": None}


def test_started_at_names_the_moment_in_utc_whatever_the_callers_zone_and_language(monkeypatch):
    with sleeping_process() as process:
        monkeypatch.setenv("TZ", "America/New_York")
        monkeypatch.setenv("LC_ALL", "de_DE.UTF-8")
        started = walk_stop.ProcessTable().started_at(process.pid)
        tokyo = subprocess.run(["ps", "-o", "lstart=", "-p", str(process.pid)], capture_output=True,
                               text=True, env={**os.environ, "LC_ALL": "C", "TZ": "Asia/Tokyo"})

    expected = datetime.strptime(" ".join(tokyo.stdout.split()), walk_stop.LSTART_FORMAT) \
        .replace(tzinfo=ZoneInfo("Asia/Tokyo"))
    assert started is not None
    assert datetime.fromisoformat(started) == expected
    assert datetime.fromisoformat(started).utcoffset() == timedelta(0)


def test_started_at_of_no_process_is_none():
    process = subprocess.Popen(["true"])
    process.wait()

    assert walk_stop.ProcessTable().started_at(process.pid) is None


def test_identity_text_records_each_processs_started_at():
    table = FakeTable({11: "Fri Oct 23 09:19:05 2026"}, {11: "2026-10-23T07:19:05+00:00"})

    assert json.loads(walk_stop.identity_text(table, 11, 12)) == {
        "run": {"pid": 11, "start": "Fri Oct 23 09:19:05 2026", "started_at": "2026-10-23T07:19:05+00:00"},
        "watcher": {"pid": 12, "start": None, "started_at": None}}


def test_a_file_written_before_started_at_reads_with_it_none():
    identity = walk_stop.read_identity(files_holding(run=(11, "Fri Oct 23 09:19:05 2026")), IDENTITY_FILE)

    assert identity == walk_stop.LaunchIdentity(
        run=walk_stop.ProcessIdentity(11, "Fri Oct 23 09:19:05 2026", None), watcher=None)


def test_a_started_at_that_is_not_text_is_malformed():
    files = FakeFiles({IDENTITY_FILE: json.dumps(
        {"run": {"pid": 11, "start": "Fri Oct 23 09:19:05 2026", "started_at": 5}, "watcher": None})})

    assert walk_stop.read_identity(files, IDENTITY_FILE) is None


# --- fakes -------------------------------------------------------------------


@pytest.mark.parametrize("files", [
    pytest.param(FakeFiles(), id="missing file"),
    pytest.param(FakeFiles({IDENTITY_FILE: ""}), id="empty file"),
    pytest.param(FakeFiles({IDENTITY_FILE: "{not json"}), id="malformed json"),
])
def test_launch_state_is_unrecorded_without_an_identity(files):
    state = walk_stop.launch_state(files, FakeTable(), IDENTITY_FILE)

    assert state == walk_stop.LaunchState.UNRECORDED


def test_launch_state_is_unrecorded_for_an_empty_path():
    assert walk_stop.launch_state(FakeFiles(), FakeTable(), "") == walk_stop.LaunchState.UNRECORDED


@pytest.mark.parametrize("run,watcher", [
    pytest.param((10, SOME_START), (11, "gone"), id="the run matches"),
    pytest.param((10, "gone"), (11, SOME_START), id="the watcher matches"),
    pytest.param((10, SOME_START), (11, SOME_START), id="both match"),
])
def test_launch_state_is_live_when_the_run_or_the_watcher_still_matches(run, watcher):
    table = FakeTable({10: SOME_START, 11: SOME_START})

    state = walk_stop.launch_state(files_holding(run=run, watcher=watcher), table, IDENTITY_FILE)

    assert state == walk_stop.LaunchState.LIVE


@pytest.mark.parametrize("run,watcher,starts", [
    pytest.param((10, SOME_START), (11, SOME_START), {}, id="dead pids"),
    pytest.param((10, SOME_START), (11, SOME_START), {10: "Sat Oct  3 01:00:00 2026",
                                                      11: "Sat Oct  3 01:00:01 2026"},
                 id="recycled pids"),
    pytest.param((10, None), (11, None), {10: SOME_START, 11: SOME_START}, id="null starts"),
    pytest.param(None, None, {}, id="neither recorded"),
])
def test_launch_state_is_gone_when_neither_matches(run, watcher, starts):
    state = walk_stop.launch_state(
        files_holding(run=run, watcher=watcher), FakeTable(starts), IDENTITY_FILE)

    assert state == walk_stop.LaunchState.GONE


def test_start_times_compare_after_collapsing_whitespace():
    table = FakeTable({10: "Fri Oct 2 15:24:58 2026"})

    state = walk_stop.launch_state(
        files_holding(run=(10, "Fri Oct  2 15:24:58 2026")), table, IDENTITY_FILE)

    assert state == walk_stop.LaunchState.LIVE


def test_stop_launch_stops_the_watcher_before_the_run():
    table = FakeTable({10: SOME_START, 11: SOME_START})
    files = files_holding(run=(10, SOME_START), watcher=(11, SOME_START))

    stop = walk_stop.stop_launch(files, table, IDENTITY_FILE, "audit 1")

    assert table.stopped == [11, 10]
    assert (stop.watcher, stop.run) == (walk_stop.Outcome.STOPPED, walk_stop.Outcome.STOPPED)


def test_stop_launch_signals_nothing_for_an_unrecorded_launch():
    table = FakeTable({10: SOME_START})

    stop = walk_stop.stop_launch(FakeFiles(), table, IDENTITY_FILE, "audit 1")

    assert stop.run == walk_stop.Outcome.UNRECORDED
    assert stop.watcher == walk_stop.Outcome.UNRECORDED
    assert stop.run.value == "no recorded identity"
    assert table.stopped == []


def test_launch_stop_describes_each_process_by_pid_and_outcome():
    stop = walk_stop.LaunchStop(
        "the audit", walk_stop.Outcome.STOPPED, walk_stop.Outcome.GONE,
        run_pid=4242, watcher_pid=4243)

    text = stop.describe()

    assert "the audit" in text
    assert "run 4242 stopped" in text
    assert "watcher 4243 already gone" in text


def test_stop_launch_reports_the_pids_it_read():
    table = FakeTable({10: SOME_START})

    stop = walk_stop.stop_launch(
        files_holding(run=(10, SOME_START), watcher=(11, SOME_START)), table,
        IDENTITY_FILE, "audit 1")

    assert (stop.run_pid, stop.watcher_pid) == (10, 11)
    assert (stop.run, stop.watcher) == (walk_stop.Outcome.STOPPED, walk_stop.Outcome.GONE)


def test_identity_path_sits_beside_the_shim():
    assert (walk_stop.identity_path("/logs/chain-x-walk-1.sh")
            == "/logs/chain-x-walk-1.identity.json")


INHERITED = {
    "DETACHED_RUN_PID": "1", "DETACHED_RUN_SESSION_ID": "s", "DETACH_PROCESS_WATCHER_PID": "2",
    "DETACH_PROCESS_WATCHER_START": "t",
}


def test_prepare_launch_empties_the_file_and_carries_its_path():
    files = FakeFiles({"/logs/chain-x-walk-1.identity.json": "old"})
    env = {"HOME": "/h", walk_stop.IDENTITY_VARIABLE: "/stale", **INHERITED}

    prepared, path = walk_stop.prepare_launch(files, "/logs/chain-x-walk-1.sh", env)

    assert path == "/logs/chain-x-walk-1.identity.json"
    assert files.contents[path] == ""
    assert prepared == {"HOME": "/h", walk_stop.IDENTITY_VARIABLE: path}
    assert env == {"HOME": "/h", walk_stop.IDENTITY_VARIABLE: "/stale", **INHERITED}


def test_without_launch_identity_carries_no_identity_variable():
    env = {"HOME": "/h", walk_stop.IDENTITY_VARIABLE: "/stale", **INHERITED}

    stripped = walk_stop.without_launch_identity(env)

    assert stripped == {"HOME": "/h"}
    assert walk_stop.IDENTITY_VARIABLE in env


def test_stop_reason_names_when_and_each_launch():
    stops = [
        walk_stop.LaunchStop("audit 1", walk_stop.Outcome.STOPPED, walk_stop.Outcome.STOPPED,
                             run_pid=10, watcher_pid=11),
        walk_stop.LaunchStop("audit 2", walk_stop.Outcome.GONE, walk_stop.Outcome.GONE,
                             run_pid=12, watcher_pid=13),
    ]

    reason = walk_stop.stop_reason("2026-10-02T15:30:00", stops)

    assert "2026-10-02T15:30:00" in reason
    assert "stopped" in reason
    assert all(stop.describe() in reason for stop in stops)


def test_stop_command_names_the_launcher_the_project_and_stop():
    assert (walk_stop.stop_command("/x/core", "chain-product", "tools")
            == "/x/core/launchers/chain-product/launcher.sh tools --stop")
    quoted = walk_stop.stop_command("/x/my core", "chain-product", "my project")
    assert quoted == "'/x/my core/launchers/chain-product/launcher.sh' 'my project' --stop"


COMMAND = "/x/core/launchers/chain-product/launcher.sh tools --stop"


def test_refusal_remedy_says_nothing_will_finish_only_when_every_launch_is_gone():
    gone = walk_stop.refusal_remedy(
        [walk_stop.LaunchState.GONE, walk_stop.LaunchState.GONE], COMMAND)
    assert "nothing will finish" in gone.lower()
    assert COMMAND in gone
    assert "delete" not in gone.lower()
    for states in ([walk_stop.LaunchState.GONE, walk_stop.LaunchState.LIVE],
                   [walk_stop.LaunchState.UNRECORDED], []):
        remedy = walk_stop.refusal_remedy(states, COMMAND)
        assert "nothing will finish" not in remedy.lower()
        assert "let it finish" in remedy.lower()
        assert COMMAND in remedy
        assert "delete" not in remedy.lower()


def test_watch_process_uses_the_owners_process_helpers():
    assert watch_process.stop_lingering is walk_stop.stop_lingering
    assert watch_process.process_alive is walk_stop.process_alive


def test_the_record_cli_reports_an_unwritable_target_on_stderr(tmp_path):
    missing_directory = tmp_path / "absent" / "launch.identity.json"

    result = subprocess.run(
        [sys.executable, str(TOOLS / "walk_stop.py"), "record", str(missing_directory)],
        capture_output=True, text=True)

    assert result.returncode != 0
    assert result.stderr.startswith("walk_stop: ")
    assert "Traceback" not in result.stderr


def test_read_identity_treats_a_files_port_that_answers_none_as_a_missing_file():
    """The engines' own `Files` answers `None` for a file it cannot read, rather than raising."""

    class AnswersNone:
        def read_text(self, path: str) -> None:
            return None

    assert walk_stop.read_identity(AnswersNone(), IDENTITY_FILE) is None
    assert walk_stop.launch_state(
        AnswersNone(), FakeTable(), IDENTITY_FILE) == walk_stop.LaunchState.UNRECORDED


@pytest.mark.parametrize("record", [
    {},
    {"run": None},
    {"run": [], "watcher": None},
    {"run": {"pid": 10}, "watcher": None},
    {"run": {"pid": True, "start": SOME_START}, "watcher": None},
    {"run": {"pid": 10, "start": 123}, "watcher": None},
    {"run": {"pid": 10, "start": SOME_START}, "watcher": "broken"},
])
def test_a_malformed_identity_object_is_unrecorded_and_signals_nothing(record):
    """Task 1's malformed-file contract also covers broken identity fields, not just JSON text.
    CP-383 requires recorded identities before claiming that nothing can finish a walk."""
    files = FakeFiles({IDENTITY_FILE: json.dumps(record)})
    table = FakeTable({10: SOME_START, 1: SOME_START})

    assert walk_stop.read_identity(files, IDENTITY_FILE) is None
    state = walk_stop.launch_state(files, table, IDENTITY_FILE)
    stop = walk_stop.stop_launch(files, table, IDENTITY_FILE, "launch")

    assert state == walk_stop.LaunchState.UNRECORDED
    assert stop.run == stop.watcher == walk_stop.Outcome.UNRECORDED
    assert table.stopped == []
    assert "nothing will finish" not in walk_stop.refusal_remedy([state], COMMAND).lower()


@pytest.mark.parametrize("live_pid", [10, 11])
def test_a_stop_checks_each_process_identity_independently(live_pid):
    """CP-374: a recycled run does not prevent stopping its live watcher, or the reverse."""
    table = FakeTable({10: "recycled", 11: "recycled", live_pid: SOME_START})
    files = files_holding(run=(10, SOME_START), watcher=(11, SOME_START))

    stop = walk_stop.stop_launch(files, table, IDENTITY_FILE, "launch")

    assert table.stopped == [live_pid]
    assert stop.run == (walk_stop.Outcome.STOPPED if live_pid == 10 else walk_stop.Outcome.GONE)
    assert stop.watcher == (walk_stop.Outcome.STOPPED if live_pid == 11 else walk_stop.Outcome.GONE)


def test_the_run_identity_is_checked_after_the_watcher_has_stopped():
    """CP-374 still applies if the run exits and its pid is recycled while the watcher stops."""
    class RecyclingTable(FakeTable):
        def stop_group(self, pid):
            super().stop_group(pid)
            self.starts[10] = "a new process"

    table = RecyclingTable({10: SOME_START, 11: SOME_START})
    files = files_holding(run=(10, SOME_START), watcher=(11, SOME_START))

    stop = walk_stop.stop_launch(files, table, IDENTITY_FILE, "launch")

    assert table.stopped == [11]
    assert stop.run == walk_stop.Outcome.GONE
    assert stop.watcher == walk_stop.Outcome.STOPPED
