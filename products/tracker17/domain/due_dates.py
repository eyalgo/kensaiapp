"""The Due dates feature entry point: calendar-date validation and the overdue rule.

Realizes SRS FR-24 (a due date is a calendar date with no time of day), FR-25 (a task is overdue
when its due date is before today and it is still open) and FR-26 (the overdue state is shown, here
decided once for every list).

Taking part: application/tracker.py supplies today's local date and asks for the overdue flag;
web/pages.py shows the date and the word the flag selects, and web/routes.py turns a refusal into
its reason. Nothing here reads a clock: today arrives as an argument.

Checked by: tests/unit/test_due_dates.py and tests/unit/test_tasks.py (the rules), and
tests/integration/test_task_tracker.py (the local date and the flag through the Tracker), and
tests/integration/test_task_routes.py (the overdue marking after a restart).
"""

from __future__ import annotations

import re
from datetime import date
from typing import TYPE_CHECKING

from domain.refusals import InvalidDueDate

if TYPE_CHECKING:
    from domain.tasks import TaskStatus

_CALENDAR_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")


def parse_calendar_date(value: str) -> date:
    """The date this exact `YYYY-MM-DD` text names, or raise InvalidDueDate.

    A compact form, a week or ordinal date, a timestamp, padding and empty text are all refused:
    `date.fromisoformat` accepts several of them, so the shape is checked first.
    """
    if _CALENDAR_DATE.fullmatch(value) is None:
        raise InvalidDueDate()
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise InvalidDueDate() from None


def is_overdue(due_date: date | None, status: TaskStatus, today: date) -> bool:
    """True when the task is open and its due date is before the supplied today."""
    return due_date is not None and status.is_open and due_date < today
