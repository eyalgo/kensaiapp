"""The Status workflow feature entry point: the moves a task's status allows and the rule that
applies one.

Realizes SRS FR-18 (the moves each status allows, and the refusal of every other move, a move to the
status the task already has included) and FR-19 (the moves a task's row and page offer come from
this one rule).

Taking part: application/tracker.py applies the rule to the current state, saves the result, and
hands the allowed moves to the pages; web/routes.py turns a submission into a move and each refusal
into its reason, and web/pages.py shows the moves, the status and the line after a move.

Checked by: tests/unit/test_workflow.py (the rule and its sixteen pairs),
tests/integration/test_move_tracker.py (the move through the Tracker),
tests/integration/test_move_routes.py (the request and its landing),
tests/integration/test_move_pages.py (the controls and the line),
tests/e2e/test_moves.py (the keys and the landing in a browser), and
tests/architecture/test_trace.py and tests/architecture/test_shapes.py (the entry and the shape).
"""

from __future__ import annotations

from dataclasses import replace
from types import MappingProxyType
from typing import TYPE_CHECKING

from domain.refusals import InvalidTaskStatus, Refusal, TaskNotFound
from domain.tasks import Task, TaskStatus, find_task

if TYPE_CHECKING:
    from domain.state import TrackerState


class MoveNotAllowed(Refusal):
    """The status workflow does not allow this move from the task's status as the state holds it.

    A move to the status the task already has is one of these. It carries no message: the words are
    the content stage's, and `web` maps this type to its reason.
    """


# Each tuple is the workflow's own order, written out and never derived from the enum's member
# order, so reordering the enum cannot reorder the buttons.
_ALLOWED_MOVES = MappingProxyType(
    {
        TaskStatus.TODO: (TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED),
        TaskStatus.IN_PROGRESS: (TaskStatus.DONE, TaskStatus.CANCELLED, TaskStatus.TODO),
        TaskStatus.DONE: (),
        TaskStatus.CANCELLED: (),
    }
)


def allowed_moves(status: TaskStatus) -> tuple[TaskStatus, ...]:
    """The statuses a task in `status` may move to, in the workflow's order."""
    return _ALLOWED_MOVES[status]


def _parse_target(target: str) -> TaskStatus:
    try:
        return TaskStatus(target)
    except ValueError:
        raise InvalidTaskStatus() from None


def move_task(state: TrackerState, task_id: int, target: str) -> tuple[TrackerState, Task]:
    """Return the state with the task's status set to `target`, and the moved task, or refuse.

    The checks run against the state handed in, never against what a page showed, in this order:
    the task is found, `target` is exactly one of the four status words, and the workflow allows the
    move from the task's status as the state holds it. The new state differs from the one handed in
    only in that task's status, and the task keeps its place among the state's tasks.
    """
    current = find_task(state, task_id)
    if current is None:
        raise TaskNotFound()
    status = _parse_target(target)
    if status not in allowed_moves(current.status):
        raise MoveNotAllowed()
    moved = replace(current, status=status)
    moved_tasks = tuple(moved if task.id == task_id else task for task in state.tasks)
    return replace(state, tasks=moved_tasks), moved
