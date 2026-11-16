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
    use its one unexplained-marker recovery. A `records-owed` halt report can launch the document
    sweep instead, as § A RECORDS-OWED HALT states. A new or revised `halt_report.md` stops that
    recovery; only development-specs, development-design (when no reading of a conflicting spec
    holds), tobiishi-seal, development-content and, for its three halts, the developer write one
    — and this engine, once, for a content step whose verdict is missing.

WHY IT STANDS BESIDE `chain.py` RATHER THAN EXTENDING IT
    `chain.py` walks documents: its registry, its cycle and its report classification are all a
    document's, it waits on one run at a time, and its command check refuses the skill launcher's
    extra arguments. This engine borrows its generic ports and changes nothing in it.

THE TWO TABLES, AND WHY THEY ARE BOTH HERE
    `CHANGE_STEPS` is the pipeline `change` walks. `WALK_STEPS` is the same
    ten behind `shukuba-open` and `tobiishi-open` and ahead of `shukuba-refine`. It is the walk
    `walk` enters, which needs no station and no change request to already be there. When
    the sealed change serves a station, the walk does not end until the route has been re-read
    after the seal. When it serves none, the walk ends `sealed` at the seal. `--steps` says which a
    start is, and a caller composes neither: both are literals here, the way
    `change/launcher.sh` already said its own was. They differ by two steps at the front
    and agree everywhere after, so a second engine would be a third copy of the state store, the
    live-walk refusal, the launch environment and the shim write.

    Three things the second table changes for every walk. The KEY is no longer a start-time fact: a
    `WALK_STEPS` walk begins with none, and `_settle` reads it off the disk the moment the
    `open` step lands — `_resolve_key` states why the TABLE, never the disk, decides whether an
    absent one is legitimate. And the walk's NAME is on its state rather than a module constant,
    because the shim, the log, the telemetry tag and every message the owner reads have to say
    which of two walks they came from. And a SEALED change is no longer always the end of a walk. A
    sealed change serves a station when a commit it landed carries a `Shukuba:` trailer, or when a
    station file names its key, whether that station is open, closed or parked. Those are the two
    marks `shukuba-refine` reads to find a unit's station, and the walk counts nothing else. An open
    station that does not name the key does not make the change serve it. A walk whose sealed
    change serves a station goes on to `refine`. One whose sealed change serves none ends `sealed`
    at the seal, because the refine would find no station and stop without a report. A walk
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

THE QA STEP
    `red-behaviour` runs the QA seat directly after `specs` on a change `qa_step_applies` says it
    concerns, and is passed with no launch on every other. That one function decides it, from the
    project card on `main` and the spec on the branch, so nothing else in this module reads the
    two lines it reads. The gate is the content step's door: `DiskReader.run_verdict` answers RUN
    or PASS for it, never UNSETTLED, `_gate_lets_through` records `red-behaviour passed — <what
    was read>` and walks on, and `entry_step` never enters a change already past it. Its
    evidence, once it ran, is QA's record committed on the change branch. That record is a red
    record or a no-reach record, whose `No reach:` line says why the recorded way in reaches none
    of the change's behaviours. `qa_red_verdict` passes the step on a no-reach record it accepts,
    at the place it would answer `missing-qa-red`, so its earlier answers keep their order, and
    the walk records `red-behaviour passed — "<the No reach: line>"` with no retry. No later step
    reads QA's files, and the audit does not cover the step.

    A run of `implementation` or `design` may leave an ask of QA's step: a reason, uncommitted, at
    `ChangeLayout.qa_ask`, which `--qa-ask-place` prints. When any run ends, `_answer_an_ask`
    reads it before the run's own evidence is judged and answers it once. It is turned down for
    the first of four reasons (another step, the gate passed QA's step with no launch, no reason,
    the seat's ask already accepted), and the end then settles as with no ask. An accepted ask
    launches `red-behaviour` and nothing else. The re-run is judged by the same `qa_red_verdict`,
    after two checks that read only the commits made since the ask (`_rerun_stalled`). A re-run
    passes on a no-reach record only when a commit made since the ask changed QA's record, and
    one that made a red over a record it did not change is refused as a red record. An
    accepted red returns the walk to the asker as `red-behaviour landed — back to <asker>`, an
    accepted no-reach record as `red-behaviour passed — "<the No reach: line>" — back to
    <asker>`, and the asker's landing closes the ask. The record of it, `QaAsks`, is per change
    and across walks: it also counts QA's runs, and a seventh is refused, `qa-runs-spent`. A walk
    with an ask open is entered at the step the ask owes, which `_key_and_entry` chooses, not
    `entry_step`, so a change already past QA's step on disk is entered there while an ask it
    accepted has not returned.

THE CLOSE
    Before it launches the audit or the seal, a walk runs the close: every scenario the product
    holds, on the change's final code, in a throwaway copy. It is no row of `CHANGE_STEPS` or
    `WALK_STEPS` but a guard at the top of `_launch_step`, the one door both walks reach `audit`
    and `seal` through, keyed on `WalkState.close_passed`; a start builds a fresh state, so no
    verdict survives a walk and a walk entered at either step runs the close first. A card on
    `main` that does not say `behave` passes it with the card's own reading. On one that does,
    `close_verdict` refuses a `Role: Developer` commit that touched the scenario folder
    (`close-refused`), then runs Behave at the branch tip and judges its report by the one reading
    QA's base run uses (`close-red`, `behave-unavailable`). A stop ends the walk halted at
    `close` through the writer every halt shares. The close launches nothing, writes nothing,
    needs no provider entry, and `--describe` runs no Behave. A pass on a `behave` card keeps its
    history line as `WalkState.close_line`, and `_launch_run` hands it to the seal launch alone
    as `CLOSE_VERDICT_VARIABLE`; the seal's action writes it into the sealed folder.

THE CHANGELOG STEP
    `changelog` runs the Content Editor's `changelog-line` on every change, directly after
    `implementation` and before `code-integrity`, whether or not the earlier content step ran. The
    skill's editorial output is never read here: the step is done once `changelog-report.md` is
    committed on the change branch (`Evidence.COMMITTED_CHANGE_FILE`, read through
    `Git.branch_has_path`), so a report that is only in the working tree or only staged does not
    count, and a run that ends without one halts the walk at the step and launches no integrity
    run. The step has no `runs_when` and no recovery of its own.

THE END HOOK
    `--on-end <command>` is an optional command a start carries on the walk's state and `_end`
    runs once, after the ended state is saved, with the end (`sealed` or `halted`) appended. It is
    how `walk` reaches `build-idea` when a walk ends without either engine importing the
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
    A developer run past its cap finishes the task it is on (or, when it cannot land, commits its
    failing tests as its red) and stops on a pause commit
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

A RECORDS-OWED HALT
    A run of `specs`, `design` or `plan` that ends without its artifact may leave a
    `halt_report.md` whose halt reason is `records-owed`. Such a step raised one item on a product
    document's companion, under *Raised from downstream*, for each records defect it found, and
    names each item in a `Raised item:` line of the report. On a project whose card on `main`
    reads `**Definition:** full`, the walk does not halt there. It first carries onto the
    product's main checkout each named item that checkout does not yet hold. It then records which
    named items the main checkout holds open, and launches `product-docs`, the product's document
    chain, once per walk. Any other report, and a `records-owed` report on any other card, halts
    the walk as before, naming the report. The rule, with every way the route ends, is the
    `records-owed` row of `core/doctrine/flow/step_outcome_contract.md` § The halts. This
    section says why the engine is shaped the way it is.

    The carry exists because the step and the sweep read two different checkouts. The step writes
    the item in the change's own worktree, because no step writes on `main`. `product-docs` reads
    the companion on the product's main checkout, from the instance root. An item left only in the
    change's worktree would never be held open at the launch, so the sweep could never fold it and
    the walk could never start the change again. The engine makes the one write on `main`, because
    it is what reads the halt and launches the sweep. It copies the item's lines as the step wrote
    them, its number included, to the end of the main checkout's *Raised from downstream* section,
    so no line already there changes. An item the main checkout already holds is not copied again.
    Where the main checkout has no companion for an item, the carry creates one from that
    companion's template, the file in the templates layer's `product-templates/` folder of the core
    the walk runs on whose name is the companion's with `_template` before `.md`, the two compared
    without regard to case. The created companion holds the template's title with its `<…>` token
    replaced by the project's name, the template's lines before its first `## ` heading, every `## `
    heading of the template in order, `None.` under each heading but *Raised from downstream*, and
    the carried items under *Raised from downstream*. Nothing else of the template is copied. Its
    frontmatter, comments, example items and guidance paragraphs are written for the run that
    authors a companion, and none of them survives into what that run writes. Left in a created
    companion, the template's example items would read as open items. Where the main checkout's
    companion has no *Raised from downstream* section, the carry adds the template's heading for
    that section at the end of the file, so no line already there changes either. An item whose
    companion has no template stays off the main checkout. The carry writes nothing for it and does
    not halt on it, because a halt before the sweep would stop the other items from folding too.
    That item ends `not folded` after the sweep.

    The carry lands as one commit on the main checkout's `main`, made through `commit_builder.py`
    with the halting step's seat as its `Role:`, because the words are that seat's and the engine is
    no seat. Before it writes anything, the carry halts when that checkout does not have `main` out,
    when a companion it would write holds an uncommitted change, or when git cannot read a
    companion's status. Committing in any of those states would put the item on another branch, or
    sweep someone else's edit into the carry's commit. When the builder refuses the commit, each
    companion the carry found is written back byte for byte and unstaged, and each companion the
    carry created is removed from disk and unstaged, because a half-carried item left on `main`
    would look carried to the next walk.

    The sweep's end comes back as an ordinary `--advance`, through this walk's own completion
    shim, and never through a command that advances the walk directly. The launcher runs the
    document chain in the foreground, and that chain can run its end hook before the launch
    returns. A hook that did not detach would wait on this walk's state lock for ever. For the
    same reason the launch runs once the lock is released, and its exit is settled under the
    lock again. A sweep's end that arrives before the launcher returns has already settled the
    run, so the exit then changes nothing.

    The launch carries the walk's forced provider. An unforced walk forces none, and an inherited
    `KENSAIAPP_AGENT_PROVIDER` is removed, so each document runs on its own entry. The launch
    records no process identity, because the document chain has its own state and its own stop.
    A stop of this walk while the sweep runs ends this walk and leaves the sweep running, and the
    sweep's later end reaches an ended walk and changes nothing.

    An item has folded only when the main checkout held it open at the launch and holds it open
    no longer, matched by its title and never by its number. An item the main checkout did not
    hold open at the launch has not folded, so the change's branch is kept. That is an item the
    carry could not place, or one neither checkout held. Once the sweep ends `sealed` with every
    item folded, the walk clears the old change in each repository: the instance's first, then an
    external product's. It removes the worktree without forcing it, so a worktree holding
    uncommitted work is refused and the walk halts rather than lose that work. It deletes the
    branch naming the tip it read just before. Then it launches `development-specs` again, and
    the walk keeps its key, because the change folder on `main` is left as it is.

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
    the engine as `checkout`. The engine's one write on that checkout is the records-owed carry
    (§ A RECORDS-OWED HALT), and the carry leaves no uncommitted change behind: it commits what
    it writes, or puts it back.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import os
import re
import shlex
import subprocess
import sys
import traceback
from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass, field, fields
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

import behave_run
import completion_shim
import development_path
import gate_suite
import product_checkout
import providers
import record_declarations
import walk_stop
from chain import (PROVIDERS, FileLock, Files, IdSource, Notifier, Processes, run_end_hook,
                   with_provider)
from providers import ProviderFiles, ProvidersRefused

__version__ = "4.9.0"


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
    COMMITTED_CHANGE_FILE = "committed_change_file"  # the same, but only once a commit carries it
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
_INTEGRITY_PREFIX = record_declarations.INTEGRITY.prefix
_INTEGRITY_REPORT = "code-integrity-report.md"

# The security report's declared line, the same shape as the integrity one (`skills/senior-engineer/
# .claude/skills/development-security/SKILL.md`). `clean`, `fixed` and `reported` pass; `stopped`
# halts; any other value, or no line, is `missing-security`. No environment is read off this report.
_SECURITY_PREFIX = record_declarations.SECURITY.prefix
_SECURITY_REPORT = "security-report.md"
_SECURITY_PASSING = frozenset({"clean", "fixed", "reported"})

# The characters a value reading undresses with — the parser's own (`record_declarations`, which
# states why a declared line is undressed before its prefix is matched).
_EMPHASIS = record_declarations.EMPHASIS

# Whether a change publishes text, as `development-design` stamps it in the design's header
# (`skills/architect/.claude/skills/development-design/SKILL.md` § Output): `yes` runs the
# `content` step, `no` passes it, and the verdict is decided upstream of the Content Editor, never
# by it (`core/roles/loaders/content_editor_global.md` § Non-responsibilities).
_PUBLISHES_TEXT = RunsWhen(
    artifact="change_design.md", prefix=record_declarations.PUBLISHES_TEXT.prefix, runs="yes",
    passes="no")

@dataclass(frozen=True)
class QaDecision:
    """Whether QA's step applies to a change, and the line or the absence that decided it."""

    applies: bool
    read: str


@dataclass(frozen=True)
class BehaveCard:
    """What the project card on `main` says about scenarios: `says_behave` is whether its one
    Behave line reads `behave`, and `read` is the line or the absence that decided it."""

    says_behave: bool
    read: str


def behave_card_reading(card: str | None) -> BehaveCard:
    """The card half of QA's decision, and the one reader of the card's Behave line. Pure: it
    reads the text it is given. The card says `behave` when it holds exactly one Behave line
    whose value, cut at an inline comment and trimmed, is `behave`. Every other reading says
    what it read, in the words QA's step pass names for that card."""
    card_label = "**Behave:**"
    if card is None:
        return BehaveCard(False, "no project.md on main")
    card_lines = [line for line in card.splitlines() if line.startswith(card_label)]
    if not card_lines:
        return BehaveCard(False, f"project.md has no {card_label} line")
    if len(card_lines) > 1:
        return BehaveCard(False, f"project.md has {len(card_lines)} {card_label} lines")
    value = card_lines[0][len(card_label):].split("<!--")[0].strip()
    if value.startswith("none — "):
        return BehaveCard(False, f"{card_label} {value}")
    if value != "behave":
        return BehaveCard(False, f"project.md's {card_label} line reads \"{value}\"")
    return BehaveCard(True, f"{card_label} behave")


def qa_step_applies(card: str | None, spec: str | None) -> QaDecision:
    """The one decision on whether QA's step applies. Pure: it reads the two texts it is given.

    The step applies when the card on main says `behave` (`behave_card_reading`) and the spec's
    Behaviour line starts with `changing`. Every other reading passes the step and says what it
    read. The spec's line label is written here and nowhere else in this module's decision."""
    spec_label = "**Behaviour:**"
    reading = behave_card_reading(card)
    if not reading.says_behave:
        return QaDecision(False, reading.read)
    if spec is None:
        return QaDecision(False, "no change_spec.md on the branch")
    spec_lines = [line for line in spec.splitlines() if line.startswith(spec_label)]
    if not spec_lines:
        return QaDecision(False, f"change_spec.md has no {spec_label} line")
    words = spec_lines[0][len(spec_label):].split()
    word = words[0].strip(_EMPHASIS) if words else ""
    if word == "changing":
        return QaDecision(True, f"{reading.read} and {spec_label} changing")
    return QaDecision(False, f"{spec_label} {word}".rstrip())


# The close is a guard at `_launch_step`, not a row of either table. Its id names it in every
# history and stop line, and `Evidence.AUDIT_FINDINGS` and `Evidence.SEALED` are the two steps it
# stands in front of.
CLOSE = "close"
_BEHIND_THE_CLOSE = frozenset({Evidence.AUDIT_FINDINGS, Evidence.SEALED})
_MISSING_QA_RED = "missing-qa-red"
# The two steps whose runs may ask QA's step to run again.
_ASKERS = frozenset({"implementation", "design"})
# QA's step runs at most this many times on one change, counted across every walk of it; every way
# into a QA launch passes the one check in `_launch_run`.
QA_RUN_CEILING = 6
_QA_RUNS_SPENT = "qa-runs-spent — QA's step has run {ceiling} times on {key}"
_MAIN_IS_RED = "main is red — "
_QA_MAIN_RED = "qa-main-red"
_THE_THREE_WAYS_IN = ("command", "server", "browser")
_NO_WAY_IN_ADVICE = "the product's architecture run (product-architecture) records the way in"


def qa_way_in(nfdr: str | None) -> str | None:
    """What `docs/nfdr.md` held when it records no way in for QA's scenarios, and `None` when it
    records one. Pure: it reads the text it is given, `None` standing for an absent file.

    The four states `red-behaviour`'s rich prompt names are no file, a Behave line that does not
    read `behave`, a way-in line that still holds its three forms, and `behave` with no way-in
    line; a way-in line with no value is the same answer, because it names nothing."""
    behave_label, way_in_label = "**Behave:**", "**Behave way in:**"
    if nfdr is None:
        return "docs/nfdr.md is absent"
    lines = nfdr.splitlines()
    behave_lines = [line for line in lines if line.startswith(behave_label)]
    if not behave_lines:
        return f"docs/nfdr.md has no {behave_label} line"
    behave = behave_lines[0][len(behave_label):].split("<!--")[0].strip()
    if behave != "behave":
        return f"docs/nfdr.md has a {behave_label} line that reads {behave}"
    way_in_lines = [line for line in lines if line.startswith(way_in_label)]
    if not way_in_lines:
        return f"docs/nfdr.md has a {behave_label} line that reads behave and no Behave way in line"
    held = way_in_lines[0][len(way_in_label):].split("<!--")[0].strip().strip(_EMPHASIS).strip()
    if not held:
        return "docs/nfdr.md has a Behave way in line with no value"
    if all(form in held for form in _THE_THREE_WAYS_IN):
        return "docs/nfdr.md has a Behave way in line that still holds its three forms"
    return None


# QA's step. It runs the QA seat on a change `qa_step_applies` says it concerns and is passed, with
# no launch, on every other. Its evidence is QA's record committed on the change branch, which is
# also what a step that ran leaves behind (`DiskReader.run_verdict`, `_gate_lets_through`).
_QA_STEP = Step("red-behaviour", "red-behaviour", "qa", Evidence.COMMITTED_CHANGE_FILE,
                development_path.QA_RECORD)

# The report `changelog-line` commits on the change branch, whatever it did to the product
# (`skills/content-editor/.claude/skills/changelog-line/SKILL.md`): its committed presence is the
# step landing, including a run that wrote no product file.
_CHANGELOG_REPORT = "changelog-report.md"

CHANGE_STEPS: tuple[Step, ...] = (
    Step("specs", "development-specs", "product-owner", Evidence.CHANGE_FILE, "change_spec.md",
         takes_key=False),
    _QA_STEP,
    Step("design", "development-design", "architect", Evidence.CHANGE_FILE, "change_design.md"),
    Step("plan", "development-plan", "tech-lead", Evidence.CHANGE_FILE, "tl_instruction.md"),
    Step("content", "development-content", "content-editor", Evidence.CHANGE_FILE,
         "change_text.md", runs_when=_PUBLISHES_TEXT),
    Step("implementation", "development-implementation", "developer", Evidence.MARKER_COMMIT),
    Step("changelog", "changelog-line", "content-editor", Evidence.COMMITTED_CHANGE_FILE,
         _CHANGELOG_REPORT),
    Step("code-integrity", "development-code-integrity", "senior-engineer", Evidence.CHANGE_FILE,
         _INTEGRITY_REPORT, declared_prefix=_INTEGRITY_PREFIX),
    Step("security", "development-security", "senior-engineer", Evidence.CHANGE_FILE,
         _SECURITY_REPORT, declared_prefix=_SECURITY_PREFIX),
    Step("audit", "development-audit", "kensaiapp-auditor", Evidence.AUDIT_FINDINGS, gates=False,
         fans_out_over=("development-specs", "development-design", "development-plan",
                        "development-content", "development-implementation")),
    Step("seal", "tobiishi-seal", "pm", Evidence.SEALED),
)

# `dependency-repair`, launched when a closing marker's red is not the change's own (CP-860). Held
# outside both tables on purpose: it is never a step a walk enters at or counts, only one the
# engine launches from `_settle` and resolves in `_advance`, so the chain-launched skill set, the
# provider file's `steps` entries and every table's order stay as they were. It takes no key — it
# coins its own (`dependency-repair/SKILL.md` § *1. Open the repair's branch*) — and its evidence
# is a report, so the launch is read by `repair_reports`, never by `is_done`.
_RED_SUITE = "red-suite"
_MERGED = "merged"
# The `Surface:` an advance carries, by the provider the repair ran on (`commit_format.md` §
# Surface tracking). `hf` and `ollama` are Claude Code aimed at another endpoint
# (`agent_run.py` `HfAdapter`, `OllamaAdapter`), so their surface is Claude Code's. A provider
# with no surface here is a refusal, never a guess.
_SURFACES = {"claude": "Claude Code", "codex": "Codex", "gemini": "Gemini",
             "hf": "Claude Code", "ollama": "Claude Code"}
_REPAIR_STEP = Step("repair", "dependency-repair", "senior-engineer", Evidence.CHANGE_FILE,
                    takes_key=False)

# The step each gated skill is, so the audit can leave out a step the change passed: a no-text
# change has no `change_text.md` to audit (`DiskReader.audited`).
_GATED_BY_SKILL = {entry.skill: entry for entry in CHANGE_STEPS if entry.runs_when}

# The two producer steps `ad-hoc-plan` stands in for, and the stub each leaves in their place. A stub
# says so on its `Planned by:` line, and its step is not audited: `development-specs` and
# `development-design` did not run, so there is no run of theirs to read — the owner's call,
# 2026-10-24 (`skills/tech-lead/.claude/skills/ad-hoc-plan/SKILL.md` § *Step 5*).
_STUBBED_BY = "ad-hoc-plan"
_STUB_ARTIFACT = {"development-specs": "change_spec.md", "development-design": "change_design.md"}

# `walk`'s table: the same pipeline, entered at the two PM moves that `change`
# requires a caller to have made by hand. Both take no key — `station` runs before one exists and
# `open` is what creates it — so both reach the disk through a `ChangeLayout` whose `key` is `""`.
# After the seal it re-reads the project's route through `shukuba-refine`, which takes the sealed
# unit's key (`skills/pm/.claude/skills/shukuba-refine/launcher.md` § Arguments). It does so only
# for a change that serves a station. A change that serves none ends the walk `sealed` at the seal,
# and the `refine` step is never launched for it.
WALK_STEPS: tuple[Step, ...] = (
    Step("station", "shukuba-open", "pm", Evidence.STATION_FILE, takes_key=False),
    Step("open", "tobiishi-open", "pm", Evidence.CHANGE_OPEN, takes_key=False),
) + CHANGE_STEPS + (
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
# Step 2 § Pausing at the context cap): an empty commit whose subject names the last task that
# landed. It never holds `_MARKER_SUBJECT`, so it is not a closing marker.
_PAUSE_SUBJECT = re.compile(r"implementation paused after task (\d+)")
# Every commit a developer run makes opens with its seat (`development-implementation/SKILL.md`,
# its per-task, pause and closing subjects, and the free-form ones a run also makes).
_DEVELOPER_PREFIX = "developer:"
# The closing marker's own never-omitted lines
# (`skills/developer/.claude/skills/development-implementation/SKILL.md` Step 3): the literal prefix
# each one's declaration starts with.
_SUITE_PREFIX = record_declarations.SUITE.prefix
# A product with no code has no suite. Its project card says so with `Test command: none`
# (`core/templates/project_template.md`), and only then may the marker declare `Suite: none`.
# The whole value must be `none`, with the inline comment cut off first and code or bold markup
# ignored. So `none` written only inside the comment does not count, and neither does a stand-in
# such as `none yet — set once the SDD settles`.
_CARD_TEST_COMMAND = re.compile(r"^\*\*Test command:\*\*(.*)$", re.MULTILINE)
_CARD_PRODUCT_PATH = re.compile(r"^\*\*Product path:\*\*(.*)$", re.MULTILINE)
_CARD_DEFINITION = re.compile(r"^\*\*Definition:\*\*(.*)$", re.MULTILINE)
# Where `dependency-repair` leaves its report (`skills/senior-engineer/.claude/skills/
# dependency-repair/SKILL.md` § The report), and the worktrees an unmerged repair leaves it in:
# the repair coins its own key, `<YYYY-MM-DD>_dependency-repair[-n]`.
_REPAIR_REPORT_DIR = "docs/dependency-repair"
_REPAIR_REPORT_SUFFIX = "_report.md"
_REPAIR_WORKTREE = re.compile(r"^\d{4}-\d{2}-\d{2}_dependency-repair")
_NO_SUITE = "none"
# The environment a gate's suite ran in (`core/tools/gate_suite.py`): one declared line in the
# closing marker and in a passing integrity report. The kind is the line's first word, and only
# these four are an environment — `unresolved` names a run that never happened. `none` is the
# card's own no-suite answer and passes only where `Suite: none` would (`card_has_no_suite`).
# `not-ready` is a fifth first word and not a kind: it is the gate's declaration that an
# environment was not ready to run the suite, so it halts the walk by name (`_bad_verdict`)
# and is never in the set.
_ENVIRONMENT_PREFIX = record_declarations.ENVIRONMENT.prefix
_ENVIRONMENT_KINDS = frozenset({"macos-guest", "container", "owners-mac", _NO_SUITE})
_NOT_READY = "not-ready"
_NOT_READY_REASON = "environment-not-ready"
# The language line is `Language resolution:`, or the same words with a parenthesised label
# before the colon. A close after two pauses carried each pause's record under `Language
# resolution (tasks 1 to 3, from <pause SHA>):`, and an exact prefix read that as no record at all,
# halting a finished, green change as missing-language (2026-10-01). The skill now asks
# for one plain heading; this keeps a labelled one from reading as absent.
_LANGUAGE_WORDS = record_declarations.LANGUAGE_RESOLUTION.prefix
_LANGUAGE_HEADING = re.compile(_LANGUAGE_WORDS + r"(?:\s*\([^)]*\))?:")
# The two lines a marker carries when the developer deferred a task it could not land
# (`skills/developer/.claude/skills/development-implementation/SKILL.md` Step 3): `Deferred: task <N> — …` names the
# task, and `Failing: <case id> — task <N>` (or `— no task`) names the task a failing case is in.
_DEFERRED_PREFIX = record_declarations.DEFERRED.prefix
_FAILING_PREFIX = record_declarations.FAILING.prefix
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
# The last ` — ` suffix of the commit holding a deferred task's partial code
# (`skills/developer/.claude/skills/development-implementation/SKILL.md` § Deferring a task,
# `developer: task <N> <slug> — deferred`). Exactly this word.
_DEFERRED_SUFFIX = "deferred"
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
_RELANE_NOTE_START = record_declarations.RELANE_NOTE.prefix
# The developer's note for a TDD-lane task whose failing tests were committed under another
# suffix — `in-progress`, most often, by a run that paused partway through the task (2026-10-29, a
# satellite walk halted missing-red-commit on a finished, green change that had no way back):
# `- Task <N> red saved as <commit> — <what the commit holds and why it is the red>`. The commit is
# 7 to 40 hex characters, either case, optionally in backticks. It counts as the task's red only where
# `landed_without_red` finds it: a non-landing commit of that same task, older than its landing,
# with a pause of this change between the two — the note is a way back for a red an earlier run
# saved, never a way through for a task one run built green-first (`DiskReader.paused_between`).
_SAVED_RED_NOTE = re.compile(r"^- Task (\d+) red saved as `?([0-9a-fA-F]{7,40})`?\s*—(.*)$")
# The largest context, in tokens, a developer run may carry before it is told to pause
# (`.claude/hooks/context_cap.py`). A walk carries its own on the state, so a resumed walk keeps the
# cap it started with; this is what a start with no `--context-cap` records.
DEFAULT_CONTEXT_CAP = 250000
# The environment variable the hook reads. Set for the implementation step alone (`_launch_run`).
_CONTEXT_CAP_VARIABLE = "KENSAIAPP_CONTEXT_CAP"
# The owner's ask to run the gates' suites on their own Mac. Set for the four steps that run a
# card's suite, and only when this walk's owner start carried the ask (`WalkState.gate_owners_mac`).
_GATE_OWNERS_MAC_VARIABLE = gate_suite.OWNERS_MAC_VARIABLE
# The close's passing line on a `behave` card, handed to the seal launch alone (the seal's action
# writes it into the sealed folder). The name carries no `KEY`, `SECRET` or `TOKEN`, which some
# providers' shells drop from a run's environment by default.
CLOSE_VERDICT_VARIABLE = "KENSAIAPP_CLOSE_VERDICT"
_GATE_CONSUMER_STEPS = frozenset({"implementation", "code-integrity", "security", "seal"})

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


# The file an ask of QA's step is left in, inside the change folder of the change worktree.
QA_ASK = "qa_ask.md"


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
    def qa_ask(self) -> str:
        """Where a run of `implementation` or `design` leaves its ask of QA's step: one file in
        the change folder of the change worktree, which `--qa-ask-place` prints."""
        return os.path.join(self.branch_change_folder, QA_ASK)

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
    """Answers what is on disk for one change. Reads only — it launches and writes nothing.

    `draft_body`, when given, stands for the closing marker's body in every read of that body —
    the commit shape's notes, and also the suite, environment and failing-case lines — so the
    developer can ask the marker's verdicts of the record it is about to commit, before the commit
    exists. Only `--check-commit-shape` gives one, and it asks the commit shape alone. Everything
    else is still read off disk."""

    def __init__(self, *, files, git, draft_body: str | None = None):
        self.files = files
        self.git = git
        self.draft_body = draft_body

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
        if self.run_verdict(change, step) is RunVerdict.PASS:
            return True
        if step.evidence is Evidence.STATION_FILE:
            return self.open_station(change.instance_root, change.project) is not None
        if step.evidence is Evidence.CHANGE_OPEN:
            # Any active change means the step landed. More than one is not decided here: the
            # walk needs the key next, and `discover_key` owns that refusal and its wording.
            return bool(self.open_change_keys(change.instance_root, change.project))
        if step.evidence is Evidence.CHANGE_FILE:
            return self.files.is_file(os.path.join(change.branch_change_folder, step.artifact))
        if step.evidence is Evidence.COMMITTED_CHANGE_FILE:
            return self.git.branch_has_path(change.instance_root, change.key,
                                            f"{change.change_rel}/{step.artifact}")
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
        if step == _QA_STEP:
            return RunVerdict.RUN if self.qa_decision(change).applies else RunVerdict.PASS
        gate = step.runs_when
        if gate is None:
            return RunVerdict.RUN
        word = self._declared_word(change, gate)
        if word == gate.runs:
            return RunVerdict.RUN
        if word == gate.passes:
            return RunVerdict.PASS
        return RunVerdict.UNSETTLED

    def qa_decision(self, change: ChangeLayout) -> QaDecision:
        """Whether QA's step applies to this change: `main`'s card and the branch's spec, handed
        to the one decision. Neither is read for anything else here."""
        return qa_step_applies(self._card(change), self.files.read_text(
            os.path.join(change.branch_change_folder, "change_spec.md")))

    def behave_card(self, change: ChangeLayout) -> BehaveCard:
        """What `main`'s project card says about scenarios, through the card half of QA's
        decision. The close reads this and nothing else of the card."""
        return behave_card_reading(self._card(change))

    def qa_way_in(self, change: ChangeLayout) -> str | None:
        """What the product's `docs/nfdr.md` on `main` held when it records no way in, else
        `None` (CP-1321). A card that names no product holds no NFDR, so the file is absent."""
        product = self._product_directory(change)
        return qa_way_in(None if product is None
                         else self.files.read_text(os.path.join(product, "docs", "nfdr.md")))

    def pass_line(self, change: ChangeLayout, step: Step) -> str:
        """The history line for a gated step the walk goes by with no launch."""
        if step == _QA_STEP:
            return f"{step.id} passed — {self.qa_decision(change).read}"
        gate = step.runs_when
        return f"{step.id} passed — {gate.prefix} {gate.passes}"

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
        declared = record_declarations.parse(body).one(record_declarations.BY_PREFIX[gate.prefix])
        if declared is None:
            return f'no "{gate.prefix}" line'
        return f'"{declared.text}", which is neither {gate.runs} nor {gate.passes}'

    def _declared_word(self, change: ChangeLayout, gate: RunsWhen) -> str | None:
        """The first word of the gate line's value, undressed — `None` when the artifact or the
        line is absent, `""` when the line carries no value. Read through the parsed record's
        `PUBLISHES_TEXT` row, as `declared_verdict` and `suite_verdict` read theirs, so
        `**Publishes text:** no` reads as `no`."""
        body = self.files.read_text(os.path.join(change.branch_change_folder, gate.artifact))
        declared = None if body is None else record_declarations.parse(body).one(
            record_declarations.BY_PREFIX[gate.prefix])
        if declared is None:
            return None
        value = declared.text[len(gate.prefix):].strip().strip(_EMPHASIS).split(maxsplit=1)
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

    def current_task(self, change: ChangeLayout, product_path: str) -> tuple[int, int] | None:
        """Which task of `tl_instruction.md` a developer run is on, as `(place, count)`: the place,
        in plan order, of the task after the furthest one that has a landing or a deferred commit,
        and how many tasks the plan lists. `None` when the instruction is unreadable or lists
        none, or when every task is behind the run — it is closing, not on a task.

        A task deferred with only its red commit has nothing that says it is behind the run, so
        it reads as the current task until a later one lands."""
        text = self.files.read_text(os.path.join(change.branch_change_folder, "tl_instruction.md"))
        tasks = list(dict.fromkeys(int(number) for number in _TASK_HEADING.findall(text or "")))
        if not tasks:
            return None
        behind = set()
        for _sha, subject in self.git.commits_ahead(self.code_repo(change, product_path), _MAIN,
                                                    change.key):
            task = _TASK_COMMIT.match(subject)
            if task and (self._lands(task.group(2))
                         or self._last_suffix(task.group(2)) == _DEFERRED_SUFFIX):
                behind.add(int(task.group(1)))
        furthest = max((place for place, number in enumerate(tasks, 1) if number in behind),
                       default=0)
        return None if furthest == len(tasks) else (furthest + 1, len(tasks))

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

    def landed_without_red(self, repo: str, key: str, tasks: list[int],
                           saved_reds: dict[int, set[str]] | None = None,
                           paused_between=None) -> list[int]:
        """Those of `tasks`, ascending and each once, that have a landing commit on `repo`'s
        `main..<key>` and no red commit older than their oldest landing (CP-189, CP-191). A task
        with no landing is not returned: a missing landing is another obligation's.

        `saved_reds` maps a task to the commit prefixes its saved-red notes name
        (`saved_red_commits`). A non-landing commit of that task whose SHA opens with one of them is
        its red whatever its suffix, when `paused_between(named, landing)` answers that a pause of
        the change lies between it and the task's oldest landing; a named commit that is another
        task's, a landing one, not on the branch, or made by the run that landed the task counts
        for nothing.

        "Older" is position in the one list `commits_ahead` answers, newest first — never author
        time, which `_worked_after` needs only because it compares two repos, and which would tie a
        red and a green made within one second."""
        # Each task's OLDEST landing and oldest red: the list is newest first, so a later position
        # is an older commit, and each write below keeps the oldest seen so far.
        landing: dict[int, tuple[int, str]] = {}
        red: dict[int, int] = {}
        saved: dict[int, list[tuple[int, str]]] = {}
        for position, (sha, subject) in enumerate(self.git.commits_ahead(repo, _MAIN, key)):
            task = _TASK_COMMIT.match(subject)
            if not task:
                continue
            number = int(task.group(1))
            if self._lands(task.group(2)):
                landing[number] = (position, sha)
            elif self._last_suffix(task.group(2)) == _RED_SUFFIX:
                red[number] = position
            elif any(sha.startswith(prefix) for prefix in (saved_reds or {}).get(number, ())):
                saved.setdefault(number, []).append((position, sha))
        for number, (landed_at, landing_sha) in landing.items():
            for position, sha in saved.get(number, ()):
                if (position > landed_at and paused_between is not None
                        and paused_between(sha, landing_sha)):
                    red[number] = max(red.get(number, -1), position)
        return sorted(number for number in set(tasks)
                      if number in landing and red.get(number, -1) < landing[number][0])

    def suite_verdict(self, change: ChangeLayout) -> str | None:
        """The closing marker's declared `Suite:` value — `"green"`, `"red"`, `"none"` (passes
        only when `main`'s card reads `Test command: none`, `card_has_no_suite`), or `None` when the marker
        carries no such line at all (or there is no marker yet)."""
        declared = self._marker_record(change).one(record_declarations.SUITE)
        if declared is None:
            return None
        # The verdict is the value's FIRST WORD. The developer writes this body by hand and
        # reaches for the evidence — `Suite: green — python3 -m pytest …, 5083 passed` — which an
        # exact read calls no verdict at all and halts a finished change as missing-suite (twice on
        # 2026-09-22). What follows the verdict is the record, and it never changes what was
        # declared: a dressed `red` still halts.
        value = declared.text[len(_SUITE_PREFIX):].strip().split(maxsplit=1)
        return value[0].strip("*_`") if value else ""

    def marker_environment_kinds(self, change: ChangeLayout) -> list[str]:
        """The kind of each `Environment:` line in the closing marker's first run of consecutive
        `Environment:` lines, in order — one per container cell a gate ran. Empty when the marker
        declares none. Read from the same parsed record `suite_verdict` reads, so a dressed line
        declares and a mention does not. Nor does a line that opens with `Environment:` after the
        first run has ended."""
        return [self._environment_kind(line.text)
                for line in self._marker_record(change).read(record_declarations.ENVIRONMENT)]

    def report_environment_kinds(self, change: ChangeLayout, step: Step) -> list[str]:
        """The kind of each `Environment:` line in the first run of consecutive `Environment:`
        lines in the step's own report, in order. A line that opens with `Environment:` after that
        run has ended declares nothing."""
        report = self._change_file_record(change, step.artifact)
        return [] if report is None else [
            self._environment_kind(line.text)
            for line in report.read(record_declarations.ENVIRONMENT)]

    def marker_environment_kind(self, change: ChangeLayout) -> str | None:
        """The kind of the closing marker's first `Environment:` line, or `None` when it has
        none. A compatibility query: the verdict reads `marker_environment_kinds`."""
        kinds = self.marker_environment_kinds(change)
        return kinds[0] if kinds else None

    def report_environment_kind(self, change: ChangeLayout, step: Step) -> str | None:
        """The kind of the first `Environment:` line in `step`'s own report, or `None`."""
        kinds = self.report_environment_kinds(change, step)
        return kinds[0] if kinds else None

    @staticmethod
    def _environment_kind(declared: str) -> str:
        """The first word of the declaration's value, case kept — `""` when the line has none."""
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

    def has_nfdr(self, change: ChangeLayout) -> bool:
        """Whether `docs/nfdr.md` exists under the card's `Product path:` on `main`. A card that
        cannot be read, or has no such line, names no product, so the answer is False and
        `dependency-repair` is not launched."""
        product = self._product_directory(change)
        return product is not None and self.files.is_file(os.path.join(product, "docs", "nfdr.md"))

    def _product_directory(self, change: ChangeLayout) -> str | None:
        """The product the card's `Product path:` names, as the instance's `main` checkout holds
        it: a relative path is read from the instance root, an absolute one as written. `main`'s
        card and not the branch's, for `card_has_no_suite`'s reason. `None` when the card cannot
        be read, or has no such line or an empty one."""
        found = _CARD_PRODUCT_PATH.search(self._card(change) or "")
        if found is None:
            return None
        value = found.group(1).split("<!--", 1)[0].strip().strip(_EMPHASIS).strip()
        if not value:
            return None
        return os.path.join(change.instance_root, value)  # an absolute `value` wins the join

    def _card(self, change: ChangeLayout) -> str | None:
        return self.files.read_text(os.path.join(change.instance_root, "system", "projects",
                                                 change.project, "project.md"))

    def definition(self, change: ChangeLayout) -> str | None:
        """The `**Definition:**` value of the project card on `main`, cut at its trailing comment
        and undressed of code and bold markup, with its case kept (CP-1103): `full` and `Full`
        are two answers. `None` when the card cannot be read, or has no such line or an empty
        one. `main`'s card and not the branch's, so a run of the change cannot edit it."""
        found = _CARD_DEFINITION.search(self._card(change) or "")
        if found is None:
            return None
        return found.group(1).split("<!--", 1)[0].strip().strip(_EMPHASIS).strip() or None

    def item_held_open(self, change: ChangeLayout, companion: str, title: str) -> bool:
        """Whether the product's main checkout holds the item open (CP-1108, CP-1109): the file
        `docs/<companion>` exists, and the `## ` section whose heading contains `Raised from
        downstream` holds a `### ` heading whose text, once its leading number is removed,
        equals `title`. HTML comments are not read. A missing or unreadable file, and a path that
        does not stay under `docs/`, hold nothing."""
        path = self.main_companion_path(change, companion)
        if path is None:
            return False
        text = self.files.read_text(path)
        return text is not None and _holds_item_open(text, title)

    def main_companion_path(self, change: ChangeLayout, companion: str) -> str | None:
        """The companion's path in the product's main checkout, or `None` when the card names no
        product or `companion` does not stay under `docs/`."""
        product = self._product_directory(change)
        return None if product is None else _under_docs(product, companion)

    def companion_template(self, core_dir: str, companion: str) -> str | None:
        """The text of `companion`'s template (CP-1425): the file in `<core_dir>/templates/
        product-templates/` named for the companion's file name with `_template` put before `.md`,
        the two compared without regard to case. `None` for a name with a directory part, when
        no file matches, and when the match cannot be read."""
        if "/" in companion:
            return None
        wanted = companion.casefold().removesuffix(".md") + "_template.md"
        folder = os.path.join(core_dir, "templates", "product-templates")
        name = next((entry for entry in self.files.list_dir(folder)
                     if entry.casefold() == wanted), None)
        return None if name is None else self.files.read_text(os.path.join(folder, name))

    def carry_repository(self, change: ChangeLayout) -> str | None:
        """The repository whose main checkout holds the companion (CP-1126): git's top level for
        the card's product directory. `None` when the card names no product or the directory is
        in no repository."""
        product = self._product_directory(change)
        return None if product is None else self.git.toplevel(product)

    def checkout_branch(self, repository: str) -> str | None:
        """The branch `repository`'s checkout has out; `None` when it is detached or git cannot
        say."""
        return self.git.current_branch(repository)

    def path_status(self, repository: str, relative: str) -> list[str] | None:
        """The `git status --porcelain` lines for one repository-relative path, empty when it is
        clean; `None` when git cannot answer."""
        return self.git.path_status(repository, relative)

    def worktree_companion_path(self, change: ChangeLayout, companion: str) -> str | None:
        """The same companion in the change's worktree of the carry's repository:
        `<repository>/.worktrees/<key>/<product directory relative to repository>/docs/...`. Git
        gives a resolved top level, so the offset is taken from the real path of each. `None`
        when there is no repository or `companion` does not stay under `docs/`."""
        product = self._product_directory(change)
        repository = self.carry_repository(change)
        if product is None or repository is None:
            return None
        offset = os.path.relpath(os.path.realpath(product), os.path.realpath(repository))
        worktree_product = os.path.normpath(
            os.path.join(repository, ".worktrees", change.key, offset))
        return _under_docs(worktree_product, companion)

    def repair_reports(self, change: ChangeLayout) -> list[str]:
        """The sorted path of every `*_report.md` under `system/projects/<project>/docs/
        dependency-repair/` that exists now: in the instance's main checkout, and in each
        `.worktrees/<YYYY-MM-DD>_dependency-repair*` worktree of it, where an unmerged repair
        leaves its report (CP-862)."""
        relative = os.path.join("system", "projects", change.project, _REPAIR_REPORT_DIR)
        roots = [change.instance_root]
        worktrees = os.path.join(change.instance_root, ".worktrees")
        roots += [os.path.join(worktrees, entry) for entry in self.files.list_dir(worktrees)
                  if _REPAIR_WORKTREE.match(entry)]
        reports = []
        for root in roots:
            folder = os.path.join(root, relative)
            reports += [os.path.join(folder, entry) for entry in self.files.list_dir(folder)
                        if entry.endswith(_REPAIR_REPORT_SUFFIX)
                        and self.files.is_file(os.path.join(folder, entry))]
        return sorted(reports)

    def repair_verdict(self, path: str) -> str | None:
        """The first word of the report's `Repair:` line, undressed, or `None` when the report
        cannot be read or carries no such line (CP-862). A line with no value reads `""`."""
        body = self.files.read_text(path)
        declared = None if body is None else record_declarations.parse(body).one(
            record_declarations.REPAIR)
        if declared is None:
            return None
        value = declared.text[len(record_declarations.REPAIR.prefix):].strip().strip(
            _EMPHASIS).split(maxsplit=1)
        return value[0].strip(_EMPHASIS) if value else ""

    def language_resolved(self, change: ChangeLayout) -> bool:
        """Whether the closing marker declares a `Language resolution:` line at all — the
        `LANGUAGE_RESOLUTION` row of the parsed record `suite_verdict` reads, matched by
        `_LANGUAGE_HEADING` so a labelled heading counts as the declaration it is."""
        return any(_LANGUAGE_HEADING.match(line.text) for line
                   in self._marker_record(change).read(record_declarations.LANGUAGE_RESOLUTION))

    def declared_verdict(self, change: ChangeLayout, step: Step) -> str | None:
        """The value of the first line in `step`'s own report that starts with its
        `declared_prefix`, or `None` when the report carries no such line — a step whose
        `declared_prefix` is empty never reports one. Reads the report through the same
        `files.read_text` path `is_done` already checks, parsed by the same
        `record_declarations.parse` a commit body goes through, and takes the row of the step's
        prefix from `BY_PREFIX`, so there is only one scan to trust."""
        if not step.declared_prefix:
            return None
        report = self._change_file_record(change, step.artifact)
        if report is None:
            return None
        declared = report.one(record_declarations.BY_PREFIX[step.declared_prefix])
        return None if declared is None else declared.text[len(step.declared_prefix):].strip()

    def deferrals(self, change: ChangeLayout) -> list[str]:
        """Every `Deferred:` line of the closing marker's body, undressed, in body order — `[]`
        when there is no marker. One line per deferred task, whatever its reason."""
        return [line.text
                for line in self._marker_record(change).read(record_declarations.DEFERRED)]

    def relaned_tasks(self, change: ChangeLayout) -> set[int]:
        """The tasks the closing marker's body re-lanes: every line in `_RELANE_NOTE`'s form.
        Empty when there is no marker. Read by the note's own line form anywhere in the body rather
        than by locating the `Developer Review Notes` section, which has no fixed end in a marker
        body."""
        relaned = set()
        for line in self._marker_record(change).read(record_declarations.RELANE_NOTE):
            note = _RELANE_NOTE.match(line.text)
            # A note with no reason records none, so it re-lanes nothing (CP-190).
            if note and note.group(2).strip().strip(_EMPHASIS).strip():
                relaned.add(int(note.group(1)))
        return relaned

    def paused_between(self, change: ChangeLayout, repo: str, older: str, newer: str) -> bool:
        """Whether a pause commit of this change lies between `older` and `newer`, two commits of
        `repo`'s `main..<key>`. Where the pause is in `repo`'s own history, by position there — a
        red saved and the pause after it can land in one second. Otherwise, for an external
        product, by author time as `_worked_after` reads it: the pause no earlier than `older`, and
        `newer` strictly after the pause. A time git cannot read answers no pause."""
        pauses = [sha for sha, subject in self._own_commits(change)
                  if _PAUSE_SUBJECT.search(subject)]
        order = [sha for sha, _subject in self.git.commits_ahead(repo, _MAIN, change.key)]
        if older not in order or newer not in order:
            return False
        for pause in pauses:
            if pause in order:
                # Newest first: `newer` above the pause, the pause above `older`.
                if order.index(newer) < order.index(pause) < order.index(older):
                    return True
                continue
            paused_at = self.git.author_time(change.instance_root, pause)
            older_at = self.git.author_time(repo, older)
            newer_at = self.git.author_time(repo, newer)
            if None not in (paused_at, older_at, newer_at) and older_at <= paused_at < newer_at:
                return True
        return False

    def saved_red_commits(self, change: ChangeLayout) -> dict[int, set[str]]:
        """The commits the closing marker's body names as a task's red under another suffix: every
        line in `_SAVED_RED_NOTE`'s form, task to the prefixes named for it. Empty when there is no
        marker. A note with no reason names nothing, as a re-lane note's does (CP-190). Whether a
        named commit is that task's red is `landed_without_red`'s to judge."""
        named: dict[int, set[str]] = {}
        for line in self._marker_record(change).read(record_declarations.RELANE_NOTE):
            note = _SAVED_RED_NOTE.match(line.text)
            if note and note.group(3).strip().strip(_EMPHASIS).strip():
                named.setdefault(int(note.group(1)), set()).add(note.group(2).lower())
        return named

    def failing_cases(self, change: ChangeLayout) -> list[str]:
        """Each `Failing:` line in the first run of consecutive `Failing:` lines in the closing
        marker's body, undressed, in body order, and none when there is no marker. The engine runs
        no tests, so these lines are the only way the marker shows which task a red case belongs
        to. A line that opens with `Failing:` after that run has ended declares no case."""
        return [line.text
                for line in self._marker_record(change).read(record_declarations.FAILING)]

    def _marker_record(self, change: ChangeLayout) -> record_declarations.ParsedRecord:
        """The closing marker's body, parsed — an empty record when there is no marker. A field is
        asked of it by its row, never by a bare prefix: a mention inside `Developer Review Notes`
        elsewhere in the body must not read as the declaration, and the row says where a
        declaration may appear."""
        if self.draft_body is not None:
            return record_declarations.parse(self.draft_body)
        sha = self.marker_commit(change)
        if sha is None:
            return record_declarations.parse("")
        return record_declarations.parse(self.git.commit_body(change.instance_root, sha))

    def _change_file_record(self, change: ChangeLayout,
                            name: str) -> record_declarations.ParsedRecord | None:
        """A file of the change folder on the branch, parsed — `None` when the file is absent."""
        body = self.files.read_text(os.path.join(change.branch_change_folder, name))
        return None if body is None else record_declarations.parse(body)

    def audited(self, change: ChangeLayout, step: Step) -> tuple[str, ...]:
        """The steps `step` audits on this change: its `fans_out_over`, less a gated step the
        change's own records do not run, which produced nothing to read, and less a step whose
        artifact is `ad-hoc-plan`'s stub, which no run of that step wrote."""
        return tuple(skill for skill in step.fans_out_over
                     if (skill not in _GATED_BY_SKILL
                         or self.run_verdict(change, _GATED_BY_SKILL[skill]) is RunVerdict.RUN)
                     and not self.stubbed(change, skill))

    def stubbed(self, change: ChangeLayout, skill: str) -> bool:
        """Whether the change branch's copy of `skill`'s artifact is `ad-hoc-plan`'s stub: its
        `Planned by:` line's first word is exactly `ad-hoc-plan`. A step with no stub, a missing
        file or a missing line is not stubbed, so it is audited as before."""
        artifact = _STUB_ARTIFACT.get(skill)
        if artifact is None:
            return False
        body = self.files.read_text(os.path.join(change.branch_change_folder, artifact))
        declared = None if body is None else record_declarations.parse(body).one(
            record_declarations.PLANNED_BY)
        if declared is None:
            return False
        value = declared.text[len(record_declarations.PLANNED_BY.prefix):].strip().strip(
            _EMPHASIS).split(maxsplit=1)
        return bool(value) and value[0].strip(_EMPHASIS) == _STUBBED_BY

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
            if (candidate.runs_when is not None or candidate == _QA_STEP) and any(
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


    def branch_tip(self, repo: str, branch: str) -> str | None:
        """The commit `branch` points at in `repo`, or `None` when it does not exist."""
        return self.git.branch_tip(repo, branch)

    def halt_snapshot(self, change: ChangeLayout) -> dict | None:
        """Identify inherited report bytes without copying their content into chain state.
        Unreadable reports have no snapshot, so they cannot be dismissed as unchanged.
        """
        path = self.halt_report(change)
        text = self.files.read_text(path) if path else None
        if text is None:
            return None
        return {"path": path, "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()}

    def halt_reason(self, path: str) -> str | None:
        """The halt report's reason: the first non-blank line under its `## Halt Reason` heading,
        read with HTML comments removed and undressed of surrounding whitespace, backticks and
        `*`, case kept (CP-1101). `None` when the report cannot be read, has no such heading, or
        nothing non-blank follows it before the next heading. Only the first heading is read."""
        text = self.files.read_text(path)
        if text is None:
            return None
        lines = _report_lines(_HTML_COMMENT.sub("", text))
        heading = next((index for index, line in enumerate(lines)
                        if line.rstrip() == _HALT_REASON_HEADING), None)
        if heading is None:
            return None
        first = next((line for line in lines[heading + 1:] if line.strip()), None)
        if first is None or first.lstrip().startswith("#"):
            return None
        return first.strip().strip(_REASON_DRESSING).strip() or None

    def raised_items(self, path: str) -> list[str]:
        """The `Raised item:` values of the halt report, in report order: the text after
        `Raised item: ` on each line that begins with it, taken as given (CP-1102). Read from the
        whole report, comments included, so a template line left behind errs toward a halt that
        names it. `[]` when the report cannot be read."""
        text = self.files.read_text(path)
        if text is None:
            return []
        return [line[len(_RAISED_ITEM_PREFIX):] for line in _report_lines(text)
                if line.startswith(_RAISED_ITEM_PREFIX)]

    @staticmethod
    def split_raised_item(value: str) -> tuple[str, str] | None:
        """A raised item's companion path and title, or `None` when the value is unreadable
        (CP-1102): the path is the text before the first ` § `, the title the text after the
        first ` — ` that follows it, and a missing separator or an empty part is unreadable."""
        path, section_sign, rest = value.partition(_ITEM_SECTION_SIGN)
        _, dash, title = rest.partition(_ITEM_TITLE_DASH)
        if not section_sign or not dash or not path or not title:
            return None
        return path, title


# --- the walk's own record ------------------------------------------------------------------

STATE_SCHEMA = 1

# Each table's own name — the walk's identity, carried on the state and worn by its shim, its log,
# its telemetry tag and every message the owner reads. A module constant could not say which of two
# walks a message came from.
CHAIN_NAMES: dict[int, str] = {id(CHANGE_STEPS): "change", id(WALK_STEPS): "walk"}


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
    chain_name: str = "change"
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
    # fresh start carrying `--gate-owners-mac` sets it — the owner's, or a build-idea queue's that
    # holds the ask — and no card, product record or inherited variable does; every later launch
    # of the walk reads it from here. Defaulted, so an older state file still loads.
    gate_owners_mac: bool = False
    # How many times this walk launched `dependency-repair` (CP-861: at most one), and the reports
    # that existed when it did, so its own is the one that is new (CP-862). Both defaulted, so an
    # older state file still loads.
    repairs: int = 0
    repair_reports_before: list = field(default_factory=list)
    # How many times this walk launched `product-docs` for a `records-owed` halt (CP-1106: at most
    # one), the id of the step whose halt it answered, and the report's named items in report order
    # with whether the main checkout held each one open at the launch (CP-1108). All defaulted, so
    # an older state file still loads (CP-1114).
    sweeps: int = 0
    sweep_step: str = ""
    sweep_items: list = field(default_factory=list)
    # QA's step: how many times it was run once more for a missing red commit (CP-1319: one),
    # the step whose red the repair answers (empty reads as the closing marker's), and the
    # scenarios `main` was red on when it did. All defaulted, so an older state file still loads.
    qa_retries: int = 0
    repair_step: str = ""
    qa_main_red: str = ""
    # The re-run an accepted ask starts has one retry of its own for a missing red commit,
    # whether or not QA's first run spent its own. Defaulted, so an older state file still loads.
    qa_rerun_retries: int = 0
    # Whether the close has passed in this walk (CP-1379). No verdict survives a walk: a start
    # builds a fresh state, so a walk entered at `audit` or `seal` runs the close first. Defaulted,
    # so an older state file still loads.
    close_passed: bool = False
    # The exact `close passed — …` history line the close recorded on a `behave` card, handed to the
    # seal launch (`CLOSE_VERDICT_VARIABLE`) and to no other. Empty on every other card, and for a
    # state written before it existed.
    close_line: str = ""
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

    def __init__(self, files, path: str, chain_name: str = "change"):
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


def ask_reason(text: str) -> str:
    """An ask's reason: its text with every run of whitespace collapsed to one space, and trimmed.
    Nothing else in the ask file is read."""
    return " ".join(text.split())


class QaAskPhase(str, Enum):
    """Where an accepted ask is: QA's step is being run again, or the walk has returned to the
    seat that asked. A closed set that is written to disk and read back."""

    RE_RUN = "re-run"
    RETURN = "return"


QA_ASK_ACCEPTED = "accepted"


@dataclass
class QaAsks:
    """What one change keeps across every walk of it: how many runs of QA's step it has had, every
    ask the engine has answered, and the accepted ask not yet returned to its asker."""

    runs: int = 0
    answered: list = field(default_factory=list)
    open: dict | None = None

    def accepted(self, step_id: str) -> bool:
        return any(entry["step"] == step_id and entry["answer"] == QA_ASK_ACCEPTED
                   for entry in self.answered)

    def step_owed(self) -> str | None:
        """The step an open ask owes the walk: QA's while its re-run is owed, the asker's once the
        re-run has landed. `None` when no ask is open."""
        if self.open is None:
            return None
        if self.open["phase"] == QaAskPhase.RE_RUN.value:
            return _QA_STEP.id
        return self.open["asker"]

    def to_json(self) -> dict:
        return asdict(self)

    @classmethod
    def from_json(cls, data: dict) -> "QaAsks":
        """Unknown keys ignored, as `WalkState.from_json` does."""
        names = {entry.name for entry in fields(cls)}
        return cls(**{name: value for name, value in data.items() if name in names})



class QaAskStore:
    """The per-change record behind a seam, kept beside the walks' state files so the `change` and
    `walk` walks of one project share it. Reaches the disk only through `files`."""

    def __init__(self, files, directory: str):
        self.files = files
        self.directory = directory

    def path(self, project: str, key: str) -> str:
        return os.path.join(self.directory, f"chain-qa-{project}-{key}.json")

    def load(self, project: str, key: str) -> QaAsks:
        """An absent or unreadable record reads as an empty one, as `StateStore.raw` reads a bad
        state file; the record is only ever written whole."""
        text = self.files.read_text(self.path(project, key))
        if text is None:
            return QaAsks()
        try:
            data = json.loads(text)
        except ValueError:
            return QaAsks()
        return QaAsks.from_json(data) if isinstance(data, dict) else QaAsks()

    def save(self, project: str, key: str, asks: QaAsks) -> None:
        path = self.path(project, key)
        self.files.make_dirs(os.path.dirname(path))
        temporary = f"{path}.tmp"
        text = json.dumps(asks.to_json(), indent=2, sort_keys=True)
        self.files.write_text(temporary, text + "\n")
        self.files.replace(temporary, path)

    def keep(self, project: str, key: str, number: int, ask_path: str) -> str:
        """Move the answered ask out of the change folder to a numbered file beside the record, so
        it is never read again and no untracked file is left for the delivery's clean-tree check."""
        kept = os.path.join(self.directory, f"chain-qa-{project}-{key}.ask-{number}.md")
        self.files.replace(ask_path, kept)
        return kept


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

# What a `records-owed` halt report is read by (CP-1101, CP-1102). The reason's dressing is
# exactly the backticks and `*` CP-1101 lists: `record_declarations.EMPHASIS` also strips `_`, which
# would read `_records-owed_` as the reason.
_HALT_REASON_HEADING = "## Halt Reason"
_REASON_DRESSING = "`*"
_RAISED_ITEM_PREFIX = "Raised item: "
_ITEM_SECTION_SIGN = " § "
_ITEM_TITLE_DASH = " — "
_RAISED_SECTION = "Raised from downstream"
_ITEM_HEADING = re.compile(r"^### +(?:[0-9.]+(?:\s+|$))?(.*?)\s*$")
_SECTION_END = re.compile(r"^#{1,2}(?:\s|$)")
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)

# The `records-owed` route (CP-1101–CP-1108). The halt is answered only from these steps, on a
# card whose `**Definition:**` is exactly `full`. The sweep's run sits outside both step tables like
# the repair, has no provider-file entry, and is named so no table step uses its word.
_RECORDS_OWED = "records-owed"
_RECORDS_OWED_STEPS = frozenset({"specs", "design", "plan"})
_FULL_DEFINITION = "full"
_SWEEP_RUN = "records-sweep"
# Where a folded, sealed sweep restarts the change: the step that raised the records is run again
# from its start, on a branch cut fresh from the records the sweep settled (CP-1112).
_REENTRY_STEP = "specs"
_SWEEP_SKILL = "product-docs"
# What the carry writes on `main` (CP-1126). The commit's words are the content step's, placed
# whole: one subject, body and progress clause for one item, another for two or more.
_CARRY_SUBJECT = "{seat}: {key} — raised {things} carried onto main for the document sweep"
_CARRY_BODY_ONE = ("The {step} step raised this item in the change's worktree and halted "
                   "records-owed. The walk copies it onto main as the step wrote it, so the "
                   "document sweep finds it open and can fold it.")
_CARRY_BODY_MANY = ("The {step} step raised these items in the change's worktree and halted "
                    "records-owed. The walk copies each onto main as the step wrote it, so the "
                    "document sweep finds it open and can fold it.")
_CARRY_PROGRESS = "carries {key}'s raised {things} onto main for the document sweep"
_CARRY_REFUSED = "{owed} — cannot carry onto main: {why}"
_CARRY_NO_SURFACE = "no surface for provider {provider}"
_CARRY_BRANCH = "{repository} is on {branch}"
_CARRY_DIRTY = "{companion} has uncommitted changes"
_CARRY_UNREADABLE = "git could not read the status of {companion}"
_CARRY_FAILED = "{owed} — carrying onto main failed: commit_builder exited {code}"
_CARRY_RESTORE_FAILED = "restoring {companion} exited {code}"
_NO_BRANCH = "detached"
# What a walk's own runs are launched with and the sweep is not: the sweep is another walk's, with
# its own state and its own stop, so it takes none of this walk's per-run variables.
_SWEEP_REMOVED_VARIABLES = (
    "DETACH_WATCHER_ON_COMPLETE", "INSTRUMENT_RUN_CHAIN", "INSTRUMENT_RUN_WALK_ID",
    "INSTRUMENT_RUN_ROLE", "INSTRUMENT_RUN_AUDIT_TARGET", _CONTEXT_CAP_VARIABLE,
    _GATE_OWNERS_MAC_VARIABLE, CLOSE_VERDICT_VARIABLE)


def engine_report_marker(step: Step) -> str:
    """The first line of a `halt_report.md` this engine wrote for `step`, and the only thing that
    tells it from a seat's own report: the engine moves a report that starts with it and leaves
    every other one where it is."""
    return f"chain_development — halt at the {step.id} step: no {step.runs_when.prefix} verdict"


def _report_lines(text: str) -> list[str]:
    """A report's lines, split on newlines alone: `str.splitlines` also splits on characters a
    raised item may hold, and an item is taken as the report gives it."""
    return [line.removesuffix("\r") for line in text.split("\n")]


_ITEM_BLOCK_END = re.compile(r"^#{1,3}(?:\s|$)")
_NOT_A_LINE_ENDING = re.compile(r"[^\r\n]")


def _under_docs(product: str, companion: str) -> str | None:
    """`docs/<companion>` under `product`, normalised, or `None` when `companion` does not stay
    under `docs/` (an absolute path wins the join and leaves it)."""
    docs = os.path.normpath(os.path.join(product, "docs"))
    path = os.path.normpath(os.path.join(docs, companion))
    return path if path.startswith(docs + os.sep) else None


def _lines_keeping_ends(text: str) -> list[str]:
    """`text` cut on `\n` alone, each line keeping its own ending, so joining them gives `text`
    back byte for byte. `str.splitlines` also cuts on characters a record may hold."""
    parts = text.split("\n")
    lines = [part + "\n" for part in parts[:-1]]
    return (lines + [parts[-1]]) if parts[-1] else lines


def _visible_lines(lines: list[str]) -> list[str]:
    """What each of `lines` reads as once HTML comments are not read: the same lines, a comment's
    characters blanked and every line ending kept, so a visible line and its raw line share an
    index and a heading inside a comment is no heading (CP-1108, CP-1125)."""
    blanked = _HTML_COMMENT.sub(lambda comment: _NOT_A_LINE_ENDING.sub(" ", comment.group()),
                                "".join(lines))
    return [line.rstrip("\r\n") for line in _lines_keeping_ends(blanked)]


def _raised_section(visible: list[str]) -> tuple[int, int] | None:
    """`(first, end)`: the index of the heading line of the first `## ` section whose heading
    contains `Raised from downstream`, and the index of the line that ends it — the next
    level-one or level-two heading, or the number of lines. `None` when there is no such
    section."""
    for first, line in enumerate(visible):
        if line.startswith("## ") and _RAISED_SECTION in line:
            end = next((index for index in range(first + 1, len(visible))
                        if _SECTION_END.match(visible[index])), len(visible))
            return first, end
    return None


@dataclass(frozen=True)
class _CarriedFile:
    """One main-checkout companion the carry writes: where it is, its name as the raised items
    give it, its path in the repository, what it holds before the carry (`None` where the carry
    creates the file) and after it, and the raised items going into it, in report order."""
    path: str
    companion: str
    relative: str
    before: str | None
    after: str
    values: tuple[str, ...]


def _item_heading_title(line: str) -> str | None:
    heading = _ITEM_HEADING.match(line)
    return heading.group(1) if heading else None


def _holds_item_open(text: str, title: str) -> bool:
    """Whether a companion's `text` holds `title` open (CP-1108): under every `## ` section whose
    heading contains `Raised from downstream` there is a `### ` heading whose text, once its
    leading number is removed, equals `title`. HTML comments are not read: they are removed and
    the text left is read, as CP-1108 always read it. `_visible_lines` blanks them in place
    instead, which an item's extent needs, and which would stop a heading that a comment opens
    its line with from being one."""
    inside = False
    for line in _report_lines(_HTML_COMMENT.sub("", text)):
        if _SECTION_END.match(line):
            inside = line.startswith("## ") and _RAISED_SECTION in line
        elif inside and _item_heading_title(line) == title:
            return True
    return False


def _extract_item(text: str, title: str) -> str | None:
    """The lines of the first item titled `title` in the *Raised from downstream* section of a
    companion's `text` (CP-1125): from its `### ` heading up to, not including, the next heading
    of level one to three outside a comment, or the end, trailing blank lines left out, every
    line ending as the text holds it. `None` when the section holds no such item."""
    lines = _lines_keeping_ends(text)
    visible = _visible_lines(lines)
    section = _raised_section(visible)
    if section is None:
        return None
    first, end = section
    start = next((index for index in range(first + 1, end)
                  if _item_heading_title(visible[index]) == title), None)
    if start is None:
        return None
    stop = next((index for index in range(start + 1, end)
                 if _ITEM_BLOCK_END.match(visible[index])), end)
    while stop > start + 1 and not lines[stop - 1].strip():
        stop -= 1
    return "".join(lines[start:stop])


def _append_items(text: str, blocks: list[str]) -> str | None:
    """A companion's `text` with `blocks` added at the end of its *Raised from downstream*
    section (CP-1125): after the section's last non-blank line, each block preceded by one blank
    line, and one blank line kept before a heading that follows. The added lines take the line
    ending of the section's last line; every byte outside the insertion is as it was. `None`
    when the text has no such section."""
    lines = _lines_keeping_ends(text)
    section = _raised_section(_visible_lines(lines))
    if section is None:
        return None
    first, end = section
    last = next(index for index in range(end - 1, first - 1, -1)
                if index == first or lines[index].strip())
    ending = next(("\r\n" if line.endswith("\r\n") else "\n"
                  for line in reversed(lines[:last + 1]) if line.endswith("\n")), "\n")
    added = []
    for block in blocks:
        added += [ending] + [line.rstrip("\r\n") + ending
                             for line in _lines_keeping_ends(block)]
    if last + 1 < len(lines) and lines[last + 1].strip():
        added.append(ending)
    closed_last = lines[last].rstrip("\r\n") + ending if not lines[last].endswith("\n") \
        else lines[last]
    return "".join(lines[:last] + [closed_last] + added + lines[last + 1:])


_TITLE_TOKEN = re.compile(r"<[^<>]*>")
_NONE_UNDER_SECTION = "None."


def _without_frontmatter(template: str) -> str:
    """`template` with a leading frontmatter block removed: a first line `---` through the next
    `---`. A text that does not open with one is returned as it is."""
    lines = template.split("\n")
    if lines[0].strip() != "---":
        return template
    end = next((index for index in range(1, len(lines)) if lines[index].strip() == "---"), None)
    return template if end is None else "\n".join(lines[end + 1:])


def _raised_heading(template: str) -> str | None:
    """The first `## ` heading of a companion template, comments not read, whose text contains
    `Raised from downstream`, as the template writes it; `None` when it has none."""
    for line in _report_lines(_HTML_COMMENT.sub("", template)):
        if line.startswith("## ") and _RAISED_SECTION in line:
            return line.rstrip()
    return None


def _companion_from_template(template: str, project: str, blocks: list[str]) -> str:
    """The text of a companion the carry creates from `template` (CP-1427): the template's `# `
    title with its `<...>` token replaced by `project`, the lines between the title and the first
    `## ` heading, every `## ` heading in the template's order, `None.` under each heading but
    the one holding `Raised from downstream`, and `blocks` under that one. Nothing else of the
    template survives: not its frontmatter, comments, example items or guidance. Ends with one
    line ending. A template with no such heading cannot hold `blocks` and raises."""
    lines = _report_lines(_HTML_COMMENT.sub("", _without_frontmatter(template)))
    title = next(index for index, line in enumerate(lines) if line.startswith("# "))
    headings = [index for index in range(title + 1, len(lines)) if lines[index].startswith("## ")]
    preamble_end = headings[0] if headings else len(lines)
    preamble = "\n".join(lines[title + 1:preamble_end]).strip("\n")
    parts = [_TITLE_TOKEN.sub(lambda _: project, lines[title].rstrip())]
    if preamble.strip():
        parts.append(preamble)
    parts += [heading if _RAISED_SECTION in heading else f"{heading}\n\n{_NONE_UNDER_SECTION}"
              for heading in (lines[index].rstrip() for index in headings)]
    skeleton = "\n\n".join(parts) + "\n"
    placed = _append_items(skeleton, blocks)
    if placed is None:
        raise ValueError(f"the template has no `## ` heading containing {_RAISED_SECTION!r}")
    return placed


def _with_raised_section(text: str, heading: str) -> str:
    """A companion's `text` with `heading` added after its last non-blank line, one blank line
    between, and no items (CP-1429). That line is closed first when it has no line ending, and
    the added lines take the ending of the last line that has one, else `\n`. Trailing blank
    lines stay after the addition, so every earlier byte is as it was."""
    lines = _lines_keeping_ends(text)
    last = next((index for index in range(len(lines) - 1, -1, -1) if lines[index].strip()), None)
    if last is None:
        return heading + "\n"
    ending = next(("\r\n" if line.endswith("\r\n") else "\n"
                  for line in reversed(lines[:last + 1]) if line.endswith("\n")), "\n")
    closed_last = lines[last] if lines[last].endswith("\n") else lines[last] + ending
    return "".join(lines[:last] + [closed_last, ending, heading + ending] + lines[last + 1:])


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
    if step.evidence is Evidence.COMMITTED_CHANGE_FILE:
        return f"{step.artifact} committed on {change.key}"
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


def _real_qa_places(change: "ChangeLayout") -> dict:
    return development_path.target(_real_contract(change), "qa")


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

    def __init__(self, *, files, gate_files, contract, tracked_files, record_reader, guest_job):
        self.files = files
        # The host's guest, from its login job (`gate_suite.GuestJob`), never from the plan.
        self.guest_job = guest_job
        self.gate_files = gate_files
        self.contract = contract
        self.tracked_files = tracked_files
        self.record_reader = record_reader

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
                out=io.StringIO(), guest_job=self.guest_job)
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


def _task_numbers(lines: list[str], prefix: str) -> list[int]:
    matches = (_TASK_TOKEN.search(line[len(prefix):]) for line in lines)
    return [int(match.group(1)) for match in matches if match]


def commit_shape_verdict(reader: DiskReader, change: ChangeLayout,
                         product_path: str) -> str | None:
    """`missing-red-commit — task <N>[, task <M>…]` for each judged TDD-lane task that landed
    with no red commit older than its first landing (CP-191, CP-193) — a `— red` subject, or a
    commit of the task a saved-red note names — or `None`. A plan that
    cannot be read is `unreadable-plan` rather than a pass: a check that passes when it cannot
    read its input passes everything (CP-195)."""
    lane = reader.tdd_lane_tasks(change)
    if lane is None:
        return "unreadable-plan"
    # A deferred task is declared unlanded, and its `— red` and `— deferred` commits are the
    # shape the skill prescribes for it (CP-189).
    deferred = set(_task_numbers(reader.deferrals(change), _DEFERRED_PREFIX))
    # A task the developer re-laned to already-green or to red-at-baseline, with its reason
    # recorded (CP-190).
    exempt = deferred | reader.relaned_tasks(change)
    judged = [number for number in lane if number not in exempt]
    repo = reader.code_repo(change, product_path)
    failing = reader.landed_without_red(
        repo, change.key, judged, reader.saved_red_commits(change),
        lambda older, newer: reader.paused_between(change, repo, older, newer))
    if not failing:
        return None
    return "missing-red-commit — " + ", ".join(f"task {number}" for number in failing)


# QA's record and the commits it judges. A QA commit is one whose body carries the QA seat's own
# `Role:` line, and the red is whichever of them changes the scenario folder.
_QA_ROLE_LINE = "Role: QA"
_DEVELOPER_ROLE_LINE = "Role: Developer"
_SCENARIO_FIELD_SEPARATOR = " — "
_SCENARIO_OUTCOMES = frozenset({"failed", "passed"})
_RED_COMMIT_VALUE = re.compile(r"^[0-9a-fA-F]{7,40}$")


class QaKind(str, Enum):
    """What a record says about a scenario: written or changed for this change, or already on
    `main` and kept."""

    NEW_OR_CHANGED = "new or changed"
    KEPT = "kept"


@dataclass(frozen=True)
class QaScenario:
    """One `Scenario:` line of QA's record: `<location> — <kind> — <rule> — <outcome>`."""

    location: str
    kind: QaKind
    rule: str
    outcome: str


def _qa_scenario(value: str) -> QaScenario | None:
    """The scenario a `Scenario:` line's value says, or `None` when it does not read as
    location — kind — rule — outcome with a kind and an outcome from the two closed sets."""
    parts = [part.strip() for part in value.split(_SCENARIO_FIELD_SEPARATOR)]
    if len(parts) < 4 or not parts[0]:
        return None
    rule = _SCENARIO_FIELD_SEPARATOR.join(parts[2:-1])
    kinds = {kind.value: kind for kind in QaKind}
    if parts[1] not in kinds or parts[-1] not in _SCENARIO_OUTCOMES or not rule:
        return None
    return QaScenario(parts[0], kinds[parts[1]], rule, parts[-1])


@dataclass(frozen=True)
class QaRedVerdict:
    """What judging QA's red answered. `refusal` is `None` when the red is accepted; `base` is the
    commit it was judged against and `outcomes` are the red run's `(location, status)`, for the
    record. `no_reach` is the record's undressed `No reach:` line, `No reach:` included, on a
    no-reach pass — `refusal` is `None` and no red was judged — and `None` on every other
    answer."""

    refusal: str | None
    base: str
    outcomes: tuple[tuple[str, str], ...]
    no_reach: str | None = None


def _not_passed(outcomes: tuple[tuple[str, str], ...]) -> str:
    return ", ".join(f"{location}: {status}" for location, status in outcomes
                     if status != "passed")


def _commits_with_role(git: Git, repo: str, key: str, role_line: str) -> list[tuple[str, str]]:
    """Each commit of `main..<key>` in `repo` whose body carries `role_line`, newest first."""
    found = []
    for sha, subject in git.commits_ahead(repo, _MAIN, key):
        lines = record_declarations.parse(git.commit_body(repo, sha)).lines
        if any(line.text == role_line for line in lines):
            found.append((sha, subject))
    return found


def _qa_commits(git: Git, repo: str, key: str) -> list[tuple[str, str]]:
    """Each commit of `main..<key>` in `repo` whose body carries the QA seat's `Role:` line,
    newest first."""
    return _commits_with_role(git, repo, key, _QA_ROLE_LINE)


def _resolved_red(git, repo: str, key: str, value: str) -> str | None:
    """The commit of `main..<key>` in `repo` whose sha opens with the record's `Red commit:`
    value, or `None` when the value is not a sha prefix or names no such commit."""
    if not _RED_COMMIT_VALUE.match(value):
        return None
    for sha, _subject in git.commits_ahead(repo, _MAIN, key):
        if sha.startswith(value.lower()):
            return sha
    return None


def qa_red_verdict(reader: DiskReader, behave: behave_run.ThrowawayBehave, change: ChangeLayout,
                   places: dict, *, environ: dict, draft: bool) -> QaRedVerdict:
    """Whether QA's red is accepted, by running it: `QaRedVerdict.refusal` is `None` or the first
    check that holds, in a fixed order that is the contract — Behave unavailable, `main` red,
    a no-reach record (below), no QA commit of the scenario folder, the red run unavailable, a
    kept scenario failing, the record's own defects, a library outside the red commit, then what
    the new scenarios did (CP-1313 to CP-1319). A commit's subject, the record's outcome column
    and a plan's lane are read for nothing: only Behave's own report is.

    A record that declares a `No reach:` line is judged in its own form, at the place the verdict
    would answer `missing-qa-red`: `_no_reach_refusal`'s refusal as `qa-record-refused — …`, or,
    when it holds none, a pass with `QaRedVerdict.no_reach` set and no red judged. The record
    decides the form, not the commits (CP-1406, CP-1407); a record with no such line is judged
    exactly as before.

    `draft` judges the scenario folder and record as the change's working tree holds them, before
    anything is committed, and skips the checks that need a commit."""
    git, repo, key = reader.git, places["repo"], places["branch"]
    folder = os.path.relpath(places["scenario_folder"], places["worktree"])
    base = git.merge_base(repo, _MAIN, key)
    if base is None:
        return QaRedVerdict(
            f"behave-unavailable — no merge base of main and {key} in {repo}", "", ())
    record_text = _qa_record_text(reader, change, places, draft=draft)
    record = record_declarations.parse(record_text or "")
    scenarios = [scenario for scenario in (
        _qa_scenario(line.text[len(record_declarations.QA_SCENARIO.prefix):].strip())
        for line in record.read(record_declarations.QA_SCENARIO)) if scenario]
    red_line = record.one(record_declarations.QA_RED)
    red_sha = None if draft or red_line is None else _resolved_red(
        git, repo, key, red_line.text[len(record_declarations.QA_RED.prefix):].strip())
    overlay = (behave_run.Overlay.tree(places["worktree"]) if draft
               else red_sha and behave_run.Overlay.commit(red_sha))
    base_report, red_report = behave.base_and_red(
        repo=repo, base=base, folder=folder, red=overlay or None, environ=environ)
    outcomes = () if red_report is None or red_report.outcomes is None else red_report.outcomes

    def verdict(refusal: str | None) -> QaRedVerdict:
        return QaRedVerdict(refusal, base, outcomes)

    if base_report.unavailable is not None:
        return verdict(f"behave-unavailable — {base_report.unavailable}")
    if _not_passed(base_report.outcomes):
        return verdict(f"main is red — {_not_passed(base_report.outcomes)}")
    no_reach = record.one(record_declarations.QA_NO_REACH)
    if no_reach is not None:
        in_no_reach = _no_reach_refusal(record, change, draft=draft)
        if in_no_reach:
            return verdict(f"qa-record-refused — {in_no_reach}")
        return QaRedVerdict(None, base, outcomes, no_reach=no_reach.text)
    qa_commits = [] if draft else _qa_commits(git, repo, key)
    if not draft and not any(
            any(path.startswith(folder + "/") for path in git.changed_paths(repo, sha))
            for sha, _subject in qa_commits):
        return verdict(_MISSING_QA_RED)
    if red_report is not None and red_report.unavailable is not None:
        return verdict(f"behave-unavailable — {red_report.unavailable}")
    red_status = dict(outcomes)
    kept_failing = ", ".join(f"{scenario.location}: failed" for scenario in scenarios
                             if scenario.kind is QaKind.KEPT
                             and red_status.get(scenario.location) == "failed")
    if kept_failing:
        return verdict(f"main is red — {kept_failing}")
    in_record = _record_refusal(record, record_text, change, red_sha, red_status, draft=draft)
    if in_record:
        return verdict(f"qa-record-refused — {in_record}")
    if not draft:
        library = _library_refusal(git, qa_commits, places, folder, red_sha)
        if library:
            return verdict(f"qa-red-refused — a library outside the red commit: {library}")
    return verdict(_outcome_refusal(scenarios, red_status))


@dataclass(frozen=True)
class CloseVerdict:
    """What the close answered. `refusal` is `None` on a pass; `commit` is the branch tip the
    scenarios ran at (`""` when none was resolved) and `scenarios` the count Behave reported."""

    refusal: str | None
    commit: str
    scenarios: int


def _touches(folder: str, path: str) -> bool:
    return path == folder or path.startswith(folder + "/")


def close_verdict(*, git: Git, behave: behave_run.ThrowawayBehave, places: dict,
                  environ: dict) -> CloseVerdict:
    """Whether every scenario the product holds passes on the change's final code. The order of
    the checks is the contract (CP-1381 to CP-1386): a developer commit that touched the scenario
    folder, no branch tip, Behave unavailable, no scenario, a scenario not passed, then the pass.
    Behave's own report is read for nothing but pass or fail, by the reading QA's base run uses
    (`_not_passed`); a commit's subject, a note, a plan's lane and QA's own commit and record are
    read for nothing, and the only commit data read is the paths and `Role:` lines of
    `main..<key>`."""
    repo, key = places["repo"], places["branch"]
    folder = os.path.relpath(places["scenario_folder"], places["worktree"])
    short = behave_run.SHORT_HASH_LENGTH
    refused, unreadable = [], []
    for sha, _subject in _commits_with_role(git, repo, key, _DEVELOPER_ROLE_LINE):
        paths = git.touched_paths(repo, sha)
        if paths is None:
            unreadable.append(sha)
        elif any(_touches(folder, path) for path in paths):
            refused.append(f"{sha[:short]} ({', '.join(paths)})")
    if refused:
        return CloseVerdict(
            f"close-refused — the scenario folder is QA's to change, and the developer changed it "
            f"in {'; '.join(refused)}", "", 0)
    if unreadable:
        return CloseVerdict(
            f"behave-unavailable — git could not list the paths commit {unreadable[0][:short]} "
            f"changed in {repo}", "", 0)
    tip = git.branch_tip(repo, key)
    if tip is None:
        return CloseVerdict(f"behave-unavailable — no branch {key} in {repo}", "", 0)
    report, _unused = behave.base_and_red(repo=repo, base=tip, folder=folder, red=None,
                                          environ=environ)
    if report.unavailable is not None:
        return CloseVerdict(f"behave-unavailable — {report.unavailable}", tip, 0)
    if not report.outcomes:
        return CloseVerdict(
            f"close-red — Behave reported no scenario in the scenario folder at {tip[:short]}",
            tip, 0)
    failing = _not_passed(report.outcomes)
    if failing:
        return CloseVerdict(f"close-red — {failing}", tip, len(report.outcomes))
    return CloseVerdict(None, tip, len(report.outcomes))


def _qa_record_text(reader: DiskReader, change: ChangeLayout, places: dict, *,
                    draft: bool) -> str | None:
    """QA's record as the change holds it: the working-tree file for a draft, else the file
    committed on the instance's change branch — never anything else on disk."""
    if draft:
        return reader.files.read_text(places["record"])
    return reader.git.show(change.instance_root, places["branch"],
                           f"{change.change_rel}/{development_path.QA_RECORD}")


# The slots a draft is exempt from: the commits they name do not exist until the red is committed.
_QA_SLOTS_OF_A_COMMIT = (record_declarations.QA_BASE, record_declarations.QA_RED)
_QA_LIBRARY_FILES = ("pyproject.toml", "uv.lock")


def _slot_value(line: record_declarations.Line, field: record_declarations.Field) -> str:
    return line.text[len(field.prefix):].strip()


def _slot_refusal(record: record_declarations.ParsedRecord,
                  slots: tuple[record_declarations.Field, ...], change: ChangeLayout, *,
                  draft: bool) -> str | None:
    """The first of `slots` that is missing or empty (the two commit slots exempt in a draft), in
    the table's order, else the `Change:` line when it holds another change's key; `None` when the
    record's slots read clean."""
    for field in slots:
        if draft and field in _QA_SLOTS_OF_A_COMMIT:
            continue
        lines = record.read(field)
        if not lines:
            return f"the record has no {field.prefix} line"
        if not all(_slot_value(line, field) for line in lines):
            return f"the record's {field.prefix} line is empty"
    held = _slot_value(record.one(record_declarations.QA_CHANGE), record_declarations.QA_CHANGE)
    if held != change.key:
        return f"the record's Change: line reads {held}, not {change.key}"
    return None


def _no_reach_refusal(record: record_declarations.ParsedRecord, change: ChangeLayout, *,
                      draft: bool) -> str | None:
    """CP-1403: why a record that declares a `No reach:` line is not an accepted no-reach record,
    or `None` when it is. The first defect in this order is the answer, so a record with two
    always gives one: the `No reach:` value empty, a `Red commit:` or `Scenario:` line beside it,
    then the form's other slots in the table's order (`Base commit:` exempt in a draft) and last
    the `Change:` key, the last two in the red record's own words."""
    no_reach = record.one(record_declarations.QA_NO_REACH)
    if not _slot_value(no_reach, record_declarations.QA_NO_REACH):
        return "the record's No reach: line is empty"
    if record.read(record_declarations.QA_RED) or record.read(record_declarations.QA_SCENARIO):
        return "the record carries a No reach: line beside a red"
    others = tuple(field for field in record_declarations.QA_NO_REACH_RECORD
                   if field is not record_declarations.QA_NO_REACH)
    return _slot_refusal(record, others, change, draft=draft)


def _record_refusal(record: record_declarations.ParsedRecord, text: str | None,
                    change: ChangeLayout, red_sha: str | None, red_status: dict[str, str], *,
                    draft: bool) -> str | None:
    """CP-1316: why QA's record cannot be checked against the branch, or `None` when it can —
    absent, empty, a slot missing or empty (the two commit slots exempt in a draft), another
    change's key, a red commit that is not the branch's, a `Scenario:` line that does not parse,
    or a location the red run did not report. The slots checked are the red record's
    (`QA_RED_RECORD`); a record with no `No reach:` line is checked exactly so."""
    path = f"{change.change_rel}/{development_path.QA_RECORD}"
    if text is None:
        return f"no record at {path}"
    if text == "":
        return f"the record at {path} is empty"
    in_slots = _slot_refusal(record, record_declarations.QA_RED_RECORD, change, draft=draft)
    if in_slots:
        return in_slots
    if not draft and red_sha is None:
        red_value = _slot_value(record.one(record_declarations.QA_RED), record_declarations.QA_RED)
        return (f"the record's Red commit: {red_value} is not a commit of the branch "
                f"{change.key} in the product's repository")
    for line in record.read(record_declarations.QA_SCENARIO):
        value = _slot_value(line, record_declarations.QA_SCENARIO)
        scenario = _qa_scenario(value)
        if scenario is None:
            return ("the record's Scenario: line does not read as "
                    f"location — kind — rule — outcome: {value}")
        if scenario.location not in red_status:
            return (f"the record names {scenario.location}, which Behave did not report for "
                    "the red commit's scenarios")
    return None


def _library_refusal(git, qa_commits: list[tuple[str, str]], places: dict, folder: str,
                     red_sha: str) -> str | None:
    """CP-1315, as the design reads it: the first of the scenario folder's library files that a
    QA commit newer than the red commit changed, or that the worktree holds uncommitted. A QA
    commit that is the red commit or one of its ancestors is not refused: the red run uses the
    red commit's tree, which already holds what such a commit changed."""
    files = [f"{folder}/{name}" for name in _QA_LIBRARY_FILES]
    repo = places["repo"]
    for sha, _subject in qa_commits:
        if sha == red_sha or git.is_ancestor(repo, sha, red_sha):
            continue
        changed = git.changed_paths(repo, sha)
        for file in files:
            if file in changed:
                return file
    for file in files:
        if git.path_status(places["worktree"], file):
            return file
    return None


def _outcome_refusal(scenarios: list[QaScenario], red_status: dict[str, str]) -> str | None:
    """CP-1314: `qa-red-refused — <reason>` when the red run does not show a red that belongs to
    this change, else `None`. A new or changed scenario must fail, and a kept one must pass or
    fail; Behave's own word for any other outcome is named as it was reported."""
    if not any(scenario.kind is QaKind.NEW_OR_CHANGED for scenario in scenarios):
        return "qa-red-refused — the record names no new or changed scenario"
    for scenario in scenarios:
        status = red_status[scenario.location]
        if scenario.kind is QaKind.NEW_OR_CHANGED:
            if status == "passed":
                return f"qa-red-refused — {scenario.location} passes before the change"
            if status != "failed":
                return f"qa-red-refused — {scenario.location}: {status}"
        elif status not in _SCENARIO_OUTCOMES:
            return f"qa-red-refused — {scenario.location}: {status}"
    return None


class DevelopmentChain:
    """The walk. Everything it uses is handed to it; it constructs nothing."""

    def __init__(self, *, store: StateStore, reader: DiskReader, files, exact_files, processes,
                 notifier, lock, log, id_source, environ: dict, engine_path: str,
                 steps: tuple[Step, ...],
                 providers: ProviderFiles, process_table: walk_stop.ProcessTable,
                 checkout: product_checkout.Checkout, environment_check,
                 behave: behave_run.ThrowawayBehave, qa_places, qa_asks: QaAskStore,
                 chain_name: str = ""):
        self.store = store
        # The per-change record of QA's runs and the asks answered, shared by every walk.
        self.qa_asks = qa_asks
        self.behave = behave
        # `qa_places(change)` is where QA's run writes and commits: the path tool's `qa` target.
        self.qa_places = qa_places
        self.environment_check = environment_check
        self.checkout = checkout
        self.process_table = process_table
        self.providers = providers
        self._due_end_hook: tuple[str, str, str, str, str] | None = None
        # The sweep's launch, decided under the state lock and run once it is released:
        # `(argv, env, cwd)`.
        self._due_sweep_launch: tuple[list[str], dict, str] | None = None
        self.reader = reader
        self.files = files
        self.exact_files = exact_files
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
        self.chain_name = chain_name or CHAIN_NAMES.get(id(steps), "change")

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
        entry = self._earlier_when_an_ask_is_open(project, key, entry)
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
                if candidate == _QA_STEP and not reason.startswith("behave-unavailable"):
                    # A refused red is QA's to run again, and nothing is wrong with the walk.
                    return key, candidate.id
                raise ChainRefused(f"stopped at {candidate.id}: {reason}")
        return key, entry.id

    def _earlier_when_an_ask_is_open(self, project: str, key: str, entry: Step) -> Step:
        """The step an open ask owes the walk (CP-1343, CP-1344), when it comes earlier in the table
        than the disk's entry. The ask is the engine's own record, so only this choice reads it:
        `DiskReader.entry_step`, which the recoveries also call, is left as the disk says."""
        owed = self.qa_asks.load(project, key).step_owed() if key else None
        steps = [candidate.id for candidate in self.steps]
        if owed is None or owed not in steps or steps.index(owed) >= steps.index(entry.id):
            return entry
        return self.steps[steps.index(owed)]

    def _resolve_key(self, instance_root: str, project: str) -> str:
        """The active change's key, or `""` for a walk that has not opened one yet.

        Which of the two is right is the TABLE's to say, never the disk's. A table carrying a
        `CHANGE_OPEN` step opens the change itself, so an empty `journey/tobiishi/` is the state
        it starts in. A table without one presumes the change is already there, and
        `discover_key`'s refusal — *"Open one with tobiishi-open first"* — is exactly the answer
        `change` owes a caller who has not. Deciding this off the disk would swallow
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
        previous = self.store.raw()
        if (isinstance(previous, dict) and previous.get("ended") == Ended.STOPPED.value
                and previous.get("key") == key):
            state.qa_retries = previous.get("qa_retries", 0)
            state.qa_rerun_retries = previous.get("qa_rerun_retries", 0)
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
                                         self.chain_name, existing.get("project", ""))
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
        self._run_due_sweep_launch()
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

        change = ChangeLayout(state.instance_root, state.project, state.key)
        if run == _SWEEP_RUN:
            self._settle_sweep(state, change, outcome)
            self.store.save(state)
            return AdvanceResult(acted=True, ended=state.ended)
        step = next(candidate for candidate in (*self.steps, _REPAIR_STEP)
                    if candidate.id == entry["step"])
        if step == _QA_STEP:
            self._count_a_qa_run(state)
        if self._left_the_checkout_dirty(state, step, entry):
            self.store.save(state)
            return AdvanceResult(acted=True, ended=state.ended)
        if state.key and self._answer_an_ask(state, change, step):
            self.store.save(state)
            return AdvanceResult(acted=True, ended=state.ended)
        if step is _REPAIR_STEP:
            self._settle_repair(state, change, outcome)
        elif step.gates:
            self._settle(state, change, step, outcome)
        else:
            self._settle_audit(state, change, step, entry["audited"], outcome)
        self.store.save(state)
        return AdvanceResult(acted=True, ended=state.ended)

    def _answer_an_ask(self, state: WalkState, change: ChangeLayout, step: Step) -> bool:
        """Read the ask the ended run left at `ChangeLayout.qa_ask`, if any, and answer it once
        (CP-1329 to CP-1335): the answer is saved before the ask is moved out of the change folder,
        so a crash between the two leaves an answered ask in place rather than an ask lost
        unanswered. `True` when the ask was accepted and QA's step launched, so the ended run's own
        end is not settled; a turned-down ask returns `False`, and the end settles as with no
        ask."""
        text = self.files.read_text(change.qa_ask)
        if text is None:
            return False
        asks = self.qa_asks.load(state.project, state.key)
        reason = ask_reason(text)
        why = self._reason_to_turn_down(change, step, reason, asks)
        asks.answered.append({"step": step.id, "reason": reason,
                              "answer": QA_ASK_ACCEPTED if why is None else f"turned down: {why}"})
        places = self.qa_places(change) if why is None else None
        if why is None:
            asks.open = {"asker": step.id,
                         "since": self.reader.branch_tip(places["repo"], places["branch"]) or "",
                         "phase": QaAskPhase.RE_RUN.value}
            record_since = self.reader.branch_tip(change.instance_root, places["branch"])
            if record_since:
                asks.open["record_since"] = record_since
        self.qa_asks.save(state.project, state.key, asks)
        self.qa_asks.keep(state.project, state.key, len(asks.answered), change.qa_ask)
        if why is not None:
            state.history.append(f"{step.id} asked QA — turned down: {why}")
            return False
        state.qa_rerun_retries = 0
        state.history.append(f"{step.id} asked QA — {reason} — running {_QA_STEP.id} again")
        self._launch_step(state, change, _QA_STEP)
        return True

    def _reason_to_turn_down(self, change: ChangeLayout, step: Step, reason: str,
                             asks: QaAsks) -> str | None:
        """The first of CP-1332's four reasons that holds, in its order, or `None` for an ask that
        is accepted."""
        if step.id not in _ASKERS:
            return "only implementation and design may ask"
        decision = self.reader.qa_decision(change)
        if not decision.applies:
            return f"QA's step passed this change — {decision.read}"
        if not reason:
            return "no reason given"
        if asks.accepted(step.id):
            return f"{step.id} has spent its one ask"
        return None

    def _count_a_qa_run(self, state: WalkState) -> None:
        """A run of QA's step that ended is counted on the change. Counted here, at its end, so a
        launch the stop command ended, which never reaches this, and a launcher that refused,
        which left no pending run, are not runs."""
        asks = self.qa_asks.load(state.project, state.key)
        asks.runs += 1
        self.qa_asks.save(state.project, state.key, asks)

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
        if step == _QA_STEP:
            self._settle_qa(state, change, step)
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
            if report and self._answer_records_owed(state, change, step, report):
                return
            self._halt(state, step, f"halt_report.md at {report}" if report
                       else f"no {_missing(change, step)} after the run ended")
            return
        reason = self._bad_verdict(change, step, state.product_path)
        if reason is not None:
            if self._launch_repair(state, change, step, reason):
                return
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
        self._close_the_return(state, step)
        self._after(state, change, step)

    def _close_the_return(self, state: WalkState, step: Step) -> None:
        """The asker has landed after QA's re-run returned the walk to it: the ask is closed, so a
        later start enters where the disk says (CP-1340). Any other landing, and an ask whose
        re-run is still owed, leaves the record as it is."""
        if not state.key:
            return
        asks = self.qa_asks.load(state.project, state.key)
        if (asks.open is not None and asks.open["phase"] == QaAskPhase.RETURN.value
                and asks.open["asker"] == step.id):
            asks.open = None
            self.qa_asks.save(state.project, state.key, asks)

    def _settle_qa(self, state: WalkState, change: ChangeLayout, step: Step) -> None:
        """QA's run has finished: ask the red verdict and act on it (CP-1313 to CP-1319). An
        accepted red lands the step, and an accepted no-reach record passes it with no retry and
        the line `red-behaviour passed — "<the No reach: line>"` (CP-1408, CP-1409); every other
        refusal halts with the verdict's own words, and QA is not run again. While an ask is open
        the run is its re-run, which two checks of the chain's own precede, and an accepted red
        returns the walk to the asker (CP-1336 to CP-1340)."""
        asks = self.qa_asks.load(state.project, state.key)
        places = self.qa_places(change)
        if asks.open is not None and self._rerun_stalled(state, change, step, asks, places):
            return
        verdict = qa_red_verdict(self.reader, self.behave, change, places,
                                 environ=self.environ, draft=False)
        if verdict.refusal == _MISSING_QA_RED and state.qa_retries == 0:
            state.qa_retries += 1
            state.history.append(f"{step.id} ended with no red commit — running it once more")
            self._launch_step(state, change, step)
            return
        if verdict.refusal is not None and verdict.refusal.startswith(_MAIN_IS_RED):
            scenarios = verdict.refusal[len(_MAIN_IS_RED):]
            if self._launch_repair(state, change, step, scenarios):
                return
            self._halt(state, step, f"{_QA_MAIN_RED} — {scenarios}")
            return
        if verdict.refusal is not None:
            self._halt(state, step, verdict.refusal)
            return
        passed = (f"{step.id} landed" if verdict.no_reach is None
                  else f'{step.id} passed — "{verdict.no_reach}"')
        if asks.open is not None:
            self._return_to_the_asker(state, change, step, asks, passed)
            return
        state.history.append(passed)
        self._after(state, change, step)

    def _rerun_stalled(self, state: WalkState, change: ChangeLayout, step: Step, asks: QaAsks,
                       places: dict) -> bool:
        """The two checks a re-run gets before the verdict, each reading only the commits made
        since the ask (CP-1337, CP-1338). Counted by membership in `since..<key>`, so
        `_qa_commits` and every check the verdict calls stay as they are (CP-1347). A no-reach
        record counts as the re-run's only when a commit since the ask changed it (CP-1411,
        CP-1412): one that did reaches the verdict with no red, and one that did not, beside a red,
        is refused (`_stale_claim_refusal`). `True` once one has launched QA's retry or halted the
        walk."""
        git, repo, key = self.reader.git, places["repo"], places["branch"]
        since = asks.open["since"] or _MAIN
        after_the_ask = {sha for sha, _subject in git.commits_ahead(repo, since, key)}
        folder = os.path.relpath(places["scenario_folder"], places["worktree"])
        red_made = any(sha in after_the_ask and any(path.startswith(folder + "/")
                                                    for path in git.changed_paths(repo, sha))
                       for sha, _subject in _qa_commits(git, repo, key))
        if not red_made:
            if self._claim_made_since_the_ask(change, places, asks):
                return False
            if state.qa_rerun_retries != 0:
                self._halt(state, step, _MISSING_QA_RED)
                return True
            state.qa_rerun_retries += 1
            state.history.append(f"{step.id} ended with no red commit — running it once more")
            self._launch_step(state, change, step)
            return True
        named = self._red_commit_named_in_the_record(change, places)
        resolved = None if named is None else _resolved_red(git, repo, key, named)
        if resolved is not None and resolved not in after_the_ask:
            self._halt(state, step, f"qa-record-refused — the record's Red commit: {named} "
                                    "was made before the ask")
            return True
        stale = self._stale_claim_refusal(change, places, asks)
        if stale:
            self._halt(state, step, f"qa-record-refused — {stale}")
            return True
        return False

    def _stale_claim_refusal(self, change: ChangeLayout, places: dict,
                             asks: QaAsks) -> str | None:
        """A re-run that made a red since the ask, over a committed no-reach record no commit since
        the ask changed: that record makes no claim (CP-1412), so the re-run is not passed on it
        and its record is held to the red record's slots. The first of them it lacks, or `None`
        when the record declares no `No reach:` line, the claim was made since the ask, or the
        record holds every red slot, which leaves the verdict to refuse it as a claim beside a
        red."""
        record = record_declarations.parse(
            _qa_record_text(self.reader, change, places, draft=False) or "")
        if record.one(record_declarations.QA_NO_REACH) is None:
            return None
        if self._claim_made_since_the_ask(change, places, asks):
            return None
        return _slot_refusal(record, record_declarations.QA_RED_RECORD, change, draft=False)

    def _claim_made_since_the_ask(self, change: ChangeLayout, places: dict, asks: QaAsks) -> bool:
        """A commit the instance change branch gained since the ask changed QA's record, and the
        committed record declares a `No reach:` line (CP-1411, CP-1412). Read against
        `record_since`, the instance branch's tip when the ask was accepted: `since` ranges the
        product repository, which holds QA's record only when the product is in the instance. An
        entry with no `record_since` reads as no claim."""
        record_since = asks.open.get("record_since")
        if not record_since:
            return False
        git = self.reader.git
        record_path = f"{change.change_rel}/{development_path.QA_RECORD}"
        changed = any(record_path in git.changed_paths(change.instance_root, sha)
                      for sha, _subject in git.commits_ahead(
                          change.instance_root, record_since, places["branch"]))
        if not changed:
            return False
        record = record_declarations.parse(
            _qa_record_text(self.reader, change, places, draft=False) or "")
        return record.one(record_declarations.QA_NO_REACH) is not None

    def _red_commit_named_in_the_record(self, change: ChangeLayout, places: dict) -> str | None:
        """The committed record's `Red commit:` value as the record writes it, or `None` when it
        names none."""
        record = record_declarations.parse(
            _qa_record_text(self.reader, change, places, draft=False) or "")
        line = record.one(record_declarations.QA_RED)
        return None if line is None else _slot_value(line, record_declarations.QA_RED)

    def _return_to_the_asker(self, state: WalkState, change: ChangeLayout, step: Step,
                             asks: QaAsks, passed: str) -> None:
        """The re-run's red, or its no-reach record, is accepted: the asker's step is launched
        next and nothing between (CP-1340). `passed` is the history line the pass earns, which
        the way back is appended to. The developer's step is entered as a start enters it, at the
        first unfinished task, and the plan is not read or written."""
        asks.open["phase"] = QaAskPhase.RETURN.value
        self.qa_asks.save(state.project, state.key, asks)
        asker = next(candidate for candidate in self.steps if candidate.id == asks.open["asker"])
        state.history.append(f"{passed} — back to {asker.id}")
        after = (self.reader.resume_after(change, state.product_path)
                 if asker.evidence is Evidence.MARKER_COMMIT else None)
        self._launch_step(state, change, asker, after=after)

    def _answer_records_owed(self, state: WalkState, change: ChangeLayout, step: Step,
                             report: str) -> bool:
        """Answer a `records-owed` halt by launching the document sweep, and say whether it did
        (CP-1101, CP-1103). A report that is not one — another step, another reason, a card whose
        `**Definition:**` on `main` is not `full` — is declined, and the caller halts on it as it
        always has (CP-1113)."""
        if (step.id not in _RECORDS_OWED_STEPS
                or self.reader.halt_reason(report) != _RECORDS_OWED
                or self.reader.definition(change) != _FULL_DEFINITION):
            return False
        named = [(value, self.reader.split_raised_item(value))
                 for value in self.reader.raised_items(report)]
        if not named:
            self._halt(state, step, f"{_RECORDS_OWED} — the halt report names no raised item: "
                                    f"halt_report.md at {report}")
            return True
        unreadable = next((value for value, parts in named if parts is None), None)
        if unreadable is not None:
            self._halt(state, step, f"{_RECORDS_OWED} — unreadable raised item: {unreadable}")
            return True
        if state.sweeps != 0:
            self._halt(state, step, f"{_RECORDS_OWED} — {_SWEEP_SKILL} already ran in this walk: "
                                    f"halt_report.md at {report}")
            return True
        if not self._carry(state, change, step, named):
            return True
        self._launch_sweep(state, change, step, named)
        return True

    def _carry(self, state: WalkState, change: ChangeLayout, step: Step,
               named: list[tuple[str, tuple[str, str] | None]]) -> bool:
        """Carry each named item the main checkout does not hold onto it, in one commit, before the
        sweep records what is held open (CP-1123–CP-1126). Whether the walk goes on to the launch:
        `False` once it has halted. Nothing carried means nothing is asked of the provider and
        nothing is written."""
        repository = self.reader.carry_repository(change)
        files = ([] if repository is None
                 else self._files_to_carry(state, change, repository, named))
        if not files:
            return True
        provider = self._provider_or_halt(state, step)
        if provider is None:
            return False
        surface = _SURFACES.get(provider)
        if surface is None:
            self._halt(state, step, _CARRY_REFUSED.format(
                owed=_RECORDS_OWED, why=_CARRY_NO_SURFACE.format(provider=provider)))
            return False
        why = self._refusal_before_writing(repository, files)
        if why is not None:
            self._halt(state, step, _CARRY_REFUSED.format(owed=_RECORDS_OWED, why=why))
            return False
        for carried in files:
            if carried.before is None:
                self.files.make_dirs(os.path.dirname(carried.path))
            self.exact_files.write_text(carried.path, carried.after)
        exit_code = self.processes.run(
            self._carry_command(state, change, step, repository, surface, files),
            cwd=repository, env=with_provider(self.environ, provider))
        if exit_code != 0:
            reason = _CARRY_FAILED.format(owed=_RECORDS_OWED, code=exit_code)
            failed = self._restore(repository, files, provider)
            if failed:
                reason += f" ({'; '.join(failed)})"
            self._halt(state, step, reason)
            return False
        return True

    def _refusal_before_writing(self, repository: str,
                                files: list[_CarriedFile]) -> str | None:
        """Why the carry may not write (CP-1127): the checkout does not have `main` out, or a
        companion it would write holds an uncommitted change, staged or not, or git cannot say.
        Committing there would put the item on another branch, or sweep someone's edit into the
        carry's commit. `None` when it may. Every check comes before the first write."""
        branch = self.reader.checkout_branch(repository)
        if branch != _MAIN:
            return _CARRY_BRANCH.format(repository=repository, branch=branch or _NO_BRANCH)
        for carried in files:
            status = self.reader.path_status(repository, carried.relative)
            if status is None:
                return _CARRY_UNREADABLE.format(companion=carried.companion)
            if status:
                return _CARRY_DIRTY.format(companion=carried.companion)
        return None

    def _restore(self, repository: str, files: list[_CarriedFile], provider: str) -> list[str]:
        """Put every file the carry wrote back as it found it, and unstage it, because the builder
        may have staged it before it refused (CP-1127, CP-1434): a file that existed is written
        back as it read, and a file the carry created is removed, not written back. Safe, since
        the checks ahead of the write showed none of them held an uncommitted change. Every file
        is restored, one failing included; what names each unstaging that exited non-zero, in
        the order written."""
        failed = []
        for carried in files:
            if carried.before is None:
                self.files.remove(carried.path)
                unstage = ["rm", "--cached", "--ignore-unmatch", "--quiet"]
            else:
                self.exact_files.write_text(carried.path, carried.before)
                unstage = ["restore", "--staged"]
            exit_code = self.processes.run(
                ["git", "-C", repository, *unstage, "--", carried.relative],
                cwd=repository, env=with_provider(self.environ, provider))
            if exit_code != 0:
                failed.append(_CARRY_RESTORE_FAILED.format(companion=carried.companion,
                                                           code=exit_code))
        return failed

    def _files_to_carry(self, state: WalkState, change: ChangeLayout, repository: str,
                        named: list[tuple[str, tuple[str, str] | None]]) -> list[_CarriedFile]:
        """The main-checkout companions the carry writes, in the order their first item was named,
        each with what it holds now (`None` where the carry creates it), what it will hold and the
        items going into it (CP-1124, CP-1426, CP-1429). An item is carried when the change
        worktree's companion holds it, the main checkout does not hold it open, and the main
        checkout's companion either has a *Raised from downstream* section, lacks the section
        (the template's heading is added), or does not exist (it is created from the template).
        A companion that exists but cannot be read, and one that needs a template that has none
        or has no such heading, carry nothing. Two items with one companion and one title are
        one."""
        blocks: dict[str, dict[str, tuple[str, str]]] = {}
        before: dict[str, str | None] = {}
        builders: dict[str, Callable[[list[str]], str]] = {}
        companions: dict[str, str] = {}
        for value, parts in named:
            companion, title = parts
            path = self.reader.main_companion_path(change, companion)
            if path is None or self.reader.item_held_open(change, companion, title):
                continue
            worktree_path = self.reader.worktree_companion_path(change, companion)
            worktree_text = (None if worktree_path is None
                             else self.exact_files.read_text(worktree_path))
            block = None if worktree_text is None else _extract_item(worktree_text, title)
            if block is None:
                continue
            main_text = self.exact_files.read_text(path)
            builder = self._companion_builder(state, companion, path, main_text)
            if builder is None:
                continue
            before[path] = main_text
            builders[path] = builder
            companions.setdefault(path, companion)
            blocks.setdefault(path, {}).setdefault(title, (value, block))
        root = os.path.realpath(repository)
        return [_CarriedFile(path, companions[path], os.path.relpath(os.path.realpath(path), root),
                             before[path], builders[path]([block for _, block in held.values()]),
                             tuple(value for value, _ in held.values()))
                for path, held in blocks.items()]

    def _companion_builder(self, state: WalkState, companion: str, path: str,
                           main_text: str | None) -> Callable[[list[str]], str] | None:
        """What the carry makes of main's companion at `path`, which reads `main_text` (`None`:
        it did not read): a function from the carried items to the text it will hold. Where it has
        the section, the items are appended; where it lacks the section, the template's heading
        is added first; where there is no file and no directory, it is created from the
        template. `None` when nothing may be written there: the path exists and does not read,
        or the template is missing or has no *Raised from downstream* heading."""
        if main_text is not None and _append_items(main_text, []) is not None:
            return lambda items: _append_items(main_text, items)
        if main_text is None and (self.files.is_file(path) or self.files.is_dir(path)):
            return None
        template = self.reader.companion_template(state.core_dir, companion)
        heading = None if template is None else _raised_heading(template)
        if heading is None:
            return None
        if main_text is not None:
            return lambda items: _append_items(_with_raised_section(main_text, heading), items)
        return lambda items: _companion_from_template(template, state.project, items)

    def _carry_command(self, state: WalkState, change: ChangeLayout, step: Step, repository: str,
                       surface: str, files: list[_CarriedFile]) -> list[str]:
        """The builder call that commits the carry in `repository`: the halting step's seat as the
        actor, the open station or else the finish line as the directional, and each companion as
        a repository-relative `--add`, which the builder's staged-set guard requires. No model wrote
        the commit, so it carries no skill, co-author or reasoning effort (CP-1126)."""
        values = [value for carried in files for value in carried.values]
        many = len(values) > 1
        things = "items" if many else "item"
        station = self.reader.open_station(state.instance_root, state.project)
        progress = _CARRY_PROGRESS.format(key=change.key, things=things)
        directional = (f"Shukuba: {station.removesuffix('.md')} — progress: {progress}"
                       if station else f"Finish-line: {state.project} — progress: {progress}")
        body = (_CARRY_BODY_MANY if many else _CARRY_BODY_ONE).format(step=step.id)
        listing = "\n".join(f"- {value}" for value in values)
        return [os.path.join(state.core_dir, "tools", "locked_python.sh"),
                os.path.join(state.core_dir, "tools", "commit_builder.py"),
                "--repo", repository, "commit",
                "--subject", _CARRY_SUBJECT.format(seat=step.role, key=change.key, things=things),
                "--body", f"{body}\n\n{listing}", "--actor", step.role,
                "--directional", directional, "--surface", surface,
                "--add", *[carried.relative for carried in files]]

    def _launch_sweep(self, state: WalkState, change: ChangeLayout, step: Step,
                      named: list[tuple[str, tuple[str, str] | None]]) -> None:
        """Record the items the main checkout holds open, mark `product-docs` due and wait for its
        end (CP-1107, CP-1108). The launch itself runs once the state lock is released
        (`_run_due_sweep_launch`): the document engine runs in the foreground, and holding this
        walk's lock for all of it would make a `--stop` of this walk wait."""
        state.sweeps += 1
        state.sweep_step = step.id
        state.sweep_items = [{"value": value, "held": self.reader.item_held_open(change, *parts)}
                             for value, parts in named]
        state.history.append(f"{step.id} {_RECORDS_OWED} — launching {_SWEEP_SKILL}")
        shim = self._shim_path(state, _SWEEP_RUN)
        self._write_shim(state, shim, _SWEEP_RUN)
        state.pending[_SWEEP_RUN] = {"step": _SWEEP_RUN, "audited": None, "identity": ""}
        self.store.save(state)
        self.notifier.send(f"{self._headline(state)} — {step.id} {_RECORDS_OWED} — launching "
                           f"{_SWEEP_SKILL}")
        argv = [os.path.join(state.core_dir, "launchers", _SWEEP_SKILL, "launcher.sh"),
                state.project, "--on-end", shlex.quote(shim)]
        if state.forced_provider:
            argv += ["--provider", state.forced_provider]
        if state.keep_awake:
            argv.append("--keep-awake")
        env = walk_stop.without_launch_identity(with_provider(self.environ, state.forced_provider))
        for name in _SWEEP_REMOVED_VARIABLES:
            env.pop(name, None)
        self._due_sweep_launch = (argv, env, state.instance_root)

    def _run_due_sweep_launch(self) -> None:
        """Run the sweep's launcher, with the state lock released, and settle a non-zero exit under
        the lock again (CP-1108): it halts at the step whose halt was answered, but only while the
        walk has not ended and the sweep is still pending. A sweep whose end arrived before the
        launcher returned has already consumed its entry, so the exit then changes nothing."""
        due, self._due_sweep_launch = self._due_sweep_launch, None
        if due is None:
            return
        argv, env, cwd = due
        exit_code = self.processes.run(argv, cwd=cwd, env=env)
        if exit_code == 0:
            return
        with self.lock.hold(self.store.path):
            state = self.store.load()
            if state.ended is not None or _SWEEP_RUN not in state.pending:
                return
            del state.pending[_SWEEP_RUN]
            halting = next(candidate for candidate in self.steps
                           if candidate.id == state.sweep_step)
            self._halt(state, halting,
                       f"{_RECORDS_OWED} — {_SWEEP_SKILL} launcher exited {exit_code}")

    def _settle_sweep(self, state: WalkState, change: ChangeLayout, end: str) -> None:
        """The sweep has ended (CP-1109–CP-1112). Every halt is named at the step whose halt it
        answered, and a halt deletes nothing and launches nothing."""
        halting = next(candidate for candidate in self.steps if candidate.id == state.sweep_step)
        unfolded = [item["value"] for item in state.sweep_items
                    if not self._folded(change, item)]
        if unfolded:
            self._halt(state, halting, f"{_RECORDS_OWED} — not folded: {'; '.join(unfolded)}")
            return
        if end != Ended.SEALED.value:
            self._halt(state, halting, f"{_RECORDS_OWED} — {_SWEEP_SKILL} ended {end}")
            return
        why = self._clear_old_change(state, change)
        if why is not None:
            self._halt(state, halting, f"{_RECORDS_OWED} — the old change branch could not be "
                                       f"deleted ({why})")
            return
        folded = f"{_SWEEP_SKILL} folded every raised item — re-entering at {_REENTRY_STEP}"
        state.history.append(folded)
        self.notifier.send(f"{self._headline(state)} — {folded}")
        self._launch_step(state, change, next(candidate for candidate in self.steps
                                              if candidate.id == _REENTRY_STEP))

    def _clear_old_change(self, state: WalkState, change: ChangeLayout) -> str | None:
        """Remove the old change's worktree and delete its branch in each repository that has
        them: the instance's, then an external product's, the order `_advance_onto_main` uses
        (CP-1111). Why it failed, or `None` when both repositories are clear. The first failure
        stops it."""
        repos = [change.instance_root]
        product = self.reader.code_repo(change, state.product_path)
        if product != change.instance_root:
            repos.append(product)
        for repo in repos:
            why = self._clear_in(repo, change.key)
            if why is not None:
                return why
        return None

    def _clear_in(self, repo: str, key: str) -> str | None:
        """Clear one repository, every command run from its root and never from inside the
        worktree being removed. The worktree is removed without `--force`: git refuses one that
        holds uncommitted work, and that refusal is the halt, since work never committed cannot be
        got back. The branch is deleted naming the tip read just before, the explicit-SHA form
        `commit_format.md` § *A destructive operation names an explicit SHA* asks for. Both are
        read again afterwards, so the folder and the branch are gone by construction."""
        worktree = os.path.join(repo, ".worktrees", key)
        label = f".worktrees/{key}"
        if self.files.is_dir(worktree):
            exit_code = self.processes.run(["git", "-C", repo, "worktree", "remove", worktree],
                                           cwd=repo, env=self.environ)
            if exit_code != 0:
                return f"{repo}: removing worktree {label} exited {exit_code}"
        tip = self.reader.branch_tip(repo, key)
        if tip is not None:
            exit_code = self.processes.run(
                ["git", "-C", repo, "update-ref", "-d", f"refs/heads/{key}", tip],
                cwd=repo, env=self.environ)
            if exit_code != 0:
                return f"{repo}: deleting branch {key} at {tip} exited {exit_code}"
        if self.files.is_dir(worktree):
            return f"{repo}: worktree {label} is still there"
        if self.reader.branch_tip(repo, key) is not None:
            return f"{repo}: branch {key} is still there"
        return None

    def _folded(self, change: ChangeLayout, item: dict) -> bool:
        """Whether the sweep folded `item` (CP-1109): the main checkout held it open at the launch
        and holds it open no longer. An item that was never there has not folded, because the sweep
        never had it to fold."""
        parts = self.reader.split_raised_item(item["value"])
        return (bool(item["held"]) and parts is not None
                and not self.reader.item_held_open(change, *parts))

    def _launch_repair(self, state: WalkState, change: ChangeLayout, step: Step,
                       reason: str) -> bool:
        """Launch `dependency-repair` in place of halting, and say whether it did (CP-860, CP-861,
        CP-1317). The engine runs no tests, so it cannot tell a red that is `main`'s from the
        change's own; the repair's audit on `main` is what does, and it writes no report when the
        red is not `main`'s (CP-865). Two reds are answered: a marker's `red-suite`, and QA's
        step finding scenarios failing on `main` (`reason` is then the scenarios). Only a product
        whose NFDR is on `main`, and only the walk's first."""
        for_qa = step == _QA_STEP
        if (not for_qa and (reason != _RED_SUITE or step.evidence is not Evidence.MARKER_COMMIT)
                or state.repairs != 0 or not self.reader.has_nfdr(change)):
            return False
        provider = self._repair_provider_or_halt(state)
        if provider is None:
            return True
        state.repair_reports_before = self.reader.repair_reports(change)
        state.repairs += 1
        if for_qa:
            state.repair_step, state.qa_main_red = step.id, reason
            said = f"{step.id} found main red — launching {_REPAIR_STEP.skill}"
        else:
            said = f"{step.id} red — launching {_REPAIR_STEP.skill}"
        state.history.append(said)
        self.notifier.send(f"{self._headline(state)} — {said}")
        self._launch_run(state, change, _REPAIR_STEP, audited=None, run=_REPAIR_STEP.id,
                         provider=provider)
        return True

    def _repair_provider_or_halt(self, state: WalkState) -> str | None:
        """The provider the repair runs on, or `None` once the walk has halted naming what the
        provider file lacks. The repair is no table step with an entry of its own in the provider
        file, so it takes the entry of the first step that runs as its seat."""
        seat = next(candidate for candidate in self.steps if candidate.role == _REPAIR_STEP.role)
        return self._provider_or_halt(state, seat)

    def _settle_repair(self, state: WalkState, change: ChangeLayout, outcome: str) -> None:
        """The repair has ended (CP-862–CP-866, CP-1317). It answers the red the walk launched it
        for, so every halt is named at that step: the marker step's `red-suite`, or QA's step's
        `qa-main-red`."""
        for_qa = state.repair_step == _QA_STEP.id
        halted_step = _QA_STEP if for_qa else next(
            candidate for candidate in self.steps
            if candidate.evidence is Evidence.MARKER_COMMIT)
        code = _QA_MAIN_RED if for_qa else _RED_SUITE
        bare = f"{code} — {state.qa_main_red}" if for_qa else code
        if outcome not in _FINISHED:
            self._halt(state, halted_step, bare)
            return
        before = set(state.repair_reports_before)
        new = [path for path in self.reader.repair_reports(change) if path not in before]
        if not new:
            self._halt(state, halted_step, bare)
            return
        # One run writes one report. Should several be new, none is trusted over another: the
        # repair is merged only if every one says so, and the halt names the first that does not.
        for report in new:
            word = self.reader.repair_verdict(report)
            if word != _MERGED:
                self._halt(state, halted_step, f"{code} — {_REPAIR_STEP.skill} "
                                               f"{word or 'declared no verdict'}: {report}")
                return
        provider = self._repair_provider_or_halt(state)
        if provider is None:
            return
        refusal = self._advance_onto_main(state, change, provider)
        if refusal is not None:
            self._halt(state, halted_step, f"{code} — main's advance refused after "
                                           f"{_REPAIR_STEP.skill} {_MERGED} ({refusal})")
            return
        if for_qa:
            said = f"{_REPAIR_STEP.id} {_MERGED} — asking {_QA_STEP.id}'s verdict again"
            state.history.append(said)
            self.notifier.send(f"{self._headline(state)} — {said}")
            self._settle_qa(state, change, _QA_STEP)
            return
        state.history.append(f"{_REPAIR_STEP.id} {_MERGED} — re-closing")
        self.notifier.send(f"{self._headline(state)} — {_REPAIR_STEP.skill} {_MERGED} — "
                           f"{halted_step.id} re-closing")
        self._launch_run(state, change, halted_step, audited=None)

    def _advance_onto_main(self, state: WalkState, change: ChangeLayout,
                           provider: str) -> str | None:
        """Take `main`'s advance onto the change's branch in each repository the change commits
        in: the instance's worktree, then an external product's (CP-863). Why it was refused, as
        a word for the halt reason, or `None` when every advance landed. The first refusal stops
        it, so a later repository is never advanced past a refused one."""
        surface = _SURFACES.get(provider)
        if surface is None:
            return f"no surface for provider {provider}"
        worktrees = [change.worktree]
        product = self.reader.code_repo(change, state.product_path)
        if product != change.instance_root:
            worktrees.append(os.path.join(product, ".worktrees", change.key))
        for worktree in worktrees:
            exit_code = self.processes.run(
                [os.path.join(state.core_dir, "tools", "locked_python.sh"),
                 os.path.join(state.core_dir, "tools", "commit_builder.py"),
                 "--repo", worktree, "advance", "--from", _MAIN, "--actor", _REPAIR_STEP.role,
                 "--surface", surface],
                cwd=worktree, env=with_provider(self.environ, provider))
            if exit_code != 0:
                return f"exit {exit_code}"
        return None

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
                                    f"(after task {state.paused_after}) — no later task "
                                    "landed")
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

        `environment-not-ready` is checked first, at the head of the marker branch and of the
        integrity branch: a not-ready environment never ran the suite, so the verdict beside it
        (`red-suite`, `integrity-stopped`) would name the wrong cause.

        The closing marker's other reasons come next — `red-suite`, `missing-suite`,
        `missing-language` — and only a marker passing all three has its tasks' commit shape
        read (`_commit_shape_verdict`), on the repo `product_path` puts the per-task commits in.
        `missing-environment` is last, for the marker and for the report alike: only a record that
        passed everything above it is read for the environment it names."""
        if step == _QA_STEP:
            return self._qa_landed_refusal(change)
        if step.declared_prefix == _SECURITY_PREFIX:
            verdict = self.reader.declared_verdict(change, step)
            if verdict == "stopped":
                return "security-stopped"
            return None if verdict in _SECURITY_PASSING else "missing-security"
        if step.declared_prefix == _INTEGRITY_PREFIX:
            if _NOT_READY in self.reader.report_environment_kinds(change, step):
                return _NOT_READY_REASON
            verdict = self.reader.declared_verdict(change, step)
            if verdict == "stopped":
                return "integrity-stopped"
            if verdict != "pass":
                return "missing-integrity"
            return self._environment_verdict(change,
                                             self.reader.report_environment_kinds(change, step))
        if step.evidence is Evidence.MARKER_COMMIT:
            if _NOT_READY in self.reader.marker_environment_kinds(change):
                return _NOT_READY_REASON
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
                                                 self.reader.marker_environment_kinds(change)))
        return None

    def _qa_landed_refusal(self, change: ChangeLayout) -> str | None:
        """QA's red verdict over a step that already landed, for a start to read (CP-1320,
        CP-1322). Asked only when the step applies and its record is committed on the branch: a
        refused run can leave that record behind, and no later step reads QA's files, so this is
        the one place a refused red is not walked past. `None` is accepted, or nothing to judge."""
        if not self.reader.qa_decision(change).applies or not self.reader.is_done(change, _QA_STEP):
            return None
        return qa_red_verdict(self.reader, self.behave, change, self.qa_places(change),
                              environ=self.environ, draft=False).refusal

    def _environment_verdict(self, change: ChangeLayout, kinds: list[str]) -> str | None:
        """`missing-environment` unless a record that passed every other check declares at least
        one environment and every declared kind is one of the environment kinds. The kinds are not
        checked against a fresh resolution, and `none` — a run that issued no suite — passes
        only where the card on `main` has no command."""
        if not kinds or any(kind not in _ENVIRONMENT_KINDS for kind in kinds):
            return "missing-environment"
        if _NO_SUITE in kinds and not self.reader.card_has_no_suite(change):
            return "missing-environment"
        return None

    def _commit_shape_verdict(self, change: ChangeLayout, product_path: str) -> str | None:
        return commit_shape_verdict(self.reader, change, product_path)

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
        return _task_numbers(lines, prefix)

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
        if (step.evidence in _BEHIND_THE_CLOSE and not state.close_passed
                and not self._run_the_close(state, change)):
            return
        if ((step.runs_when is not None or step == _QA_STEP)
                and not self._gate_lets_through(state, change, step)):
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

    def _run_the_close(self, state: WalkState, change: ChangeLayout) -> bool:
        """Run the close in front of the audit or the seal: whether the walk may go on. It is no
        run: it launches no seat or provider, writes no `halt_report.md`, makes no pending entry,
        shim or commit, and tells the owner nothing on a pass. A card that does not say `behave`
        passes it with the card's own reading and asks the path tool nothing. On a `behave` card
        the verdict decides, and any refusal ends the walk halted at `close`."""
        card = self.reader.behave_card(change)
        if not card.says_behave:
            state.history.append(f"close passed — {card.read}")
            state.close_passed = True
            return True
        try:
            places = self.qa_places(change)
        except development_path.ToolError as error:
            self._halt_at(state, CLOSE, f"behave-unavailable — {error.message}")
            return False
        verdict = close_verdict(git=self.reader.git, behave=self.behave, places=places,
                                environ=self.environ)
        if verdict.refusal is not None:
            self._halt_at(state, CLOSE, verdict.refusal)
            return False
        count = "1 scenario" if verdict.scenarios == 1 else f"{verdict.scenarios} scenarios"
        line = f"close passed — {count} passed at {verdict.commit[:behave_run.SHORT_HASH_LENGTH]}"
        state.history.append(line)
        state.close_line = line
        state.close_passed = True
        return True

    def _gate_lets_through(self, state: WalkState, change: ChangeLayout, step: Step) -> bool:
        """The one gate every way into a step with a `RunsWhen` line shares, because `_start` and
        `_after` both reach a step through `_launch_step`. `True` launches the step. A pass calls
        `_after` on the step, so the walk past it is the walk past any landed step, and returns
        `False`."""
        verdict = self.reader.run_verdict(change, step)
        if verdict is RunVerdict.UNSETTLED:
            self._halt_for_missing_verdict(state, change, step)
            return False
        if step.runs_when is not None:
            self._clear_own_report(change, step)
        if verdict is RunVerdict.PASS:
            state.history.append(self.reader.pass_line(change, step))
            self._after(state, change, step)
            return False
        if step == _QA_STEP:
            held = self.reader.qa_way_in(change)
            if held is not None:
                self._halt(state, step, f"no-way-in — {held} — {_NO_WAY_IN_ADVICE}")
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
        if step == _QA_STEP and (self.qa_asks.load(state.project, state.key).runs
                                 >= QA_RUN_CEILING):
            self._halt(state, step, _QA_RUNS_SPENT.format(ceiling=QA_RUN_CEILING, key=state.key))
            return
        if step.evidence is Evidence.MARKER_COMMIT and not self._environment_allows(
                state, change, step):
            return
        if provider is None:
            provider = self._provider_or_halt(state, step)
            if provider is None:
                return
        run = run or (step.id if audited is None else f"{step.id}-{audited}")
        shim = self._shim_path(state, run)
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
        # The close's line is the seal's alone and is removed from every other launch, for the same
        # reason: a seal reached by `--advance` inherits the last audit's environment.
        if step.evidence is Evidence.SEALED and state.close_line:
            env[CLOSE_VERDICT_VARIABLE] = state.close_line
        else:
            env.pop(CLOSE_VERDICT_VARIABLE, None)
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

    @staticmethod
    def _shim_path(state: WalkState, run: str) -> str:
        return os.path.join(state.shim_dir, f"chain-{state.chain_name}-{state.project}-{run}.sh")

    def _write_shim(self, state: WalkState, shim: str, run: str) -> None:
        completion_shim.write_shim(self.files, shim, engine_path=self.engine_path,
                                   advance_args=("--advance", self.store.path, run),
                                   log_path=self._log_path(state))

    def _after(self, state: WalkState, change: ChangeLayout, step: Step) -> None:
        """The step has landed: launch the next one, or end the walk after the last. A walk
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
        self._halt_at(state, step.id, reason)

    def _halt_at(self, state: WalkState, stopped_at: str, reason: str) -> None:
        """The one writer of `stopped at <id>: <reason>`; `stopped_at` is a step's id, or `close`."""
        self._end(state, Ended.HALTED, f"stopped at {stopped_at}: {reason}")

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
        # The engine inherits the last step's launch environment, so the owner's ask is removed
        # here as at every launch that is not a suite step: the ask never outlives its walk.
        env = with_provider(self.environ, forced_provider)
        env.pop(_GATE_OWNERS_MAC_VARIABLE, None)
        env.pop(CLOSE_VERDICT_VARIABLE, None)
        run_end_hook(hook, end, cwd=cwd, processes=self.processes, notifier=self.notifier,
                     headline=headline, env=env)

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


# --- the ports `chain.py` does not have -------------------------------------------------


class ExactFiles:
    """Reads and writes a text file with its line endings as they lie on disk. `chain.Files`
    reads with universal newlines, so a companion with CRLF endings would come back rewritten;
    the carry copies and restores bytes, so it goes through this port."""

    def read_text(self, path: str) -> str | None:
        """The file's text, every line ending kept, or `None` when it cannot be read — the shape
        `Files.read_text` has."""
        try:
            with open(path, encoding="utf-8", newline="") as handle:
                return handle.read()
        except (OSError, UnicodeDecodeError):
            return None

    def write_text(self, path: str, text: str) -> None:
        """Replace the file with `text`, line endings untouched. The text goes to a sibling file
        first and the sibling replaces the target, so a crash never leaves a half-written file."""
        staging = f"{path}.{os.getpid()}.staging"
        try:
            with open(staging, "w", encoding="utf-8", newline="") as handle:
                handle.write(text)
            os.replace(staging, path)
        except BaseException:
            with contextlib.suppress(OSError):
                os.unlink(staging)
            raise


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

    def branch_tip(self, repo: str, branch: str) -> str | None:
        """The commit `branch` points at in `repo`, or `None` when the branch does not exist or
        git cannot answer — the same absence-as-a-value shape. One `rev-parse --verify --quiet`
        of the full ref name, so a tag or a path of the same name is never read as the branch."""
        result = subprocess.run(
            ["git", "-C", repo, "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}"],
            capture_output=True, text=True)
        sha = result.stdout.strip()
        return sha if result.returncode == 0 and sha else None

    def merge_base(self, repo: str, a: str, b: str) -> str | None:
        """The commit where branch `b` leaves `a`, or `None` when either does not exist or git
        cannot answer — the same absence-as-a-value shape."""
        result = subprocess.run(["git", "-C", repo, "merge-base", a, b],
                                capture_output=True, text=True)
        sha = result.stdout.strip()
        return sha if result.returncode == 0 and sha else None

    def show(self, repo: str, ref: str, path: str) -> str | None:
        """The text of `path` at `ref`, or `None` when the file is absent there, the ref does not
        exist or git cannot answer."""
        result = subprocess.run(["git", "-C", repo, "show", f"{ref}:{path}"],
                                capture_output=True, text=True)
        return result.stdout if result.returncode == 0 else None

    def changed_paths(self, repo: str, sha: str) -> list[str]:
        """The paths one commit changes (a root commit's included), or `[]` when the commit does
        not exist or git cannot answer."""
        result = subprocess.run(
            ["git", "-C", repo, "diff-tree", "--root", "--no-commit-id", "--name-only", "-r", sha],
            capture_output=True, text=True)
        if result.returncode != 0:
            return []
        return [line for line in result.stdout.splitlines() if line]

    def touched_paths(self, repo: str, sha: str) -> list[str] | None:
        """The repo-relative paths one commit touches, a root commit's included, or `None` when
        git cannot answer — never `[]` for a failure, so a commit git cannot read is told apart
        from one that touches nothing. A merge lists only the paths whose content differs from
        every parent (the combined-diff form), and with no rename detection a rename lists both
        its old and its new path. `changed_paths` is left as it is: QA's verdict reads it.

        `-z` because without it git C-quotes a path outside ASCII or holding a quote, and a quoted
        path under the scenario folder no longer starts with the folder, so the close would pass
        a commit that changed a scenario."""
        result = subprocess.run(
            ["git", "-C", repo, "diff-tree", "--root", "--no-commit-id", "--name-only", "-r", "-c",
             "-z", sha], capture_output=True, encoding="utf-8", errors="surrogateescape")
        if result.returncode != 0:
            return None
        return [path for path in result.stdout.split("\0") if path]

    def is_ancestor(self, repo: str, older: str, newer: str) -> bool:
        """Whether `older` is an ancestor of `newer`, read by `merge-base --is-ancestor`'s exit
        status; `False` for an unknown commit, never an exception."""
        return subprocess.run(["git", "-C", repo, "merge-base", "--is-ancestor", older, newer],
                              capture_output=True).returncode == 0

    def toplevel(self, path: str) -> str | None:
        """The top level of the repository `path` is in, as git gives it, or `None` when `path`
        is in no repository or git cannot answer — the same absence-as-a-value shape."""
        result = subprocess.run(["git", "-C", path, "rev-parse", "--show-toplevel"],
                                capture_output=True, text=True)
        top = result.stdout.strip()
        return top if result.returncode == 0 and top else None

    def current_branch(self, repo: str) -> str | None:
        """The short name of the branch `repo`'s checkout has out, or `None` when HEAD is
        detached or git cannot answer. One `symbolic-ref --quiet --short HEAD`: a non-zero exit is
        the absence."""
        result = subprocess.run(["git", "-C", repo, "symbolic-ref", "--quiet", "--short", "HEAD"],
                                capture_output=True, text=True)
        branch = result.stdout.strip()
        return branch if result.returncode == 0 and branch else None

    def path_status(self, repo: str, path: str) -> list[str] | None:
        """The `git status --porcelain` lines for one repo-relative `path`, untracked files
        listed singly, the reading `product_checkout.Checkout` makes narrowed to one path. `[]`
        for a clean path, `None` when git cannot answer."""
        result = subprocess.run(
            ["git", "-C", repo, "--no-optional-locks", "status", "--porcelain",
             "--untracked-files=all", "--", path], capture_output=True, text=True)
        if result.returncode != 0:
            return None
        return [line for line in result.stdout.split("\n") if line]

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
    "change": CHANGE_STEPS,
    "walk": WALK_STEPS,
}


def build_chain(state_path: str, *, notifier_command: str, engine_path: str,
                steps: tuple[Step, ...] | None = None) -> DevelopmentChain:
    files = Files()
    processes = Processes()
    table = CHANGE_STEPS if steps is None else steps
    name = CHAIN_NAMES.get(id(table), "change")
    return DevelopmentChain(
        store=StateStore(files, state_path, name),
        reader=DiskReader(files=files, git=Git()),
        files=files,
        exact_files=ExactFiles(),
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
        environment_check=GateEnvironmentCheck(
            files=files, gate_files=gate_suite.ReadOnlyFiles(), contract=_real_contract,
            tracked_files=_real_tracked_files, record_reader=gate_suite.GitRecordReader(),
            guest_job=gate_suite.GuestJob(Path.home() / gate_suite.GUEST_JOB, str(Path.home()))),
        behave=behave_run.ThrowawayBehave(),
        qa_places=_real_qa_places,
        qa_asks=QaAskStore(files, os.path.dirname(os.path.abspath(state_path))),
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
    default: a walk advanced on the change table has no `station` or `open` step to
    settle, and crashed on its first advance (measured on a satellite, 2026-09-18)."""
    return raw["chain_name"] if raw.get("chain_name") in STEP_TABLES else default


def card_product_path(files, instance_root: str, project: str, home: str) -> str | None:
    """The card's `Product path:` resolved as the chain's launcher resolves it
    (`core/launchers/change/launcher.sh`): `~/` against `home`, an absolute path as
    written, a relative one against `instance_root`. `None` when the card or the line is missing."""
    card = files.read_text(os.path.join(instance_root, "system", "projects", project,
                                        "project.md"))
    found = _CARD_PRODUCT_PATH.search(card or "")
    if found is None:
        return None
    value = found.group(1).split("<!--", 1)[0].strip()
    if not value:
        return None
    if value.startswith("~/"):
        return os.path.join(home, value[2:])
    return os.path.join(instance_root, value)  # an absolute `value` wins the join


def check_commit_shape(args, *, files, git, home: str, out, err) -> int:
    """`--check-commit-shape`: the chain's commit-shape verdict on the closing marker the developer
    is about to commit. Prints `commit shape: ok` and exits 0, or prints the verdict the chain
    would halt on — `missing-red-commit — task <N>…` or `unreadable-plan` — and exits 1.

    It reads the change where the chain reads it, and refuses (exit 2) inputs that cannot name it,
    rather than answering of nothing: an answer of `ok` over no commits is the very miss this check
    exists to stop. The product path is the card's, resolved as the launcher resolves it, so the
    developer resolves nothing by hand; `--instance-root` is the main checkout, the folder whose
    `.worktrees/<key>` holds the change; and the repo the task commits land in must carry the key's
    branch with commits on it."""
    missing = [flag for flag, value in (("--instance-root", args.instance_root),
                                        ("--project", args.project),
                                        ("--draft-body", args.draft_body)) if not value]
    if missing:
        print(f"chain_development: --check-commit-shape requires {', '.join(missing)}", file=err)
        return 2
    key = args.check_commit_shape
    root = args.instance_root
    if not files.is_dir(os.path.join(root, ".worktrees", key)):
        print(f"chain_development: no change worktree {root}/.worktrees/{key} — --instance-root is "
              f"the main checkout that holds it, and {key} must be the change's key", file=err)
        return 2
    product_path = card_product_path(files, root, args.project, home)
    if product_path is None:
        print(f"chain_development: no Product path: line in "
              f"{root}/system/projects/{args.project}/project.md", file=err)
        return 2
    draft = files.read_text(args.draft_body)
    if draft is None:
        print(f"chain_development: no draft body at {args.draft_body}", file=err)
        return 2
    reader = DiskReader(files=files, git=git, draft_body=draft)
    change = ChangeLayout(root, args.project, key)
    repo = reader.code_repo(change, product_path)
    if not git.commits_ahead(repo, _MAIN, key):
        print(f"chain_development: no commits of {key} on {repo} — the card's Product path must "
              f"name the repo the task commits land in", file=err)
        return 2
    verdict = commit_shape_verdict(reader, change, product_path)
    if verdict is None:
        print("commit shape: ok", file=out)
        return 0
    print(verdict, file=out)
    return 1


def _named_change(args, flag: str, *, files, err) -> ChangeLayout | None:
    """What the QA commands share: the change they are asked about, or `None` after saying on
    `err` why it cannot be named (the caller exits 2). Like `--check-commit-shape`, they refuse
    rather than answer of a change they cannot find."""
    missing = [name for name, value in (("--instance-root", args.instance_root),
                                        ("--project", args.project)) if not value]
    if missing:
        print(f"chain_development: {flag} requires {', '.join(missing)}", file=err)
        return None
    key = getattr(args, flag[2:].replace("-", "_"))
    change = ChangeLayout(args.instance_root, args.project, key)
    if not files.is_dir(change.worktree):
        print(f"chain_development: no change worktree {change.worktree} — --instance-root is "
              f"the main checkout that holds it, and {key} must be the change's key", file=err)
        return None
    return change


def _qa_command_change(args, flag: str, *, files, places, err) -> tuple[ChangeLayout, dict] | None:
    """What `--qa-applies` and `--check-qa-red` share: the change they are asked about and QA's
    places, or `None` after saying on `err` why neither can be named (the caller exits 2)."""
    change = _named_change(args, flag, files=files, err=err)
    if change is None:
        return None
    try:
        return change, places(change)
    except development_path.ToolError as exc:
        print(f"chain_development: {exc.code} — {exc.message}", file=err)
        return None


def qa_ask_place(args, *, files, out, err) -> int:
    """`--qa-ask-place`: where a run of `implementation` or `design` leaves its ask of QA's step
    in change KEY's worktree. Prints that path and exits 0; exits 2 when the change cannot be
    named. The place comes from the layout alone, so no product is resolved. Writes, launches and
    sends nothing."""
    change = _named_change(args, "--qa-ask-place", files=files, err=err)
    if change is None:
        return 2
    print(change.qa_ask, file=out)
    return 0


def qa_applies(args, *, files, git, places, out, err) -> int:
    """`--qa-applies`: whether QA's step applies to the change, asked of the one decision
    (CP-1302). Prints `red-behaviour applies — <read>` and exits 0, or `red-behaviour does not
    apply — <read>` and exits 1; exits 2 when the change cannot be named. Writes, launches and
    sends nothing."""
    found = _qa_command_change(args, "--qa-applies", files=files, places=places, err=err)
    if found is None:
        return 2
    decision = DiskReader(files=files, git=git).qa_decision(found[0])
    verb = "applies" if decision.applies else "does not apply"
    print(f"{_QA_STEP.id} {verb} — {decision.read}", file=out)
    return 0 if decision.applies else 1


def check_qa_red(args, *, files, git, behave, places, environ: dict, out, err) -> int:
    """`--check-qa-red`: the chain's verdict on QA's red, asked before QA commits it. Prints
    `qa red: accepted`, `qa red: no reach — "<the No reach: line>"` or the refusal on line 1,
    then `Base commit: <sha>`, then a `Scenario: <location> — <status>` line for each scenario
    the red run reported; exits 0 accepted or no reach, 1 refused, 2 when the change cannot be
    named. `--draft` judges the working tree. Writes nothing outside the throwaway run's own
    directory."""
    found = _qa_command_change(args, "--check-qa-red", files=files, places=places, err=err)
    if found is None:
        return 2
    change, where = found
    verdict = qa_red_verdict(DiskReader(files=files, git=git), behave, change, where,
                             environ=environ, draft=args.draft)
    if verdict.no_reach is not None:
        first_line = f'qa red: no reach — "{verdict.no_reach}"'
    else:
        first_line = verdict.refusal or "qa red: accepted"
    print(first_line, file=out)
    print(f"Base commit: {verdict.base}", file=out)
    for location, status in verdict.outcomes:
        print(f"Scenario: {location} — {status}", file=out)
    return 0 if verdict.refusal is None else 1


def main(argv: list[str] | None = None) -> int:
    """`--start <state>` is the launcher's entry; `--advance <state> <run> <outcome>` is what a
    per-run shim fires; `--describe <state>` is what the launcher's `--dry-run` asks. None ever
    lets a traceback out as the whole answer: the advance runs detached from a hook nobody watches,
    so stderr goes to the chain's log and the owner's channel is the only place a stop can be seen
    — and the describe, which answers at a terminal, sends to that channel nothing at all."""
    try:
        from dotenv import load_dotenv
        from pathlib import Path
        load_dotenv()
        load_dotenv(Path.home() / ".env")
    except ImportError:
        pass

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
    parser.add_argument("--check-commit-shape", metavar="KEY",
                        help="the commit-shape verdict the chain would give change KEY's closing "
                             "marker, asked of the draft body in --draft-body before the marker "
                             "is committed; needs --instance-root (the main checkout) and "
                             "--project, reads the product path off the card, and writes, "
                             "launches and sends nothing")
    parser.add_argument("--qa-applies", metavar="KEY",
                        help="whether QA's step applies to change KEY, asked of the chain's one "
                             "decision: exit 0 and `red-behaviour applies — <read>`, or exit 1 "
                             "and `red-behaviour does not apply — <read>`; needs --instance-root "
                             "(the main checkout) and --project, and writes, launches and sends "
                             "nothing")
    parser.add_argument("--check-qa-red", metavar="KEY",
                        help="the verdict the chain would give change KEY's QA red, asked by "
                             "running Behave on a throwaway copy: `qa red: accepted`, "
                             "`qa red: no reach — \"<the No reach: line>\"` or the refusal, "
                             "then the base commit and each red-run scenario; exit 0 accepted "
                             "or no reach, 1 refused; needs --instance-root and --project")
    parser.add_argument("--qa-ask-place", metavar="KEY",
                        help="the place in change KEY's folder, in its change worktree, where a "
                             "run of implementation or design leaves an ask of QA's step: the "
                             "reason, in plain text, left uncommitted; prints that path and "
                             "exits 0; needs --instance-root (the main checkout) and --project, "
                             "and writes, launches and sends nothing")
    parser.add_argument("--draft", action="store_true",
                        help="with --check-qa-red, judge the working tree rather than commits")
    parser.add_argument("--draft-body", metavar="FILE",
                        help="the closing marker's draft body, for --check-commit-shape")
    parser.add_argument("--instance-root")
    parser.add_argument("--product-path")
    parser.add_argument("--project")
    parser.add_argument("--core-dir")
    parser.add_argument("--shim-dir")
    parser.add_argument("--steps", choices=sorted(STEP_TABLES), default="change",
                        help="which walk this is: the change pipeline, or the same "
                             "pipeline entered at the two journey moves that open a station "
                             "and a change")
    parser.add_argument("--notifier", default="")
    parser.add_argument("--keep-awake", action="store_true")
    parser.add_argument("--context-cap", type=_positive_integer, default=DEFAULT_CONTEXT_CAP,
                        metavar="TOKENS",
                        help="the context, in tokens, past which the developer's run is told to "
                             "pause and a fresh one takes over; read only "
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
                                  args.list_open_changes, args.check_commit_shape,
                                  args.qa_applies, args.check_qa_red,
                                  args.qa_ask_place) if entry]
    if len(chosen) > 1:
        print("chain_development: --start, --advance, --describe, --stop, "
              "--list-open-changes, --check-commit-shape, --qa-applies, --check-qa-red and "
              "--qa-ask-place are mutually exclusive", file=sys.stderr)
        return 2
    if not chosen:
        print("chain_development: one of --start, --advance, --describe, --stop, "
              "--list-open-changes, --check-commit-shape, --qa-applies, --check-qa-red or "
              "--qa-ask-place is required", file=sys.stderr)
        return 2

    if args.qa_ask_place:
        return qa_ask_place(args, files=Files(), out=sys.stdout, err=sys.stderr)

    if args.qa_applies:
        return qa_applies(args, files=Files(), git=Git(), places=_real_qa_places,
                          out=sys.stdout, err=sys.stderr)

    if args.check_qa_red:
        return check_qa_red(args, files=Files(), git=Git(), behave=behave_run.ThrowawayBehave(),
                            places=_real_qa_places, environ=dict(os.environ),
                            out=sys.stdout, err=sys.stderr)

    if args.check_commit_shape:
        return check_commit_shape(args, files=Files(), git=Git(), home=os.path.expanduser("~"),
                                  out=sys.stdout, err=sys.stderr)

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
