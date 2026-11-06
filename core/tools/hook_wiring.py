"""The one rewrite of a settings document's live hooks and core directories.

A host's tracked `settings.json` names each hook command as the runner and the script,
`${CLAUDE_PROJECT_DIR}/core/tools/locked_python.sh` and
`${CLAUDE_PROJECT_DIR}/.claude/hooks/<script>`, which resolve to whichever repo the session runs
in. Two consumers need the same document with both
prefixes pointed at one fixed hooks directory and one fixed core directory instead: a pinned run
(the pin's own hooks and runner, `agent_run.py`) and a satellite (the host's hooks and runner,
`link_satellite.py`, because a satellite holds neither hook scripts nor a `core/` of its own).
Keeping the rewrite here means both read the prefixes from one place, and each command reaches the
lock at the root of the copy whose runner it names.
"""

from __future__ import annotations

from pathlib import Path

__version__ = "1.1.0"

LIVE_HOOKS_PREFIX = "${CLAUDE_PROJECT_DIR}/.claude/hooks/"
LIVE_CORE_PREFIX = "${CLAUDE_PROJECT_DIR}/core/"


def rewrite_hooks_dir(document, hooks_dir: Path, core_dir: Path):
    """The same document with `LIVE_HOOKS_PREFIX` replaced by `hooks_dir` plus a slash and
    `LIVE_CORE_PREFIX` by `core_dir` plus a slash, wherever either appears inside a string value,
    at any depth. Keys and non-string values come back as they were, and the document passed in is
    not mutated."""
    if isinstance(document, dict):
        return {
            key: rewrite_hooks_dir(value, hooks_dir, core_dir) for key, value in document.items()
        }
    if isinstance(document, list):
        return [rewrite_hooks_dir(item, hooks_dir, core_dir) for item in document]
    if isinstance(document, str):
        return document.replace(LIVE_HOOKS_PREFIX, str(hooks_dir) + "/").replace(
            LIVE_CORE_PREFIX, str(core_dir) + "/"
        )
    return document
