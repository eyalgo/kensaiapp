"""The timed run: project creation and, at task volume, adding a task, editing one, adding and
removing a task's label, saving the operator's name, adding a comment, adding and removing a
name on the People assignee list, and moving a task from `todo` to `in-progress`, each with the
page it lands on.

A script, not a collected test: pytest does not pick it up, because its name does not start with
`test_`. Run it from the product root with `python3 tests/timed_run.py`. It uses locations of its
own in a temporary directory, never `data/`, a real `SavedData`, and `Site.handle` with the
same-origin marks a browser sends. It exits non-zero on a refused or failed action, on a landing
that is not the saved task's page, and on any action at or over the limit (SDD § 4 TS-5; NFDR
QC-48; SRS NFR-1).

The task measurement seeds 1,000 tasks of 20 comments each through the real saved data, adds one
more through the request path, and times that POST and its landing GET apart. The field edit seeds
its own 1,000 tasks in a location of its own, loads one task's edit form, submits its shown values
with a changed title, and times that POST and its landing GET apart too. The label add and the label
remove each seed their own 1,000 tasks, send the one label request, and time that POST and its
landing GET apart and as a total, which must stay under the limit even when each part does. The name
save seeds its own 1,000 tasks, posts one ordinary name to People, and times that POST and its
landing GET apart; it counts only as a changed save whose landing shows the saved name. The comment
add, the assignee add and the assignee remove each seed a full-volume fixture of their own too, send
the one form POST, and time it, its landing GET and their total; each counts only when the saved
file is the fixture with that one change and the landing shows the action's completion line. The
status move comes last, on a fixture of its own: it sends the one list-row move of a `todo` task,
and counts only when the saved file is the fixture with that task's status replaced and nothing
else, and the project list it lands on shows the move's completion line. Its harness is checked by
tests/integration/test_timed_run.py.
"""

from __future__ import annotations

import re
import sys
import tempfile
import time
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime, timedelta
from html import escape, unescape
from pathlib import Path
from urllib.parse import urlencode

PRODUCT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRODUCT_ROOT))

from application import Tracker
from domain import (
    LONG_TEXT_MAX,
    SHORT_TEXT_MAX,
    Comment,
    Task,
    TaskStatus,
    TrackerState,
    empty_state,
    find_task,
    restore_state,
    restore_task,
)
from persistence import SavedData
from web import Site

LIMIT_SECONDS = 1.0
HOST = "127.0.0.1:8017"
FORM_HEADERS = {
    "Host": HOST,
    "Sec-Fetch-Site": "same-origin",
    "Content-Type": "application/x-www-form-urlencoded",
}
ORDINARY_CREATES = 50
CREATED_PREFIX = "/projects/"
TASK_VOLUME = 1000
COMMENTS_PER_TASK = 20
VOLUME_PROJECT_NAME = "Volume project"
SEED_INSTANT = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)
SEED_FIRST_DUE = date(2026, 11, 1)
SEED_PRIORITIES = ("low", "medium", "high", "critical")
SEED_STATUSES = ("todo", "in-progress", "done", "cancelled")
ADDED_TITLE = "Review the new task in the list"
ADDED_PREFIX = "/tasks/"
ADDED_SUFFIX = "?added"
ADD_LABEL = f"add a task at {TASK_VOLUME} tasks"
LANDING_LABEL = f"landing page at {TASK_VOLUME} tasks"
EDIT_TASK_ID = TASK_VOLUME // 2
EDITED_TITLE = "Revise the title of this seeded task"
EDITED_SUFFIX = "?saved"
EDIT_LABEL = f"edit a task at {TASK_VOLUME} tasks"
EDIT_LANDING_LABEL = f"edit landing page at {TASK_VOLUME} tasks"
LABEL_TASK_ID = TASK_VOLUME // 4
LABEL_ADDED = "needs review"
LABEL_REMOVED = "seed"
NAME_VALUE = "Jordan Rivera"
NAME_ADDRESS = "/operator-name"
PEOPLE_ADDRESS = "/people"
NAME_LABEL = f"set your name at {TASK_VOLUME} tasks"
NAME_LANDING_LABEL = f"name landing page at {TASK_VOLUME} tasks"
COMMENT_TASK_ID = 250
COMMENT_TEXT = "Compare the new figures with the report before the next review."
COMMENT_OPERATOR_NAME = "Jordan Rivera"
ASSIGNEE_NAME = "Avery Chen"
MOVE_TASK_ID = 4
MOVE_STATUS = TaskStatus.IN_PROGRESS
MOVE_PLACE = "list"
MOVE_LABEL = f"move a task at {TASK_VOLUME} tasks"
MOVE_LANDING_LABEL = f"move landing page at {TASK_VOLUME} tasks"
MOVE_TOTAL_LABEL = f"move total at {TASK_VOLUME} tasks"
TASK_FIELDS = ("title", "priority", "assignee", "due_date")
SHOWN_VALUE = re.compile(r'<input type="hidden" name="shown_([a-z_]+)" value="([^"]*)">')


@dataclass(frozen=True)
class Spec:
    """One project creation to time, with a label that says which length it is."""

    label: str
    name: str
    description: str


@dataclass(frozen=True)
class Timed:
    label: str
    seconds: float
    created: bool


class RealClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


def specs() -> list[Spec]:
    """Ordinary lengths (a short name and a short description), then each maximum."""
    ordinary = [
        Spec(f"ordinary create {n}", f"Project {n}", "A short description of the project.")
        for n in range(1, ORDINARY_CREATES + 1)
    ]
    maximum = Spec("create at both maximums", "N" * SHORT_TEXT_MAX, "D" * LONG_TEXT_MAX)
    return [*ordinary, maximum]


def timed_creates(site: Site, to_time: list[Spec]) -> list[Timed]:
    """Create each project through the request path and time it. `created` is a 303 to its page."""
    results = []
    for spec in to_time:
        body = urlencode({"name": spec.name, "description": spec.description}).encode("utf-8")
        started = time.perf_counter()
        response = site.handle("POST", "/projects", FORM_HEADERS, body)
        seconds = time.perf_counter() - started
        location = dict(response.headers).get("Location", "")
        results.append(
            Timed(
                spec.label, seconds, response.status == 303 and location.startswith(CREATED_PREFIX)
            )
        )
    return results


def verdict(results: list[Timed], limit: float) -> int:
    """Print each action with its time, and return 1 when one was refused, failed or too slow."""
    status = 0
    for result in results:
        problems = []
        if not result.created:
            problems.append("refused or failed")
        if result.seconds >= limit:
            problems.append(f"at or over {limit:g} s")
        print(
            f"{result.label}: {result.seconds * 1000:.1f} ms"
            + (f" — {', '.join(problems)}" if problems else "")
        )
        if problems:
            status = 1
    return status


class FixtureShapeError(ValueError):
    """A fixture whose tasks hold unequal numbers of comments, which no report line can state."""


def _seeded_task(number: int) -> Task:
    """The number-th seeded task: an ordinary title, 20 comments, dated in a spread of days."""
    comments = [
        Comment(
            f"Comment {index} on task {number}: a short ordinary note about the work.",
            "Seed Author",
            SEED_INSTANT + timedelta(minutes=index),
        )
        for index in range(1, COMMENTS_PER_TASK + 1)
    ]
    due = None if number % 5 == 0 else (SEED_FIRST_DUE + timedelta(days=number % 60)).isoformat()
    return restore_task(
        id=number,
        project_id=1,
        title=f"Seeded task {number}: write up the work for this part",
        status=SEED_STATUSES[number % len(SEED_STATUSES)],
        priority=SEED_PRIORITIES[number % len(SEED_PRIORITIES)],
        assignee=None,
        labels=("seed",),
        due_date=due,
        created_at=SEED_INSTANT + timedelta(seconds=number),
        comments=comments,
    )


def seeded_state() -> TrackerState:
    """One project holding 1,000 tasks of 20 comments each, built from immutable domain values."""
    tasks = [_seeded_task(number) for number in range(1, TASK_VOLUME + 1)]
    return restore_state(
        [(1, VOLUME_PROJECT_NAME, "Holds the task-volume fixture.")],
        2,
        tasks=tasks,
        next_task_id=TASK_VOLUME + 1,
    )


def _open_volume(saved_data: SavedData, state: TrackerState) -> tuple[Site, TrackerState]:
    """Save the state through the real saved data, load it as a start would, and serve it."""
    saved_data.save(state)
    loaded = saved_data.load()
    assert loaded is not None
    return Site(Tracker(loaded, saved_data, RealClock()), HOST), loaded


def open_task_volume(saved_data: SavedData) -> tuple[Site, TrackerState]:
    """The 1,000-task fixture, saved, loaded and served."""
    return _open_volume(saved_data, seeded_state())


def open_assignee_add_volume(saved_data: SavedData) -> tuple[Site, TrackerState]:
    """The 1,000-task fixture, whose assignee list does not yet hold the name to be added."""
    return _open_volume(saved_data, seeded_state())


def open_assignee_remove_volume(saved_data: SavedData) -> tuple[Site, TrackerState]:
    """The 1,000-task fixture, whose assignee list holds the name to be removed."""
    return _open_volume(saved_data, replace(seeded_state(), assignees=(ASSIGNEE_NAME,)))


def open_comment_volume(saved_data: SavedData) -> tuple[Site, TrackerState]:
    """The 1,000-task fixture with the saved operator name a comment is written under."""
    return _open_volume(saved_data, replace(seeded_state(), operator_name=COMMENT_OPERATOR_NAME))


def _added_task_address(location: str, expected_id: int) -> bool:
    return location == f"{ADDED_PREFIX}{expected_id}{ADDED_SUFFIX}"


def _saved_the_added_task(saved_data: SavedData, before: TrackerState, task_id: int) -> bool:
    """True when the saved file holds every earlier task as it was, and the new one beside it."""
    after = saved_data.load()
    if after is None or len(after.tasks) != len(before.tasks) + 1:
        return False
    added = after.tasks[-1]
    return (
        after.tasks[:-1] == before.tasks
        and added.id == task_id
        and added.title == ADDED_TITLE
        and after.next_task_id == task_id + 1
    )


def measure_task_volume(
    site: Site, saved_data: SavedData, timer: Callable[[], float] = time.perf_counter
) -> list[Timed]:
    """Add one task through the request path and fetch the page it lands on, timing each apart.

    The add counts as done only when it is a 303 to the new task's page and the saved file holds the
    earlier tasks unchanged and the new one. The landing counts as done only when it is a 200 whose
    page shows the saved task's title. With no valid landing address the landing is not attempted.
    """
    before = saved_data.load()
    assert before is not None
    new_id = before.next_task_id
    project_id = before.projects[0].id
    body = urlencode({"title": ADDED_TITLE}).encode("utf-8")
    started = timer()
    response = site.handle("POST", f"/projects/{project_id}/tasks", FORM_HEADERS, body)
    add_seconds = timer() - started
    location = dict(response.headers).get("Location", "")
    added = (
        response.status == 303
        and _added_task_address(location, new_id)
        and _saved_the_added_task(saved_data, before, new_id)
    )
    results = [Timed(ADD_LABEL, add_seconds, added)]
    if not _added_task_address(location, new_id):
        return [*results, Timed(LANDING_LABEL, 0.0, False)]
    started = timer()
    landing = site.handle("GET", location, {"Host": HOST}, b"")
    landing_seconds = timer() - started
    shown = landing.status == 200 and escape(ADDED_TITLE) in landing.body.decode("utf-8")
    return [*results, Timed(LANDING_LABEL, landing_seconds, shown)]


def _saved_the_edit(saved_data: SavedData, before: TrackerState, task_id: int) -> bool:
    """True when the saved file is the fixture with this one task's title replaced, and no more."""
    after = saved_data.load()
    if after is None:
        return False
    edited = tuple(
        replace(task, title=EDITED_TITLE) if task.id == task_id else task for task in before.tasks
    )
    return after == replace(before, tasks=edited)


def _loaded_form_body(site: Site, task_id: int) -> bytes | None:
    """The body the task's own form would send with a changed title, or None with no form to load.

    The visible values and the shown values are the ones the loaded page carries; only the title
    differs, as it does when an operator types a new one.
    """
    page = site.handle("GET", f"/tasks/{task_id}", {"Host": HOST}, b"")
    shown = {
        name: unescape(value) for name, value in SHOWN_VALUE.findall(page.body.decode("utf-8"))
    }
    if page.status != 200 or set(shown) != set(TASK_FIELDS):
        return None
    submitted = {**shown, "title": EDITED_TITLE}
    shown_fields = {f"shown_{name}": value for name, value in shown.items()}
    return urlencode({**submitted, **shown_fields}).encode("utf-8")


def measure_task_edit(
    site: Site, saved_data: SavedData, timer: Callable[[], float] = time.perf_counter
) -> list[Timed]:
    """Edit one task's title through the request path and fetch the page it lands on, timing each apart.

    The edit counts as done only when it is a 303 to the task's saved page and the saved file is the
    fixture with that one title replaced. The landing counts as done only when it is a 200 whose page
    shows the edited title. With no loaded form or no saved address the edit or landing is not attempted.
    """
    before = saved_data.load()
    assert before is not None
    address = f"{ADDED_PREFIX}{EDIT_TASK_ID}"
    body = _loaded_form_body(site, EDIT_TASK_ID)
    if body is None:
        return [Timed(EDIT_LABEL, 0.0, False), Timed(EDIT_LANDING_LABEL, 0.0, False)]
    started = timer()
    response = site.handle("POST", address, FORM_HEADERS, body)
    edit_seconds = timer() - started
    location = dict(response.headers).get("Location", "")
    saved_address = location == f"{address}{EDITED_SUFFIX}"
    edited = (
        response.status == 303
        and saved_address
        and _saved_the_edit(saved_data, before, EDIT_TASK_ID)
    )
    results = [Timed(EDIT_LABEL, edit_seconds, edited)]
    if not saved_address:
        return [*results, Timed(EDIT_LANDING_LABEL, 0.0, False)]
    started = timer()
    landing = site.handle("GET", location, {"Host": HOST}, b"")
    landing_seconds = timer() - started
    shown = landing.status == 200 and escape(EDITED_TITLE) in landing.body.decode("utf-8")
    return [*results, Timed(EDIT_LANDING_LABEL, landing_seconds, shown)]


def edit_fixture_report(state: TrackerState) -> str:
    """The volume and the lengths of the text the field-edit measurement ran on."""
    task = state.tasks[0]
    comments = sum(len(each.comments) for each in state.tasks)
    return (
        f"edit fixture: {len(state.tasks)} tasks, {COMMENTS_PER_TASK} comments each "
        f"({comments} in all); title of {len(task.title)} characters, "
        f"edited title of {len(EDITED_TITLE)} characters"
    )


def fixture_report(state: TrackerState) -> str:
    """The volume and the actual lengths of the ordinary text the task measurement ran on."""
    task = state.tasks[0]
    comments = sum(len(each.comments) for each in state.tasks)
    return (
        f"task fixture: {len(state.tasks)} tasks, {COMMENTS_PER_TASK} comments each "
        f"({comments} in all); title of {len(task.title)} characters, "
        f"comment of {len(task.comments[0].text)} characters, "
        f"added title of {len(ADDED_TITLE)} characters"
    )


@dataclass(frozen=True)
class LabelAction:
    """One label action to time: its route, its label, and the page line that shows its result."""

    name: str
    route: str
    label: str
    flag: str
    completion: str

    @property
    def request_label(self) -> str:
        return f"{self.name} a label at {TASK_VOLUME} tasks"

    @property
    def landing_label(self) -> str:
        return f"label {self.name} landing page at {TASK_VOLUME} tasks"

    @property
    def total_label(self) -> str:
        return f"label {self.name} total at {TASK_VOLUME} tasks"

    @property
    def fixture_label(self) -> str:
        return f"label {self.name} fixture"


LABEL_ADD = LabelAction(
    "add", "labels", LABEL_ADDED, "label_added", "You added the label '{label}' to '{title}'."
)
LABEL_REMOVE = LabelAction(
    "remove",
    "labels/remove",
    LABEL_REMOVED,
    "label_removed",
    "You removed the label '{label}' from '{title}'.",
)


def _saved_the_label_change(
    saved_data: SavedData, before: TrackerState, action: LabelAction
) -> bool:
    """True when the saved file is the fixture with this one task's labels changed as intended."""
    after = saved_data.load()
    if after is None:
        return False
    changed = []
    for task in before.tasks:
        if task.id != LABEL_TASK_ID:
            changed.append(task)
        elif action is LABEL_ADD:
            changed.append(replace(task, labels=(*task.labels, action.label)))
        else:
            kept = tuple(each for each in task.labels if each != action.label)
            changed.append(replace(task, labels=kept))
    return after == replace(before, tasks=tuple(changed))


def _measure_label_action(
    site: Site, saved_data: SavedData, timer: Callable[[], float], action: LabelAction
) -> list[Timed]:
    """Send one label request and fetch the page it lands on, timing each apart and together.

    The request counts as done only when it is a 303 to the task's address carrying the action's
    outcome and the saved file is the fixture with that one label change. The landing counts as done
    only when it is a 200 whose page shows the action's completion line for the label and the task.
    The total, submission plus landing, is held to the limit as well. With no valid landing address
    the landing is not attempted and the total is not a success.
    """
    before = saved_data.load()
    assert before is not None
    task = next(each for each in before.tasks if each.id == LABEL_TASK_ID)
    address = f"{ADDED_PREFIX}{LABEL_TASK_ID}"
    expected = f"{address}?{urlencode({action.flag: action.label})}"
    body = urlencode({"label": action.label}).encode("utf-8")
    started = timer()
    response = site.handle("POST", f"{address}/{action.route}", FORM_HEADERS, body)
    request_seconds = timer() - started
    location = dict(response.headers).get("Location", "")
    redirected = response.status == 303 and location == expected
    saved = redirected and _saved_the_label_change(saved_data, before, action)
    results = [Timed(action.request_label, request_seconds, saved)]
    if not redirected:
        return [
            *results,
            Timed(action.landing_label, 0.0, False),
            Timed(action.total_label, request_seconds, False),
        ]
    started = timer()
    landing = site.handle("GET", location, {"Host": HOST}, b"")
    landing_seconds = timer() - started
    shown = landing.status == 200 and _shows(landing.body.decode("utf-8"), action, task.title)
    return [
        *results,
        Timed(action.landing_label, landing_seconds, shown),
        Timed(action.total_label, request_seconds + landing_seconds, saved and shown),
    ]


def _shows(page: str, action: LabelAction, title: str) -> bool:
    """True when the page carries the action's completion line, its values escaped as the page
    does."""
    line = action.completion.format(label=escape(action.label), title=escape(title))
    return line in page


def measure_label_add(
    site: Site, saved_data: SavedData, timer: Callable[[], float] = time.perf_counter
) -> list[Timed]:
    """Add one label to one task through the request path and fetch the page it lands on."""
    return _measure_label_action(site, saved_data, timer, LABEL_ADD)


def measure_label_remove(
    site: Site, saved_data: SavedData, timer: Callable[[], float] = time.perf_counter
) -> list[Timed]:
    """Remove one label from one task through the request path and fetch the page it lands on."""
    return _measure_label_action(site, saved_data, timer, LABEL_REMOVE)


def label_fixture_report(state: TrackerState, action: LabelAction) -> str:
    """The volume and the actual lengths of the ordinary text a label measurement ran on."""
    task = next(each for each in state.tasks if each.id == LABEL_TASK_ID)
    comments = sum(len(each.comments) for each in state.tasks)
    verb = "added" if action is LABEL_ADD else "removed"
    return (
        f"{action.fixture_label}: {len(state.tasks)} tasks, {COMMENTS_PER_TASK} comments each "
        f"({comments} in all); title of {len(task.title)} characters, "
        f"label {verb} of {len(action.label)} characters"
    )


def _saved_the_name(saved_data: SavedData, before: TrackerState) -> bool:
    """True when the saved file is the fixture with the name set, and nothing else changed."""
    after = saved_data.load()
    return after == replace(before, operator_name=NAME_VALUE)


def _name_landing_shows(page: str) -> bool:
    """True when the People page holds the saved name in its field and in its completion line."""
    name = escape(NAME_VALUE)
    in_field = f'id="operator-name" name="name" maxlength="{SHORT_TEXT_MAX}" value="{name}"' in page
    return in_field and f"You set your name to '{name}'." in page


def measure_operator_name(
    *, site: Site, saved_data: SavedData, timer: Callable[[], float]
) -> list[Timed]:
    """Save the operator's name through the request path and fetch the page it lands on, timing
    each apart.

    The save counts as done only when it is a 303 to People carrying exactly the saved name and the
    saved file is the fixture with that name set and nothing else changed. The landing counts as
    done only when it is a 200 whose page shows the saved name in its field and its completion line.
    A refusal, a failure, a no-change redirect or a wrong address is not a save, and then the
    landing is not attempted.
    """
    before = saved_data.load()
    assert before is not None
    expected = f"{PEOPLE_ADDRESS}?{urlencode({'operator_saved': NAME_VALUE})}"
    body = urlencode({"name": NAME_VALUE}).encode("utf-8")
    started = timer()
    response = site.handle("POST", NAME_ADDRESS, FORM_HEADERS, body)
    save_seconds = timer() - started
    location = dict(response.headers).get("Location", "")
    redirected = response.status == 303 and location == expected
    saved = redirected and _saved_the_name(saved_data, before)
    results = [Timed(NAME_LABEL, save_seconds, saved)]
    if not redirected:
        return [*results, Timed(NAME_LANDING_LABEL, 0.0, False)]
    started = timer()
    landing = site.handle("GET", location, {"Host": HOST}, b"")
    landing_seconds = timer() - started
    shown = landing.status == 200 and _name_landing_shows(landing.body.decode("utf-8"))
    return [*results, Timed(NAME_LANDING_LABEL, landing_seconds, shown)]


def name_fixture_report(state: TrackerState) -> str:
    """The volume and the actual lengths of the ordinary text the name measurement ran on."""
    task = state.tasks[0]
    comments = sum(len(each.comments) for each in state.tasks)
    return (
        f"name fixture: {len(state.tasks)} tasks, {COMMENTS_PER_TASK} comments each "
        f"({comments} in all); title of {len(task.title)} characters, "
        f"name of {len(NAME_VALUE)} characters"
    )


@dataclass(frozen=True)
class TimedAction:
    """One form submission to time: its row labels, its one field, and what counts as done.

    `redirect` is the exact address a done submission redirects to. `saved` says whether the saved
    state read back is the fixture with this action's one change and no other. `shows` says whether
    the landing page carries the action's completion line. All three read the loaded pre-state and
    never the product code that did the work, so a product that did it wrongly cannot pass itself.
    """

    request_label: str
    landing_label: str
    total_label: str
    address: str
    field: str
    value: str
    redirect: Callable[[TrackerState], str]
    saved: Callable[[TrackerState, TrackerState | None], bool]
    shows: Callable[[str, TrackerState], bool]


def _measure_action(
    *, site: Site, saved_data: SavedData, timer: Callable[[], float], action: TimedAction
) -> list[Timed]:
    """Send the action's one request and fetch the page it lands on, timing each apart and together.

    The request counts as done only when it is a 303 to the action's exact address and the saved
    file read back is the fixture with that one change. The landing counts as done only when it is a
    200 whose page shows the completion line. The total, submission plus landing and not the gap
    between them, is held to the limit as well. With any other answer the landing is not requested
    and its row and the total's are not done. The saved file is read outside both timed intervals.
    """
    before = saved_data.load()
    assert before is not None
    body = urlencode({action.field: action.value}).encode("utf-8")
    started = timer()
    response = site.handle("POST", action.address, FORM_HEADERS, body)
    request_seconds = timer() - started
    location = dict(response.headers).get("Location", "")
    redirected = response.status == 303 and location == action.redirect(before)
    saved = redirected and action.saved(before, saved_data.load())
    results = [Timed(action.request_label, request_seconds, saved)]
    if not redirected:
        return [
            *results,
            Timed(action.landing_label, 0.0, False),
            Timed(action.total_label, request_seconds, False),
        ]
    started = timer()
    landing = site.handle("GET", location, {"Host": HOST}, b"")
    landing_seconds = timer() - started
    shown = landing.status == 200 and action.shows(landing.body.decode("utf-8"), before)
    return [
        *results,
        Timed(action.landing_label, landing_seconds, shown),
        Timed(action.total_label, request_seconds + landing_seconds, saved and shown),
    ]


def _volume_line(state: TrackerState) -> str:
    """The task count, the comments on each task and the total, read from the loaded fixture."""
    counts = {len(task.comments) for task in state.tasks}
    if len(counts) != 1:
        raise FixtureShapeError(
            f"error: the fixture's tasks hold {sorted(counts)} comments each; a fixture line "
            "states one number for every task, so give every task the same count"
        )
    (per_task,) = counts
    return (
        f"{len(state.tasks)} tasks, {per_task} comments each ({per_task * len(state.tasks)} in all)"
    )


def _comment_task(state: TrackerState) -> Task:
    task = find_task(state, COMMENT_TASK_ID)
    assert task is not None
    return task


def _comment_redirect(before: TrackerState) -> str:
    position = len(_comment_task(before).comments) + 1
    return f"{ADDED_PREFIX}{COMMENT_TASK_ID}?{urlencode({'comment_added': position})}"


def _saved_the_comment(before: TrackerState, after: TrackerState | None) -> bool:
    """True when the saved file is the fixture with one comment last on the task and nothing else.

    The comment's text is the one sent and its author the name the fixture saved. Its time is the
    tracker's own reading of the clock, so it is the one value taken from the saved file.
    """
    saved = None if after is None else find_task(after, COMMENT_TASK_ID)
    earlier = _comment_task(before).comments
    if saved is None or before.operator_name is None or len(saved.comments) != len(earlier) + 1:
        return False
    added = Comment(COMMENT_TEXT, before.operator_name, saved.comments[-1].created_at)
    expected = tuple(
        replace(task, comments=(*task.comments, added)) if task.id == COMMENT_TASK_ID else task
        for task in before.tasks
    )
    return after == replace(before, tasks=expected)


def _comment_landing_shows(page: str, before: TrackerState) -> bool:
    """True when the page carries the completion line and the added text, both escaped as shown."""
    title = escape(_comment_task(before).title)
    return f"You added a comment to '{title}'." in page and escape(COMMENT_TEXT) in page


COMMENT_ADD = TimedAction(
    request_label=f"add a comment at {TASK_VOLUME} tasks",
    landing_label=f"comment landing page at {TASK_VOLUME} tasks",
    total_label=f"comment total at {TASK_VOLUME} tasks",
    address=f"{ADDED_PREFIX}{COMMENT_TASK_ID}/comments",
    field="text",
    value=COMMENT_TEXT,
    redirect=_comment_redirect,
    saved=_saved_the_comment,
    shows=_comment_landing_shows,
)


def measure_comment_add(
    *, site: Site, saved_data: SavedData, timer: Callable[[], float]
) -> list[Timed]:
    """Add one comment to one task through the request path and fetch the page it lands on."""
    return _measure_action(site=site, saved_data=saved_data, timer=timer, action=COMMENT_ADD)


def comment_fixture_report(state: TrackerState) -> str:
    """The volume and the actual lengths of the ordinary text the comment measurement ran on."""
    task = _comment_task(state)
    assert state.operator_name is not None
    return (
        f"comment fixture: {_volume_line(state)}; title of {len(task.title)} characters, "
        f"comment of {len(task.comments[0].text)} characters, "
        f"name of {len(state.operator_name)} characters, "
        f"added comment of {len(COMMENT_TEXT)} characters"
    )


def _assignee_add_redirect(before: TrackerState) -> str:
    return f"{PEOPLE_ADDRESS}?{urlencode({'added': ASSIGNEE_NAME})}"


def _saved_the_assignee_add(before: TrackerState, after: TrackerState | None) -> bool:
    """True when the saved file is the fixture with the name last on the assignee list, no more."""
    return after == replace(before, assignees=(*before.assignees, ASSIGNEE_NAME))


def _assignee_add_landing_shows(page: str, before: TrackerState) -> bool:
    return f"You added '{escape(ASSIGNEE_NAME)}' to the assignees." in page


ASSIGNEE_ADD = TimedAction(
    request_label=f"add an assignee at {TASK_VOLUME} tasks",
    landing_label=f"assignee add landing page at {TASK_VOLUME} tasks",
    total_label=f"assignee add total at {TASK_VOLUME} tasks",
    address="/assignees",
    field="name",
    value=ASSIGNEE_NAME,
    redirect=_assignee_add_redirect,
    saved=_saved_the_assignee_add,
    shows=_assignee_add_landing_shows,
)


def measure_assignee_add(
    *, site: Site, saved_data: SavedData, timer: Callable[[], float]
) -> list[Timed]:
    """Add one name to the assignee list on People and fetch the page it lands on."""
    return _measure_action(site=site, saved_data=saved_data, timer=timer, action=ASSIGNEE_ADD)


def _assignee_remove_redirect(before: TrackerState) -> str:
    return f"{PEOPLE_ADDRESS}?{urlencode({'removed': ASSIGNEE_NAME})}"


def _saved_the_assignee_remove(before: TrackerState, after: TrackerState | None) -> bool:
    """True when the saved file is the fixture with the name gone from the list, and no more.

    Every task keeps the assignee it carried, because the comparison is of the whole state.
    """
    kept = tuple(name for name in before.assignees if name != ASSIGNEE_NAME)
    return ASSIGNEE_NAME in before.assignees and after == replace(before, assignees=kept)


def _assignee_remove_landing_shows(page: str, before: TrackerState) -> bool:
    line = (
        f"You removed '{escape(ASSIGNEE_NAME)}' from the assignees, "
        "and tasks that already carry the name keep it."
    )
    return line in page


ASSIGNEE_REMOVE = TimedAction(
    request_label=f"remove an assignee at {TASK_VOLUME} tasks",
    landing_label=f"assignee remove landing page at {TASK_VOLUME} tasks",
    total_label=f"assignee remove total at {TASK_VOLUME} tasks",
    address="/assignees/remove",
    field="name",
    value=ASSIGNEE_NAME,
    redirect=_assignee_remove_redirect,
    saved=_saved_the_assignee_remove,
    shows=_assignee_remove_landing_shows,
)


def measure_assignee_remove(
    *, site: Site, saved_data: SavedData, timer: Callable[[], float]
) -> list[Timed]:
    """Remove one name from the assignee list on People and fetch the page it lands on."""
    return _measure_action(site=site, saved_data=saved_data, timer=timer, action=ASSIGNEE_REMOVE)


def _task_text_lengths(state: TrackerState) -> str:
    """The lengths of a fixture task's title and one of its comments, in characters."""
    task = state.tasks[0]
    return (
        f"title of {len(task.title)} characters, comment of {len(task.comments[0].text)} characters"
    )


def assignee_add_fixture_report(state: TrackerState) -> str:
    """The volume and the actual lengths of the ordinary text the assignee add ran on."""
    return (
        f"assignee add fixture: {_volume_line(state)}; {_task_text_lengths(state)}, "
        f"name added of {len(ASSIGNEE_NAME)} characters"
    )


def assignee_remove_fixture_report(state: TrackerState) -> str:
    """The volume and the actual lengths of the ordinary text the assignee remove ran on."""
    return (
        f"assignee remove fixture: {_volume_line(state)}; {_task_text_lengths(state)}, "
        f"name removed of {len(ASSIGNEE_NAME)} characters"
    )


def _move_redirect(task: Task) -> str:
    """The exact address a done move redirects to: the moved task's project list, in this order."""
    outcome = urlencode({"moved": MOVE_STATUS.value, "move_task": MOVE_TASK_ID})
    return f"/projects/{task.project_id}?{outcome}"


def _saved_the_move(before: TrackerState, task: Task, after: TrackerState | None) -> bool:
    """True when the task was `todo` and the saved file is the fixture with its status replaced.

    The expectation is built from the loaded pre-state by replacing one field, and never by the
    workflow's own move rule, so a product that moved the task wrongly cannot pass itself. The whole
    state is compared: every other task, project, counter, the assignee list and the operator name.
    """
    expected = tuple(
        replace(each, status=MOVE_STATUS) if each.id == task.id else each for each in before.tasks
    )
    return task.status is TaskStatus.TODO and after == replace(before, tasks=expected)


def measure_task_move(
    *, site: Site, saved_data: SavedData, timer: Callable[[], float]
) -> list[Timed]:
    """Move one `todo` task to `in-progress` from its project's list and fetch the page it lands on.

    Three rows come back, in order: the POST, the landing GET and their total. The task and its
    project are read from the loaded pre-state before the POST interval opens. The POST counts as
    done only when it is a 303 to the exact project-list address and the saved file read back is
    the pre-state with that one status replaced; a task that was not `todo` never counts. The
    landing counts as done only when it is a 200 whose page carries the completion line with the
    title escaped as the page shows it. The total, the two intervals added and not the gap between
    them, counts only when both do. The readback sits between the two intervals. With any other
    answer to the POST the landing is not requested: its row is zero and failed, and the total is
    the POST's time. Nothing is printed here; `verdict` prints the rows.
    """
    before = saved_data.load()
    assert before is not None
    task = find_task(before, MOVE_TASK_ID)
    assert task is not None
    body = urlencode({"status": MOVE_STATUS.value, "place": MOVE_PLACE}).encode("utf-8")
    started = timer()
    response = site.handle("POST", f"{ADDED_PREFIX}{MOVE_TASK_ID}/move", FORM_HEADERS, body)
    post_seconds = timer() - started
    location = dict(response.headers).get("Location", "")
    redirected = response.status == 303 and location == _move_redirect(task)
    saved = redirected and _saved_the_move(before, task, saved_data.load())
    results = [Timed(MOVE_LABEL, post_seconds, saved)]
    if not redirected:
        return [
            *results,
            Timed(MOVE_LANDING_LABEL, 0.0, False),
            Timed(MOVE_TOTAL_LABEL, post_seconds, False),
        ]
    started = timer()
    landing = site.handle("GET", location, {"Host": HOST}, b"")
    landing_seconds = timer() - started
    line = f"You moved '{escape(task.title)}' to {MOVE_STATUS.value}."
    shown = landing.status == 200 and line in landing.body.decode("utf-8")
    return [
        *results,
        Timed(MOVE_LANDING_LABEL, landing_seconds, shown),
        Timed(MOVE_TOTAL_LABEL, post_seconds + landing_seconds, saved and shown),
    ]


def move_fixture_report(state: TrackerState) -> str:
    """The volume and the actual lengths of the ordinary text the move measurement ran on.

    Every number is read from the fixture as loaded back: the counts from all its tasks, the
    lengths, in code points, from the task the move acts on. Nothing is printed here.
    """
    task = find_task(state, MOVE_TASK_ID)
    assert task is not None
    return (
        f"move fixture: {_volume_line(state)}; title of {len(task.title)} characters, "
        f"comment of {len(task.comments[0].text)} characters"
    )


def main(directory: Path | None = None, timer: Callable[[], float] = time.perf_counter) -> int:
    """Run the project creates, then the add, the edit, the label add and remove, the name save, the
    comment add, the assignee add and remove and the status move at task volume; 1 when any
    failed."""
    if directory is None:
        with tempfile.TemporaryDirectory() as temporary:
            return main(Path(temporary), timer)
    saved_data = SavedData(directory / "data")
    project_site = Site(Tracker(empty_state(), saved_data, RealClock()), HOST)
    status = verdict(timed_creates(project_site, specs()), LIMIT_SECONDS)
    task_data = SavedData(directory / "task-volume")
    task_site, seeded = open_task_volume(task_data)
    print(fixture_report(seeded))
    task_status = verdict(measure_task_volume(task_site, task_data, timer), LIMIT_SECONDS)
    edit_data = SavedData(directory / "edit-volume")
    edit_site, edit_seeded = open_task_volume(edit_data)
    print(edit_fixture_report(edit_seeded))
    edit_status = verdict(measure_task_edit(edit_site, edit_data, timer), LIMIT_SECONDS)
    label_status = 0
    for action, measure in ((LABEL_ADD, measure_label_add), (LABEL_REMOVE, measure_label_remove)):
        label_data = SavedData(directory / f"label-{action.name}-volume")
        label_site, label_seeded = open_task_volume(label_data)
        print(label_fixture_report(label_seeded, action))
        label_status = max(
            label_status, verdict(measure(label_site, label_data, timer), LIMIT_SECONDS)
        )
    name_data = SavedData(directory / "name-volume")
    name_site, name_seeded = open_task_volume(name_data)
    print(name_fixture_report(name_seeded))
    name_results = measure_operator_name(site=name_site, saved_data=name_data, timer=timer)
    name_status = verdict(name_results, LIMIT_SECONDS)
    new_action_status = _run_new_actions(directory, timer)
    move_status = _run_move(directory, timer)
    return max(
        status, task_status, edit_status, label_status, name_status, new_action_status, move_status
    )


def _run_new_actions(directory: Path, timer: Callable[[], float]) -> int:
    """Time the comment add, the assignee add and the assignee remove, each on a fixture of its own.

    Each prints its fixture line and then its three rows, in that order, after every older line.
    """
    actions = (
        ("comment-volume", open_comment_volume, comment_fixture_report, measure_comment_add),
        (
            "assignee-add-volume",
            open_assignee_add_volume,
            assignee_add_fixture_report,
            measure_assignee_add,
        ),
        (
            "assignee-remove-volume",
            open_assignee_remove_volume,
            assignee_remove_fixture_report,
            measure_assignee_remove,
        ),
    )
    status = 0
    for location, open_volume, report, measure in actions:
        action_data = SavedData(directory / location)
        action_site, action_seeded = open_volume(action_data)
        print(report(action_seeded))
        results = measure(site=action_site, saved_data=action_data, timer=timer)
        status = max(status, verdict(results, LIMIT_SECONDS))
    return status


def _run_move(directory: Path, timer: Callable[[], float]) -> int:
    """Time the status move on a fixture of its own, after every other line the run prints.

    Prints the fixture line, then the move's three rows: the POST, the landing and the total.
    """
    move_data = SavedData(directory / "move-volume")
    move_site, move_seeded = open_task_volume(move_data)
    print(move_fixture_report(move_seeded))
    results = measure_task_move(site=move_site, saved_data=move_data, timer=timer)
    return verdict(results, LIMIT_SECONDS)


if __name__ == "__main__":
    sys.exit(main())
