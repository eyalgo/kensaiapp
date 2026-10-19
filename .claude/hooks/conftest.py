"""Pytest bootstrap for `.claude/hooks` — the same net `core/launchers` and `core/tools` run inside.

A hook's own suite spawns `git` in throwaway repositories exactly as a launcher suite does, so it
needs the same guard against an inherited `GIT_CONFIG_*` override: under a pin the injected
`core.hooksPath` reaches every `git` a fixture spawns, and a throwaway repo's own commit is then
refused by the pin's `commit-msg` hook. Measured 2026-09-23, under a pinned session:
`.claude/hooks/test_written_forward_guard.py` failed 9 cases and `test_resolve_core.py` 1, all of
them that refusal; with the variables cleared, all pass.

`core/tools` is appended to `sys.path`, not inserted, so no module a hook suite imports is shadowed
by one there.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2] / "core" / "tools"))

from pytest_guardrails import (  # noqa: E402,F401
    _no_ambient_colour,
    _no_ambient_git_config,
    _no_ambient_ollama,
    _no_ambient_telemetry,
)
