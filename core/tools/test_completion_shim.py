"""The completion-hook shim's contract, run as real processes.

WHY THIS FILE LOOKS LIKE THIS
    The contract is about processes — a hook that returns while its engine is still working, an
    engine that outlives the hook and writes after the watcher is gone — so each test here writes a
    real shim and runs it. The engine is a stand-in script that records what it was given, waits on
    a release file the test writes, and then writes to both of its output streams. Only the disk
    port is a fake, and only where the test is about what `write_shim` asks of it.
"""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

import pytest

import chain
import completion_shim

# How long the stand-in engine holds on its release file, at most. The same cap
# `test_chain_development.py` holds its stub launcher for.
HOLD_CAP = 30
# The bound the hook is run under here, standing in for the watcher's own, which is a literal
# inside `watch_agent.py`. It is under the hold cap, so a hook that waited on its engine times out.
HOOK_BOUND = 15

_ENGINE = """\
import json, os, sys, time
here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(here, "argv.json"), "w") as handle:
    json.dump(sys.argv[1:], handle)
with open(os.path.join(here, "stdin.txt"), "w") as handle:
    handle.write(sys.stdin.read())
release = os.path.join(here, "release")
for _ in range(HOLD_CAP * 20):
    if os.path.exists(release):
        break
    time.sleep(0.05)
print("engine out line")
print("engine err line", file=sys.stderr)
with open(os.path.join(here, "marker"), "a") as handle:
    handle.write("done\\n")
""".replace("HOLD_CAP", str(HOLD_CAP))


def wait_for(predicate, seconds: float = 20.0) -> bool:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.1)
    return predicate()


class RecordingFiles(completion_shim.ShimFiles):
    """The port, recording each call in order."""

    def __init__(self):
        self.calls: list[tuple[str, ...]] = []

    def make_dirs(self, path: str) -> None:
        self.calls.append(("make_dirs", path))

    def write_text(self, path: str, text: str) -> None:
        self.calls.append(("write_text", path, text))

    def make_executable(self, path: str) -> None:
        self.calls.append(("make_executable", path))


class Engine:
    """A stand-in engine on disk, held until released, and the shim that starts it."""

    def __init__(self, root: Path, *, directory: str = "an engine dir",
                 log_name: str = "a log dir/engine.log",
                 advance_args=("--advance", "a state.json")):
        self.directory = root / directory
        self.directory.mkdir(parents=True)
        self.script = self.directory / "engine.py"
        self.script.write_text(_ENGINE)
        self.log = root / log_name
        # The shim appends to a log and never makes the log's directory; its caller does.
        self.log.parent.mkdir(parents=True)
        self.advance_args = tuple(advance_args)
        self.shim = root / "shims" / "hook.sh"
        completion_shim.write_shim(chain.Files(), str(self.shim), engine_path=str(self.script),
                                   advance_args=self.advance_args, log_path=str(self.log))

    @property
    def release(self) -> Path:
        return self.directory / "release"

    @property
    def marker(self) -> Path:
        return self.directory / "marker"

    def fire(self, outcome="completed", **kwargs) -> subprocess.CompletedProcess:
        """The hook, run the way the watcher runs it."""
        return subprocess.run([str(self.shim), outcome], capture_output=True, text=True,
                              timeout=HOOK_BOUND, **kwargs)

    def finished(self, runs: int = 1) -> bool:
        return self.marker.exists() and len(self.marker.read_text().splitlines()) >= runs


@pytest.fixture
def engine(tmp_path):
    held = Engine(tmp_path)
    yield held
    held.release.write_text("")  # never leave an engine holding past its test


def test_the_hook_returns_inside_the_watchers_bound_while_its_engine_is_held(engine):
    began = time.monotonic()

    result = engine.fire()

    assert result.returncode == 0
    assert time.monotonic() - began < HOLD_CAP - 10
    assert not engine.marker.exists()


def test_the_engine_outlives_the_hook_and_finishes_once_released(engine):
    engine.fire()

    engine.release.write_text("")

    assert wait_for(engine.finished)


def test_the_engines_output_goes_to_its_log_never_the_hooks_pipe(engine):
    result = engine.fire()
    engine.release.write_text("")
    assert wait_for(engine.finished)

    assert (result.stdout, result.stderr) == ("", "")
    assert wait_for(lambda: engine.log.exists()
                    and set(engine.log.read_text().splitlines())
                    == {"engine out line", "engine err line"})


def test_the_log_is_appended_never_truncated(engine):
    engine.log.write_text("an earlier line\n")
    engine.fire()
    engine.fire()

    engine.release.write_text("")

    assert wait_for(lambda: engine.finished(runs=2))
    # The marker `finished` waits for is written before the engine's buffered stdout is flushed
    # at exit, so the log is read until its whole content has arrived, under one deadline.
    complete = sorted(["engine out line", "engine err line"] * 2)
    deadline = time.monotonic() + 30.0
    while True:
        lines = engine.log.read_text().splitlines()
        if sorted(lines[1:]) == complete or time.monotonic() >= deadline:
            break
        time.sleep(0.05)
    assert lines[0] == "an earlier line"
    assert sorted(lines[1:]) == sorted(["engine out line", "engine err line"] * 2)


@pytest.mark.parametrize("outcome", [
    "completed", "produced_nothing", "timeout", "vanished", "appear_error", "stopped", "failed",
])
def test_the_outcome_reaches_the_engine_as_its_last_argument(engine, outcome):
    engine.release.write_text("")
    engine.fire(outcome)
    assert wait_for(engine.finished)

    argv = json.loads((engine.directory / "argv.json").read_text())

    assert argv == [*engine.advance_args, outcome]


def test_every_word_survives_spaces_and_shell_metacharacters(tmp_path):
    awkward = "a $HOME 'single' \"double\" word"
    held = Engine(tmp_path, directory=f"engine {awkward}", log_name=f"logs {awkward}/engine.log",
                  advance_args=("--advance", awkward, "--launch", "$(echo hi)"))
    held.release.write_text("")
    try:
        held.fire()

        assert wait_for(held.finished)
        assert json.loads((held.directory / "argv.json").read_text()) == [
            "--advance", awkward, "--launch", "$(echo hi)", "completed"]
        assert wait_for(lambda: held.log.exists() and "engine out line" in held.log.read_text())
    finally:
        held.release.write_text("")


def test_the_engine_reads_nothing_from_the_hooks_stdin(engine):
    engine.release.write_text("")

    engine.fire(input="leak")

    assert wait_for(engine.finished)
    assert (engine.directory / "stdin.txt").read_text() == ""


def test_write_shim_makes_the_directory_writes_the_text_and_marks_it_executable():
    files = RecordingFiles()
    arguments = dict(engine_path="/pinned/engine.py", advance_args=("--advance", "/state.json"),
                     log_path="/logs/engine.log")

    returned = completion_shim.write_shim(files, "/shims/hook.sh", **arguments)

    assert returned == "/shims/hook.sh"
    assert files.calls == [
        ("make_dirs", "/shims"),
        ("write_text", "/shims/hook.sh", completion_shim.shim_text(**arguments)),
        ("make_executable", "/shims/hook.sh"),
    ]


# ---- the final-message receipt -------------------------------------------------------------------


class ReceiptFiles:
    """The receipt's port, in memory: the writer's `write_text` / `replace_file`, the reader's
    `read_text`, each call recorded in order."""

    def __init__(self, contents: dict[str, str] | None = None, *, unreadable: bool = False):
        self.contents = dict(contents or {})
        self.unreadable = unreadable
        self.calls: list[tuple[str, ...]] = []

    def write_text(self, path: str, text: str) -> None:
        self.calls.append(("write_text", path))
        self.contents[path] = text

    def replace_file(self, source: str, destination: str) -> None:
        self.calls.append(("replace_file", source, destination))
        self.contents[destination] = self.contents.pop(source)

    def read_text(self, path: str) -> str:
        self.calls.append(("read_text", path))
        if self.unreadable:
            raise OSError("unreadable")
        if path not in self.contents:
            raise FileNotFoundError(path)
        return self.contents[path]


def test_the_result_key_is_detached_run_result_file():
    assert completion_shim.RESULT_FILE_VARIABLE == "DETACHED_RUN_RESULT_FILE"


@pytest.mark.parametrize("message", [None, "one line", "two\nlines\n", 'say "hi" \\ \'x\'',
                                     "ünïcode — ✓"])
def test_a_receipt_round_trips_null_multiline_quotes_and_unicode(message):
    files = ReceiptFiles()

    completion_shim.write_result(files, "/run/receipt.json", message)

    assert completion_shim.read_result(files, "/run/receipt.json") == message


def test_no_destination_means_no_io():
    files = ReceiptFiles()

    completion_shim.write_result(files, None, "a message")
    completion_shim.write_result(files, "", "a message")

    assert completion_shim.read_result(files, None) is None
    assert completion_shim.read_result(files, "") is None
    assert files.calls == []


def test_a_receipt_is_published_through_a_temporary_sibling_and_replaced():
    files = ReceiptFiles()

    completion_shim.write_result(files, "/run/receipt.json", "done")

    (written, source_path), (replaced, source, destination) = files.calls
    assert (written, replaced) == ("write_text", "replace_file")
    assert source_path == source != "/run/receipt.json"
    assert source.startswith("/run/")
    assert destination == "/run/receipt.json"
    assert json.loads(files.contents["/run/receipt.json"]) == {"last_message": "done"}


def test_a_missing_receipt_reads_as_no_message():
    assert completion_shim.read_result(ReceiptFiles(), "/run/receipt.json") is None


def test_an_unreadable_receipt_reads_as_no_message():
    files = ReceiptFiles({"/run/receipt.json": '{"last_message": "x"}'}, unreadable=True)

    assert completion_shim.read_result(files, "/run/receipt.json") is None


@pytest.mark.parametrize("text", ["", "not json {", '{"last_message": '])
def test_a_malformed_receipt_reads_as_no_message(text):
    files = ReceiptFiles({"/run/receipt.json": text})

    assert completion_shim.read_result(files, "/run/receipt.json") is None


@pytest.mark.parametrize("text", ['{"last_message": 5}', '{"last_message": ["a"]}', '["a"]',
                                  '"a string"', "{}"])
def test_a_wrong_typed_receipt_reads_as_no_message(text):
    files = ReceiptFiles({"/run/receipt.json": text})

    assert completion_shim.read_result(files, "/run/receipt.json") is None


def test_the_disk_receipt_files_publish_and_read_a_real_receipt(tmp_path):
    destination = str(tmp_path / "receipt.json")

    completion_shim.write_result(completion_shim.DiskReceiptFiles(), destination, "on disk")

    assert completion_shim.read_result(completion_shim.DiskReceiptFiles(), destination) == "on disk"
    assert sorted(path.name for path in tmp_path.iterdir()) == ["receipt.json"]


def test_a_receipt_with_unreadable_utf8_reads_as_no_message(tmp_path):
    destination = tmp_path / "receipt.json"
    destination.write_bytes(b'\xff{"last_message": "done"}')

    assert completion_shim.read_result(
        completion_shim.DiskReceiptFiles(), str(destination)) is None


def test_a_port_that_answers_none_for_an_unreadable_file_reads_as_no_message():
    """The queue's own disk port answers `None` for a file it cannot read, rather than raising."""

    class NoneForMissing(ReceiptFiles):
        def read_text(self, path):
            return self.contents.get(path)

    assert completion_shim.read_result(NoneForMissing(), "/run/receipt.json") is None
