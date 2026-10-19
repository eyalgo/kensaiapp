"""Unit tests of the label rules in domain/labels.py (layer 1), with no file and no clock.

Checks SRS FR-23 (a task's labels, added and removed one at a time), FR-39 and FR-40 (refusals and
the label maximum) and DR-6 (saved labels are checked by the same rules). Change spec rules CP-182,
CP-187 to CP-193 and CP-197 and CP-202 are the ones each test names.
"""

from __future__ import annotations

import pytest

from domain import (
    SHORT_TEXT_MAX,
    EmptyLabel,
    LabelNotCarried,
    RepeatedSavedLabel,
    TextField,
    TextTooLong,
    add_label,
    check_label,
    check_saved_labels,
    remove_label,
)

OUTSIDE_THE_BASIC_PLANE = "\U0001f600"


def test_empty_label_is_refused():
    """CP-190: the label holding no character at all, and only that one."""
    with pytest.raises(EmptyLabel):
        check_label("")


def test_overlong_label_is_refused_by_code_point_count():
    """CP-191, CP-188: 201 code points are refused, a non-Basic-Plane character counting one."""
    for value in (
        "x" * (SHORT_TEXT_MAX + 1),
        OUTSIDE_THE_BASIC_PLANE * (SHORT_TEXT_MAX + 1),
        "x" * SHORT_TEXT_MAX + OUTSIDE_THE_BASIC_PLANE,
        " " * (SHORT_TEXT_MAX + 1),
    ):
        with pytest.raises(TextTooLong) as refusal:
            check_label(value)
        assert refusal.value.field is TextField.LABEL
        assert refusal.value.maximum == SHORT_TEXT_MAX == 200


def test_label_at_maximum_is_accepted_verbatim():
    """CP-188: exactly 200 code points are accepted, with a non-Basic-Plane character or spaces."""
    for value in (
        "x" * SHORT_TEXT_MAX,
        OUTSIDE_THE_BASIC_PLANE + "x" * (SHORT_TEXT_MAX - 1),
        " " + "x" * (SHORT_TEXT_MAX - 2) + " ",
        OUTSIDE_THE_BASIC_PLANE * SHORT_TEXT_MAX,
    ):
        assert len(value) == SHORT_TEXT_MAX
        assert check_label(value) == value


def test_spaces_only_label_is_accepted():
    """CP-188: nothing is stripped, so a label of spaces is a label."""
    for value in ("   ", " ", "\t", "  \n"):
        assert check_label(value) == value
        labels, changed = add_label((), value)
        assert labels == (value,) and changed is True


def test_new_label_appends_after_existing_labels():
    """CP-187: the new label goes last and every earlier one keeps its place."""
    before = ("bug", "ui")

    labels, changed = add_label(before, "ops")

    assert labels == ("bug", "ui", "ops") and changed is True
    assert before == ("bug", "ui")
    assert add_label((), "first") == (("first",), True)


def test_repeated_label_add_returns_unchanged_collection():
    """CP-189: an exact repeat changes nothing; a case or a space makes a different label."""
    before = ("bug", "ui")

    labels, changed = add_label(before, "bug")

    assert labels is before and changed is False
    for distinct in ("Bug", " bug", "bug ", "BUG"):
        added, added_changed = add_label(before, distinct)
        assert added == ("bug", "ui", distinct) and added_changed is True
    assert add_label(("bug", "Bug"), "Bug") == (("bug", "Bug"), False)


def test_remove_keeps_survivors_in_order():
    """CP-192: first, middle, last and the sole label each leave the others as they were."""
    labels = ("bug", "ui", "ops")

    assert remove_label(labels, "bug") == ("ui", "ops")
    assert remove_label(labels, "ui") == ("bug", "ops")
    assert remove_label(labels, "ops") == ("bug", "ui")
    assert remove_label(("only",), "only") == ()
    assert labels == ("bug", "ui", "ops")


def test_remove_of_absent_label_is_refused():
    """CP-193: membership decides, so an absent, case-different, empty or over-long value is the
    one refusal; removal applies no add rule."""
    labels = ("bug", "ui")
    for absent in ("ops", "BUG", " bug", "", "x" * (SHORT_TEXT_MAX + 1)):
        with pytest.raises(LabelNotCarried):
            remove_label(labels, absent)
    with pytest.raises(LabelNotCarried):
        remove_label((), "bug")


def test_saved_labels_are_ordered_and_unique_per_task():
    """CP-197: a repeat is refused exactly; empty and distinct collections are readable."""
    assert check_saved_labels([]) == ()
    assert check_saved_labels(["b", "a", "B", " a"]) == ("b", "a", "B", " a")
    assert isinstance(check_saved_labels(["x"]), tuple)
    with pytest.raises(RepeatedSavedLabel):
        check_saved_labels(["bug", "ui", "bug"])
    with pytest.raises(RepeatedSavedLabel):
        check_saved_labels(["   ", "   "])


def test_saved_labels_apply_the_value_rules_to_each_label():
    """CP-197: an empty label and an over-long label are refused wherever they sit."""
    with pytest.raises(EmptyLabel):
        check_saved_labels(["bug", ""])
    with pytest.raises(TextTooLong) as refusal:
        check_saved_labels(["x" * (SHORT_TEXT_MAX + 1), "bug"])
    assert refusal.value.field is TextField.LABEL
    boundary = ["x" * SHORT_TEXT_MAX, OUTSIDE_THE_BASIC_PLANE * SHORT_TEXT_MAX]
    assert check_saved_labels(boundary) == tuple(boundary)
