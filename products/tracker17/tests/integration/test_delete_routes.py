"""Integration tests of the deletion requests through the real Site, application and domain (layer 3).

Checks SRS FR-17 (deleting a task with its comments, never reissuing its identity), FR-39 (the
refusal words), NFR-3 (a failed save changes nothing), NFR-4 (a submission from another site is
refused), NFR-5 (typed text is shown as text) and AC-12. Change spec rules CP-529 to CP-545 and the
design's T6 to T11 are the ones each test names. The real Site, Tracker and SavedData are used, with
an injected Clock and a saver that can be made to fail; no product name is patched.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from urllib.parse import urlencode

import pytest
from test_delete_pages import FAILURE, TITLE, add_comments, press_delete, strips, task_root
from test_move_routes import world_with
from test_pages import Element, parse
from test_routes import FORM, SAME_ORIGIN, get, header, page
from test_summary_pages import groups, rows_of
from test_task_routes import World, focused, location, make_world

from application import TaskFields
from domain import TrackerState
from persistence import SavedData
from web import Response

PATTERN = "/tasks/{task}/delete/confirm"


def confirm(
    world: World, task: int | str = 1, body: bytes = b"", headers: dict[str, str] | None = None
) -> Response:
    """The confirming press of Delete task, as the strip's form sends it."""
    target = PATTERN.format(task=task)
    return world.site.handle("POST", target, {**(headers or SAME_ORIGIN), **FORM}, body)


def saved_state(world: World) -> TrackerState:
    state = SavedData(world.location).load()
    assert state is not None
    return state


def without_task(state: TrackerState, task_id: int) -> TrackerState:
    return replace(state, tasks=tuple(t for t in state.tasks if t.id != task_id))


def test_confirmed_delete_lands_on_its_unfiltered_project(tmp_path: Path) -> None:
    """CP-533, CP-534, T6: one save removes exactly the task and its comments, keeps both
    counters and every other value, and lands on the owning project with one line."""
    world = make_world(tmp_path, projects=("Alpha", "Beta"))
    world.tracker.add_task(1, TITLE, "high", "Dana", "2026-10-01")
    world.tracker.add_task(1, "Keep")
    world.tracker.add_task(2, "Elsewhere")
    add_comments(world, 3)
    world.tracker.add_task_label(1, "ui")
    expected = without_task(saved_state(world), 1)
    saves = world.saver.saves
    body = urlencode(
        {
            "title": "Elsewhere",
            "project_id": "2",
            "status": "done",
            "filter_status": "todo",
            "sort_field": "title",
            "place": "list",
        }
    ).encode()
    response = confirm(world, 1, body)
    assert location(response) == "/projects/1?deleted_task=Set+up+CI"
    assert world.saver.saves == saves + 1
    assert saved_state(world) == expected
    assert saved_state(world).next_task_id == 4
    assert world.tracker.task(1) is None
    landed = get(world.site, location(response))
    assert landed.status == 200 and header(landed, "Cache-Control") == "no-store"
    assert header(landed, "Clear-Site-Data") is None
    root = parse(page(landed))
    (heading,) = focused(root)
    assert heading.tag == "h1" and heading.text() == "Alpha"
    (line,) = heading.described_by()
    assert line.text() == "You deleted 'Set up CI'."
    assert len([e for e in root.walk() if "deleted" in e.text() and e.tag == "p"]) == 1
    assert "#" not in location(response)
    assert "Keep" in root.text() and TITLE not in root.find_all("table")[0].text()


def test_confirmation_uses_the_title_current_at_each_request(tmp_path: Path) -> None:
    """CP-530, CP-534: the sentence uses the title held at the GET; completion uses the task the
    POST returned; submitted values cannot choose the target or the success metadata."""
    world = world_with(tmp_path, title="First")
    world.tracker.edit_task(1, TaskFields(title="Second"), TaskFields(title="First"))
    opened = parse(page(get(world.site, location(press_delete(world)))))
    sentence = opened.by_id("confirm-sentence")
    assert sentence is not None and "Delete 'Second'?" in sentence.text()
    world.tracker.edit_task(1, TaskFields(title="Third"), TaskFields(title="Second"))
    forged = urlencode({"title": "Forged", "project_id": "9", "id": "2"}).encode()
    response = confirm(world, 1, forged)
    assert location(response) == "/projects/1?deleted_task=Third"


def test_last_task_delete_keeps_the_first_task_invitation(tmp_path: Path) -> None:
    """CP-534, CP-537, T6: the empty project keeps its invitation beneath the completion line."""
    world = world_with(tmp_path)
    root = parse(page(get(world.site, location(confirm(world)))))
    line = root.by_id("deleted-line")
    (invitation,) = [e for e in root.walk() if "no-tasks" in (e.attrs.get("class") or "")]
    assert line is not None and line.text() == f"You deleted '{TITLE}'."
    assert "This project has no tasks yet." in invitation.text()
    order = list(root.walk())
    assert order.index(line) < order.index(invitation)


def test_delete_completion_reads_never_repeat_the_action(tmp_path: Path) -> None:
    """T6: repeated GETs of the landing keep the same line, with no further save."""
    world = world_with(tmp_path)
    target = location(confirm(world))
    saves, stored = world.saver.saves, world.bytes_on_disk()
    first = page(get(world.site, target))
    for _ in range(3):
        assert page(get(world.site, target)) == first
    assert world.saver.saves == saves and world.bytes_on_disk() == stored


@pytest.mark.parametrize("title", ["<b>x</b>", "A&B", 'say "hi"', "it's", "Ünï—☃", "a%2Fb+c"])
def test_deletion_titles_are_text_in_every_outcome(tmp_path: Path, title: str) -> None:
    """CP-535, T8: the title survives query encoding and shows as text in the sentence, the
    completion and the failure; no typed markup becomes an element."""
    world = world_with(tmp_path, title=title)
    sentence = task_root(world, "?delete_confirm").by_id("confirm-sentence")
    assert sentence is not None and sentence.text() == f"Delete '{title}'? You can't undo this."
    world.saver.failing = True
    failed = confirm(world)
    assert location(failed) == "/tasks/1?delete_failed"
    shown = task_root(world, "?delete_failed")
    (line,) = [e for e in shown.walk() if e.attrs.get("id") == "delete-failure"]
    assert (
        line.text() == f"The tracker couldn't delete '{title}', and nothing was changed. Try again."
    )
    world.saver.failing = False
    done = parse(page(get(world.site, location(confirm(world)))))
    assert done.by_id("deleted-line").text() == f"You deleted '{title}'."  # type: ignore[union-attr]
    for root in (shown, done):
        assert root.find_all("b") == []


def test_failed_confirm_keeps_saved_bytes_and_current_pages(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """CP-536, T9: a save that fails before replacement leaves the file and every read as they
    were; the terminal names the deletion and the error; the redirect carries the marker alone."""
    world = world_with(tmp_path)
    add_comments(world, 2)
    before_bytes, before_state = world.bytes_on_disk(), saved_state(world)
    reads = (
        world.tracker.task(1),
        world.tracker.project_tasks(1),
        world.tracker.project_summary(1),
    )
    world.saver.failing = True
    response = confirm(world)
    assert location(response) == "/tasks/1?delete_failed"
    assert world.bytes_on_disk() == before_bytes and saved_state(world) == before_state
    assert reads == (
        world.tracker.task(1),
        world.tracker.project_tasks(1),
        world.tracker.project_summary(1),
    )
    errors = capsys.readouterr().err.splitlines()
    assert errors[0] == "The tracker couldn't delete 'Set up CI', and nothing was changed."
    assert errors[1] == "PermissionError: the disk said no"
    root = task_root(world, "?delete_failed")
    assert root.by_id("delete-failure") is not None
    assert "You deleted" not in root.text() and "Traceback" not in root.text()
    assert "PermissionError" not in location(response)
    listed = page(get(world.site, "/projects/1"))
    assert TITLE in listed
    (line,) = [e for e in root.walk() if e.attrs.get("id") == "delete-failure"]
    assert line.text() == FAILURE


def row_titles(root: Element) -> list[str]:
    tables = root.find_all("table")
    if not tables:
        return []
    (body,) = tables[0].find_all("tbody")
    return [row.find_all("td")[0].text() for row in body.find_all("tr")]


SPECS = [
    # (project, title, priority, assignee, due date, status)
    (1, "T1", "low", "Dana", "2026-10-01", "todo"),
    (1, "T2", "medium", "Cy", "", "in-progress"),
    (1, "T3", "high", "", "2026-12-01", "done"),
    (1, "T4", "critical", "Dana", "", "cancelled"),
    (2, "U1", "low", "", "2026-10-02", "todo"),
    (2, "U2", "high", "Cy", "", "todo"),
]
MOVES = {
    "todo": [],
    "in-progress": ["in-progress"],
    "done": ["in-progress", "done"],
    "cancelled": ["cancelled"],
}
TODAY = "2026-10-11"


def counts_for(live: list[tuple[int, str, str, str, str, str]], project: int) -> list[int]:
    mine = [spec for spec in live if spec[0] == project]
    statuses = [sum(1 for s in mine if s[5] == name) for name in STATUSES_IN_ORDER]
    priorities = [
        sum(1 for s in mine if s[2] == name) for name in ("low", "medium", "high", "critical")
    ]
    overdue = sum(1 for s in mine if s[4] and s[4] < TODAY)
    undated = sum(1 for s in mine if not s[4])
    return [len(mine), *statuses, *priorities, overdue, undated]


STATUSES_IN_ORDER = ["todo", "in-progress", "done", "cancelled"]


def test_deletion_disappears_from_every_list_and_summary_count(tmp_path: Path) -> None:
    """CP-537, T7: after each genuine deletion, both lists, a filtered and sorted result and the
    Summary hold exactly the survivors; reads never save; the last deletion leaves zero counts."""
    world = make_world(tmp_path, projects=("Alpha", "Beta"))
    world.tracker.add_assignee("Cy")
    for index, (project, title, priority, assignee, due, status) in enumerate(SPECS, start=1):
        world.tracker.add_task(project, title, priority, assignee, due)
        for step in MOVES[status]:
            world.tracker.move_task(index, step)
    world.tracker.remove_assignee("Cy")
    live = list(SPECS)
    for index in range(1, len(SPECS) + 1):
        assert location(confirm(world, index)).startswith("/projects/")
        live = [spec for spec in live if spec[1] != SPECS[index - 1][1]]
        stored = world.bytes_on_disk()
        for project in (1, 2):
            mine = [s for s in live if s[0] == project]
            shown = parse(page(get(world.site, f"/projects/{project}")))
            assert sorted(row_titles(shown)) == sorted(spec[1] for spec in mine)
            todo = sorted((s[1] for s in mine if s[5] == "todo"), reverse=True)
            filtered = parse(
                page(
                    get(
                        world.site,
                        f"/projects/{project}?filter_status=todo"
                        "&sort_field=title&sort_direction=descending",
                    )
                )
            )
            assert row_titles(filtered) == todo
            summary = world.tracker.project_summary(project)
            assert summary is not None
            flat = [
                summary.total,
                *(c.count for c in summary.status_counts),
                *(c.count for c in summary.priority_counts),
                summary.overdue,
                summary.no_due_date,
            ]
            assert flat == counts_for(live, project)
            page_counts = [
                int(count)
                for group in groups(parse(page(get(world.site, f"/projects/{project}/summary"))))
                for _, count in rows_of(group)
            ]
            assert page_counts[:11] == flat
        everything = parse(page(get(world.site, "/tasks")))
        assert sorted(row_titles(everything)) == sorted(spec[1] for spec in live)
        assert world.bytes_on_disk() == stored
    assert live == []
    assert world.tracker.project_summary(1).total == 0  # type: ignore[union-attr]


def held_world(tmp_path: Path, status: str = "todo") -> World:
    """Task 1 in the given status, carrying the label `ui`, with a saved operator name, beside a
    survivor: every refusal payload below is one this world would accept for task 1."""
    world = world_with(tmp_path, status)
    world.tracker.set_operator_name("Lee")
    world.tracker.add_task_label(1, "ui")
    world.tracker.add_task(1, "Survivor")
    return world


def stale_world(tmp_path: Path, status: str = "todo") -> tuple[World, bytes]:
    """A world whose task 1 was genuinely deleted, with the bytes saved right after."""
    world = held_world(tmp_path, status)
    assert location(confirm(world)).startswith("/projects/1?deleted_task=")
    return world, world.bytes_on_disk()


def assert_refused_as_missing(world: World, response: Response, stored: bytes) -> None:
    saves = world.saver.saves
    assert location(response) == "/tasks/1"
    assert world.bytes_on_disk() == stored
    missing = get(world.site, "/tasks/1")
    assert missing.status == 404 and header(missing, "Cache-Control") is None
    assert "There's no task at this address" in missing.body.decode()
    assert world.saver.saves == saves and world.bytes_on_disk() == stored


def send(world: World, path: str, body: dict[str, str]) -> Response:
    return world.site.handle("POST", path, {**SAME_ORIGIN, **FORM}, urlencode(body).encode())


def test_deleted_target_refuses_edit_without_saving(tmp_path: Path) -> None:
    """CP-540, CP-541, T10."""
    world, stored = stale_world(tmp_path)
    response = send(world, "/tasks/1", {"title": "New", "shown_title": TITLE})
    assert_refused_as_missing(world, response, stored)


def test_deleted_target_refuses_label_add_without_saving(tmp_path: Path) -> None:
    """CP-540, CP-541, T10."""
    world, stored = stale_world(tmp_path)
    assert_refused_as_missing(world, send(world, "/tasks/1/labels", {"label": "bug"}), stored)


def test_deleted_target_refuses_label_remove_without_saving(tmp_path: Path) -> None:
    """CP-540, CP-541, T10."""
    world, stored = stale_world(tmp_path)
    response = send(world, "/tasks/1/labels/remove", {"label": "ui"})
    assert_refused_as_missing(world, response, stored)


def test_deleted_target_refuses_comment_add_without_saving(tmp_path: Path) -> None:
    """CP-540, CP-541, T10."""
    world, stored = stale_world(tmp_path)
    assert_refused_as_missing(world, send(world, "/tasks/1/comments", {"text": "hi"}), stored)


@pytest.mark.parametrize(
    ("status", "targets"),
    [
        ("todo", ["in-progress", "cancelled"]),
        ("in-progress", ["done", "cancelled", "todo"]),
        # The workflow offers a done or cancelled task no move; any word sent is still refused.
        ("done", ["in-progress"]),
        ("cancelled", ["todo"]),
    ],
)
def test_deleted_target_refuses_each_ordinary_move_without_saving(
    tmp_path: Path, status: str, targets: list[str]
) -> None:
    """CP-540, CP-541, T10: every target word named from the task's former status."""
    for target in targets:
        (tmp_path / target).mkdir()
        world, stored = stale_world(tmp_path / target, status)
        response = send(world, "/tasks/1/move", {"status": target, "place": "task"})
        assert_refused_as_missing(world, response, stored)


def test_deleted_target_refuses_cancellation_first_press_without_saving(tmp_path: Path) -> None:
    """CP-540, CP-541, T10."""
    world, stored = stale_world(tmp_path)
    response = send(world, "/tasks/1/move", {"status": "cancelled", "place": "task"})
    assert_refused_as_missing(world, response, stored)


def test_deleted_target_refuses_cancellation_confirm_without_saving(tmp_path: Path) -> None:
    """CP-540, CP-541, T10."""
    world, stored = stale_world(tmp_path)
    assert_refused_as_missing(
        world, send(world, "/tasks/1/move/confirm", {"place": "task"}), stored
    )


def test_deleted_target_refuses_delete_first_press_without_saving(tmp_path: Path) -> None:
    """CP-540, CP-541, T10: a stale or repeated opening of the confirmation."""
    world, stored = stale_world(tmp_path)
    assert_refused_as_missing(world, press_delete(world), stored)


def test_deleted_target_refuses_delete_confirm_without_saving(tmp_path: Path) -> None:
    """CP-540, CP-541, T10: a stale or repeated confirmation, twice in a row."""
    world, stored = stale_world(tmp_path)
    assert_refused_as_missing(world, confirm(world), stored)
    assert_refused_as_missing(world, confirm(world), stored)


@pytest.mark.parametrize(
    ("status", "path", "body", "landing", "saves"),
    [
        ("todo", "/tasks/1", {"title": "New", "shown_title": TITLE}, "/tasks/1?saved", 1),
        ("todo", "/tasks/1/labels", {"label": "bug"}, "/tasks/1?label_added=bug", 1),
        ("todo", "/tasks/1/labels/remove", {"label": "ui"}, "/tasks/1?label_removed=ui", 1),
        ("todo", "/tasks/1/comments", {"text": "hi"}, "/tasks/1?comment_added=1", 1),
        ("todo", "/tasks/1/move", {"status": "in-progress", "place": "task"}, "moved=", 1),
        ("in-progress", "/tasks/1/move", {"status": "done", "place": "task"}, "moved=", 1),
        ("in-progress", "/tasks/1/move", {"status": "todo", "place": "task"}, "moved=", 1),
        ("todo", "/tasks/1/move", {"status": "cancelled", "place": "task"}, "move_confirm=", 0),
        ("todo", "/tasks/1/move/confirm", {"place": "task"}, "moved=cancelled", 1),
        ("todo", "/tasks/1/delete", {}, "/tasks/1?delete_confirm", 0),
        ("todo", "/tasks/1/delete/confirm", {}, "/projects/1?deleted_task=", 1),
    ],
)
def test_each_refused_payload_is_accepted_for_a_held_task(
    tmp_path: Path, status: str, path: str, body: dict[str, str], landing: str, saves: int
) -> None:
    """T10: the payloads the deleted-target tests send are whole and otherwise valid, so their
    refusal is the deleted target's and not the payload's: sent for the held task, each is accepted."""
    world = held_world(tmp_path, status)
    before = world.saver.saves
    where = location(send(world, path, body))
    assert landing in where and "refused=" not in where and "failed=" not in where, where
    assert world.saver.saves == before + saves


def test_a_deleted_identity_is_never_reissued(tmp_path: Path) -> None:
    """CP-539: the next added task takes an identity above every one issued before."""
    world, _ = stale_world(tmp_path)
    added = world.tracker.add_task(1, "Fresh")
    assert added.id == 3
    assert location(confirm(world, 3)).startswith("/projects/1")
    assert world.tracker.add_task(1, "Later").id == 4


@pytest.mark.parametrize(
    "query",
    [
        "",
        "?delete_confirm",
        "?delete_back",
        "?delete_failed",
        "?delete_confirm&delete_back&delete_failed",
        "?move_confirm=cancelled&move_task=1",
        "?saved&unknown=1&delete_confirm=1",
    ],
)
def test_missing_task_wins_over_every_query(tmp_path: Path, query: str) -> None:
    """CP-538, T11: a deleted task's address is the existing 404, with no cache header."""
    world, _ = stale_world(tmp_path)
    missing = get(world.site, f"/tasks/1{query}")
    assert missing.status == 404 and header(missing, "Cache-Control") is None
    assert "There's no task at this address" in missing.body.decode()
    assert header(missing, "Clear-Site-Data") is None


@pytest.mark.parametrize(
    "target", ["/tasks/99?delete_confirm", "/tasks/99?delete_back", "/tasks/99?delete_failed"]
)
def test_a_never_held_task_answers_the_same(tmp_path: Path, target: str) -> None:
    """CP-538: a task nothing ever held is the same existing answer."""
    world = world_with(tmp_path)
    missing = get(world.site, target)
    assert missing.status == 404 and header(missing, "Cache-Control") is None


def test_live_delete_views_have_their_response_policy(tmp_path: Path) -> None:
    """T11: confirmation, back-out, failure and the landing are 200 with no-store; neither POST
    bypasses the origin checks; no response clears site data."""
    world = world_with(tmp_path)
    for query in ("?delete_confirm", "?delete_back", "?delete_failed"):
        shown = get(world.site, f"/tasks/1{query}")
        assert shown.status == 200 and header(shown, "Cache-Control") == "no-store", query
        assert header(shown, "Clear-Site-Data") is None
    stored, saves = world.bytes_on_disk(), world.saver.saves
    for path in ("/tasks/1/delete", "/tasks/1/delete/confirm"):
        for marks in (
            {"Host": SAME_ORIGIN["Host"]},
            {**SAME_ORIGIN, "Sec-Fetch-Site": "cross-site"},
            {**SAME_ORIGIN, "Sec-Fetch-Site": "same-site"},
            {**SAME_ORIGIN, "Host": "evil.example:80"},
        ):
            refused = world.site.handle("POST", path, {**marks, **FORM}, b"")
            assert refused.status == 403 and refused.body == b"", (path, marks)
    assert world.bytes_on_disk() == stored and world.saver.saves == saves
    assert world.tracker.task(1) is not None
    opened = press_delete(world)
    assert header(opened, "Clear-Site-Data") is None
    landing = confirm(world)
    assert header(landing, "Clear-Site-Data") is None
    done = get(world.site, location(landing))
    assert done.status == 200 and header(done, "Cache-Control") == "no-store"
    assert header(done, "Clear-Site-Data") is None


def test_first_press_for_a_held_task_never_saves_and_a_get_never_deletes(tmp_path: Path) -> None:
    """Design § 3 C: the first press saves nothing, and neither new address deletes on a GET."""
    world = world_with(tmp_path)
    stored, saves = world.bytes_on_disk(), world.saver.saves
    assert location(press_delete(world)) == "/tasks/1?delete_confirm"
    for path in ("/tasks/1/delete", "/tasks/1/delete/confirm"):
        assert get(world.site, path).status == 404
    assert world.bytes_on_disk() == stored and world.saver.saves == saves
    assert focused(task_root(world, "?delete_confirm")) != []
    assert len(strips(task_root(world, "?delete_confirm"))) == 1


def test_a_task_identity_too_long_to_read_is_the_missing_task(tmp_path: Path) -> None:
    """CP-538, CP-540: the existing typed missing-task answer covers an unreadable identity."""
    world = world_with(tmp_path)
    digits = "9" * 5000
    for path in (f"/tasks/{digits}/delete", f"/tasks/{digits}/delete/confirm"):
        assert world.site.handle("POST", path, {**SAME_ORIGIN, **FORM}, b"").status == 404
