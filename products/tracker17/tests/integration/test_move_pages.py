"""Integration tests of the pages' move controls and landing through the real Site (layers 3 and 4).

Checks SRS FR-19 (the moves a task offers and the status shown in words), AC-12, NFR-12 (state is
carried by words and a named control) and UXD UX-A6 (each move is a button of its own). Change spec
rules CP-297 to CP-306, CP-308, CP-311 and CP-313, the cancel-confirmation change's CP-319 to
CP-326, CP-329, CP-331 and CP-335 and CP-336, the out-of-date-move change's CP-359, CP-361 to
CP-364 and CP-370, and NFDR QC-36 are the ones each test names.
Where a test checks words, they are the strings of this change's text record. Pages are read
through the real Site, Tracker and SavedData, with an injected Clock; no product name is patched.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from pathlib import Path

import pytest
from test_move_routes import (
    ADDRESS_FOR,
    LIST,
    PLACES,
    SUBMISSION_FOR,
    TASK_PLACE,
    TITLE,
    base_of,
    buttons,
    description,
    press,
    rows,
    strips,
    world_with,
)
from test_pages import Element, parse
from test_routes import get, page
from test_task_routes import World, focused, follow, make_world

from application import TaskStatus
from web import pages

CONTROL_TAGS = ("button", "input", "select", "textarea", "a", "form")


def task_page(world: World, query: str = "", task: int = 1, status: int = 200) -> Element:
    return parse(page(get(world.site, f"/tasks/{task}{query}"), status))


def project_page(world: World, query: str = "", status: int = 200) -> Element:
    return parse(page(get(world.site, f"/projects/1{query}"), status))


def status_area(root: Element) -> Element:
    (area,) = [e for e in root.find_all("section") if e.attrs.get("id") == "status"]
    return area


def world_with_all_statuses(tmp_path: Path) -> World:
    world = make_world(tmp_path)
    for title in ("Plain", "Going", "Finished", "Dropped"):
        world.tracker.add_task(1, title)
    world.tracker.move_task(2, "in-progress")
    world.tracker.move_task(3, "in-progress")
    world.tracker.move_task(3, "done")
    world.tracker.move_task(4, "cancelled")
    return world


def test_each_saved_status_offers_the_workflow_moves_in_order(tmp_path: Path) -> None:
    """P1, CP-297, CP-301, CP-319: every status, on a row and on a task page, offers exactly the
    moves the workflow answers for it, in its order, one native button per move; none shows a
    confirmation before a press. The cancelled button reads cancelled and is named for the title."""
    world = world_with_all_statuses(tmp_path)
    expected = []
    for number in range(1, 5):
        saved = world.tracker.task(number)
        assert saved is not None
        expected.append([move.value for move in world.tracker.allowed_moves(saved.status)])
    assert expected[0] == ["in-progress", "cancelled"] and expected[2] == []
    root = project_page(world)
    assert [buttons(cells[6]) for cells in rows(root)] == expected
    assert [cells[6].text() for cells in rows(root)[2:]] == ["", ""]
    titles = ["Plain", "Going", "Finished", "Dropped"]
    for number, (title, moves) in enumerate(zip(titles, expected, strict=True), start=1):
        on_task_page = status_area(task_page(world, task=number))
        for scope in (rows(root)[number - 1][6], on_task_page):
            assert buttons(scope) == moves
            names = [b.attrs["aria-label"] for b in scope.find_all("button")]
            assert names == [f"Move '{title}' to {move}" for move in moves]
    for shown in [root, *(task_page(world, task=number) for number in range(1, 5))]:
        assert strips(shown) == [] and "confirm" not in shown.text().lower()
        assert "Move to cancelled" not in shown.text() and focused(shown) == []


def test_task_page_shows_the_status_in_words_and_its_moves(tmp_path: Path) -> None:
    """P2, CP-299, CP-300: the status area names the status and offers the moves in order; a done
    task shows the status and no button."""
    world = world_with_all_statuses(tmp_path)
    going = status_area(task_page(world, task=2))
    assert going.find_all("h2")[0].text() == "Status"
    assert going.by_id("task-status") is not None
    assert going.by_id("task-status").text() == "in-progress"
    assert buttons(going) == ["done", "cancelled", "todo"]
    finished = status_area(task_page(world, task=3))
    assert finished.by_id("task-status").text() == "done" and buttons(finished) == []
    root = task_page(world, task=3)
    assert root.find_all("table") == [] and [e.text() for e in root.find_all("dt")] == ["Project"]


def test_the_done_button_name_is_move_title_to_done_on_the_row_and_the_task_page(
    tmp_path: Path,
) -> None:
    """P3, CP-298: the accessible name carries the task and the move; the visible label is the
    status word."""
    world = world_with(tmp_path, "in-progress")
    for root, scope in (
        (project_page(world), lambda r: rows(r)[0][6]),
        (task_page(world), status_area),
    ):
        done = [b for b in scope(root).find_all("button") if b.text() == "done"]
        assert [b.attrs["aria-label"] for b in done] == [f"Move '{TITLE}' to done"]


def test_every_move_control_is_a_lone_submit_button_in_a_post_form_with_no_tabindex_accesskey_or_disabled(
    tmp_path: Path,
) -> None:
    """P4, CP-300: the structural half of the keyboard rule, the browser's keys being E2E1."""
    world = world_with(tmp_path, "in-progress")
    for root in (project_page(world), task_page(world)):
        moves = [b for b in root.walk() if "move-button" in (b.attrs.get("class") or "").split()]
        assert len(moves) == 3
        for button in moves:
            assert button.tag == "button" and button.attrs["type"] == "submit"
            for forbidden in ("tabindex", "accesskey", "disabled"):
                assert forbidden not in button.attrs
            form = button.parent
            assert form is not None and form.tag == "form" and form.attrs["method"] == "post"
            assert form.attrs["action"] == "/tasks/1/move"
            assert form.find_all("button") == [button]
            controls = [e for e in form.walk() if e.tag in ("input", "select", "textarea")]
            assert {e.attrs["type"] for e in controls} == {"hidden"}
            assert {e.attrs["name"] for e in controls} == {"status", "place"}


def test_the_completion_line_and_button_name_escape_the_title_once(tmp_path: Path) -> None:
    """P5, CP-305, QC-36: the line reads exactly as the text record words it, and the markup holds
    the title once-escaped."""
    title = "a < b & c"
    world = world_with(tmp_path, title=title)
    landing = follow(world.site, press(world.site, 1, "in-progress", LIST))
    root = parse(landing)
    assert description(focused(root)[0]) == "You moved 'a < b & c' to in-progress."
    assert (
        "a &lt; b &amp; c" in landing and "&amp;lt;" not in landing and "&amp;amp;" not in landing
    )
    done = [b for b in root.find_all("button") if b.text() == "done"]
    assert [b.attrs["aria-label"] for b in done] == ["Move 'a < b & c' to done"]


OUTCOMES = {
    "moved": "move_task=1&moved=in-progress",
    "refused": "move_task=1&move_refused=not-allowed",
    "not-a-status": "move_task=1&move_refused=not-a-status",
    "failed": "move_task=1&move_failed=in-progress",
}
LINES = {
    "moved": "You moved 'Set up CI' to in-progress.",
    "refused": SUBMISSION_FOR["todo"],
    "not-a-status": SUBMISSION_FOR["todo"],
    "failed": (
        "The tracker couldn't move 'Set up CI' to in-progress, and nothing was changed. Try again."
    ),
}


@pytest.mark.parametrize("outcome", OUTCOMES)
@pytest.mark.parametrize("place", [LIST, TASK_PLACE])
def test_a_landing_page_has_exactly_one_autofocus_on_a_non_control_status_element_that_names_the_line(
    tmp_path: Path, place: str, outcome: str
) -> None:
    """P6, CP-303 to CP-305, CP-308, CP-311, EX-14: one focus, on the status word, in the moved
    row's status cell or the status area; the line is beside the moves, in the row's moves cell or
    the status area, and takes no focus."""
    world = world_with(tmp_path)
    root = (
        project_page(world, "?" + OUTCOMES[outcome])
        if place == LIST
        else task_page(world, "?" + OUTCOMES[outcome])
    )
    (target,) = focused(root)
    assert target.tag not in CONTROL_TAGS and target.attrs["tabindex"] == "-1"
    assert target.text() == "todo"
    (line,) = target.described_by()
    assert line.text() == LINES[outcome]
    assert "autofocus" not in line.attrs and "tabindex" not in line.attrs
    assert [e for e in root.walk() if e.attrs.get("id") == line.attrs["id"]] == [line]
    if place == LIST:
        (row,) = rows(root)
        word_holder, line_holder = row[1], row[6]
    else:
        word_holder = line_holder = status_area(root)
    assert target in list(word_holder.walk())
    assert line in list(line_holder.walk())
    others = [e for e in root.walk() if e.tag == "p" and "outcome" in (e.attrs.get("class") or "")]
    assert len(others) <= 1


@pytest.mark.parametrize("mode", ["move_confirm", "move_back"])
@pytest.mark.parametrize("final", ["done", "cancelled"])
@pytest.mark.parametrize("place", [LIST, TASK_PLACE])
def test_an_address_refusal_has_exactly_one_autofocus_on_a_non_control_status_element(
    tmp_path: Path, place: str, final: str, mode: str
) -> None:
    """CP-360 to CP-362, EX-14: the address refusal, like a refused press, has one focus on the
    status word in the task's status cell or area, which the address line describes; the line sits
    beside the moves, takes no focus and holds no reload, link or control; the page holds no
    strip and no outcome paragraph beside it."""
    world = world_with(tmp_path, final)
    query = f"?move_task=1&{mode}=cancelled"
    root = project_page(world, query) if place == LIST else task_page(world, query)
    (target,) = focused(root)
    assert target.tag not in CONTROL_TAGS and target.attrs["tabindex"] == "-1"
    assert target.text() == final
    (line,) = target.described_by()
    assert line.text() == ADDRESS_FOR[final]
    assert "autofocus" not in line.attrs and "tabindex" not in line.attrs
    assert [e for e in line.walk() if e.tag in CONTROL_TAGS] == []
    assert strips(root) == []
    if place == LIST:
        (row,) = rows(root)
        word_holder, line_holder = row[1], row[6]
    else:
        word_holder = line_holder = status_area(root)
    assert target in list(word_holder.walk()) and line in list(line_holder.walk())
    others = [e for e in root.walk() if e.tag == "p" and "outcome" in (e.attrs.get("class") or "")]
    assert len(others) <= 1


def test_a_move_outcome_wins_over_created_label_and_comment_outcomes(tmp_path: Path) -> None:
    """P7, D-7: an address carrying a move outcome beside any other has exactly one focus, the
    move's."""
    world = world_with(tmp_path)
    world.tracker.add_task_label(1, "ui")
    move = OUTCOMES["moved"]
    for other in ("created", "task_refused=blank-title", "task_failed=add"):
        root = project_page(world, f"?{other}&{move}")
        (target,) = focused(root)
        assert description(target) == LINES["moved"] and "You created" not in root.text()
    others = (
        "added",
        "saved",
        "edit_refused=blank-title",
        "edit_failed=save",
        "label_added=ui",
        "label_removed=ui",
        "label_refused=empty",
        "label_failed=add",
        "comment_refused=blank",
        "comment_failed=add",
        "comment_added=1",
    )
    for other in others:
        root = task_page(world, f"?{other}&{move}")
        (target,) = focused(root)
        assert description(target) == LINES["moved"], other
        assert target.text() == "todo"


@pytest.mark.parametrize(
    "query",
    [
        "move_task=1&move_refused=bogus",
        "move_task=1&moved=finished",
        "move_task=1&moved=",
        "move_task=1&move_failed=finished",
        "move_task=999&moved=done",
        "move_task=0&moved=done",
        "move_task=x&moved=done",
        "moved=done",
        "move_refused=not-allowed",
    ],
)
def test_forged_outcomes_render_the_page_plain(tmp_path: Path, query: str) -> None:
    """P8, CP-304: an unknown refusal code, a non-status word or a task that is not on the page
    gives the plain page."""
    world = world_with(tmp_path)
    assert page(get(world.site, f"/projects/1?{query}")) == page(get(world.site, "/projects/1"))
    assert page(get(world.site, f"/tasks/1?{query}")) == page(get(world.site, "/tasks/1"))
    assert focused(parse(page(get(world.site, f"/tasks/1?{query}")))) == []


def test_a_move_outcome_about_one_row_shows_nothing_on_the_other_rows(tmp_path: Path) -> None:
    """CP-303, CP-305: only the moved task's row takes the focus and holds the line."""
    world = make_world(tmp_path)
    world.tracker.add_task(1, "First")
    world.tracker.add_task(1, "Second")
    root = project_page(world, "?move_task=2&moved=in-progress")
    first, second = rows(root)
    assert focused(root) == [second[1].find_all("span")[0]]
    assert first[1].text() == "todo" and first[6].find_all("p") == []
    assert description(focused(root)[0]) == "You moved 'Second' to in-progress."


def test_a_move_outcome_about_a_real_task_of_another_page_renders_the_page_plain(
    tmp_path: Path,
) -> None:
    """P8, CP-303: an outcome naming a task that exists but is not a row of this project's page,
    or is not the task this page shows, is no outcome; the page renders plain."""
    world = make_world(tmp_path, projects=("Alpha", "Beta"))
    world.tracker.add_task(1, "Here")
    world.tracker.add_task(2, "There")
    query = "?move_task=2&moved=in-progress"
    assert page(get(world.site, f"/projects/1{query}")) == page(get(world.site, "/projects/1"))
    assert page(get(world.site, f"/tasks/1{query}")) == page(get(world.site, "/tasks/1"))
    assert focused(project_page(world, query)) == []


# --- The refusal's context, and the moves its line names (out-of-date-move) -------------------

ADDRESS_LINE = ADDRESS_FOR["done"]


def address_context() -> pages.MoveRefusalContext:
    return pages.MoveRefusalContext.CANCELLATION_ADDRESS


def project_html(world: World, **options: object) -> str:
    project = world.tracker.project(1)
    assert project is not None
    return pages.project_page(project, world.tracker.project_tasks(1), **options)


def task_html(world: World, **options: object) -> str:
    context = world.tracker.task_edit_context(1)
    assert context is not None
    return pages.task_page(context, **options)


BUILDERS = {LIST: project_html, TASK_PLACE: task_html}


def test_move_outcome_retains_existing_construction_and_defaults() -> None:
    """Design A, CP-363, T6: the four existing fields keep their order and meaning, positionally and
    by keyword, and use the submission context; the extended value stays immutable."""
    assert [f.name for f in fields(pages.MoveOutcome)][:4] == [
        "task_id",
        "refusal",
        "failed",
        "moved",
    ]
    positional = pages.MoveOutcome(1, pages.MoveRefusal.NOT_ALLOWED, None, None)
    keyword = pages.MoveOutcome(task_id=1, moved=TaskStatus.DONE)
    assert positional.refusal is pages.MoveRefusal.NOT_ALLOWED and positional.moved is None
    assert keyword.moved is TaskStatus.DONE and keyword.refusal is None
    assert pages.MoveOutcome().task_id is None and pages.MoveOutcome().refusal is None
    for outcome in (positional, keyword, pages.MoveOutcome()):
        assert outcome.refusal_context is pages.MoveRefusalContext.SUBMISSION
    assert [f.name for f in fields(pages.MoveOutcome)][-1] == "refusal_context"
    assert {c.name for c in pages.MoveRefusalContext} == {"SUBMISSION", "CANCELLATION_ADDRESS"}
    with pytest.raises(FrozenInstanceError):
        positional.task_id = 2


@pytest.mark.parametrize("place", PLACES)
def test_refusal_context_selects_only_the_rendered_tasks_refusal(
    tmp_path: Path, place: str
) -> None:
    """Design A, CP-359, CP-361, CP-363, T6, T7: both builders render the address line for the
    address context and the submission line for the default; the context beside no refusal about
    this task changes neither a failure nor a completion, makes no outcome, and takes no focus for
    an absent or foreign task; a refusal still comes before a failure and a completion."""
    world = world_with(tmp_path, "done")
    build = BUILDERS[place]
    allowed = world.tracker.allowed_moves
    plain = build(world, allowed_moves=allowed)
    for code in pages.MoveRefusal:
        address = pages.MoveOutcome(1, refusal=code, refusal_context=address_context())
        (target,) = focused(parse(build(world, allowed_moves=allowed, move_outcome=address)))
        assert description(target) == ADDRESS_LINE
        submitted = pages.MoveOutcome(1, refusal=code)
        (target,) = focused(parse(build(world, allowed_moves=allowed, move_outcome=submitted)))
        assert description(target) == SUBMISSION_FOR["done"]
    done = TaskStatus.DONE
    for words in ({"failed": done}, {"moved": done}):
        beside = pages.MoveOutcome(1, refusal_context=address_context(), **words)
        alone = pages.MoveOutcome(1, **words)
        assert build(world, allowed_moves=allowed, move_outcome=beside) == build(
            world, allowed_moves=allowed, move_outcome=alone
        )
    for nothing in (
        pages.MoveOutcome(refusal_context=address_context()),
        pages.MoveOutcome(1, refusal_context=address_context()),
        pages.MoveOutcome(
            2, refusal=pages.MoveRefusal.NOT_ALLOWED, refusal_context=address_context()
        ),
    ):
        shown = build(world, allowed_moves=allowed, move_outcome=nothing)
        assert shown == plain and focused(parse(shown)) == []
    every = pages.MoveOutcome(
        1, pages.MoveRefusal.NOT_ALLOWED, done, done, refusal_context=address_context()
    )
    (target,) = focused(parse(build(world, allowed_moves=allowed, move_outcome=every)))
    assert description(target) == ADDRESS_LINE


def test_a_refusal_with_either_context_touches_only_its_own_row(tmp_path: Path) -> None:
    """Design A, CP-363, T7: the other rows of the list are those of the plain page, whichever
    context the refusal about the done task carries."""
    world = world_with_all_statuses(tmp_path)
    allowed = world.tracker.allowed_moves
    plain = rows(parse(project_html(world, allowed_moves=allowed)))
    for context in pages.MoveRefusalContext:
        outcome = pages.MoveOutcome(3, pages.MoveRefusal.NOT_ALLOWED, refusal_context=context)
        shown = rows(parse(project_html(world, allowed_moves=allowed, move_outcome=outcome)))
        for index in (0, 1, 3):
            assert [signature(c) for c in shown[index]] == [signature(c) for c in plain[index]]


OFFERED = [
    ((), "can't be moved."),
    ((TaskStatus.CANCELLED,), "can be moved to cancelled."),
    ((TaskStatus.CANCELLED, TaskStatus.TODO), "can be moved to cancelled or todo."),
    (
        (TaskStatus.TODO, TaskStatus.DONE, TaskStatus.CANCELLED),
        "can be moved to todo, done or cancelled.",
    ),
]


@pytest.mark.parametrize("place", PLACES)
@pytest.mark.parametrize("code", list(pages.MoveRefusal), ids=lambda c: c.value)
@pytest.mark.parametrize(("offered", "ending"), OFFERED, ids=["none", "one", "two", "three"])
def test_refusal_line_and_controls_share_the_supplied_move_order(
    tmp_path: Path,
    place: str,
    code: pages.MoveRefusal,
    offered: tuple[TaskStatus, ...],
    ending: str,
) -> None:
    """Design A, CP-359, CP-364, T6: an allowed-moves callable handed to either public builder gives
    the one ordered tuple that the buttons and the named moves both follow, whatever the workflow's
    own order; an empty tuple names no move. No product name is patched and no table is copied."""
    world = world_with(tmp_path, "in-progress")
    outcome = pages.MoveOutcome(1, refusal=code)
    root = parse(BUILDERS[place](world, allowed_moves=lambda status: offered, move_outcome=outcome))
    (target,) = focused(root)
    line = "The status of 'Set up CI' has changed to in-progress. A task in in-progress " + ending
    assert description(target) == line
    scope = rows(root)[0][6] if place == LIST else status_area(root)
    assert buttons(scope) == [move.value for move in offered]


# --- The cancelled move and its in-place confirmation (cancel-confirmation) --------------------

SENTENCE = "Move 'Set up CI' to cancelled? A cancelled task can't be moved again."
HOSTILE_TITLE = 'a < b & "c" it\'s'


def moves_container(scope: Element) -> Element:
    (container,) = [e for e in scope.walk() if "moves" in (e.attrs.get("class") or "").split()]
    return container


def signature(element: Element) -> tuple:
    return tuple(
        (
            e.tag,
            tuple(sorted((k, v) for k, v in e.attrs.items())),
            e.text() if not e.children else "",
        )
        for e in element.walk()
    )


def many_tasks_world(tmp_path: Path) -> World:
    """Four tasks: the one the strip opens on is task 2, in-progress, with a move either side."""
    return world_with_all_statuses(tmp_path)


def opened_scope(root: Element, place: str, task: int = 2) -> Element:
    return rows(root)[task - 1][6] if place == LIST else status_area(root)


@pytest.mark.parametrize("task", [1, 2])
@pytest.mark.parametrize("place", PLACES)
def test_opening_replaces_only_the_selected_cancelled_button(
    tmp_path: Path, place: str, task: int
) -> None:
    """CP-321, CP-322, CP-336: the strip stands where cancelled stood: the sentence, then the
    confirming POST form, then the back-out GET form; the other moves, rows and forms stay."""
    world = many_tasks_world(tmp_path)
    query = f"?move_task={task}&move_confirm=cancelled"
    plain = project_page(world) if place == LIST else task_page(world, task=task)
    opened = (
        project_page(world, query, 202) if place == LIST else task_page(world, query, task, 202)
    )
    title = ["Plain", "Going"][task - 1]
    scope = opened_scope(opened, place, task)
    (strip,) = strips(scope)
    (sentence, confirming, backing) = [c for c in strip.children if isinstance(c, Element)]
    assert sentence.text() == f"Move '{title}' to cancelled? A cancelled task can't be moved again."
    assert confirming.tag == "form" and confirming.attrs["method"] == "post"
    assert confirming.attrs["action"] == f"/tasks/{task}/move/confirm"
    (confirm_button,) = confirming.find_all("button")
    assert confirm_button.text() == "Move to cancelled" and "aria-label" not in confirm_button.attrs
    assert {e.attrs["name"]: e.attrs["value"] for e in confirming.find_all("input")} == {
        "place": place
    }
    assert backing.tag == "form" and backing.attrs["method"] == "get"
    assert backing.attrs["action"] == ("/projects/1" if place == LIST else f"/tasks/{task}")
    (back_button,) = backing.find_all("button")
    assert back_button.text() == "Back out" and "aria-label" not in back_button.attrs
    assert [(e.attrs["name"], e.attrs["value"]) for e in backing.find_all("input")] == [
        ("move_task", str(task)),
        ("move_back", "cancelled"),
    ]
    assert "You moved" not in opened.text()
    # Everything else is as the plain page has it.
    kept = [m for m in buttons(scope) if m not in ("Move to cancelled", "Back out")]
    assert kept == [m for m in buttons(opened_scope(plain, place, task)) if m != "cancelled"]
    if place == LIST:
        for index, (before, after) in enumerate(zip(rows(plain), rows(opened), strict=True), 1):
            if index != task:
                assert [signature(c) for c in before] == [signature(c) for c in after]
    others = [e for e in moves_container(scope).children if isinstance(e, Element)]
    assert strip.parent in others and strip.parent.attrs["class"] == "move-slot"


def test_confirmation_titles_are_shown_as_text_once(tmp_path: Path) -> None:
    """CP-322, CP-336, QC-36: `<`, `&`, double and single quotes survive as typed in the sentence
    and in the accessible names, escaped once in the markup and never twice."""
    world = world_with(tmp_path, title=HOSTILE_TITLE)
    for address in ("/projects/1", "/tasks/1"):
        plain = page(get(world.site, address))
        shown = page(get(world.site, f"{address}?move_task=1&move_confirm=cancelled"), 202)
        for text in (plain, shown):
            assert "&amp;lt;" not in text and "&amp;amp;" not in text and "&amp;quot;" not in text
        root = parse(shown)
        (strip,) = strips(root)
        assert strip.find_all("p")[0].text() == (
            f"Move '{HOSTILE_TITLE}' to cancelled? A cancelled task can't be moved again."
        )
        assert "a &lt; b &amp; &quot;c&quot; it&#x27;s" in shown
        named = [b for b in parse(plain).find_all("button") if b.text() == "cancelled"]
        assert [b.attrs["aria-label"] for b in named] == [f"Move '{HOSTILE_TITLE}' to cancelled"]


@pytest.mark.parametrize("place", PLACES)
def test_confirmation_sentence_alone_owns_focus_and_is_not_a_tab_stop(
    tmp_path: Path, place: str
) -> None:
    """CP-320, CP-323, CP-324: the sentence sits outside both forms with tabindex -1 and the page's
    only autofocus; the controls after it are native, enabled, and carry no shortcut or positive
    tabindex; the strip names the trigger-size context it follows."""
    world = world_with(tmp_path)
    root = parse(page(get(world.site, f"{base_of(place)}?move_task=1&move_confirm=cancelled"), 202))
    (strip,) = strips(root)
    classes = strip.attrs["class"].split()
    assert "confirm-strip" in classes and "strip-row-control" in classes
    (sentence,) = focused(root)
    assert sentence.parent is strip and sentence.attrs["id"] == "confirm-sentence"
    assert sentence.tag not in CONTROL_TAGS and sentence.attrs["tabindex"] == "-1"
    ancestors = []
    node = sentence.parent
    while node is not None:
        ancestors.append(node.tag)
        node = node.parent
    assert "form" not in ancestors
    elements = [c for c in strip.children if isinstance(c, Element)]
    assert [c.tag for c in elements] == ["p", "form", "form"]
    for form, css in zip(elements[1:], ("button-confirm", "button-secondary"), strict=True):
        (button,) = form.find_all("button")
        assert button.attrs["type"] == "submit" and css in button.attrs["class"].split()
        for forbidden in ("tabindex", "accesskey", "disabled", "autofocus"):
            assert forbidden not in button.attrs
        assert [e.attrs["type"] for e in form.find_all("input")] == ["hidden"] * len(
            form.find_all("input")
        )


@pytest.mark.parametrize("place", PLACES)
def test_move_query_collisions_select_one_interaction_and_focus_owner(
    tmp_path: Path, place: str
) -> None:
    """CP-324, CP-326: refusal, then failure, then completion, then opening, then backing out;
    one strip and one autofocus at most; unknown codes, invalid task values and another task on a
    task page change nothing; repeated keys do not multiply strips or focus targets."""
    world = many_tasks_world(tmp_path)
    world.tracker.add_task(1, "Other", "", "", "")
    base = base_of(place)
    word = {"refusal": "move_refused=not-allowed", "failure": "move_failed=in-progress"}
    word["completion"] = "moved=in-progress"
    open_, back = "move_confirm=cancelled", "move_back=cancelled"
    target = "move_task=1"

    def shown(*parts: str, status: int = 200) -> Element:
        return parse(page(get(world.site, f"{base}?{target}&{'&'.join(parts)}"), status))

    # One interaction by precedence: a lower one never adds a strip, a line or a focus.
    for winner, parts in {
        "refusal": (word["completion"], word["failure"], word["refusal"], open_, back),
        "failure": (word["completion"], word["failure"], open_, back),
        "completion": (word["completion"], open_, back),
    }.items():
        root = shown(*parts)
        assert strips(root) == [], winner
        (status,) = focused(root)
        assert status.text() == "todo" and len(status.described_by()) == 1, winner
    assert description(focused(shown(word["failure"], open_))[0]).startswith("The tracker")
    assert description(focused(shown(word["refusal"], word["failure"]))[0]).startswith("The status")
    root = shown(back, open_, open_, back, status=202)
    assert len(strips(root)) == 1 and [e.attrs.get("id") for e in focused(root)] == [
        "confirm-sentence"
    ]
    assert "You moved" not in root.text()
    unknown = shown("move_refused=bogus", open_, status=202)
    assert len(strips(unknown)) == 1
    # No interaction effect: the page is the plain one.
    plain = page(get(world.site, base))
    for query in (
        "move_task=1&move_confirm=bogus",
        "move_task=1&move_confirm=",
        "move_task=1&move_back=other",
        "move_task=x&move_confirm=cancelled",
        "move_confirm=cancelled",
        "move_task=1&move_confirm=bogus&move_confirm=cancelled",
    ):
        assert page(get(world.site, f"{base}?{query}")) == plain, query
    if place == TASK_PLACE:
        assert page(get(world.site, "/tasks/1?move_task=5&move_confirm=cancelled")) == plain
    # Beside an unrelated outcome, the interaction owns the one focus.
    unrelated = (
        ("created",) if place == LIST else ("added", "saved", "label_added=ui", "comment_added=1")
    )
    for other in unrelated:
        root = parse(page(get(world.site, f"{base}?{other}&{target}&{open_}"), 202))
        assert [e.attrs.get("id") for e in focused(root)] == ["confirm-sentence"], other
        assert "You created" not in root.text() and "You added" not in root.text()


@pytest.mark.parametrize("place", PLACES)
def test_back_out_restores_only_the_selected_trigger(tmp_path: Path, place: str) -> None:
    """CP-329, CP-331: backing out shows no strip or completion, restores one cancelled button
    with the page's sole autofocus and keeps every other form; a move the workflow no longer
    offers lands on the current status and its reason instead."""
    world = many_tasks_world(tmp_path)
    base = "/projects/1" if place == LIST else "/tasks/2"
    plain = parse(page(get(world.site, base)))
    root = parse(page(get(world.site, f"{base}?move_task=2&move_back=cancelled")))
    assert strips(root) == [] and "You moved" not in root.text()
    (trigger,) = focused(root)
    assert trigger.tag == "button" and trigger.text() == "cancelled"
    assert "tabindex" not in trigger.attrs
    assert trigger.attrs["aria-label"] == "Move 'Going' to cancelled"
    scope = opened_scope(root, place)
    assert trigger in list(scope.walk())
    assert buttons(scope) == ["done", "cancelled", "todo"]
    kept = [e for e in root.walk() if e.tag == "form"]
    assert len(kept) == len([e for e in plain.walk() if e.tag == "form"])
    gone = parse(
        page(
            get(
                world.site,
                f"{'/projects/1' if place == LIST else '/tasks/4'}?move_task=4&move_back=cancelled",
            )
        )
    )
    assert strips(gone) == []
    (status,) = focused(gone)
    assert status.text() == "cancelled"
    assert description(status) == ADDRESS_FOR["cancelled"].replace("Set up CI", "Dropped")


def test_plain_confirmation_strip_is_reusable_without_a_move_subject(tmp_path: Path) -> None:
    """CP-335: the strip is built from plain text, destinations and fields alone; the same
    sentence, forms, order and focus contract hold for a fixture and for the cancellation."""
    markup = pages.confirm_strip(
        sentence="Delete <b>'x' & \"y\"</b>? It can't come back.",
        sentence_id="fixture-sentence",
        confirm=pages.StripForm("Delete it", "/things/9/delete", "post", {"place": "list"}),
        back_out=pages.StripForm("Back out", "/things/9", "get", {"thing": "9", "back": "yes"}),
        size="row-control",
        focus=True,
    )
    assert "&amp;lt;" not in markup and "<b>" not in markup
    root = parse(markup)
    (strip,) = strips(root)
    elements = [c for c in strip.children if isinstance(c, Element)]
    assert [c.tag for c in elements] == ["p", "form", "form"]
    assert elements[0].text() == "Delete <b>'x' & \"y\"</b>? It can't come back."
    assert elements[0].attrs["tabindex"] == "-1" and "autofocus" in elements[0].attrs
    assert [e.attrs["name"] for e in elements[2].find_all("input")] == ["thing", "back"]
    assert elements[1].attrs["method"] == "post" and elements[2].attrs["method"] == "get"
    unfocused = parse(
        pages.confirm_strip(
            sentence="s",
            sentence_id="s1",
            confirm=pages.StripForm("Go", "/a", "post", {}),
            back_out=pages.StripForm("Back out", "/b", "get", {}),
            size="row-control",
            focus=False,
        )
    )
    assert focused(unfocused) == []
    world = world_with(tmp_path)
    real = parse(page(get(world.site, "/tasks/1?move_task=1&move_confirm=cancelled"), 202))
    (real_strip,) = strips(real)
    shape = lambda s: [
        (c.tag, c.attrs.get("class"), c.attrs.get("method"))
        for c in s.children
        if isinstance(c, Element)
    ]
    assert shape(real_strip)[0][:2] == shape(strip)[0][:2]
    assert [(t, m) for t, _, m in shape(real_strip)] == [(t, m) for t, _, m in shape(strip)]
