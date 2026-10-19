"""The tracker state as one immutable value (SDD § 3, What the system holds)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

from domain.assignees import check_assignee_names
from domain.operator_name import check_operator_name
from domain.projects import Project, check_project_values
from domain.refusals import IdentityReused, NameInUse, ProjectNotFound

if TYPE_CHECKING:
    from domain.tasks import Task


@dataclass(frozen=True)
class TrackerState:
    """Every project, the counter that issues the next project identity, the assignee list, every
    task, the counter that issues the next task identity and the operator name.

    The assignees are in the order they were added, each exactly as typed and each once. Task
    identities are unique across all projects and never reused. The operator name is one string
    exactly as typed, or None when none is set.
    """

    projects: tuple[Project, ...]
    next_project_id: int
    assignees: tuple[str, ...] = ()
    tasks: tuple[Task, ...] = ()
    next_task_id: int = 1
    operator_name: str | None = None


def empty_state() -> TrackerState:
    """The state of a tracker with no saved data: no projects, identities starting at 1."""
    return TrackerState(projects=(), next_project_id=1)


def restore_state(
    projects: Sequence[tuple[int, str, str]],
    next_project_id: int,
    assignees: Sequence[str] = (),
    *,
    tasks: Sequence[Task] = (),
    next_task_id: int = 1,
    operator_name: str | None = None,
) -> TrackerState:
    """Build the state from saved values, applying the rules every create and add applies (SD-5).

    Raises a refusal when any project breaks a value rule, when two projects share a name or an
    identity, when an identity is not below the counter, or when an assignee name is blank, too
    long or given twice, or when a task refers to no saved project, shares an identity with another,
    has an identity that is not positive or not below the task counter, or the counter is below 1,
    or when a present operator name is blank or too long. It never returns part of the data.
    """
    restored: list[Project] = []
    names_seen: set[str] = set()
    identities_seen: set[int] = set()
    for identity, name, description in projects:
        check_project_values(name, description)
        if name in names_seen:
            raise NameInUse()
        if identity in identities_seen or identity >= next_project_id:
            raise IdentityReused()
        names_seen.add(name)
        identities_seen.add(identity)
        restored.append(Project(id=identity, name=name, description=description))
    check_task_identities(tasks, next_task_id, identities_seen)
    return TrackerState(
        projects=tuple(restored),
        next_project_id=next_project_id,
        assignees=check_assignee_names(assignees),
        tasks=tuple(tasks),
        next_task_id=next_task_id,
        operator_name=None if operator_name is None else check_operator_name(operator_name),
    )


def check_task_identities(tasks: Sequence[Task], next_task_id: int, project_ids: set[int]) -> None:
    """Refuse a task counter below 1, a task of no saved project, and a task identity that is not
    positive, is shared, or is not below the counter."""
    if next_task_id < 1:
        raise IdentityReused()
    task_ids_seen: set[int] = set()
    for task in tasks:
        if task.project_id not in project_ids:
            raise ProjectNotFound()
        if task.id < 1 or task.id in task_ids_seen or task.id >= next_task_id:
            raise IdentityReused()
        task_ids_seen.add(task.id)
