"""Unit tests of the task rules in domain/tasks.py (layer 1), with no file and no clock.

Checks SRS FR-15 (creating a task), FR-39 and FR-40 (refusals and the title maximum), FR-36 (the
list order), DR-2 (the Task entity and its identity) and DR-6 (saved tasks are checked by the same
rules), FR-16 (editing a task's title, priority, assignee and due date) and FR-23 (a task's
labels, added and removed and checked on restoration). Change spec rules CP-111 to CP-113, CP-116
to CP-121, CP-130, CP-135, CP-137 and CP-140 are the ones each test names, and CP-151 to CP-154,
CP-157 to CP-160, CP-162 to CP-165, CP-167, CP-171 and CP-172 for the edit, and CP-189, CP-194,
CP-197, CP-199 and CP-201 for the labels.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, date, datetime, timedelta

import pytest

from domain import (
    SHORT_TEXT_MAX,
    AssigneeNotListed,
    BlankComment,
    BlankName,
    BlankTitle,
    Comment,
    EmptyLabel,
    InvalidDueDate,
    InvalidPriority,
    InvalidTaskStatus,
    LabelNotCarried,
    Priority,
    ProjectNotFound,
    Refusal,
    RepeatedSavedLabel,
    Task,
    TaskEditContext,
    TaskEditOutcome,
    TaskFields,
    TaskLabelOutcome,
    TaskNotFound,
    TaskStatus,
    TextField,
    TextTooLong,
    TrackerState,
    add_assignee,
    add_task,
    add_task_label,
    create_project,
    edit_task,
    find_task,
    list_project_tasks,
    remove_assignee,
    remove_task_label,
    restore_state,
    restore_task,
    task_edit_context,
)

NOW = datetime(2026, 10, 11, 9, 30, tzinfo=UTC)


def _base() -> TrackerState:
    return restore_state([(1, "Alpha", ""), (2, "Beta", "")], 3, ["Dana", "Ari"])


def _restored(**changes):
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


def test_add_task_saves_all_values_and_leaves_original_state_unchanged():
    """CP-111, CP-112."""
    before = _base()

    state, task = add_task(before, 1, "Set up CI", "high", "Dana", "2026-10-20", NOW)

    assert task == Task(
        id=1,
        project_id=1,
        title="Set up CI",
        status=TaskStatus.TODO,
        priority=Priority.HIGH,
        assignee="Dana",
        labels=(),
        due_date=date(2026, 10, 20),
        created_at=NOW,
        comments=(),
    )
    assert task.created_at.utcoffset() == timedelta(0)
    assert state.tasks == (task,)
    assert state.next_task_id == 2
    assert before == _base()
    assert before.tasks == () and before.next_task_id == 1


def test_title_only_add_uses_defaults():
    """CP-112: absent or empty optional strings mean medium, unassigned, undated."""
    _, task = add_task(_base(), 1, "Write notes", "", "", "", NOW)

    assert (task.priority, task.assignee, task.due_date) == (Priority.MEDIUM, None, None)
    assert task.status is TaskStatus.TODO
    assert task.labels == () and task.comments == ()


@pytest.mark.parametrize("word", ["low", "medium", "high", "critical"])
def test_all_four_priorities_are_accepted(word):
    _, task = add_task(_base(), 1, "T", word, "", "", NOW)

    assert task.priority is Priority(word)


def test_task_title_is_exact_and_need_not_be_unique():
    """CP-111, CP-113: spaces survive, duplicates are allowed, identities are global."""
    state, first = add_task(_base(), 1, " Notes ", "", "", "", NOW)
    state, second = add_task(state, 1, " Notes ", "", "", "", NOW)
    state, third = add_task(state, 2, " Notes ", "", "", "", NOW)

    assert (first.title, second.title, third.title) == (" Notes ",) * 3
    assert [first.id, second.id, third.id] == [1, 2, 3]
    assert state.next_task_id == 4


def test_title_bounds_count_code_points():
    """CP-111, CP-118: 200 accepted, 201 refused, a character outside the BMP counts one."""
    _, accepted = add_task(_base(), 1, "t" * 200, "", "", "", NOW)
    assert len(accepted.title) == 200
    _, astral = add_task(_base(), 1, "\U0001f600" * 200, "", "", "", NOW)
    assert len(astral.title) == 200

    for too_long in ("t" * 201, "\U0001f600" * 201):
        with pytest.raises(TextTooLong) as refusal:
            add_task(_base(), 1, too_long, "", "", "", NOW)
        assert refusal.value.field is TextField.TITLE
        assert refusal.value.maximum == SHORT_TEXT_MAX == 200


@pytest.mark.parametrize("title", ["", "   ", "\t\n", "  　", " "])
def test_blank_titles_are_refused(title):
    """CP-117: empty text and Unicode-whitespace-only text have no character to show."""
    with pytest.raises(BlankTitle):
        add_task(_base(), 1, title, "", "", "", NOW)


def test_title_of_201_spaces_gets_the_too_long_reason():
    """CP-118."""
    with pytest.raises(TextTooLong):
        add_task(_base(), 1, " " * 201, "", "", "", NOW)


def test_refusal_precedence_consumes_no_identity():
    """CP-116 to CP-121 and the design's order: project, length, blank, priority, assignee, date."""
    before = _base()
    everything_wrong = ("t" * 201, "urgent", "Carol", "2026-02-30")

    with pytest.raises(ProjectNotFound):
        add_task(before, 9, *everything_wrong, NOW)
    with pytest.raises(TextTooLong):
        add_task(before, 1, *everything_wrong, NOW)
    with pytest.raises(BlankTitle):
        add_task(before, 1, " ", "urgent", "Carol", "2026-02-30", NOW)
    with pytest.raises(InvalidPriority):
        add_task(before, 1, "T", "urgent", "Carol", "2026-02-30", NOW)
    with pytest.raises(AssigneeNotListed):
        add_task(before, 1, "T", "high", "Carol", "2026-02-30", NOW)
    with pytest.raises(InvalidDueDate):
        add_task(before, 1, "T", "high", "Dana", "2026-02-30", NOW)

    assert before == _base()
    _, task = add_task(before, 1, "T", "", "", "", NOW)
    assert task.id == 1


def test_new_assignment_requires_current_exact_listed_name():
    """CP-116, CP-119: the name must be on the list now, exactly as saved."""
    with pytest.raises(AssigneeNotListed) as case_changed:
        add_task(_base(), 1, "T", "", "dana", "", NOW)
    assert case_changed.value.name == "dana"
    with pytest.raises(AssigneeNotListed) as padded:
        add_task(_base(), 1, "T", "", " Dana", "", NOW)
    assert padded.value.name == " Dana"
    with pytest.raises(AssigneeNotListed):
        add_task(_base(), 1, "T", "", "None", "", NOW)

    listed = add_assignee(_base(), " Ari ")
    _, task = add_task(listed, 1, "T", "", " Ari ", "", NOW)
    assert task.assignee == " Ari "


def test_stale_assignee_is_refused_after_the_name_leaves_the_list():
    """CP-119."""
    state, _ = add_task(_base(), 1, "Earlier", "", "Dana", "", NOW)
    state = remove_assignee(state, "Dana")

    with pytest.raises(AssigneeNotListed):
        add_task(state, 1, "Plan", "", "Dana", "", NOW)


def test_calendar_date_requires_exact_valid_iso_date():
    """CP-110, CP-120: empty means none on the form; a bad date is refused."""
    _, leap = add_task(_base(), 1, "T", "", "", "2028-02-29", NOW)
    assert leap.due_date == date(2028, 2, 29)

    for bad in (
        "2027-02-29",
        "2026-02-30",
        "20261011",
        "2026-W41-7",
        "2026-10-11T00:00",
        " 2026-10-11",
    ):
        with pytest.raises(InvalidDueDate):
            add_task(_base(), 1, "T", "", "", bad, NOW)


def test_task_restoration_accepts_all_statuses_and_historical_assignee():
    """CP-137: an off-list exact valid assignee is readable; labels and comments are carried."""
    comment = Comment(text="Looks fine", author="Dana", created_at=NOW)
    for status in ("todo", "in-progress", "done", "cancelled"):
        assert _restored(status=status).status is TaskStatus(status)
    for priority in ("low", "medium", "high", "critical"):
        assert _restored(priority=priority).priority is Priority(priority)

    task = _restored(
        assignee="Carol", labels=["bug", "ui"], due_date="2026-10-20", comments=[comment]
    )

    assert task.assignee == "Carol"
    assert task.labels == ("bug", "ui")
    assert task.comments == (comment,)
    assert task.due_date == date(2026, 10, 20)


@pytest.mark.parametrize(
    ("change", "refusal"),
    [
        ({"title": ""}, BlankTitle),
        ({"title": "  \t"}, BlankTitle),
        ({"title": "t" * 201}, TextTooLong),
        ({"status": "started"}, InvalidTaskStatus),
        ({"status": ""}, InvalidTaskStatus),
        ({"status": "Done"}, InvalidTaskStatus),
        ({"priority": ""}, InvalidPriority),
        ({"priority": "urgent"}, InvalidPriority),
        ({"assignee": "n" * 201}, TextTooLong),
        ({"due_date": ""}, InvalidDueDate),
        ({"due_date": "2026-02-30"}, InvalidDueDate),
        ({"due_date": "20261011"}, InvalidDueDate),
    ],
)
def test_task_restoration_refuses_each_invalid_value(change, refusal):
    """CP-137: each break is refused alone, and a saved priority receives no default."""
    with pytest.raises(refusal):
        _restored(**change)


@pytest.mark.parametrize("assignee", ["", "   "])
def test_a_blank_saved_assignee_is_refused_as_a_blank_name(assignee):
    """CP-137: an assignee name with no character other than whitespace."""
    with pytest.raises(BlankName):
        _restored(assignee=assignee)


def test_state_restoration_keeps_tasks_and_counter():
    task = _restored(project_id=2, id=4)

    state = restore_state(
        [(1, "Alpha", ""), (2, "Beta", "")], 3, ["Dana"], tasks=[task], next_task_id=5
    )

    assert state.tasks == (task,)
    assert state.next_task_id == 5
    assert state.assignees == ("Dana",)


def test_task_values_are_immutable():
    """CP-135: Task, Comment, the state and their containers cannot be mutated."""
    comment = Comment(text="c", author="a", created_at=NOW)
    task = _restored(labels=["x"], comments=[comment])
    state, _ = add_task(_base(), 1, "T", "", "", "", NOW)

    with pytest.raises(FrozenInstanceError):
        task.title = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        comment.text = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        state.next_task_id = 9  # type: ignore[misc]
    assert isinstance(task.labels, tuple) and isinstance(task.comments, tuple)
    assert isinstance(state.tasks, tuple)


def test_find_task_returns_the_task_or_none():
    state, task = add_task(_base(), 2, "T", "", "", "", NOW)

    assert find_task(state, task.id) == task
    assert find_task(state, 99) is None
    assert find_task(state, 0) is None


def test_list_project_tasks_orders_explicitly_by_date_then_identity():
    """CP-130: dated first, earliest first, then the identity; storage order is not the rule."""
    stored = [
        _restored(id=1, title="undated 1"),
        _restored(id=2, title="later", due_date="2026-11-02"),
        _restored(id=3, title="undated 2", created_at=NOW - timedelta(days=9)),
        _restored(id=4, title="earlier", due_date="2026-10-10", created_at=NOW + timedelta(days=9)),
        _restored(id=5, title="tie second", due_date="2026-10-20"),
        _restored(id=6, title="other", project_id=2, due_date="2026-01-01"),
        _restored(id=7, title="tie first", due_date="2026-10-20", created_at=NOW),
    ]
    shuffled = [stored[6], stored[3], stored[0], stored[5], stored[1], stored[4], stored[2]]
    state = restore_state([(1, "Alpha", ""), (2, "Beta", "")], 3, tasks=shuffled, next_task_id=8)

    titles = [task.title for task in list_project_tasks(state, 1)]

    assert titles == ["earlier", "tie second", "tie first", "later", "undated 1", "undated 2"]
    assert [task.title for task in list_project_tasks(state, 2)] == ["other"]


def test_list_project_tasks_of_an_empty_or_all_undated_project():
    state, first = add_task(_base(), 1, "A", "", "", "", NOW)
    state, second = add_task(state, 1, "B", "", "", "", NOW)

    assert list_project_tasks(state, 2) == ()
    assert list_project_tasks(state, 1) == (first, second)
    assert list_project_tasks(_base(), 1) == ()


def test_other_domain_changes_keep_tasks_and_counter():
    """CP-105, CP-135: creating a project and People changes leave tasks and counter alone."""
    state, task = add_task(_base(), 1, "T", "", "Dana", "", NOW)

    state, _ = create_project(state, "Gamma", "")
    state = add_assignee(state, "Eve")
    state = remove_assignee(state, "Dana")

    assert state.tasks == (task,)
    assert state.next_task_id == 2
    assert find_task(state, task.id).assignee == "Dana"  # type: ignore[union-attr]


SAVED_FIELDS = TaskFields(
    title="Set up CI", priority="high", assignee="Dana", due_date="2026-10-20"
)


def _state_with(*tasks: Task, assignees=("Dana", "Ari")) -> TrackerState:
    return restore_state(
        [(1, "Alpha", ""), (2, "Beta", "")],
        3,
        assignees,
        tasks=tasks,
        next_task_id=max((task.id for task in tasks), default=0) + 1,
    )


def _saved_task(**changes) -> Task:
    values = {
        "title": "Set up CI",
        "priority": "high",
        "assignee": "Dana",
        "due_date": "2026-10-20",
    }
    values.update(changes)
    return _restored(**values)


def _edit(state, submitted, shown=SAVED_FIELDS, task_id=1):
    return edit_task(state, task_id, submitted, shown)


def test_task_edit_saves_all_four_fields_exactly():
    """CP-153: every changed value applies as submitted, spaces and names exact."""
    before = _state_with(_saved_task(), assignees=("Dana", " Eve "))
    submitted = TaskFields(
        title=" Ship it ", priority="critical", assignee=" Eve ", due_date="2026-11-01"
    )

    state, outcome = _edit(before, submitted)

    assert outcome.changed is True
    assert outcome.task == state.tasks[0]
    assert (outcome.task.title, outcome.task.priority) == (" Ship it ", Priority.CRITICAL)
    assert (outcome.task.assignee, outcome.task.due_date) == (" Eve ", date(2026, 11, 1))
    assert before == _state_with(_saved_task(), assignees=("Dana", " Eve "))


@pytest.mark.parametrize(
    ("field", "value", "check"),
    [
        ("title", "Renamed", lambda task: task.title == "Renamed"),
        ("priority", "low", lambda task: task.priority is Priority.LOW),
        ("priority", "medium", lambda task: task.priority is Priority.MEDIUM),
        ("priority", "high", lambda task: task.priority is Priority.HIGH),
        ("priority", "critical", lambda task: task.priority is Priority.CRITICAL),
        ("assignee", "Ari", lambda task: task.assignee == "Ari"),
        ("due_date", "2028-02-29", lambda task: task.due_date == date(2028, 2, 29)),
        ("due_date", "2026-12-31", lambda task: task.due_date == date(2026, 12, 31)),
    ],
)
def test_task_edit_changes_each_field_independently(field, value, check):
    """CP-152, CP-153: one changed field leaves the other three at their current values."""
    saved = _saved_task(priority="low" if value == "high" else "high")
    shown = replace(SAVED_FIELDS, priority=saved.priority.value)

    _, outcome = _edit(_state_with(saved), TaskFields(**{field: value}), shown)

    assert check(outcome.task)
    others = {"title", "priority", "assignee", "due_date"} - {field}
    for other in others:
        assert getattr(outcome.task, other) == getattr(saved, other)


def test_task_edit_clears_optional_fields():
    """CP-153: present-empty assignee and due date clear; present-empty priority has no default."""
    state = _state_with(_saved_task())

    _, cleared = _edit(state, TaskFields(assignee="", due_date=""))
    assert (cleared.task.assignee, cleared.task.due_date) == (None, None)
    assert cleared.changed is True

    with pytest.raises(InvalidPriority):
        _edit(state, TaskFields(priority=""))


def test_task_edit_uses_only_complete_changed_pairs():
    """CP-151: a missing submitted or shown value is unchanged; None is not empty."""
    state = _state_with(_saved_task())
    unchanged_requests = [
        (TaskFields(title="Other"), TaskFields()),
        (TaskFields(), TaskFields(title="Set up CI")),
        (TaskFields(assignee=""), TaskFields()),
        (TaskFields(assignee=None), TaskFields(assignee="")),
        (TaskFields(title="same"), TaskFields(title="same")),
        (TaskFields(assignee="", due_date=""), TaskFields(assignee="", due_date="")),
    ]
    for submitted, shown in unchanged_requests:
        after, outcome = edit_task(state, 1, submitted, shown)
        assert outcome.changed is False
        assert after is state and outcome.task == state.tasks[0]

    _, empty_is_a_value = edit_task(state, 1, TaskFields(assignee=""), TaskFields(assignee="Dana"))
    assert empty_is_a_value.changed is True and empty_is_a_value.task.assignee is None


def test_task_edit_replaces_stale_changed_field():
    """CP-151, CP-154: the comparison is with the shown value, never with the current one."""
    other_tab = _state_with(_saved_task(title="Their title", priority="high"))

    _, title = edit_task(other_tab, 1, TaskFields(title="My title"), TaskFields(title="Set up CI"))
    assert title.task.title == "My title"

    _, priority = edit_task(other_tab, 1, TaskFields(priority="medium"), TaskFields(priority="low"))
    assert priority.task.priority is Priority.MEDIUM


def test_task_edit_preserves_concurrent_untouched_fields():
    """CP-152: a field equal to its shown value keeps what is current, a newer value included."""
    other_tab = _state_with(_saved_task(priority="critical", assignee="Ari"))
    shown = TaskFields(title="Set up CI", priority="low", assignee="Dana")
    submitted = TaskFields(title="Renamed", priority="low", assignee="Dana")

    _, outcome = edit_task(other_tab, 1, submitted, shown)

    assert outcome.task.title == "Renamed"
    assert outcome.task.priority is Priority.CRITICAL
    assert outcome.task.assignee == "Ari"


def test_task_edit_changed_to_current_still_reports_change():
    """CP-155: the outcome says a supplied pair differed, though the task already holds it."""
    state = _state_with(_saved_task(title="Already"))

    after, outcome = edit_task(state, 1, TaskFields(title="Already"), TaskFields(title="Before"))

    assert outcome.changed is True
    assert outcome.task == state.tasks[0]
    assert after == state


def test_task_edit_with_no_changes_returns_current_values():
    """CP-157, CP-158: nothing changed, nothing validated, original state returned."""
    state = _state_with(_saved_task(assignee="Carol"))
    invalid_but_unchanged = TaskFields(title="", priority="urgent", assignee="Carol", due_date="x")

    after, outcome = edit_task(state, 1, invalid_but_unchanged, invalid_but_unchanged)

    assert after is state
    assert outcome == TaskEditOutcome(task=state.tasks[0], changed=False)


def test_task_edit_keeps_or_replaces_unlisted_assignee():
    """CP-158, CP-159: an off-list name is kept untouched, replaced, and then cannot return."""
    state = _state_with(_saved_task(assignee="Carol"))
    shown = TaskFields(title="Set up CI", assignee="Carol")

    _, kept = edit_task(state, 1, TaskFields(title="Renamed", assignee="Carol"), shown)
    assert (kept.task.title, kept.task.assignee) == ("Renamed", "Carol")

    replaced_state, replaced = edit_task(state, 1, TaskFields(assignee="Ari"), shown)
    assert replaced.task.assignee == "Ari"
    _, none = edit_task(state, 1, TaskFields(assignee=""), shown)
    assert none.task.assignee is None

    with pytest.raises(AssigneeNotListed) as restored:
        edit_task(replaced_state, 1, TaskFields(assignee="Carol"), TaskFields(assignee="Ari"))
    assert restored.value.name == "Carol"


@pytest.mark.parametrize(
    ("field", "value", "refusal"),
    [
        *[("title", value, BlankTitle) for value in ("", " ", "\t\n", "　")],
        ("title", "t" * 201, TextTooLong),
        ("title", " " * 201, TextTooLong),
        *[("priority", value, InvalidPriority) for value in ("urgent", "", "High")],
        ("assignee", "Carol", AssigneeNotListed),
        ("assignee", "dana", AssigneeNotListed),
        *[
            ("due_date", value, InvalidDueDate)
            for value in ("2026-02-30", "2027-02-29", "20261011", "2026-10-11T00:00", " x")
        ],
    ],
)
def test_task_edit_rejects_each_invalid_changed_value(field, value, refusal):
    """CP-161 to CP-164: each changed value that breaks a rule is refused, alone."""
    before = _state_with(_saved_task())

    with pytest.raises(refusal):
        _edit(before, TaskFields(**{field: value}))

    assert before == _state_with(_saved_task())


def test_task_edit_accepts_a_title_of_200_code_points():
    """CP-162: the maximum is inclusive."""
    _, outcome = _edit(_state_with(_saved_task()), TaskFields(title="\U0001f600" * 200))

    assert len(outcome.task.title) == 200


@pytest.mark.parametrize(
    ("submitted", "refusal"),
    [
        (TaskFields("t" * 201, "urgent", "Carol", "x"), TextTooLong),
        (TaskFields(" ", "urgent", "Carol", "x"), BlankTitle),
        (TaskFields("Fine", "urgent", "Carol", "x"), InvalidPriority),
        (TaskFields("Fine", "low", "Carol", "x"), AssigneeNotListed),
        (TaskFields("Fine", "low", "Ari", "x"), InvalidDueDate),
    ],
)
def test_task_edit_uses_complete_refusal_precedence(submitted, refusal):
    """CP-160, CP-165: title length, blankness, priority, assignee, due date, in that order."""
    before = _state_with(_saved_task())

    with pytest.raises(refusal):
        _edit(before, submitted)

    assert before == _state_with(_saved_task())


def test_task_edit_missing_task_wins_over_no_change():
    """CP-167: the identity is found first, whatever the request holds."""
    state = _state_with(_saved_task())

    for task_id in (0, 99):
        with pytest.raises(TaskNotFound):
            edit_task(state, task_id, TaskFields(), TaskFields())
        with pytest.raises(TaskNotFound):
            edit_task(state, task_id, TaskFields(title=""), TaskFields(title="x"))


@pytest.mark.parametrize("status", ["todo", "in-progress", "done", "cancelled"])
def test_task_edit_preserves_every_protected_value(status):
    """CP-171: identity, project, status, labels, comments, created instant, position, counters."""
    comment = Comment(text="Looks fine", author="Dana", created_at=NOW)
    before_task = _saved_task(id=2, status=status, labels=["bug"], comments=[comment])
    neighbours = (_restored(id=1, title="First"), before_task, _restored(id=3, project_id=2))
    state = restore_state(
        [(1, "Alpha", ""), (2, "Beta", "x")], 3, ["Dana", "Ari"], tasks=neighbours, next_task_id=9
    )

    after, outcome = edit_task(state, 2, TaskFields(title="Renamed"), TaskFields(title="Set up CI"))

    assert after.tasks == (neighbours[0], replace(before_task, title="Renamed"), neighbours[2])
    assert outcome.task is after.tasks[1]
    assert (after.projects, after.assignees) == (state.projects, state.assignees)
    assert (after.next_task_id, after.next_project_id) == (9, 3)
    assert state.tasks == neighbours


def test_task_edit_values_are_immutable():
    """CP-172: the edit carriers and the outcome cannot be mutated."""
    fields = TaskFields(title="x")
    outcome = TaskEditOutcome(task=_saved_task(), changed=False)

    with pytest.raises(FrozenInstanceError):
        fields.title = "y"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        outcome.changed = True  # type: ignore[misc]


def test_task_edit_context_shows_saved_fields():
    """CP-145: the saved strings, the task and the project exactly as held."""
    task = _saved_task(title=" Set up CI ")
    state = _state_with(task)

    context = task_edit_context(state, 1)

    assert context is not None
    assert context.task == task
    assert context.project == state.projects[0] and context.project.name == "Alpha"
    assert context.fields == TaskFields(
        title=" Set up CI ", priority="high", assignee="Dana", due_date="2026-10-20"
    )
    bare = task_edit_context(_state_with(_saved_task(assignee=None, due_date=None)), 1)
    assert bare is not None
    assert (bare.fields.assignee, bare.fields.due_date) == ("", "")


def test_task_edit_context_orders_listed_choices():
    """CP-147: none first, then listed names in saved order, each once, exactly as saved."""
    names = ("<b>Dana</b>", " Ari ", "dana", "Ari")
    context = task_edit_context(_state_with(_saved_task(assignee=" Ari "), assignees=names), 1)

    assert context is not None
    assert context.assignee_choices == ("", *names)
    assert context.assignee_unlisted is False


def test_task_edit_context_appends_carried_unlisted_name():
    """CP-148: the carried name follows none and the listed names, once, with the flag on."""
    carried = task_edit_context(_state_with(_saved_task(assignee="Carol")), 1)
    listed = task_edit_context(_state_with(_saved_task(assignee="Ari")), 1)
    unassigned = task_edit_context(_state_with(_saved_task(assignee=None)), 1)

    assert carried is not None and listed is not None and unassigned is not None
    assert carried.assignee_choices == ("", "Dana", "Ari", "Carol")
    assert carried.assignee_unlisted is True
    assert listed.assignee_choices == ("", "Dana", "Ari") and listed.assignee_unlisted is False
    assert unassigned.assignee_choices == ("", "Dana", "Ari")
    assert unassigned.assignee_unlisted is False


def test_task_edit_context_handles_empty_people():
    """CP-148: with no names listed, none alone, or none then the carried name."""
    unassigned = task_edit_context(_state_with(_saved_task(assignee=None), assignees=()), 1)
    carried = task_edit_context(_state_with(_saved_task(assignee="Carol"), assignees=()), 1)

    assert unassigned is not None and carried is not None
    assert unassigned.assignee_choices == ("",)
    assert carried.assignee_choices == ("", "Carol") and carried.assignee_unlisted is True


@pytest.mark.parametrize("status", ["todo", "in-progress", "done", "cancelled"])
def test_task_edit_context_exists_in_every_status(status):
    """CP-144: the same context in all four statuses, with no workflow rule."""
    context = task_edit_context(_state_with(_saved_task(status=status)), 1)

    assert context is not None
    assert context.task.status is TaskStatus(status)
    assert context.fields.title == "Set up CI"


def test_task_edit_context_missing_task_returns_none():
    state = _state_with(_saved_task())

    assert task_edit_context(state, 99) is None
    assert task_edit_context(state, 0) is None


def test_task_edit_context_is_pure_and_immutable():
    """CP-150: the query changes nothing, and the context cannot be mutated."""
    state = _state_with(_saved_task())

    context = task_edit_context(state, 1)

    assert state == _state_with(_saved_task())
    assert isinstance(context, TaskEditContext)
    with pytest.raises(FrozenInstanceError):
        context.assignee_unlisted = True  # type: ignore[misc]
    assert isinstance(context.assignee_choices, tuple)


def _state_with_labelled_tasks() -> TrackerState:
    comment = Comment(text="first", author="Dana", created_at=NOW)
    labelled = _saved_task(labels=["bug", "ui"], comments=[comment])
    other = _restored(id=2, project_id=2, title="Other", labels=["bug"])
    return _state_with(labelled, other)


def test_label_actions_change_only_target_labels():
    """CP-187, CP-192, CP-199: only the target task's labels move; the outcome reports the
    change."""
    before = _state_with_labelled_tasks()
    target = find_task(before, 1)
    assert target is not None

    for act, expected in (
        (lambda state: add_task_label(state, 1, "ops"), ("bug", "ui", "ops")),
        (lambda state: remove_task_label(state, 1, "bug"), ("ui",)),
    ):
        after, outcome = act(before)

        assert isinstance(outcome, TaskLabelOutcome) and outcome.changed is True
        assert outcome.task == find_task(after, 1)
        assert outcome.task.labels == expected
        assert replace(outcome.task, labels=target.labels) == target
        assert find_task(after, 2) == find_task(before, 2)
        assert after.assignees == before.assignees and after.projects == before.projects
        assert (after.next_task_id, after.next_project_id) == (
            before.next_task_id,
            before.next_project_id,
        )


def test_duplicate_task_label_reports_no_change():
    """CP-189: an exact repeat leaves the state and the labels as they were."""
    before = _state_with_labelled_tasks()

    after, outcome = add_task_label(before, 1, "bug")

    assert after is before
    assert outcome.changed is False
    assert outcome.task == find_task(before, 1)
    assert outcome.task.labels == ("bug", "ui")
    case_distinct, distinct_outcome = add_task_label(before, 1, "Bug")
    assert distinct_outcome.changed is True
    assert find_task(case_distinct, 1).labels == ("bug", "ui", "Bug")  # type: ignore[union-attr]


def test_missing_task_precedes_label_validation():
    """CP-194: a missing task is the one refusal, even for a value the label rules would refuse."""
    state = _state_with_labelled_tasks()

    for label in ("ops", "", "x" * 201):
        with pytest.raises(TaskNotFound):
            add_task_label(state, 99, label)
    for label in ("bug", "absent", "", "x" * 201):
        with pytest.raises(TaskNotFound):
            remove_task_label(state, 99, label)


def test_label_refusals_name_their_conditions():
    """CP-190, CP-191, CP-193, CP-201: each refusal is its own type, raised after the task is
    found."""
    state = _state_with_labelled_tasks()

    with pytest.raises(EmptyLabel):
        add_task_label(state, 1, "")
    with pytest.raises(TextTooLong) as too_long:
        add_task_label(state, 1, "x" * 201)
    assert too_long.value.field is TextField.LABEL
    with pytest.raises(LabelNotCarried):
        remove_task_label(state, 1, "ops")
    with pytest.raises(LabelNotCarried):
        remove_task_label(state, 2, "ui")


def test_label_success_and_refusal_leave_input_immutable():
    """CP-199: the state a label action is given is untouched by a success and by each refusal."""
    state = _state_with_labelled_tasks()

    add_task_label(state, 1, "ops")
    remove_task_label(state, 1, "ui")
    add_task_label(state, 1, "bug")
    for refused in (
        lambda: add_task_label(state, 1, ""),
        lambda: add_task_label(state, 1, "x" * 201),
        lambda: remove_task_label(state, 1, "absent"),
        lambda: add_task_label(state, 99, "ops"),
    ):
        with pytest.raises(Refusal):
            refused()

    assert state == _state_with_labelled_tasks()
    assert find_task(state, 1).labels == ("bug", "ui")  # type: ignore[union-attr]


def test_restore_task_checks_saved_label_rules():
    """CP-197, CP-264: empty, over-long and repeated labels are refused through the unchanged
    signature, and so is a comment of empty text; empty, spaces-only, case-distinct and boundary
    label collections are readable."""
    with pytest.raises(EmptyLabel):
        _restored(labels=["bug", ""])
    with pytest.raises(TextTooLong) as too_long:
        _restored(labels=["x" * 201])
    assert too_long.value.field is TextField.LABEL
    with pytest.raises(RepeatedSavedLabel):
        _restored(labels=["bug", "ui", "bug"])

    boundary = "\U0001f600" + "x" * 199
    for readable in ([], ["   "], ["bug", "Bug", " bug"], [boundary, "x" * 200]):
        assert _restored(labels=readable).labels == tuple(readable)
    with pytest.raises(BlankComment):
        _restored(comments=[Comment(text="", author="", created_at=NOW)])
