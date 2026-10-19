"""Integration tests of the Tracker over the assignee list, with hand-written fakes (layer 3).

Checks SRS FR-9 (an action is reported done only after the save), FR-20 and FR-22 (the assignee
list), FR-39 (a refused action saves nothing), NFR-8 (a failed save leaves the state as it was) and
DR-4 (the assignee list). Change spec rules CP-81, CP-86, CP-89 to CP-93, CP-96, CP-97 and CP-105
are the ones each test names. No product name is patched: the real Tracker is handed each fake.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from application import (
    AssigneeNameInUse,
    AssigneeNotFound,
    BlankName,
    Refusal,
    TextTooLong,
    Tracker,
    TrackerState,
)
from domain import restore_state

PROJECTS = [(1, "Alpha", "first"), (2, "Beta", "")]
NEXT_PROJECT_ID = 3


class CountingClock:
    def __init__(self) -> None:
        self.reads = 0

    def now(self) -> datetime:
        self.reads += 1
        return datetime(2026, 10, 11, 12, 0, tzinfo=UTC)


class RecordingSaver:
    """Keeps every state it was handed, and what the tracker listed at the moment of each save."""

    def __init__(self) -> None:
        self.saved: list[TrackerState] = []
        self.listed_during_save: list[tuple[str, ...]] = []
        self.tracker: Tracker | None = None

    def save(self, state: TrackerState) -> None:
        if self.tracker is not None:
            self.listed_during_save.append(self.tracker.assignees())
        self.saved.append(state)


class FailingSaver:
    def __init__(self) -> None:
        self.calls = 0

    def save(self, state: TrackerState) -> None:
        self.calls += 1
        raise PermissionError("the disk said no")


def _state(*assignees: str) -> TrackerState:
    return restore_state(PROJECTS, NEXT_PROJECT_ID, assignees)


def _tracker(saver, *assignees: str, clock: CountingClock | None = None) -> Tracker:
    return Tracker(_state(*assignees), saver, clock or CountingClock())


@pytest.mark.parametrize("starting", [(), ("Dana", " Ari", "Bo")], ids=["empty", "populated"])
def test_assignee_query_does_not_save_or_read_the_clock(starting):
    """CP-81, CP-86: the list comes back in its order and nothing is written or timed."""
    saver = RecordingSaver()
    clock = CountingClock()
    tracker = _tracker(saver, *starting, clock=clock)

    assert tracker.assignees() == starting
    assert tracker.assignees() == starting

    assert saver.saved == []
    assert clock.reads == 0


def test_assignee_action_reports_the_exact_name_after_save():
    """FR-9, CP-86, CP-93: the exact value comes back, and the saver already holds the candidate."""
    saver = RecordingSaver()
    tracker = _tracker(saver, "Dana")

    added = tracker.add_assignee(" Ari ")

    assert added == " Ari "
    assert [state.assignees for state in saver.saved] == [("Dana", " Ari ")]

    removed = tracker.remove_assignee("Dana")

    assert removed == "Dana"
    assert [state.assignees for state in saver.saved] == [("Dana", " Ari "), (" Ari ",)]
    assert tracker.assignees() == (" Ari ",)


def test_assignee_candidate_is_saved_before_becoming_current():
    """CP-97: during the save the tracker still shows the old list, and afterwards the new one."""
    saver = RecordingSaver()
    tracker = _tracker(saver, "Dana")
    saver.tracker = tracker

    tracker.add_assignee("Ari")
    tracker.remove_assignee("Dana")

    assert saver.listed_during_save == [("Dana",), ("Dana", "Ari")]
    assert tracker.assignees() == ("Ari",)


def test_failed_assignee_save_leaves_the_old_state_current():
    """CP-97, NFR-8: the failure propagates and the names, projects and counter stay."""
    saver = FailingSaver()
    tracker = _tracker(saver, "Dana", "Ari")

    with pytest.raises(PermissionError, match="the disk said no"):
        tracker.add_assignee("Bo")
    with pytest.raises(PermissionError, match="the disk said no"):
        tracker.remove_assignee("Dana")

    assert saver.calls == 2
    assert tracker.assignees() == ("Dana", "Ari")
    assert [project.name for project in tracker.projects()] == ["Alpha", "Beta"]

    recorder = RecordingSaver()
    healthy = Tracker(_state("Dana", "Ari"), recorder, CountingClock())
    assert healthy.create_project("Gamma", "").id == NEXT_PROJECT_ID
    assert recorder.saved[-1].next_project_id == NEXT_PROJECT_ID + 1


def test_refused_assignee_action_never_calls_the_saver():
    """CP-89 to CP-91, CP-96: each refusal propagates its type and the state stays as it was."""
    saver = RecordingSaver()
    tracker = _tracker(saver, "Dana")

    with pytest.raises(BlankName):
        tracker.add_assignee("   ")
    with pytest.raises(AssigneeNameInUse):
        tracker.add_assignee("Dana")
    with pytest.raises(TextTooLong):
        tracker.add_assignee("n" * 201)
    with pytest.raises(AssigneeNotFound):
        tracker.remove_assignee("dana")

    assert saver.saved == []
    assert tracker.assignees() == ("Dana",)


def test_assignee_actions_check_current_state_after_other_actions():
    """CP-92, CP-96: each action is decided by the list as it stands when the action is applied."""
    saver = RecordingSaver()
    tracker = _tracker(saver, "Dana")

    tracker.add_assignee("Eve")
    with pytest.raises(AssigneeNameInUse):
        tracker.add_assignee("Eve")

    tracker.remove_assignee("Dana")
    with pytest.raises(AssigneeNotFound):
        tracker.remove_assignee("Dana")

    tracker.add_assignee("Dana")
    assert tracker.remove_assignee("Dana") == "Dana"
    assert tracker.assignees() == ("Eve",)


@pytest.mark.parametrize("starting", [(), ("Dana", "Ari")], ids=["empty", "populated"])
def test_projects_and_assignees_preserve_each_other(starting):
    """CP-105: a project create keeps the list, and a list action keeps projects and counter."""
    saver = RecordingSaver()
    tracker = _tracker(saver, *starting)

    created = tracker.create_project("Gamma", "")
    assert tracker.assignees() == starting
    assert saver.saved[-1].assignees == starting

    tracker.add_assignee("Cy")
    tracker.remove_assignee("Cy")

    assert [project.name for project in tracker.projects()] == ["Alpha", "Beta", "Gamma"]
    assert tracker.project(created.id) == created
    assert saver.saved[-1].next_project_id == NEXT_PROJECT_ID + 1
    assert saver.saved[-1].projects == saver.saved[0].projects
    assert tracker.assignees() == starting


def test_assignee_refusals_are_available_through_application():
    """The types web maps are exported here, so web never imports domain (NFDR QC-5, QC-16)."""
    assert issubclass(AssigneeNameInUse, Refusal)
    assert issubclass(AssigneeNotFound, Refusal)
