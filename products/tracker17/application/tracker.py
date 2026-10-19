"""The Tracker: the operator's actions over the current state.

Each action applies a `domain` rule to the current state. An action whose result changes the state
saves the new state and only then makes it current (SDD § 4 SD-2); an edit whose outcome reports no
changed field, or a label action whose outcome reports no change, returns the current task without
a save. It decides no rule, and knows nothing of how or where the state is saved.
"""

from __future__ import annotations

from dataclasses import dataclass

from application.contracts import Clock, Saver
from domain import (
    OperatorNameOutcome,
    Project,
    Task,
    TaskEditContext,
    TaskEditOutcome,
    TaskFields,
    TaskLabelOutcome,
    TrackerState,
    add_assignee,
    add_task,
    add_task_comment,
    add_task_label,
    create_project,
    edit_task,
    find_project,
    find_task,
    is_overdue,
    list_assignees,
    list_project_tasks,
    list_projects,
    remove_assignee,
    remove_task_label,
    set_operator_name,
    task_edit_context,
)


@dataclass(frozen=True)
class TaskRow:
    """One row of a project's task list: the task, and whether it is overdue on the page's date."""

    task: Task
    overdue: bool


class Tracker:
    """Holds the current state while the tracker runs."""

    def __init__(self, state: TrackerState, saver: Saver, clock: Clock) -> None:
        self._state = state
        self._saver = saver
        self._clock = clock

    def create_project(self, name: str, description: str) -> Project:
        """Create a project. A refusal or a saver failure propagates; the state stays as it was."""
        new_state, project = create_project(self._state, name, description)
        self._save_then_publish(new_state)
        return project

    def operator_name(self) -> str | None:
        """The one operator name, exactly as saved, or None when none is set."""
        return self._state.operator_name

    def set_operator_name(self, name: str) -> OperatorNameOutcome:
        """Set the operator name; a refusal or a saver failure propagates, the state as it was.

        The domain decides whether the name is valid and whether it differs from the saved one. An
        outcome that reports a change is saved before it becomes current; one that reports none, the
        exact name already saved, saves and publishes nothing.
        """
        new_state, outcome = set_operator_name(self._state, name)
        if outcome.changed:
            self._save_then_publish(new_state)
        return outcome

    def projects(self) -> tuple[Project, ...]:
        """Every project, in the order `domain` gives."""
        return list_projects(self._state)

    def project(self, project_id: int) -> Project | None:
        """The project with this identity, or None."""
        return find_project(self._state, project_id)

    def assignees(self) -> tuple[str, ...]:
        """Every assignee name, earliest added first."""
        return list_assignees(self._state)

    def add_assignee(self, name: str) -> str:
        """Add the name to the end of the list. A refusal or a saver failure propagates.

        Returns the name exactly as given, once it is saved.
        """
        self._save_then_publish(add_assignee(self._state, name))
        return name

    def remove_assignee(self, name: str) -> str:
        """Remove the exactly matching name. A refusal or a saver failure propagates.

        Returns the name exactly as given, once the removal is saved.
        """
        self._save_then_publish(remove_assignee(self._state, name))
        return name

    def add_task(
        self,
        project_id: int,
        title: str,
        priority: str = "",
        assignee: str = "",
        due_date: str = "",
    ) -> Task:
        """Add a task to the project. A refusal or a saver failure propagates.

        The creation instant is the one the clock gives for this add. Returns the task once it is
        saved.
        """
        new_state, task = add_task(
            self._state, project_id, title, priority, assignee, due_date, self._clock.now()
        )
        self._save_then_publish(new_state)
        return task

    def edit_task(self, task_id: int, submitted: TaskFields, shown: TaskFields) -> TaskEditOutcome:
        """Apply the changed fields to the task. A refusal or a saver failure propagates.

        The domain decides which fields changed. An outcome that reports a change is saved before
        it becomes current; one that reports none saves and publishes nothing.
        """
        new_state, outcome = edit_task(self._state, task_id, submitted, shown)
        if outcome.changed:
            self._save_then_publish(new_state)
        return outcome

    def add_task_label(self, task_id: int, label: str) -> TaskLabelOutcome:
        """Add the label to the task. A refusal or a saver failure propagates.

        The domain decides whether the label changes anything. An outcome that reports a change is
        saved before it becomes current; one that reports none, a label already carried, saves and
        publishes nothing.
        """
        new_state, outcome = add_task_label(self._state, task_id, label)
        if outcome.changed:
            self._save_then_publish(new_state)
        return outcome

    def remove_task_label(self, task_id: int, label: str) -> TaskLabelOutcome:
        """Remove the exactly matching label from the task. A refusal or a saver failure propagates.

        The removal is saved before it becomes current.
        """
        new_state, outcome = remove_task_label(self._state, task_id, label)
        if outcome.changed:
            self._save_then_publish(new_state)
        return outcome

    def add_task_comment(self, task_id: int, text: str) -> Task:
        """Add a comment to the task under the operator name saved now. A refusal or a saver
        failure propagates; the state stays as it was.

        The written instant is the one the clock gives for this add. Every accepted add is a new
        comment, so it is always saved, before it becomes current. Returns the updated task.
        """
        new_state, task = add_task_comment(self._state, task_id, text, self._clock.now())
        self._save_then_publish(new_state)
        return task

    def task_edit_context(self, task_id: int) -> TaskEditContext | None:
        """What the task's edit form is built from, or None when no task has this identity."""
        return task_edit_context(self._state, task_id)

    def task(self, task_id: int) -> Task | None:
        """The task with this identity, or None."""
        return find_task(self._state, task_id)

    def project_tasks(self, project_id: int) -> tuple[TaskRow, ...]:
        """The project's tasks in list order, each with its overdue flag.

        One clock read gives the date for the whole list: the machine-local calendar date of that
        instant. A later call reads the clock again.
        """
        today = self._clock.now().astimezone().date()
        return tuple(
            TaskRow(task, is_overdue(task.due_date, task.status, today))
            for task in list_project_tasks(self._state, project_id)
        )

    def _save_then_publish(self, new_state: TrackerState) -> None:
        self._saver.save(new_state)
        self._state = new_state
