"""The one rewrite of a settings document's live hooks directory.

A host's tracked `settings.json` names each hook script as
`${CLAUDE_PROJECT_DIR}/.claude/hooks/<script>`, which resolves to whichever repo the session runs
in. Two consumers need the same document with that prefix pointed at one fixed hooks directory
instead: a pinned run (the pin's own hooks, `agent_run.py`) and a satellite (the host's hooks,
`link_satellite.py`, because a satellite holds no hook scripts of its own). Keeping the rewrite
here means both read the prefix from one place.
"""

from __future__ import annotations

from pathlib import Path

__version__ = "1.0.0"

LIVE_HOOKS_PREFIX = "${CLAUDE_PROJECT_DIR}/.claude/hooks/"


def rewrite_hooks_dir(document, hooks_dir: Path):
    """The same document with `LIVE_HOOKS_PREFIX` replaced by `hooks_dir` plus a slash, wherever
    it appears inside a string value, at any depth. Keys and non-string values come back as they
    were, and the document passed in is not mutated."""
    replacement = str(hooks_dir) + "/"
    if isinstance(document, dict):
        return {key: rewrite_hooks_dir(value, hooks_dir) for key, value in document.items()}
    if isinstance(document, list):
        return [rewrite_hooks_dir(item, hooks_dir) for item in document]
    if isinstance(document, str):
        return document.replace(LIVE_HOOKS_PREFIX, replacement)
    return document
