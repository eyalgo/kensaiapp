"""Integration tests of the Tracker over renaming a project, with hand-written fakes (layer 3).

Checks SRS FR-9 (an action is reported done only after the save), FR-10 and FR-39 (the naming rules
and their refusals), FR-12 (renaming leaves the project's tasks the same tasks), NFR-6 (the saved
data gains no field), NFR-8 (a failed save leaves the state as it was), DR-1 (the project entity)
and NFDR QC-21 (an action reporting no change saves nothing) and QC-54 (the saver receives only
saves). Change spec rules CP-550, CP-553 to CP-555, CP-557, CP-562 and CP-567 are the ones each
test names. No product name is patched: the real Tracker is handed each fake. The rename rule is
tested in tests/unit/test_projects.py.
"""

from __future__ import annotations

import dataclasses
import json
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from application import (
    SHORT_TEXT_MAX,
    BlankName,
    Comment,
    FilterInput,
    NameInUse,
    Project,
    ProjectNotFound,
    ProjectRenameOutcome,
    TextTooLong,
    Tracker,
    TrackerState,
)
from domain import restore_state, restore_task
from persistence import SavedData

PROJECTS = [(1, "Alpha", "the first"), (2, "Beta", ""), (3, "gamma", "third")]
NEXT_PROJECT_ID = 4
CREATED_AT = datetime(2026, 10, 11, 12, 0, tzinfo=UTC)
LATER = datetime(2026, 10, 12, 8, 30, tzinfo=UTC)


class CountingClock:
    def __init__(self) -> None:
        self.reads = 0

    def now(self) -> datetime:
        self.reads += 1
        return CREATED_AT


class RecordingSaver:
    """Keeps every state it was handed, and the project name the tracker showed during each save."""

    def __init__(self) -> None:
        self.saved: list[TrackerState] = []
        self.shown_during_save: list[str | None] = []
        self.tracker: Tracker | None = None

    def save(self, state: TrackerState) -> None:
        if self.tracker is not None:
            project = self.tracker.project(1)
            self.shown_during_save.append(None if project is None else project.name)
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


def _tasks():
    return [
        restore_task(
            4,
            1,
            "Write it",
            "in-progress",
            "high",
            "Dana",
            ["ui", "urgent"],
            "2026-11-01",
            CREATED_AT,
            [
                Comment(text="first", author="Dana", created_at=CREATED_AT),
                Comment(text="second", author="Sam", created_at=LATER),
            ],
        ),
        restore_task(5, 1, "Ship it", "done", "low", None, [], None, LATER, []),
        restore_task(6, 1, "Plan it", "todo", "medium", "Sam", ["later"], "2026-12-24", LATER, []),
        restore_task(7, 2, "Elsewhere", "todo", "medium", None, [], None, CREATED_AT, []),
    ]


def _state() -> TrackerState:
    """Three projects with descriptions, four tasks in varied states, two assignees and a name."""
    return restore_state(
        PROJECTS,
        NEXT_PROJECT_ID,
        ("Dana", "Sam"),
        tasks=_tasks(),
        next_task_id=8,
        operator_name="Dana",
    )


def _tracker(saver, clock: CountingClock | None = None) -> Tracker:
    return Tracker(_state(), saver, clock or CountingClock())


def _everything_shown(tracker: Tracker):
    """Every value the tracker shows for names and tasks, to compare before with after."""
    return (
        tracker.projects(),
        [tracker.project(identity) for identity in (1, 2, 3)],
        [tracker.task(identity) for identity in range(4, 8)],
        tracker.assignees(),
        tracker.operator_name(),
    )


def test_rename_saves_once_before_publishing():
    """FR-9, CP-550: the saver holds the candidate once, readers still show the old name during
    that save, and readers and the outcome show the new name afterwards. The clock is not read."""
    saver = RecordingSaver()
    clock = CountingClock()
    tracker = _tracker(saver, clock)
    saver.tracker = tracker
    before = _state()

    outcome = tracker.rename_project(1, "Zed")

    expected_project = Project(id=1, name="Zed", description="the first")
    assert outcome == ProjectRenameOutcome(
        project=expected_project, previous_name="Alpha", changed=True
    )
    assert saver.saved == [
        dataclasses.replace(
            before, projects=(expected_project, before.projects[1], before.projects[2])
        )
    ]
    assert saver.shown_during_save == ["Alpha"]
    assert tracker.project(1) == expected_project
    assert [project.name for project in tracker.projects()] == ["Beta", "gamma", "Zed"]
    assert clock.reads == 0


def test_unchanged_rename_never_saves():
    """CP-553, QC-21: the exact saved name is not refused, not saved and not published, also after a
    rename that did save; the clock is not read."""
    saver = RecordingSaver()
    clock = CountingClock()
    tracker = _tracker(saver, clock)

    unchanged = tracker.rename_project(1, "Alpha")
    assert unchanged == ProjectRenameOutcome(
        project=Project(id=1, name="Alpha", description="the first"),
        previous_name="Alpha",
        changed=False,
    )
    assert saver.saved == []

    tracker.rename_project(1, "Zed")
    again = tracker.rename_project(1, "Zed")

    assert again.changed is False
    assert again.previous_name == "Zed"
    assert len(saver.saved) == 1
    assert clock.reads == 0


@pytest.mark.parametrize(
    ("project_id", "name", "refusal"),
    [
        (1, "", BlankName),
        (1, "   ", BlankName),
        (1, "Beta", NameInUse),
        (1, "x" * (SHORT_TEXT_MAX + 1), TextTooLong),
        (1, " " * (SHORT_TEXT_MAX + 1), TextTooLong),
        (99, "Zed", ProjectNotFound),
        (99, "", ProjectNotFound),
    ],
    ids=["empty", "spaces", "in-use", "too-long", "long-spaces", "missing", "missing-and-blank"],
)
def test_refused_rename_keeps_the_current_state(project_id, name, refusal):
    """CP-555, CP-558: each refusal is the domain's type, nothing is saved and every value the
    tracker shows is as it was."""
    saver = RecordingSaver()
    tracker = _tracker(saver)
    before = _everything_shown(tracker)

    with pytest.raises(refusal):
        tracker.rename_project(project_id, name)

    assert saver.saved == []
    assert _everything_shown(tracker) == before


def test_failed_rename_keeps_the_current_state():
    """FR-9, NFR-8, CP-557: the saver's error propagates after one attempted save, and every value
    the tracker shows is as it was."""
    saver = FailingSaver()
    tracker = _tracker(saver)
    before = _everything_shown(tracker)

    with pytest.raises(PermissionError, match="the disk said no"):
        tracker.rename_project(1, "Zed")

    assert saver.calls == 1
    assert _everything_shown(tracker) == before


def test_each_rename_uses_the_name_current_at_the_action():
    """CP-550, CP-553, CP-555: the previous name is the one saved when the rename ran, a name an
    earlier page showed can be renamed back to, and a name already current saves nothing."""
    saver = RecordingSaver()
    tracker = _tracker(saver)

    first = tracker.rename_project(1, "Zed")
    second = tracker.rename_project(1, "Yak")
    back = tracker.rename_project(1, "Alpha")
    nothing = tracker.rename_project(1, "Alpha")

    assert [
        (o.previous_name, o.project.name, o.changed) for o in (first, second, back, nothing)
    ] == [
        ("Alpha", "Zed", True),
        ("Zed", "Yak", True),
        ("Yak", "Alpha", True),
        ("Alpha", "Alpha", False),
    ]
    assert len(saver.saved) == 3
    with pytest.raises(NameInUse):
        tracker.rename_project(2, "Alpha")


def test_rename_preserves_tasks_and_survives_restart(tmp_path: Path):
    """FR-12, NFR-6, CP-554, CP-562: against real saved data, the whole state in memory and read back
    from disk is the starting state with only the project's name replaced; the saved data gains no
    field, both counters and every identity are unchanged, and a fresh Tracker built on the saved
    data shows the new name and each task and comment field by field as before."""
    saved_data = SavedData(tmp_path)
    starting = _state()
    saved_data.save(starting)

    class TeeSaver:
        def __init__(self) -> None:
            self.states: list[TrackerState] = []

        def save(self, state: TrackerState) -> None:
            self.states.append(state)
            saved_data.save(state)

    tee = TeeSaver()
    keys_before = _stored_key_sets(tmp_path)
    tracker = Tracker(saved_data.load(), tee, CountingClock())

    tracker.rename_project(1, "Zed")

    expected = dataclasses.replace(
        starting,
        projects=(
            Project(id=1, name="Zed", description="the first"),
            Project(id=2, name="Beta", description=""),
            Project(id=3, name="gamma", description="third"),
        ),
    )
    assert tee.states == [expected]
    reloaded = saved_data.load()
    assert reloaded == expected
    assert _stored_key_sets(tmp_path) == keys_before
    stored = json.loads((tmp_path / "tracker.json").read_text(encoding="utf-8"))
    assert stored["next_project_id"] == NEXT_PROJECT_ID
    assert stored["next_task_id"] == 8
    assert [project["id"] for project in stored["projects"]] == [1, 2, 3]
    assert [task["id"] for task in stored["tasks"]] == [4, 5, 6, 7]

    restarted = Tracker(saved_data.load(), tee, CountingClock())
    assert restarted.project(1) == Project(id=1, name="Zed", description="the first")
    for original in starting.tasks:
        after = restarted.task(original.id)
        assert after is not None
        for field in dataclasses.fields(original):
            assert getattr(after, field.name) == getattr(original, field.name), field.name
    assert restarted.assignees() == ("Dana", "Sam")
    assert restarted.operator_name() == "Dana"
    assert restarted.task(4).comments[1].author == "Sam"
    assert restarted.task(4).due_date == date(2026, 11, 1)


def _stored_key_sets(location: Path):
    document = json.loads((location / "tracker.json").read_text(encoding="utf-8"))
    return (
        frozenset(document),
        {frozenset(project) for project in document["projects"]},
        {frozenset(task) for task in document["tasks"]},
        {frozenset(comment) for task in document["tasks"] for comment in task["comments"]},
    )


def test_rename_saver_receives_only_saves():
    """QC-54, CP-567: a rename and the reads that follow reach the saver with nothing but whole
    saves, never a read."""
    saver = CallRecordingSaver()
    tracker = _tracker(saver)

    tracker.rename_project(1, "Zed")
    tracker.rename_project(1, "Zed")
    tracker.projects()
    tracker.project(1)
    tracker.project_tasks(1)
    tracker.project_summary(1)
    tracker.project_task_list(1, FilterInput())
    tracker.all_task_list(FilterInput())
    tracker.task(4)
    tracker.assignees()
    tracker.operator_name()

    assert saver.saves == 1
    assert saver.other_access == []
