"""Integration tests of the project page's sort controls, each page read back as a browser parses it
(layer 4).

Realizes SRS FR-36 and FR-39 and NFR-9 for the page, and checks the change spec rules CP-426 to
CP-428, CP-435, CP-436, CP-441 to CP-443 and CP-445, the design's T5, T7 and T9, and NFDR QC-5,
QC-23 and QC-36. The page is built through the real Site over a real Tracker, so the controls are
read from the application's read model exactly as a browser is served them. Where a test checks
words, they are the strings of this change's text record.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from test_filter_pages import (
    FIELD_LABELS,
    FIELD_NAMES,
    control,
    filter_form,
    labelled,
    project,
    rows_of,
    shown_in_field,
    three_task_world,
)
from test_pages import Element, parse
from test_routes import get, page
from test_task_routes import World, focused, make_world, utc_zone  # noqa: F401

SORT_NAMES = ["sort_field", "sort_direction"]
SORT_LABELS = ["Sort by", "Direction"]

pytestmark = pytest.mark.usefixtures("utc_zone")


def selected_values(root: Element, name: str) -> list[str]:
    return [
        o.attrs["value"] for o in control(root, name).find_all("option") if "selected" in o.attrs
    ]


def attempts(root: Element, identifier: str) -> list[str]:
    area = root.by_id(f"{identifier}-attempt")
    assert area is not None, identifier
    return [child.text() for child in area.walk() if child.tag == "span"]


def test_nonempty_list_offers_nine_labelled_controls_in_one_form(tmp_path: Path) -> None:
    """CP-426, CP-436, T5: the seven filter controls, then Sort by and Direction, then the one Apply
    and Clear, each labelled; the offered choices and the defaults they show."""
    root = project(three_task_world(tmp_path))
    form = filter_form(root)
    named = [e.attrs["name"] for e in form.walk() if e.tag in ("select", "input")]
    assert named == [*FIELD_NAMES, *SORT_NAMES]
    assert [control(root, name).attrs["id"] for name in SORT_NAMES] == [
        "sort-field",
        "sort-direction",
    ]
    assert [
        labelled(root, identifier) for identifier in ("sort-field", "sort-direction")
    ] == SORT_LABELS
    field = control(root, "sort_field")
    assert field.tag == "select"
    assert [(o.attrs["value"], o.text()) for o in field.find_all("option")] == [
        ("due_date", "Due date"),
        ("priority", "Priority"),
        ("created_time", "Created time"),
        ("title", "Title"),
    ]
    direction = control(root, "sort_direction")
    assert direction.tag == "select"
    assert [(o.attrs["value"], o.text()) for o in direction.find_all("option")] == [
        ("ascending", "Ascending"),
        ("descending", "Descending"),
    ]
    assert selected_values(root, "sort_field") == ["due_date"]
    assert selected_values(root, "sort_direction") == ["ascending"]
    assert "aria-label" not in field.attrs and "aria-label" not in direction.attrs
    (apply_button,) = form.find_all("button")
    assert apply_button.text() == "Apply"
    (clear,) = form.find_all("a")
    assert clear.text() == "Clear" and clear.attrs["href"] == "/projects/1"
    everything = list(form.walk())
    assert everything.index(control(root, "filter_overdue")) < everything.index(field)
    assert everything.index(direction) < everything.index(apply_button)
    assert len([f for f in root.find_all("form") if f.attrs.get("method") == "get"]) == 1


def test_an_empty_project_has_no_controls_even_with_malformed_sort_choices(tmp_path: Path) -> None:
    """CP-426, T5: the first-task page, with no sort control and no refusal, for valid and malformed
    sort choices alike."""
    world = make_world(tmp_path)
    for query in (
        "",
        "sort_field=title",
        "sort_field=colour&sort_direction=up&sort_direction=down",
    ):
        root = project(world, query)
        assert [f.attrs.get("method") for f in root.find_all("form")] == ["post"], query
        assert root.find_all("table") == [] and "no tasks yet" in root.text(), query
        assert all(e.attrs.get("name") not in SORT_NAMES for e in root.walk()), query
        assert "Sort by" not in root.text() and "Apply" not in root.text(), query


def test_sort_controls_show_the_defaults_when_unset_independently(tmp_path: Path) -> None:
    """CP-428, CP-436, T5: no choice, blank choices and each control alone leave the other at its
    default; a Direction alone leaves Sort by at Due date."""
    world = three_task_world(tmp_path)
    for query, field, direction in (
        ("", "due_date", "ascending"),
        ("sort_field=&sort_direction=", "due_date", "ascending"),
        ("sort_field=priority", "priority", "ascending"),
        ("sort_direction=descending", "due_date", "descending"),
        ("sort_field=title&sort_direction=", "title", "ascending"),
        ("sort_field=&sort_direction=descending", "due_date", "descending"),
    ):
        root = project(world, query)
        assert selected_values(root, "sort_field") == [field], query
        assert selected_values(root, "sort_direction") == [direction], query


def test_count_appears_only_for_a_nonempty_sort_choice_in_the_sort_only_words(
    tmp_path: Path,
) -> None:
    """CP-435, T5: no count for an unset address, a blank sort or an unknown parameter; a count in
    the non-filter words for a sort alone, an explicit default and a direction alone."""
    world = three_task_world(tmp_path)
    for query in ("", "sort_field=&sort_direction=", "sorting=title"):
        text = project(world, query).text()
        assert "This project has" not in text and "this filter" not in text, query
    for query in (
        "sort_field=title",
        "sort_field=due_date&sort_direction=ascending",
        "sort_direction=descending",
    ):
        root = project(world, query)
        assert root.by_id("filter-count") is not None, query
        assert "This project has 3 tasks." in root.text(), query
        assert "this filter" not in root.text(), query
        assert "applied" not in root.text().lower(), query


def test_sort_only_count_for_one_task_uses_the_singular_words(tmp_path: Path) -> None:
    """CP-435, T5: a project of one task reads 'This project has 1 task.' after a sort."""
    world = make_world(tmp_path)
    world.tracker.add_task(1, "Only", "low", "", "")
    root = project(world, "sort_field=title")
    assert "This project has 1 task." in root.text()
    assert "1 tasks" not in root.text()


def test_a_filter_with_a_sort_keeps_the_filters_count_words(tmp_path: Path) -> None:
    """CP-435, T5: when a filter field is set the count keeps the filter's words, with or without a
    sort, and never the sort-only words."""
    world = three_task_world(tmp_path)
    both = project(world, "filter_status=todo&sort_field=title&sort_direction=descending")
    assert "3 tasks match this filter." in both.text()
    assert "This project has" not in both.text()
    one = project(world, "filter_priority=high&sort_field=priority")
    assert "1 task matches this filter." in one.text()
    assert selected_values(one, "filter_priority") == ["high"]
    assert selected_values(one, "sort_field") == ["priority"]


def test_zero_matches_keeps_the_existing_empty_state_with_or_without_a_sort(tmp_path: Path) -> None:
    """CP-435 reading, CP-401, T6: a valid filter that matches nothing shows the filter's sentence
    and Clear, no table, no separate count and no first-task invitation."""
    world = three_task_world(tmp_path)
    for query in (
        "filter_label=Bug",
        "filter_label=Bug&sort_field=title&sort_direction=descending",
    ):
        root = project(world, query)
        assert "No tasks match this filter. Press Clear to see every task." in root.text(), query
        assert root.find_all("table") == [] and "no tasks yet" not in root.text(), query
        assert root.by_id("filter-count") is None, query
        assert "This project has" not in root.text(), query
        assert [a.text() for a in filter_form(root).find_all("a")] == ["Clear"], query


REFUSED = [
    (
        "sort_field=colour",
        "sort_field",
        (
            "Sort by can't be 'colour', because the list doesn't sort by that. "
            "Pick Due date, Priority, Created time or Title."
        ),
    ),
    (
        "sort_field=Title",
        "sort_field",
        "Sort by can't be 'Title', because the list doesn't sort by that.",
    ),
    (
        "sort_field=%20title",
        "sort_field",
        "Sort by can't be ' title', because the list doesn't sort by that.",
    ),
    (
        "sort_direction=sideways",
        "sort_direction",
        (
            "Direction can't be 'sideways', because the list doesn't sort that way. "
            "Pick Ascending or Descending."
        ),
    ),
    (
        "sort_direction=Ascending",
        "sort_direction",
        "Direction can't be 'Ascending', because the list doesn't sort that way.",
    ),
    (
        "sort_field=title&sort_field=title",
        "sort_field",
        "Sort by takes one value, not 2. Pick Due date, Priority, Created time or Title.",
    ),
    (
        "sort_field=&sort_field=",
        "sort_field",
        "Sort by takes one value, not 2. Pick Due date, Priority, Created time or Title.",
    ),
    (
        "sort_field=title&sort_field=&sort_field=priority",
        "sort_field",
        "Sort by takes one value, not 3.",
    ),
    (
        "sort_direction=ascending&sort_direction=descending",
        "sort_direction",
        "Direction takes one value, not 2. Pick Ascending or Descending.",
    ),
    (
        "sort_direction=&sort_direction=",
        "sort_direction",
        "Direction takes one value, not 2. Pick Ascending or Descending.",
    ),
]


@pytest.mark.parametrize(("query", "name", "words"), REFUSED)
def test_each_sort_refusal_shows_its_reason_at_its_field(
    tmp_path: Path, query: str, name: str, words: str
) -> None:
    """CP-441, CP-442, CP-443, T7: the reason sits at its control and describes it, one autofocus
    lands there, no table or count shows, and Clear is in view."""
    root = project(three_task_world(tmp_path), query)
    reason = control(root, name).described_by()
    assert len(reason) == 1 and words in reason[0].text()
    assert [e.attrs.get("name") for e in focused(root)] == [name]
    assert root.find_all("table") == []
    assert root.by_id("filter-count") is None and "This project has" not in root.text()
    assert [a.text() for a in filter_form(root).find_all("a")] == ["Clear"]


def test_a_refused_sort_keeps_every_choice_as_sent(tmp_path: Path) -> None:
    """CP-442, T7: the refused control holds its value exactly as sent, the repeated values show as
    attempts, and the filter choices beside it stay."""
    world = three_task_world(tmp_path)
    invalid = project(world, "filter_priority=high&sort_field=colour&sort_direction=descending")
    assert shown_in_field(invalid, "filter_priority") == ["high"]
    assert selected_values(invalid, "sort_field") == ["colour"]
    assert selected_values(invalid, "sort_direction") == ["descending"]
    repeated = project(world, "sort_field=title&sort_field=&sort_field=priority")
    assert attempts(repeated, "sort-field") == ["title", "", "priority"]
    assert selected_values(repeated, "sort_field") == ["due_date"]
    both = project(world, "sort_direction=up&sort_direction=down")
    assert attempts(both, "sort-direction") == ["up", "down"]
    assert selected_values(both, "sort_direction") == ["ascending"]


def test_the_first_refused_control_alone_takes_the_focus(tmp_path: Path) -> None:
    """CP-442, T7: a reversed range with an invalid Direction focuses Due from; both sort controls
    refused focus Sort by; each refused control is still described by its own reason."""
    world = three_task_world(tmp_path)
    range_and_direction = project(
        world,
        "filter_due_from=2026-10-10&filter_due_to=2026-10-01&sort_direction=sideways",
    )
    assert [e.attrs.get("name") for e in focused(range_and_direction)] == ["filter_due_from"]
    (range_reason,) = control(range_and_direction, "filter_due_from").described_by()
    (direction_reason,) = control(range_and_direction, "sort_direction").described_by()
    assert "later than the Due to date" in range_reason.text()
    assert "Direction can't be 'sideways'" in direction_reason.text()
    assert "autofocus" not in control(range_and_direction, "sort_direction").attrs
    both = project(world, "sort_field=colour&sort_direction=sideways")
    assert [e.attrs.get("name") for e in focused(both)] == ["sort_field"]
    assert len(control(both, "sort_field").described_by()) == 1
    assert len(control(both, "sort_direction").described_by()) == 1
    filter_first = project(world, "filter_status=blocked&sort_field=colour")
    assert [e.attrs.get("name") for e in focused(filter_first)] == ["filter_status"]


def test_titles_and_refused_tokens_are_escaped(tmp_path: Path) -> None:
    """CP-445, T9: a title with markup characters shows as typed in title order, and a refused token
    holding markup cannot become markup in an option, a reason or an attempt."""
    world = make_world(tmp_path)
    world.tracker.add_task(1, '<b>&"x"', "low", "", "")
    world.tracker.add_task(1, "alpha", "low", "", "")
    root = project(world, "sort_field=title")
    assert rows_of(root) == ['<b>&"x"', "alpha"]
    assert root.find_all("b") == []
    markup = "%3Cb%3Eboom%3C%2Fb%3E"
    single = project(world, f"sort_field={markup}&sort_direction={markup}")
    assert selected_values(single, "sort_field") == ["<b>boom</b>"]
    assert "<b>boom</b>" in control(single, "sort_field").described_by()[0].text()
    assert single.find_all("b") == []
    repeated = project(world, f"sort_field={markup}&sort_field={markup}")
    assert attempts(repeated, "sort-field") == ["<b>boom</b>", "<b>boom</b>"]
    assert repeated.find_all("b") == []


def test_applying_a_sort_adds_no_message(tmp_path: Path) -> None:
    """CP-427, T5: no completion, applied or saved line stands on a sorted page."""
    root = project(three_task_world(tmp_path), "sort_field=priority&sort_direction=descending")
    text = root.text().lower()
    assert "applied" not in text and "saved" not in text and "sorted" not in text
    assert rows_of(root) == ["Write docs", "Ship", "Fix bug"]


# ---- All tasks: the page over every project (CP-459 to CP-466, CP-470, CP-474, T3, T4, T8, T10) ----

ALL_TASKS_COLUMNS = [
    "Title",
    "Project",
    "Status",
    "Priority",
    "Assignee",
    "Labels",
    "Due date",
    "Moves",
]
NO_TASKS_YET = "There are no tasks yet. Open Projects to add a task to a project."


def two_project_world(tmp_path: Path) -> World:
    """Alpha and Beta interleaved. By due date the order is 2, 1, 4, 3 (3 is undated); task 2 is
    overdue on the clock's day, 2026-10-11."""
    world = make_world(tmp_path, projects=("Alpha", "Beta"))
    world.tracker.add_task(1, "Write docs", "high", "Dana", "2026-10-20")
    world.tracker.add_task(2, "Fix bug", "low", " Ari", "2026-10-10")
    world.tracker.add_task(1, "Ship", "medium", "", "")
    world.tracker.add_task(2, "Plan", "critical", "", "2026-10-25")
    world.tracker.add_task_label(1, "bug")
    world.tracker.add_task_label(2, "ui")
    world.tracker.add_task_label(4, "Bug")
    return world


def offered(root: Element, name: str) -> list[str]:
    return [o.attrs["value"] or "" for o in control(root, name).find_all("option")]


def all_tasks(world: World, query: str = "", status: int = 200) -> Element:
    target = "/tasks" + (f"?{query}" if query else "")
    return parse(page(get(world.site, target), status))


def table_rows(root: Element) -> list[list[Element]]:
    (table,) = root.find_all("table")
    (body,) = table.find_all("tbody")
    return [row.find_all("td") for row in body.find_all("tr")]


def task_numbers(root: Element) -> list[int]:
    return [
        int(str(cells[0].find_all("a")[0].attrs["href"]).rsplit("/", 1)[1])
        for cells in table_rows(root)
    ]


def test_all_tasks_has_one_row_per_task_and_project_after_title(tmp_path: Path) -> None:
    """CP-462, CP-463, CP-464, CP-465, T3: title, one h1, eight headers, every task once in the
    default order, the project as a plain link, the row's own cells and no project controls."""
    world = two_project_world(tmp_path)
    saves = world.saver.saves
    root = all_tasks(world)
    assert [e.text() for e in root.find_all("title")] == ["All tasks - tracker17"]
    assert [e.text() for e in root.find_all("h1")] == ["All tasks"]
    (table,) = root.find_all("table")
    assert [th.text() for th in table.find_all("th")] == ALL_TASKS_COLUMNS
    assert task_numbers(root) == [2, 1, 4, 3]
    first = table_rows(root)[0]
    (title_link,) = first[0].find_all("a")
    assert title_link.attrs["aria-label"] == "Fix bug, number 1 on the task list"
    (project_link,) = first[1].find_all("a")
    assert (project_link.text(), project_link.attrs["href"]) == ("Beta", "/projects/2")
    assert "aria-label" not in project_link.attrs
    assert [cell.text() for cell in first[2:6]] == ["todo", "low", " Ari", "ui"]
    assert "2026-10-10" in first[6].text() and "Overdue" in first[6].text()
    assert [b.text() for b in first[7].find_all("button")] == ["in-progress", "cancelled"]
    assert table_rows(root)[3][5].text() == "none" and table_rows(root)[3][4].text() == "unassigned"
    assert [link.text() for link in table_rows(root)[2][1].find_all("a")] == ["Beta"]
    names = {e.attrs.get("name") for e in root.walk()}
    assert not names & {"title", "name", "description", "assignee", "priority"}
    text = root.text().lower()
    for absent in ("rename", "delete", "summary"):
        assert absent not in text, absent
    assert world.saver.saves == saves


def test_project_links_carry_no_choice_while_choices_are_applied(tmp_path: Path) -> None:
    """CP-463: with a filter and a sort applied, each Project cell still links to its project's
    page with no filter or sort choice in the address."""
    world = two_project_world(tmp_path)
    root = all_tasks(world, "filter_status=todo&sort_field=title&sort_direction=descending")
    assert task_numbers(root) == [1, 3, 4, 2]
    links = [cells[1].find_all("a") for cells in table_rows(root)]
    assert [[(a.text(), a.attrs["href"]) for a in cell] for cell in links] == [
        [("Alpha", "/projects/1")],
        [("Alpha", "/projects/1")],
        [("Beta", "/projects/2")],
        [("Beta", "/projects/2")],
    ]


def test_global_empty_page_precedes_controls_and_refusals(tmp_path: Path) -> None:
    """CP-466, T4: no project, or only empty projects, show the invitation under the heading and
    nothing else, whatever the address carries."""
    queries = [
        "",
        "filter_status=done&sort_field=title",
        "filter_status=nope&sort_field=colour&sort_direction=a&sort_direction=b",
        "filter_label=x&filter_label=y&filter_due_from=2026-10-20&filter_due_to=2026-10-01",
    ]
    for projects in ((), ("Alpha", "Beta")):
        world = make_world(tmp_path / f"p{len(projects)}", projects=projects)
        saves = world.saver.saves
        for query in queries:
            root = all_tasks(world, query)
            (main,) = root.find_all("main")
            children = [child for child in main.children if isinstance(child, Element)]
            assert [child.tag for child in children] == ["h1", "p"], query
            assert children[1].text() == NO_TASKS_YET, query
            (link,) = children[1].find_all("a")
            assert (link.text(), link.attrs["href"]) == ("Projects", "/"), query
            for tag in ("form", "table", "select", "input", "button"):
                assert root.find_all(tag) == [], (query, tag)
            assert "filter" not in main.text().lower() and "match" not in main.text(), query
        assert world.saver.saves == saves


def test_all_tasks_controls_and_options_cover_the_whole_scope(tmp_path: Path) -> None:
    """CP-467, CP-468, T5: nine labelled controls in order, one Apply and one Clear, assignees in
    list order, and every label of every task once in code-point order, before any matching."""
    world = two_project_world(tmp_path)
    root = all_tasks(world, "filter_status=done")
    form = filter_form(root)
    assert form.attrs["action"] == "/tasks" and "novalidate" in form.attrs
    names = [*FIELD_NAMES, *SORT_NAMES]
    assert [labelled(root, name.replace("_", "-")) for name in names] == [
        *FIELD_LABELS,
        *SORT_LABELS,
    ]
    assert [e.text() for e in form.find_all("button")] == ["Apply"]
    clear = [a for a in form.find_all("a") if a.text() == "Clear"]
    assert len(clear) == 1 and clear[0].attrs["href"] == "/tasks"
    assert offered(root, "filter_assignee") == ["", "Dana", " Ari"]
    assert offered(root, "filter_label") == ["", "Bug", "bug", "ui"]
    assert "applied" not in root.text().lower()


def test_global_count_and_no_match_states_use_the_read_model(tmp_path: Path) -> None:
    """CP-470, CP-471, T8: the filter's count, the sort-only count over the whole tracker, the
    no-match state without table or count, and no count without a choice."""
    world = two_project_world(tmp_path)
    assert "tasks match" not in all_tasks(world).text() and "The tracker has" not in (
        all_tasks(world).text()
    )
    one = all_tasks(world, "filter_priority=critical")
    assert "1 task matches this filter." in one.text() and task_numbers(one) == [4]
    two = all_tasks(world, "filter_status=todo&filter_label=bug")
    assert task_numbers(two) == [1] and "1 task matches this filter." in two.text()
    several = all_tasks(world, "filter_status=todo&sort_field=title")
    assert "4 tasks match this filter." in several.text()
    assert task_numbers(several) == [2, 4, 3, 1]
    only_sort = all_tasks(world, "sort_field=title&sort_direction=descending")
    assert "The tracker has 4 tasks." in only_sort.text()
    assert "filter" not in only_sort.by_id("filter-count").text()
    explicit_default = all_tasks(world, "sort_field=due_date&sort_direction=ascending")
    assert "The tracker has 4 tasks." in explicit_default.text()
    nothing = all_tasks(world, "filter_status=done&sort_field=title")
    assert "No tasks match this filter. Press Clear to see every task." in nothing.text()
    assert nothing.find_all("table") == [] and nothing.by_id("filter-count") is None
    assert "no tasks yet" not in nothing.text().lower()
    assert control(nothing, "filter_status").find_all("option")[0].text() == "Any status"
    single = make_world(tmp_path / "single", projects=("Alpha",))
    single.tracker.add_task(1, "Only", "low", "", "")
    assert "The tracker has 1 task." in all_tasks(single, "sort_field=title").text()


def test_every_global_choice_refusal_keeps_raw_values_and_first_field_focus(
    tmp_path: Path,
) -> None:
    """CP-474, T10: ordered reasons beside their fields, raw values kept, the first refused field
    owning the focus, no list, no count, Clear still offered, and nothing saved."""
    world = two_project_world(tmp_path)
    saves = world.saver.saves
    root = all_tasks(
        world,
        "filter_due_from=2026-10-20&filter_due_to=2026-10-01&filter_status=nope"
        "&filter_label=a&filter_label=b&sort_field=colour&sort_direction=up&sort_direction=down",
    )
    assert root.find_all("table") == [] and root.by_id("filter-count") is None
    assert [e.attrs.get("name") for e in focused(root)] == ["filter_status"]
    reasons = [
        control(root, name).described_by()[0].text()
        for name in (
            "filter_status",
            "filter_label",
            "filter_due_from",
            "sort_field",
            "sort_direction",
        )
    ]
    assert reasons[0].startswith("The status filter can't be 'nope'")
    assert reasons[1].startswith("The label filter takes one label, not 2.")
    assert reasons[2].startswith("The Due from date, 2026-10-20, is later than the Due to date")
    assert reasons[3].startswith("Sort by can't be 'colour'")
    assert reasons[4].startswith("Direction takes one value, not 2.")
    assert attempts(root, "filter-label") == ["a", "b"]
    assert any(a.text() == "Clear" for a in filter_form(root).find_all("a"))
    assert world.saver.saves == saves
    repeated_assignee = all_tasks(world, "filter_assignee=Dana&filter_assignee=Dana")
    assert "The assignee filter takes one name, not 2." in repeated_assignee.text()
    unlisted = all_tasks(world, "filter_assignee=Zed&sort_field=title")
    assert "The name 'Zed' isn't on the assignee list." in unlisted.text()


def test_global_typed_values_are_text_in_every_rendered_context(tmp_path: Path) -> None:
    """CP-479, T15: project names, titles, labels and assignees with markup characters are text in
    cells, options, hidden fields and accessible names; the table keeps its scroll wrapper."""
    hostile = '<b>&"x"'
    world = make_world(tmp_path, people=(hostile,), projects=(hostile, "Beta"))
    world.tracker.add_task(1, hostile, "low", hostile, "")
    world.tracker.add_task_label(1, hostile)
    page_text = page(get(world.site, "/tasks?filter_label=" + "%3Cb%3E%26%22x%22"))
    root = parse(page_text)
    assert root.find_all("b") == [] and "<b>&" not in page_text
    (cells,) = table_rows(root)
    assert cells[0].text() == hostile and cells[1].text() == hostile
    assert cells[4].text() == hostile and cells[5].text() == hostile
    assert cells[0].find_all("a")[0].attrs["aria-label"] == f"{hostile}, number 1 on the task list"
    assert all(hostile in b.attrs["aria-label"] for b in cells[7].find_all("button")), "move names"
    assert offered(root, "filter_assignee") == ["", hostile]
    (table,) = root.find_all("table")
    wrapper = table.parent
    assert wrapper is not None and wrapper.attrs["class"] == "table-scroll"
    assert root.find_all("script") == []
