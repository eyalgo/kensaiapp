"""The guards a launcher suite inherits from `core/tools/pytest_guardrails.py`.

A launcher suite runs inside the same net `core/tools` does — `core/launchers/conftest.py` says so
in its own first sentence — and a guard reaches a folder's tests only by being imported into that
folder's `conftest.py`, where its `autouse=True` registers it. So the check is the import itself.

The git-config guard is here because of what its absence did: under a PINNED run the pin injects
`core.hooksPath` through `GIT_CONFIG_COUNT`/`GIT_CONFIG_KEY_n`, every `git` subprocess a fixture
spawns inherits it, and a throwaway repo's own seed commit is then refused by the pin's
`commit-msg` hook. Measured 2026-09-23 inside a pinned chain run: 18 failures across 17 launcher
files, 16 of them exactly that commit refusal, while the same suite ran green with the variables
cleared. `core/tools` gained the guard on 2026-09-23 (`pytest_guardrails._no_ambient_git_config`);
`core/launchers` imported only its sibling.
"""

from __future__ import annotations

import os
import socket
import urllib.parse

import pytest

# Imported by the collision-proof alias `core/launchers/conftest.py` registers for
# itself: under pytest's prepend import mode every folder's `conftest.py` answers to the
# same bare module name, so a bare `import conftest` resolves to whichever one a worker
# imported last.
import kensaiapp_launchers_conftest as launchers_conftest

def test_the_launcher_suites_inherit_the_git_config_guard():
    assert hasattr(launchers_conftest, "_no_ambient_git_config")


def test_the_launcher_suites_inherit_the_telemetry_guard():
    assert hasattr(launchers_conftest, "_no_ambient_telemetry")


def test_the_ollama_address_points_where_nothing_listens():
    address = urllib.parse.urlsplit(os.environ["KENSAIAPP_OLLAMA_URL"])

    assert address.hostname == "127.0.0.1"
    with pytest.raises(ConnectionRefusedError):
        socket.create_connection((address.hostname, address.port), timeout=5).close()
