"""Unit tests of the priority rules in domain/priorities.py (layer 1), with no file and no clock.

Checks SRS FR-15 (a task has one of four priorities) and FR-16 and FR-36 as far as they name the
priority words. Change spec rules CP-108, CP-112, CP-120, CP-137 and CP-140 are the ones each test
names.
"""

from __future__ import annotations

import pytest

from domain import PRIORITY_CHOICES, InvalidPriority, Priority, parse_priority


def test_choices_are_the_four_words_in_ascending_urgency():
    """CP-108: the four words, written as the words, in the order the form offers them."""
    assert PRIORITY_CHOICES == ("low", "medium", "high", "critical")
    assert [priority.value for priority in Priority] == list(PRIORITY_CHOICES)


def test_priority_is_a_string_valued_enum():
    assert Priority.HIGH == "high"
    assert Priority("critical") is Priority.CRITICAL


@pytest.mark.parametrize("word", PRIORITY_CHOICES)
def test_each_of_the_four_words_is_accepted(word):
    """CP-112, CP-120."""
    assert parse_priority(word) is Priority(word)


@pytest.mark.parametrize("value", ["", "urgent", "Low", "HIGH", " medium", "medium ", "none", "1"])
def test_any_other_value_is_refused_without_a_default(value):
    """CP-120, CP-137: the default belongs to a form that sends nothing, never to a saved value."""
    with pytest.raises(InvalidPriority):
        parse_priority(value)
