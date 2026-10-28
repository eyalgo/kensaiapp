"""Integration tests of the task page's deletion control and its confirmation (layer 3).

Checks SRS FR-17 (deleting a task with its comments), FR-39 (the refusal and failure words), NFR-3
(a failed save changes nothing), NFR-5 (typed text is shown as text) and AC-12 (what a move or a
delete leaves on the page). Change spec rules CP-529 to CP-532, CP-534 and CP-536, and the design's
T4 and T12, are the ones each test names. Where a test checks words they are the strings of this
change's text record. The real Site, Tracker and SavedData are used; no product name is patched.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from test_move_routes import STATUSES, world_with
from test_pages import Element, parse
from test_routes import FORM, SAME_ORIGIN, get, header, page
from test_task_routes import World, focused, location

from application import TaskFields
from web import Response, pages

TITLE = "Set up CI"
SENTENCE = "Delete 'Set up CI'? You can't undo this."
FAILURE = "The tracker couldn't delete 'Set up CI', and nothing was changed. Try again."
TRIGGER_LABEL = "Delete task"
BACK_OUT = "Back out"
CONFIRM_ACTION = "/tasks/1/delete/confirm"
TRIGGER_ACTION = "/tasks/1/delete"


def press_delete(world: World, task: int | str = 1) -> Response:
    """The first press of Delete task, as a form sends it."""
    return world.site.handle("POST", f"/tasks/{task}/delete", {**SAME_ORIGIN, **FORM}, b"")


def task_root(world: World, query: str = "", task: int = 1) -> Element:
    return parse(page(get(world.site, f"/tasks/{task}{query}")))


def delete_forms(root: Element) -> list[Element]:
    return [
        f
        for f in root.find_all("form")
        if f.attrs["action"].startswith("/tasks/") and "/delete" in f.attrs["action"]
    ]


def strips(root: Element) -> list[Element]:
    return [e for e in root.walk() if "confirm-strip" in (e.attrs.get("class") or "")]


def trigger_of(root: Element) -> Element:
    (form,) = [f for f in root.find_all("form") if f.attrs["action"] == TRIGGER_ACTION]
    (button,) = form.find_all("button")
    return button


def inside(element: Element, ancestor: Element) -> bool:
    node: Element | None = element
    while node is not None:
        if node is ancestor:
            return True
        node = node.parent
    return False


def add_comments(world: World, count: int) -> None:
    world.tracker.set_operator_name("Lee")
    for number in range(count):
        world.tracker.add_task_comment(1, f"Comment {number}")


def test_the_delete_modes_are_the_closed_vocabulary() -> None:
    """T4: the task page's deletion states are four, and a neutral area adds nothing."""
    assert {mode.value for mode in pages.DeleteMode} == {
        "ordinary",
        "confirmation",
        "backed-out",
        "failed",
    }
    assert pages.DeleteArea().mode is pages.DeleteMode.ORDINARY


@pytest.mark.parametrize("status", STATUSES)
@pytest.mark.parametrize("comments", [0, 3])
def test_delete_control_is_task_level_in_every_status(
    tmp_path: Path, status: str, comments: int
) -> None:
    """CP-529, T4: one separate Delete task form after the task's content, outside every other
    form and every written comment, in every status."""
    world = world_with(tmp_path, status)
    add_comments(world, comments)
    root = task_root(world)
    (main,) = root.find_all("main")
    comments_section = root.by_id("comments")
    assert comments_section is not None
    forms = main.find_all("form")
    delete_form = forms[-1]
    assert delete_form.attrs["action"] == TRIGGER_ACTION and delete_form.attrs["method"] == "post"
    assert [f.attrs["action"] for f in forms].count(TRIGGER_ACTION) == 1
    (button,) = delete_form.find_all("button")
    assert button.text() == TRIGGER_LABEL and "aria-label" not in button.attrs
    assert [e for e in delete_form.walk() if e.tag == "form"] == [delete_form]
    assert not inside(delete_form, comments_section)
    for other in forms[:-1]:
        assert not inside(delete_form, other) and not inside(other, delete_form)
    assert focused(root) == []
    order = list(root.walk())
    assert order.index(delete_form) > order.index(comments_section)
    for item in comments_section.find_all("li"):
        assert [e for e in item.walk() if e.tag in ("a", "button", "form", "input")] == []


def test_no_list_row_offers_deletion(tmp_path: Path) -> None:
    """CP-529: neither a project's rows nor All tasks' rows carry a delete form."""
    world = world_with(tmp_path)
    for address in ("/projects/1", "/tasks"):
        shown = page(get(world.site, address))
        root = parse(shown)
        assert delete_forms(root) == [], address
        assert "Delete" not in shown, address


def test_delete_first_press_opens_confirmation_without_saving(tmp_path: Path) -> None:
    """CP-530, CP-531, T4: 303 to the pending address, then the strip in the trigger's place with
    the sentence, the confirming form and Back out in that order; nothing is saved."""
    world = world_with(tmp_path)
    before, saves = world.bytes_on_disk(), world.saver.saves
    response = press_delete(world)
    assert location(response) == "/tasks/1?delete_confirm"
    assert header(response, "Cache-Control") is None
    shown = get(world.site, "/tasks/1?delete_confirm")
    assert shown.status == 200 and header(shown, "Cache-Control") == "no-store"
    root = parse(page(shown))
    (strip,) = strips(root)
    sentence = root.by_id("confirm-sentence")
    assert sentence is not None and sentence.text() == SENTENCE
    assert focused(root) == [sentence]
    first, second = strip.find_all("form")
    assert (first.attrs["action"], first.attrs["method"]) == (CONFIRM_ACTION, "post")
    assert [b.text() for b in first.find_all("button")] == [TRIGGER_LABEL]
    assert (second.attrs["action"], second.attrs["method"]) == ("/tasks/1", "get")
    assert [b.text() for b in second.find_all("button")] == [BACK_OUT]
    assert {i.attrs["name"] for i in second.find_all("input")} == {"delete_back"}
    order = list(strip.walk())
    assert order.index(sentence) < order.index(first) < order.index(second)
    assert [f for f in root.find_all("form") if f.attrs["action"] == TRIGGER_ACTION] == []
    assert world.bytes_on_disk() == before and world.saver.saves == saves
    assert world.tracker.task(1) is not None


def test_the_sentence_uses_the_title_held_now_and_shows_it_as_text(tmp_path: Path) -> None:
    """CP-530, CP-535: the saved title is shown whole, escaped, in the sentence."""
    world = world_with(tmp_path, title="<b>A&B</b> \"q\" 's' é")
    root = task_root(world, "?delete_confirm")
    sentence = root.by_id("confirm-sentence")
    assert sentence is not None
    assert sentence.text() == "Delete '<b>A&B</b> \"q\" 's' é'? You can't undo this."
    assert [e for e in root.find_all("b")] == []


def test_back_out_restores_the_trigger_without_an_outcome(tmp_path: Path) -> None:
    """CP-532, T4: Back out is a GET that restores and focuses the trigger, with no line, no strip
    and no save."""
    world = world_with(tmp_path)
    before = world.bytes_on_disk()
    shown = get(world.site, "/tasks/1?delete_back")
    assert shown.status == 200 and header(shown, "Cache-Control") == "no-store"
    root = parse(page(shown))
    trigger = trigger_of(root)
    assert trigger.text() == TRIGGER_LABEL
    assert focused(root) == [trigger] and "aria-describedby" not in trigger.attrs
    assert strips(root) == []
    for absent in ("delete-failure", "delete-line", "move-line"):
        assert root.by_id(absent) is None
    text = root.text()
    assert "You deleted" not in text and "couldn't delete" not in text
    assert world.bytes_on_disk() == before


def test_the_failed_page_shows_one_failure_line_on_the_focused_trigger(tmp_path: Path) -> None:
    """CP-536, T9: the failure beside the restored trigger, which has focus and is described by it."""
    world = world_with(tmp_path, title=TITLE)
    shown = get(world.site, "/tasks/1?delete_failed")
    assert shown.status == 200 and header(shown, "Cache-Control") == "no-store"
    root = parse(page(shown))
    trigger = trigger_of(root)
    assert focused(root) == [trigger]
    (line,) = trigger.described_by()
    assert line.text() == FAILURE and strips(root) == []
    assert "You deleted" not in root.text() and "Traceback" not in root.text()
    assert [e for e in root.walk() if e.attrs.get("id") == line.attrs.get("id")] == [line]


@pytest.mark.parametrize(
    ("query", "mode"),
    [
        ("?delete_failed&delete_confirm&delete_back", "failed"),
        ("?delete_confirm&delete_back", "confirmation"),
        ("?delete_back", "backed-out"),
        ("?delete_failed", "failed"),
    ],
)
def test_delete_outcome_resolves_one_focus_before_other_regions(
    tmp_path: Path, query: str, mode: str
) -> None:
    """T12: failure beats confirmation, which beats back-out; exactly one focus target results."""
    world = world_with(tmp_path)
    root = task_root(world, query)
    assert len(focused(root)) == 1
    if mode == "confirmation":
        assert len(strips(root)) == 1 and focused(root)[0].attrs["id"] == "confirm-sentence"
    else:
        assert strips(root) == [] and focused(root) == [trigger_of(root)]
        assert (root.by_id("delete-failure") is not None) == (mode == "failed")


NOISE = [
    "move_task=1&moved=in-progress",
    "move_task=1&move_confirm=cancelled",
    "move_task=1&move_failed=done",
    "move_task=999&move_confirm=cancelled",
    "move_task=999&moved=done",
    "saved",
    "added",
    "edit_refused=blank-title&title=&shown_title=Set+up+CI",
    "edit_failed=save&title=x",
    "label_added=ui&label=ui",
    "label_refused=empty&label=",
    "comment_added=1",
    "comment_refused=blank",
    "comment_failed=add",
]

# Every line a move, edit, label or comment outcome puts on the task page.
OTHER_OUTCOME_IDS = (
    "move-line",
    "saved-line",
    "added-line",
    "edit-failure",
    "label-reason",
    "label-failure",
    "label-added-line",
    "label-removed-line",
    "comment-reason",
    "comment-failure",
    "comment-added-line",
)


@pytest.mark.parametrize("noise", NOISE)
@pytest.mark.parametrize("marker", ["delete_confirm", "delete_back", "delete_failed"])
def test_an_active_deletion_suppresses_every_other_outcome_and_focus(
    tmp_path: Path, noise: str, marker: str
) -> None:
    """T12: any active deletion state wins over the move, comment, label and edit outcomes and
    their autofocus, even a conflicting move reference to a task nothing holds."""
    world = world_with(tmp_path)
    world.tracker.set_operator_name("Lee")
    world.tracker.add_task_comment(1, "One")
    world.tracker.add_task_label(1, "ui")
    shown = get(world.site, f"/tasks/1?{marker}&{noise}")
    root = parse(page(shown))
    (target,) = focused(root)
    if marker == "delete_confirm":
        assert target.attrs["id"] == "confirm-sentence" and len(strips(root)) == 1
    else:
        assert target is trigger_of(root) and strips(root) == []
    for absent in OTHER_OUTCOME_IDS:
        assert root.by_id(absent) is None, absent
    assert header(shown, "Cache-Control") == "no-store"


@pytest.mark.parametrize("noise", [noise for noise in NOISE if "move_task=999" not in noise])
def test_the_noise_shows_its_own_outcome_without_a_deletion_state(
    tmp_path: Path, noise: str
) -> None:
    """T12, control: each address the suppression test pairs with a deletion marker, other than a
    move reference to a task nothing holds, shows an outcome of its own when sent alone, so its
    absence beside the marker is the deletion's doing."""
    world = world_with(tmp_path)
    world.tracker.set_operator_name("Lee")
    world.tracker.add_task_comment(1, "One")
    world.tracker.add_task_label(1, "ui")
    # A pending cancellation is a 202, so the body is read without `page`'s 200 check.
    root = parse(get(world.site, f"/tasks/1?{noise}").body.decode())
    lines = [i for i in OTHER_OUTCOME_IDS if root.by_id(i) is not None]
    assert lines or strips(root) or focused(root), noise


@pytest.mark.parametrize(
    "query",
    [
        "?saved",
        "?added",
        "?move_task=1&moved=in-progress",
        "?comment_failed=add",
        "?label_added=ui",
    ],
)
def test_without_a_deletion_state_the_earlier_precedence_holds(tmp_path: Path, query: str) -> None:
    """T12: an address with no recognized deletion marker is answered as before."""
    world = world_with(tmp_path)
    world.tracker.set_operator_name("Lee")
    world.tracker.add_task_label(1, "ui")
    root = task_root(world, query)
    assert len(focused(root)) == 1 and strips(root) == []
    assert root.by_id("delete-failure") is None
    assert trigger_of(root).attrs.get("autofocus") is None


def test_unknown_delete_words_change_nothing(tmp_path: Path) -> None:
    """T12: a value carried beside a deletion key is not what selects it; unknown keys are ignored."""
    world = world_with(tmp_path)
    plain = page(get(world.site, "/tasks/1"))
    assert page(get(world.site, "/tasks/1?delete=yes&deleted_task=x&delete_confirmed")) == plain


def test_project_completion_beats_every_other_outcome(tmp_path: Path) -> None:
    """T12, CP-534: the project page's deletion line owns the one focus and the heading describes it."""
    world = world_with(tmp_path, title="Other")
    world.tracker.add_task(1, "Gone")
    queries = [
        "created",
        "move_task=1&moved=in-progress",
        "move_task=1&move_confirm=cancelled",
        "task_refused=blank&title=",
        "task_failed=add&title=x",
        "filter_status=todo",
    ]
    for query in queries:
        shown = get(world.site, f"/projects/1?deleted_task=Gone&{query}")
        assert shown.status == 200 and header(shown, "Cache-Control") == "no-store", query
        root = parse(page(shown))
        (heading,) = focused(root)
        assert heading.tag == "h1" and heading.attrs["tabindex"] == "-1"
        (line,) = heading.described_by()
        assert line.text() == "You deleted 'Gone'."
        assert root.by_id("created-line") is None and root.by_id("move-line") is None
        assert strips(root) == [], query


def test_the_project_page_without_a_deleted_title_adds_no_line(tmp_path: Path) -> None:
    """A neutral call adds no deletion outcome; the page equals the plain one."""
    world = world_with(tmp_path)
    plain = page(get(world.site, "/projects/1"))
    assert "You deleted" not in plain
    assert page(get(world.site, "/projects/1?deleted_task=")) == plain


def test_failed_page_beside_a_saved_title_edit_uses_the_title_held_now(tmp_path: Path) -> None:
    """CP-530, CP-536: the sentence and the failure line use the current title."""
    world = world_with(tmp_path)
    world.tracker.edit_task(1, TaskFields(title="Renamed"), TaskFields(title=TITLE))
    root = task_root(world, "?delete_confirm")
    sentence = root.by_id("confirm-sentence")
    assert sentence is not None and sentence.text() == "Delete 'Renamed'? You can't undo this."
    failed = task_root(world, "?delete_failed")
    (line,) = trigger_of(failed).described_by()
    assert line.text() == (
        "The tracker couldn't delete 'Renamed', and nothing was changed. Try again."
    )
