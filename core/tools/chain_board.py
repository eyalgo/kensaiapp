#!/usr/bin/env python3
"""chain_board.py — one instance's chain walks as two lists: what waits on the owner, what runs.

WHY THIS EXISTS
    The owner learned what waited on them by reading `system/logs/*-state.json` by hand, or by
    waiting for a message. Three engines write those files (`chain.py`, `chain_development.py`,
    `build_idea.py`), each in its own shape, and the kensaiapp side pane
    (`core/tools/kensaiapp-panel/`) needs one reading of all three. A parser inside the pane
    would be a second copy of the engines' shapes, so the pane runs this and draws what it prints.

WHAT IT DECIDES
    A walk that ended on a quiet end is in neither list. A walk with any other end — an end this
    reader has never seen included — waits on the owner. A walk with no end is running, unless it
    waits on launches and every one of them is gone by `walk_stop.launch_state`: nothing will
    finish that walk, so it waits on the owner with the status `gone`. A build-idea walk that
    ended on the owner's act is in neither list once a chain started after it ends by resuming
    that project's build-idea: the owner has acted, and that chain is the walk. A build-idea walk
    whose report sits in a seed the project has since dropped is in neither list either: what
    the report owed went to `nemawashi/drop/` with the seed. A development walk
    that ended on any end but a quiet one is in neither list once its change unit is sealed or
    dropped (its folder is in `journey/tobiishi/trail/` or `drop/`), or once a development walk
    started after it over the same project and change key: `chain-development` resumes a halted
    `chain-change` walk in a state file of its own, so the later walk is the one to read, and if
    it stops too it waits on the owner as its own row. The unit's folder is what outlasts the
    later walk, whose state file the next change overwrites. A development walk that halted
    before its change unit existed (it records no change key) has no unit to seal and no key to
    resume, so it is in neither list once any walk started after it over the same project, as a
    definition walk is. A definition walk that ended on any
    end but a quiet one or `left_for_the_owner` is in neither list once any walk started after it
    over the same project: `chain.py` keeps one state file per project and records no change, so
    the later walk on the project is the owner's act. `left_for_the_owner` stays, because a
    signature is owed whatever ran next, and `chain-change` starts its change walk on that end by
    itself. Every other status and reason is the engine's own; this module adds no words for a
    person to read.

    A single skill run writes no state file. The `skill` launcher, started by no engine, leaves a
    run record beside the state files (`skill-*.run.json`: the skill, the project, the start and
    the launch's identity file). Its run is running while that launch is live, and in neither list
    otherwise: a single run's end is reported by its own watcher, and no walk waits on it.

    A running walk's row also carries when its current step started: the earliest start among
    the launches it waits on, read from each launch's identity file (`walk_stop`), which records
    the run's process start, or the watcher's where the run's is missing. A launch recorded with
    `started_at` gives that; one recorded before it existed gives its `ps` text read as English in
    the machine's local time, and none where that text does not read. A waiting row, a skill run
    and a walk between launches carry none.

    A running development walk on its implementation step also carries which task of the plan
    the developer run is on, and how many the plan lists, as `chain_development` reads them off
    the change's branch (`DiskReader.current_task`); the reader is handed that reading. Every
    other row carries `0` for both, as does a walk whose plan cannot be read or whose run is past
    its last task.

    The quiet ends are built from the engines' own enums, so a renamed value fails at import
    rather than leaking a walk into the wrong list.

    Each project a row names, with one seed at its seedbed root, also gets its route: the seed's
    checklist as it reads now, each item reached, current, parked (its station sits in
    `shukuba/parked/`) or ahead, and under each the walks opened for it — sealed, dropped or open.
    Which of them a person sees is the pane's call; the reader hands it every one, because a run
    can still be on a walk after its station has closed. The current item is the one the project's
    open station is named for. A walk belongs to the station whose name its opening commit carries on
    its `Shukuba:` line, the only place the record links the two; that history is the second
    collaborator the reader is handed. An open unit whose opening commit names no station — one
    opened by hand carries `Agari:` — is the current station's, because exactly one station is open
    and units open inside it; a sealed or dropped one the history does not link is under no station.
    A history that cannot be read links nothing, so then every open unit is the current station's —
    right whenever, as usual, one unit is open at a time.
    A trailer written before stations were named by their dated stem names the bare slug, and
    matches by it. A refine that re-cuts the checklist changes the route on the next read.

READ-ONLY
    Nothing here opens a file for writing, and no engine is changed. The engines and `walk_stop`
    are imported from this file's own folder, so a satellite is read with the core it binds.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable

import build_idea
import chain
import chain_development
import journey_status
import walk_stop

__version__ = "1.13.0"

QUIET_ENDS = frozenset(end.value for end in (
    chain_development.Ended.SEALED, chain_development.Ended.STOPPED,
    build_idea.QueueEnd.STOPPED, build_idea.QueueEnd.DONE,
    build_idea.QueueEnd.HANDED_OFF, build_idea.QueueEnd.RETIRE_LAUNCHED,
    chain.CycleEnd.SETTLED, chain.CycleEnd.EMPTY_RUN,
))

STATE_FILE_PATTERN = "*-state.json"
SKILL_RUN_PATTERN = "skill-*.run.json"
SKILL_LAUNCHER = "skill"
BUILD_IDEA_LAUNCHER = "build-idea"
CHAIN_LAUNCHER_PREFIX = "chain-"
DEFAULT_DEVELOPMENT_CHAIN = "development"
DEFAULT_PRODUCT_CHAIN = "product"
STATION_FOLDERS = ("", "parked", "trail")
CHANGE_FOLDERS = (("", "open"), ("trail", "sealed"), ("drop", "dropped"))
SEED_FOLDERS = ("", "trail", "drop")
CLOSED_CHANGE_FOLDERS = ("trail", "drop")
HEADING_PREFIX = "# "
HEADING_SEPARATOR = " — "
NO_START_TIME = float("-inf")
# The step whose runs work through a plan's tasks, named by the skill it runs so a renamed step
# fails at import.
IMPLEMENTATION_STEP = next(step.id for step in chain_development.DEVELOPMENT_STEPS
                           if step.skill == "development-implementation")

_LAUNCHER_PATH = re.compile(r"[^\s`'\"(]*core/launchers/([\w-]+)/launcher\.sh")
_MARKDOWN_PATH = re.compile(r"[^\s`'\"(),;]+\.md\b")
# Where a path may start in a reason: at its start, or after a space, a quote or a bracket.
_PATH_START = r"(?<![^\s`'\"(])"
_DATE_PREFIX = re.compile(r"^\d{4}-\d{2}-\d{2}_")
_ON_END_BUILD_IDEA = re.compile(r"core/launchers/build-idea/launcher\.sh\s+([\w.-]+)")
# A seed's checklist item: its indent, its tick, and its text up to the ` — ` that opens the
# description. The tick is read the way `journey_status` counts it.
_CHECKLIST_ITEM = re.compile(r"^([ \t]*)- \[([ x])\] (.+?)(?: — |$)", re.MULTILINE)
_ITEM_NUMBER = re.compile(r"^[\d↳]+\.\s*")
_SHUKUBA_TRAILER = re.compile(r"^Shukuba: (\S+)", re.MULTILINE)
RECORD_SEPARATOR = "\x1e"
INDENT_PER_DEPTH = 2
HISTORY_TIMEOUT_SECONDS = 10

LaunchState = Callable[[str], walk_stop.LaunchState]
# An identity path in, when that launch's run started out (ISO 8601), or "" where none is recorded.
LaunchStart = Callable[[str], str]
# Per change key, the station its opening commit names, for one project of one instance.
OpenedStations = Callable[[Path, str], dict[str, str]]
# The instance root, a project, a change key and the walk's product path in; the developer run's
# `(place, count)` among its plan's tasks out, or `None` where none is read.
TaskProgress = Callable[[Path, str, str, str], tuple[int, int] | None]


class WalkKind(Enum):
    BUILD_IDEA = "build_idea.py"
    CHAIN_DEVELOPMENT = "chain_development.py"
    CHAIN = "chain.py"


# The key each engine's state holds and the others' do not. A project's name may begin `change-`,
# so a walk's kind is read from what it holds and never from the file's name.
_KIND_MARKERS = (("rows", WalkKind.BUILD_IDEA), ("audits", WalkKind.CHAIN_DEVELOPMENT),
                 ("spine", WalkKind.CHAIN))


@dataclass(frozen=True)
class Row:
    launcher: str
    project: str
    seed: str
    station: str
    walk: str
    key: str
    step: str
    status: str
    reason: str
    started_at: str
    step_started_at: str
    task: int
    tasks: int


class StopState(str, Enum):
    REACHED = "reached"
    CURRENT = "current"
    PARKED = "parked"
    AHEAD = "ahead"


@dataclass(frozen=True)
class Walk:
    name: str
    key: str
    state: str


@dataclass(frozen=True)
class Stop:
    name: str
    state: StopState
    depth: int
    walks: list[Walk]


@dataclass(frozen=True)
class Route:
    project: str
    seed: str
    stations: list[Stop]


@dataclass(frozen=True)
class Board:
    instance: str
    waiting: list[Row]
    running: list[Row]
    routes: list[Route]


@dataclass(frozen=True)
class _Verdict:
    waiting: bool
    status: str
    reason: str


def find_instance_root(start: Path) -> Path | None:
    """The nearest directory at or above `start` holding `kensaiapp.md` and `system/logs/`, else
    the nearest holding `kensaiapp.md`.

    A worktree has no `system/logs/` (it is git-ignored), so a session in one reads its main
    checkout. A fresh clone has none either, until a launcher first writes there; it is still an
    instance, with nothing to show."""
    folders = (start, *start.parents)
    for folder in folders:
        if (folder / "kensaiapp.md").is_file() and (folder / "system" / "logs").is_dir():
            return folder
    return next((folder for folder in folders if (folder / "kensaiapp.md").is_file()), None)


def read_board(root: Path, launch_state: LaunchState, opened_stations: OpenedStations,
               launch_start: LaunchStart, task_progress: TaskProgress) -> Board:
    waiting: list[Row] = []
    running: list[Row] = []
    walks = []
    for path in sorted((root / "system" / "logs").glob(STATE_FILE_PATTERN)):
        state = _read_state(path)
        kind = _walk_kind(state)
        if state is not None and kind is not None:
            walks.append((kind, state))
    handed_back = _handed_back_to_build_idea(walks)
    resumed = _development_starts(walks)
    project_starts = _project_starts(walks)
    for kind, state in walks:
        if kind is WalkKind.BUILD_IDEA and (_is_superseded(state, handed_back)
                                            or _is_in_a_dropped_seed(root, state)):
            continue
        if kind is WalkKind.CHAIN_DEVELOPMENT and _is_taken_up(root, state, resumed,
                                                               project_starts):
            continue
        if kind is WalkKind.CHAIN and _is_moved_past(state, project_starts):
            continue
        verdict = _judge(root, state, launch_state)
        if verdict is None:
            continue
        project = str(state.get("project") or "")
        task, tasks = (0, 0) if verdict.waiting else _task_progress(root, kind, state,
                                                                    task_progress)
        row = Row(launcher=_launcher_name(kind, state), project=project,
                  seed=_seed(root, project, str(state.get("seed") or "")),
                  station=_station(root, project, str(state.get("station") or "")),
                  walk=_walk(state), key=str(state.get("key") or ""),
                  step=_step(kind, state), status=verdict.status,
                  reason=verdict.reason, started_at=str(state.get("started_at") or ""),
                  step_started_at="" if verdict.waiting else _step_start(state, launch_start),
                  task=task, tasks=tasks)
        (waiting if verdict.waiting else running).append(row)
    running.extend(_live_skill_runs(root, launch_state))
    waiting.sort(key=_newest_first, reverse=True)
    running.sort(key=_newest_first, reverse=True)
    projects = dict.fromkeys(row.project for row in waiting + running if row.project)
    routes = [route for route in (_route(root, project, opened_stations) for project in projects)
              if route is not None]
    return Board(instance=root.name, waiting=waiting, running=running, routes=routes)


def _handed_back_to_build_idea(walks: list[tuple[WalkKind, dict]]) -> dict[str, list[float]]:
    """Per project, the start of each chain walk whose end resumes that project's build-idea."""
    handed_back: dict[str, list[float]] = {}
    for kind, state in walks:
        if kind is WalkKind.BUILD_IDEA:
            continue
        resumed = _ON_END_BUILD_IDEA.search(str(state.get("on_end") or ""))
        if resumed:
            handed_back.setdefault(resumed.group(1), []).append(_start_time(state))
    return handed_back


def _is_superseded(state: dict, handed_back: dict[str, list[float]]) -> bool:
    """A build-idea walk that ended on the owner's act, and a chain started after it hands back to
    it: the owner has acted, and the walk resumes when that chain ends."""
    if state.get("ended") != build_idea.QueueEnd.OWNER_OWED.value:
        return False
    started = _start_time(state)
    return any(later > started for later in handed_back.get(str(state.get("project") or ""), []))


def _is_in_a_dropped_seed(root: Path, state: dict) -> bool:
    """A build-idea walk whose report has moved, inside its seed folder, to the project's
    `nemawashi/drop/`: the moves that report named went with the seed, and this walk waits on
    nobody. The report file itself is looked for, so a dropped seed that only shares the folder
    name hides nothing."""
    project = str(state.get("project") or "")
    report = Path(str(state.get("report") or ""))
    if not project or not report.name:
        return False
    dropped = _journey(root, project) / "nemawashi" / "drop" / report.parent.name / report.name
    return dropped.is_file()


def _development_starts(walks: list[tuple[WalkKind, dict]]) -> dict[tuple[str, str], list[float]]:
    """Per project and change key, the start of each development walk over it."""
    starts: dict[tuple[str, str], list[float]] = {}
    for kind, state in walks:
        if kind is WalkKind.CHAIN_DEVELOPMENT and state.get("key"):
            starts.setdefault(_change(state), []).append(_start_time(state))
    return starts


def _is_taken_up(root: Path, state: dict, starts: dict[tuple[str, str], list[float]],
                 project_starts: dict[str, list[float]]) -> bool:
    """A development walk that stopped short, over a change that is sealed or dropped, or that a
    development walk started after it took up: this one waits on nobody. One that halted before
    its change existed is taken up by any walk started after it over its project."""
    ended = state.get("ended")
    if ended is None or ended in QUIET_ENDS:
        return False
    if not state.get("key"):
        return _is_started_after(state, project_starts)
    project, key = _change(state)
    tobiishi = root / "system" / "projects" / project / "journey" / "tobiishi"
    if project and any((tobiishi / folder / key).is_dir() for folder in CLOSED_CHANGE_FOLDERS):
        return True
    started = _start_time(state)
    return any(later > started for later in starts.get((project, key), []))


def _project_starts(walks: list[tuple[WalkKind, dict]]) -> dict[str, list[float]]:
    """Per project, the start of each walk over it, of any kind."""
    starts: dict[str, list[float]] = {}
    for _, state in walks:
        starts.setdefault(str(state.get("project") or ""), []).append(_start_time(state))
    return starts


def _is_moved_past(state: dict, starts: dict[str, list[float]]) -> bool:
    """A definition walk that stopped short with no signature owed, and a walk started after it
    over the same project: the owner has moved on, and this one waits on nobody."""
    ended = state.get("ended")
    if ended is None or ended in QUIET_ENDS or ended == chain.CycleEnd.LEFT_FOR_THE_OWNER.value:
        return False
    return _is_started_after(state, starts)


def _is_started_after(state: dict, starts: dict[str, list[float]]) -> bool:
    """Whether a walk started after this one over the same project."""
    project = str(state.get("project") or "")
    if not project:
        return False
    started = _start_time(state)
    return any(later > started for later in starts.get(project, []))


def _change(state: dict) -> tuple[str, str]:
    return str(state.get("project") or ""), str(state.get("key"))


def _live_skill_runs(root: Path, launch_state: LaunchState) -> list[Row]:
    rows = []
    for path in sorted((root / "system" / "logs").glob(SKILL_RUN_PATTERN)):
        record = _read_state(path)
        if record is None or not record.get("skill") or not record.get("identity"):
            continue
        if launch_state(str(record["identity"])) is not walk_stop.LaunchState.LIVE:
            continue
        project = str(record.get("project") or "")
        rows.append(Row(launcher=SKILL_LAUNCHER, project=project, seed=_seed(root, project, ""),
                        station=_station(root, project, ""), walk=str(record["skill"]), key="",
                        step="",
                        status="", reason="", started_at=str(record.get("started_at") or ""),
                        step_started_at="", task=0, tasks=0))
    return rows


def _read_state(path: Path) -> dict | None:
    try:
        state = json.loads(path.read_text())
    except (OSError, ValueError):
        return None
    return state if isinstance(state, dict) else None


def _walk_kind(state: dict | None) -> WalkKind | None:
    if state is None:
        return None
    for marker, kind in _KIND_MARKERS:
        if marker in state:
            return kind
    return None


def _launcher_name(kind: WalkKind, state: dict) -> str:
    """The name each engine already gives its own stop command."""
    if kind is WalkKind.BUILD_IDEA:
        return BUILD_IDEA_LAUNCHER
    default = (DEFAULT_DEVELOPMENT_CHAIN if kind is WalkKind.CHAIN_DEVELOPMENT
               else DEFAULT_PRODUCT_CHAIN)
    return CHAIN_LAUNCHER_PREFIX + (state.get("chain_name") or default)


def _launches(pending: object) -> list[dict]:
    """`chain.py` keeps one launch (a dict holding an `identity`); the other two keep a map."""
    if not isinstance(pending, dict) or not pending:
        return []
    if "identity" in pending:
        return [pending]
    return [entry for entry in pending.values() if isinstance(entry, dict)]


def _judge(root: Path, state: dict, launch_state: LaunchState) -> _Verdict | None:
    """`None` is a quiet walk, which no list holds."""
    ended = state.get("ended")
    if ended is not None:
        if ended in QUIET_ENDS:
            return None
        return _Verdict(True, str(ended), _clean_reason(root, str(state.get("ended_reason") or "")))
    launches = [_launch_state(launch, launch_state) for launch in _launches(state.get("pending"))]
    if launches and all(one is walk_stop.LaunchState.GONE for one in launches):
        return _Verdict(True, walk_stop.LaunchState.GONE.value, "")
    return _Verdict(False, "", "")


def _step_start(state: dict, launch_start: LaunchStart) -> str:
    """The earliest recorded start among the launches the walk waits on, else ""."""
    starts = [start for start in (launch_start(str(launch["identity"]))
                                  for launch in _launches(state.get("pending"))
                                  if launch.get("identity"))
              if _timestamp(start) != NO_START_TIME]
    return min(starts, key=_timestamp, default="")


def _task_progress(root: Path, kind: WalkKind, state: dict,
                   task_progress: TaskProgress) -> tuple[int, int]:
    """The developer run's place among its plan's tasks and their count, for a development walk
    with a launch out on its implementation step; `(0, 0)` for every other walk and where none is
    read. A launch's step is the one its entry records, not its run's name: the chain relaunches a
    developer run that ended with no marker as `implementation-recovery`."""
    pending = state.get("pending")
    key = str(state.get("key") or "")
    if (kind is not WalkKind.CHAIN_DEVELOPMENT or not key
            or not any(launch.get("step") == IMPLEMENTATION_STEP
                       for launch in _launches(pending))):
        return 0, 0
    project = str(state.get("project") or "")
    return task_progress(root, project, key, str(state.get("product_path") or "")) or (0, 0)


def _launch_state(launch: dict, launch_state: LaunchState) -> walk_stop.LaunchState:
    identity = launch.get("identity")
    if not identity:
        return walk_stop.LaunchState.UNRECORDED
    return launch_state(str(identity))


def _journey(root: Path, project: str) -> Path:
    return root / "system" / "projects" / project / "journey"


def _seed(root: Path, project: str, recorded: str) -> str:
    """The recorded seed's own heading wherever it now sits, else the heading of the one seed at
    the project's seedbed root. A root holding none or several names no seed."""
    if not project:
        return ""
    nemawashi = _journey(root, project) / "nemawashi"
    if recorded:
        for folder in SEED_FOLDERS:
            path = nemawashi / folder / Path(recorded).name
            if path.is_file() or path.is_dir():
                heading = _heading(journey_status._seed_text_path(path))
                if heading:
                    return heading
    seeds = journey_status._seed_entries(nemawashi)
    if len(seeds) != 1:
        return ""
    return _heading(journey_status._seed_text_path(seeds[0])) or ""


def _station(root: Path, project: str, recorded: str) -> str:
    """The recorded station's own heading, else the heading of the project's one open station."""
    if not project:
        return ""
    if recorded:
        heading = _station_heading(root, project, recorded)
        if heading:
            return heading
    open_stations = journey_status._md_files(_journey(root, project) / "shukuba")
    if len(open_stations) != 1:
        return ""
    return _heading(open_stations[0]) or ""


def _route(root: Path, project: str, opened_stations: OpenedStations) -> Route | None:
    """The project's one active seed's checklist, read now. No seed, or several, is no route."""
    journey = _journey(root, project)
    seeds = journey_status._seed_entries(journey / "nemawashi")
    if len(seeds) != 1:
        return None
    seed_path = journey_status._seed_text_path(seeds[0])
    try:
        text = seed_path.read_text()
    except OSError:
        return None
    open_stations = journey_status._md_files(journey / "shukuba")
    current = open_stations[0].stem if len(open_stations) == 1 else ""
    parked = {_DATE_PREFIX.sub("", path.stem)
              for path in journey_status._md_files(journey / "shukuba" / "parked")}
    stops = []
    for indent, tick, label in _CHECKLIST_ITEM.findall(text):
        name = label.replace("**", "").strip()
        slug = _ITEM_NUMBER.sub("", name)
        state = StopState.REACHED if tick == "x" else StopState.AHEAD
        if state is StopState.AHEAD and slug in parked:
            state = StopState.PARKED
        if current and slug == _DATE_PREFIX.sub("", current):
            state = StopState.CURRENT
        stops.append(Stop(name=name, state=state, depth=len(indent.expandtabs()) // INDENT_PER_DEPTH,
                          walks=[]))
    if current and not any(stop.state is StopState.CURRENT for stop in stops):
        stops.append(Stop(name=_DATE_PREFIX.sub("", current), state=StopState.CURRENT, depth=0,
                          walks=[]))
    slugs = [_ITEM_NUMBER.sub("", stop.name) for stop in stops]
    current_at = next((at for at, stop in enumerate(stops) if stop.state is StopState.CURRENT), None)
    openings = opened_stations(root, project)
    walks_at: dict[int, list[Walk]] = {at: [] for at in range(len(stops))}
    for walk in _units(journey / "tobiishi"):
        at = _item_opened_for(walk, openings.get(walk.key), slugs, current_at, current)
        if at is not None:
            walks_at[at].append(walk)
    stops = [Stop(stop.name, stop.state, stop.depth, walks_at[at]) for at, stop in enumerate(stops)]
    return Route(project=project, seed=_heading(seed_path) or "", stations=stops)


def _units(tobiishi: Path) -> list[Walk]:
    """Every change unit of the project, open, sealed or dropped, in the order of its key."""
    walks = []
    for folder, state in CHANGE_FOLDERS:
        where = tobiishi / folder
        if not where.is_dir():
            continue
        for unit in where.iterdir():
            if unit.is_dir() and unit.name not in CLOSED_CHANGE_FOLDERS:
                walks.append(Walk(name=_DATE_PREFIX.sub("", unit.name), key=unit.name,
                                  state=state))
    return sorted(walks, key=lambda walk: walk.key)


def _item_opened_for(walk: Walk, opened_for: str | None, slugs: list[str], current_at: int | None,
                     current_stem: str) -> int | None:
    """Which checklist item the unit was opened for, by its place in the checklist; a unit sits
    under one item only. The current item takes a trailer naming its own dated stem, or before
    2026-09-14 its bare slug. A dated trailer naming another stem is a station an earlier walk of
    the route opened under the same slug, so it goes to the first other item of that slug, never
    to the current one. An open unit the history links to no station is the current item's."""
    if opened_for is None:
        return current_at if walk.state == "open" else None
    if current_at is not None and opened_for in (current_stem, slugs[current_at]):
        return current_at
    slug = _DATE_PREFIX.sub("", opened_for)
    return next((at for at, item in enumerate(slugs) if item == slug and at != current_at), None)


def _walk(state: dict) -> str:
    """The change key's words, else the document a definition chain is on."""
    if state.get("key"):
        return _words(str(state["key"]))
    pending = state.get("pending")
    document = pending.get("document") if isinstance(pending, dict) else None
    return str(document or state.get("current_document") or "")


def _step(kind: WalkKind, state: dict) -> str:
    """The step the walk is on: the pending steps' names, the pending rows' moves, or the
    document a definition chain is writing."""
    pending = state.get("pending")
    if kind is WalkKind.CHAIN:
        document = pending.get("document") if isinstance(pending, dict) else None
        return str(document or state.get("current_document") or "")
    if not isinstance(pending, dict):
        return ""
    if kind is WalkKind.CHAIN_DEVELOPMENT:
        return ", ".join(pending)
    moves = {str(row.get("number")): row.get("move") for row in state.get("rows") or []
             if isinstance(row, dict)}
    return ", ".join(str(moves[number]) for number in pending if moves.get(number))


def _station_heading(root: Path, project: str, station: str) -> str | None:
    journey = _journey(root, project) / "shukuba"
    for folder in STATION_FOLDERS:
        path = journey / folder / station
        if path.is_file():
            return _heading(path)
    return None


def _heading(path: Path) -> str | None:
    """The file's first `# ` heading, as it reads after its ` — `."""
    try:
        lines = path.read_text().splitlines()
    except OSError:
        return None
    for line in lines:
        if line.startswith(HEADING_PREFIX):
            return line[len(HEADING_PREFIX):].split(HEADING_SEPARATOR, 1)[-1].strip()
    return None


def _words(name: str) -> str:
    return _DATE_PREFIX.sub("", Path(name).stem if name.endswith(".md") else name).replace("-", " ")


def _clean_reason(root: Path, reason: str) -> str:
    """The reason with no pinned launcher path and no `.md` path in it: a launcher reads as its
    name, and a file as its heading, or as its name in words where it is not found. Any other path
    inside the instance reads from below its project's folder, or from the instance's root."""
    reason = _LAUNCHER_PATH.sub(lambda match: match.group(1), reason)
    reason = _MARKDOWN_PATH.sub(lambda match: _file_in_words(root, match.group(0)), reason)
    projects = re.escape(str(root / "system" / "projects"))
    reason = re.sub(_PATH_START + projects + r"/[^/\s]+/", "", reason)
    return re.sub(_PATH_START + re.escape(str(root)) + "/", "", reason)


def _file_in_words(root: Path, token: str) -> str:
    path = Path(token) if Path(token).is_absolute() else root / token
    if path.is_relative_to(root) and path.is_file():
        heading = _heading(path)
        if heading:
            return heading
    return _words(Path(token).name)


def _newest_first(row: Row) -> float:
    """A sort key for `reverse=True`: the start time, so a row with none falls last."""
    return _timestamp(row.started_at)


def _start_time(state: dict) -> float:
    return _timestamp(str(state.get("started_at") or ""))


def _timestamp(started_at: str) -> float:
    try:
        return datetime.fromisoformat(started_at).timestamp()
    except ValueError:
        return NO_START_TIME


def _as_json(instance: str | None, board: Board | None) -> str:
    waiting = [asdict(row) for row in board.waiting] if board else []
    running = [asdict(row) for row in board.running] if board else []
    routes = [asdict(route) for route in board.routes] if board else []
    return json.dumps({"instance": instance, "waiting": waiting, "running": running,
                       "routes": routes})


def main(argv: list[str] | None = None) -> int:
    """Print the board of the instance at or above the given folder (default: here) as JSON."""
    args = sys.argv[1:] if argv is None else argv
    root = find_instance_root(Path(args[0] if args else ".").resolve())
    if root is None:
        print(_as_json(None, None))
        return 0
    print(_as_json(root.name, read_board(root, build_launch_state(), build_opened_stations(),
                                         build_launch_start(), build_task_progress())))
    return 0


def git_opened_stations(root: Path, project: str) -> dict[str, str]:
    """Per change key, the station named on the `Shukuba:` line of the commit that added the
    unit's `change_request.md` at the tobiishi root. The oldest such commit wins, so a unit's
    later commits never move it. A history that cannot be read links nothing."""
    tobiishi = f"system/projects/{project}/journey/tobiishi/"
    opened = re.compile(rf"^{re.escape(tobiishi)}([^/]+)/change_request\.md$", re.MULTILINE)
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "log", "--diff-filter=A", "--no-renames", "--name-only",
             f"--format={RECORD_SEPARATOR}%B", "--", tobiishi],
            capture_output=True, text=True, timeout=HISTORY_TIMEOUT_SECONDS, check=False)
    except (OSError, subprocess.SubprocessError):
        return {}
    if result.returncode != 0:
        return {}
    stations: dict[str, str] = {}
    for record in reversed(result.stdout.split(RECORD_SEPARATOR)):
        trailer = _SHUKUBA_TRAILER.search(record)
        if trailer is None:
            continue
        for key in opened.findall(record):
            stations.setdefault(key, trailer.group(1))
    return stations


def development_task(reader: chain_development.DiskReader, root: Path, project: str, key: str,
                     product_path: str) -> tuple[int, int] | None:
    """The developer run's place among its plan's tasks and their count, read off the change's
    branch by the chain's own reader. A git that cannot be run or read reads no task, so the
    board is still printed."""
    change = chain_development.ChangeLayout(str(root), project, key)
    try:
        return reader.current_task(change, product_path)
    except (OSError, subprocess.SubprocessError, UnicodeDecodeError):
        return None


def launch_started_at(files: walk_stop.DiskFiles, identity: str) -> str:
    """When the launch's run started, else its watcher, as ISO 8601: the recorded `started_at`,
    else, for a file written before it, the `ps -o lstart=` text read as the machine's local time."""
    recorded = walk_stop.read_identity(files, identity)
    if recorded is None:
        return ""
    for process in (recorded.run, recorded.watcher):
        if process is None:
            continue
        if process.started_at and _timestamp(process.started_at) != NO_START_TIME:
            return process.started_at
        if process.start:
            try:
                return datetime.strptime(" ".join(process.start.split()),
                                         walk_stop.LSTART_FORMAT).astimezone().isoformat()
            except ValueError:
                continue
    return ""


# The composition root: the only place the real filesystem, process table and git history are
# constructed.
def build_launch_state() -> LaunchState:
    files, table = walk_stop.DiskFiles(), walk_stop.ProcessTable()
    return lambda identity: walk_stop.launch_state(files, table, identity)


def build_opened_stations() -> OpenedStations:
    return git_opened_stations


def build_launch_start() -> LaunchStart:
    files = walk_stop.DiskFiles()
    return lambda identity: launch_started_at(files, identity)


def build_task_progress() -> TaskProgress:
    reader = chain_development.DiskReader(files=chain.Files(), git=chain_development.Git())
    return lambda root, project, key, product_path: development_task(reader, root, project, key,
                                                                     product_path)


if __name__ == "__main__":
    sys.exit(main())
