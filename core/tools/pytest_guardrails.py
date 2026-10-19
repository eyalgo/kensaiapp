"""pytest_guardrails.py — the net every suite under `core/tools/` and `core/launchers/` runs inside.
Each root's `conftest.py` imports the fixture and the hooks below; `-p pytest_guardrails` loads them
into any other run.

Six guards, all nets rather than mechanisms. The mechanism is a test handing its subprocess an
environment it built; these exist for the test that forgets, as `conftest.py`'s notifier net does.

1. **No inherited telemetry.** A machine that turns telemetry on for every session exports
   `CLAUDE_CODE_ENABLE_TELEMETRY` and `OTEL_*` into each shell, and a test asserting what a tool
   exported must not read those as the tool's. They are cleared before every test; a test may still
   set its own.
2. **No inherited `GIT_CONFIG_*` override.** A session whose own `core.hooksPath` is injected via
   `GIT_CONFIG_COUNT` + `GIT_CONFIG_KEY_N`/`GIT_CONFIG_VALUE_N` (rather than a repo-local
   `.git/config`) leaks that override into every `git` subprocess a test spawns — including a
   throwaway fixture repo's own commit, which this repo's real `commit-msg` hook then refuses for
   trailers no fixture message carries. Measured 2026-09-23: under such a session, `pytest
   core/tools/` reported 234 failed; with the ambient variables cleared, 3762 passed, 1 skipped.
   Cleared before every test, the same way telemetry is; a test may still set its own.
3. **No secret in a report — whole, or shortened.** A failing assertion prints the objects it
   compared, and an object built from the environment prints every credential the shell carries —
   on 2026-09-10 one failing test printed two live API credentials into a session transcript. The
   value of every secret-named variable is replaced by `<redacted:NAME>` **where the output
   leaves** — the terminal writer every channel pytest itself prints through (an assertion
   failure, captured output, a collection error, the warnings summary, a parametrize id, a skip
   reason), and the junit file, once, after it is written — rather than by mutating each report
   object. No report's `longrepr` is ever replaced by a value of a different type, so nothing
   pytest inspects about a report (a skip's `(path, line, reason)` tuple included) breaks, and the
   guard never changes a run's exit code. pytest shortens a long repr to a head run and a tail run
   around `...`; a run of at least `_MIN_FRAGMENT_LENGTH` characters taken from a secret's start or
   end is redacted too, so the shortened form leaks no more than the full one does.

   **Not covered:** a test's own `print()` under `-s` / `--capture=no`. Disabling pytest's capture
   also bypasses the terminal writer this guard patches — the print goes straight to the real file
   descriptor. Measured, stated here and in `test_pytest_guardrails.py`'s
   `TestCaptureNoIsMeasuredNotAssumed`, not assumed away.
4. **No inherited colour request.** A shell exporting `FORCE_COLOR` makes Python 3.14's argparse
   colour `--help`, and the `test_commit_builder.py` help tests look for plain text: measured
   2026-10-02, `pytest core/tools/` gave 3 failed, 5585 passed, 1 skipped under it, and
   `NO_COLOR=1 pytest core/tools/` gave 5588 passed, 1 skipped. `FORCE_COLOR` is removed and
   `NO_COLOR` set before every test, so plain `pytest core/tools/` is green whatever the shell
   exports; a test may still set its own.
5. **No inherited provider force.** Every launcher reads an exported `KENSAIAPP_AGENT_PROVIDER` as
   a force and appends `--provider` to the argv a launcher test compares: measured 2026-10-03, the
   chain-* and build-idea launcher suites gave 5 failed, 268 passed under it. Cleared before every
   test; a test may still set its own.
6. **No live Ollama server.** An `ollama` command is refused unless a server answers at
   `KENSAIAPP_OLLAMA_URL`, else `http://localhost:11434`, which is the owner's own server. Left
   alone, a suite would pass or fail on whether that server happens to be running, and a test could
   spend the owner's local model. Every test is given an `http://127.0.0.1:<port>` address where
   nothing listens; a test that needs a server sets its own over it.
"""

from __future__ import annotations

import os
import re
import socket
from collections.abc import Mapping
from pathlib import Path

import pytest

__version__ = "1.5.0"

_SECRET_NAME = re.compile(r"KEY|SECRET|TOKEN|PASSWORD|PASSWD|CREDENTIAL|PRIVATE", re.IGNORECASE)
# A value this short is a flag or a count, not a credential, and redacting it would scramble output.
_MIN_SECRET_LENGTH = 8
# pytest shortens a long repr by keeping a head run and a tail run around `...`
# (`_pytest._io.saferepr._ellipsize`), sized off `maxsize = (80 - 15 - len(op) - 2) // 2`
# (`_pytest/assertion/util.py`) for a two-character operator such as `==`. For that `maxsize`,
# `_ellipsize`'s own split keeps a 12-character head and a 13-character tail of the raw string
# once the repr's quote character is subtracted — 12 is the smaller of the two, so it is the run
# length guaranteed present whichever end shows. Measured against a live pytest run in
# `TestShortenedFragmentThreshold`, not read off pytest's source and assumed to hold.
_MIN_FRAGMENT_LENGTH = 12
_TELEMETRY_PREFIXES = ("OTEL_", "CLAUDE_CODE_ENABLE_TELEMETRY")


def secret_values(environ: Mapping[str, str]) -> dict[str, str]:
    """The variables in `environ` whose name marks them as secret and whose value is long enough
    to be one."""
    return {
        name: value
        for name, value in environ.items()
        if _SECRET_NAME.search(name) and len(value) >= _MIN_SECRET_LENGTH
    }


def _redact_head_runs(text: str, value: str, marker: str) -> str:
    """`text` with every run that starts like `value` for at least `_MIN_FRAGMENT_LENGTH`
    characters replaced by `marker` — the whole run, however far it keeps matching `value`, not
    only its first `_MIN_FRAGMENT_LENGTH`. pytest's repr cap keeps a head far longer than that
    (about 118 characters at the default 240), and cutting only its first 12 leaves the rest
    printed."""
    head = value[:_MIN_FRAGMENT_LENGTH]
    pieces = []
    start = 0
    while (found := text.find(head, start)) != -1:
        end = found + len(head)
        while end - found < len(value) and end < len(text) and text[end] == value[end - found]:
            end += 1
        pieces.append(text[start:found])
        pieces.append(marker)
        start = end
    pieces.append(text[start:])
    return "".join(pieces)


def _redact_tail_runs(text: str, value: str, marker: str) -> str:
    """The mirror of `_redact_head_runs`: every run that ends like `value` for at least
    `_MIN_FRAGMENT_LENGTH` characters, replaced whole."""
    return _redact_head_runs(text[::-1], value[::-1], marker[::-1])[::-1]


def redact(text: str, secrets: Mapping[str, str]) -> str:
    """`text` with every occurrence of each secret value redacted — whole, or shortened to a run
    of at least `_MIN_FRAGMENT_LENGTH` characters taken from its start or its end, which is what
    pytest's own truncation leaves behind; such a run is redacted in full, whatever its length.
    Longest value first so a secret that contains another is replaced whole before its shorter
    shared runs are considered."""
    for name, value in sorted(secrets.items(), key=lambda item: len(item[1]), reverse=True):
        marker = f"<redacted:{name}>"
        text = text.replace(value, marker)
        if len(value) < _MIN_FRAGMENT_LENGTH:
            continue
        text = _redact_head_runs(text, value, marker)
        text = _redact_tail_runs(text, value, marker)
    return text


# Taken at import, before any fixture runs, so a value a guard or a test later removes from the
# environment is still known to the hook. Grown by `pytest_runtest_makereport` below with whatever
# a test sets for itself, because output is printed at session end — after a `monkeypatch.setenv`
# a test made has already been undone by that test's own teardown.
_SECRETS_SEEN = dict(secret_values(os.environ))


@pytest.fixture(autouse=True)
def _no_ambient_telemetry(monkeypatch):
    for name in [name for name in os.environ if name.startswith(_TELEMETRY_PREFIXES)]:
        monkeypatch.delenv(name)


@pytest.fixture(autouse=True)
def _no_ambient_git_config(monkeypatch):
    """No test in this folder inherits the invoking session's `GIT_CONFIG_*` override
    variables — see guard 2 in the module docstring for why an inherited `core.hooksPath`
    override breaks a throwaway fixture repo's own commit. A test that genuinely exercises one
    of these variables sets it for itself, which still works; this only clears what was
    inherited."""
    for name in [
        name for name in os.environ
        if name == "GIT_CONFIG_COUNT" or name.startswith(("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_"))
    ]:
        monkeypatch.delenv(name)


@pytest.fixture(autouse=True)
def _no_ambient_colour(monkeypatch):
    """No test inherits the invoking shell's `FORCE_COLOR` — see guard 4 in the module docstring.
    Colour is declined for the test and for every process it starts."""
    monkeypatch.delenv("FORCE_COLOR", raising=False)
    monkeypatch.setenv("NO_COLOR", "1")


@pytest.fixture(autouse=True)
def _no_ambient_provider_force(monkeypatch):
    """No test inherits the invoking shell's `KENSAIAPP_AGENT_PROVIDER` — see guard 5 in the module
    docstring."""
    monkeypatch.delenv("KENSAIAPP_AGENT_PROVIDER", raising=False)


@pytest.fixture(autouse=True)
def _no_ambient_ollama(monkeypatch):
    """No test reaches the owner's Ollama server — see guard 6 in the module docstring. The port
    is one the OS just handed out and this fixture has closed again, so nothing listens on it."""
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    monkeypatch.setenv("KENSAIAPP_OLLAMA_URL", f"http://127.0.0.1:{port}")


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo) -> None:
    """Observe, never mutate. A plain (non-wrapper) hookimpl that returns `None` never blocks the
    real report from being built, and reads `os.environ` while a test's own `monkeypatch.setenv`
    is still in effect — before that test's teardown unsets it — so a secret set only inside the
    test body is not lost by the time the deferred terminal output for it is finally written."""
    _SECRETS_SEEN.update(secret_values(os.environ))


def _current_secrets() -> dict[str, str]:
    """Every secret-named variable seen at any point in this process: at import, and at every
    report `pytest_runtest_makereport` observed since."""
    return dict(_SECRETS_SEEN)


@pytest.hookimpl(trylast=True)
def pytest_configure(config: pytest.Config) -> None:
    """Redact at the one place every terminal-bound line passes through: the session's
    `TerminalReporter._tw.write`. `trylast` so `_pytest.terminal`'s own `pytest_configure` has
    already registered the `terminalreporter` plugin this reads — a plain hookimpl here runs before
    it and finds nothing.
    """
    terminal_reporter = config.pluginmanager.get_plugin("terminalreporter")
    if terminal_reporter is None:
        return
    tw = terminal_reporter._tw
    original_write = tw.write

    def _redacting_write(msg, *, flush: bool = False, **markup: bool) -> None:
        if isinstance(msg, str):
            secrets = _current_secrets()
            if secrets:
                msg = redact(msg, secrets)
        original_write(msg, flush=flush, **markup)

    tw.write = _redacting_write


@pytest.hookimpl(wrapper=True)
def pytest_sessionfinish(session: pytest.Session):
    """Redact the junit file once, after the `junitxml` plugin has written it. A hookwrapper always
    runs after every plain hookimpl for the same spec, `junitxml`'s included, whatever registration
    order gave it — so this needs no ordering marker of its own."""
    workeroutput = getattr(session.config, "workeroutput", None)
    if workeroutput is not None:
        # An xdist worker: hand what it saw to the controller, which prints the reports.
        workeroutput["secrets_seen"] = _current_secrets()
    result = yield
    xmlpath = getattr(session.config.option, "xmlpath", None)
    if xmlpath:
        secrets = _current_secrets()
        if secrets:
            path = Path(xmlpath)
            if path.exists():
                text = path.read_text(encoding="utf-8")
                cleaned = redact(text, secrets)
                if cleaned != text:
                    path.write_text(cleaned, encoding="utf-8")
    return result


@pytest.hookimpl(optionalhook=True)
def pytest_testnodedown(node, error) -> None:
    """Under `pytest-xdist` a test runs in a worker, so a secret it set for itself is seen there by
    `pytest_runtest_makereport` — while its report is printed here, in the controller. Each worker
    hands its `_SECRETS_SEEN` over as it finishes (`pytest_sessionfinish` above); the failure
    sections and the junit file are written after every worker is down, so they redact it too."""
    _SECRETS_SEEN.update(getattr(node, "workeroutput", {}).get("secrets_seen", {}))
