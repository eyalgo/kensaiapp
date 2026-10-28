"""Integration tests of the Tracker over tasks, with hand-written fakes (layer 3).

Checks SRS FR-9 (an action is reported done only after the save), FR-15 (creating a task), FR-16
(editing a task's four fields), FR-25 and FR-36 (the overdue flag and the list order), FR-39 (a
refused action saves nothing), NFR-8 (a failed save leaves the state as it was) and DR-2 (the Task
entity). Change spec rules CP-107, CP-111, CP-114, CP-124, CP-125 and CP-131 are the ones each test
names, CP-533, CP-534 and CP-536 for deleting a task (FR-17), and CP-152, CP-155, CP-157, CP-160, CP-167, CP-168, CP-171 and CP-172 for the edit. No
product name is patched:
the real Tracker is handed each fake, and the machine's time zone is set through the environment.
"""

from __future__ import annotations

import time
from collections.abc import Iterator
from dataclasses import replace
from datetime import UTC, date, datetime

import pytest

from application import (
    SHORT_TEXT_MAX,
    AssigneeNotListed,
    BlankTitle,
    FilterInput,
    InvalidDueDate,
    InvalidPriority,
    ProjectNotFound,
    Task,
    TaskEditContext,
    TaskEditOutcome,
    TaskFields,
    TaskNotFound,
    TaskRow,
    TaskStatus,
    TextField,
    TextTooLong,
    Tracker,
    TrackerState,
)
from domain import Comment, restore_state, restore_task, task_edit_context

PROJECTS = [(1, "Alpha", "first"), (2, "Beta", "")]
NEXT_PROJECT_ID = 3
CREATED = datetime(2026, 10, 11, 12, 0, tzinfo=UTC)


class SequenceClock:
    """Returns each instant it was given, then the last one again; counts every read."""

    def __init__(self, *instants: datetime) -> None:
        self._instants = list(instants) or [CREATED]
        self.reads = 0

    def now(self) -> datetime:
        index = min(self.reads, len(self._instants) - 1)
        self.reads += 1
        return self._instants[index]


def _all_tasks(tracker: Tracker) -> tuple[Task, ...]:
    """Every task through the public reads, one project after the other."""
    return tuple(row.task for project_id in (1, 2) for row in tracker.project_tasks(project_id))


class RecordingSaver:
    """Keeps every state it was handed, and what the tracker held at the moment of each save."""

    def __init__(self) -> None:
        self.saved: list[TrackerState] = []
        self.held_during_save: list[tuple[Task, ...]] = []
        self.tracker: Tracker | None = None

    def save(self, state: TrackerState) -> None:
        if self.tracker is not None:
            self.held_during_save.append(_all_tasks(self.tracker))
        self.saved.append(state)


class FailingSaver:
    def __init__(self) -> None:
        self.calls = 0

    def save(self, state: TrackerState) -> None:
        self.calls += 1
        raise PermissionError("the disk said no")


def _tracker(saver, *assignees: str, clock: SequenceClock | None = None) -> Tracker:
    state = restore_state(PROJECTS, NEXT_PROJECT_ID, assignees)
    return Tracker(state, saver, clock or SequenceClock())


@pytest.fixture
def local_zone(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Set the machine's local zone to UTC+14, where local midnight is ten hours before UTC's."""
    monkeypatch.setenv("TZ", "Pacific/Kiritimati")
    time.tzset()
    yield
    monkeypatch.undo()
    time.tzset()


def test_add_task_saves_once_before_publishing():
    """FR-9, CP-107, CP-111: the saver sees the candidate while the tracker shows the old state."""
    saver = RecordingSaver()
    tracker = _tracker(saver, "Dana")
    saver.tracker = tracker

    task = tracker.add_task(1, "Write it", "high", "Dana", "2026-12-01")

    assert len(saver.saved) == 1
    assert saver.saved[0].tasks == (task,)
    assert saver.saved[0].next_task_id == 2
    assert saver.held_during_save == [()]
    assert tracker.task(task.id) == task
    assert task.title == "Write it"
    assert task.assignee == "Dana"
    assert task.due_date == date(2026, 12, 1)
    assert task.status is TaskStatus.TODO


def test_refused_task_add_never_calls_the_saver():
    """FR-39, CP-111 to CP-113: each refusal propagates, leaves every read as it was, no identity."""
    saver = RecordingSaver()
    clock = SequenceClock()
    tracker = _tracker(saver, "Dana", clock=clock)
    tracker.add_task(1, "Kept", "", "", "")
    saved_before = len(saver.saved)

    with pytest.raises(ProjectNotFound):
        tracker.add_task(9, "t", "", "", "")
    with pytest.raises(TextTooLong) as too_long:
        tracker.add_task(1, "t" * (SHORT_TEXT_MAX + 1), "", "", "")
    with pytest.raises(BlankTitle):
        tracker.add_task(1, "  ", "", "", "")
    with pytest.raises(InvalidPriority):
        tracker.add_task(1, "t", "urgent", "", "")
    with pytest.raises(AssigneeNotListed) as not_listed:
        tracker.add_task(1, "t", "", "Zed", "")
    with pytest.raises(InvalidDueDate):
        tracker.add_task(1, "t", "", "", "2026-13-01")

    assert too_long.value.field is TextField.TITLE
    assert not_listed.value.name == "Zed"
    assert len(saver.saved) == saved_before
    assert [task.title for task in _all_tasks(tracker)] == ["Kept"]
    assert tracker.add_task(1, "Next", "", "", "").id == 2


def test_failed_save_keeps_tasks_and_counter():
    """NFR-8, CP-122: the failure propagates, old reads remain, the identity is not consumed."""
    saver = FailingSaver()
    tracker = _tracker(saver)

    with pytest.raises(PermissionError, match="the disk said no"):
        tracker.add_task(1, "Lost", "", "", "")

    assert saver.calls == 1
    assert _all_tasks(tracker) == ()
    assert tracker.task(1) is None

    recorder = RecordingSaver()
    healthy = Tracker(restore_state(PROJECTS, NEXT_PROJECT_ID), recorder, SequenceClock())
    assert healthy.add_task(1, "First", "", "", "").id == 1


def test_add_uses_the_current_people_list():
    """CP-119: a name removed after a page was read is refused; earlier tasks keep the name."""
    saver = RecordingSaver()
    tracker = _tracker(saver, "Dana", "Ari")
    earlier = tracker.add_task(1, "Early", "", "Dana", "")

    tracker.remove_assignee("Dana")

    with pytest.raises(AssigneeNotListed):
        tracker.add_task(1, "Late", "", "Dana", "")
    assert tracker.task(earlier.id) == earlier
    assert earlier.assignee == "Dana"
    assert tracker.add_task(1, "Other", "", "Ari", "").assignee == "Ari"


def test_project_and_people_actions_retain_tasks():
    """CP-105, CP-113: each existing action keeps every task and counter and saves the whole."""
    saver = RecordingSaver()
    tracker = _tracker(saver, "Dana")
    task = tracker.add_task(1, "Keep me", "", "Dana", "")

    tracker.create_project("Gamma", "")
    tracker.add_assignee("Ari")
    tracker.remove_assignee("Dana")

    assert tracker.task(task.id) == task
    assert [state.tasks for state in saver.saved] == [(task,)] * 4
    assert [state.next_task_id for state in saver.saved] == [2] * 4
    assert saver.saved[-1].assignees == ("Ari",)


def test_task_lookup_and_project_rows_return_complete_values():
    """CP-114, CP-124, CP-125: lookup, isolation, domain order, flags, and no read saves."""
    saver = RecordingSaver()
    clock = SequenceClock(CREATED)
    tracker = _tracker(saver, clock=clock)
    undated = tracker.add_task(1, "Undated", "", "", "")
    late = tracker.add_task(1, "Late", "", "", "2026-10-10")
    soon = tracker.add_task(1, "Soon", "", "", "2026-10-20")
    other = tracker.add_task(2, "Elsewhere", "", "", "")
    saves = len(saver.saved)

    rows = tracker.project_tasks(1)

    assert rows == (TaskRow(late, True), TaskRow(soon, False), TaskRow(undated, False))
    assert tracker.project_tasks(2) == (TaskRow(other, False),)
    assert tracker.project_tasks(3) == ()
    assert tracker.task(0) is None
    assert tracker.task(99) is None
    assert tracker.task(soon.id) == soon
    assert len(saver.saved) == saves


def test_project_page_uses_one_injected_local_date(local_zone):
    """CP-131, CP-140: one Clock read per projection, converted to the machine-local date."""
    # 2026-10-10 15:00 UTC is already 2026-10-11 05:00 in UTC+14, so a task due on the
    # 10th is overdue by local date but would not be by the UTC date.
    before_local_midnight = datetime(2026, 10, 10, 9, 0, tzinfo=UTC)  # local 2026-10-10 23:00
    after_local_midnight = datetime(2026, 10, 10, 11, 0, tzinfo=UTC)  # local 2026-10-11 01:00
    clock = SequenceClock(CREATED, before_local_midnight, after_local_midnight)
    tracker = _tracker(RecordingSaver(), clock=clock)
    tracker.add_task(1, "Due the tenth", "", "", "2026-10-10")
    assert clock.reads == 1

    first = tracker.project_tasks(1)
    assert clock.reads == 2
    assert [row.overdue for row in first] == [False]

    second = tracker.project_tasks(1)
    assert clock.reads == 3
    assert [row.overdue for row in second] == [True]


def test_add_records_the_injected_creation_instant():
    """CP-111: the task holds the one instant the clock supplied, read once for the add."""
    instant = datetime(2026, 3, 4, 5, 6, 7, tzinfo=UTC)
    clock = SequenceClock(instant)
    tracker = _tracker(RecordingSaver(), clock=clock)

    task = tracker.add_task(1, "Timed", "", "", "")

    assert task.created_at == instant
    assert clock.reads == 1


def _stored_task(**changes) -> Task:
    values = {
        "id": 1,
        "project_id": 1,
        "title": "Set up CI",
        "status": "todo",
        "priority": "high",
        "assignee": "Dana",
        "labels": ("bug",),
        "due_date": "2026-10-20",
        "created_at": CREATED,
        "comments": (Comment(text="Looks fine", author="Dana", created_at=CREATED),),
    }
    values.update(changes)
    return restore_task(**values)


def _tracker_holding(saver, *tasks: Task, assignees=("Dana", "Ari"), clock=None) -> Tracker:
    state = restore_state(
        PROJECTS,
        NEXT_PROJECT_ID,
        assignees,
        tasks=tasks,
        next_task_id=max(task.id for task in tasks) + 1,
    )
    return Tracker(state, saver, clock or SequenceClock())


SAVED = TaskFields(title="Set up CI", priority="high", assignee="Dana", due_date="2026-10-20")


def test_tracker_edit_saves_once_before_publishing():
    """CP-155, CP-157: one whole-state save while reads show the old task; then the new is current."""
    saver = RecordingSaver()
    original = _stored_task()
    tracker = _tracker_holding(saver, original)
    saver.tracker = tracker

    outcome = tracker.edit_task(1, TaskFields(title="Renamed"), SAVED)

    assert isinstance(outcome, TaskEditOutcome) and outcome.changed is True
    assert len(saver.saved) == 1
    assert saver.saved[0].tasks == (outcome.task,)
    assert saver.held_during_save == [(original,)]
    assert tracker.task(1) == outcome.task == replace(original, title="Renamed")


def test_tracker_edit_changed_to_current_still_saves():
    """CP-155: a difference between submitted and shown saves, though the task already holds it."""
    saver = RecordingSaver()
    tracker = _tracker_holding(saver, _stored_task(title="Already"))

    outcome = tracker.edit_task(1, TaskFields(title="Already"), TaskFields(title="Before"))

    assert outcome.changed is True
    assert len(saver.saved) == 1
    assert tracker.task(1) == outcome.task


def test_tracker_unchanged_edit_never_saves():
    """CP-157: nothing changed returns the current task with no save and no publication."""
    saver = RecordingSaver()
    original = _stored_task(assignee="Carol")
    tracker = _tracker_holding(saver, original)

    outcome = tracker.edit_task(1, SAVED, SAVED)
    absent = tracker.edit_task(1, TaskFields(title="Other"), TaskFields())

    assert outcome == absent == TaskEditOutcome(task=original, changed=False)
    assert saver.saved == []
    assert tracker.task(1) == original


@pytest.mark.parametrize(
    ("task_id", "submitted", "refusal"),
    [
        (9, TaskFields(title="x"), TaskNotFound),
        (1, TaskFields(title="t" * (SHORT_TEXT_MAX + 1)), TextTooLong),
        (1, TaskFields(title=" "), BlankTitle),
        (1, TaskFields(priority="urgent"), InvalidPriority),
        (1, TaskFields(assignee="Zed"), AssigneeNotListed),
        (1, TaskFields(due_date="2026-13-01"), InvalidDueDate),
    ],
)
def test_tracker_refused_edit_never_saves(task_id, submitted, refusal):
    """CP-160, CP-167, CP-172: every typed refusal passes through; nothing is saved or changed."""
    saver = RecordingSaver()
    original = _stored_task()
    tracker = _tracker_holding(saver, original)

    with pytest.raises(refusal):
        tracker.edit_task(task_id, submitted, SAVED)

    assert saver.saved == []
    assert tracker.task(1) == original


def test_tracker_failed_edit_keeps_current_state():
    """CP-168: a saver failure propagates and the task and the whole state stay as they were."""
    saver = FailingSaver()
    original = _stored_task()
    tracker = _tracker_holding(saver, original)

    with pytest.raises(PermissionError, match="the disk said no"):
        tracker.edit_task(1, TaskFields(title="Lost"), SAVED)

    assert saver.calls == 1
    assert tracker.task(1) == original
    assert tracker.project_tasks(1) == (TaskRow(original, False),)


def test_tracker_edit_never_reads_clock_or_saved_data():
    """CP-171: no clock read for an edit or a context lookup; the saver is only ever saved to."""
    saver = RecordingSaver()
    clock = SequenceClock()
    tracker = _tracker_holding(saver, _stored_task(), clock=clock)

    tracker.edit_task(1, TaskFields(title="Renamed"), SAVED)
    tracker.edit_task(1, SAVED, SAVED)
    tracker.task_edit_context(1)
    tracker.task_edit_context(9)

    assert clock.reads == 0
    assert len(saver.saved) == 1


@pytest.mark.parametrize("status", ["todo", "in-progress", "done", "cancelled"])
def test_tracker_edit_preserves_other_fields_in_every_status(status):
    """CP-152, CP-171: protected values stay, and an untouched field keeps a concurrent value."""
    saver = RecordingSaver()
    original = _stored_task(status=status, priority="critical", assignee="Ari")
    other = _stored_task(id=2, project_id=2, title="Elsewhere")
    tracker = _tracker_holding(saver, original, other)
    shown = TaskFields(title="Set up CI", priority="low", assignee="Dana")

    outcome = tracker.edit_task(1, TaskFields("Renamed", "low", "Dana"), shown)

    assert outcome.task == replace(original, title="Renamed")
    assert saver.saved[0].tasks == (outcome.task, other)
    assert saver.saved[0].next_task_id == 3
    assert saver.saved[0].projects == restore_state(PROJECTS, NEXT_PROJECT_ID).projects
    assert saver.saved[0].assignees == ("Dana", "Ari")


def test_tracker_task_edit_context_delegates_saved_values():
    """CP-145, CP-148: listed, unlisted, unassigned and missing match the domain; nothing saves."""
    saver = RecordingSaver()
    tasks = (
        _stored_task(),
        _stored_task(id=2, assignee="Carol"),
        _stored_task(id=3, assignee=None, due_date=None),
    )
    tracker = _tracker_holding(saver, *tasks)
    state = restore_state(PROJECTS, NEXT_PROJECT_ID, ("Dana", "Ari"), tasks=tasks, next_task_id=4)

    for task_id in (1, 2, 3):
        context = tracker.task_edit_context(task_id)
        assert isinstance(context, TaskEditContext)
        assert context == task_edit_context(state, task_id)
    assert tracker.task_edit_context(2).assignee_unlisted is True  # type: ignore[union-attr]
    assert tracker.task_edit_context(99) is None
    assert saver.saved == []


def test_tracker_edited_due_date_updates_list_order_and_overdue():
    """CP-171: the list recomputes order and the overdue flag from the edited date, no clock write."""
    saver = RecordingSaver()
    clock = SequenceClock(CREATED)
    tracker = _tracker_holding(
        saver,
        _stored_task(id=1, title="A", due_date="2026-10-20"),
        _stored_task(id=2, title="B", due_date="2026-10-25"),
        _stored_task(id=3, title="C", due_date=None),
        clock=clock,
    )

    def titles() -> list[str]:
        return [row.task.title for row in tracker.project_tasks(1)]

    assert titles() == ["A", "B", "C"]
    reads = clock.reads

    tracker.edit_task(2, TaskFields(due_date="2026-10-15"), TaskFields(due_date="2026-10-25"))
    assert clock.reads == reads
    assert titles() == ["B", "A", "C"]

    tracker.edit_task(3, TaskFields(due_date="2026-10-20"), TaskFields(due_date=""))
    assert titles() == ["B", "A", "C"]  # equal dates keep identity order

    tracker.edit_task(1, TaskFields(due_date="2026-10-01"), TaskFields(due_date="2026-10-20"))
    rows = tracker.project_tasks(1)
    assert [(row.task.title, row.overdue) for row in rows] == [
        ("A", True),
        ("B", False),
        ("C", False),
    ]


def _every_read(tracker: Tracker) -> tuple:
    """The public reads a deletion must change together or not at all, without any clock read."""
    return (
        tracker.task(1),
        tracker.task(2),
        tracker.task_edit_context(1),
        tracker.task_edit_context(2),
        tracker.project_tasks(1),
        tracker.project_tasks(2),
        tracker.project_task_list(1, FilterInput()),
        tracker.all_task_list(FilterInput()),
        tracker.project_summary(1),
        tracker.project_summary(2),
        tracker.projects(),
        tracker.assignees(),
        tracker.operator_name(),
    )


def _holding_two_tasks(saver, clock=None) -> Tracker:
    second_comments = (
        Comment(text="One", author="Dana", created_at=CREATED),
        Comment(text="Two", author="Ari", created_at=CREATED),
    )
    return _tracker_holding(
        saver,
        _stored_task(id=1, title="First"),
        _stored_task(id=2, title="Second", comments=second_comments),
        clock=clock,
    )


class _ReadingSaver(RecordingSaver):
    """A recording saver that also keeps every public read the tracker gave at the moment of a save."""

    def __init__(self) -> None:
        super().__init__()
        self.reads_during_save: list[tuple] = []

    def save(self, state: TrackerState) -> None:
        if self.tracker is not None:
            self.reads_during_save.append(_every_read(self.tracker))
        super().save(state)


def test_delete_task_saves_once_before_publishing():
    """CP-533: the saver gets the exact candidate once while every read still shows the old task."""
    saver = _ReadingSaver()
    tracker = _holding_two_tasks(saver)
    saver.tracker = tracker
    original = tracker.task(2)
    survivor = tracker.task(1)
    assert original is not None and survivor is not None
    held = _every_read(tracker)
    expected = restore_state(
        PROJECTS, NEXT_PROJECT_ID, ("Dana", "Ari"), tasks=(survivor,), next_task_id=3
    )

    removed = tracker.delete_task(2)

    assert removed == original
    assert saver.saved == [expected]
    assert saver.reads_during_save == [held]
    assert saver.held_during_save == [(survivor, original)]
    assert tracker.task(2) is None and tracker.task_edit_context(2) is None
    assert [row.task.id for row in tracker.project_tasks(1)] == [1]
    assert [row.task.id for row in tracker.all_task_list(FilterInput()).rows] == [1]
    summary = tracker.project_summary(1)
    assert summary is not None and summary.total == 1


def test_delete_task_returns_metadata_from_the_current_task():
    """CP-534: a title edited before the deletion is the one returned, with the owning project."""
    saver = RecordingSaver()
    tracker = _tracker_holding(saver, _stored_task(id=1, title="Old", project_id=2))
    tracker.edit_task(1, TaskFields(title="Edited by now"), TaskFields(title="Old"))

    removed = tracker.delete_task(1)

    assert (removed.title, removed.project_id) == ("Edited by now", 2)
    assert tracker.task(1) is None


def test_missing_delete_calls_no_saver():
    """A task nobody holds is refused as TaskNotFound with no save, and every read is unchanged."""
    saver = RecordingSaver()
    tracker = _holding_two_tasks(saver)
    before = _every_read(tracker)

    with pytest.raises(TaskNotFound):
        tracker.delete_task(99)

    assert saver.saved == []
    assert _every_read(tracker) == before


def test_failed_delete_preserves_every_application_read():
    """CP-536: the saver's own error propagates after one attempt; nothing read has changed."""
    saver = FailingSaver()
    tracker = _holding_two_tasks(saver)
    before = _every_read(tracker)

    with pytest.raises(PermissionError, match="the disk said no"):
        tracker.delete_task(2)

    assert saver.calls == 1
    assert _every_read(tracker) == before


def test_deletion_needs_no_clock_read():
    """Design B: a successful, a refused and a failed deletion never ask the clock for an instant."""
    clock = SequenceClock()
    tracker = _holding_two_tasks(RecordingSaver(), clock=clock)
    with pytest.raises(TaskNotFound):
        tracker.delete_task(99)
    failing = _holding_two_tasks(FailingSaver(), clock=clock)
    with pytest.raises(PermissionError):
        failing.delete_task(2)

    tracker.delete_task(2)

    assert clock.reads == 0
