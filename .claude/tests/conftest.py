"""Pytest bootstrap for `.claude/tests` — the same net `.claude/hooks` runs inside.

`test_resolve_core_githooks.py` asks `git config --get core.hooksPath` of a throwaway repository,
so an inherited `GIT_CONFIG_*` override answers for it: under a pin the injected `core.hooksPath`
is what every `git` a fixture spawns reads, and a fresh repo then looks already wired. Measured
2026-09-30, under a pinned session: 5 of that file's 6 cases failed, the first on "precondition: a
fresh repo carries no hooksPath"; with the variables cleared, all 6 pass.

`core/tools` is appended to `sys.path`, not inserted, so no module a suite here imports is
shadowed by one there.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2] / "core" / "tools"))

from pytest_guardrails import (  # noqa: E402,F401
    _no_ambient_colour,
    _no_ambient_git_config,
    _no_ambient_telemetry,
)
