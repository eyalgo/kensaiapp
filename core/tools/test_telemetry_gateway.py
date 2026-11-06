"""Tests for telemetry_gateway.py — the one door to the optional telemetry package.

Nothing here monkeypatches the module under test. The gateway is handed a hand-written backend
through `build_telemetry`, and the backend records what it received. The package is made
unimportable (or recorded) with an import blocker, never by patching a gateway name.

The second half holds the completed-caller contracts: what each reader under the shared roots does
with the package absent in a started interpreter, and the tracked-tree boundary. Every input is
made here — a test reads nothing of the machine it runs on
(`core/doctrine/engineering/testing_doctrine.md`).
"""

from __future__ import annotations

import ast
import importlib.abc
import importlib.util
import json
import os
import subprocess
import sys
import uuid
from dataclasses import dataclass
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


# ═══ The callers, without the package ══════════════════════════════════════════════════════

REPO = TOOLS_DIR.parents[1]
HOOK = REPO / ".claude" / "hooks" / "context_cap.py"
GATEWAY_PATH = "core/tools/telemetry_gateway.py"
THE_TWO_PATHS = {GATEWAY_PATH, "core/tools/test_telemetry_gateway.py"}
SIX_OLD_MODULES = {
    "otel_receiver", "agent_usage", "run_usage", "flow_usage", "context_gauge",
    "apply_telemetry_env",
}
# The callers under this repository's shared roots. A caller that lives in a private project is
# tested in that project, never from here.
CALLERS = (
    ".claude/hooks/context_cap.py",
    "core/tools/chain_usage.py",
    "core/tools/run_provenance.py",
)


class HarnessError(Exception):
    """The harness itself failed. Never a skip."""


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
    }
    for reader, (args, status) in refusals.items():
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

    for relative in CALLERS:
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
