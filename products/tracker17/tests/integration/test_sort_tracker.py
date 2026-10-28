"""Integration tests of the Tracker's sorted project list, with hand-written fakes (layer 3).

Checks SRS FR-36 (a list sorts by one field at a time, with the count and the choices), FR-39 (a
refusal keeps every typed problem and saves nothing), AC-12 and AC-14 (the refusal and sort tests)
and NFR-8 (a read never reaches the saver). Change spec rules CP-434, CP-435, CP-443, CP-447 and
CP-449 are the ones each test names; the design row is T4. No product name is patched: the real
Tracker is handed each fake, and the machine's time zone is set through the environment.
"""

from __future__ import annotations

import time
from collections.abc import Iterator
from datetime import UTC, datetime

import pytest

from application import (
    FilterInput,
    InvalidSortDirection,
    InvalidSortField,
    ProjectTaskList,
    RepeatedSortValue,
    ReversedFilterRange,
    SortControl,
    SortDirection,
    SortInput,
    SortKey,
    TaskSort,
    Tracker,
    TrackerState,
)
from domain import restore_state

PROJECTS = [(1, "Alpha", "first"), (2, "Beta", "")]
NEXT_PROJECT_ID = 3
CREATED = datetime(2026, 10, 6, 12, 0, tzinfo=UTC)


class SequenceClock:
    """Returns each instant it was given, then the last one again; counts every read."""

    def __init__(self, *instants: datetime) -> None:
        self._instants = list(instants) or [CREATED]
        self.reads = 0

    def now(self) -> datetime:
        index = min(self.reads, len(self._instants) - 1)
        self.reads += 1
        return self._instants[index]

    def restart(self, *instants: datetime) -> None:
        """Hand out these instants from now on, with the read count back at zero."""
        self._instants = list(instants)
        self.reads = 0


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


def ids(listed: ProjectTaskList) -> list[int]:
    return [row.task.id for row in listed.rows]


def sort_of(field: str = "", direction: str = "") -> SortInput:
    return SortInput(
        field=(field,) if field else (),
        direction=(direction,) if direction else (),
    )


def seeded_tracker(saver: RecordingSaver | None = None) -> Tracker:
    """Project 1 holds tasks 1 to 4 (task 4 is `Done`, low); project 2 holds task 5."""
    tracker = make_tracker(saver or RecordingSaver())
    tracker.add_task(1, "beta", "high", "dana", "2026-10-10")
    tracker.add_task(1, "Alpha", "low", "ali", "2026-10-02")
    tracker.add_task(1, "alpha", "critical", "dana", "")
    tracker.add_task(1, "Zed", "low", "", "2026-10-02")
    tracker.add_task(2, "Elsewhere", "critical", "dana", "")
    tracker.add_task_label(1, "ui")
    tracker.add_task_label(5, "Bug")
    return tracker


def test_sorted_read_projects_domain_order_and_choices():
    """CP-428, CP-429 to CP-433, CP-435, T4: the rows follow the domain order in both directions,
    the raw choices and the validated defaults come back, and the options stay the project's."""
    tracker = seeded_tracker()
    default = tracker.project_task_list(1, FilterInput())
    assert ids(default) == [2, 4, 1, 3]
    assert default.sorting == TaskSort()
    assert default.sort_fields == SortInput()
    assert default.count_requested is False

    by_title = tracker.project_task_list(1, FilterInput(), sort_fields=sort_of("title"))
    assert ids(by_title) == [2, 3, 1, 4]
    assert by_title.sorting == TaskSort(SortKey.TITLE, SortDirection.ASCENDING, True)
    assert by_title.sort_fields == sort_of("title")

    by_priority = tracker.project_task_list(
        1, FilterInput(), sort_fields=sort_of("priority", "descending")
    )
    assert ids(by_priority) == [3, 1, 2, 4]
    assert by_priority.sorting == TaskSort(SortKey.PRIORITY, SortDirection.DESCENDING, True)

    by_created = tracker.project_task_list(
        1, FilterInput(), sort_fields=sort_of("created_time", "descending")
    )
    assert ids(by_created) == [4, 3, 2, 1]

    assert by_title.task_count == 4
    assert by_title.match_count == 4
    assert by_title.assignees == ("dana", "ali")
    assert by_title.labels == ("ui",)
    other = tracker.project_task_list(2, FilterInput(), sort_fields=sort_of("title"))
    assert ids(other) == [5]
    assert other.task_count == 1
    assert other.labels == ("Bug",)


def test_sorted_read_keeps_filter_membership_and_filter_only_narrowed():
    """CP-434, CP-435, T4: a sort alone requests a count without claiming a filter; a filter plus
    a sort keeps the filter's matches in the sort's order and narrows by the existing rules."""
    tracker = seeded_tracker()
    sort_only = tracker.project_task_list(1, FilterInput(), sort_fields=sort_of("title"))
    assert sort_only.narrowed is False
    assert sort_only.count_requested is True

    filtered = tracker.project_task_list(
        1, FilterInput(priority=("low",)), sort_fields=sort_of("title", "descending")
    )
    assert ids(filtered) == [4, 2]
    assert filtered.narrowed is True
    assert filtered.count_requested is True
    assert filtered.match_count == 2
    assert filtered.task_count == 4

    filter_only = tracker.project_task_list(1, FilterInput(priority=("low",)))
    assert filter_only.narrowed is True
    assert filter_only.count_requested is True
    assert ids(filter_only) == [2, 4]

    blank = tracker.project_task_list(1, FilterInput(), sort_fields=SortInput(field=("",)))
    assert blank.count_requested is False
    assert blank.narrowed is False


def test_sorted_read_projects_all_refusals_without_results():
    """CP-441, CP-442, CP-443, T4: filter and sort problems come back together in domain order,
    with the raw input, empty rows, no validated choices and no visible count."""
    tracker = seeded_tracker()
    fields = FilterInput(due_from=("2026-10-10",), due_to=("2026-10-01",))
    sort_fields = SortInput(field=("colour",), direction=("up", "down"))

    listed = tracker.project_task_list(1, fields, sort_fields=sort_fields)

    assert [type(problem) for problem in listed.problems] == [
        ReversedFilterRange,
        InvalidSortField,
        RepeatedSortValue,
    ]
    assert listed.problems[1].control is SortControl.FIELD
    assert listed.problems[2].control is SortControl.DIRECTION
    assert listed.problems[2].count == 2
    assert listed.fields == fields
    assert listed.sort_fields == sort_fields
    assert listed.rows == ()
    assert listed.match_count == 0
    assert listed.filter is None
    assert listed.sorting is None
    assert listed.count_requested is False
    assert listed.task_count == 4
    assert listed.assignees == ("dana", "ali")
    assert listed.labels == ("ui",)
    direction = tracker.project_task_list(1, FilterInput(), sort_fields=sort_of("", "sideways"))
    assert [type(problem) for problem in direction.problems] == [InvalidSortDirection]


def test_sorted_read_distinguishes_empty_project_and_zero_matches():
    """CP-426, CP-435, CP-442, T4: an empty project ignores malformed choices and shows no count;
    a nonempty project whose valid filter matches nothing still checks the sort, and shows none."""
    tracker = make_tracker(RecordingSaver())
    bad = SortInput(field=("colour",))
    empty = tracker.project_task_list(1, FilterInput(), sort_fields=bad)
    assert (empty.task_count, empty.rows, empty.problems, empty.count_requested) == (
        0,
        (),
        (),
        False,
    )
    assert empty.sorting == TaskSort()

    tracker.add_task(1, "One", "low", "", "")
    zero = tracker.project_task_list(
        1, FilterInput(priority=("critical",)), sort_fields=sort_of("title")
    )
    assert zero.rows == ()
    assert zero.problems == ()
    assert zero.match_count == 0
    assert zero.count_requested is False
    refused = tracker.project_task_list(1, FilterInput(priority=("critical",)), sort_fields=bad)
    assert [type(problem) for problem in refused.problems] == [InvalidSortField]
    assert refused.rows == ()


def test_one_clock_read_serves_sorted_selection_and_row_marking(local_zone):
    """CP-447, T4: a clock whose second read is past local midnight is read once per list; the
    selection and every row's overdue flag use the first local date, the next list the second."""
    late = datetime(2026, 10, 7, 12, 0, tzinfo=UTC)  # local date 2026-10-08
    early = datetime(2026, 10, 5, 12, 0, tzinfo=UTC)  # local date 2026-10-06
    clock = SequenceClock(CREATED)
    tracker = make_tracker(RecordingSaver(), clock)
    task = tracker.add_task(1, "Edge", "low", "", "2026-10-07")
    clock.restart(late, early)

    overdue_on = FilterInput(overdue=("on",))
    listed = tracker.project_task_list(1, overdue_on, sort_fields=sort_of("title"))
    reads_for_first = clock.reads
    again = tracker.project_task_list(1, overdue_on, sort_fields=sort_of("title"))

    assert reads_for_first == 1
    assert clock.reads == 2
    assert ids(listed) == [task.id]
    assert [row.overdue for row in listed.rows] == [True]
    assert again.rows == ()
    assert again.match_count == 0


def test_sorted_reads_never_call_the_saver(utc_zone):
    """CP-447, CP-450, NFR-8, T4: a valid, an invalid, a repeated and a clear-equivalent read leave
    the recording saver with only the saves the setup made."""
    saver = RecordingSaver()
    tracker = seeded_tracker(saver)
    saved_before = len(saver.saved)

    tracker.project_task_list(1, FilterInput(), sort_fields=sort_of("priority", "descending"))
    tracker.project_task_list(1, FilterInput(), sort_fields=sort_of("colour"))
    tracker.project_task_list(1, FilterInput(), sort_fields=SortInput(field=("title", "title")))
    tracker.project_task_list(1, FilterInput(), sort_fields=SortInput())
    tracker.project_task_list(1, FilterInput(), sort_fields=sort_of("title"))
    tracker.project_task_list(1, FilterInput(), sort_fields=sort_of("title"))

    assert len(saver.saved) == saved_before


def test_existing_two_argument_list_read_remains_compatible():
    """CP-447, CP-449, T4: a caller that passes only the filter keeps the old members, the default
    due-date order, no sort request, and the older `project_tasks` read orders as before."""
    tracker = seeded_tracker()

    listed = tracker.project_task_list(1, FilterInput())

    assert ids(listed) == [2, 4, 1, 3]
    assert [row.task.id for row in tracker.project_tasks(1)] == [2, 4, 1, 3]
    assert listed.sort_fields == SortInput()
    assert listed.sorting == TaskSort()
    assert listed.count_requested is False
    assert listed.narrowed is False
    assert listed.problems == ()
    assert listed.fields == FilterInput()
    assert (listed.task_count, listed.match_count) == (4, 4)
    assert listed.filter is not None
    assert listed.filter.narrows is False
