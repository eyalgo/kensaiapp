"""Unit tests of the project Summary rules in domain/summary.py (layer 1), with no file and no clock.

Checks SRS FR-38 (the summary of one project: the total, each status, each priority, the overdue
count, the tasks with no due date and the open tasks per assignee, zero counts included), FR-25 (the
overdue rule the count shares with the list and the filter), FR-35 (the overdue filter), NFR-9 (the
trace from the requirement to this code) and AC-13, AC-14 (the overdue boundary and the summary
test). Change spec rules CP-496 to CP-500, CP-505 to CP-507 and CP-508 are the ones each test
names. The design rows T01 to T04 are the coverage references.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError, fields
from datetime import UTC, date, datetime

import pytest

from domain import (
    Priority,
    Project,
    Task,
    TaskStatus,
    TrackerState,
    summarize_project,
)
from domain.summary import AssigneeCount, PriorityCount, ProjectSummary, StatusCount

TODAY = date(2026, 10, 28)
YESTERDAY = date(2026, 10, 27)
CREATED = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)
ALPHA = 1
BETA = 2
GAMMA = 3
STATUS_ORDER = [
    TaskStatus.TODO,
    TaskStatus.IN_PROGRESS,
    TaskStatus.DONE,
    TaskStatus.CANCELLED,
]
PRIORITY_ORDER = [Priority.LOW, Priority.MEDIUM, Priority.HIGH, Priority.CRITICAL]


def make_task(
    task_id: int,
    *,
    project_id: int = ALPHA,
    status: TaskStatus = TaskStatus.TODO,
    priority: Priority = Priority.MEDIUM,
    assignee: str | None = None,
    due: date | None = None,
) -> Task:
    return Task(
        id=task_id,
        project_id=project_id,
        title=f"task {task_id}",
        status=status,
        priority=priority,
        assignee=assignee,
        labels=(),
        due_date=due,
        created_at=CREATED,
        comments=(),
    )


def make_state(*tasks: Task, assignees: tuple[str, ...] = ("ari", "bo")) -> TrackerState:
    return TrackerState(
        projects=(Project(ALPHA, "Alpha", ""), Project(BETA, "Beta", ""), Project(GAMMA, "Gamma", "")),
        next_project_id=4,
        assignees=assignees,
        tasks=tasks,
        next_task_id=max((task.id for task in tasks), default=0) + 1,
    )


def summary_of(
    state: TrackerState, project_id: int = ALPHA, today: date = TODAY
) -> ProjectSummary:
    summary = summarize_project(state, project_id, today)
    assert summary is not None
    return summary


def status_rows(summary: ProjectSummary) -> list[tuple[TaskStatus, int]]:
    return [(row.status, row.count) for row in summary.status_counts]


def priority_rows(summary: ProjectSummary) -> list[tuple[Priority, int]]:
    return [(row.priority, row.count) for row in summary.priority_counts]


def assignee_rows(summary: ProjectSummary) -> list[tuple[str | None, int]]:
    return [(row.assignee, row.count) for row in summary.assignee_counts]


def mixed_state() -> TrackerState:
    """The change spec's Example 9: five Alpha tasks across every row, and one Beta task."""
    return make_state(
        make_task(1, status=TaskStatus.TODO, priority=Priority.LOW, due=YESTERDAY),
        make_task(2, status=TaskStatus.IN_PROGRESS, priority=Priority.MEDIUM, assignee="ari"),
        make_task(
            3,
            status=TaskStatus.DONE,
            priority=Priority.HIGH,
            assignee="ari",
            due=date(2026, 10, 1),
        ),
        make_task(4, status=TaskStatus.CANCELLED, priority=Priority.CRITICAL, assignee="dan"),
        make_task(5, status=TaskStatus.TODO, priority=Priority.CRITICAL, assignee="eve", due=TODAY),
        make_task(6, project_id=BETA, status=TaskStatus.TODO, assignee="bo"),
    )


def test_summary_counts_only_the_requested_project() -> None:
    """CP-496 to CP-500, CP-507, T01: every row, in order, and both total identities."""
    summary = summary_of(mixed_state())

    assert summary.project == Project(ALPHA, "Alpha", "")
    assert summary.total == 5
    assert status_rows(summary) == [
        (TaskStatus.TODO, 2),
        (TaskStatus.IN_PROGRESS, 1),
        (TaskStatus.DONE, 1),
        (TaskStatus.CANCELLED, 1),
    ]
    assert priority_rows(summary) == [
        (Priority.LOW, 1),
        (Priority.MEDIUM, 1),
        (Priority.HIGH, 1),
        (Priority.CRITICAL, 2),
    ]
    assert summary.overdue == 1
    assert summary.no_due_date == 2
    assert assignee_rows(summary) == [("ari", 1), ("bo", 0), ("eve", 1), (None, 1)]
    assert summary.total == sum(row.count for row in summary.status_counts)
    assert summary.total == sum(row.count for row in summary.priority_counts)
    other = summary_of(mixed_state(), BETA)
    assert other.total == 1
    assert assignee_rows(other) == [("ari", 0), ("bo", 1), (None, 0)]


def test_summary_preserves_required_zero_rows() -> None:
    """CP-496, CP-499, CP-502, T02: an empty project keeps every row, the unassigned bucket last."""
    listed = summary_of(make_state(), GAMMA)
    assert listed.total == 0
    assert status_rows(listed) == [(status, 0) for status in STATUS_ORDER]
    assert priority_rows(listed) == [(priority, 0) for priority in PRIORITY_ORDER]
    assert (listed.overdue, listed.no_due_date) == (0, 0)
    assert assignee_rows(listed) == [("ari", 0), ("bo", 0), (None, 0)]

    unnamed = summary_of(make_state(assignees=()), GAMMA)
    assert assignee_rows(unnamed) == [(None, 0)]

    populated = summary_of(
        make_state(make_task(1, status=TaskStatus.DONE, priority=Priority.HIGH)), ALPHA
    )
    assert status_rows(populated) == [
        (TaskStatus.TODO, 0),
        (TaskStatus.IN_PROGRESS, 0),
        (TaskStatus.DONE, 1),
        (TaskStatus.CANCELLED, 0),
    ]
    assert priority_rows(populated) == [
        (Priority.LOW, 0),
        (Priority.MEDIUM, 0),
        (Priority.HIGH, 1),
        (Priority.CRITICAL, 0),
    ]
    assert assignee_rows(populated) == [("ari", 0), ("bo", 0), (None, 0)]


def test_missing_project_is_distinct_from_empty_project() -> None:
    """CP-495, T02: an identity nothing holds is None, and an empty project is a zero result."""
    state = make_state()
    assert summarize_project(state, 99, TODAY) is None
    assert summarize_project(state, 0, TODAY) is None
    assert summarize_project(state, GAMMA, TODAY) is not None


def test_summary_assignees_keep_list_order_then_exact_casefold_order() -> None:
    """CP-499, CP-500, T03: the list's order, then unlisted names ignoring case, exact text on a tie."""
    tasks = (
        make_task(1, assignee="zed"),
        make_task(2, assignee="amy"),
        make_task(3, assignee="Amy"),
        make_task(4, assignee="bo"),
        make_task(5, assignee="zed"),
        make_task(6, assignee="zed "),
        make_task(7, assignee=None),
        make_task(8, assignee="ari"),
    )
    summary = summary_of(make_state(*tasks, assignees=("bo", "ari", "cy")))

    assert assignee_rows(summary) == [
        ("bo", 1),
        ("ari", 1),
        ("cy", 0),
        ("Amy", 1),
        ("amy", 1),
        ("zed", 2),
        ("zed ", 1),
        (None, 1),
    ]


def test_summary_casefold_ties_keep_exact_names_separate() -> None:
    """CP-500, T03 (TL addition): different names with one case-folded form stay two rows."""
    assert "Straße".casefold() == "STRASSE".casefold()
    tasks = (
        make_task(1, assignee="Straße"),
        make_task(2, assignee="STRASSE"),
        make_task(3, assignee="Straße"),
    )
    summary = summary_of(make_state(*tasks, assignees=()))

    assert assignee_rows(summary) == [("STRASSE", 1), ("Straße", 2), (None, 0)]


def test_summary_omits_removed_names_with_only_closed_or_other_project_tasks() -> None:
    """CP-499, T03: a removed name needs an open task of this project to earn a row."""
    tasks = (
        make_task(1, status=TaskStatus.DONE, assignee="dan"),
        make_task(2, status=TaskStatus.CANCELLED, assignee="dan"),
        make_task(3, project_id=BETA, status=TaskStatus.TODO, assignee="gus"),
        make_task(4, status=TaskStatus.IN_PROGRESS, assignee="eve"),
    )
    summary = summary_of(make_state(*tasks))

    assert assignee_rows(summary) == [("ari", 0), ("bo", 0), ("eve", 1), (None, 0)]


def test_summary_does_not_merge_a_real_unassigned_name_with_none() -> None:
    """CP-500, Locked Answer b-5, T03: a listed name spelled (unassigned) is its own row."""
    tasks = (
        make_task(1, assignee="(unassigned)"),
        make_task(2, assignee="(unassigned)"),
        make_task(3, assignee=None),
    )
    summary = summary_of(make_state(*tasks, assignees=("ari", "(unassigned)")))

    assert assignee_rows(summary) == [("ari", 0), ("(unassigned)", 2), (None, 1)]


def test_summary_overdue_uses_the_supplied_date() -> None:
    """CP-497, CP-508, T04: an open task due before the supplied day is overdue, and no other is."""
    tasks = (
        make_task(1, status=TaskStatus.TODO, due=YESTERDAY),
        make_task(2, status=TaskStatus.IN_PROGRESS, due=TODAY),
        make_task(3, status=TaskStatus.TODO, due=None),
        make_task(4, status=TaskStatus.DONE, due=YESTERDAY),
        make_task(5, status=TaskStatus.CANCELLED, due=YESTERDAY),
    )
    state = make_state(*tasks)

    assert summary_of(state, ALPHA, TODAY).overdue == 1
    assert summary_of(state, ALPHA, date(2026, 10, 29)).overdue == 2
    assert summary_of(state, ALPHA, YESTERDAY).overdue == 0


def test_summary_undated_count_includes_every_status() -> None:
    """CP-498, T04: closed undated tasks count as undated and in no assignee row."""
    tasks = (
        make_task(1, status=TaskStatus.TODO, assignee="ari"),
        make_task(2, status=TaskStatus.DONE, assignee="ari"),
        make_task(3, status=TaskStatus.CANCELLED, assignee=None),
        make_task(4, status=TaskStatus.IN_PROGRESS, due=TODAY, assignee="bo"),
    )
    summary = summary_of(make_state(*tasks))

    assert summary.no_due_date == 3
    assert assignee_rows(summary) == [("ari", 1), ("bo", 1), (None, 0)]


def test_summary_is_an_immutable_read() -> None:
    """CP-506, T04: the input is unchanged, every value is frozen and tuple-backed, counts are >= 0."""
    state = mixed_state()
    before = deepcopy(state)
    summary = summary_of(state)

    assert state == before
    assert isinstance(summary.status_counts, tuple)
    assert isinstance(summary.priority_counts, tuple)
    assert isinstance(summary.assignee_counts, tuple)
    for value in (
        summary,
        summary.status_counts[0],
        summary.priority_counts[0],
        summary.assignee_counts[0],
    ):
        field = fields(value)[0].name
        with pytest.raises(FrozenInstanceError):
            setattr(value, field, None)
    for count in (
        summary.total,
        summary.overdue,
        summary.no_due_date,
        *(row.count for row in summary.status_counts),
        *(row.count for row in summary.priority_counts),
        *(row.count for row in summary.assignee_counts),
    ):
        assert count >= 0
    assert summary.assignee_counts[-1].assignee is None
    assert [type(row) for row in summary.status_counts] == [StatusCount] * 4
    assert [type(row) for row in summary.priority_counts] == [PriorityCount] * 4
    assert all(type(row) is AssigneeCount for row in summary.assignee_counts)
    assert summarize_project(state, ALPHA, TODAY) == summary
