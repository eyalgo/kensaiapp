#!/usr/bin/env python3
"""chain_development.py — the change pipeline walked as a chain of step launchers, and the
same pipeline entered two steps earlier at the journey moves that open a station and a change.

WHY THIS EXISTS
    This engine walks the change pipeline deterministically: one detached `claude --print` run per
    step (or another provider's — § THE PROVIDER), each
    started through `<CORE>/launchers/skill/launcher.sh` from that skill's own `launcher.md`, and
    each started only when the previous run has ended AND its artifact is on disk. No model
    decides what runs next. The 2026-09-11 ruling that fenced the earlier Workflow-driven run and
    every step skill off is spent (the owner, 2026-09-18, and before that 2026-09-15), so a step
    skill is edited on its merits.

WHY IT READS THE DISK AND NOT A MESSAGE
    A detached run returns nothing to its launcher, so the only record of a step is what it left:
    the folder artifacts `<CORE>/doctrine/flow/folder_state_handoff.md` § State is derived, not
    tracked names, the developer's closing marker commit, each auditor's branch, and the sealed
    folder under `trail/`. A missing artifact halts unless the developer can resume a pause or
    use its one unexplained-marker recovery. A new or revised `halt_report.md` stops that recovery;
    only development-specs, development-design (when no reading of a conflicting spec holds),
    tobiishi-seal, development-content and, for its three halts, the developer write one — and
    this engine, once, for a content step whose verdict is missing.

WHY IT STANDS BESIDE `chain.py` RATHER THAN EXTENDING IT
    `chain.py` walks documents: its registry, its cycle and its report classification are all a
    document's, it waits on one run at a time, and its command check refuses the skill launcher's
    extra arguments. This engine borrows its generic ports and changes nothing in it.

THE TWO TABLES, AND WHY THEY ARE BOTH HERE
    `DEVELOPMENT_STEPS` is the pipeline `chain-development` walks. `CHANGE_STEPS` is the same
    eight behind `shukuba-open` and `tobiishi-open` and ahead of `shukuba-refine`. It is the walk
    `chain-change` enters, which needs no station and no change request to already be there. When
    the sealed change serves a station, the walk does not end until the route has been re-read
    after the seal. When it serves none, the walk ends `sealed` at the seal. `--steps` says which a
    start is, and a caller composes neither: both are literals here, the way
    `chain-development/launcher.sh` already said its own was. They differ by two steps at the front
    and agree everywhere after, so a second engine would be a third copy of the state store, the
    live-walk refusal, the launch environment and the shim write.

    Three things the second table changes for every walk. The KEY is no longer a start-time fact: a
    `CHANGE_STEPS` walk begins with none, and `_settle` reads it off the disk the moment the
    `change` step lands — `_resolve_key` states why the TABLE, never the disk, decides whether an
    absent one is legitimate. And the walk's NAME is on its state rather than a module constant,
    because the shim, the log, the telemetry tag and every message the owner reads have to say
    which of two walks they came from. And a SEALED change is no longer always the end of a walk. A
    sealed change serves a station when a commit it landed carries a `Shukuba:` trailer, or when a
    station file names its key, whether that station is open, closed or parked. Those are the two
    marks `shukuba-refine` reads to find a unit's station, and the walk counts nothing else. An open
    station that does not name the key does not make the change serve it. A change walk whose sealed
    change serves a station goes on to `refine`. One whose sealed change serves none ends `sealed`
    at the seal, because the refine would find no station and stop without a report. A change walk
    started on a project whose last unit is sealed, not yet refined and serving a station carries
    that unit's key and enters at `refine`, while a station is still open. A unit that serves no
    station is owed no refine, so the start carries no key and enters at the first step whose
    evidence is missing. `_resolve_key` and `DiskReader.resume_index` state how.

THE CONTENT STEP
    `content` runs the Content Editor on a change that publishes text and is passed, with no
    launch, on one that does not. Which it is lies in one declared line of `change_design.md`,
    `Publishes text:`, stamped by the architect, never by the seat the step runs
    (`RunsWhen`, `DiskReader.run_verdict`). The gate is `_gate_lets_through`, in `_launch_step`,
    the one door `_start` and `_after` share. A line that says neither `yes` nor `no` halts the
    walk before any launch, with a `halt_report.md` the engine writes itself — the one place it
    writes one — and moves aside again once the verdict is settled, so the delivery's clean-tree
    check never meets it. A change already past the step is never entered there (`entry_step`).

THE END HOOK
    `--on-end <command>` is an optional command a start carries on the walk's state and `_end`
    runs once, after the ended state is saved, with the end (`sealed` or `halted`) appended. It is
    how `chain-change` reaches `build-idea` when a walk ends without either engine importing the
    other. The state carries it because the run that ends a walk is a fresh process handed only a
    state path. A hook that fails is one message to the owner and never a change to the end.

THE CONTEXT CAP
    `--context-cap <tokens>` (default `DEFAULT_CONTEXT_CAP`) is the context past which a developer
    run is told to pause. It is kept on the state as `context_cap`, so a walk resumed from its state
    file keeps the cap it started with, and `_launch_run` hands it to the implementation step alone
    as `KENSAIAPP_CONTEXT_CAP` — the variable `.claude/hooks/context_cap.py` reads. Every other
    step has it removed from its environment, because the engine's own environment is the
    previous run's.

THE PROVIDER
    Each launch goes to the provider the walk was forced onto, else the one
    the instance's `.providers.toml` names for its step (`steps.<id>`), read through the
    `ProviderFiles` this engine is given at the instance root the walk is for; the rule is
    `core/tools/providers.py`'s, and this module holds no
    provider of its own. An unforced walk checks every step of its own table at `--describe` and
    at start, so a missing entry, an unknown value or an unreadable file refuses the walk before
    anything launches, naming what is wrong. Each launch then reads the file again, and a launch
    the file can no longer answer halts the walk there, naming the entry; the audit fan-out reads
    once for its four runs. `--provider` is the force, and a forced walk never reads the file;
    it is kept on the state as `forced_provider`, so every later step of the walk and its
    on-end hook carry it. `_launch_run` sets `KENSAIAPP_AGENT_PROVIDER` on every launch rather than
    letting one inherit it, for the context cap's reason: the engine's own environment is the
    previous run's. An unforced walk's on-end hook has the variable removed, because the chain
    launchers a hook may reach read it as a force.

A PAUSE IS NOT AN END
    A developer run past its cap finishes the task it is on and stops on a pause commit
    (`developer: <key> — implementation paused after task <N>`) instead of the closing marker.
    The step is still not done — `marker_commit` reads only the marker phrase — so `_settle`
    reads the pause (`DiskReader.paused_after`) where it would otherwise halt on a missing marker
    and relaunches the step through `entry_step` and `_launch_run`, with `N` after the key so the
    launch prompt tells the fresh run where to start. The last pause's `N` is kept on the state
    (`paused_after`), and a pause that is not after a later task than that one halts: nothing
    else bounds how often a run may pause, and a run that stops making progress would otherwise
    be relaunched for ever.

    A pause is read only where it ended the run: while it is the newest developer commit on the
    instance branch and, for a product in its own repo, no developer commit on the product
    branch was authored after it. A pause with developer work above it is history — the
    relaunched run went past it — so reading it would relaunch after a task the branch has
    passed, or halt that run as making no progress. The run is read as a bare end instead.

    A developer run that ends bare, with neither a closing marker nor a pause read that way,
    gets one recovery (`_recover_missing_marker`): relaunched from the first unfinished task,
    where a start would begin (`DiskReader.resume_after`), and halted on the missing marker if it
    ends bare again. A run the watcher reports as `failed` — a provider error, or a process that
    vanished — is resumed once from its newest landed task commit instead. A second failure
    halts.

THE PRODUCT CHECKOUT
    `_launch_run` reads the product checkout — the lines `git status --porcelain
    --untracked-files=all` prints for the walk's `product_path`, the instance root when that is
    empty, the reading the seal's preflight makes — and keeps them on that run's `pending` entry.
    Every launch and relaunch takes its own, so a run is compared with the checkout it found.
    When the run's end reaches `_advance`, before the gated/audit split and so ahead of every
    recovery, the checkout is read again. A line present now and absent at launch halts the walk
    at the run's step, an audit run included; a checkout read at launch and unreadable at the end
    halts it the same way with its own reason. Nothing is relaunched or resumed over the dirt: no
    pause relaunch, no failure resume, no missing-marker recovery. A line present at launch is
    never counted against the run. A launch whose checkout could not be read records nothing, and
    a pending run with nothing recorded — every one written before this check included — is not
    checked. The reading, the comparison and both reasons are `product_checkout.py`'s, handed to
    the engine as `checkout`; the engine never writes the checkout.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import traceback
from collections.abc import Iterable
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field, fields
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

import completion_shim
import development_path
import gate_suite
import product_checkout
import providers
import walk_stop
from chain import PROVIDERS, Files, IdSource, Notifier, Processes, run_end_hook, with_provider
from providers import ProviderFiles, ProvidersRefused

__version__ = "3.15.1"


class ChainRefused(Exception):
    """A walk that cannot start from what is on disk. The entry point converts it to a message
    on stderr and to the owner's channel before anything launches."""


class ChainAlreadyWalking(ChainRefused):
    """The project's state file still describes a walk with a run pending — one walk per
    project, because the state file IS that project's walk."""


class Evidence(Enum):
    """What a step leaves behind when it is done — the four shapes a step's output takes."""

    STATION_FILE = "station_file"      # a station at the shukuba root, on main — no key needed
    CHANGE_OPEN = "change_open"        # change_request.md in tobiishi/, on main — the key's source
    CHANGE_FILE = "change_file"        # an artifact in the change folder, on the change branch
    MARKER_COMMIT = "marker_commit"    # the developer's closing marker, on the change branch
    AUDIT_FINDINGS = "audit_findings"  # flow_findings/<step>.md, on that audit's own branch
    SEALED = "sealed"                  # the change folder under trail/, on main
    REFINED = "refined"                # <key>_report.md in the unit's seed folder, on main


@dataclass(frozen=True)
class RunsWhen:
    """The declared line that decides whether a step runs: the first line of `artifact`, on the
    change branch, that starts with `prefix`, read by its first word. `runs` is the word that
    launches the step and `passes` the word that lets the walk go by it with no launch; any other
    word, or no line, settles nothing and halts the walk before the step."""

    artifact: str
    prefix: str
    runs: str
    passes: str


class RunVerdict(Enum):
    """What a step's `RunsWhen` line says: launch it, go by it, or nothing usable."""

    RUN = "run"
    PASS = "pass"
    UNSETTLED = "unsettled"


@dataclass(frozen=True)
class Step:
    """One step of the pipeline. `role` is the agent role responsible for it. The engine hands it
    to each of the step's launches as `INSTRUMENT_RUN_ROLE`, and `run_telemetry.sh` stamps it onto
    that launch's telemetry as `kensai.role` (`core/tools/run_telemetry.sh` § The chain tags). A
    reader never derives it from `skill`.
    `gates` is False for the one step whose absence never stops a walk — `development-audit is
    not a gate` (`skills/kensaiapp-auditor/.claude/skills/development-audit/SKILL.md` § Critical Rules) — and `fans_out_over`
    names the steps that audit runs once per. The provider a step runs on is not the table's:
    the instance's `.providers.toml` names it, under `steps.<id>` (§ THE PROVIDER)."""

    id: str
    skill: str
    role: str
    evidence: Evidence
    artifact: str = ""
    takes_key: bool = True
    gates: bool = True
    fans_out_over: tuple[str, ...] = ()
    declared_prefix: str = ""
    runs_when: RunsWhen | None = None


# The one report whose evidence file carries a declared verdict the chain reads before treating
# the file's mere presence as the step landing (`skills/senior-engineer/.claude/skills/
# development-code-integrity/SKILL.md` § Always write the `code-integrity-report`, § When to
# STOP: both never-omitted lines start with this literal prefix, whatever the outcome).
_INTEGRITY_PREFIX = "Integrity:"
_INTEGRITY_REPORT = "code-integrity-report.md"

# The markdown wrappers a declared line can arrive dressed in. Both bodies the scan below reads are
# markdown written by a model, and every place the skills name a declared line shows it inside
# backticks — so `**Integrity: pass**` is the natural way to write one. A walk was halted
# `missing-integrity` by exactly that, on a green suite the step had just proved (a `chain-change`
# walk, 2026-09-17). The line is undressed before its prefix is matched; what counts as a
# value is not widened by an inch — `Integrity: Pass` and `Integrity: passed` still halt.
_EMPHASIS = "*_`"

# Whether a change publishes text, as `development-design` stamps it in the design's header
# (`skills/architect/.claude/skills/development-design/SKILL.md` § Output): `yes` runs the
# `content` step, `no` passes it, and the verdict is decided upstream of the Content Editor, never
# by it (`core/roles/loaders/content_editor_global.md` § Non-responsibilities).
_PUBLISHES_TEXT = RunsWhen(artifact="change_design.md", prefix="Publishes text:", runs="yes",
                           passes="no")

DEVELOPMENT_STEPS: tuple[Step, ...] = (
    Step("specs", "development-specs", "product-owner", Evidence.CHANGE_FILE, "change_spec.md",
         takes_key=False),
    Step("design", "development-design", "architect", Evidence.CHANGE_FILE, "change_design.md"),
    Step("plan", "development-plan", "tech-lead", Evidence.CHANGE_FILE, "tl_instruction.md"),
    Step("content", "development-content", "content-editor", Evidence.CHANGE_FILE,
         "change_text.md", runs_when=_PUBLISHES_TEXT),
    Step("implementation", "development-implementation", "developer", Evidence.MARKER_COMMIT),
    Step("code-integrity", "development-code-integrity", "senior-engineer", Evidence.CHANGE_FILE,
         _INTEGRITY_REPORT, declared_prefix=_INTEGRITY_PREFIX),
    Step("audit", "development-audit", "kensaiapp-auditor", Evidence.AUDIT_FINDINGS, gates=False,
         fans_out_over=("development-specs", "development-design", "development-plan",
                        "development-content", "development-implementation")),
    Step("seal", "tobiishi-seal", "pm", Evidence.SEALED),
)

# The step each gated skill is, so the audit can leave out a step the change passed: a no-text
# change has no `change_text.md` to audit (`DiskReader.audited`).
_GATED_BY_SKILL = {entry.skill: entry for entry in DEVELOPMENT_STEPS if entry.runs_when}

# `chain-change`'s table: the same pipeline, entered at the two PM moves that `chain-development`
# requires a caller to have made by hand. Both take no key — `station` runs before one exists and
# `change` is what creates it — so both reach the disk through a `ChangeLayout` whose `key` is `""`.
# After the seal it re-reads the project's route through `shukuba-refine`, which takes the sealed
# unit's key (`skills/pm/.claude/skills/shukuba-refine/launcher.md` § Arguments). It does so only
# for a change that serves a station. A change that serves none ends the walk `sealed` at the seal,
# and the `refine` step is never launched for it.
CHANGE_STEPS: tuple[Step, ...] = (
    Step("station", "shukuba-open", "pm", Evidence.STATION_FILE, takes_key=False),
    Step("change", "tobiishi-open", "pm", Evidence.CHANGE_OPEN, takes_key=False),
) + DEVELOPMENT_STEPS + (
    Step("refine", "shukuba-refine", "pm", Evidence.REFINED),
)

# tobiishi-seal's own reading of the developer's record (`tobiishi-seal/SKILL.md` § Step 1): any
# commit in `main..<key>` whose subject says so. The chain reads it no looser than the seal will, so
# a change the chain passes is never one the seal then refuses for its marker — and it also asks the
# subject to name the change's own key (`developer: <key> — implementation complete`,
# `development-implementation/SKILL.md` Step 3), because a branch rebuilt onto a base can carry
# another change's marker ahead of `main`.
_MARKER_SUBJECT = "implementation complete"
# What a developer run past its context cap leaves instead (`development-implementation/SKILL.md`
# Step 2 § Pausing at the context cap): an empty commit whose subject names the last task it
# committed. It never holds `_MARKER_SUBJECT`, so it is not a closing marker.
_PAUSE_SUBJECT = re.compile(r"implementation paused after task (\d+)")
# Every commit a developer run makes opens with its seat (`development-implementation/SKILL.md`,
# its per-task, pause and closing subjects, and the free-form ones a run also makes).
_DEVELOPER_PREFIX = "developer:"
# The closing marker's own never-omitted lines
# (`skills/developer/.claude/skills/development-implementation/SKILL.md` Step 3): the literal prefix
# each one's declaration starts with.
_SUITE_PREFIX = "Suite:"
# A product with no code has no suite. Its project card says so with `Test command: none`
# (`core/templates/project_template.md`), and only then may the marker declare `Suite: none`.
# The whole value must be `none`, with the inline comment cut off first and code or bold markup
# ignored. So `none` written only inside the comment does not count, and neither does a stand-in
# such as `none yet — set once the SDD settles`.
_CARD_TEST_COMMAND = re.compile(r"^\*\*Test command:\*\*(.*)$", re.MULTILINE)
_NO_SUITE = "none"
# The environment a gate's suite ran in (`core/tools/gate_suite.py`): one declared line in the
# closing marker and in a passing integrity report. The kind is the line's first word, and only
# these four are an environment — `unresolved` names a run that never happened. `none` is the
# card's own no-suite answer and passes only where `Suite: none` would (`card_has_no_suite`).
_ENVIRONMENT_PREFIX = "Environment:"
_ENVIRONMENT_KINDS = frozenset({"macos-guest", "container", "owners-mac", _NO_SUITE})
# The language line is `Language resolution:`, or the same words with a parenthesised label
# before the colon. A close after two pauses carried each pause's record under `Language
# resolution (tasks 1 to 3, from <pause SHA>):`, and an exact prefix read that as no record at all,
# halting a finished, green change as missing-language (2026-10-01). The skill now asks
# for one plain heading; this keeps a labelled one from reading as absent.
_LANGUAGE_WORDS = "Language resolution"
_LANGUAGE_HEADING = re.compile(_LANGUAGE_WORDS + r"(?:\s*\([^)]*\))?:")
# The two lines a marker carries when the developer deferred a task it could not land
# (`skills/developer/.claude/skills/development-implementation/SKILL.md` Step 3): `Deferred: task <N> — …` names the
# task, and `Failing: <case id> — task <N>` (or `— no task`) names the task a failing case is in.
_DEFERRED_PREFIX = "Deferred:"
_FAILING_PREFIX = "Failing:"
# The first whole `task <N>` after a line's prefix. `\b` on both sides, so `task 3` never reads a
# `task 30`, and `task x` reads no number at all.
_TASK_TOKEN = re.compile(r"\btask (\d+)\b")
_MAIN = "main"
# A per-task commit's subject: `developer: task <N> <slug>` (or the older `task-<N>`), the number a
# whole token. What follows it is `_landing_suffix`'s to read.
_TASK_COMMIT = re.compile(r"^developer: task[ -](\d+)(?=\s|$)(.*)$")
# The two last ` — ` suffixes that say a per-task commit finished its task. Any other suffix —
# `red`, `deferred`, `green except …`, an older slug after a dash — reads as not landed: a wrong
# "not landed" costs a redo the already-green lane absorbs, and a wrong "landed" skips unfinished
# work (`skills/developer/.claude/skills/test-driven-development/SKILL.md`, the commit forms).
_LANDING_SUFFIXES = frozenset({"green", "refactor"})
_SUFFIX_SEPARATOR = " — "
# The last ` — ` suffix of a per-task red commit
# (`skills/developer/.claude/skills/test-driven-development/SKILL.md`,
# `developer: <slug> — red`, called with the slug `task <N> <slug>`). Exactly this word.
_RED_SUFFIX = "red"
# A heading of one task in `tl_instruction.md`: `### Task <N>: <title>`, the number a whole token.
_TASK_HEADING = re.compile(r"^### Task (\d+)\b", re.MULTILINE)
# Any markdown heading: its `#` run is its level, and what follows the space is its title.
_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
# The two level-4 headings a task's lane is read from (`development-implementation/SKILL.md`
# Step 2). The Behaviours heading is read as a prefix, because the plan writes a parenthetical
# after it — `#### Behaviours to verify (developer adds tests to …)`. The Implement heading is the
# whole word, so `#### Implementation notes` is not it.
_BEHAVIOURS_TITLE = "Behaviours to verify"
_IMPLEMENT_TITLE = re.compile(r"^Implement(?![A-Za-z])")
# The literal `#### Implement` text that routes a task with Behaviours out of the TDD lane and into
# one plain commit (`skills/developer/.claude/skills/development-implementation/SKILL.md:242-258`,
# text `development-plan` is required to write). Matched as a substring of the Implement body, so a
# marker the plan dressed in backticks or bold still reads.
_ONE_COMMIT_MARKERS: tuple[str, ...] = (
    "No spec tests — implement per project layout above.",  # lane (b), no-test structural
    "Verified by review — no test.",  # lane (c), review-verified
    "Tests cannot go red.",  # lane (d), already-green
    "No new tests — TDD under green",  # lane (a), preserving relocation
    "Tests are red at baseline.",  # lane (f), red already on `main`
)
# The developer's note for a TDD-lane task it re-laned to a lane with no red commit of its own, in
# the one line forms `development-implementation/SKILL.md` Step 3 fixes for Developer Review Notes:
# `- Task <N> no red (lane d) — <why a red phase was impossible>, …` (already-green) and
# `- Task <N> red at baseline (lane f) — <the listed tests red before, green after>, …` (its failing
# tests were already on `main`). Read off the line's own start, the number a whole token; the reason
# is everything after the em dash that follows the closing bracket. A qualifier after the lane
# letter, opened by a comma or a semicolon — `(lane d, re-laned)` — is still the note: a developer
# who adds words inside the bracket has written the note, not prose about one (2026-10-12, a
# satellite walk halted missing-red-commit on exactly that line).
_RELANE_NOTE = re.compile(
    r"^- Task (\d+) (?:no red \(lane d(?:[,;][^)]*)?\)"
    r"|red at baseline \(lane f(?:[,;][^)]*)?\))\s*—(.*)$")
_RELANE_NOTE_START = "- Task "
# The largest context, in tokens, a developer run may carry before it is told to pause
# (`.claude/hooks/context_cap.py`). A walk carries its own on the state, so a resumed walk keeps the
# cap it started with; this is what a start with no `--context-cap` records.
DEFAULT_CONTEXT_CAP = 250000
# The environment variable the hook reads. Set for the implementation step alone (`_launch_run`).
_CONTEXT_CAP_VARIABLE = "KENSAIAPP_CONTEXT_CAP"
# The owner's ask to run the gates' suites on their own Mac. Set for the three steps that run a
# card's suite, and only when this walk's owner start carried the ask (`WalkState.gate_owners_mac`).
_GATE_OWNERS_MAC_VARIABLE = "KENSAIAPP_GATE_OWNERS_MAC"
_GATE_CONSUMER_STEPS = frozenset({"implementation", "code-integrity", "seal"})

# The two stops the environment check can end an implementation launch with. The words are
# `change_text.md`'s, section *The walk's decision-owed stop message*.
_DECISION_OWED = (
    "environment-decision-owed — the product owes an environment decision, so implementation "
    "was not launched: {detail}. To go on, record the environment for the product's gates in "
    "its decision files and start the walk again, or start it again with the owner's ask "
    "(--gate-owners-mac).")
_CHECK_UNAVAILABLE = (
    "environment-check-unavailable — implementation was not launched, because the walk cannot "
    "tell whether the product owes an environment decision: {problem}. To go on, correct what "
    "that names and start the walk again.")
_INPUTS_HEADING = "## Gate environment inputs"
_PLAN_FILE = "tl_instruction.md"
_NO_INPUTS_SECTION = 'the change\'s plan has no "Gate environment inputs" section'
_NO_INPUTS_BLOCK = 'the change\'s plan holds no JSON block under "Gate environment inputs"'
_MANY_INPUTS_BLOCKS = ('the change\'s plan holds more than one JSON block under '
                       '"Gate environment inputs"')
# `tobiishi-seal` flips the project's `CONTEXT_PM.md` status to this line when the change lands
# (`skills/pm/.claude/skills/tobiishi-seal/SKILL.md`, the `caller-seal-action` block) — the same line
# `shukuba-refine` reads its default unit off (`SKILL.md` § Input). Matched as a prefix, so a
# date after it still reads.
_SEALED_STATUS = "**Status:** Sealed"
_KEY_TOKEN = re.compile(r"\d{4}-\d{2}-\d{2}_[A-Za-z0-9][A-Za-z0-9-]*")
# Where a seed can sit once its unit is refined: the seedbed root and `unpicked/`, which is where
# `shukuba-refine` lands its report (`SKILL.md` Step 6), and `trail/` and `drop/`, where the
# Principal PM may have moved the seed since.
_SEED_HOMES = ("", "unpicked", "trail", "drop")
# Where a station file sits under `journey/shukuba/`: open at the root, reached in `trail/`, or
# parked — the three homes `shukuba-refine` looks in for the file naming a unit (`SKILL.md` Step 2).
_STATION_HOMES = ("", "trail", "parked")


@dataclass(frozen=True)
class ChangeLayout:
    """Every path one change's walk touches, derived from the key alone — the convention
    `create_change_worktree.py` creates the worktree by: branch `<key>`, path
    `<repo>/.worktrees/<key>`, so every consumer derives it from the key."""

    instance_root: str
    project: str
    key: str

    @property
    def journey(self) -> str:
        return os.path.join(self.instance_root, "system", "projects", self.project, "journey")

    @property
    def tobiishi(self) -> str:
        return os.path.join(self.journey, "tobiishi")

    @property
    def shukuba(self) -> str:
        """The station root. Read before a key exists, so it hangs off the project alone —
        `key` is `""` for every walk that has not reached `tobiishi-open` yet."""
        return os.path.join(self.journey, "shukuba")

    @property
    def nemawashi(self) -> str:
        return os.path.join(self.journey, "nemawashi")

    @property
    def change_rel(self) -> str:
        return f"system/projects/{self.project}/journey/tobiishi/{self.key}"

    @property
    def worktree(self) -> str:
        return os.path.join(self.instance_root, ".worktrees", self.key)

    @property
    def branch_change_folder(self) -> str:
        return os.path.join(self.worktree, self.change_rel)

    @property
    def branch_trail_folder(self) -> str:
        """The change folder on the branch once the seal's `caller-seal-action` has moved it
        under `trail/` — where a seal that halts after the move writes its report."""
        return os.path.join(self.worktree, "system", "projects", self.project, "journey",
                            "tobiishi", "trail", self.key)

    @property
    def main_change_folder(self) -> str:
        return os.path.join(self.tobiishi, self.key)

    @property
    def trail_folder(self) -> str:
        return os.path.join(self.tobiishi, "trail", self.key)

    def audit_branch(self, audited_skill: str) -> str:
        return f"{self.key}__audit-{audited_skill}"

    def findings_path(self, audited_skill: str) -> str:
        return f"{self.change_rel}/flow_findings/{audited_skill}.md"


class DiskReader:
    """Answers what is on disk for one change. Reads only — it launches and writes nothing."""

    def __init__(self, *, files, git):
        self.files = files
        self.git = git

    def open_change_keys(self, instance_root: str, project: str) -> list[str]:
        """Every active change on disk: each folder under `journey/tobiishi/` — `trail/` and
        `drop/` aside — holding a `change_request.md`, the same rule development-specs discovers
        one by. The list, not the one: `is_done` asks whether any exists before a walk has a
        key, and `discover_key` asks for exactly one."""
        tobiishi = ChangeLayout(instance_root, project, "").tobiishi
        return [entry for entry in self.files.list_dir(tobiishi)
                if entry not in ("trail", "drop")
                and self.files.is_file(os.path.join(tobiishi, entry, "change_request.md"))]

    def open_station(self, instance_root: str, project: str) -> str | None:
        """The open station's file name, or `None`. One `<date>_<slug>.md` at the shukuba root is
        the whole of what `shukuba-open` leaves (`shukuba-open/SKILL.md` Step 3a). `README.md` is
        the stamped readme, and `parked/` and `trail/` are where a station goes when it is parked
        or reached — a walk that read any of them as an open station would skip the step that
        opens one."""
        stations = self.open_stations(instance_root, project)
        return stations[0] if stations else None

    def open_stations(self, instance_root: str, project: str) -> list[str]:
        """Every station file name at the shukuba root, sorted, read as `open_station` reads one.
        A root holds one; a caller that acts on a station reads this, so two are never one."""
        shukuba = ChangeLayout(instance_root, project, "").shukuba
        return sorted(entry for entry in self.files.list_dir(shukuba)
                      if entry != "README.md" and entry.endswith(".md")
                      and self.files.is_file(os.path.join(shukuba, entry)))

    def unrefined_sealed_key(self, instance_root: str, project: str) -> str | None:
        """The unit `contexts/CONTEXT_PM.md` names as sealed, when its route has not been refined
        yet and it serves a station — or `None`. The same default `shukuba-refine` takes
        (`SKILL.md` § Input). The unit itself is `sealed_key`'s.

        Owed only while a station is still open at the shukuba root. A seal leaves its station open
        and the refine comes before the close, so a root with no open station means the route has
        moved on. The unit's seed is then usually in `trail/`, where `shukuba-refine` stops without
        a report (`SKILL.md` Step 2). Carrying the key there would halt every later start at
        `refine`.

        Owed only for a unit that serves a station, too. A unit that serves none gives
        `shukuba-refine` no station to find, so its refine would stop without a report as well. For
        such a unit a start carries no key and does not enter at `refine`."""
        if self.open_station(instance_root, project) is None:
            return None
        key = self.sealed_key(instance_root, project)
        if key is None:
            return None
        unit = ChangeLayout(instance_root, project, key)
        if self.refined(unit) or not self.serves_station(unit):
            return None
        return key

    def sealed_key(self, instance_root: str, project: str) -> str | None:
        """The unit `contexts/CONTEXT_PM.md` names as sealed, or `None`: a `Sealed` status and the
        first `<YYYY-MM-DD>_<slug>` it names that resolves to a folder under `tobiishi/trail/` —
        the unit `tobiishi-open` writes first. The context, never the trail's newest folder, so
        the trail's other units are never picked.

        It carries none of the gates `unrefined_sealed_key` adds — no open station, no refine
        owed, no station the unit serves — because a caller that starts from a refined unit
        (`build-idea`, which runs the refine's own report) is exactly the one those gates answer
        `None` for."""
        context = os.path.join(instance_root, "system", "projects", project, "contexts",
                               "CONTEXT_PM.md")
        text = self.files.read_text(context)
        if text is None or not any(line.strip().startswith(_SEALED_STATUS)
                                   for line in text.splitlines()):
            return None
        for token in _KEY_TOKEN.findall(text):
            if self.files.is_dir(ChangeLayout(instance_root, project, token).trail_folder):
                return token
        return None

    def serves_station(self, change: ChangeLayout) -> bool:
        """Whether the sealed unit serves a station: a commit it landed carries a `Shukuba:`
        trailer, or a station file — at the shukuba root, in `trail/` or in `parked/` — names its
        key. The two marks `shukuba-refine` reads, and nothing else; no station is chosen, so
        conflicting or unresolvable marks still answer `True`. An empty key serves none."""
        if not change.key:
            return False
        return (self.git.unit_has_shukuba(change.instance_root, change.key)
                or any(change.key in text for text in self._station_texts(change)))

    def _station_texts(self, change: ChangeLayout) -> Iterable[str]:
        """The text of every station Markdown file in the three station homes. `README.md` and
        anything that is not a Markdown file are left out."""
        for home in _STATION_HOMES:
            folder = os.path.join(change.shukuba, home) if home else change.shukuba
            for entry in self.files.list_dir(folder):
                path = os.path.join(folder, entry)
                if entry != "README.md" and entry.endswith(".md") and self.files.is_file(path):
                    yield self.files.read_text(path) or ""

    def refined(self, change: ChangeLayout) -> bool:
        """Whether `shukuba-refine` has left its report for this unit: `<key>_report.md` in a seed
        folder, wherever that seed now sits (`_SEED_HOMES`)."""
        return self.report_path(change) is not None

    def report_path(self, change: ChangeLayout) -> str | None:
        """Where `shukuba-refine` left this unit's `<key>_report.md`, or `None`: the first seed
        folder, in `_SEED_HOMES` order, that holds it."""
        name = f"{change.key}_report.md"
        for home in _SEED_HOMES:
            folder = os.path.join(change.nemawashi, home) if home else change.nemawashi
            for seed in self.files.list_dir(folder):
                candidate = os.path.join(folder, seed, name)
                if self.files.is_file(candidate):
                    return candidate
        return None

    def discover_key(self, instance_root: str, project: str) -> str:
        """The single active change. Refuses on none and on more than one — the two states a
        walk cannot carry."""
        tobiishi = ChangeLayout(instance_root, project, "").tobiishi
        keys = self.open_change_keys(instance_root, project)
        if not keys:
            raise ChainRefused(f"no active change under {tobiishi} — no folder there holds a "
                               f"change_request.md. Open one with tobiishi-open first.")
        if len(keys) > 1:
            raise ChainRefused(f"more than one active change under {tobiishi}: "
                               f"{', '.join(keys)}. A walk carries exactly one.")
        return keys[0]

    def is_done(self, change: ChangeLayout, step: Step) -> bool:
        if step.evidence is Evidence.STATION_FILE:
            return self.open_station(change.instance_root, change.project) is not None
        if step.evidence is Evidence.CHANGE_OPEN:
            # Any active change means the step landed. More than one is not decided here: the
            # walk needs the key next, and `discover_key` owns that refusal and its wording.
            return bool(self.open_change_keys(change.instance_root, change.project))
        if step.evidence is Evidence.CHANGE_FILE:
            if self.files.is_file(os.path.join(change.branch_change_folder, step.artifact)):
                return True
            # A step the change's own records pass is done with no artifact: that is how a
            # walk's restart, and `describe`, find it behind them.
            return self.run_verdict(change, step) is RunVerdict.PASS
        if step.evidence is Evidence.MARKER_COMMIT:
            return self.marker_commit(change) is not None
        if step.evidence is Evidence.AUDIT_FINDINGS:
            return all(self.audit_done(change, audited) for audited in self.audited(change, step))
        if step.evidence is Evidence.REFINED:
            return self.refined(change)
        return self.files.is_dir(change.trail_folder)

    def run_verdict(self, change: ChangeLayout, step: Step) -> RunVerdict:
        """What `step`'s `RunsWhen` line says, from the change branch's copy of its artifact. A
        step with no such line always runs. The verdict is the value's first word and must be
        exactly the step's `runs` or `passes` word: `Yes` and `maybe` are unsettled, never
        coerced, and a missing file or line is unsettled too."""
        gate = step.runs_when
        if gate is None:
            return RunVerdict.RUN
        word = self._declared_word(change, gate)
        if word == gate.runs:
            return RunVerdict.RUN
        if word == gate.passes:
            return RunVerdict.PASS
        return RunVerdict.UNSETTLED

    def branch_has_halt_report(self, change: ChangeLayout) -> bool:
        """Whether the change branch carries a committed `halt_report.md` in its change folder."""
        return self.git.branch_has_path(change.instance_root, change.key,
                                        f"{change.change_rel}/{_HALT_REPORT}")

    def run_finding(self, change: ChangeLayout, gate: RunsWhen) -> str:
        """What the gate's artifact holds in place of a usable verdict, named for the report and
        the halt reason."""
        body = self.files.read_text(os.path.join(change.branch_change_folder, gate.artifact))
        if body is None:
            return f"no {gate.artifact}"
        declared = self._first_declared_line(body, gate.prefix)
        if declared is None:
            return f'no "{gate.prefix}" line'
        return f'"{declared}", which is neither {gate.runs} nor {gate.passes}'

    def _declared_word(self, change: ChangeLayout, gate: RunsWhen) -> str | None:
        """The first word of the gate line's value, undressed — `None` when the artifact or the
        line is absent, `""` when the line carries no value. The same scan `declared_verdict` and
        `suite_verdict` make, so `**Publishes text:** no` reads as `no`."""
        body = self.files.read_text(os.path.join(change.branch_change_folder, gate.artifact))
        declared = None if body is None else self._first_declared_line(body, gate.prefix)
        if declared is None:
            return None
        value = declared[len(gate.prefix):].strip().strip(_EMPHASIS).split(maxsplit=1)
        return value[0].strip(_EMPHASIS) if value else ""

    def reclosed_after_integrity(self, change: ChangeLayout) -> bool:
        """Whether the developer's newest closing marker is newer than the commit that last wrote
        `code-integrity-report.md` on the branch — a re-close made after integrity's verdict.
        Ordered by every commit in `main..<key>`, newest first, not only the ones whose subject
        names the key — integrity's subject need not name it. A report no commit on the branch
        wrote answers False, so the start keeps re-entering implementation."""
        marker = self.marker_commit(change)
        report = self.git.last_commit_touching(
            change.instance_root, change.key, f"{change.change_rel}/{_INTEGRITY_REPORT}")
        order = [sha for sha, _ in self.git.commits_ahead(change.instance_root, _MAIN, change.key)]
        if marker is None or report not in order:
            return False
        return order.index(marker) < order.index(report)

    def marker_commit(self, change: ChangeLayout) -> str | None:
        for sha, subject in self._own_commits(change):
            if _MARKER_SUBJECT in subject:
                return sha
        return None

    def _own_commits(self, change: ChangeLayout) -> list[tuple[str, str]]:
        """The commits in `main..<key>` whose subject names this change's key — the developer's
        marker and pause subjects both do. Another change's, carried onto the branch by a rebase or
        a merge, is never this change's record."""
        return [(sha, subject)
                for sha, subject in self.git.commits_ahead(change.instance_root, _MAIN, change.key)
                if change.key in subject]

    def paused_after(self, change: ChangeLayout, product_path: str) -> int | None:
        """The `N` of this change's pause, only while that pause is where the developer run ended:
        the newest developer commit on the instance branch, and — for a product in its own repo —
        with no developer commit on the product branch authored after it. `None` otherwise: a
        pause with any developer commit above it, a closing marker's included, is history, and
        the run it ended has been followed by work this read must not skip back over."""
        newest = next(iter(self._developer_commits(change, change.instance_root)), None)
        if newest is None or change.key not in newest[1]:
            return None
        paused = _PAUSE_SUBJECT.search(newest[1])
        if paused is None:
            return None
        repo = self.code_repo(change, product_path)
        if repo != change.instance_root and self._worked_after(change, repo, newest[0]):
            return None
        return int(paused.group(1))

    # Author time, because commits in two repositories have no log order between them and it is
    # the one order both carry. Not `>=`: a task commit and the pause naming it can land in one
    # second, and counting that tie would bury a pause that did end the run.
    def _worked_after(self, change: ChangeLayout, repo: str, pause_sha: str) -> bool:
        """Whether a developer commit in `repo` was authored strictly after the instance pause. A
        tie is not after, and a time git cannot read — the pause's or a commit's — is not after
        either, so the pause stands where the order cannot be read."""
        paused_at = self.git.author_time(change.instance_root, pause_sha)
        if paused_at is None:
            return False
        for sha, _subject in self._developer_commits(change, repo):
            authored_at = self.git.author_time(repo, sha)
            if authored_at is not None and authored_at > paused_at:
                return True
        return False

    def _developer_commits(self, change: ChangeLayout, repo: str) -> list[tuple[str, str]]:
        """This change's developer commits in `repo`'s `main..<key>`, newest first: every subject
        opening `developer:`, except one naming another change's key — carried onto the branch
        by a rebase or a merge, it is never this change's record (`_own_commits`' rule). A subject
        naming no key at all, a per-task commit's, is this change's."""
        return [(sha, subject)
                for sha, subject in self.git.commits_ahead(repo, _MAIN, change.key)
                if subject.startswith(_DEVELOPER_PREFIX)
                and (change.key in subject or not _KEY_TOKEN.search(subject))]

    def resumable_task(self, change: ChangeLayout, product_path: str) -> int | None:
        """The `N` of the newest landed per-task commit, when no closing marker is newer. `None`
        when a marker already owns the resume, or when no task has landed. A task lands the way
        `_landed_tasks` reads it: no ` — ` suffix, or a last suffix of `green` or `refactor`.

        A pause owns nothing here: the one caller asks only once `paused_after` has answered
        `None`, so every pause on the branch is buried under later developer work, and the resume
        passes the newest landed task, never a buried pause's number (CP-184).

        The task commits are read where code commits land — `code_repo`, the repo `resume_after`
        reads too. For a product in its own repo that is not where the marker lands: it is a
        pipeline commit, on the instance branch. Commits in two repositories have no log order
        between them, so there any marker of this change's owns the resume, as a newer one does in
        one repo."""
        repo = self.code_repo(change, product_path)
        # No pause clause, not even a reduced copy of `paused_after`'s rule: that would be a second
        # pause read, and whether a pause ended the run is `paused_after`'s alone to say.
        if repo != change.instance_root:
            if any(_MARKER_SUBJECT in subject for _sha, subject in self._own_commits(change)):
                return None
        for _sha, subject in self.git.commits_ahead(repo, _MAIN, change.key):
            if change.key in subject and _MARKER_SUBJECT in subject:
                return None
            task = _TASK_COMMIT.match(subject)
            if task and self._lands(task.group(2)):
                return int(task.group(1))
        return None

    def resume_after(self, change: ChangeLayout, product_path: str) -> int | None:
        """Where a start at the developer step tells the run to begin: the number of the task
        before the first task of `tl_instruction.md`, in its order, that has no landing commit —
        `None` when that is the instruction's first task, or when the instruction is unreadable or
        lists none. The last task's number when every task has landed."""
        text = self.files.read_text(os.path.join(change.branch_change_folder, "tl_instruction.md"))
        tasks = [int(number) for number in _TASK_HEADING.findall(text or "")]
        if not tasks:
            return None
        landed = self._landed_tasks(self.code_repo(change, product_path), change.key)
        unlanded = next((number for number in tasks if number not in landed), None)
        if unlanded is None:
            return tasks[-1]
        return None if unlanded == tasks[0] else unlanded - 1

    def tdd_lane_tasks(self, change: ChangeLayout) -> list[int] | None:
        """The TDD-lane tasks of the change's own `tl_instruction.md` on the branch, in plan order:
        each `### Task <N>` whose block has a `#### Behaviours to verify` heading and an
        `#### Implement` body carrying none of `_ONE_COMMIT_MARKERS` — lane (e) of
        `development-implementation/SKILL.md` Step 2. A task with no Implement heading, or no
        Behaviours heading, is in no lane and is not returned. `None` when the file cannot be read,
        so a caller can tell an absent plan from one that judges nothing (`[]`)."""
        text = self.files.read_text(os.path.join(change.branch_change_folder, "tl_instruction.md"))
        if text is None:
            return None
        lane: list[int] = []
        for number, block in self._task_blocks(text):
            if number not in lane and self._in_tdd_lane(block):
                lane.append(number)
        return lane

    @staticmethod
    def _task_blocks(text: str) -> list[tuple[int, list[str]]]:
        """Each `### Task <N>` heading with the lines under it, up to the next heading of level 2
        or 3 — so a `## TL Review Notes` after the last task never becomes part of it. Bounded by
        heading level rather than by the next task heading, which is what keeps that trailing
        section out."""
        blocks: list[tuple[int, list[str]]] = []
        current: list[str] | None = None
        for line in text.splitlines():
            heading = _HEADING.match(line)
            if heading and len(heading.group(1)) in (2, 3):
                task = _TASK_HEADING.match(line)
                current = [] if task else None
                if task:
                    blocks.append((int(task.group(1)), current))
                continue
            if current is not None:
                current.append(line)
        return blocks

    @staticmethod
    def _in_tdd_lane(block: list[str]) -> bool:
        """Whether one task block is lane (e): a Behaviours heading anywhere in it, and an Implement
        body — the lines under `#### Implement` up to the next heading of level 4 or higher —
        carrying no one-commit marker."""
        has_behaviours = False
        implement: list[str] | None = None
        in_implement = False
        for line in block:
            heading = _HEADING.match(line)
            if heading and len(heading.group(1)) <= 4:
                in_implement = False
                title = heading.group(2).strip()
                if len(heading.group(1)) == 4 and title.startswith(_BEHAVIOURS_TITLE):
                    has_behaviours = True
                elif (len(heading.group(1)) == 4 and implement is None
                      and _IMPLEMENT_TITLE.match(title)):
                    implement, in_implement = [], True
                continue
            if in_implement:
                implement.append(line)
        if not has_behaviours or implement is None:
            return False
        body = "\n".join(implement)
        return not any(marker in body for marker in _ONE_COMMIT_MARKERS)

    def code_repo(self, change: ChangeLayout, product_path: str) -> str:
        """The repository a change's per-task commits land in: the product's own when it lies
        outside the instance, else the instance's. The one reading both resume questions share,
        and the one `development_path.py` gives an absolute path inside the instance too."""
        # An empty path is the product living in the instance. It is never the repo: `_outside`
        # answers True for `""` through its ValueError branch, and `git -C ""` means "here".
        if product_path and self._outside(product_path, change.instance_root):
            return product_path
        return change.instance_root

    @staticmethod
    def _outside(path: str, root: str) -> bool:
        """Whether `path` lies outside `root`, compared by path component: `/x/inst-other` is
        outside `/x/inst`, which a string-prefix test would call inside. An external product's
        per-task commits are on its own repository's branch of the same name, so that is the repo
        a resume reads; a product inside the instance shares the instance's."""
        path, root = os.path.normpath(path), os.path.normpath(root)
        try:
            return os.path.commonpath([path, root]) != root
        except ValueError:
            return True

    def _landed_tasks(self, repo: str, key: str) -> set[int]:
        landed = set()
        for _sha, subject in self.git.commits_ahead(repo, _MAIN, key):
            task = _TASK_COMMIT.match(subject)
            if task and self._lands(task.group(2)):
                landed.add(int(task.group(1)))
        return landed

    @staticmethod
    def _lands(rest_of_subject: str) -> bool:
        """Whether what follows a per-task subject's number lands the task: no ` — ` suffix, or a
        last suffix that is exactly `green` or `refactor`."""
        suffix = DiskReader._last_suffix(rest_of_subject)
        return suffix is None or suffix in _LANDING_SUFFIXES

    @staticmethod
    def _last_suffix(rest_of_subject: str) -> str | None:
        """The text after a per-task subject's last ` — `, stripped, or `None` when it has none."""
        if _SUFFIX_SEPARATOR not in rest_of_subject:
            return None
        return rest_of_subject.rsplit(_SUFFIX_SEPARATOR, 1)[1].strip()

    def landed_without_red(self, repo: str, key: str, tasks: list[int]) -> list[int]:
        """Those of `tasks`, ascending and each once, that have a landing commit on `repo`'s
        `main..<key>` and no red commit older than their oldest landing (CP-189, CP-191). A task
        with no landing is not returned: a missing landing is another obligation's.

        "Older" is position in the one list `commits_ahead` answers, newest first — never author
        time, which `_worked_after` needs only because it compares two repos, and which would tie a
        red and a green made within one second."""
        # Each task's OLDEST landing and oldest red: the list is newest first, so a later position
        # is an older commit, and each write below keeps the oldest seen so far.
        landing: dict[int, int] = {}
        red: dict[int, int] = {}
        for position, (_sha, subject) in enumerate(self.git.commits_ahead(repo, _MAIN, key)):
            task = _TASK_COMMIT.match(subject)
            if not task:
                continue
            number = int(task.group(1))
            if self._lands(task.group(2)):
                landing[number] = position
            elif self._last_suffix(task.group(2)) == _RED_SUFFIX:
                red[number] = position
        return sorted(number for number in set(tasks)
                      if number in landing and red.get(number, -1) < landing[number])

    def suite_verdict(self, change: ChangeLayout) -> str | None:
        """The closing marker's declared `Suite:` value — `"green"`, `"red"`, `"none"` (passes
        only when `main`'s card reads `Test command: none`, `card_has_no_suite`), or `None` when the marker
        carries no such line at all (or there is no marker yet)."""
        declared = self._declared_line(change, _SUITE_PREFIX)
        if declared is None:
            return None
        # The verdict is the value's FIRST WORD. The developer writes this body by hand and
        # reaches for the evidence — `Suite: green — python3 -m pytest …, 5083 passed` — which an
        # exact read calls no verdict at all and halts a finished change as missing-suite (twice on
        # 2026-09-22). What follows the verdict is the record, and it never changes what was
        # declared: a dressed `red` still halts.
        value = declared[len(_SUITE_PREFIX):].strip().split(maxsplit=1)
        return value[0].strip("*_`") if value else ""

    def marker_environment_kind(self, change: ChangeLayout) -> str | None:
        """The kind of the closing marker's first `Environment:` line, or `None` when it has none
        — the same scan `suite_verdict` makes, so a dressed line declares and a mention does
        not."""
        return self._environment_kind(self._declared_line(change, _ENVIRONMENT_PREFIX))

    def report_environment_kind(self, change: ChangeLayout, step: Step) -> str | None:
        """The kind of the first `Environment:` line in `step`'s own report, or `None`."""
        body = self.files.read_text(os.path.join(change.branch_change_folder, step.artifact))
        return None if body is None else self._environment_kind(
            self._first_declared_line(body, _ENVIRONMENT_PREFIX))

    @staticmethod
    def _environment_kind(declared: str | None) -> str | None:
        """The first word of the declaration's value, case kept — `""` when the line has none."""
        if declared is None:
            return None
        value = declared[len(_ENVIRONMENT_PREFIX):].strip().strip(_EMPHASIS).split(maxsplit=1)
        return value[0].strip(_EMPHASIS) if value else ""

    def card_has_no_suite(self, change: ChangeLayout) -> bool:
        """Whether the project card on `main` declares `Test command: none`. It is `main`'s copy
        and not the branch's: the card is settled on `main`, a branch opened before that carries
        the old value, and a card the developer's own run could edit would let `Suite: none` hide a
        red suite. A card that cannot be read, or that has no such line, has a suite, so
        `Suite: none` never passes by default."""
        card = self.files.read_text(os.path.join(change.instance_root, "system", "projects",
                                                 change.project, "project.md"))
        found = _CARD_TEST_COMMAND.search(card or "")
        if found is None:
            return False
        value = found.group(1).split("<!--", 1)[0].strip().strip("*_`").strip()
        return value.lower() == _NO_SUITE

    def language_resolved(self, change: ChangeLayout) -> bool:
        """Whether the closing marker declares a `Language resolution:` line at all — the
        same line scan `suite_verdict` uses, over the same body, matched by `_LANGUAGE_HEADING`
        so a labelled heading counts as the declaration it is."""
        return any(_LANGUAGE_HEADING.match(line) for line
                   in self._declared_lines_of_marker(change, _LANGUAGE_WORDS))

    def declared_verdict(self, change: ChangeLayout, step: Step) -> str | None:
        """The value of the first line in `step`'s own report that starts with its
        `declared_prefix`, or `None` when the report carries no such line — a step whose
        `declared_prefix` is empty never reports one. Reads the report through the same
        `files.read_text` path `is_done` already checks, scanned by the same line-prefix rule
        `_declared_line` applies to a commit body, so there is only one scan to trust."""
        if not step.declared_prefix:
            return None
        path = os.path.join(change.branch_change_folder, step.artifact)
        body = self.files.read_text(path)
        if body is None:
            return None
        declared = self._first_declared_line(body, step.declared_prefix)
        return None if declared is None else declared[len(step.declared_prefix):].strip()

    def deferrals(self, change: ChangeLayout) -> list[str]:
        """Every `Deferred:` line of the closing marker's body, undressed, in body order — `[]`
        when there is no marker. One line per deferred task, whatever its reason."""
        return self._declared_lines_of_marker(change, _DEFERRED_PREFIX)

    def relaned_tasks(self, change: ChangeLayout) -> set[int]:
        """The tasks the closing marker's body re-lanes: every line in `_RELANE_NOTE`'s form.
        Empty when there is no marker. Read by the note's own line form anywhere in the body rather
        than by locating the `Developer Review Notes` section, which has no fixed end in a marker
        body."""
        relaned = set()
        for line in self._declared_lines_of_marker(change, _RELANE_NOTE_START):
            note = _RELANE_NOTE.match(line)
            # A note with no reason records none, so it re-lanes nothing (CP-190).
            if note and note.group(2).strip().strip(_EMPHASIS).strip():
                relaned.add(int(note.group(1)))
        return relaned

    def failing_cases(self, change: ChangeLayout) -> list[str]:
        """Every `Failing:` line of the closing marker's body, undressed, in body order — `[]`
        when there is no marker. The engine runs no tests, so these lines are the only way the
        marker shows which task a red case belongs to."""
        return self._declared_lines_of_marker(change, _FAILING_PREFIX)

    def _declared_line(self, change: ChangeLayout, prefix: str) -> str | None:
        """The first line of the closing marker's body whose undressed form starts with
        `prefix`, or `None`. Scanned by literal line prefix, never a regex over the whole
        body — a mention inside `Developer Review Notes` elsewhere in the body must not read
        as the declaration."""
        declared = self._declared_lines_of_marker(change, prefix)
        return declared[0] if declared else None

    def _declared_lines_of_marker(self, change: ChangeLayout, prefix: str) -> list[str]:
        sha = self.marker_commit(change)
        if sha is None:
            return []
        return self._declared_lines(self.git.commit_body(change.instance_root, sha), prefix)

    @staticmethod
    def _declared_lines(body: str, prefix: str) -> list[str]:
        """Every line of `body` whose undressed form starts with `prefix`, undressed, in order.
        The one scan `_first_declared_line`, and through it `_declared_line` (a commit body) and
        `declared_verdict` (a report's file text), run — one parser, however many lines a caller
        wants, so the marker's `Suite:` line, the report's `Integrity:` line and the marker's
        `Deferred:` lines all read past the same wrappers.

        It is the undressed line that comes back, and that half carries the fix: callers take the
        value with `declared[len(prefix):].strip()`, so a returned `**Integrity: pass**` would hand
        them `pass**` and halt exactly as the raw line did."""
        undressed = (line.strip().strip(_EMPHASIS).strip() for line in body.splitlines())
        return [line for line in undressed if line.startswith(prefix)]

    @staticmethod
    def _first_declared_line(body: str, prefix: str) -> str | None:
        """The first line `_declared_lines` finds, or `None`."""
        declared = DiskReader._declared_lines(body, prefix)
        return declared[0] if declared else None

    def audited(self, change: ChangeLayout, step: Step) -> tuple[str, ...]:
        """The steps `step` audits on this change: its `fans_out_over`, less a gated step the
        change's own records do not run, which produced nothing to read."""
        return tuple(skill for skill in step.fans_out_over
                     if skill not in _GATED_BY_SKILL
                     or self.run_verdict(change, _GATED_BY_SKILL[skill]) is RunVerdict.RUN)

    def audit_done(self, change: ChangeLayout, audited_skill: str) -> bool:
        return self.git.branch_has_path(change.instance_root, change.audit_branch(audited_skill),
                                        change.findings_path(audited_skill))

    def resume_index(self, change: ChangeLayout, steps: tuple[Step, ...]) -> int:
        """Where the scan for an entry starts: just past the seal when the change is sealed, else
        the first step. A sealed change has left the evidence of every step before the seal
        behind — its change request under `trail/`, its worktree removed — so those steps are
        taken as landed on the seal's word rather than read again and found missing."""
        if change.key:
            for index, candidate in enumerate(steps):
                if candidate.evidence is Evidence.SEALED and self.is_done(change, candidate):
                    return index + 1
        return 0

    def entry_step(self, change: ChangeLayout, steps: tuple[Step, ...]) -> Step | None:
        """The first step from `resume_index` whose evidence is not on disk, or None when the
        walk has nothing left. Recomputed from the disk on every start. `describe` refuses a
        start whose skipped steps — every one from `resume_index` up to this — declared a bad
        verdict, rather than entering here regardless of what they declared."""
        first = self.resume_index(change, steps)
        for position, candidate in enumerate(steps[first:], start=first):
            if self.is_done(change, candidate):
                continue
            # A step the records can skip is never the entry of a change that is already past it:
            # a later gating step on disk says the walk went by, and it resumes where it would
            # have before the step existed (CP-442).
            if candidate.runs_when is not None and any(
                    later.gates and self.is_done(change, later) for later in steps[position + 1:]):
                continue
            return candidate
        return None

    def halt_report(self, change: ChangeLayout) -> str | None:
        """Where a halted step left its report, or None. The change branch first — every step
        past the worktree writes there, and a seal that halts after its folder move writes into
        the moved folder, `trail/<key>/` on the branch (`tobiishi-seal/SKILL.md` § *Where a halt
        writes its report*) — then development-specs' three pre-worktree homes, deepest first
        (`development-specs/SKILL.md` § Outputs)."""
        keyed = (
            os.path.join(change.branch_change_folder, "halt_report.md"),
            os.path.join(change.branch_trail_folder, "halt_report.md"),
            os.path.join(change.main_change_folder, "halt_report.md"),
        ) if change.key else ()
        candidates = keyed + (
            os.path.join(change.tobiishi, "halt_report.md"),
            os.path.join(change.instance_root, "halt_report.md"),
        )
        return next((path for path in candidates if self.files.is_file(path)), None)


    def halt_snapshot(self, change: ChangeLayout) -> dict | None:
        """Identify inherited report bytes without copying their content into chain state.
        Unreadable reports have no snapshot, so they cannot be dismissed as unchanged.
        """
        path = self.halt_report(change)
        text = self.files.read_text(path) if path else None
        if text is None:
            return None
        return {"path": path, "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()}


# --- the walk's own record ------------------------------------------------------------------

STATE_SCHEMA = 1

# Each table's own name — the walk's identity, carried on the state and worn by its shim, its log,
# its telemetry tag and every message the owner reads. A module constant could not say which of two
# walks a message came from.
CHAIN_NAMES: dict[int, str] = {id(DEVELOPMENT_STEPS): "development", id(CHANGE_STEPS): "change"}


class Ended(str, Enum):
    SEALED = "sealed"
    HALTED = "halted"
    STOPPED = walk_stop.STOPPED


@dataclass
class WalkState:
    """Everything a later `--advance` needs, because the completion hook re-enters as a fresh
    process with one run id and one outcome and nothing else."""

    instance_root: str
    product_path: str
    project: str
    core_dir: str
    shim_dir: str
    engine_path: str
    key: str
    walk_id: str
    product_docs: str
    chain_name: str = "development"
    notifier: str = ""
    keep_awake: bool = False
    started_at: str = ""
    pending: dict = field(default_factory=dict)
    audits: dict = field(default_factory=dict)
    history: list = field(default_factory=list)
    suite: str | None = None
    marker: str | None = None
    ended: str | None = None
    ended_reason: str = ""
    reentries: int = 0
    # The command run once when this walk ends, with the end appended (`_run_end_hook`). Defaulted,
    # so a state written before it existed still loads at the same `STATE_SCHEMA`.
    on_end: str = ""
    # Defaulted for the same reason: a state written before the cap existed loads with today's.
    context_cap: int = DEFAULT_CONTEXT_CAP
    # The `N` of the pause the developer step was last relaunched after, or `None` when it has not
    # paused. Defaulted, so an older state file still loads.
    paused_after: int | None = None
    # How many times a `failed` developer run has been resumed from its last task or pause
    # commit. One is the budget; a second failure halts. Defaulted, so an older state file
    # still loads.
    failure_resumes: int = 0
    # One fresh attempt to close an otherwise unexplained missing developer marker.
    # Defaulted so walks persisted before recovery existed remain readable.
    marker_recoveries: int = 0
    # Report inherited at developer launch; absent in older states, which remain conservative.
    developer_halt_before: dict | None = None
    # A restarted developer must supersede the marker it inherited.
    developer_marker_before: str | None = None
    # The marker's `Deferred:` lines, undressed, in the marker's order — what the walk sealed over
    # unfinished. Defaulted, so an older state file still loads.
    deferrals: list = field(default_factory=list)
    # The provider `--provider` forced every step of this walk onto, or empty when each step
    # runs on its own. Defaulted, so an older state file still loads.
    forced_provider: str = ""
    # The owner's ask, made at this walk's start, to run the gates' suites on their own Mac. Only a
    # fresh owner start sets it — no card, product record or inherited variable does — and every
    # later launch of the walk reads it from here. Defaulted, so an older state file still loads.
    gate_owners_mac: bool = False
    schema_version: int = STATE_SCHEMA

    def to_json(self) -> dict:
        return asdict(self)

    @classmethod
    def from_json(cls, data: dict) -> "WalkState":
        """Unknown keys ignored — never `cls(**data)`, which turns a shape difference into a
        crash out of the completion hook."""
        names = {entry.name for entry in fields(cls)}
        return cls(**{name: value for name, value in data.items() if name in names})


class StateStore:
    """The state file behind a seam. A `.tmp` sibling is written whole and then replaced over
    the real path, so no reader ever observes half a file."""

    def __init__(self, files, path: str, chain_name: str = "development"):
        self.files = files
        self.path = os.path.abspath(path)
        # Only so an absence names the walk that has none. The default keeps every caller that
        # builds a store to read one field — the notifier, before the engine exists — unchanged.
        self.chain_name = chain_name

    def raw(self) -> dict:
        text = self.files.read_text(self.path)
        if text is None:
            return {}
        try:
            return json.loads(text)
        except ValueError:
            return {}

    def load(self) -> WalkState:
        data = self.raw()
        if not data:
            raise ChainRefused(f"no {self.chain_name} chain state at {self.path}")
        if data.get("schema_version") != STATE_SCHEMA:
            raise ChainRefused(f"{self.path} was written at state schema "
                               f"{data.get('schema_version')!r}; this engine speaks "
                               f"{STATE_SCHEMA}. Start the chain again through its launcher.")
        return WalkState.from_json(data)

    def save(self, state: WalkState) -> None:
        self.files.make_dirs(os.path.dirname(self.path))
        temporary = f"{self.path}.tmp"
        self.files.write_text(temporary,
                              json.dumps(state.to_json(), indent=2, sort_keys=True) + "\n")
        self.files.replace(temporary, self.path)


@dataclass(frozen=True)
class AdvanceResult:
    acted: bool
    ended: str | None


@dataclass(frozen=True)
class StartPlan:
    """What a start would do: the change it carries, the id of the step it enters at, and the
    provider each step of the walk's table would run on, in table order."""

    key: str
    entry: str
    providers: tuple[tuple[str, str], ...] = ()


# The two hook outcome values (`watch_process.ProcessHookOutcome`, spelled as `watch_agent.py`'s
# `HookOutcome`) that mean the run finished. PRODUCED_NOTHING is one
# of them: the watcher reads it off the instance root's HEAD, which a step committing inside
# `.worktrees/<key>` never moves — so it says nothing about the step, and the disk decides.
_FINISHED = frozenset({"completed", "produced_nothing"})


_HALT_REPORT = "halt_report.md"


def engine_report_marker(step: Step) -> str:
    """The first line of a `halt_report.md` this engine wrote for `step`, and the only thing that
    tells it from a seat's own report: the engine moves a report that starts with it and leaves
    every other one where it is."""
    return f"chain_development — halt at the {step.id} step: no {step.runs_when.prefix} verdict"


def _missing_verdict_report(step: Step, found: str) -> str:
    gate = step.runs_when
    return "\n".join([
        engine_report_marker(step),
        "",
        f"The {step.id} step runs on one declared line in `{gate.artifact}`, and the walk found "
        f"none it can read: {found}.",
        "",
        f"Add one of these lines to the header of `{gate.artifact}`, after `**Behaviour:**`:",
        "",
        f"    **{gate.prefix}** {gate.runs} — <the places the words live>",
        f"    **{gate.prefix}** {gate.passes}",
        "",
        f"The value's first word must be exactly `{gate.runs}` or `{gate.passes}`. Commit the "
        "line on the change branch and start the walk again. The engine moves this report out of "
        "the change folder once the verdict is settled.",
        "",
    ])


def _missing(change: ChangeLayout, step: Step) -> str:
    """What a finished step failed to leave, named the way the owner looks for it."""
    if step.evidence is Evidence.STATION_FILE:
        return f"a station at {change.shukuba}"
    if step.evidence is Evidence.CHANGE_OPEN:
        return f"a folder holding a change_request.md under {change.tobiishi}"
    if step.evidence is Evidence.CHANGE_FILE:
        return step.artifact
    if step.evidence is Evidence.MARKER_COMMIT:
        return f"developer closing marker commit on {change.key}"
    if step.evidence is Evidence.REFINED:
        return f"{change.key}_report.md in a seed folder under {change.nemawashi}"
    return f"trail/{change.key}/ on main"


class EnvironmentCheckUnavailable(Exception):
    """The walk could not carry out the environment check. `str(self)` is the problem, in the
    words the stop message puts after its colon."""


def _gate_inputs_blocks(plan: str) -> tuple[int, list[str]]:
    """How many `## Gate environment inputs` sections the plan holds outside any fence, and the
    body of every fenced block inside them. A section runs to the next heading of any level: the
    plan's task blocks follow it as `### Task` headings, and their fenced hints are not its
    evidence."""
    sections, blocks = 0, []
    in_section, in_fence, current = False, False, None
    for line in plan.splitlines():
        if line.strip().startswith("```"):
            if in_fence and current is not None:
                blocks.append("\n".join(current))
                current = None
            elif not in_fence and in_section:
                current = []
            in_fence = not in_fence
        elif in_fence:
            if current is not None:
                current.append(line)
        elif _HEADING.match(line):
            in_section = line.strip() == _INPUTS_HEADING
            sections += in_section
    return sections, blocks


def _real_contract(change: "ChangeLayout") -> dict:
    return development_path.resolve_from_paths(
        change.worktree, change.project, change.key,
        development_path.GitRepos(development_path.Git()))


def _real_tracked_files(root: str) -> list[str]:
    """The tracked files of the product tree at `root`, one product-relative name each."""
    result = subprocess.run(["git", "-C", root, "ls-files", "-z"], capture_output=True, text=True)
    if result.returncode != 0:
        lines = (result.stderr or "git ls-files failed").strip().splitlines()
        raise OSError(lines[0] if lines else "git ls-files failed")
    return [name for name in result.stdout.split("\0") if name]


class GateEnvironmentCheck:
    """The production environment-check port. It reads the plan's sourced evidence from the
    change's branch, prepares the current path contract, tracked-file inventory and the
    product's committed decision record (read afresh at every ask), and asks
    `gate_suite.check_gate` — which starts no process. Policy stays in the gate tool: this class
    prepares context and reports a check it could not make."""

    def __init__(self, *, files, gate_files=None, contract=_real_contract,
                 tracked_files=_real_tracked_files, record_reader=None):
        self.files = files
        self.gate_files = gate_files if gate_files is not None else gate_suite.ReadOnlyFiles()
        self.contract = contract
        self.tracked_files = tracked_files
        self.record_reader = record_reader if record_reader is not None \
            else gate_suite.GitRecordReader()

    def check(self, change: "ChangeLayout", core_dir: str) -> "gate_suite.CheckResult":
        inputs = self._planned_inputs(change)
        try:
            paths = self.contract(change)
        except development_path.ToolError as error:
            raise EnvironmentCheckUnavailable(
                f"the product's paths cannot be resolved: {error.message}") from None
        try:
            tracked = self.tracked_files(str(gate_suite.product_tree(paths)))
        except OSError as error:
            raise EnvironmentCheckUnavailable(
                f"the product's tracked files cannot be listed: {error}") from None
        try:
            record = gate_suite.read_decision_record(paths, self.record_reader)
            context = gate_suite.CheckContext(
                paths=paths, tracked_files=tuple(tracked), decision_record=record)
            return gate_suite.check_gate(
                worktree=change.worktree, project=change.project, key=change.key, inputs=inputs,
                context=context, files=self.gate_files, core_root=Path(core_dir),
                out=io.StringIO())
        except (gate_suite.GateError, gate_suite.InputError) as error:
            raise EnvironmentCheckUnavailable(
                f"the gate tool could not make the check: {error}") from None

    def _planned_inputs(self, change: "ChangeLayout") -> object:
        plan = self.files.read_text(os.path.join(change.branch_change_folder, _PLAN_FILE))
        sections, blocks = _gate_inputs_blocks(plan or "")
        if not sections:
            raise EnvironmentCheckUnavailable(_NO_INPUTS_SECTION)
        if not blocks:
            raise EnvironmentCheckUnavailable(_NO_INPUTS_BLOCK)
        if sections > 1 or len(blocks) > 1:
            raise EnvironmentCheckUnavailable(_MANY_INPUTS_BLOCKS)
        try:
            return json.loads(blocks[0])
        except ValueError as error:
            raise EnvironmentCheckUnavailable(
                f'the block under "Gate environment inputs" in the change\'s plan is not JSON: '
                f"{error}") from None


class DevelopmentChain:
    """The walk. Everything it uses is handed to it; it constructs nothing."""

    def __init__(self, *, store: StateStore, reader: DiskReader, files, processes, notifier,
                 lock, log, id_source, environ: dict, engine_path: str, steps: tuple[Step, ...],
                 providers: ProviderFiles, process_table: walk_stop.ProcessTable,
                 checkout: product_checkout.Checkout, environment_check,
                 chain_name: str = ""):
        self.store = store
        self.environment_check = environment_check
        self.checkout = checkout
        self.process_table = process_table
        self.providers = providers
        self._due_end_hook: tuple[str, str, str, str, str] | None = None
        self.reader = reader
        self.files = files
        self.processes = processes
        self.notifier = notifier
        self.lock = lock
        self.log = log
        self.id_source = id_source
        self.environ = dict(environ)
        self.engine_path = engine_path
        self.steps = steps
        # Handed in where a caller names it; otherwise the table's own name, so a test that builds
        # the engine with a table and nothing else still gets the walk that table belongs to.
        self.chain_name = chain_name or CHAIN_NAMES.get(id(steps), "development")

    # -- entry -------------------------------------------------------------------------------

    def describe(self, *, instance_root: str, project: str, product_path: str = "",
                 forced_provider: str = "") -> StartPlan:
        """What a start would do, decided by the same checks `start` makes and touching nothing:
        no lock, no write, no launch, no message. Never walks past a bad verdict. An integrity
        stop with declared unfinished tasks returns an explicit start to implementation;
        other bad verdicts refuse. Advance still halts on every bad verdict.

        `product_path` says where the per-task commits the verdict reads are (`code_repo`). Empty
        means the product lives in the instance, so the instance's branch is read.

        The plan names every step's provider: the force for each on a forced walk, with the
        provider file unread; otherwise the file's entry for each step of this walk's own table,
        and a `ChainRefused` naming every entry the file cannot give (CP-281, CP-282)."""
        key, entry = self._key_and_entry(instance_root, project, product_path)
        return StartPlan(key=key, entry=entry,
                         providers=self._step_providers(instance_root, forced_provider))

    def _step_providers(self, instance_root: str,
                        forced_provider: str) -> tuple[tuple[str, str], ...]:
        if forced_provider:
            return tuple((step.id, forced_provider) for step in self.steps)
        try:
            resolved = self.providers.at(instance_root).resolve(
                [providers.step(step.id) for step in self.steps])
        except ProvidersRefused as refused:
            raise ChainRefused(str(refused)) from None
        return tuple((step.id, resolved[providers.step(step.id)]) for step in self.steps)

    def _key_and_entry(self, instance_root: str, project: str,
                       product_path: str) -> tuple[str, str]:
        self._refuse_to_overwrite_a_live_walk()
        key = self._resolve_key(instance_root, project)
        change = ChangeLayout(instance_root, project, key)
        entry = self.reader.entry_step(change, self.steps)
        if entry is None:
            refined = (" and its route refined"
                       if any(c.evidence is Evidence.REFINED for c in self.steps) else "")
            raise ChainRefused(f"{key} is already sealed{refined} — {change.trail_folder} exists.")
        for candidate in self.steps[self.reader.resume_index(change, self.steps):]:
            if candidate.id == entry.id:
                break
            reason = self._bad_verdict(change, candidate, product_path)
            if reason is not None:
                if reason == "integrity-stopped" and self.reader.deferrals(change):
                    # An explicit start asks the developer to finish its declared unfinished
                    # work. Advance still halts here; no callback retries a rejected deferral.
                    # Once the developer has re-closed since the verdict, that work is done:
                    # the start runs integrity again rather than spending another re-close.
                    if self.reader.reclosed_after_integrity(change):
                        return key, candidate.id
                    developer = self.steps[self._marker_step_index()]
                    return key, developer.id
                raise ChainRefused(f"stopped at {candidate.id}: {reason}")
        return key, entry.id

    def _resolve_key(self, instance_root: str, project: str) -> str:
        """The active change's key, or `""` for a walk that has not opened one yet.

        Which of the two is right is the TABLE's to say, never the disk's. A table carrying a
        `CHANGE_OPEN` step opens the change itself, so an empty `journey/tobiishi/` is the state
        it starts in. A table without one presumes the change is already there, and
        `discover_key`'s refusal — *"Open one with tobiishi-open first"* — is exactly the answer
        `chain-development` owes a caller who has not. Deciding this off the disk would swallow
        that refusal.

        A table that also carries a `REFINED` step owes the refine before it opens anything new,
        for a unit that serves a station. With no change open, the unit `CONTEXT_PM.md` names as
        sealed, not yet refined and serving a station is the walk's key while a station is still
        open, and the walk enters at `refine`. A sealed unit that serves no station is owed no
        refine. With no unit owed a refine, the key is `""` and the walk enters at the first step
        whose evidence is missing."""
        opens_the_change = any(candidate.evidence is Evidence.CHANGE_OPEN
                               for candidate in self.steps)
        if opens_the_change and not self.reader.open_change_keys(instance_root, project):
            refines = any(candidate.evidence is Evidence.REFINED for candidate in self.steps)
            sealed = self.reader.unrefined_sealed_key(instance_root, project) if refines else None
            return sealed or ""
        return self.reader.discover_key(instance_root, project)

    def start(self, *, instance_root: str, product_path: str, project: str, core_dir: str,
              shim_dir: str, notifier_command: str = "", keep_awake: bool = False,
              started_at: str = "", on_end: str = "",
              context_cap: int = DEFAULT_CONTEXT_CAP,
              forced_provider: str = "", gate_owners_mac: bool = False) -> AdvanceResult:
        with self.lock.hold(self.store.path):
            result = self._start(instance_root=instance_root, product_path=product_path,
                                 project=project, core_dir=core_dir, shim_dir=shim_dir,
                                 notifier_command=notifier_command, keep_awake=keep_awake,
                                 started_at=started_at, on_end=on_end, context_cap=context_cap,
                                 forced_provider=forced_provider,
                                 gate_owners_mac=gate_owners_mac)
        self._run_due_end_hook()
        return result

    def _start(self, *, instance_root: str, product_path: str, project: str, core_dir: str,
               shim_dir: str, notifier_command: str, keep_awake: bool, started_at: str,
               on_end: str, context_cap: int, forced_provider: str,
               gate_owners_mac: bool) -> AdvanceResult:
        plan = self.describe(instance_root=instance_root, project=project,
                             product_path=product_path, forced_provider=forced_provider)
        key = plan.key
        change = ChangeLayout(instance_root, project, key)
        entry = next(candidate for candidate in self.steps if candidate.id == plan.entry)
        state = WalkState(
            instance_root=instance_root, product_path=product_path, project=project,
            core_dir=core_dir, shim_dir=shim_dir, engine_path=self.engine_path, key=key,
            walk_id=self.id_source.new_id(),
            product_docs=os.path.join(product_path, "docs"),
            chain_name=self.chain_name,
            notifier=notifier_command, keep_awake=keep_awake, started_at=started_at,
            on_end=on_end, context_cap=context_cap, forced_provider=forced_provider,
            gate_owners_mac=gate_owners_mac)
        if self.steps.index(entry) > self._marker_step_index():
            self._record_marker(state, change)
        self.store.save(state)
        self.log.append(self._log_path(state),
                        f"chain_development: started walk={state.walk_id} "
                        f"change={key or '(none yet)'} entry={entry.id} at={started_at}")
        self.notifier.send(f"{self._headline(state)} started — change {key}, entering at "
                           f"{entry.id}")
        if entry.runs_when is None:
            # A start that enters at a step with no gate of its own never reaches `_launch_step`'s
            # gate for the steps behind it, so a report one of them left is cleared here.
            for gated in self.steps:
                if gated.runs_when is not None:
                    self._clear_own_report(change, gated)
        after = (self.reader.resume_after(change, product_path)
                 if entry.evidence is Evidence.MARKER_COMMIT else None)
        self._launch_step(state, change, entry, after=after)
        self.store.save(state)
        return AdvanceResult(acted=True, ended=state.ended)

    def _refuse_to_overwrite_a_live_walk(self) -> None:
        existing = self.store.raw()
        if not existing or existing.get("ended") is not None or not existing.get("pending"):
            return
        states = [walk_stop.launch_state(self.files, self.process_table, entry.get("identity", ""))
                  for entry in existing["pending"].values()]
        command = walk_stop.stop_command(existing.get("core_dir", ""),
                                         f"chain-{self.chain_name}", existing.get("project", ""))
        raise ChainAlreadyWalking(
            f"{self.store.path} is still walking {existing.get('key')}, waiting on "
            f"{', '.join(sorted(existing['pending']))}. "
            f"{walk_stop.refusal_remedy(states, command)}")

    def stop(self, stopped_at: str) -> str:
        """End the walk now: stop every launch it waits on, write `stopped`, keep the state file.
        Returns the one message sent. A walk that already ended, or none, is left as it is and the
        message says so."""
        with self.lock.hold(self.store.path):
            message = self._stop(stopped_at)
        self._run_due_end_hook()
        return message

    def _stop(self, stopped_at: str) -> str:
        if not self.store.raw():
            return self._tell(f"no {self.chain_name} walk to stop at {self.store.path}")
        state = self.store.load()
        if state.ended is not None:
            return self._tell(f"{self._headline(state)} — nothing to stop: "
                              f"the walk already ended {state.ended}")
        stops = [walk_stop.stop_launch(self.files, self.process_table,
                                       entry.get("identity", ""), run)
                 for run, entry in state.pending.items()]
        state.pending = {}
        return self._end(state, Ended.STOPPED, walk_stop.stop_reason(stopped_at, stops))

    def _tell(self, message: str) -> str:
        self.notifier.send(message)
        return message

    def advance(self, run: str, outcome: str) -> AdvanceResult:
        """What the per-run shim calls when that run ends. Does nothing when the walk has ended
        (counted) or when `run` is not pending (a repeated or stale delivery). Otherwise the run
        leaves `pending` and is saved BEFORE anything is decided, so a second delivery of the
        same end is itself a no-op."""
        with self.lock.hold(self.store.path):
            result = self._advance(run, outcome)
        self._run_due_end_hook()
        return result

    def _advance(self, run: str, outcome: str) -> AdvanceResult:
        state = self.store.load()
        if state.ended is not None:
            state.reentries += 1
            self.store.save(state)
            return AdvanceResult(acted=False, ended=state.ended)
        entry = state.pending.pop(run, None)
        if entry is None:
            return AdvanceResult(acted=False, ended=None)
        self.store.save(state)

        step = next(candidate for candidate in self.steps if candidate.id == entry["step"])
        change = ChangeLayout(state.instance_root, state.project, state.key)
        if self._left_the_checkout_dirty(state, step, entry):
            self.store.save(state)
            return AdvanceResult(acted=True, ended=state.ended)
        if step.gates:
            self._settle(state, change, step, outcome)
        else:
            self._settle_audit(state, change, step, entry["audited"], outcome)
        self.store.save(state)
        return AdvanceResult(acted=True, ended=state.ended)

    @staticmethod
    def _checkout_path(state: WalkState) -> str:
        """The checkout the walk watches: the product's, or the instance's own when the product
        lives in it (an empty `product_path`)."""
        return state.product_path or state.instance_root

    def _left_the_checkout_dirty(self, state: WalkState, step: Step, entry: dict) -> bool:
        """Compare the product checkout with the reading `_launch_run` took for this run, before
        any recovery or the audit path reads the run's end, and halt at `step` with the reason
        when the run left new entries in it. An entry with nothing recorded is not checked, and
        the checkout is not read for it."""
        before = entry.get(product_checkout.CHECKOUT_BEFORE)
        if before is None:
            return False
        path = self._checkout_path(state)
        reason = product_checkout.left_dirty(before, self.checkout.entries(path), path)
        if reason is None:
            return False
        self._halt(state, step, reason)
        return True

    def _settle(self, state: WalkState, change: ChangeLayout, step: Step, outcome: str) -> None:
        if outcome not in _FINISHED:
            if outcome == "failed" and self._relaunch_after_a_failure(state, change, step):
                return
            self._halt(state, step, f"the run ended {outcome}")
            return
        if (step.evidence is Evidence.MARKER_COMMIT
                and state.developer_marker_before is not None
                and self.reader.marker_commit(change) == state.developer_marker_before):
            if self._relaunch_after_a_pause(state, change, step):
                return
            self._halt(state, step, "no new developer closing marker after the run ended")
            return
        # The artifact is read before any halt report: a pre-worktree report stays on main
        # after the owner repairs the change, and reading it first would stop every later walk
        # at a step that has since succeeded.
        if not self.reader.is_done(change, step):
            report = self.reader.halt_report(change)
            if (report and step.evidence is Evidence.MARKER_COMMIT
                    and state.developer_halt_before is not None
                    and self.reader.halt_snapshot(change) == state.developer_halt_before):
                report = None
            if not report:
                if self._relaunch_after_a_pause(state, change, step):
                    return
                if self._recover_missing_marker(state, change, step):
                    return
            self._halt(state, step, f"halt_report.md at {report}" if report
                       else f"no {_missing(change, step)} after the run ended")
            return
        reason = self._bad_verdict(change, step, state.product_path)
        if reason is not None:
            self._halt(state, step, reason)
            return
        if step.evidence is Evidence.CHANGE_OPEN:
            # The one moment a walk gains its key. Written onto the state before `_after` moves
            # on, because every later step reads `state.key` for its launcher argument and for
            # the layout `advance` rebuilds on each re-entry.
            state.key = self.reader.discover_key(state.instance_root, state.project)
        if step.evidence is Evidence.MARKER_COMMIT:
            self._record_marker(state, change)
        state.history.append(f"{step.id} landed")
        self._after(state, change, step)

    def _record_marker(self, state: WalkState, change: ChangeLayout) -> None:
        """What the closing marker declared, kept on the state for the sealed message."""
        state.suite = self.reader.suite_verdict(change)
        state.marker = self.reader.marker_commit(change)
        state.deferrals = self.reader.deferrals(change)

    def _recover_missing_marker(self, state: WalkState, change: ChangeLayout, step: Step) -> bool:
        """One recovery for a finished developer run with neither marker nor halt report.
        Resume from the product's first unfinished task, including task one; only the
        developer can write a marker, and its verdict still gates the next step.
        """
        if step.evidence is not Evidence.MARKER_COMMIT or state.marker_recoveries >= 1:
            return False
        if self.reader.entry_step(change, self.steps) is not step:
            return False
        after = self.reader.resume_after(change, state.product_path)
        state.marker_recoveries += 1
        state.history.append(f"{step.id} missing marker — recovering once")
        self.notifier.send(f"{self._headline(state)} — missing developer closing marker — "
                           "recovering once")
        # A distinct callback identity keeps a repeated delivery from the ended run from
        # consuming the recovery's pending entry. Its shim must also be a separate file.
        self._launch_run(state, change, step, audited=None, after=after,
                         run=f"{step.id}-recovery")
        return True

    def _relaunch_after_a_pause(self, state: WalkState, change: ChangeLayout, step: Step) -> bool:
        """Resume an explicit context-cap pause that ended the run (`DiskReader.paused_after`).
        A task commit alone is not a pause, and neither is a pause with developer work above it:
        an unexplained missing marker uses the bounded recovery and first unfinished task.
        """
        after = self.reader.paused_after(change, state.product_path)
        if after is None:
            return False
        return self._relaunch_developer(state, change, step, after, failure=False)

    def _relaunch_after_a_failure(self, state: WalkState, change: ChangeLayout, step: Step) -> bool:
        """Whether a `failed` developer run was resumed from the pause it ended on — read only
        where it ended the run (`DiskReader.paused_after`) — or else from its newest landed task
        commit. One such resume is the budget. A second failure halts, even when a later task has
        landed, so a crashing run is not relaunched for ever."""
        after = self.reader.paused_after(change, state.product_path)
        if after is None:
            after = self.reader.resumable_task(change, state.product_path)
        if after is None:
            return False
        return self._relaunch_developer(state, change, step, after, failure=True)

    def _relaunch_developer(self, state: WalkState, change: ChangeLayout, step: Step,
                            after: int, *, failure: bool) -> bool:
        """Relaunch the developer step after `after`. The fresh run is told where to start by
        the launch prompt (`_launch_run`'s `after`), never by anything it reads off the branch."""
        if step.evidence is not Evidence.MARKER_COMMIT:
            return False
        # The relaunch goes through `entry_step`, so it can only restart the step that ended. When
        # an earlier step's evidence has gone missing, `entry_step` answers that step instead, and
        # handing it a task number would send it somewhere it was never asked to go.
        resumed = self.reader.entry_step(change, self.steps)
        if (state.developer_marker_before is not None
                and self.reader.marker_commit(change) == state.developer_marker_before
                and resumed is not None
                and self.steps.index(resumed) > self.steps.index(step)):
            resumed = step
        if resumed is not step:
            return False
        if failure and state.failure_resumes >= 1:
            self._halt(state, step, "the developer run failed again after one resume from its "
                                    "last task commit")
            return True
        # Nothing bounds how often a run may pause, so a run that stops without getting past the
        # last pause would be relaunched for ever. A resume must be after a later task than the
        # one before it.
        if state.paused_after is not None and after <= state.paused_after:
            self._halt(state, step, f"paused after task {after}, no later than the last pause "
                                    f"(after task {state.paused_after}) — the developer made no "
                                    "progress")
            return True
        if failure:
            state.failure_resumes += 1
        state.paused_after = after
        verb = "failed after" if failure else "paused after"
        state.history.append(f"{step.id} {verb} task {after}")
        self.notifier.send(f"{self._headline(state)} — {verb} task {after} — resuming")
        self._launch_run(state, change, resumed, audited=None, after=after)
        return True

    def _bad_verdict(self, change: ChangeLayout, step: Step, product_path: str) -> str | None:
        """The first bad reason `step`'s own declared verdict gives, or `None` when everything
        it declares reads good. `_settle` halts on what this returns for the step that just
        landed; `describe` raises on it for every step before the entry it would otherwise walk
        past silently — one method, so the reasons and their order have one owner.

        The closing marker's reasons come first — `red-suite`, `missing-suite`,
        `missing-language` — and only a marker passing all three has its tasks' commit shape
        read (`_commit_shape_verdict`), on the repo `product_path` puts the per-task commits in.
        `missing-environment` is last, for the marker and for the report alike: only a record that
        passed everything above it is read for the environment it names."""
        if step.declared_prefix:
            verdict = self.reader.declared_verdict(change, step)
            if verdict == "stopped":
                return "integrity-stopped"
            if verdict != "pass":
                return "missing-integrity"
            return self._environment_verdict(change,
                                             self.reader.report_environment_kind(change, step))
        if step.evidence is Evidence.MARKER_COMMIT:
            suite = self.reader.suite_verdict(change)
            if suite == "red":
                if not self._red_is_deferred(change):
                    return "red-suite"
            elif suite == _NO_SUITE:
                # Only the card may say there is no suite, so this cannot hide a red one.
                if not self.reader.card_has_no_suite(change):
                    return "missing-suite"
            elif suite != "green":
                return "missing-suite"
            if not self.reader.language_resolved(change):
                return "missing-language"
            return (self._commit_shape_verdict(change, product_path)
                    or self._environment_verdict(change,
                                                 self.reader.marker_environment_kind(change)))
        return None

    def _environment_verdict(self, change: ChangeLayout, kind: str | None) -> str | None:
        """`missing-environment` unless a record that passed every other check names one of the
        environment kinds. The kind is not checked against a fresh resolution, and `none` — a run
        that issued no suite — passes only where the card on `main` has no command."""
        if kind not in _ENVIRONMENT_KINDS:
            return "missing-environment"
        if kind == _NO_SUITE and not self.reader.card_has_no_suite(change):
            return "missing-environment"
        return None

    def _commit_shape_verdict(self, change: ChangeLayout, product_path: str) -> str | None:
        """`missing-red-commit — task <N>[, task <M>…]` for each judged TDD-lane task that landed
        with no red commit older than its first landing (CP-191, CP-193), or `None`. A plan that
        cannot be read is `unreadable-plan` rather than a pass: a check that passes when it cannot
        read its input passes everything (CP-195)."""
        lane = self.reader.tdd_lane_tasks(change)
        if lane is None:
            return "unreadable-plan"
        # A deferred task is declared unlanded, and its `— red` and `— deferred` commits are the
        # shape the skill prescribes for it (CP-189).
        deferred = set(self._task_numbers(self.reader.deferrals(change), _DEFERRED_PREFIX))
        # A task the developer re-laned to already-green or to red-at-baseline, with its reason
        # recorded (CP-190).
        exempt = deferred | self.reader.relaned_tasks(change)
        judged = [number for number in lane if number not in exempt]
        repo = self.reader.code_repo(change, product_path)
        failing = self.reader.landed_without_red(repo, change.key, judged)
        if not failing:
            return None
        return "missing-red-commit — " + ", ".join(f"task {number}" for number in failing)

    def _red_is_deferred(self, change: ChangeLayout) -> bool:
        """Whether a `Suite: red` marker's red is owned by deferred tasks: at least one `Failing:`
        line, and every one of them names a task some `Deferred:` line names. The engine runs no
        tests, so it can only compare those declarations. A `Failing:` line naming no readable task
        (`— no task`, `— task x`) is owned by no deferral and keeps the red. A `Deferred:` line
        naming no readable task defers nothing, and is never itself a halt."""
        failing = self.reader.failing_cases(change)
        deferred = self._task_numbers(self.reader.deferrals(change), _DEFERRED_PREFIX)
        failing_tasks = self._task_numbers(failing, _FAILING_PREFIX)
        return (bool(failing) and len(failing_tasks) == len(failing)
                and all(number in deferred for number in failing_tasks))

    @staticmethod
    def _task_numbers(lines: list[str], prefix: str) -> list[int]:
        matches = (_TASK_TOKEN.search(line[len(prefix):]) for line in lines)
        return [int(match.group(1)) for match in matches if match]

    def _marker_step_index(self) -> int:
        """Where the one step whose evidence is `MARKER_COMMIT` sits in `self.steps` — `start`
        compares an entry against this to know whether it is entering past it."""
        return next(index for index, candidate in enumerate(self.steps)
                    if candidate.evidence is Evidence.MARKER_COMMIT)

    def _settle_audit(self, state: WalkState, change: ChangeLayout, step: Step, audited: str,
                      outcome: str) -> None:
        if outcome not in _FINISHED:
            state.audits[audited] = f"the run ended {outcome}"
        elif self.reader.audit_done(change, audited):
            state.audits[audited] = "findings recorded"
        else:
            state.audits[audited] = "no findings file"
        if not self._pending_for(state, step):
            self._after(state, change, step)

    # -- launching ---------------------------------------------------------------------------

    def _launch_step(self, state: WalkState, change: ChangeLayout, step: Step,
                     after: int | None = None) -> None:
        if step.runs_when is not None and not self._gate_lets_through(state, change, step):
            return
        if not step.fans_out_over:
            self._launch_run(state, change, step, audited=None, after=after)
            return
        # One read for the whole fan-out, so a refusal can never fall between two of its runs.
        provider = self._provider_or_halt(state, step)
        if provider is None:
            return
        for audited in self.reader.audited(change, step):
            self._launch_run(state, change, step, audited=audited, provider=provider)
        if not self._pending_for(state, step):
            self._after(state, change, step)

    def _gate_lets_through(self, state: WalkState, change: ChangeLayout, step: Step) -> bool:
        """The one gate every way into a step with a `RunsWhen` line shares, because `_start` and
        `_after` both reach a step through `_launch_step`. `True` launches the step. A pass calls
        `_after` on the step, so the walk past it is the walk past any landed step, and returns
        `False`."""
        gate = step.runs_when
        verdict = self.reader.run_verdict(change, step)
        if verdict is RunVerdict.UNSETTLED:
            self._halt_for_missing_verdict(state, change, step)
            return False
        self._clear_own_report(change, step)
        if verdict is RunVerdict.PASS:
            state.history.append(f"{step.id} passed — {gate.prefix} {gate.passes}")
            self._after(state, change, step)
            return False
        return True

    def _clear_own_report(self, change: ChangeLayout, step: Step) -> None:
        """Once the verdict is settled, move this engine's own report out of the change folder,
        beside the walk's state file. An untracked file there fails the delivery's clean-tree
        check, and the report has said what it had to. A report that does not start with the
        engine's marker is another seat's and stays, and so does one committed on the branch."""
        report = os.path.join(change.branch_change_folder, _HALT_REPORT)
        text = self.files.read_text(report)
        if text is None or text.splitlines()[:1] != [engine_report_marker(step)]:
            return
        if self.reader.branch_has_halt_report(change):
            return
        self.files.replace(report, f"{self.store.path}.{step.id}-halt-report.md")

    def _halt_for_missing_verdict(self, state: WalkState, change: ChangeLayout,
                                  step: Step) -> None:
        """Halt before any launch, with a `halt_report.md` in the change folder on the branch —
        the first place `DiskReader.halt_report` reads. The engine writes it because no seat has
        run to. It never overwrites a report already there: whoever wrote that one is the one
        its reader is waiting for, and the halt then names it instead."""
        gate = step.runs_when
        found = self.reader.run_finding(change, gate)
        report = os.path.join(change.branch_change_folder, _HALT_REPORT)
        if not self.files.is_file(report):
            self.files.make_dirs(change.branch_change_folder)
            self.files.write_text(report, _missing_verdict_report(step, found))
        self._halt(state, step, f"missing-text-verdict — {found} in {gate.artifact}; "
                                f"halt_report.md at {report}")

    def _provider_or_halt(self, state: WalkState, step: Step) -> str | None:
        """The provider `step`'s launch goes to — the walk's force, else the provider file's entry
        read now (CP-283) — or `None` once the walk has halted naming what the file lacks."""
        try:
            return self.providers.at(state.instance_root).launch_provider(
                state.forced_provider, providers.step(step.id))
        except ProvidersRefused as refused:
            self._halt(state, step, str(refused))
            return None

    def _environment_allows(self, state: WalkState, change: ChangeLayout, step: Step) -> bool:
        """Whether an implementation launch may go ahead. Asked at the one boundary every
        implementation launch passes — a first entry, an advance, a pause or failure relaunch, a
        missing-marker recovery, an explicit restart — before its shim, its pending entry or its
        launcher exists. Only an owed decision stops it; the walk's stored ask bypasses it."""
        if state.gate_owners_mac:
            return True
        try:
            result = self.environment_check.check(change, state.core_dir)
        except EnvironmentCheckUnavailable as unavailable:
            self._halt(state, step, _CHECK_UNAVAILABLE.format(problem=unavailable))
            return False
        if result.answer is gate_suite.CheckAnswer.OWES_DECISION:
            self._halt(state, step, _DECISION_OWED.format(detail=result.detail))
            return False
        return True

    def _launch_run(self, state: WalkState, change: ChangeLayout, step: Step,
                    audited: str | None, after: int | None = None,
                    run: str | None = None, provider: str | None = None) -> None:
        """Launch one run of `step`. `provider` is the fan-out's one read; every other launch
        reads the file here, before its shim or its pending entry is written."""
        if step.evidence is Evidence.MARKER_COMMIT and not self._environment_allows(
                state, change, step):
            return
        if provider is None:
            provider = self._provider_or_halt(state, step)
            if provider is None:
                return
        run = run or (step.id if audited is None else f"{step.id}-{audited}")
        shim = os.path.join(state.shim_dir, f"chain-{state.chain_name}-{state.project}-{run}.sh")
        self._write_shim(state, shim, run)

        argv = [os.path.join(state.core_dir, "launchers", "skill", "launcher.sh"), step.skill,
                state.project]
        if step.takes_key:
            argv.append(state.key)
        if audited is not None:
            argv.append(audited)
        if after is not None:
            argv.append(str(after))
        if state.keep_awake:
            argv.append("--keep-awake")
        env = with_provider(self.environ, provider)
        env["DETACH_WATCHER_ON_COMPLETE"] = shim
        env["INSTRUMENT_RUN_CHAIN"] = state.chain_name
        env["INSTRUMENT_RUN_WALK_ID"] = state.walk_id
        env["INSTRUMENT_RUN_ROLE"] = step.role
        # The cap is the developer's alone, and is removed rather than merely not set for the same
        # reason the audit target is below: an `--advance` is fired by the previous run's shim,
        # which inherits that run's launch environment, so the step after implementation would
        # otherwise start under the cap its predecessor was given.
        if step.evidence is Evidence.MARKER_COMMIT:
            env[_CONTEXT_CAP_VARIABLE] = str(state.context_cap)
        else:
            env.pop(_CONTEXT_CAP_VARIABLE, None)
        # The owner's ask is the same shape as the cap: set for the steps that run a suite and only
        # when this walk's stored ask says so, removed from every other launch.
        if step.id in _GATE_CONSUMER_STEPS and state.gate_owners_mac:
            env[_GATE_OWNERS_MAC_VARIABLE] = "1"
        else:
            env.pop(_GATE_OWNERS_MAC_VARIABLE, None)
        # The engine's own environment is the previous run's: an `--advance` is fired by that
        # run's shim, which inherits its launch environment. So a non-audit launch removes the
        # target rather than merely not setting it, or the seal inherits the last audit's.
        if audited is not None:
            env["INSTRUMENT_RUN_AUDIT_TARGET"] = audited
        else:
            env.pop("INSTRUMENT_RUN_AUDIT_TARGET", None)

        if step.evidence is Evidence.MARKER_COMMIT:
            state.developer_halt_before = self.reader.halt_snapshot(change)
            state.developer_marker_before = self.reader.marker_commit(change)
        env, identity = walk_stop.prepare_launch(self.files, shim, env)
        state.pending[run] = {"step": step.id, "audited": audited, "identity": identity}
        # The product checkout as this run found it, saved with the run it describes. An
        # unreadable checkout records nothing, and `_advance` does not check a run that has none.
        checkout_before = self.checkout.entries(self._checkout_path(state))
        if checkout_before is not None:
            state.pending[run][product_checkout.CHECKOUT_BEFORE] = checkout_before
        self.store.save(state)
        exit_code = self.processes.run(argv, cwd=state.instance_root, env=env)
        if exit_code == 0:
            state.history.append(f"launched {run}")
            return
        state.pending.pop(run, None)
        if step.gates:
            self._halt(state, step, f"launcher exited {exit_code}")
        else:
            state.audits[audited] = f"launcher exited {exit_code}"

    @staticmethod
    def _log_path(state: WalkState) -> str:
        """The one log a project's walks share: every shim appends its advance here, and a start
        marks where each walk begins in it."""
        return os.path.join(state.shim_dir, f"chain-{state.chain_name}-{state.project}.log")

    def _write_shim(self, state: WalkState, shim: str, run: str) -> None:
        completion_shim.write_shim(self.files, shim, engine_path=self.engine_path,
                                   advance_args=("--advance", self.store.path, run),
                                   log_path=self._log_path(state))

    def _after(self, state: WalkState, change: ChangeLayout, step: Step) -> None:
        """The step has landed: launch the next one, or end the walk after the last. A change walk
        also ends `sealed` at a landed seal when the change serves no station, because its `refine`
        would have no station to find."""
        index = self.steps.index(step)
        following = self.steps[index + 1] if index + 1 < len(self.steps) else None
        if following is None or self._owes_no_refine(step, following, change):
            self._end(state, Ended.SEALED, self._sealed_summary(state))
            return
        self._launch_step(state, change, following)

    def _owes_no_refine(self, step: Step, following: Step, change: ChangeLayout) -> bool:
        """Whether a landed seal ends the walk instead of going on to its refine: the next step
        is the refine and the sealed unit serves no station. Asked only of a seal that has already
        landed, and never of a table with no refine."""
        return (step.evidence is Evidence.SEALED and following.evidence is Evidence.REFINED
                and not self.reader.serves_station(change))

    @staticmethod
    def _pending_for(state: WalkState, step: Step) -> list[str]:
        return [run for run, entry in state.pending.items() if entry["step"] == step.id]

    # -- ending: the one place a walk writes `ended` and tells the owner ---------------------

    def _halt(self, state: WalkState, step: Step, reason: str) -> None:
        self._end(state, Ended.HALTED, f"stopped at {step.id}: {reason}")

    def _end(self, state: WalkState, ended: Ended, what: str) -> str:
        """Write the end, tell the owner, and return what was sent."""
        state.ended = ended.value
        state.ended_reason = what
        self.store.save(state)
        message = f"{self._headline(state)} — {what}"
        self.notifier.send(message)
        self._due_end_hook = (state.on_end, ended.value, state.instance_root,
                              self._headline(state), state.forced_provider)
        return message

    def _run_due_end_hook(self) -> None:
        """Run the command this walk was started with, once, with the end appended. It runs after
        the ended state is saved and the owner told, so a hook that starts the next queue reads a
        walk that has ended, and only once `start` or `advance` has released the state lock: the
        hook may start the next walk on this same project, which takes that lock, and run under it
        the two wait on each other for ever (build-idea's first loop, 2026-09-18)."""
        due, self._due_end_hook = self._due_end_hook, None
        if due is None:
            return
        hook, end, cwd, headline, forced_provider = due
        run_end_hook(hook, end, cwd=cwd, processes=self.processes, notifier=self.notifier,
                     headline=headline, env=with_provider(self.environ, forced_provider))

    def _sealed_summary(self, state: WalkState) -> str:
        audits = "; ".join(f"{skill}: {result}" for skill, result in sorted(state.audits.items()))
        deferred = (f" with deferrals ({', '.join(self._deferral_labels(state.deferrals))})"
                    if state.deferrals else "")
        return (f"sealed {state.key} — suite {state.suite or 'unrecorded'} "
                f"(marker {state.marker or 'unrecorded'}){deferred}; "
                f"audits: {audits or 'none recorded'}")

    @staticmethod
    def _deferral_labels(deferrals: list[str]) -> list[str]:
        """`task <N>` for each deferral, or the line itself when it names no readable task — a
        deferral the message cannot number is still one the owner should see."""
        labels = []
        for line in deferrals:
            token = _TASK_TOKEN.search(line[len(_DEFERRED_PREFIX):])
            labels.append(f"task {token.group(1)}" if token else line)
        return labels

    @staticmethod
    def _headline(state: WalkState) -> str:
        instance = os.path.basename(os.path.normpath(state.instance_root))
        return f"{instance} · {state.project} · {state.chain_name} chain"


# --- the three ports `chain.py` does not have -------------------------------------------------


class Git:
    """The questions the reader asks git, each answered read-only against the one repo it is
    handed — the instance's, or an external product's."""

    def commits_ahead(self, repo: str, base: str, branch: str) -> list[tuple[str, str]]:
        """`(sha, subject)` for every commit in `base..branch`, newest first; `[]` when the
        branch does not exist — an absence the reader always has a decision for."""
        result = subprocess.run(
            ["git", "-C", repo, "log", "--format=%H%x09%s", f"{base}..{branch}"],
            capture_output=True, text=True)
        if result.returncode != 0:
            return []
        return [tuple(line.split("\t", 1)) for line in result.stdout.splitlines() if "\t" in line]

    def branch_has_path(self, repo: str, branch: str, path: str) -> bool:
        return subprocess.run(["git", "-C", repo, "cat-file", "-e", f"{branch}:{path}"],
                              capture_output=True).returncode == 0

    def commit_body(self, repo: str, sha: str) -> str:
        """The full body of one commit, `commits_ahead`'s own shape: one read-only call,
        returning `""` on a non-zero exit so an absent commit is a decision rather than an
        exception."""
        result = subprocess.run(["git", "-C", repo, "log", "-1", "--format=%B", sha],
                                capture_output=True, text=True)
        return result.stdout if result.returncode == 0 else ""

    # Author time and not committer time: a rebase and an amend both reset the committer's and
    # keep the author's, so only the author's still orders a commit the way it was made.
    def author_time(self, repo: str, sha: str) -> int | None:
        """The author time of one commit, in whole epoch seconds, or `None` when git cannot answer
        — `commit_body`'s one-call, absence-as-a-value shape."""
        result = subprocess.run(["git", "-C", repo, "log", "-1", "--format=%at", sha],
                                capture_output=True, text=True)
        stamp = result.stdout.strip()
        return int(stamp) if result.returncode == 0 and stamp.isdigit() else None

    def last_commit_touching(self, repo: str, branch: str, path: str) -> str | None:
        """The newest commit on `branch` that changed `path`, or `None` when git cannot answer or
        no commit did — the same absence-as-a-value shape."""
        result = subprocess.run(
            ["git", "-C", repo, "log", "-1", "--format=%H", branch, "--", path],
            capture_output=True, text=True)
        sha = result.stdout.strip()
        return sha if result.returncode == 0 and sha else None

    def unit_has_shukuba(self, repo: str, key: str) -> bool:
        """Whether any commit the unit `key` landed on `main` carries a `Shukuba:` trailer,
        whatever its value; `False` when git cannot answer.

        What the unit landed is the second-parent range of its newest delivery merge, the unit's
        branch being gone once it is delivered. With no delivery merge it is the reachable commits
        whose messages name the key — `shukuba-refine`'s own reading of *the unit's commits*
        (`SKILL.md` § Step 1). Only a parsed trailer counts, so prose that mentions the word
        outside the trailer block is no mark."""
        if not key:
            return False
        merge = self._newest_delivery_merge(repo, key)
        scope = ([f"{merge}^1..{merge}^2"] if merge
                 else ["main", "--fixed-strings", f"--grep={key}"])
        result = subprocess.run(
            ["git", "-C", repo, "log", *scope, "--format=%(trailers:key=Shukuba,keyonly,only)"],
            capture_output=True, text=True)
        return result.returncode == 0 and bool(result.stdout.strip())

    @staticmethod
    def _newest_delivery_merge(repo: str, key: str) -> str | None:
        """The newest merge on `main` whose subject starts `merge: <key> →`, or `None`."""
        result = subprocess.run(
            ["git", "-C", repo, "log", "main", "--min-parents=2", "--format=%H%x09%s"],
            capture_output=True, text=True)
        if result.returncode != 0:
            return None
        delivery = f"merge: {key} →"
        for line in result.stdout.splitlines():
            sha, _, subject = line.partition("\t")
            if subject.startswith(delivery):
                return sha
        return None


class FileLock:
    """An exclusive `flock` on `<state>.lock`. Four or five audit runs can end within a second of each
    other, each waking its own engine process; without this, two of them load, change and save
    the same state and the second silently erases the first's record."""

    @contextmanager
    def hold(self, state_path: str):
        os.makedirs(os.path.dirname(os.path.abspath(state_path)), exist_ok=True)
        handle = os.open(f"{state_path}.lock", os.O_CREAT | os.O_RDWR, 0o644)
        try:
            fcntl.flock(handle, fcntl.LOCK_EX)
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)
            os.close(handle)


class WalkLog:
    """Appends one line to the chain log. The shims write the same file with `>>` from detached
    engine processes, so this opens for append and never rewrites what is there."""

    def append(self, path: str, line: str) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(line + "\n")


# --- the composition root: the only place a concrete implementation is constructed ----------


_START_REQUIRED_FLAGS: tuple[tuple[str, str], ...] = (
    ("--instance-root", "instance_root"),
    ("--product-path", "product_path"),
    ("--project", "project"),
    ("--core-dir", "core_dir"),
    ("--shim-dir", "shim_dir"),
)

_DESCRIBE_REQUIRED_FLAGS: tuple[tuple[str, str], ...] = (
    ("--instance-root", "instance_root"),
    ("--project", "project"),
)


# What `--steps` accepts, and the one place the flag's values meet the tables. Each value names a
# literal this engine holds; nothing here lets a caller compose a table of their own.
STEP_TABLES: dict[str, tuple[Step, ...]] = {
    "development": DEVELOPMENT_STEPS,
    "change": CHANGE_STEPS,
}


def build_chain(state_path: str, *, notifier_command: str, engine_path: str,
                steps: tuple[Step, ...] | None = None) -> DevelopmentChain:
    files = Files()
    processes = Processes()
    table = DEVELOPMENT_STEPS if steps is None else steps
    name = CHAIN_NAMES.get(id(table), "development")
    return DevelopmentChain(
        store=StateStore(files, state_path, name),
        reader=DiskReader(files=files, git=Git()),
        files=files,
        processes=processes,
        notifier=Notifier(notifier_command, processes),
        lock=FileLock(),
        log=WalkLog(),
        id_source=IdSource(),
        environ=dict(os.environ),
        engine_path=engine_path,
        steps=table,
        providers=ProviderFiles(files),
        process_table=walk_stop.ProcessTable(),
        checkout=product_checkout.Checkout(),
        environment_check=GateEnvironmentCheck(files=files),
        chain_name=name,
    )


def _positive_integer(text: str) -> int:
    """`--context-cap`'s type: whole tokens, more than none. argparse turns the refusal into its
    own usage error, so a bad value never reaches a start and no state is written."""
    if not re.fullmatch(r"[0-9]+", text) or int(text) == 0:
        raise argparse.ArgumentTypeError(f"{text!r} is not a positive integer of tokens")
    return int(text)


def _walk_of(raw: dict, default: str) -> str:
    """Which walk a state belongs to. It was fixed at the walk's start and written to its state;
    a shim or a stop names only the state. Read the table from there, never from the flag's
    default: a change walk advanced on the development table has no `station` or `change` step to
    settle, and crashed on its first advance (measured on a satellite, 2026-09-18)."""
    return raw["chain_name"] if raw.get("chain_name") in STEP_TABLES else default


def main(argv: list[str] | None = None) -> int:
    try:
        from dotenv import load_dotenv
        from pathlib import Path
        load_dotenv()
        load_dotenv(Path.home() / ".env")
    except ImportError:
        pass

    """`--start <state>` is the launcher's entry; `--advance <state> <run> <outcome>` is what a
    per-run shim fires; `--describe <state>` is what the launcher's `--dry-run` asks. None ever
    lets a traceback out as the whole answer: the advance runs detached from a hook nobody watches,
    so stderr goes to the chain's log and the owner's channel is the only place a stop can be seen
    — and the describe, which answers at a terminal, sends to that channel nothing at all."""
    parser = argparse.ArgumentParser(description="walk the change pipeline as a chain of launchers")
    parser.add_argument("--start", metavar="STATE_PATH")
    parser.add_argument("--advance", nargs=3, metavar=("STATE_PATH", "RUN", "OUTCOME"))
    parser.add_argument("--stop", metavar="STATE_PATH",
                        help="end the walk now: stop its run and watcher, write `stopped`, keep "
                             "the state file; --notifier names the channel when given, else the "
                             "state's")
    parser.add_argument("--describe", metavar="STATE_PATH",
                        help="say which change a start would carry and the step it would enter "
                             "at, or why it would refuse — writing, launching and sending nothing")
    parser.add_argument("--list-open-changes", action="store_true",
                        help="print active change keys as JSON without writing or launching")
    parser.add_argument("--instance-root")
    parser.add_argument("--product-path")
    parser.add_argument("--project")
    parser.add_argument("--core-dir")
    parser.add_argument("--shim-dir")
    parser.add_argument("--steps", choices=sorted(STEP_TABLES), default="development",
                        help="which walk this is: the change pipeline, or the same "
                             "pipeline entered at the two journey moves that open a station "
                             "and a change")
    parser.add_argument("--notifier", default="")
    parser.add_argument("--keep-awake", action="store_true")
    parser.add_argument("--context-cap", type=_positive_integer, default=DEFAULT_CONTEXT_CAP,
                        metavar="TOKENS",
                        help="the context, in tokens, past which the developer's run is told to "
                             "pause at a task boundary and a fresh one takes over; read only "
                             f"with --start (default {DEFAULT_CONTEXT_CAP})")
    parser.add_argument("--provider", choices=PROVIDERS, default="",
                        help="force every step of the walk onto this provider, over the one "
                             ".providers.toml at the instance root names, which is then not "
                             "read; read with --start, and with --describe to say which "
                             "provider each step would run on")
    parser.add_argument("--gate-owners-mac", action="store_true",
                        help="the owner's ask to run the gates' suites on their own Mac, over any "
                             "environment the product resolves; read only with --start, and "
                             "stored in the walk's state — an --advance or --describe ignores it")
    parser.add_argument("--on-end", default="", metavar="COMMAND",
                        help="a command run once when the walk ends, sealed or halted, with the "
                             "end appended as its last argument; read only with --start")
    args = parser.parse_args(argv)

    chosen = [entry for entry in (args.start, args.advance, args.describe, args.stop,
                                  args.list_open_changes) if entry]
    if len(chosen) > 1:
        print("chain_development: --start, --advance, --describe, --stop and "
              "--list-open-changes are mutually exclusive",
              file=sys.stderr)
        return 2
    if not chosen:
        print("chain_development: one of --start, --advance, --describe, --stop or "
              "--list-open-changes is required",
              file=sys.stderr)
        return 2

    if args.list_open_changes:
        if not args.instance_root or not args.project:
            print("chain_development: --list-open-changes requires --instance-root and --project",
                  file=sys.stderr)
            return 2
        reader = DiskReader(files=Files(), git=Git())
        print(json.dumps(sorted(reader.open_change_keys(args.instance_root, args.project))))
        return 0

    engine_path = os.path.abspath(__file__)
    steps = STEP_TABLES[args.steps]
    # The name for main()'s own messages. A refusal or a crash never reaches `_headline`, which
    # reads a state file that a refused start never wrote — so the two say which walk stopped
    # from the same place the walk itself takes its name.
    walk = args.steps

    if args.describe:
        missing = [flag for flag, attribute in _DESCRIBE_REQUIRED_FLAGS
                   if not getattr(args, attribute)]
        if missing:
            print(f"chain_development: --describe requires {', '.join(missing)}", file=sys.stderr)
            return 2
        # Built with no notifier command at all, so nothing on this path can send: a dry run is the
        # owner asking a question at a terminal, never an event for their phone.
        chain = build_chain(args.describe, notifier_command="", engine_path=engine_path,
                            steps=steps)
        try:
            plan = chain.describe(instance_root=args.instance_root, project=args.project,
                                  product_path=args.product_path or "",
                                  forced_provider=args.provider)
        except ChainRefused as exc:
            print(f"chain_development: {exc}", file=sys.stderr)
            return 3
        except Exception:
            traceback.print_exc(file=sys.stderr)
            return 5
        print(f"key={plan.key}")
        print(f"entry={plan.entry}")
        print("providers=" + " ".join(f"{step}={provider}" for step, provider in plan.providers))
        return 0

    if args.stop:
        raw = StateStore(Files(), args.stop).raw()
        walk = _walk_of(raw, walk)
        chain = build_chain(args.stop, notifier_command=args.notifier or raw.get("notifier", ""),
                            engine_path=engine_path, steps=STEP_TABLES[walk])
        try:
            print(chain.stop(datetime.now(timezone.utc).isoformat()))
        except ChainRefused as exc:
            print(f"chain_development: {exc}", file=sys.stderr)
            return 3
        except Exception as exc:
            traceback.print_exc(file=sys.stderr)
            chain.notifier.send(
                f"{walk} chain crashed stopping — {str(exc) or type(exc).__name__}")
            return 5
        return 0

    if args.advance:
        state_path, run, outcome = args.advance
        raw = StateStore(Files(), state_path).raw()
        notifier_command = raw.get("notifier", "")
        walk = _walk_of(raw, walk)
        steps = STEP_TABLES[walk]
        chain = build_chain(state_path, notifier_command=notifier_command,
                            engine_path=engine_path, steps=steps)
        try:
            result = chain.advance(run, outcome)
        except ChainRefused as exc:
            print(f"chain_development: {exc}", file=sys.stderr)
            chain.notifier.send(f"{walk} chain refused to advance {run} — {exc}")
            return 3
        except Exception as exc:
            traceback.print_exc(file=sys.stderr)
            chain.notifier.send(f"{walk} chain crashed advancing {run} on {outcome!r} "
                                f"— {str(exc) or type(exc).__name__}")
            return 5
        print(f"chain_development: acted={result.acted} ended={result.ended}")
        return 0

    missing = [flag for flag, attribute in _START_REQUIRED_FLAGS if not getattr(args, attribute)]
    if missing:
        print(f"chain_development: --start requires {', '.join(missing)}", file=sys.stderr)
        return 2

    chain = build_chain(args.start, notifier_command=args.notifier, engine_path=engine_path,
                        steps=steps)
    try:
        result = chain.start(instance_root=args.instance_root, product_path=args.product_path,
                             project=args.project, core_dir=args.core_dir,
                             shim_dir=args.shim_dir, notifier_command=args.notifier,
                             keep_awake=args.keep_awake,
                             started_at=datetime.now(timezone.utc).isoformat(),
                             on_end=args.on_end, context_cap=args.context_cap,
                             forced_provider=args.provider,
                             gate_owners_mac=args.gate_owners_mac)
    except ChainRefused as exc:
        print(f"chain_development: {exc}", file=sys.stderr)
        chain.notifier.send(f"{walk} chain refused to start — {exc}")
        return 3
    except Exception as exc:
        traceback.print_exc(file=sys.stderr)
        chain.notifier.send(f"{walk} chain crashed starting — {exc}")
        return 5
    print(f"chain_development: acted={result.acted} ended={result.ended}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
