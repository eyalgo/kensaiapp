"""Unit tests of the status workflow in domain/workflow.py (layer 1), with no file and no clock.

Checks SRS FR-18 (the moves a status allows and the refusal of every other) and FR-19 (the moves a
task's page and its rows offer come from this one rule), and acceptance criterion AC-12 (one test
per refusal). Change spec rules CP-293 to CP-296, CP-309 and CP-316 are the ones each test names.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from datetime import UTC, datetime
from itertools import product
from types import MappingProxyType

import pytest

from domain import (
    InvalidTaskStatus,
    MoveNotAllowed,
    Refusal,
    TaskNotFound,
    TaskStatus,
    TrackerState,
    allowed_moves,
    move_task,
    restore_state,
    restore_task,
    workflow,
)

NOW = datetime(2026, 10, 19, 9, 30, tzinfo=UTC)
TODO = TaskStatus.TODO
IN_PROGRESS = TaskStatus.IN_PROGRESS
DONE = TaskStatus.DONE
CANCELLED = TaskStatus.CANCELLED

WORKFLOW = {
    TODO: (IN_PROGRESS, CANCELLED),
    IN_PROGRESS: (DONE, CANCELLED, TODO),
    DONE: (),
    CANCELLED: (),
}


def _task(task_id: int, status: TaskStatus, project_id: int = 1, title: str = "Plan"):
    return restore_task(
        id=task_id,
        project_id=project_id,
        title=f"{title} {task_id}",
        status=status.value,
        priority="medium",
        assignee=None,
        labels=["ui"],
        due_date="2026-12-01",
        created_at=NOW,
        comments=[],
    )


def _state_with(status: TaskStatus) -> TrackerState:
    """A state of three tasks across two projects; the middle one, identity 2, has `status`."""
    tasks = (_task(1, TODO), _task(2, status), _task(3, DONE, project_id=2))
    return restore_state(
        [(1, "Alpha", ""), (2, "Beta", "")],
        3,
        ["Dana"],
        tasks=tasks,
        next_task_id=4,
        operator_name="Ari",
    )


def _pair_id(pair: tuple[TaskStatus, TaskStatus]) -> str:
    start, target = pair
    outcome = "allowed" if target in WORKFLOW[start] else "refused"
    return f"{start.value}->{target.value}:{outcome}"


ALL_PAIRS = list(product(TaskStatus, TaskStatus))


def test_allowed_moves_for_each_status_give_exactly_the_workflow_tuple_in_order():
    """CP-293: the moves each status allows, in the workflow's order."""
    assert allowed_moves(TODO) == (IN_PROGRESS, CANCELLED)
    assert allowed_moves(IN_PROGRESS) == (DONE, CANCELLED, TODO)
    assert allowed_moves(DONE) == ()
    assert allowed_moves(CANCELLED) == ()


@pytest.mark.parametrize("pair", ALL_PAIRS, ids=_pair_id)
def test_every_one_of_sixteen_pairs_has_its_outcome(pair):
    """CP-293, CP-294, CP-295, CP-296: five moves are made, eleven are refused, state unchanged."""
    start, target = pair
    state = _state_with(start)
    if target in WORKFLOW[start]:
        new_state, moved = move_task(state, 2, target.value)
        assert moved.status is target
        assert new_state.tasks[1] == moved
        assert new_state == replace(
            state, tasks=(state.tasks[0], replace(state.tasks[1], status=target), state.tasks[2])
        )
    else:
        with pytest.raises(MoveNotAllowed):
            move_task(state, 2, target.value)
        assert state == _state_with(start)


@pytest.mark.parametrize("target", ["finished", "", "Done"])
def test_a_target_that_is_not_a_status_raises_invalid_task_status_and_changes_nothing(target):
    """CP-309: only the four status words exactly are statuses, the empty string included."""
    state = _state_with(IN_PROGRESS)
    with pytest.raises(InvalidTaskStatus):
        move_task(state, 2, target)
    assert state == _state_with(IN_PROGRESS)


@pytest.mark.parametrize("target", ["finished", "", "done"])
def test_an_unknown_task_raises_task_not_found_even_with_a_non_status_target(target):
    """CP-310 and the check order: the task is found first, whatever the target is."""
    with pytest.raises(TaskNotFound):
        move_task(_state_with(TODO), 999, target)


def test_move_not_allowed_is_a_refusal_and_carries_no_message():
    """CP-294, CP-316: a typed refusal that holds no wording; web maps it to its reason."""
    refusal = MoveNotAllowed()
    assert isinstance(refusal, Refusal)
    assert refusal.args == ()
    assert str(refusal) == ""
    assert MoveNotAllowed.__module__ == "domain.workflow"


def test_allowed_moves_returns_a_tuple_and_the_table_cannot_be_assigned_through():
    """CP-316: every value the module defines is immutable."""
    for status in TaskStatus:
        assert type(allowed_moves(status)) is tuple
    for name, value in vars(workflow).items():
        if name.startswith("__"):
            continue
        assert not isinstance(value, (dict, list, set)), name
        if isinstance(value, Mapping):
            assert isinstance(value, MappingProxyType), name
            with pytest.raises(TypeError):
                value[TODO] = ()  # type: ignore[index]


def test_moving_a_task_keeps_every_task_in_its_place():
    """CP-295: the moved task keeps its position, and nothing else in the state differs."""
    state = _state_with(IN_PROGRESS)
    new_state, moved = move_task(state, 2, "done")
    assert [task.id for task in new_state.tasks] == [1, 2, 3]
    assert new_state.tasks[0] is state.tasks[0]
    assert new_state.tasks[2] is state.tasks[2]
    assert moved == replace(state.tasks[1], status=DONE)
    assert replace(new_state, tasks=state.tasks) == state
