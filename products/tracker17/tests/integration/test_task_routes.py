"""Integration tests of web's task requests, run in one process with no socket (layer 3).

Checks SRS FR-15 (creating a task), FR-16 (editing a task's four fields), FR-36 (the list order),
FR-39 and FR-40 (refusals and the title maximum), NFR-4 (a request from another site is refused),
NFR-5 (typed text is shown as text), NFR-8 (a failed save leaves the state as it was) and DR-2 (the
Task entity). Change spec rules CP-113 to CP-125, CP-130, CP-131 and CP-140 (the add), CP-144 to
CP-171 (the edit) and NFDR QC-7, QC-8, QC-9, QC-31, QC-34, QC-35, QC-56 and QC-57 are the ones each
test names. The real Site, Tracker and SavedData are used, with an injected Clock and a saver that
can be made to fail; no product name is patched. The pages these requests answer with are checked
in tests/integration/test_task_pages.py.
"""

from __future__ import annotations

import os
import re
import time
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode

import pytest
from test_pages import Element, parse
from test_routes import FORM, HOST, SAME_ORIGIN, get, header, page

from application import SHORT_TEXT_MAX, Saver, TaskFields, Tracker, TrackerState
from domain import empty_state
from persistence import SavedData
from web import Response, Site, pages

NOON = datetime(2026, 10, 11, 12, 0, tzinfo=UTC)


@pytest.fixture
def utc_zone() -> Iterator[None]:
    """The machine-local date is the UTC date, so the clock's noon is the same day everywhere."""
    earlier = os.environ.get("TZ")
    os.environ["TZ"] = "UTC"
    time.tzset()
    yield
    if earlier is None:
        del os.environ["TZ"]
    else:
        os.environ["TZ"] = earlier
    time.tzset()


class MovableClock:
    def __init__(self, instant: datetime = NOON) -> None:
        self.instant = instant

    def now(self) -> datetime:
        return self.instant


class SwitchedSaver:
    """Saves through the real SavedData, or raises while switched to fail."""

    def __init__(self, inner: Saver) -> None:
        self.inner = inner
        self.failing = False
        self.saves = 0

    def save(self, state: TrackerState) -> None:
        if self.failing:
            raise PermissionError("the disk said no")
        self.inner.save(state)
        self.saves += 1


@dataclass
class World:
    site: Site
    tracker: Tracker
    saver: SwitchedSaver
    clock: MovableClock
    location: Path

    @property
    def saved_file(self) -> Path:
        return self.location / "tracker.json"

    def bytes_on_disk(self) -> bytes:
        return self.saved_file.read_bytes()

    def restarted(self) -> World:
        """A new tracker over the saved file, as the operator gets after a stop and a start."""
        state = SavedData(self.location).load()
        assert state is not None
        tracker = Tracker(state, self.saver, self.clock)
        return World(Site(tracker, HOST), tracker, self.saver, self.clock, self.location)


def make_world(
    tmp_path: Path,
    people: tuple[str, ...] = ("Dana", " Ari"),
    projects: tuple[str, ...] = ("Alpha",),
) -> World:
    location = tmp_path / "data"
    saver = SwitchedSaver(SavedData(location))
    clock = MovableClock()
    tracker = Tracker(empty_state(), saver, clock)
    for name in projects:
        tracker.create_project(name, "")
    for person in people:
        tracker.add_assignee(person)
    return World(Site(tracker, HOST), tracker, saver, clock, location)


def add_task(
    site: Site,
    project_id: int = 1,
    headers: dict[str, str] | None = None,
    body: bytes | None = None,
    **fields: str,
) -> Response:
    sent = urlencode(fields).encode("utf-8") if body is None else body
    target = f"/projects/{project_id}/tasks"
    return site.handle("POST", target, {**(headers or SAME_ORIGIN), **FORM}, sent)


def location(response: Response) -> str:
    assert response.status == 303
    return header(response, "Location") or ""


def follow(site: Site, response: Response) -> str:
    return page(get(site, location(response)))


def focused(root: Element) -> list[Element]:
    return [element for element in root.walk() if "autofocus" in element.attrs]


def control(root: Element, identifier: str) -> Element:
    found = root.by_id(identifier)
    assert found is not None, identifier
    return found


def chosen(select: Element) -> list[str | None]:
    """The values of the options marked selected."""
    return [o.attrs.get("value") for o in select.find_all("option") if "selected" in o.attrs]


def offered(select: Element) -> list[str | None]:
    return [o.attrs.get("value") for o in select.find_all("option")]


def form_values(root: Element) -> dict[str, str | None]:
    """What the add-task form would send as it stands: the four fields' current values."""
    selected_priority = chosen(control(root, "task-priority"))
    selected_assignee = chosen(control(root, "task-assignee"))
    return {
        "title": control(root, "task-title").attrs.get("value"),
        "priority": selected_priority[0] if selected_priority else None,
        "assignee": selected_assignee[0] if selected_assignee else None,
        "due_date": control(root, "task-due-date").attrs.get("value"),
    }


def tasks_of(tracker: Tracker, project_id: int = 1) -> list[str]:
    return [row.task.title for row in tracker.project_tasks(project_id)]


pytestmark = pytest.mark.usefixtures("utc_zone")


def test_add_all_fields_and_title_only_land_on_saved_task(tmp_path: Path) -> None:
    """CP-113, CP-114, CP-123, CP-124: a 303 to the task, its saved fields, and its quoted line."""
    world = make_world(tmp_path)
    full = add_task(
        world.site,
        title="  Write it  ",
        priority="high",
        assignee=" Ari",
        due_date="2026-12-01",
    )
    assert location(full) == "/tasks/1?added"
    only_title = add_task(world.site, title="Plain")
    assert location(only_title) == "/tasks/2?added"
    first, second = world.tracker.task(1), world.tracker.task(2)
    assert first is not None and second is not None
    assert (first.title, first.priority.value, first.assignee) == ("  Write it  ", "high", " Ari")
    assert str(first.due_date) == "2026-12-01"
    assert (second.priority.value, second.assignee, second.due_date) == ("medium", None, None)
    assert first.created_at == NOON and first.status.value == "todo"
    duplicate = add_task(world.site, title="  Write it  ")
    assert location(duplicate) == "/tasks/3?added"
    landing = parse(follow(world.site, full))
    (heading,) = [e for e in landing.find_all("h1")]
    assert heading.text() == "  Write it  "
    assert heading.attrs["tabindex"] == "-1" and "autofocus" in heading.attrs
    (line,) = heading.described_by()
    assert line.text() == "You added '  Write it  '."
    assert focused(landing) == [heading]
    plain = parse(page(get(world.site, "/tasks/1")))
    assert "You added" not in plain.text() and focused(plain) == []


def test_task_read_reload_and_history_never_save(tmp_path: Path) -> None:
    """CP-115, CP-125: both task GETs, repeated, and the project page leave state as it was."""
    world = make_world(tmp_path)
    add_task(world.site, title="Keep", priority="low")
    before = (world.bytes_on_disk(), world.saver.saves, world.tracker.task(1))
    for target in ("/tasks/1?added", "/tasks/1?added", "/tasks/1", "/projects/1", "/tasks/1?added"):
        assert get(world.site, target).status == 200
    assert (world.bytes_on_disk(), world.saver.saves, world.tracker.task(1)) == before
    assert world.tracker.task(2) is None


@pytest.mark.parametrize("title", ["", "   ", "\t\n", "　 "], ids=["empty", "ascii", "tab", "uni"])
def test_blank_title_retains_all_four_fields_and_focuses_title(tmp_path: Path, title: str) -> None:
    """CP-117, CP-118: the form comes back as sent, focus is on the title, nothing is saved."""
    world = make_world(tmp_path)
    before = world.bytes_on_disk()
    response = add_task(
        world.site, title=title, priority="high", assignee="Dana", due_date="2026-12-01"
    )
    shown = parse(follow(world.site, response))
    assert form_values(shown) == {
        "title": title,
        "priority": "high",
        "assignee": "Dana",
        "due_date": "2026-12-01",
    }
    title_field = control(shown, "task-title")
    assert focused(shown) == [title_field]
    (reason,) = title_field.described_by()
    assert reason.tag == "p" and reason.text() == "A task needs a title. Type one."
    assert world.bytes_on_disk() == before and world.tracker.task(1) is None
    assert location(add_task(world.site, title="Next")) == "/tasks/1?added"


@pytest.mark.parametrize(
    "sent", ["x" * 201, "\U0001f600" * 201, " " * 201], ids=["ascii", "emoji", "spaces"]
)
def test_too_long_title_exposes_no_submitted_fields(tmp_path: Path, sent: str) -> None:
    """CP-118, CP-140: 201 characters get the too-long reason with fresh defaults and no text."""
    world = make_world(tmp_path)
    before = world.bytes_on_disk()
    response = add_task(
        world.site, title=sent, priority="high", assignee="Dana", due_date="2026-12-01"
    )
    where = location(response)
    assert sent[:5] not in where and "Dana" not in where and "2026-12-01" not in where
    shown_page = follow(world.site, response)
    shown = parse(shown_page)
    assert form_values(shown) == {
        "title": "",
        "priority": "medium",
        "assignee": "",
        "due_date": "",
    }
    assert "2026-12-01" not in shown_page
    if sent.strip():
        assert sent[:5] not in shown_page
    title_field = control(shown, "task-title")
    assert focused(shown) == [title_field]
    (reason,) = title_field.described_by()
    assert reason.text() == "A task title can't be longer than 200 characters. Type a shorter one."
    crafted = page(
        get(world.site, where + "&title=Leaked&priority=critical&assignee=Dana&due_date=2026-01-01")
    )
    assert "Leaked" not in crafted and "2026-01-01" not in crafted
    crafted_root = parse(crafted)
    assert form_values(crafted_root)["priority"] == "medium"
    assert form_values(crafted_root)["assignee"] == ""
    assert world.bytes_on_disk() == before


def test_title_bound_accepts_200_code_points(tmp_path: Path) -> None:
    """CP-118: the maximum is counted in characters, so 200 non-BMP characters are saved."""
    world = make_world(tmp_path)
    exact = "\U0001f600" * SHORT_TEXT_MAX
    assert location(add_task(world.site, title=exact)) == "/tasks/1?added"
    assert world.tracker.task(1) is not None and world.tracker.task(1).title == exact  # type: ignore[union-attr]


def test_stale_assignee_rebuilds_choices_and_retains_other_fields(tmp_path: Path) -> None:
    """CP-119: a name removed after the form was read is refused; the rest of the form stays."""
    world = make_world(tmp_path)
    assert offered(control(parse(page(get(world.site, "/projects/1"))), "task-assignee")) == [
        "",
        "Dana",
        " Ari",
    ]
    world.tracker.remove_assignee("Dana")
    before = world.bytes_on_disk()
    response = add_task(
        world.site, title="Late", priority="critical", assignee="Dana", due_date="2026-11-02"
    )
    shown = parse(follow(world.site, response))
    assignee = control(shown, "task-assignee")
    assert focused(shown) == [assignee]
    assert offered(assignee) == ["", " Ari"] and chosen(assignee) == [""]
    (reason,) = assignee.described_by()
    assert reason.text().startswith("The name 'Dana' is no longer on the assignee list. Open '")
    (reload,) = reason.find_all("a")
    assert reload.attrs["href"] == "/projects/1" and reload.text() == "Alpha"
    assert reason.text().endswith("' again to reload the page.")
    values = form_values(shown)
    assert (values["title"], values["priority"], values["due_date"]) == (
        "Late",
        "critical",
        "2026-11-02",
    )
    assert world.bytes_on_disk() == before and world.tracker.task(1) is None
    assert get(world.site, "/projects/1").status == 200


def test_invalid_priority_and_date_focus_the_rejected_control(tmp_path: Path) -> None:
    """CP-120, CP-121: the reason sits on the rejected control; it resets, the rest is kept."""
    world = make_world(tmp_path)
    before = world.bytes_on_disk()
    bad_priority = parse(
        follow(
            world.site,
            add_task(
                world.site, title="T", priority="urgent", assignee="Dana", due_date="2026-12-01"
            ),
        )
    )
    priority = control(bad_priority, "task-priority")
    assert focused(bad_priority) == [priority] and chosen(priority) == ["medium"]
    (priority_reason,) = priority.described_by()
    assert priority_reason.text() == (
        "A task's priority has to be low, medium, high or critical. Pick one of the four."
    )
    kept = form_values(bad_priority)
    assert (kept["title"], kept["assignee"], kept["due_date"]) == ("T", "Dana", "2026-12-01")
    bad_date = parse(
        follow(
            world.site,
            add_task(
                world.site, title="T", priority="high", assignee="Dana", due_date="2026-02-30"
            ),
        )
    )
    due = control(bad_date, "task-due-date")
    assert focused(bad_date) == [due] and due.attrs.get("value") in (None, "")
    (date_reason,) = due.described_by()
    assert date_reason.text() == (
        "A due date has to be a calendar date. Pick one, or leave the due date empty."
    )
    kept = form_values(bad_date)
    assert (kept["title"], kept["priority"], kept["assignee"]) == ("T", "high", "Dana")
    assert world.bytes_on_disk() == before


@pytest.mark.parametrize(
    ("fields", "focus"),
    [
        ({"title": " ", "priority": "urgent", "due_date": "bad"}, "task-title"),
        (
            {"title": "T", "priority": "urgent", "assignee": "Zed", "due_date": "bad"},
            "task-priority",
        ),
        ({"title": "T", "assignee": "Zed", "due_date": "bad"}, "task-assignee"),
        ({"title": "T", "due_date": "bad"}, "task-due-date"),
    ],
    ids=["blank-first", "priority-before-assignee", "assignee-before-date", "date-last"],
)
def test_mixed_invalid_fields_follow_the_design_precedence(
    tmp_path: Path, fields: dict[str, str], focus: str
) -> None:
    """CP-117 to CP-121: the order project, length, blank, priority, assignee, date."""
    world = make_world(tmp_path)
    before = world.bytes_on_disk()
    shown = parse(follow(world.site, add_task(world.site, **fields)))
    assert [e.attrs.get("id") for e in focused(shown)] == [focus]
    assert world.bytes_on_disk() == before


def test_failed_add_retains_form_and_reports_one_failure(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """CP-122, NFR-8, QC-56: one console report, a described form, and the file as it was."""
    world = make_world(tmp_path)
    before = (world.bytes_on_disk(), world.tracker.project_tasks(1))
    world.saver.failing = True
    capsys.readouterr()
    response = add_task(
        world.site, title=" Lost ", priority="low", assignee=" Ari", due_date="2026-12-01"
    )
    err = capsys.readouterr().err
    assert err == (
        "The tracker couldn't add ' Lost ', and nothing was changed.\n"
        "PermissionError: the disk said no\n"
    )
    shown_page = follow(world.site, response)
    assert "PermissionError" not in shown_page and "the disk said no" not in shown_page
    shown = parse(shown_page)
    assert form_values(shown) == {
        "title": " Lost ",
        "priority": "low",
        "assignee": " Ari",
        "due_date": "2026-12-01",
    }
    (form,) = [e for e in shown.find_all("form") if e.attrs.get("action") == "/projects/1/tasks"]
    assert focused(shown) == [form] and form.attrs["tabindex"] == "-1"
    (failure,) = form.described_by()
    assert failure.text() == (
        "The tracker couldn't add ' Lost ', and nothing was changed. "
        "What you typed is still in the form. Try again."
    )
    assert (world.bytes_on_disk(), world.tracker.project_tasks(1)) == before
    world.saver.failing = False
    assert location(add_task(world.site, title="Again")) == "/tasks/1?added"
    assert capsys.readouterr().err == ""


@pytest.mark.parametrize("target", ["/tasks/99", "/tasks/0", "/tasks/" + "9" * 5000, "/tasks/00"])
def test_missing_task_addresses_get_the_task_not_found_page(tmp_path: Path, target: str) -> None:
    """CP-125: a task-shaped address with no task gets the task page; nothing is saved."""
    world = make_world(tmp_path)
    add_task(world.site, title="Only")
    before = (world.bytes_on_disk(), world.saver.saves)
    response = get(world.site, target)
    assert response.status == 404
    assert response.body == pages.task_not_found_page().encode("utf-8")
    assert (world.bytes_on_disk(), world.saver.saves) == before
    root = parse(response.body.decode("utf-8"))
    (main,) = root.find_all("main")
    assert [a.attrs["href"] for a in main.find_all("a")] == ["/"]
    assert [a.text() for a in main.find_all("a")] == ["Projects"]


@pytest.mark.parametrize(
    "target", ["/tasks/abc", "/tasks/", "/tasks", "/projects/1/tasks", "/tasks/1/x"]
)
def test_other_unknown_paths_keep_the_project_not_found_page(tmp_path: Path, target: str) -> None:
    """CP-125: only a task-shaped address gets the task wording."""
    world = make_world(tmp_path)
    add_task(world.site, title="Only")
    response = get(world.site, target)
    assert response.status == 404
    assert response.body == pages.not_found_page().encode("utf-8")


@pytest.mark.parametrize("project", ["99", "0", "9" * 5000])
def test_a_missing_project_post_gets_project_not_found_and_saves_nothing(
    tmp_path: Path, project: str
) -> None:
    """CP-113: an add to a project nobody holds changes nothing."""
    world = make_world(tmp_path)
    before = (world.bytes_on_disk(), world.saver.saves)
    response = add_task(world.site, project_id=project, title="Orphan")  # type: ignore[arg-type]
    assert response.status == 404
    assert response.body == pages.not_found_page().encode("utf-8")
    assert (world.bytes_on_disk(), world.saver.saves) == before


@pytest.mark.parametrize(
    "marks",
    [
        {"Host": HOST, "Sec-Fetch-Site": "cross-site"},
        {"Host": HOST, "Sec-Fetch-Site": "same-site"},
        {"Host": HOST, "Sec-Fetch-Site": "none"},
        {"Host": HOST},
        {"Host": "evil.example:8017", "Sec-Fetch-Site": "same-origin"},
    ],
    ids=["cross-site", "same-site", "none", "absent", "bad-host"],
)
def test_every_task_submission_passes_existing_origin_guard_first(
    tmp_path: Path, marks: dict[str, str]
) -> None:
    """NFR-4, QC-31: refused before the body is read, before any action, with nothing saved."""
    world = make_world(tmp_path)
    before = (world.bytes_on_disk(), world.saver.saves)
    for body in (b"title=Sneaky", b"title=%FF"):
        response = add_task(world.site, headers=marks, body=body)
        assert response.status == 403 and response.body == b""
    assert (world.bytes_on_disk(), world.saver.saves) == before
    assert location(add_task(world.site, title="Welcome")) == "/tasks/1?added"


@pytest.mark.parametrize(
    "body",
    [b"title=\xff\xfe", b"title=%FF", b"title=Alpha&assignee=%C3", b"title=%ED%A0%80"],
    ids=["raw", "percent", "cut-sequence", "surrogate"],
)
def test_task_form_uses_existing_strict_utf8_codec(tmp_path: Path, body: bytes) -> None:
    """QC-9: bytes that are not UTF-8 answer an empty 400 and save nothing."""
    world = make_world(tmp_path)
    before = (world.bytes_on_disk(), world.saver.saves)
    response = add_task(world.site, body=body)
    assert response.status == 400 and response.body == b""
    assert (world.bytes_on_disk(), world.saver.saves) == before


def test_task_form_normalizes_line_breaks_once(tmp_path: Path) -> None:
    """RT-10: CR LF and a lone CR are saved as LF before any rule applies."""
    world = make_world(tmp_path)
    add_task(world.site, body=b"title=a%0D%0Ab%0Dc%0Ad")
    task = world.tracker.task(1)
    assert task is not None and task.title == "a\nb\nc\nd"
    assert location(add_task(world.site, body=b"title=%0D%0A%0D")).startswith("/projects/1?")


def test_project_order_and_overdue_survive_restart(tmp_path: Path) -> None:
    """CP-130, CP-131: date then identity, flags from the injected day, same after a restart."""
    world = make_world(tmp_path)
    for title, due in [
        ("A undated", ""),
        ("B tomorrow", "2026-10-12"),
        ("C yesterday", "2026-10-10"),
        ("D yesterday too", "2026-10-10"),
        ("E today", "2026-10-11"),
    ]:
        add_task(world.site, title=title, due_date=due)

    def listing(world: World) -> list[tuple[str, bool]]:
        root = parse(page(get(world.site, "/projects/1")))
        (table,) = root.find_all("table")
        rows = table.find_all("tbody")[0].find_all("tr")
        return [
            (row.find_all("td")[0].text(), "Overdue" in row.find_all("td")[5].text())
            for row in rows
        ]

    expected = [
        ("C yesterday", True),
        ("D yesterday too", True),
        ("E today", False),
        ("B tomorrow", False),
        ("A undated", False),
    ]
    assert listing(world) == expected
    assert listing(world.restarted()) == expected
    world.clock.instant = NOON + timedelta(days=1)
    assert listing(world.restarted())[2:4] == [("E today", True), ("B tomorrow", False)]


# --- Editing a task's four fields (change spec rules CP-144 to CP-171) -------------------------

EDIT_FIELDS = ("title", "priority", "assignee", "due_date")
SEEDED = {"title": "Set up CI", "priority": "high", "assignee": "Dana", "due_date": "2026-10-20"}


def edit(
    site: Site,
    task_id: int | str = 1,
    headers: dict[str, str] | None = None,
    body: bytes | None = None,
    **fields: str,
) -> Response:
    sent = urlencode(fields).encode("utf-8") if body is None else body
    return site.handle("POST", f"/tasks/{task_id}", {**(headers or SAME_ORIGIN), **FORM}, sent)


def edit_form(root: Element) -> Element:
    """The one form that saves the four fields: its action is the task's own address, no deeper."""
    (form,) = [
        e for e in root.find_all("form") if re.fullmatch(r"/tasks/\d+", e.attrs.get("action", ""))
    ]
    return form


def edit_values(root: Element) -> dict[str, str]:
    """What the edit form would send as it stands: the four fields and the four shown values."""
    values: dict[str, str] = {}
    for element in edit_form(root).walk():
        name = element.attrs.get("name")
        if name is None:
            continue
        if element.tag == "input":
            values[name] = element.attrs.get("value") or ""
        elif element.tag == "select":
            picked = chosen(element) or offered(element)[:1]
            values[name] = picked[0] or ""
    return values


def loaded(site: Site, task_id: int | str = 1) -> dict[str, str]:
    return edit_values(parse(page(get(site, f"/tasks/{task_id}"))))


def seeded(tmp_path: Path, **kwargs: tuple[str, ...]) -> World:
    world = make_world(tmp_path, **kwargs)
    add_task(world.site, **SEEDED)
    return world


def task_fields(world: World, task_id: int = 1) -> dict[str, str | None]:
    task = world.tracker.task(task_id)
    assert task is not None
    return {
        "title": task.title,
        "priority": task.priority.value,
        "assignee": task.assignee,
        "due_date": None if task.due_date is None else task.due_date.isoformat(),
    }


def refused_page(world: World, response: Response) -> Element:
    assert "edit_refused=" in location(response)
    return parse(follow(world.site, response))


def reason_of(root: Element, field_id: str) -> str:
    """The one reason on the page, which must describe the one focused control."""
    control_ = control(root, field_id)
    assert focused(root) == [control_]
    (reason,) = control_.described_by()
    assert [e for e in edit_form(root).find_all("p") if "reason" in e.attrs.get("class", "")] == [
        reason
    ]
    return reason.text()


def test_task_edit_saves_all_fields_and_each_one_field(tmp_path: Path) -> None:
    """CP-151 to CP-153, CP-155: every changed value is saved exactly; each single change alone."""
    world = seeded(tmp_path)
    values = loaded(world.site)
    sent = {**values, "title": " Ship it ", "priority": "critical", "assignee": " Ari"}
    sent["due_date"] = "2026-11-01"
    saves = world.saver.saves
    response = edit(world.site, **sent)
    assert location(response) == "/tasks/1?saved"
    assert task_fields(world) == {
        "title": " Ship it ",
        "priority": "critical",
        "assignee": " Ari",
        "due_date": "2026-11-01",
    }
    assert world.saver.saves == saves + 1
    landing = parse(follow(world.site, response))
    assert edit_values(landing)["title"] == " Ship it "
    assert world.restarted().tracker.task(1) == world.tracker.task(1)
    for field, new in (
        ("title", "Only title"),
        ("priority", "low"),
        ("priority", "medium"),
        ("assignee", "Dana"),
        ("assignee", ""),
        ("due_date", "2028-02-29"),
        ("due_date", ""),
    ):
        before = task_fields(world)
        shown = loaded(world.site)
        assert location(edit(world.site, **{**shown, field: new})) == "/tasks/1?saved", field
        after = task_fields(world)
        assert after[field] == (new or None), (field, new)
        assert {k: v for k, v in after.items() if k != field} == {
            k: v for k, v in before.items() if k != field
        }, (field, new)


def test_task_edit_preserves_absent_and_empty_pairs(tmp_path: Path) -> None:
    """CP-151: an absent submitted or shown value is unchanged; a present empty one is a value."""
    world = seeded(tmp_path)
    before = (world.bytes_on_disk(), world.saver.saves)
    for body in (
        b"",
        b"title=Other",
        b"shown_title=Set+up+CI",
        b"priority=&assignee=&due_date=&title=",
        b"shown_priority=&shown_assignee=Other&shown_due_date=&shown_title=",
    ):
        assert location(edit(world.site, body=body)) == "/tasks/1", body
    assert (world.bytes_on_disk(), world.saver.saves) == before
    cleared = edit(
        world.site, body=b"assignee=&shown_assignee=Dana&due_date=&shown_due_date=2026-10-20"
    )
    assert location(cleared) == "/tasks/1?saved"
    assert task_fields(world)["assignee"] is None and task_fields(world)["due_date"] is None
    kept = (world.bytes_on_disk(), world.saver.saves)
    refused = edit(world.site, body=b"priority=&shown_priority=high")
    assert "edit_refused=invalid-priority" in location(refused)
    assert (world.bytes_on_disk(), world.saver.saves) == kept


def test_task_edit_normalizes_both_field_sets(tmp_path: Path) -> None:
    """CP-151, RT-10: line breaks are normalized in both sets, and nothing else is."""
    world = seeded(tmp_path)
    before = (world.bytes_on_disk(), world.saver.saves)
    same = edit(world.site, body=b"title=a%0D%0Ab%0Dc&shown_title=a%0Ab%0Ac")
    assert location(same) == "/tasks/1" and (world.bytes_on_disk(), world.saver.saves) == before
    changed = edit(world.site, body=b"title=x%0D%0Ay&shown_title=x")
    assert location(changed) == "/tasks/1?saved" and task_fields(world)["title"] == "x\ny"
    trimmed = edit(world.site, body=b"title=x+&shown_title=x")
    assert location(trimmed) == "/tasks/1?saved" and task_fields(world)["title"] == "x "
    before = (world.bytes_on_disk(), world.saver.saves)
    for shown_breaks in (b"title=p%0Aq&shown_title=p%0D%0Aq", b"title=p%0Aq&shown_title=p%0Dq"):
        unchanged = edit(world.site, body=shown_breaks)
        assert location(unchanged) == "/tasks/1", shown_breaks
        assert (world.bytes_on_disk(), world.saver.saves) == before, shown_breaks
    cased = edit(world.site, body=b"priority=HIGH&shown_priority=high")
    assert "edit_refused=invalid-priority" in location(cased)


def test_task_edit_no_change_has_no_save_or_completion(tmp_path: Path) -> None:
    """CP-155 to CP-157: a no-change save is a plain redirect; changed-to-current saves once."""
    world = seeded(tmp_path)
    before = (world.bytes_on_disk(), world.saver.saves)
    unchanged = edit(world.site, **loaded(world.site))
    assert location(unchanged) == "/tasks/1"
    assert (world.bytes_on_disk(), world.saver.saves) == before
    plain = parse(follow(world.site, unchanged))
    assert "You saved changes" not in plain.text() and focused(plain) == []
    stale = loaded(world.site)
    world.tracker.edit_task(1, TaskFields(title="Elsewhere"), TaskFields(title="Set up CI"))
    saves = world.saver.saves
    to_current = edit(world.site, **{**stale, "title": "Elsewhere"})
    assert location(to_current) == "/tasks/1?saved" and world.saver.saves == saves + 1
    heading = parse(follow(world.site, to_current)).find_all("h1")[0]
    assert heading.described_by()[0].text() == "You saved changes to 'Elsewhere'."


def test_task_edit_stale_form_replaces_changed_values(tmp_path: Path) -> None:
    """CP-152, CP-154: the comparison is with the form's own values, so a stale edit replaces."""
    world = seeded(tmp_path)
    first_tab = loaded(world.site)
    edit(world.site, **{**loaded(world.site), "title": "Second tab"})
    assert location(edit(world.site, **{**first_tab, "title": "First tab"})) == "/tasks/1?saved"
    assert task_fields(world)["title"] == "First tab"
    edit(world.site, **{**loaded(world.site), "priority": "low"})
    tab = loaded(world.site)
    edit(world.site, **{**loaded(world.site), "priority": "high"})
    assert location(edit(world.site, **{**tab, "priority": "medium"})) == "/tasks/1?saved"
    assert task_fields(world)["priority"] == "medium"
    tab = loaded(world.site)
    edit(world.site, **{**loaded(world.site), "priority": "critical"})
    edit(world.site, **{**tab, "title": "Title only"})
    assert task_fields(world)["title"] == "Title only"
    assert task_fields(world)["priority"] == "critical"


def test_task_edit_keeps_then_replaces_unlisted_assignee(tmp_path: Path) -> None:
    """CP-158, CP-159: a left-the-list name is kept until replaced, and then cannot be set."""
    kept_world = seeded(tmp_path / "kept")
    kept_world.tracker.remove_assignee("Dana")
    kept = edit(kept_world.site, **{**loaded(kept_world.site), "title": "Kept"})
    assert location(kept) == "/tasks/1?saved" and task_fields(kept_world)["assignee"] == "Dana"
    for index, replacement in enumerate((" Ari", "")):
        world = seeded(tmp_path / f"replaced{index}")
        world.tracker.remove_assignee("Dana")
        before = parse(page(get(world.site, "/tasks/1")))
        assert "no longer on the assignee list" in before.text()
        replaced = edit(world.site, **{**loaded(world.site), "assignee": replacement})
        assert location(replaced) == "/tasks/1?saved"
        assert task_fields(world)["assignee"] == (replacement or None)
        after = parse(page(get(world.site, "/tasks/1")))
        assert "Dana" not in offered(control(after, "edit-assignee"))
        assert "no longer on the assignee list" not in after.text()
        crafted = edit(world.site, assignee="Dana", shown_assignee=replacement)
        assert "edit_refused=assignee-not-listed" in location(crafted)
        assert task_fields(world)["assignee"] == (replacement or None)


def test_task_edit_rejects_assignee_removed_after_load(tmp_path: Path) -> None:
    """CP-163: the stale reason names the page as out of date and links to the task."""
    world = seeded(tmp_path)
    form = loaded(world.site)
    world.tracker.remove_assignee(" Ari")
    before = world.bytes_on_disk()
    response = edit(world.site, **{**form, "assignee": " Ari", "title": "Typed", "priority": "low"})
    shown = refused_page(world, response)
    assert reason_of(shown, "edit-assignee") == (
        "The name ' Ari' is no longer on the assignee list, so this page is out of date. "
        "Open 'Set up CI' again to reload the page."
    )
    (reload,) = control(shown, "edit-assignee").described_by()[0].find_all("a")
    assert reload.attrs["href"] == "/tasks/1" and reload.text() == "Set up CI"
    values = edit_values(shown)
    assert (values["title"], values["priority"], values["due_date"]) == (
        "Typed",
        "low",
        "2026-10-20",
    )
    assert world.bytes_on_disk() == before


def test_task_edit_blank_title_refusal_keeps_all_entered_values(tmp_path: Path) -> None:
    """CP-160, CP-161: nothing is saved, focus and the reason are on the title, both sets stay."""
    world = seeded(tmp_path)
    before = (world.bytes_on_disk(), world.saver.saves)
    form = loaded(world.site)
    response = edit(
        world.site, **{**form, "title": " \t", "priority": "low", "due_date": "2026-12-01"}
    )
    shown = refused_page(world, response)
    assert reason_of(shown, "edit-title") == "A task needs a title. Type one."
    assert edit_values(shown) == {
        **form,
        "title": " \t",
        "priority": "low",
        "due_date": "2026-12-01",
    }
    assert (world.bytes_on_disk(), world.saver.saves) == before


@pytest.mark.parametrize("sent", ["x" * 201, " " * 201], ids=["characters", "spaces"])
def test_task_edit_too_long_discards_all_submission_text(tmp_path: Path, sent: str) -> None:
    """CP-162: the page and its address hold no sent text; the form opens from saved values."""
    world = seeded(tmp_path)
    before = world.bytes_on_disk()
    response = edit(
        world.site,
        title=sent,
        shown_title="ZSHOWN",
        priority="low",
        shown_priority="critical",
        assignee=" Ari",
        shown_assignee="Dana",
        due_date="2027-01-01",
        shown_due_date="2026-10-20",
    )
    where = location(response)
    for leaked in ("ZSHOWN", "2027-01-01", "Ari", "critical", "x" * 5):
        assert leaked not in where, leaked
    shown_page = follow(world.site, response)
    assert "ZSHOWN" not in shown_page and "2027-01-01" not in shown_page
    root = parse(shown_page)
    assert reason_of(root, "edit-title") == (
        "A task title can't be longer than 200 characters. Type a shorter one."
    )
    assert edit_values(root) == {**SEEDED, **{f"shown_{k}": v for k, v in SEEDED.items()}}
    assert world.bytes_on_disk() == before
    again = parse(page(get(world.site, where + "&title=Leak&shown_title=Leak")))
    assert "Leak" not in again.text() and edit_values(again)["title"] == "Set up CI"
    world.tracker.edit_task(1, TaskFields(priority="critical"), TaskFields(priority="high"))
    retry = edit(world.site, **{**edit_values(root), "title": "Retried"})
    assert location(retry) == "/tasks/1?saved"
    assert task_fields(world)["title"] == "Retried"
    assert task_fields(world)["priority"] == "critical"


def test_task_edit_invalid_priority_refusal_changes_nothing(tmp_path: Path) -> None:
    """CP-164: a hand-built priority is refused beside the priority control."""
    world = seeded(tmp_path)
    before = (world.bytes_on_disk(), world.saver.saves)
    response = edit(world.site, **{**loaded(world.site), "priority": "urgent", "title": "Moved"})
    shown = refused_page(world, response)
    assert reason_of(shown, "edit-priority") == (
        "A task's priority has to be low, medium, high or critical. Pick one of the four."
    )
    assert edit_values(shown)["title"] == "Moved"
    assert (world.bytes_on_disk(), world.saver.saves) == before


def test_task_edit_invalid_due_date_refusal_changes_nothing(tmp_path: Path) -> None:
    """CP-164: a hand-built date is refused beside the date field."""
    world = seeded(tmp_path)
    before = (world.bytes_on_disk(), world.saver.saves)
    response = edit(
        world.site, **{**loaded(world.site), "due_date": "2026-02-30", "title": "Moved"}
    )
    shown = refused_page(world, response)
    assert reason_of(shown, "edit-due-date") == (
        "A due date has to be a calendar date. Give one, or leave the due date empty."
    )
    assert edit_values(shown)["due_date"] == "2026-02-30"
    assert (world.bytes_on_disk(), world.saver.saves) == before


@pytest.mark.parametrize(
    ("changes", "focus"),
    [
        (
            {"title": "x" * 201, "priority": "no", "assignee": "Nobody", "due_date": "no"},
            "edit-title",
        ),
        ({"title": " ", "priority": "no", "assignee": "Nobody", "due_date": "no"}, "edit-title"),
        ({"priority": "no", "assignee": "Nobody", "due_date": "no"}, "edit-priority"),
        ({"assignee": "Nobody", "due_date": "no"}, "edit-assignee"),
        ({"due_date": "no"}, "edit-due-date"),
    ],
    ids=["too-long", "blank", "priority", "assignee", "date"],
)
def test_task_edit_multiple_refusals_show_only_first_reason(
    tmp_path: Path, changes: dict[str, str], focus: str
) -> None:
    """CP-165: one reason, for the first refused field in the explicit order; nothing is saved."""
    world = seeded(tmp_path)
    before = (world.bytes_on_disk(), world.saver.saves)
    shown = refused_page(world, edit(world.site, **{**loaded(world.site), **changes}))
    reason_of(shown, focus)
    assert (world.bytes_on_disk(), world.saver.saves) == before


@pytest.mark.parametrize("target", ["99", "0", "9" * 5000])
def test_task_edit_missing_identity_uses_task_not_found(tmp_path: Path, target: str) -> None:
    """CP-167: no task at the address saves nothing and shows the task not-found page."""
    world = seeded(tmp_path)
    before = (world.bytes_on_disk(), world.saver.saves)
    response = edit(world.site, target, title="Ghost", shown_title="")
    if response.status == 303:
        assert location(response) == f"/tasks/{target}"
        response = get(world.site, location(response))
    assert response.status == 404
    assert response.body == pages.task_not_found_page().encode("utf-8")
    assert (world.bytes_on_disk(), world.saver.saves) == before


def test_task_edit_retry_keeps_original_baseline(tmp_path: Path) -> None:
    """CP-166: after a retaining outcome the next save compares with the original form."""
    world = seeded(tmp_path)

    def other_tab_assigns_ari() -> None:
        world.tracker.edit_task(1, TaskFields(assignee=" Ari"), TaskFields(assignee="Dana"))

    first = edit(world.site, **{**loaded(world.site), "title": "", "priority": "low"})
    shown = refused_page(world, first)
    other_tab_assigns_ari()
    retry = edit(world.site, **{**edit_values(shown), "title": "Fixed"})
    assert location(retry) == "/tasks/1?saved"
    assert task_fields(world) == {**SEEDED, "title": "Fixed", "priority": "low", "assignee": " Ari"}
    world.tracker.edit_task(1, TaskFields(assignee="Dana"), TaskFields(assignee=" Ari"))
    refused = edit(world.site, **{**loaded(world.site), "due_date": "nope", "priority": "medium"})
    shown = refused_page(world, refused)
    world.tracker.edit_task(1, TaskFields(title="Tab"), TaskFields(title="Fixed"))
    retry = edit(world.site, **{**edit_values(shown), "due_date": "2026-12-24"})
    assert task_fields(world) == {
        **SEEDED,
        "title": "Tab",
        "priority": "medium",
        "due_date": "2026-12-24",
    }
    hand_built = edit(world.site, body=b"title=&shown_title=Tab&priority=low")
    shown = refused_page(world, hand_built)
    values = edit_values(shown)
    assert "shown_priority" not in values and values["shown_title"] == "Tab"
    assert "shown_priority" not in location(hand_built)


@pytest.mark.parametrize("outcome", ["refused", "failed"])
def test_task_edit_retry_keeps_a_field_the_request_did_not_send(
    tmp_path: Path, outcome: str
) -> None:
    """CP-166: a field the request showed but did not send was never changed, so the retry keeps
    whatever is saved when it is applied, through a refusal and through a failed save alike."""
    world = seeded(tmp_path)
    world.tracker.edit_task(1, TaskFields(priority="medium"), TaskFields(priority="high"))
    typed = b"" if outcome == "refused" else b"Lost"
    world.saver.failing = outcome == "failed"
    first = edit(world.site, body=b"title=" + typed + b"&shown_title=Set+up+CI&shown_priority=high")
    assert f"edit_{outcome}=" in location(first)
    world.saver.failing = False
    retained = parse(follow(world.site, first))
    world.tracker.edit_task(1, TaskFields(priority="critical"), TaskFields(priority="medium"))
    retry = edit(world.site, **{**edit_values(retained), "title": "Fixed"})
    assert location(retry) == "/tasks/1?saved"
    assert task_fields(world) == {**SEEDED, "title": "Fixed", "priority": "critical"}


def test_task_edit_failed_save_retains_form_without_python_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """CP-168: nothing changes, the form keeps both sets, the console names action then error."""
    world = seeded(tmp_path)
    form = loaded(world.site)
    before = (world.bytes_on_disk(), task_fields(world))
    world.saver.failing = True
    capsys.readouterr()
    response = edit(world.site, **{**form, "title": "Lost", "priority": "low"})
    assert "edit_failed=" in location(response)
    assert capsys.readouterr().err.splitlines() == [
        "The tracker couldn't save changes to 'Set up CI', and nothing was changed.",
        "PermissionError: the disk said no",
    ]
    shown_page = follow(world.site, response)
    for leaked in ("PermissionError", "disk said no", "Traceback"):
        assert leaked not in shown_page and leaked not in location(response), leaked
    root = parse(shown_page)
    form_element = edit_form(root)
    assert focused(root) == [form_element] and form_element.attrs["tabindex"] == "-1"
    (failure,) = form_element.described_by()
    assert failure.text() == (
        "The tracker couldn't save changes to 'Set up CI', and nothing was changed. "
        "What you typed is still in the form. Try again."
    )
    assert edit_values(root) == {**form, "title": "Lost", "priority": "low"}
    assert (world.bytes_on_disk(), task_fields(world)) == before
    world.saver.failing = False
    assert location(edit(world.site, **edit_values(root))) == "/tasks/1?saved"
    assert task_fields(world)["title"] == "Lost" and task_fields(world)["priority"] == "low"


@pytest.mark.parametrize(
    "marks",
    [
        {"Host": HOST, "Sec-Fetch-Site": "cross-site"},
        {"Host": HOST, "Sec-Fetch-Site": "same-site"},
        {"Host": HOST, "Sec-Fetch-Site": "none"},
        {"Host": HOST},
        {"Host": "evil.example:8017", "Sec-Fetch-Site": "same-origin"},
    ],
    ids=["cross-site", "same-site", "none", "absent", "bad-host"],
)
def test_task_edit_origin_gate_prevents_all_actions(tmp_path: Path, marks: dict[str, str]) -> None:
    """CP-169: refused before any action, with the saver untouched and the bytes the same."""
    world = seeded(tmp_path)
    before = (world.bytes_on_disk(), world.saver.saves)
    response = edit(world.site, headers=marks, title="Sneaky", shown_title="Set up CI")
    assert response.status == 403 and response.body == b""
    assert (world.bytes_on_disk(), world.saver.saves) == before


def test_task_edit_completion_describes_heading_after_save(tmp_path: Path) -> None:
    """CP-155, CP-156: one completion line, described from a focused heading, never saved again."""
    world = seeded(tmp_path)
    response = edit(world.site, **{**loaded(world.site), "title": "  New  "})
    root = parse(follow(world.site, response))
    (heading,) = root.find_all("h1")
    assert heading.text() == "  New  "
    assert focused(root) == [heading] and heading.attrs["tabindex"] == "-1"
    (line,) = heading.described_by()
    assert line.text() == "You saved changes to '  New  '."
    before = (world.bytes_on_disk(), world.saver.saves)
    for target in (location(response), location(response), "/tasks/1"):
        get(world.site, target)
    assert (world.bytes_on_disk(), world.saver.saves) == before
    plain = parse(page(get(world.site, "/tasks/1")))
    assert "You saved changes" not in plain.text() and focused(plain) == []
    added = parse(page(get(world.site, "/tasks/1?added")))
    assert added.find_all("h1")[0].described_by()[0].text() == "You added '  New  '."


@pytest.mark.parametrize(
    "query",
    [
        "?edit_refused=bogus&title=Leak&shown_title=Leak",
        "?edit_failed=other&title=Leak&shown_title=Leak",
        "?title=Leak&shown_title=Leak&priority=low",
        "?edit_refused=too-long&title=Leak&shown_title=Leak",
    ],
)
def test_task_edit_ignores_unrecognized_outcome_query(tmp_path: Path, query: str) -> None:
    """RT-8: only a recognized retaining outcome rebuilds a retained form; nothing saves."""
    world = seeded(tmp_path)
    before = (world.bytes_on_disk(), world.saver.saves)
    shown_page = page(get(world.site, "/tasks/1" + query))
    assert "Leak" not in shown_page
    root = parse(shown_page)
    assert edit_values(root)["title"] == "Set up CI"
    assert (world.bytes_on_disk(), world.saver.saves) == before
