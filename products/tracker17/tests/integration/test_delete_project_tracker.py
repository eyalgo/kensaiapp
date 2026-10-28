"""Integration tests of the Tracker over deleting a project, with hand-written fakes (layer 3).

Checks SRS FR-9 (an action is reported done only after the save), FR-13 (deleting a project with its
tasks and their comments), NFR-8 (a failed save leaves the state as it was) and NFDR QC-54 (the
saver receives only saves). Change spec rules CP-575, CP-576, CP-578 and CP-591 are the ones each
test names. No product name is patched: the real Tracker is handed each fake. The cascade rule is
tested in tests/unit/test_projects.py.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from application import (
    Comment,
    FilterInput,
    Project,
    ProjectDeletionOutcome,
    ProjectNotFound,
    Tracker,
    TrackerState,
)
from domain import restore_state, restore_task

CREATED_AT = datetime(2026, 10, 28, 12, 0, tzinfo=UTC)


class FixedClock:
    def now(self) -> datetime:
        return CREATED_AT


class ObservingSaver:
    """Keeps every state it is handed, and what the tracker shows while each save is under way."""

    def __init__(self) -> None:
        self.saved: list[TrackerState] = []
        self.shown_during_save: list[tuple[str | None, int]] = []
        self.tracker: Tracker | None = None

    def save(self, state: TrackerState) -> None:
        if self.tracker is not None:
            project = self.tracker.project(2)
            self.shown_during_save.append(
                (
                    None if project is None else project.name,
                    self.tracker.project_task_list(2, FilterInput()).task_count,
                )
            )
        self.saved.append(state)


class FailingSaver:
    def __init__(self) -> None:
        self.calls = 0

    def save(self, state: TrackerState) -> None:
        self.calls += 1
        raise PermissionError("the disk said no")


class CallRecordingSaver:
    """A saver that answers save and records any other attribute the tracker reaches for."""

    def __init__(self) -> None:
        self.saves = 0
        self.other_access: list[str] = []

    def save(self, state: TrackerState) -> None:
        self.saves += 1

    def __getattr__(self, name: str):
        self.other_access.append(name)
        raise AttributeError(name)


def _comments(count: int) -> list[Comment]:
    return [
        Comment(text=f"Note {number}", author="Dana", created_at=CREATED_AT)
        for number in range(count)
    ]


def _state() -> TrackerState:
    """Project 2 holds a task in each status, with comments; projects 1 and 3 hold survivors."""
    tasks = [
        restore_task(5, 1, "Survivor", "todo", "medium", None, [], None, CREATED_AT, _comments(1)),
        restore_task(
            6, 2, "Open", "todo", "high", "Dana", ["ui"], "2026-11-01", CREATED_AT, _comments(2)
        ),
        restore_task(7, 2, "Running", "in-progress", "low", None, [], None, CREATED_AT, []),
        restore_task(8, 2, "Finished", "done", "low", None, [], None, CREATED_AT, _comments(1)),
        restore_task(9, 2, "Dropped", "cancelled", "low", None, [], None, CREATED_AT, []),
        restore_task(10, 3, "Elsewhere", "todo", "medium", None, [], None, CREATED_AT, []),
    ]
    return restore_state(
        [(1, "Alpha", "first"), (2, "Beta", "second"), (3, "Gamma", "")],
        4,
        ("Dana", "Sam"),
        tasks=tasks,
        next_task_id=11,
        operator_name="Dana",
    )


def _tracker(saver) -> Tracker:
    return Tracker(_state(), saver, FixedClock())


def _everything_shown(tracker: Tracker):
    """Every value the tracker shows for projects, tasks, lists and names."""
    return (
        tracker.projects(),
        [tracker.project(identity) for identity in (1, 2, 3)],
        [tracker.task(identity) for identity in range(5, 11)],
        [tracker.project_task_list(identity, FilterInput()) for identity in (1, 2, 3)],
        tracker.all_task_list(FilterInput()),
        [tracker.project_summary(identity) for identity in (1, 2, 3)],
        tracker.assignees(),
        tracker.operator_name(),
    )


def test_delete_project_saves_once_before_publishing():
    """FR-9, CP-575: the saver sees the exact candidate while every read still shows the old
    project; afterwards the outcome is returned and every read shows the new state."""
    saver = ObservingSaver()
    tracker = _tracker(saver)
    saver.tracker = tracker

    outcome = tracker.delete_project(2)

    assert outcome == ProjectDeletionOutcome(project=Project(2, "Beta", "second"), task_count=4)
    assert saver.shown_during_save == [("Beta", 4)]
    assert len(saver.saved) == 1
    candidate = saver.saved[0]
    assert [project.id for project in candidate.projects] == [1, 3]
    assert [task.id for task in candidate.tasks] == [5, 10]
    assert (candidate.next_project_id, candidate.next_task_id) == (4, 11)
    assert tracker.project(2) is None
    assert [task for task in range(6, 10) if tracker.task(task) is not None] == []
    assert [project.id for project in tracker.projects()] == [1, 3]
    assert tracker.all_task_list(FilterInput()).task_count == 2
    assert (tracker.assignees(), tracker.operator_name()) == (("Dana", "Sam"), "Dana")


def test_delete_project_refusal_never_calls_the_saver():
    """CP-582: a missing or already removed target raises ProjectNotFound, saves nothing and
    leaves the state as it was."""
    saver = ObservingSaver()
    tracker = _tracker(saver)
    before = _everything_shown(tracker)

    with pytest.raises(ProjectNotFound):
        tracker.delete_project(99)
    assert saver.saved == []
    assert _everything_shown(tracker) == before

    tracker.delete_project(2)
    saves_after_removal = len(saver.saved)
    after_removal = _everything_shown(tracker)
    with pytest.raises(ProjectNotFound):
        tracker.delete_project(2)

    assert len(saver.saved) == saves_after_removal
    assert _everything_shown(tracker) == after_removal


def test_delete_project_failed_save_keeps_every_read_unchanged():
    """FR-9, NFR-8, CP-578: the saver's error propagates after one attempted save and every read
    keeps the old value, with no outcome returned."""
    saver = FailingSaver()
    tracker = _tracker(saver)
    before = _everything_shown(tracker)

    with pytest.raises(PermissionError, match="the disk said no"):
        tracker.delete_project(2)

    assert saver.calls == 1
    assert _everything_shown(tracker) == before
    assert tracker.project(2) == Project(2, "Beta", "second")
    assert tracker.task(6) is not None


def test_delete_project_uses_state_at_confirm_time():
    """CP-576: the outcome reports the name and count held when the action runs, not those read
    when the confirmation was built."""
    tracker = _tracker(ObservingSaver())
    count_at_confirmation = tracker.project_task_list(2, FilterInput()).task_count
    assert count_at_confirmation == 4

    tracker.add_task(2, "Late arrival", "", "", "")
    tracker.rename_project(2, "Beta, renamed")
    outcome = tracker.delete_project(2)

    assert outcome.project.name == "Beta, renamed"
    assert outcome.task_count == 5


def test_delete_project_receives_saves_only():
    """QC-54, CP-591: the saver is handed whole-state saves for the action and never read."""
    saver = CallRecordingSaver()
    tracker = _tracker(saver)

    tracker.delete_project(2)
    tracker.projects()
    tracker.project(1)
    tracker.project_task_list(1, FilterInput())
    tracker.all_task_list(FilterInput())
    tracker.task(5)

    assert saver.saves == 1
    assert saver.other_access == []
