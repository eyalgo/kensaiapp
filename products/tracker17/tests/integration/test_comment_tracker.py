"""Integration tests of the Tracker's comment action with hand-written fakes (layer 3).

Checks SRS FR-9 (an action is reported done only after the save), FR-28 (adding a comment under the
saved name at the moment of the add), FR-30 (a rename leaves earlier authors alone), FR-39 (a
refused action saves nothing), NFR-3 (a page read is not what the add uses) and AC-18 (a failed
save is not a refusal). Change spec rules CP-249 to CP-252, CP-260 and CP-271 and NFDR QC-21 and
QC-54 are the ones each test names. No product name is patched: the real Tracker is handed each
fake. The comment rules themselves are tested in tests/unit/test_comments.py.
"""

from __future__ import annotations

import inspect
from datetime import UTC, datetime, timedelta

import pytest

import application
import domain
from application import (
    LONG_TEXT_MAX,
    BlankComment,
    Comment,
    OperatorNameNotSet,
    Refusal,
    Saver,
    Task,
    TaskNotFound,
    TextField,
    TextTooLong,
    Tracker,
    TrackerState,
)
from domain import restore_state, restore_task

PROJECTS = [(1, "Alpha", "first"), (2, "Beta", "")]
CREATED = datetime(2026, 10, 11, 12, 0, tzinfo=UTC)
WRITTEN = datetime(2026, 10, 12, 12, 32, tzinfo=UTC)
LATER = WRITTEN + timedelta(minutes=5)
EARLIER_COMMENT = Comment(text="first", author="Dana", created_at=CREATED)


class ListClock:
    """Gives the instants it was handed, one per read, and counts the reads."""

    def __init__(self, *instants: datetime) -> None:
        self._instants = list(instants)
        self.reads = 0

    def now(self) -> datetime:
        self.reads += 1
        return self._instants.pop(0)


def _tasks() -> list[Task]:
    commented = restore_task(
        1,
        1,
        "Set up CI",
        "in-progress",
        "high",
        "Dana",
        ["bug"],
        "2026-10-20",
        CREATED,
        [EARLIER_COMMENT],
    )
    other = restore_task(2, 2, "Other", "done", "low", None, [], None, CREATED, [])
    return [commented, other]


def _state(operator_name: str | None = "Sam") -> TrackerState:
    return restore_state(
        PROJECTS,
        3,
        ("Dana",),
        tasks=_tasks(),
        next_task_id=3,
        operator_name=operator_name,
    )


def _all_tasks(tracker: Tracker) -> tuple[Task | None, ...]:
    """Both tasks as the tracker holds them, read without touching the clock."""
    return tuple(tracker.task(task_id) for task_id in (1, 2))


class RecordingSaver:
    """Keeps every state it was handed, and what the tracker held at the moment of each save."""

    def __init__(self) -> None:
        self.saved: list[TrackerState] = []
        self.held_during_save: list[tuple[Task | None, ...]] = []
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


class SaveOnlySaver:
    """Offers save and nothing else: any other attribute it is asked for is recorded."""

    def __init__(self) -> None:
        self.saved: list[TrackerState] = []
        self.other_attributes_asked_for: list[str] = []

    def save(self, state: TrackerState) -> None:
        self.saved.append(state)

    def __getattr__(self, name: str):
        self.other_attributes_asked_for.append(name)
        raise AttributeError(name)


def _tracker(
    saver: Saver,
    operator_name: str | None = "Sam",
    clock: ListClock | None = None,
) -> Tracker:
    tracker = Tracker(_state(operator_name), saver, clock or ListClock(WRITTEN, LATER))
    if isinstance(saver, RecordingSaver):
        saver.tracker = tracker
    return tracker


def _comments(tracker: Tracker, task_id: int = 1) -> tuple[Comment, ...]:
    task = tracker.task(task_id)
    assert task is not None
    return task.comments


def test_comment_action_saves_once_before_publishing():
    """CP-249, CP-250: one instant, one whole new state saved while the old task is current."""
    saver = RecordingSaver()
    clock = ListClock(WRITTEN, LATER)
    tracker = _tracker(saver, "Sam", clock)
    before = _all_tasks(tracker)

    returned = tracker.add_task_comment(1, "Looks good")

    assert clock.reads == 1
    assert len(saver.saved) == 1
    assert saver.held_during_save == [before]
    saved_task = next(task for task in saver.saved[0].tasks if task.id == 1)
    assert saved_task.comments == (
        EARLIER_COMMENT,
        Comment(text="Looks good", author="Sam", created_at=WRITTEN),
    )
    assert returned == saved_task
    assert tracker.task(1) == returned
    assert saver.saved[0].operator_name == "Sam"


def test_comment_action_uses_the_name_at_action_time():
    """CP-251: a name read earlier is not the author; the saved name at the add is."""
    tracker = _tracker(RecordingSaver(), "Sam")
    assert tracker.operator_name() == "Sam"
    tracker.set_operator_name("Lee")

    renamed = tracker.add_task_comment(1, "Hi")

    assert renamed.comments[-1].author == "Lee"

    unset = _tracker(RecordingSaver(), None)
    assert unset.operator_name() is None
    unset.set_operator_name("Sam")

    named = unset.add_task_comment(1, "Hi")

    assert named.comments[-1].author == "Sam"


def test_rename_keeps_historical_comment_authors():
    """CP-252: earlier authors stay as written, and the next comment carries the saved new name."""
    saver = RecordingSaver()
    tracker = _tracker(saver, "Sam")
    tracker.add_task_comment(1, "As Sam")
    written_as_sam = _comments(tracker)

    tracker.set_operator_name("Lee")
    tracker.add_task_comment(1, "As Lee")

    comments = _comments(tracker)
    assert comments[: len(written_as_sam)] == written_as_sam
    assert [comment.author for comment in comments] == ["Dana", "Sam", "Lee"]
    assert saver.saved[-1].operator_name == "Lee"


@pytest.mark.parametrize(
    ("task_id", "text", "operator_name", "refusal"),
    [
        pytest.param(99, "Hi", "Sam", TaskNotFound, id="unknown-task"),
        pytest.param(99, "", None, TaskNotFound, id="unknown-task-beats-blank-and-no-name"),
        pytest.param(1, "", "Sam", BlankComment, id="empty"),
        pytest.param(1, " \t\n 　", "Sam", BlankComment, id="whitespace"),
        pytest.param(1, "x" * (LONG_TEXT_MAX + 1), "Sam", TextTooLong, id="too-long"),
        pytest.param(1, "Hi", None, OperatorNameNotSet, id="no-name"),
    ],
)
def test_comment_action_refusals_save_nothing_and_keep_current_state(
    task_id, text, operator_name, refusal
):
    """CP-249, CP-255 to CP-259: each typed refusal propagates, with no save and no new state."""
    saver = RecordingSaver()
    tracker = _tracker(saver, operator_name)
    before = _all_tasks(tracker)

    with pytest.raises(refusal) as raised:
        tracker.add_task_comment(task_id, text)

    assert type(raised.value) is refusal
    assert saver.saved == []
    assert _all_tasks(tracker) == before
    assert tracker.operator_name() == operator_name


def test_failed_comment_save_keeps_the_previous_task_current():
    """CP-260: a saver failure is not a refusal; it propagates and nothing becomes current."""
    saver = FailingSaver()
    tracker = _tracker(saver, "Sam")
    before = _all_tasks(tracker)

    with pytest.raises(PermissionError, match="the disk said no") as raised:
        tracker.add_task_comment(1, "Hi")

    assert not isinstance(raised.value, Refusal)
    assert saver.calls == 1
    assert _all_tasks(tracker) == before
    assert _comments(tracker) == (EARLIER_COMMENT,)
    assert tracker.operator_name() == "Sam"


def test_comment_action_reaches_only_the_injected_saver_and_clock():
    """CP-271, QC-54: a successful add is one save and one instant, and no load is reached."""
    saver = SaveOnlySaver()
    clock = ListClock(WRITTEN)
    tracker = Tracker(_state("Sam"), saver, clock)

    tracker.add_task_comment(1, "Hi")

    assert len(saver.saved) == 1
    assert clock.reads == 1
    assert saver.other_attributes_asked_for == []
    assert not hasattr(Saver, "load")


def test_comment_refusals_are_available_through_application():
    """CP-266: web gets the domain's own refusal types from application, and none of its own."""
    assert application.BlankComment is domain.BlankComment
    assert application.OperatorNameNotSet is domain.OperatorNameNotSet
    assert application.TextField is domain.TextField
    assert TextField.COMMENT.value == "comment"
    assert issubclass(BlankComment, Refusal) and issubclass(OperatorNameNotSet, Refusal)

    own_refusals = [
        name
        for module in (application, application.tracker, application.contracts)
        for name, member in inspect.getmembers(module, inspect.isclass)
        if issubclass(member, Refusal) and member.__module__.startswith("application")
    ]
    assert own_refusals == []
