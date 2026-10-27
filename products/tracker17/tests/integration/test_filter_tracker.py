"""Integration tests of the Tracker's filtered project list, with hand-written fakes (layer 3).

Checks SRS FR-32 to FR-35 (a list narrowed by filter, with the count and the choices), FR-25 and
AC-13 (the overdue filter and the row marking agree on the same date), FR-39 (a refusal keeps every
typed problem and saves nothing), AC-12 and AC-14 (the refusal and filter tests) and NFR-8 (a read
never reaches the saver). Change spec rules CP-393, CP-396, CP-399, CP-405, CP-406, CP-412, CP-413
and CP-415 are the ones each test names; the design rows are T4. No product name is patched: the
real Tracker is handed each fake, and the machine's time zone is set through the environment.
"""

from __future__ import annotations

import time
from collections.abc import Iterator
from datetime import UTC, date, datetime

import pytest

from application import (
    FilterAssigneeNotListed,
    FilterField,
    FilterInput,
    InvalidFilterStatus,
    ProjectTaskList,
    RepeatedFilterValue,
    ReversedFilterRange,
    TaskRow,
    TaskStatus,
    Tracker,
    TrackerState,
)
from domain import filter_project_tasks, restore_state

PROJECTS = [(1, "Alpha", "first"), (2, "Beta", "")]
NEXT_PROJECT_ID = 3
CREATED = datetime(2026, 10, 6, 12, 0, tzinfo=UTC)
TODAY = date(2026, 10, 6)


class SequenceClock:
    """Returns each instant it was given, then the last one again; counts every read."""

    def __init__(self, *instants: datetime) -> None:
        self._instants = list(instants) or [CREATED]
        self.reads = 0

    def now(self) -> datetime:
        index = min(self.reads, len(self._instants) - 1)
        self.reads += 1
        return self._instants[index]


class RecordingSaver:
    """Keeps every state it was handed."""

    def __init__(self) -> None:
        self.saved: list[TrackerState] = []

    def save(self, state: TrackerState) -> None:
        self.saved.append(state)


@pytest.fixture
def utc_zone(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Set the machine's local zone to UTC, so a clock instant names the date it reads as."""
    monkeypatch.setenv("TZ", "UTC")
    time.tzset()
    yield
    monkeypatch.undo()
    time.tzset()


@pytest.fixture
def local_zone(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Set the machine's local zone to UTC+14, where local midnight is ten hours before UTC's."""
    monkeypatch.setenv("TZ", "Pacific/Kiritimati")
    time.tzset()
    yield
    monkeypatch.undo()
    time.tzset()


def make_tracker(saver: RecordingSaver, clock: SequenceClock | None = None) -> Tracker:
    state = restore_state(PROJECTS, NEXT_PROJECT_ID, ("dana", "ali"))
    return Tracker(state, saver, clock or SequenceClock())


def one(field: str, *values: str) -> FilterInput:
    return FilterInput(**{field: tuple(values)})


def ids(listed: ProjectTaskList) -> list[int]:
    return [row.task.id for row in listed.rows]


def test_project_task_list_projects_domain_selection(utc_zone):
    """CP-396, CP-397, CP-412, T4: rows, order, options and counts agree with the domain's own
    selection for a valid filter, an unfiltered query and an empty project."""
    saver = RecordingSaver()
    tracker = make_tracker(saver)
    tracker.add_task(1, "Late", "high", "dana", "2026-10-10")
    tracker.add_task(1, "Soon", "low", "ali", "2026-10-02")
    tracker.add_task(1, "Undated", "high", "dana", "")
    tracker.add_task(2, "Elsewhere", "high", "dana", "")
    tracker.add_task_label(1, "ui")
    tracker.add_task_label(2, "Bug")
    state = saver.saved[-1]
    fields = one("priority", "high")

    listed = tracker.project_task_list(1, fields)
    expected = filter_project_tasks(state, 1, fields, TODAY)

    assert [row.task for row in listed.rows] == list(expected.tasks)
    assert ids(listed) == [1, 3]
    assert listed.match_count == expected.match_count == 2
    assert listed.task_count == expected.task_count == 3
    assert listed.filter == expected.filter
    assert listed.fields == fields
    assert listed.problems == ()
    assert listed.assignees == expected.assignees == ("dana", "ali")
    assert listed.labels == expected.labels == ("Bug", "ui")
    unfiltered = tracker.project_task_list(1, FilterInput())
    assert ids(unfiltered) == [2, 1, 3]
    assert unfiltered.match_count == 3
    other = tracker.project_task_list(2, FilterInput())
    assert other.task_count == 1
    nobody = make_tracker(RecordingSaver()).project_task_list(1, one("status", "blocked", "x"))
    assert (nobody.task_count, nobody.rows, nobody.match_count, nobody.problems) == (0, (), 0, ())


def test_refused_list_preserves_typed_problems_and_raw_choices():
    """CP-405, CP-406, T4: every typed refusal reaches the read model in control order, with the
    raw choices, the full-project options and no result rows or count."""
    saver = RecordingSaver()
    tracker = make_tracker(saver)
    tracker.add_task(1, "One", "", "", "")
    tracker.add_task_label(1, "ui")
    fields = FilterInput(
        status=("blocked",),
        assignee=("carol",),
        label=("a", "b"),
        due_from=("2026-10-10",),
        due_to=("2026-10-01",),
    )

    listed = tracker.project_task_list(1, fields)

    assert [type(problem) for problem in listed.problems] == [
        InvalidFilterStatus,
        FilterAssigneeNotListed,
        RepeatedFilterValue,
        ReversedFilterRange,
    ]
    assert [problem.field for problem in listed.problems] == [
        FilterField.STATUS,
        FilterField.ASSIGNEE,
        FilterField.LABEL,
        FilterField.DUE_FROM,
    ]
    assert listed.fields == fields
    assert listed.rows == ()
    assert listed.match_count == 0
    assert listed.task_count == 1
    assert listed.assignees == ("dana", "ali")
    assert listed.labels == ("ui",)
    assert listed.filter is None


def test_overdue_filter_and_row_marking_agree(utc_zone):
    """CP-415, AC-13: yesterday open, today open, yesterday done and yesterday cancelled give the
    same verdict through the filter and through the row marker on one date."""
    tracker = make_tracker(RecordingSaver(), SequenceClock(CREATED))
    yesterday, today = "2026-10-05", "2026-10-06"
    open_yesterday = tracker.add_task(1, "Open yesterday", "", "", yesterday).id
    open_today = tracker.add_task(1, "Open today", "", "", today).id
    done_yesterday = tracker.add_task(1, "Done yesterday", "", "", yesterday).id
    cancelled_yesterday = tracker.add_task(1, "Cancelled yesterday", "", "", yesterday).id
    tracker.move_task(done_yesterday, "in-progress")
    tracker.move_task(done_yesterday, "done")
    tracker.move_task(cancelled_yesterday, "cancelled")

    filtered = tracker.project_task_list(1, one("overdue", "on"))
    everything = tracker.project_task_list(1, FilterInput())

    assert ids(filtered) == [open_yesterday]
    assert all(row.overdue for row in filtered.rows)
    marked = {row.task.id: row.overdue for row in everything.rows}
    assert marked == {
        open_yesterday: True,
        open_today: False,
        done_yesterday: False,
        cancelled_yesterday: False,
    }
    assert {row.task.id for row in everything.rows if row.overdue} == set(ids(filtered))
    assert tracker.task(cancelled_yesterday).status is TaskStatus.CANCELLED  # type: ignore[union-attr]


def test_one_local_date_snapshot_serves_the_whole_page(local_zone):
    """CP-396, CP-399, T4: a clock whose second read is past local midnight is read once per
    query, every result uses its first local date, and the next query recomputes."""
    before_local_midnight = datetime(2026, 10, 10, 9, 0, tzinfo=UTC)  # local 2026-10-10 23:00
    after_local_midnight = datetime(2026, 10, 10, 11, 0, tzinfo=UTC)  # local 2026-10-11 01:00
    clock = SequenceClock(CREATED, before_local_midnight, after_local_midnight)
    tracker = make_tracker(RecordingSaver(), clock)
    tracker.add_task(1, "Due the tenth", "", "", "2026-10-10")
    assert clock.reads == 1

    first = tracker.project_task_list(1, one("overdue", "on"))
    assert clock.reads == 2
    assert first.rows == ()
    assert first.match_count == 0
    assert first.task_count == 1
    first_unfiltered = tracker.project_task_list(1, FilterInput())
    assert clock.reads == 3
    assert [row.overdue for row in first_unfiltered.rows] == [True]

    later = tracker.project_task_list(1, one("overdue", "on"))
    assert clock.reads == 4
    assert [row.overdue for row in later.rows] == [True]
    assert later.match_count == 1


def test_filter_queries_never_reach_the_saver():
    """CP-413, T4: valid, refused, clear and repeated reads leave the recording saver as it was
    and the current state unchanged."""
    saver = RecordingSaver()
    tracker = make_tracker(saver)
    tracker.add_task(1, "One", "high", "dana", "2026-10-01")
    tracker.add_task(1, "Two", "low", "", "")
    saves, before = len(saver.saved), tracker.project_tasks(1)

    for fields in (
        one("priority", "high"),
        one("priority", "urgent"),
        one("status", "todo", "todo"),
        FilterInput(),
        one("priority", "high"),
        one("overdue", "on"),
    ):
        tracker.project_task_list(1, fields)

    assert len(saver.saved) == saves
    assert tracker.project_tasks(1) == before


def test_existing_project_tasks_remains_compatible():
    """Design § 2 transitive check, T4: the old signature returns its ordered rows and flags, and
    they equal the unfiltered query's rows."""
    tracker = make_tracker(RecordingSaver())
    undated = tracker.add_task(1, "Undated", "", "", "")
    late = tracker.add_task(1, "Late", "", "", "2026-10-01")
    soon = tracker.add_task(1, "Soon", "", "", "2026-10-20")

    rows = tracker.project_tasks(1)

    assert rows == (TaskRow(late, True), TaskRow(soon, False), TaskRow(undated, False))
    assert tracker.project_task_list(1, FilterInput()).rows == rows
