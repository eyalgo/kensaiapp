"""Tests for telemetry_gateway.py — the one door to the optional telemetry package.

Nothing here monkeypatches the module under test. The gateway is handed a hand-written backend
through `build_telemetry`, and the backend records what it received. The package is made
unimportable (or recorded) with an import blocker, never by patching a gateway name.

The second half holds the completed-caller contracts: what each of the four readers does with the
package absent in a started interpreter, the tracked-tree boundary, and four live comparisons
against the readers' previous implementation. The comparisons run both sides on one snapshot of
the live inputs, taken once and shared by every worker; nothing here writes to, or appends to, an
original input. The previous implementation is read from Git at the base the change started from
and materialized in a temporary tree, never from the checkout.
"""

from __future__ import annotations

import ast
import fcntl
import hashlib
import importlib.abc
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace

import pytest

import telemetry_gateway as gateway

PACKAGE = "ka_telemetry"
TOOLS_DIR = Path(__file__).resolve().parent

CONTEXT_LINE = (
    "context cap: the cap needs the ka_telemetry package, which this Python cannot import; "
    "this run is not capped"
)


# ── the import blocker ──────────────────────────────────────────────────────


class PackageBlocker(importlib.abc.MetaPathFinder):
    """Records every attempt to import the package and raises `error` for it."""

    def __init__(self, error: BaseException):
        self.error = error
        self.attempts: list[str] = []

    def find_spec(self, name, path=None, target=None):
        if name == PACKAGE or name.startswith(PACKAGE + "."):
            self.attempts.append(name)
            raise self.error
        return None


def block_package(monkeypatch, error: BaseException) -> PackageBlocker:
    """Make every import of the package raise `error` for the rest of the test, whatever the
    interpreter has installed, and report the attempts."""
    for name in [loaded for loaded in sys.modules if loaded.split(".")[0] == PACKAGE]:
        monkeypatch.delitem(sys.modules, name)
    blocker = PackageBlocker(error)
    monkeypatch.setattr(sys, "meta_path", [blocker, *sys.meta_path])
    return blocker


SUBPROCESS_BLOCKER = f"""
import importlib.abc, json, sys
attempts = []
class Blocker(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path=None, target=None):
        if name == {PACKAGE!r} or name.startswith({PACKAGE!r} + "."):
            attempts.append(name)
            raise ModuleNotFoundError(name)
        return None
sys.meta_path.insert(0, Blocker())
sys.path.insert(0, {str(TOOLS_DIR)!r})
"""


# ── the hand-written backend ────────────────────────────────────────────────


def package_run(session_id, name=None, cwd=None, state=None, started_at=None):
    return SimpleNamespace(
        session_id=session_id, name=name, cwd=cwd, state=state, started_at=started_at
    )


def package_spend(input=0, output=0, cache_read=0, cache_write_1h=0, cache_write_5m=0,
                  thinking=None):
    return SimpleNamespace(
        input=input, output=output, cache_read=cache_read, cache_write_1h=cache_write_1h,
        cache_write_5m=cache_write_5m, thinking=thinking,
    )


class FakeBackend:
    """The bundle `build_telemetry` accepts: `runs`, `gauge` and `logs`, each recording what
    it received into `calls` and answering from the fields a test sets beforehand."""

    def __init__(self):
        self.calls: list[tuple] = []
        self.file_port = SimpleNamespace(
            find_transcripts=lambda session_id, projects_root: [],
            read_lines=lambda path: None,
        )
        self.process_port = SimpleNamespace(run=lambda argv: "")
        self.parsed_runs = SimpleNamespace(
            runs=(), interactive_excluded=0, dropped_no_session=0, total_seen=0, listed=0
        )
        self.transcript = None
        self.records = []
        self.spend = {}
        self.span = None
        self.context = None
        self.parsed_logs = SimpleNamespace(records=(), skipped=0)
        self.attribute = None
        self.runs = SimpleNamespace(
            Files=self._make_files,
            Processes=self._make_processes,
            runs_from=self._runs_from,
            transcript_for=self._transcript_for,
            usage_records=self._usage_records,
            spend_by_model=self._spend_by_model,
            span_seconds=self._span_seconds,
        )
        self.gauge = SimpleNamespace(current_context=self._current_context)
        self.logs = SimpleNamespace(read_log_lines=self._read_log_lines, _attr=self._attr)

    def _make_files(self):
        self.calls.append(("Files",))
        return self.file_port

    def _make_processes(self):
        self.calls.append(("Processes",))
        return self.process_port

    def _runs_from(self, text):
        self.calls.append(("runs_from", text))
        return self.parsed_runs

    def _transcript_for(self, session_id, projects_root, files):
        self.calls.append(("transcript_for", session_id, projects_root, files))
        return self.transcript

    def _usage_records(self, path, files):
        self.calls.append(("usage_records", path, files))
        return iter(self.records)

    def _spend_by_model(self, records):
        consumed = list(records)
        self.calls.append(("spend_by_model", consumed))
        return self.spend

    def _span_seconds(self, records):
        consumed = list(records)
        self.calls.append(("span_seconds", consumed))
        return self.span

    def _current_context(self, path, files):
        self.calls.append(("current_context", path, files))
        return self.context

    def _read_log_lines(self, lines):
        self.calls.append(("read_log_lines", lines))
        return self.parsed_logs

    def _attr(self, record, key):
        self.calls.append(("_attr", record, key))
        return self.attribute


@pytest.fixture
def backend():
    return FakeBackend()


@pytest.fixture
def telemetry(backend):
    return gateway.build_telemetry(backend)


# ── Task 1 — the optional adapter ───────────────────────────────────────────


def test_import_is_silent_and_does_not_attempt_package_loading():
    script = SUBPROCESS_BLOCKER + """
import telemetry_gateway
print(json.dumps(attempts))
"""
    done = subprocess.run(
        [sys.executable, "-I", "-c", script], capture_output=True, text=True, timeout=60
    )
    assert done.returncode == 0
    assert done.stderr == ""
    assert json.loads(done.stdout) == []


def test_wiring_reports_unavailable_only_when_package_import_fails(monkeypatch):
    blocker = block_package(monkeypatch, ModuleNotFoundError(PACKAGE))
    with pytest.raises(gateway.TelemetryUnavailable):
        gateway.build_telemetry()
    assert blocker.attempts, "wiring never tried the package"

    unrelated = RuntimeError("the package's own import blew up")
    block_package(monkeypatch, unrelated)
    with pytest.raises(RuntimeError) as raised:
        gateway.build_telemetry()
    assert raised.value is unrelated


def test_injected_backend_needs_no_installed_package(monkeypatch, backend):
    blocker = block_package(monkeypatch, ModuleNotFoundError(PACKAGE))
    built = gateway.build_telemetry(backend)
    assert built.files is backend.file_port
    assert built.processes is backend.process_port
    assert backend.calls == [("Files",), ("Processes",)]
    assert blocker.attempts == []


def test_gateway_preserves_listing_and_spend_values(backend, telemetry):
    backend.parsed_runs = SimpleNamespace(
        runs=(
            package_run("s-b", name="second", cwd="/w/b", state="done", started_at=20),
            package_run("s-a"),
        ),
        interactive_excluded=3,
        dropped_no_session=2,
        total_seen=7,
        listed=2,
    )
    listing = telemetry.parse_runs("[]")
    assert [run.session_id for run in listing.runs] == ["s-b", "s-a"]
    assert (listing.runs[0].name, listing.runs[0].cwd) == ("second", "/w/b")
    assert (listing.runs[0].state, listing.runs[0].started_at) == ("done", 20)
    assert (listing.runs[1].name, listing.runs[1].cwd) == (None, None)
    assert (listing.runs[1].state, listing.runs[1].started_at) == (None, None)
    assert (listing.interactive_excluded, listing.dropped_no_session) == (3, 2)
    assert listing.total_seen == 7

    backend.parsed_runs = SimpleNamespace(
        runs=(), interactive_excluded=0, dropped_no_session=0, total_seen=0, listed=0
    )
    assert telemetry.parse_runs("[]").runs == ()

    backend.spend = {
        "model-z": package_spend(1, 2, 3, 4, 5, thinking=6),
        "model-a": package_spend(thinking=None),
        "model-m": package_spend(thinking=0),
    }
    spent = telemetry.spend_by_model(iter([]))
    assert list(spent) == ["model-z", "model-a", "model-m"]
    assert (spent["model-z"].input, spent["model-z"].output) == (1, 2)
    assert (spent["model-z"].cache_read, spent["model-z"].cache_write_1h) == (3, 4)
    assert (spent["model-z"].cache_write_5m, spent["model-z"].thinking) == (5, 6)
    assert spent["model-a"].thinking is None
    assert spent["model-m"].thinking == 0


def test_gateway_delegates_each_operation_with_its_arguments(backend, telemetry):
    projects_root = Path("/projects")
    path = Path("/projects/p/s.jsonl")
    backend.parsed_runs = SimpleNamespace(
        runs=(), interactive_excluded=0, dropped_no_session=0, total_seen=0, listed=0
    )

    telemetry.parse_runs("[{}]")
    assert telemetry.find_transcript("s-1", projects_root, telemetry.files) is None
    backend.transcript = path
    assert telemetry.find_transcript("s-1", projects_root, telemetry.files) == path
    assert telemetry.files.read_lines(path) is None  # an absent file stays absent
    assert telemetry.current_context(path, telemetry.files) is None
    backend.context = 5000
    assert telemetry.current_context(path, telemetry.files) == 5000
    backend.span = 12.5
    assert telemetry.span_seconds(iter([("u", "m", "t")])) == 12.5
    backend.spend = {}
    telemetry.spend_by_model(iter([("u", "m", "t")]))
    list(telemetry.read_usage(path, telemetry.files))

    assert backend.calls == [
        ("Files",),
        ("Processes",),
        ("runs_from", "[{}]"),
        ("transcript_for", "s-1", projects_root, backend.file_port),
        ("transcript_for", "s-1", projects_root, backend.file_port),
        ("current_context", path, backend.file_port),
        ("current_context", path, backend.file_port),
        ("span_seconds", [("u", "m", "t")]),
        ("spend_by_model", [("u", "m", "t")]),
        ("usage_records", path, backend.file_port),
    ]

    empty = telemetry.parse_logs([])
    assert (empty.records, empty.skipped) == ((), 0)
    backend.parsed_logs = SimpleNamespace(records=("a", "b"), skipped=4)
    read = telemetry.parse_logs(["x", "y"])
    assert (read.records, read.skipped) == (("a", "b"), 4)
    assert ("read_log_lines", ["x", "y"]) in backend.calls


def test_usage_iteration_does_not_drop_or_replay_records(backend, telemetry):
    backend.records = [({"input_tokens": n}, "m", f"t{n}") for n in range(4)]
    path = Path("/projects/p/s.jsonl")
    stream = telemetry.read_usage(path, telemetry.files)
    first = next(stream)
    rest = list(stream)
    assert [first, *rest] == backend.records
    assert list(stream) == []  # exhausted: nothing replayed

    stream = telemetry.read_usage(path, telemetry.files)
    backend.spend = {"m": package_spend(input=4)}
    spent = telemetry.spend_by_model(stream)
    assert backend.calls[-1] == ("spend_by_model", backend.records)
    assert list(stream) == []  # the one pass was the gateway's hand-over
    assert type(spent["m"]).__module__ == gateway.__name__  # no package class leaks out


def test_attribute_lookup_prefers_record_then_resource(backend, telemetry):
    record = object()
    backend.attribute = "from-record"
    assert telemetry.attribute_value(record, "kensai.model") == "from-record"
    backend.attribute = "from-resource"
    assert telemetry.attribute_value(record, "kensai.model") == "from-resource"
    backend.attribute = None
    assert telemetry.attribute_value(record, "kensai.absent") is None
    lookups = [call for call in backend.calls if call[0] == "_attr"]
    assert lookups == [
        ("_attr", record, "kensai.model"),
        ("_attr", record, "kensai.model"),
        ("_attr", record, "kensai.absent"),
    ]
    assert all(call[1] is record for call in lookups)  # the record stays opaque


@pytest.mark.parametrize("reader", list(gateway.ReaderName))
def test_dependency_messages_are_exact_for_every_reader(reader):
    message = gateway.dependency_message(reader)
    assert message == (
        f"{reader.value}: needs the ka_telemetry package, which this Python cannot import"
    )
    assert not message.endswith("\n")
    assert gateway.CONTEXT_UNAVAILABLE == CONTEXT_LINE
    assert [member.value for member in gateway.ReaderName] == [
        "chain_usage", "run_provenance", "measure",
    ]


# ═══ Task 3 — the four callers, without the package and against their previous selves ═══════

REPO = TOOLS_DIR.parents[1]
BASE = "ff83151f9d9d5a97f815d1e1b79886cc1a08413a"
HOOK = REPO / ".claude" / "hooks" / "context_cap.py"
MEASURE = (
    REPO / "system" / "projects" / "product-definition" / "docs" / "sdd-runner-cache-read"
    / "measure.py"
)
LIVE_TELEMETRY = Path.home() / ".kensaiapp" / "telemetry"
LIVE_PROJECTS = Path.home() / ".claude" / "projects"
VENV = Path.home() / ".kensaiapp" / "venv"
GATEWAY_PATH = "core/tools/telemetry_gateway.py"
THE_TWO_PATHS = {GATEWAY_PATH, "core/tools/test_telemetry_gateway.py"}
SIX_OLD_MODULES = {
    "otel_receiver", "agent_usage", "run_usage", "flow_usage", "context_gauge",
    "apply_telemetry_env",
}
FOUR_CALLERS = (
    ".claude/hooks/context_cap.py",
    "core/tools/chain_usage.py",
    "core/tools/run_provenance.py",
    "system/projects/product-definition/docs/sdd-runner-cache-read/measure.py",
)


class MissingPrerequisite(Exception):
    """A live comparison cannot be made on this host: the reason names what is missing."""


class HarnessError(Exception):
    """The harness itself failed. Never a skip."""


def need(condition: object, reason: str) -> None:
    if not condition:
        raise MissingPrerequisite(reason)


def skipping_for_prerequisites(test: Callable) -> Callable:
    """A missing prerequisite is a named skip; every other exception stays what it is."""
    import functools

    @functools.wraps(test)
    def wrapper(*args, **kwargs):
        try:
            return test(*args, **kwargs)
        except MissingPrerequisite as exc:
            pytest.skip(f"missing prerequisite: {exc}")

    return wrapper


@dataclass(frozen=True)
class Outcome:
    """What one started command produced, byte for byte."""

    stdout: bytes
    stderr: bytes
    status: int


def start(argv: list[str], *, home: Path, env: dict | None = None, stdin: bytes | None = None,
          cwd: Path | None = None, path: str = "/usr/bin:/bin") -> Outcome:
    environment = {"PATH": path, "HOME": str(home), "PYTHONDONTWRITEBYTECODE": "1",
                   "LC_ALL": "C", **(env or {})}
    try:
        done = subprocess.run(argv, input=stdin, capture_output=True, env=environment,
                              cwd=cwd, timeout=600, check=False)
    except (OSError, subprocess.SubprocessError) as exc:
        raise HarnessError(f"could not start {argv[0]}: {exc}") from exc
    return Outcome(done.stdout, done.stderr, done.returncode)


# ── the comparator: byte equality unless the package's PRD makes a difference on purpose ───


@dataclass(frozen=True)
class PrdDifference:
    """One difference the telemetry package's PRD makes on purpose (CP-672): the importer it
    affects, the stream or status it changes, the PRD clause that states it, and the narrow
    transformation of the previous output it produces on those same inputs."""

    importer: str
    changed: str
    clause: str
    transform: Callable[[object], object]


# Every difference observed on this host is recorded here with its clause. None was observed.
PRD_DIFFERENCES: tuple[PrdDifference, ...] = ()


def differences(importer: str, old: Outcome, new: Outcome,
                allowed: tuple[PrdDifference, ...] = PRD_DIFFERENCES) -> list[str]:
    found = []
    for changed in ("stdout", "stderr", "status"):
        before, after = getattr(old, changed), getattr(new, changed)
        if before == after:
            continue
        rules = [a for a in allowed if a.importer == importer and a.changed == changed]
        if any(a.clause and a.transform(before) == after for a in rules):
            continue
        found.append(f"{importer}: {changed} differs")
    return found


def test_comparator_rejects_every_unapproved_difference():
    old = Outcome(b"run 1\nrun 2\n", b"", 0)
    authorized = PrdDifference(
        "chain_usage", "stdout", "PRD section 'Core Features'",
        lambda out: out.replace(b"1", b"one"),
    )
    renamed = Outcome(b"run one\nrun 2\n", b"", 0)
    assert differences("chain_usage", old, renamed, (authorized,)) == []
    # the same delta for another importer, another stream, another value: all fail
    assert differences("measure", old, renamed, (authorized,))
    assert differences("chain_usage", old, Outcome(b"run 1\nrun 3\n", b"", 0), (authorized,))
    assert differences("chain_usage", old, Outcome(b"run 1\nrun 2\n", b"extra\n", 0), (authorized,))
    assert differences("chain_usage", old, Outcome(b"run 1\nrun 2\n", b"", 1), (authorized,))
    assert differences("chain_usage", old, Outcome(b"run 1\n", b"", 0), (authorized,))
    # a rule that names no clause authorizes nothing
    unnamed = PrdDifference("chain_usage", "stdout", "", lambda out: out + b"x")
    assert differences("chain_usage", old, Outcome(old.stdout + b"x", b"", 0), (unnamed,))
    assert differences("chain_usage", old, old, ()) == []


def test_a_missing_prerequisite_is_a_named_skip_and_a_harness_error_is_not():
    @skipping_for_prerequisites
    def absent():
        need(False, "the venv interpreter is absent")

    with pytest.raises(pytest.skip.Exception) as skipped:
        absent()
    assert "the venv interpreter is absent" in str(skipped.value)

    @skipping_for_prerequisites
    def broken():
        start(["/nonexistent/interpreter"], home=Path("/tmp"))

    with pytest.raises(HarnessError):
        broken()


# ── forced absence: the package unimportable in every interpreter a command starts ─────────

SITECUSTOMIZE = '''
import importlib.abc, os, sys

class _Block(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path=None, target=None):
        if name == "ka_telemetry" or name.startswith("ka_telemetry."):
            with open(os.environ["TELEMETRY_BLOCK_LOG"], "a") as log:
                log.write(os.path.realpath(sys.prefix) + "\\n")
            raise ModuleNotFoundError(name)
        return None

sys.meta_path.insert(0, _Block())
'''


@dataclass(frozen=True)
class Blocked:
    outcome: Outcome
    attempted_by: list[str]


def run_blocked(argv: list[str], tmp_path: Path, *, home: Path, stdin: bytes | None = None,
                env: dict | None = None) -> Blocked:
    """Run `argv` with the package refused by a `sitecustomize` every started interpreter reads,
    the hook's venv child included, and report which interpreters tried to import it."""
    block_dir = tmp_path / "block"
    block_dir.mkdir(exist_ok=True)
    (block_dir / "sitecustomize.py").write_text(SITECUSTOMIZE)
    log = tmp_path / f"attempts-{uuid.uuid4().hex}.log"
    outcome = start(
        argv, home=home, stdin=stdin, path=os.environ.get("PATH", "/usr/bin:/bin"),
        env={"PYTHONPATH": str(block_dir), "TELEMETRY_BLOCK_LOG": str(log),
             "CLAUDE_PROJECT_DIR": str(REPO), **(env or {})},
    )
    attempts = log.read_text().splitlines() if log.exists() else []
    return Blocked(outcome, attempts)


def make_venv(home: Path) -> Path:
    """A real venv at the place the hook retries, holding no package: whatever the host has
    installed, this one cannot supply it."""
    target = home / ".kensaiapp" / "venv"
    done = subprocess.run([sys.executable, "-m", "venv", "--without-pip", str(target)],
                          capture_output=True, timeout=120, check=False)
    if done.returncode != 0:
        raise HarnessError(f"could not make a venv: {done.stderr.decode()}")
    return target / "bin" / "python"


def write_usage_transcript(path: Path, *, input_tokens: int) -> Path:
    """A one-response transcript whose current context is `input_tokens`."""
    usage = {"input_tokens": input_tokens, "cache_read_input_tokens": 0,
             "cache_creation_input_tokens": 0}
    path.write_text(json.dumps({"type": "assistant", "message": {"id": "m1", "usage": usage}})
                    + "\n")
    return path


OWN_PREFIX = os.path.realpath(sys.prefix)
HOOK_STDIN = json.dumps({"tool_name": "Bash", "transcript_path": "/nonexistent/t.jsonl"}).encode()


def test_commands_without_package_end_cleanly(tmp_path):
    bare = tmp_path / "bare-home"
    bare.mkdir()
    venv_home = tmp_path / "venv-home"
    venv_home.mkdir()
    venv_python = make_venv(venv_home)
    notice = (CONTEXT_LINE + "\n").encode()
    cap = {"KENSAIAPP_CONTEXT_CAP": "1000"}

    no_venv = run_blocked(
        [sys.executable, str(HOOK)], tmp_path, home=bare, stdin=HOOK_STDIN, env=cap
    )
    assert no_venv.outcome == Outcome(notice, b"", 0)
    assert no_venv.attempted_by == [OWN_PREFIX]  # the blocker really refused it

    retried = run_blocked([sys.executable, str(HOOK)], tmp_path, home=venv_home,
                          stdin=HOOK_STDIN, env=cap)
    assert retried.outcome == Outcome(notice, b"", 0)  # the venv child's notice, forwarded once
    venv_prefix = os.path.realpath(venv_python.parents[1])
    assert sorted(set(retried.attempted_by)) == sorted({OWN_PREFIX, venv_prefix})

    refusals = {
        "chain_usage": (["chain_usage.py", "--logs-dir", "/missing", "--project", "demo"], 1),
        "run_provenance": (["run_provenance.py", str(uuid.uuid4())], 4),
        "measure": (None, 1),
    }
    for reader, (args, status) in refusals.items():
        if reader == "measure":
            argv = [sys.executable, str(MEASURE), "totals", "--agents-json", "/missing.json"]
        else:
            argv = [sys.executable, str(TOOLS_DIR / args[0]), *args[1:]]
        blocked = run_blocked(argv, tmp_path, home=bare)
        assert blocked.outcome.stdout == b"", reader
        assert blocked.outcome.stderr == (
            f"{reader}: needs the ka_telemetry package, which this Python cannot import\n".encode()
        ), reader
        assert blocked.outcome.status == status, reader
        assert blocked.attempted_by == [OWN_PREFIX], reader
        assert b"Traceback" not in blocked.outcome.stderr


@pytest.mark.parametrize(
    "stdin",
    [b'"scalar"', b"[1, 2]", b"{}", b"null", b'{"transcript_path": "/missing"}',
     b'{"transcript_path": ""}'],
)
def test_unavailable_hook_notice_precedes_transcript_access(tmp_path, stdin):
    bare = tmp_path / "home"
    bare.mkdir()
    venv_home = tmp_path / "venv-home"
    venv_home.mkdir()
    venv_python = make_venv(venv_home)
    cap = {"KENSAIAPP_CONTEXT_CAP": "5"}
    empty = tmp_path / "empty.jsonl"
    empty.write_text("")
    malformed = tmp_path / "bad.jsonl"
    malformed.write_text("not json\n{")
    over_cap = write_usage_transcript(tmp_path / "over.jsonl", input_tokens=1_000_000)
    payloads = [stdin] + [
        json.dumps({"transcript_path": str(path)}).encode()
        for path in (empty, malformed, over_cap)  # over the cap: still the notice, never a pause
    ]
    for payload in payloads:
        no_venv = run_blocked(
            [sys.executable, str(HOOK)], tmp_path, home=bare, stdin=payload, env=cap
        )
        in_venv = run_blocked([str(venv_python), str(HOOK)], tmp_path, home=venv_home,
                              stdin=payload, env=cap)
        for blocked in (no_venv, in_venv):  # the second proves a venv child does not retry again
            assert blocked.outcome == Outcome((CONTEXT_LINE + "\n").encode(), b"", 0)


def test_unavailable_hook_stays_silent_for_ineligible_input(tmp_path):
    bare = tmp_path / "home"
    bare.mkdir()
    for cap, stdin in (
        (None, HOOK_STDIN), ("abc", HOOK_STDIN), ("0", HOOK_STDIN), ("1_000", HOOK_STDIN),
        ("٣", HOOK_STDIN), ("1000", b"this is not json"),
    ):
        blocked = run_blocked([sys.executable, str(HOOK)], tmp_path, home=bare, stdin=stdin,
                              env={} if cap is None else {"KENSAIAPP_CONTEXT_CAP": cap})
        assert blocked.outcome == Outcome(b"", b"", 0), (cap, stdin)
        assert blocked.attempted_by == []  # silent before the package was even asked for


@skipping_for_prerequisites
def test_the_hook_caps_from_a_satellite_through_the_host_core(tmp_path):
    """CP-662's example: a satellite with no `core/`, whose `.env` names this host's core, cap
    1000 and a transcript at 5000 gives the pause notice naming 5000. Started under the venv and
    under the suite's own interpreter, which reaches the package directly or through the retry."""
    need(os.access(VENV / "bin" / "python", os.X_OK), f"the package interpreter {VENV}/bin/python")
    probe = subprocess.run([str(VENV / "bin" / "python"), "-c", f"import {PACKAGE}"],
                           capture_output=True, check=False)
    need(probe.returncode == 0, "the package cannot be imported by the venv interpreter")
    home = tmp_path / "home"
    (home / ".kensaiapp").mkdir(parents=True)
    (home / ".kensaiapp" / "venv").symlink_to(VENV)
    satellite = tmp_path / "satellite"
    satellite.mkdir()
    (satellite / ".env").write_text(f"CORE={REPO / 'core'}\n")
    assert not (satellite / "core").exists()
    transcript = write_usage_transcript(tmp_path / "t.jsonl", input_tokens=5_000)
    payload = json.dumps({"tool_name": "Bash", "transcript_path": str(transcript)}).encode()

    for interpreter in (str(home / ".kensaiapp" / "venv" / "bin" / "python"), sys.executable):
        done = start([interpreter, str(HOOK)], home=home, stdin=payload,
                     env={"CLAUDE_PROJECT_DIR": str(satellite), "KENSAIAPP_CONTEXT_CAP": "1000"})
        assert (done.status, done.stderr) == (0, b""), interpreter
        context = json.loads(done.stdout)["hookSpecificOutput"]["additionalContext"]
        assert "5000" in context and "1000" in context, interpreter
        assert "paused after task" in context, interpreter


# ── the previous implementation, from Git, in a temporary tree ──────────────────────────────


def materialize_previous(destination: Path) -> Path:
    """The callers' previous bytes and everything they import, at `BASE`, laid out as in the
    repository so the measurement's relative core lookup and the hook's resolver work. Nothing
    in the checkout is read or changed."""
    destination.mkdir(parents=True, exist_ok=True)
    archive = subprocess.run(
        ["git", "-C", str(REPO), "archive", BASE, "core/tools", ".claude/hooks",
         "system/projects/product-definition/docs/sdd-runner-cache-read"],
        capture_output=True, check=False,
    )
    if archive.returncode != 0:
        raise HarnessError(f"git archive {BASE} failed: {archive.stderr.decode()}")
    unpack = subprocess.run(["tar", "-x", "-C", str(destination)], input=archive.stdout,
                            capture_output=True, check=False)
    if unpack.returncode != 0:
        raise HarnessError(f"could not unpack the previous tree: {unpack.stderr.decode()}")
    return destination


@pytest.fixture(scope="module")
def previous(tmp_path_factory):
    return materialize_previous(tmp_path_factory.mktemp("previous-tree"))


def test_parser_outputs_survive_dependency_absence(tmp_path, previous):
    """Help, unknown options and invalid choices are answered by the parser, exactly as the
    previous implementation answered them, with the package unimportable on both sides."""
    home = tmp_path / "home"
    home.mkdir()
    old_tools = previous / "core" / "tools"
    old_measure = previous / MEASURE.relative_to(REPO)
    pairs = [
        ("chain_usage", old_tools / "chain_usage.py", TOOLS_DIR / "chain_usage.py", a)
        for a in (["--help"], ["--no-such-option"], ["--since"])
    ] + [
        ("measure", old_measure, MEASURE, a)
        for a in (["--help"], ["not-a-command"], ["totals", "--no-such-option"])
    ] + [
        ("run_provenance", old_tools / "run_provenance.py", TOOLS_DIR / "run_provenance.py", a)
        for a in ([], ["one", "two"])
    ]
    for importer, old_file, new_file, args in pairs:
        old = run_blocked([sys.executable, str(old_file), *args], tmp_path, home=home).outcome
        new = run_blocked([sys.executable, str(new_file), *args], tmp_path, home=home).outcome
        assert new == old, (importer, args)
        assert (old.status == 2) or args == ["--help"], (importer, args)
    # parser-accepted calls lacking data take the dependency refusal before any validation
    lacking = ([], ["--project", "demo"], ["--logs-dir", "/missing"], ["--state", "/missing.json"])
    for args in lacking:
        blocked = run_blocked([sys.executable, str(TOOLS_DIR / "chain_usage.py"), *args],
                              tmp_path, home=home)
        assert blocked.outcome.status == 1
        assert blocked.outcome.stdout == b""
        assert blocked.outcome.stderr.startswith(b"chain_usage: needs the ")
    measure = run_blocked([sys.executable, str(MEASURE), "totals", "--agents-json", "/missing"],
                          tmp_path, home=home)
    assert (measure.outcome.status, measure.outcome.stdout) == (1, b"")


def test_migrated_imports_are_safe_without_the_package():
    script = SUBPROCESS_BLOCKER + """
import telemetry_gateway, chain_usage, run_provenance
parsed = chain_usage.watch_log_name("watch-demo-20260909-145750.log", "demo")
print(json.dumps([attempts, parsed is not None]))
"""
    done = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True,
                          timeout=60, cwd=TOOLS_DIR)
    assert (done.returncode, done.stderr) == (0, "")
    assert json.loads(done.stdout) == [[], True]


# ── the measurement, through an explicit reader ─────────────────────────────────────────────


def load_measure():
    spec = importlib.util.spec_from_file_location("measure_under_test", MEASURE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # a dataclass resolves its own module by name
    spec.loader.exec_module(module)
    return module


def test_measurement_uses_explicit_gateway_reader(backend, tmp_path, capsys):
    measure = load_measure()
    agents = tmp_path / "agents.json"
    block = {"type": "assistant", "message": {
        "id": "m1", "model": "model-a",
        "usage": {"input_tokens": 3, "output_tokens": 2, "cache_read_input_tokens": 1},
        "content": [{"type": "tool_use", "name": "Bash"}]}}
    transcript = {Path("/x/s-1.jsonl"): [json.dumps(block), json.dumps(block)]}
    backend.file_port.read_lines = lambda path: (
        ["[]"] if path == agents else transcript.get(path)
    )
    backend.parsed_runs = SimpleNamespace(
        runs=(package_run("s-1", name="alpha run", started_at=5), package_run("s-2", name="beta")),
        interactive_excluded=1, dropped_no_session=0, total_seen=3, listed=2,
    )
    backend.runs.transcript_for = lambda session_id, root, files: (
        backend.calls.append(("transcript_for", session_id, root, files))
        or (Path("/x/s-1.jsonl") if session_id == "s-1" else None)
    )
    backend.records = [(block["message"]["usage"], "model-a", None)]
    backend.spend = {"model-a": package_spend(input=3, output=2, cache_read=1)}
    reader = measure.build_reader(gateway.build_telemetry(backend))

    measure.cmd_totals(reader, agents, "alpha")
    shown = capsys.readouterr().out
    assert "# /alpha/i -> 1 runs of 3 rows (1 interactive excluded)" in shown
    assert "raw_records=1" in shown and "api_calls=1" in shown
    names = [call[0] for call in backend.calls]
    assert names.count("runs_from") == 1 and names.count("usage_records") == 1
    assert names.count("spend_by_model") == 2  # raw and deduplicated, both through the gateway
    assert ("transcript_for", "s-1", reader.projects_root, backend.file_port) in backend.calls

    measure.cmd_totals(reader, agents, "beta")
    assert "NO TRANSCRIPT" in capsys.readouterr().out
    measure.cmd_totals(reader, agents, "no-such-run")
    assert "-> 0 runs of 3 rows" in capsys.readouterr().out


# ── the tracked tree has one door ───────────────────────────────────────────────────────────


def git_lines(*args: str) -> list[str]:
    done = subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True,
                          check=False)
    if done.returncode not in (0, 1):
        raise HarnessError(done.stderr)
    return done.stdout.splitlines()


def test_tracked_python_has_only_the_gateway_package_boundary():
    assert set(git_lines("grep", "-l", "ka_telemetry", "--", "*.py")) == THE_TWO_PATHS

    gateway_tree = ast.parse((REPO / GATEWAY_PATH).read_text())
    for node in ast.walk(gateway_tree):
        if isinstance(node, ast.FunctionDef):
            nested = {id(inner) for inner in ast.walk(node)}
            for other in ast.walk(gateway_tree):
                if isinstance(other, (ast.Import, ast.ImportFrom)) and id(other) in nested:
                    assert node.name == "build_telemetry"
    imports = [n for n in ast.walk(gateway_tree)
               if isinstance(n, ast.ImportFrom) and (n.module or "").startswith(PACKAGE)]
    assert len(imports) == 1
    assert not [n for n in gateway_tree.body if isinstance(n, (ast.Import, ast.ImportFrom))
                and PACKAGE in ast.unparse(n)]

    for relative in FOUR_CALLERS:
        tree = ast.parse((REPO / relative).read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert not {a.name.split(".")[0] for a in node.names} & SIX_OLD_MODULES, relative
            if isinstance(node, ast.ImportFrom):
                assert (node.module or "").split(".")[0] not in SIX_OLD_MODULES, relative
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    assert "run_usage" not in ast.unparse(base), relative
                    assert PACKAGE not in ast.unparse(base), relative

    private = [line for line in git_lines("grep", "-n", "-F", "_attr(", "--", "*.py")
               if line.split(":")[0] not in THE_TWO_PATHS | {
                   "core/tools/agent_usage.py", "core/tools/test_agent_usage.py"}]
    assert private == []
    calls = [n for n in ast.walk(gateway_tree)
             if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
             and n.func.attr == "_attr"]
    assert len(calls) == 1


# ── the live comparisons: one snapshot, two implementations ─────────────────────────────────


def take_copy(source: Path, destination: Path) -> None:
    """A copy of `source` as it stands now, bounded by the size it has at opening: a clone where
    the volume offers one, otherwise a loop that stops at the size read when it opened, so a
    file still being appended to cannot make it chase a moving end."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    cloned = subprocess.run(["/bin/cp", "-c", str(source), str(destination)],
                            capture_output=True, check=False)
    if cloned.returncode != 0:
        with source.open("rb") as reading, destination.open("wb") as writing:
            remaining = os.fstat(reading.fileno()).st_size
            while remaining:
                chunk = reading.read(min(1 << 20, remaining))
                if not chunk:
                    break
                writing.write(chunk)
                remaining -= len(chunk)
    destination.chmod(0o444)


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as reading:
        for block in iter(lambda: reading.read(1 << 24), b""):
            hasher.update(block)
    return hasher.hexdigest()


def test_the_copy_is_bounded_and_unaffected_by_a_later_append(tmp_path):
    """A controlled append to a temporary stand-in after it was copied reaches neither the copy
    nor a reader of it. The owner's own inputs are never appended to."""
    stand_in = tmp_path / "stand-in.jsonl"
    stand_in.write_text("line one\nline two\n")
    copy = tmp_path / "snap" / "stand-in.jsonl"
    take_copy(stand_in, copy)
    before = digest(copy)
    with stand_in.open("a") as appending:
        appending.write("line three, written by the receiver after the snapshot\n")
    assert digest(copy) == before
    assert copy.read_text() == "line one\nline two\n"
    assert not copy.is_symlink() and copy.stat().st_nlink == 1


@dataclass(frozen=True)
class Snapshot:
    root: Path
    home: Path
    previous: Path
    agents: Path
    logs_dir: Path
    project: str
    run_id: str
    transcript: Path
    cap: int
    population: str
    manifest: dict = field(default_factory=dict)

    @property
    def python(self) -> str:
        return str(self.home / ".kensaiapp" / "venv" / "bin" / "python")

    @property
    def projects_root(self) -> Path:
        return self.home / ".claude" / "projects"


def previous_context(
    snapshot_previous: Path, python: str, transcript: Path, home: Path
) -> int | None:
    code = ("import sys; from pathlib import Path; sys.path.insert(0, sys.argv[1]); "
            "import context_gauge, run_usage; "
            "print(context_gauge.current_context(Path(sys.argv[2]), run_usage.Files()))")
    done = start([python, "-c", code, str(snapshot_previous / "core" / "tools"), str(transcript)],
                 home=home)
    text = done.stdout.decode().strip()
    return int(text) if text.isdigit() else None


def build_snapshot(root: Path) -> dict:
    """Take every live input once and select the four nonempty invocations from the copies."""
    need(os.access(VENV / "bin" / "python", os.X_OK), f"the package interpreter {VENV}/bin/python")
    probe = subprocess.run([str(VENV / "bin" / "python"), "-c", f"import {PACKAGE}"],
                           capture_output=True, check=False)
    need(probe.returncode == 0, "the package cannot be imported by the venv interpreter")
    need((LIVE_TELEMETRY / "logs.jsonl").is_file(), "the live telemetry log")
    claude = shutil.which("claude")
    need(claude, "the claude command that lists agents")
    listing = subprocess.run(
        [claude, "agents", "--json", "--all"], capture_output=True, check=False
    )
    need(listing.returncode == 0, "a readable agents listing")
    rows = json.loads(listing.stdout)
    need(rows, "an agents listing with rows")

    home = root / "home"
    (home / ".kensaiapp").mkdir(parents=True)
    (home / ".kensaiapp" / "venv").symlink_to(VENV)  # the one link: the installation itself
    (home / ".claude" / "projects").mkdir(parents=True)
    agents = root / "agents.json"
    agents.write_bytes(listing.stdout)
    for name in ("logs.jsonl", "metrics.jsonl"):
        if (LIVE_TELEMETRY / name).is_file():
            take_copy(LIVE_TELEMETRY / name, home / ".kensaiapp" / "telemetry" / name)
    previous = materialize_previous(root / "previous")
    python = str(home / ".kensaiapp" / "venv" / "bin" / "python")

    def copy_transcript(session_id: str) -> Path | None:
        for live in LIVE_PROJECTS.glob(f"*/{session_id}.jsonl"):
            if live.stat().st_size <= 150_000_000:
                target = home / ".claude" / "projects" / live.parent.name / live.name
                take_copy(live, target)
                return target
        return None

    # provenance: an exact run ID whose previous parser proves provenance in the copied log
    log_copy = home / ".kensaiapp" / "telemetry" / "logs.jsonl"
    size = log_copy.stat().st_size
    with log_copy.open("rb") as reading:
        reading.seek(max(0, size - 64_000_000))
        tail = reading.read()
    pattern = rb'"kensai\.run_id", "value": \{"stringValue": "([0-9a-f-]{36})"'
    ordered = list(dict.fromkeys(reversed(re.findall(pattern, tail))))[:25]
    run_id = ""
    for candidate in ordered:
        out = start([python, str(previous / "core/tools/run_provenance.py"), candidate.decode()],
                    home=home)
        if out.status == 0 and len(out.stdout.splitlines()) == 5:
            run_id = candidate.decode()
            break
    need(run_id, "a run ID in the copied log whose provenance the previous parser proves")

    # transcripts: the listing's runs that have a readable transcript, newest first
    runnable = [r for r in rows if r.get("kind") != "interactive" and r.get("name")]
    runnable.sort(key=lambda r: r.get("startedAt") or 0, reverse=True)
    copied: list[tuple[dict, Path]] = []
    for row in runnable:
        if len(copied) >= 6:
            break
        target = copy_transcript(row["sessionId"])
        if target is not None:
            copied.append((row, target))
    need(copied, "a listed run with a readable transcript")

    # hook: a copied transcript whose previous context reading exceeds one
    transcript, cap = None, 0
    for _row, target in copied:
        reading = previous_context(previous, python, target, home)
        if reading and reading > 1:
            transcript, cap = target, reading - 1
            break
    need(transcript, "a copied transcript with a previous context reading above one")

    # measurement: an exact-name population whose previous table has a run row
    population = ""
    for row, _target in copied:
        regex = "^" + re.escape(row["name"]) + "$"
        out = start([python, str(previous / MEASURE.relative_to(REPO)), "totals",
                     "--agents-json", str(agents), "--population", regex], home=home)
        if out.status == 0 and b"raw_records=" in out.stdout:
            population = regex
            break
    need(population, "a listed run the previous measurement tabulates")

    # chain: an instance's watcher logs for a project, joined to a copied transcript
    roots = list(dict.fromkeys(
        Path(r["cwd"].split("/.worktrees/")[0]) for r in rows if r.get("cwd")
    ))
    short_ids = {r["id"]: r["sessionId"] for r in rows if r.get("id") and r.get("sessionId")}
    chosen = None
    for instance in roots:
        logs = instance / "system" / "logs"
        if not logs.is_dir():
            continue
        stems = [m.group(1) for n in logs.iterdir() if (m := re.match(r"watch-([^-]+)-", n.name))]
        for project in [s for s, _ in sorted(((s, stems.count(s)) for s in set(stems)),
                                              key=lambda p: -p[1])][:6]:
            mine = sorted(logs.glob(f"watch-{project}-*.log"))[-25:]
            target_dir = root / "instance" / project / "system" / "logs"
            for log in mine:
                take_copy(log, target_dir / log.name)
                text = log.read_text(errors="replace")
                for short in re.findall(r"\(run ([0-9a-f]{8}) ", text):
                    if short in short_ids:
                        copy_transcript(short_ids[short])
                for session in re.findall(r"\(run session ([0-9a-f-]{36})\)", text):
                    copy_transcript(session)
            out = start([python, str(previous / "core/tools/chain_usage.py"), "--logs-dir",
                         str(target_dir), "--project", project, "--agents-json", str(agents),
                         "--projects-root", str(home / ".claude" / "projects"), "--json"],
                        home=home)
            try:
                runs = json.loads(out.stdout)["runs"]
            except (ValueError, KeyError):
                runs = []
            if out.status == 0 and any(r.get("transcript") == "read" for r in runs):
                chosen = (target_dir, project)
                break
        if chosen:
            break
    need(chosen, "an instance's watcher logs with a run joined to a readable transcript")

    manifest = {}
    for path in sorted(p for p in root.rglob("*") if p.is_file() and not p.is_symlink()
                       and "previous" not in p.relative_to(root).parts):
        manifest[str(path.relative_to(root))] = [path.stat().st_size, digest(path)]
    (root / "manifest.json").write_text(json.dumps(manifest))
    return {"logs_dir": str(chosen[0]), "project": chosen[1], "run_id": run_id,
            "transcript": str(transcript), "cap": cap, "population": population}


@pytest.fixture(scope="session")
def snapshot(tmp_path_factory):
    """One snapshot per test run, shared by every xdist worker: the first to ask builds it under
    a lock, the rest read what it recorded, and the last one out removes it."""
    run = os.environ.get("PYTEST_XDIST_TESTRUNUID") or uuid.uuid4().hex
    root = Path(tempfile.gettempdir()) / f"telemetry-gateway-snapshot-{run}"
    lock_path = root.with_suffix(".lock")
    users = root.with_suffix(".users")
    with lock_path.open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        users.write_text(str(int(users.read_text() or "0") + 1) if users.exists() else "1")
        ready = root / "ready.json"
        if not ready.exists():
            root.mkdir(exist_ok=True)
            try:
                ready.write_text(json.dumps(build_snapshot(root)))
            except MissingPrerequisite as exc:
                ready.write_text(json.dumps({"missing": str(exc)}))
        fcntl.flock(lock, fcntl.LOCK_UN)
    recorded = json.loads(ready.read_text())
    try:
        if "missing" in recorded:
            pytest.skip(f"missing prerequisite: {recorded['missing']}")
        yield Snapshot(
            root=root, home=root / "home", previous=root / "previous", agents=root / "agents.json",
            logs_dir=Path(recorded["logs_dir"]), project=recorded["project"],
            run_id=recorded["run_id"], transcript=Path(recorded["transcript"]),
            cap=recorded["cap"], population=recorded["population"],
            manifest=json.loads((root / "manifest.json").read_text()),
        )
    finally:
        with lock_path.open("a+") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            remaining = int(users.read_text()) - 1
            users.write_text(str(remaining))
            if remaining == 0:
                shutil.rmtree(root, ignore_errors=True)
                users.unlink(missing_ok=True)
            fcntl.flock(lock, fcntl.LOCK_UN)
        if remaining == 0:
            lock_path.unlink(missing_ok=True)


def stat_key(path: Path) -> tuple[int, int]:
    info = path.stat()
    return info.st_size, info.st_mtime_ns


def both_sides(snap: Snapshot, importer: str):
    """The previous and the candidate command for `importer`, on the same snapshot, the same
    interpreter and the same environment."""
    old_tools = snap.previous / "core" / "tools"
    chain_args = ["--logs-dir", str(snap.logs_dir), "--project", snap.project,
                  "--agents-json", str(snap.agents), "--projects-root", str(snap.projects_root),
                  "--json"]
    measure_args = ["totals", "--agents-json", str(snap.agents), "--population", snap.population]
    payload = json.dumps({"tool_name": "Bash", "transcript_path": str(snap.transcript)}).encode()
    cap = {"KENSAIAPP_CONTEXT_CAP": str(snap.cap)}
    if importer == "run_provenance":
        return (
            start([snap.python, str(old_tools / "run_provenance.py"), snap.run_id], home=snap.home),
            start([snap.python, str(TOOLS_DIR / "run_provenance.py"), snap.run_id], home=snap.home),
        )
    if importer == "context_cap":
        return (
            start([snap.python, str(snap.previous / ".claude/hooks/context_cap.py")],
                  home=snap.home, stdin=payload,
                  env={**cap, "CLAUDE_PROJECT_DIR": str(snap.previous)}),
            start([snap.python, str(HOOK)], home=snap.home, stdin=payload,
                  env={**cap, "CLAUDE_PROJECT_DIR": str(REPO)}),
        )
    if importer == "chain_usage":
        return (
            start([snap.python, str(old_tools / "chain_usage.py"), *chain_args], home=snap.home),
            start([snap.python, str(TOOLS_DIR / "chain_usage.py"), *chain_args], home=snap.home),
        )
    return (
        start([snap.python, str(snap.previous / MEASURE.relative_to(REPO)), *measure_args],
              home=snap.home),
        start([snap.python, str(MEASURE), *measure_args], home=snap.home),
    )


def settled(snap: Snapshot, importer: str, qualifies: Callable[[Outcome], bool]) -> None:
    inputs = [snap.agents, snap.home / ".kensaiapp" / "telemetry" / "logs.jsonl", snap.transcript]
    stamps = [stat_key(path) for path in inputs]
    old, new = both_sides(snap, importer)
    assert qualifies(old), f"the previous {importer} output is empty or not the selected case"
    assert differences(importer, old, new) == [], (old, new)
    assert [stat_key(path) for path in inputs] == stamps


@skipping_for_prerequisites
def test_live_provenance_matches_old_files(snapshot):
    settled(snapshot, "run_provenance",
            lambda out: out.status == 0 and len(out.stdout.splitlines()) == 5 and out.stderr == b"")


@skipping_for_prerequisites
def test_live_hook_matches_old_files(snapshot):
    settled(snapshot, "context_cap",
            lambda out: out.status == 0
            and "pause" in json.loads(out.stdout)["hookSpecificOutput"]["additionalContext"])


@skipping_for_prerequisites
def test_live_chain_matches_old_files(snapshot):
    settled(snapshot, "chain_usage",
            lambda out: out.status == 0 and len(json.loads(out.stdout)["runs"]) >= 1)


@skipping_for_prerequisites
def test_live_measurement_matches_old_files(snapshot):
    settled(snapshot, "measure", lambda out: out.status == 0 and b"raw_records=" in out.stdout)


@skipping_for_prerequisites
def test_live_comparisons_share_one_immutable_snapshot(snapshot):
    """Every worker reads the one snapshot, whose files still carry the hashes recorded when it
    was taken, with no link back to a live input."""
    for relative, (size, recorded) in snapshot.manifest.items():
        path = snapshot.root / relative
        assert path.stat().st_size == size, relative
        assert not path.is_symlink() and path.stat().st_nlink == 1, relative
    assert digest(snapshot.agents) == snapshot.manifest["agents.json"][1]
    log = snapshot.home / ".kensaiapp" / "telemetry" / "logs.jsonl"
    assert digest(log) == snapshot.manifest[str(log.relative_to(snapshot.root))][1]
    links = [p for p in snapshot.root.rglob("*") if p.is_symlink() and "previous" not in p.parts]
    assert links == [snapshot.home / ".kensaiapp" / "venv"]
    for path in snapshot.root.rglob("*"):
        if path.is_file() and "previous" not in path.parts:
            assert str(path.resolve()).startswith(str(snapshot.root.resolve())), path


@skipping_for_prerequisites
def test_documented_commands_and_registered_hook_use_installed_package(snapshot):
    """The venv commands the usage text names, and the literal command settings registers."""
    for reader, argv in (
        ("run_provenance",
         [snapshot.python, str(TOOLS_DIR / "run_provenance.py"), snapshot.run_id]),
        ("measure", [snapshot.python, str(MEASURE), "totals", "--agents-json",
                     str(snapshot.agents), "--population", snapshot.population]),
    ):
        done = start(argv, home=snapshot.home)
        assert done.status == 0 and done.stdout and done.stderr == b"", reader
    chain = start([snapshot.python, str(TOOLS_DIR / "chain_usage.py"), "--logs-dir",
                   str(snapshot.logs_dir), "--project", snapshot.project, "--agents-json",
                   str(snapshot.agents), "--projects-root", str(snapshot.projects_root), "--json"],
                  home=snapshot.home)
    assert chain.status == 0 and json.loads(chain.stdout)["runs"]

    settings = json.loads((REPO / ".claude" / "settings.json").read_text())
    command = next(
        h["command"]
        for e in settings["hooks"]["PostToolUse"]
        if e.get("matcher") == "Bash"
        for h in e["hooks"]
        if "context_cap.py" in h["command"]
    )
    payload = json.dumps(
        {"tool_name": "Bash", "transcript_path": str(snapshot.transcript)}
    ).encode()
    suite_python = str(Path(sys.executable).parent)
    path = f"{suite_python}:/usr/bin:/bin"  # a pytest-capable python3 first, without a venv one

    def registered(cap: int) -> Outcome:
        return start(["/bin/sh", "-c", command], home=snapshot.home, stdin=payload, path=path,
                     env={"CLAUDE_PROJECT_DIR": str(REPO), "KENSAIAPP_CONTEXT_CAP": str(cap)})

    over = registered(snapshot.cap)
    assert over.status == 0 and over.stderr == b""
    assert "paused after task" in json.loads(over.stdout)["hookSpecificOutput"]["additionalContext"]
    equal = registered(snapshot.cap + 1)
    assert equal == Outcome(b"", b"", 0)

    interpreter = "~/.kensaiapp/venv/bin/python <CORE>/tools/"
    for module in ("chain_usage.py", "run_provenance.py"):
        assert interpreter + module in (TOOLS_DIR / module).read_text()
    assert "4 this Python cannot import the telemetry package" in (
        TOOLS_DIR / "run_provenance.py").read_text()
    assert "~/.kensaiapp/venv/bin/python measure.py totals" in MEASURE.read_text()
