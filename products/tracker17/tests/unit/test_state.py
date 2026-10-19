"""Unit tests of restore_state in domain, the start-time build of the tracker state (layer 1).

Checks SRS DR-2 (the task identity and its counter), DR-6 (saved data is checked by the same rules
at start), DR-1 (the project entity), DR-4 (the assignee list), DR-5 (the one operator name), FR-39
and FR-40 (refusals and maximum lengths), AC-7 (unreadable saved data) and AC-12 (each refusal).
Change spec rules CP-8, CP-15, CP-100, CP-101, CP-105, CP-228 and CP-231 and SDD § 4 SD-5 are the
ones each test names.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from domain import (
    AssigneeNameInUse,
    BlankName,
    IdentityReused,
    NameInUse,
    ProjectNotFound,
    TextField,
    TextTooLong,
    TrackerState,
    create_project,
    empty_state,
    list_assignees,
    restore_state,
    restore_task,
)


def test_restore_refuses_a_blank_name():
    with pytest.raises(BlankName):
        restore_state([(1, "   ", "")], 2)


def test_restore_refuses_two_projects_with_one_exact_name():
    with pytest.raises(NameInUse):
        restore_state([(1, "Alpha", ""), (2, "Alpha", "")], 3)


def test_restore_accepts_names_that_differ_only_by_case():
    state = restore_state([(1, "Alpha", ""), (2, "alpha", "")], 3)

    assert [project.name for project in state.projects] == ["Alpha", "alpha"]


def test_restore_refuses_over_long_values():
    with pytest.raises(TextTooLong) as name_error:
        restore_state([(1, "n" * 201, "")], 2)
    assert name_error.value.field is TextField.NAME

    with pytest.raises(TextTooLong) as description_error:
        restore_state([(1, "Alpha", "d" * 4001)], 2)
    assert description_error.value.field is TextField.DESCRIPTION


def test_restore_refuses_a_shared_identity():
    with pytest.raises(IdentityReused):
        restore_state([(1, "Alpha", ""), (1, "Beta", "")], 2)


def test_restore_refuses_an_identity_not_below_the_counter():
    with pytest.raises(IdentityReused):
        restore_state([(2, "Alpha", "")], 2)
    with pytest.raises(IdentityReused):
        restore_state([(5, "Alpha", "")], 2)


def test_a_valid_set_round_trips():
    state = empty_state()
    for name, description in [("beta", "b"), ("Alpha", "line\nbreak"), ("alpha", "")]:
        state, _ = create_project(state, name, description)

    restored = restore_state(
        [(project.id, project.name, project.description) for project in state.projects],
        state.next_project_id,
    )

    assert restored == state


def test_restore_of_no_projects_is_the_empty_state():
    assert restore_state([], 1) == empty_state()


def test_old_state_callers_default_to_no_assignees():
    """CP-100: the constructor's two arguments and restore's two arguments still build a state."""
    assert TrackerState(projects=(), next_project_id=1).assignees == ()
    assert empty_state().assignees == ()
    assert restore_state([(1, "Alpha", "")], 2).assignees == ()


def test_restore_retains_order_and_refuses_invalid_assignees_whole():
    """CP-101: every domain value break is refused, and none leaves part of the data."""
    exact = ["Dana", "Ari", " Ari", "ari", "<b>A&B</b>", "n" * 200]
    state = restore_state([(1, "Alpha", "")], 2, exact)
    assert list_assignees(state) == tuple(exact)
    assert state.projects[0].name == "Alpha"

    with pytest.raises(BlankName):
        restore_state([], 1, ["Dana", "  "])
    with pytest.raises(BlankName):
        restore_state([], 1, [""])
    with pytest.raises(AssigneeNameInUse):
        restore_state([], 1, ["Dana", "Ari", "Dana"])
    with pytest.raises(TextTooLong) as too_long:
        restore_state([], 1, ["Dana", "n" * 201])
    assert too_long.value.field is TextField.NAME
    with pytest.raises(TextTooLong):
        restore_state([], 1, [" " * 201])

    with pytest.raises(NameInUse):
        restore_state([(1, "Alpha", ""), (2, "Alpha", "")], 3, ["Dana"])
    with pytest.raises(IdentityReused):
        restore_state([(1, "Alpha", ""), (1, "Beta", "")], 2, ["Dana"])
    with pytest.raises(BlankName):
        restore_state([(1, " ", "")], 2, ["Dana"])


def test_creating_a_project_preserves_assignees():
    """CP-100, CP-105: the real project rule keeps the list, and the list is not a project value."""
    state = restore_state([(1, "Alpha", "")], 2, ["Dana", "Ari"])

    created, project = create_project(state, "Beta", "")

    assert list_assignees(created) == ("Dana", "Ari")
    assert [item.name for item in created.projects] == ["Alpha", "Beta"]
    assert created.next_project_id == 3
    assert project.id == 2


def _task(identity: int, project_id: int = 1):
    return restore_task(
        id=identity,
        project_id=project_id,
        title="Plan",
        status="todo",
        priority="medium",
        assignee=None,
        labels=(),
        due_date=None,
        created_at=datetime(2026, 10, 11, 9, 30, tzinfo=UTC),
        comments=(),
    )


def test_old_callers_default_to_no_tasks_and_a_counter_of_one():
    """CP-135, CP-136: the first three arguments still build a state, and tasks default to none."""
    assert TrackerState(projects=(), next_project_id=1).tasks == ()
    assert TrackerState(projects=(), next_project_id=1).next_task_id == 1
    assert empty_state().tasks == () and empty_state().next_task_id == 1
    legacy = restore_state([(1, "Alpha", "")], 2, ["Dana"])
    assert legacy.tasks == () and legacy.next_task_id == 1


def test_state_restoration_checks_task_identity_and_project_invariants():
    """CP-137: refuse the whole state when a task breaks an identity or project rule."""
    projects = [(1, "Alpha", "")]
    good = _task(3)
    assert restore_state(projects, 2, tasks=[good], next_task_id=4).tasks == (good,)

    with pytest.raises(IdentityReused):
        restore_state(projects, 2, tasks=[_task(3), _task(3)], next_task_id=9)
    with pytest.raises(IdentityReused):
        restore_state(projects, 2, tasks=[_task(4)], next_task_id=4)
    with pytest.raises(IdentityReused):
        restore_state(projects, 2, tasks=[_task(5)], next_task_id=4)
    with pytest.raises(IdentityReused):
        restore_state(projects, 2, tasks=[_task(0)], next_task_id=4)
    with pytest.raises(IdentityReused):
        restore_state(projects, 2, tasks=[_task(-1)], next_task_id=4)
    with pytest.raises(IdentityReused):
        restore_state(projects, 2, next_task_id=0)
    with pytest.raises(ProjectNotFound):
        restore_state(projects, 2, tasks=[_task(1, project_id=7)], next_task_id=2)


def test_empty_and_legacy_state_construction_have_no_name():
    """CP-228: every way to build a state without a name leaves it unset, positional calls too."""
    assert empty_state().operator_name is None
    assert TrackerState(projects=(), next_project_id=1).operator_name is None
    assert TrackerState((), 1, ("Dana",), (), 4).operator_name is None
    assert restore_state([(1, "Alpha", "")], 2).operator_name is None
    assert restore_state([(1, "Alpha", "")], 2, ["Dana"]).operator_name is None
    assert restore_state([(1, "Alpha", "")], 2, operator_name=None).operator_name is None
    positional = restore_state([(1, "Alpha", "")], 2, ["Dana"], tasks=[_task(1)], next_task_id=2)
    assert positional.assignees == ("Dana",) and positional.operator_name is None


def test_restore_operator_name_keeps_exact_valid_values():
    """CP-217, CP-228: an ordinary, a space-surrounded and a 200-code-point name restore as given,
    and nothing else in the state moves."""
    boundary = "a" * 199 + "\U0001f600"
    for name in ("Sam", " Sam ", "sAM", boundary):
        state = restore_state([(1, "Alpha", "")], 2, ["Dana"], operator_name=name)
        assert state.operator_name == name
        assert state.projects == restore_state([(1, "Alpha", "")], 2, ["Dana"]).projects
        assert state.assignees == ("Dana",)
        assert state.next_project_id == 2


def test_restore_operator_name_refuses_whole_invalid_state():
    """CP-228, CP-231: a blank or over-long name raises the refusal setting raises, and no state
    comes back even though every other value is valid."""
    for blank in ("", "   ", "\t", "\u00a0", "\u3000"):
        with pytest.raises(BlankName):
            restore_state([(1, "Alpha", "")], 2, ["Dana"], operator_name=blank)
    for over_long in ("a" * 201, " " * 201, "a" * 200 + "\U0001f600"):
        with pytest.raises(TextTooLong) as refused:
            restore_state([(1, "Alpha", "")], 2, ["Dana"], operator_name=over_long)
        assert refused.value.field is TextField.NAME
