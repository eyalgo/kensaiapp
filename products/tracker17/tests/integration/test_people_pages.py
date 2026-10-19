"""Integration tests of web's People page builder, read back as a browser parses it (layer 4).

Checks SRS FR-20 and FR-22 (the assignee list and removing a name), FR-27 (the operator's name),
FR-39 and FR-40 (refusals and the maximum length), NFR-4 (no outside content or script) and NFR-5
(typed text is shown as text). Change spec rules CP-80 to CP-85, CP-87, CP-89 to CP-91, CP-94, CP-96
and CP-97, and CP-211 to CP-217, CP-220 to CP-222, CP-225, CP-232 and CP-238, and NFDR QC-36 are
the ones each test names. Where a test checks words, they are the strings of this change's text
record; the focus tests check where a line sits and which element it describes.
"""

from __future__ import annotations

from typing import Any

import pytest
from test_pages import Element, parse

from application import SHORT_TEXT_MAX
from web import pages

HOSTILE = '<b>A&B</b> "quoted"'
VARIANTS = ["Dana", "dana", "Dana ", "Dana  ", " Dana"]
EMPTY_TEXT = "There are no assignees yet. Tasks can be assigned only to names on this list."
FIELD_FAILURES = (
    pages.AssigneeRefusal.BLANK_NAME,
    pages.AssigneeRefusal.ASSIGNEE_NAME_IN_USE,
    pages.AssigneeRefusal.TOO_LONG,
)


def main_of(root: Element) -> Element:
    (main,) = root.find_all("main")
    return main


def focused(root: Element) -> list[Element]:
    return [element for element in root.walk() if "autofocus" in element.attrs]


def controls(root: Element) -> list[Element]:
    """The tab stops in reading order: links, buttons and fields, hidden fields left out."""
    found = []
    for element in root.walk():
        if element.tag in {"a", "button", "textarea"} or (
            element.tag == "input" and element.attrs.get("type") != "hidden"
        ):
            found.append(element)
    return found


def assignees_section(root: Element) -> Element:
    """The Assignees section: the one holding its heading, which People shares with Your name."""
    found = root.by_id("assignees-heading")
    assert found is not None and found.parent is not None
    return found.parent


def name_input(root: Element) -> Element:
    (field,) = [
        e for e in assignees_section(root).find_all("input") if e.attrs.get("type") == "text"
    ]
    return field


def add_button(root: Element) -> Element:
    (form,) = [f for f in root.find_all("form") if f.attrs.get("action") == "/assignees"]
    (button,) = form.find_all("button")
    return button


def name_spans(root: Element) -> list[Element]:
    return [e for e in root.find_all("span") if "assignee-name" in (e.attrs["class"] or "")]


def remove_buttons(root: Element) -> list[Element]:
    return [
        button
        for form in root.find_all("form")
        if form.attrs.get("action") == "/assignees/remove"
        for button in form.find_all("button")
    ]


def heading(root: Element) -> Element:
    found = root.by_id("assignees-heading")
    assert found is not None
    return found


def described_text(element: Element) -> str:
    return " ".join(line.text() for line in element.described_by())


def test_the_people_header_has_projects_then_people_on_the_people_page() -> None:
    """CP-80."""
    root = parse(pages.people_page([]))
    (header,) = root.find_all("header")
    links = header.find_all("a")
    assert [(link.attrs["href"], link.text()) for link in links] == [
        ("/", "Projects"),
        ("/people", "People"),
    ]
    assert header.text().startswith("tracker17")


def test_people_has_its_title_list_and_add_form() -> None:
    """CP-81, CP-84, CP-85, CP-91."""
    page = pages.people_page([])
    root = parse(page)
    assert root.find_all("title")[0].text() == "People - tracker17"
    (title,) = root.find_all("h1")
    assert title.text() == "People"
    assert heading(root).text() == "Assignees"
    assert heading(root).attrs["id"] == "assignees-heading"
    assert EMPTY_TEXT in main_of(root).text()
    assert root.find_all("ul") == []
    field = name_input(root)
    assert int(field.attrs["maxlength"]) == SHORT_TEXT_MAX
    assignees = assignees_section(root)
    (label,) = assignees.find_all("label")
    assert label.text() == "Name" and label.attrs["for"] == field.attrs["id"]
    assert add_button(root).text() == "Add"
    assert len(assignees.find_all("input")) == 1
    assert len(assignees.find_all("button")) == 1
    assert "autofocus" not in page
    words = main_of(root).text().lower()
    for unavailable in ("all tasks", "operator"):
        assert unavailable not in words, unavailable
    assert root.find_all("textarea") == []


def test_people_shows_each_exact_name_and_one_remove() -> None:
    """CP-82, CP-83."""
    root = parse(pages.people_page(VARIANTS))
    spans = name_spans(root)
    assert [span.text() for span in spans] == VARIANTS
    assert root.find_all("li") and len(root.find_all("li")) == len(VARIANTS)
    removes = remove_buttons(root)
    assert len(removes) == len(VARIANTS)
    forms = [f for f in root.find_all("form") if f.attrs.get("action") == "/assignees/remove"]
    assert [f.attrs["method"] for f in forms] == ["post"] * len(VARIANTS)
    assert [
        [i.attrs["value"] for i in f.find_all("input") if i.attrs["name"] == "name"] for f in forms
    ] == [[name] for name in VARIANTS]
    accessible = [button.attrs["aria-label"] for button in removes]
    assert len(set(accessible)) == len(VARIANTS)
    for position, (button, name) in enumerate(zip(removes, VARIANTS, strict=True), start=1):
        assert button.text() == "Remove"
        assert button.attrs["aria-label"] == (
            f"Remove '{name}', number {position} on the assignee list"
        )
        assert button.attrs["aria-label"].startswith(button.text())


def test_added_name_is_the_only_non_tab_focus_target() -> None:
    """CP-87."""
    root = parse(pages.people_page(["Dana", "Cy", "Ari"], added="Cy"))
    (target,) = focused(root)
    assert target.tag == "span" and target.text() == "Cy"
    assert target.attrs["tabindex"] == "-1"
    (line,) = target.described_by()
    assert line.tag == "p" and line.text() == "You added 'Cy' to the assignees."
    assert "autofocus" not in line.attrs
    order = controls(root)
    # The next control in reading order after the added name is its own Remove.
    everything = list(root.walk())
    following = [e for e in everything[everything.index(target) + 1 :] if e in order]
    assert following[0].attrs["aria-label"] == "Remove 'Cy', number 2 on the assignee list"


def test_removed_or_absent_subject_uses_the_assignees_heading() -> None:
    """CP-94, CP-96; design T18."""
    removed = parse(pages.people_page(["Ari"], removed="Dana"))
    (target,) = focused(removed)
    assert target is heading(removed) and target.attrs["tabindex"] == "-1"
    assert described_text(target) == (
        "You removed 'Dana' from the assignees, and tasks that already carry the name keep it."
    )
    stale = parse(
        pages.people_page(["Ari"], refusal=pages.AssigneeRefusal.ASSIGNEE_NOT_FOUND, name="Dana")
    )
    (target,) = focused(stale)
    assert target is heading(stale)
    (line,) = target.described_by()
    assert line.text() == (
        "The name 'Dana' is no longer on the assignee list. Open People again to reload the list."
    )
    (link,) = line.find_all("a")
    assert link.attrs["href"] == "/people" and link.text() == "People"
    for page in (
        pages.people_page(["Ari"], added="Dana"),
        pages.people_page(["Ari"], failed=pages.FailedAction.REMOVE, name="Dana"),
    ):
        root = parse(page)
        (target,) = focused(root)
        assert target is heading(root)
        assert described_text(target)
    emptied = parse(pages.people_page([], removed="Dana"))
    assert add_button(emptied) is not None and EMPTY_TEXT in main_of(emptied).text()
    assert focused(emptied) == [heading(emptied)]


def test_refused_add_describes_and_focuses_the_retained_input() -> None:
    """CP-89, CP-90."""
    blank = parse(pages.people_page(["Dana"], refusal=pages.AssigneeRefusal.BLANK_NAME, name="  "))
    (target,) = focused(blank)
    assert target is name_input(blank) and target.attrs["value"] == "  "
    assert described_text(target) == "An assignee needs a name. Type one."
    in_use = parse(
        pages.people_page(
            ["Dana "], refusal=pages.AssigneeRefusal.ASSIGNEE_NAME_IN_USE, name="Dana "
        )
    )
    (target,) = focused(in_use)
    assert target is name_input(in_use) and target.attrs["value"] == "Dana "
    assert described_text(target) == (
        "An assignee named 'Dana ' is already on the list. Choose a different name."
    )
    for root in (blank, in_use):
        field_line = name_input(root).described_by()[0]
        (form,) = [f for f in root.find_all("form") if f.attrs.get("action") == "/assignees"]
        assert field_line in list(form.walk())


def test_too_long_refusal_renders_none_of_the_payload() -> None:
    """CP-91; design T11, T18."""
    page = pages.people_page(
        ["Dana"],
        refusal=pages.AssigneeRefusal.TOO_LONG,
        name="PAYLOAD-NAME",
        added="PAYLOAD-ADDED",
        removed="PAYLOAD-REMOVED",
        failed=pages.FailedAction.ADD,
    )
    assert "PAYLOAD" not in page
    root = parse(page)
    (target,) = focused(root)
    assert target is name_input(root) and target.attrs["value"] == ""
    assert described_text(target) == (
        f"An assignee name can't be longer than {SHORT_TEXT_MAX} characters. Type a shorter one."
    )


def test_failed_action_focuses_its_control() -> None:
    """CP-97."""
    add = parse(pages.people_page(["Dana"], failed=pages.FailedAction.ADD, name="Cy "))
    (target,) = focused(add)
    assert target is add_button(add) and name_input(add).attrs["value"] == "Cy "
    (line,) = target.described_by()
    assert line.text() == (
        "The tracker couldn't add 'Cy ' to the assignees, and nothing was changed. "
        "What you typed is still in the form. Try again."
    )
    remove = parse(
        pages.people_page(["Ari", "Dana"], failed=pages.FailedAction.REMOVE, name="Dana")
    )
    (target,) = focused(remove)
    assert target is remove_buttons(remove)[1]
    (line,) = target.described_by()
    assert line.text() == (
        "The tracker couldn't remove 'Dana' from the assignees, and nothing was changed. Try again."
    )
    assert len(name_spans(remove)) == 2
    for root in (add, remove):
        for element in focused(root):
            assert element.tag != "p"


@pytest.mark.parametrize(
    "refusal",
    [None, *FIELD_FAILURES, pages.AssigneeRefusal.ASSIGNEE_NOT_FOUND],
)
def test_every_dynamic_name_is_text_in_every_people_context(
    refusal: pages.AssigneeRefusal | None,
) -> None:
    """CP-82, QC-36."""
    page = pages.people_page(
        [HOSTILE, "Ari"],
        refusal=refusal,
        name=HOSTILE,
        added=None if refusal else HOSTILE,
    )
    root = parse(page)
    assert root.find_all("b") == [] and root.find_all("script") == []
    assert "<b>" not in page
    assert [span.text() for span in name_spans(root)] == [HOSTILE, "Ari"]
    assert remove_buttons(root)[0].attrs["aria-label"] == (
        f"Remove '{HOSTILE}', number 1 on the assignee list"
    )
    ids = [e.attrs["id"] for e in root.walk() if "id" in e.attrs]
    assert all("A&B" not in identifier and "<" not in identifier for identifier in ids)
    assert len(ids) == len(set(ids))
    assert "http-equiv" not in page


def test_dynamic_names_in_every_outcome_line_are_text() -> None:
    """CP-82, QC-36: the added, removed, failed and refusal lines carry the name literally."""
    for kwargs in (
        {"added": HOSTILE},
        {"removed": HOSTILE},
        {"failed": pages.FailedAction.ADD, "name": HOSTILE},
        {"failed": pages.FailedAction.REMOVE, "name": HOSTILE},
        {"refusal": pages.AssigneeRefusal.ASSIGNEE_NAME_IN_USE, "name": HOSTILE},
        {"refusal": pages.AssigneeRefusal.ASSIGNEE_NOT_FOUND, "name": HOSTILE},
    ):
        page = pages.people_page([HOSTILE], **kwargs)
        root = parse(page)
        assert root.find_all("b") == [], kwargs
        lines = [e for e in root.find_all("p") if HOSTILE in e.text()]
        assert lines, kwargs
        assert "<b>" not in page, kwargs


def test_plain_people_has_no_action_focus_or_outcome() -> None:
    """Design § 3 D: a plain render holds no autofocus and no outcome line."""
    page = pages.people_page(["Dana", "Ari"])
    root = parse(page)
    assert focused(root) == []
    assert [e for e in root.walk() if "aria-describedby" in e.attrs] == []
    assert assignees_section(root).find_all("p") == []
    assert all("tabindex" not in e.attrs for e in root.walk())


def test_outcome_precedence_is_refusal_then_failure_then_success() -> None:
    """Design § 3 D, T18: a combined outcome shows one line, the highest-precedence one."""
    both = parse(
        pages.people_page(
            ["Dana"],
            refusal=pages.AssigneeRefusal.BLANK_NAME,
            failed=pages.FailedAction.ADD,
            added="Dana",
            removed="Dana",
        )
    )
    assert [e.tag for e in focused(both)] == ["input"]
    failed_over_success = parse(
        pages.people_page(["Dana"], failed=pages.FailedAction.REMOVE, name="Dana", added="Dana")
    )
    assert [e.tag for e in focused(failed_over_success)] == ["button"]
    added_over_removed = parse(pages.people_page(["Dana"], added="Dana", removed="Dana"))
    (target,) = focused(added_over_removed)
    assert target.tag == "span"


def test_the_page_builder_reads_a_tuple_and_a_list_alike() -> None:
    """The page builder takes immutable sequences: a tuple and a list render the same."""
    assert pages.people_page(("Dana", "Ari")) == pages.people_page(["Dana", "Ari"])


ADDED_LINE = "You added '{name}' to the assignees."
FAILED_REMOVE_LINE = (
    "The tracker couldn't remove '{name}' from the assignees, and nothing was changed. Try again."
)
REMOVED_LINE = (
    "You removed '{name}' from the assignees, and tasks that already carry the name keep it."
)
STALE_LINE = (
    "The name '{name}' is no longer on the assignee list. Open People again to reload the list."
)


def test_an_absent_subject_keeps_its_own_authored_line_on_the_heading() -> None:
    """Design T18; change text, "A later page whose added or failed-remove name has left the list
    shows the same line": the line is the outcome's own, not some other line."""
    for page, line in (
        (pages.people_page(["Ari"], added="Dana"), ADDED_LINE),
        (
            pages.people_page(["Ari"], failed=pages.FailedAction.REMOVE, name="Dana"),
            FAILED_REMOVE_LINE,
        ),
    ):
        root = parse(page)
        (target,) = focused(root)
        assert target is heading(root)
        assert described_text(target) == line.format(name="Dana")
        assert [span.text() for span in name_spans(root)] == ["Ari"]
        assert all("aria-describedby" not in button.attrs for button in remove_buttons(root))


def test_a_removal_or_stale_line_sits_at_the_top_of_the_list_area() -> None:
    """CP-94, CP-96: the line is at the top of the area that held the list, under its heading and
    before the list or the empty text and the Add form; the stale reason takes the same place."""
    for assignees, kwargs, line in (
        (["Ari"], {"removed": "Dana"}, REMOVED_LINE),
        ([], {"removed": "Dana"}, REMOVED_LINE),
        (
            ["Ari"],
            {"refusal": pages.AssigneeRefusal.ASSIGNEE_NOT_FOUND, "name": "Dana"},
            STALE_LINE,
        ),
    ):
        root = parse(pages.people_page(assignees, **kwargs))
        section = assignees_section(root)
        order = [e for e in section.walk() if e.tag in {"h2", "p", "ul", "form"}]
        assert order[0] is heading(root), kwargs
        assert order[1].tag == "p" and order[1].text() == line.format(name="Dana"), kwargs
        assert heading(root).described_by() == [order[1]], kwargs
        assert all(e.tag != "p" or e.text() != order[1].text() for e in order[2:]), kwargs


def test_a_stale_remove_outranks_a_failure_and_a_success() -> None:
    """Design § 3 D, T18: a refusal comes before a failure and a success, the stale one included."""
    root = parse(
        pages.people_page(
            ["Dana", "Cy"],
            refusal=pages.AssigneeRefusal.ASSIGNEE_NOT_FOUND,
            name="Bo",
            failed=pages.FailedAction.ADD,
            added="Cy",
            removed="Dana",
        )
    )
    (target,) = focused(root)
    assert target is heading(root)
    assert described_text(target) == STALE_LINE.format(name="Bo")
    texts = main_of(root).text()
    assert "couldn't add" not in texts and "You added" not in texts and "You removed" not in texts
    assert name_input(root).attrs["value"] == ""


@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {"added": "Dana"},
        {"removed": "Bo"},
        {"refusal": pages.AssigneeRefusal.BLANK_NAME, "name": " "},
        {"refusal": pages.AssigneeRefusal.ASSIGNEE_NAME_IN_USE, "name": "Dana"},
        {"refusal": pages.AssigneeRefusal.TOO_LONG},
        {"refusal": pages.AssigneeRefusal.ASSIGNEE_NOT_FOUND, "name": "Bo"},
        {"failed": pages.FailedAction.ADD, "name": "Cy"},
        {"failed": pages.FailedAction.REMOVE, "name": "Dana"},
    ],
    ids=[
        "plain",
        "added",
        "removed",
        "blank",
        "in-use",
        "too-long",
        "stale",
        "fail-add",
        "fail-rm",
    ],
)
def test_no_people_state_offers_an_absent_area_or_a_second_assignee_field(
    kwargs: dict[str, Any],
) -> None:
    """CP-85, CP-238, in every state of the page: no word or link for an area the tracker lacks,
    and one assignee name field only. Your name and the keep-their-name sentence are this
    change's, so only those two words leave the absence list."""
    root = parse(pages.people_page(["Dana"], **kwargs))
    words = main_of(root).text().lower()
    for unavailable in ("all tasks", "operator", "assign to"):
        assert unavailable not in words, unavailable
    assert root.find_all("textarea") == []
    fields = [e for e in assignees_section(root).find_all("input") if e.attrs.get("type") == "text"]
    assert len(fields) == 1
    hrefs = {link.attrs["href"] for link in root.find_all("a")}
    assert hrefs <= {"/", "/people"}


OPERATOR_NOTE = "Comments you've already written keep the name they were written under."
NO_NAME_LINE = "No name is set. You need a name to comment."
BLANK_REASON = "Your name can't be blank. Type a name."
OPERATOR_TOO_LONG = (
    f"Your name can't be longer than {SHORT_TEXT_MAX} characters. Type a shorter one."
)
OPERATOR_FAILURE = (
    "The tracker couldn't set your name to '{name}', and nothing was changed. "
    "What you typed is still in the form. Try again."
)
OPERATOR_COMPLETED = "You set your name to '{name}'."
OPERATOR_ADDRESS = "/operator-name"
BLANK = pages.OperatorNameRefusal.BLANK_NAME
TOO_LONG = pages.OperatorNameRefusal.TOO_LONG
ASSIGNEE_OUTCOMES: list[dict[str, Any]] = [
    {"added": "Dana"},
    {"removed": "Dana"},
    {"refusal": pages.AssigneeRefusal.BLANK_NAME, "name": " "},
    {"refusal": pages.AssigneeRefusal.ASSIGNEE_NAME_IN_USE, "name": "Dana"},
    {"refusal": pages.AssigneeRefusal.TOO_LONG},
    {"refusal": pages.AssigneeRefusal.ASSIGNEE_NOT_FOUND, "name": "Dana"},
    {"failed": pages.FailedAction.ADD, "name": "Cy"},
    {"failed": pages.FailedAction.REMOVE, "name": "Dana"},
]


def your_name_section(root: Element) -> Element:
    found = root.by_id("your-name")
    assert found is not None
    return found


def operator_field(root: Element) -> Element:
    found = root.by_id("operator-name")
    assert found is not None
    return found


def operator_button(root: Element) -> Element:
    found = root.by_id("save-operator-name")
    assert found is not None
    return found


def operator_lines(root: Element) -> list[Element]:
    return [e for e in root.walk() if e.attrs.get("id") == "operator-name-outcome"]


def test_people_shows_your_name_above_unchanged_assignees() -> None:
    """CP-211, CP-213, CP-215: the section, its label, field, Save, note and no-name line sit in
    their defined places, above Assignees, and the title, header and navigation are unchanged."""
    page = pages.people_page([])
    root = parse(page)
    assert root.find_all("title")[0].text() == "People - tracker17"
    (title,) = root.find_all("h1")
    assert title.text() == "People"
    (header,) = root.find_all("header")
    assert [(a.attrs["href"], a.text()) for a in header.find_all("a")] == [
        ("/", "Projects"),
        ("/people", "People"),
    ]
    sections = main_of(root).find_all("section")
    assert sections[0] is your_name_section(root)
    assert sections.index(your_name_section(root)) < sections.index(assignees_section(root))
    own = your_name_section(root)
    own_heading = root.by_id("your-name-heading")
    assert own_heading is not None and own_heading.tag == "h2"
    assert own_heading.text() == "Your name" and own_heading.parent is own
    (form,) = own.find_all("form")
    assert form.attrs["method"] == "post" and form.attrs["action"] == OPERATOR_ADDRESS
    (label,) = form.find_all("label")
    field, button = operator_field(root), operator_button(root)
    assert label.text() == "Your name" and label.attrs["for"] == "operator-name"
    assert field.tag == "input" and field.attrs["type"] == "text" and field.attrs["name"] == "name"
    assert button.tag == "button" and button.attrs["type"] == "submit" and button.text() == "Save"
    assert [e for e in form.find_all("input") if e.attrs.get("type") != "hidden"] == [field]
    assert form.find_all("button") == [button]
    walked = list(own.walk())
    assert walked.index(label) < walked.index(field) < walked.index(button)
    (note,) = [e for e in own.find_all("p") if e.text() == OPERATOR_NOTE]
    assert note.tag == "p" and "autofocus" not in note.attrs and "tabindex" not in note.attrs
    assert note in list(form.walk())
    (no_name,) = [e for e in own.find_all("p") if e.text() == NO_NAME_LINE]
    assert "id" not in no_name.attrs or no_name.attrs["id"] != "operator-name-outcome"
    assert "autofocus" not in page and operator_lines(root) == []
    assert heading(root).text() == "Assignees"
    assert add_button(root).text() == "Add"


def test_people_name_field_uses_saved_name_and_shared_maximum() -> None:
    """CP-212, CP-214: the saved text fills the field exactly, an unset name shows it empty with
    the no-name line, a saved name removes that line, and no sentence states a limit."""
    unset = parse(pages.people_page([]))
    assert operator_field(unset).attrs["value"] == ""
    assert NO_NAME_LINE in your_name_section(unset).text()
    for saved in ("Sam", " Sam ", "x" * SHORT_TEXT_MAX):
        root = parse(pages.people_page([], operator_name=saved))
        assert operator_field(root).attrs["value"] == saved
        assert NO_NAME_LINE not in main_of(root).text()
        assert OPERATOR_NOTE in your_name_section(root).text()
    for root in (unset, parse(pages.people_page([], operator_name="Sam"))):
        assert int(operator_field(root).attrs["maxlength"]) == SHORT_TEXT_MAX
        text = your_name_section(root).text()
        assert str(SHORT_TEXT_MAX) not in text and "longer than" not in text
        assert "at most" not in text and "up to" not in text


@pytest.mark.parametrize(
    ("area", "saved", "target", "line"),
    [
        (
            pages.OperatorNameArea(saved="Sam"),
            "Sam",
            "input",
            OPERATOR_COMPLETED.format(name="Sam"),
        ),
        (pages.OperatorNameArea(refusal=BLANK, typed="  "), "Sam", "input", BLANK_REASON),
        (pages.OperatorNameArea(refusal=TOO_LONG), None, "input", OPERATOR_TOO_LONG),
        (
            pages.OperatorNameArea(failed=True, typed="Lee"),
            "Sam",
            "button",
            OPERATOR_FAILURE.format(name="Lee"),
        ),
    ],
    ids=["completed", "blank", "too-long", "failed"],
)
def test_operator_outcome_focus_has_one_linked_accessible_description(
    area: pages.OperatorNameArea, saved: str | None, target: str, line: str
) -> None:
    """CP-216, CP-220 to CP-222: success and both refusals focus the field, a failure focuses Save,
    each described by its one line, with one focus and one action outcome; the line takes none."""
    root = parse(pages.people_page(["Dana"], operator_name=saved, operator_area=area))
    (focus,) = focused(root)
    assert focus.tag == target
    assert focus is (operator_field(root) if target == "input" else operator_button(root))
    (described,) = focus.described_by()
    assert described.tag == "p" and described.text() == line
    assert operator_lines(root) == [described]
    assert "autofocus" not in described.attrs and "tabindex" not in described.attrs
    assert described in list(your_name_section(root).walk())
    assert root.find_all("script") == []
    assert all("#" not in (a.attrs.get("href") or "") for a in root.find_all("a"))
    assert all(e.tag in {"input", "button"} for e in root.walk() if "autofocus" in e.attrs)


def test_operator_name_and_outcome_values_render_as_text() -> None:
    """CP-225, QC-36: the field and the completion and failure lines carry `<`, `&` and quotes as
    typed, with no injected tags, no duplicate identifiers and the surrounding structure intact."""
    plain_structure = [e.tag for e in parse(pages.people_page([])).walk() if e.tag != "p"]
    for saved, area in (
        (HOSTILE, pages.OperatorNameArea(saved=HOSTILE)),
        (None, pages.OperatorNameArea(failed=True, typed=HOSTILE)),
        (None, pages.OperatorNameArea(refusal=BLANK, typed=HOSTILE)),
        (HOSTILE, None),
    ):
        page = pages.people_page([], operator_name=saved, operator_area=area)
        root = parse(page)
        assert root.find_all("b") == [] and root.find_all("script") == []
        assert "<b>" not in page
        ids = [e.attrs["id"] for e in root.walk() if "id" in e.attrs]
        assert len(ids) == len(set(ids))
        assert [e.tag for e in root.walk() if e.tag != "p"] == plain_structure
        assert operator_field(root).attrs["value"] == HOSTILE
        if area is not None and area.saved is not None:
            (line,) = operator_lines(root)
            assert line.text() == OPERATOR_COMPLETED.format(name=HOSTILE)
        if area is not None and area.failed:
            (line,) = operator_lines(root)
            assert line.text() == OPERATOR_FAILURE.format(name=HOSTILE)


def test_people_operator_precedence_holds_for_direct_page_values() -> None:
    """CP-215, CP-222: refusal beats failure and completion, failure beats completion, and a
    recognized operator outcome suppresses every assignee outcome and its focus; a plain operator
    area leaves each assignee outcome exactly as it is."""
    refused = parse(
        pages.people_page(
            ["Dana"],
            operator_name="Sam",
            operator_area=pages.OperatorNameArea(
                refusal=BLANK, typed=" ", failed=True, saved="Sam"
            ),
        )
    )
    (focus,) = focused(refused)
    assert focus is operator_field(refused) and described_text(focus) == BLANK_REASON
    failed = parse(
        pages.people_page(
            ["Dana"],
            operator_name="Sam",
            operator_area=pages.OperatorNameArea(failed=True, typed="Lee", saved="Sam"),
        )
    )
    (focus,) = focused(failed)
    assert focus is operator_button(failed)
    assert described_text(focus) == OPERATOR_FAILURE.format(name="Lee")
    for area in (
        pages.OperatorNameArea(saved="Sam"),
        pages.OperatorNameArea(failed=True, typed="Lee"),
        pages.OperatorNameArea(refusal=BLANK, typed=""),
        pages.OperatorNameArea(refusal=TOO_LONG),
    ):
        for outcome in ASSIGNEE_OUTCOMES:
            page = pages.people_page(["Dana"], operator_name="Sam", operator_area=area, **outcome)
            root = parse(page)
            (focus,) = focused(root)
            assert focus in (operator_field(root), operator_button(root)), (area, outcome)
            assert len(operator_lines(root)) == 1
            assert [e for e in assignees_section(root).find_all("p")] == []
            assert heading(root).attrs.get("tabindex") is None
            assert name_input(root).attrs["value"] == ""
    for outcome in ASSIGNEE_OUTCOMES:
        plain = pages.people_page(["Dana"], **outcome)
        assert (
            pages.people_page(["Dana"], operator_area=pages.OperatorNameArea(), **outcome) == plain
        )
        assert pages.people_page(["Dana"], operator_area=None, **outcome) == plain


def test_operator_too_long_page_discards_forged_typed_text() -> None:
    """CP-221: a too-long outcome shows the saved name, or nothing when none is saved, and none of a
    forged typed value, including beside failure and completion metadata."""
    for saved, shown in (("Saved", "Saved"), (None, "")):
        for area in (
            pages.OperatorNameArea(refusal=TOO_LONG, typed="PAYLOAD-TYPED"),
            pages.OperatorNameArea(
                refusal=TOO_LONG, typed="PAYLOAD-TYPED", failed=True, saved="PAYLOAD-SAVED"
            ),
        ):
            page = pages.people_page(["Dana"], operator_name=saved, operator_area=area)
            assert "PAYLOAD" not in page
            root = parse(page)
            (focus,) = focused(root)
            assert focus is operator_field(root) and focus.attrs["value"] == shown
            assert described_text(focus) == OPERATOR_TOO_LONG


def test_operator_typed_text_applies_only_to_a_blank_refusal_or_a_failure() -> None:
    """CP-220, CP-222: an empty typed value differs from none; none falls back to the saved name,
    or empty when unset; typed text beside no recognized blank refusal or failure is ignored."""
    for saved in ("Sam", None):
        fallback = saved or ""
        for kwargs in ({"refusal": BLANK}, {"failed": True}):
            absent = parse(
                pages.people_page(
                    [], operator_name=saved, operator_area=pages.OperatorNameArea(**kwargs)
                )
            )
            assert operator_field(absent).attrs["value"] == fallback, kwargs
            empty = parse(
                pages.people_page(
                    [],
                    operator_name=saved,
                    operator_area=pages.OperatorNameArea(typed="", **kwargs),
                )
            )
            assert operator_field(empty).attrs["value"] == "", kwargs
            typed = parse(
                pages.people_page(
                    [],
                    operator_name=saved,
                    operator_area=pages.OperatorNameArea(typed="  kept ", **kwargs),
                )
            )
            assert operator_field(typed).attrs["value"] == "  kept ", kwargs
        for area in (
            pages.OperatorNameArea(typed="forged"),
            pages.OperatorNameArea(typed="forged", saved="Lee"),
        ):
            root = parse(pages.people_page([], operator_name=saved, operator_area=area))
            assert operator_field(root).attrs["value"] == fallback, area
