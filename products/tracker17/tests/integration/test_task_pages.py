"""Integration tests of web's task pages, each page read back as a browser parses it (layer 4).

Checks SRS FR-15 (creating a task), FR-16 (editing a task's four fields), FR-24 to FR-26 (the due
date and the overdue marking), FR-36 (the list order), NFR-4 (no script) and NFR-5 (typed text is
shown as text), and DR-2 (the Task entity). Change spec rules CP-106 to CP-110, CP-118, CP-124 to
CP-129 and CP-133 (the add), CP-144 to CP-150 and CP-175 (the edit) and NFDR QC-33, QC-36 and QC-56
are the ones each test names. Whole-path pages are read through the real Site, Tracker and
SavedData; the renderer's own contract is read through the page builders with rows or a context
handed in.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from test_pages import HOSTILE, Element, parse
from test_routes import HOST, get, page
from test_task_routes import (
    NOON,
    MovableClock,
    SwitchedSaver,
    add_task,
    chosen,
    control,
    edit_form,
    edit_values,
    focused,
    make_world,
    offered,
    utc_zone,  # noqa: F401 - a fixture, used through pytestmark
)

from application import (
    SHORT_TEXT_MAX,
    Project,
    Task,
    TaskEditContext,
    TaskFields,
    TaskRow,
    TaskStatus,
    Tracker,
)
from domain import Priority, restore_state, restore_task, task_edit_context
from persistence import SavedData
from web import Site, pages

pytestmark = pytest.mark.usefixtures("utc_zone")

ALPHA = Project(id=1, name="Alpha", description="")
CREATED = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)


def a_task(
    identity: int,
    title: str = "Task",
    *,
    assignee: str | None = None,
    labels: tuple[str, ...] = (),
    due: date | None = None,
    priority: Priority = Priority.MEDIUM,
    status: TaskStatus = TaskStatus.TODO,
) -> Task:
    return Task(
        id=identity,
        project_id=1,
        title=title,
        status=status,
        priority=priority,
        assignee=assignee,
        labels=labels,
        due_date=due,
        created_at=CREATED,
        comments=(),
    )


def context_of(
    task: Task, people: tuple[str, ...] = (), project: Project = ALPHA
) -> TaskEditContext:
    """The edit form's context for a task held by a state with this project and this People."""
    state = restore_state(
        [(project.id, project.name, project.description)],
        project.id + 1,
        list(people),
        tasks=[task],
        next_task_id=task.id + 1,
    )
    context = task_edit_context(state, task.id)
    assert context is not None
    return context


def the_add_form(root: Element) -> Element:
    (form,) = [e for e in root.find_all("form") if e.attrs.get("action") == "/projects/1/tasks"]
    return form


def labels_by_control(root: Element) -> dict[str | None, str]:
    return {label.attrs.get("for"): label.text() for label in root.find_all("label")}


def list_rows(root: Element) -> list[list[Element]]:
    (table,) = root.find_all("table")
    (body,) = table.find_all("tbody")
    return [row.find_all("td") for row in body.find_all("tr")]


@pytest.mark.parametrize("populated", [False, True], ids=["empty", "populated"])
def test_form_is_present_for_empty_and_populated_projects(tmp_path: Path, populated: bool) -> None:
    """CP-106 to CP-110: four labelled fields and Add, in the order and with the defaults named."""
    world = make_world(tmp_path)
    if populated:
        add_task(world.site, title="Existing")
    root = parse(page(get(world.site, "/projects/1")))
    form = the_add_form(root)
    assert form.attrs["method"] == "post"
    labels = labels_by_control(root)
    assert [
        labels[i] for i in ("task-title", "task-priority", "task-assignee", "task-due-date")
    ] == [
        "Title",
        "Priority",
        "Assignee",
        "Due date",
    ]
    title = control(root, "task-title")
    assert title.attrs["name"] == "title" and title.attrs["maxlength"] == str(SHORT_TEXT_MAX)
    priority = control(root, "task-priority")
    assert priority.attrs["name"] == "priority"
    assert [o.text() for o in priority.find_all("option")] == ["low", "medium", "high", "critical"]
    assert offered(priority) == ["low", "medium", "high", "critical"]
    assert chosen(priority) == ["medium"]
    assignee = control(root, "task-assignee")
    assert assignee.attrs["name"] == "assignee"
    assert [o.text() for o in assignee.find_all("option")] == ["unassigned", "Dana", " Ari"]
    assert offered(assignee) == ["", "Dana", " Ari"] and chosen(assignee) == [""]
    due = control(root, "task-due-date")
    assert due.attrs["type"] == "date" and due.attrs["name"] == "due_date"
    assert due.attrs["value"] == ""
    (button,) = form.find_all("button")
    assert button.text() == "Add" and button.attrs["type"] == "submit"
    assert root.find_all("script") == [] and focused(root) == []
    assert [e.text() for e in root.find_all("title")] == ["Alpha - tracker17"]
    (heading,) = root.find_all("h1")
    assert heading.text() == "Alpha"
    created = parse(page(get(world.site, "/projects/1?created")))
    assert focused(created) == [created.find_all("h1")[0]]


def test_the_form_with_no_assignee_offers_only_unassigned_and_a_people_link(tmp_path: Path) -> None:
    """CP-109: the reason there is no one to pick, and the way to add one."""
    world = make_world(tmp_path, people=())
    root = parse(page(get(world.site, "/projects/1")))
    assignee = control(root, "task-assignee")
    assert offered(assignee) == [""] and [o.text() for o in assignee.find_all("option")] == [
        "unassigned"
    ]
    form = the_add_form(root)
    (people,) = [a for a in form.find_all("a")]
    assert people.attrs["href"] == "/people" and people.text() == "People"
    assert "There are no assignees yet. Open People to add one." in form.text()
    with_people = parse(page(get(make_world(tmp_path / "other").site, "/projects/1")))
    assert the_add_form(with_people).find_all("a") == []


def test_project_list_shows_every_own_task_in_seven_columns(tmp_path: Path) -> None:
    """CP-126 to CP-129 and CP-297: title link, status, priority, assignee, labels, date and moves;
    no limit."""
    location = tmp_path / "data"
    first = restore_task(
        1,
        1,
        " Spaced ",
        "in-progress",
        "high",
        "Gone",
        ["ops", "urgent"],
        "2026-10-20",
        CREATED,
        [],
    )
    second = restore_task(2, 1, "Spaced", "todo", "low", None, [], None, CREATED, [])
    other = restore_task(3, 2, "Elsewhere", "todo", "low", None, [], None, CREATED, [])
    bulk = [
        restore_task(i, 1, f"Bulk {i}", "done", "medium", None, [], None, CREATED, [])
        for i in range(4, 124)
    ]
    state = restore_state(
        [(1, "Alpha", ""), (2, "Beta", "")],
        3,
        ["Dana"],
        tasks=[first, second, other, *bulk],
        next_task_id=124,
    )
    tracker = Tracker(state, SwitchedSaver(SavedData(location)), MovableClock(NOON))
    root = parse(page(get(Site(tracker, HOST), "/projects/1")))
    (table,) = root.find_all("table")
    headers = [th.text() for th in table.find_all("th")]
    assert headers == ["Title", "Status", "Priority", "Assignee", "Labels", "Due date", "Moves"]
    rows = list_rows(root)
    assert len(rows) == 122 and all(len(cells) == 7 for cells in rows)
    values = [[cell.text() for cell in cells[:6]] for cells in rows[:2]]
    assert values[0][:4] == [" Spaced ", "in-progress", "high", "Gone"]
    assert "ops" in values[0][4] and "urgent" in values[0][4]
    assert values[0][5].startswith("2026-10-20")
    assert values[1] == ["Spaced", "todo", "low", "unassigned", "none", "none"]
    assert [b.text() for b in rows[0][6].find_all("button")] == ["done", "todo"]
    assert [b.text() for b in rows[1][6].find_all("button")] == ["in-progress"]
    assert rows[2][6].text() == "" and rows[2][6].find_all("button") == []
    (link,) = rows[0][0].find_all("a")
    assert link.attrs["href"] == "/tasks/1" and link.text() == " Spaced "
    assert link.attrs["aria-label"] == " Spaced , number 1 on the task list"
    assert rows[1][0].find_all("a")[0].attrs["aria-label"] == "Spaced, number 2 on the task list"
    assert "Elsewhere" not in root.text() and "Bulk 123" in root.text()
    assert "no tasks yet" not in root.text()


def test_the_invitation_shows_only_when_the_list_is_empty_even_after_failed_adds(
    tmp_path: Path,
) -> None:
    """CP-126: the invitation replaces the list; a failed add leaves the project empty."""
    world = make_world(tmp_path)
    empty = parse(page(get(world.site, "/projects/1")))
    assert empty.find_all("table") == []
    assert (
        "This project has no tasks yet. Give the first task a title and press Add." in empty.text()
    )
    world.saver.failing = True
    add_task(world.site, title="Lost")
    still_empty = parse(page(get(world.site, "/projects/1")))
    assert still_empty.find_all("table") == []
    assert "Give the first task a title and press Add." in still_empty.text()
    world.saver.failing = False
    add_task(world.site, title="Kept")
    populated = parse(page(get(world.site, "/projects/1")))
    assert len(list_rows(populated)) == 1
    assert "no tasks yet" not in populated.text()


def test_renderer_preserves_supplied_row_order_and_overdue_flags() -> None:
    """CP-127, CP-131: the renderer decides no order and no overdue state; it shows what it gets."""
    early = a_task(1, "Early", due=date(2026, 1, 1))
    late = a_task(2, "Late", due=date(2027, 1, 1))
    undated = a_task(3, "Undated")
    rows = (TaskRow(undated, False), TaskRow(late, True), TaskRow(early, False))
    root = parse(pages.project_page(ALPHA, rows, (), priority_choices=pages.PRIORITY_CHOICES))
    shown = list_rows(root)
    assert [cells[0].text() for cells in shown] == ["Undated", "Late", "Early"]
    assert ["Overdue" in cells[5].text() for cells in shown] == [False, True, False]
    assert shown[1][5].text().startswith("2027-01-01") and shown[1][5].text().endswith("Overdue")


def test_the_page_builder_shows_no_sent_text_beside_a_too_long_title() -> None:
    """CP-118: whatever the builder is handed with the too-long outcome, the page holds none of it.

    The route already drops the fields; this holds the page to the same rule on its own, so the
    form opens at its opening values and the reason quotes nothing that was sent.
    """
    handed = pages.TaskForm(
        title="Leaked title",
        priority="critical",
        assignee="Dana",
        due_date="2026-01-01",
        refusal=pages.TaskRefusal.TOO_LONG,
    )
    shown_page = pages.project_page(ALPHA, (), ("Dana",), form=handed)
    for sent in ("Leaked title", "2026-01-01"):
        assert sent not in shown_page, sent
    root = parse(shown_page)
    assert control(root, "task-title").attrs.get("value") in (None, "")
    assert chosen(control(root, "task-priority")) == ["medium"]
    assert chosen(control(root, "task-assignee")) == [""]
    assert control(root, "task-due-date").attrs.get("value") in (None, "")
    title_field = control(root, "task-title")
    assert focused(root) == [title_field]
    (reason,) = title_field.described_by()
    assert reason.text() == "A task title can't be longer than 200 characters. Type a shorter one."


def test_task_page_shows_the_four_fields_in_the_one_authorized_form(tmp_path: Path) -> None:
    """CP-124, CP-144, CP-149, CP-150: title, priority, assignee and due date, one form, no more.

    The label area's Add form sits beside it as a separate form (CP-182, CP-199).
    """
    world = make_world(tmp_path)
    add_task(
        world.site, title=" Full ", priority="critical", assignee="Dana", due_date="2026-12-01"
    )
    add_task(world.site, title="Bare")
    root = parse(page(get(world.site, "/tasks/1")))
    assert [e.text() for e in root.find_all("title")] == [" Full  - tracker17"]
    (heading,) = root.find_all("h1")
    assert heading.text() == " Full "
    (main,) = root.find_all("main")
    assert [e.text() for e in main.find_all("dt")] == ["Project"]
    assert [e.text() for e in main.find_all("dd")] == ["Alpha"]
    bare = parse(page(get(world.site, "/tasks/2")))
    assert edit_values(bare) == {
        "title": "Bare",
        "priority": "medium",
        "assignee": "",
        "due_date": "",
        "shown_title": "Bare",
        "shown_priority": "medium",
        "shown_assignee": "",
        "shown_due_date": "",
    }
    for shown in (root, bare):
        (shown_main,) = shown.find_all("main")
        form = edit_form(shown)
        assert form.attrs["method"] == "post" and form.attrs["action"].startswith("/tasks/")
        assert [f.attrs["action"] for f in shown_main.find_all("form")] == [
            form.attrs["action"],
            f"{form.attrs['action']}/move",
            f"{form.attrs['action']}/labels",
            f"{form.attrs['action']}/comments",
        ]
        assert len(form.find_all("button")) == 1 and form.find_all("textarea") == []
        for tag in ("script", "table"):
            assert shown.find_all(tag) == [], tag
        text = shown_main.text().lower()
        for absent in ("overdue", "delete"):
            assert absent not in text, absent
        # CP-274: the one link the main area admits is the no-name notice's link to People.
        assert [a.attrs["href"] for a in shown_main.find_all("a")] == ["/people"]
    assert [a.attrs["href"] for a in root.find_all("header")[0].find_all("a")] == ["/", "/people"]


def test_the_task_page_shows_a_past_due_date_without_the_overdue_marker(tmp_path: Path) -> None:
    """The wording decision: the task page shows no marker, the list does."""
    world = make_world(tmp_path)
    add_task(world.site, title="Late one", due_date="2026-10-01")
    assert "Overdue" not in page(get(world.site, "/tasks/1"))
    assert "Overdue" in page(get(world.site, "/projects/1"))


def test_every_rendered_value_is_literal_text() -> None:
    """CP-133, QC-36: markup characters are shown once-escaped everywhere a value lands."""
    task = a_task(7, HOSTILE, assignee=HOSTILE, labels=(HOSTILE,), due=date(2026, 12, 1))
    project = Project(id=1, name=HOSTILE, description="")
    form = pages.TaskForm(title=HOSTILE, priority="high", assignee=HOSTILE, due_date=HOSTILE)
    built = {
        "list": pages.project_page(project, (TaskRow(task, True),), (HOSTILE,)),
        "retained": pages.project_page(
            project,
            (),
            (HOSTILE,),
            form=pages.TaskForm(
                title=HOSTILE,
                assignee=HOSTILE,
                due_date="2026-12-01",
                refusal=pages.TaskRefusal.ASSIGNEE_NOT_LISTED,
            ),
        ),
        "failed": pages.project_page(project, (), (HOSTILE,), form=_failed(form)),
        "task": pages.task_page(context_of(task, (HOSTILE,), project), added=True),
        "plain task": pages.task_page(context_of(task, (HOSTILE,), project)),
    }
    for name, shown_page in built.items():
        assert "<b>" not in shown_page, name
        assert '"quoted"' not in shown_page, name
    listed = parse(built["list"])
    cells = list_rows(listed)[0]
    assert cells[0].text() == HOSTILE and cells[3].text() == HOSTILE and HOSTILE in cells[4].text()
    assert cells[0].find_all("a")[0].attrs["aria-label"] == f"{HOSTILE}, number 1 on the task list"
    retained = parse(built["retained"])
    assert control(retained, "task-title").attrs["value"] == HOSTILE
    reason = control(retained, "task-assignee").described_by()[0]
    assert HOSTILE in reason.text() and reason.find_all("a")[0].text() == HOSTILE
    failure = the_add_form(parse(built["failed"])).described_by()[0]
    assert HOSTILE in failure.text()
    on_task = parse(built["task"])
    assert on_task.find_all("h1")[0].text() == HOSTILE
    assert on_task.find_all("h1")[0].described_by()[0].text() == f"You added '{HOSTILE}'."
    assert [e.text() for e in on_task.find_all("title")] == [f"{HOSTILE} - tracker17"]
    assert on_task.find_all("dd")[0].text() == HOSTILE
    for root in (listed, retained, on_task):
        assert [e for e in root.walk() if e.tag == "b"] == []


def _failed(form: pages.TaskForm) -> pages.TaskForm:
    return pages.TaskForm(
        title=form.title,
        priority=form.priority,
        assignee=form.assignee,
        due_date="2026-12-01",
        failed=True,
    )


def test_the_page_builders_need_no_world_to_show_an_empty_project() -> None:
    """The defaults: no rows, no people, the opening form, and the invitation."""
    root = parse(pages.project_page(ALPHA))
    assert "Give the first task a title and press Add." in root.text()
    assert chosen(control(root, "task-priority")) == ["medium"]


def test_task_page_opens_edit_form_from_saved_values(tmp_path: Path) -> None:
    """CP-144 to CP-146, CP-149, CP-150: one labelled Save form in every status, as saved."""
    statuses = ("todo", "in-progress", "done", "cancelled")
    tasks = [
        restore_task(
            index, 1, f" Task {status} ", status, "high", "Dana", [], "2026-10-20", CREATED, []
        )
        for index, status in enumerate(statuses, start=1)
    ]
    state = restore_state(
        [(1, "Alpha", "")], 2, ["Dana", " Ari"], tasks=tasks, next_task_id=len(tasks) + 1
    )
    saver = SwitchedSaver(SavedData(tmp_path / "data"))
    site = Site(Tracker(state, saver, MovableClock(NOON)), HOST)
    for index, status in enumerate(statuses, start=1):
        shown_page = page(get(site, f"/tasks/{index}"))
        assert page(get(site, f"/tasks/{index}")) == shown_page
        root = parse(shown_page)
        form = edit_form(root)
        assert form.attrs["action"] == f"/tasks/{index}" and form.attrs["method"] == "post"
        moves = {"todo": 1, "in-progress": 2, "done": 0, "cancelled": 0}[status]
        assert [f.attrs["action"] for f in root.find_all("form")] == [
            f"/tasks/{index}",
            *[f"/tasks/{index}/move"] * moves,
            f"/tasks/{index}/labels",
            f"/tasks/{index}/comments",
        ]
        assert focused(root) == []
        labels = labels_by_control(root)
        assert [
            labels[i] for i in ("edit-title", "edit-priority", "edit-assignee", "edit-due-date")
        ] == ["Title", "Priority", "Assignee", "Due date"]
        title = control(root, "edit-title")
        assert title.attrs["name"] == "title" and title.attrs["maxlength"] == str(SHORT_TEXT_MAX)
        assert title.attrs["value"] == f" Task {status} "
        priority = control(root, "edit-priority")
        assert offered(priority) == ["low", "medium", "high", "critical"]
        assert [o.text() for o in priority.find_all("option")] == offered(priority)
        assert chosen(priority) == ["high"]
        assignee = control(root, "edit-assignee")
        assert offered(assignee) == ["", "Dana", " Ari"] and chosen(assignee) == ["Dana"]
        assert [o.text() for o in assignee.find_all("option")] == ["unassigned", "Dana", " Ari"]
        due = control(root, "edit-due-date")
        assert due.attrs["type"] == "date" and due.attrs["value"] == "2026-10-20"
        assert [b.text() for b in form.find_all("button")] == ["Save"]
        hidden = {
            e.attrs["name"]: e.attrs["value"]
            for e in form.find_all("input")
            if e.attrs.get("type") == "hidden"
        }
        assert hidden == {
            "shown_title": f" Task {status} ",
            "shown_priority": "high",
            "shown_assignee": "Dana",
            "shown_due_date": "2026-10-20",
        }
        (main,) = root.find_all("main")
        # CP-274: only the no-name notice's link to People; no operator name is saved here.
        assert [a.attrs["href"] for a in main.find_all("a")] == ["/people"]
        assert main.find_all("script") == []
        assert [e.text() for e in main.find_all("dt")] == ["Project"]
        assert [e.text() for e in main.find_all("dd")] == ["Alpha"]


def test_task_page_shows_carried_unlisted_assignee(tmp_path: Path) -> None:
    """CP-147, CP-148: the carried name is chosen, with the notice beside the control."""
    carried = (" Gone <b>", "Gone")
    for name in carried:
        for people in ((), ("Dana",)):
            task = a_task(1, assignee=name)
            context = context_of(task, people)
            root = parse(pages.task_page(context))
            assignee = control(root, "edit-assignee")
            assert offered(assignee) == ["", *people, name] and chosen(assignee) == [name]
            notice = (
                f"The name '{name}' is no longer on the assignee list. Picking another assignee or "
                f"unassigned replaces it. After that, '{name}' can't be assigned to a task until "
                "it's added back on People."
            )
            (field,) = [e for e in root.find_all("div") if assignee in e.children]
            texts = [e for e in field.find_all("p") if e.text() == notice]
            assert len(texts) == 1 and all(o.text() != notice for o in assignee.find_all("option"))
            assert field.find_all("a") == [] and edit_values(root)["assignee"] == name
    for task in (a_task(1, assignee="Dana"), a_task(1)):
        root = parse(pages.task_page(context_of(task, ("Dana",))))
        assert "no longer on the assignee list" not in root.text()
        assert offered(control(root, "edit-assignee")) == ["", "Dana"]
    plain = parse(pages.task_page(context_of(a_task(1), ())))
    assert offered(control(plain, "edit-assignee")) == [""]
    assert chosen(control(plain, "edit-assignee")) == [""]


def test_task_edit_renders_every_operator_value_as_text() -> None:
    """CP-175, QC-36: visible and hidden values, names and outcomes are shown once-escaped."""
    project = Project(id=1, name=HOSTILE, description="")
    task = a_task(7, HOSTILE, assignee=HOSTILE, due=date(2026, 12, 1))
    context = context_of(task, (HOSTILE,), project)
    hostile = TaskFields(title=HOSTILE, priority="high", assignee=HOSTILE, due_date="2026-12-01")
    retained = pages.TaskEditForm(
        fields=hostile, shown=hostile, refusal=pages.TaskEditRefusal.ASSIGNEE_NOT_LISTED
    )
    built = {
        "plain": pages.task_page(context),
        "saved": pages.task_page(context, saved=True),
        "added": pages.task_page(context, added=True),
        "refused": pages.task_page(context, form=retained),
        "failed": pages.task_page(context, form=pages.TaskEditForm(hostile, hostile, None, True)),
        "unlisted": pages.task_page(context_of(task, ("Dana",), project)),
    }
    for name, shown_page in built.items():
        assert "<b>" not in shown_page, name
        assert '"quoted"' not in shown_page, name
        root = parse(shown_page)
        assert [e for e in root.walk() if e.tag == "b"] == [], name
        assert root.find_all("h1")[0].text() == HOSTILE, name
        assert edit_values(root)["title"] == HOSTILE and edit_values(root)["shown_title"] == HOSTILE
        assert [e.text() for e in root.find_all("dd")] == [HOSTILE], name
    saved = parse(built["saved"]).find_all("h1")[0].described_by()[0]
    assert saved.text() == f"You saved changes to '{HOSTILE}'."
    reason = control(parse(built["refused"]), "edit-assignee").described_by()[0]
    assert reason.text().startswith(f"The name '{HOSTILE}' is no longer on the assignee list")
    assert reason.find_all("a")[0].text() == HOSTILE
    failure = edit_form(parse(built["failed"])).described_by()[0]
    assert failure.text().startswith(f"The tracker couldn't save changes to '{HOSTILE}'")
    notice = [
        p for p in parse(built["unlisted"]).find_all("p") if "no longer on the assignee" in p.text()
    ]
    assert notice[0].text().startswith(f"The name '{HOSTILE}' is no longer")


@pytest.mark.parametrize("line", ["added", "saved"])
def test_task_edit_completion_line_is_not_shown_with_a_refusal_or_failure(line: str) -> None:
    """CP-156, CP-161, CP-168: a refused or failed outcome owns focus, so a completion line gives
    way, the added line (CP-115) as well as the saved one."""
    context = context_of(a_task(1, "Kept"), ())
    refused = pages.TaskEditForm(
        fields=TaskFields(title=""),
        shown=TaskFields(title="Kept"),
        refusal=pages.TaskEditRefusal.BLANK_TITLE,
    )
    root = parse(pages.task_page(context, form=refused, **{line: True}))
    assert "You saved changes" not in root.text() and "You added" not in root.text()
    assert focused(root) == [control(root, "edit-title")]
    assert [e.attrs.get("value") for e in root.find_all("input") if e.attrs["name"] == "title"] == [
        ""
    ]
    failed = pages.TaskEditForm(
        fields=TaskFields(title="Typed"), shown=TaskFields(title="Kept"), failed=True
    )
    root = parse(pages.task_page(context, form=failed, **{line: True}))
    assert "You saved changes" not in root.text() and "You added" not in root.text()
    assert focused(root) == [edit_form(root)]
