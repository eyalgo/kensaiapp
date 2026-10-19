#!/usr/bin/env python3
"""Compatibility import for the provider-neutral task-context reader.

The parser moved to ``<CORE>/tools/task_context.py`` so Claude hooks and Codex
runs consume one context definition.  This module keeps the hook-local import
surface for any older caller while resolving the instance's bound core before
loading that implementation.  It is not itself a hook.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

__version__ = "2.0.0"


def _implementation(project_dir: str):
    import resolve_core

    core_root = Path(resolve_core._resolve(project_dir))
    candidates = (
        core_root / "tools",
        Path(__file__).resolve().parents[2] / "core" / "tools",
    )
    for candidate in reversed(candidates):
        sys.path.insert(0, str(candidate))
    import task_context

    return task_context, core_root


def map_path(project_dir: str) -> str:
    task_context, core_root = _implementation(project_dir)
    return str(task_context.map_path(core_root))


def routes(path: str):
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    task_context, _ = _implementation(project_dir)
    return task_context.routes(Path(path))


def unprompted(rows):
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    task_context, _ = _implementation(project_dir)

    return task_context.unprompted(rows)


def routing_context(project_dir: str) -> str:
    task_context, core_root = _implementation(project_dir)
    return task_context.routing_context(core_root)


def standing_rules_context(project_dir: str) -> str:
    task_context, core_root = _implementation(project_dir)
    return task_context.standing_rules_context(core_root)
