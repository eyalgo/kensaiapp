"""completion_shim.py — the one owner of the completion-hook shim every engine writes.

WHY THIS EXISTS

The watcher runs a completion hook as `subprocess.run([hook, outcome], capture_output=True,
timeout=60)` (`watch_agent.py`'s `run_on_complete_hook`, which `watch_process.py` calls). An engine
that `exec`s itself from the hook puts the whole advance — which may launch four or five audits — under that
bound, and an engine still writing to the captured pipe holds `subprocess.run` open until it closes.

So the contract, stated here once and held by every engine through this module: a completion hook
hands off and returns at once. The shim starts the engine detached, with every descriptor
redirected, and the engine's output goes to the engine's log, never the watcher's pipe.

This module renders the shim and writes it through the `files` port it is given. It constructs no
collaborator and imports no engine, so `chain.py`, `chain_development.py` and `build_idea.py` can
each import it without a cycle.
"""

from __future__ import annotations

import json
import os
import shlex

__version__ = "1.1.0"

_SHIM_TEMPLATE = """#!/usr/bin/env bash
set -euo pipefail
nohup python3 {words} "$1" </dev/null >>{log} 2>&1 &
"""


class ShimFiles:
    """The three disk operations `write_shim` uses. A plain class, as the other ports are: a fake
    satisfies it by having these methods."""

    def make_dirs(self, path: str) -> None:
        raise NotImplementedError

    def write_text(self, path: str, text: str) -> None:
        raise NotImplementedError

    def make_executable(self, path: str) -> None:
        raise NotImplementedError


def shim_text(engine_path: str, advance_args: tuple[str, ...], log_path: str) -> str:
    """The shim's text: the engine started detached with `advance_args`, then the hook's outcome
    (`"$1"`) as its last argument, its output appended to `log_path`. Every word is quoted."""
    words = " ".join(shlex.quote(word) for word in (engine_path, *advance_args))
    return _SHIM_TEMPLATE.format(words=words, log=shlex.quote(log_path))


def write_shim(files: ShimFiles, shim_path: str, *, engine_path: str,
               advance_args: tuple[str, ...], log_path: str) -> str:
    """Write the shim at `shim_path`, executable, and return that path."""
    files.make_dirs(os.path.dirname(os.path.abspath(shim_path)))
    files.write_text(shim_path, shim_text(engine_path, advance_args, log_path))
    files.make_executable(shim_path)
    return shim_path


# ---- the final-message receipt ---------------------------------------------------------------
#
# An optional sidecar next to the shim. A watcher that was told where to put it publishes the
# provider's final message there before it runs the completion hook, so an engine the hook starts
# can read what the run said. The file carries the message and nothing else: whether the message
# means success is the engine's reading, not the transport's.

RESULT_FILE_VARIABLE = "DETACHED_RUN_RESULT_FILE"
_MESSAGE_FIELD = "last_message"
_SIBLING_SUFFIX = ".tmp"


class DiskReceiptFiles:
    """The disk implementation of the receipt's port: the writer's `write_text` and
    `replace_file`, and the reader's `read_text`."""

    def write_text(self, path: str, text: str) -> None:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)

    def replace_file(self, source: str, destination: str) -> None:
        os.replace(source, destination)

    def read_text(self, path: str) -> str:
        with open(path, encoding="utf-8") as handle:
            return handle.read()


def write_result(files: DiskReceiptFiles, destination: str | None,
                 last_message: str | None) -> None:
    """Publish `last_message` (a string, or None for no message) at `destination`, through a
    sibling file that is then replaced over it, so the destination never holds partial JSON. No
    destination writes nothing."""
    if not destination:
        return
    sibling = destination + _SIBLING_SUFFIX
    files.write_text(sibling, json.dumps({_MESSAGE_FIELD: last_message}))
    files.replace_file(sibling, destination)


def read_result(files: DiskReceiptFiles, destination: str | None) -> str | None:
    """The message a receipt at `destination` carries, or None when there is no destination, no
    file, or a file that is unreadable, not JSON, or not the receipt's shape."""
    if not destination:
        return None
    try:
        text = files.read_text(destination)
    except (OSError, UnicodeError):
        return None
    if text is None:    # the queue's own port answers None for a file it cannot read
        return None
    try:
        payload = json.loads(text)
    except ValueError:
        return None
    if not isinstance(payload, dict):
        return None
    message = payload.get(_MESSAGE_FIELD)
    return message if isinstance(message, str) else None
