#!/usr/bin/env python3
"""chain_usage.py — what a chain walk spent, per document and per cycle.

WHY THIS EXISTS
    The telemetry package's `run_usage` reads what one background run spent, and its
    `flow_usage` reads what a workflow run spent, one row per step. Neither has a notion of a
    **chain**: `chain.py` walks a spine of documents, folding each one through
    `producer -> companion-self-answer -> producer` until it settles, and the runs that walk it
    appear in `run_usage`'s flat ledger as unattributed rows — nothing says which document a run
    belongs to, whether it produced or answered, or how many cycles a document took. Three readers,
    three populations, one unit apiece: a run there, a step there, a document cycle here.

    Measured against the live disk on 2026-09-09, over one instance's finished definition
    chain (239 watcher logs and 592 agent rows):

    1. **The chain-driven population is a watcher log carrying an `on_complete:` line.**
       `watch_agent.py:675` prints `on_complete: ran.`, and only under the
       `if args.on_complete:` guard at `:814-815`. The chain shim is the only caller that
       passes `--on-complete`, so that line's presence in a log **is** the fact that the run
       was chain-driven. 144 of the 239 logs carried it. Since 2026-09-25 the chains' runs are
       detached `claude --print` processes watched by `watch_process.py`, which prints the same
       line through the same `run_on_complete_hook` and names its run's own session id
       (`(run session <uuid>)`) — the join for a run no `claude agents` listing holds.
    2. **A log's name says which side of the cycle ran.** Every producer launcher passes
       `--log-stem "$project"` (`product-srs/launcher.sh:220` and its eight siblings);
       `companion-self-answer/launcher.sh:365` passes `--log-stem "$project-$doc_stem"`. So an
       untagged name is a producer and a tagged one is a self-answer, and the tag is the
       document — read off the launchers, not guessed from the body. **Not yet true of a
       producer started through `<CORE>/launchers/skill/launcher.sh`**, which every producer but
       the SDD's has been since 2026-09-17: that launcher passes `--log-stem "$skill"`, so its
       run's log is `watch-<skill>-<stamp>.log`, which `find_watch_logs` does not look for.
    3. **A producer's document comes from its transcript's first `user` record**, which reads
       `invoke the <skill> skill for the <project> project.` — the literal every producer
       launcher builds (`product-srs/launcher.sh:181` and its siblings). All 74 untagged
       chain-driven logs in that walk resolved this way.
    4. **The document a tag or a skill names is `chain.DOCUMENT_REGISTRY`'s, never a table
       here.** A tag matches a spec's `self_answer_arg`; a skill matches its `skill`.
       `product-architecture` writes two documents, so `architecture` is one key covering ADR
       and NFDR.
    5. **A watcher log's clock is UTC and its body's is not.** `detach_watcher.sh:320` stamps
       the filename with `date -u`; the `watch_agent: watching … at <time>` line inside is
       local. The filename is what this reader orders runs by.
    6. **There is a second population with no watcher log at all.** `product-sdd`'s runner
       starts three seats as separate background sessions named
       `sdd-<project>-run<N>-<cpo|cto|cdo>` (`kensaiapp_structure.md`, § *A trail is not the
       document's sibling*, "The archived run record is a frozen format").
       They leave no watcher log, so a reader built on population 1 alone omits them silently
       — 78 sessions on this machine, roughly a third of the walk's output tokens. That name
       scheme is a **convention** the skill calls a default rather than a fact like the
       `on_complete:` line, and this reader no longer takes it as the primary source: every run
       already states its own seats' names in its head block (the seat
       block `kensaiapp_structure.md` states, § *A trail is not the document's sibling*), so a
       seat is read off its run's own record wherever it parses
       (`record_seats`), and the name pattern above is consulted only as the named fallback for
       a run whose record does not. **Measured again on 2026-09-10:** all 22 real run records on
       disk parsed to exactly three seats each, and joined against this machine's own
       `claude agents --json --all`, the two sources agreed on every seat — neither missed one
       the other found. `SeatEvidence` states, per run, which of the two decided it, so a figure
       still says which population it rests on.
    7. **A cycle opens at a producer run.** Cycle N of a document is its Nth producer run in
       this reading plus every run for that document until the next producer — self-answers
       and, for the SDD, the seats that producer started. Runs before the document's first
       producer are **cycle 0**: the tail of a cycle whose producer ran outside this reading,
       stated rather than folded into cycle 1.

    **No price model, no currency** — this counts, it does not price, exactly like both
    siblings. **The five spend classes are kept apart and never summed**, and `thinking` stays
    a share of `output` rather than an addend: the telemetry gateway's `spend_by_model` does all
    of it here, and the package's `flow_usage` takes the same split from the package's
    `run_usage`.

    **What this reader does not attribute.** The chain engine's own `chain.py` invocations
    cost nothing to attribute because they are not runs; the shim that fires them leaves no
    session. A run launched by hand during a walk leaves a watcher log with no `on_complete:`
    line and is out of the population by definition, counted and named rather than dropped.

Usage:  ~/.kensaiapp/venv/bin/python <CORE>/tools/chain_usage.py
            --logs-dir DIR --project NAME [--json]
        ~/.kensaiapp/venv/bin/python <CORE>/tools/chain_usage.py
            --state <chain-state.json> [--json]

Under a Python that cannot import the telemetry package, it reads nothing, prints one line on stderr
saying so, and exits 1. `--help` and argument errors are answered without the package.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

import chain
import telemetry_gateway

__version__ = "1.5.1"

# The line `watch_agent.py:675` prints, and only under the `if args.on_complete:` guard at
# `:814-815`. A log carrying it was watched for a run the chain launched.
CHAIN_DRIVEN_MARKER = "on_complete:"

POPULATION_NOTE = (
    "Population 1 (measured): watcher logs for this project carrying an `on_complete:` line — "
    "the line watch_agent.py prints only when the chain passed --on-complete."
)

# `watch-<project>[-<tag>]-<YYYYMMDD>-<HHMMSS>.log`, the shape `detach_watcher.sh:320` writes.
# The stamp is `date -u`, so it is UTC.
_NAME_STAMP = re.compile(r"^(?:-(?P<tag>.+))?-(?P<date>\d{8})-(?P<time>\d{6})\.log$")

# The short run id a watcher log names, in all three forms the live logs carry: `completed`,
# `finished its turn and is idle`, and `declared itself finished at <marker>`. Only the id is
# read; what follows it is the watcher's prose and this reader has no use for it.
_RUN_LINE = re.compile(r"\(run ([0-9a-f]{8})\b")

# The session a `watch_process.py` log names — a `--print` run's own conversation id, joined to
# its transcript with no agent row between (`watch_process._state_note`).
_SESSION_LINE = re.compile(r"\(run session ([0-9a-fA-F-]{36})\)")

# The phrase every producer's prompt opens with — `skills/cto/.claude/skills/product-srs/launcher.md`'s
# `**Prompt:** invoke the product-srs skill for the {project} project.`
_PRODUCER_PROMPT = re.compile(r"invoke the ([a-z0-9][a-z0-9-]*) skill")

# The one producer that starts seats of its own, and the prefix its seat names carry —
# `kensaiapp_structure.md`, § *A trail is not the document's sibling*, "the default session name
# each seat answered to, `sdd-<project>-run<N>-<cpo|cto|cdo>`". A default the runner minted, not a
# fact the harness
# enforces, which is why the seats are a stated convention and the `on_complete:` line is not.
SEAT_RUNNER_SKILL = "product-sdd"
SEAT_RUNNER_PREFIX = "sdd"

SEAT_POPULATION_NOTE = (
    "Population 2: background sessions named `sdd-<project>-run<N>-<cpo|cto|cdo>` — the SDD "
    "runner's three seats, which leave no watcher log at all. Each run's own record states the "
    "names it minted (the seat block `kensaiapp_structure.md` states for the trail), and a "
    "seat is read off "
    "that record wherever it parses; the name pattern is consulted only as the named fallback, "
    "for a run whose record does not parse or when no record is given at all — this reading's "
    "own sourcing, run by run, follows below."
)


# ── Task 1 — the population is the watcher logs that carry an `on_complete:` line ──


@dataclass(frozen=True)
class WatchLogName:
    """What a watcher log's filename says: the tag, when it carries one, and the UTC instant
    the watcher was detached. `tag is None` is a producer run and a tag is a
    `companion-self-answer` run — the two log stems the launchers pass (see § 2 above)."""

    tag: str | None
    started_at: int  # epoch milliseconds, UTC


@dataclass(frozen=True)
class WatchLog:
    """One chain-driven watcher log — its name, what the name says, and the short id of the
    run it watched. `short_id is None` for a log whose body never named a run: this reader
    still carries the log, because a run it cannot join is a coverage fact, not a non-run."""

    name: str
    tag: str | None
    started_at: int
    short_id: str | None
    session_id: str | None = None


@dataclass(frozen=True)
class WatchLogs:
    """`watch_logs`'s whole answer — the population, plus what was seen and left out and why.
    `not_chain_driven` and `unparsed_names` are two different exclusions: the first is a log
    for a run the chain did not launch (out of scope by definition), the second is a file this
    reader could not read a name from (in scope and unreadable). Conflating them would hide
    the second, which is the undercount worth knowing about."""

    logs: tuple[WatchLog, ...]
    not_chain_driven: int
    unparsed_names: tuple[str, ...]
    total_seen: int


def watch_log_name(name: str, project: str) -> WatchLogName | None:
    """What `name` says, or `None` when it is not a watcher log for `project` at all.

    The stamp is read as UTC because `detach_watcher.sh:320` writes it with `date -u`. A
    project whose own name ends in something that looks like a tag is genuinely ambiguous on
    disk — `watch-a-b-<stamp>.log` is project `a` tag `b` and project `a-b` untagged, and
    nothing in the filename tells them apart — so the caller's `project` decides, and the
    remainder is the tag."""
    prefix = f"watch-{project}"
    if not name.startswith(prefix):
        return None
    match = _NAME_STAMP.match(name[len(prefix) :])
    if match is None:
        return None
    stamp = datetime.strptime(
        match.group("date") + match.group("time"), "%Y%m%d%H%M%S"
    ).replace(tzinfo=timezone.utc)
    return WatchLogName(tag=match.group("tag"), started_at=int(stamp.timestamp() * 1000))


def chain_driven(body: str) -> bool:
    """Whether `body` is the log of a run the chain launched — it carries the `on_complete:`
    line `watch_agent.py:675` prints only when `--on-complete` was passed."""
    return CHAIN_DRIVEN_MARKER in body


def short_id_in(body: str) -> str | None:
    """The short id of the run a watcher log watched, or `None` when the body named none —
    which happens when the watcher gave up without identifying its own run."""
    match = _RUN_LINE.search(body)
    return match.group(1) if match else None


def session_id_in(body: str) -> str | None:
    """The session id a process watcher's log names, or `None` — a `claude --bg` watcher's log
    names a short agent id instead (`short_id_in`)."""
    match = _SESSION_LINE.search(body)
    return match.group(1) if match else None


def watch_logs(logs_dir: Path, project: str, files: Files) -> WatchLogs:
    """Every chain-driven watcher log for `project` under `logs_dir`, oldest first.

    A `logs_dir` that does not exist reads as no logs rather than raising — the same
    "nothing to read" answer `Files.find_watch_logs` gives for one that exists and holds
    none."""
    kept: list[WatchLog] = []
    unparsed: list[str] = []
    not_chain_driven = 0
    seen = 0

    for path in files.find_watch_logs(logs_dir, project):
        parsed = watch_log_name(path.name, project)
        if parsed is None:
            unparsed.append(path.name)
            continue
        seen += 1
        body = files.read_text(path) or ""
        if not chain_driven(body):
            not_chain_driven += 1
            continue
        kept.append(
            WatchLog(
                name=path.name,
                tag=parsed.tag,
                started_at=parsed.started_at,
                short_id=short_id_in(body),
                session_id=session_id_in(body),
            )
        )

    return WatchLogs(
        logs=tuple(sorted(kept, key=lambda log: (log.started_at, log.name))),
        not_chain_driven=not_chain_driven,
        unparsed_names=tuple(sorted(unparsed)),
        total_seen=seen,
    )


# ── Task 2 — the document a run belongs to comes from chain.py's own registry ──


@dataclass(frozen=True)
class DocumentKey:
    """One document cycle this reader attributes runs to. The key is the **self-answer
    argument** rather than a document name, because `product-architecture` writes two
    documents in one run: `architecture` is one key covering ADR and NFDR, and a walk of it is
    one cycle, not two. Over `chain.DOCUMENT_REGISTRY` the key, the skill and the cycle are
    in one-to-one correspondence — the assumption both lookups below rest on, and the one
    `test_the_real_registry_yields_one_key_per_skill` exists to catch breaking."""

    key: str
    skill: str
    documents: tuple[str, ...]


def document_keys(registry) -> tuple[DocumentKey, ...]:
    """One `DocumentKey` per self-answer argument in `registry` — `chain.DOCUMENT_REGISTRY`'s
    shape, handed in rather than reached for so a caller can read a walk against a different
    registry than this machine's. Registry order is kept: it is `chain.py`'s own reading order
    and nothing here improves on it."""
    grouped: dict[str, list] = {}
    for spec in registry.values():
        grouped.setdefault(spec.self_answer_arg, []).append(spec)
    return tuple(
        DocumentKey(
            key=key,
            skill=specs[0].skill,
            documents=tuple(spec.name for spec in specs),
        )
        for key, specs in grouped.items()
    )


def key_for_tag(tag: str, keys: tuple[DocumentKey, ...]) -> DocumentKey | None:
    """The document cycle a watcher log's tag names, or `None` when it names none — never a
    guess. Matched case-insensitively, because the doc stems on disk are not uniformly cased:
    `watch-<project>-fdr-*` and `watch-<project>-SRS-*` were both written on 2026-09-09.

    `None` is a real answer, not a failure: a watcher log tagged `from-product-docs` is a run
    of a skill that writes no chain document, and this reader reports it unattributed rather
    than forcing it into a cycle."""
    for key in keys:
        if key.key.lower() == tag.strip().lower():
            return key
    return None


def key_for_skill(skill: str, keys: tuple[DocumentKey, ...]) -> DocumentKey | None:
    """The document cycle a producer's skill name belongs to, or `None`.

    A skill is matched against the skill `chain.py`'s registry names for the document."""
    wanted = skill.strip().lower()
    for key in keys:
        if key.skill.lower() == wanted:
            return key
    return None


def producer_skill(prompt_text: str | None) -> str | None:
    """The skill a producer launcher's opening prompt names, or `None` when it names none.

    Every producer's prompt opens with the same literal — `skills/cto/.claude/skills/product-srs/launcher.md`'s
    `**Prompt:** invoke the product-srs skill for the {project} project.` — and `product-sdd`'s
    appends four more sentences of run instructions after it, so the match is on the phrase
    rather than the whole string."""
    if not prompt_text:
        return None
    match = _PRODUCER_PROMPT.search(prompt_text)
    return match.group(1) if match else None


def first_user_text(path: Path, files: Files) -> str | None:
    """The text of the first `user` record in the transcript at `path`, or `None` when there
    is none — an unreadable transcript, or one this reader reached before its first turn
    landed.

    `content` arrives either as a plain string or as a list of blocks; both are read, and a
    malformed line is skipped rather than fatal, the same read-a-live-file posture
    the telemetry gateway's usage reader already takes."""
    lines = files.read_lines(path)
    if lines is None:
        return None
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except (ValueError, TypeError):
            continue
        if not isinstance(record, dict) or record.get("type") != "user":
            continue
        content = (record.get("message") or {}).get("content")
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            joined = " ".join(
                block.get("text", "") for block in content if isinstance(block, dict)
            )
            return joined.strip()
    return None


# ── Task 3 — the runs: a log joins to a session, and the seats are their own population ──


class Kind(str, Enum):
    """Which side of a document's cycle a run was. The value is written into `--json` output,
    so it is the `(str, Enum)` form per `languages/python/conventions.md` § Constructs."""

    PRODUCER = "producer"
    SELF_ANSWER = "self-answer"
    SEAT = "seat"


class Source(str, Enum):
    """How this reader found the run at all — which of the two populations it came from, and
    therefore how strong its attribution is. A watcher log is a measurement (§ 1 above); a seat
    session is a name-scheme convention (§ 6). Reporting them apart is what lets a reader see
    which of the two any figure rests on."""

    WATCH_LOG = "watch-log"
    SEAT_SESSION = "seat-session"


class SeatEvidence(str, Enum):
    """How a `Kind.SEAT` run's attribution was found — its own run record stating the name
    (`record_seats`), or today's name-pattern convention (`seat_rows`), consulted only as the
    named fallback for a run whose record could not be read. `None` on every other kind of run —
    the axis only applies to seats."""

    RECORD = "record"
    CONVENTION = "convention"


class Transcript(str, Enum):
    """What became of the run's transcript. `NO_SESSION` and `MISSING` are two different
    facts: the first is a run this reader could not name a session for at all, the second is a
    named session whose transcript is not on disk — transcripts get pruned, and six seat
    transcripts from the walk measured were already gone on 2026-09-09."""

    READ = "read"
    MISSING = "missing"
    NO_SESSION = "no-session"


@dataclass(frozen=True)
class AgentRow:
    """One row of `claude agents --json --all`, projected to what this reader joins on.

    The gateway's `parse_runs` is not reused for this, for two reasons that are both about the
    join rather than about taste: it drops `id`, which is the only field a watcher log gives
    this reader to join on, and it excludes `kind == "interactive"`, which is right for a
    ledger of background runs and wrong for a join keyed on an id a log already named."""

    id: str
    session_id: str
    name: str | None
    started_at: int | None
    state: str | None


@dataclass(frozen=True)
class SeatRow:
    """One SDD seat session — its agent row, which seat it held, and the runner's own run
    number from the name. The run number is the runner's counter, not this reader's cycle:
    they are two different numberings and are never reported as one."""

    row: AgentRow
    seat: str
    runner_run: int


@dataclass(frozen=True)
class ChainRun:
    """One run of a chain walk, whichever population it came from, with the usage records its
    transcript carried. The records are kept rather than a summed spend, so an aggregate over
    several runs is the gateway's `spend_by_model` over their combined records — the package's own
    accumulator applied once, never a second accumulator adding `Spend`s together.

    `cycle` is `None` until `with_cycles` assigns it, and `document_key is None` is a real
    answer: a run whose document this reader could not name is reported unattributed."""

    label: str
    source: Source
    kind: Kind
    document_key: str | None
    session_id: str | None
    started_at: int | None
    transcript: Transcript
    records: tuple
    cycle: int | None = None
    seat: str | None = None
    runner_run: int | None = None
    seat_evidence: SeatEvidence | None = None


def agent_rows(agents_json_text: str) -> tuple[AgentRow, ...]:
    """Parse `claude agents --json --all` output into the rows this reader joins against. A
    row with no `sessionId` is dropped — there is nothing to join it on — and this reader has
    no use for a count of those, because it never looked for them: its population is the logs
    and the seat names, not the agents list."""
    try:
        rows = json.loads(agents_json_text)
    except (ValueError, TypeError) as exc:
        raise ValueError(
            f"chain_usage: could not parse `claude agents --json --all` output as JSON: {exc}"
        ) from exc
    if not isinstance(rows, list):
        raise ValueError(
            "chain_usage: `claude agents --json --all` output was not a JSON array "
            f"(got {type(rows).__name__})"
        )
    parsed = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        session_id = row.get("sessionId")
        row_id = row.get("id")
        if not session_id or not row_id:
            continue
        parsed.append(
            AgentRow(
                id=row_id,
                session_id=session_id,
                name=row.get("name"),
                started_at=row.get("startedAt"),
                state=row.get("state"),
            )
        )
    return tuple(parsed)


def seat_rows(rows: tuple[AgentRow, ...], project: str) -> tuple[SeatRow, ...]:
    """Every SDD seat session for `project`, one per session and never one per name: the
    runner relaunches a blocked seat under the same name, so one `run10-cpo` seat name covers
    four sessions on this machine and keying on the name would lose three transcripts."""
    pattern = re.compile(
        rf"^{SEAT_RUNNER_PREFIX}-{re.escape(project)}-run(\d+)-(cpo|cto|cdo)$"
    )
    seats = []
    for row in rows:
        match = pattern.match(row.name or "")
        if match is None:
            continue
        seats.append(
            SeatRow(row=row, seat=match.group(2), runner_run=int(match.group(1)))
        )
    return tuple(seats)


# ── A run's seats are found by what its record says, not by convention ──


# The record's own seat line, as `kensaiapp_structure.md` § *A trail is not the document's
# sibling* states it: `  - CTO — `<session-name>``,
# two-space indent. The "Standing declared move" line beneath it is zero-indented and carries no
# seat, so a pattern anchored on the two-space indent never reads it as a fourth seat.
_SEATS_HEADER = "Seats, and the names they answer to:"
_SEAT_LINE = re.compile(r"^  - (CTO|CPO|CDO) — `([^`]+)`(.*)$")
_RECORDED_ID = re.compile(r"`([0-9a-f]{8})`")


@dataclass(frozen=True)
class RecordedSeat:
    """One seat a run record's own head block states — which seat, the session name it answers
    to, and every session id the record wrote down for it, in the order it wrote them. Real
    records carry a note after the name only after a relaunch (`run-10.md`'s three seats each
    carry four ids); most carry none, so `recorded_ids` is empty far more often than not."""

    seat: str
    name: str
    recorded_ids: tuple[str, ...]


def record_seats(text: str) -> tuple[RecordedSeat, ...] | None:
    """The three seats `text`'s own **Seats, and the names they answer to** block states, or
    `None` when it does not state exactly three — never a partial guess. Only the lines under
    that header are read: the **Standing declared move** line beneath it is a different bullet
    at a different indent and contributes no seat. A note after a name, including one wrapped
    onto an indented continuation line, is read for the session ids it carries, in order."""
    lines = text.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if _SEATS_HEADER in line)
    except StopIteration:
        return None

    entries: list[list[str]] = []  # [seat, name, note] per line, note grown by continuations
    for line in lines[start + 1 :]:
        match = _SEAT_LINE.match(line)
        if match is not None:
            entries.append([match.group(1).lower(), match.group(2), match.group(3)])
            continue
        if entries and line.startswith("    ") and line.strip():
            entries[-1][2] += " " + line.strip()
            continue
        break

    if len(entries) != 3:
        return None
    seats = tuple(
        RecordedSeat(seat=seat, name=name, recorded_ids=tuple(_RECORDED_ID.findall(note)))
        for seat, name, note in entries
    )
    if len({seat.seat for seat in seats}) != 3:
        return None
    return seats


_RUN_RECORD_NAME = re.compile(r"^run-(\d+)\.md$")


@dataclass(frozen=True)
class RunRecord:
    """One `docs/trail/sdd/run-<N>.md`, the runner's own run number from its name, and its seats
    — `None` when `record_seats` could not read exactly three from it, a real absence this
    reader carries forward rather than raising over."""

    run: int
    path: Path
    seats: tuple[RecordedSeat, ...] | None


def product_run_records(product_path: Path, files: Files) -> tuple[RunRecord, ...]:
    """Every `docs/trail/sdd/run-<N>.md` under `product_path`, in run order, each parsed through
    `record_seats`. `cycle-<N>.md` and `self_answer-<N>.md` sit beside the runs on disk and are a
    different population entirely — only a name matching `run-<N>.md` becomes a `RunRecord` at
    all. A product with no `docs/trail/sdd/` yields no records, not an error."""
    numbered = []
    for path in files.find_run_records(product_path):
        match = _RUN_RECORD_NAME.match(path.name)
        if match is None:
            continue
        numbered.append((int(match.group(1)), path))
    numbered.sort(key=lambda pair: pair[0])
    return tuple(
        RunRecord(run=run, path=path, seats=record_seats(files.read_text(path) or ""))
        for run, path in numbered
    )


@dataclass(frozen=True)
class RecordSeatJoin:
    """Every SDD seat session a project's own run records name, joined to the agent rows that
    carry that name — several rows under one recorded name are several seat sessions, one per
    session, exactly as `seat_rows` already holds for the pattern. `unmatched` names a recorded
    seat name no agent row answered to, so it is reported rather than silently dropped; a run
    whose record did not parse at all contributes neither a seat nor an unmatched name — it has
    nothing to report until `read_seats` falls it back to the pattern (Task 4)."""

    seats: tuple[SeatRow, ...]
    unmatched: tuple[str, ...]


def seat_rows_from_records(
    records: tuple[RunRecord, ...], rows: tuple[AgentRow, ...]
) -> RecordSeatJoin:
    """Join `records` to `rows` by exact name — the record supplies which seat a name answers to
    and the runner's own run number; the agent row supplies the session. Scoped entirely by what
    `records` already holds: a caller that reads records for one product never has another
    product's names to join against, so another product's rows are never read even when handed
    in `rows` alongside this product's own."""
    by_name: dict[str, list[AgentRow]] = {}
    for row in rows:
        if row.name:
            by_name.setdefault(row.name, []).append(row)

    seats: list[SeatRow] = []
    unmatched: list[str] = []
    for record in records:
        if record.seats is None:
            continue
        for recorded in record.seats:
            matches = by_name.get(recorded.name, ())
            if not matches:
                unmatched.append(recorded.name)
                continue
            seats.extend(
                SeatRow(row=row, seat=recorded.seat, runner_run=record.run) for row in matches
            )
    return RecordSeatJoin(seats=tuple(seats), unmatched=tuple(unmatched))


def _records_for(
    session_id: str | None,
    projects_root: Path,
    files: Files,
    telemetry: telemetry_gateway.Telemetry,
) -> tuple[Transcript, tuple, Path | None]:
    """The transcript state and usage records for `session_id` — resolved through the
    gateway's `find_transcript` and read through its `read_usage`, the package's own
    resolution and reader rather than a second pair."""
    if session_id is None:
        return Transcript.NO_SESSION, (), None
    path = telemetry.find_transcript(session_id, projects_root, files)
    if path is None:
        return Transcript.MISSING, (), None
    return Transcript.READ, tuple(telemetry.read_usage(path, files)), path


def runs_from_logs(
    logs: tuple[WatchLog, ...],
    rows: tuple[AgentRow, ...],
    projects_root: Path,
    files: Files,
    keys: tuple[DocumentKey, ...],
    telemetry: telemetry_gateway.Telemetry,
) -> tuple[ChainRun, ...]:
    """One `ChainRun` per watcher log. A tagged log is a `companion-self-answer` run whose
    document the tag names; an untagged one is a producer whose document comes from the first
    `user` record of its transcript, so a producer with no readable transcript is
    unattributed — a stated absence rather than a guess.

    A run's `started_at` is the log's own UTC stamp, not the agent row's `startedAt`: the
    stamp is the watcher's detachment, which is the launch this reader orders cycles by, and
    it exists even for a log that joins to no agent row at all."""
    by_short_id = {row.id: row for row in rows}
    runs = []
    for log in logs:
        row = by_short_id.get(log.short_id) if log.short_id else None
        session_id = log.session_id or (row.session_id if row else None)
        state, records, path = _records_for(session_id, projects_root, files, telemetry)

        if log.tag is not None:
            kind = Kind.SELF_ANSWER
            key = key_for_tag(log.tag, keys)
        else:
            kind = Kind.PRODUCER
            skill = producer_skill(first_user_text(path, files)) if path else None
            key = key_for_skill(skill, keys) if skill else None

        runs.append(
            ChainRun(
                label=log.name,
                source=Source.WATCH_LOG,
                kind=kind,
                document_key=key.key if key else None,
                session_id=session_id,
                started_at=log.started_at,
                transcript=state,
                records=records,
            )
        )
    return tuple(runs)


@dataclass(frozen=True)
class SeatReading:
    """This project's seat sessions, plus which evidence found each one and the recorded names
    no agent row answered to. `evidence` is keyed on the runner's own run number, not the seat,
    because a run's whole three seats share one source: the record either named all three or it
    did not parse at all (`record_seats` never yields a partial three)."""

    seats: tuple[SeatRow, ...]
    evidence: dict[int, SeatEvidence]
    unmatched_recorded_names: tuple[str, ...]


def read_seats(
    product_path: Path | None,
    project: str,
    rows: tuple[AgentRow, ...],
    files: Files,
) -> SeatReading:
    """This project's seat sessions, read by record wherever a run's own record parses, and by
    the name pattern for every run it does not — including every run, when `product_path` is
    `None` altogether (the stated fallback: a reading with no product path is never a reason to
    reach for a new resolver). A run whose record parses is never also read through the
    pattern — the record is the whole answer for that run, decoy pattern-matches included."""
    pattern_seats = seat_rows(rows, project)

    if product_path is None:
        evidence = {seat.runner_run: SeatEvidence.CONVENTION for seat in pattern_seats}
        return SeatReading(seats=pattern_seats, evidence=evidence, unmatched_recorded_names=())

    records = product_run_records(product_path, files)
    join = seat_rows_from_records(records, rows)
    parsed_runs = {record.run for record in records if record.seats is not None}

    pattern_by_run: dict[int, list[SeatRow]] = {}
    for seat in pattern_seats:
        pattern_by_run.setdefault(seat.runner_run, []).append(seat)

    seats: list[SeatRow] = list(join.seats)
    evidence: dict[int, SeatEvidence] = {run: SeatEvidence.RECORD for run in parsed_runs}
    for run, run_seats in pattern_by_run.items():
        if run in parsed_runs:
            continue
        seats.extend(run_seats)
        evidence[run] = SeatEvidence.CONVENTION

    return SeatReading(
        seats=tuple(seats), evidence=evidence, unmatched_recorded_names=join.unmatched
    )


def runs_from_seats(
    seats: tuple[SeatRow, ...],
    projects_root: Path,
    files: Files,
    keys: tuple[DocumentKey, ...],
    telemetry: telemetry_gateway.Telemetry,
    evidence: dict[int, SeatEvidence] | None = None,
) -> tuple[ChainRun, ...]:
    """One `ChainRun` per SDD seat session, attributed to the document its runner writes —
    resolved through `key_for_skill(SEAT_RUNNER_SKILL, …)` rather than a literal document
    name, so the two stay in step if the registry moves.

    A seat's `started_at` is the agents list's `startedAt`, epoch ms UTC — the same clock the
    log stamps resolve to, which is what lets one cycle rule order both populations.

    `evidence` states, per runner run number, which of `SeatEvidence`'s two sources decided that
    run's seats (`read_seats`'s own answer). A run number the map does not name, or no map at
    all, means `CONVENTION` — `seats` handed in bare, e.g. straight from `seat_rows`, is always
    pattern-found by construction."""
    key = key_for_skill(SEAT_RUNNER_SKILL, keys)
    runs = []
    for seat in seats:
        state, records, _path = _records_for(
            seat.row.session_id, projects_root, files, telemetry
        )
        runs.append(
            ChainRun(
                label=seat.row.name or seat.row.session_id,
                source=Source.SEAT_SESSION,
                kind=Kind.SEAT,
                document_key=key.key if key else None,
                session_id=seat.row.session_id,
                started_at=seat.row.started_at,
                transcript=state,
                records=records,
                seat=seat.seat,
                runner_run=seat.runner_run,
                seat_evidence=(evidence or {}).get(seat.runner_run, SeatEvidence.CONVENTION),
            )
        )
    return tuple(runs)


def run_spend(
    run: ChainRun, telemetry: telemetry_gateway.Telemetry
) -> dict[str, telemetry_gateway.Spend]:
    """One `Spend` per model this run used — the gateway's `spend_by_model` over the records
    it already holds. The five classes are kept apart and `thinking` stays a share of
    `output`, because that function is the one place either rule is implemented."""
    return telemetry.spend_by_model(run.records)


def run_span(run: ChainRun, telemetry: telemetry_gateway.Telemetry) -> float | None:
    """The run's wall time from its own transcript — the gateway's `span_seconds`, a span
    measured first-to-last and never a sum. `None` for a run with no timestamped record at
    all, which is a different fact from a run that took no time."""
    return telemetry.span_seconds(run.records)


# ── Task 4 — the cycles, the aggregation, and the coverage this reading states ──


CYCLE_NOTE = (
    "A cycle opens at a producer run: cycle N of a document is its Nth producer run in this "
    "reading plus every run for that document until the next producer. Cycle 0 is the runs "
    "before the document's first producer here — the tail of a cycle whose producer ran "
    "outside this reading, never folded into cycle 1."
)


def with_cycles(runs: tuple[ChainRun, ...]) -> tuple[ChainRun, ...]:
    """Every run with its cycle assigned, per document, in the order they started.

    Producer-opens rather than producer-closes, and the live disk chose it: the SDD runner
    starts its seats a minute or two after itself, so only producer-opens puts a seat in the
    cycle of the producer that actually launched it.

    Two runs keep `cycle = None`, for two different reasons this function does not conflate: a
    run with no document (there is no per-document sequence to place it in) and a run with no
    start time (there is no position in one). `coverage` names the second; the first is already
    named as unattributed."""
    placeable = [
        (index, run)
        for index, run in enumerate(runs)
        if run.document_key and run.started_at is not None
    ]
    placeable.sort(key=lambda pair: (pair[1].started_at, pair[1].label))

    cycle_now: dict[str, int] = {}
    assigned: dict[int, int] = {}
    for index, run in placeable:
        key = run.document_key
        if run.kind is Kind.PRODUCER:
            cycle_now[key] = cycle_now.get(key, 0) + 1
        assigned[index] = cycle_now.get(key, 0)

    return tuple(
        replace(run, cycle=assigned[index]) if index in assigned else run
        for index, run in enumerate(runs)
    )


def parse_day(text: str) -> int:
    """A `YYYY-MM-DD` date as epoch milliseconds at midnight **UTC** — the clock both
    populations already report in, so a window means the same thing to a watcher log's
    filename stamp and to an agent row's `startedAt`."""
    try:
        day = datetime.strptime(text, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"chain_usage: not a YYYY-MM-DD date: {text}") from exc
    return int(day.timestamp() * 1000)


def within(
    runs: tuple[ChainRun, ...], *, since: int | None, until: int | None
) -> tuple[ChainRun, ...]:
    """The runs inside `[since, until)`, in epoch milliseconds. A run with no start time is
    **never** windowed out: it has no position to judge, and dropping it would be an
    undercount this reader could not name afterwards."""
    kept = []
    for run in runs:
        if run.started_at is None:
            kept.append(run)
            continue
        if since is not None and run.started_at < since:
            continue
        if until is not None and run.started_at >= until:
            continue
        kept.append(run)
    return tuple(kept)


@dataclass(frozen=True)
class DocumentRow:
    """One document cycle's whole reading. `cycles` counts the productions this reading saw,
    so it never counts cycle 0 — that cycle's producer ran outside the window and counting it
    would claim a production nobody read."""

    key: str | None
    documents: tuple[str, ...]
    cycles: int
    producers: int
    self_answers: int
    seats: int
    runs: int
    spend: dict[str, telemetry_gateway.Spend]


@dataclass(frozen=True)
class CycleRow:
    """One `(document, cycle)` pair — the finest unit this reader reports."""

    key: str | None
    documents: tuple[str, ...]
    cycle: int | None
    producers: int
    self_answers: int
    seats: int
    runs: int
    started_at: int | None
    spend: dict[str, telemetry_gateway.Spend]


def _combined_spend(
    runs, telemetry: telemetry_gateway.Telemetry
) -> dict[str, telemetry_gateway.Spend]:
    """The spend across several runs — the gateway's `spend_by_model` over their combined
    records, which is the package's accumulator applied once rather than a second one adding
    `Spend`s. That is what keeps "no class is ever summed with another" true here without
    this module implementing the rule a second time."""
    records = [record for run in runs for record in run.records]
    return telemetry.spend_by_model(records)


def _key_order(keys: tuple[DocumentKey, ...]) -> dict[str | None, int]:
    """Registry order, with the unattributed row last — `chain.py`'s own reading order, which
    is upstream-first, and nothing here improves on it."""
    order = {key.key: index for index, key in enumerate(keys)}
    order[None] = len(order)
    return order


def _documents_for(key: str | None, keys: tuple[DocumentKey, ...]) -> tuple[str, ...]:
    for candidate in keys:
        if candidate.key == key:
            return candidate.documents
    return ()


def _counts(runs) -> tuple[int, int, int]:
    producers = sum(1 for run in runs if run.kind is Kind.PRODUCER)
    self_answers = sum(1 for run in runs if run.kind is Kind.SELF_ANSWER)
    seats = sum(1 for run in runs if run.kind is Kind.SEAT)
    return producers, self_answers, seats


def by_document(
    runs: tuple[ChainRun, ...],
    keys: tuple[DocumentKey, ...],
    telemetry: telemetry_gateway.Telemetry,
) -> tuple[DocumentRow, ...]:
    """One row per document cycle this reading saw, in registry order, with the unattributed
    runs as a row of their own at the end. A document with no runs gets no row: this reader
    reports what it read, and the spine's own coverage is stated separately."""
    grouped: dict[str | None, list[ChainRun]] = {}
    for run in runs:
        grouped.setdefault(run.document_key, []).append(run)

    order = _key_order(keys)
    rows = []
    for key in sorted(grouped, key=lambda k: order.get(k, len(order))):
        group = grouped[key]
        producers, self_answers, seats = _counts(group)
        rows.append(
            DocumentRow(
                key=key,
                documents=_documents_for(key, keys),
                cycles=len({run.cycle for run in group if run.cycle}),
                producers=producers,
                self_answers=self_answers,
                seats=seats,
                runs=len(group),
                spend=_combined_spend(group, telemetry),
            )
        )
    return tuple(rows)


def by_cycle(
    runs: tuple[ChainRun, ...],
    keys: tuple[DocumentKey, ...],
    telemetry: telemetry_gateway.Telemetry,
) -> tuple[CycleRow, ...]:
    """One row per `(document, cycle)`, in registry order then cycle order. A run this reader
    could not place carries `cycle = None` and gets its own row rather than joining another
    document's."""
    grouped: dict[tuple[str | None, int | None], list[ChainRun]] = {}
    for run in runs:
        grouped.setdefault((run.document_key, run.cycle), []).append(run)

    order = _key_order(keys)
    rows = []
    for key, cycle in sorted(
        grouped, key=lambda pair: (order.get(pair[0], len(order)), pair[1] is None, pair[1] or 0)
    ):
        group = grouped[(key, cycle)]
        producers, self_answers, seats = _counts(group)
        starts = [run.started_at for run in group if run.started_at is not None]
        rows.append(
            CycleRow(
                key=key,
                documents=_documents_for(key, keys),
                cycle=cycle,
                producers=producers,
                self_answers=self_answers,
                seats=seats,
                runs=len(group),
                started_at=min(starts) if starts else None,
                spend=_combined_spend(group, telemetry),
            )
        )
    return tuple(rows)


@dataclass(frozen=True)
class Coverage:
    """What this reading covered and what it could not, never implied. The two populations are
    counted apart because they are different evidence (a measured `on_complete:` line against
    a stated name scheme), and the runs this reader could not attribute or place are **named**
    rather than only counted — a count says a gap exists, a name says which run to open."""

    logs_seen: int
    logs_not_chain_driven: int
    logs_unparsed: tuple[str, ...]
    chain_driven_runs: int
    seat_runs: int
    transcripts_read: int
    transcripts_missing: int
    no_session: int
    unattributed: tuple[str, ...]
    unplaced: tuple[str, ...]


def coverage(runs: tuple[ChainRun, ...], logs: WatchLogs) -> Coverage:
    """The coverage of one reading — each figure counted independently over `runs` and over
    the population `logs` came from, never derived from one another."""
    return Coverage(
        logs_seen=logs.total_seen,
        logs_not_chain_driven=logs.not_chain_driven,
        logs_unparsed=logs.unparsed_names,
        chain_driven_runs=sum(1 for run in runs if run.source is Source.WATCH_LOG),
        seat_runs=sum(1 for run in runs if run.source is Source.SEAT_SESSION),
        transcripts_read=sum(1 for run in runs if run.transcript is Transcript.READ),
        transcripts_missing=sum(1 for run in runs if run.transcript is Transcript.MISSING),
        no_session=sum(1 for run in runs if run.transcript is Transcript.NO_SESSION),
        unattributed=tuple(run.label for run in runs if run.document_key is None),
        unplaced=tuple(
            run.label for run in runs if run.document_key is not None and run.cycle is None
        ),
    )


# ── Task 5 — the state file, the whole reading, both renderings and the CLI ──


@dataclass(frozen=True)
class ChainStateFacts:
    """The four things this reader takes from a chain's own state file: which project and
    which instance the walk ran in, what the chain was called and how it ended, and the spine
    it was given.

    **Never the state's `rounds` counter.** That is the engine's own per-document numbering,
    reset by a walk this reader may not be looking at; the cycles here are derived from the
    logs. Reporting both as one number would be a fiction, so only one of them is reported."""

    chain_name: str | None
    project: str | None
    instance_root: str | None
    product_path: str | None
    spine: tuple[str, ...]
    ended: str | None
    ended_reason: str | None


def chain_state(path: Path, files: Files) -> ChainStateFacts | None:
    """The facts above from the state file at `path`, or `None` when it cannot be read or
    parsed. `None` is not fatal anywhere: the state file is an anchor this reader can do
    without, and a walk read from a logs directory alone reads exactly the same runs."""
    text = files.read_text(path)
    if text is None:
        return None
    try:
        data = json.loads(text)
    except (ValueError, TypeError):
        return None
    if not isinstance(data, dict):
        return None
    spine = data.get("spine")
    return ChainStateFacts(
        chain_name=data.get("chain_name"),
        project=data.get("project"),
        instance_root=data.get("instance_root"),
        product_path=data.get("product_path"),
        spine=tuple(spine) if isinstance(spine, list) else (),
        ended=data.get("ended"),
        ended_reason=data.get("ended_reason"),
    )


def logs_dir_for(state: ChainStateFacts | None) -> Path | None:
    """The logs directory a state file implies — `<instance_root>/system/logs`, where
    `detach_watcher.sh` writes and where the state file itself sits. `None` when the state
    names no instance root, so the caller asks for one rather than reading an invented path."""
    if state is None or not state.instance_root:
        return None
    return Path(state.instance_root) / "system" / "logs"


def key_for_document(name: str, keys: tuple[DocumentKey, ...]) -> DocumentKey | None:
    """The cycle key covering the document called `name`, or `None`. A spine names documents
    (`ADR`) while this reader keys cycles by the self-answer argument (`architecture`), so
    without this a walked ADR would read as a spine document nothing ran for."""
    wanted = name.strip().lower()
    for key in keys:
        if any(document.lower() == wanted for document in key.documents):
            return key
    return None


def spine_without_runs(
    spine: tuple[str, ...], runs: tuple[ChainRun, ...], keys: tuple[DocumentKey, ...]
) -> tuple[str, ...]:
    """The spine documents this reading saw no run for, in spine order. A spine entry the
    registry does not know is named too rather than skipped — it is exactly the case where
    this reader cannot say whether anything ran."""
    ran = {run.document_key for run in runs}
    missing = []
    for name in spine:
        key = key_for_document(name, keys)
        if key is None or key.key not in ran:
            missing.append(name)
    return tuple(missing)


@dataclass(frozen=True)
class Reading:
    """One whole reading of a walk — every run from both populations with its cycle assigned,
    what the reading covered, the keys it attributed against, and the window and state file it
    was scoped by, with the telemetry collaborator the aggregation and renderings read spend
    through — and every seat name a run record states that no agent row answered to, so
    a recorded seat with no session is reported rather than dropped."""

    project: str
    runs: tuple[ChainRun, ...]
    coverage: Coverage
    keys: tuple[DocumentKey, ...]
    state: ChainStateFacts | None
    since: int | None
    until: int | None
    telemetry: telemetry_gateway.Telemetry
    unmatched_recorded_names: tuple[str, ...] = ()


def read_walk(
    *,
    logs_dir: Path,
    project: str,
    agents_json_text: str,
    projects_root: Path,
    files: Files,
    keys: tuple[DocumentKey, ...],
    since: int | None,
    until: int | None,
    telemetry: telemetry_gateway.Telemetry,
    state: ChainStateFacts | None = None,
) -> Reading:
    """Assemble both populations into one reading: the chain-driven watcher logs, the SDD seat
    sessions, the transcript join for each, the window, and the cycle assignment.

    The window is applied **before** cycles are cut, deliberately: a cycle is a fact about the
    runs in this reading, and a producer outside the window did not open a cycle this reading
    can see. That is what cycle 0 is for.

    The seats' product path is `state.product_path` alone — no new resolver. A reading with no
    state, or a state naming no product path, falls back to the name pattern for every seat,
    which is `read_seats`'s own stated behaviour for `product_path=None`."""
    rows = agent_rows(agents_json_text)
    logs = watch_logs(logs_dir, project, files)

    product_path = Path(state.product_path) if state and state.product_path else None
    seat_reading = read_seats(product_path, project, rows, files)

    runs = runs_from_logs(logs.logs, rows, projects_root, files, keys, telemetry)
    runs += runs_from_seats(
        seat_reading.seats, projects_root, files, keys, telemetry, evidence=seat_reading.evidence
    )
    runs = with_cycles(within(runs, since=since, until=until))

    return Reading(
        project=project,
        runs=runs,
        coverage=coverage(runs, logs),
        keys=keys,
        state=state,
        since=since,
        until=until,
        telemetry=telemetry,
        unmatched_recorded_names=seat_reading.unmatched_recorded_names,
    )


# ── Task 5b — the two renderings, and neither one totals ──


def _stamp(epoch_ms: int | None) -> str:
    if epoch_ms is None:
        return "n/a"
    return (
        datetime.fromtimestamp(epoch_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%MZ")
    )


def _spend_lines(spend: dict[str, telemetry_gateway.Spend], indent: str) -> list[str]:
    """One line per model, five classes apart, `thinking` beside `output` and never inside
    it."""
    lines = []
    for model, amount in spend.items():
        thinking = "" if amount.thinking is None else f" thinking={amount.thinking}"
        lines.append(
            f"{indent}{model}: input={amount.input} output={amount.output}{thinking} "
            f"cache_read={amount.cache_read} cache_write_1h={amount.cache_write_1h} "
            f"cache_write_5m={amount.cache_write_5m}"
        )
    return lines


def _coverage_lines(cov: Coverage) -> list[str]:
    lines = [
        f"Coverage: {cov.chain_driven_runs} chain-driven run(s) + {cov.seat_runs} seat "
        f"session(s) read.",
        f"  Transcripts: {cov.transcripts_read} read / {cov.transcripts_missing} missing / "
        f"{cov.no_session} with no session to join.",
        f"  Watcher logs seen for this project: {cov.logs_seen}; "
        f"{cov.logs_not_chain_driven} carried no on_complete: line and are out of the "
        f"population.",
    ]
    if cov.logs_unparsed:
        lines.append("  Log names this reader could not parse: " + ", ".join(cov.logs_unparsed))
    if cov.unattributed:
        lines.append("  Runs attributed to no document: " + ", ".join(cov.unattributed))
    if cov.unplaced:
        lines.append("  Runs no cycle could be assigned to: " + ", ".join(cov.unplaced))
    return lines


def _document_label(row) -> str:
    if row.key is None:
        return "(unattributed)"
    documents = ", ".join(row.documents)
    return f"{row.key} ({documents})" if documents and documents != row.key else row.key


def seat_sourcing_line(runs: tuple[ChainRun, ...]) -> str:
    """One sentence naming how *this reading's own* seat runs were found — record, the name
    pattern's convention, or a mix — as distinct from `SEAT_POPULATION_NOTE`, which states the
    mechanism in general and is the same on every reading. Empty when the reading holds no seat
    run at all; the caller decides whether to print it."""
    seat_runs = [run for run in runs if run.kind is Kind.SEAT]
    if not seat_runs:
        return ""
    record_read = any(run.seat_evidence is SeatEvidence.RECORD for run in seat_runs)
    fell_back = any(run.seat_evidence is SeatEvidence.CONVENTION for run in seat_runs)
    if record_read and not fell_back:
        return "This reading's seats are stated by each run's own record."
    if record_read and fell_back:
        return (
            "This reading's seats are stated by each run's own record, except the run(s) whose "
            "record did not parse, which the name-pattern convention found instead."
        )
    return "This reading's seats were all found by the name-pattern convention."


def _population_sentences(runs: tuple[ChainRun, ...]) -> list[str]:
    """The population sentences both renderings open with — the two general notes, then this
    reading's own seat sourcing when it holds a seat run. One list, so the table and the JSON
    cannot say different things about where the seats came from."""
    sentences = [POPULATION_NOTE, SEAT_POPULATION_NOTE]
    sourcing = seat_sourcing_line(runs)
    if sourcing:
        sentences.append(sourcing)
    return sentences


def render(reading: Reading) -> str:
    """The human report — the two populations and the cycle rule in the reader's own words,
    then one section per document and one line per cycle, then coverage. Every number is one
    of the five classes or a plain count; none is their sum."""
    lines = _population_sentences(reading.runs)
    if reading.unmatched_recorded_names:
        lines.append(
            "Seat names a run record states that no agent session answered to: "
            + ", ".join(reading.unmatched_recorded_names)
        )
    lines.append(CYCLE_NOTE)
    lines.append("")

    if reading.state is not None:
        lines.append(
            f"Chain: {reading.state.chain_name} / project {reading.state.project} — "
            f"ended: {reading.state.ended} ({reading.state.ended_reason})"
        )
        if reading.state.spine:
            lines.append("  Spine: " + ", ".join(reading.state.spine))
            missing = spine_without_runs(reading.state.spine, reading.runs, reading.keys)
            if missing:
                lines.append("  Spine documents with no run in this reading: " + ", ".join(missing))
        lines.append("")

    window = (
        f"Window: {_stamp(reading.since)} to {_stamp(reading.until)} "
        "(a run with no start time is never windowed out)"
    )
    lines.append(window)
    lines.extend(_coverage_lines(reading.coverage))
    lines.append("")

    documents = by_document(reading.runs, reading.keys, reading.telemetry)
    if not documents:
        lines.append("No runs read.")
        return "\n".join(lines).rstrip() + "\n"

    cycles = by_cycle(reading.runs, reading.keys, reading.telemetry)
    for row in documents:
        lines.append(
            f"{_document_label(row)}  cycles={row.cycles}  runs={row.runs} "
            f"(producer={row.producers} self-answer={row.self_answers} seat={row.seats})"
        )
        lines.extend(_spend_lines(row.spend, "    "))
        for cycle in (c for c in cycles if c.key == row.key):
            label = "cycle 0 (opened before this reading)" if cycle.cycle == 0 else (
                "cycle (unplaced)" if cycle.cycle is None else f"cycle {cycle.cycle}"
            )
            lines.append(
                f"    {label}  started={_stamp(cycle.started_at)}  runs={cycle.runs} "
                f"(producer={cycle.producers} self-answer={cycle.self_answers} "
                f"seat={cycle.seats})"
            )
            lines.extend(_spend_lines(cycle.spend, "      "))
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _spend_payload(spend: dict[str, telemetry_gateway.Spend]) -> dict:
    return {
        model: {
            "input": amount.input,
            "output": amount.output,
            "thinking": amount.thinking,
            "cache_read": amount.cache_read,
            "cache_write_1h": amount.cache_write_1h,
            "cache_write_5m": amount.cache_write_5m,
        }
        for model, amount in spend.items()
    }


def render_json(reading: Reading) -> str:
    """The machine rows — the same population sentences, cycle rule, coverage and figures the
    table carries, plus the per-run rows the table summarises."""
    payload = {
        "populations": _population_sentences(reading.runs),
        "cycle_rule": CYCLE_NOTE,
        "unmatched_recorded_names": list(reading.unmatched_recorded_names),
        "project": reading.project,
        "window": {"since": reading.since, "until": reading.until},
        "chain": None
        if reading.state is None
        else {
            "chain_name": reading.state.chain_name,
            "project": reading.state.project,
            "product_path": reading.state.product_path,
            "spine": list(reading.state.spine),
            "ended": reading.state.ended,
            "ended_reason": reading.state.ended_reason,
            "spine_without_runs": list(
                spine_without_runs(reading.state.spine, reading.runs, reading.keys)
            ),
        },
        "coverage": {
            "chain_driven_runs": reading.coverage.chain_driven_runs,
            "seat_runs": reading.coverage.seat_runs,
            "transcripts_read": reading.coverage.transcripts_read,
            "transcripts_missing": reading.coverage.transcripts_missing,
            "no_session": reading.coverage.no_session,
            "logs_seen": reading.coverage.logs_seen,
            "logs_not_chain_driven": reading.coverage.logs_not_chain_driven,
            "logs_unparsed": list(reading.coverage.logs_unparsed),
            "unattributed": list(reading.coverage.unattributed),
            "unplaced": list(reading.coverage.unplaced),
        },
        "documents": [
            {
                "key": row.key,
                "documents": list(row.documents),
                "cycles": row.cycles,
                "runs": row.runs,
                "producers": row.producers,
                "self_answers": row.self_answers,
                "seats": row.seats,
                "spend": _spend_payload(row.spend),
            }
            for row in by_document(reading.runs, reading.keys, reading.telemetry)
        ],
        "cycles": [
            {
                "key": row.key,
                "cycle": row.cycle,
                "started_at": row.started_at,
                "runs": row.runs,
                "producers": row.producers,
                "self_answers": row.self_answers,
                "seats": row.seats,
                "spend": _spend_payload(row.spend),
            }
            for row in by_cycle(reading.runs, reading.keys, reading.telemetry)
        ],
        "runs": [
            {
                "label": run.label,
                "source": run.source.value,
                "kind": run.kind.value,
                "document_key": run.document_key,
                "cycle": run.cycle,
                "seat": run.seat,
                "runner_run": run.runner_run,
                "seat_evidence": run.seat_evidence.value if run.seat_evidence else None,
                "session_id": run.session_id,
                "started_at": run.started_at,
                "transcript": run.transcript.value,
                "span_seconds": run_span(run, reading.telemetry),
                "spend": _spend_payload(run_spend(run, reading.telemetry)),
            }
            for run in reading.runs
        ],
    }
    return json.dumps(payload, indent=2)


# ── The ports ───────────────────────────
#
# Every world-reach this reader makes arrives through one of these two, and neither is
# constructed anywhere but `build_reader()`.


class Files:
    """Every filesystem touch this reader makes. It **composes** the gateway's transcript file
    port rather than restating it: `find_transcripts` and `read_lines` are exactly the reaches
    the gateway's `find_transcript` and `read_usage` take through their own `files` argument,
    so both forward to `transcripts` and this reader hands itself straight to both. Only the
    reaches that port does not have — a logs directory, a whole file read as text, and the run
    records — are written here."""

    def __init__(self, transcripts: Any):
        self._transcripts = transcripts

    def find_transcripts(self, session_id: str, projects_root: Path) -> list[Path]:
        """Every transcript of `session_id` under `projects_root`, as the transcript port finds
        them."""
        return self._transcripts.find_transcripts(session_id, projects_root)

    def read_lines(self, path: Path) -> list[str] | None:
        """`path`'s lines, or `None` when it cannot be read, as the transcript port reads
        them."""
        return self._transcripts.read_lines(path)

    def find_watch_logs(self, logs_dir: Path, project: str) -> list[Path]:
        """Every `watch-<project>-*.log` under `logs_dir`, in no particular order — a
        prefilter, not the population: `watch_log_name` is what decides whether a name is
        really this project's. A nonexistent `logs_dir` yields no matches rather than raising,
        the same answer `Path.glob` gives for one that exists and holds none."""
        return list(logs_dir.glob(f"watch-{project}-*.log"))

    def read_text(self, path: Path) -> str | None:
        """`path`'s whole text, or `None` when it cannot be read at all — a watcher log is
        prose read whole, never line-by-line and never as JSON."""
        try:
            return path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None

    def find_run_records(self, product_path: Path) -> list[Path]:
        """Every `run-*.md` under `<product_path>/docs/trail/sdd/`, in no particular order — a
        prefilter, not the population: `product_run_records` decides which names are really a
        run record and what order they read in. A `product_path` with no `docs/trail/sdd/`
        yields no matches rather than raising, the same answer `Path.glob` gives for one that
        exists and holds none."""
        return list((product_path / "docs" / "trail" / "sdd").glob("run-*.md"))


# ── The composition root: the only place a concrete implementation is constructed ────


@dataclass(frozen=True)
class Reader:
    """The reader's whole environment: the two ports it reaches the world through, the
    projects root resolved to a concrete `Path` — the one environment reach `build_reader`
    performs itself — and the telemetry collaborator every spend and usage read goes
    through."""

    files: Files
    processes: Any
    projects_root: Path
    telemetry: telemetry_gateway.Telemetry


def build_reader(
    projects_root: Path | None = None, telemetry: telemetry_gateway.Telemetry | None = None
) -> Reader:
    """Wire the real ports. The only place `Files()` is constructed. A `projects_root` of
    `None` resolves to `~/.claude/projects`, here rather than at an argparse default or inside
    a unit's own body. A test passes its own `telemetry`; otherwise the gateway loads the
    package, or raises `TelemetryUnavailable`."""
    default_root = Path.home() / ".claude" / "projects"
    wired = telemetry_gateway.build_telemetry() if telemetry is None else telemetry
    return Reader(
        files=Files(wired.files),
        processes=wired.processes,
        projects_root=projects_root if projects_root is not None else default_root,
        telemetry=wired,
    )


# ── Task 5c — the CLI ────────────────────────────


def _agents_json_text(
    agents_json_path: Path | None, files: Files, processes: Any
) -> str:
    """The `claude agents --json --all` text this run reads: a saved file when one is given —
    the seam a test uses to shell out to nothing — else the live command. A missing saved file
    is a usage error a caller can act on, so it is `SystemExit` rather than a silent empty
    reading."""
    if agents_json_path is not None:
        lines = files.read_lines(agents_json_path)
        if lines is None:
            raise SystemExit(f"error: could not read {agents_json_path}")
        return "\n".join(lines)
    return processes.run(["claude", "agents", "--json", "--all"])


def main(
    argv: list[str] | None = None, *, telemetry: telemetry_gateway.Telemetry | None = None
) -> int:
    parser = argparse.ArgumentParser(
        prog="chain_usage.py",
        description=(
            "What a chain walk spent, per document and per cycle. Two populations, stated "
            "apart: the watcher logs carrying an `on_complete:` line, and the SDD runner's "
            "seat sessions, which leave no log at all. No price model and no currency — this "
            "counts, it does not price — and the five usage classes are never summed."
        ),
    )
    parser.add_argument(
        "--state",
        type=Path,
        default=None,
        help=(
            "a chain state file (system/logs/chain-<project>-state.json); supplies the "
            "project and the logs directory when those are not given, and adds the chain's "
            "name, spine and end state to the report"
        ),
    )
    parser.add_argument(
        "--logs-dir",
        type=Path,
        default=None,
        help="the walking instance's system/logs/ (default: derived from --state)",
    )
    parser.add_argument(
        "--project", default=None, help="the project walked (default: read from --state)"
    )
    parser.add_argument(
        "--agents-json",
        type=Path,
        default=None,
        help="path to saved `claude agents --json --all` output (default: shell out to it)",
    )
    parser.add_argument(
        "--projects-root",
        type=Path,
        default=None,
        help="root holding <slug>/<sessionId>.jsonl transcripts (default: ~/.claude/projects)",
    )
    parser.add_argument(
        "--since", default=None, help="read only runs started on or after this UTC date "
        "(YYYY-MM-DD)"
    )
    parser.add_argument(
        "--until", default=None, help="read only runs started before this UTC date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--json", action="store_true", help="emit the reading as JSON instead of the report"
    )
    args = parser.parse_args(argv)

    try:
        reader = build_reader(args.projects_root, telemetry)
    except telemetry_gateway.TelemetryUnavailable:
        print(
            telemetry_gateway.dependency_message(telemetry_gateway.ReaderName.CHAIN_USAGE),
            file=sys.stderr,
        )
        return 1

    state = chain_state(args.state, reader.files) if args.state is not None else None
    if args.state is not None and state is None:
        print(f"error: could not read a chain state from {args.state}", file=sys.stderr)
        return 1

    project = args.project or (state.project if state else None)
    if not project:
        print(
            "error: --project is required (or a --state file that names one)", file=sys.stderr
        )
        return 1

    logs_dir = args.logs_dir or logs_dir_for(state)
    if logs_dir is None:
        print(
            "error: --logs-dir is required (or a --state file naming an instance_root)",
            file=sys.stderr,
        )
        return 1

    try:
        since = parse_day(args.since) if args.since else None
        until = parse_day(args.until) if args.until else None
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    text = _agents_json_text(args.agents_json, reader.files, reader.processes)
    try:
        reading = read_walk(
            logs_dir=logs_dir,
            project=project,
            agents_json_text=text,
            projects_root=reader.projects_root,
            files=reader.files,
            keys=document_keys(chain.DOCUMENT_REGISTRY),
            since=since,
            until=until,
            telemetry=reader.telemetry,
            state=state,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(render_json(reading))
    else:
        print(render(reading), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
