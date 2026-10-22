"""Tests for chain_board.py — one instance's chain walks as WAITING ON YOU and RUNNING NOW.

Every case reads real files under `tmp_path`: an instance root holds `kensaiapp.md` and
`system/logs/*-state.json` in the three engines' shapes, and station and seed files where a
case needs them. The one collaborator the reader is handed, `launch_state`, is a fake that answers from a
dict and records what it was asked. Every project, instance and station name here is invented.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

import chain_board
from walk_stop import LaunchState

STARTED = "2026-03-01T10:00:00+00:00"
ROW_KEYS = {"launcher", "project", "seed", "station", "walk", "key", "step", "status", "reason",
            "started_at"}


class FakeLaunches:
    """`launch_state` as the reader is handed it: an identity path in, a `LaunchState` out."""

    def __init__(self, states: dict[str, LaunchState] | None = None) -> None:
        self.states = dict(states or {})
        self.asked: list[str] = []

    def __call__(self, identity: str) -> LaunchState:
        self.asked.append(identity)
        return self.states[identity]


class FakeOpenings:
    """The history the reader is handed: per project, change key to the station it was opened
    for. Records which projects it was asked about."""

    def __init__(self, stations: dict[str, str] | None = None) -> None:
        self.stations = dict(stations or {})
        self.asked: list[str] = []

    def __call__(self, root: Path, project: str) -> dict[str, str]:
        self.asked.append(project)
        return dict(self.stations)


def make_instance(base: Path, name: str) -> Path:
    root = base / name
    (root / "system" / "logs").mkdir(parents=True)
    (root / "kensaiapp.md").write_text("# an instance\n")
    return root


def write_state(root: Path, file_name: str, state: dict) -> None:
    (root / "system" / "logs" / file_name).write_text(json.dumps(state))


def build_idea_walk(project: str = "widgets", **fields) -> dict:
    return {"rows": [], "project": project, "station": "", "key": "", "ended": None,
            "ended_reason": "", "pending": {}, "started_at": STARTED, **fields}


def development_walk(project: str = "widgets", chain_name: str = "change", **fields) -> dict:
    return {"audits": {}, "chain_name": chain_name, "project": project, "key": "", "ended": None,
            "ended_reason": "", "pending": {}, "started_at": STARTED, **fields}


def product_walk(project: str = "widgets", chain_name: str = "product", **fields) -> dict:
    return {"spine": [], "chain_name": chain_name, "project": project, "current_document": "",
            "ended": None, "ended_reason": "", "pending": {}, "started_at": STARTED, **fields}


def one_launch(identity: str) -> dict:
    return {"identity": identity, "kind": "producer"}


def waiting_rows(root: Path, launches: FakeLaunches | None = None) -> list[chain_board.Row]:
    return chain_board.read_board(root, launches or FakeLaunches(), FakeOpenings()).waiting


def running_rows(root: Path, launches: FakeLaunches | None = None) -> list[chain_board.Row]:
    return chain_board.read_board(root, launches or FakeLaunches(), FakeOpenings()).running


def write_station(root: Path, project: str, folder: str, station: str, heading: str) -> None:
    where = root / "system" / "projects" / project / "journey" / "shukuba" / folder
    where.mkdir(parents=True, exist_ok=True)
    (where / station).write_text(f"# {heading}\n\nbody\n")


def test_reading_one_instance_returns_no_row_of_another(tmp_path):
    alpha = make_instance(tmp_path, "alpha")
    beta = make_instance(tmp_path, "beta")
    write_state(alpha, "build-idea-alpha-proj-state.json",
                build_idea_walk("alpha-proj", ended="halted", ended_reason="stuck"))
    write_state(alpha, "chain-change-alpha-proj-state.json", development_walk("alpha-proj"))
    write_state(beta, "build-idea-beta-proj-state.json",
                build_idea_walk("beta-proj", ended="halted", ended_reason="stuck"))
    write_state(beta, "chain-change-beta-proj-state.json", development_walk("beta-proj"))

    first = chain_board.read_board(alpha, FakeLaunches(), FakeOpenings())
    second = chain_board.read_board(beta, FakeLaunches(), FakeOpenings())

    assert [row.project for row in first.waiting + first.running] == ["alpha-proj", "alpha-proj"]
    assert [row.project for row in second.waiting + second.running] == ["beta-proj", "beta-proj"]
    assert (first.instance, second.instance) == ("alpha", "beta")


@pytest.mark.parametrize("builder, end", [
    (development_walk, "sealed"), (development_walk, "stopped"),
    (build_idea_walk, "stopped"), (build_idea_walk, "done"),
    (build_idea_walk, "handed-off"), (build_idea_walk, "retire-launched"),
    (product_walk, "settled"), (product_walk, "empty_run"),
])
def test_every_quiet_end_lands_in_neither_list(tmp_path, builder, end):
    root = make_instance(tmp_path, "inst")
    write_state(root, "walk-state.json", builder(ended=end, ended_reason="over"))

    board = chain_board.read_board(root, FakeLaunches(), FakeOpenings())

    assert (board.waiting, board.running) == ([], [])


@pytest.mark.parametrize("builder, end", [
    (development_walk, "halted"), (build_idea_walk, "halted"), (build_idea_walk, "owner-owed"),
    (product_walk, "left_for_the_owner"), (product_walk, "could_not_be_settled"),
    (product_walk, "machinery"), (product_walk, "cap"), (product_walk, "no_runnable_command"),
])
def test_every_other_end_waits_on_the_owner(tmp_path, builder, end):
    root = make_instance(tmp_path, "inst")
    write_state(root, "walk-state.json", builder(ended=end, ended_reason=f"the reason for {end}"))

    board = chain_board.read_board(root, FakeLaunches(), FakeOpenings())

    assert board.running == []
    assert [(row.status, row.reason) for row in board.waiting] == [(end, f"the reason for {end}")]


def test_an_end_the_reader_has_never_seen_waits_on_the_owner(tmp_path):
    root = make_instance(tmp_path, "inst")
    write_state(root, "walk-state.json", product_walk(ended="something-new", ended_reason="odd"))

    rows = waiting_rows(root)

    assert [(row.status, row.reason) for row in rows] == [("something-new", "odd")]


def test_a_walk_whose_launches_are_all_gone_waits_with_status_gone(tmp_path):
    root = make_instance(tmp_path, "inst")
    pending = {"design": one_launch("/logs/a.identity.json"),
               "plan": one_launch("/logs/b.identity.json")}
    write_state(root, "walk-state.json", development_walk(pending=pending))
    launches = FakeLaunches({"/logs/a.identity.json": LaunchState.GONE,
                             "/logs/b.identity.json": LaunchState.GONE})

    board = chain_board.read_board(root, launches, FakeOpenings())

    assert [row.status for row in board.waiting] == [LaunchState.GONE.value]
    assert board.running == []


def test_a_walk_with_a_live_launch_is_running(tmp_path):
    root = make_instance(tmp_path, "inst")
    pending = {"design": one_launch("/logs/a.identity.json"),
               "plan": one_launch("/logs/b.identity.json")}
    write_state(root, "walk-state.json", development_walk(pending=pending))
    launches = FakeLaunches({"/logs/a.identity.json": LaunchState.LIVE,
                             "/logs/b.identity.json": LaunchState.GONE})

    board = chain_board.read_board(root, launches, FakeOpenings())

    assert board.waiting == []
    assert [(row.status, row.reason) for row in board.running] == [("", "")]


def test_a_walk_with_an_unrecorded_launch_is_running(tmp_path):
    root = make_instance(tmp_path, "inst")
    write_state(root, "walk-state.json",
                development_walk(pending={"design": one_launch("/logs/a.identity.json")}))
    launches = FakeLaunches({"/logs/a.identity.json": LaunchState.UNRECORDED})

    board = chain_board.read_board(root, launches, FakeOpenings())

    assert (len(board.waiting), len(board.running)) == (0, 1)


def test_a_walk_waiting_on_no_launch_is_running(tmp_path):
    root = make_instance(tmp_path, "inst")
    write_state(root, "walk-state.json", development_walk(pending={}))

    board = chain_board.read_board(root, FakeLaunches(), FakeOpenings())

    assert (len(board.waiting), len(board.running)) == (0, 1)


def test_a_launch_with_no_identity_is_unrecorded_and_never_asked_about(tmp_path):
    root = make_instance(tmp_path, "inst")
    write_state(root, "walk-state.json", development_walk(pending={"design": {"step": "design"}}))
    launches = FakeLaunches()

    board = chain_board.read_board(root, launches, FakeOpenings())

    assert launches.asked == []
    assert (len(board.waiting), len(board.running)) == (0, 1)


def test_a_chain_walk_with_a_single_pending_launch_is_judged_by_it(tmp_path):
    root = make_instance(tmp_path, "inst")
    pending = {"document": "SDD", "identity": "/logs/solo.identity.json", "kind": "producer"}
    write_state(root, "walk-state.json", product_walk(pending=pending))
    launches = FakeLaunches({"/logs/solo.identity.json": LaunchState.GONE})

    board = chain_board.read_board(root, launches, FakeOpenings())

    assert launches.asked == ["/logs/solo.identity.json"]
    assert [row.status for row in board.waiting] == ["gone"]


def test_all_kinds_share_one_list_newest_first(tmp_path):
    root = make_instance(tmp_path, "inst")
    halted = {"ended": "halted", "ended_reason": "stuck"}
    write_state(root, "a-state.json",
                build_idea_walk("one", started_at="2026-03-01T08:00:00+00:00", **halted))
    write_state(root, "b-state.json",
                development_walk("two", started_at="2026-03-01T12:00:00+00:00", **halted))
    write_state(root, "c-state.json",
                product_walk("three", started_at="2026-03-01T10:00:00+00:00", **halted))

    rows = waiting_rows(root)

    assert [(row.project, row.launcher) for row in rows] == [
        ("two", "chain-change"), ("three", "chain-product"), ("one", "build-idea")]


def test_a_walk_with_no_start_time_comes_last(tmp_path):
    root = make_instance(tmp_path, "inst")
    halted = {"ended": "halted", "ended_reason": "stuck"}
    write_state(root, "a-state.json", build_idea_walk("untimed", started_at="", **halted))
    write_state(root, "b-state.json",
                build_idea_walk("early", started_at="2026-03-01T08:00:00+00:00", **halted))
    write_state(root, "c-state.json", development_walk("missing", **halted))
    state_without_time = json.loads((root / "system/logs/c-state.json").read_text())
    del state_without_time["started_at"]
    write_state(root, "c-state.json", state_without_time)

    rows = waiting_rows(root)

    assert rows[0].project == "early"
    assert {row.project for row in rows[1:]} == {"untimed", "missing"}


@pytest.mark.parametrize("builder, fields, expected", [
    (build_idea_walk, {}, "build-idea"),
    (development_walk, {"chain_name": "change"}, "chain-change"),
    (development_walk, {"chain_name": "development"}, "chain-development"),
    (product_walk, {"chain_name": "agari"}, "chain-agari"),
    (product_walk, {"chain_name": "product"}, "chain-product"),
    (product_walk, {"chain_name": ""}, "chain-product"),
])
def test_each_kind_is_named_by_its_launcher(tmp_path, builder, fields, expected):
    root = make_instance(tmp_path, "inst")
    write_state(root, "walk-state.json", builder(ended="halted", ended_reason="stuck", **fields))

    rows = waiting_rows(root)

    assert [row.launcher for row in rows] == [expected]


def test_a_kind_is_known_by_content_not_by_file_name(tmp_path):
    root = make_instance(tmp_path, "inst")
    write_state(root, "chain-change-widgets-state.json",
                product_walk("change-widgets", chain_name="", ended="halted", ended_reason="x"))

    rows = waiting_rows(root)

    assert [(row.launcher, row.project) for row in rows] == [("chain-product", "change-widgets")]


def write_seed(root: Path, project: str, folder: str, seed: str, heading: str,
               as_folder: bool = False) -> None:
    where = root / "system" / "projects" / project / "journey" / "nemawashi" / folder
    where.mkdir(parents=True, exist_ok=True)
    if as_folder:
        (where / seed).mkdir()
        (where / seed / "seed.md").write_text(f"# {heading}\n\nbody\n")
    else:
        (where / seed).write_text(f"# {heading}\n\nbody\n")


def test_station_is_the_recorded_stations_own_heading(tmp_path):
    root = make_instance(tmp_path, "inst")
    station = "2026-01-02_the-widgets-ship.md"
    write_station(root, "widgets", "", station, "宿場 Shukuba — the widgets ship")
    write_station(root, "widgets", "", "2026-01-01_another-open-one.md", "another open one")
    write_state(root, "walk-state.json", build_idea_walk(
        station=station, ended="halted", ended_reason="x"))

    rows = waiting_rows(root)

    assert [row.station for row in rows] == ["the widgets ship"]


def test_station_finds_a_station_already_closed_to_trail(tmp_path):
    root = make_instance(tmp_path, "inst")
    station = "2026-01-02_the-widgets-ship.md"
    write_station(root, "widgets", "trail", station, "宿場 Shukuba — the widgets ship")
    write_state(root, "walk-state.json", build_idea_walk(
        station=station, ended="halted", ended_reason="x"))

    rows = waiting_rows(root)

    assert [row.station for row in rows] == ["the widgets ship"]


def test_station_finds_a_parked_station(tmp_path):
    root = make_instance(tmp_path, "inst")
    station = "2026-01-02_the-widgets-ship.md"
    write_station(root, "widgets", "parked", station, "宿場 Shukuba — the widgets ship")
    write_state(root, "walk-state.json", build_idea_walk(
        station=station, ended="halted", ended_reason="x"))

    rows = waiting_rows(root)

    assert [row.station for row in rows] == ["the widgets ship"]


def test_station_is_the_projects_one_open_station_when_the_walk_records_none(tmp_path):
    root = make_instance(tmp_path, "inst")
    write_station(root, "widgets", "", "2026-01-02_the-widgets-ship.md",
                  "宿場 Shukuba — the widgets ship")
    write_station(root, "widgets", "trail", "2026-01-01_an-old-one.md", "an old one")
    write_state(root, "walk-state.json", development_walk(key="2026-01-03_a-change"))

    rows = running_rows(root)

    assert [row.station for row in rows] == ["the widgets ship"]


@pytest.mark.parametrize("open_stations", [0, 2])
def test_no_station_when_none_is_recorded_and_the_project_has_not_one_open(tmp_path,
                                                                          open_stations):
    root = make_instance(tmp_path, "inst")
    for number in range(open_stations):
        write_station(root, "widgets", "", f"2026-01-0{number + 1}_open.md", f"open {number}")
    write_state(root, "walk-state.json", development_walk(key="2026-01-03_a-change"))

    rows = running_rows(root)

    assert [row.station for row in rows] == [""]


def test_seed_is_the_projects_one_seed_at_the_seedbed_root(tmp_path):
    root = make_instance(tmp_path, "inst")
    write_seed(root, "widgets", "", "2026-01-01_widgets-everywhere.md",
               "根回し Nemawashi — widgets everywhere")
    write_seed(root, "widgets", "unpicked", "2026-01-05_a-later-idea.md", "a later idea")
    write_state(root, "walk-state.json", development_walk(key="2026-01-03_a-change"))

    rows = running_rows(root)

    assert [row.seed for row in rows] == ["widgets everywhere"]


def test_seed_reads_a_folder_seed_by_its_seed_md(tmp_path):
    root = make_instance(tmp_path, "inst")
    write_seed(root, "widgets", "", "2026-01-01_widgets-everywhere",
               "根回し Nemawashi — widgets everywhere", as_folder=True)
    (root / "system" / "projects" / "widgets" / "journey" / "nemawashi" / "README.md").write_text(
        "# not a seed\n")
    write_state(root, "walk-state.json", development_walk(key="2026-01-03_a-change"))

    rows = running_rows(root)

    assert [row.seed for row in rows] == ["widgets everywhere"]


def test_seed_is_the_recorded_seed_found_where_it_was_retired_to(tmp_path):
    root = make_instance(tmp_path, "inst")
    seed = "2026-01-01_widgets-everywhere"
    write_seed(root, "widgets", "trail", seed, "根回し Nemawashi — widgets everywhere",
               as_folder=True)
    write_seed(root, "widgets", "", "2026-01-09_the-next-seed.md", "the next seed")
    recorded = str(root / "system" / "projects" / "widgets" / "journey" / "nemawashi" / seed)
    write_state(root, "walk-state.json", build_idea_walk(
        seed=recorded, ended="halted", ended_reason="x"))

    rows = waiting_rows(root)

    assert [row.seed for row in rows] == ["widgets everywhere"]


@pytest.mark.parametrize("root_seeds", [0, 2])
def test_no_seed_when_none_is_recorded_and_the_seedbed_root_has_not_one(tmp_path, root_seeds):
    root = make_instance(tmp_path, "inst")
    for number in range(root_seeds):
        write_seed(root, "widgets", "", f"2026-01-0{number + 1}_seed.md", f"seed {number}")
    write_state(root, "walk-state.json", development_walk(key="2026-01-03_a-change"))

    rows = running_rows(root)

    assert [row.seed for row in rows] == [""]


def test_walk_is_the_change_keys_words(tmp_path):
    root = make_instance(tmp_path, "inst")
    write_state(root, "walk-state.json", development_walk(key="2026-01-02_the-widgets-ship"))

    rows = running_rows(root)

    assert [row.walk for row in rows] == ["the widgets ship"]


def test_a_walk_with_a_station_and_a_change_shows_both(tmp_path):
    root = make_instance(tmp_path, "inst")
    station = "2026-01-02_the-widgets-ship.md"
    write_station(root, "widgets", "", station, "宿場 Shukuba — the widgets ship")
    write_state(root, "walk-state.json", build_idea_walk(
        station=station, key="2026-01-02_the-first-widget", ended="halted", ended_reason="x"))

    (row,) = waiting_rows(root)

    assert (row.station, row.walk) == ("the widgets ship", "the first widget")


def test_walk_is_the_document_on_a_definition_chain(tmp_path):
    root = make_instance(tmp_path, "inst")
    pending = {"document": "UXD", "identity": "/logs/solo.identity.json", "kind": "producer"}
    write_state(root, "walk-state.json", product_walk(pending=pending))
    launches = FakeLaunches({"/logs/solo.identity.json": LaunchState.LIVE})

    rows = running_rows(root, launches)

    assert [row.walk for row in rows] == ["UXD"]


def test_a_walk_with_no_journey_has_no_seed_station_or_walk(tmp_path):
    root = make_instance(tmp_path, "inst")
    write_state(root, "walk-state.json", development_walk())

    (row,) = running_rows(root)

    assert (row.seed, row.station, row.walk) == ("", "", "")


def test_step_is_the_pending_steps_on_a_development_chain(tmp_path):
    root = make_instance(tmp_path, "inst")
    pending = {"design": one_launch("/logs/a.identity.json"),
               "content": one_launch("/logs/b.identity.json")}
    write_state(root, "walk-state.json", development_walk(pending=pending))
    launches = FakeLaunches({"/logs/a.identity.json": LaunchState.LIVE,
                             "/logs/b.identity.json": LaunchState.LIVE})

    rows = running_rows(root, launches)

    assert [row.step for row in rows] == ["design, content"]


def test_step_is_the_document_on_a_definition_chain(tmp_path):
    root = make_instance(tmp_path, "inst")
    pending = {"document": "UXD", "identity": "/logs/solo.identity.json", "kind": "producer"}
    write_state(root, "walk-state.json", product_walk(pending=pending))
    launches = FakeLaunches({"/logs/solo.identity.json": LaunchState.LIVE})

    rows = running_rows(root, launches)

    assert [row.step for row in rows] == ["UXD"]


def test_step_is_the_pending_rows_move_on_a_build_idea_walk(tmp_path):
    root = make_instance(tmp_path, "inst")
    rows_table = [{"number": 1, "move": "close the reached station"},
                  {"number": 2, "move": "open the next station"}]
    write_state(root, "walk-state.json", build_idea_walk(
        rows=rows_table, pending={"2": one_launch("/logs/a.identity.json")}))
    launches = FakeLaunches({"/logs/a.identity.json": LaunchState.LIVE})

    rows = running_rows(root, launches)

    assert [row.step for row in rows] == ["open the next station"]


def test_a_walk_waiting_on_nothing_has_no_step(tmp_path):
    root = make_instance(tmp_path, "inst")
    write_state(root, "walk-state.json", development_walk(pending={}))

    rows = running_rows(root)

    assert [row.step for row in rows] == [""]


OWNER_OWED = {"ended": "owner-owed", "ended_reason": "owner's act owed"}
HANDS_BACK = "/pins/x/core/launchers/build-idea/launcher.sh widgets --chain-ended"


def test_an_owner_owed_build_idea_a_later_chain_hands_back_to_is_in_neither_list(tmp_path):
    root = make_instance(tmp_path, "inst")
    write_state(root, "a-state.json", build_idea_walk(**OWNER_OWED))
    write_state(root, "b-state.json", development_walk(
        on_end=HANDS_BACK, started_at="2026-03-01T11:00:00+00:00"))

    board = chain_board.read_board(root, FakeLaunches(), FakeOpenings())

    assert board.waiting == []
    assert [row.launcher for row in board.running] == ["chain-change"]


def test_an_owner_owed_build_idea_stays_when_the_chain_started_before_it(tmp_path):
    root = make_instance(tmp_path, "inst")
    write_state(root, "a-state.json", build_idea_walk(**OWNER_OWED))
    write_state(root, "b-state.json", development_walk(
        on_end=HANDS_BACK, started_at="2026-03-01T09:00:00+00:00"))

    assert [row.launcher for row in waiting_rows(root)] == ["build-idea"]


def test_an_owner_owed_build_idea_stays_when_the_chain_hands_back_to_another_project(tmp_path):
    root = make_instance(tmp_path, "inst")
    write_state(root, "a-state.json", build_idea_walk(**OWNER_OWED))
    write_state(root, "b-state.json", development_walk(
        "gadgets", on_end=HANDS_BACK.replace("widgets", "gadgets"),
        started_at="2026-03-01T11:00:00+00:00"))

    assert [row.launcher for row in waiting_rows(root)] == ["build-idea"]


def test_a_halted_build_idea_stays_though_a_later_chain_hands_back_to_it(tmp_path):
    root = make_instance(tmp_path, "inst")
    write_state(root, "a-state.json", build_idea_walk(ended="halted", ended_reason="it broke"))
    write_state(root, "b-state.json", development_walk(
        on_end=HANDS_BACK, started_at="2026-03-01T11:00:00+00:00"))

    assert [row.launcher for row in waiting_rows(root)] == ["build-idea"]


SEED = "2026-03-01_a-widget-seed"


REPORT = "2026-03-01_a-widget-change_report.md"


def report_in(root: Path, folder: str, write: bool = True) -> str:
    """The unit's report inside SEED's folder under nemawashi/<folder>, written there."""
    where = root / "system" / "projects" / "widgets" / "journey" / "nemawashi" / folder / SEED
    where.mkdir(parents=True, exist_ok=True)
    if write:
        (where / REPORT).write_text("# a report\n")
    return str(where / REPORT)


def test_an_owner_owed_build_idea_whose_seed_was_dropped_is_in_neither_list(tmp_path):
    root = make_instance(tmp_path, "inst")
    recorded = report_in(root, "", write=False)
    report_in(root, "drop")
    write_state(root, "a-state.json", build_idea_walk(report=recorded, **OWNER_OWED))

    assert waiting_rows(root) == []


def test_an_owner_owed_build_idea_stays_when_a_dropped_seed_only_shares_its_folder_name(tmp_path):
    root = make_instance(tmp_path, "inst")
    recorded = report_in(root, "")
    report_in(root, "drop", write=False)
    write_state(root, "a-state.json", build_idea_walk(report=recorded, **OWNER_OWED))

    assert [row.launcher for row in waiting_rows(root)] == ["build-idea"]


@pytest.mark.parametrize("folder", ["", "unpicked", "trail"])
def test_an_owner_owed_build_idea_stays_while_its_seed_is_not_dropped(tmp_path, folder):
    root = make_instance(tmp_path, "inst")
    write_state(root, "a-state.json", build_idea_walk(report=report_in(root, folder),
                                                      **OWNER_OWED))

    assert [row.launcher for row in waiting_rows(root)] == ["build-idea"]


def test_an_owner_owed_build_idea_on_a_retired_seeds_refine_report_stays(tmp_path):
    root = make_instance(tmp_path, "inst")
    refine = root / "system" / "projects" / "widgets" / "docs" / "nemawashi-refine"
    refine.mkdir(parents=True)
    (refine / f"{SEED}_report.md").write_text("# a refine report\n")
    write_state(root, "a-state.json", build_idea_walk(report=str(refine / f"{SEED}_report.md"),
                                                      **OWNER_OWED))

    assert [row.launcher for row in waiting_rows(root)] == ["build-idea"]


LATER = "2026-03-01T12:00:00+00:00"
CHANGE = "2026-03-01_a-widget-change"


def test_a_halted_change_walk_a_later_development_walk_took_up_is_in_neither_list(tmp_path):
    root = make_instance(tmp_path, "inst")
    write_state(root, "chain-change-widgets-state.json",
                development_walk(key=CHANGE, ended="halted", ended_reason="stopped at seal"))
    write_state(root, "chain-development-widgets-state.json", development_walk(
        chain_name="development", key=CHANGE, ended="sealed", started_at=LATER))

    board = chain_board.read_board(root, FakeLaunches(), FakeOpenings())

    assert (board.waiting, board.running) == ([], [])


def test_the_later_walk_is_the_row_while_it_runs(tmp_path):
    root = make_instance(tmp_path, "inst")
    write_state(root, "chain-change-widgets-state.json",
                development_walk(key=CHANGE, ended="halted", ended_reason="stopped at seal"))
    write_state(root, "chain-development-widgets-state.json",
                development_walk(chain_name="development", key=CHANGE, started_at=LATER))

    board = chain_board.read_board(root, FakeLaunches(), FakeOpenings())

    assert board.waiting == []
    assert [row.launcher for row in board.running] == ["chain-development"]


def close_change(root: Path, project: str, folder: str, key: str) -> None:
    (root / "system" / "projects" / project / "journey" / "tobiishi" / folder / key).mkdir(
        parents=True)


@pytest.mark.parametrize("folder", ["trail", "drop"])
def test_a_halted_change_walk_over_a_sealed_or_dropped_unit_is_in_neither_list(tmp_path, folder):
    """The later walk's state file is overwritten by the next change; the unit's folder is not."""
    root = make_instance(tmp_path, "inst")
    write_state(root, "chain-change-widgets-state.json",
                development_walk(key=CHANGE, ended="halted", ended_reason="stopped at seal"))
    write_state(root, "chain-development-widgets-state.json", development_walk(
        chain_name="development", key="2026-03-02_the-next-change", ended="sealed",
        started_at=LATER))
    close_change(root, "widgets", folder, CHANGE)

    board = chain_board.read_board(root, FakeLaunches(), FakeOpenings())

    assert (board.waiting, board.running) == ([], [])


def test_a_halted_change_walk_stays_when_another_projects_unit_of_that_key_is_sealed(tmp_path):
    root = make_instance(tmp_path, "inst")
    write_state(root, "chain-change-widgets-state.json",
                development_walk(key=CHANGE, ended="halted", ended_reason="stopped at seal"))
    close_change(root, "gadgets", "trail", CHANGE)

    (row,) = waiting_rows(root)

    assert row.project == "widgets"


def test_a_halted_change_walk_stays_when_the_later_walk_is_over_another_change(tmp_path):
    root = make_instance(tmp_path, "inst")
    write_state(root, "chain-change-widgets-state.json",
                development_walk(key=CHANGE, ended="halted", ended_reason="stopped at seal"))
    write_state(root, "chain-development-widgets-state.json", development_walk(
        chain_name="development", key="2026-03-01_another-change", ended="sealed",
        started_at=LATER))

    (row,) = waiting_rows(root)

    assert (row.launcher, row.status) == ("chain-change", "halted")


def test_a_halted_change_walk_stays_when_the_other_walk_started_before_it(tmp_path):
    root = make_instance(tmp_path, "inst")
    write_state(root, "chain-change-widgets-state.json", development_walk(
        key=CHANGE, ended="halted", ended_reason="stopped at seal", started_at=LATER))
    write_state(root, "chain-development-widgets-state.json",
                development_walk(chain_name="development", key=CHANGE, ended="sealed"))

    (row,) = waiting_rows(root)

    assert row.launcher == "chain-change"


def test_a_halted_change_walk_stays_when_the_later_walk_is_another_projects(tmp_path):
    root = make_instance(tmp_path, "inst")
    write_state(root, "chain-change-widgets-state.json",
                development_walk(key=CHANGE, ended="halted", ended_reason="stopped at seal"))
    write_state(root, "chain-development-gadgets-state.json", development_walk(
        "gadgets", chain_name="development", key=CHANGE, ended="sealed", started_at=LATER))

    (row,) = waiting_rows(root)

    assert row.project == "widgets"


def test_a_later_walk_that_halts_too_is_the_one_row_waiting(tmp_path):
    root = make_instance(tmp_path, "inst")
    write_state(root, "chain-change-widgets-state.json",
                development_walk(key=CHANGE, ended="halted", ended_reason="first"))
    write_state(root, "chain-development-widgets-state.json", development_walk(
        chain_name="development", key=CHANGE, ended="halted", ended_reason="second",
        started_at=LATER))

    (row,) = waiting_rows(root)

    assert (row.launcher, row.reason) == ("chain-development", "second")


KEYLESS_HALT = "stopped at change: no change_request was written"


@pytest.mark.parametrize("later", [product_walk, development_walk, build_idea_walk])
def test_a_development_walk_halted_before_its_change_existed_is_moved_past_by_a_later_walk(
        tmp_path, later):
    root = make_instance(tmp_path, "inst")
    write_state(root, "chain-change-widgets-state.json",
                development_walk(ended="halted", ended_reason=KEYLESS_HALT))
    write_state(root, "later-state.json", later(started_at=LATER))

    board = chain_board.read_board(root, FakeLaunches(), FakeOpenings())

    assert board.waiting == []
    assert len(board.running) == 1


def test_a_development_walk_halted_before_its_change_existed_stays_when_the_other_started_first(
        tmp_path):
    root = make_instance(tmp_path, "inst")
    write_state(root, "chain-change-widgets-state.json",
                development_walk(ended="halted", ended_reason=KEYLESS_HALT, started_at=LATER))
    write_state(root, "chain-widgets-state.json", product_walk())

    (row,) = waiting_rows(root)

    assert row.launcher == "chain-change"


def test_a_development_walk_halted_before_its_change_existed_stays_for_another_projects_walk(
        tmp_path):
    root = make_instance(tmp_path, "inst")
    write_state(root, "chain-change-widgets-state.json",
                development_walk(ended="halted", ended_reason=KEYLESS_HALT))
    write_state(root, "chain-gadgets-state.json", product_walk("gadgets", started_at=LATER))

    (row,) = waiting_rows(root)

    assert row.project == "widgets"


def test_a_development_walk_halted_before_its_change_existed_with_no_project_stays(tmp_path):
    root = make_instance(tmp_path, "inst")
    write_state(root, "chain-change-state.json",
                development_walk("", ended="halted", ended_reason=KEYLESS_HALT))
    write_state(root, "chain-state.json", product_walk("", started_at=LATER))

    (row,) = waiting_rows(root)

    assert row.launcher == "chain-change"


def test_a_halted_change_walk_with_a_key_stays_though_a_definition_walk_started_later(tmp_path):
    root = make_instance(tmp_path, "inst")
    write_state(root, "chain-change-widgets-state.json",
                development_walk(key=CHANGE, ended="halted", ended_reason="stopped at seal"))
    write_state(root, "chain-widgets-state.json", product_walk(started_at=LATER))

    (row,) = waiting_rows(root)

    assert row.launcher == "chain-change"


MOVED_PAST_ENDS = ["machinery", "could_not_be_settled", "cap", "no_runnable_command", "unheard"]


@pytest.mark.parametrize("end", MOVED_PAST_ENDS)
@pytest.mark.parametrize("later", [development_walk, build_idea_walk])
def test_a_stopped_definition_walk_a_later_walk_on_its_project_moved_past_is_in_neither_list(
        tmp_path, end, later):
    root = make_instance(tmp_path, "inst")
    write_state(root, "chain-widgets-state.json",
                product_walk(ended=end, ended_reason="the launched run produced nothing"))
    write_state(root, "later-state.json", later(started_at=LATER))

    board = chain_board.read_board(root, FakeLaunches(), FakeOpenings())

    assert board.waiting == []
    assert len(board.running) == 1


def test_a_definition_walk_left_for_the_owner_stays_though_a_later_walk_started(tmp_path):
    root = make_instance(tmp_path, "inst")
    write_state(root, "chain-widgets-state.json",
                product_walk(ended="left_for_the_owner", ended_reason="a signature is owed"))
    write_state(root, "chain-change-widgets-state.json", development_walk(started_at=LATER))

    (row,) = waiting_rows(root)

    assert (row.launcher, row.status) == ("chain-product", "left_for_the_owner")


def test_a_stopped_definition_walk_stays_when_the_other_walk_started_before_it(tmp_path):
    root = make_instance(tmp_path, "inst")
    write_state(root, "chain-widgets-state.json",
                product_walk(ended="machinery", ended_reason="it broke", started_at=LATER))
    write_state(root, "chain-change-widgets-state.json", development_walk(ended="sealed"))

    (row,) = waiting_rows(root)

    assert row.launcher == "chain-product"


def test_a_stopped_definition_walk_stays_when_the_later_walk_is_another_projects(tmp_path):
    root = make_instance(tmp_path, "inst")
    write_state(root, "chain-widgets-state.json",
                product_walk(ended="machinery", ended_reason="it broke"))
    write_state(root, "chain-change-gadgets-state.json",
                development_walk("gadgets", started_at=LATER))

    (row,) = waiting_rows(root)

    assert row.project == "widgets"


def write_skill_run(root: Path, file_name: str, **fields) -> None:
    write_state(root, file_name, {"skill": "shukuba-refine", "project": "widgets",
                                  "started_at": STARTED, "identity": "/logs/run.identity.json",
                                  **fields})


def test_a_live_skill_run_is_running(tmp_path):
    root = make_instance(tmp_path, "inst")
    write_skill_run(root, "skill-shukuba-refine@widgets.run.json")
    launches = FakeLaunches({"/logs/run.identity.json": LaunchState.LIVE})

    (row,) = running_rows(root, launches)

    assert (row.launcher, row.project, row.walk, row.step, row.status) == (
        "skill", "widgets", "shukuba-refine", "", "")
    assert row.started_at == STARTED


@pytest.mark.parametrize("state", [LaunchState.GONE, LaunchState.UNRECORDED])
def test_a_skill_run_that_is_not_live_is_in_neither_list(tmp_path, state):
    root = make_instance(tmp_path, "inst")
    write_skill_run(root, "skill-shukuba-refine@widgets.run.json")
    launches = FakeLaunches({"/logs/run.identity.json": state})

    board = chain_board.read_board(root, launches, FakeOpenings())

    assert (board.waiting, board.running) == ([], [])


def test_a_skill_run_record_naming_no_identity_is_skipped_and_never_asked_about(tmp_path):
    root = make_instance(tmp_path, "inst")
    write_skill_run(root, "skill-shukuba-refine@widgets.run.json", identity="")
    (root / "system" / "logs" / "skill-broken.run.json").write_text("{not json")
    launches = FakeLaunches()

    board = chain_board.read_board(root, launches, FakeOpenings())

    assert (board.running, launches.asked) == ([], [])


def test_a_live_skill_run_sorts_among_the_walks(tmp_path):
    root = make_instance(tmp_path, "inst")
    write_state(root, "a-state.json", development_walk("older"))
    write_skill_run(root, "skill-shukuba-refine@widgets.run.json", started_at=LATER)
    launches = FakeLaunches({"/logs/run.identity.json": LaunchState.LIVE})

    rows = running_rows(root, launches)

    assert [row.project for row in rows] == ["widgets", "older"]


def test_no_row_holds_a_md_path_or_a_pinned_launcher_path(tmp_path):
    root = make_instance(tmp_path, "inst")
    station = "2026-01-02_the-widgets-ship.md"
    write_station(root, "widgets", "", station, "宿場 Shukuba — the widgets ship")
    pinned = "/home/someone/.kensaiapp/pins/20260101T000000Z-abc/core/launchers/build-idea"
    pinned += "/launcher.sh"
    reason = (f"resume with `{pinned} widgets`,"
              " or `core/launchers/chain-change/launcher.sh widgets`;"
              f" see system/projects/widgets/journey/shukuba/{station} and"
              " system/projects/widgets/notes/2026-02-03_the-missing-note.md")
    write_state(root, "walk-state.json", build_idea_walk(
        station=station, ended="owner-owed", ended_reason=reason))

    (row,) = waiting_rows(root)

    for text in (row.launcher, row.project, row.seed, row.station, row.walk, row.step, row.status,
                 row.reason, row.started_at):
        assert ".md" not in text and "launcher.sh" not in text
    assert "build-idea widgets" in row.reason
    assert "chain-change widgets" in row.reason
    assert "the widgets ship" in row.reason
    assert "the missing note" in row.reason


def test_an_absolute_md_path_inside_the_instance_reads_as_its_heading(tmp_path):
    root = make_instance(tmp_path, "inst")
    station = "2026-01-02_the-widgets-ship.md"
    write_station(root, "widgets", "", station, "宿場 Shukuba — the widgets ship")
    absolute = root / "system" / "projects" / "widgets" / "journey" / "shukuba" / station
    write_state(root, "walk-state.json", build_idea_walk(
        ended="owner-owed", ended_reason=f"open {absolute} § Attempts"))

    (row,) = waiting_rows(root)

    assert row.reason == "open the widgets ship § Attempts"


def test_an_md_path_outside_the_instance_reads_as_its_name_in_words(tmp_path):
    root = make_instance(tmp_path, "inst")
    outside = tmp_path / "elsewhere" / "2026-01-02_a-far-note.md"
    outside.parent.mkdir()
    outside.write_text("# Note — words from outside the instance\n")
    write_state(root, "walk-state.json", build_idea_walk(
        ended="owner-owed", ended_reason=f"see {outside}"))

    (row,) = waiting_rows(root)

    assert row.reason == "see a far note"


def test_a_path_inside_a_project_reads_from_below_the_project_folder(tmp_path):
    root = make_instance(tmp_path, "inst")
    tobiishi = root / "system" / "projects" / "widgets" / "journey" / "tobiishi"
    write_state(root, "walk-state.json", build_idea_walk(
        ended="halted", ended_reason=f"no folder under {tobiishi} after the run ended"))

    (row,) = waiting_rows(root)

    assert row.reason == "no folder under journey/tobiishi after the run ended"


def test_a_path_inside_the_instance_reads_from_its_root(tmp_path):
    root = make_instance(tmp_path, "inst")
    write_state(root, "walk-state.json", build_idea_walk(
        ended="halted", ended_reason=f"missing {root / 'system' / 'logs' / 'run.log'}"))

    (row,) = waiting_rows(root)

    assert row.reason == "missing system/logs/run.log"


def test_the_instance_path_inside_a_longer_path_is_left_whole(tmp_path):
    root = make_instance(tmp_path, "inst")
    elsewhere = f"/b{root}/system/logs/run.log"
    write_state(root, "walk-state.json", build_idea_walk(
        ended="halted", ended_reason=f"missing {elsewhere}"))

    (row,) = waiting_rows(root)

    assert row.reason == f"missing {elsewhere}"


def test_running_rows_are_newest_first_too(tmp_path):
    root = make_instance(tmp_path, "inst")
    write_state(root, "a-state.json",
                build_idea_walk("one", started_at="2026-03-01T08:00:00+00:00"))
    write_state(root, "b-state.json", development_walk("untimed", started_at=""))
    write_state(root, "c-state.json",
                product_walk("three", started_at="2026-03-01T10:00:00+00:00"))

    rows = running_rows(root)

    assert [row.project for row in rows] == ["three", "one", "untimed"]


def test_the_instance_is_found_from_a_folder_below_it(tmp_path):
    root = make_instance(tmp_path, "inst")
    worktree = root / ".worktrees" / "2026-03-01_a-change"
    (worktree / "sub").mkdir(parents=True)
    (worktree / "kensaiapp.md").write_text("# a worktree's copy\n")

    assert chain_board.find_instance_root(worktree / "sub") == root


def test_a_fresh_clone_with_no_logs_is_an_instance_with_nothing_to_show(tmp_path, capsys):
    clone = tmp_path / "clone"
    (clone / "sub").mkdir(parents=True)
    (clone / "kensaiapp.md").write_text("# a fresh clone\n")

    assert chain_board.find_instance_root(clone / "sub") == clone
    assert chain_board.main([str(clone)]) == 0
    assert json.loads(capsys.readouterr().out) == {"instance": "clone", "waiting": [], "running": [],
                                                    "routes": []}


def test_a_folder_in_no_instance_has_no_instance(tmp_path, capsys):
    nowhere = tmp_path / "nowhere"
    nowhere.mkdir()

    assert chain_board.find_instance_root(nowhere) is None
    assert chain_board.main([str(nowhere)]) == 0
    assert json.loads(capsys.readouterr().out) == {"instance": None, "waiting": [], "running": [],
                                                    "routes": []}


def test_unreadable_and_foreign_files_are_skipped(tmp_path):
    root = make_instance(tmp_path, "inst")
    logs = root / "system" / "logs"
    (logs / "broken-state.json").write_text("{not json")
    (logs / "list-state.json").write_text("[1, 2]")
    (logs / "held-state.json.lock").write_text(json.dumps(build_idea_walk(ended="halted")))
    write_state(root, "foreign-state.json", {"project": "widgets", "ended": "halted"})

    board = chain_board.read_board(root, FakeLaunches(), FakeOpenings())

    assert (board.waiting, board.running) == ([], [])


def test_the_cli_prints_the_board_as_json(tmp_path, capsys):
    root = make_instance(tmp_path, "inst")
    write_state(root, "a-state.json", build_idea_walk(ended="halted", ended_reason="stuck"))
    write_state(root, "b-state.json", development_walk("other"))

    status = chain_board.main([str(root)])

    printed = json.loads(capsys.readouterr().out)
    assert status == 0
    assert printed["instance"] == "inst"
    assert [set(row) for row in printed["waiting"] + printed["running"]] == [ROW_KEYS, ROW_KEYS]
    assert (len(printed["waiting"]), len(printed["running"])) == (1, 1)
    assert printed["routes"] == []


# --- the route: the active seed's checklist, each station with its walks ------------------------


ROUTE_SEED = """# 根回し Nemawashi seed — widgets everywhere

## Stations

- [x] the-first-widget — a widget exists
- [ ] the-widgets-ship — the widgets reach a person
  - [ ] 2↳. **a-nested-step** — one step inside it
- [ ] the-widgets-sing — they make a sound
"""


def write_route(root: Path, project: str = "widgets", seed_text: str = ROUTE_SEED,
                open_station: str | None = "2026-03-02_the-widgets-ship.md") -> Path:
    journey = root / "system" / "projects" / project / "journey"
    (journey / "nemawashi").mkdir(parents=True, exist_ok=True)
    seed = journey / "nemawashi" / "2026-03-01_widgets-everywhere.md"
    seed.write_text(seed_text)
    if open_station:
        write_station(root, project, "", open_station, "the widgets ship")
    return journey


def write_unit(journey: Path, folder: str, key: str) -> None:
    where = journey / "tobiishi" / folder / key
    where.mkdir(parents=True)
    (where / "change_request.md").write_text(f"# Change request — {key}\n")




def board_with_route(root: Path, openings: FakeOpenings | None = None) -> chain_board.Board:
    write_state(root, "chain-change-widgets-state.json",
                development_walk(key="2026-03-03_ship-one"))
    return chain_board.read_board(root, FakeLaunches(), openings or FakeOpenings())


def test_a_route_reads_the_seed_checklist_as_reached_current_and_ahead(tmp_path):
    root = make_instance(tmp_path, "inst")
    write_route(root)

    [route] = board_with_route(root).routes

    assert (route.project, route.seed) == ("widgets", "widgets everywhere")
    assert [(stop.name, stop.state.value, stop.depth) for stop in route.stations] == [
        ("the-first-widget", "reached", 0),
        ("the-widgets-ship", "current", 0),
        ("2↳. a-nested-step", "ahead", 1),
        ("the-widgets-sing", "ahead", 0),
    ]


def test_each_station_carries_its_walks_in_key_order_wherever_they_sit(tmp_path):
    root = make_instance(tmp_path, "inst")
    journey = write_route(root)
    write_unit(journey, "", "2026-03-03_ship-one")
    write_unit(journey, "trail", "2026-03-02_ship-zero")
    write_unit(journey, "drop", "2026-03-02_ship-tried")
    write_unit(journey, "trail", "2026-03-01_made-the-first")
    openings = FakeOpenings({"2026-03-03_ship-one": "2026-03-02_the-widgets-ship",
                             "2026-03-02_ship-zero": "2026-03-02_the-widgets-ship",
                             "2026-03-02_ship-tried": "2026-03-02_the-widgets-ship",
                             "2026-03-01_made-the-first": "2026-03-01_the-first-widget"})

    stations = board_with_route(root, openings).routes[0].stations

    current = next(stop for stop in stations if stop.state is chain_board.StopState.CURRENT)
    assert [(walk.name, walk.key, walk.state) for walk in current.walks] == [
        ("ship-tried", "2026-03-02_ship-tried", "dropped"),
        ("ship-zero", "2026-03-02_ship-zero", "sealed"),
        ("ship-one", "2026-03-03_ship-one", "open"),
    ]
    reached = next(stop for stop in stations if stop.name == "the-first-widget")
    assert [(walk.key, walk.state) for walk in reached.walks] == [("2026-03-01_made-the-first", "sealed")]
    assert all(stop.walks == [] for stop in stations if stop not in (current, reached))
    assert openings.asked == ["widgets"]


def test_an_open_unit_the_history_does_not_link_is_the_open_stations(tmp_path):
    """A unit opened by hand carries `Agari:`, not `Shukuba:`, on its opening commit."""
    root = make_instance(tmp_path, "inst")
    journey = write_route(root)
    write_unit(journey, "", "2026-03-03_ship-one")

    stations = board_with_route(root).routes[0].stations

    current = next(stop for stop in stations if stop.state is chain_board.StopState.CURRENT)
    assert [(walk.key, walk.state) for walk in current.walks] == [("2026-03-03_ship-one", "open")]


def test_a_closed_unit_the_history_does_not_link_is_under_no_station(tmp_path):
    root = make_instance(tmp_path, "inst")
    journey = write_route(root)
    write_unit(journey, "trail", "2026-03-01_by-hand")
    write_unit(journey, "drop", "2026-03-01_by-hand-too")

    stations = board_with_route(root).routes[0].stations

    assert all(stop.walks == [] for stop in stations)


def test_an_open_unit_linked_to_another_station_is_that_stations_not_the_open_ones(tmp_path):
    root = make_instance(tmp_path, "inst")
    journey = write_route(root)
    write_unit(journey, "", "2026-03-03_elsewhere")

    stations = board_with_route(
        root, FakeOpenings({"2026-03-03_elsewhere": "2026-03-01_the-first-widget"})).routes[0].stations

    assert [(stop.name, [walk.key for walk in stop.walks]) for stop in stations if stop.walks] == [
        ("the-first-widget", ["2026-03-03_elsewhere"])]


def test_a_closed_station_keeps_its_walks_after_it_closes(tmp_path):
    """A run can still be on the walk once its station is closed: build-idea's after-close steps."""
    root = make_instance(tmp_path, "inst")
    journey = write_route(root, open_station=None)
    write_station(root, "widgets", "trail", "2026-03-02_the-widgets-ship.md", "the widgets ship")
    write_unit(journey, "trail", "2026-03-03_ship-one")

    stations = board_with_route(
        root, FakeOpenings({"2026-03-03_ship-one": "2026-03-02_the-widgets-ship"})).routes[0].stations

    ship = next(stop for stop in stations if stop.name == "the-widgets-ship")
    assert [(walk.key, walk.state) for walk in ship.walks] == [("2026-03-03_ship-one", "sealed")]


def test_a_parked_station_keeps_its_walks(tmp_path):
    root = make_instance(tmp_path, "inst")
    journey = write_route(root, open_station=None)
    write_station(root, "widgets", "parked", "2026-03-02_the-widgets-ship.md", "the widgets ship")
    write_unit(journey, "drop", "2026-03-03_ship-tried")

    stations = board_with_route(
        root, FakeOpenings({"2026-03-03_ship-tried": "2026-03-02_the-widgets-ship"})).routes[0].stations

    ship = next(stop for stop in stations if stop.name == "the-widgets-ship")
    assert (ship.state.value, [walk.state for walk in ship.walks]) == ("parked", ["dropped"])


def test_a_walk_of_an_earlier_station_with_the_same_slug_is_not_the_current_stations(tmp_path):
    """A dated trailer names one station: an earlier station cut under the same slug is another."""
    root = make_instance(tmp_path, "inst")
    journey = write_route(root)
    write_unit(journey, "trail", "2026-01-05_an-older-ship")

    stations = board_with_route(
        root, FakeOpenings({"2026-01-05_an-older-ship": "2026-01-04_the-widgets-ship"})).routes[0].stations

    assert all(stop.walks == [] for stop in stations)


def test_a_walk_sits_under_one_item_when_the_checklist_names_its_station_twice(tmp_path):
    root = make_instance(tmp_path, "inst")
    twice = ROUTE_SEED + "- [ ] the-first-widget — named again\n"
    journey = write_route(root, seed_text=twice)
    write_unit(journey, "trail", "2026-03-01_made-the-first")

    stations = board_with_route(
        root, FakeOpenings({"2026-03-01_made-the-first": "2026-03-01_the-first-widget"})).routes[0].stations

    assert [(stop.name, len(stop.walks)) for stop in stations if stop.name == "the-first-widget"] == [
        ("the-first-widget", 1), ("the-first-widget", 0)]


def test_with_no_station_open_an_unlinked_open_unit_is_under_no_station(tmp_path):
    root = make_instance(tmp_path, "inst")
    journey = write_route(root, open_station=None)
    write_unit(journey, "", "2026-03-03_by-hand")

    stations = board_with_route(root).routes[0].stations

    assert all(stop.walks == [] for stop in stations)


def test_a_trailer_naming_the_bare_slug_links_by_the_slug(tmp_path):
    """Before 2026-09-14 a `Shukuba:` trailer named the station's slug, not its dated stem."""
    root = make_instance(tmp_path, "inst")
    journey = write_route(root)
    write_unit(journey, "trail", "2026-03-02_an-old-unit")

    stations = board_with_route(
        root, FakeOpenings({"2026-03-02_an-old-unit": "the-widgets-ship"})).routes[0].stations

    current = next(stop for stop in stations if stop.state is chain_board.StopState.CURRENT)
    assert [walk.key for walk in current.walks] == ["2026-03-02_an-old-unit"]


def test_two_open_stations_leave_nothing_current(tmp_path):
    root = make_instance(tmp_path, "inst")
    write_route(root)
    write_station(root, "widgets", "", "2026-03-05_a-second-open-one.md", "a second open one")

    stations = board_with_route(root).routes[0].stations

    assert [stop.state.value for stop in stations] == ["reached", "ahead", "ahead", "ahead"]


def test_with_no_open_station_nothing_is_current(tmp_path):
    root = make_instance(tmp_path, "inst")
    write_route(root, open_station=None)

    stations = board_with_route(root).routes[0].stations

    assert [stop.state.value for stop in stations] == ["reached", "ahead", "ahead", "ahead"]


def test_an_open_station_the_checklist_does_not_name_is_added_last_as_current(tmp_path):
    root = make_instance(tmp_path, "inst")
    write_route(root, open_station="2026-03-04_an-unplanned-stop.md")

    stations = board_with_route(root).routes[0].stations

    assert [(stop.name, stop.state.value) for stop in stations][-1] == (
        "an-unplanned-stop", "current")
    assert [stop.state.value for stop in stations[:-1]] == ["reached", "ahead", "ahead", "ahead"]


def test_a_numbered_bold_item_is_current_for_its_station(tmp_path):
    root = make_instance(tmp_path, "inst")
    write_route(root, seed_text="# seed — define it\n\n- [ ] 1. **product-prd** — the PRD\n",
                open_station="2026-03-02_product-prd.md")

    [stop] = board_with_route(root).routes[0].stations

    assert (stop.name, stop.state.value) == ("1. product-prd", "current")


def test_the_route_is_read_again_on_every_read(tmp_path):
    root = make_instance(tmp_path, "inst")
    write_route(root)
    board_with_route(root)
    write_route(root, seed_text=ROUTE_SEED.replace(
        "- [ ] the-widgets-sing — they make a sound\n",
        "- [ ] the-widgets-dance — a re-cut stop\n- [ ] the-widgets-sing — they make a sound\n"))

    stations = chain_board.read_board(root, FakeLaunches(), FakeOpenings()).routes[0].stations

    assert [stop.name for stop in stations][-2:] == ["the-widgets-dance", "the-widgets-sing"]


@pytest.mark.parametrize("seeds", [0, 2])
def test_a_seedbed_root_without_exactly_one_seed_has_no_route(tmp_path, seeds):
    root = make_instance(tmp_path, "inst")
    nemawashi = root / "system" / "projects" / "widgets" / "journey" / "nemawashi"
    nemawashi.mkdir(parents=True)
    for number in range(seeds):
        (nemawashi / f"2026-03-0{number + 1}_seed.md").write_text(ROUTE_SEED)

    assert board_with_route(root).routes == []


def test_only_a_project_a_row_names_gets_a_route(tmp_path):
    root = make_instance(tmp_path, "inst")
    write_route(root, project="widgets")
    write_route(root, project="gadgets")
    openings = FakeOpenings()

    board = board_with_route(root, openings)

    assert [route.project for route in board.routes] == ["widgets"]
    assert openings.asked == ["widgets"]


def test_a_row_carries_its_change_key(tmp_path):
    root = make_instance(tmp_path, "inst")

    [row] = board_with_route(root).running

    assert row.key == "2026-03-03_ship-one"


def test_the_cli_prints_each_route(tmp_path, capsys):
    root = make_instance(tmp_path, "inst")
    write_route(root)
    write_state(root, "chain-change-widgets-state.json", development_walk())

    chain_board.main([str(root)])

    [route] = json.loads(capsys.readouterr().out)["routes"]
    assert route["seed"] == "widgets everywhere"
    assert route["stations"][1] == {"name": "the-widgets-ship", "state": "current", "depth": 0,
                                    "walks": []}


# --- the history: which station each change unit was opened for --------------------------------


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def commit_unit(repo: Path, path: str, message: str) -> None:
    target = repo / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("# a change request\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", message)


def make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "someone@example.invalid")
    git(repo, "config", "user.name", "someone")
    return repo


UNITS = "system/projects/widgets/journey/tobiishi"


def test_the_history_links_a_unit_to_the_station_its_opening_commit_names(tmp_path):
    repo = make_repo(tmp_path)
    commit_unit(repo, f"{UNITS}/2026-03-03_ship-one/change_request.md",
                "open tobiishi: ship-one\n\nShukuba: 2026-03-02_the-widgets-ship — progress: x\n")
    (repo / UNITS / "trail").mkdir()
    git(repo, "mv", f"{UNITS}/2026-03-03_ship-one", f"{UNITS}/trail/2026-03-03_ship-one")
    git(repo, "commit", "-q", "-m",
        "seal: ship-one\n\nShukuba: 2026-03-09_another-station — progress: y\n")

    assert chain_board.git_opened_stations(repo, "widgets") == {
        "2026-03-03_ship-one": "2026-03-02_the-widgets-ship"}


def test_the_history_ignores_an_opening_with_no_station_and_another_projects_units(tmp_path):
    repo = make_repo(tmp_path)
    commit_unit(repo, f"{UNITS}/2026-03-03_by-hand/change_request.md",
                "widgets: open change by-hand\n\nAgari: widgets — progress: x\n")
    commit_unit(repo, "system/projects/gadgets/journey/tobiishi/2026-03-03_g/change_request.md",
                "open tobiishi: g\n\nShukuba: 2026-03-02_a-gadget-stop — progress: x\n")

    assert chain_board.git_opened_stations(repo, "widgets") == {}


def test_a_history_that_cannot_be_read_links_nothing(tmp_path):
    assert chain_board.git_opened_stations(tmp_path / "no-repo", "widgets") == {}


def test_an_unticked_item_whose_station_is_parked_reads_parked(tmp_path):
    root = make_instance(tmp_path, "inst")
    write_route(root, open_station=None)
    write_station(root, "widgets", "parked", "2026-03-02_the-widgets-ship.md", "the widgets ship")

    stations = board_with_route(root).routes[0].stations

    assert [(stop.name, stop.state.value) for stop in stations][:2] == [
        ("the-first-widget", "reached"), ("the-widgets-ship", "parked")]
