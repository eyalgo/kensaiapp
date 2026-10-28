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
    FIELD_NAMES,
    control,
    filter_form,
    labelled,
    project,
    rows_of,
    shown_in_field,
    three_task_world,
)
from test_pages import Element
from test_task_routes import focused, make_world, utc_zone  # noqa: F401

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
