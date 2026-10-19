"""Integration tests of application's Tracker with hand-written fakes for its contracts (layer 3).

Checks SRS FR-9 (an action is reported done only after the save), FR-10 and FR-11 (create and list
projects), NFR-8 (a failed save leaves the state as it was), AC-6 (a restart lists the project),
AC-9 and AC-18 (interrupted and failed saves) and DR-6 (identities are not reused). Change spec
rules CP-24 and CP-25 and NFDR QC-10, QC-21 and QC-49 are the ones each test names.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from application import (
    LONG_TEXT_MAX,
    SHORT_TEXT_MAX,
    BlankName,
    Clock,
    NameInUse,
    Project,
    Refusal,
    Saver,
    TextField,
    TextTooLong,
    Tracker,
    TrackerState,
)
from domain import empty_state


class FixedClock:
    def now(self) -> datetime:
        return datetime(2026, 10, 7, 12, 0, tzinfo=UTC)


class RecordingSaver:
    """Keeps every state it was handed, and what the tracker listed at the moment of each save."""

    def __init__(self) -> None:
        self.saved: list[TrackerState] = []
        self.listed_during_save: list[tuple[Project, ...]] = []
        self.tracker: Tracker | None = None

    def save(self, state: TrackerState) -> None:
        if self.tracker is not None:
            self.listed_during_save.append(self.tracker.projects())
        self.saved.append(state)


class FailingSaver:
    def __init__(self) -> None:
        self.calls = 0

    def save(self, state: TrackerState) -> None:
        self.calls += 1
        raise PermissionError("the disk said no")


def _tracker(saver: Saver | None = None, state: TrackerState | None = None) -> Tracker:
    return Tracker(state or empty_state(), saver or RecordingSaver(), FixedClock())


def test_the_saver_gets_the_new_state_before_it_is_shown():
    saver = RecordingSaver()
    tracker = _tracker(saver)
    saver.tracker = tracker

    created = tracker.create_project("Alpha", "x")

    assert saver.listed_during_save == [()]
    assert tracker.projects() == (created,)
    assert saver.saved[-1].projects == (created,)


def test_a_failing_saver_leaves_the_state_unchanged():
    saver = FailingSaver()
    tracker = _tracker(saver)

    with pytest.raises(PermissionError, match="the disk said no"):
        tracker.create_project("Alpha", "x")

    assert saver.calls == 1
    assert tracker.projects() == ()
    assert tracker.project(1) is None


def test_a_refusal_makes_no_save_call():
    saver = RecordingSaver()
    tracker = _tracker(saver)
    tracker.create_project("Alpha", "")
    saved_before = len(saver.saved)

    with pytest.raises(BlankName):
        tracker.create_project("   ", "")
    with pytest.raises(NameInUse):
        tracker.create_project("Alpha", "")
    with pytest.raises(TextTooLong):
        tracker.create_project("n" * 201, "")

    assert len(saver.saved) == saved_before
    assert [project.name for project in tracker.projects()] == ["Alpha"]


def test_a_restart_lists_the_project():
    saver = RecordingSaver()
    first_run = _tracker(saver)
    created = first_run.create_project("Alpha", "x")

    second_run = _tracker(RecordingSaver(), saver.saved[-1])

    assert second_run.projects() == (created,)


def test_an_identity_is_not_issued_twice_across_a_restart():
    saver = RecordingSaver()
    first_run = _tracker(saver)
    first = first_run.create_project("Alpha", "")

    second_run = _tracker(RecordingSaver(), saver.saved[-1])
    second = second_run.create_project("Beta", "")

    assert second.id != first.id
    assert second.id == 2


def test_projects_come_back_in_the_domain_order():
    tracker = _tracker()
    for name in ("beta", "Alpha", "alpha"):
        tracker.create_project(name, "")

    assert [project.name for project in tracker.projects()] == ["Alpha", "alpha", "beta"]


def test_project_returns_none_for_an_unknown_identity():
    tracker = _tracker()
    created = tracker.create_project("Alpha", "")

    assert tracker.project(created.id) == created
    assert tracker.project(99) is None


def test_the_names_web_needs_are_reexported():
    assert SHORT_TEXT_MAX == 200 and LONG_TEXT_MAX == 4000
    assert issubclass(BlankName, Refusal) and issubclass(NameInUse, Refusal)
    assert issubclass(TextTooLong, Refusal)
    assert {field.value for field in TextField} == {
        "name",
        "description",
        "title",
        "label",
        "comment",
    }
    assert Clock is not None and Saver is not None and Project is not None
