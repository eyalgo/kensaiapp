"""Integration tests of the Tracker over the operator name, with hand-written fakes (layer 3).

Checks SRS FR-9 (an action is reported done only after the save), FR-27 (the operator's name),
FR-39 (a refused action saves nothing), NFR-8 (a failed save leaves the state as it was), DR-5 (the
one operator name) and NFDR QC-54 (the saver receives only saves). Change spec rules CP-216 to
CP-222, CP-229 and CP-235 are the ones each test names. No product name is patched: the real
Tracker is handed each fake. The name rule is tested in tests/unit/test_operator_name.py.
"""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime

import pytest

from application import (
    SHORT_TEXT_MAX,
    BlankName,
    Comment,
    OperatorNameOutcome,
    TextTooLong,
    Tracker,
    TrackerState,
)
from domain import restore_state, restore_task

PROJECTS = [(1, "Alpha", "first"), (2, "Beta", "")]
NEXT_PROJECT_ID = 3
CREATED_AT = datetime(2026, 10, 11, 12, 0, tzinfo=UTC)
BLANK_FORMS = ("", "   ", "\t", " ", "　")


class CountingClock:
    def __init__(self) -> None:
        self.reads = 0

    def now(self) -> datetime:
        self.reads += 1
        return CREATED_AT


class RecordingSaver:
    """Keeps every state it was handed, and what the tracker reported at the moment of each save."""

    def __init__(self) -> None:
        self.saved: list[TrackerState] = []
        self.reported_during_save: list[str | None] = []
        self.tracker: Tracker | None = None

    def save(self, state: TrackerState) -> None:
        if self.tracker is not None:
            self.reported_during_save.append(self.tracker.operator_name())
        self.saved.append(state)


class FailingSaver:
    def __init__(self) -> None:
        self.calls = 0

    def save(self, state: TrackerState) -> None:
        self.calls += 1
        raise PermissionError("the disk said no")


def _state(operator_name: str | None = None) -> TrackerState:
    """A state with projects, a task with a label and a comment, an assignee and both counters."""
    task = restore_task(
        4,
        1,
        "Write it",
        "todo",
        "medium",
        "Dana",
        ["urgent"],
        None,
        CREATED_AT,
        [Comment(text="first", author="Dana", created_at=CREATED_AT)],
    )
    return restore_state(
        PROJECTS,
        NEXT_PROJECT_ID,
        ("Dana",),
        tasks=[task],
        next_task_id=5,
        operator_name=operator_name,
    )


def _tracker(
    saver, operator_name: str | None = None, clock: CountingClock | None = None
) -> Tracker:
    return Tracker(_state(operator_name), saver, clock or CountingClock())


@pytest.mark.parametrize("starting", [None, "Sam", " Sam "], ids=["unset", "plain", "spaced"])
def test_operator_name_reader_reports_unset_and_restored_name(starting):
    """CP-212, CP-226: the reader gives the current scalar exactly, with no save and no clock."""
    saver = RecordingSaver()
    clock = CountingClock()
    tracker = _tracker(saver, starting, clock)

    assert tracker.operator_name() == starting
    assert tracker.operator_name() == starting

    assert saver.saved == []
    assert clock.reads == 0


@pytest.mark.parametrize("starting", [None, "Sam"], ids=["first-name", "replacement"])
def test_name_change_saves_once_before_the_reader_publishes(starting):
    """FR-9, CP-216: the saver holds the whole candidate once, and the reader still shows the old
    name during that save and the new name afterwards."""
    saver = RecordingSaver()
    tracker = _tracker(saver, starting)
    saver.tracker = tracker
    before = _state(starting)

    outcome = tracker.set_operator_name("Sam Lee")

    assert outcome == OperatorNameOutcome(name="Sam Lee", changed=True)
    assert saver.saved == [dataclasses.replace(before, operator_name="Sam Lee")]
    assert saver.reported_during_save == [starting]
    assert tracker.operator_name() == "Sam Lee"


@pytest.mark.parametrize(
    ("starting", "submitted"),
    [(None, "Sam"), ("Sam", "Sam "), ("Sam", "sam"), ("Sam", " Sam"), ("Sam", "Lee")],
    ids=["first", "trailing-space", "case-only", "leading-space", "different"],
)
def test_replacing_name_preserves_every_unrelated_value(starting, submitted):
    """CP-217, CP-226, CP-229: only the scalar differs, surrounding spaces and case included."""
    saver = RecordingSaver()
    tracker = _tracker(saver, starting)

    outcome = tracker.set_operator_name(submitted)

    assert outcome == OperatorNameOutcome(name=submitted, changed=True)
    assert saver.saved == [dataclasses.replace(_state(starting), operator_name=submitted)]
    assert tracker.operator_name() == submitted


def test_same_name_never_reaches_even_a_failing_saver():
    """CP-218: the exact saved name is not refused, not saved and not published."""
    saver = FailingSaver()
    tracker = _tracker(saver, "Sam")

    outcome = tracker.set_operator_name("Sam")

    assert outcome == OperatorNameOutcome(name="Sam", changed=False)
    assert saver.calls == 0
    assert tracker.operator_name() == "Sam"


@pytest.mark.parametrize("starting", [None, "Sam"], ids=["unset", "saved"])
def test_each_domain_name_refusal_propagates_without_a_save(starting):
    """CP-219 to CP-221, CP-230: each refusal is the domain's type and nothing is saved or kept."""
    saver = RecordingSaver()
    tracker = _tracker(saver, starting)

    for blank in BLANK_FORMS:
        with pytest.raises(BlankName):
            tracker.set_operator_name(blank)
    with pytest.raises(TextTooLong):
        tracker.set_operator_name("x" * (SHORT_TEXT_MAX + 1))
    with pytest.raises(TextTooLong):
        tracker.set_operator_name(" " * (SHORT_TEXT_MAX + 1))

    assert saver.saved == []
    assert tracker.operator_name() == starting


@pytest.mark.parametrize("starting", [None, "Sam"], ids=["unset", "saved"])
def test_failed_name_save_does_not_publish(starting):
    """NFR-8, CP-222: the saver's error propagates; the name stays and no outcome is returned."""
    saver = FailingSaver()
    tracker = _tracker(saver, starting)

    with pytest.raises(PermissionError, match="the disk said no"):
        tracker.set_operator_name("Sam Lee")

    assert saver.calls == 1
    assert tracker.operator_name() == starting


def test_name_action_never_reads_clock_and_saver_receives_only_saves():
    """CP-235, QC-54: the clock is unused, and the saver's only calls are saves of whole states."""
    saver = RecordingSaver()
    clock = CountingClock()
    tracker = _tracker(saver, None, clock)

    tracker.set_operator_name("Sam")
    tracker.set_operator_name("Sam")
    tracker.operator_name()

    assert clock.reads == 0
    assert [type(saved) for saved in saver.saved] == [TrackerState]
