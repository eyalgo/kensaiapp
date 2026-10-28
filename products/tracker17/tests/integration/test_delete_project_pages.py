"""Integration tests of a project's Delete project control, its confirmation and the Projects
completion line, each page read as a browser parses it (layer 4, reached through the real Site).

Checks SRS FR-13 (deleting a project with its tasks and comments), FR-39 (the failure words), NFR-5
(typed text is shown as text), NFR-12 (state is carried by words, one thing has focus) and AC-12.
Change spec rules CP-569 to CP-577 and the design's T4 to T7 are the ones each test names. Where a
test checks words they are the strings of this change's text record. The real Site, Tracker and
SavedData are used; no product name is patched.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from test_delete_pages import BACK_OUT, inside, strips
from test_pages import Element, parse
from test_routes import get
from test_task_routes import World, add_task, focused, make_world

TRIGGER_LABEL = "Delete project"
TRIGGER_ACTION = "/projects/1/delete"
CONFIRM_ACTION = "/projects/1/delete/confirm"
SECTION_ID = "delete-project"
FAILURE_ID = "delete-project-failure"
OPEN = "project_delete_confirm"
BACK = "project_delete_back"
FAILED = "project_delete_failed"
STATUS_PATH = {
    "todo": (),
    "in-progress": ("in-progress",),
    "done": ("in-progress", "done"),
    "cancelled": ("cancelled",),
}


def sentence_for(name: str, count: int) -> str:
    if count == 0:
        return f"Delete '{name}', which has no tasks? You can't undo this."
    noun = "1 task" if count == 1 else f"{count} tasks"
    return f"Delete '{name}' and its {noun}? You can't undo this."


def completion_for(name: str, count: int) -> str:
    if count == 0:
        return f"You deleted '{name}', which had no tasks."
    noun = "1 task" if count == 1 else f"{count} tasks"
    return f"You deleted '{name}' and its {noun}."


def project_root(world: World, query: str = "", project: int = 1) -> Element:
    """A project's Tasks view for this query, checked to answer 202 exactly when it shows a
    confirmation strip (CP-583) and 200 otherwise."""
    response = get(world.site, f"/projects/{project}{query}")
    root = parse(response.body.decode("utf-8"))
    assert response.status == (202 if strips(root) else 200), query
    return root


def with_statuses(world: World, statuses: tuple[str, ...]) -> None:
    """One task for each status given, reached by the workflow's own moves, each with a comment."""
    world.tracker.set_operator_name("Lee")
    for number, status in enumerate(statuses, start=1):
        add_task(world.site, 1, title=f"Task {number}")
        for step in STATUS_PATH[status]:
            world.tracker.move_task(number, step)
        world.tracker.add_task_comment(number, "Noted")


def trigger_form(root: Element) -> Element | None:
    found = [f for f in root.find_all("form") if f.attrs.get("action") == TRIGGER_ACTION]
    assert len(found) <= 1
    return found[0] if found else None


def trigger_of(root: Element) -> Element:
    form = trigger_form(root)
    assert form is not None
    (button,) = form.find_all("button")
    return button


def project_delete_forms(root: Element) -> list[Element]:
    return [
        f
        for f in root.find_all("form")
        if (f.attrs.get("action") or "").startswith("/projects/")
        and "/delete" in (f.attrs.get("action") or "")
    ]


def hidden_pairs(form: Element) -> list[tuple[str, str]]:
    return [
        (i.attrs["name"] or "", i.attrs["value"] or "")
        for i in form.find_all("input")
        if i.attrs.get("type") == "hidden"
    ]


def the_section(root: Element) -> Element:
    section = root.by_id(SECTION_ID)
    assert section is not None
    return section


def test_delete_project_is_offered_only_below_its_tasks_view_results(tmp_path: Path) -> None:
    """CP-569, T4: in the ordinary, empty, no-match, refused-filter and refused-sort states the
    section stands after the list and before Rename, outside every other form; no other page and
    no list row offers a project deletion."""
    empty = make_world(tmp_path / "empty")
    listed = make_world(tmp_path / "listed")
    with_statuses(listed, ("todo", "todo"))
    states = [
        (empty, ""),
        (listed, ""),
        (listed, "?filter_status=done"),
        (listed, "?filter_status=bogus"),
        (listed, "?sort_field=bogus"),
    ]
    for world, query in states:
        root = project_root(world, query)
        form = trigger_form(root)
        assert form is not None, query
        assert form.attrs["method"] == "post"
        button = trigger_of(root)
        assert button.text() == TRIGGER_LABEL and "aria-label" not in button.attrs, query
        assert focused(root) == [] or all(e.tag != "button" for e in focused(root)), query
        (main,) = root.find_all("main")
        children = [c for c in main.children if isinstance(c, Element)]
        section = the_section(root)
        assert children[-2] is section and children[-1].attrs.get("id") == "rename-project", query
        ordered = list(root.walk())
        for earlier in ("filter", "task-list", "filter-no-match", "filter-count"):
            found = root.by_id(earlier)
            if found is not None:
                assert ordered.index(found) < ordered.index(form), (query, earlier)
        for table in root.find_all("table"):
            assert project_delete_forms(table) == [], query
        for other in root.find_all("form"):
            if other is not form:
                assert not inside(form, other) and not inside(other, form), query
        assert [f for f in section.find_all("form")] == [form], query
    for address in ("/", "/projects/1/summary", "/tasks/1", "/tasks", "/people"):
        shown = parse(get(listed.site, address).body.decode("utf-8"))
        assert project_delete_forms(shown) == [], address
        assert TRIGGER_LABEL not in shown.text(), address


def test_project_confirmation_counts_all_current_tasks(tmp_path: Path) -> None:
    """CP-570, T4: zero, one and many tasks choose the sentence; the count is every task in every
    status, never comments and never the rows a filter shows; the sentence, confirming control and
    Back out follow in that order in the shared strip, and the current saved name is used."""
    many = make_world(tmp_path / "many", projects=("Alpha",))
    with_statuses(many, ("todo", "in-progress", "done", "cancelled"))
    one = make_world(tmp_path / "one", projects=("Solo",))
    with_statuses(one, ("todo",))
    none = make_world(tmp_path / "none", projects=("Empty",))
    cases = [(many, "Alpha", 4), (one, "Solo", 1), (none, "Empty", 0)]
    for world, name, count in cases:
        for query in (f"?{OPEN}", f"?{OPEN}&filter_status=done", f"?{OPEN}&filter_label=nothing"):
            root = project_root(world, query)
            (strip,) = strips(root)
            sentence = root.by_id("confirm-sentence")
            assert sentence is not None and sentence.text() == sentence_for(name, count), query
            assert "strip-control" in strip.attrs["class"]
            confirm, back = strip.find_all("form")
            assert (confirm.attrs["action"], confirm.attrs["method"]) == (CONFIRM_ACTION, "post")
            assert [b.text() for b in confirm.find_all("button")] == [TRIGGER_LABEL]
            assert (back.attrs["action"], back.attrs["method"]) == ("/projects/1", "get")
            assert [b.text() for b in back.find_all("button")] == [BACK_OUT]
            order = list(strip.walk())
            assert order.index(sentence) < order.index(confirm) < order.index(back)
            assert trigger_form(root) is None and focused(root) == [sentence]
            assert the_section(root) is not None and inside(strip, the_section(root))
    many.tracker.rename_project(1, "Alpha Two")
    renamed = project_root(many, f"?{OPEN}").by_id("confirm-sentence")
    assert renamed is not None and renamed.text() == sentence_for("Alpha Two", 4)


CHOICES = (
    "filter_status=todo&filter_status=&filter_label=&sort_field=title&sort_field=&sort_direction="
)
CARRIED = [
    ("filter_status", "todo"),
    ("filter_status", ""),
    ("filter_label", ""),
    ("sort_field", "title"),
    ("sort_field", ""),
    ("sort_direction", ""),
]
UNRELATED = "unrelated=1&move_task=1&rename_typed=x&title=y&created&deleted_task=Gone"


def test_project_deletion_preserves_only_filter_and_sort_choices(tmp_path: Path) -> None:
    """CP-572, T5: complete pairs, repeated and blank values reach the trigger, the confirming
    form, Back out and the failure page's trigger; no other key of the address is generated."""
    world = make_world(tmp_path)
    with_statuses(world, ("todo",))
    ordinary = project_root(world, f"?{CHOICES}&{UNRELATED}")
    assert hidden_pairs(trigger_form(ordinary) or ordinary) == CARRIED
    opened = project_root(world, f"?{OPEN}&{CHOICES}&{UNRELATED}")
    confirm, back = strips(opened)[0].find_all("form")
    assert hidden_pairs(confirm) == CARRIED
    assert hidden_pairs(back) == [(BACK, ""), *CARRIED]
    backed = project_root(world, f"?{BACK}&{CHOICES}&{UNRELATED}")
    assert hidden_pairs(trigger_form(backed) or backed) == CARRIED
    failed = project_root(world, f"?{FAILED}&{CHOICES}&{UNRELATED}")
    assert hidden_pairs(trigger_form(failed) or failed) == CARRIED
    plain = project_root(world, f"?{UNRELATED}")
    assert hidden_pairs(trigger_form(plain) or plain) == []


MARKERS = {
    "failure": FAILED,
    "confirmation": OPEN,
    "back-out": BACK,
}
COMBINATIONS = [
    (f"?{OPEN}&{BACK}&{FAILED}", "failure"),
    (f"?{OPEN}&{FAILED}", "failure"),
    (f"?{BACK}&{FAILED}", "failure"),
    (f"?{BACK}&{OPEN}", "confirmation"),
    (f"?{BACK}", "back-out"),
]
MOVE_NOISE = [
    "move_task=1&moved=in-progress",
    "move_task=1&move_confirm=cancelled",
    "move_task=1&move_back=cancelled",
    "move_task=1&move_failed=done",
    "move_task=1&move_refused=not-allowed",
    "move_task=999&move_confirm=cancelled",
    "move_task=999&moved=done",
    "deleted_task=Gone",
]


@pytest.mark.parametrize("noise", [*MOVE_NOISE, ""])
@pytest.mark.parametrize(("query", "winner"), COMBINATIONS)
def test_project_deletion_mode_precedence_controls_body_and_focus(
    tmp_path: Path, query: str, winner: str, noise: str
) -> None:
    """CP-573, CP-574, T6: failure before confirmation before back-out; every move marker and the
    deleted-task line is suppressed, even a move naming a task nothing holds; exactly one focus."""
    world = make_world(tmp_path)
    with_statuses(world, ("todo",))
    root = project_root(world, f"{query}&{noise}" if noise else query)
    if winner == "confirmation":
        assert len(strips(root)) == 1 and trigger_form(root) is None
        assert [e.attrs.get("id") for e in focused(root)] == ["confirm-sentence"]
    else:
        assert strips(root) == []
        assert focused(root) == [trigger_of(root)]
        assert (root.by_id(FAILURE_ID) is not None) == (winner == "failure")
    assert root.by_id("move-line") is None and root.by_id("deleted-line") is None
    assert root.by_id("list-section") is None
    assert "You deleted" not in root.text() and "Traceback" not in root.text()


def test_without_a_deletion_marker_the_earlier_precedence_holds(tmp_path: Path) -> None:
    """CP-574, T6: a move or completion address with no project deletion marker is answered as it
    was: the deleted-task line shows, and a move naming no task is the task not-found page."""
    world = make_world(tmp_path)
    with_statuses(world, ("todo",))
    done = project_root(world, "?deleted_task=Gone")
    assert done.by_id("deleted-line") is not None
    assert get(world.site, "/projects/1?move_task=999&move_confirm=cancelled").status == 404
    assert trigger_of(done).attrs.get("autofocus", False) is False


def test_back_out_and_failure_focus_the_trigger_with_the_right_line(tmp_path: Path) -> None:
    """CP-573, CP-578, T6: Back out puts the trigger back in place with focus and shows no line;
    a failure focuses the same trigger, described by the one failure line."""
    world = make_world(tmp_path, projects=("Alpha",))
    with_statuses(world, ("todo",))
    backed = project_root(world, f"?{BACK}")
    trigger = trigger_of(backed)
    assert focused(backed) == [trigger] and "aria-describedby" not in trigger.attrs
    assert strips(backed) == [] and backed.by_id(FAILURE_ID) is None
    assert "You deleted" not in backed.text() and "couldn't delete" not in backed.text()
    failed = project_root(world, f"?{FAILED}")
    trigger = trigger_of(failed)
    assert focused(failed) == [trigger]
    (line,) = trigger.described_by()
    assert line.attrs["id"] == FAILURE_ID
    assert line.text() == (
        "The tracker couldn't delete the project 'Alpha', and nothing was changed. Try again."
    )
    assert strips(failed) == []


def test_project_deletion_keeps_rename_and_add_displays_with_one_focus(tmp_path: Path) -> None:
    """CP-574, T7: while a deletion state shows, the rename area and the add-task form keep what
    their own keys ask for, but neither takes focus; with no deletion state they do as before."""
    world = make_world(tmp_path, projects=("Alpha",))
    with_statuses(world, ("todo",))
    rename = "rename_refused=blank-name&rename_typed=Typed+name"
    adding = "task_refused=blank-title&title=Typed+title"
    for marker, owner in ((OPEN, "confirm-sentence"), (BACK, None), (FAILED, None)):
        root = project_root(world, f"?{marker}&{rename}&{adding}")
        field = root.by_id("project-name")
        assert field is not None and field.attrs["value"] == "Typed name"
        assert root.by_id("rename-outcome") is not None
        title = root.by_id("task-title")
        assert title is not None and title.attrs["value"] == "Typed title"
        assert root.by_id("add-task-failure") is None
        (target,) = focused(root)
        if owner is not None:
            assert target.attrs["id"] == owner
        else:
            assert target is trigger_of(root)
    failed_add = project_root(world, f"?{OPEN}&task_failed=add&title=x")
    assert failed_add.by_id("add-task-failure") is not None
    assert [e.attrs.get("id") for e in focused(failed_add)] == ["confirm-sentence"]
    assert all("autofocus" not in f.attrs for f in failed_add.find_all("form"))
    without = project_root(world, f"?{rename}")
    assert [e.attrs.get("id") for e in focused(without)] == ["project-name"]


def test_a_typed_value_holding_autofocus_survives_the_focus_suppression(tmp_path: Path) -> None:
    """T7: only the page's own attribute is removed; a typed value that contains the word stays."""
    world = make_world(tmp_path, projects=("Alpha",))
    typed = 'my autofocus " autofocus x'
    root = project_root(world, f"?{OPEN}&rename_typed={typed}&rename_failed=save")
    field = root.by_id("project-name")
    assert field is not None and field.attrs["value"] == typed
    assert [e.attrs.get("id") for e in focused(root)] == ["confirm-sentence"]


def landing(world: World, name: str, count: str | None) -> Element:
    pairs = f"deleted_project={name}" + (f"&deleted_project_tasks={count}" if count else "")
    response = get(world.site, f"/?{pairs}")
    assert response.status in (200,)
    return parse(response.body.decode("utf-8"))


@pytest.mark.parametrize("count", [0, 1, 2, 13])
def test_projects_completion_covers_zero_one_many_and_empty_projects(
    tmp_path: Path, count: int
) -> None:
    """CP-576, T7: the heading takes focus and is described by the one line, at the page start,
    with a project left and with none; a zero count is accepted."""
    world = make_world(tmp_path, projects=("Beta",))
    root = landing(world, "Alpha", str(count))
    (heading,) = focused(root)
    assert heading.tag == "h1" and heading.text() == "Projects"
    (line,) = heading.described_by()
    assert line.text() == completion_for("Alpha", count)
    assert [e for e in root.walk() if "You deleted" in e.text() and e.tag == "p"] == [line]
    assert "Beta" in root.text()
    empty = make_world(tmp_path / "again", projects=())
    shown = landing(empty, "Only", str(count))
    (heading,) = focused(shown)
    assert heading.tag == "h1"
    assert heading.described_by()[0].text() == completion_for("Only", count)
    assert "There are no projects yet." in shown.text()


@pytest.mark.parametrize(
    ("query", "label"),
    [
        ("deleted_project=Alpha", "no count"),
        ("deleted_project_tasks=3", "no name"),
        ("deleted_project=Alpha&deleted_project_tasks=", "blank count"),
        ("deleted_project=Alpha&deleted_project_tasks=-1", "negative"),
        ("deleted_project=Alpha&deleted_project_tasks=1.5", "decimal"),
        ("deleted_project=Alpha&deleted_project_tasks=two", "word"),
        ("deleted_project=Alpha&deleted_project_tasks=007", "padded"),
        ("deleted_project=Alpha&deleted_project_tasks=%D9%A3", "other digits"),
        ("deleted_project=&deleted_project_tasks=3", "blank name"),
        # More digits than Python reads as an int: no deletion removed that many tasks, so it is no
        # count, and the page must not fail on it.
        (f"deleted_project=Alpha&deleted_project_tasks={'9' * 5000}", "too long to read"),
    ],
)
def test_malformed_or_incomplete_completions_are_ignored(
    tmp_path: Path, query: str, label: str
) -> None:
    """CP-576, T7: an incomplete or malformed pair gives the ordinary Projects page, 200 without
    the no-store header, whatever else the address carries."""
    world = make_world(tmp_path, projects=("Beta",))
    plain = get(world.site, "/")
    shown = get(world.site, f"/?{query}")
    assert shown.status == 200 and shown.body == plain.body, label
    assert all(key.lower() != "cache-control" for key, _ in shown.headers), label


def test_project_deletion_names_remain_text(tmp_path: Path) -> None:
    """CP-577, T7: `<b>R&D "x"</b>` and surrounding whitespace survive as typed text in the
    confirmation, the failure line and the completion, with no element or attribute injected."""
    name = ' <b>R&D "x"</b> '
    world = make_world(tmp_path, projects=(name,))
    with_statuses(world, ("todo", "done"))
    opened = project_root(world, f"?{OPEN}")
    sentence = opened.by_id("confirm-sentence")
    assert sentence is not None and sentence.text() == sentence_for(name, 2)
    failed = project_root(world, f"?{FAILED}")
    (line,) = trigger_of(failed).described_by()
    assert f"project '{name}'," in line.text()
    for root in (opened, failed):
        assert root.find_all("b") == []
    done = landing(world, "%20%3Cb%3ER%26D%20%22x%22%3C%2Fb%3E%20", "2")
    (heading,) = focused(done)
    assert heading.described_by()[0].text() == completion_for(name, 2)
    assert done.find_all("b") == []
