"""Integration tests of the project deletion requests through the real Site, application and
domain (layer 3).

Checks SRS FR-13 (deleting a project with its tasks and comments), FR-17 (counts and lists), FR-15
(identities are never reissued), FR-39 (the refusal words), NFR-3 (a failed save changes nothing),
NFR-4 (a submission from another site is refused), NFR-5 (typed text is shown as text), AC-12 and
the response policy of NFDR QC-63. Change spec rules CP-570 to CP-588 and the design's T8 to T13 are
the ones each test names. The real Site, Tracker and SavedData are used, with an injected Clock and a
saver that can be made to fail; no product name is patched.
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import parse_qs, urlencode

import pytest
from test_delete_pages import strips
from test_delete_project_pages import landing, sentence_for
from test_pages import parse
from test_routes import FORM, HOST, SAME_ORIGIN, get, header, page
from test_task_routes import World, add_task, location, make_world

from web import Response, Site

NOT_FOUND_PROJECT = "There's no project at this address"
NOT_FOUND_TASK = "There's no task at this address"
CHOICES = [
    ("filter_status", "todo"),
    ("filter_status", ""),
    ("filter_label", ""),
    ("sort_field", "title"),
    ("sort_field", ""),
    ("sort_direction", ""),
]


def press(
    world: World,
    project: int | str = 1,
    *,
    confirming: bool = False,
    pairs: list[tuple[str, str]] | None = None,
    headers: dict[str, str] | None = None,
) -> Response:
    """A press of Delete project (or of its confirming control), as the strip's form sends it."""
    target = f"/projects/{project}/delete" + ("/confirm" if confirming else "")
    body = urlencode(pairs or []).encode()
    return world.site.handle("POST", target, {**(headers or SAME_ORIGIN), **FORM}, body)


def two_projects(tmp_path: Path) -> World:
    """Alpha holds four tasks in all four statuses and comments; Beta holds one with a comment."""
    world = make_world(tmp_path, projects=("Alpha", "Beta"))
    world.tracker.set_operator_name("Lee")
    for number, path in enumerate(((), ("in-progress",), ("in-progress", "done"), ("cancelled",))):
        add_task(world.site, 1, title=f"Alpha task {number}")
        for step in path:
            world.tracker.move_task(number + 1, step)
        world.tracker.add_task_comment(number + 1, f"Alpha comment {number}")
        world.tracker.add_task_label(number + 1, "ui")
    add_task(world.site, 2, title="Beta task")
    world.tracker.add_task_comment(5, "Beta comment")
    return world


def heading_of(response: Response) -> str:
    root = parse(response.body.decode("utf-8"))
    return root.find_all("h1")[0].text()


def test_first_project_delete_press_redirects_without_saving(tmp_path: Path) -> None:
    """CP-570, CP-572, T8: 303 to the Tasks view with the confirmation marker and the filter and
    sort choices; nothing is saved; a forged target, name or count cannot choose anything."""
    world = two_projects(tmp_path)
    before, saves = world.bytes_on_disk(), world.saver.saves
    forged = [("project_id", "2"), ("name", "Forged"), ("count", "99"), ("deleted_project", "x")]
    response = press(world, pairs=[*CHOICES, *forged])
    target = location(response)
    path, _, query = target.partition("?")
    assert path == "/projects/1"
    assert query.startswith("project_delete_confirm&")
    carried = parse_qs(query.removeprefix("project_delete_confirm&"), keep_blank_values=True)
    assert carried == {
        "filter_status": ["todo", ""],
        "filter_label": [""],
        "sort_field": ["title", ""],
        "sort_direction": [""],
    }
    assert header(response, "Cache-Control") is None and header(response, "Clear-Site-Data") is None
    assert world.bytes_on_disk() == before and world.saver.saves == saves
    assert location(press(world)) == "/projects/1?project_delete_confirm"


def test_confirm_project_delete_saves_once_and_reports_current_outcome(tmp_path: Path) -> None:
    """CP-575, CP-576, T8: one save, 303 to Projects with the removed name and count read when it
    ran, the carried choices dropped from this different-page landing, and a reload changes nothing."""
    world = two_projects(tmp_path)
    opened = get(world.site, "/projects/1?project_delete_confirm")
    sentence = parse(opened.body.decode()).by_id("confirm-sentence")
    assert sentence is not None and sentence.text() == sentence_for("Alpha", 4)
    world.tracker.rename_project(1, "Alpha Two")
    add_task(world.site, 1, title="Late task")
    saves = world.saver.saves
    forged = [("project_id", "2"), ("name", "Forged"), ("count", "99")]
    response = press(world, confirming=True, pairs=[*CHOICES, *forged])
    assert location(response) == "/?deleted_project=Alpha+Two&deleted_project_tasks=5"
    assert world.saver.saves == saves + 1
    assert world.tracker.project(1) is None and world.tracker.project(2) is not None
    after, saves = world.bytes_on_disk(), world.saver.saves
    shown = get(world.site, location(response))
    assert shown.status == 200 and header(shown, "Cache-Control") == "no-store"
    first = shown.body
    assert get(world.site, location(response)).body == first
    assert world.bytes_on_disk() == after and world.saver.saves == saves
    assert "Alpha Two" not in parse(first.decode()).find_all("ul")[0].text()


def test_failed_project_delete_keeps_saved_and_visible_state(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """CP-578, T9: a failed save leaves the saved bytes and every project, task and comment page
    as they were; the terminal names the deletion and the error once; the failure page keeps the
    choices and says nothing of the exception."""
    world = two_projects(tmp_path)
    reads = ("/projects/1", "/projects/1/summary", "/tasks/1", "/tasks/2", "/tasks", "/")
    pages_before = {address: get(world.site, address).body for address in reads}
    before = world.bytes_on_disk()
    world.saver.failing = True
    response = press(world, confirming=True, pairs=CHOICES)
    target = location(response)
    path, _, query = target.partition("?")
    assert path == "/projects/1" and query.startswith("project_delete_failed&")
    assert parse_qs(query.removeprefix("project_delete_failed&"), keep_blank_values=True) == {
        "filter_status": ["todo", ""],
        "filter_label": [""],
        "sort_field": ["title", ""],
        "sort_direction": [""],
    }
    assert "PermissionError" not in target
    assert world.bytes_on_disk() == before
    assert {address: get(world.site, address).body for address in reads} == pages_before
    errors = capsys.readouterr().err.splitlines()
    assert errors == [
        "The tracker couldn't delete the project 'Alpha', and nothing was changed.",
        "PermissionError: the disk said no",
    ]
    failed = get(world.site, target)
    root = parse(page(failed))
    assert "Traceback" not in root.text() and "PermissionError" not in root.text()
    assert root.by_id("delete-project-failure") is not None
    (form,) = [f for f in root.find_all("form") if f.attrs["action"] == "/projects/1/delete"]
    kept = [
        (i.attrs["name"], i.attrs["value"]) for i in form.find_all("input") if i.attrs.get("name")
    ]
    assert kept == CHOICES


def test_deleted_project_and_children_disappear_from_every_read(tmp_path: Path) -> None:
    """CP-579, CP-580, T10: no list, count, filter or sort result holds the project or its tasks;
    the surviving project keeps its Summary and comments; every address of the project and of
    each task it held answers its 404 with no cache header, and no deleted comment shows anywhere."""
    world = two_projects(tmp_path)
    beta_summary = get(world.site, "/projects/2/summary").body
    beta_page = get(world.site, "/projects/2").body
    assert location(press(world, confirming=True)).startswith("/?deleted_project=Alpha")
    projects = parse(page(get(world.site, "/"))).find_all("ul")[0].text()
    assert "Alpha" not in projects and "Beta" in projects
    for address in ("/tasks", "/tasks?filter_status=todo", "/tasks?sort_field=title"):
        shown = page(get(world.site, address))
        assert "Alpha" not in shown and "Alpha task" not in shown, address
        assert "Beta task" in shown or "filter_status" in address, address
    assert "The tracker has 1 task." in page(get(world.site, "/tasks?sort_field=title"))
    assert get(world.site, "/projects/2/summary").body == beta_summary
    assert get(world.site, "/projects/2").body == beta_page
    task_ids = (1, 2, 3, 4)
    queries = ("", "?delete_confirm", "?move_task=1&move_confirm=cancelled", "?saved", "?x=1")
    for query in queries:
        for address in ("/projects/1", "/projects/1/summary"):
            shown = get(world.site, address + query)
            assert shown.status == 404 and header(shown, "Cache-Control") is None, address + query
            assert heading_of(shown) == NOT_FOUND_PROJECT
        for identifier in task_ids:
            shown = get(world.site, f"/tasks/{identifier}{query}")
            assert shown.status == 404 and header(shown, "Cache-Control") is None
            assert heading_of(shown) == NOT_FOUND_TASK
            assert "Alpha comment" not in shown.body.decode()
    for address in ("/projects/1?project_delete_confirm", "/projects/1?project_delete_failed"):
        shown = get(world.site, address)
        assert shown.status == 404 and header(shown, "Cache-Control") is None
    for never in (
        "/projects/99",
        "/projects/99?project_delete_confirm",
        "/tasks/99?delete_confirm",
    ):
        shown = get(world.site, never)
        assert shown.status == 404 and header(shown, "Cache-Control") is None, never
    for address in ("/", "/tasks", "/projects/2", "/projects/2/summary", "/tasks/5", "/people"):
        assert "Alpha comment" not in get(world.site, address).body.decode(), address


def submit_to_deleted_project(world: World, case: str) -> Response:
    forms = {
        "add-task": ("/projects/1/tasks", {"title": "Late"}),
        "rename": ("/projects/1/rename", {"name": "Renamed"}),
        "first-press": ("/projects/1/delete", {}),
        "confirm": ("/projects/1/delete/confirm", {}),
        "confirm-again": ("/projects/1/delete/confirm", {"name": "Alpha"}),
    }
    target, fields = forms[case]
    body = urlencode(fields).encode()
    return world.site.handle("POST", target, {**SAME_ORIGIN, **FORM}, body)


@pytest.mark.parametrize("case", ["add-task", "rename", "first-press", "confirm", "confirm-again"])
def test_deleted_project_submission_changes_nothing(tmp_path: Path, case: str) -> None:
    """CP-582, CP-587, CP-594, CP-595, CP-599, CP-602, T1, T4: a submission whose target is the
    deleted project saves nothing and is sent to the bare project address, which shows the 404
    with no Cache-Control. Each case deletes the project through its confirmation first."""
    world = two_projects(tmp_path)
    assert location(press(world, confirming=True)).startswith("/?deleted_project=")
    if case == "confirm-again":
        assert location(press(world, confirming=True)) == "/projects/1"
    before, saves = world.bytes_on_disk(), world.saver.saves
    projects_before = world.tracker.projects()
    survivor_before = world.tracker.project_tasks(2)
    response = submit_to_deleted_project(world, case)
    assert response.status == 303 and location(response) == "/projects/1"
    shown = get(world.site, "/projects/1")
    assert shown.status == 404 and heading_of(shown) == NOT_FOUND_PROJECT
    assert header(shown, "Cache-Control") is None
    assert world.bytes_on_disk() == before and world.saver.saves == saves
    assert world.tracker.projects() == projects_before
    assert world.tracker.project_tasks(2) == survivor_before


CHILD_CASES: dict[str, tuple[str, dict[str, str]]] = {
    "edit": ("/tasks/1", {"title": "", "priority": "bogus", "due_date": "nope"}),
    "add-label": ("/tasks/1/labels", {"label": ""}),
    "remove-label": ("/tasks/1/labels/remove", {"label": "never carried"}),
    "add-comment": ("/tasks/1/comments", {"text": ""}),
    "move": ("/tasks/1/move", {"status": "bogus", "place": "list"}),
    "open-cancellation": ("/tasks/1/move", {"status": "cancelled", "place": "task"}),
    "confirm-cancellation": ("/tasks/1/move/confirm", {"place": "all-tasks"}),
    "open-delete": ("/tasks/1/delete", {}),
    "confirm-delete": ("/tasks/1/delete/confirm", {}),
}


@pytest.mark.parametrize("case", sorted(CHILD_CASES))
def test_deleted_child_submission_changes_nothing(tmp_path: Path, case: str) -> None:
    """CP-582, CP-587, T12: after the parent is deleted through its confirmation, each submission
    for a task it held is sent to that task's address, which shows its 404, and saves nothing;
    the missing target wins over invalid submitted values."""
    world = two_projects(tmp_path)
    assert location(press(world, confirming=True)).startswith("/?deleted_project=")
    before, saves = world.bytes_on_disk(), world.saver.saves
    target, fields = CHILD_CASES[case]
    response = world.site.handle(
        "POST", target, {**SAME_ORIGIN, **FORM}, urlencode(fields).encode()
    )
    assert location(response) == "/tasks/1"
    shown = get(world.site, "/tasks/1")
    assert shown.status == 404 and heading_of(shown) == NOT_FOUND_TASK
    assert header(shown, "Cache-Control") is None
    assert world.bytes_on_disk() == before and world.saver.saves == saves


def test_project_delete_response_policy_matches_rendered_state(tmp_path: Path) -> None:
    """CP-583, CP-588, T13: a shown confirmation is 202; back-out, failure and the Projects
    completion are 200; every one carries no-store; a failure beats the confirmation at 200; an
    address with no deletion state keeps its policy; a missing target is 404 with no cache header
    whatever the query; and no response of either press or state carries Clear-Site-Data."""
    world = two_projects(tmp_path)
    expected = {
        "?project_delete_confirm": 202,
        "?project_delete_back": 200,
        "?project_delete_failed": 200,
        "?project_delete_failed&project_delete_confirm": 200,
        "?project_delete_confirm&project_delete_back": 202,
    }
    for query, status in expected.items():
        shown = get(world.site, f"/projects/1{query}")
        assert shown.status == status, query
        assert header(shown, "Cache-Control") == "no-store", query
        assert header(shown, "Clear-Site-Data") is None, query
        assert (len(strips(parse(shown.body.decode()))) == 1) == (status == 202), query
    for plain in ("/projects/1", "/projects/1?filter_status=todo", "/projects/1/summary", "/"):
        shown = get(world.site, plain)
        assert shown.status == 200 and header(shown, "Cache-Control") is None, plain
    opening = press(world)
    assert header(opening, "Clear-Site-Data") is None and header(opening, "Cache-Control") is None
    confirmed = press(world, confirming=True)
    assert (
        header(confirmed, "Clear-Site-Data") is None and header(confirmed, "Cache-Control") is None
    )
    done = get(world.site, location(confirmed))
    assert done.status == 200 and header(done, "Cache-Control") == "no-store"
    assert header(done, "Clear-Site-Data") is None
    for query in ("", "?project_delete_confirm", "?project_delete_back", "?project_delete_failed"):
        gone = get(world.site, f"/projects/1{query}")
        assert gone.status == 404 and header(gone, "Cache-Control") is None, query
        assert header(gone, "Clear-Site-Data") is None
    never = get(world.site, "/projects/777?project_delete_confirm")
    assert never.status == 404 and header(never, "Cache-Control") is None


@pytest.mark.parametrize("confirming", [False, True], ids=["first-press", "confirm"])
@pytest.mark.parametrize(
    "headers",
    [
        {"Host": HOST, "Sec-Fetch-Site": "cross-site"},
        {"Host": HOST, "Sec-Fetch-Site": "same-site"},
        {"Host": HOST, "Sec-Fetch-Site": "none"},
        {"Host": HOST},
        {"Host": "evil.example", "Sec-Fetch-Site": "same-origin"},
    ],
    ids=["cross-site", "same-site", "none", "no-mark", "foreign-host"],
)
def test_project_delete_submissions_require_same_origin_and_own_host(
    tmp_path: Path, confirming: bool, headers: dict[str, str]
) -> None:
    """CP-588, T13: each new route refuses a cross-site, same-site, none, absent or foreign-host
    request with 403 and leaves the saved bytes as they were."""
    world = two_projects(tmp_path)
    before, saves = world.bytes_on_disk(), world.saver.saves
    response = press(world, confirming=confirming, headers=headers)
    assert response.status == 403
    assert world.bytes_on_disk() == before and world.saver.saves == saves
    assert world.tracker.project(1) is not None


@pytest.mark.parametrize("suffix", ["/delete", "/delete/confirm"])
def test_get_on_project_delete_action_addresses_never_deletes(tmp_path: Path, suffix: str) -> None:
    """CP-575, T13: a GET on either action URL is not a submission; it saves nothing and gets the
    answer any unknown page gets."""
    world = two_projects(tmp_path)
    before, saves = world.bytes_on_disk(), world.saver.saves
    shown = get(world.site, f"/projects/1{suffix}")
    unknown = get(world.site, "/projects/1/no-such-page")
    assert (shown.status, shown.body) == (unknown.status, unknown.body)
    assert world.bytes_on_disk() == before and world.saver.saves == saves
    assert world.tracker.project(1) is not None


@pytest.mark.parametrize("confirming", [False, True], ids=["first-press", "confirm"])
def test_overlong_numeric_project_target_is_missing(tmp_path: Path, confirming: bool) -> None:
    """CP-582, T13: a project number more digits than any identity can have redirects to its bare
    address, which shows the project 404; nothing is saved and nothing crashes."""
    world = two_projects(tmp_path)
    before, saves = world.bytes_on_disk(), world.saver.saves
    digits = "9" * 5000
    response = press(world, digits, confirming=confirming)
    assert location(response) == f"/projects/{digits}"
    shown = get(world.site, location(response))
    assert shown.status == 404 and heading_of(shown) == NOT_FOUND_PROJECT
    assert world.bytes_on_disk() == before and world.saver.saves == saves


def test_the_landing_names_what_the_deletion_removed_when_the_project_was_empty(
    tmp_path: Path,
) -> None:
    """CP-576, T8: an empty project's confirmation lands with a zero count and the form for it."""
    world = make_world(tmp_path, projects=("Empty",))
    response = press(world, confirming=True)
    assert location(response) == "/?deleted_project=Empty&deleted_project_tasks=0"
    root = landing(world, "Empty", "0")
    assert "which had no tasks" in root.text()


def test_every_press_is_one_of_the_submission_routes() -> None:
    """QC-7, T13: both presses are SUBMISSION routes, so the origin check stands before them."""
    kinds = {route.pattern: route.kind for route in Site.ROUTES if route.method == "POST"}
    assert kinds["/projects/[0-9]+/delete"] == "submission"
    assert kinds["/projects/[0-9]+/delete/confirm"] == "submission"
