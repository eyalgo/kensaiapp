"""Unit tests of the project rules in domain (layer 1).

Checks SRS FR-10 (create a project), FR-11 (list projects), FR-12 (rename a project, leaving its
tasks the same tasks), FR-39 and FR-40 (refusals and maximum lengths), DR-1 (the project entity) and
AC-12 (each refusal gives its own reason). Change spec rules CP-12 to CP-16 and CP-20 are the ones
the creation tests name; CP-551 to CP-555 and CP-558 are the ones the rename tests name; CP-575,
CP-576, CP-581 and CP-582 are the ones the project deletion tests name (SRS FR-13).
"""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime

import pytest

from domain import (
    LONG_TEXT_MAX,
    SHORT_TEXT_MAX,
    BlankName,
    Comment,
    NameInUse,
    Project,
    ProjectDeletionOutcome,
    ProjectNotFound,
    ProjectRenameOutcome,
    Refusal,
    TextField,
    TextTooLong,
    add_assignee,
    add_task,
    add_task_comment,
    add_task_label,
    create_project,
    delete_project,
    empty_state,
    find_project,
    list_projects,
    rename_project,
    restore_state,
    restore_task,
    set_operator_name,
)
from errors import AppError


def _state_with(*names: str):
    state = empty_state()
    for name in names:
        state, _ = create_project(state, name, "")
    return state


def test_list_orders_names_ignoring_letter_case():
    state = _state_with("beta", "Alpha", "alpha")

    assert [project.name for project in list_projects(state)] == ["Alpha", "alpha", "beta"]


def test_list_orders_non_ascii_names_ignoring_letter_case():
    state = _state_with("émile", "Émile", "Zed", "Ägir")

    assert [project.name for project in list_projects(state)] == ["Zed", "Ägir", "Émile", "émile"]


def test_name_and_description_are_kept_exactly_as_given():
    _, project = create_project(empty_state(), "  Alpha  ", "line one\nline two")

    assert project.name == "  Alpha  "
    assert project.description == "line one\nline two"


@pytest.mark.parametrize(
    "blank",
    ["", "   ", "\t", "\n", " \t\n ", "  "],
    ids=["empty", "three-spaces", "tab", "line-break", "mixed", "two-no-break-spaces"],
)
def test_a_blank_name_is_refused(blank):
    with pytest.raises(BlankName):
        create_project(empty_state(), blank, "")


def test_a_name_in_use_is_refused_by_exact_text():
    state = _state_with("Alpha")

    with pytest.raises(NameInUse):
        create_project(state, "Alpha", "")
    create_project(state, "alpha", "")
    create_project(state, "Alpha ", "")


def test_length_limits_are_inclusive():
    _, project = create_project(empty_state(), "n" * 200, "d" * 4000)
    assert len(project.name) == 200 and len(project.description) == 4000

    with pytest.raises(TextTooLong) as name_error:
        create_project(empty_state(), "n" * 201, "")
    assert name_error.value.field is TextField.NAME
    assert name_error.value.maximum == 200

    with pytest.raises(TextTooLong) as description_error:
        create_project(empty_state(), "Alpha", "d" * 4001)
    assert description_error.value.field is TextField.DESCRIPTION
    assert description_error.value.maximum == 4000


def test_the_maximums_are_stated_in_domain():
    assert SHORT_TEXT_MAX == 200
    assert LONG_TEXT_MAX == 4000


def test_a_character_outside_the_basic_plane_counts_as_one():
    emoji = "\U0001f600"
    create_project(empty_state(), emoji * 200, "")
    with pytest.raises(TextTooLong):
        create_project(empty_state(), emoji * 201, "")
    create_project(empty_state(), "Alpha", emoji * 4000)


def test_a_line_break_counts_as_one_character():
    create_project(empty_state(), "Alpha", "\n" * 4000)
    with pytest.raises(TextTooLong):
        create_project(empty_state(), "Alpha", "\n" * 4001)


def test_over_long_wins_over_blank_and_in_use():
    state = _state_with("Alpha")

    with pytest.raises(TextTooLong) as over_long_name_and_blank_name:
        create_project(state, " " * 201, "")
    assert over_long_name_and_blank_name.value.field is TextField.NAME

    with pytest.raises(TextTooLong) as blank_name_and_long_description:
        create_project(state, "   ", "d" * 4001)
    assert blank_name_and_long_description.value.field is TextField.DESCRIPTION

    with pytest.raises(TextTooLong) as in_use_and_long_description:
        create_project(state, "Alpha", "d" * 4001)
    assert in_use_and_long_description.value.field is TextField.DESCRIPTION

    with pytest.raises(TextTooLong) as both_long:
        create_project(state, "n" * 201, "d" * 4001)
    assert both_long.value.field is TextField.NAME


def test_identities_rise_from_one_and_the_counter_moves_on():
    state, first = create_project(empty_state(), "Alpha", "")
    assert first.id == 1
    assert state.next_project_id == 2

    state, second = create_project(state, "Beta", "")
    assert second.id == 2
    assert state.next_project_id == 3


def test_a_refused_create_returns_no_new_state():
    state = _state_with("Alpha")
    before = (state.projects, state.next_project_id)

    for name, description in [("", ""), ("Alpha", ""), ("n" * 201, "")]:
        with pytest.raises(Refusal):
            create_project(state, name, description)

    assert (state.projects, state.next_project_id) == before


def test_find_project_returns_none_for_an_unknown_identity():
    state, project = create_project(empty_state(), "Alpha", "")

    assert find_project(state, project.id) == project
    assert find_project(state, 99) is None


def test_the_predecessors_project_name_rules_come_over():
    # tracker16-X's project-name tests (SDD § 11 R-5), re-expressed for these rules.
    project = Project(id=1, name="alpha", description="")
    with pytest.raises(dataclasses.FrozenInstanceError):
        project.name = "beta"  # type: ignore[misc]
    assert (project.id, project.name, project.description) == (1, "alpha", "")

    with pytest.raises(BlankName):
        create_project(empty_state(), "", "")
    with pytest.raises(BlankName):
        create_project(empty_state(), "   ", "")
    _, kept = create_project(empty_state(), "  alpha  ", "")
    assert kept.name == "  alpha  "


def test_every_refusal_is_an_app_error_and_a_refusal():
    for refusal in (BlankName, NameInUse, TextTooLong):
        assert issubclass(refusal, Refusal)
        assert issubclass(refusal, AppError)


WRITTEN_AT = datetime(2026, 10, 28, 9, 30, tzinfo=UTC)


def _state_with_work():
    """Alpha (with a description and two tasks, one commented and labelled), Gamma and delta."""
    state, _ = create_project(empty_state(), "Alpha", "Alpha's description")
    state, _ = create_project(state, "Gamma", "")
    state, _ = create_project(state, "delta", "Another description")
    state, _ = set_operator_name(state, "Dana")
    state = add_assignee(state, "Dana")
    state, _ = add_task(state, 1, "First", "high", "Dana", "2026-11-01", WRITTEN_AT)
    state, _ = add_task(state, 1, "Second", "", "", "", WRITTEN_AT)
    state, _ = add_task(state, 2, "Elsewhere", "", "", "", WRITTEN_AT)
    state, _ = add_task_label(state, 1, "ui")
    state, _ = add_task_comment(state, 1, "Looks fine", WRITTEN_AT)
    return state


def test_rename_changes_only_the_selected_project_name():
    state = _state_with_work()
    before = dataclasses.replace(state)

    new_state, _ = rename_project(state, 1, "Zed")

    expected = dataclasses.replace(
        state,
        projects=(
            Project(id=1, name="Zed", description="Alpha's description"),
            Project(id=2, name="Gamma", description=""),
            Project(id=3, name="delta", description="Another description"),
        ),
    )
    assert new_state == expected
    assert new_state.tasks is state.tasks
    assert new_state.next_task_id == state.next_task_id
    assert new_state.next_project_id == state.next_project_id
    assert new_state.operator_name == "Dana"
    assert new_state.assignees == ("Dana",)
    assert state == before


def test_rename_reports_the_current_and_previous_name():
    state = _state_with_work()

    _, outcome = rename_project(state, 1, "Zed")

    assert outcome == ProjectRenameOutcome(
        project=Project(id=1, name="Zed", description="Alpha's description"),
        previous_name="Alpha",
        changed=True,
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        outcome.changed = False  # type: ignore[misc]


def test_own_name_is_accepted_without_a_change():
    state = _state_with_work()

    new_state, outcome = rename_project(state, 1, "Alpha")

    assert new_state is state
    assert outcome == ProjectRenameOutcome(
        project=find_project(state, 1), previous_name="Alpha", changed=False
    )


def test_rename_keeps_case_spaces_and_code_points():
    state = _state_with_work()
    long_name = "\U0001f600" * 199 + "é"

    case_only, case_outcome = rename_project(state, 1, "alpha")
    spaced, spaced_outcome = rename_project(state, 1, " Alpha ")
    longest, longest_outcome = rename_project(state, 1, long_name)
    unchanged_by_trailing_space, trailing_outcome = rename_project(state, 1, "Alpha ")

    assert case_outcome.changed and find_project(case_only, 1).name == "alpha"
    assert spaced_outcome.changed and find_project(spaced, 1).name == " Alpha "
    assert longest_outcome.changed and find_project(longest, 1).name == long_name
    assert len(long_name) == SHORT_TEXT_MAX
    assert trailing_outcome.changed
    assert find_project(unchanged_by_trailing_space, 1).name == "Alpha "
    assert rename_project(state, 1, "a\nb")[1].project.name == "a\nb"


@pytest.mark.parametrize(
    "blank",
    ["", "   ", "\t", "\n", " \t\n ", "\u00a0\u00a0", "\u3000"],
    ids=["empty", "spaces", "tab", "line-break", "mixed", "no-break-spaces", "ideographic-space"],
)
def test_rename_refuses_blank_names_as_creation_does(blank):
    state = _state_with_work()
    before = dataclasses.replace(state)

    with pytest.raises(BlankName):
        rename_project(state, 1, blank)
    with pytest.raises(BlankName):
        create_project(state, blank, "")

    assert state == before


def test_rename_refuses_only_another_projects_exact_name():
    state = _state_with_work()
    before = dataclasses.replace(state)

    with pytest.raises(NameInUse):
        rename_project(state, 1, "Gamma")
    for different in ("gamma", "Gamma ", " Gamma"):
        _, outcome = rename_project(state, 1, different)
        assert outcome.changed

    assert state == before


def test_rename_refuses_overlong_before_blank():
    state = _state_with_work()
    before = dataclasses.replace(state)

    for name in ("n" * 201, " " * 201):
        with pytest.raises(TextTooLong) as refused:
            rename_project(state, 1, name)
        assert refused.value.field is TextField.NAME
        assert refused.value.maximum == SHORT_TEXT_MAX

    assert state == before


def test_missing_rename_target_precedes_name_validation():
    state = _state_with_work()
    before = dataclasses.replace(state)

    for name in ("Zed", "", "   ", "Gamma", "n" * 201):
        with pytest.raises(ProjectNotFound):
            rename_project(state, 99, name)

    assert state == before


def test_a_renamed_project_is_listed_by_the_explicit_order_not_its_position():
    state = _state_with_work()

    renamed, _ = rename_project(state, 1, "Zed")
    assert [project.name for project in renamed.projects] == ["Zed", "Gamma", "delta"]
    assert [project.name for project in list_projects(renamed)] == ["delta", "Gamma", "Zed"]

    tied, _ = rename_project(state, 1, "gamma")
    assert [project.name for project in list_projects(tied)] == ["delta", "Gamma", "gamma"]


def test_creation_still_refuses_the_description_before_a_blank_name():
    state = _state_with_work()

    with pytest.raises(TextTooLong) as refused:
        create_project(state, "   ", "d" * 4001)

    assert refused.value.field is TextField.DESCRIPTION


DELETION_WRITTEN_AT = datetime(2026, 10, 28, 8, 0, tzinfo=UTC)


def _saved_task(**changes):
    values = {
        "id": 1,
        "project_id": 1,
        "title": "Plan",
        "status": "todo",
        "priority": "medium",
        "assignee": None,
        "labels": (),
        "due_date": None,
        "created_at": DELETION_WRITTEN_AT,
        "comments": (),
    }
    values.update(changes)
    return restore_task(**values)


def _comments(count: int) -> list[Comment]:
    return [
        Comment(text=f"Note {number}", author="Dana", created_at=DELETION_WRITTEN_AT)
        for number in range(count)
    ]


def _state_for_project_deletion():
    """Project 2 holds a task in each status, with comments, interleaved among project 1 and 3."""
    tasks = (
        _saved_task(id=9, project_id=1, title="Survivor nine", comments=_comments(1)),
        _saved_task(id=4, project_id=2, title="Todo", status="todo", comments=_comments(2)),
        _saved_task(id=6, project_id=3, title="Survivor six"),
        _saved_task(id=2, project_id=2, title="Running", status="in-progress"),
        _saved_task(id=8, project_id=1, title="Survivor eight", labels=["bug"]),
        _saved_task(id=5, project_id=2, title="Finished", status="done", comments=_comments(3)),
        _saved_task(id=3, project_id=2, title="Dropped", status="cancelled"),
    )
    return restore_state(
        [(1, "Alpha", "first"), (2, "Beta", "second"), (3, "Gamma", "")],
        4,
        ["Dana", "Ari"],
        tasks=tasks,
        next_task_id=10,
        operator_name="Dana",
    )


def test_delete_project_removes_only_its_tasks_and_comments():
    """CP-575: the project, all four statuses of its tasks and their comments go; survivors stay."""
    state = _state_for_project_deletion()

    after, _ = delete_project(state, 2)

    assert [project.id for project in after.projects] == [1, 3]
    assert after.tasks == (state.tasks[0], state.tasks[2], state.tasks[4])
    assert [task.id for task in after.tasks] == [9, 6, 8]
    assert [len(task.comments) for task in after.tasks] == [1, 0, 0]
    assert all(task.project_id != 2 for task in after.tasks)


def test_delete_empty_project_preserves_every_other_value():
    """CP-575, CP-576: no tasks still removes the project and reports zero; the rest is untouched."""
    held = restore_state(
        [(1, "Alpha", ""), (2, "Beta", "")],
        3,
        ["Dana"],
        tasks=(_saved_task(id=1, project_id=1, comments=_comments(2)),),
        next_task_id=2,
        operator_name="Dana",
    )

    after, outcome = delete_project(held, 2)

    assert outcome == ProjectDeletionOutcome(project=Project(2, "Beta", ""), task_count=0)
    assert after.projects == (Project(1, "Alpha", ""),)
    assert after.tasks == held.tasks
    assert (after.assignees, after.operator_name) == (("Dana",), "Dana")
    assert (after.next_project_id, after.next_task_id) == (3, 2)


@pytest.mark.parametrize(
    ("project_id", "task_count"), [(3, 1), (1, 2), (2, 4)], ids=["one", "two", "many"]
)
def test_delete_project_reports_the_removed_project_and_actual_task_count(project_id, task_count):
    """CP-576: the count is every task in every status, never comments, from this call's state."""
    state = _state_for_project_deletion()

    _, outcome = delete_project(state, project_id)

    assert outcome.project == next(
        project for project in state.projects if project.id == project_id
    )
    assert outcome.task_count == task_count


def test_delete_project_returns_the_name_supplied_in_this_calls_state():
    """CP-576: the name and count come from the state handed in, not from an earlier read."""
    state = _state_for_project_deletion()
    renamed, _ = rename_project(state, 2, "Beta, renamed")

    _, outcome = delete_project(renamed, 2)

    assert outcome.project.name == "Beta, renamed"
    assert outcome.task_count == 4


def test_delete_project_leaves_the_input_unchanged():
    """CP-575, CP-582: the supplied state keeps every value; result and outcome are immutable."""
    state = _state_for_project_deletion()
    snapshot = _state_for_project_deletion()

    after, outcome = delete_project(state, 2)

    assert state == snapshot
    assert after is not state
    with pytest.raises(dataclasses.FrozenInstanceError):
        after.next_task_id = 1  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        outcome.task_count = 0  # type: ignore[misc]


@pytest.mark.parametrize("repeated", [False, True], ids=["never-held", "already-removed"])
def test_delete_missing_project_is_refused(repeated):
    """CP-582: an absent identity raises ProjectNotFound and produces no changed state."""
    state = _state_for_project_deletion()
    snapshot = _state_for_project_deletion()
    target = 99
    if repeated:
        state, _ = delete_project(state, 2)
        snapshot = state
        target = 2

    with pytest.raises(ProjectNotFound):
        delete_project(state, target)

    assert state == snapshot


@pytest.mark.parametrize("project_id", [3, 2, 1])
def test_delete_project_never_rewinds_identity_counters(project_id):
    """CP-581: removing the highest or any identity lowers neither counter."""
    state = _state_for_project_deletion()

    after, _ = delete_project(state, project_id)

    assert (after.next_project_id, after.next_task_id) == (4, 10)
    created, project = create_project(after, "Delta", "")
    created, task = add_task(created, project.id, "Fresh", "", "", "", DELETION_WRITTEN_AT)
    assert project.id == 4
    assert task.id == 10
