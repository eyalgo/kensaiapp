"""The Summary feature entry point: the counts of one project, worked out as plain numbers.

Realizes SRS FR-38 (a project's summary: the total, each status and each priority with zero counts
included, the overdue count, the tasks with no due date and the open tasks of every assignee), FR-25
(the overdue rule, decided once for the list marking, the filter and this count), FR-35 (the overdue
filter this count is taken through) and NFR-9 (the trace from the requirement to this code).

Taking part: nothing here reads a clock or a file, so today arrives as an argument and the state as
a value. The rows come back in the order the page shows them and carry identifiers, never words.
The counts for the total, each status, each priority and overdue are taken through the project
filter in domain/filtering.py; open membership is TaskStatus.is_open in domain/tasks.py.

Checked by: tests/unit/test_summary.py (the rules), and tests/architecture/test_trace.py and
tests/architecture/test_shapes.py (the entry and the shape).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date

from domain.assignees import list_assignees
from domain.filtering import OVERDUE_ON, FilterInput, filter_project_tasks
from domain.priorities import Priority
from domain.projects import Project, find_project
from domain.state import TrackerState
from domain.tasks import TaskStatus


@dataclass(frozen=True)
class StatusCount:
    """How many of the project's tasks hold one status."""

    status: TaskStatus
    count: int


@dataclass(frozen=True)
class PriorityCount:
    """How many of the project's tasks hold one priority."""

    priority: Priority
    count: int


@dataclass(frozen=True)
class AssigneeCount:
    """How many of the project's open tasks one assignee carries.

    `assignee` is the name exactly as saved, or None for the bucket of open tasks with no assignee.
    None is the identity of that bucket; no label for it is held here, so a name spelled like the
    page's label stays a different row.
    """

    assignee: str | None
    count: int


@dataclass(frozen=True)
class ProjectSummary:
    """One project's counts, in the order the page shows them.

    The status rows follow the workflow's order and the priority rows run from low to critical,
    each with a row even at zero. The assignee rows are the listed names in list order, then each
    unlisted name an open task of the project carries, then the unassigned bucket.
    """

    project: Project
    total: int
    status_counts: tuple[StatusCount, ...]
    priority_counts: tuple[PriorityCount, ...]
    overdue: int
    no_due_date: int
    assignee_counts: tuple[AssigneeCount, ...]


def summarize_project(state: TrackerState, project_id: int, today: date) -> ProjectSummary | None:
    """The project's summary as of `today`, or None when no project holds this identity.

    A project with no tasks returns its zero result, which is not the same as None.
    """
    project = find_project(state, project_id)
    if project is None:
        return None
    everything = filter_project_tasks(state, project_id, FilterInput(), today)
    return ProjectSummary(
        project=project,
        total=everything.match_count,
        status_counts=tuple(
            StatusCount(status, _matching(state, project_id, today, status=(status.value,)))
            for status in TaskStatus
        ),
        priority_counts=tuple(
            PriorityCount(priority, _matching(state, project_id, today, priority=(priority.value,)))
            for priority in Priority
        ),
        overdue=_matching(state, project_id, today, overdue=(OVERDUE_ON,)),
        no_due_date=sum(1 for task in everything.tasks if task.due_date is None),
        assignee_counts=_assignee_counts(
            state, Counter(task.assignee for task in everything.tasks if task.status.is_open)
        ),
    )


def _matching(state: TrackerState, project_id: int, today: date, **choices: tuple[str, ...]) -> int:
    """How many of the project's tasks the public project filter returns for these choices."""
    return filter_project_tasks(state, project_id, FilterInput(**choices), today).match_count


def _assignee_counts(
    state: TrackerState, open_by_assignee: Counter[str | None]
) -> tuple[AssigneeCount, ...]:
    """The listed names, then the unlisted names found on open tasks, then the unassigned bucket.

    A name is compared exactly. Letter case orders the unlisted names only: the folded text first,
    the exact text breaking a tie so equal-looking names keep their separate rows in one order.
    """
    listed = list_assignees(state)
    unlisted = sorted(
        {name for name in open_by_assignee if name is not None and name not in listed},
        key=lambda name: (name.casefold(), name),
    )
    names: tuple[str | None, ...] = (*listed, *unlisted, None)
    return tuple(AssigneeCount(name, open_by_assignee[name]) for name in names)
