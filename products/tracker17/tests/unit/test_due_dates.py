"""Unit tests of the due-date rules in domain/due_dates.py (layer 1), with no file and no clock.

Checks SRS FR-24 (a due date is a calendar date with no time of day), FR-25 (when a task is
overdue) and FR-26 (the overdue state is shown). Change spec rules CP-110, CP-120, CP-129, CP-131,
CP-137 and CP-140 are the ones each test names.
"""

from __future__ import annotations

from datetime import date

import pytest

from domain import InvalidDueDate, TaskStatus, is_overdue, parse_calendar_date

TODAY = date(2026, 10, 11)


def test_a_valid_calendar_date_is_read_as_that_date():
    """CP-110, CP-129."""
    assert parse_calendar_date("2026-10-20") == date(2026, 10, 20)


def test_a_leap_day_is_a_date_only_in_a_leap_year():
    """CP-120."""
    assert parse_calendar_date("2028-02-29") == date(2028, 2, 29)
    with pytest.raises(InvalidDueDate):
        parse_calendar_date("2027-02-29")


@pytest.mark.parametrize(
    "value",
    [
        "",
        "2026-02-30",
        "2026-13-01",
        "2026-00-10",
        "0000-01-01",
        "20261011",
        "2026-W41-7",
        "2026-284",
        "2026-10-11T09:30:00",
        "2026-10-11T09:30:00Z",
        "2026-10-1",
        "2026-1-11",
        "26-10-11",
        "10/11/2026",
        " 2026-10-11",
        "2026-10-11 ",
        "2026-10-11\n",
        "２０２６-１０-１１",
        "tomorrow",
    ],
)
def test_anything_but_an_exact_year_month_day_calendar_date_is_refused(value):
    """CP-120, CP-137: no week date, compact form, timestamp, padding or empty text."""
    with pytest.raises(InvalidDueDate):
        parse_calendar_date(value)


@pytest.mark.parametrize(
    ("status", "open_task"),
    [
        (TaskStatus.TODO, True),
        (TaskStatus.IN_PROGRESS, True),
        (TaskStatus.DONE, False),
        (TaskStatus.CANCELLED, False),
    ],
)
def test_overdue_matrix(status, open_task):
    """CP-131: only an open task due before the supplied today is overdue."""
    yesterday, today, tomorrow = date(2026, 10, 10), TODAY, date(2026, 10, 12)

    assert is_overdue(yesterday, status, TODAY) is open_task
    assert is_overdue(today, status, TODAY) is False
    assert is_overdue(tomorrow, status, TODAY) is False
    assert is_overdue(None, status, TODAY) is False


def test_the_four_statuses_are_written_as_their_words():
    """CP-137: the saved words."""
    assert [status.value for status in TaskStatus] == ["todo", "in-progress", "done", "cancelled"]
