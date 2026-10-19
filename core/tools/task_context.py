#!/usr/bin/env python3
"""Render Kensaiapp's task routing and standing rules as provider-neutral context.

``task_map.md`` owns every task-to-doctrine route.  This module reads that one
table and renders the two context blocks consumed by both provider surfaces:
the complete routing index and the smaller set of rules whose triggers are
noticed mid-work.  Provider hooks and launch adapters add their own transport
envelope; none redefines what a row means or which rows are standing.

The standing block ends with one section of doctrine carried whole: § The rules
of ``governance/talking_to_the_owner.md``.  It binds a session's first reply,
which is written before any named file would be opened, so a name would come
too late.  It is read from that file every time the context is rendered, so it
is the file's own text, not a copy.

The caller supplies the resolved core root.  Resolving ``<CORE>`` belongs to
the instance/bootstrap layer, while this module is a pure reader of the core
it is handed.  Missing or malformed input is fail-empty so a context aid never
prevents an agent run from starting.
"""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

__version__ = "2.2.0"

TASK_MAP = Path("doctrine") / "task_map.md"
TASK_MAP_SENTINEL = "KENSAIAPP_TASK_MAP"
STANDING_RULES_SENTINEL = "KENSAIAPP_STANDING_RULES"
OWNER_REPLY = Path("doctrine") / "governance" / "talking_to_the_owner.md"
OWNER_REPLY_SENTINEL = "KENSAIAPP_OWNER_REPLY"

_HEADER = "When you're about to"
_RULES_HEADING = "## The rules"
_UNPROMPTED = "unprompted"
_EM_DASH = "—"

_CODEX_RUNTIME_SURFACE = "Execution surface: Codex."

_ROUTING_PREAMBLE = (
    f"Task→doctrine map ({TASK_MAP_SENTINEL}): before you act on a task, the doctrine that "
    "governs it is indexed at `<CORE>/doctrine/task_map.md`, which is the authority. Every "
    "route it carries is below — find what you are about to do and read the doctrine named "
    "beside it:"
)

_STANDING_PREAMBLE = (
    f"Standing rules ({STANDING_RULES_SENTINEL}): you are already bound by these — now, before "
    "reading them, and without being asked. Their trigger is something you notice mid-work "
    "rather than set out to do, so nothing will prompt you to look them up, and not having "
    "opened a rule's doctrine does not suspend it. When one of these happens, open the file "
    "named beside it and follow it: reading tells you what the rule requires, it is not what "
    "puts it in force. `<CORE>/doctrine/task_map.md` marks which routes these are and each "
    "doctrine owns what its rule says:"
)

_OWNER_REPLY_PREAMBLE = (
    f"How to reply to the owner ({OWNER_REPLY_SENTINEL}): these rules bind every reply you write "
    "that the owner reads, from your first one. They are § The rules of "
    "`<CORE>/doctrine/governance/talking_to_the_owner.md`, word for word:"
)


class Route(NamedTuple):
    """One task-map row and its governing doctrine."""

    trigger: str
    consult: str
    layer: str
    fires: str

    @property
    def short(self) -> str:
        """The task phrase before the row's explanatory em dash."""
        return self.trigger.split(_EM_DASH)[0].strip()


def map_path(core_root: Path) -> Path:
    """Return the task map under an already-resolved core root."""
    return core_root / TASK_MAP


def _cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def routes(path: Path) -> list[Route]:
    """Read every body row, or return an empty list when no table is readable."""
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []

    result: list[Route] = []
    for line in lines:
        if not line.startswith("|"):
            continue
        if _HEADER in line or set(line) <= set("|- "):
            continue
        cells = _cells(line)
        if len(cells) < 3:
            continue
        result.append(Route(
            trigger=cells[0],
            consult=cells[1].strip("`"),
            layer=cells[2],
            fires=cells[3] if len(cells) > 3 else "",
        ))
    return result


def unprompted(rows: list[Route]) -> list[Route]:
    """Return the rows marked as binding before a session thinks to consult them."""
    return [route for route in rows if route.fires == _UNPROMPTED]


def _render(preamble: str, selected: list[Route]) -> str:
    if not selected:
        return ""
    lines = [f"  {route.short} → {route.consult}" for route in selected]
    return preamble + "\n" + "\n".join(lines)


def routing_context(core_root: Path) -> str:
    """Render every task route from the resolved core's authoritative map."""
    return _render(_ROUTING_PREAMBLE, routes(map_path(core_root)))


def owner_reply_rules(core_root: Path) -> str:
    """Return § The rules of the owner-reply doctrine as written, or "" when it is unreadable.

    The section is carried whole rather than named, because it binds every reply and a pointer
    would be opened only after the first reply was already written."""
    try:
        lines = (core_root / OWNER_REPLY).read_text(
            encoding="utf-8-sig", errors="replace").splitlines()
    except OSError:
        return ""
    headings = [line.rstrip() for line in lines]
    try:
        start = headings.index(_RULES_HEADING) + 1
    except ValueError:
        return ""
    section: list[str] = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        section.append(line)
    return "\n".join(section).strip()


def owner_reply_context(core_root: Path) -> str:
    """Render the owner-reply rules under their preamble, or nothing when there are none."""
    rules = owner_reply_rules(core_root)
    return f"{_OWNER_REPLY_PREAMBLE}\n{rules}" if rules else ""


def standing_rules_context(core_root: Path) -> str:
    """Render the map rows marked ``unprompted``, followed by the owner-reply rules."""
    blocks = (
        _render(_STANDING_PREAMBLE, unprompted(routes(map_path(core_root)))),
        owner_reply_context(core_root),
    )
    return "\n\n".join(block for block in blocks if block)


def _effort_sentence(reasoning_effort: str) -> str:
    """Tell a launched run which resolved level to hand the commit builder. It carries no
    leading separator: each bootstrap joins it to its own text."""
    return (
        f'Pass `--reasoning-effort "{reasoning_effort}"` to the builder; '
        "the launch already resolved this value."
    )


_GEMINI_RUNTIME_SURFACE = "Execution surface: Gemini."


def gemini_bootstrap(
    core_root: Path,
    prompt: str,
    model: str | None,
    reasoning_effort: str | None = None,
) -> str:
    """Prepend the shared Kensaiapp context to one Gemini task prompt."""
    # commit_format.md § Filling the model: the assigned model, or the provider when none was.
    identity = model if model is not None else "Gemini"
    attribution = f'`--surface Gemini` and `--co-authored-by "{identity} <noreply@google.com>"`'
    runtime_identity = (
        f"{_GEMINI_RUNTIME_SURFACE} For commit attribution, use {attribution}; "
        "never inherit another provider's identity from an example."
    )
    if reasoning_effort is not None:
        runtime_identity += f" {_effort_sentence(reasoning_effort)}"
    blocks = [
        f"Kensaiapp core resolution: `<CORE>` = `{core_root}`.",
        runtime_identity,
        routing_context(core_root),
        standing_rules_context(core_root),
        "CRITICAL: Do not use view_file or read_file to read agent instructions, rules, or core "
        "context files (like AGENTS.md, kensaiapp.md or skills/*/.claude/agents/*.md). Their "
        "contents are already provided to you.",
        prompt,
    ]
    return " ".join(" ".join(block.split()) for block in blocks if block)


def codex_bootstrap(
    core_root: Path,
    prompt: str,
    model: str | None,
    reasoning_effort: str | None = None,
) -> str:
    """Prepend the shared Kensaiapp context to one Codex task prompt."""
    # commit_format.md § Filling the model: the assigned model, or the provider when none was.
    identity = model if model is not None else "Codex"
    attribution = f'`--surface Codex` and `--co-authored-by "{identity} <noreply@openai.com>"`'
    runtime_identity = (
        f"{_CODEX_RUNTIME_SURFACE} For commit attribution, use {attribution}; "
        "never inherit another provider's identity from an example."
    )
    if reasoning_effort is not None:
        runtime_identity += f" {_effort_sentence(reasoning_effort)}"
    blocks = [
        f"Kensaiapp core resolution: `<CORE>` = `{core_root}`.",
        runtime_identity,
        routing_context(core_root),
        standing_rules_context(core_root),
        prompt,
    ]
    # Keep the command renderable as one shell-parseable dry-run line.  The source blocks use
    # line breaks for human-facing hook output; Codex receives the same words with whitespace
    # collapsed, so an argv printer never emits one quoted argument across several lines.
    return " ".join(" ".join(block.split()) for block in blocks if block)


def claude_bootstrap(prompt: str, reasoning_effort: str | None) -> str:
    """Append the launch's resolved effort to one Claude task prompt.

    With no level the prompt comes back unchanged. With one, the result is the prompt, one
    space, and the effort sentence. The prompt is kept byte-for-byte — unlike the Codex and
    Gemini bootstraps, nothing here collapses whitespace — and nothing else is added: no core
    resolution, no surface or identity instruction, no routing context. A Claude run already
    has those from its own session.
    """
    if reasoning_effort is None:
        return prompt
    return f"{prompt} {_effort_sentence(reasoning_effort)}"
