"""Pytest bootstrap for `core/tools` — puts this directory on `sys.path` so
tests import `commit_builder` directly (a flat stdlib module, no package,
matching the convention `.claude/hooks/` already uses for `resolve_core.py`),
regardless of pytest's import mode or the working directory it is launched
from. Follows the `.claude/conftest.py`
precedent (same one-line shim, scoped to this directory).
"""

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

# No inherited telemetry variable, no inherited GIT_CONFIG_* override, and no secret value in a
# failure report — pytest_guardrails.py.
from pytest_guardrails import (  # noqa: E402,F401
    _no_ambient_colour,
    _no_ambient_git_config,
    _no_ambient_ollama,
    _no_ambient_provider_force,
    _no_ambient_telemetry,
    pytest_configure,
    pytest_runtest_makereport,
    pytest_sessionfinish,
    pytest_testnodedown,
)

import pin  # noqa: E402


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


@pytest.fixture(autouse=True)
def _no_ambient_notifier(monkeypatch):
    """No test in this folder inherits the machine's real `KENSAIAPP_NOTIFIER`.

    A net, not the mechanism. The mechanism is injection — a tool takes its notifier as an
    argument (`chain.py`'s `notify`, `watch_agent.py`'s `--notify`). The one environment read,
    `watch_agent.default_notifier()`, happens when arguments are parsed, inside a test, where
    this fixture has already cleared the variable. This exists for the tool that forgets, because the failure is invisible
    to pytest: on 2026-08-31 a green `test_chain.py` sent six real messages to the owner's
    phone, and nothing in the suite, the integrity pass or the flow could see it — a send is
    not a failure. A person noticing their phone was the only detector.

    Tests that genuinely exercise sending set their own value, which still works: this only
    clears what was inherited.
    """
    monkeypatch.delenv("KENSAIAPP_NOTIFIER", raising=False)
