"""Integration tests of the project page's filter area, each page read back as a browser parses it
(layer 4).

Realizes SRS FR-32 to FR-35 and FR-39 and NFR-9 for the page, and checks the change spec rules
CP-393 to CP-395, CP-398, CP-401 to CP-406, CP-411, CP-412 and CP-416, the design's T5, T7 and T9,
and NFDR QC-16, QC-23 and QC-36. The page is built through the real Site over a real Tracker, so
the area is read from the application's read model exactly as a browser is served it. Where a test
checks words, they are the strings of this change's text record.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from urllib.parse import quote

import pytest
from test_pages import Element, parse
from test_routes import get, page
from test_task_routes import World, focused, make_world, utc_zone  # noqa: F401

FIELD_LABELS = ["Status", "Priority", "Assignee", "Label", "Due from", "Due to", "Overdue"]
FIELD_NAMES = [
    "filter_status",
    "filter_priority",
    "filter_assignee",
    "filter_label",
    "filter_due_from",
    "filter_due_to",
    "filter_overdue",
]

pytestmark = pytest.mark.usefixtures("utc_zone")


def three_task_world(tmp_path: Path) -> World:
    """Dana and ' Ari' on the list; task 1 overdue and labelled, 2 later, 3 undated."""
    world = make_world(tmp_path)
    world.tracker.add_task(1, "Write docs", "high", "Dana", "2026-10-01")
    world.tracker.add_task(1, "Fix bug", "low", " Ari", "2026-10-20")
    world.tracker.add_task(1, "Ship", "medium", "", "")
    world.tracker.add_task_label(1, "bug")
    world.tracker.add_task_label(2, "ui")
    return world


def project(world: World, query: str = "", status: int = 200) -> Element:
    target = "/projects/1" + (f"?{query}" if query else "")
    return parse(page(get(world.site, target), status))


def filter_form(root: Element) -> Element:
    (form,) = [f for f in root.find_all("form") if f.attrs.get("method") == "get"]
    return form


def control(root: Element, name: str) -> Element:
    (found,) = [
        e for e in filter_form(root).walk() if e.attrs.get("name") == name and e.tag != "form"
    ]
    return found


def labelled(root: Element, identifier: str) -> str:
    (label,) = [e for e in filter_form(root).find_all("label") if e.attrs.get("for") == identifier]
    return label.text()


def rows_of(root: Element) -> list[str]:
    (table,) = root.find_all("table")
    return [a.text() for a in table.find_all("a")]


def reason_of(root: Element, name: str) -> Element | None:
    return control(root, name).described_by()[0] if control(root, name).described_by() else None


def test_nonempty_project_offers_labelled_filter_controls(tmp_path: Path) -> None:
    """CP-393, CP-394, CP-395, T5: seven labelled controls above the list, four values in each
    enumerated list, names and labels from the project, and Apply and Clear after them."""
    root = project(three_task_world(tmp_path))
    form = filter_form(root)
    assert form.attrs["action"] == "/projects/1" and "novalidate" in form.attrs
    assert [control(root, name).attrs["id"] for name in FIELD_NAMES] == [
        name.replace("_", "-") for name in FIELD_NAMES
    ]
    assert [labelled(root, name.replace("_", "-")) for name in FIELD_NAMES] == FIELD_LABELS
    status = control(root, "filter_status")
    assert [o.attrs["value"] for o in status.find_all("option")] == [
        "",
        "todo",
        "in-progress",
        "done",
        "cancelled",
    ]
    assert [o.text() for o in status.find_all("option")][0] == "Any status"
    priority = control(root, "filter_priority")
    assert [o.attrs["value"] for o in priority.find_all("option")] == [
        "",
        "low",
        "medium",
        "high",
        "critical",
    ]
    assert [o.text() for o in priority.find_all("option")][0] == "Any priority"
    assignee = control(root, "filter_assignee")
    assert [o.attrs["value"] for o in assignee.find_all("option")] == ["", "Dana", " Ari"]
    assert [o.text() for o in assignee.find_all("option")][0] == "Any assignee"
    label = control(root, "filter_label")
    assert [o.attrs["value"] for o in label.find_all("option")] == ["", "bug", "ui"]
    assert [o.text() for o in label.find_all("option")][0] == "Any label"
    assert control(root, "filter_due_from").attrs["type"] == "date"
    assert control(root, "filter_due_to").attrs["type"] == "date"
    overdue = control(root, "filter_overdue")
    assert overdue.attrs["type"] == "checkbox" and overdue.attrs["value"] == "on"
    assert priority.attrs["aria-label"] == "Priority filter"
    assert assignee.attrs["aria-label"] == "Assignee filter"
    (apply_button,) = form.find_all("button")
    assert apply_button.text() == "Apply" and apply_button.attrs["type"] == "submit"
    (clear,) = form.find_all("a")
    assert clear.text() == "Clear" and clear.attrs["href"] == "/projects/1"
    everything = list(root.walk())
    assert everything.index(form) < everything.index(root.find_all("table")[0])
    assert rows_of(root) == ["Write docs", "Fix bug", "Ship"]


def test_empty_project_retains_first_task_page_without_filters(tmp_path: Path) -> None:
    """CP-393, T5: an empty project shows the invitation and one add form, no filter controls,
    for valid and malformed choices alike."""
    world = make_world(tmp_path)
    for query in ("", "filter_status=todo", "filter_status=blocked&filter_status=todo"):
        root = project(world, query)
        forms = root.find_all("form")
        assert [f.attrs.get("method") for f in forms] == ["post"], query
        assert root.find_all("table") == [] and "no tasks yet" in root.text()
        assert root.find_all("select")[0].attrs["name"] != "filter_status"
        assert "Apply" not in root.text() and "Clear" not in root.text()


def test_unset_controls_show_no_filter_count(tmp_path: Path) -> None:
    """CP-395, CP-398, T5: no count or applied message for unset or singleton-empty fields, and an
    unknown parameter adds no filter."""
    world = three_task_world(tmp_path)
    for query in (
        "",
        "filter_status=&filter_priority=&filter_overdue=",
        "unknown=todo&filter_extra=1",
    ):
        root = project(world, query)
        assert "match this filter" not in root.text(), query
        assert rows_of(root) == ["Write docs", "Fix bug", "Ship"], query


def test_count_is_a_sentence_for_one_and_for_several(tmp_path: Path) -> None:
    """CP-398: the count words, one or several, above the list."""
    world = three_task_world(tmp_path)
    one = project(world, "filter_status=todo&filter_priority=high")
    assert "1 task matches this filter." in one.text()
    several = project(world, "filter_status=todo")
    assert "3 tasks match this filter." in several.text()


def test_no_matches_keeps_choices_and_clear_without_an_empty_project_message(
    tmp_path: Path,
) -> None:
    """CP-401, T5: a retained unmatched label, the filter's empty sentence, Clear in view, and no
    table, no count and no first-task invitation."""
    root = project(three_task_world(tmp_path), "filter_label=Bug")
    assert "No tasks match this filter. Press Clear to see every task." in root.text()
    assert root.find_all("table") == [] and "no tasks yet" not in root.text()
    assert "match this filter." not in root.text().replace(
        "No tasks match this filter. Press Clear to see every task.", ""
    )
    label = control(root, "filter_label")
    selected = [o for o in label.find_all("option") if "selected" in o.attrs]
    assert [(o.attrs["value"], o.text()) for o in selected] == [("Bug", "Bug")]
    assert [a.text() for a in filter_form(root).find_all("a")] == ["Clear"]


def test_controls_hold_the_chosen_values_after_an_apply(tmp_path: Path) -> None:
    """CP-395, CP-396: every chosen value shows in its control."""
    query = (
        "filter_status=todo&filter_priority=high&filter_assignee=Dana&filter_label=bug"
        "&filter_due_from=2026-10-01&filter_due_to=2026-10-05&filter_overdue=on"
    )
    root = project(three_task_world(tmp_path), query)
    for name, value in (
        ("filter_status", "todo"),
        ("filter_priority", "high"),
        ("filter_assignee", "Dana"),
        ("filter_label", "bug"),
    ):
        picked = [o for o in control(root, name).find_all("option") if "selected" in o.attrs]
        assert [o.attrs["value"] for o in picked] == [value], name
    assert control(root, "filter_due_from").attrs["value"] == "2026-10-01"
    assert control(root, "filter_due_to").attrs["value"] == "2026-10-05"
    assert "checked" in control(root, "filter_overdue").attrs
    assert rows_of(root) == ["Write docs"]


REFUSED = [
    ("filter_status=blocked", "filter_status", "The status filter can't be 'blocked'"),
    ("filter_priority=urgent", "filter_priority", "The priority filter can't be 'urgent'"),
    ("filter_assignee=carol", "filter_assignee", "The name 'carol' isn't on the assignee list."),
    (
        "filter_due_from=2026-02-30",
        "filter_due_from",
        "The Due from date can't be '2026-02-30', because it isn't a calendar date.",
    ),
    (
        "filter_due_to=2026-02-30",
        "filter_due_to",
        "The Due to date can't be '2026-02-30', because it isn't a calendar date.",
    ),
    (
        "filter_due_from=2026-10-10&filter_due_to=2026-10-01",
        "filter_due_from",
        "The Due from date, 2026-10-10, is later than the Due to date, 2026-10-01.",
    ),
    (
        "filter_overdue=maybe",
        "filter_overdue",
        "The Overdue filter can't be 'maybe', because it's either on or off.",
    ),
    ("filter_status=todo&filter_status=done", "filter_status", "takes one status, not 2."),
    ("filter_priority=low&filter_priority=low", "filter_priority", "takes one priority, not 2."),
    ("filter_assignee=&filter_assignee=", "filter_assignee", "takes one name, not 2."),
    ("filter_label=a&filter_label=b&filter_label=c", "filter_label", "takes one label, not 3."),
    ("filter_due_from=&filter_due_from=", "filter_due_from", "Due from takes one date, not 2."),
    ("filter_due_to=x&filter_due_to=y", "filter_due_to", "Due to takes one date, not 2."),
    (
        "filter_overdue=on&filter_overdue=on",
        "filter_overdue",
        "The Overdue filter takes one value, not 2.",
    ),
]


@pytest.mark.parametrize(("query", "name", "words"), REFUSED)
def test_each_refusal_shows_its_reason_at_its_field(
    tmp_path: Path, query: str, name: str, words: str
) -> None:
    """CP-402 to CP-406, T7: the reason sits at its field and describes it, one autofocus lands
    there, and no result table, count or no-match line shows, with Clear in view."""
    root = project(three_task_world(tmp_path), query)
    reason = control(root, name).described_by()
    assert len(reason) == 1 and words in reason[0].text()
    assert [e.attrs.get("name") for e in focused(root)] == [name]
    assert root.find_all("table") == []
    assert "match this filter" not in root.text() and "No tasks match" not in root.text()
    assert [a.text() for a in filter_form(root).find_all("a")] == ["Clear"]


def test_the_assignee_reason_has_its_own_form_when_the_list_is_empty(tmp_path: Path) -> None:
    """CP-403, wording decision: with no names on the list, the reason offers only Any assignee."""
    world = make_world(tmp_path, people=())
    world.tracker.add_task(1, "Only")
    root = project(world, "filter_assignee=carol")
    (reason,) = control(root, "filter_assignee").described_by()
    assert reason.text() == "The name 'carol' isn't on the assignee list. Pick Any assignee."
    repeated = project(world, "filter_assignee=a&filter_assignee=b")
    (again,) = control(repeated, "filter_assignee").described_by()
    assert again.text() == "The assignee filter takes one name, not 2. Pick Any assignee."
    labels = project(world, "filter_label=a&filter_label=b")
    (word,) = control(labels, "filter_label").described_by()
    assert word.text() == "The label filter takes one label, not 2. Pick Any label."


def test_simultaneous_refusals_focus_only_the_first_field(tmp_path: Path) -> None:
    """CP-405, T7: a bad Status and a reversed range both show, one autofocus on Status, and every
    refused field is described by its own reason."""
    root = project(
        three_task_world(tmp_path),
        "filter_status=blocked&filter_due_from=2026-10-10&filter_due_to=2026-10-01",
    )
    assert [e.attrs.get("name") for e in focused(root)] == ["filter_status"]
    (status,) = control(root, "filter_status").described_by()
    (range_reason,) = control(root, "filter_due_from").described_by()
    assert "can't be 'blocked'" in status.text() and "later than the Due to date" in range_reason.text()
    assert "autofocus" not in control(root, "filter_due_from").attrs
    assert control(root, "filter_due_to").described_by() == []


def attempt_values(root: Element, name: str) -> list[str]:
    area = root.by_id(f"{name.replace('_', '-')}-attempt")
    assert area is not None, name
    return [child.text() for child in area.walk() if child.tag == "span"]


def test_malformed_and_repeated_attempts_remain_visible(tmp_path: Path) -> None:
    """CP-405, design 3 C, T7: every raw date, invalid overdue token and repeated value, blank
    duplicates included, is shown in its field's area, escaped; the correction control keeps its
    single-value shape and a corrected Apply is accepted."""
    world = three_task_world(tmp_path)
    root = project(
        world,
        "filter_due_from=2026-02-30&filter_overdue=maybe&filter_label=a&filter_label=&filter_label=%3Cb%3E",
    )
    assert attempt_values(root, "filter_due_from") == ["2026-02-30"]
    assert attempt_values(root, "filter_overdue") == ["maybe"]
    assert attempt_values(root, "filter_label") == ["a", "", "<b>"]
    assert "<b>" not in [e.tag for e in root.walk()]
    assert control(root, "filter_due_from").attrs.get("value", "") == ""
    assert "checked" not in control(root, "filter_overdue").attrs
    assert [o.attrs["value"] for o in control(root, "filter_label").find_all("option")] == [
        "",
        "bug",
        "ui",
    ]
    corrected = project(world, "filter_label=bug&filter_due_from=2026-10-01")
    assert rows_of(corrected) == ["Write docs"] and focused(corrected) == []


def test_a_removed_assignee_is_refused_even_when_a_task_still_carries_it(tmp_path: Path) -> None:
    """CP-403, T6: choices use the current list, so an old address shows the assignee reason."""
    world = three_task_world(tmp_path)
    world.tracker.remove_assignee("Dana")
    root = project(world, "filter_assignee=Dana")
    (reason,) = control(root, "filter_assignee").described_by()
    assert "The name 'Dana' isn't on the assignee list." in reason.text()
    assert [o.attrs["value"] for o in control(root, "filter_assignee").find_all("option")] == [
        "",
        " Ari",
        "Dana",
    ]


SPECIAL = ['<i>&"x"', " spaced ", "it's"]


@pytest.mark.parametrize("special", SPECIAL)
def test_names_and_labels_round_trip_as_text(tmp_path: Path, special: str) -> None:
    """CP-411, T9: `<`, `&`, quotes and surrounding spaces survive option values, the display and a
    percent-encoded address, and never become markup."""
    world = make_world(tmp_path, people=(special,))
    world.tracker.add_task(1, "T", "medium", special, "")
    world.tracker.add_task_label(1, special)
    world.tracker.add_task(1, "Other")
    encoded = quote(special, safe="")
    for key in ("filter_assignee", "filter_label"):
        root = project(world, f"{key}={encoded}")
        picked = [o for o in control(root, key).find_all("option") if "selected" in o.attrs]
        assert [o.attrs["value"] for o in picked] == [special], key
        assert picked[0].text() == special
        assert rows_of(root) == ["T"], key
        assert "match this filter" in root.text()
    shown = project(world, f"filter_label={encoded}")
    assert shown.find_all("i") == [] and shown.find_all("b") == []
    raw = page(get(world.site, f"/projects/1?filter_label={encoded}"))
    assert "<i>" not in raw
