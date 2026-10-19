#!/usr/bin/env python3
"""build_idea.py — a refine report's `## Next moves` run as a queue, by a program.

WHY THIS EXISTS
    `shukuba-refine` ends by writing a table of the moves a landed unit leaves owed — close the
    station, pick a seed, cut the route, walk the next change — and until this engine the owner
    typed each of them. The table already says which seat makes each move and the command that
    starts it, so what was missing was only something to read it and start the commands in the
    order it gives. This is that: the report is the queue, and the engine is nothing but its
    reader.

WHY IT IS DETERMINISTIC
    No model decides what runs next. The kinds a row can be are a literal in this file, spelled
    the way the two refine prompts spell them, and each maps to one launcher and
    one way of telling that it worked. The sweep's launcher is the one the project card's
    `**Definition:**` names, `chain-product` for `full` and `chain-agari` for `prd-agari`; a `none`
    card has no sweep. A row whose kind is not in the table is refused before
    anything starts. A runnable row whose Command cell is not the command the table says that
    kind runs is refused alone: it never runs, the rows waiting on it are blocked, the rows that
    do not wait on it still run, and the queue ends halted naming the cell — one cell of prose
    no longer costs the rows before it (2026-10-13). The cell is CHECKED against the table and
    never executed, so a wrong report can cost the owner a refusal and cannot cost them a command
    they did not expect. A close's cell may name the station's dated stem after the project; the
    close is launched naming the station its row names, else the one station the queue found
    open at the shukuba root, else none, and `shukuba-retire` resolves the station from that and
    refuses one that is not open (2026-10-13). A row starts when every row its After cell names
    has LANDED and no other row of the queue is running, so the rows run one at a time, in row
    order. Landed is a fact read off the disk — the station's file moved from the shukuba root
    into trail/, a seed at the seedbed root, a seed with a checklist — and never the fact that a
    launcher exited, because every launcher backgrounds its run and returns at once: a chain started beside a still-running close finds
    the station open and opens a change for it (2026-09-18).

THE PROVIDER A ROW GOES TO
    `core/tools/providers.py` is the rule, and this module holds no provider of its own. A skill
    row runs on the provider the queue was forced onto (`--provider`, kept on the state as
    `forced_provider`), else the one the instance's `.providers.toml` (at its root) names for its
    kind (`build-idea."<kind>"`), read through the `ProviderFiles` this engine is given, which
    answers for the instance root a launch is for. An unforced
    start checks all six skill rows' entries before anything is saved or launched, so a missing
    entry, an unknown value or an unreadable file refuses the queue, naming what is wrong. The
    dry run (`--describe`) makes the same check, at the end of the same plan, so it refuses
    exactly where the start would. Each
    skill row's launch then reads the file again; a launch the file can no longer answer fails
    that row naming the entry, and the queue launches nothing more and ends halted once no run is
    in flight. A forced queue, start or dry run, never reads the file. A row that starts a
    chain is handed the force alone — its launcher reads `KENSAIAPP_AGENT_PROVIDER` as one — and
    has the variable removed when the queue is unforced, so the nested chain runs each step on
    its own provider and not on the previous row's.

THE PRODUCT CHECKOUT
    `_launch` reads the product checkout — the lines `git status --porcelain
    --untracked-files=all` prints for the state's `product_path`, the reading the seal's preflight
    makes — and keeps them on that row's pending entry, for a skill row and a chain row alike. A
    hand-off row leaves `pending` at once and records nothing, and an empty `product_path` records
    nothing. When the row's end reaches `advance`, before `_record` reads anything of it, the
    checkout is read again. A line present now and absent at launch fails the row with the
    reason, and sets `checkout_dirty`; a checkout read at launch and unreadable at the end fails
    it the same way with its own reason. While `checkout_dirty` stands the queue launches nothing
    — as for `provider_refused` — and ends halted once no run is in flight, the halted line
    naming the row and the reason; the next start clears it, and the failed row goes back to
    waiting. A line present at launch is never counted against a row, and a pending row with
    nothing recorded, every one written before this check included, is not checked. The reading,
    the comparison and both reasons are `product_checkout.py`'s, handed to the engine as
    `checkout`; the engine never writes the checkout.

WHY THE REPORT IS NEVER WRITTEN
    The report is a record of what a refine run did (`shukuba_refine_report_template.md`:
    "nothing edits it after the run that wrote it"). Progress lives in this engine's own state
    file, one per project, and the report is only ever read. A queue that ticked its own rows
    off in the report would make the record say what the queue had done, which is a second thing
    the report was never for.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import time
import traceback
from dataclasses import asdict, dataclass, field, fields
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

import completion_shim
import development_path
import journey_names
import journey_status
import pin
import product_checkout
import reporters
import providers
import walk_stop
from chain import (EXIT_ALREADY_WALKING, PROVIDERS, Files, IdSource, Notifier, Processes,
                   walk_is_live, with_provider)
from chain import StateStore as ChainStateStore
from chain_development import (_FINISHED, DEFAULT_CONTEXT_CAP, AdvanceResult,
                               ChangeLayout, DiskReader, FileLock, Git, WalkLog,
                               _positive_integer)
from chain_development import StateStore as WalkStateStore
from providers import ProviderFiles, ProvidersRefused

__version__ = "2.13.0"


# --- the kinds a row can be ---------------------------------------------------------------------


class Disposition(Enum):
    """What the engine does with a row of a kind. The five are closed: a kind the table does
    not hold is refused, so there is no sixth thing a row can turn out to want."""

    RUN_SKILL = "run_skill"    # a skill run through the skill launcher; landed is read off the disk
    RUN_CHAIN = "run_chain"    # a chain launcher; landed when the chain ends settled
    HAND_OFF = "hand_off"      # a launcher whose walk is not this queue's to wait on
    OWNER = "owner"            # a station only the owner walks; the queue stops at it
    SKIP = "skip"              # a kind with no launcher at all; named, and blocks nothing else


class Landed(Enum):
    """How a run row is known to have worked. Each is a fact a fresh session can check."""

    STATION_CLOSED = "station_closed"
    SEED_PICKED = "seed_picked"
    ROUTE_CUT = "route_cut"
    WALK_ENDED = "walk_ended"
    SEED_RETIRED = "seed_retired"
    SEED_REFINED = "seed_refined"
    DOCS_CUT = "docs_cut"
    README_STATUS_REPORTED = "readme_status_reported"
    NONE = "none"


_PROJECT = "<project>"
# The station a close acts on, by its dated stem (`BuildIdea._station` says where it comes from).
# Dropped from the argv when nothing names one.
_STATION = "<station>"
_STEM_FORM = "<YYYY-MM-DD>_<slug>"


@dataclass(frozen=True)
class Kind:
    """One row of the kind table. `arguments` may hold `<project>` and `<station>`, filled at
    `expected_argv`;
    `role` is the seat whose move it is, the value a run's telemetry is tagged with.
    `takes_context_cap` is True for the launcher that accepts `--context-cap` — `chain-change`
    alone. It is a fact of the launcher rather than of the disposition: `chain-product` is a
    `RUN_CHAIN` row too, and refuses a flag it does not know. The provider a `RUN_SKILL` row runs
    on is not the table's: the instance's `.providers.toml` names it, under `build-idea."<kind>"`
    (§ THE PROVIDER A ROW GOES TO)."""

    disposition: Disposition
    launcher: str = ""
    arguments: tuple[str, ...] = ()
    role: str = ""
    landed: Landed = Landed.NONE
    takes_context_cap: bool = False


# The two refine prompts own report kinds; `refine a seed` is the engine's retirement
# continuation. The suite compares the report kinds and commands with both prompt tables.
KINDS: dict[str, Kind] = {
    # No launcher of its own: the card's `Definition:` names the chain (`SWEEP_LAUNCHERS`).
    "sweep the product's companions": Kind(
        Disposition.RUN_CHAIN, "", (_PROJECT,), landed=Landed.WALK_ENDED),
    "close the reached station": Kind(
        Disposition.RUN_SKILL, "skill", ("shukuba-retire", _PROJECT, _STATION), "scrum-master",
        Landed.STATION_CLOSED),
    # Immediately after the close it follows: the table reads in the order the queue runs the two.
    "readme-status": Kind(
        Disposition.RUN_SKILL, "skill", ("readme-status", _PROJECT), "content-editor",
        Landed.README_STATUS_REPORTED),
    "pick a seed": Kind(
        Disposition.RUN_SKILL, "skill", ("nemawashi-pick", _PROJECT), "pm", Landed.SEED_PICKED),
    "cut the route": Kind(
        Disposition.RUN_SKILL, "skill", ("stations-from-seed", _PROJECT), "pm", Landed.ROUTE_CUT),
    "walk the next change": Kind(Disposition.HAND_OFF, "chain-change", (_PROJECT,),
                                 takes_context_cap=True),
    "the owner's act": Kind(Disposition.OWNER),
    "retire a seed": Kind(Disposition.RUN_SKILL, "skill", ("nemawashi-retire", _PROJECT),
                          "scrum-master", Landed.SEED_RETIRED),
    "refine a seed": Kind(Disposition.RUN_SKILL, "skill", ("nemawashi-refine", _PROJECT),
                          "principal-pm", Landed.SEED_REFINED),
    "cut from the product's documents": Kind(
        Disposition.RUN_SKILL, "skill", ("seeds-from-product-docs", _PROJECT),
        "principal-pm", Landed.DOCS_CUT),
    "re-run a halted cut": Kind(Disposition.OWNER),
    "drop a seed": Kind(Disposition.SKIP),
    "cut a seed": Kind(Disposition.SKIP),
    "route across projects": Kind(Disposition.SKIP),
}

_RETIRE = "retire a seed"
_PICK = "pick a seed"
_SWEEP = "sweep the product's companions"
_REFINE = "refine a seed"
_NEMAWASHI_KINDS = frozenset({
    "sweep the product's companions", "cut from the product's documents",
    "re-run a halted cut", "route across projects", "pick a seed", "cut the route",
    "walk the next change", "the owner's act",
})

_RUNNABLE = frozenset({Disposition.RUN_SKILL, Disposition.RUN_CHAIN, Disposition.HAND_OFF})
# The rows whose launcher can answer EXIT_ALREADY_WALKING: only a chain start refuses a live walk, a
# skill launcher never does (CP-540).
_CHAIN_STARTS = frozenset({Disposition.RUN_CHAIN, Disposition.HAND_OFF})

# The queue's own members in the provider file: every kind whose row runs a skill. A chain row is
# none — it is handed the force alone — so an entry for one is never asked about.
_SKILL_ROWS: tuple[str, ...] = tuple(
    move for move, kind in KINDS.items() if kind.disposition is Disposition.RUN_SKILL)


class QueueRefused(Exception):
    """A queue that cannot start from what is on disk. The entry point converts it to a message
    on stderr and to the owner's channel before anything launches."""


NO_STATION_MESSAGE = ("build_idea: nothing was started — {key} serves no station, "
                      "so it is owed no refine report")


class UnitReportMissing(QueueRefused):
    """The unit's own `<key>_report.md` is in no seed folder. It carries the unit's layout so the
    start can ask whether the unit serves a station; every other refusal stays a plain
    `QueueRefused`, among them the retired seed's missing nemawashi-refine report."""

    def __init__(self, message: str, layout: ChangeLayout):
        super().__init__(message)
        self.layout = layout


@dataclass(frozen=True)
class NoStationStart(AdvanceResult):
    """The one start that succeeds with nothing to run: the unit serves no station, so it is owed
    no refine report and there is no queue to begin. `key` is the unit that was asked about."""

    key: str

    def message(self) -> str:
        return NO_STATION_MESSAGE.format(key=self.key)


# --- the card's definition: which chain a sweep runs ------------------------------------------


class Definition(str, Enum):
    """How far the project card says the product's definition goes. The value is the word the card
    writes after `**Definition:**`, so a card's text is read into a member by its value."""

    FULL = "full"
    PRD_AGARI = "prd-agari"
    NONE = "none"


# The launcher folder a sweep runs, by definition. `none` has no entry: it has no sweep.
SWEEP_LAUNCHERS: dict[Definition, str] = {
    Definition.FULL: "chain-product",
    Definition.PRD_AGARI: "chain-agari",
}

_DEFINITION_LINE = "**Definition:**"
_COMMENT_OPENS = "<!--"
_THE_SWEEP_IS_DECIDED = "and the sweep is decided by that line"
_THE_THREE = "full, prd-agari or none"


def card_path(instance_root: str, project: str) -> str:
    """The project card the sweep's definition is read from."""
    return os.path.join(instance_root, "system", "projects", project, "project.md")


def read_definition(card_text: str | None, *, card: str) -> Definition:
    """The card's definition, read the way `chain-change` reads it: the one line beginning exactly
    `**Definition:**`, its text after the label up to any `<!--`, trimmed. `card_text` is `None`
    when there is no card file, and `card` is the path the refusals name. A card with no such
    line, with more than one, or with a value outside the three refuses."""
    lines = [line for line in (card_text or "").splitlines() if line.startswith(_DEFINITION_LINE)]
    if not lines:
        raise QueueRefused(f"no 'Definition:' line in {card}, {_THE_SWEEP_IS_DECIDED} — "
                           f"add {_DEFINITION_LINE} {_THE_THREE}")
    if len(lines) > 1:
        raise QueueRefused(f"{card} carries {len(lines)} 'Definition:' lines, "
                           f"{_THE_SWEEP_IS_DECIDED} — it must carry one")
    value = lines[0][len(_DEFINITION_LINE):].split(_COMMENT_OPENS)[0].strip()
    try:
        return Definition(value)
    except ValueError:
        raise QueueRefused(f"'Definition:' in {card} reads '{value}', {_THE_SWEEP_IS_DECIDED} — "
                           f"it must be {_THE_THREE}") from None


def sweep_definition(card_text: str | None, *, instance_root: str, project: str,
                     number: int) -> Definition:
    """The definition a sweep row, row `number`, runs under: the card's, read by
    `read_definition`. A `none` card defines no product chain, so it has no sweep row to run and
    this refuses naming the row."""
    card = card_path(instance_root, project)
    definition = read_definition(card_text, card=card)
    if definition is Definition.NONE:
        raise QueueRefused(f"row {number}: 'Definition:' in {card} reads {definition.value} — "
                           f"the card defines no product chain, so no \"{_SWEEP}\" row runs "
                           f"for it")
    return definition


# --- the table ------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Row:
    """One row of `## Next moves`. `command` and `source` are the cells as written; `after` is
    the row numbers this row waits on, already read."""

    number: int
    move: str
    whose: str
    command: str
    after: tuple[int, ...]
    source: str


_COLUMNS = ("#", "move", "whose", "command", "after")
_SIX_COLUMN_HEADER = "| # | Move | Whose | Command | After | From |"
_NO_WAIT = "—"
_AFTER_LIST = re.compile(r"\d+(?:\s*,\s*\d+)*")


def expected_argv(kind: str, *, core_dir: str, project: str,
                  definition: Definition | None = None, station: str = "") -> list[str]:
    """The command a runnable kind starts: its launcher under `<core_dir>/launchers/`, then its
    arguments with the project and the `station` stem filled in — a kind given no station drops
    `<station>`. The sweep's launcher is the chain its card's `definition` names, so for the sweep
    one is required and `none` has no argv; every other kind ignores it."""
    spec = KINDS[kind]
    if spec.disposition not in _RUNNABLE:
        raise ValueError(f"{kind!r} runs nothing — {spec.disposition.value} rows have no argv")
    launcher = spec.launcher
    if kind == _SWEEP:
        if definition not in SWEEP_LAUNCHERS:
            raise ValueError(f"the sweep runs the chain its card's definition names, and "
                             f"{definition!r} names none")
        launcher = SWEEP_LAUNCHERS[definition]
    script = os.path.join(core_dir, "launchers", launcher, "launcher.sh")
    filled = {_PROJECT: project, _STATION: station}
    return [script] + [filled.get(argument, argument) for argument in spec.arguments
                       if not (argument == _STATION and not station)]


def _station_position(move: str) -> int | None:
    """Where a kind's argv carries the station, or `None` for a kind that takes none."""
    arguments = KINDS.get(move, Kind(Disposition.SKIP)).arguments
    return arguments.index(_STATION) + 1 if _STATION in arguments else None


def _written_station_word(row: Row) -> str:
    """The word a close row's Command holds where the station goes, as written, or "" when it
    holds none there or cannot be read."""
    position = _station_position(row.move)
    if position is None:
        return ""
    try:
        written = shlex.split(reporters._plain_cell(row.command))
    except ValueError:
        return ""
    return written[position] if len(written) == position + 1 else ""


def written_station(row: Row) -> str:
    """The station stem a close row's Command names after the project — a `.md` suffix dropped —
    or "" when it names none, or a word that is not a dated stem."""
    return journey_names.station_stem(_written_station_word(row)) or ""


def parse_queue(text: str) -> list[Row]:
    """The rows of the report's `## Next moves` table, in the order written. A section that holds
    no table — the `None — <why>` form — is an empty queue. A report with no such section, a
    table missing a column this engine reads, or a cell that is not what its column holds is
    refused, because the queue is run as written and a guess would be a wrong run."""
    if not re.search(r"^## Next moves\s*$", text, re.MULTILINE):
        raise QueueRefused("the report has no '## Next moves' section")
    section = reporters._self_answer_section(text, "## Next moves")
    header = reporters._table_header(section)
    if not header:
        return []
    missing = [name.capitalize() if name != "#" else name for name in _COLUMNS
               if name not in header]
    if missing:
        raise QueueRefused(
            f"the '## Next moves' table has no {', '.join(missing)} column — the queue reads the "
            f"six-column header {_SIX_COLUMN_HEADER}, so a report written before the After "
            f"column cannot be run")
    position = {name: header.index(name) for name in _COLUMNS}
    source_at = header.index("from") if "from" in header else None
    rows = []
    for cells in reporters._table_rows(section):
        def cell(name: str, cells=cells) -> str:
            index = position[name]
            return cells[index].strip() if index < len(cells) else ""

        number = _row_number(cell("#"))
        rows.append(Row(
            number=number,
            move=reporters._plain_cell(cell("move")),
            whose=reporters._plain_cell(cell("whose")),
            command=cell("command"),
            after=_after(number, cell("after")),
            source=(cells[source_at].strip() if source_at is not None and source_at < len(cells)
                    else "")))
    return rows


def _row_number(cell: str) -> int:
    if not re.fullmatch(r"\d+", cell):
        raise QueueRefused(f"a row's # cell is {cell!r}, not a row number")
    return int(cell)


def _after(number: int, cell: str) -> tuple[int, ...]:
    """`—` waits on nothing; otherwise comma-separated row numbers. Anything else is refused,
    because a wait this engine cannot read is one it would either drop or invent."""
    if cell == _NO_WAIT:
        return ()
    if not _AFTER_LIST.fullmatch(cell):
        raise QueueRefused(f"row {number}: After is {cell!r}, which is neither {_NO_WAIT!r} nor "
                           f"row numbers separated by commas")
    return tuple(dict.fromkeys(int(part) for part in cell.split(",")))


def _numbers(numbers) -> str:
    """Row numbers as a message reads them: `1, 2`, or `—` for none."""
    return ", ".join(str(number) for number in numbers) or _NO_WAIT


def validate(rows: list[Row], *, core_dir: str, instance_root: str, project: str,
             card: str | None) -> dict[int, str]:
    """Refuse a queue that could not run as written, before anything starts, and return the rows
    whose Command is not their kind's command, each with why. Every refusal names the row and
    why. A runnable row's Command is compared with what its kind runs and never executed; one that
    does not match refuses that row alone, which then never runs, so the rows that do not wait on
    it still can. An OWNER or SKIP row's Command is prose for a person, so it is not compared.
    `card` is the project card's text (`None` when there is no file): it is read only for a sweep
    row, whose chain it names, so a queue with no sweep row is never refused over it."""
    numbers = [row.number for row in rows]
    definition = None
    refused: dict[int, str] = {}
    for number in numbers:
        if numbers.count(number) > 1:
            raise QueueRefused(f"row {number} appears more than once")
    for row in rows:
        if row.move == _REFINE:
            raise QueueRefused("refine a seed is an internal continuation, not a report move")
        if row.move not in KINDS:
            raise QueueRefused(f"row {row.number}: {row.move!r} is not a kind this queue runs "
                               f"— the kinds are {', '.join(KINDS)}")
        for waited_on in row.after:
            if waited_on not in numbers:
                raise QueueRefused(f"row {row.number}: After names row {waited_on}, which the "
                                   f"table does not have")
            if waited_on >= row.number:
                raise QueueRefused(f"row {row.number}: After names row {waited_on}, which is not "
                                   f"an earlier row — a row can only wait on one before it")
        if KINDS[row.move].disposition in _RUNNABLE:
            if row.move == _SWEEP and definition is None:
                definition = sweep_definition(card, instance_root=instance_root, project=project,
                                              number=row.number)
            reason = _check_command(row, core_dir, instance_root, project, definition)
            if reason:
                refused[row.number] = reason
    return refused


def _check_command(row: Row, core_dir: str, instance_root: str, project: str,
                   definition: Definition | None) -> str:
    """Why the row's Command is not what its kind runs, or "" when it is. A close may name its
    station's dated stem after the project — with `.md` or without, which is repaired rather than
    refused — and a report written before it did still runs."""
    word, station = _written_station_word(row), written_station(row)
    expected = expected_argv(row.move, core_dir=core_dir, project=project, definition=definition,
                             station=station)
    if word and not station:
        return (f"its Command {row.command!r} names {word!r} where the station's dated stem goes "
                f"— {shlex.join(expected)} {_STEM_FORM}")
    try:
        written = shlex.split(reporters._plain_cell(row.command))
    except ValueError as exc:
        return f"its Command {row.command!r} cannot be read as a command ({exc})"
    if station:
        written[_station_position(row.move)] = station
    matches = (bool(written)
               and pin.same_launcher(written[0], expected[0], core_dir=core_dir,
                                      instance_root=instance_root)
               and written[1:] == expected[1:])
    if not matches:
        return (f"its Command {row.command!r} is not what {row.move!r} runs — "
                f"{shlex.join(expected)}")
    return ""


# --- the queue's own record ---------------------------------------------------------------------


class RowStatus(str, Enum):
    """Where one row is. Written to the state file by its value."""

    WAITING = "waiting"
    LAUNCHED = "launched"
    LANDED = "landed"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"
    END = "end"
    HANDED_OFF = "handed-off"


class QueueEnd(str, Enum):
    """The persisted end of a queue; old retirement ends remain readable on resume."""

    STOPPED = "stopped"
    HALTED = "halted"
    WAITING_ON_A_WALK = "waiting-on-a-walk"
    OWNER_OWED = "owner-owed"
    RETIRE_LAUNCHED = "retire-launched"
    HANDED_OFF = "handed-off"
    DONE = "done"


# A row that will never land, so a row waiting on it never can either.
_DEAD = frozenset({RowStatus.FAILED, RowStatus.BLOCKED, RowStatus.SKIPPED, RowStatus.END,
                   RowStatus.HANDED_OFF})
# A row that resume leaves as the record has it: it either ran to its end, or was never a run.
_KEPT_ON_RESUME = frozenset({RowStatus.LANDED, RowStatus.HANDED_OFF, RowStatus.SKIPPED,
                             RowStatus.END})
# The `chain.py` ends a sweep can finish on and be landed: a settled one, and one whose only
# open items are the owner's. Every other end is a failure (`chain.py` `CycleEnd`).
_CHAIN_LANDED = frozenset({"settled", "left_for_the_owner"})

QUEUE_SCHEMA = 1
# The queue's own name: the telemetry tag its skill runs carry, and what its messages are headed by.
QUEUE_NAME = "build-idea"
# How often a watch on a walk reads it, in seconds. A walk's steps run for minutes, so thirty
# seconds adds little delay and costs nothing measurable.
WALK_POLL_SECONDS = 30
_STOPPED_BY_THE_OWNER = "stopped by the owner"


@dataclass
class QueueState:
    """Everything a later `--advance` needs, because the completion shim re-enters as a fresh
    process with one row number and one outcome and nothing else. Every field is defaulted and an
    unknown key is ignored, so a file written by another version of this engine loads."""

    project: str = ""
    instance_root: str = ""
    core_dir: str = ""
    shim_dir: str = ""
    engine_path: str = ""
    notifier: str = ""
    keep_awake: bool = False
    # The developer's context cap every `chain-change` row is launched with. Recorded at a fresh
    # start and kept by a resume, so a queue carries one cap for its whole life.
    context_cap: int = DEFAULT_CONTEXT_CAP
    # The provider `--provider` forced every row and nested chain of this queue onto, or empty
    # when each runs on its own. Stated by every start, a resume included: the start a
    # `chain-change` walk's end makes carries the force in its environment and so restates it.
    forced_provider: str = ""
    # The product the project builds, read by the launcher off its card. A pick waits for the
    # product chain while one of its documents has a live companion; "" checks nothing.
    product_path: str = ""
    queue_id: str = ""
    key: str = ""
    report: str = ""
    # The report's content when this queue was built from it. A refine re-read writes its report
    # again at the same path, so the path alone cannot tell a rewrite from the report this queue
    # already ran; "" on a record written before the digest was kept, which resumes as it did.
    report_digest: str = ""
    seed: str = ""         # the exact active seed path captured before retirement
    station: str = ""      # the open station's file name at the first start, or ""
    rows: list = field(default_factory=list)
    pending: dict = field(default_factory=dict)
    ended: str | None = None
    ended_reason: str = ""
    started_at: str = ""
    reentries: int = 0
    # The owner's stop. It lives on this one state file, so the lock that already serialises the
    # advances serialises it too, and it survives a new report: only a plain start clears it.
    stop_requested: bool = False
    stop_requested_at: str = ""
    # A skill row's launch the provider file could not give a provider for (CP-283). From then on
    # the queue launches nothing, and ends halted once no run is in flight; the next start, which
    # checks the file again, clears it.
    provider_refused: bool = False
    # A row whose run left new entries in the product checkout, or left it unreadable. Held the
    # way `provider_refused` is: the queue launches nothing and ends halted once no run is in
    # flight, and the next start clears it.
    checkout_dirty: bool = False
    # The state file of the definition chain's walk this queue waits on (CP-523, CP-524): a pick
    # found the project's walk still walking, or a sweep row's chain refused to start because it
    # was. Held the way `checkout_dirty` is — the queue launches nothing and ends
    # waiting-on-a-walk once no run is in flight. An ended walk releases the hold when the queue
    # next settles (CP-541), and a watcher wakes a queue that ended on it (CP-542); a start clears
    # it too. "" when the queue waits on no walk.
    waiting_on_walk: str = ""
    # Whether the watcher started when the queue ended waiting-on-a-walk is running (CP-544). It
    # decides which form of the end is told to the owner. Cleared with the hold.
    walk_watched: bool = False
    schema_version: int = QUEUE_SCHEMA

    def to_json(self) -> dict:
        return asdict(self)

    @classmethod
    def from_json(cls, data: dict) -> "QueueState":
        names = {entry.name for entry in fields(cls)}
        return cls(**{name: value for name, value in data.items() if name in names})


class QueueStore:
    """The state file behind a seam. A `.tmp` sibling is written whole and then replaced over the
    real path, so no reader ever observes half a file."""

    def __init__(self, files: Files, path: str):
        self.files = files
        self.path = os.path.abspath(path)

    def raw(self) -> dict:
        text = self.files.read_text(self.path)
        if text is None:
            return {}
        try:
            return json.loads(text)
        except ValueError:
            return {}

    def load(self) -> QueueState:
        data = self.raw()
        if not data:
            raise QueueRefused(f"no build-idea queue state at {self.path}")
        if data.get("schema_version") != QUEUE_SCHEMA:
            raise QueueRefused(f"{self.path} was written at state schema "
                               f"{data.get('schema_version')!r}; this engine speaks "
                               f"{QUEUE_SCHEMA}. Start the queue again through its launcher.")
        return QueueState.from_json(data)

    def save(self, state: QueueState) -> None:
        self.files.make_dirs(os.path.dirname(self.path))
        temporary = f"{self.path}.tmp"
        self.files.write_text(temporary,
                              json.dumps(state.to_json(), indent=2, sort_keys=True) + "\n")
        self.files.replace(temporary, self.path)


@dataclass(frozen=True)
class PlannedRow:
    """One row as a start would run it. `argv` is `None` for a row that runs nothing, a refused
    one included; `refused` is why its Command is not its kind's command, "" when it is."""

    number: int
    move: str
    disposition: Disposition
    after: tuple[int, ...]
    argv: list[str] | None
    command: str
    refused: str = ""


@dataclass(frozen=True)
class Plan:
    """What a start would do: the unit, the report it reads and its rows."""

    key: str
    report: str
    rows: tuple[PlannedRow, ...]
    seed: str = ""
    digest: str = ""


# What each landed fact says when it does not hold, for the failed row's reason.
_NOT_LANDED = {
    Landed.STATION_CLOSED: "the station has not moved from the shukuba root to trail/",
    Landed.SEED_PICKED: "no seed sits at the seedbed root",
    Landed.ROUTE_CUT: "the seed at the seedbed root has no station checklist",
    Landed.SEED_RETIRED: "the recorded seed has not moved from the root to trail/",
    Landed.SEED_REFINED: "no fresh nemawashi-refine report was written",
    Landed.DOCS_CUT: "no candidate sits in unpicked/ for the pick to take",
    Landed.README_STATUS_REPORTED: "readme-status neither made its commit nor found nothing to "
                                   "change",
}

# What a finished `readme-status` run's final message reports a result with: the two sentences
# `skills/content-editor/.claude/skills/readme-status/prompts/thin.md` publishes. The commit
# sentence must open the message, with both quoted fields nonempty and its terminating period. The
# nothing-to-change sentence may open it, or stand as a whole line anywhere in it once the line's
# blockquote markers, surrounding `*` emphasis and outer whitespace are stripped; case, inner
# spacing and the period stay verbatim. A run that wrote a preamble or set the sentence in bold still reported it.
_README_STATUS_COMMIT = re.compile(r"readme-status made commit `[^`]+` in `[^`]+`\.")
_README_STATUS_NOTHING = "readme-status found nothing to change and made no commit."
_WHAT_LEFT_FILE = os.path.join("docs", "what_left.md")


def _bare_line(line: str) -> str:
    """One message line without its blockquote markers, surrounding `*` emphasis or outer
    whitespace — the markdown a run may wrap a sentence in."""
    text = line.strip()
    while text.startswith(">"):
        text = text[1:].lstrip()
    return text.strip("*").strip()


# --- the queue ------------------------------------------------------------------------------------



def _digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _same_report(existing: dict, plan: Plan) -> bool:
    """Whether a start resumes the recorded queue: the same report, and — when the record kept
    one — the same content. A record with no digest predates it and resumes as it always did."""
    return (existing.get("report") == plan.report
            and existing.get("report_digest", plan.digest) in ("", plan.digest))

class WalkWatcher:
    """What the queue leaves a watch on a walk through. `start` runs `argv` detached from this
    process, its output appended to `log_path`, and says whether it could; `sleep` waits between
    two readings of the walk."""

    def start(self, argv: list[str], log_path: str) -> bool:
        # Detached the way the completion shim backgrounds an advance: its own session, stdin
        # from /dev/null, stdout and stderr appended to the queue's log.
        try:
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            with open(log_path, "ab") as output:
                subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=output,
                                 stderr=subprocess.STDOUT, start_new_session=True)
        except OSError:
            return False
        return True

    def sleep(self, seconds: float) -> None:
        time.sleep(seconds)


class BuildIdea:
    """The queue. Everything it uses is handed to it; it constructs nothing.

    `store` is the state file, `reader` the `DiskReader` that finds the sealed unit and its report,
    `journey` the seedbed (`root_seeds(nemawashi_dir)`, `checklist_items(seed_path)`), `files`
    the disk, `processes` what launchers are started through, `notifier` the owner's channel,
    `lock` the exclusive hold every advance and the stop share, `log` the queue's log, `id_source`
    what mints a queue's id, `environ` the environment a launch inherits and `engine_path` what
    each row's shim will run — pinned at start, so an edit to the engine cannot change a queue
    already in flight, `process_table` the port a stop reaches processes through and `checkout`
    the port that reads the product checkout, `watcher` the port that leaves a watch on a walk
    behind and waits between its readings."""

    def __init__(self, *, store: QueueStore, reader: DiskReader, journey: Journey, files: Files,
                 processes: Processes, notifier: Notifier, lock: FileLock, log: WalkLog,
                 id_source: IdSource, environ: dict, engine_path: str, providers: ProviderFiles,
                 process_table: walk_stop.ProcessTable, checkout: product_checkout.Checkout,
                 watcher: WalkWatcher):
        self.store = store
        self.watcher = watcher
        self.checkout = checkout
        self.process_table = process_table
        self.providers = providers
        self.reader = reader
        self.journey = journey
        self.files = files
        self.processes = processes
        self.notifier = notifier
        self.lock = lock
        self.log = log
        self.id_source = id_source
        self.environ = dict(environ)
        self.engine_path = engine_path

    # -- entry -----------------------------------------------------------------------------------

    def describe(self, instance_root: str, project: str, key: str = "",
                 core_dir: str = "", shim_dir: str = "", *, forced_provider: str = "") -> Plan:
        """What a start would do, decided by the same checks `start` makes and touching nothing:
        no lock, no write, no launch, no message. A dry run built on anything else could report a
        queue the real start refuses — so the live `chain-change` walk, the fully consumed
        report and the provider file are refused here, where both the dry run and the start meet
        them. The provider file is read last, once the plan holds, and never when
        `forced_provider` is given: a forced queue does not read it. `shim_dir` is where the
        launcher keeps the queue's logs, `<instance_root>/system/logs` when omitted."""
        plan = self._plan(instance_root, project, key, core_dir, shim_dir)
        if not forced_provider:
            self._refuse_a_provider_file_missing_a_row(instance_root)
        return plan

    def _plan(self, instance_root: str, project: str, key: str, core_dir: str,
              shim_dir: str) -> Plan:
        """`describe` before its provider check: one body with four ways out, so the check lives
        in the one place that follows all of them."""
        self._refuse_a_live_queue()
        self._refuse_a_live_chain_change(
            shim_dir or os.path.join(instance_root, "system", "logs"), project)
        key = key or self.reader.sealed_key(instance_root, project)
        if not key:
            context = os.path.join(instance_root, "system", "projects", project, "contexts",
                                   "CONTEXT_PM.md")
            raise QueueRefused(f"no sealed unit to run for {project}: {context} names none. "
                               f"Name a unit by its key, or seal one first.")
        existing = self.store.raw()
        change = ChangeLayout(instance_root, project, key)
        # Only a retire that has started moves the report out from under its path; before that,
        # the report is read and its digest decides, like any other.
        # A retire the owner's stop caught in flight counts: its run may have moved the report
        # before the stop reached it, and the stop leaves the row `failed`.
        retiring = any(entry["move"] == _RETIRE
                       and (entry["status"] in (RowStatus.LAUNCHED, RowStatus.LANDED,
                                                RowStatus.HANDED_OFF)
                            or entry.get("reason", "").startswith(_STOPPED_BY_THE_OWNER))
                       for entry in existing.get("rows", []))
        seed = existing.get("seed", "") if existing.get("key") == key and retiring else ""
        old_retirement = existing.get("key") == key and any(
            entry["move"] == _RETIRE and entry["status"] == RowStatus.HANDED_OFF
            for entry in existing.get("rows", []))
        if old_retirement and not seed:
            report = self.reader.report_path(change)
            folder = os.path.dirname(report or "")
            if os.path.dirname(folder) != os.path.join(change.nemawashi, "trail"):
                raise QueueRefused("the previous retirement has not landed in trail/ yet")
            seed = os.path.join(change.nemawashi, os.path.basename(folder))
        if seed:
            state = self.store.load()
            state.seed = seed
            core = core_dir or self._default_core()
            if self._refine_rewritten(state):
                return self._retired_plan(
                    key, os.path.join(change.nemawashi, "trail", os.path.basename(seed)), core,
                    instance_root, project, shim_dir)
            plan = Plan(key=key, report=state.report, rows=tuple(
                PlannedRow(entry["number"], entry["move"], KINDS[entry["move"]].disposition,
                           tuple(entry["after"]),
                           None if entry.get("refused") else self._argv(
                               entry["move"], core, instance_root, project, state.seed,
                               entry["number"],
                               station=self._station(entry["move"], entry["command"],
                                                     instance_root, project, state.station)),
                           entry["command"], entry.get("refused", ""))
                for entry in state.rows), seed=state.seed, digest=state.report_digest)
            self._resumed(plan, core, shim_dir, "", False, by_owner=True)
            return plan
        report = self.reader.report_path(change)
        if report is None:
            raise UnitReportMissing(
                f"no {key}_report.md in any seed folder under {change.nemawashi} "
                f"— run shukuba-refine on {key} first", change)
        core = core_dir or self._default_core()
        folder = os.path.dirname(report)
        if os.path.dirname(folder) == os.path.join(change.nemawashi, "trail"):
            return self._retired_plan(key, folder, core, instance_root, project, shim_dir)
        text = self.files.read_text(report) or ""
        rows = parse_queue(text)
        refused = validate(rows, core_dir=core, instance_root=instance_root, project=project,
                           card=self._card_text(instance_root, project))
        seed = ""
        if any(row.move == _RETIRE for row in rows):
            seeds = self.journey.root_seeds(change.nemawashi)
            if len(seeds) != 1:
                raise QueueRefused("retirement needs exactly one active seed at the seedbed root")
            seed = seeds[0]
        return self._planned(key, report, text, rows, refused, seed, core, instance_root, project,
                             shim_dir)

    def _refine_rewritten(self, state: QueueState) -> bool:
        """Whether the refine report this queue already carried has been written again since."""
        carried = [entry for entry in state.rows
                   if entry["move"] == _REFINE and entry.get("continued")]
        if not carried or not carried[-1].get("report_digest"):
            return False
        text = self.files.read_text(self._refine_report(state))
        return text is not None and _digest(text) != carried[-1]["report_digest"]

    def _retired_plan(self, key: str, seed_folder: str, core: str, instance_root: str,
                      project: str, shim_dir: str) -> Plan:
        """The unit's seed has retired to trail/, so the moves its report named are behind it and
        what is owed is the retired seed's own nemawashi-refine report — run by hand, or by a
        queue this record no longer holds."""
        seed = os.path.basename(seed_folder)
        report = self._refine_report_path(instance_root, project, seed)
        text = self.files.read_text(report)
        if text is None:
            raise QueueRefused(
                f"{key}'s seed {seed} has retired to trail/ and {report} is not there — run "
                f"{shlex.join(self._argv(_REFINE, core, instance_root, project, seed))} first")
        rows, refused = self._nemawashi_rows(text, core_dir=core, instance_root=instance_root,
                                             project=project)
        return self._planned(key, report, text, rows, refused, seed_folder, core, instance_root,
                             project, shim_dir)

    def _planned(self, key: str, report: str, text: str, rows: list[Row],
                 refused: dict[int, str], seed: str, core: str, instance_root: str, project: str,
                 shim_dir: str) -> Plan:
        plan = Plan(key=key, report=report, seed=seed, digest=_digest(text), rows=tuple(
            PlannedRow(
                number=row.number, move=row.move, disposition=KINDS[row.move].disposition,
                after=row.after, command=row.command, refused=refused.get(row.number, ""),
                argv=None if row.number in refused else self._argv(
                    row.move, core, instance_root, project, number=row.number,
                    station=self._station(row.move, row.command, instance_root, project)))
            for row in rows))
        if _same_report(self.store.raw(), plan):
            # The resume, worked out on a copy of the record and never saved: it refuses a report
            # with nothing left to run.
            self._resumed(plan, core, shim_dir, "", False, by_owner=True)
        return plan

    def start(self, *, instance_root: str, project: str, core_dir: str, shim_dir: str,
              key: str = "", notifier_command: str = "", keep_awake: bool = False,
              started_at: str = "", by_hook: bool = False,
              context_cap: int = DEFAULT_CONTEXT_CAP, product_path: str = "",
              forced_provider: str = "") -> AdvanceResult:
        """Begin a queue on the sealed unit's report, every row that waits on nothing launched and
        the rest left to `advance`. A report the state file already records, unchanged since, is
        RESUMED instead: the record says what landed, the disk says what landed since, and only
        what is still owed runs. A report rewritten at the same path is a new queue. A unit whose
        seed has retired to trail/ runs that seed's nemawashi-refine report. A start the `chain-change` walk's own end makes (`by_hook`) does nothing while the
        owner's stop stands, and says so. Such a start on a unit with no refine report that
        serves no station has nothing to run either: it touches nothing and returns
        `NoStationStart`, whose message says why."""
        with self.lock.hold(self.store.path):
            existing = self.store.raw()
            if by_hook and existing.get("stop_requested"):
                self.notifier.send(
                    f"{project}: build-idea is stopped — chain-change's end did not restart it; "
                    f"run {self._resume_command(core_dir, project)} to resume")
                return AdvanceResult(acted=False, ended=existing.get("ended"))
            if existing.get("stop_requested"):
                # A plain start means "no longer stopped", even when a live walk means it cannot
                # start now: that walk's end will reach this queue through the hook, and must not
                # find the stop still standing.
                cleared = self.store.load()
                cleared.stop_requested, cleared.stop_requested_at = False, ""
                self.store.save(cleared)
            try:
                plan = self.describe(instance_root, project, key, core_dir, shim_dir,
                                     forced_provider=forced_provider)
            except UnitReportMissing as missing:
                if not by_hook or self.reader.serves_station(missing.layout):
                    raise
                return NoStationStart(acted=False, ended=None, key=missing.layout.key)
            if existing and _same_report(existing, plan):
                state = self._resumed(plan, core_dir, shim_dir, notifier_command, keep_awake,
                                      by_owner=not by_hook)
            else:
                state = self._fresh(plan, instance_root, project, core_dir, shim_dir,
                                    notifier_command, keep_awake, started_at, context_cap)
            # Every start says where the product is, and one that names none means none: a card
            # that dropped its path must not leave the queue checking a stale one.
            state.product_path = product_path
            state.forced_provider = forced_provider
            self.store.save(state)
            self.log.append(self._log_path(state),
                            f"build_idea: started queue={state.queue_id} key={state.key} "
                            f"rows={len(state.rows)} at={started_at}")
            self.notifier.send(self._start_message(state))
            self._settle(state)
            self.store.save(state)
            return AdvanceResult(acted=True, ended=state.ended)

    def _fresh(self, plan: Plan, instance_root: str, project: str, core_dir: str, shim_dir: str,
               notifier_command: str, keep_awake: bool, started_at: str,
               context_cap: int) -> QueueState:
        """A new record, replacing whatever the state file held."""
        return QueueState(
            seed=plan.seed, project=project, instance_root=instance_root, core_dir=core_dir,
            shim_dir=shim_dir, engine_path=self.engine_path, notifier=notifier_command,
            keep_awake=keep_awake, context_cap=context_cap,
            queue_id=self.id_source.new_id(), key=plan.key,
            report=plan.report, report_digest=plan.digest,
            station=self._the_one_open_station(instance_root, project),
            rows=[self._entry(planned) for planned in plan.rows], started_at=started_at)

    def _resumed(self, plan: Plan, core_dir: str, shim_dir: str, notifier_command: str,
                 keep_awake: bool, *, by_owner: bool) -> QueueState:
        """The recorded queue, picked up. A row recorded landed, handed off, skipped or end keeps
        that. A skill row that is not recorded landed is landed all the same if its fact holds on
        the disk now, checked against the station recorded at the first start. Every other row
        that runs something goes back to waiting — a sweep has no fact on the disk to check, so
        what the record says is all there is. The record is never trusted downward: the disk can
        raise a row to landed and nothing lowers one.

        The one row no disk fact can land is the owner's act, and the owner's own start says it is
        made (`by_owner`): each such row whose After rows have all landed lands. A start the
        `chain-change` walk's end makes is not the owner and lands none."""
        state = self.store.load()
        state.seed = plan.seed or state.seed
        state.report_digest = state.report_digest or plan.digest
        state.core_dir, state.shim_dir = core_dir, shim_dir
        state.notifier, state.keep_awake = notifier_command, keep_awake
        state.pending, state.ended, state.ended_reason = {}, None, ""
        # This start has just checked the provider file again (`start`), so an earlier refusal no
        # longer stands; the row it failed goes back to waiting with every other failed row.
        state.provider_refused = False
        state.checkout_dirty = False
        state.waiting_on_walk, state.walk_watched = "", False
        argv = {planned.number: planned.argv or [] for planned in plan.rows}
        # The report is the same report, but the check that refused a cell may not be: this
        # start's plan checked every Command against the core it runs on, so its verdict is the
        # one that stands. A row that is no longer refused goes back to waiting below.
        refused = {planned.number: planned.refused for planned in plan.rows}
        for entry in state.rows:
            entry["argv"] = argv.get(entry["number"], entry["argv"])
            entry.pop("refused", None)
            if refused.get(entry["number"]):
                entry["refused"] = refused[entry["number"]]
                entry["status"], entry["reason"] = RowStatus.FAILED.value, entry["refused"]
                continue
            if entry["move"] == _RETIRE and entry["status"] == RowStatus.HANDED_OFF:
                if not self._landed(state, Landed.SEED_RETIRED, entry):
                    raise QueueRefused("the previous retirement has not landed in trail/ yet")
                entry["status"] = RowStatus.LANDED.value
            if RowStatus(entry["status"]) in _KEPT_ON_RESUME:
                continue
            kind = KINDS[entry["move"]]
            landed = (kind.disposition is Disposition.RUN_SKILL
                      and self._landed(state, kind.landed, entry))
            entry["status"] = (RowStatus.LANDED if landed else RowStatus.WAITING).value
            entry["reason"] = ""
        # After the loop above, not inside it: whether an owner's act's After rows have landed is
        # that loop's result.
        if by_owner:
            self._land_the_owners_acts(state)
        if not any(entry["status"] == RowStatus.WAITING or self._needs_continuation(entry)
                   for entry in state.rows):
            refused = [entry for entry in state.rows if entry.get("refused")]
            if refused:
                raise QueueRefused(
                    f"{state.report} has nothing left it can run — "
                    + "; ".join(f"row {entry['number']} is refused: {entry['refused']}"
                                for entry in refused))
            raise QueueRefused(f"{state.report} is fully consumed — every row it runs has landed "
                               f"or was handed off")
        return state

    def _refuse_a_provider_file_missing_a_row(self, instance_root: str) -> None:
        """An unforced queue checks every skill row's entry before anything is saved or launched,
        not only the rows this report holds: a row the queue adds later (a sweep, a refine) must
        not be the one that finds the file silent hours in (CP-281, CP-282)."""
        try:
            self.providers.at(instance_root).resolve(
                providers.build_idea_row(move) for move in _SKILL_ROWS)
        except ProvidersRefused as refused:
            raise QueueRefused(str(refused)) from None

    def _land_the_owners_acts(self, state: QueueState) -> None:
        """Land each owner's act recorded `end` whose After rows have all landed."""
        for entry in state.rows:
            if (KINDS[entry["move"]].disposition is Disposition.OWNER
                    and entry["status"] == RowStatus.END
                    and all(status is RowStatus.LANDED
                            for status in self._statuses(state, entry["after"]))):
                entry["status"] = RowStatus.LANDED.value

    def _refuse_a_live_chain_change(self, shim_dir: str, project: str) -> None:
        """A `chain-change` walk on the project is live while its state records no end and a run
        pending — the rule `DevelopmentChain` applies to its own state. Its end starts this queue
        through the hook, so a start beside it would only race the restart."""
        path = os.path.join(shim_dir, f"chain-change-{project}-state.json")
        walk = WalkStateStore(self.files, path).raw()
        if walk and walk.get("ended") is None and walk.get("pending"):
            raise QueueRefused(
                f"a chain-change walk is live on {project}: {path} still has a run pending. Let "
                f"it finish — its end starts this queue again — or start this once it has ended.")

    def advance(self, row: int, outcome: str) -> AdvanceResult:
        """What a row's shim calls when its run ends. Does nothing when the queue has ended
        (counted) or when `row` is not pending (a repeated or stale delivery). Otherwise the row
        leaves `pending` and is saved BEFORE anything is decided, so a second delivery of the same
        end is itself a no-op."""
        with self.lock.hold(self.store.path):
            state = self.store.load()
            if state.ended is not None:
                state.reentries += 1
                self.store.save(state)
                return AdvanceResult(acted=False, ended=state.ended)
            pending = state.pending.pop(str(row), None)
            if pending is None:
                return AdvanceResult(acted=False, ended=None)
            entry = self._row(state, row)
            if KINDS[entry["move"]].landed is Landed.README_STATUS_REPORTED:
                # The ending is saved before the landing fact is read: a resume inspects the same
                # attempt's ending, and an absent one never means the run finished.
                entry["ending"] = outcome
            self.store.save(state)
            reason = self._left_the_checkout_dirty(state, pending)
            if reason is None:
                self._record(state, entry, outcome)
            else:
                entry["status"], entry["reason"] = RowStatus.FAILED.value, reason
                state.checkout_dirty = True
            self._settle(state)
            self.store.save(state)
            return AdvanceResult(acted=True, ended=state.ended)

    def wake(self, queue_id: str) -> AdvanceResult:
        """What the watch calls once the walk it watches is no longer live. Acts only on the same
        queue, still ended waiting-on-a-walk, not stopped and with that walk no longer live; the
        guards are read under the lock, so a second wake of the same end does nothing (CP-542).
        A walk that ended `stopped` does not continue the queue: the owner is told and the queue
        stays as it is (CP-543). Otherwise the hold is released, the owner is told the queue is
        continuing, and the queue settles as an advance would."""
        with self.lock.hold(self.store.path):
            existing = self.store.raw()
            if not self._is_waiting_on_a_walk(existing, queue_id):
                return AdvanceResult(acted=False, ended=existing.get("ended"))
            state = self.store.load()
            walk = ChainStateStore(self.files, state.waiting_on_walk).raw()
            if walk_is_live(walk):
                return AdvanceResult(acted=False, ended=state.ended)
            resume = self._resume_command(state.core_dir or self._default_core(), state.project)
            if walk.get("ended") == walk_stop.STOPPED:
                self.notifier.send(f"{self._headline(state)} — still waiting on a walk — "
                                   f"{state.waiting_on_walk} was stopped, so the queue does not "
                                   f"continue by itself. Resume with: {resume}")
                return AdvanceResult(acted=False, ended=state.ended)
            self.notifier.send(f"{self._headline(state)} — continuing — {state.waiting_on_walk} "
                               f"is no longer walking, so the queue carries on from the rows "
                               f"that waited for it")
            state.ended, state.ended_reason = None, ""
            state.waiting_on_walk, state.walk_watched = "", False
            self._settle(state)
            self.store.save(state)
            return AdvanceResult(acted=True, ended=state.ended)

    def wait_on_walk(self, queue_id: str, poll_seconds: float = WALK_POLL_SECONDS) -> AdvanceResult:
        """The watch itself: read the queue's state each poll, without the lock. It ends when the
        queue is no longer the same waiting queue (resumed, stopped, replaced) or when the walk
        is no longer live, and then `wake` decides under the lock whether to act."""
        while True:
            state = self.store.raw()
            if not self._is_waiting_on_a_walk(state, queue_id):
                return AdvanceResult(acted=False, ended=state.get("ended"))
            if not walk_is_live(ChainStateStore(self.files, state["waiting_on_walk"]).raw()):
                return self.wake(queue_id)
            self.watcher.sleep(poll_seconds)

    @staticmethod
    def _is_waiting_on_a_walk(raw: dict, queue_id: str) -> bool:
        """Whether a state file's raw dict is `queue_id`, ended waiting-on-a-walk, not stopped."""
        return (raw.get("queue_id") == queue_id
                and raw.get("ended") == QueueEnd.WAITING_ON_A_WALK.value
                and not raw.get("stop_requested"))

    def stop(self, instance_root: str, project: str, requested_at: str) -> str:
        """The owner's stop: every row in flight is stopped, nothing new starts, the queue ends
        `stopped` at once, and the queue's own restart is suppressed until a plain start clears
        it. A skill row's run and watcher are stopped through `walk_stop`; a chain row through
        that chain's own `--stop`. Recorded on the state file, created when there is none, so a
        stop asked for between two queues still holds. One message goes to the owner and the same
        line is returned."""
        with self.lock.hold(self.store.path):
            existing = self.store.raw()
            state = (self.store.load() if existing
                     else QueueState(project=project, instance_root=instance_root))
            state.stop_requested, state.stop_requested_at = True, requested_at
            live = existing and state.ended is None and state.rows
            resume = self._resume_command(state.core_dir or self._default_core(), project)
            headline = self._headline(state)
            if not live:
                said = (f"{headline} — stop recorded; no queue is live — the loop will not "
                        f"restart itself. Resume with: {resume}")
            else:
                stopped = self._stop_rows_in_flight(state)
                said = (f"{headline} — stopped; {'; '.join(stopped)}. Resume with: {resume}"
                        if stopped else
                        f"{headline} — stopped; no run was in flight. Resume with: {resume}")
                said = "\n".join([said, *self._finish(state).splitlines()[1:]])
            self.store.save(state)
            self.notifier.send(said)
            return said

    def _stop_rows_in_flight(self, state: QueueState) -> list[str]:
        """Stop what every pending row launched, mark each row `failed` naming the stop, and empty
        `pending`. Returns one line per row saying what became of it."""
        said = []
        for number in sorted(state.pending, key=int):
            entry = self._row(state, int(number))
            if KINDS[entry["move"]].disposition is Disposition.RUN_SKILL:
                what = walk_stop.stop_launch(
                    self.files, self.process_table, state.pending[number].get("identity", ""),
                    "launch").describe()
            else:
                what = self._stop_chain_row(state, entry)
            entry["status"] = RowStatus.FAILED.value
            entry["reason"] = f"{_STOPPED_BY_THE_OWNER} — {what}"
            said.append(f"{number}. {entry['move']}: {what}")
        state.pending.clear()
        return said

    def _stop_chain_row(self, state: QueueState, entry: dict) -> str:
        """A chain row's run is a walk with a state of its own, so its stop is that chain's own
        `--stop`, launched the way the row was, with no run's identity inherited."""
        exit_code = self.processes.run(
            [*entry["argv"], "--stop"], cwd=state.instance_root,
            env=walk_stop.without_launch_identity(self.environ))
        return f"its chain's --stop exited {exit_code}"

    def _default_core(self) -> str:
        return os.path.dirname(os.path.dirname(self.engine_path))

    @staticmethod
    def _resume_command(core_dir: str, project: str) -> str:
        return f"{os.path.join(core_dir, 'launchers', 'build-idea', 'launcher.sh')} {project}"

    def _card_text(self, instance_root: str, project: str) -> str | None:
        """The project card as the disk holds it now, `None` when there is none. Read fresh by
        every start and dry run that needs it, and never parsed here."""
        return self.files.read_text(card_path(instance_root, project))

    def _argv(self, move: str, core: str, instance_root: str, project: str, seed: str = "",
              number: int = 0, *, station: str = "") -> list[str] | None:
        """The command a row starts. A sweep row's is the chain its card names, read now; `number`
        is the row the card's refusal names. A close names `station`, when there is one."""
        if KINDS[move].disposition not in _RUNNABLE:
            return None
        definition = (sweep_definition(self._card_text(instance_root, project),
                                       instance_root=instance_root, project=project, number=number)
                      if move == _SWEEP else None)
        argv = expected_argv(move, core_dir=core, project=project, definition=definition,
                             station=station)
        if move == _REFINE:
            argv.append(os.path.basename(seed).removesuffix(".md"))
        return argv

    def _station(self, move: str, command: str, instance_root: str, project: str,
                 recorded: str = "") -> str:
        """The stem a close is launched naming: the one its row's Command names, else the station
        recorded at the first start (`recorded`), else the one station at the shukuba root now.
        "" for every other kind, and when none of the three names one — the skill then resolves
        the station from the project alone."""
        if _STATION not in KINDS[move].arguments:
            return ""
        written = written_station(Row(0, move, "", command, (), ""))
        return (written or recorded
                or self._the_one_open_station(instance_root, project)).removesuffix(".md")

    @staticmethod
    def _launched_station(entry: dict) -> str:
        """The station stem a close row's recorded argv names, or ""."""
        position = _station_position(entry["move"])
        argv = entry.get("argv") or []
        return (journey_names.station_stem(argv[position]) or ""
                if position is not None and len(argv) > position else "")

    def _the_one_open_station(self, instance_root: str, project: str) -> str:
        """The open station's file name when the shukuba root holds exactly one, else "". Of two,
        the queue names neither: picking one would close a station nobody chose."""
        stations = self.reader.open_stations(instance_root, project)
        return stations[0] if len(stations) == 1 else ""

    @staticmethod
    def _refine_report(state: QueueState) -> str:
        return BuildIdea._refine_report_path(state.instance_root, state.project, state.seed)

    @staticmethod
    def _refine_report_path(instance_root: str, project: str, seed: str) -> str:
        seed = os.path.basename(seed).removesuffix(".md")
        return os.path.join(instance_root, "system", "projects", project,
                            "docs", "nemawashi-refine", f"{seed}_report.md")

    def _refuse_a_live_queue(self) -> None:
        existing = self.store.raw()
        if not existing or existing.get("ended") is not None or not existing.get("pending"):
            return
        pending = existing["pending"]
        states = [walk_stop.launch_state(self.files, self.process_table,
                                         pending[number].get("identity", ""))
                  for number in sorted(pending, key=int)]
        core_dir = existing.get("core_dir") or self._default_core()
        command = walk_stop.stop_command(core_dir, QUEUE_NAME, existing.get("project", ""))
        raise QueueRefused(
            f"{self.store.path} is still running {existing.get('key')}, waiting on rows "
            f"{', '.join(sorted(pending))}. {walk_stop.refusal_remedy(states, command)}")

    @staticmethod
    def _entry(planned: PlannedRow) -> dict:
        status = {Disposition.SKIP: RowStatus.SKIPPED,
                  Disposition.OWNER: RowStatus.END}.get(planned.disposition, RowStatus.WAITING)
        entry = {"number": planned.number, "move": planned.move, "command": planned.command,
                 "after": list(planned.after), "argv": planned.argv or [],
                 "status": status.value, "reason": ""}
        if planned.refused:
            entry.update(status=RowStatus.FAILED.value, reason=planned.refused,
                         refused=planned.refused)
        return entry

    @staticmethod
    def _row(state: QueueState, number: int) -> dict:
        return next(entry for entry in state.rows if entry["number"] == number)

    # -- reading what a run left ------------------------------------------------------------------

    def _left_the_checkout_dirty(self, state: QueueState, pending: dict) -> str | None:
        """The reason a row's end fails it: the product checkout holds entries it did not hold at
        the row's launch, or cannot be read now. `None` when nothing was recorded at launch — an
        empty `product_path`, an unreadable checkout, a hand-off, a state written before this
        check — and the checkout is not read for it."""
        before = pending.get(product_checkout.CHECKOUT_BEFORE)
        if before is None:
            return None
        return product_checkout.left_dirty(
            before, self.checkout.entries(state.product_path), state.product_path)

    def _record(self, state: QueueState, entry: dict, outcome: str) -> None:
        """Land or fail a row that ended. What counts is the kind's own fact: a chain landed on
        the end it reports, and a skill landed on the disk — a run that finished having changed
        nothing has not landed, whatever it says."""
        kind = KINDS[entry["move"]]
        if kind.disposition is Disposition.RUN_CHAIN:
            landed, why = outcome in _CHAIN_LANDED, f"the chain ended {outcome}"
        elif outcome not in _FINISHED:
            landed, why = False, f"the run ended {outcome}"
        else:
            landed = self._landed(state, kind.landed, entry)
            why = f"the run finished but {_NOT_LANDED.get(kind.landed, 'nothing landed')}"
        if landed and entry["move"] == _REFINE:
            try:
                self._refined_rows(state)
            except QueueRefused as exc:
                landed, why = False, str(exc)
        entry["status"] = (RowStatus.LANDED if landed else RowStatus.FAILED).value
        entry["reason"] = "" if landed else why

    def _landed(self, state: QueueState, fact: Landed, entry: dict) -> bool:
        change = ChangeLayout(state.instance_root, state.project, state.key)
        if fact is Landed.SEED_RETIRED:
            if not state.seed:
                return False
            trail = os.path.join(change.nemawashi, "trail", os.path.basename(state.seed))
            return (not self.files.is_file(state.seed) and not self.files.is_dir(state.seed)
                    and (self.files.is_file(trail)
                         or self.files.is_file(os.path.join(trail, "seed.md"))))
        if fact is Landed.SEED_REFINED:
            report = self.files.read_text(self._refine_report(state))
            return ("before" in entry and report is not None
                    and self.journey.report_revision(self._refine_report(state)) != entry["before"])
        if fact is Landed.DOCS_CUT:
            # The PM always picks unless it can't (owner, 2026-09-30): a cut that finished lands
            # whenever the pool holds a candidate, new or not. Only an empty pool holds the pick.
            return "before" in entry and bool(self._candidates(state))
        if fact is Landed.README_STATUS_REPORTED:
            return self._readme_status_reported(state, entry)
        if fact is Landed.STATION_CLOSED:
            # The station the close was launched naming, else the one open at the first start:
            # closed is that file moved from the root into trail/, which is what the skill does.
            # Gone from the root alone is not enough — a refused close moves nothing, and a
            # station it never named may be gone for another reason.
            stem = self._launched_station(entry) or state.station.removesuffix(".md")
            if stem:
                name = f"{stem}.md"
                return (self.files.is_file(os.path.join(change.shukuba, "trail", name))
                        and not self.files.is_file(os.path.join(change.shukuba, name)))
            return self.reader.open_station(state.instance_root, state.project) is None
        seeds = self.journey.root_seeds(change.nemawashi)
        if fact is Landed.SEED_PICKED:
            return bool(seeds)
        if fact is Landed.ROUTE_CUT:
            return bool(seeds) and self.journey.checklist_items(seeds[0]) > 0
        return True

    def _readme_status_reported(self, state: QueueState, entry: dict) -> bool:
        """A `readme-status` run that finished landed in exactly three cases: its final message
        (the receipt of this attempt) opens with the commit sentence, opens with the
        nothing-to-change sentence or holds it as a whole line, or the product has no what-left file when the run ends. A run
        with no recorded finished ending lands in none of them, whatever the product holds."""
        if entry.get("ending") not in _FINISHED:
            return False
        message = completion_shim.read_result(self.files, entry.get("receipt"))
        if message is not None and (_README_STATUS_COMMIT.match(message)
                                    or message.startswith(_README_STATUS_NOTHING)
                                    or _README_STATUS_NOTHING in map(_bare_line,
                                                                     message.splitlines())):
            return True
        product = self._product_directory(state)
        return product is not None and not self.files.is_file(
            os.path.join(product, _WHAT_LEFT_FILE))

    def _product_directory(self, state: QueueState) -> str | None:
        """The product the queue was started on; for a state that kept none, the one the project
        card names, a relative value against the instance. `None` when neither resolves: an
        unresolved product is no evidence that a file is absent."""
        if state.product_path:
            return os.path.join(state.instance_root, state.product_path)
        card = self._card_text(state.instance_root, state.project)
        if card is None:
            return None
        try:
            kind, value = development_path.parse_product_path(card, self.environ.get("HOME"))
        except development_path.ToolError:
            return None
        return value if kind == development_path.FIXED else os.path.join(
            state.instance_root, value)

    def _candidates(self, state: QueueState) -> dict[str, str]:
        pool = os.path.join(ChangeLayout(state.instance_root, state.project, state.key).nemawashi,
                            "unpicked")
        candidates = {}
        for name in self.files.list_dir(pool):
            if name == "README.md":
                continue
            path = os.path.join(pool, name)
            if self.files.is_dir(path):
                path = os.path.join(path, "seed.md")
            elif not name.endswith(".md"):
                continue
            text = self.files.read_text(path)
            if text is not None:
                candidates[path] = text
        return candidates

    def _refined_rows(self, state: QueueState) -> tuple[list[Row], dict[int, str]]:
        return self._nemawashi_rows(self.files.read_text(self._refine_report(state)) or "",
                                    core_dir=state.core_dir, instance_root=state.instance_root,
                                    project=state.project)

    def _nemawashi_rows(self, text: str, *, core_dir: str, instance_root: str,
                        project: str) -> tuple[list[Row], dict[int, str]]:
        rows = parse_queue(text)
        if not rows:
            section = reporters._self_answer_section(text, "## Next moves").strip()
            if " ".join(section.split()) != "Nothing is owed; the project's seedbed is exhausted.":
                raise QueueRefused(
                    "nemawashi-refine left no moves and no exhausted-seedbed verdict")
        for row in rows:
            if row.move not in _NEMAWASHI_KINDS:
                raise QueueRefused(f"row {row.number}: {row.move!r} is not a nemawashi next move")
        refused = validate(rows, core_dir=core_dir, instance_root=instance_root, project=project,
                           card=self._card_text(instance_root, project))
        return rows, refused

    @staticmethod
    def _needs_continuation(entry: dict) -> bool:
        return (entry["move"] in (_RETIRE, _REFINE)
                and entry["status"] == RowStatus.LANDED and not entry.get("continued"))

    def _continue_seed(self, state: QueueState) -> bool:
        if state.pending:
            return False
        for entry in state.rows:
            if not self._needs_continuation(entry):
                continue
            offset = max(row["number"] for row in state.rows)
            if entry["move"] == _RETIRE:
                argv = self._argv(_REFINE, state.core_dir, state.instance_root, state.project,
                                  state.seed)
                rows = [Row(1, _REFINE, "Principal PM", shlex.join(argv), (), "retirement")]
                refused = {}
            else:
                try:
                    rows, refused = self._refined_rows(state)
                except QueueRefused as exc:
                    entry["status"], entry["reason"] = RowStatus.FAILED.value, str(exc)
                    return True
                entry["report_digest"] = _digest(
                    self.files.read_text(self._refine_report(state)) or "")
            for row in rows:
                planned = PlannedRow(
                    row.number + offset, row.move, KINDS[row.move].disposition,
                    tuple(number + offset for number in row.after),
                    None if row.number in refused else self._argv(
                        row.move, state.core_dir, state.instance_root, state.project,
                        state.seed, row.number + offset),
                    row.command, refused.get(row.number, ""))
                added = self._entry(planned)
                added["from_refinement"] = True
                state.rows.append(added)
            entry["continued"] = True
            self.store.save(state)
            return True
        return False

    # -- settling: block, launch, end -------------------------------------------------------------

    def _settle(self, state: QueueState) -> None:
        """Recompute until nothing moves: block every waiting row whose After holds a row that
        will never land, launch the first waiting row whose After rows have all landed when no row
        is running (one row at a time, row order), and end when
        nothing is launched or waiting. A launch can fail at once, which blocks its dependents on
        the next turn, so this repeats rather than running once. Safe to run twice.

        While the owner's stop stands it blocks nothing and launches nothing: the outcome that
        brought us here is already recorded, and once nothing is in flight the queue ends
        stopped. A provider refusal and a row that dirtied the product checkout are held the same
        way, and end it halted; a walk it waits on holds it too, and ends it waiting-on-a-walk."""
        if state.stop_requested:
            if not state.pending:
                self.notifier.send(self._finish(state))
            return
        self._release_an_ended_walk(state)
        moved = not self._held(state)
        while moved:
            moved = self._continue_seed(state)
            moved = self._block(state) or moved
            moved = self._launch_ready(state) or moved
            moved = moved and not self._held(state)
        if self._held(state):
            if not state.pending:
                if self._ends_waiting_on_a_walk(state):
                    # The detached reader can run before start returns (CP-542). Publish its
                    # waiting state first; wake takes this same lock before it can change it.
                    self._finish(state)
                    state.walk_watched = self.watcher.start(self._watch_argv(state),
                                                            self._log_path(state))
                self.notifier.send(self._finish(state))
            return
        if not any(entry["status"] in (RowStatus.LAUNCHED, RowStatus.WAITING)
                   for entry in state.rows):
            self.notifier.send(self._finish(state))

    def _release_an_ended_walk(self, state: QueueState) -> None:
        """Stop waiting on a walk that is no longer live (CP-541), read the way the chain's own
        refusal reads it. One check at the top of every settle serves an advance, a start and a
        wake alike."""
        if state.waiting_on_walk and not walk_is_live(
                ChainStateStore(self.files, state.waiting_on_walk).raw()):
            state.waiting_on_walk = ""

    @staticmethod
    def _ends_waiting_on_a_walk(state: QueueState) -> bool:
        """Whether `_finish` will write waiting-on-a-walk: the hold is set and no row failed (a
        failure outranks the wait). A stop never gets here: `_settle` returns before its held
        branch while one stands."""
        return (bool(state.waiting_on_walk)
                and not any(entry["status"] == RowStatus.FAILED for entry in state.rows))

    def _watch_argv(self, state: QueueState) -> list[str]:
        """The watch, run on the pinned engine as the completion shim runs an advance, so an edit
        to the engine cannot change a queue already in flight."""
        return ["python3", state.engine_path, "--wait-on-walk", self.store.path, state.queue_id]

    @staticmethod
    def _held(state: QueueState) -> bool:
        """The queue launches nothing: a provider the file cannot give, a run that left the
        product checkout dirtier, or a walk it waits on. The first two end it halted once
        nothing is in flight, the last ends it waiting-on-a-walk."""
        return state.provider_refused or state.checkout_dirty or bool(state.waiting_on_walk)

    def _statuses(self, state: QueueState, numbers) -> list[RowStatus]:
        return [RowStatus(self._row(state, number)["status"]) for number in numbers]

    def _block(self, state: QueueState) -> bool:
        """Block dead dependencies and old-report successors after retirement. Only the
        Principal PM's fresh report may release the next pick. Owner rows also guard hand-offs
        and retirement even when a report omitted their dependency."""
        moved = False
        retired = [entry["number"] for entry in state.rows
                   if entry["move"] == _RETIRE
                   and entry["status"] in (RowStatus.LAUNCHED, RowStatus.LANDED,
                                            RowStatus.HANDED_OFF)]
        for entry in state.rows:
            if entry["status"] != RowStatus.WAITING:
                continue
            owner_rows = [owner["number"] for owner in state.rows
                          if KINDS[owner["move"]].disposition is Disposition.OWNER
                          and owner.get("from_refinement") == entry.get("from_refinement")]
            if retired and entry["number"] > retired[0] and not entry.get("from_refinement"):
                entry["status"] = RowStatus.BLOCKED.value
                entry["reason"] = f"the retire (row {retired[0]}) continues through nemawashi-refine"
                moved = True
            elif any(status in _DEAD for status in self._statuses(state, entry["after"])):
                entry["status"] = RowStatus.BLOCKED.value
                moved = True
            # Applied on every settle, not once when the row is entered: a resume puts every blocked
            # row back to waiting, so a rule applied only at entry would be lost on the first one.
            elif (owner_rows
                    and (KINDS[entry["move"]].disposition is Disposition.HAND_OFF
                         or entry["move"] == _RETIRE)
                    and not self._waits_on_any(state, entry, set(owner_rows))):
                entry["status"] = RowStatus.BLOCKED.value
                entry["reason"] = f"the owner's act comes first (row {owner_rows[0]})"
                moved = True
        return moved

    def _waits_on_any(self, state: QueueState, entry: dict, numbers: set[int]) -> bool:
        """Whether a row's After holds one of `numbers`, directly or through the rows it waits on.
        A row waits only on earlier rows, so the recursion ends."""
        return any(number in numbers
                   or self._waits_on_any(state, self._row(state, number), numbers)
                   for number in entry["after"])

    def _launch_ready(self, state: QueueState) -> bool:
        """Launch the first ready row, in row order, once no row of the queue is running — one row
        at a time, so no two runs share the product checkout and none is judged by what another
        left half-written (CP-572, CP-573). A row is running while its status is `launched`; a
        launch that fails, is refused as walking or hands off leaves none running, so the next ready
        row of the same pass may then start. A ready pick is still checked against the product's
        companions while another row runs (CP-574): only its own launch waits."""
        moved = False
        for entry in list(state.rows):
            if self._held(state):
                break
            if (entry["status"] == RowStatus.WAITING
                    and all(status is RowStatus.LANDED
                            for status in self._statuses(state, entry["after"]))):
                if self._waits_for_the_product(state, entry):
                    moved = True
                    continue
                if self._a_row_is_running(state):
                    continue
                self._launch(state, entry)
                moved = True
                if entry["move"] == _RETIRE:
                    break
        return moved

    @staticmethod
    def _a_row_is_running(state: QueueState) -> bool:
        return any(entry["status"] == RowStatus.LAUNCHED for entry in state.rows)

    def _waits_for_the_product(self, state: QueueState, entry: dict) -> bool:
        """The PM picks unless it can't (owner, 2026-09-30). While a companion is live the pick
        can't yet: a sweep row, running the chain the project card names, is put in front of it,
        once, and the pick waits on it — on a sweep row the queue already holds, if it holds one,
        before it adds another. A sweep that ends settled releases the pick; one that halts
        blocks it. A `none` card names no chain, so the pick does not wait."""
        if (entry["move"] != _PICK or entry.get("swept")
                or not self._live_companions(state.product_path, state.instance_root,
                                             state.project)):
            return False
        try:
            definition = read_definition(self._card_text(state.instance_root, state.project),
                                         card=card_path(state.instance_root, state.project))
        except QueueRefused as unreadable:
            # The pick cannot know whether to wait, so it fails with the card's own reason; its
            # dependents are blocked and the queue ends halted once nothing is in flight.
            entry["status"], entry["reason"] = RowStatus.FAILED.value, str(unreadable)
            return True
        if definition is Definition.NONE:
            return False
        queued = self._queued_sweep(state, entry)
        if queued is not None:
            entry["after"] = [*entry["after"], queued["number"]]
            entry["swept"] = True
            return True
        walk = self._walk_path(state)
        if walk_is_live(ChainStateStore(self.files, walk).raw()):
            # No second walk of the definition chain: the project's state file is that walk, and
            # a sweep row started now would only be refused (CP-523). The pick stays as it is, so
            # the next start checks the companions again.
            state.waiting_on_walk = walk
            return True
        number = max(row["number"] for row in state.rows) + 1
        planned = PlannedRow(number, _SWEEP, KINDS[_SWEEP].disposition, tuple(entry["after"]),
                             self._argv(_SWEEP, state.core_dir, state.instance_root, state.project,
                                        number=number),
                             "the pick waits on a live product companion")
        added = self._entry(planned)
        added["from_refinement"] = entry.get("from_refinement", False)
        state.rows.append(added)
        entry["after"] = [*entry["after"], number]
        entry["swept"] = True
        return True

    @staticmethod
    def _walk_path(state: QueueState) -> str:
        """The one state file both definition chains write for the project (`chain-product` and
        `chain-agari` share it), so it names the walk whichever chain started it."""
        return os.path.join(state.shim_dir, f"chain-{state.project}-state.json")

    def _queued_sweep(self, state: QueueState, pick: dict) -> dict | None:
        """The sweep row this queue already holds, for the pick to wait on (CP-522): one still
        waiting or launched that does not itself wait on the pick, since two rows each waiting
        on the other would never run."""
        for row in state.rows:
            if (row["move"] == _SWEEP
                    and row["status"] in (RowStatus.WAITING, RowStatus.LAUNCHED)
                    and not self._waits_on_any(state, row, {pick["number"]})):
                return row
        return None

    def _live_companions(self, product_path: str, instance_root: str, project: str) -> list[str]:
        """The Agari's companion, `system/projects/<project>/agari_open_issues.md` in the
        instance, and every `*_open_issues.md` under the product's docs/ — a companion outlives
        its round only while it holds something open (`core/tools/chain.py`
        `_live_companions`). The Agari's lives in the instance, so a missing product path says
        nothing about it."""
        found = []
        agari = os.path.join(instance_root, "system", "projects", project,
                             "agari_open_issues.md")
        if self.files.is_file(agari):
            found.append(agari)
        if not product_path:
            return found
        folders, seen = [os.path.join(product_path, "docs")], set()
        while folders:
            folder = folders.pop()
            if self.files.real_path(folder) in seen:
                continue            # a link back into the tree: walked once, never again
            seen.add(self.files.real_path(folder))
            for name in self.files.list_dir(folder):
                path = os.path.join(folder, name)
                if name.endswith("_open_issues.md") and self.files.is_file(path):
                    found.append(path)
                elif self.files.is_dir(path):
                    folders.append(path)
        return found

    def _launch(self, state: QueueState, entry: dict) -> None:
        """Start one row's launcher. The row is recorded pending and saved BEFORE the launcher
        runs, so a crash between the two leaves a state the next advance can act on."""
        kind = KINDS[entry["move"]]
        number = entry["number"]
        # Set or removed on every launch, never inherited: the engine's own environment is the
        # previous row's. A skill row runs on one provider; a chain is handed the force alone,
        # which its launcher reads as one, and otherwise runs each step on its own.
        if kind.disposition is Disposition.RUN_SKILL:
            try:
                provider = self.providers.at(state.instance_root).launch_provider(
                    state.forced_provider, providers.build_idea_row(entry["move"]))
            except ProvidersRefused as refused:
                # Read before anything of this launch is written (CP-283): the row fails naming
                # the entry, and the queue launches nothing more.
                entry["status"] = RowStatus.FAILED.value
                entry["reason"] = str(refused)
                state.provider_refused = True
                return
        else:
            provider = state.forced_provider
        argv, env = list(entry["argv"]), with_provider(self.environ, provider)
        # Set or removed on every launch, as the provider is: the engine's own environment is the
        # previous row's, and only a `readme-status` row is given a receipt of its own.
        env.pop(completion_shim.RESULT_FILE_VARIABLE, None)
        if kind.landed is Landed.README_STATUS_REPORTED:
            env[completion_shim.RESULT_FILE_VARIABLE] = self._fresh_receipt(state, entry)
        if kind.role:
            env["INSTRUMENT_RUN_CHAIN"] = QUEUE_NAME
            env["INSTRUMENT_RUN_WALK_ID"] = state.queue_id
            env["INSTRUMENT_RUN_ROLE"] = kind.role
            # The engine's own environment is the previous row's, inherited through its shim.
            env.pop("INSTRUMENT_RUN_AUDIT_TARGET", None)
        pending = {"move": entry["move"]}
        if kind.disposition is not Disposition.HAND_OFF and state.product_path:
            # The product checkout as this row found it, saved with the row it describes. An
            # unreadable checkout records nothing, and `advance` does not check a row without one.
            checkout_before = self.checkout.entries(state.product_path)
            if checkout_before is not None:
                pending[product_checkout.CHECKOUT_BEFORE] = checkout_before
        if kind.disposition is Disposition.RUN_SKILL:
            shim = self._write_shim(state, number)
            env, pending["identity"] = walk_stop.prepare_launch(self.files, shim, env)
            env["DETACH_WATCHER_ON_COMPLETE"] = shim
        else:
            # A chain, or a hand-off, tells this queue nothing through a run's completion hook, so
            # the previous row's hook must not be inherited and fired for it, and it records no
            # identity: only a skill row's run launcher writes one.
            env = walk_stop.without_launch_identity(env)
            env.pop("DETACH_WATCHER_ON_COMPLETE", None)
            if kind.disposition is Disposition.RUN_CHAIN:
                # One word as the chain's shell-style split reads it: a shim path holding a space
                # would otherwise split in two, the hook would never run, and the row would wait
                # for ever.
                argv += ["--on-end", shlex.quote(self._write_shim(state, number))]
        if kind.takes_context_cap:
            argv += ["--context-cap", str(state.context_cap)]
        if state.keep_awake:
            argv.append("--keep-awake")
        if kind.landed is Landed.SEED_REFINED:
            entry["before"] = self.journey.report_revision(self._refine_report(state))
        elif kind.landed is Landed.DOCS_CUT:
            entry["before"] = self._candidates(state)
        entry["status"] = RowStatus.LAUNCHED.value
        state.pending[str(number)] = pending
        self.store.save(state)
        exit_code = self.processes.run(argv, cwd=state.instance_root, env=env)
        if exit_code != 0:
            state.pending.pop(str(number), None)
            if kind.disposition in _CHAIN_STARTS and exit_code == EXIT_ALREADY_WALKING:
                walk = self._walk_path(state)
                entry["status"] = RowStatus.WAITING.value
                entry["reason"] = (f"its launcher exited {EXIT_ALREADY_WALKING}: {walk} is still "
                                   f"walking, so its chain did not start — the row waits, and is "
                                   f"launched again when the queue continues after that walk is "
                                   f"no longer walking")
                state.waiting_on_walk = walk
                return
            entry["status"] = RowStatus.FAILED.value
            entry["reason"] = f"its launcher exited {exit_code}"
            return
        self.notifier.send(f"{self._headline(state)} — launched {number}. {entry['move']}")
        if kind.disposition is Disposition.HAND_OFF:
            state.pending.pop(str(number), None)
            entry["status"] = RowStatus.HANDED_OFF.value

    @staticmethod
    def _fresh_receipt(state: QueueState, entry: dict) -> str:
        """A destination no earlier attempt of any row had, kept on the row before the launcher
        runs, with the prior attempt's ending cleared: a late watcher from a previous attempt
        writes somewhere this attempt never reads."""
        attempt = entry.get("attempts", 0) + 1
        entry["attempts"] = attempt
        entry.pop("ending", None)
        entry["receipt"] = os.path.abspath(os.path.join(
            state.shim_dir,
            f"build-idea-{state.project}-row-{entry['number']}-{state.queue_id}-{attempt}"
            f".receipt.json"))
        return entry["receipt"]

    def _write_shim(self, state: QueueState, number: int) -> str:
        shim = os.path.join(state.shim_dir, f"build-idea-{state.project}-row-{number}.sh")
        return completion_shim.write_shim(self.files, shim, engine_path=self.engine_path,
                                          advance_args=("--advance", self.store.path, str(number)),
                                          log_path=self._log_path(state))

    # -- ending ------------------------------------------------------------------------------------

    def _finish(self, state: QueueState) -> str:
        """Record how the queue ended and return what to tell the owner: the end on the first line,
        then every row that did not run — never run, failed, skipped, blocked — one per line."""
        by_status = {status: [entry for entry in state.rows if entry["status"] == status.value]
                     for status in RowStatus}
        owner_rows = [entry for entry in by_status[RowStatus.END]
                      if KINDS[entry["move"]].disposition is Disposition.OWNER]
        if state.stop_requested:
            end, what = QueueEnd.STOPPED, "stopped — the owner asked, and nothing new was started"
        elif by_status[RowStatus.FAILED]:
            end = QueueEnd.HALTED
            what = "halted — " + "; ".join(
                f"{entry['number']}. {entry['move']} failed: {entry['reason']}"
                for entry in by_status[RowStatus.FAILED])
        elif state.waiting_on_walk:
            end = QueueEnd.WAITING_ON_A_WALK
            resume = self._resume_command(state.core_dir or self._default_core(), state.project)
            still_walking = (f"waiting on a walk — {state.waiting_on_walk} is still walking, so "
                             f"nothing more was started.")
            what = (f"{still_walking} The queue is watching that walk and continues by itself "
                    f"once it is no longer walking, unless the walk was stopped. If the queue "
                    f"does not continue, resume with: {resume}"
                    if state.walk_watched else
                    f"{still_walking} The queue could not watch that walk, so it does not "
                    f"continue by itself when the walk is no longer walking. Once that walk is "
                    f"no longer walking, resume with: {resume}")
        elif owner_rows:
            end = QueueEnd.OWNER_OWED
            resume = self._resume_command(state.core_dir or self._default_core(), state.project)
            what = ("owner's act owed — "
                    + "; ".join(f"{entry['number']}. {entry['command']}" for entry in owner_rows)
                    + f" — once it is made, resume with: {resume}")
        elif by_status[RowStatus.HANDED_OFF]:
            end = QueueEnd.HANDED_OFF
            what = "handed off — the next change is walking"
        else:
            end, what = QueueEnd.DONE, "done — every row ran or was named"
        state.ended, state.ended_reason = end.value, what
        self.store.save(state)
        lines = [f"{self._headline(state)} — {what}"]
        if end is QueueEnd.STOPPED or self._held(state):
            lines += [f"never run: {entry['number']}. {entry['move']}"
                      for entry in by_status[RowStatus.WAITING]]
        if end is QueueEnd.STOPPED:
            lines += [f"failed: {entry['number']}. {entry['move']} — {entry['reason']}"
                      for entry in by_status[RowStatus.FAILED]]
        lines += [f"skipped: {entry['number']}. {entry['move']} — nothing runs it"
                  for entry in by_status[RowStatus.SKIPPED]]
        lines += [f"blocked: {entry['number']}. {entry['move']} — "
                  f"{entry['reason'] or 'waits on ' + _numbers(entry['after'])}"
                  for entry in by_status[RowStatus.BLOCKED]]
        return "\n".join(lines)

    # -- what the owner reads ----------------------------------------------------------------------

    def _start_message(self, state: QueueState) -> str:
        says = {Disposition.OWNER: "end — the owner makes it",
                Disposition.SKIP: "skip — no launcher"}
        carried = {RowStatus.LANDED: "already landed", RowStatus.HANDED_OFF: "already handed off"}
        lines = [f"{self._headline(state)} started — {state.key}, {len(state.rows)} rows from "
                 f"{os.path.basename(state.report)}"]
        for entry in state.rows:
            after = _numbers(entry["after"])
            what = (carried.get(RowStatus(entry["status"]))
                    or says.get(KINDS[entry["move"]].disposition, "runs"))
            lines.append(f"{entry['number']}. {entry['move']} — after {after} — {what}")
        return "\n".join(lines)

    @staticmethod
    def _headline(state: QueueState) -> str:
        instance = os.path.basename(os.path.normpath(state.instance_root))
        return f"{instance} · {state.project} · {QUEUE_NAME}"

    @staticmethod
    def _log_path(state: QueueState) -> str:
        """The one log a project's queue shares: every shim appends its advance here."""
        return os.path.join(state.shim_dir, f"build-idea-{state.project}.log")


# --- the composition root: the only place a concrete implementation is constructed ----------


class Journey:
    """The seedbed, read through `journey_status`'s own reading of it, so a seed means here what it
    means to every other reader: a `.md` file, or a folder holding `seed.md`."""

    def report_revision(self, path: str) -> list[int] | None:
        """A rewrite counts even when a fresh run reaches the same report text."""
        try:
            stat = Path(path).stat()
        except OSError:
            return None
        return [stat.st_mtime_ns, stat.st_ctime_ns, stat.st_size]

    def root_seeds(self, nemawashi_dir: str) -> list[str]:
        """The seeds directly in the seedbed root, sorted — `unpicked/`, `trail/` and `drop/` are
        folders with no `seed.md`, so they are not among them."""
        return [str(seed) for seed in journey_status._seed_entries(Path(nemawashi_dir))]

    def checklist_items(self, seed_path: str) -> int:
        """How many station items the seed's own text carries, ticked or not. `0` for a seed whose
        text cannot be read, which is a seed with no route cut."""
        try:
            text = journey_status._seed_text_path(Path(seed_path)).read_text(encoding="utf-8")
        except OSError:
            return 0
        return journey_status._checklist_counts(text)[1]


def build_queue(state_path: str, *, notifier_command: str, engine_path: str) -> BuildIdea:
    files = Files()
    processes = Processes()
    return BuildIdea(
        store=QueueStore(files, state_path),
        reader=DiskReader(files=files, git=Git()),
        journey=Journey(),
        files=files,
        processes=processes,
        notifier=Notifier(notifier_command, processes),
        lock=FileLock(),
        log=WalkLog(),
        id_source=IdSource(),
        environ=dict(os.environ),
        engine_path=engine_path,
        providers=ProviderFiles(files),
        process_table=walk_stop.ProcessTable(),
        checkout=product_checkout.Checkout(),
        watcher=WalkWatcher(),
    )


_START_REQUIRED_FLAGS: tuple[tuple[str, str], ...] = (
    ("--instance-root", "instance_root"),
    ("--project", "project"),
    ("--core-dir", "core_dir"),
    ("--shim-dir", "shim_dir"),
)

_DESCRIBE_REQUIRED_FLAGS: tuple[tuple[str, str], ...] = (
    ("--instance-root", "instance_root"),
    ("--project", "project"),
)


def _describe_line(planned: PlannedRow) -> str:
    after = _numbers(planned.after)
    what = {Disposition.OWNER: "owner", Disposition.SKIP: "skip"}.get(
        planned.disposition, shlex.join(planned.argv or []))
    if planned.refused:
        what = f"refused: {planned.refused}"
    return f"{planned.number}. {planned.move} — after {after} — {what}"


def main(argv: list[str] | None = None) -> int:
    try:
        from dotenv import load_dotenv
        from pathlib import Path
        load_dotenv()
        load_dotenv(Path.home() / ".env")
    except ImportError:
        pass

    """`--start <state>` is the launcher's entry; `--advance <state> <row> <outcome>` is what a
    row's shim fires; `--describe <state>` is what the launcher's `--dry-run` asks. None ever lets
    a traceback out as the whole answer: the advance runs detached from a hook nobody watches, so
    stderr goes to the queue's log and the owner's channel is the only place a stop can be seen —
    and the describe, which answers at a terminal, sends to that channel nothing at all."""
    parser = argparse.ArgumentParser(description="run a refine report's next moves as a queue")
    parser.add_argument("--start", metavar="STATE_PATH")
    parser.add_argument("--advance", nargs=3, metavar=("STATE_PATH", "ROW", "OUTCOME"))
    parser.add_argument("--describe", metavar="STATE_PATH",
                        help="say what a start would run, or why it would refuse — writing, "
                             "launching and sending nothing")
    parser.add_argument("--stop", metavar="STATE_PATH",
                        help="record the owner's stop: runs in flight finish, nothing new "
                             "starts, and chain-change's end does not restart the queue")
    parser.add_argument("--wait-on-walk", nargs=2, metavar=("STATE_PATH", "QUEUE_ID"),
                        help="the watch a queue leaves behind when it ends waiting-on-a-walk: "
                             "poll that walk, and continue the queue once it is no longer "
                             "walking")
    parser.add_argument("--instance-root")
    parser.add_argument("--project")
    parser.add_argument("--core-dir")
    parser.add_argument("--shim-dir")
    parser.add_argument("--key", default="",
                        help="the unit whose report to run; the sealed unit when omitted")
    parser.add_argument("--notifier", default="")
    parser.add_argument("--keep-awake", action="store_true")
    parser.add_argument("--product-path", default="",
                        help="the product the project builds; a pick waits for the product "
                             "chain while one of its documents has a live companion")
    parser.add_argument("--context-cap", type=_positive_integer, default=DEFAULT_CONTEXT_CAP,
                        metavar="TOKENS",
                        help="the developer's context cap for every chain-change row this queue "
                             "launches; read only with --start, and kept by a resumed queue "
                             f"(default {DEFAULT_CONTEXT_CAP})")
    parser.add_argument("--provider", choices=PROVIDERS, default="",
                        help="force every row and nested chain of the queue onto this "
                             "provider, over the one .providers.toml at the instance root "
                             "names, which is then not read; read with --start and "
                             "--describe")
    parser.add_argument("--by-hook", action="store_true",
                        help="this start is the one chain-change's end makes: it does nothing "
                             "while a stop stands")
    args = parser.parse_args(argv)

    chosen = [entry for entry in (args.start, args.advance, args.describe, args.stop,
                                  args.wait_on_walk) if entry]
    if len(chosen) > 1:
        print("build_idea: --start, --advance, --describe, --stop and --wait-on-walk are "
              "mutually exclusive", file=sys.stderr)
        return 2
    if not chosen:
        print("build_idea: one of --start, --advance, --describe, --stop or --wait-on-walk is "
              "required", file=sys.stderr)
        return 2

    engine_path = os.path.abspath(__file__)

    if args.describe:
        missing = [flag for flag, attribute in _DESCRIBE_REQUIRED_FLAGS
                   if not getattr(args, attribute)]
        if missing:
            print(f"build_idea: --describe requires {', '.join(missing)}", file=sys.stderr)
            return 2
        # Built with no notifier command at all, so nothing on this path can send: a dry run is
        # the owner asking a question at a terminal, never an event for their phone.
        queue = build_queue(args.describe, notifier_command="", engine_path=engine_path)
        try:
            plan = queue.describe(args.instance_root, args.project, args.key,
                                  args.core_dir or "", args.shim_dir or "",
                                  forced_provider=args.provider)
        except QueueRefused as exc:
            print(f"build_idea: {exc}", file=sys.stderr)
            return 3
        except Exception:
            traceback.print_exc(file=sys.stderr)
            return 5
        for planned in plan.rows:
            print(_describe_line(planned))
        return 0

    if args.stop:
        missing = [flag for flag, attribute in _DESCRIBE_REQUIRED_FLAGS
                   if not getattr(args, attribute)]
        if missing:
            print(f"build_idea: --stop requires {', '.join(missing)}", file=sys.stderr)
            return 2
        queue = build_queue(args.stop, notifier_command=args.notifier, engine_path=engine_path)
        try:
            said = queue.stop(args.instance_root, args.project,
                              datetime.now(timezone.utc).isoformat())
        except QueueRefused as exc:
            print(f"build_idea: {exc}", file=sys.stderr)
            queue.notifier.send(f"build-idea refused to stop — {exc}")
            return 3
        except Exception as exc:
            traceback.print_exc(file=sys.stderr)
            queue.notifier.send(f"build-idea crashed stopping — {str(exc) or type(exc).__name__}")
            return 5
        print(said)
        return 0

    if args.wait_on_walk:
        state_path, queue_id = args.wait_on_walk
        notifier_command = QueueStore(Files(), state_path).raw().get("notifier", "")
        queue = build_queue(state_path, notifier_command=notifier_command,
                            engine_path=engine_path)
        try:
            result = queue.wait_on_walk(queue_id)
        except QueueRefused as exc:
            print(f"build_idea: {exc}", file=sys.stderr)
            queue.notifier.send(f"build-idea refused to continue after a walk — {exc}")
            return 3
        except Exception as exc:
            print(f"build_idea: {str(exc) or type(exc).__name__}", file=sys.stderr)
            queue.notifier.send(f"build-idea crashed watching a walk — "
                                f"{str(exc) or type(exc).__name__}")
            return 5
        print(f"build_idea: acted={result.acted} ended={result.ended}")
        return 0

    if args.advance:
        state_path, row, outcome = args.advance
        notifier_command = QueueStore(Files(), state_path).raw().get("notifier", "")
        queue = build_queue(state_path, notifier_command=notifier_command,
                            engine_path=engine_path)
        try:
            result = queue.advance(int(row), outcome)
        except QueueRefused as exc:
            print(f"build_idea: {exc}", file=sys.stderr)
            queue.notifier.send(f"build-idea refused to advance row {row} — {exc}")
            return 3
        except Exception as exc:
            traceback.print_exc(file=sys.stderr)
            queue.notifier.send(f"build-idea crashed advancing {row} on {outcome!r} "
                                f"— {str(exc) or type(exc).__name__}")
            return 5
        print(f"build_idea: acted={result.acted} ended={result.ended}")
        return 0

    missing = [flag for flag, attribute in _START_REQUIRED_FLAGS if not getattr(args, attribute)]
    if missing:
        print(f"build_idea: --start requires {', '.join(missing)}", file=sys.stderr)
        return 2
    queue = build_queue(args.start, notifier_command=args.notifier, engine_path=engine_path)
    try:
        result = queue.start(instance_root=args.instance_root, project=args.project,
                             core_dir=args.core_dir, shim_dir=args.shim_dir, key=args.key,
                             notifier_command=args.notifier, keep_awake=args.keep_awake,
                             started_at=datetime.now(timezone.utc).isoformat(),
                             by_hook=args.by_hook, context_cap=args.context_cap,
                             product_path=args.product_path,
                             forced_provider=args.provider)
    except QueueRefused as exc:
        print(f"build_idea: {exc}", file=sys.stderr)
        queue.notifier.send(f"build-idea refused to start — {exc}")
        return 3
    except Exception as exc:
        traceback.print_exc(file=sys.stderr)
        queue.notifier.send(f"build-idea crashed starting — {str(exc) or type(exc).__name__}")
        return 5
    if isinstance(result, NoStationStart):
        print(result.message())
        return 0
    print(f"build_idea: acted={result.acted} ended={result.ended}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
