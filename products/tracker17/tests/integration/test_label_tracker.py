"""Integration tests of the Tracker's label actions with a hand-written saver and clock (layer 3).

Checks SRS FR-23 (a task's labels are added and removed one at a time and saved before they show),
FR-39 and FR-40 (refusals and the label maximum) and NFR-3. Change spec rules CP-187 to CP-194,
CP-199 and CP-204 and NFDR QC-21 and QC-49 are the ones each test names. No product name is
patched: the real Tracker is handed each fake.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from application import (
    SHORT_TEXT_MAX,
    EmptyLabel,
    LabelNotCarried,
    Refusal,
    Task,
    TaskLabelOutcome,
    TaskNotFound,
    TextField,
    TextTooLong,
    Tracker,
    TrackerState,
)
from domain import Comment, restore_state, restore_task

PROJECTS = [(1, "Alpha", "first"), (2, "Beta", "")]
CREATED = datetime(2026, 10, 11, 12, 0, tzinfo=UTC)
PEOPLE = ("Dana", "Ari")


class FixedClock:
    def now(self) -> datetime:
        return CREATED


def _tasks() -> list[Task]:
    comment = Comment(text="first", author="Dana", created_at=CREATED)
    labelled = restore_task(
        id=1,
        project_id=1,
        title="Set up CI",
        status="in-progress",
        priority="high",
        assignee="Dana",
        labels=["bug", "ui"],
        due_date="2026-10-20",
        created_at=CREATED,
        comments=[comment],
    )
    other = restore_task(
        id=2,
        project_id=2,
        title="Other",
        status="todo",
        priority="low",
        assignee=None,
        labels=["bug"],
        due_date=None,
        created_at=CREATED,
        comments=[],
    )
    return [labelled, other]


def _state() -> TrackerState:
    return restore_state(PROJECTS, 3, PEOPLE, tasks=_tasks(), next_task_id=3)


def _all_tasks(tracker: Tracker) -> tuple[Task, ...]:
    return tuple(row.task for project_id in (1, 2) for row in tracker.project_tasks(project_id))


class RecordingSaver:
    """Keeps every state it was handed, and what the tracker showed at the moment of each save."""

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


def _tracker(saver) -> Tracker:
    tracker = Tracker(_state(), saver, FixedClock())
    if isinstance(saver, RecordingSaver):
        saver.tracker = tracker
    return tracker


def _labels(tracker: Tracker, task_id: int = 1) -> tuple[str, ...]:
    task = tracker.task(task_id)
    assert task is not None
    return task.labels


ACTIONS = [
    pytest.param(Tracker.add_task_label, "ops", ("bug", "ui", "ops"), id="add"),
    pytest.param(Tracker.remove_task_label, "bug", ("ui",), id="remove"),
]


def test_the_label_names_web_needs_are_reexported():
    """QC-5, QC-16: web reaches the outcome and the refusals through application alone."""
    assert issubclass(EmptyLabel, Refusal) and issubclass(LabelNotCarried, Refusal)
    assert issubclass(TextTooLong, Refusal) and issubclass(TaskNotFound, Refusal)
    assert TextField.LABEL.value == "label" and SHORT_TEXT_MAX == 200
    assert TaskLabelOutcome is not None


@pytest.mark.parametrize(("act", "label", "expected"), ACTIONS)
def test_label_action_saves_once_before_publication(act, label, expected):
    """CP-187, CP-192: the saver sees the candidate while the tracker still shows the old labels,
    and the saved result then becomes current."""
    saver = RecordingSaver()
    tracker = _tracker(saver)
    before = _all_tasks(tracker)

    outcome = act(tracker, 1, label)

    assert isinstance(outcome, TaskLabelOutcome) and outcome.changed is True
    assert len(saver.saved) == 1
    assert saver.held_during_save == [before]
    assert saver.saved[0].tasks[0].labels == expected
    assert outcome.task == saver.saved[0].tasks[0] == tracker.task(1)
    assert _labels(tracker) == expected


def test_repeated_add_hands_saver_nothing():
    """CP-189, CP-204, QC-21: an exact repeat reports no change and sends no save; a different
    case or a surrounding space is a different label and is saved."""
    saver = RecordingSaver()
    tracker = _tracker(saver)

    outcome = tracker.add_task_label(1, "bug")

    assert outcome.changed is False and outcome.task == tracker.task(1)
    assert saver.saved == []
    assert _labels(tracker) == ("bug", "ui")
    for distinct in ("Bug", " bug", "bug "):
        assert tracker.add_task_label(1, distinct).changed is True
    assert len(saver.saved) == 3
    assert _labels(tracker) == ("bug", "ui", "Bug", " bug", "bug ")


@pytest.mark.parametrize(
    ("act", "task_id", "label", "refusal"),
    [
        pytest.param(Tracker.add_task_label, 1, "", EmptyLabel, id="empty-add"),
        pytest.param(Tracker.add_task_label, 1, "x" * 201, TextTooLong, id="overlong-add"),
        pytest.param(Tracker.remove_task_label, 1, "ops", LabelNotCarried, id="absent-remove"),
        pytest.param(Tracker.remove_task_label, 1, "BUG", LabelNotCarried, id="case-remove"),
        pytest.param(Tracker.add_task_label, 99, "ops", TaskNotFound, id="add-missing-task"),
        pytest.param(Tracker.remove_task_label, 99, "bug", TaskNotFound, id="remove-missing-task"),
    ],
)
def test_label_refusal_hands_saver_nothing(act, task_id, label, refusal):
    """CP-190, CP-191, CP-193, CP-194: each refusal propagates, leaves every task as it was and
    sends the saver nothing."""
    saver = RecordingSaver()
    tracker = _tracker(saver)
    before = _all_tasks(tracker)

    with pytest.raises(refusal):
        act(tracker, task_id, label)

    assert saver.saved == []
    assert _all_tasks(tracker) == before


@pytest.mark.parametrize(("act", "label", "expected"), ACTIONS)
def test_failed_label_save_leaves_previous_state_current(act, label, expected):
    """QC-49: a failing saver propagates its failure, no outcome comes back, and every task
    keeps its labels and fields."""
    saver = FailingSaver()
    tracker = _tracker(saver)
    before = _all_tasks(tracker)

    with pytest.raises(PermissionError):
        act(tracker, 1, label)

    assert saver.calls == 1
    assert _all_tasks(tracker) == before
    assert _labels(tracker) == ("bug", "ui")


@pytest.mark.parametrize(("act", "label", "expected"), ACTIONS)
def test_label_actions_preserve_unrelated_reads_and_fields(act, label, expected):
    """CP-199: the label rows, the edit context, the other task, the people and both counters stay
    consistent, and no field of the task other than its labels moves."""
    saver = RecordingSaver()
    tracker = _tracker(saver)
    before_task = tracker.task(1)
    before_context = tracker.task_edit_context(1)
    before_other = tracker.task(2)
    assert before_task is not None and before_context is not None

    act(tracker, 1, label)

    task = tracker.task(1)
    context = tracker.task_edit_context(1)
    assert task is not None and context is not None
    assert task.labels == expected
    assert task.labels != before_task.labels
    assert (task.title, task.priority, task.assignee, task.due_date, task.comments) == (
        before_task.title,
        before_task.priority,
        before_task.assignee,
        before_task.due_date,
        before_task.comments,
    )
    assert (task.id, task.project_id, task.status, task.created_at) == (
        before_task.id,
        before_task.project_id,
        before_task.status,
        before_task.created_at,
    )
    assert context.fields == before_context.fields and context.task == task
    assert tracker.task(2) == before_other
    assert [row.task.labels for row in tracker.project_tasks(1)] == [expected]
    assert tracker.assignees() == PEOPLE
    saved = saver.saved[0]
    assert (saved.next_task_id, saved.next_project_id) == (3, 3)
