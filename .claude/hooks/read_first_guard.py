#!/usr/bin/env python3
"""PreToolUse hook on every tool — refuse an agent run's acting calls until it has read the files
its agent file tells it to read first.

An agent file tells its run to read a list of files before it acts. Without this hook, nothing
makes a run do so, and it can edit, commit or spawn another run having opened none of them. This
hook refuses every call of an agent run that is not a read until the run has used `Read` on each
file on that list.

**What a run owes.** The list is the agent file's read instruction: the paragraph that tells the
run to `Read` files "in full", with the numbered list right after it when there is one. A `<CORE>/`
path is owed under the core this session resolved, by the resolution `resolve_core.py` performs.
The same file under a different core does not count. The overlay item is owed as the file named by
this agent's row in the loader map of `AGENTS.md`, whatever the agent file's own parenthetical
says. `AGENTS.md` itself is not owed, because the run only looks the overlay up there. A `§` after
a path narrows what to read, so the whole file is still owed. A listed file that is not on disk is
not owed, because a run cannot read it. An item the agent file makes conditional on the run's task
is not owed, because the hook sees the call and not the task. The agent files mark such an item
with "only when your task", with "the file your task names", or by placing the whole instruction
under a heading that opens "If your task".

**What is refused.** `Read`, `Grep` and `Glob` are reading calls. The hook never refuses a reading
call. Every other call is an acting call. A `Bash` call is acting even when its command is a `cat`,
because nothing here can show that a command only reads. An acting call is refused while any owed
file is unread in its `session_id`. The refusal names every owed file still unread. A file counts
as read once a `Read` call in the same `session_id` names it, with or without `offset` or `limit`.
A `Grep` or `Glob` that touches the file does not count. Once every owed file has been read, the
hook refuses nothing more in that session.

**Where reads are kept.** Each session's reads are kept under the platform temp directory, outside
every checkout. A file the hook wrote inside a checkout would leave that checkout dirty. The seal
refuses a dirty checkout (`core/tools/deliver_change.py`, "dirty checkout").

**Asserts only what it can prove.** Satellites run this repo's hooks
(`brief_anchor_guard.py`, "runs this repo's hooks"), so a false refusal here stops
work beyond this repo. A call with no agent is never refused. Neither is a call whose agent has no
agent file, such as the built-in `general-purpose`. Neither is a call whose agent file has no read
instruction the hook can find. The hook does not check that a `Read` covered the whole file. The
hook records every `Read` in a session, whatever agent made it. Whether a spawned subagent shares
its parent's `session_id` is not known here. The hook does not depend on the answer. Its
registration is in `.claude/settings.json`, so it covers only the runs that file configures.

Fails open on every error, matching `resolve_core.py`, `development-bash-approve.py`,
`written_forward_guard.py` and `brief_anchor_guard.py`: a guard that raises must not break a
session. On every call it does not refuse, it prints nothing. So it never approves a call that
another hook or the permission prompt would have stopped.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import tempfile
from collections.abc import Callable

__version__ = "1.0.1"

LEDGER_DIRNAME = "kensaiapp-read-first-guard"

_READING_TOOLS = frozenset({"Read", "Grep", "Glob"})

# The agent files' own words for an item, or a whole instruction, that depends on the run's task.
_CONDITIONAL_ITEM_MARKERS = ("only when your task", "the file your task names")
_CONDITIONAL_HEADING = "If your task"

_READ_IN_FULL = re.compile(r"\bRead\b.*\bin full\b", re.DOTALL)
_LIST_ITEM = re.compile(r"\s*\d+\.\s")
_HEADING = re.compile(r"#{1,6}\s+(.*)")
_BACKTICK_SPAN = re.compile(r"`([^`\n]+)`")
# A path token: a span with a `/` and a file extension, and no whitespace (so a command is not one).
_PATH_TOKEN = re.compile(r"[^\s/]*(?:/[^\s/]+)+\.[A-Za-z0-9]+")
_CORE_PREFIX = "<CORE>/"


class Files:
    """The filesystem as the guard reaches it."""

    def read_text(self, path: str) -> str:
        with open(path, encoding="utf-8", errors="replace") as handle:
            return handle.read()

    def is_file(self, path: str) -> bool:
        return os.path.isfile(path)

    def real_path(self, path: str) -> str:
        return os.path.realpath(path)


class Ledger:
    """The reads of each session: one append-only file per session under `directory`, named by a
    digest of the session id so the id never becomes a path component. A line is the real path
    of one file a `Read` named; an append in one write is how parallel reads avoid a lock."""

    def __init__(self, *, directory: str) -> None:
        self._directory = directory

    def _path(self, session_id: str) -> str:
        return os.path.join(self._directory, hashlib.sha256(session_id.encode()).hexdigest())

    def record(self, session_id: str, real_path: str) -> None:
        os.makedirs(self._directory, mode=0o700, exist_ok=True)
        descriptor = os.open(self._path(session_id), os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
        try:
            os.write(descriptor, f"{real_path}\n".encode())
        finally:
            os.close(descriptor)

    def reads(self, session_id: str) -> set[str] | None:
        """The real paths read in the session, or None when this ledger cannot be relied on: where
        reads cannot be recorded, an empty answer would refuse a run that did read."""
        try:
            os.makedirs(self._directory, mode=0o700, exist_ok=True)
        except OSError:
            return None
        if not os.access(self._directory, os.W_OK):
            return None
        try:
            with open(self._path(session_id), encoding="utf-8") as handle:
                return {line.rstrip("\n") for line in handle if line.strip()}
        except FileNotFoundError:
            return set()
        except OSError:
            return None


def _paragraphs(lines: list[str], start: int) -> list[tuple[int, int]]:
    """The `(first, last + 1)` line index of each blank-line-separated paragraph from `start`."""
    spans, first = [], None
    for index in range(start, len(lines) + 1):
        blank = index == len(lines) or not lines[index].strip()
        if not blank and first is None:
            first = index
        elif blank and first is not None:
            spans.append((first, index))
            first = None
    return spans


def _body_start(lines: list[str]) -> int:
    """The first line after the agent file's frontmatter, whose description is no instruction."""
    if lines and lines[0].strip() == "---":
        for index in range(1, len(lines)):
            if lines[index].strip() == "---":
                return index + 1
    return 0


def _list_items(lines: list[str], start: int) -> list[str]:
    """The numbered list that begins at `start` (after blank lines), each item carried on through
    its indented continuation lines. No list at `start` is an empty answer."""
    index = start
    while index < len(lines) and not lines[index].strip():
        index += 1
    items: list[list[str]] = []
    while index < len(lines):
        line = lines[index]
        if _LIST_ITEM.match(line):
            items.append([line])
        elif not line.strip():
            ahead = index
            while ahead < len(lines) and not lines[ahead].strip():
                ahead += 1
            if ahead >= len(lines) or not items or not (
                _LIST_ITEM.match(lines[ahead]) or lines[ahead][:1].isspace()
            ):
                break
            index = ahead
            continue
        elif items and line[:1].isspace():
            items[-1].append(line)
        else:
            break
        index += 1
    return [" ".join(" ".join(item).split()) for item in items]


def _read_instruction(agent_text: str) -> list[str]:
    """The chunks of an agent file's read instruction: the paragraph that tells the run to `Read`
    files "in full", then each item of the numbered list that follows it. An agent file with no
    such paragraph, or one under a heading that opens "If your task", gives none."""
    lines = agent_text.splitlines()
    for first, end in _paragraphs(lines, _body_start(lines)):
        paragraph = " ".join(" ".join(lines[first:end]).split())
        if not _READ_IN_FULL.search(paragraph):
            continue
        for above in range(first - 1, -1, -1):
            heading = _HEADING.fullmatch(lines[above].strip())
            if heading:
                if heading.group(1).startswith(_CONDITIONAL_HEADING):
                    return []
                break
        return [paragraph, *_list_items(lines, end)]
    return []


def _overlay_path(agents_md: str, agent: str) -> str | None:
    """The file `agent`'s row in the loader map of `AGENTS.md` names, or None."""
    row = re.compile(rf"- `{re.escape(agent)}:`\s*→\s*`?([^\s`]+)`?")
    in_map = False
    for line in agents_md.splitlines():
        if line.startswith("## "):
            in_map = line[3:].strip() == "Loader map"
        elif in_map:
            match = row.fullmatch(line.strip())
            if match:
                return match.group(1)
    return None


def _path_tokens(chunk: str) -> list[str]:
    return [span for span in _BACKTICK_SPAN.findall(chunk) if _PATH_TOKEN.fullmatch(span)]


def _refusal(*, tool: str, agent: str, agent_file: str, unread: list[str]) -> str:
    owed = "\n".join(f"  {path}" for path in unread)
    return (
        f"This `{tool}` call is refused.\n"
        f"`{agent_file}` tells a `{agent}` run to read the files listed below before it acts. "
        "No `Read` call in this session has named them:\n"
        "\n"
        f"{owed}\n"
        "\n"
        "Read each file above with the `Read` tool, then make this call again. "
        "A `Read` with `offset` or `limit` counts. A `Grep` or `Glob` of a file does not count.\n"
        "This check never refuses `Read`, `Grep` or `Glob`. "
        "It refuses every other call until each file above has been read in this session. "
        "After that, it refuses no call in this session."
    )


class ReadFirstGuard:
    """Decides one `PreToolUse` call. Everything it reaches the world through is handed to it."""

    def __init__(self, *, project_dir: str, files: Files, ledger: Ledger,
                 agent_file_of: Callable[[str], str | None],
                 core_dir_of: Callable[[], str]) -> None:
        self._project_dir = project_dir
        self._files = files
        self._ledger = ledger
        self._agent_file_of = agent_file_of
        self._core_dir_of = core_dir_of

    def refusal(self, payload: dict) -> str | None:
        """The message to refuse this call with, or None to say nothing."""
        tool = payload.get("tool_name")
        tool_input = payload.get("tool_input")
        session_id = payload.get("session_id")
        if not isinstance(tool, str) or not isinstance(session_id, str) or not session_id:
            return None
        if tool == "Read":
            self._record_read(session_id, tool_input)
            return None
        if tool in _READING_TOOLS:
            return None
        agent = payload.get("agent_type")
        if not isinstance(agent, str) or not agent:
            return None
        agent_file = self._agent_file_of(agent)
        if agent_file is None:
            return None
        owed = self._owed(agent, agent_file)
        if not owed:
            return None
        read = self._ledger.reads(session_id)
        if read is None:
            return None
        unread = [shown for shown, real in owed if real not in read]
        if not unread:
            return None
        return _refusal(tool=tool, agent=agent, agent_file=agent_file, unread=unread)

    def _record_read(self, session_id: str, tool_input: object) -> None:
        file_path = tool_input.get("file_path") if isinstance(tool_input, dict) else None
        if not isinstance(file_path, str) or not file_path:
            return
        try:
            named = os.path.join(self._project_dir, file_path)
            self._ledger.record(session_id, self._files.real_path(named))
        except OSError:
            return

    def _owed(self, agent: str, agent_file: str) -> list[tuple[str, str]]:
        """The owed files as `(path to name in a Read, real path)`, in the order the agent file
        first lists them, none twice. Raises when the agent file or `AGENTS.md` is unreadable."""
        owed: list[tuple[str, str]] = []
        seen: set[str] = set()
        for chunk in _read_instruction(self._files.read_text(agent_file)):
            if any(marker in chunk for marker in _CONDITIONAL_ITEM_MARKERS):
                continue
            if "Loader map" in chunk:
                named = self._overlay(agent)
                tokens = [] if named is None else [named]
            else:
                tokens = _path_tokens(chunk)
            for token in tokens:
                shown = self._absolute(token)
                if not self._files.is_file(shown):
                    continue
                real = self._files.real_path(shown)
                if real not in seen:
                    seen.add(real)
                    owed.append((shown, real))
        return owed

    def _overlay(self, agent: str) -> str | None:
        try:
            agents_md = self._files.read_text(os.path.join(self._project_dir, "AGENTS.md"))
        except FileNotFoundError:
            return None  # an instance with no AGENTS.md has no overlay to owe
        return _overlay_path(agents_md, agent)

    def _absolute(self, token: str) -> str:
        if token.startswith(_CORE_PREFIX):
            return os.path.normpath(os.path.join(self._core_dir_of(), token[len(_CORE_PREFIX):]))
        return os.path.normpath(os.path.join(self._project_dir, token))


def _emit_deny(reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))


# --- the composition root: the only place a concrete collaborator is constructed ---------------


def _build_guard(environ: dict[str, str]) -> ReadFirstGuard:
    hooks_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, hooks_dir)
    import brief_anchor_guard
    import resolve_core

    project_dir = os.path.abspath(environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    host_root = brief_anchor_guard._hook_host_root()
    return ReadFirstGuard(
        project_dir=project_dir,
        files=Files(),
        ledger=Ledger(directory=os.path.join(tempfile.gettempdir(), LEDGER_DIRNAME)),
        agent_file_of=lambda name: brief_anchor_guard._agent_file(project_dir, host_root, name),
        core_dir_of=lambda: resolve_core._resolve(project_dir),
    )


def main() -> int:
    """Best-effort by contract: whatever goes wrong, the call is left alone, nothing is printed,
    and the exit status is 0. A guard that raised would break a session it was asked to protect."""
    try:
        payload = json.load(sys.stdin)
        if isinstance(payload, dict):
            reason = _build_guard(dict(os.environ)).refusal(payload)
            if reason is not None:
                _emit_deny(reason)
    except Exception:  # noqa: BLE001 — fail open by contract
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
