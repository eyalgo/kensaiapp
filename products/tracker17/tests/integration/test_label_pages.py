"""Integration tests of the label area on a task's page, rendered from plain values (layer 3).

Checks SRS FR-23 (the label area with a Remove button for each label and an Add field), FR-39 and
FR-40 (a refusal's reason beside the field, and the label maximum) and NFR-5 (typed text is shown as
text). Change spec rules CP-182 to CP-186, CP-187 to CP-193, CP-199 and CP-203 and NFDR QC-9 and
QC-36 are the ones each test names. Where a test checks words, they are the strings of this change's
text record; the focus tests check where a line sits and which element it
describes. The page builder is handed plain values and calls no route.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest
from test_pages import Element, parse
from test_task_pages import a_task, context_of

from application import SHORT_TEXT_MAX, TaskEditContext
from web import pages

HOSTILE = "<b>A&B</b> \"quoted\" 'single'"
TITLE = "Set up CI"
NO_LABELS = "This task has no labels. Type a label and press Add."
EMPTY_REASON = "A label needs at least one character. Type a label."
TOO_LONG_REASON = f"A label can't be longer than {SHORT_TEXT_MAX} characters. Type a shorter one."


def page_of(
    labels: tuple[str, ...] = (),
    area: pages.LabelArea | None = None,
    *,
    title: str = TITLE,
    form: pages.TaskEditForm | None = None,
    added: bool = False,
    saved: bool = False,
) -> Element:
    context = context_of(a_task(1, title, labels=labels))
    return parse(pages.task_page(context, form=form, added=added, saved=saved, label_area=area))


def context(labels: tuple[str, ...] = (), title: str = TITLE) -> TaskEditContext:
    return context_of(a_task(1, title, labels=labels))


def section(root: Element) -> Element:
    (found,) = [e for e in root.find_all("section") if e.attrs.get("id") == "labels"]
    return found


def add_form(root: Element) -> Element:
    (found,) = [f for f in root.find_all("form") if f.attrs.get("action") == "/tasks/1/labels"]
    return found


def remove_forms(root: Element) -> list[Element]:
    return [f for f in root.find_all("form") if f.attrs.get("action") == "/tasks/1/labels/remove"]


def label_field(root: Element) -> Element:
    (field,) = [e for e in add_form(root).find_all("input") if e.attrs.get("type") == "text"]
    return field


def label_texts(root: Element) -> list[Element]:
    return [e for e in section(root).walk() if "label-text" in (e.attrs.get("class") or "").split()]


def focused(root: Element) -> list[Element]:
    return [element for element in root.walk() if "autofocus" in element.attrs]


def description(element: Element) -> str:
    return " ".join(found.text() for found in element.described_by())


def test_task_page_shows_ordered_labels_with_separate_forms() -> None:
    """CP-182: labels as saved and in order, each with a Remove form; a labelled Add field."""
    root = page_of(("ui", "bug", " Bug "))
    area = section(root)
    assert [h.text() for h in area.find_all("h2")] == ["Labels"]
    assert [e.text() for e in label_texts(root)] == ["ui", "bug", " Bug "]
    forms = remove_forms(root)
    assert len(forms) == 3
    for form, value in zip(forms, ("ui", "bug", " Bug "), strict=True):
        (button,) = form.find_all("button")
        assert button.text() == "Remove" and form.attrs["method"] == "post"
        (hidden,) = form.find_all("input")
        assert hidden.attrs == {"type": "hidden", "name": "label", "value": value}
    form = add_form(root)
    assert form.attrs["method"] == "post"
    field = label_field(root)
    assert field.attrs["name"] == "label" and field.attrs["value"] == ""
    (label,) = [x for x in form.find_all("label") if x.attrs.get("for") == field.attrs["id"]]
    assert label.text() == "Label"
    (button,) = form.find_all("button")
    assert button.text() == "Add" and button.attrs["type"] == "submit"
    assert all(f.find_all("form") == [f] for f in root.find_all("form"))
    assert root.find_all("script") == [] and NO_LABELS not in root.text()


def test_the_label_area_follows_the_edit_form_and_leaves_its_fields_alone() -> None:
    """CP-199: the edit form is as it was; the label area is a separate section after it."""
    root = page_of(("ui",))
    (edit,) = [f for f in root.find_all("form") if f.attrs.get("action") == "/tasks/1"]
    assert [i.attrs["name"] for i in edit.find_all("input")] == [
        "title",
        "due_date",
        "shown_title",
        "shown_priority",
        "shown_assignee",
        "shown_due_date",
    ]
    order = [e for e in root.walk() if e is edit or e is section(root)]
    assert order == [edit, section(root)]
    assert edit not in list(section(root).walk()) and section(root) not in list(edit.walk())


def test_label_less_task_shows_sentence_and_add() -> None:
    """CP-183: the published sentence, with the field and Add in view; no empty list."""
    root = page_of(())
    area = section(root)
    assert NO_LABELS in area.text()
    assert [e for e in area.walk() if e.tag in {"ul", "ol", "li"}] == []
    assert remove_forms(root) == []
    assert label_field(root).attrs["type"] == "text"
    assert [b.text() for b in add_form(root).find_all("button")] == ["Add"]
    assert focused(root) == []


def test_remove_accessible_name_names_label_and_task() -> None:
    """CP-185: the visible word unbroken, the exact label and the task's title."""
    root = page_of((" ui ", "bug"), title=" Set up CI ")
    buttons = [f.find_all("button")[0] for f in remove_forms(root)]
    assert [b.attrs["aria-label"] for b in buttons] == [
        "Remove label ' ui ' from ' Set up CI '",
        "Remove label 'bug' from ' Set up CI '",
    ]
    assert all(b.text() in b.attrs["aria-label"] for b in buttons)


def test_label_maxlength_comes_through_application() -> None:
    """CP-186: the field's maxlength is the application's domain maximum; no note beside it."""
    root = page_of(("ui",))
    assert label_field(root).attrs["maxlength"] == str(SHORT_TEXT_MAX)
    assert [e for e in section(root).walk() if "note" in (e.attrs.get("class") or "")] == []
    assert str(SHORT_TEXT_MAX) not in section(root).text()


def test_label_page_escapes_text_and_attributes() -> None:
    """QC-36: a typed label and a title are text everywhere, and no identifier carries one."""
    area = pages.LabelArea(label=HOSTILE, failed=pages.FailedAction.ADD)
    html = pages.task_page(
        context_of(a_task(1, HOSTILE, labels=(HOSTILE, " <i> "))), label_area=area
    )
    root = parse(html)
    assert "<b>" not in html and "<i>" not in html
    assert [e.text() for e in label_texts(root)] == [HOSTILE, " <i> "]
    forms = remove_forms(root)
    assert [f.find_all("input")[0].attrs["value"] for f in forms] == [HOSTILE, " <i> "]
    assert [f.find_all("button")[0].attrs["aria-label"] for f in forms] == [
        f"Remove label '{HOSTILE}' from '{HOSTILE}'",
        f"Remove label ' <i> ' from '{HOSTILE}'",
    ]
    assert label_field(root).attrs["value"] == HOSTILE
    assert description(add_form(root)).startswith(
        f"The tracker couldn't add the label '{HOSTILE}' to '{HOSTILE}', and nothing"
    )
    identifiers = [e.attrs["id"] for e in root.walk() if "id" in e.attrs]
    assert len(identifiers) == len(set(identifiers))
    assert all(set(i) <= set("abcdefghijklmnopqrstuvwxyz0123456789-") for i in identifiers)


@pytest.mark.parametrize(
    ("area", "line"),
    [
        (
            pages.LabelArea(added=HOSTILE),
            f"You added the label '{HOSTILE}' to '{HOSTILE}'.",
        ),
        (
            pages.LabelArea(removed=HOSTILE),
            f"You removed the label '{HOSTILE}' from '{HOSTILE}'.",
        ),
        (
            pages.LabelArea(label=HOSTILE, refusal=pages.LabelRefusal.NOT_CARRIED),
            (
                f"The label '{HOSTILE}' isn't on '{HOSTILE}'. "
                "The labels shown are the ones the task carries."
            ),
        ),
        (
            pages.LabelArea(label=HOSTILE, failed=pages.FailedAction.REMOVE),
            (
                f"The tracker couldn't remove the label '{HOSTILE}' from '{HOSTILE}', and nothing "
                "was changed. Try again."
            ),
        ),
    ],
    ids=["added", "removed", "not-carried", "failed-remove"],
)
def test_every_label_outcome_line_shows_typed_text_as_text(
    area: pages.LabelArea, line: str
) -> None:
    """QC-36, CP-187, CP-192, CP-193: each line that quotes a label or the title shows them exactly
    as typed, as text, and is the focused element's description (change_text.md: a typed value is
    placed exactly as typed, between the straight single quotes)."""
    html = pages.task_page(context_of(a_task(1, HOSTILE, labels=(HOSTILE,))), label_area=area)
    root = parse(html)
    assert "<b>" not in html
    (target,) = focused(root)
    assert description(target) == line


def test_added_label_is_the_only_focus_target() -> None:
    """CP-187: the added label's text takes focus, and the completion line describes it."""
    root = page_of(("ui", " bug "), pages.LabelArea(added=" bug "))
    assert focused(root) == [label_texts(root)[1]]
    target = label_texts(root)[1]
    assert target.attrs["tabindex"] == "-1" and target.text() == " bug "
    assert description(target) == "You added the label ' bug ' to 'Set up CI'."
    assert focused(root)[0] is target
    assert "ui" not in description(target)


def test_removed_label_describes_focused_task_heading() -> None:
    """CP-192: the heading at the top takes focus; the removal line is its description."""
    root = page_of(("ui",), pages.LabelArea(removed="bug "))
    (heading,) = root.find_all("h1")
    assert focused(root) == [heading]
    assert heading.attrs["tabindex"] == "-1"
    assert description(heading) == "You removed the label 'bug ' from 'Set up CI'."
    (line,) = heading.described_by()
    assert line.parent is not None and line.parent.tag == "main"


@pytest.mark.parametrize(
    ("refusal", "retained", "reason", "kept"),
    [
        (pages.LabelRefusal.EMPTY, "", EMPTY_REASON, ""),
        (pages.LabelRefusal.TOO_LONG, "leaked", TOO_LONG_REASON, ""),
    ],
    ids=["empty", "too-long"],
)
def test_label_refusal_focus_and_retention_match_condition(
    refusal: pages.LabelRefusal, retained: str, reason: str, kept: str
) -> None:
    """CP-190, CP-191: the field takes focus with its reason; too-long keeps none of the text."""
    root = page_of(("ui",), pages.LabelArea(label=retained, refusal=refusal))
    field = label_field(root)
    assert focused(root) == [field]
    assert description(field) == reason
    assert field.attrs["value"] == kept
    assert "leaked" not in root.text() and "leaked" not in str([e.attrs for e in root.walk()])
    (reason_element,) = field.described_by()
    assert reason_element.parent is not None and field.parent is reason_element.parent


def test_stale_remove_focuses_the_section_with_its_reason() -> None:
    """CP-193: the label section takes focus, the reason is its description."""
    root = page_of(("ui",), pages.LabelArea(label="gone ", refusal=pages.LabelRefusal.NOT_CARRIED))
    area = section(root)
    assert focused(root) == [area] and area.attrs["tabindex"] == "-1"
    assert description(area) == (
        "The label 'gone ' isn't on 'Set up CI'. The labels shown are the ones the task carries."
    )
    assert [e.text() for e in label_texts(root)] == ["ui"]
    assert label_field(root).attrs["value"] == ""


def test_empty_refusal_on_a_label_less_task_keeps_the_sentence() -> None:
    """CP-183, CP-190: the field holds nothing and the no-labels sentence is still there."""
    root = page_of((), pages.LabelArea(label="", refusal=pages.LabelRefusal.EMPTY))
    assert label_field(root).attrs["value"] == "" and focused(root) == [label_field(root)]
    assert NO_LABELS in section(root).text()


@pytest.mark.parametrize(
    ("action", "line", "kept"),
    [
        (
            pages.FailedAction.ADD,
            (
                "The tracker couldn't add the label ' x ' to 'Set up CI', and nothing was "
                "changed. What you typed is still in the form. Try again."
            ),
            " x ",
        ),
        (
            pages.FailedAction.REMOVE,
            (
                "The tracker couldn't remove the label ' x ' from 'Set up CI', and nothing was "
                "changed. Try again."
            ),
            "",
        ),
    ],
    ids=["add", "remove"],
)
def test_label_save_failure_focus_names_failed_action(
    action: pages.FailedAction, line: str, kept: str
) -> None:
    """QC-49: the Add form or the label section takes focus; no completion, no Python error."""
    root = page_of(("ui",), pages.LabelArea(label=" x ", failed=action))
    target = add_form(root) if action is pages.FailedAction.ADD else section(root)
    assert focused(root) == [target] and target.attrs["tabindex"] == "-1"
    assert description(target) == line
    assert label_field(root).attrs["value"] == kept
    text = root.text()
    assert "You added" not in text and "You removed" not in text
    assert "Error" not in text and "Traceback" not in text


def test_plain_label_area_leaves_existing_edit_outcome_intact() -> None:
    """CP-199: with no recognized label outcome, the edit form's outcomes are as they were."""
    for area in (None, pages.LabelArea()):
        saved = page_of(("ui",), area, saved=True)
        (heading,) = saved.find_all("h1")
        assert focused(saved) == [heading]
        assert description(heading) == "You saved changes to 'Set up CI'."
        failed = page_of(("ui",), area, form=pages.TaskEditForm(failed=True))
        (edit,) = [f for f in failed.find_all("form") if f.attrs.get("action") == "/tasks/1"]
        assert focused(failed) == [edit]
        refused = page_of(
            ("ui",), area, form=pages.TaskEditForm(refusal=pages.TaskEditRefusal.BLANK_TITLE)
        )
        assert len(focused(refused)) == 1
        plain = page_of(("ui",), area)
        assert focused(plain) == [] and plain.find_all("h1")[0].attrs["tabindex"] == "-1"
    added = page_of(("ui",), None, added=True)
    assert description(added.find_all("h1")[0]) == "You added 'Set up CI'."


def test_a_label_outcome_for_a_label_the_task_does_not_carry_is_a_plain_page() -> None:
    """CP-189: an added label that is not on the task has nothing to focus and nothing to say."""
    root = page_of(("ui",), pages.LabelArea(added="elsewhere"))
    assert focused(root) == [] and "elsewhere" not in root.text()
    assert [e.text() for e in label_texts(root)] == ["ui"]


@pytest.mark.parametrize(
    ("area", "target_of", "line"),
    [
        (
            pages.LabelArea(
                label="x",
                refusal=pages.LabelRefusal.EMPTY,
                failed=pages.FailedAction.ADD,
                added="ui",
                removed="old",
            ),
            lambda root: label_field(root),
            EMPTY_REASON,
        ),
        (
            pages.LabelArea(label="x", failed=pages.FailedAction.REMOVE, added="ui", removed="old"),
            lambda root: section(root),
            (
                "The tracker couldn't remove the label 'x' from 'Set up CI', and nothing was "
                "changed. Try again."
            ),
        ),
        (
            pages.LabelArea(added="ui", removed="old"),
            lambda root: label_texts(root)[0],
            "You added the label 'ui' to 'Set up CI'.",
        ),
    ],
    ids=["refusal-first", "failure-before-success", "added-before-removed"],
)
def test_mixed_label_outcomes_produce_one_focus_and_description(
    area: pages.LabelArea, target_of: Callable[[Element], Element], line: str
) -> None:
    """Refusal, then failure, then added, then removed; a label outcome beats the edit's own."""
    edit_noise = pages.TaskEditForm(refusal=pages.TaskEditRefusal.BLANK_TITLE, failed=True)
    root = page_of(("ui",), area, form=edit_noise, added=True, saved=True)
    target = target_of(root)
    assert focused(root) == [target]
    assert description(target) == line
    assert "You saved changes" not in root.text() and "You added 'Set up CI'" not in root.text()
    assert "A task needs a title" not in root.text()
    assert len(focused(root)) == 1
    for element in root.walk():
        if element.tag == "p" and "id" in element.attrs:
            assert element is not focused(root)[0]


def test_every_describing_line_exists_exactly_once() -> None:
    """The one description names an element on the page, and no two elements share an id."""
    for area in (
        pages.LabelArea(added="ui"),
        pages.LabelArea(removed="gone"),
        pages.LabelArea(label="x", refusal=pages.LabelRefusal.NOT_CARRIED),
        pages.LabelArea(label="x", failed=pages.FailedAction.ADD),
    ):
        root = page_of(("ui",), area)
        identifiers = [e.attrs["id"] for e in root.walk() if "id" in e.attrs]
        assert len(identifiers) == len(set(identifiers))
        (target,) = focused(root)
        assert len(target.described_by()) == 1
