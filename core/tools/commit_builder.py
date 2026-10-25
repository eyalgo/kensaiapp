#!/usr/bin/env python3
"""commit_builder.py — the one executable that constructs every commit and merge.

Single place a caller (a skill, a workflow subagent, an interactive session)
hands a subject + body and its own identity, and gets back a commit or merge
with every required trailer in canonical order, with the git op already run.
One code path serves both `git commit` and `git merge --no-ff` — the merge
path additionally emits `Merge-Authorized:` in place of the directional
trailer and `Role:`.

Canonical formats this executable constructs. The commit format's prose
single source stays `core/doctrine/governance/commit_format.md` (this module
is its executable source, not a second definition). The merge format has no
separate prose file — it lives here, in this module, as its single source
(the former `.claude/skills/_shared/merge-format.md` retired 2026-07-08):

  commit:
    <subject>

    <body>

    Shukuba: <...>  |  Michi: <...>   <- topmost, exactly one, caller-supplied
    Role: <derived from --actor via AGENT_ROLE>
    Surface: <...>
    Co-Authored-By: <...>  <- optional; omitted when no model authored the
                             commit (a deterministic launcher). See below.
    Claude-Session: <the session URL, from --claude-session; optional>
    Skill-Version: <supplied by explicit --skill only; optional, omitted
                     when no --skill is passed or the named skill's source
                     can't be resolved>
    Prompt-Version: <the same, for --prompt: which prompt a session read to
                     produce this output. Independent of Skill-Version: —
                     both may appear, either may appear alone>
    Workflow-Version: <the same, for --workflow: which saved Workflow script
                     drove the run. The third independent fact; any subset of
                     the three may appear>

  merge (replaces Role: / the directional trailer with Merge-Authorized:):
    merge: <branch> → <target-branch> — <description>

    -> <each branch commit, one per line>

    Merge-Authorized: <...>
    Surface: <...>
    Co-Authored-By: <...>
    Claude-Session: <the session URL, from --claude-session; optional>

  advance (a branch taking a named ref's advance — a `--no-ff` merge whose
  authorizer comes from any commit actor, since it lands nothing on `main`;
  same Role:-less shape as merge, and carries no body):
    merge: <ref> → <branch> — take <ref>'s advance

    Merge-Authorized: <...> — takes <ref> at <40-hex sha>
    Surface: <...>
    Co-Authored-By: <...>  <- optional, as above
    Claude-Session: <the session URL, from --claude-session; optional>

`AGENT_ROLE` is this module's sole home for the actor -> Role mapping (the
`enforce_commit_role.py` PreToolUse hook that used to keep a mirror of it was
retired 2026-07-07; this module is the only copy now). Two trailers are
actor-derived, each from its own map:
`Role:` on the commit path (via `AGENT_ROLE`) and the `Merge-Authorized:`
authorizer token on the merge path (via `MERGE_AUTHORIZER`) — same shape,
different table. The `advance` path emits `Merge-Authorized:` too, but derives
it from `AGENT_ROLE` directly rather than from `MERGE_AUTHORIZER`: an advance
lands nothing on `main`, so any actor that may author a commit may authorize
one — `MERGE_AUTHORIZER`'s narrower set governs `merge` alone. Every other
trailer's content is supplied by the caller,
exactly as subject/body are; the caller resolves the directional trailer, the
merge context, the `Surface:` value, and the `Co-Authored-By:` model string,
and this module places them in order.

`Co-Authored-By:` is optional on both ops. Every caller until 2026-09-03 was
an AI session with a real model to name, so the flag was required; the first
committer that runs no model at all — `core/launchers/product-skeleton/`, a
deterministic copier the owner invokes — has none, and naming one would put a
model's signature on bytes it never saw. Omitted, no line is written, and the
absence positively means no model authored the commit. Doctrine already
allowed it: `commit_format.md` makes `Role:` and `Surface:` the enforced set
and `verify_commit_msg.py` presence-checks exactly those two, so only this
CLI insisted.

The staged-set guard: before running the `commit` op, the builder reads the
staged set (`git diff --cached --name-only --no-renames`, so a staged rename
shows as its two halves) and refuses — making no commit — unless every
staged path is covered by `--add` ∪ `--rm` ∪ `--staged` (the third flag is a
declaration only: "this was staged outside the builder, deliberately", for
a caller that pre-staged via `git mv`). The guard catches every entry a
concurrent session staged before this call ran; it does **not** close the
window between the guard's own read and the `git commit` a few lines later
(milliseconds) — a stage that lands inside that window is still swept, and
no plumbing in this module attempts to close it (`git commit-tree` would
bypass the `commit-msg` hook that verifies every trailer). `--take-index`
waives the guard entirely for one call — for an interactive session that
staged by hand and cannot usefully enumerate paths — and restores the
pre-guard whole-index behaviour for that call only.

A third, non-required trailer — `Skill-Version:` — records provenance: which
skill produced this commit's output, at what declared semantic version and
exact source SHA (`<name>@<semver> <sha>`, added 2026-07-09). It is stamped
**iff** the caller passes `--skill <name>`, naming the producing skill outright
(explicit-only, 2026-07-24). The earlier `--actor` → `ACTOR_SKILL` derivation
was retired: it inferred *what skill produced the output* from *who committed*,
so any role or general-purpose session that committed via `--actor` without
running a skill got a skill falsely stamped. Absence of the line now positively
means **no producing skill authored this commit** — a role or general-purpose
session hand-authoring, a `pm` seal/bookkeeping commit, every merge — never
"unknown." The impure `resolve_skill_version` helper turns the explicit name
into the value and it is placed last in the trailer block — on the `commit`
path only. A merge is authored by the merge authorizer, not a producing skill,
so it never carries the line. Its presence or absence never blocks a commit;
the required set `verify_commit_msg.py` enforces is unchanged.

`Prompt-Version:` is its sibling, and answers the case `Skill-Version:`
structurally cannot (added 2026-08-20). A **prompt** read straight by a
session has no `SKILL.md` to read a version out of, so its output committed
with no provenance line at all — making a run that followed a versioned lens
byte-identical to a hand-authored commit. `--prompt <name>` names the prompt
outright and stamps `Prompt-Version: <name>@<semver> <sha>`, resolved from
`core/prompts/<name>.md`, or — for `<skill>/<prompt>` — from that skill's own
`prompts/<prompt>.md` — a **name**, never a path, because `--repo` is
frequently not the instance and there is exactly one `core/prompts/` (a
satellite carries no `core/` at all and resolves `<CORE>` to this instance's).
The two trailers are independent facts — which skill ran, which prompt ran —
so there is no mutually-exclusive group: a thin skill over a fat prompt
records both, in that order. Everything else is `Skill-Version:`'s contract
verbatim: explicit-only, non-required, best-effort, omitted rather than
fabricated, and never on a merge.

`Workflow-Version:` is the third of the set, and closes the last silent case
(added 2026-08-25). A **workflow** can hold the load-bearing half of a
capability — the SDD conversation's turn loop, closure rule and report
derivation all live in `.claude/workflows/sdd-conversation.js` — so a run could
commit a document while naming the skill and the prompt and staying silent
about the component that actually drove it. `--workflow <name>` stamps
`Workflow-Version: <name>@<semver> <sha>` from `.claude/workflows/<name>.js`.

Its **read** is the one thing that does not copy from its two siblings. A skill
and a prompt both declare their version in frontmatter; a workflow has none,
and `versioning.md` puts its `// Version: x.y.z` marker **below** the `meta`
block rather than at the head of the file — because the workflow tests execute
the real bytes through an anchored `source.replace(/^export const meta/, …)`
that anything above the block would turn into a no-op. So this resolver reads a
comment, not frontmatter. Everything else is the siblings' contract verbatim:
a bare name (never a path), resolved against the **instance** repo and never
`--repo`, explicit-only, non-required, best-effort, omitted rather than
fabricated, and never on a merge.

Stdlib-only imports.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from collections.abc import Callable, Sequence
from enum import Enum, auto
from pathlib import Path
from typing import Literal

import gate_suite
import pin
import record_declarations
import skill_path

__version__ = "1.27.1"

Op = Literal["commit", "merge", "advance"]

# The levels `--reasoning-effort` admits on `commit`, `merge` and `advance`, in the order
# `commit_format.md` § `Reasoning-Effort:` trailer names them. Stated here rather than imported
# from `agent_run.Effort`, which holds the same five: importing it would make the commit builder
# depend on the run launcher. `test_commit_builder.py` holds the two together instead, and holds
# this tuple to the doctrine's own Shape line.
REASONING_EFFORT_LEVELS = ("low", "medium", "high", "xhigh", "max")

# Actor identity (the caller's own `agent_type` — a workflow subagent's
# identity, e.g. "developer", "tech-lead") -> doctrine Role value. This is the
# sole home of the mapping (the `enforce_commit_role.py` hook that once
# mirrored it was retired 2026-07-07). Add a row here (and to
# `commit_format.md`'s Role list) to admit a new actor.
AGENT_ROLE = {
    "cpo": "CPO",
    "cto": "CTO",
    "cdo": "CDO",
    "product-owner": "Product Owner",
    "architect": "Architect",
    "tech-lead": "Tech Lead",
    "developer": "Developer",
    "senior-engineer": "Senior Engineer",
    "content-manager": "Content Manager",
    "content-editor": "Content Editor",
    "pm": "PM",
    "principal-pm": "Principal PM",
    "principal-architect": "Principal Architect",
    "scrum-master": "Scrum Master",
    "kensaiapp-auditor": "KensaiApp Auditor",
    "kaizen-fix-author": "Kaizen Fix Author",
    "kaizen-fixer": "Kaizen Fixer",
}

# Merge actor -> `Merge-Authorized:` authorizer token.
#
# THIS TABLE IS AN ALLOWLIST, NOT A DICTIONARY, AND ITS MEANING IS IN WHAT IT
# OMITS. Every value here is spelled identically in AGENT_ROLE, so as a
# translation table it would be pure duplication and someone would rightly
# delete it. What it does that AGENT_ROLE cannot is be **narrower**: AGENT_ROLE
# is everyone who may author a commit; this is the subset who may authorize a
# merge to main, which is the highest-consequence op in the repo.
#
# The omission that carries the policy: `developer` is in AGENT_ROLE and is NOT
# here, deliberately. A developer does not authorize a merge **to `main`** —
# the `senior-engineer` runs `development-code-integrity` over it first and
# merges on the strength of that pass. That separation is the whole point of
# the worker/reviewer split (the Developer implements, the Senior Engineer
# reviews and merges), and this table is where it is written down in executable form.
# `test_commit_builder.py` pins the exclusion, because an intentional absence
# has no line to read and is otherwise indistinguishable from an oversight.
#
# A developer DOES authorize its own branch's `advance` — a merge that lands
# nothing on `main` and is the branch's own housekeeping. That path derives
# its authorizer from AGENT_ROLE directly, never from this table, so this
# stays the to-`main` allowlist alone.
#
# What this is NOT: enforcement. The actor is self-declared, so a `developer`
# passing `--actor pm` would produce `Merge-Authorized: PM` and nothing here
# would catch it. The table buys a stated policy and deliberate friction — you
# must edit it to add an authorizer — not a security control. Do not reason
# about it as a gate.
#
# Adding an ACTOR authorizer is a data change, not a new code path. An
# INTERACTIVE, human-gated merge does not belong here at all — it has no actor
# to key on; see INTERACTIVE_MERGE_AUTHORIZERS below.
MERGE_AUTHORIZER = {
    "pm": "PM",                            # the automated seal (tobiishi-seal)
    "senior-engineer": "Senior Engineer",  # merges after code-integrity passes on a branch
}

# The authorizers an INTERACTIVE caller may claim verbatim, with no subagent identity to derive from.
#
# This mirrors the commit path's `--actor` XOR `--role` split, which the merge path lacked: a merge
# the owner directed had no way to say so, and the only honest-looking option was to borrow an actor
# that did not do the authorizing. `Product` is what doctrine already named for this case —
# commit_format.md: "a future interactive, human-gated merge would derive Merge-Authorized: Product".
#
# It is a SET, not a free-form string, and that is the point. `--role` on the commit path is verbatim
# and unvalidated, which is fine there; a merge to main is the highest-consequence op in the repo, and
# MERGE_AUTHORIZER's whole value is being a closed, deliberately narrow list. An unchecked `--authorizer`
# would dissolve that in one flag — any caller could write anything and the allowlist would mean nothing.
# Two closed sets, one per identity kind, is what keeps the property true on both paths.
#
# Why `Product` cannot simply be a MERGE_AUTHORIZER row: that table is keyed by **actor** (a subagent
# `agent_type`), and its rows must be spelled as that actor's own `Role:` — a property
# test_commit_builder.py pins as a strict subset of AGENT_ROLE. `Product` is a Role value with no
# corresponding subagent; there is no `product` agent to be the actor. It belongs on the interactive
# axis, not the actor axis.
INTERACTIVE_MERGE_AUTHORIZERS = {
    "Product",   # the owner directed this merge — a human gate, not an automated one
}

# Matches the `  version: "X.Y.Z"` line inside a `---` frontmatter block —
# a SKILL.md's (for `Skill-Version:`) or a doctrine file's (for `--bump`)
# block — a plain line scan, stdlib only, no YAML dependency.
_VERSION_LINE = re.compile(r'^\s*version:\s*"([^"]+)"\s*$')
# A saved Workflow script's marker: a `// Version: x.y.z` comment, which
# `versioning.md` requires to sit BELOW the `meta` block. Anchored to a whole
# line so a mention inside prose or a string cannot match.
_WORKFLOW_VERSION_COMMENT = re.compile(r"^\s*//\s*Version:\s*(\d+\.\d+\.\d+)\s*$")
# Two more of the marker forms `versioning.md` § Where the test lands names.
# Both are anchored at column 0, which is where every
# one of them sits on disk: an indented lookalike is a mention, not a marker.
# The shell form alone allows trailing text, because 20 of the 22 files
# carrying it write `# Version: x.y.z — what that version changed`.
_PY_VERSION_LINE = re.compile(r'^__version__ = "(\d+\.\d+\.\d+)"\s*$')
_SHELL_VERSION_COMMENT = re.compile(r"^# Version: (\d+\.\d+\.\d+)(?:\s|$)")
# A Claude Code plugin's marker: the manifest's own top-level `"version"`,
# read only in a file named `plugin.json` — any other JSON file's `"version"`
# is that format's business, not a marker `versioning.md` names.
_PLUGIN_MANIFEST_NAME = "plugin.json"
_SEMVER = re.compile(r"\d+\.\d+\.\d+")

# The directional trailer's own grammar (a --directional caller supplies as
# one line): a form name anchored at the line's start (leading whitespace
# tolerated), a colon, and the first whitespace-delimited token after it —
# `commit_format.md` § Directional trailer names the three legal forms.
_DIRECTIONAL_FORM_RE = re.compile(r"^\s*(Shukuba|Agari|Michi):\s*(\S*)")

# Tokens that are readings, not referents — `commit_format.md`'s `progress:`
# (Shukuba/Agari) and `serves:`/`aside:` (Michi/Shukuba/Agari) — compared
# lowercased so `Progress`/`PROGRESS` are caught the same way. Named at
# module level so a test can pin the set directly.
_DIRECTIONAL_SKIP_TOKENS = frozenset({"progress", "aside", "serves"})

# A declared Way in `system/michi.md` — `## Way N — <title>  (slug: `<slug>`)`,
# the whole shape `core/templates/michi_template.md:13` mandates, heading and
# all. The heading anchor is load-bearing, not decoration: that same template
# line spells the shape out literally, backticks included, inside a blockquote
# telling the reader what to write — and `spawn_satellite.py` stamps the
# template verbatim (substituting `<instance>` alone), so an unanchored
# pattern reads a fresh instance's placeholder as a declared Way called
# `<kebab-slug>` and turns "no Ways declared yet" into "every real referent is
# MISSING". Requiring the marker to sit on a heading line keeps a declaration
# distinct from prose, a blockquote, or an example that merely quotes one.
_MICHI_SLUG_RE = re.compile(r"^#{1,6} .*\(slug:\s*`([^`]+)`\)", re.MULTILINE)

# A station filename's `<YYYY-MM-DD>_<slug>` stem — the `Shukuba:` token
# `commit_format.md` names (2026-09-14). Commits written before carry the
# bare slug too, so `_resolve_shukuba` still accepts a matched stem's bare
# slug as well as the stem itself.
_DATED_STEM_RE = re.compile(r"^\d{4}-\d{2}-\d{2}_(.+)$")

# Every folder a station file may legitimately sit in, relative to a
# project's `journey/shukuba/` — its own root (the open station), plus the
# two lifecycle folders a close (`shukuba-retire`) or a park
# (`shukuba-park`) moves it into.
_SHUKUBA_LIFECYCLE_SUBDIRS = ("", "trail", "parked")


def _directional_referent(directional: str) -> tuple[str, str] | None:
    """Turn a `--directional` line into the one referent that has to
    resolve, or `None` ("nothing to check here"). Pure — no filesystem, no
    git; the resolvers that actually check existence are their own
    functions, called only when this returns a referent.

    `None` on: a line that does not open with `Shukuba:`/`Agari:`/`Michi:`
    at its start (leading whitespace tolerated); no token after the colon;
    a token of `none` (the project/instance hasn't reached this referent
    yet — `commit_format.md` §Directional trailer); a token ending `:`
    (a bare `progress:`/`aside:`/`serves:` with no slug — on `Shukuba:` and
    `Agari:` a malformed line `_unnamed_referent_refusal` refuses); or a token lowercasing to one
    of `_DIRECTIONAL_SKIP_TOKENS` (a reading word with no colon, e.g.
    `Shukuba: progress — x`). Otherwise `(form, token)`, the token returned
    verbatim as the first whitespace-delimited word after the colon — a
    dated station stem (`YYYY-MM-DD_migrate-scripts-to-tools`) comes back
    whole, unsplit."""
    match = _DIRECTIONAL_FORM_RE.match(directional)
    if match is None:
        return None
    form, token = match.group(1), match.group(2)
    if not token or token == "none" or token.endswith(":"):
        return None
    if token.lower() in _DIRECTIONAL_SKIP_TOKENS:
        return None
    return (form, token)


class DirectionalResolution(Enum):
    """Whether a directional referent's token actually exists in the tree
    the commit lands in. A bare `Enum` — every member is only ever compared,
    never written out or read back — per this house's own Python convention
    for a closed value set (`conventions.md` § Constructs).

    `MISSING` is the only value a refusal may ever be built from
    (`_directional_refusal`, Task 4). `UNCHECKABLE` means the check could not
    tell — no `system/projects/` (an external product repo, a repo with no
    kensaiapp structure at all) or a placeholder `system/michi.md` declaring
    no Ways yet — and a check that cannot tell is not a check that failed."""
    RESOLVES = auto()
    MISSING = auto()
    UNCHECKABLE = auto()


def _resolve_agari(repo: str, token: str) -> DirectionalResolution:
    """Does `Agari: <token>` name a real project? `RESOLVES` when
    `<repo>/system/projects/<token>/agari.md` is a file; `UNCHECKABLE` when
    `<repo>/system/projects/` itself does not exist (an external product
    repo, or a tree with no kensaiapp structure — the referent cannot be
    checked, not "wrong"); `MISSING` otherwise — including the recorded
    incident this check exists for (`Agari: versioning` against a tree whose
    only project is `doctrine`).

    `token` is untrusted input (it rides in from a commit's own
    `--directional` string), so the candidate path is resolved and checked
    for containment inside `system/projects/` before anything is read — a
    `..` or an embedded `/` must never let this reach outside that
    directory, even when a file of the same name happens to sit there."""
    projects_root = Path(repo) / "system" / "projects"
    if not projects_root.is_dir():
        return DirectionalResolution.UNCHECKABLE
    projects_root = projects_root.resolve()
    candidate = (projects_root / token / "agari.md").resolve()
    if projects_root not in candidate.parents:
        return DirectionalResolution.MISSING
    return (
        DirectionalResolution.RESOLVES
        if candidate.is_file()
        else DirectionalResolution.MISSING
    )


def _resolve_michi(repo: str, token: str) -> DirectionalResolution:
    """Does `Michi: <token>` name a Way this instance has actually declared?
    `RESOLVES` when `<token>` appears as a `(slug: `<token>`)` marker on a
    **heading** line of `<repo>/system/michi.md`; `UNCHECKABLE` when the file
    is absent, or present but declares no Ways at all — the stamped
    placeholder included, since a fresh instance before `kensaiapp-michi` has
    run must not have every commit refused; `MISSING` when the file declares
    at least one real Way but not this one — including a token that appears
    only in the file's prose, or inside an example, with no heading
    declaration of its own."""
    michi_md = Path(repo) / "system" / "michi.md"
    try:
        text = michi_md.read_text(encoding="utf-8")
    except OSError:
        return DirectionalResolution.UNCHECKABLE
    slugs = set(_MICHI_SLUG_RE.findall(text))
    if not slugs:
        return DirectionalResolution.UNCHECKABLE
    return (
        DirectionalResolution.RESOLVES
        if token in slugs
        else DirectionalResolution.MISSING
    )


def _resolve_shukuba(repo: str, token: str) -> DirectionalResolution:
    """Does `Shukuba: <token>` name a real station of some project? `RESOLVES`
    when a `.md` file (never `README.md`) exists whose stem is `token`, or
    matches `<YYYY-MM-DD>_<token>`, under ANY project's `journey/shukuba/` —
    its root, its `trail/`, or its `parked/`. `<repo>/system/projects/`
    absent -> `UNCHECKABLE`; everything else -> `MISSING`.

    Four facts the accept-set is built from — narrowing this back to the
    root folder alone silently breaks the two commits this check exists not
    to break:

    1. The station file moves BEFORE the builder is invoked for that commit.
       `shukuba-retire` `git mv`s the station to `trail/` and then calls the
       builder with `Shukuba: <YYYY-MM-DD>_<slug> — progress: reached, closed to trail`;
       `shukuba-park` does the same to `parked/`. A root-only check refuses
       every close and every park — the exact valid-commit rejection this
       check must not commit.
    2. Read the filesystem, not the git index, and read it before staging.
       A newly opened station is written to disk and staged with `--add` in
       the same invocation — `shukuba-open`'s commit; at check time the file
       is on disk and not yet in the index.
    3. Both slug spellings are in live use — a bare slug and the full
       `<date>_<slug>` stem. `commit_format.md` names the stem (2026-09-14);
       the bare slug stays accepted because the recipes and commits written
       before that ruling carry it.
    4. `Shukuba:` never resolves against the instance router
       `system/shukuba/`. `commit_format.md` fixes it to a *project's*
       station; an instance-scoped commit takes `Michi:` instead — so that
       folder is never searched, deliberately.

    `token` is never used to build a filesystem path — it is only ever
    compared against the set of station stems actually found on disk, built
    once per call. A token carrying `..` or `/` therefore can never match
    anything real and can never cause a read outside the tree; it is
    unreachable membership, not a path to resolve."""
    projects_root = Path(repo) / "system" / "projects"
    if not projects_root.is_dir():
        return DirectionalResolution.UNCHECKABLE

    accepted: set[str] = set()
    for project_dir in projects_root.iterdir():
        if not project_dir.is_dir():
            continue
        shukuba_root = project_dir / "journey" / "shukuba"
        for subdir in _SHUKUBA_LIFECYCLE_SUBDIRS:
            lifecycle_dir = shukuba_root / subdir if subdir else shukuba_root
            if not lifecycle_dir.is_dir():
                continue
            for md_file in lifecycle_dir.glob("*.md"):
                if md_file.name == "README.md":
                    continue
                stem = md_file.stem
                accepted.add(stem)
                dated = _DATED_STEM_RE.match(stem)
                if dated:
                    accepted.add(dated.group(1))

    return (
        DirectionalResolution.RESOLVES
        if token in accepted
        else DirectionalResolution.MISSING
    )


def _unnamed_referent_refusal(directional: str) -> str | None:
    """The refusal for a `Shukuba:`/`Agari:` line that puts a reading where
    its station or project belongs, or `None`. Pure — the shape alone
    decides it."""
    match = _DIRECTIONAL_FORM_RE.match(directional)
    if match is None or match.group(1) == "Michi":
        return None
    form, token = match.group(1), match.group(2)
    if token.rstrip(":").lower() not in _DIRECTIONAL_SKIP_TOKENS:
        return None
    referent = "station" if form == "Shukuba" else "project"
    shape = "<YYYY-MM-DD>_<slug>" if form == "Shukuba" else "<project>"
    lines = [
        f"commit_builder: refusing to commit — {form}: names no {referent}: {directional.strip()!r}.",
        f"Write {form}: {shape} — progress: <how>, or — aside: <why>.",
    ]
    if form == "Shukuba":
        lines.append(
            "With no station open, write Agari: <project> — progress: <how>, "
            "or — aside: <why>, instead."
        )
    return "\n".join(lines)


def _directional_refusal(repo: str, directional: str) -> str | None:
    """Whether a `--directional` line's referent should refuse the commit —
    mirroring `_staged_set_guard_refusal` / `_bump_refusal`'s house shape: a
    function returning the message to print, or `None` to proceed.

    A line `_directional_referent` cannot parse, or that carries no referent
    at all (`none`, or `Michi:`'s bare `aside:`), returns `None` immediately
    — there is nothing to check. Otherwise the parsed form
    dispatches to its own resolver, and the message is built **only** for
    `MISSING` — `RESOLVES` and `UNCHECKABLE` both proceed silently, per
    `commit_format.md`'s never-block rule: this refuses a referent that IS
    present and does NOT exist, never a referent this check merely could not
    verify.

    One shape is refused before any referent is read: a `Shukuba:` or
    `Agari:` line whose first word is a reading (`progress:`, `aside:`)
    where the station or project belongs. `commit_format.md` gives those
    two forms no state without a referent — only `Agari: none` — so the
    line is malformed, whatever the tree holds. `Michi: aside:` is the one
    reading that legally stands first, and it is left alone."""
    unnamed = _unnamed_referent_refusal(directional)
    if unnamed is not None:
        return unnamed
    parsed = _directional_referent(directional)
    if parsed is None:
        return None
    form, token = parsed

    if form == "Agari":
        resolution = _resolve_agari(repo, token)
        searched = f"system/projects/{token}/agari.md"
        ways_out = (
            "Ways out: check the project name is spelled correctly, or use "
            "one of the names under system/projects/."
        )
    elif form == "Michi":
        resolution = _resolve_michi(repo, token)
        searched = f'system/michi.md, for a "(slug: `{token}`)" entry'
        ways_out = (
            "Ways out: check the slug is spelled correctly, or use one of "
            "the Ways declared in system/michi.md."
        )
    else:  # "Shukuba"
        resolution = _resolve_shukuba(repo, token)
        searched = (
            "every project's journey/shukuba/ (its open root), "
            "journey/shukuba/trail/, and journey/shukuba/parked/"
        )
        ways_out = (
            "Ways out: check the station slug is spelled correctly — "
            "trail/ and parked/ were searched too, so a genuinely closed "
            "or parked station should already have matched — or open the "
            "station first."
        )

    if resolution != DirectionalResolution.MISSING:
        return None

    return "\n".join([
        f"commit_builder: refusing to commit — {form}: {token!r} does not resolve.",
        f"Looked in {searched} — not found.",
        ways_out,
    ])


class UnknownActorError(ValueError):
    """An actor with no `AGENT_ROLE` mapping (or, on the merge path, no
    `MERGE_AUTHORIZER` mapping). The builder refuses to construct a commit or
    merge it cannot derive the trailer for, rather than emit a Role-less or
    malformed trailer block that the `commit-msg` hook would then reject."""


def _role_for(actor: str) -> str:
    """Map an actor to its doctrine `Role:` value, or refuse."""
    try:
        return AGENT_ROLE[actor]
    except KeyError:
        raise UnknownActorError(
            f"unknown actor {actor!r} has no AGENT_ROLE mapping — refusing "
            "to build a commit with no derivable Role:"
        ) from None


def _merge_authorizer_for(actor: str | None, authorizer: str | None = None) -> str:
    """Resolve the `Merge-Authorized:` token from an actor or an interactive authorizer, or refuse.

    Exactly one arrives, enforced by the CLI's mutually-exclusive group. Both paths are closed
    sets — see INTERACTIVE_MERGE_AUTHORIZERS for why the verbatim one is validated where the
    commit path's `--role` is not.
    """
    if authorizer is not None:
        if authorizer not in INTERACTIVE_MERGE_AUTHORIZERS:
            raise UnknownActorError(
                f"unknown merge authorizer {authorizer!r} — an interactive merge may claim only "
                f"{sorted(INTERACTIVE_MERGE_AUTHORIZERS)}. Refusing to build a merge whose "
                "authorizer is a string nobody sanctioned."
            )
        return authorizer
    try:
        return MERGE_AUTHORIZER[actor]  # type: ignore[index]
    except KeyError:
        raise UnknownActorError(
            f"unknown merge actor {actor!r} has no MERGE_AUTHORIZER mapping — "
            "refusing to build a merge with no derivable Merge-Authorized:"
        ) from None


def _advance_authorizer_for(actor: str | None, authorizer: str | None = None) -> str:
    """Resolve the `Merge-Authorized:` token for an `advance` from any commit actor or an
    interactive authorizer, or refuse. Exactly one arrives, enforced by the CLI's
    mutually-exclusive group.

    Unlike `_merge_authorizer_for` (the merge-**to-`main`** path, narrowed by
    `MERGE_AUTHORIZER` because that op is the highest-consequence write in the repo), an advance
    lands nothing on `main` — it is the branch's own housekeeping, taking an advance the branch
    would otherwise simply fall behind on — so any actor that may author a commit may authorize
    it: the lookup is `AGENT_ROLE` directly, never `MERGE_AUTHORIZER`. The interactive axis
    (`--authorizer`) stays the same closed set `merge` uses — `INTERACTIVE_MERGE_AUTHORIZERS` —
    because an owner-directed advance has the same no-subagent-identity shape a directed merge
    does."""
    if authorizer is not None:
        if authorizer not in INTERACTIVE_MERGE_AUTHORIZERS:
            raise UnknownActorError(
                f"unknown advance authorizer {authorizer!r} — an interactive advance may claim "
                f"only {sorted(INTERACTIVE_MERGE_AUTHORIZERS)}. Refusing to build an advance "
                "whose authorizer is a string nobody sanctioned."
            )
        return authorizer
    try:
        return AGENT_ROLE[actor]  # type: ignore[index]
    except KeyError:
        raise UnknownActorError(
            f"unknown actor {actor!r} has no AGENT_ROLE mapping — refusing to build an advance "
            "with no derivable Merge-Authorized:"
        ) from None


def _read_frontmatter_semver(md: Path) -> str | None:
    """Line-scan a file's `---` frontmatter block for its declared
    `version:` value. Returns `None` (never raises) when the file is absent,
    unreadable, has no frontmatter block, or the block carries no `version:`
    line — the caller treats every one of these as "unresolvable"."""
    try:
        lines = md.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    if not lines or lines[0].strip() != "---":
        return None
    try:
        frontmatter_end = lines.index("---", 1)
    except ValueError:
        return None
    for line in lines[1:frontmatter_end]:
        match = _VERSION_LINE.match(line)
        if match:
            return match.group(1)
    return None


def _pin_git_source(repo: str) -> tuple[str, str | None] | None:
    """Where a `git log` against `repo` should actually run: `(repo, None)` — unrestricted, at
    `HEAD` — when `repo` is not a pin, or `(source_host_root, source_head)` when it is, so the
    query never touches the pin's own directory, which is a plain copy of a git repo and not one
    itself (`git -C <pin> ...` finds nothing). Restricting to `source_head` — the host's `HEAD` at
    the moment the pin was made — matters as much as redirecting the repo: without it, a commit
    landed on the host *after* the pin was taken would change what a run still executing under
    that pin attributes a pinned file to, even though the pinned file itself never moved.

    Returns `None` for a pin with no recorded `source_head` — made before that field existed, or
    from a host that was not a git work tree at pin time. There is nowhere left to resolve a
    revision from, and this function never guesses one; the caller reads that as "unresolvable",
    same as every other gap `_skill_source_sha` / `_prompt_source_sha` already treat that way.

    Shared by `_skill_source_sha` and `_prompt_source_sha` — the only two callers that turn a
    resolved source root into somewhere `git log` can actually run."""
    found = pin.of_core(Path(repo) / "core")
    if found is None:
        return (repo, None)
    if found.source_head is None:
        return None
    return (str(found.source_host_root), found.source_head)


def _skill_source_sha(repo: str, skill_dir: Path) -> str | None:
    """The skill source's last-modifying commit — `git log -1 --format=%H --
    <skill_dir, repo-relative>` — full 40-char `%H`, never `%h` and never repo
    `HEAD`. `HEAD` changes on every commit regardless of the skill and would
    carry no drift signal; the skill's last-modifying commit changes only
    when that skill's own source changes, which is the signal the trailer
    exists to carry. `skill_dir` is the directory `skill_path.resolve_skill_dir`
    already found (flat or grouped) — passed to `git log` as a repo-relative
    pathspec via `os.path.relpath`, which reproduces today's
    `.claude/skills/<name>/` literal exactly for a flat skill.

    When `repo` is a pin (a launch-time frozen copy, `pin.py`), the pin's own directory is not a
    git repo and carries no history of its own — `_pin_git_source` redirects the `git log` to the
    pin's `source_host_root`, restricted to the `source_head` recorded when the pin was made, so a
    host commit after that moment cannot change the answer. A pin recorded with no `source_head`
    resolves to `None` here too — never guessed.

    Returns `None` (never raises) on any git failure — an uncommitted or nonexistent skill
    path is "unresolvable", not an error."""
    pathspec = os.path.relpath(skill_dir, repo) + "/"
    source = _pin_git_source(repo)
    if source is None:
        return None
    git_repo, rev = source
    cmd = ["git", "-C", git_repo, "log", "-1", "--format=%H"]
    if rev is not None:
        cmd.append(rev)
    cmd += ["--", pathspec]
    result = subprocess.run(cmd, capture_output=True, text=True)
    sha = result.stdout.strip()
    if result.returncode != 0 or not sha:
        return None
    return sha


def instance_repo_root() -> Path:
    """The kensaiapp instance root that owns this builder and its skills — the
    parent of `core/tools/`, derived from this file's own location. Skill
    source resolves through `skill_path.resolve_skill_dir`, under either the
    flat or the grouped layout, against this instance root — whichever repo a
    commit actually lands in. For an external product the commit-target repo
    holds no skill source at all, so `Skill-Version:` provenance must resolve
    against the instance, never the commit target — that is why the call site
    hands this path (not `--repo`) to `resolve_skill_version`.

    **Not always a git repo itself.** Under a pin (`pin.py`), this file's own
    location is inside the pin's frozen copy, so this returns the pin's root —
    a plain directory tree, not something `git -C <this path>` can query.
    `_skill_source_sha` / `_prompt_source_sha` (via `_pin_git_source`) detect
    that case and redirect the actual `git log` to the pin's recorded
    `source_host_root`; nothing here needs to know the difference."""
    return Path(__file__).resolve().parents[2]


def resolve_skill_version(
    skill_repo: str, skill_name: str | None = None
) -> str | None:
    """Turn a producing skill into its `Skill-Version:` trailer value
    `<name>@<semver> <sha>`, or `None`. All file-read and git-subprocess work
    lives here — `build_message` stays pure and only places the value this
    function hands it.

    The producing skill's *name* is supplied **explicitly** by the caller
    (`--skill <name>`), and only explicitly. There is no actor derivation: the
    former `actor -> ACTOR_SKILL` fallback was retired (2026-07-24) because it
    inferred *what skill produced the output* from *who committed*, which is
    false for any role or general-purpose session that commits without running
    a skill. A caller that ran a producing skill names it; a caller that ran
    none passes no `--skill` and correctly carries no line.

    `skill_repo` is the repo that holds the skill *source* — the kensaiapp
    instance repo — NOT the commit-target repo. For an in-repo product the two
    coincide; for an external product they differ, and passing the commit
    target here would silently resolve to `None` (the external repo holds no
    skill source at all). The call site supplies `instance_repo_root()`.

    The skill's directory is resolved through `skill_path.resolve_skill_dir`
    (flat first, then the single grouped match) — never a hand-built
    `.claude/skills/<name>` literal, so a skill under the grouped layout
    resolves exactly as a flat one does. `None` on: no explicit `skill_name`
    (the skill-less path — a `--role` commit, or a bare `--actor` with no
    `--skill`), or a named skill that does not resolve to exactly one
    directory (not found, or ambiguous — two copies of one name), or whose
    resolved source can't be read (`SKILL.md` absent, or present with no
    `version:` line, or its source has no committed revision). Never
    fabricates a value, never raises — the trailer is best-effort,
    non-required provenance; a missing value must never block a commit."""
    if skill_name is None:
        return None
    name = skill_name
    resolution = skill_path.resolve_skill_dir(skill_repo, name)
    if resolution.status != skill_path.FOUND:
        return None
    skill_md = resolution.path / "SKILL.md"
    semver = _read_frontmatter_semver(skill_md)
    if semver is None:
        return None
    sha = _skill_source_sha(skill_repo, resolution.path)
    if sha is None:
        return None
    return f"{name}@{semver} {sha}"


def _prompt_source_sha(repo: str, prompt_md: Path) -> str | None:
    """The prompt file's last-modifying commit — `git log -1 --format=%H --
    <prompt_md, repo-relative>`. `_skill_source_sha`'s twin, and the only place
    the two paths differ: a prompt is a **file** where a skill is a directory.
    Same contract otherwise — full 40-char `%H`, never repo `HEAD` (which
    moves on every commit and carries no drift signal), `None` rather than
    a raise on any git failure, and the same `_pin_git_source` redirect when
    `repo` is a pin rather than the git repo itself."""
    pathspec = os.path.relpath(prompt_md, repo)
    source = _pin_git_source(repo)
    if source is None:
        return None
    git_repo, rev = source
    cmd = ["git", "-C", git_repo, "log", "-1", "--format=%H"]
    if rev is not None:
        cmd.append(rev)
    cmd += ["--", pathspec]
    result = subprocess.run(cmd, capture_output=True, text=True)
    sha = result.stdout.strip()
    if result.returncode != 0 or not sha:
        return None
    return sha


def resolve_prompt_version(
    prompt_repo: str, prompt_name: str | None = None
) -> str | None:
    """Turn a prompt a session read into its `Prompt-Version:` trailer value
    `<name>@<semver> <sha>`, or `None`. The sibling of
    `resolve_skill_version`, and the answer to the case that one structurally
    cannot cover: a prompt has no `SKILL.md`, so a run that followed it
    committed indistinguishably from a hand-authored one.

    The name is supplied **explicitly** (`--prompt <name>`), and only
    explicitly — born with the property `Skill-Version:` had to be corrected
    into on 2026-07-24. Nothing is ever inferred from the actor.

    It takes a **name**, not a path, in one of two forms: a bare `<name>` is
    `core/prompts/<name>.md`, and `<skill>/<prompt>` is that skill's own
    `prompts/<prompt>.md`, the skill resolved through
    `skill_path.resolve_skill_dir` as `resolve_skill_version` resolves it. The
    satellites carry no `core/` of their own and resolve `<CORE>` to this
    instance's, so a name has exactly one resolution from anywhere while a
    path has as many as there are callers —
    and `prompt_repo` is the *instance* repo, not the commit target, for the
    same reason `resolve_skill_version` takes one (an external product repo
    holds no prompt source). The call site supplies `instance_repo_root()`.

    The frontmatter reader is shared as-is: `_read_frontmatter_semver` scans
    any `---` block for a `version:` line, and every prompt carries one.

    `None` on: no explicit `prompt_name`, or a named prompt whose source can't
    be read (file absent, present with no `version:` line, or having no
    committed revision). Never fabricates, never raises — non-required
    provenance must never block a commit."""
    if prompt_name is None:
        return None
    name = prompt_name
    if "/" in name:
        skill_name, _, prompt = name.partition("/")
        if not prompt or "/" in prompt:
            return None
        resolution = skill_path.resolve_skill_dir(prompt_repo, skill_name)
        if resolution.status != skill_path.FOUND:
            return None
        prompt_md = resolution.path / "prompts" / f"{prompt}.md"
    else:
        prompt_md = Path(prompt_repo) / "core" / "prompts" / f"{name}.md"
    semver = _read_frontmatter_semver(prompt_md)
    if semver is None:
        return None
    sha = _prompt_source_sha(prompt_repo, prompt_md)
    if sha is None:
        return None
    return f"{name}@{semver} {sha}"


def _read_comment_marker_semver(js: Path) -> str | None:
    """Line-scan a saved Workflow script for its `// Version: x.y.z` marker.

    The sibling of `_read_frontmatter_semver`, and a separate function rather
    than a widened one: a workflow carries no frontmatter at all, so there is
    no `---` block to scan and nothing to share but the intent.

    **First match wins, and the file is scanned whole.** There is no delimiter
    to bound the search the way `---` bounds frontmatter, and bounding it by
    line count would encode a guess about how long a `meta` block may be.
    `versioning.md` places the marker directly below `meta`, so the first
    whole-line match is that marker in every conforming file; a second
    occurrence further down cannot win, which is what makes a stray mention in
    a later comment harmless.

    Returns `None` (never raises) when the file is absent, unreadable, or
    carries no marker — every one of which the caller treats as
    "unresolvable"."""
    try:
        lines = js.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    for line in lines:
        match = _WORKFLOW_VERSION_COMMENT.match(line)
        if match:
            return match.group(1)
    return None


def _workflow_source_sha(repo: str, name: str) -> str | None:
    """The workflow's last-modifying commit — `git log -1 --format=%H --
    .claude/workflows/<name>.js`. The third of the trio, and the same contract
    as the other two: full 40-char `%H`, never repo `HEAD` (which moves on
    every commit and carries no drift signal), and `None` rather than a raise
    on any git failure."""
    result = subprocess.run(
        ["git", "-C", repo, "log", "-1", "--format=%H", "--", f".claude/workflows/{name}.js"],
        capture_output=True, text=True,
    )
    sha = result.stdout.strip()
    if result.returncode != 0 or not sha:
        return None
    return sha


def resolve_workflow_version(
    workflow_repo: str, workflow_name: str | None = None
) -> str | None:
    """Turn the saved Workflow script that drove a run into its
    `Workflow-Version:` trailer value `<name>@<semver> <sha>`, or `None`.

    The case its two siblings structurally cannot cover: a workflow may hold
    the load-bearing half of a capability — a turn loop, a closure rule, a
    report derivation — and a commit could name the skill and the prompt while
    saying nothing about the component that actually drove the run.

    Explicit-only (`--workflow <name>`), like both siblings and like neither
    of them had to be corrected into. Nothing is inferred from the actor.

    It takes a **name**, not a path, for the same reason and with the same
    force as `resolve_prompt_version`: `.claude/workflows/<name>.js` is the one
    location a saved workflow lives in, and `workflow_repo` is the *instance*
    repo rather than the commit target, because an external product repo holds
    no workflow source. The call site supplies `instance_repo_root()`.

    The read is `_read_comment_marker_semver`, not the shared frontmatter
    reader — see that function for why a workflow's marker is a comment and
    why it sits below `meta`.

    `None` on: no explicit `workflow_name`, or a named workflow whose source
    cannot be read (file absent, present with no marker, or having no committed
    revision). Never fabricates, never raises — non-required provenance must
    never block a commit."""
    if workflow_name is None:
        return None
    name = workflow_name
    workflow_js = Path(workflow_repo) / ".claude" / "workflows" / f"{name}.js"
    semver = _read_comment_marker_semver(workflow_js)
    if semver is None:
        return None
    sha = _workflow_source_sha(workflow_repo, name)
    if sha is None:
        return None
    return f"{name}@{semver} {sha}"


def _assemble(subject: str, body: str, trailers: list[str]) -> str:
    """Join subject, body, and the trailer block with canonical commit-message
    spacing. Shared by both ops — trailer order becomes a fact of this
    explicit ordered sequence, never an insertion-anchor accident."""
    trailer_block = "\n".join(trailers)
    sections = [subject]
    if body:
        sections.append(body)
    sections.append(trailer_block)
    return "\n\n".join(sections)


def build_message(
    op: Op,
    *,
    subject: str | None = None,
    body: str = "",
    actor: str | None = None,
    role: str | None = None,
    authorizer: str | None = None,
    directional: str | None = None,
    branch: str | None = None,
    target_branch: str | None = None,
    description: str | None = None,
    branch_commits: list[str] | None = None,
    merge_context: str | None = None,
    from_ref: str | None = None,
    taken_sha: str | None = None,
    surface: str,
    co_authored_by: str | None = None,
    reasoning_effort: str | None = None,
    claude_session: str | None = None,
    skill_version: str | None = None,
    prompt_version: str | None = None,
    workflow_version: str | None = None,
) -> str:
    """Assemble a canonical commit, merge, or advance message.

    One function serves all three ops — `op` selects which trailer list and
    body get built. One trailer is actor-derived per path: `Role:` (actor ->
    `AGENT_ROLE`) on `commit`, the `Merge-Authorized:` authorizer (actor ->
    `MERGE_AUTHORIZER`) on `merge`, and the same trailer key again on
    `advance` — but resolved via `AGENT_ROLE` directly (`_advance_authorizer_for`),
    since an advance lands nothing on `main` and any commit actor may authorize
    one. Every other trailer's content (the
    directional line, `Surface:`, `Co-Authored-By:`, `Reasoning-Effort:`, the merge context, the
    branch-commit lines, the taken ref and sha) is caller-supplied — this
    function places it, it does not resolve it.

    `skill_version` is the same shape: the finished `<name>@<semver> <sha>`
    value (or `None`), resolved elsewhere (`resolve_skill_version`) and
    handed in for placement only — this function does no file or git I/O to
    produce it. On `commit`, a truthy value is appended after runtime/session
    attribution and before any prompt or workflow provenance; `None` (the
    default, or an explicit `None`) appends nothing. On `merge` and `advance`
    the parameter is ignored outright — a merge (or an advance) is authored
    by its authorizer, not a producing skill, so it never carries the line.

    `reasoning_effort` is an already-resolved optional runtime value, placed
    directly after `Co-Authored-By:` when present (or `Surface:` otherwise)
    on **all three ops**. This builder places it but never selects or infers it.

    `claude_session` is the URL of the Claude Code session that produced the
    commit, placed after `Reasoning-Effort:` when present (otherwise directly
    after `Co-Authored-By:`) on **all three ops** — the
    two answer neighbouring questions, which model and which conversation, and
    a merge or an advance is made in a session exactly as a commit is.
    Optional throughout: omitted, nothing is appended, and a run with no
    session URL to give is not a run that has to invent one.

    `prompt_version` is its sibling and behaves identically — placed after
    `Skill-Version:` when truthy, appended nowhere on `merge` or `advance`.
    The two are independent: either, both, or neither may appear, and passing
    one says nothing about the other.

    `from_ref` and `taken_sha` are `advance`-only: the ref named by `--from`
    and the 40-hex sha of the commit actually merged (the resume case may
    differ from `from_ref`'s current tip — the caller resolves which sha that
    is; this function only places it in the `Merge-Authorized:` context).
    Both are ignored on `commit` and `merge`.
    """
    if op == "commit":
        # Two ways in: a workflow caller passes `actor` (mapped through
        # AGENT_ROLE), an interactive caller passes its posture `role`
        # verbatim (no subagent identity to derive from). Exactly one — the
        # CLI enforces it via a required mutually-exclusive group.
        role_value = role if role is not None else _role_for(actor)  # type: ignore[arg-type]
        trailers = [
            directional,
            f"Role: {role_value}",
            f"Surface: {surface}",
        ]
        # A committer with no model behind it omits the line rather than
        # naming one. `Role:` and `Surface:` are the enforced set
        # (`verify_commit_msg.py`), so the absence is clean, and it
        # positively means no model authored this commit.
        if co_authored_by:
            trailers.append(f"Co-Authored-By: {co_authored_by}")
        if reasoning_effort:
            trailers.append(f"Reasoning-Effort: {reasoning_effort}")
        if claude_session:
            trailers.append(f"Claude-Session: {claude_session}")
        if skill_version:
            trailers.append(f"Skill-Version: {skill_version}")
        if prompt_version:
            trailers.append(f"Prompt-Version: {prompt_version}")
        if workflow_version:
            trailers.append(f"Workflow-Version: {workflow_version}")
        return _assemble(subject, body, trailers)  # type: ignore[arg-type]

    if op == "merge":
        resolved = _merge_authorizer_for(actor, authorizer)
        merge_subject = f"merge: {branch} → {target_branch} — {description}"
        # A blank entry is refused rather than dropped. `[""]` rendered `-> ` into
        # `ea557199` on `main`, from a caller whose zsh expanded an unset array
        # under `"${ARR[@]}"` to one empty string instead of to no arguments.
        # Dropping it would leave that caller a merge with no commit list and no
        # signal; the visible bullet is what exposed the defect, so the refusal
        # keeps the visibility and moves it earlier.
        for entry in branch_commits or []:
            if not entry.strip():
                raise ValueError(
                    "branch_commits carries a blank entry — a commit line cannot be "
                    "empty. Pass no entries for an empty body, or check the caller: "
                    'in zsh, `"${ARR[@]}"` on an unset array yields one empty string.'
                )
        merge_body = "\n".join(f"-> {line}" for line in (branch_commits or []))
        trailers = [
            f"Merge-Authorized: {resolved} — {merge_context}",
            f"Surface: {surface}",
        ]
        if co_authored_by:
            trailers.append(f"Co-Authored-By: {co_authored_by}")
        if reasoning_effort:
            trailers.append(f"Reasoning-Effort: {reasoning_effort}")
        if claude_session:
            trailers.append(f"Claude-Session: {claude_session}")
        return _assemble(merge_subject, merge_body, trailers)

    if op == "advance":
        resolved = _advance_authorizer_for(actor, authorizer)
        advance_subject = f"merge: {from_ref} → {branch} — take {from_ref}'s advance"
        trailers = [
            f"Merge-Authorized: {resolved} — takes {from_ref} at {taken_sha}",
            f"Surface: {surface}",
        ]
        if co_authored_by:
            trailers.append(f"Co-Authored-By: {co_authored_by}")
        if reasoning_effort:
            trailers.append(f"Reasoning-Effort: {reasoning_effort}")
        if claude_session:
            trailers.append(f"Claude-Session: {claude_session}")
        return _assemble(advance_subject, "", trailers)

    raise ValueError(f"unknown op {op!r} — expected 'commit', 'merge', or 'advance'")


def _run_git_rm(repo: str, paths: list[str]) -> int:
    """Stage a removal via `git -C <repo> rm` — the `-C` form, never `cd
    <repo> && git rm`. A `cd <dir> && git ...` compound trips the harness's
    "cd-then-git can run untrusted hooks" guard and halts an autonomous run;
    `git -C` does not. Staging lives here so the caller emits a single
    allow-listed `python3 commit_builder.py` call with nothing to improvise."""
    if not paths:
        return 0
    return subprocess.run(["git", "-C", repo, "rm", *paths]).returncode


def _run_git_add(repo: str, paths: list[str]) -> int:
    """Stage additions/modifications via `git -C <repo> add` — the `-C` form,
    for the same guard-avoidance reason as `_run_git_rm`."""
    if not paths:
        return 0
    return subprocess.run(["git", "-C", repo, "add", *paths]).returncode


def _run_git_commit(repo: str, message: str, allow_empty: bool = False) -> int:
    cmd = ["git", "-C", repo, "commit", "-m", message]
    if allow_empty:
        cmd.append("--allow-empty")
    return subprocess.run(cmd).returncode


def _read_staged_paths(repo: str) -> list[str]:
    """The full staged set at commit time, with rename detection off — a
    staged rename shows as its two halves (the deletion of the old path and
    the addition of the new), each checked independently by the guard
    below. Never `git status --porcelain` (that reads the working tree
    too); `--cached` only, so unstaged dirt never enters this read.

    `-z` (NUL-separated) is load-bearing, not a style choice: without it git
    renders the path for *display*, C-quoting any name that carries a
    non-ASCII byte (`core.quotePath` defaults to true), so `見本.md` arrives
    as the 29-character literal `"\\350\\246\\213\\346\\234\\254.md"`. The
    guard compares these against the caller's declarations verbatim, so a
    quoted path matches no `--add`/`--rm`/`--staged` value and a fully
    declared commit is refused — with a message naming a path that does not
    exist and a `--staged` remedy that cannot work. `-z` emits raw path
    bytes, which is what the caller declared."""
    result = subprocess.run(
        ["git", "-C", repo, "diff", "--cached", "--name-only", "--no-renames", "-z"],
        capture_output=True, text=True,
    )
    return [path for path in result.stdout.split("\0") if path]


def _repo_prefix(repo: str) -> str:
    """Where `repo` sits inside its work tree — `products/demo/` for a product held inside the
    instance repo, `""` at the root. `git -C <repo> add x` resolves `x` against `repo`, but
    `_read_staged_paths` reads the index from the root, so a declaration is read through this
    prefix before it is compared; without it every commit made with `--repo` at a subdirectory
    is refused for paths it declared."""
    result = subprocess.run(
        ["git", "-C", repo, "rev-parse", "--show-prefix"], capture_output=True, text=True,
    )
    return result.stdout.strip()


def _covers(declared: str, staged_path: str) -> bool:
    """A declared path covers a staged path when it equals it exactly, or
    when it is a directory prefix of it at a `/` boundary — a string-only
    prefix (`docs/prop` against `docs/proposals/x`) does not count.

    A trailing slash on the declaration is stripped first. `docs/x/` is how a
    caller naturally writes a directory, and it names exactly what `docs/x`
    names; git never emits one, so left in it produced `docs/x//` and matched
    nothing — the caller then got their declaration rejected as matching-nothing
    *and* its own paths reported undeclared, two refusals for one correct call.
    Stripping cannot widen coverage, because the `/` boundary is re-added here
    rather than taken from the caller."""
    declared = declared.rstrip("/")
    return staged_path == declared or staged_path.startswith(f"{declared}/")


def _staged_set_guard_refusal(
    repo: str, add_paths: list[str], rm_paths: list[str], staged_paths: list[str]
) -> str | None:
    """Refuse the commit unless every staged path is covered by what the
    caller declared (--add ∪ --rm ∪ --staged) and every --staged
    declaration matches something actually staged. Returns the refusal
    message to print, or `None` when the guard passes and the commit may
    proceed. Called after staging (`_run_git_rm`/`_run_git_add`) and before
    `_run_git_commit` — it sees the final staged set, and performs no
    rollback of its own: the caller's staging stands exactly as found."""
    staged = _read_staged_paths(repo)
    prefix = _repo_prefix(repo)
    declared = [prefix + d for d in (*add_paths, *rm_paths, *staged_paths)]
    uncovered = [p for p in staged if not any(_covers(d, p) for d in declared)]
    unmatched = [d for d in staged_paths if not any(_covers(prefix + d, p) for p in staged)]

    if not uncovered and not unmatched:
        return None

    lines = ["commit_builder: refusing to commit — staged content is not fully declared."]
    if uncovered:
        lines.append("Staged but not covered by --add/--rm/--staged:")
        lines.extend(f"  {path}" for path in uncovered)
        lines.append(
            "Ways out: if you staged these deliberately outside the builder (e.g. a "
            "git mv), declare them with --staged; if you are an interactive session "
            "accepting the whole index, pass --take-index. If a path above is not "
            "yours, stop and look — another session may have staged it."
        )
    if unmatched:
        lines.append("--staged declaration(s) that match nothing in the staged set:")
        lines.extend(f"  {path}" for path in unmatched)
        lines.append(
            "The move a declaration names may not have happened, or the path is wrong."
        )
    return "\n".join(lines)


# ── the five marker forms a --bump can move ────────────────────────────────
# `versioning.md` § Bump semantics binds every versioned artifact to one rule
# — "A branch never edits a version marker", the landing commit sets the
# number — and § Where the test lands gives five forms for it, whose digits
# are "one set whatever the marker's form" (§ Bump semantics again).
#
# **Read every form in that table, and add one here when the table gains
# one.** A form this module cannot read is a rule that reaches none of the
# files carrying it — while only frontmatter was read, that was every
# executable in the instance: 23 Python files, 22 shell headers, 4 workflows,
# each either bumped on a branch against the rule or never bumped at all. Do
# not answer a form this module cannot read by exempting it in doctrine
# instead; the digits are one set, and an exemption makes the rule mean less
# than it says.

MARKER_FORMS = ("frontmatter", "python", "workflow", "shell", "plugin")

# ── whose markers these are ────────────────────────────────────────────────
# `versioning.md` governs kensaiapp's own artifacts, and they live in four
# layers of an instance. A product's `__version__` is the product's release
# number — content a change may need to set — and its repository is not an
# instance. Read as a marker, it was refused on the branch that came to fix it
# (2026-10-19, a satellite's product) and bumped by every seal that touched it.
_INSTANCE_IDENTITY = "kensaiapp.md"
KENSAIAPP_LAYERS = ("core", ".claude", "skills", "system")


def _work_tree_root(repo: str) -> Path:
    """The top of the work tree `repo` sits in — `repo` itself when git cannot
    say, which then reads as no instance rather than raising."""
    result = subprocess.run(
        ["git", "-C", repo, "rev-parse", "--show-toplevel"], capture_output=True, text=True,
    )
    return Path(result.stdout.strip()) if result.returncode == 0 else Path(repo)


def _is_kensaiapp_path(repo: str, path: str) -> bool:
    """Is `path` — relative to the work tree's top, as git's diffs name it —
    one of kensaiapp's own artifacts, the only files whose marker the branch
    guard, `merge --bump` and `markers --base` judge? True when the work tree
    is an instance (its top holds `kensaiapp.md`, the identity every instance
    carries) and `path` sits in one of `KENSAIAPP_LAYERS`. A product
    repository fails the first test, and an instance's internal product under
    `products/` fails the second.

    **The top, not `repo`.** `--repo` may name a subdirectory
    (`_repo_prefix`); read there, an instance looked like a product and its
    markers went unguarded. The path is normalised first, so
    `core/../products/x` is judged where it lands."""
    if not (_work_tree_root(repo) / _INSTANCE_IDENTITY).is_file():
        return False
    parts = Path(os.path.normpath(path)).parts
    return parts[:1] in {(layer,) for layer in KENSAIAPP_LAYERS}


def _plugin_version_span(text: str) -> tuple[int, int] | None:
    """The character span of a plugin manifest's top-level `"version"` value,
    its quotes excluded, or None when the manifest carries none.

    **Found by walking the manifest's own nesting, not by matching a line.**
    A `"version"` inside another key (a dependency's) can hold the very value
    the top level holds, so neither a line pattern nor a value match can tell
    the two apart; only the depth can. Layout is free: one line or many, any
    spacing around the colon. A manifest that does not parse, is not an
    object, or whose top-level `"version"` is absent or not X.Y.Z, carries
    none."""
    try:
        manifest = json.loads(text)
    except ValueError:
        return None
    if not isinstance(manifest, dict):
        return None
    version = manifest.get("version")
    if not isinstance(version, str) or not _SEMVER.fullmatch(version):
        return None
    decoder = json.JSONDecoder()
    depth = 0
    index = 0
    while index < len(text):
        char = text[index]
        if char in "{[":
            depth += 1
        elif char in "}]":
            depth -= 1
        elif char == '"':
            key, after = decoder.raw_decode(text, index)
            if depth == 1 and key == "version":
                colon = after
                while text[colon].isspace():
                    colon += 1
                if text[colon] == ":":
                    start = colon + 1
                    while text[start].isspace():
                        start += 1
                    value, end = decoder.raw_decode(text, start)
                    if value == version:
                        return start + 1, end - 1
            index = after
            continue
        index += 1
    return None


def _locate_plugin_marker(text: str) -> tuple[str, int, str] | None:
    """A plugin manifest's marker: the line holding its top-level `"version"`
    value, found by `_plugin_version_span`."""
    span = _plugin_version_span(text)
    if span is None:
        return None
    start, end = span
    return "plugin", text.count("\n", 0, start), text[start:end]


def _locate_marker(path: Path) -> tuple[str, int, str] | None:
    """`(form, line index, semver)` of a file's live version marker, or None
    when it carries none — an absent file, an unreadable one, and one with no
    marker are all "unresolvable", exactly as `_read_frontmatter_semver`
    treats them.

    **A file with a frontmatter block is a frontmatter file, full stop.** The
    block is checked first and is anchored at line 1, so a doctrine page
    *documenting* the `__version__` form cannot have its own marker lost to
    the example in its body. Where the block exists but carries no `version:`
    line, the answer is None rather than whatever a whole-file scan would
    turn up next.

    The other three forms are mutually exclusive by syntax and are scanned in
    one pass, first whole-line match winning. For the shell form that choice
    is the convention itself: a header carries its versions newest-first, so
    the topmost entry is the live one (the same rule
    `core/launchers/cold-read/test_cold_read.py:199-201` reads by).

    **A file that is not decodable UTF-8 is unreadable, so None.** None of
    `MARKER_FORMS` can live in bytes that are not text, and every caller that
    walks a branch's diff meets whatever the branch touched — a PNG, an
    `.icns`, a latin-1 fixture.

    **A file named `plugin.json` is a plugin manifest, read for its top-level
    `"version"` alone** (`_locate_plugin_marker`)."""
    try:
        lines = path.read_text(encoding="utf-8").split("\n")
    except (OSError, UnicodeDecodeError):
        return None
    if path.name == _PLUGIN_MANIFEST_NAME:
        return _locate_plugin_marker("\n".join(lines))
    if lines and lines[0].strip() == "---":
        try:
            frontmatter_end = lines.index("---", 1)
        except ValueError:
            return None
        for index, line in enumerate(lines[1:frontmatter_end], start=1):
            match = _VERSION_LINE.match(line)
            if match:
                return "frontmatter", index, match.group(1)
        return None
    for index, line in enumerate(lines):
        for form, pattern in (
            ("python", _PY_VERSION_LINE),
            ("workflow", _WORKFLOW_VERSION_COMMENT),
            ("shell", _SHELL_VERSION_COMMENT),
        ):
            match = pattern.match(line)
            if match:
                return form, index, match.group(1)
    return None


def _read_marker_semver(path: Path) -> tuple[str, str] | None:
    """`(form, semver)` — `_locate_marker` without the line index, for callers
    that only need to know whether the marker is readable and what it says."""
    located = _locate_marker(path)
    return None if located is None else (located[0], located[2])


def _markers_report(paths: list[str]) -> str:
    """One line per `path`, in the order given — straight out of
    `_locate_marker`, never re-derived. An absent, unreadable, or
    marker-less path is answered `<path>: no marker`, the same shape
    `_locate_marker` already gives all three (its own docstring, `:1035`):
    a question about a file's marker gets an answer, not a traceback."""
    lines = []
    for path in paths:
        located = _locate_marker(Path(path))
        if located is None:
            lines.append(f"{path}: no marker")
        else:
            form, index, semver = located
            # `_locate_marker` returns a 0-BASED index (its docstring: "line
            # index"); the report prints a 1-BASED line, because every other
            # answer a session can compare this against is 1-based — `grep -n`,
            # an editor, and every `path:line` citation in the doctrine. A
            # session that cross-checked the two would otherwise find them
            # disagreeing, which is the two-answers-standing this subcommand
            # exists to remove.
            lines.append(f"{path}: {form} line {index + 1} semver {semver}")
    return "\n".join(lines)


class UnknownRefError(ValueError):
    """`ref` given to `markers --base` does not resolve in the repo — a
    caller mistake (a typo, a deleted branch), not a file's absence. Raised
    by `_locate_marker_at_ref` so its caller prints a clean refusal naming
    `ref` (per `_rev`'s own resolve-or-None shape, `:1218`), never a raw git
    failure surfacing as a traceback."""


def _locate_marker_at_ref(repo: str, path: str, ref: str) -> tuple[str, int, str] | None:
    """`_locate_marker`'s answer for `path` **as it stood at** `ref` — read
    the blob at `<ref>:<path>` to a temp file and resolve it there, through
    `_locate_marker` itself, never re-derived.

    A path that did not exist at `ref` (or whose blob git cannot read there)
    answers `None`, the same "no marker" shape `_locate_marker` gives an
    absent file today (`:1035-1037`) — a question about the past gets an
    answer, not a traceback. `ref` failing to resolve in `repo` at all is
    the different failure `UnknownRefError` names."""
    if _rev(repo, ref) is None:
        raise UnknownRefError(
            f"unknown ref {ref!r} does not resolve in {repo!r} — refusing "
            "to answer a marker as of a commit that isn't there"
        )
    blob = subprocess.run(
        ["git", "-C", repo, "show", f"{ref}:{path}"],
        capture_output=True,
    )
    if blob.returncode != 0:
        return None
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir) / Path(path).name
        tmp_path.write_bytes(blob.stdout)
        return _locate_marker(tmp_path)


def _changed_paths(repo: str, ref: str) -> list[str]:
    """Every path that differs between `ref` and the working tree in `repo`
    — added, modified or deleted since `ref`, repo-relative, in git's own
    order. **Never `--cached`** (unlike the staged-set guard's read at
    `:956`): a branch's own moved marker must be caught whether the edit is
    staged or not, since `git diff <ref>` (no `--cached`) already folds the
    index and the working tree together against an arbitrary ref. An
    untracked file is not part of this set until it is staged — a git
    property, not a choice this function makes."""
    result = subprocess.run(
        ["git", "-C", repo, "diff", ref, "--name-only", "--no-renames", "-z"],
        capture_output=True, text=True,
    )
    return [path for path in result.stdout.split("\0") if path]


def _marker_pair(located: tuple[str, int, str] | None) -> tuple[str, str] | None:
    """`(form, semver)` out of `_locate_marker`'s 3-tuple — the line index
    plays no part in whether a marker "moved"; only the digits and their
    form do."""
    return None if located is None else (located[0], located[2])


def _moved_markers(
    repo: str, ref: str
) -> list[tuple[str, tuple[str, str] | None, tuple[str, str] | None]]:
    """`(path, base, now)` for every path in `_changed_paths(repo, ref)`
    whose marker's `(form, semver)` differs between `ref` and the working
    tree — a file whose content changed but whose marker did not is not
    "moved" and is not included, per `versioning.md` § Bump semantics: the
    marker being edited is what counts, not the file. `ref` not resolving
    raises `UnknownRefError`, checked once here rather than left to
    `_locate_marker_at_ref`'s own per-path check — `_changed_paths` would
    otherwise answer "nothing changed" against a ref git itself refused,
    which is a wrong answer, not a caught one."""
    if _rev(repo, ref) is None:
        raise UnknownRefError(
            f"unknown ref {ref!r} does not resolve in {repo!r} — refusing "
            "to compare markers against a commit that isn't there"
        )
    moved = []
    for path in _changed_paths(repo, ref):
        if not _is_kensaiapp_path(repo, path):
            continue
        base = _marker_pair(_locate_marker_at_ref(repo, path, ref))
        now = _marker_pair(_locate_marker(Path(repo) / path))
        if base != now:
            moved.append((path, base, now))
    return moved


def _semver_or_no_marker(pair: tuple[str, str] | None) -> str:
    return "no marker" if pair is None else pair[1]


def _moved_markers_report(repo: str, ref: str) -> tuple[str, int]:
    """The `markers --base <ref>` report text and exit code — non-zero when
    at least one marker moved, so a gate reads the exit code rather than
    parsing the text (Reached-when 1-2)."""
    moved = _moved_markers(repo, ref)
    if not moved:
        return "", 0
    lines = [
        f"{path}: {_semver_or_no_marker(base)} -> {_semver_or_no_marker(now)}"
        for path, base, now in moved
    ]
    return "\n".join(lines), 1


def _rewritten_marker(
    text: str, form: str, index: int, current: str, new: str, description: str
) -> str:
    """`text` with its marker moved to `new`.

    **Four forms rewrite the line; the shell form prepends a new one above
    it.** That asymmetry is the file format's, not a preference. A shell
    header is a changelog stack — measured on `ce4ecb63`, 19 of the 22 files
    carrying this form hold two or more entries newest-first, and 20 of 22
    topmost lines carry an `— description` naming what *that* version changed.
    Rewriting the digits in place would leave the old note under the new
    number: a tool writing a false sentence into 20 source files, unreviewed,
    at merge time. Prepending is also what the practice already is by hand
    (`cd669155`). The `version:` frontmatter, `__version__`, `// Version:`
    and plugin `"version"` forms are one bare value each with nothing to
    relabel, so they move in place — the plugin's by its span, because one
    line of a manifest can hold more than its version.

    The description is the merge's own `--description`, whitespace-collapsed:
    a comment is one line, and the flag is specified as one line. It is not
    wrapped — how long a change description runs is the merge author's call
    and not this module's (`where_taste_appears.md`)."""
    if form == "plugin":
        span = _plugin_version_span(text)
        assert span is not None and text[span[0]:span[1]] == current
        return text[: span[0]] + new + text[span[1] :]
    lines = text.split("\n")
    if form == "shell":
        note = " ".join(description.split())
        lines.insert(index, f"# Version: {new} — {note}" if note else f"# Version: {new}")
    else:
        lines[index] = lines[index].replace(current, new, 1)
    return "\n".join(lines)


BUMP_LEVELS = ("major", "minor", "patch")


def _bumped(version: str, level: str) -> str:
    """`version` one `level` up, per `versioning.md` § *Bump semantics*."""
    major, minor, patch = (int(part) for part in version.split("."))
    if level == "major":
        return f"{major + 1}.0.0"
    if level == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def _split_bump(spec: str) -> tuple[str, str]:
    path, _, level = spec.rpartition("=")
    return path, level


def _bump_refusal(repo: str, specs: list[str], branch: str | None = None) -> str | None:
    """Every reason a `--bump` cannot be applied, checked BEFORE the merge runs
    so a bad spec never leaves a half-done merge in the target worktree.
    Returns the refusal text, or None when every spec is usable.

    A path absent from the target's tree until the merge brings it — a file the
    branch added or renamed — is read from `branch`, the copy the merge will
    land; `_apply_bumps` runs after the merge, when the file is on disk."""
    problems = []
    for spec in specs:
        path, level = _split_bump(spec)
        if not path or level not in BUMP_LEVELS:
            problems.append(
                f"  {spec} — expected <path>=<level>, level one of {list(BUMP_LEVELS)}"
            )
            continue
        if not _is_kensaiapp_path(repo, _repo_prefix(repo) + path):
            problems.append(
                f"  {spec} — not a kensaiapp artifact: a marker --bump moves "
                "sits under core/, .claude/, skills/ or system/ of an instance "
                "(one holding kensaiapp.md); a product's version is its own "
                "content, set by the change that needs it"
            )
            continue
        marker = _read_marker_semver(Path(repo) / path)
        if marker is None and branch is not None and not (Path(repo) / path).exists():
            try:
                at_branch = _locate_marker_at_ref(repo, path, branch)
            except UnknownRefError:
                at_branch = None  # an unresolvable branch reads as no marker: refused below
            marker = None if at_branch is None else (at_branch[0], at_branch[2])
        if marker is None:
            problems.append(
                f"  {spec} — no version marker in any of the five forms "
                "(frontmatter `version:`, `__version__`, `// Version:`, "
                "`# Version:`, a `plugin.json`'s `\"version\"`): absent file, "
                "or no marker line"
            )
            continue
        _, current = marker
        try:
            _bumped(current, level)
        except ValueError:
            problems.append(f"  {spec} — its version {current!r} is not X.Y.Z")
    if not problems:
        return None
    return "\n".join(
        ["commit_builder: refusing to merge — unusable --bump:", *problems]
    )


def _apply_bumps(repo: str, specs: list[str], description: str = "") -> int:
    """Move each named file's marker one level up and stage it, so the bump
    lands inside the merge commit. Callers validate with `_bump_refusal`
    first; anything unusable here is a bug, not a user error.

    **The rewrite is line-targeted — the line `_locate_marker` matched.** It
    used to be a whole-file `text.replace('"<current>"', …, 1)`, which is
    safe for frontmatter (always the first thing in the file) and wrong for a
    module whose docstring or a constant above the marker quotes the same
    value.

    `description` is the merge's one-line change description, used only by the
    shell form, which prepends rather than rewrites — see
    `_rewritten_marker`."""
    for spec in specs:
        path, level = _split_bump(spec)
        target = Path(repo) / path
        located = _locate_marker(target)
        assert located is not None  # guaranteed by _bump_refusal
        form, index, current = located
        target.write_text(
            _rewritten_marker(
                target.read_text(encoding="utf-8"),
                form, index, current, _bumped(current, level), description,
            ),
            encoding="utf-8",
        )
    return _run_git_add(repo, [path for path, _ in map(_split_bump, specs)])


def _rev(repo: str, rev: str) -> str | None:
    """The commit `rev` resolves to in `repo`, or None when it does not
    resolve. Never raises — an absent `MERGE_HEAD` and a deleted branch are
    both "no answer", which is what every caller here branches on."""
    result = subprocess.run(
        ["git", "-C", repo, "rev-parse", "-q", "--verify", f"{rev}^{{commit}}"],
        capture_output=True, text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def _current_branch(repo: str) -> str | None:
    """The checked-out branch name, or ``None`` for a detached head/failure."""
    result = subprocess.run(
        ["git", "-C", repo, "symbolic-ref", "--quiet", "--short", "HEAD"],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def _merge_base(repo: str, base: str) -> str | None:
    """Where this branch left `base` — the commit its own edits are measured from, or `None` when
    the two share no history (a repo outside the landing convention)."""
    result = subprocess.run(
        ["git", "-C", repo, "merge-base", base, "HEAD"],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 and result.stdout.strip() else None


def _branch_changes(repo: str, ref: str) -> list[tuple[str, str, str | None]]:
    """Return ``(status, old_path, new_path)`` changes with rename identity preserved."""
    result = subprocess.run(
        [
            "git", "-C", repo, "diff", ref, "--name-status", "--find-renames", "-z",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return []
    fields = result.stdout.split("\0")
    changes: list[tuple[str, str, str | None]] = []
    index = 0
    while index < len(fields) and fields[index]:
        status = fields[index]
        index += 1
        if status.startswith(("R", "C")):
            if index + 1 >= len(fields):
                return []
            changes.append((status, fields[index], fields[index + 1]))
            index += 2
        else:
            if index >= len(fields):
                return []
            changes.append((status, fields[index], None))
            index += 1
    return changes


LANDING_BASE = "main"

_COPY_HINT_LINES = (
    "An added file may keep a version other than 1.0.0 only if it is a verbatim copy of a "
    "file in another git repository.",
    "Declare that source with --copied-from <repo> <revision>, and the builder compares each "
    "added file's bytes with the files at that revision.",
)


class CopyCheck(Enum):
    """What `_check_copy` found for one file against the declared copy sources."""

    MATCHED = auto()
    NO_MATCH = auto()
    UNRESOLVABLE = auto()


def _git_bytes(args: list[str], stdin: bytes | None = None) -> bytes | None:
    """Raw stdout of one git call, or ``None`` when git exited non-zero."""
    result = subprocess.run(["git", *args], input=stdin, capture_output=True)
    return result.stdout if result.returncode == 0 else None


def _blob_ids_at(source_repo: str, commit_sha: str) -> set[str] | None:
    """Every blob id in `commit_sha`'s tree, at any path, or ``None`` when the source's path or
    commit does not resolve."""
    listing = _git_bytes(["-C", source_repo, "ls-tree", "-r", "-z", "--full-tree", commit_sha])
    if listing is None:
        return None
    ids: set[str] = set()
    for entry in listing.split(b"\0"):
        metadata, _, _ = entry.partition(b"\t")
        fields = metadata.decode().split()
        if len(fields) == 3 and fields[1] == "blob":
            ids.add(fields[2])
    return ids


def _source_holds(file_bytes: bytes, source_repo: str, commit_sha: str) -> bool | None:
    """Whether a blob at `commit_sha` in `source_repo` equals `file_bytes`; ``None`` when the
    source does not resolve.

    Matches by blob identity first — hashed in the source repository, with `--no-filters` so no
    clean filter or line-ending conversion alters the bytes — then confirms by reading the blob
    back, so the verdict rests on the bytes and never on the hash alone.
    """
    blob_ids = _blob_ids_at(source_repo, commit_sha)
    if blob_ids is None:
        return None
    hashed = _git_bytes(
        ["-C", source_repo, "hash-object", "--no-filters", "--stdin"], stdin=file_bytes
    )
    if hashed is None:
        return None
    blob_id = hashed.decode().strip()
    if blob_id not in blob_ids:
        return False
    return _git_bytes(["-C", source_repo, "cat-file", "blob", blob_id]) == file_bytes


def _check_copy(
    file_bytes: bytes, copy_sources: Sequence[tuple[str, str]]
) -> tuple[CopyCheck, tuple[str, str] | None]:
    """Judge a file's bytes against the declared `(source_repo, commit_sha)` pairs.

    A file passes on any source it matches, even when another declared source does not resolve.
    Otherwise a source that did not resolve is reported with the verdict, since a file that
    matched nothing the builder could read was not compared at all rather than found different.
    """
    unresolved: tuple[str, str] | None = None
    for source in copy_sources:
        held = _source_holds(file_bytes, *source)
        if held:
            return CopyCheck.MATCHED, None
        if held is None and unresolved is None:
            unresolved = source
    if unresolved is not None:
        return CopyCheck.UNRESOLVABLE, unresolved
    return CopyCheck.NO_MATCH, None


def _staged_bytes(repo: str, path: str) -> bytes | None:
    """The bytes `path` carries in the index — what the commit lands — or ``None`` when the index
    holds no blob for it."""
    return _git_bytes(["-C", repo, "cat-file", "blob", f":{path}"])


def _added_file_violation(
    path: str, version: str, file_bytes: bytes | None, copy_sources: Sequence[tuple[str, str]]
) -> str | None:
    """The refusal line for an added file above ``1.0.0``, or ``None`` when its bytes equal a
    file at a declared source. `file_bytes` are the bytes the commit carries; ``None`` (nothing
    staged to compare) never matches."""
    line = f"  {path}: new artifact starts at 1.0.0, found {version}"
    if not copy_sources:
        return line
    if file_bytes is None:
        return f"{line}, and no declared source holds a file with the same bytes"
    verdict, unresolved = _check_copy(file_bytes, copy_sources)
    if verdict is CopyCheck.MATCHED:
        return None
    if verdict is CopyCheck.UNRESOLVABLE and unresolved is not None:
        source_repo, source_commit = unresolved
        return (
            f"{line}, and the declared source {source_repo} at {source_commit} "
            "no longer resolves, so the bytes could not be compared"
        )
    return f"{line}, and no declared source holds a file with the same bytes"


def _branch_marker_refusal(
    repo: str, base: str = LANDING_BASE, copy_sources: Sequence[tuple[str, str]] = ()
) -> str | None:
    """Refuse branch-local marker edits while permitting new ``1.0.0`` artifacts and verified
    verbatim copies.

    The landing commit owns version movement.  A feature branch may change an
    existing artifact's content, rename it with its marker intact, or add a new
    versioned artifact at its creation version — or add a file at another
    version when its bytes equal a file at one of `copy_sources`, the
    ``(source_repo, commit_sha)`` pairs declared with ``--copied-from``.
    Deleting an artifact is not a marker edit to a surviving file and has no
    value for a landing bump to rewrite, so deletion is outside this guard.

    Repositories without a local ``main`` ref are outside Kensaiapp's landing
    convention and remain usable by the generic commit builder. A path that is
    not one of kensaiapp's own artifacts (`_is_kensaiapp_path`) — a product's
    files, in its own repository or under an instance's ``products/`` — is
    outside it too, whatever its version line says.
    """
    branch = _current_branch(repo)
    if branch == base or _rev(repo, base) is None:
        return None

    # Judge what the BRANCH changed, not how it differs from `base`'s tip. A branch falls behind
    # `base` the moment another session lands anything, and a bump among that is `base`'s own
    # movement rather than this branch's edit — read against the tip, it refused every commit on a
    # live branch, empty pause commits included, until the branch was rebased (2026-09-22: seven
    # rebases inside one walk). The merge base is where this branch's own edits begin.
    against = _merge_base(repo, base) or base

    violations: list[str] = []
    added_file_refused = False
    for status, old_path, new_path in _branch_changes(repo, against):
        kind = status[0]
        if kind == "D":
            continue
        if not any(
            _is_kensaiapp_path(repo, str(p)) for p in (old_path, new_path) if p
        ):
            continue
        if kind == "R":
            before = _marker_pair(_locate_marker_at_ref(repo, old_path, against))
            after = _read_marker_semver(Path(repo) / str(new_path))
            if before != after:
                violations.append(
                    f"  {old_path} -> {new_path}: "
                    f"{_semver_or_no_marker(before)} -> {_semver_or_no_marker(after)}"
                )
            continue

        path = str(new_path or old_path)
        after = _read_marker_semver(Path(repo) / path)
        if kind in {"A", "C"}:
            if after is not None and after[1] != "1.0.0":
                # The staged blob, not the working file: it is what the commit lands.
                violation = _added_file_violation(
                    path, after[1], _staged_bytes(repo, path), copy_sources
                )
                if violation is not None:
                    violations.append(violation)
                    added_file_refused = True
            continue

        before = _marker_pair(_locate_marker_at_ref(repo, old_path, against))
        if before != after:
            violations.append(
                f"  {path}: {_semver_or_no_marker(before)} -> "
                f"{_semver_or_no_marker(after)}"
            )

    if not violations:
        return None
    branch_name = branch or "detached HEAD"
    return "\n".join([
        "commit_builder: refusing to commit — version markers move only in the "
        f"landing commit on {base}.",
        f"Branch {branch_name!r} carries marker changes against {base}:",
        *violations,
        "Restore existing markers to their landing-branch values; create new "
        "versioned artifacts at 1.0.0. Apply approved bumps with merge --bump.",
        *(_COPY_HINT_LINES if added_file_refused else ()),
    ])


def _copy_source_key(branch: str) -> str:
    """The per-branch git config key holding the branch's declared copy sources. Git drops the
    ``branch.<name>`` section when the branch is deleted, and every worktree of the repository
    shares it."""
    return f"branch.{branch}.kensaiappCopySource"


def _declared_copy_sources(repo: str, branch: str | None) -> list[tuple[str, str]]:
    """The ``(source_repo, commit_sha)`` pairs declared against `branch`; empty on a detached
    head. Each entry is stored ``<sha> <abs repo>``, the sha first so a path holding spaces
    survives a split on the first space."""
    if branch is None:
        return []
    stored = _git_bytes(["-C", repo, "config", "--get-all", _copy_source_key(branch)])
    if stored is None:
        return []
    pairs: list[tuple[str, str]] = []
    for entry in stored.decode().splitlines():
        commit_sha, _, source_repo = entry.partition(" ")
        pairs.append((source_repo, commit_sha))
    return pairs


def _record_copy_sources(repo: str, branch: str, sources: Sequence[tuple[str, str]]) -> None:
    """Record each pair against `branch`, once — a pair already recorded adds nothing."""
    recorded = _declared_copy_sources(repo, branch)
    for source_repo, commit_sha in sources:
        if (source_repo, commit_sha) in recorded:
            continue
        subprocess.run(
            ["git", "-C", repo, "config", "--add", _copy_source_key(branch),
             f"{commit_sha} {source_repo}"],
            check=True,
        )
        recorded.append((source_repo, commit_sha))


def _copy_declaration_refusal(reason_lines: Sequence[str], ways_out: str) -> str:
    return "\n".join([
        *reason_lines,
        "Nothing was staged and nothing was recorded.",
        f"Ways out: {ways_out}",
    ])


def _copy_unresolvable_refusal(repo_arg: str, revision: str, reason: str, ways_out: str) -> str:
    return _copy_declaration_refusal(
        [
            "commit_builder: refusing to commit — "
            f"--copied-from '{repo_arg}' '{revision}' does not resolve.",
            reason,
        ],
        ways_out,
    )


def _resolve_copy_declaration(
    repo: str, declared: Sequence[Sequence[str]]
) -> tuple[list[tuple[str, str]], str | None]:
    """Resolve each ``--copied-from <repo> <revision>`` pair to an absolute repository path and
    the full commit sha, or the refusal text for the first thing that cannot be declared.

    A declaration needs a branch to live on that the marker guard also judges: a detached head
    has none, and the guard does not run on the landing branch.
    """
    branch = _current_branch(repo)
    if branch is None:
        return [], _copy_declaration_refusal(
            [
                "commit_builder: refusing to commit — --copied-from needs a branch, "
                "and HEAD is detached.",
                "A declaration is recorded against the checked-out branch, so with no branch "
                "it would apply to no commit.",
            ],
            "check out the branch that will carry the copy, then run the command again.",
        )
    if branch == LANDING_BASE:
        return [], _copy_declaration_refusal(
            [
                f"commit_builder: refusing to commit — --copied-from is declared on {branch}.",
                "The marker guard does not run on main, so a declaration there would change "
                "nothing.",
            ],
            "drop --copied-from, because commits on main are not checked against it, or make "
            "the copy on a feature branch and declare the source there.",
        )
    resolved: list[tuple[str, str]] = []
    for repo_arg, revision in declared:
        source_repo = str(Path(repo_arg).resolve())
        if _git_bytes(["-C", source_repo, "rev-parse", "--git-dir"]) is None:
            return [], _copy_unresolvable_refusal(
                repo_arg, revision, f"'{repo_arg}' is not a git repository.",
                "check the path, or give the path of the repository the file was copied from.",
            )
        commit_sha = _rev(source_repo, revision)
        if commit_sha is None:
            return [], _copy_unresolvable_refusal(
                repo_arg, revision, f"'{revision}' names no commit in '{repo_arg}'.",
                "check the revision is spelled correctly and exists in that repository.",
            )
        resolved.append((source_repo, commit_sha))
    return resolved, None


def _merge_in_progress(repo: str) -> bool:
    """Whether `repo` is mid-merge — `MERGE_HEAD` resolves. True after a
    `git merge --no-commit` that conflicted (or that succeeded but was left
    uncommitted); false otherwise, including when a merge failed for a
    reason that never touched the working tree (an unknown branch, for
    instance). Consulted so a conflicted `--bump` merge can be *resumed* by
    re-running the identical `commit_builder.py merge` command, rather than
    re-attempting a merge git will itself refuse ("you have not concluded
    your merge").

    It answers about the *repository*, never about this invocation — it
    cannot tell a merge this command started from one someone else left
    behind, which is why the resume path checks `MERGE_HEAD` against the
    branch it was asked to merge before finishing anything."""
    return _rev(repo, "MERGE_HEAD") is not None


def _foreign_merge_refusal(repo: str, branch: str, merge_head: str) -> str:
    """Why a merge already in progress will not be resumed by a command that
    names a different branch."""
    found = subprocess.run(
        ["git", "-C", repo, "log", "-1", "--format=%h %s", merge_head],
        capture_output=True, text=True,
    ).stdout.strip() or merge_head
    return "\n".join([
        f"commit_builder: refusing to resume — the merge already in progress "
        f"is not `{branch}`.",
        f"  MERGE_HEAD is {found}",
        f"Finishing it under this command would land a merge commit whose "
        f"subject names `{branch}` while its second parent is that commit, "
        f"and `{branch}` would not be merged at all. The `commit-msg` hook "
        "cannot catch that: the trailer format would be valid and only the "
        "content false.",
        "Ways out: finish the merge in progress with the command that started "
        "it, or `git merge --abort` and re-run this one.",
    ])


# Rolling the bump back, rather than the obvious alternative of skipping a
# bump already applied: `versioning.md` § Bump semantics rules that one out
# outright — "Do not make the landing commit's bump idempotent
# (bump-unless-already-bumped): it would absorb exactly the deviation that
# must surface." So bump-once has to come from control flow. `_apply_bumps`
# reads whatever version the file currently holds, so a bump left applied by
# a run that did not land is bumped *again* by the next run, and the marker
# ends two levels up silently — the wrong number this mechanism exists to
# prevent.
def _bump_and_commit(
    repo: str, message: str, bumps: list[str], description: str = ""
) -> int:
    """Apply the bumps and land the merge commit as one unit: a bump exists
    on disk only inside a commit that landed. If the commit is refused — a
    premature resume with paths still unmerged, a `pre-commit` hook, anything
    — every bumped file is written back as it was found and re-staged."""
    before = {
        path: (Path(repo) / path).read_text(encoding="utf-8")
        for path, _ in map(_split_bump, bumps)
    }
    rc = _apply_bumps(repo, bumps, description)
    if rc == 0:
        rc = _run_git_commit(repo, message)
    if rc != 0:
        for path, text in before.items():
            (Path(repo) / path).write_text(text, encoding="utf-8")
        _run_git_add(repo, list(before))
    return rc


_CONFLICT_RESUME_HINT = (
    "commit_builder: merge conflict — the merge is left in progress, on\n"
    "purpose (this module never resolves a conflict; that is a human\n"
    "judgement). To finish it:\n"
    "  1. Resolve the conflicts in the working tree.\n"
    "  2. `git add` the resolved paths.\n"
    "  3. Re-run this exact commit_builder.py merge command again (same\n"
    "     --bump and all) — it will detect the merge already in progress,\n"
    "     apply the bump, and land the merge commit.\n"
    "Do not finish it with a plain `git commit` or `git merge --continue`:\n"
    "neither carries the bump this merge was asked to apply, and neither\n"
    "writes the canonical merge trailer format this module owns."
)


def _run_git_merge(
    repo: str, branch: str, message: str, bumps: list[str] | None = None,
    description: str = "",
) -> int:
    """`git merge --no-ff`. With `bumps`, the merge is taken in two phases —
    `--no-commit`, apply the version bumps, then commit — so the bump lands
    *inside* the merge commit. It has to: `tobiishi-seal` requires that nothing
    commits to main after the merge, and §Versioning requires the commit that
    lands the edit to carry the bump. Without `bumps` the one-shot merge is
    unchanged.

    A conflict on the two-phase path is a non-zero return code from the
    `--no-commit` merge, same as any other failure — but unlike the one-shot
    path (whose `-m message` is preserved by git itself in `MERGE_MSG` for a
    later `git commit --no-edit --cleanup=strip` to pick up — `--cleanup=strip`
    because git appends its own `# Conflicts:` block to `MERGE_MSG`, and the
    commit-msg hook then refuses the amend that would remove it, having lost
    `MERGE_HEAD` and read the result as an ordinary commit missing `Role:`),
    `--no-commit` records no message anywhere,
    so bailing here used to strand the caller with no bump and no way to
    finish through this module. This resumes instead: a call that finds
    `MERGE_HEAD` already resolving goes straight to bumping and committing —
    the identical command, re-run once the caller has resolved and staged the
    conflict by hand.

    Two things bound that resume, because `MERGE_HEAD` describes the
    *repository* and not this invocation. It is only resumed when
    `MERGE_HEAD` is the branch this command names, so a merge someone else
    left behind is refused rather than finished under a subject that would
    misname it. And the bump is applied and committed as one unit
    (`_bump_and_commit`), so a resume that does not land leaves the version
    marker exactly where it found it and the next re-run bumps once, not
    twice."""
    if not bumps:
        return subprocess.run(
            ["git", "-C", repo, "merge", "--no-ff", branch, "-m", message]
        ).returncode

    merge_head = _rev(repo, "MERGE_HEAD")
    if merge_head is not None:
        if _rev(repo, branch) != merge_head:
            print(_foreign_merge_refusal(repo, branch, merge_head), file=sys.stderr)
            return 1
        return _bump_and_commit(repo, message, bumps, description)

    rc = subprocess.run(
        ["git", "-C", repo, "merge", "--no-ff", "--no-commit", branch]
    ).returncode
    if rc != 0:
        if _merge_in_progress(repo):
            print(_CONFLICT_RESUME_HINT, file=sys.stderr)
        return rc
    return _bump_and_commit(repo, message, bumps, description)


# ── the `advance` op — a branch takes a named ref's advance ────────────────
# A `--no-ff` merge of `--from <ref>`'s commit into the checked-out branch,
# authorized by the branch's own actor (`_advance_authorizer_for`, above).
# Two-phase like the `--bump` path of `_run_git_merge`: `--no-commit` first,
# then a plain `git commit -F` with the built message, so a conflict re-run is
# the identical command. Unlike `merge`, this runs neither the staged-set
# guard (`_staged_set_guard_refusal`, `commit`-only) nor `_branch_marker_refusal`
# (`commit`-only too) — the merge commits the advance itself, and any version
# markers it brings in are `main`'s, not the branch's own edit.

def _is_ancestor(repo: str, ancestor: str, descendant: str) -> bool:
    """Whether `ancestor` is `descendant` itself or an ancestor of it — `git
    merge-base --is-ancestor`, exit 0 meaning yes. Git treats a commit as its
    own ancestor for this check, so equality needs no separate comparison."""
    return subprocess.run(
        ["git", "-C", repo, "merge-base", "--is-ancestor", ancestor, descendant],
        capture_output=True,
    ).returncode == 0


def _short_sha(repo: str, rev: str) -> str:
    """`rev`'s abbreviated form, for the nothing-to-take message —
    `git rev-parse --short`."""
    result = subprocess.run(
        ["git", "-C", repo, "rev-parse", "--short", rev],
        capture_output=True, text=True,
    )
    return result.stdout.strip()


def _advance_detached_head_refusal() -> str:
    return "\n".join([
        "commit_builder: refusing to advance — HEAD is detached.",
        "Ways out: check out the branch that should take the advance.",
    ])


def _advance_self_ref_refusal(branch: str, from_ref: str) -> str:
    return "\n".join([
        f"commit_builder: refusing to advance — the checked-out branch {branch!r} is "
        "the ref itself.",
        "Ways out: name a --from ref other than the branch being advanced.",
    ])


def _advance_unresolvable_ref_refusal(from_ref: str) -> str:
    return "\n".join([
        f"commit_builder: refusing to advance — {from_ref!r} does not resolve to a commit.",
        "Ways out: check the ref is spelled correctly and exists in this repo.",
    ])


def _advance_staged_refusal(staged_paths: list[str]) -> str:
    lines = ["commit_builder: refusing to advance — the index holds staged changes:"]
    lines.extend(f"  {path}" for path in staged_paths)
    lines.append(
        "Ways out: commit or unstage them first — an advance must not carry another "
        "session's staged work into the merge commit."
    )
    return "\n".join(lines)


def _advance_foreign_merge_refusal(repo: str, from_ref: str, merge_head: str) -> str:
    """Why a merge already in progress will not be resumed as this advance —
    `_foreign_merge_refusal`'s sibling, for the ref-ancestry test `advance`
    resumes on rather than a named-branch match."""
    found = subprocess.run(
        ["git", "-C", repo, "log", "-1", "--format=%h %s", merge_head],
        capture_output=True, text=True,
    ).stdout.strip() or merge_head
    return "\n".join([
        "commit_builder: refusing to resume — the merge already in progress does not "
        f"take {from_ref!r}'s advance.",
        f"  MERGE_HEAD is {found}",
        "Ways out: finish the merge in progress with the command that started it, or "
        "`git merge --abort` and re-run this advance.",
    ])


_ADVANCE_CONFLICT_RESUME_HINT = (
    "commit_builder: merge conflict — the merge is left in progress, on\n"
    "purpose (this module never resolves a conflict; that is a human\n"
    "judgement). To finish it:\n"
    "  1. Resolve the conflicts in the working tree.\n"
    "  2. `git add` the resolved paths.\n"
    "  3. Re-run this exact commit_builder.py advance command again — it\n"
    "     will detect the merge already in progress and land the advance\n"
    "     commit.\n"
    "Do not finish it with a plain `git commit` or `git merge --continue`:\n"
    "neither writes the canonical advance trailer format this module owns."
)


_BODY_FILE_NOT_STAGED = "Nothing was staged and no commit was made."


def _body_file_conflict_refusal(path: str) -> str:
    return "\n".join([
        "commit_builder: refusing to commit — --body and --body-file were both given.",
        "A commit takes its body from one of the two, so the builder will not guess which one "
        "you meant.",
        f"{_BODY_FILE_NOT_STAGED} The body file '{path}' is left in place.",
        'Ways out: pass only one of the two. An empty --body "" still counts as given.',
    ])


def _body_file_missing_refusal(path: str) -> str:
    return "\n".join([
        f"commit_builder: refusing to commit — the body file '{path}' does not exist.",
        _BODY_FILE_NOT_STAGED,
        "Ways out: check the path given to --body-file. The builder removes a body file once "
        "its commit lands, so if this path was already used for a commit, write the body to a "
        "new file from mktemp.",
    ])


def _body_file_unreadable_refusal(path: str, reason: str) -> str:
    return "\n".join([
        f"commit_builder: refusing to commit — the body file '{path}' cannot be read: "
        f"{reason}.",
        f"{_BODY_FILE_NOT_STAGED} The body file is left in place.",
        "Ways out: make the file readable as text, or write the body to a new file from mktemp.",
    ])


def _body_file_not_removed_notice(path: str, reason: str) -> str:
    return "\n".join([
        f"commit_builder: the commit landed, but the body file '{path}' could not be removed: "
        f"{reason}.",
        "Remove it by hand. It holds the body of the commit that just landed and is not needed "
        "again.",
    ])


def _read_body_file(path: str) -> str:
    """The file's text, read as UTF-8 with no newline conversion: a `\\r\\n` inside the body
    reaches the message as written, which `Path.read_text` would turn into `\\n`."""
    with open(path, encoding="utf-8", newline="") as handle:
        return handle.read()


def _body_from_file(
    path: str, read_body_file: Callable[[str], str]
) -> tuple[str | None, str | None]:
    """`(body, None)` for a readable file, `(None, refusal)` for one that is missing or cannot be
    read. The body is the text with its trailing newline characters removed and nothing else."""
    try:
        return read_body_file(path).rstrip("\r\n"), None
    except FileNotFoundError:
        return None, _body_file_missing_refusal(path)
    except (OSError, UnicodeDecodeError) as error:
        reason = error.strerror if isinstance(error, OSError) and error.strerror else str(error)
        return None, _body_file_unreadable_refusal(path, reason)


def _remove_body_file(path: str) -> None:
    """Delete the body file after its commit landed. The commit stands whatever happens here, so
    a failed removal is a notice on stderr and never a changed exit status."""
    try:
        os.remove(path)
    except OSError as error:
        print(_body_file_not_removed_notice(path, error.strerror or str(error)), file=sys.stderr)


_CLOSING_MARKER_PHRASE = "implementation complete"
_NO_GATE_ENVIRONMENT = "(the gate run printed no Environment: line)"
_MARKER_REFUSAL_FIRST_LINE = (
    "commit_builder: refusing to commit — the closing marker does not match this change's "
    "last gate run."
)
_MARKER_WAYS_OUT = (
    "Ways out: take the Environment: line and each failing case id from this change's last gate "
    "run, then commit again. If the body was read from a file, check that this run wrote it. A "
    "body another change left behind carries that change's lines, not this one's."
)


def _declared_pairs(
    record: record_declarations.ParsedRecord, field: record_declarations.Field
) -> list[tuple[str, str]]:
    """`(line as written, line with its emphasis and whitespace removed)` for each line of the
    parsed record that declares `field`, in body order — the form the refusal's helpers take."""
    return [(line.raw, line.text) for line in record.read(field)]


def _failing_case_id(stripped_line: str) -> str:
    """The text after `Failing:`, trimmed, up to the line's last ` — ` (the whole remainder when
    there is none), trimmed again."""
    remainder = stripped_line[len(record_declarations.FAILING.prefix):].strip()
    return (remainder.rsplit(" — ", 1)[0] if " — " in remainder else remainder).strip()


_MARKER_WAYS_OUT_SEVERAL = (
    "Ways out: take every Environment: line and each failing case id from this change's last "
    "gate run, then commit again. If the body was read from a file, check that this run wrote "
    "it. A body another change left behind carries that change's lines, not this one's."
)


def _indented(lines) -> list[str]:
    return [f"  {line}" for line in lines]


def _single_environment_blocks(
    environments: list[tuple[str, str]], run: "gate_suite.GateRun"
) -> list[str]:
    """The refusal's environment block for a run that printed no `Environment:` line or one."""
    printed = run.environment_lines[0] if run.environment_lines else None
    gate_line = printed if printed is not None else _NO_GATE_ENVIRONMENT
    if not environments:
        return ["The marker has no Environment: line. The gate run printed:", f"  {gate_line}"]
    differing = [raw for raw, stripped in environments if stripped != printed]
    if not differing:
        return []
    return [
        "The marker's Environment: line differs from the one the gate run printed.",
        *(f"  marker:   {raw}" for raw in differing),
        f"  gate run: {gate_line}",
    ]


def _several_environment_blocks(
    environments: list[tuple[str, str]], run: "gate_suite.GateRun"
) -> list[str]:
    """The refusal's environment blocks for a run of several containers: the marker's declared
    lines against the run's as sets — order and repetition are not compared — naming each line
    the marker lacks, in the run's order, then each it carries that the run did not print, in the
    marker's order and as the marker writes it, each once."""
    printed = list(dict.fromkeys(run.environment_lines))
    if not environments:
        return [f"The marker has no Environment: line. The gate run printed these "
                f"{len(printed)}:", *_indented(printed)]
    declared = {stripped for _, stripped in environments}
    missing = [line for line in printed if line not in declared]
    extra = list(dict.fromkeys(raw for raw, stripped in environments if stripped not in printed))
    blocks: list[str] = []
    if missing:
        blocks += ["These Environment: lines from the gate run are missing from the marker:",
                   *_indented(missing)]
    if extra:
        blocks += ["These Environment: lines in the marker are not ones the gate run printed:",
                   *_indented(extra)]
    return blocks


def _closing_marker_refusal(
    body: str, run: "gate_suite.GateRun", body_file: str | None
) -> str | None:
    """The refusal for a closing marker whose `Environment:` or `Failing:` lines contradict the
    gate run, naming every failing check, or None when it matches. Judged before anything is
    staged; `Suite:` and the completeness of the `Failing:` lines are not judged. A run of two or
    more containers is judged as a whole set of lines; a run of none or one keeps its
    single-line judgement and wording."""
    several = len(run.environment_lines) > 1
    record = record_declarations.parse(body)
    environments = _declared_pairs(record, record_declarations.ENVIRONMENT)
    blocks = (_several_environment_blocks if several else _single_environment_blocks)(
        environments, run)

    failing = _declared_pairs(record, record_declarations.FAILING)
    if failing and run.status == 0:
        blocks += [
            "The gate run exited 0, so the marker must carry no Failing: line. It carries:",
            *(f"  {raw}" for raw, _ in failing),
        ]
    elif failing:
        printed = run.stdout + run.stderr
        absent = [(raw, _failing_case_id(stripped)) for raw, stripped in failing]
        absent = [(raw, case) for raw, case in absent if not case or case not in printed]
        if absent:
            blocks.append("These Failing: lines name a case that appears nowhere in the gate "
                          "run's output:")
            for raw, case in absent:
                blocks += [f"  {raw}", f"    case id looked for: {case}"]

    if not blocks:
        return None
    return "\n".join([
        _MARKER_REFUSAL_FIRST_LINE,
        *blocks,
        "Nothing was staged and no commit was made. HEAD and the index are as they were.",
        *([f"The body file '{body_file}' is left in place."] if body_file is not None else []),
        _MARKER_WAYS_OUT_SEVERAL if several else _MARKER_WAYS_OUT,
    ])


def _marker_gate_run(repo: str, records) -> "gate_suite.GateRun | None":
    """This change's last gate run: the one recorded for `repo`'s work tree root and the branch
    it is on, or None when there is none (and none for a detached head)."""
    branch = _current_branch(repo)
    if branch is None:
        return None
    return records.latest(str(_work_tree_root(repo)), branch)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="commit_builder.py",
        description=(
            "Assemble a canonical commit or merge message (commit trailers in "
            "canonical order per core/doctrine/governance/commit_format.md; the "
            "merge format is defined by this module) and run the git op."
        ),
    )
    parser.add_argument(
        "--repo", default=".", help="repo to run the git op in (default: cwd)"
    )

    subparsers = parser.add_subparsers(dest="op", required=True)

    commit_parser = subparsers.add_parser("commit", help="assemble + run a git commit")
    commit_parser.add_argument("--subject", required=True)
    # `--body` has no default text: an explicit empty `--body ""` is a body given, which
    # `--body-file` may not accompany, and an omitted one is the empty body.
    commit_parser.add_argument("--body")
    commit_parser.add_argument(
        "--body-file",
        help=(
            "read the commit body from this file instead of --body: its text with the trailing "
            "newlines removed, every other character as the file holds it. The builder removes "
            "the file once the commit lands and leaves it in place on every refusal, failed "
            "staging or rejected commit. Make the path with mktemp in the run that writes the "
            "body; never a fixed or shared name. Mutually exclusive with --body."
        ),
    )
    # Exactly one of --actor (workflow: derive Role: from the agent_type) or
    # --role (interactive: the posture-supplied Role: value, used verbatim).
    identity = commit_parser.add_mutually_exclusive_group(required=True)
    identity.add_argument(
        "--actor",
        help="the caller's own agent_type; mapped through AGENT_ROLE to derive Role:",
    )
    identity.add_argument(
        "--role",
        help=(
            "the Role: value verbatim — for an interactive caller with no "
            "subagent identity to derive from (supplied from its own posture)"
        ),
    )
    commit_parser.add_argument(
        "--directional",
        required=True,
        help=(
            "the full Shukuba:/Agari:/Michi: line, already resolved by the "
            "caller. A referent that IS present (a project name, a Way slug, "
            "a station slug) is resolved against --repo's own journey and "
            "refused if it does not exist; none and Michi's aside: carry no "
            "referent and are never checked, and a Shukuba:/Agari: line with "
            "progress: or aside: where the name belongs is refused"
        ),
    )
    commit_parser.add_argument("--surface", required=True)
    commit_parser.add_argument("--co-authored-by")
    commit_parser.add_argument(
        "--reasoning-effort", choices=REASONING_EFFORT_LEVELS,
        help="resolved runtime reasoning effort; never inferred by the builder",
    )
    commit_parser.add_argument(
        "--claude-session",
        help=(
            "URL of the session that produced this commit; placed after Reasoning-Effort: "
            "when present, otherwise after Co-Authored-By:. Optional — omit it and no line "
            "is written."
        ),
    )
    commit_parser.add_argument(
        "--skill",
        help=(
            "name the producing skill that authored this commit's output, so "
            "Skill-Version: records what ran. Explicit-only: the trailer is "
            "stamped iff this flag is passed — omit it for a skill-less commit "
            "(a --role hand-authoring, a bare --actor bookkeeping commit), "
            "which correctly carries no line. Resolved against the instance "
            "repo (where the skill source lives), never --repo."
        ),
    )
    commit_parser.add_argument(
        "--prompt",
        help=(
            "name the prompt this session read to produce the output, so "
            "Prompt-Version: records what it followed — the sibling of "
            "--skill, for output a prompt produced with no skill around it. "
            "Takes the bare NAME (pm_right_size), resolved to "
            "core/prompts/<name>.md in the instance repo, or <skill>/<prompt> "
            "(nemawashi-pick/thin), resolved to that skill's "
            "prompts/<prompt>.md — never a path and "
            "never --repo. Independent of --skill: pass either, both, or "
            "neither. Explicit-only, and omitting it correctly carries no line."
        ),
    )
    commit_parser.add_argument(
        "--workflow",
        help=(
            "name the saved Workflow script that drove this run, so "
            "Workflow-Version: records what held the loop — the third of the "
            "provenance trio, for a capability whose load-bearing half is a "
            "workflow rather than a skill or a prompt. Takes the bare NAME "
            "(sdd-conversation), resolved to .claude/workflows/<name>.js in "
            "the instance repo, never a path and never --repo. Its version is "
            "read from the `// Version:` comment below the meta block, not "
            "from frontmatter, which a workflow does not have. Independent of "
            "--skill and --prompt: pass any subset. Explicit-only, and "
            "omitting it correctly carries no line."
        ),
    )
    commit_parser.add_argument(
        "--rm",
        nargs="*",
        action="extend",
        default=[],
        dest="rm_paths",
        help=(
            "paths to stage for removal via `git -C <repo> rm` before the "
            "commit — e.g. docs/PRD_open_issues.md on the round that finishes "
            "clean. Staged inside the builder (the `-C` form) so the caller "
            "never composes a `cd <repo> && git rm` compound, which would trip "
            "the harness untrusted-hooks guard and halt an autonomous run. "
            "Repeats accumulate (`--rm a --rm b` == `--rm a b`); the "
            "single-flag form stays the documented house style."
        ),
    )
    commit_parser.add_argument(
        "--add",
        nargs="*",
        action="extend",
        default=[],
        dest="add_paths",
        help=(
            "paths to stage via `git -C <repo> add` before the commit — e.g. "
            "docs/PRD.md. Same `-C`-form guard-avoidance as --rm. Repeats "
            "accumulate (`--add a --add b` == `--add a b`); the single-flag "
            "form stays the documented house style."
        ),
    )
    commit_parser.add_argument(
        "--staged",
        nargs="*",
        action="extend",
        default=[],
        dest="staged_paths",
        help=(
            "paths staged OUTSIDE the builder, deliberately (e.g. a `git mv` "
            "rename) — declare both halves of a rename, or a covering "
            "directory prefix. The staged-set guard refuses any staged path "
            "not covered by --add ∪ --rm ∪ --staged; this flag is a "
            "declaration only and stages nothing itself. Repeats accumulate."
        ),
    )
    commit_parser.add_argument(
        "--take-index",
        action="store_true",
        help=(
            "accept the whole index as staged and skip the staged-set guard "
            "entirely, for THIS call — for an interactive session that "
            "staged by hand and cannot usefully enumerate paths. This "
            "waives the check: it restores the pre-guard whole-index "
            "behaviour, and a concurrent session's staged file can be swept "
            "in. Never use this in a skill's or workflow's scripted call — "
            "interactive use only."
        ),
    )
    commit_parser.add_argument(
        "--copied-from",
        nargs=2,
        action="append",
        default=[],
        metavar=("REPO", "REVISION"),
        help=(
            "declare that files this branch adds are verbatim copies of files in the git "
            "repository at REPO, at REVISION. An added file whose version marker is not 1.0.0 "
            "then passes the marker guard when its bytes equal a file at that revision, at any "
            "path there. REVISION is anything REPO resolves to a commit, and it is recorded as "
            "that commit, so a branch named there moving later changes nothing. The declaration "
            "is recorded against the checked-out branch, holds for every later commit on that "
            "branch without repeating the flag, and ends when the branch is deleted. Refused on "
            "main and on a detached HEAD. Repeat the flag to declare more than one source."
        ),
    )
    commit_parser.add_argument(
        "--allow-empty",
        action="store_true",
        help=(
            "make an empty marker commit (nothing staged) — e.g. "
            "development-implementation's closing commit"
        ),
    )

    merge_parser = subparsers.add_parser("merge", help="assemble + run a git merge --no-ff")
    merge_parser.add_argument(
        "--check-only", action="store_true",
        help="validate merge metadata and bumps without any repository effects",
    )
    merge_parser.add_argument("--branch", required=True, help="the branch being merged")
    merge_parser.add_argument("--target-branch", required=True)
    merge_parser.add_argument("--description", required=True, help="one-line change description")
    merge_parser.add_argument(
        "--branch-commits",
        nargs="*",
        action="extend",
        default=[],
        help=(
            "each branch commit line (git log <target>..<branch> --oneline); "
            "the builder prefixes each with '-> '. Repeats accumulate "
            "(`--branch-commits a --branch-commits b` == `--branch-commits a b`)."
        ),
    )
    # Exactly one of --actor (an agent: derive the authorizer from MERGE_AUTHORIZER) or
    # --authorizer (interactive: the human-gated authorizer, verbatim but validated). Mirrors the
    # commit path's --actor/--role split, which the merge path did not have.
    merge_identity = merge_parser.add_mutually_exclusive_group(required=True)
    merge_identity.add_argument(
        "--authorizer",
        help=(
            "the Merge-Authorized: value for an INTERACTIVE, human-gated merge, with no subagent "
            f"identity to derive from. Allowed: {sorted(INTERACTIVE_MERGE_AUTHORIZERS)}"
        ),
    )
    merge_identity.add_argument(
        "--actor",
        help="the merge actor; mapped through MERGE_AUTHORIZER to derive the Merge-Authorized: authorizer",
    )
    merge_parser.add_argument(
        "--merge-context",
        required=True,
        help=(
            "the authorization context after the authorizer, e.g. "
            "'tobiishi-seal <key> (PoC: green suite)' — builder emits "
            "'Merge-Authorized: <authorizer> — <merge-context>'"
        ),
    )
    merge_parser.add_argument(
        "--bump",
        action="extend",
        nargs="*",
        default=[],
        dest="bump_specs",
        metavar="PATH=LEVEL",
        help=(
            "bump a file's version marker one level (major|minor|patch) and "
            "land it INSIDE the merge commit — e.g. "
            "core/doctrine/setup/kensaiapp_structure.md=minor. All five forms "
            "`versioning.md` names are moved: a frontmatter `version:`, a "
            "Python `__version__`, a workflow `// Version:`, a plugin "
            "manifest's `\"version\"` and a shell "
            "`# Version:` header (which gains a new entry above the current "
            "one, carrying --description, rather than being rewritten in "
            "place). Per `versioning.md` §Bump semantics a branch never edits "
            "a version marker; the commit that lands the edit on main sets "
            "the number, and for branch work that commit is this merge. "
            "Repeats accumulate. An unusable spec refuses before the merge "
            "runs."
        ),
    )
    merge_parser.add_argument("--surface", required=True)
    merge_parser.add_argument("--co-authored-by")
    merge_parser.add_argument(
        "--reasoning-effort", choices=REASONING_EFFORT_LEVELS,
        help="resolved runtime reasoning effort; never inferred by the builder",
    )
    merge_parser.add_argument(
        "--claude-session",
        help=(
            "URL of the session that made this merge; placed after Reasoning-Effort: when "
            "present, otherwise after Co-Authored-By:. Optional — omit it and no line is "
            "written."
        ),
    )

    advance_parser = subparsers.add_parser(
        "advance",
        help=(
            "merge --from <ref>'s commit into the checked-out branch as a --no-ff merge "
            "authorized by the branch's own actor — a branch taking main's advance"
        ),
    )
    advance_parser.add_argument(
        "--from",
        required=True,
        dest="from_ref",
        help=(
            "the ref whose commit is merged into the checked-out branch. No default — "
            "never assumed to be main."
        ),
    )
    # Exactly one of --actor (any commit actor; mapped through AGENT_ROLE directly, never
    # MERGE_AUTHORIZER — an advance lands nothing on main) or --authorizer (interactive: the
    # same closed INTERACTIVE_MERGE_AUTHORIZERS set the merge path uses).
    advance_identity = advance_parser.add_mutually_exclusive_group(required=True)
    advance_identity.add_argument(
        "--actor",
        help=(
            "the caller's own agent_type; mapped through AGENT_ROLE to derive "
            "Merge-Authorized: — any commit actor may authorize an advance"
        ),
    )
    advance_identity.add_argument(
        "--authorizer",
        help=(
            "the Merge-Authorized: value for an INTERACTIVE, human-gated advance, with no "
            f"subagent identity to derive from. Allowed: {sorted(INTERACTIVE_MERGE_AUTHORIZERS)}"
        ),
    )
    advance_parser.add_argument("--surface", required=True)
    advance_parser.add_argument("--co-authored-by")
    advance_parser.add_argument(
        "--reasoning-effort", choices=REASONING_EFFORT_LEVELS,
        help="resolved runtime reasoning effort; never inferred by the builder",
    )
    advance_parser.add_argument(
        "--claude-session",
        help=(
            "URL of the session that made this advance; placed after Reasoning-Effort: "
            "when present, otherwise after Co-Authored-By:. Optional — omit it and no line "
            "is written."
        ),
    )

    check_parser = subparsers.add_parser(
        "check-directional",
        help="judge a --directional line as commit would, and commit nothing",
    )
    check_parser.add_argument(
        "--directional",
        required=True,
        help="the full Shukuba:/Agari:/Michi: line a later commit will carry. Exits 0 when "
             "commit would take it, else prints commit's refusal and exits 1 — for a caller "
             "that commits only after an effect it cannot undo, such as the seal's product merge",
    )

    markers_parser = subparsers.add_parser(
        "markers",
        help="print each path's version marker (form, line, semver), out of _locate_marker",
    )
    markers_parser.add_argument(
        "paths",
        nargs="*",
        help="one or more file paths to resolve a marker for, in the order to report them. "
             "Omit when --base is given — that mode discovers the changed set itself",
    )
    markers_parser.add_argument(
        "--base",
        help="a ref — walk the files that differ between it and the working tree and name "
             "every one whose version marker moved (gained, lost, or changed semver), "
             "exiting non-zero when at least one did. A clean comparison prints nothing "
             "and exits 0, so a gate reads the exit code rather than the text. Mutually "
             "exclusive with explicit paths, which this mode discovers on its own.",
    )

    return parser


def main(
    argv: list[str] | None = None,
    *,
    read_body_file: Callable[[str], str] = _read_body_file,
    gate_run_records=None,
) -> int:
    args = _build_arg_parser().parse_args(argv)

    if args.op == "commit":
        # The body is settled before anything is staged or recorded, so a refusal about it leaves
        # the index, HEAD and the body file exactly as they were.
        body = args.body or ""
        if args.body_file is not None:
            if args.body is not None:
                print(_body_file_conflict_refusal(args.body_file), file=sys.stderr)
                return 1
            body, body_refusal = _body_from_file(args.body_file, read_body_file)
            if body_refusal is not None:
                print(body_refusal, file=sys.stderr)
                return 1
        try:
            skill_version = resolve_skill_version(
                str(instance_repo_root()), args.skill
            )
            prompt_version = resolve_prompt_version(
                str(instance_repo_root()), args.prompt
            )
            workflow_version = resolve_workflow_version(
                str(instance_repo_root()), args.workflow
            )
            message = build_message(
                "commit",
                subject=args.subject,
                body=body,
                actor=args.actor,
                role=args.role,
                directional=args.directional,
                surface=args.surface,
                co_authored_by=args.co_authored_by,
                reasoning_effort=args.reasoning_effort,
                claude_session=args.claude_session,
                skill_version=skill_version,
                prompt_version=prompt_version,
                workflow_version=workflow_version,
            )
        except UnknownActorError as exc:
            print(f"commit_builder: {exc}", file=sys.stderr)
            return 1
        # Before anything is staged, same as UnknownActorError above: a
        # refusal here must leave the index and the working tree exactly as
        # it found them. Runs unconditionally — --take-index waives only the
        # staged-set guard below, never this check.
        directional_refusal = _directional_refusal(args.repo, args.directional)
        if directional_refusal is not None:
            print(directional_refusal, file=sys.stderr)
            return 1
        # A closing marker is held to the gate run made for this change, before the copy
        # declaration is recorded or anything is staged — --take-index waives nothing here. With
        # no gate run on record, or any other subject, the commit goes on as it always did.
        if _CLOSING_MARKER_PHRASE in args.subject:
            records = (gate_run_records if gate_run_records is not None
                       else gate_suite.default_run_records())
            run = _marker_gate_run(args.repo, records)
            marker_refusal = (_closing_marker_refusal(body, run, args.body_file)
                              if run is not None else None)
            if marker_refusal is not None:
                print(marker_refusal, file=sys.stderr)
                return 1
        # Same rule as the directional check: a declaration that cannot be made leaves the index
        # untouched and records nothing. A declaration recorded before a LATER refusal (the
        # staged-set or marker guard) stays — it only ever lets through bytes the guard compares.
        branch = _current_branch(args.repo)
        if args.copied_from:
            declared_sources, declaration_refusal = _resolve_copy_declaration(
                args.repo, args.copied_from
            )
            if declaration_refusal is not None:
                print(declaration_refusal, file=sys.stderr)
                return 1
            assert branch is not None  # guaranteed by _resolve_copy_declaration
            _record_copy_sources(args.repo, branch, declared_sources)
        # Stage inside the builder, via `git -C` — rm before add so a path
        # can't be re-added by a broad `add` after its removal. Bail on the
        # first non-zero so a staging failure never yields a partial commit.
        rc = _run_git_rm(args.repo, args.rm_paths)
        if rc != 0:
            return rc
        rc = _run_git_add(args.repo, args.add_paths)
        if rc != 0:
            return rc
        if not args.take_index:
            refusal = _staged_set_guard_refusal(
                args.repo, args.add_paths, args.rm_paths, args.staged_paths
            )
            if refusal is not None:
                print(refusal, file=sys.stderr)
                return 1
        marker_refusal = _branch_marker_refusal(
            args.repo, copy_sources=_declared_copy_sources(args.repo, branch)
        )
        if marker_refusal is not None:
            print(marker_refusal, file=sys.stderr)
            return 1
        committed = _run_git_commit(args.repo, message, allow_empty=args.allow_empty)
        if committed == 0 and args.body_file is not None:
            _remove_body_file(args.body_file)
        return committed

    if args.op == "check-directional":
        refusal = _directional_refusal(args.repo, args.directional)
        if refusal is not None:
            print(refusal, file=sys.stderr)
            return 1
        return 0

    if args.op == "markers":
        if args.base is not None:
            if args.paths:
                print(
                    "commit_builder: refusing — markers --base takes no explicit "
                    "paths; it discovers the changed set itself from the diff "
                    "against --base",
                    file=sys.stderr,
                )
                return 1
            try:
                report, exit_code = _moved_markers_report(args.repo, args.base)
            except UnknownRefError as exc:
                print(f"commit_builder: {exc}", file=sys.stderr)
                return 1
            if report:
                print(report)
            return exit_code
        if not args.paths:
            print(
                "commit_builder: markers needs --base <ref> or at least one path",
                file=sys.stderr,
            )
            return 1
        print(_markers_report(args.paths))
        return 0

    if args.op == "advance":
        branch = _current_branch(args.repo)
        if branch is None:
            print(_advance_detached_head_refusal(), file=sys.stderr)
            return 1
        if branch == args.from_ref:
            print(_advance_self_ref_refusal(branch, args.from_ref), file=sys.stderr)
            return 1
        taken = _rev(args.repo, args.from_ref)
        if taken is None:
            print(_advance_unresolvable_ref_refusal(args.from_ref), file=sys.stderr)
            return 1

        # A resume is recognised by MERGE_HEAD being `<ref>`'s commit or an ancestor of it —
        # `<ref>` may have advanced further while the conflict was open. Anything else is a
        # foreign merge in progress and is refused untouched.
        merge_head = _rev(args.repo, "MERGE_HEAD")
        if merge_head is not None:
            if not _is_ancestor(args.repo, merge_head, taken):
                print(
                    _advance_foreign_merge_refusal(args.repo, args.from_ref, merge_head),
                    file=sys.stderr,
                )
                return 1
            taken_sha = merge_head
        else:
            # The staged-index and nothing-to-take checks apply only to a fresh advance — a
            # resume's staged paths are the conflict's own resolution, not foreign work.
            staged = _read_staged_paths(args.repo)
            if staged:
                print(_advance_staged_refusal(staged), file=sys.stderr)
                return 1
            if _is_ancestor(args.repo, taken, "HEAD"):
                short = _short_sha(args.repo, taken)
                print(
                    f"commit_builder: {branch} already holds {args.from_ref} ({short}) "
                    "— nothing to take"
                )
                return 0
            taken_sha = taken

        # Resolved before any git write (the merge --no-commit below), so an unknown actor
        # or authorizer leaves HEAD, the index, and the working tree exactly as found.
        try:
            message = build_message(
                "advance",
                actor=args.actor,
                authorizer=args.authorizer,
                branch=branch,
                from_ref=args.from_ref,
                taken_sha=taken_sha,
                surface=args.surface,
                co_authored_by=args.co_authored_by,
                reasoning_effort=args.reasoning_effort,
                claude_session=args.claude_session,
            )
        except UnknownActorError as exc:
            print(f"commit_builder: {exc}", file=sys.stderr)
            return 1

        if merge_head is None:
            rc = subprocess.run(
                ["git", "-C", args.repo, "merge", "--no-ff", "--no-commit", taken]
            ).returncode
            if rc != 0:
                if _merge_in_progress(args.repo):
                    print(_ADVANCE_CONFLICT_RESUME_HINT, file=sys.stderr)
                return rc

        return _run_git_commit(args.repo, message)

    try:
        message = build_message(
            "merge",
            actor=args.actor,
            authorizer=args.authorizer,
            branch=args.branch,
            target_branch=args.target_branch,
            description=args.description,
            branch_commits=args.branch_commits,
            merge_context=args.merge_context,
            surface=args.surface,
            co_authored_by=args.co_authored_by,
            reasoning_effort=args.reasoning_effort,
            claude_session=args.claude_session,
        )
    except ValueError as exc:
        print(f"commit_builder: {exc}", file=sys.stderr)
        return 1
    refusal = _bump_refusal(args.repo, args.bump_specs, args.branch)
    if refusal is not None:
        print(refusal, file=sys.stderr)
        return 1
    if args.check_only:
        return 0
    return _run_git_merge(
        args.repo, args.branch, message, args.bump_specs, args.description
    )


if __name__ == "__main__":
    sys.exit(main())
