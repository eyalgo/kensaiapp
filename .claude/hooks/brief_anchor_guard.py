#!/usr/bin/env python3
"""PreToolUse `Agent` hook — refuse a spawn whose brief cites something that is not there.

A delegated run gets one shot at understanding its task and cannot ask a follow-up. When the brief
points at the wrong place, the run works from the wrong place and the cost is already paid by the
time anyone finds out: `delegate_contract.md` § 3 makes a run mark each brief claim confirmed or
contradicted, and `15848b6` is that rule working — six citations wrong, reported after the run.

This guard moves the check in front of the spawn. **All six of those citations were in range** —
`brand.md:69-70` exists, it simply holds different text — so checking that a path exists and a range
fits catches none of them. What makes a citation checkable is the text it claims, quoted: the guard
opens the range, compares, and when it does not match it looks for the quote elsewhere in the file
and reports where it actually is, so the denial carries its own fix.

`Agent` is the tool name and the brief is in `tool_input["prompt"]` — measured over 2857 transcript
files under `~/.claude/projects/` (717 `Agent`, 0 `Task`), the method
`docs/proposals/archive/written-forward-fires/rationale.md` § 3d used for `Write`/`Edit`. A missing
key is read as absent, never raised on.

**Asserts only what it can prove.** Every satellite's `settings.json` runs this repo's
hooks, so a false positive here blocks work in every satellite as well as here. A brief with no citations passes
untouched; an ambiguous bare filename is skipped rather than guessed at; an unknown agent skips the
tool-grant check.

`Workflow`-spawned agents carry their briefs inside the script (no `prompt` key — measured) and a
`claude --bg` launch never touches this tool. Neither is covered, and neither is claimed.

Fails open on every error, matching `resolve_core.py`, `development-bash-approve.py` and
`written_forward_guard.py`: a guard that raises must not break a session.
"""

from __future__ import annotations

import glob
import json
import os
import re
import sys

__version__ = "1.2.1"

# `path:L12-L20`, `path:12-20`, `path:L12`, `path:12`. The path must carry an extension — a dot in
# its last segment — so ordinary prose ("Step 4:12-20") is not read as a citation.
_CITATION = re.compile(
    r"(?<![\w/])(?P<path>[\w.\-/]*[\w\-]+\.[A-Za-z0-9]+):L?(?P<start>\d+)(?:\s*[-–]\s*L?(?P<end>\d+))?"
)

# The anchor is a DOUBLE-quoted run. Backticks are ordinary prose punctuation in this fleet's
# writing (paths, flags), so only quotes are read as a claim about content.
_ANCHOR = re.compile(r"[\"“”]([^\"“”]{8,})[\"“”]")

_ANCHOR_WINDOW = 300  # characters after the citation, not crossing a blank line

_MCP_TOKEN = re.compile(r"mcp__[a-z0-9_-]+")

# The tier vocabulary the fleet actually writes, measured over 584 real briefs: `Opus`, `Fable`,
# `Sonnet`, `haiku`, `Opus 5 (1M context)`, `claude-opus-5[1m]`. Deliberately NOT a bare `claude-*`
# pattern — `claude-design` (an MCP server) and `claude-501` (a scratch path) both appear in real
# briefs, and matching those would wave a brief through as if it had named a tier.
_TIER = re.compile(r"\b(opus|sonnet|haiku|fable)\b", re.I)

# The one agent whose spawn is denied for naming no tier: its model is chosen per run, by the
# spawner.
_TIER_CHECKED_AGENT = "delegate"

_FIX = (
    "A brief's citation carries the text it claims, so it can be checked before the run starts "
    "(`agent-invoke` § Step 4). Quote the sentence you are pointing at:\n"
    '    path/to/file.md:L12-L20 "the sentence that is actually there"\n'
    "A `delegate` brief also names the tier it runs on: that slot has no skill, so its tier is "
    "chosen per run by its spawner and the brief is where the run learns it.\n"
    "Fix the problems above and spawn again."
)


def _project_dir() -> str:
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def _hook_host_root() -> str:
    """The repo this hook file sits in, through its real path: a satellite's `settings.json` runs
    this file from the host's `.claude/hooks/` by absolute path, so the real path lands in the host
    (or in the pin, under a pinned run)."""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))


def _resolve(path: str, root: str) -> str | None:
    """The file a citation names, or None when it cannot be resolved *provably*.

    A brief legitimately cites relative to a base this guard does not have — `product-srs/SKILL.md`
    lives under `skills/cto/.claude/skills/`, `evals/inputs/README.md` under a skill dir, and a cross-instance
    path under another repo entirely. Measured over 584 real briefs, that is what almost every
    unresolvable path turned out to be. So an unresolvable path is **skipped, never denied**: it is
    not provably wrong, and a dead path announces itself to the agent on the first Read anyway.
    What this guard exists for is the citation that resolves and points at the wrong text."""
    if os.path.isabs(path):
        return path if os.path.isfile(path) else None
    direct = os.path.join(root, path)
    if os.path.isfile(direct):
        return direct
    # Otherwise: usable only when exactly one file in the repo ends with the cited suffix.
    tail = "/" + path.lstrip("./")
    matches = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in (".git", "node_modules", "__pycache__")]
        for name in filenames:
            candidate = os.path.join(dirpath, name)
            if candidate.endswith(tail):
                matches.append(candidate)
                if len(matches) > 1:
                    return None  # ambiguous — not provable
    return matches[0] if matches else None


def _anchors_after(text: str, index: int) -> list[str]:
    """Every quoted run in the window after a citation. All of them, not the first: a brief may
    quote something unrelated on its way to the real anchor, and denying on the wrong one would
    block a citation that is sound."""
    window = text[index : index + _ANCHOR_WINDOW]
    paragraph = window.split("\n\n")[0]
    return [m.group(1) for m in _ANCHOR.finditer(paragraph)]


_EMPHASIS = str.maketrans("", "", "*`")


def _normalise(text: str) -> str:
    """Words, not formatting. This fleet's prose is dense with `**bold**` and `code` spans, and a
    brief quotes the *sentence* — `"the instance has no Shukuba of its own"` against a file holding
    `the instance has **no Shukuba of its own**`. Comparing raw would deny that, so the markers both
    sides use are dropped. `_` is left alone: here it is part of identifiers, not emphasis."""
    return " ".join(text.translate(_EMPHASIS).split())


def _fragments(anchor: str) -> list[str]:
    """An anchor split on its elisions. This fleet quotes with `…` and `...` cut through the
    middle — "**is** … **created**" — and an elided quote can never match as one substring, so
    each fragment is required instead, in order."""
    parts = [_normalise(p) for p in re.split(r"\u2026|\.\.\.", anchor)]
    return [p for p in parts if p]


def _holds(haystack: str, anchor: str) -> bool:
    cursor = 0
    for fragment in _fragments(anchor):
        found = haystack.find(fragment, cursor)
        if found < 0:
            return False
        cursor = found + len(fragment)
    return True


def _where_it_actually_is(lines: list[str], anchor: str) -> str | None:
    """The 1-indexed line range holding `anchor`, when it sits somewhere else in the file."""
    for i in range(len(lines)):
        for j in range(i, min(i + 6, len(lines))):
            if _holds(_normalise("\n".join(lines[i : j + 1])), anchor):
                return f"{i + 1}" if i == j else f"{i + 1}-{j + 1}"
    return None


def _citation_problems(prompt: str, root: str) -> list[str]:
    problems = []
    for match in _CITATION.finditer(prompt):
        path = match.group("path")
        start = int(match.group("start"))
        end = int(match.group("end") or start)
        shown = f"{path}:{start}" if start == end else f"{path}:{start}-{end}"

        resolved = _resolve(path, root)
        if resolved is None:
            continue  # unresolvable against a base we do not have — not provable, so not asserted

        try:
            lines = open(resolved, encoding="utf-8", errors="replace").read().splitlines()
        except OSError:
            continue
        if end > len(lines) or start < 1 or start > end:
            problems.append(f"{shown} — the file has {len(lines)} lines")
            continue

        anchors = _anchors_after(prompt, match.end())
        if not anchors:
            problems.append(f"{shown} — cited with no quoted text, so nothing here can be checked")
            continue

        cited = _normalise("\n".join(lines[start - 1 : end]))
        if any(_holds(cited, anchor) for anchor in anchors):
            continue

        anchor = anchors[0]
        real = _where_it_actually_is(lines, anchor)
        if real:
            problems.append(f'{shown} — "{anchor[:60]}" is at {path}:{real}, not {start}-{end}')
        else:
            problems.append(f'{shown} — "{anchor[:60]}" is not in this file')
    return problems


def _agent_file(project_root: str, hook_host_root: str, subagent_type: str) -> str | None:
    """The file of agent `subagent_type`, from the first root that holds it: the project's own
    `.claude/agents/<name>.md`, then its group `skills/<group>/.claude/agents/<name>.md`, then the
    same group file under the host this hook file sits in. A satellite holds no `skills/` of its
    own, and its `settings.json` runs this file from the host, so the host's groups answer for it. Of
    several groups holding the name, the last in name order wins, as in `pin.py` — compared part
    by part, as `pin.py` sorts its paths, so `a` comes before `a-b`; compared as whole strings,
    `a-b/…` would sort first and the guard would read a file the run never loads."""
    flat = os.path.join(project_root, ".claude", "agents", f"{subagent_type}.md")
    if os.path.isfile(flat):
        return flat
    agent_md = f"{glob.escape(subagent_type)}.md"
    for root in (project_root, hook_host_root):
        pattern = os.path.join(glob.escape(root), "skills", "*", ".claude", "agents", agent_md)
        grouped = sorted(glob.glob(pattern), key=lambda path: path.split(os.sep))
        if grouped:
            return grouped[-1]
    return None


def _frontmatter(
    project_root: str, hook_host_root: str, subagent_type: str
) -> dict[str, str] | None:
    """A spawned agent's frontmatter fields, or None when it has no file — a built-in agent
    (`Explore`, `Plan`, `general-purpose`) is not something this guard can check against."""
    path = _agent_file(project_root, hook_host_root, subagent_type)
    if path is None:
        return None
    try:
        lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    except OSError:
        return None
    if not lines or lines[0].strip() != "---":
        return None
    fields = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" in line and not line.startswith((" ", "\t", "-")):
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip()
    return fields


def _tier_problems(prompt: str, fields: dict[str, str] | None, model: str) -> list[str]:
    """`delegate` runs on whatever its spawner chose, and the brief is the only place it can learn
    which. Measured: it was spawned 58 times, every one passed a `model` in the call, and 37 never
    named it in the prompt — which is what both run reports mean by "The brief named no tier"
    (`delegate_contract.md:41`).

    Only `delegate` is checked. Its tier is per run by design — that slot has no skill, so no
    `intelligence/<provider>.md` holds it. Every other agent carries no `model:` line either, since
    a run's intelligence is its skill's (`skill_intelligence.md`); an agent spawned for a job with
    no skill runs on what the spawner passes or the provider's default, and that is the spawner's
    choice, not something this guard can require the brief to restate."""
    if fields is None or fields.get("name") != _TIER_CHECKED_AGENT:
        return []
    if _TIER.search(prompt):
        return []
    name = fields.get("name", "?")
    if model:
        return [
            f"no tier named — this run is spawned on `{model}`, and `{name}` pins no model, so the "
            "brief is the only place it can learn what it is running on"
        ]
    return [
        f"no tier named, and none passed — `{name}` pins no model, so this spawner has not chosen "
        "one; it has hidden the choice (`delegate_contract.md:39-41`)"
    ]


def _granted_tools(fields: dict[str, str] | None) -> str | None:
    return fields.get("tools") if fields else None


def _tool_problems(prompt: str, fields: dict[str, str] | None) -> list[str]:
    grant = _granted_tools(fields)
    if grant is None or grant.strip() == "*":
        return []
    named = sorted({token for token in _MCP_TOKEN.findall(prompt)})
    problems = []
    for token in named:
        if not any(token.startswith(g) or g.startswith(token) for g in _MCP_TOKEN.findall(grant)):
            problems.append(
                f"{token} — not granted to `{fields.get('name', '?')}`, whose tools are: {grant}"
            )
    return problems


def _emit_deny(problems: list[str]) -> None:
    reason = "This brief cannot be verified, so the run is not started:\n\n"
    reason += "\n".join(f"  {p}" for p in problems)
    reason += f"\n\n{_FIX}"
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))


def _handle(payload: dict) -> None:
    if payload.get("tool_name") != "Agent":
        return

    tool_input = payload.get("tool_input") or {}
    prompt = tool_input.get("prompt")
    if not prompt:
        return  # missing key → absent

    root = _project_dir()
    fields = _frontmatter(root, _hook_host_root(), tool_input.get("subagent_type") or "")
    problems = _citation_problems(prompt, root)
    problems += _tier_problems(prompt, fields, tool_input.get("model") or "")
    problems += _tool_problems(prompt, fields)
    if problems:
        _emit_deny(problems)


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:  # noqa: BLE001 — unparseable → defer
        return
    try:
        _handle(payload)
    except Exception:  # noqa: BLE001 — fail open by contract
        return


if __name__ == "__main__":
    main()
