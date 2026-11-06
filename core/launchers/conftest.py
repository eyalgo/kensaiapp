"""Pytest bootstrap for `core/launchers` — loads the net `core/tools/pytest_guardrails.py` holds, so
a launcher suite runs inside the same guards as `core/tools`: no inherited telemetry variable, no
inherited `GIT_CONFIG_*` override, no secret value in a failure report, and no real network
connection. The git-config one earns its place here — under a pin the injected `core.hooksPath`
reaches every `git` a fixture spawns, and a throwaway repo's own seed commit is then refused by the
pin's `commit-msg` hook (measured inside a pinned chain run, 2026-09-23: 18 failures across 17
launcher files, 16 of them that refusal).

`core/tools` is appended to `sys.path`, not inserted, so no module a launcher suite imports is
shadowed by one there.

WHY THE `warm_executables` FIXTURE EXISTS. Every launcher suite writes its stubs (`caffeinate`,
`claude`, the notifier, a synthetic launcher) as a new executable file for each case and then runs
them inside a timing window. On this machine the FIRST exec of a newly written file is slow, and
under a full `-n 32` run those first execs queue behind each other: an idle machine measured a
freshly written file at a median 238 ms against 4.6 ms for one exec'd before, and 64 fresh files
exec'd at once at a median 8.5 s, while an already-exec'd file stayed at 5.5 ms through the same
burst. A case's stub start latency was therefore decided by the rest of the machine, and the cases
that bound it (a keep-awake presence check, `elapsed < 4.0`) failed only when the suite ran loaded.
The cost belongs to the file, not to its path or its text — a fresh file with an identical body
still measured 110 ms, and a symlink to a warm file 4.8 ms — so the fix reuses the same FILE: one
per distinct body, per worker, exec'd once during fixture setup, reached from each case through a
symlink in its own `bin/`. A longer wait was rejected because it leaves the dependence in place.
"""

from __future__ import annotations

import errno
import hashlib
import http.server
import json
import os
import re
import signal
import subprocess
import sys
import threading
import time
from collections.abc import Mapping
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parent.parent / "tools"))

from pytest_guardrails import (  # noqa: E402,F401
    _no_ambient_colour,
    _no_ambient_git_config,
    _no_ambient_ollama,
    _no_ambient_provider_force,
    _no_ambient_telemetry,
    _no_real_home,
    _no_real_network,
    pytest_configure,
    pytest_runtest_makereport,
    pytest_sessionfinish,
    pytest_testnodedown,
)

import pin  # noqa: E402
import walk_stop  # noqa: E402
from codex_test_support import CODEX_STUB


def _granted_dirs(argv):
    """Every directory `--add-dir` grants, in order, whichever spelling the caller used.

    The pin's own grant is written as ONE token (`--add-dir=<pin root>`, `agent_run.py`'s Claude
    delivery, `b7fe07e8d`) so that a prompt sitting after it is not read as its value; a group or
    product grant the launcher appends itself is still two. A test asserting on what was granted
    is asking which directories, never which spelling.
    """
    dirs = []
    skip = False
    for index, token in enumerate(argv):
        if skip:
            skip = False
            continue
        if token == "--add-dir":
            dirs.append(argv[index + 1])
            skip = True
        elif token.startswith("--add-dir="):
            dirs.append(token[len("--add-dir="):])
    return dirs


def _plugin_skills(argv):
    """What the launched command's plugin offers under `skills/`: every name it lists, and the
    set of groups the listed grouped skills belong to. The pin is read off the plugin's own path
    (`<pin>/instances/<instance key>/plugins/<grant key>`), so a case needs no pin handle."""
    plugin = Path(argv[argv.index("--plugin-dir") + 1])
    listed = {entry.name for entry in (plugin / "skills").iterdir()}
    pin_root = plugin.parents[3]
    group_of = {
        entry.name: group.name
        for group in (pin_root / "skills").iterdir()
        for entry in (group / ".claude" / "skills").glob("*")
    }
    return listed, {group_of[name] for name in listed if name in group_of}


# The `claude` flags `agent_run.ClaudeAdapter` writes with a separate value — `Shape.TURN`'s and the
# pin delivery's. Every other token is a bare flag (`--print`, `--verbose`), a one-token
# `--add-dir=<dir>`, or the run's one positional argument, its prompt.
_CLAUDE_VALUE_FLAGS = frozenset({
    "--output-format", "--session-id", "--resume", "--name", "--agent", "--model", "--effort",
    "--permission-mode", "--permission-prompts", "--settings", "--setting-sources",
    "--plugin-dir", "--agents", "--append-system-prompt-file",
})

# How every detached `claude` run a launcher starts opens (`agent_run.py`, `Shape.TURN`).
_PRINT_RUN_HEAD = ["--print", "--output-format", "stream-json", "--verbose"]


def _prompt_of(argv):
    """The one positional token of a `claude` argv, wherever the shape puts it — the run's prompt."""
    positional, skip = [], False
    for token in argv:
        if skip:
            skip = False
        elif token in _CLAUDE_VALUE_FLAGS:
            skip = True
        elif not token.startswith("--"):
            positional.append(token)
    assert len(positional) == 1, argv
    return positional[0]


def _provider_argv(tokens):
    """`tokens` from the provider's own name on: the leading `env KEY=value …` that hands a detached
    run its variables (`agent_run._env_prefix`) belongs to the launch, not to the provider."""
    tokens = list(tokens)
    if tokens[:1] == ["env"]:
        tokens = tokens[1:]
        while tokens and "=" in tokens[0] and not tokens[0].startswith("-"):
            tokens = tokens[1:]
    if len(tokens) > 1 and Path(tokens[1]).name == "codex_skill_run.py":
        return ["codex-skill", *tokens[2:]]
    return tokens


def _without_session_id(argv):
    """`argv` with its `--session-id` value masked: every launch names a fresh conversation."""
    argv = list(argv)
    if "--session-id" in argv:
        argv[argv.index("--session-id") + 1] = "<session>"
    return argv


def assert_launch_recorded_its_identity(stdout, identity_file):
    """What a launch leaves for the engine that named `identity_file` (CP-370): the run pid the
    runner's JSON record printed, and a watcher pid. Every run launcher records it through the one
    shared function, so the three suites ask the one question."""
    record = next(json.loads(line) for line in stdout.splitlines() if line.startswith("{"))
    identity = walk_stop.read_identity(walk_stop.DiskFiles(), str(identity_file))
    assert identity is not None, f"no identity recorded at {identity_file}"
    assert identity.run.pid == record["pid"]
    assert isinstance(identity.watcher.pid, int)


# Every suite under `core/launchers/` reaches `_granted_dirs` above through this key, never
# through `import conftest`. Pytest's default "prepend" import mode names an unpackaged
# conftest.py by its bare basename, and `.claude/conftest.py` — an ancestor of `.claude/hooks/`,
# collected in the same run by this repo's own verify command — answers to that same bare name.
# Whichever of the two conftest.py files a worker happens to import last wins the shared
# `sys.modules["conftest"]` slot, so a bare `from conftest import _granted_dirs` in a launcher
# suite can silently resolve to `.claude/conftest.py` and raise ImportError. Pytest itself never
# hits this: it tracks every conftest.py it loads by absolute path, not by this name, and always
# loads this file before collecting anything under `core/launchers/`. A private, never-reused key
# gives every suite that same guarantee.
sys.modules["kensaiapp_launchers_conftest"] = sys.modules[__name__]


@pytest.fixture(scope="session", autouse=True)
def _session_pin(tmp_path_factory: pytest.TempPathFactory) -> pin.Pin:
    """One pin of this worktree's host, made once for the whole test session (once per xdist
    worker) and inherited by every launcher a test starts, in place of a fresh copy on every
    launch — the same inheritance `pin_run.sh`'s own rule 2 gives a real nested launch.

    `KENSAIAPP_PINS_HOME` is pointed at a session-scoped temporary directory, never the real
    `~/.kensaiapp/pins/`, so nothing this suite runs writes there. A test that exercises the pin
    mechanism itself overrides both `KENSAIAPP_PINS_HOME` and `KENSAIAPP_PIN` (`monkeypatch`,
    function-scoped, restored to this session's values once that test ends).
    """
    host_root = Path(__file__).resolve().parents[2]
    pins_home_dir = tmp_path_factory.mktemp("session_pin_home")
    previous_pins_home = os.environ.get("KENSAIAPP_PINS_HOME")
    previous_pin = os.environ.get("KENSAIAPP_PIN")
    os.environ["KENSAIAPP_PINS_HOME"] = str(pins_home_dir)
    made = pin.make(host_root, pins_home_dir)
    os.environ["KENSAIAPP_PIN"] = str(made.root)
    yield made
    if previous_pins_home is None:
        os.environ.pop("KENSAIAPP_PINS_HOME", None)
    else:
        os.environ["KENSAIAPP_PINS_HOME"] = previous_pins_home
    if previous_pin is None:
        os.environ.pop("KENSAIAPP_PIN", None)
    else:
        os.environ["KENSAIAPP_PIN"] = previous_pin

# Variables a warm-up leaves alone: pointing `PATH` at a scratch file would stop the stub finding
# any command, and `HOME` is not a log a stub writes.
_KEPT_VARIABLES = frozenset({"PATH", "HOME"})
_VARIABLE_REFERENCE = re.compile(r"\$\{?([A-Z_][A-Z0-9_]*)")
_WARM_FILE_MODE = 0o555
_ENV_LAUNCHER = "/usr/bin/env"
_HANDOVER_POLL_SECONDS = 0.01
# A stub that holds (`exec sleep …`) never exits on its own; its first exec is long finished by
# the time the handover is over, so this is only how long it is given to exit before it is killed.
_HOLDING_STUB_GRACE_SECONDS = 0.5
# A stub with any other shebang (`#!/bin/sh`) has no `/usr/bin/env` phase to watch, so its first
# exec can only be seen finishing by the process exiting. The suites' such stubs all exit at once;
# this bound only stops a body that does not from holding fixture setup.
_DIRECT_INTERPRETER_EXIT_SECONDS = 30.0
# An `open` mode with any of these characters writes; every other mode only reads.
_WRITE_MODE_CHARACTERS = frozenset("wxa+")


class _ReadOnlyLink(Path):
    """The path `WarmExecutables.link` returns: a `Path` that refuses a write itself.

    The refusal is raised here, not left to the warm file's mode, because root writes through a
    mode of `0o555` and the guarantee must hold whoever runs the suite. Only this path refuses.
    A path derived from it (`resolve()`, `parent`, `/`) is a plain `Path`, so a case that
    resolves the link to read what it points at is not held to the refusal.
    """

    def with_segments(self, *path_segments: str | os.PathLike[str]) -> Path:
        return Path(*path_segments)

    def open(self, mode: str = "r", *arguments, **options):
        if _WRITE_MODE_CHARACTERS.intersection(mode):
            raise self._refusal()
        return super().open(mode, *arguments, **options)

    def write_text(self, *arguments, **options) -> int:
        raise self._refusal()

    def write_bytes(self, *arguments, **options) -> int:
        raise self._refusal()

    def _refusal(self) -> PermissionError:
        return PermissionError(errno.EACCES, os.strerror(errno.EACCES), str(self))


class WarmFiles:
    """The filesystem `WarmExecutables` writes each warm file and links each case through."""

    def write_executable(self, path: Path, body: str, mode: int) -> None:
        path.write_text(body)
        path.chmod(mode)

    def symlink(self, destination: Path, target: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.symlink_to(target)


class WarmProcesses:
    """The process `WarmExecutables` starts: a warm file's one exec, leaving nothing running."""

    def run_once(self, path: Path, *, cwd: Path, env: dict[str, str], waits_out_handover: bool,
                 exit_wait_seconds: float) -> None:
        """Exec `path` once, wait out its interpreter handover when asked, and kill what is left.

        The slow part of a first exec is not `Popen` returning: the process then sits as
        `/usr/bin/env bash <file>` until the interpreter takes the file over, and a warm-up that
        killed it there measured no faster than no warm-up at all (246 ms against 257 ms, where
        a file run to completion measured 7 ms). So a run that waits out the handover does that
        first, then lets a stub that exits do so within `exit_wait_seconds`, and kills one that
        holds.
        """
        process = subprocess.Popen(
            [str(path)],
            cwd=str(cwd),
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        if waits_out_handover:
            self._wait_out_interpreter_handover(process)
        try:
            process.wait(timeout=exit_wait_seconds)
        except subprocess.TimeoutExpired:
            pass
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass  # the group already exited; macOS reports a finished group as EPERM
        process.wait()

    @staticmethod
    def _wait_out_interpreter_handover(process: subprocess.Popen) -> None:
        while process.poll() is None:
            command = subprocess.run(
                ["ps", "-o", "command=", "-p", str(process.pid)],
                capture_output=True,
                text=True,
            ).stdout.strip()
            if not command.startswith(_ENV_LAUNCHER):
                return
            time.sleep(_HANDOVER_POLL_SECONDS)


class WarmExecutables:
    """Executable stubs that are written and exec'd once, then shared through symlinks.

    One warm file per distinct body, kept in this worker's own directory, so two xdist workers
    never write the same file. A case takes a stub with `link`; it never receives the warm file
    itself. The link it receives refuses a write itself, so that a write through it fails loudly
    instead of changing the stub every later case on the worker sees. The warm file's read-only
    mode is the second fence, for a write that does not go through the returned link.

    It reaches the filesystem, a process and the environment only through what it is handed;
    `build_warm_executables` is where the real ones are built.
    """

    def __init__(self, directory: Path, *, files: WarmFiles, processes: WarmProcesses,
                 environ: Mapping[str, str]) -> None:
        self._directory = directory
        self._scratch = directory / "warm-up.scratch"
        self._files = files
        self._processes = processes
        self._environ = environ
        self._warm: dict[str, Path] = {}

    def over(self, directory: Path) -> WarmExecutables:
        """A facility of its own over `directory`, handed the same collaborators as this one."""
        return WarmExecutables(directory, files=self._files, processes=self._processes,
                               environ=self._environ)

    def link(self, destination: Path, body: str) -> Path:
        """Make `destination` a symlink to the warm file for `body`, and return it as a link that
        refuses a write."""
        self._files.symlink(destination, self._warm_file(body))
        return _ReadOnlyLink(destination)

    def _warm_file(self, body: str) -> Path:
        digest = hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]
        if digest not in self._warm:
            path = self._directory / f"stub-{digest}"
            self._files.write_executable(path, body, _WARM_FILE_MODE)
            self._exec_once(path, body)
            self._warm[digest] = path
        return self._warm[digest]

    def _exec_once(self, path: Path, body: str) -> None:
        """Exec `path` so its first exec happens here, and leave no trace of it in any case.

        A body opening with `/usr/bin/env` has an interpreter handover to wait out before a stub
        that holds is killed (`WarmProcesses.run_once`). A body with another shebang shows no such
        phase, so it is simply run to its exit. Every variable the body references points at a
        scratch file of this worker's own, so anything the stub writes lands there and in no
        case's log.
        """
        env = {
            name: str(self._scratch)
            for name in _VARIABLE_REFERENCE.findall(body)
            if name not in _KEPT_VARIABLES
        }
        env["PATH"] = self._environ["PATH"]
        handover = body.startswith(f"#!{_ENV_LAUNCHER}")
        self._processes.run_once(
            path,
            cwd=self._directory,
            env=env,
            waits_out_handover=handover,
            exit_wait_seconds=(
                _HOLDING_STUB_GRACE_SECONDS if handover else _DIRECT_INTERPRETER_EXIT_SECONDS
            ),
        )


def build_warm_executables(directory: Path) -> WarmExecutables:
    """The composition root: the one place `WarmExecutables`' real collaborators are built."""
    return WarmExecutables(directory, files=WarmFiles(), processes=WarmProcesses(),
                           environ=os.environ)


@pytest.fixture(scope="session")
def warm_executables(tmp_path_factory: pytest.TempPathFactory) -> WarmExecutables:
    """The worker's warm stubs — `warm_executables.link(bin_dir / "claude", CLAUDE_STUB)`."""
    return build_warm_executables(tmp_path_factory.mktemp("warm_executables"))


class OllamaStub:
    """A stub Ollama server on `127.0.0.1` that answers `GET /api/version` with 200.

    A launcher case that needs an answering server sets `KENSAIAPP_OLLAMA_URL` in the run's
    environment to `address`; a case about an absent server leaves the suite guard's address,
    where nothing listens.
    """

    def __init__(self) -> None:
        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-Length", "0")
                self.end_headers()

            def log_message(self, *arguments):
                pass

        self._server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.address = f"http://127.0.0.1:{self._server.server_address[1]}"
        threading.Thread(target=self._server.serve_forever, daemon=True).start()

    def close(self) -> None:
        self._server.shutdown()
        self._server.server_close()


@pytest.fixture
def ollama_server():
    """An answering stub Ollama server, closed when the case ends."""
    stub = OllamaStub()
    yield stub
    stub.close()
