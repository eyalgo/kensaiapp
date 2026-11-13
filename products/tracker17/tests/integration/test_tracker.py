"""Integration tests of application's Tracker with hand-written fakes for its contracts (layer 3).

Checks SRS FR-9 (an action is reported done only after the save), FR-10 and FR-11 (create and list
projects), NFR-8 (a failed save leaves the state as it was), AC-6 (a restart lists the project),
AC-9 and AC-18 (interrupted and failed saves) and DR-6 (identities are not reused). Change spec
rules CP-24 and CP-25 and NFDR QC-10, QC-21 and QC-49 are the ones each test names. The All tasks
read (FR-31) adds CP-482 and CP-485, with design rows T3 and T17.
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
from tests.fakes import FakeSaver


class FixedClock:
    def now(self) -> datetime:
        return datetime(2026, 10, 7, 12, 0, tzinfo=UTC)


def _tracker(saver: Saver | None = None, state: TrackerState | None = None) -> Tracker:
    return Tracker(state or empty_state(), saver or FakeSaver(), FixedClock())


def test_the_saver_gets_the_new_state_before_it_is_shown():
    saver = FakeSaver()
    tracker = _tracker(saver)
    saver.watch = tracker.projects

    created = tracker.create_project("Alpha", "x")

    assert saver.seen == [()]
    assert tracker.projects() == (created,)
    assert saver.saved[-1].projects == (created,)


def test_a_failing_saver_leaves_the_state_unchanged():
    saver = FakeSaver(error=PermissionError("the disk said no"))
    tracker = _tracker(saver)

    with pytest.raises(PermissionError, match="the disk said no"):
        tracker.create_project("Alpha", "x")

    assert saver.calls == 1
    assert tracker.projects() == ()
    assert tracker.project(1) is None


def test_a_refusal_makes_no_save_call():
    saver = FakeSaver()
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
    saver = FakeSaver()
    first_run = _tracker(saver)
    created = first_run.create_project("Alpha", "x")

    second_run = _tracker(FakeSaver(), saver.saved[-1])

    assert second_run.projects() == (created,)


def test_an_identity_is_not_issued_twice_across_a_restart():
    saver = FakeSaver()
    first_run = _tracker(saver)
    first = first_run.create_project("Alpha", "")

    second_run = _tracker(FakeSaver(), saver.saved[-1])
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


def test_a_filter_query_hands_the_recording_saver_no_call():
    """CP-413, CP-417: reading a project's task list, valid, refused or cleared, never saves."""
    from application import FilterInput

    saver = FakeSaver()
    tracker = _tracker(saver)
    tracker.create_project("Alpha", "")
    tracker.add_task(1, "Seed")
    saved = len(saver.saved)
    for fields in (
        FilterInput(status=("todo",)),
        FilterInput(status=("blocked",)),
        FilterInput(status=("todo", "done")),
        FilterInput(),
    ):
        tracker.project_task_list(1, fields)
    assert len(saver.saved) == saved


def test_project_read_and_application_exports_remain_compatible():
    """CP-482, CP-485, T17: the project read and the existing public imports still work, and the
    added read hands back the same value type with no markup, query key or destination in it."""
    import application
    from application import ProjectTaskList, TaskRow

    for name in ("Tracker", "ProjectTaskList", "TaskRow", "FilterInput", "SortInput"):
        assert name in application.__all__
    tracker = Tracker(empty_state(), FakeSaver(), FixedClock())
    project = tracker.create_project("Alpha", "")
    tracker.add_task(project.id, "Only", "", "", "")

    project_read = tracker.project_task_list(project.id, application.FilterInput())
    all_read = tracker.all_task_list(application.FilterInput())

    assert isinstance(all_read, ProjectTaskList) and isinstance(all_read.rows[0], TaskRow)
    assert [row.task for row in project_read.rows] == [row.task for row in all_read.rows]
    assert not hasattr(all_read, "html") and not hasattr(all_read, "place")
    assert [field for field in vars(all_read)] == [field for field in vars(project_read)]
