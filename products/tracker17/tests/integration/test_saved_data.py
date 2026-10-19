"""Integration tests of persistence against real files in a test's own directory (layer 2).

Checks SRS DR-2 (the Task entity and its counter), FR-15 (a task is kept), DR-4 (the assignee list), DR-6 (saved data is read once and checked at start), FR-20
(the list is kept), AC-6 (a project survives a restart), AC-7 (unreadable saved data is refused
whole), AC-9 (an interrupted save leaves one whole state), NFR-2 and NFR-6 (the save is whole and
atomic, and holds only the required fields) and FR-16 (an edited task keeps the saved format).
Change spec rules CP-4, CP-6, CP-7, CP-8, CP-26, CP-96 and CP-99 to CP-101, CP-134 to CP-137,
CP-170 and CP-171, CP-197 to CP-199, CP-209, CP-226 to CP-228, CP-233 to CP-234, CP-263, CP-264,
CP-269 and CP-270 and NFDR QC-42, QC-46 are the ones each test names. The operator name is SRS DR-5
and FR-27: one string or null, checked at start by the rule a set applies.
Labels are FR-23 and FR-40: saved labels are checked at start by the same rules an add applies.
"""

from __future__ import annotations

import dataclasses
import json
import os
import random
import signal
import subprocess
import sys
import textwrap
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest

from application import TaskFields, Tracker
from domain import (
    AssigneeNotFound,
    Comment,
    TrackerState,
    add_assignee,
    add_task,
    create_project,
    empty_state,
    list_project_tasks,
    remove_assignee,
    restore_state,
    restore_task,
)
from persistence import DEFAULT_LOCATION, SavedData, UnreadableData

PRODUCT_ROOT = Path(__file__).resolve().parents[2]
FILE_NAME = "tracker.json"


def _state_with(*pairs: tuple[str, str]) -> TrackerState:
    state = empty_state()
    for name, description in pairs:
        state, _ = create_project(state, name, description)
    return state


def _with_assignees(state: TrackerState, *names: str) -> TrackerState:
    for name in names:
        state = add_assignee(state, name)
    return state


class _FixedClock:
    def now(self) -> datetime:
        return datetime(2026, 10, 11, 12, 0, tzinfo=UTC)


def _write(location: Path, content: bytes) -> Path:
    location.mkdir(parents=True, exist_ok=True)
    saved_file = location / FILE_NAME
    saved_file.write_bytes(content)
    return saved_file


def _document(projects: list, next_project_id: int = 10) -> bytes:
    return json.dumps({"next_project_id": next_project_id, "projects": projects}).encode()


def _legacy_document(*projects: dict, next_project_id: int = 10) -> bytes:
    """Saved data as it was written before the assignee list: the counter and the projects only."""
    return _document(list(projects), next_project_id)


def _listing(location: Path) -> list[str]:
    return sorted(path.name for path in location.iterdir())


def _project(identity=1, name="Alpha", description="") -> dict:
    return {"id": identity, "name": name, "description": description}


def test_no_file_loads_as_none(tmp_path):
    assert SavedData(tmp_path / "data").load() is None


def test_save_then_load_round_trips(tmp_path):
    state = _state_with(("Alpha", "  two lines\nand spaces  "), ("beta", ""))
    saved = SavedData(tmp_path / "data")

    saved.save(state)

    assert SavedData(tmp_path / "data").load() == state


def test_the_first_save_creates_the_directory(tmp_path):
    location = tmp_path / "does" / "not" / "exist"

    SavedData(location).save(_state_with(("Alpha", "")))

    assert (location / FILE_NAME).is_file()


@pytest.mark.parametrize(
    "content",
    [
        b'{"next_project_id": 2, "projects": [{"id": 1, "na',
        b"\xff\xfe\x00 not utf-8 \x80",
        b"",
        b"[]",
        b"{}",
        b'{"next_project_id": 2}',
        b'{"next_project_id": 2, "projects": {}}',
        b'{"next_project_id": 2, "projects": [{"id": 1, "name": "A"}]}',
        b'{"next_project_id": 2, "projects": [], "extra": 1}',
    ],
    ids=[
        "truncated",
        "not-utf-8",
        "empty-file",
        "list-not-object",
        "empty-object",
        "no-projects-key",
        "projects-not-a-list",
        "project-missing-description",
        "unknown-key",
    ],
)
def test_unreadable_files_raise_and_stay_unchanged(tmp_path, content):
    location = tmp_path / "data"
    saved_file = _write(location, content)

    with pytest.raises(UnreadableData) as error:
        SavedData(location).load()

    assert error.value.location == location
    assert saved_file.read_bytes() == content


def test_a_directory_in_place_of_the_file_is_unreadable(tmp_path):
    location = tmp_path / "data"
    (location / FILE_NAME).mkdir(parents=True)

    with pytest.raises(UnreadableData) as error:
        SavedData(location).load()

    assert error.value.location == location


@pytest.mark.parametrize(
    "content",
    [
        _document([_project(name=7)]),
        _document([_project(description=None)]),
        b'{"next_project_id": 2, "projects": [{"id": true, "name": "A", "description": ""}]}',
        b'{"next_project_id": true, "projects": []}',
        b'{"next_project_id": 2.0, "projects": []}',
        b'{"next_project_id": 2, "projects": ["Alpha"]}',
    ],
    ids=[
        "name-not-a-string",
        "description-not-a-string",
        "id-is-json-true",
        "counter-is-json-true",
        "counter-is-a-float",
        "project-not-an-object",
    ],
)
def test_a_wrong_type_is_unreadable(tmp_path, content):
    location = tmp_path / "data"
    saved_file = _write(location, content)

    with pytest.raises(UnreadableData):
        SavedData(location).load()

    assert saved_file.read_bytes() == content


@pytest.mark.parametrize(
    "content",
    [
        _document([_project(name="   ")]),
        _document([_project(1, "Alpha"), _project(2, "Alpha")]),
        _document([_project(name="n" * 201)]),
        _document([_project(description="d" * 4001)]),
        _document([_project(1, "Alpha"), _project(1, "Beta")]),
        _document([_project(identity=10)], next_project_id=10),
    ],
    ids=[
        "blank-name",
        "duplicate-name",
        "name-201-characters",
        "description-4001-characters",
        "shared-identity",
        "identity-not-below-the-counter",
    ],
)
def test_a_broken_domain_rule_is_unreadable(tmp_path, content):
    location = tmp_path / "data"
    saved_file = _write(location, content)

    with pytest.raises(UnreadableData):
        SavedData(location).load()

    assert saved_file.read_bytes() == content


def test_default_location_is_the_product_data_directory(tmp_path):
    environment = {**os.environ, "PYTHONPATH": str(PRODUCT_ROOT)}

    result = subprocess.run(
        [sys.executable, "-c", "from persistence import DEFAULT_LOCATION; print(DEFAULT_LOCATION)"],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=True,
    )

    assert Path(result.stdout.strip()) == PRODUCT_ROOT / "data"
    assert DEFAULT_LOCATION == PRODUCT_ROOT / "data"
    assert DEFAULT_LOCATION.is_absolute()


SAVE_FOREVER = textwrap.dedent(
    """
    import sys
    from pathlib import Path
    from domain import create_project, empty_state
    from persistence import SavedData

    def build(letter):
        state = empty_state()
        for index in range(6):
            state, _ = create_project(state, f"{letter}{index}", letter * 3500)
        return state

    saved = SavedData(Path(sys.argv[1]))
    first, second = build("a"), build("b")
    saved.save(first)
    print("ready", flush=True)
    while True:
        saved.save(second)
        saved.save(first)
    """
)


def _build_alternating_states() -> tuple[TrackerState, TrackerState]:
    states = []
    for letter in ("a", "b"):
        state = empty_state()
        for index in range(6):
            state, _ = create_project(state, f"{letter}{index}", letter * 3500)
        states.append(state)
    return states[0], states[1]


def test_a_killed_save_leaves_one_whole_state(tmp_path):
    first, second = _build_alternating_states()
    environment = {**os.environ, "PYTHONPATH": str(PRODUCT_ROOT)}
    generator = random.Random(2026)

    for attempt in range(40):
        location = tmp_path / f"attempt-{attempt}"
        process = subprocess.Popen(
            [sys.executable, "-c", SAVE_FOREVER, str(location)],
            cwd=tmp_path,
            env=environment,
            stdout=subprocess.PIPE,
            text=True,
        )
        assert process.stdout is not None
        assert process.stdout.readline().strip() == "ready"
        try:
            process.wait(timeout=generator.uniform(0.0, 0.08))
        except subprocess.TimeoutExpired:
            pass
        process.send_signal(signal.SIGKILL)
        process.wait()
        process.stdout.close()

        assert SavedData(location).load() in (first, second)


def test_a_leftover_second_file_is_ignored(tmp_path):
    location = tmp_path / "data"
    state = _state_with(("Alpha", "x"))
    saved = SavedData(location)
    saved.save(state)

    for stray in ("tracker.json.partial", "tracker.json.tmp", "other.json", "tracker.json~"):
        (location / stray).write_bytes(b"not the saved data {{{")

    assert saved.load() == state


def test_a_failed_save_raises_and_leaves_the_old_file_whole(tmp_path):
    location = tmp_path / "data"
    saved = SavedData(location)
    saved.save(_state_with(("Alpha", "x")))
    before = (location / FILE_NAME).read_bytes()
    location.chmod(0o500)
    try:
        with pytest.raises(OSError):
            saved.save(_state_with(("Alpha", "x"), ("Beta", "y")))
    finally:
        location.chmod(0o700)

    assert (location / FILE_NAME).read_bytes() == before
    assert sorted(path.name for path in location.iterdir()) == [FILE_NAME]


FULL_KEYS = {"next_project_id", "projects", "assignees", "next_task_id", "tasks", "operator_name"}


def test_current_saved_data_has_exactly_its_six_keys(tmp_path):
    """CP-100, CP-105, CP-135, CP-226: every save writes the six keys; projects, counter and People
    keep their shape, and a state with no task saves an empty list and a counter of 1."""
    location = tmp_path / "data"
    SavedData(location).save(_state_with(("Alpha", "x"), ("beta", "")))

    document = json.loads((location / FILE_NAME).read_text(encoding="utf-8"))

    assert set(document) == FULL_KEYS
    assert document["assignees"] == []
    assert document["tasks"] == [] and document["next_task_id"] == 1
    assert document["next_project_id"] == 3
    assert [set(project) for project in document["projects"]] == [{"id", "name", "description"}] * 2

    SavedData(location).save(_with_assignees(_state_with(("Alpha", "x")), "Dana"))
    document = json.loads((location / FILE_NAME).read_text(encoding="utf-8"))
    assert set(document) == FULL_KEYS
    assert document["assignees"] == ["Dana"]


def test_saved_assignees_round_trip_exactly_in_order(tmp_path):
    """CP-99: the list comes back in its order with every space, character and mark kept."""
    saved = SavedData(tmp_path / "data")
    names = ("Dana", " Ari ", "dana", "Zoë", "<b>A&B</b>", 'say "hi"', "Dana  Lee", "\U0001d11e")
    state = _with_assignees(_state_with(("Alpha", "x")), *names)

    saved.save(state)
    assert saved.load() == state
    assert saved.load().assignees == names

    readded = add_assignee(remove_assignee(state, "Dana"), "Dana")
    saved.save(readded)
    assert saved.load().assignees == (*names[1:], "Dana")

    saved.save(empty_state())
    assert saved.load() == empty_state()
    assert saved.load().assignees == ()


def test_legacy_data_loads_without_writing(tmp_path):
    """CP-100: data written before the list loads with no names, and nothing is written."""
    location = tmp_path / "data"
    content = _legacy_document(_project(1, "Alpha", "x"), _project(2, "Beta"), next_project_id=3)
    saved_file = _write(location, content)
    before = _listing(location)

    state = SavedData(location).load()

    assert state is not None
    assert [project.name for project in state.projects] == ["Alpha", "Beta"]
    assert state.next_project_id == 3
    assert state.assignees == ()
    assert saved_file.read_bytes() == content
    assert _listing(location) == before


def test_first_successful_action_saves_the_complete_shape(tmp_path):
    """CP-100: the first add, or the first project create, writes the whole current shape."""
    for action in ("add", "create"):
        location = tmp_path / action
        content = _legacy_document(_project(1, "Alpha", "x"), next_project_id=2)
        saved_file = _write(location, content)
        saved = SavedData(location)
        state = saved.load()
        assert state is not None
        tracker = Tracker(state, saved, _FixedClock())

        if action == "add":
            tracker.add_assignee("Dana")
        else:
            tracker.create_project("Beta", "")

        document = json.loads(saved_file.read_text(encoding="utf-8"))
        assert set(document) == FULL_KEYS
        assert document["tasks"] == [] and document["next_task_id"] == 1
        assert document["assignees"] == (["Dana"] if action == "add" else [])
        assert [project["name"] for project in document["projects"]] == (
            ["Alpha"] if action == "add" else ["Alpha", "Beta"]
        )
        assert document["next_project_id"] == (2 if action == "add" else 3)


def test_refused_remove_on_legacy_empty_list_writes_nothing(tmp_path):
    """CP-96, CP-100: a refusal never upgrades the saved document."""
    location = tmp_path / "data"
    content = _legacy_document(_project(1, "Alpha"), next_project_id=2)
    saved_file = _write(location, content)
    saved = SavedData(location)
    state = saved.load()
    assert state is not None
    tracker = Tracker(state, saved, _FixedClock())
    before = _listing(location)

    with pytest.raises(AssigneeNotFound):
        tracker.remove_assignee("Dana")

    assert tracker.assignees() == ()
    assert saved_file.read_bytes() == content
    assert _listing(location) == before


def _present(assignees: object) -> bytes:
    document = {"next_project_id": 2, "projects": [_project()], "assignees": assignees}
    return json.dumps(document).encode()


INVALID_ASSIGNEE_LISTS = [
    pytest.param(["Dana", ""], id="empty-name"),
    pytest.param(["Dana", "   "], id="whitespace-name"),
    pytest.param(["Dana", "Ari", "Dana"], id="duplicate"),
    pytest.param(["n" * 201], id="name-201-characters"),
    pytest.param(["Dana", 7], id="number-member"),
    pytest.param(["Dana", 7, None, True], id="mixed-members"),
    pytest.param([["Dana"]], id="nested-list"),
    pytest.param(None, id="null"),
    pytest.param("Dana", id="scalar-text"),
    pytest.param(7, id="scalar-number"),
    pytest.param({"Dana": 1}, id="mapping"),
]


@pytest.mark.parametrize("assignees", INVALID_ASSIGNEE_LISTS)
def test_invalid_present_assignee_list_is_unreadable_and_untouched(tmp_path, assignees):
    """CP-101: a present list that breaks a rule is unreadable whole, and the file is as it was."""
    location = tmp_path / "data"
    content = _present(assignees)
    saved_file = _write(location, content)
    before = _listing(location)

    with pytest.raises(UnreadableData) as error:
        SavedData(location).load()

    assert error.value.location == location
    assert saved_file.read_bytes() == content
    assert _listing(location) == before


def test_a_valid_present_assignee_list_loads(tmp_path):
    """CP-99: the contrast case for the table above, the same document with a rule-keeping list."""
    saved_file = _write(tmp_path / "data", _present(["Dana", "dana", " Dana"]))

    state = SavedData(tmp_path / "data").load()

    assert state is not None
    assert state.assignees == ("Dana", "dana", " Dana")
    assert saved_file.read_bytes() == _present(["Dana", "dana", " Dana"])


@pytest.mark.parametrize(
    "content",
    [
        b'{"next_project_id": 2, "assignees": []}',
        b'{"projects": [], "assignees": []}',
        b'{"next_project_id": 2, "projects": [], "assignees": [], "extra": 1}',
        b'{"next_project_id": 2, "projects": [{"id": 1, "name": "A"}], "assignees": []}',
        b'{"next_project_id": 2, "projects": {}, "assignees": []}',
        b'{"next_project_id": true, "projects": [], "assignees": []}',
    ],
    ids=[
        "no-projects-key",
        "no-counter-key",
        "unknown-key",
        "project-missing-description",
        "projects-not-a-list",
        "counter-is-json-true",
    ],
)
def test_unknown_or_missing_required_saved_keys_still_refuse(tmp_path, content):
    """CP-100, CP-101: only the list may be missing; every other shape rule still refuses whole."""
    location = tmp_path / "data"
    saved_file = _write(location, content)

    with pytest.raises(UnreadableData):
        SavedData(location).load()

    assert saved_file.read_bytes() == content


NOW = datetime(2026, 10, 11, 9, 30, tzinfo=UTC)
TASK_KEYS = {
    "id",
    "project_id",
    "title",
    "status",
    "priority",
    "assignee",
    "labels",
    "due_date",
    "created_at",
    "comments",
}


def _task_entry(**changes) -> dict:
    entry = {
        "id": 1,
        "project_id": 1,
        "title": "Plan",
        "status": "todo",
        "priority": "medium",
        "assignee": None,
        "labels": [],
        "due_date": None,
        "created_at": "2026-10-11T09:30:00Z",
        "comments": [],
    }
    entry.update(changes)
    return entry


def _full_document(tasks: object = None, next_task_id: object = 2, **others) -> bytes:
    document = {
        "next_project_id": 3,
        "projects": [_project(1, "Alpha"), _project(2, "Beta")],
        "assignees": ["Dana", "Ari"],
        "next_task_id": next_task_id,
        "tasks": [_task_entry()] if tasks is None else tasks,
    }
    document.update(others)
    return json.dumps(document).encode()


def _stored(**changes):
    values = {
        "id": 1,
        "project_id": 1,
        "title": "Plan",
        "status": "todo",
        "priority": "medium",
        "assignee": None,
        "labels": (),
        "due_date": None,
        "created_at": NOW,
        "comments": (),
    }
    values.update(changes)
    return restore_task(**values)


def _state_holding_every_field() -> TrackerState:
    comment = Comment(text=" first\n<b>&</b> ", author="Dana", created_at=NOW)
    later = Comment(text="second", author="Ari", created_at=datetime(2026, 10, 12, tzinfo=UTC))
    tasks = [
        _stored(id=1, title=" Notes ", status="in-progress", priority="low"),
        _stored(
            id=2,
            title="Set up CI",
            status="done",
            priority="high",
            assignee="Dana",
            labels=["bug", "ui"],
            due_date="2026-10-20",
            comments=[comment, later],
        ),
        _stored(id=3, project_id=2, title='say "hi" é', status="cancelled", priority="critical"),
        _stored(id=4, project_id=2, title=" Notes ", assignee="Carol"),
    ]
    return restore_state(
        [(1, "Alpha", "x"), (2, "Beta", "")],
        3,
        ["Dana", " Ari ", "dana"],
        tasks=tasks,
        next_task_id=5,
    )


def test_tasks_and_counter_round_trip_every_field(tmp_path):
    """CP-134, CP-135: every field of every task and the counter come back exactly."""
    location = tmp_path / "data"
    saved = SavedData(location)
    state = _state_holding_every_field()

    saved.save(state)
    document = json.loads((location / FILE_NAME).read_text(encoding="utf-8"))

    assert saved.load() == state
    assert document["next_task_id"] == 5
    assert [set(entry) for entry in document["tasks"]] == [TASK_KEYS] * 4
    assert document["assignees"] == ["Dana", " Ari ", "dana"]
    second = document["tasks"][1]
    assert second["status"] == "done" and second["priority"] == "high"
    assert second["due_date"] == "2026-10-20" and second["assignee"] == "Dana"
    assert second["created_at"] == "2026-10-11T09:30:00Z"
    assert second["labels"] == ["bug", "ui"]
    assert [set(comment) for comment in second["comments"]] == [
        {"text", "author", "created_at"}
    ] * 2
    assert second["comments"][1]["created_at"] == "2026-10-12T00:00:00Z"
    assert document["tasks"][0]["assignee"] is None and document["tasks"][0]["due_date"] is None


def test_a_newly_added_task_saves_with_no_labels_and_no_comments(tmp_path):
    """CP-135: a task added with no label and no comment saves empty collections for both."""
    saved = SavedData(tmp_path / "data")
    state, _ = add_task(_state_with(("Alpha", "")), 1, "T", "high", "", "2026-10-20", NOW)

    saved.save(state)
    entry = json.loads((tmp_path / "data" / FILE_NAME).read_text(encoding="utf-8"))["tasks"][0]

    assert entry["labels"] == [] and entry["comments"] == []
    assert saved.load() == state


def test_restart_keeps_task_identities_fields_and_list_order(tmp_path):
    """CP-113, CP-130, CP-134: after a restart the next task takes the next identity."""
    saved = SavedData(tmp_path / "data")
    state = _state_with(("Alpha", ""))
    for title, due in (("Later", "2026-11-02"), ("Undated", ""), ("Earlier", "2026-10-10")):
        state, _ = add_task(state, 1, title, "", "", due, NOW)
    saved.save(state)

    restored = saved.load()
    assert restored is not None
    order_before = [task.title for task in list_project_tasks(state, 1)]
    assert [task.title for task in list_project_tasks(restored, 1)] == order_before
    assert order_before == ["Earlier", "Later", "Undated"]

    again, fresh = add_task(restored, 1, "Fourth", "", "", "", NOW)

    assert fresh.id == 4 and fresh.id not in {task.id for task in state.tasks}
    assert again.next_task_id == 5


def test_both_legacy_forms_load_without_rewriting(tmp_path):
    """CP-136: both older files read with no tasks and a counter of 1, bytes unchanged until a save."""
    forms = {
        "projects-only": _legacy_document(_project(1, "Alpha"), next_project_id=2),
        "with-people": json.dumps(
            {"next_project_id": 2, "projects": [_project()], "assignees": ["Dana", " Ari"]}
        ).encode(),
    }
    for name, content in forms.items():
        location = tmp_path / name
        saved_file = _write(location, content)
        before = _listing(location)
        saved = SavedData(location)

        state = saved.load()

        assert state is not None, name
        assert state.tasks == () and state.next_task_id == 1, name
        assert saved_file.read_bytes() == content and _listing(location) == before, name

        saved.save(state)
        assert set(json.loads(saved_file.read_text(encoding="utf-8"))) == FULL_KEYS, name


def test_first_task_save_on_a_legacy_file_writes_the_full_shape(tmp_path):
    """CP-136: the first save after a legacy start saves the tasks with the rest."""
    saved_file = _write(
        tmp_path / "data", _legacy_document(_project(1, "Alpha"), next_project_id=2)
    )
    saved = SavedData(tmp_path / "data")
    state = saved.load()
    assert state is not None

    new_state, _ = add_task(state, 1, "First", "", "", "", NOW)
    saved.save(new_state)

    document = json.loads(saved_file.read_text(encoding="utf-8"))
    assert set(document) == FULL_KEYS
    assert document["assignees"] == [] and document["next_task_id"] == 2
    assert [entry["title"] for entry in document["tasks"]] == ["First"]


def _unreadable_at_load(tmp_path, content: bytes) -> None:
    location = tmp_path / "data"
    saved_file = _write(location, content)
    before = _listing(location)

    with pytest.raises(UnreadableData) as error:
        SavedData(location).load()

    assert error.value.location == location
    assert saved_file.read_bytes() == content and _listing(location) == before


def _without(entry: dict, key: str) -> dict:
    return {name: value for name, value in entry.items() if name != key}


MALFORMED_SHAPES = [
    pytest.param(
        json.dumps({"next_project_id": 2, "projects": [_project()], "tasks": []}).encode(),
        id="tasks-without-counter-or-assignees",
    ),
    pytest.param(
        json.dumps(
            {"next_project_id": 2, "projects": [_project()], "assignees": [], "next_task_id": 1}
        ).encode(),
        id="counter-without-tasks",
    ),
    pytest.param(
        json.dumps(
            {"next_project_id": 2, "projects": [_project()], "assignees": [], "tasks": []}
        ).encode(),
        id="tasks-without-counter",
    ),
    pytest.param(_full_document(extra=1), id="extra-top-level-key"),
    pytest.param(_full_document(tasks={}), id="tasks-object"),
    pytest.param(_full_document(tasks="none"), id="tasks-text"),
    pytest.param(_full_document(tasks=["Plan"]), id="task-not-an-object"),
    pytest.param(_full_document(tasks=[_without(_task_entry(), "title")]), id="task-missing-key"),
    pytest.param(_full_document(tasks=[_task_entry(extra=1)]), id="task-extra-key"),
    pytest.param(_full_document(tasks=[_task_entry(id=True)]), id="boolean-task-id"),
    pytest.param(_full_document(tasks=[_task_entry(id="1")]), id="text-task-id"),
    pytest.param(_full_document(tasks=[_task_entry(id=1.0)]), id="float-task-id"),
    pytest.param(_full_document(tasks=[_task_entry(project_id=True)]), id="boolean-project-id"),
    pytest.param(_full_document(next_task_id=True), id="boolean-counter"),
    pytest.param(_full_document(next_task_id="2"), id="text-counter"),
    pytest.param(_full_document(next_task_id=2.5), id="float-counter"),
    pytest.param(_full_document(next_task_id=None), id="null-counter"),
    pytest.param(_full_document(tasks=[_task_entry(title=7)]), id="number-title"),
    pytest.param(_full_document(tasks=[_task_entry(status=3)]), id="number-status"),
    pytest.param(_full_document(tasks=[_task_entry(priority=None)]), id="null-priority"),
    pytest.param(_full_document(tasks=[_task_entry(assignee=7)]), id="number-assignee"),
    pytest.param(_full_document(tasks=[_task_entry(due_date=20261020)]), id="number-due-date"),
    pytest.param(_full_document(tasks=[_task_entry(labels="bug")]), id="labels-text"),
    pytest.param(_full_document(tasks=[_task_entry(labels=["bug", 7])]), id="number-label"),
    pytest.param(_full_document(tasks=[_task_entry(comments={})]), id="comments-object"),
    pytest.param(_full_document(tasks=[_task_entry(comments=["hi"])]), id="comment-not-an-object"),
    pytest.param(
        _full_document(tasks=[_task_entry(comments=[{"text": "t", "author": "a"}])]),
        id="comment-missing-key",
    ),
    pytest.param(
        _full_document(
            tasks=[
                _task_entry(
                    comments=[
                        {"text": "t", "author": "a", "created_at": "2026-10-11T09:30:00Z", "x": 1}
                    ]
                )
            ]
        ),
        id="comment-extra-key",
    ),
    pytest.param(
        _full_document(
            tasks=[
                _task_entry(
                    comments=[{"text": 1, "author": "a", "created_at": "2026-10-11T09:30:00Z"}]
                )
            ]
        ),
        id="comment-number-text",
    ),
    pytest.param(_full_document(tasks=[_task_entry(created_at=1)]), id="number-instant"),
    pytest.param(
        _full_document(tasks=[_task_entry(created_at="yesterday")]), id="undecodable-instant"
    ),
    pytest.param(
        _full_document(tasks=[_task_entry(created_at="2026-10-11T09:30:00")]), id="naive-instant"
    ),
    pytest.param(
        _full_document(tasks=[_task_entry(created_at="2026-10-11")]), id="date-only-instant"
    ),
    pytest.param(
        _full_document(
            tasks=[
                _task_entry(
                    comments=[{"text": "t", "author": "a", "created_at": "2026-10-11T09:30:00"}]
                )
            ]
        ),
        id="naive-comment-instant",
    ),
]


@pytest.mark.parametrize("content", MALFORMED_SHAPES)
def test_partial_extra_or_malformed_task_shape_is_unreadable(tmp_path, content):
    """CP-136, CP-137: a shape that is none of the three forms is unreadable whole, bytes kept."""
    _unreadable_at_load(tmp_path, content)


RULE_BREAKS = [
    pytest.param(_task_entry(status="started"), 2, id="unknown-status"),
    pytest.param(_task_entry(status=""), 2, id="empty-status"),
    pytest.param(_task_entry(priority="urgent"), 2, id="unknown-priority"),
    pytest.param(_task_entry(priority=""), 2, id="empty-priority"),
    pytest.param(_task_entry(project_id=9), 2, id="unknown-project"),
    pytest.param(_task_entry(title=""), 2, id="empty-title"),
    pytest.param(_task_entry(title="  \u00a0\t"), 2, id="blank-title"),
    pytest.param(_task_entry(title="t" * 201), 2, id="title-201-characters"),
    pytest.param(_task_entry(due_date="2026-02-30"), 2, id="impossible-date"),
    pytest.param(_task_entry(due_date=""), 2, id="empty-date"),
    pytest.param(_task_entry(due_date="20261020"), 2, id="compact-date"),
    pytest.param(_task_entry(assignee=""), 2, id="empty-assignee"),
    pytest.param(_task_entry(assignee="   "), 2, id="blank-assignee"),
    pytest.param(_task_entry(assignee="n" * 201), 2, id="assignee-201-characters"),
    pytest.param(_task_entry(id=0), 2, id="zero-identity"),
    pytest.param(_task_entry(id=-3), 2, id="negative-identity"),
    pytest.param(_task_entry(id=2), 2, id="identity-equal-to-counter"),
    pytest.param(_task_entry(id=5), 2, id="identity-above-counter"),
    pytest.param(_task_entry(), 0, id="zero-counter"),
    pytest.param(_task_entry(), -1, id="negative-counter"),
]


@pytest.mark.parametrize(("entry", "counter"), RULE_BREAKS)
def test_each_task_rule_break_is_unreadable_at_start(tmp_path, entry, counter):
    """CP-137: each break alone makes the data unreadable, and the bytes stay as they were."""
    _unreadable_at_load(tmp_path, _full_document(tasks=[entry], next_task_id=counter))


def test_two_tasks_with_one_identity_are_unreadable(tmp_path):
    """CP-137."""
    _unreadable_at_load(
        tmp_path, _full_document(tasks=[_task_entry(), _task_entry(title="Other")], next_task_id=3)
    )


def test_historical_assignee_and_structural_label_comment_values_load(tmp_path):
    """CP-137, CP-209, CP-264: an off-list assignee is readable, and so are comments that keep the
    comment rules whoever wrote them; labels that keep the label rules (CP-197) load as saved."""
    comment = {"text": "Seen", "author": "Nobody Now", "created_at": "2026-10-11T09:30:00Z"}
    other = {"text": "Again", "author": "Dana", "created_at": "2026-10-11T09:30:00Z"}
    entry = _task_entry(assignee="Carol", labels=["x", "X", " x"], comments=[comment, other])
    saved_file = _write(tmp_path / "data", _full_document(tasks=[entry]))

    state = SavedData(tmp_path / "data").load()

    assert state is not None
    task = state.tasks[0]
    assert task.assignee == "Carol" and "Carol" not in state.assignees
    assert task.labels == ("x", "X", " x") and len(task.comments) == 2
    assert saved_file.read_bytes() == _full_document(tasks=[entry])


LABEL_BREAKS = [
    pytest.param([""], id="empty-label"),
    pytest.param(["x" * 201], id="label-201-code-points"),
    pytest.param(["\U0001f600" * 201], id="label-201-non-basic-plane-characters"),
    pytest.param(["bug", "ui", "bug"], id="repeated-label"),
    pytest.param(["   ", "   "], id="repeated-spaces-only-label"),
]


@pytest.mark.parametrize("labels", LABEL_BREAKS)
def test_saved_label_break_refuses_whole_file_unchanged(tmp_path, labels):
    """CP-197, CP-205: a valid task before the invalid one is not loaded either; the file stays."""
    entries = [
        _task_entry(id=1, labels=["bug"]),
        _task_entry(id=2, title="Other", labels=labels),
    ]
    _unreadable_at_load(tmp_path, _full_document(tasks=entries, next_task_id=3))


VALID_LABEL_COLLECTIONS = [
    pytest.param([], id="no-labels"),
    pytest.param(["   "], id="spaces-only"),
    pytest.param(["x" * 200], id="exactly-200-code-points"),
    pytest.param(["\U0001f600" + "x" * 199], id="200-code-points-with-non-basic-plane"),
    pytest.param(["bug", "Bug", " bug", "bug "], id="case-and-space-distinct"),
]


@pytest.mark.parametrize("labels", VALID_LABEL_COLLECTIONS)
def test_valid_saved_labels_load_verbatim(tmp_path, labels):
    """CP-197: the readable collections come back exactly as saved, in order."""
    content = _full_document(tasks=[_task_entry(labels=labels)])
    saved_file = _write(tmp_path / "data", content)

    state = SavedData(tmp_path / "data").load()

    assert state is not None
    assert state.tasks[0].labels == tuple(labels)
    assert saved_file.read_bytes() == content


def test_the_same_label_on_different_tasks_loads(tmp_path):
    """CP-197: uniqueness is per task, so one label may be carried by two tasks."""
    entries = [
        _task_entry(id=1, labels=["bug"]),
        _task_entry(id=2, title="Other", labels=["bug"]),
    ]
    _write(tmp_path / "data", _full_document(tasks=entries, next_task_id=3))

    state = SavedData(tmp_path / "data").load()

    assert state is not None
    assert [task.labels for task in state.tasks] == [("bug",), ("bug",)]


def test_task_save_failure_preserves_original_file(tmp_path):
    """CP-122, CP-134: a failed save with tasks held leaves the earlier file whole and readable."""
    location = tmp_path / "data"
    saved = SavedData(location)
    state = _state_holding_every_field()
    saved.save(state)
    before = (location / FILE_NAME).read_bytes()
    bigger, _ = add_task(state, 1, "Another", "", "", "", NOW)
    location.chmod(0o500)
    try:
        with pytest.raises(OSError):
            saved.save(bigger)
    finally:
        location.chmod(0o700)

    assert (location / FILE_NAME).read_bytes() == before
    assert saved.load() == state
    assert _listing(location) == [FILE_NAME]


SAVE_TASKS_FOREVER = textwrap.dedent(
    """
    import sys
    from datetime import UTC, datetime
    from pathlib import Path
    from domain import add_task, create_project, empty_state
    from persistence import SavedData

    def build(letter):
        state, _ = create_project(empty_state(), "P", "")
        for index in range(30):
            state, _ = add_task(
                state, 1, letter * 150 + str(index), "high", "", "2026-10-20",
                datetime(2026, 10, 11, tzinfo=UTC),
            )
        return state

    saved = SavedData(Path(sys.argv[1]))
    first, second = build("a"), build("b")
    saved.save(first)
    print("ready", flush=True)
    while True:
        saved.save(second)
        saved.save(first)
    """
)


def test_a_killed_save_with_tasks_leaves_one_whole_state(tmp_path):
    """CP-134: an interrupted save with tasks and a counter leaves one complete file."""
    environment = {**os.environ, "PYTHONPATH": str(PRODUCT_ROOT)}
    generator = random.Random(2027)
    states = []
    for letter in ("a", "b"):
        state, _ = create_project(empty_state(), "P", "")
        for index in range(30):
            state, _ = add_task(
                state,
                1,
                letter * 150 + str(index),
                "high",
                "",
                "2026-10-20",
                NOW.replace(hour=0, minute=0),
            )
        states.append(state)

    for attempt in range(25):
        location = tmp_path / f"attempt-{attempt}"
        process = subprocess.Popen(
            [sys.executable, "-c", SAVE_TASKS_FOREVER, str(location)],
            cwd=tmp_path,
            env=environment,
            stdout=subprocess.PIPE,
            text=True,
        )
        assert process.stdout is not None
        assert process.stdout.readline().strip() == "ready"
        try:
            process.wait(timeout=generator.uniform(0.0, 0.06))
        except subprocess.TimeoutExpired:
            pass
        process.send_signal(signal.SIGKILL)
        process.wait()
        process.stdout.close()

        assert SavedData(location).load() in states


def test_task_edit_restart_preserves_format_and_protected_fields(tmp_path):
    """CP-170, CP-171: older data loads as it is, and an edit changes only the edited fields."""
    location = tmp_path / "data"
    saved = SavedData(location)
    comment = Comment(text="note", author="Dana", created_at=NOW)
    tasks = [
        _stored(
            id=1,
            title="Later",
            due_date="2026-11-02",
            status="done",
            labels=["bug"],
            comments=[comment],
        ),
        _stored(id=2, title="Undated"),
        _stored(id=3, title="Tied", due_date="2026-10-10"),
        _stored(id=4, title="Tied too", due_date="2026-10-10"),
    ]
    original = restore_state([(1, "Alpha", "")], 2, ["Dana"], tasks=tasks, next_task_id=5)
    saved.save(original)
    before = json.loads((location / FILE_NAME).read_text(encoding="utf-8"))
    state = saved.load()
    assert state == original

    tracker = Tracker(state, saved, _FixedClock())
    outcome = tracker.edit_task(
        1,
        TaskFields(title="Edited", due_date="2026-10-10"),
        TaskFields(title="Later", due_date="2026-11-02"),
    )
    assert outcome.changed

    document = json.loads((location / FILE_NAME).read_text(encoding="utf-8"))
    assert set(document) == set(before) == FULL_KEYS
    assert document["next_task_id"] == before["next_task_id"] == 5
    assert [set(entry) for entry in document["tasks"]] == [TASK_KEYS] * 4
    edited = document["tasks"][0]
    assert (edited["title"], edited["due_date"]) == ("Edited", "2026-10-10")
    for key in ("id", "project_id", "status", "labels", "created_at", "comments"):
        assert edited[key] == before["tasks"][0][key], key
    assert document["tasks"][1:] == before["tasks"][1:]

    restarted = Tracker(SavedData(location).load(), saved, _FixedClock())
    rows = restarted.project_tasks(1)
    assert [row.task.title for row in rows] == ["Edited", "Tied", "Tied too", "Undated"]
    assert [row.overdue for row in rows] == [False, True, True, False]


def _saved_document(location: Path) -> dict:
    return json.loads((location / FILE_NAME).read_text(encoding="utf-8"))


def _restart(location: Path) -> Tracker:
    """A tracker built the way a start builds one: from what the saved data loads."""
    saved = SavedData(location)
    state = saved.load()
    assert state is not None
    return Tracker(state, saved, _FixedClock())


def test_labels_survive_add_reload_remove_reload(tmp_path):
    """CP-198, CP-199: each action saves through the real file, and a newly built tracker loads
    exactly the result, in order."""
    location = tmp_path / "data"
    SavedData(location).save(_state_holding_every_field())

    _restart(location).add_task_label(2, "ops")
    added = _restart(location).task(2)
    assert added is not None and added.labels == ("bug", "ui", "ops")
    assert _saved_document(location)["tasks"][1]["labels"] == ["bug", "ui", "ops"]

    _restart(location).remove_task_label(2, "bug")
    removed = _restart(location).task(2)
    assert removed is not None and removed.labels == ("ui", "ops")
    assert _saved_document(location)["tasks"][1]["labels"] == ["ui", "ops"]

    _restart(location).remove_task_label(2, "ui")
    _restart(location).remove_task_label(2, "ops")
    emptied = _restart(location).task(2)
    assert emptied is not None and emptied.labels == ()
    assert _saved_document(location)["tasks"][1]["labels"] == []


def test_label_actions_preserve_saved_shape_and_other_values(tmp_path):
    """CP-198, CP-199: the saved keys, the People list, the counters and every non-label field of
    every task are what they were after both saves and both reloads."""
    location = tmp_path / "data"
    SavedData(location).save(_state_holding_every_field())
    before = _saved_document(location)

    _restart(location).add_task_label(2, "ops")
    after_add = _saved_document(location)
    _restart(location).remove_task_label(2, "bug")
    after_remove = _saved_document(location)

    for document in (after_add, after_remove):
        assert set(document) == set(before) == FULL_KEYS
        assert document["assignees"] == before["assignees"] == ["Dana", " Ari ", "dana"]
        assert document["next_task_id"] == before["next_task_id"] == 5
        assert document["next_project_id"] == before["next_project_id"]
        assert document["projects"] == before["projects"]
        assert [set(entry) for entry in document["tasks"]] == [TASK_KEYS] * 4
        assert [set(comment) for comment in document["tasks"][1]["comments"]] == [
            {"text", "author", "created_at"}
        ] * 2
        for position, entry in enumerate(document["tasks"]):
            original = before["tasks"][position]
            assert {k: v for k, v in entry.items() if k != "labels"} == {
                k: v for k, v in original.items() if k != "labels"
            }
        assert [entry["labels"] for entry in document["tasks"][:1] + document["tasks"][2:]] == [
            before_entry["labels"] for before_entry in before["tasks"][:1] + before["tasks"][2:]
        ]
    assert after_add["tasks"][1]["labels"] == ["bug", "ui", "ops"]
    assert after_remove["tasks"][1]["labels"] == ["ui", "ops"]


# --- The operator name (SRS DR-5, FR-27; change spec CP-226 to CP-228, CP-233, CP-234) ---

OLD_STATE_KEYS = (
    {"next_project_id", "projects"},
    {"next_project_id", "projects", "assignees"},
    {"next_project_id", "projects", "assignees", "next_task_id", "tasks"},
)
NON_BMP_CHARACTER = chr(0x1F600)
BOUNDARY_NAME = "a" * 199 + NON_BMP_CHARACTER


def _with_name(**changes) -> bytes:
    """The six-key document of _full_document with `operator_name` and any other key replaced."""
    document = json.loads(_full_document())
    document["operator_name"] = None
    document.update(changes)
    return json.dumps(document, ensure_ascii=False).encode("utf-8")


def _saved_after(tmp_path, state: TrackerState) -> dict:
    SavedData(tmp_path / "data").save(state)
    return _saved_document(tmp_path / "data")


def test_saved_operator_name_has_only_the_six_allowed_keys(tmp_path):
    """CP-226, CP-234: each full save writes the previous five keys plus `operator_name`, a string
    verbatim when set and JSON null when unset, and nothing else about any person."""
    state = _state_holding_every_field()

    unset = _saved_after(tmp_path / "unset", state)
    named = _saved_after(tmp_path / "named", dataclasses.replace(state, operator_name=" Sam "))

    assert set(unset) == set(named) == FULL_KEYS
    assert set(unset) == OLD_STATE_KEYS[2] | {"operator_name"}
    assert unset["operator_name"] is None
    assert named["operator_name"] == " Sam "
    assert {k: v for k, v in named.items() if k != "operator_name"} == {
        k: v for k, v in unset.items() if k != "operator_name"
    }


def test_operator_name_round_trip_preserves_the_complete_rich_state(tmp_path):
    """CP-226: projects, task fields, labels, comments in order, assignees and both counters come
    back exactly beside the name, and the name comes back exactly as saved."""
    saved = SavedData(tmp_path / "data")
    state = dataclasses.replace(_state_holding_every_field(), operator_name="  Sam <b>&</b> Lee ")

    saved.save(state)
    restored = saved.load()

    assert restored == state
    assert restored is not None and restored.operator_name == "  Sam <b>&</b> Lee "
    assert restored.tasks[1].comments == state.tasks[1].comments
    assert restored.assignees == ("Dana", " Ari ", "dana")
    assert (restored.next_project_id, restored.next_task_id) == (3, 5)


def test_each_legacy_shape_loads_without_a_name_or_a_write(tmp_path):
    """CP-227: the three older forms load with every value they can hold, no name, and unchanged
    bytes; the first real change then writes the six-key full form."""
    documents = [
        _legacy_document(_project(1, "Alpha", "x"), _project(2, "Beta"), next_project_id=3),
        json.dumps(
            {"next_project_id": 2, "projects": [_project()], "assignees": ["Dana", " Ari"]}
        ).encode(),
        _full_document(),
    ]
    for content, keys in zip(documents, OLD_STATE_KEYS, strict=True):
        assert set(json.loads(content)) == keys
        location = tmp_path / str(len(keys))
        saved_file = _write(location, content)
        before = _listing(location)
        saved = SavedData(location)

        state = saved.load()

        assert state is not None and state.operator_name is None
        assert saved_file.read_bytes() == content and _listing(location) == before
        old = json.loads(content)
        assert [project.name for project in state.projects] == [p["name"] for p in old["projects"]]
        assert list(state.assignees) == old.get("assignees", [])
        assert [task.title for task in state.tasks] == [t["title"] for t in old.get("tasks", [])]
        assert state.next_task_id == old.get("next_task_id", 1)

        saved.save(dataclasses.replace(state, operator_name="Sam"))
        written = json.loads(saved_file.read_text(encoding="utf-8"))
        assert set(written) == FULL_KEYS and written["operator_name"] == "Sam"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        pytest.param(None, None, id="null"),
        pytest.param(BOUNDARY_NAME, BOUNDARY_NAME, id="200-code-points-with-a-non-bmp-character"),
        pytest.param("  Sam  ", "  Sam  ", id="surrounded-by-spaces"),
        pytest.param("\u200b", "\u200b", id="zero-width-space-alone"),
    ],
)
def test_new_saved_name_loads_null_boundary_and_surrounded_spaces(tmp_path, value, expected):
    """CP-228: null, a name of exactly 200 code points and a space-surrounded name load as given,
    and loading rewrites nothing."""
    content = _with_name(operator_name=value)
    saved_file = _write(tmp_path / "data", content)

    state = SavedData(tmp_path / "data").load()

    assert state is not None and state.operator_name == expected
    assert saved_file.read_bytes() == content


@pytest.mark.parametrize(
    "value",
    [
        pytest.param(True, id="boolean"),
        pytest.param(7, id="number"),
        pytest.param(["Sam"], id="list"),
        pytest.param({"name": "Sam"}, id="object"),
    ],
)
def test_invalid_operator_name_type_refuses_the_whole_file_untouched(tmp_path, value):
    """CP-228: a name that is neither text nor null makes the whole file unreadable, unchanged."""
    _unreadable_at_load(tmp_path, _with_name(operator_name=value))


@pytest.mark.parametrize(
    "value",
    [
        pytest.param("", id="empty"),
        pytest.param("   ", id="whitespace-only"),
        pytest.param("a" * 201, id="201-code-points"),
        pytest.param(" " * 201, id="201-spaces"),
    ],
)
def test_invalid_operator_name_value_refuses_the_whole_file_untouched(tmp_path, value):
    """CP-228, CP-220, CP-221: the domain restore rule refuses a blank or over-long saved name."""
    _unreadable_at_load(tmp_path, _with_name(operator_name=value))


def test_name_format_keeps_exact_required_and_unknown_key_checks(tmp_path):
    """CP-227, CP-228: an unknown key, a missing required key and an old shape with a name added
    stay unreadable, so the key sets are not widened by accident."""
    projects_only = json.loads(_legacy_document(_project(1, "Alpha"), next_project_id=2))
    people = {**projects_only, "assignees": []}
    full = json.loads(_with_name(operator_name="Sam"))
    shapes = {
        "unknown-key": {**full, "nickname": "Sam"},
        "missing-tasks": {k: v for k, v in full.items() if k != "tasks"},
        "missing-counter": {k: v for k, v in full.items() if k != "next_task_id"},
        "missing-projects": {k: v for k, v in full.items() if k != "projects"},
        "projects-only-with-a-name": {**projects_only, "operator_name": "Sam"},
        "people-with-a-name": {**people, "operator_name": "Sam"},
    }
    for name, document in shapes.items():
        _unreadable_at_load(tmp_path / name, json.dumps(document).encode())


# --- Saved comments (SRS DR-3, DR-6, FR-28; change spec CP-263, CP-264, CP-269, CP-270) ---

PROJECT_KEYS = {"id", "name", "description"}
COMMENT_KEYS = {"text", "author", "created_at"}


class _SteppingClock:
    """Gives an instant a minute after the one before: one for the task, then one per comment."""

    def __init__(self) -> None:
        self._next = NOW

    def now(self) -> datetime:
        instant, self._next = self._next, self._next + timedelta(minutes=1)
        return instant


def _acted_on_the_real_file(location: Path) -> Tracker:
    """AC-6's sequence through the tracker's actions: a project, an assignee, a task with every
    field, a label, the operator's own name, a comment, a rename and a second comment."""
    saved = SavedData(location)
    tracker = Tracker(empty_state(), saved, _SteppingClock())
    project = tracker.create_project("Alpha", "first project")
    tracker.add_assignee("Dana")
    task = tracker.add_task(project.id, "Set up CI", "high", "Dana", "2026-10-20")
    tracker.add_task_label(task.id, "bug")
    tracker.set_operator_name("Sam")
    tracker.add_task_comment(task.id, " first\n<b>&</b> ")
    tracker.set_operator_name("Lee")
    tracker.add_task_comment(task.id, "second")
    return tracker


def test_bad_comment_prevents_partial_loading(tmp_path):
    """CP-264, CP-270: valid projects, tasks and comments before the broken comment come back as no
    state at all, and the bytes and the directory listing are as they were."""
    valid = {"text": "Seen", "author": "Dana", "created_at": "2026-10-11T09:30:00Z"}
    broken = {**valid, "text": " \t"}
    tasks = [
        _task_entry(id=1, comments=[valid, valid]),
        _task_entry(id=2, project_id=2, title="Next", comments=[valid]),
        _task_entry(id=3, title="Last", comments=[valid, broken]),
    ]

    _unreadable_at_load(tmp_path, _full_document(tasks=tasks, next_task_id=4))


def test_every_field_and_comment_survives_action_and_restart(tmp_path):
    """CP-263, CP-269: everything entered through the tracker's actions is found again by a tracker
    built from the real saved data, comments in the order they were added."""
    location = tmp_path / "data"
    acted = _acted_on_the_real_file(location)

    restarted = _restart(location)

    assert restarted.projects() == acted.projects()
    assert restarted.assignees() == ("Dana",)
    assert restarted.operator_name() == "Lee"
    task = restarted.task(1)
    assert task is not None and task == acted.task(1)
    assert (task.title, task.priority.value, task.assignee) == ("Set up CI", "high", "Dana")
    assert (task.due_date, task.labels, task.status.value) == (
        date(2026, 10, 20),
        ("bug",),
        "todo",
    )
    assert task.comments == (
        Comment(text=" first\n<b>&</b> ", author="Sam", created_at=NOW + timedelta(minutes=1)),
        Comment(text="second", author="Lee", created_at=NOW + timedelta(minutes=2)),
    )
    assert (restarted.task(1), restarted.assignees()) == (acted.task(1), acted.assignees())


def test_comment_restart_has_only_the_existing_saved_keys(tmp_path):
    """CP-263, CP-269: the state, each project, each task, each comment and the counters hold
    exactly the keys they held before this change, and nothing of a request or an outcome."""
    location = tmp_path / "data"
    _acted_on_the_real_file(location)

    document = _saved_document(location)

    assert set(document) == FULL_KEYS
    assert all(set(project) == PROJECT_KEYS for project in document["projects"])
    assert all(set(task) == TASK_KEYS for task in document["tasks"])
    comments = [comment for task in document["tasks"] for comment in task["comments"]]
    assert len(comments) == 2
    assert all(set(comment) == COMMENT_KEYS for comment in comments)
    assert (document["next_project_id"], document["next_task_id"]) == (2, 2)
    assert document["tasks"][0]["comments"][1] == {
        "text": "second",
        "author": "Lee",
        "created_at": "2026-10-11T09:32:00Z",
    }
