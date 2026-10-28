"""Integration tests of the Rename area on a project's Tasks view, each page read as a browser
parses it (layer 4, with the states reached through the real Site).

Checks SRS FR-10 and FR-39 (the naming rules and the maximum length), FR-12 (renaming a project),
NFR-5 (typed text is shown as text), UXD UX-F10 (the Rename area), UX-I3 to UX-I5 and UX-A3, and
acceptance criteria AC-12 and AC-18. Change spec rules CP-546 to CP-550, CP-553, CP-556, CP-557 and
CP-564 and NFDR QC-9 and QC-36 are the ones each test names. The tests check where a line sits and
which control it describes, and use the words of this change's text record only where a test
names them.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from test_pages import Element, parse
from test_routes import get
from test_task_routes import World, add_task, focused, make_world

from application import SHORT_TEXT_MAX, Project
from web import pages

SAVED = "  Alpha  "


def rename_form(root: Element) -> Element:
    (form,) = [f for f in root.find_all("form") if (f.attrs["action"] or "").endswith("/rename")]
    return form


def name_field(root: Element) -> Element:
    (field,) = rename_form(root).find_all("input")
    return field


def save_button(root: Element) -> Element:
    (button,) = rename_form(root).find_all("button")
    return button


def shown(world: World, query: str = "") -> Element:
    response = get(world.site, f"/projects/1{query}")
    assert response.status in (200, 202), query
    return parse(response.body.decode("utf-8"))


def world_with_tasks(tmp_path: Path) -> World:
    world = make_world(tmp_path, projects=(SAVED,))
    add_task(world.site, title="One")
    add_task(world.site, title="Two")
    return world


def assert_area_is_last_and_ordinary(root: Element, saved: str = SAVED) -> None:
    (main,) = root.find_all("main")
    (last,) = [c for c in main.children if isinstance(c, Element)][-1:]
    assert rename_form(root) in list(last.walk())
    inputs = list(rename_form(root).walk())
    assert inputs.index(name_field(root)) < inputs.index(save_button(root))
    assert name_field(root).attrs["value"] == saved
    assert "aria-describedby" not in name_field(root).attrs
    assert "aria-describedby" not in save_button(root).attrs


EMPTY_STATES = [
    "",
    "?created",
    "?task_refused=blank-title",
    "?task_failed=add&title=x",
    "?filter_status=bogus",
    "?deleted_task=Gone",
]
LISTED_STATES = [
    "",
    "?filter_status=done",
    "?filter_status=bogus",
    "?sort_field=bogus",
    "?created",
    "?task_refused=blank-title",
    "?task_failed=add&title=x",
    "?move_task=1&moved=in-progress",
    "?filter_status=done&move_task=1&moved=in-progress",
    "?move_confirm=cancelled&move_task=1",
    "?move_back=cancelled&move_task=1",
    "?deleted_task=Gone",
]


def test_every_tasks_view_state_has_the_rename_area(tmp_path: Path) -> None:
    """CP-546, CP-564: with tasks, without, with no matches, with a refused filter or sort, and
    under every completion, refusal, failure and confirmation, the area is the page's last part,
    the saved name exact, the field before Save, and the page never has two autofocus elements."""
    empty = make_world(tmp_path / "empty", projects=(SAVED,))
    listed = world_with_tasks(tmp_path / "listed")
    for world, states in ((empty, EMPTY_STATES), (listed, LISTED_STATES)):
        for query in states:
            root = shown(world, query)
            assert name_field(root).attrs["value"] == SAVED, query
            (main,) = root.find_all("main")
            (last,) = [c for c in main.children if isinstance(c, Element)][-1:]
            assert rename_form(root) in list(last.walk()), query
            ordered = list(rename_form(root).walk())
            assert ordered.index(name_field(root)) < ordered.index(save_button(root)), query
            assert len(focused(root)) <= 1, query
            assert "aria-describedby" not in name_field(root).attrs, query
            assert "aria-describedby" not in save_button(root).attrs, query
    assert_area_is_last_and_ordinary(shown(listed))


@pytest.mark.parametrize(
    "outcome",
    [
        "?created",
        "?deleted_task=Gone",
        "?move_task=1&moved=in-progress",
        "?move_confirm=cancelled&move_task=1",
        "?task_refused=blank-title",
    ],
)
@pytest.mark.parametrize(
    "forged",
    [
        "rename_saved=Forged&rename_from=Old",
        "rename_refused=blank-name&rename_typed=Forged",
        "rename_failed=save&rename_typed=Forged",
    ],
)
def test_an_existing_outcome_keeps_the_focus_over_forged_rename_markers(
    tmp_path: Path, outcome: str, forged: str
) -> None:
    """CP-546: a hand-written combined address leaves the existing outcome's one focus alone and
    shows the ordinary Rename area, with no line and no typed text."""
    world = world_with_tasks(tmp_path)
    root = shown(world, f"{outcome}&{forged}")
    assert len(focused(root)) == 1
    assert name_field(root).attrs["value"] == SAVED
    assert "aria-describedby" not in name_field(root).attrs
    assert "aria-describedby" not in save_button(root).attrs
    assert "Forged" not in root.text()


def test_the_rename_focus_is_not_taken_by_text_that_looks_like_an_attribute(
    tmp_path: Path,
) -> None:
    """CP-546, CP-561: a task title reading `autofocus` in a value or in text does not stand for an
    autofocus element, so a completed rename still focuses its field."""
    world = make_world(tmp_path, projects=("Alpha",))
    add_task(world.site, title="a autofocus b")
    add_task(world.site, title='x" autofocus="')
    root = shown(world, "?rename_saved=Beta&rename_from=Alpha")
    assert focused(root) == [name_field(root)]


def test_rename_control_has_label_limit_and_no_limit_sentence(tmp_path: Path) -> None:
    """CP-546, CP-547, CP-564, QC-9: a visible label, `maxlength` equal to the application's
    export, one POST naming this project with no old-name or shown-name field and no maximum
    sentence; no other page offers a rename."""
    world = world_with_tasks(tmp_path)
    root = shown(world)
    form = rename_form(root)
    assert form.attrs["method"] == "post" and form.attrs["action"] == "/projects/1/rename"
    field = name_field(root)
    assert field.attrs["type"] == "text" and field.attrs["name"] == "name"
    assert int(field.attrs["maxlength"] or 0) == SHORT_TEXT_MAX
    (label,) = form.find_all("label")
    assert label.attrs["for"] == field.attrs["id"] and label.text() == "Project name"
    assert save_button(root).text() == "Save" and save_button(root).attrs["type"] == "submit"
    assert [e.attrs.get("name") for e in form.find_all("input")] == ["name"]
    assert str(SHORT_TEXT_MAX) not in form.text() and "200" not in form.text()
    for target in ("/", "/tasks", "/people", "/projects/1/summary", "/tasks/1", "/projects/99"):
        other = parse(get(world.site, target).body.decode("utf-8"))
        actions = [f.attrs["action"] or "" for f in other.find_all("form")]
        assert not [a for a in actions if a.endswith("/rename")], target


def test_the_page_builder_shows_each_rename_outcome_by_the_closed_choice() -> None:
    """CP-550, CP-553, CP-556, CP-557: a refusal beats a failure and a failure beats a completion;
    blank and in-use keep the typed text, too long and a completion show the saved name, a failure
    focuses Save, and an absent area is an empty submission's opposite."""
    project = Project(id=3, name="Saved", description="")
    refusal = pages.ProjectNameRefusal

    def built(**area: object) -> Element:
        return parse(pages.project_page(project, rename_area=pages.ProjectRenameArea(**area)))  # type: ignore[arg-type]

    plain = parse(pages.project_page(project))
    assert name_field(plain).attrs["value"] == "Saved" and focused(plain) == []
    blank = built(typed="", refusal=refusal.BLANK_NAME, failed=True, saved="N", previous="O")
    assert focused(blank) == [name_field(blank)] and name_field(blank).attrs["value"] == ""
    in_use = built(typed="Taken", refusal=refusal.NAME_IN_USE)
    assert name_field(in_use).attrs["value"] == "Taken"
    assert "'Taken'" in name_field(in_use).described_by()[0].text()
    long = built(typed="Forged", refusal=refusal.TOO_LONG)
    assert name_field(long).attrs["value"] == "Saved" and "Forged" not in long.text()
    failed = built(typed="Wanted", failed=True, saved="N", previous="O")
    assert (
        focused(failed) == [save_button(failed)] and name_field(failed).attrs["value"] == "Wanted"
    )
    assert "'Wanted'" in save_button(failed).described_by()[0].text()
    done = built(saved="Saved", previous="Old")
    assert focused(done) == [name_field(done)]
    assert name_field(done).described_by()[0].text() == "You renamed 'Old' to 'Saved'."
    assert focused(built(typed="x")) == [] and focused(built(saved="Only")) == []
    absent = built(refusal=refusal.BLANK_NAME)
    assert name_field(absent).attrs["value"] == "Saved"
    assert name_field(absent).described_by()[0].text() == "A project needs a name. Type one."
