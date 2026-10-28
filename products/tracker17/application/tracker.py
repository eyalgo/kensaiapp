"""The Tracker: the operator's actions over the current state.

Each action applies a `domain` rule to the current state. An action whose result changes the state
saves the new state and only then makes it current (SDD § 4 SD-2); an edit whose outcome reports no
changed field, or a label action whose outcome reports no change, returns the current task without
a save. It decides no rule, and knows nothing of how or where the state is saved.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

from application.contracts import Clock, Saver
from domain import (
    FilterFieldRefusal,
    FilterInput,
    FilterOptions,
    OperatorNameOutcome,
    Project,
    ProjectListRefused,
    SortedSelection,
    SortFieldRefusal,
    SortInput,
    Task,
    TaskEditContext,
    TaskEditOutcome,
    TaskFields,
    TaskFilter,
    TaskLabelOutcome,
    TaskSort,
    TaskStatus,
    TrackerState,
    add_assignee,
    add_task,
    add_task_comment,
    add_task_label,
    all_filter_options,
    allowed_moves,
    create_project,
    edit_task,
    find_project,
    find_task,
    is_overdue,
    list_assignees,
    list_project_tasks,
    list_projects,
    move_task,
    project_filter_options,
    remove_assignee,
    remove_task_label,
    set_operator_name,
    sort_all_tasks,
    sort_project_tasks,
    task_edit_context,
)

NO_SORT = SortInput()


@dataclass(frozen=True)
class TaskRow:
    """One row of a task list, a project's or all tasks: the task, and whether it is overdue on the
    page's date."""

    task: Task
    overdue: bool


@dataclass(frozen=True)
class ProjectTaskList:
    """A task list read for one page, whichever scope the read supplied (one project's tasks, or all
    tasks): the whole scope's task count, the matching rows in list order, how many matched and the
    choices as validated.

    A refusal of the filter or of the sort has no rows, no match count, no validated choices and no
    visible count: it carries the typed problems in control order beside the raw choices it was sent
    with. Both kinds carry the options of the whole scope, so the controls can be built from
    either. `narrowed` speaks of the filter alone; `count_requested` is the domain's word on
    whether the page owes the operator the number of tasks it lists.
    """

    task_count: int
    rows: tuple[TaskRow, ...]
    match_count: int
    filter: TaskFilter | None
    fields: FilterInput
    problems: tuple[FilterFieldRefusal | SortFieldRefusal, ...]
    assignees: tuple[str, ...]
    labels: tuple[str, ...]
    sort_fields: SortInput
    sorting: TaskSort | None
    count_requested: bool

    @property
    def narrowed(self) -> bool:
        """Whether the validated choices narrow the list. A refused filter narrows nothing."""
        return self.filter is not None and self.filter.narrows


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

    def move_task(self, task_id: int, status: str) -> Task:
        """Move the task to the status. A refusal or a saver failure propagates; the state stays.

        The domain checks the move against the state held now, never against what a page showed.
        The accepted move is saved before it becomes current. Returns the moved task.
        """
        new_state, task = move_task(self._state, task_id, status)
        self._save_then_publish(new_state)
        return task

    def allowed_moves(self, status: TaskStatus) -> tuple[TaskStatus, ...]:
        """The statuses a task in `status` may move to, in the order `domain` gives."""
        return allowed_moves(status)

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

    def project_task_list(
        self,
        project_id: int,
        fields: FilterInput,
        *,
        sort_fields: SortInput = NO_SORT,
    ) -> ProjectTaskList:
        """The project's tasks narrowed by the filter and ordered by the sort, read for one page,
        saving nothing.

        One clock read gives the date for the whole page: the machine-local calendar date of that
        instant serves the selection and every row's overdue flag. A refused filter or sort comes
        back as the typed problems, never raised, with the options of the whole project.
        """
        return self._read_list(
            fields,
            sort_fields,
            lambda today: sort_project_tasks(self._state, project_id, fields, sort_fields, today),
            project_filter_options(self._state, project_id),
        )

    def all_task_list(
        self,
        fields: FilterInput,
        *,
        sort_fields: SortInput = NO_SORT,
    ) -> ProjectTaskList:
        """Every project's tasks narrowed by the filter and ordered by the sort, read for one page,
        saving nothing.

        The rules, the clock read and the refusal as page data are the project read's. A refused
        choice comes back with the options of all tasks. Project names are not in the result: a
        page gets them from `projects()`.
        """
        return self._read_list(
            fields,
            sort_fields,
            lambda today: sort_all_tasks(self._state, fields, sort_fields, today),
            all_filter_options(self._state),
        )

    def _read_list(
        self,
        fields: FilterInput,
        sort_fields: SortInput,
        select: Callable[[date], SortedSelection],
        options: FilterOptions,
    ) -> ProjectTaskList:
        """Read the clock once, run the scope's selection against that date and project the
        selection, or the refusal that stops it, for the page."""
        today = self._clock.now().astimezone().date()
        try:
            selection = select(today)
        except ProjectListRefused as refused:
            return ProjectTaskList(
                task_count=options.task_count,
                rows=(),
                match_count=0,
                filter=None,
                fields=fields,
                problems=refused.refusals,
                assignees=options.assignees,
                labels=options.labels,
                sort_fields=sort_fields,
                sorting=None,
                count_requested=False,
            )
        rows = tuple(
            TaskRow(task, is_overdue(task.due_date, task.status, today)) for task in selection.tasks
        )
        return ProjectTaskList(
            task_count=selection.task_count,
            rows=rows,
            match_count=selection.match_count,
            filter=selection.filter,
            fields=fields,
            problems=(),
            assignees=selection.assignees,
            labels=selection.labels,
            sort_fields=sort_fields,
            sorting=selection.sorting,
            count_requested=selection.count_requested,
        )

    def _save_then_publish(self, new_state: TrackerState) -> None:
        self._saver.save(new_state)
        self._state = new_state
