"""Integration tests of the Tracker's move action with a hand-written saver and clock (layer 3).

Checks SRS FR-18 (a task moves along the moves its status allows and is saved before it shows),
AC-9 (a saved change survives a restart), AC-13 (a task moved to done is no longer overdue) and
AC-18 (a failing save changes nothing). Change spec rules CP-293 to CP-295, CP-302, CP-307, CP-308
and CP-311 and NFDR QC-21 and QC-28 are the ones each test names. No product name is patched: the
real Tracker is handed each fake, and the clock is handed in.
"""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest

from application import (
    InvalidTaskStatus,
    MoveNotAllowed,
    Task,
    TaskNotFound,
    TaskStatus,
    Tracker,
    TrackerState,
)
from domain import Comment, restore_state, restore_task
from persistence.saved_data import FILE_NAME, SavedData

PROJECTS = [(1, "Alpha", "first"), (2, "Beta", "")]
CREATED = datetime(2026, 10, 11, 12, 0, tzinfo=UTC)
TODAY = datetime(2026, 10, 19, 12, 0, tzinfo=UTC)
PEOPLE = ("Dana", "Ari")


class FixedClock:
    def __init__(self, instant: datetime = CREATED) -> None:
        self._instant = instant

    def now(self) -> datetime:
        return self._instant


def _task(task_id: int, status: str, title: str, due_date: str | None = None) -> Task:
    comment = Comment(text="first", author="Dana", created_at=CREATED)
    return restore_task(
        id=task_id,
        project_id=1,
        title=title,
        status=status,
        priority="high",
        assignee="Dana",
        labels=["bug", "ui"],
        due_date=due_date,
        created_at=CREATED,
        comments=[comment, comment],
    )


def _state(*tasks: Task) -> TrackerState:
    return restore_state(PROJECTS, 3, PEOPLE, tasks=tasks, next_task_id=len(tasks) + 1)


class RecordingSaver:
    """Keeps every state it was handed, and what the tracker showed at the moment of each save."""

    def __init__(self) -> None:
        self.saved: list[TrackerState] = []
        self.shown_during_save: list[Task | None] = []
        self.tracker: Tracker | None = None

    def save(self, state: TrackerState) -> None:
        if self.tracker is not None:
            self.shown_during_save.append(self.tracker.task(1))
        self.saved.append(state)


class FailingSaver:
    def __init__(self) -> None:
        self.calls = 0

    def save(self, state: TrackerState) -> None:
        self.calls += 1
        raise PermissionError("the disk said no")


def _tracker(saver, *tasks: Task, clock: FixedClock | None = None) -> Tracker:
    tracker = Tracker(_state(*tasks), saver, clock or FixedClock())
    if isinstance(saver, RecordingSaver):
        saver.tracker = tracker
    return tracker


def _status_of(tracker: Tracker, task_id: int = 1) -> TaskStatus:
    task = tracker.task(task_id)
    assert task is not None
    return task.status


def test_the_names_web_needs_to_tell_a_move_refusal_are_reexported():
    """QC-5, QC-16: web reaches the two move refusals through application alone."""
    assert issubclass(MoveNotAllowed, Exception) and issubclass(InvalidTaskStatus, Exception)


def test_the_move_is_saved_before_it_becomes_current():
    """CP-302, SD-2: the saver sees the candidate while the tracker still shows the old status.

    A refused move reaches no save and leaves the state.
    """
    saver = RecordingSaver()
    tracker = _tracker(saver, _task(1, "todo", "Set up CI"), _task(2, "done", "Other"))
    before = tracker.task(1)

    moved = tracker.move_task(1, "in-progress")

    assert moved.status is TaskStatus.IN_PROGRESS
    assert len(saver.saved) == 1
    assert saver.shown_during_save == [before]
    assert saver.saved[0].tasks[0].status is TaskStatus.IN_PROGRESS
    assert tracker.task(1) == moved
    with pytest.raises(MoveNotAllowed):
        tracker.move_task(1, "in-progress")
    with pytest.raises(MoveNotAllowed):
        tracker.move_task(2, "todo")
    with pytest.raises(InvalidTaskStatus):
        tracker.move_task(1, "finished")
    with pytest.raises(TaskNotFound):
        tracker.move_task(999, "done")
    assert len(saver.saved) == 1
    assert tracker.task(1) == moved


def test_a_moved_task_survives_a_restart_and_only_its_status_differs_in_the_saved_file(
    tmp_path: Path,
):
    """CP-295: Write it, with its fields, moves to done; the saved JSON differs in its status only."""
    location = tmp_path / "data"
    other = _task(2, "todo", "Other")
    written = restore_task(
        id=1,
        project_id=1,
        title="Write it",
        status="in-progress",
        priority="high",
        assignee="Dana",
        labels=["ui", "bug"],
        due_date="2026-12-01",
        created_at=CREATED,
        comments=[Comment(text="one", author="Dana", created_at=CREATED)] * 2,
    )
    saved_data = SavedData(location)
    saved_data.save(_state(written, other))
    before = json.loads((location / FILE_NAME).read_text(encoding="utf-8"))
    tracker = Tracker(saved_data.load() or _state(), saved_data, FixedClock())

    tracker.move_task(1, "done")

    after = json.loads((location / FILE_NAME).read_text(encoding="utf-8"))
    assert before["tasks"][0].pop("status") == "in-progress"
    assert after["tasks"][0].pop("status") == "done"
    assert after == before
    restarted = saved_data.load()
    assert restarted is not None
    assert Tracker(restarted, saved_data, FixedClock()).task(1) == replace(
        written, status=TaskStatus.DONE
    )


def test_a_failing_saver_raises_and_leaves_the_current_state_as_it_was():
    """CP-311: the saver's error reaches the caller and the state is the old one."""
    saver = FailingSaver()
    tracker = _tracker(saver, _task(1, "todo", "Set up CI"))
    before = tracker.task(1)

    with pytest.raises(PermissionError):
        tracker.move_task(1, "in-progress")

    assert saver.calls == 1
    assert tracker.task(1) == before


def test_allowed_moves_gives_the_domain_tuples():
    """CP-293, QC-21: the query hands the workflow's own tuples on, unchanged."""
    tracker = _tracker(RecordingSaver())
    assert tracker.allowed_moves(TaskStatus.TODO) == (TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED)
    assert tracker.allowed_moves(TaskStatus.IN_PROGRESS) == (
        TaskStatus.DONE,
        TaskStatus.CANCELLED,
        TaskStatus.TODO,
    )
    assert tracker.allowed_moves(TaskStatus.DONE) == ()
    assert tracker.allowed_moves(TaskStatus.CANCELLED) == ()


def test_a_task_due_yesterday_moved_to_done_is_not_overdue_and_moved_to_todo_still_is():
    """CP-307, QC-28: overdue follows the saved status; the clock is handed in, nothing patched."""
    clock = FixedClock(TODAY)
    due = "2026-10-18"
    done_tracker = _tracker(
        RecordingSaver(), _task(1, "in-progress", "A", due_date=due), clock=clock
    )
    todo_tracker = _tracker(
        RecordingSaver(), _task(1, "in-progress", "B", due_date=due), clock=clock
    )
    assert done_tracker.project_tasks(1)[0].overdue is True

    done_tracker.move_task(1, "done")
    todo_tracker.move_task(1, "todo")

    assert done_tracker.project_tasks(1)[0].overdue is False
    assert todo_tracker.project_tasks(1)[0].overdue is True


def test_move_is_checked_against_the_current_state_not_a_stale_page():
    """CP-308: the same todo to in-progress move asked twice is refused the second time."""
    saver = RecordingSaver()
    tracker = _tracker(saver, _task(1, "todo", "Set up CI"))

    tracker.move_task(1, "in-progress")
    with pytest.raises(MoveNotAllowed):
        tracker.move_task(1, "in-progress")

    assert len(saver.saved) == 1
    assert _status_of(tracker) is TaskStatus.IN_PROGRESS
