"""Integration tests of the Tracker's project Summary read, with hand-written fakes (layer 3).

Checks SRS FR-38 (a project's summary), FR-25 (today is the machine's local date, the day the
overdue count is taken on) and NFR-8 (a read never reaches the saver). Change spec rules CP-493,
CP-494 and CP-497 are the ones each test names; the design row is T05. No product name is patched:
the real Tracker is handed each fake, and the machine's time zone is set through the environment.
"""

from __future__ import annotations

import time
from collections.abc import Iterator
from datetime import UTC, datetime

import pytest

from application import Priority, Project, ProjectSummary, TaskStatus, Tracker, TrackerState
from domain import restore_state

PROJECTS = [(1, "Alpha", "first"), (2, "Beta", ""), (3, "Gamma", "empty")]
NEXT_PROJECT_ID = 4
NOON = datetime(2026, 10, 27, 12, 0, tzinfo=UTC)
NEXT_NOON = datetime(2026, 10, 28, 12, 0, tzinfo=UTC)


class SequenceClock:
    """Returns each instant it was given, then the last one again; counts every read."""

    def __init__(self, *instants: datetime) -> None:
        self._instants = list(instants) or [NOON]
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


def make_tracker(
    saver: RecordingSaver,
    clock: SequenceClock,
    projects: list[tuple[int, str, str]] = PROJECTS,
) -> Tracker:
    state = restore_state(projects, NEXT_PROJECT_ID, ("ari", "bo"))
    return Tracker(state, saver, clock)


def seeded_tracker(saver: RecordingSaver, clock: SequenceClock) -> Tracker:
    """Alpha holds an overdue open task, a task due today, a done task and an unlisted name."""
    tracker = make_tracker(saver, clock)
    tracker.add_task(1, "late", "low", "ari", "2026-10-26")
    tracker.add_task(1, "today", "high", "", "2026-10-27")
    tracker.add_task(1, "finished", "medium", "bo", "2026-10-01")
    tracker.add_task(2, "elsewhere", "critical", "bo", "")
    tracker.move_task(3, "done")
    return tracker


def assignee_rows(summary: ProjectSummary) -> list[tuple[str | None, int]]:
    return [(row.assignee, row.count) for row in summary.assignee_counts]


def test_summary_reads_the_injected_clock_once_per_call(utc_zone):
    """CP-497, T05: one clock read for a populated, an empty and a missing project, no save."""
    saver = RecordingSaver()
    clock = SequenceClock()
    tracker = seeded_tracker(saver, clock)
    saves_before = len(saver.saved)

    for project_id in (1, 3, 99):
        clock.restart(NOON)
        tracker.project_summary(project_id)
        assert clock.reads == 1, project_id

    assert len(saver.saved) == saves_before


def test_summary_uses_the_machine_local_calendar_day(local_zone):
    """CP-497, T05: the instant is 27 October in UTC and 28 October at UTC+14; a task due the 27th
    is overdue on the local day, and an unconverted date would not count it."""
    saver = RecordingSaver()
    clock = SequenceClock()
    tracker = make_tracker(saver, clock)
    tracker.add_task(1, "due on the 27th", "medium", "", "2026-10-27")
    clock.restart(NOON)

    summary = tracker.project_summary(1)

    assert summary is not None
    assert summary.overdue == 1
    assert NOON.date().isoformat() == "2026-10-27"


def test_summary_recomputes_after_midnight(utc_zone):
    """CP-494, T05: the next call, on the next day, counts the task overdue; the earlier result is
    the snapshot it was."""
    saver = RecordingSaver()
    clock = SequenceClock()
    tracker = make_tracker(saver, clock)
    tracker.add_task(1, "due on the 27th", "medium", "", "2026-10-27")
    clock.restart(NOON, NEXT_NOON)

    first = tracker.project_summary(1)
    second = tracker.project_summary(1)

    assert first is not None and second is not None
    assert (first.overdue, second.overdue) == (0, 1)
    assert first.overdue == 0
    assert first is not second


def test_summary_reads_current_tasks_and_assignees_without_saving(utc_zone):
    """T05: counts follow the existing add, move and assignee actions, and a read saves nothing."""
    saver = RecordingSaver()
    clock = SequenceClock()
    tracker = seeded_tracker(saver, clock)
    clock.restart(NOON)

    summary = tracker.project_summary(1)

    assert summary is not None
    assert summary.total == 3
    assert [(row.status, row.count) for row in summary.status_counts] == [
        (TaskStatus.TODO, 2),
        (TaskStatus.IN_PROGRESS, 0),
        (TaskStatus.DONE, 1),
        (TaskStatus.CANCELLED, 0),
    ]
    assert [(row.priority, row.count) for row in summary.priority_counts] == [
        (Priority.LOW, 1),
        (Priority.MEDIUM, 1),
        (Priority.HIGH, 1),
        (Priority.CRITICAL, 0),
    ]
    assert summary.overdue == 1
    assert summary.no_due_date == 0
    assert assignee_rows(summary) == [("ari", 1), ("bo", 0), (None, 1)]

    saves_before = len(saver.saved)
    tracker.remove_assignee("ari")
    tracker.move_task(2, "cancelled")
    tracker.add_task(1, "new", "critical", "bo", "")
    after_actions = len(saver.saved)
    clock.restart(NOON)

    changed = tracker.project_summary(1)

    assert after_actions == saves_before + 3
    assert len(saver.saved) == after_actions
    assert changed is not None
    assert changed.total == 4
    assert assignee_rows(changed) == [("bo", 1), ("ari", 1), (None, 0)]
    assert tracker.project_summary(1) == changed


def test_summary_distinguishes_missing_empty_and_current_project_metadata(utc_zone):
    """CP-493, T05, T07: absence is None, an empty project is zeros, and the project comes back
    exactly as saved; the same identity under a new name carries the new name."""
    clock = SequenceClock()
    tracker = make_tracker(RecordingSaver(), clock)

    assert tracker.project_summary(99) is None
    empty = tracker.project_summary(3)
    assert empty is not None
    assert empty.project == Project(3, "Gamma", "empty")
    assert empty.total == 0

    renamed = make_tracker(
        RecordingSaver(), clock, [(1, "  Renamed  ", "first"), (2, "Beta", ""), (3, "Gamma", "")]
    )
    before = tracker.project_summary(1)
    after = renamed.project_summary(1)
    assert before is not None and after is not None
    assert (before.project.id, after.project.id) == (1, 1)
    assert (before.project.name, after.project.name) == ("Alpha", "  Renamed  ")
