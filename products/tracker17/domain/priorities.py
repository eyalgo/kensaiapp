"""The Priorities feature entry point: the four priority words and the rule that accepts one.

Realizes SRS FR-15 (a task has one of four priorities, `medium` unless one is chosen) and, for the
words it fixes, FR-16 and FR-36.

Taking part: application/tracker.py exports the choices and the add that applies them; web/pages.py
offers the choices in order and web/routes.py turns a refusal into its reason. The default for a
form that sends no priority is applied by domain/tasks.py, never here: a saved priority has none.

Checked by: tests/unit/test_priorities.py and tests/unit/test_tasks.py (the rules), and
tests/integration/test_task_tracker.py (the add through the Tracker), and
tests/integration/test_task_pages.py and tests/integration/test_task_routes.py (the choices and the
refusal on the page).
"""

from __future__ import annotations

from enum import Enum

from domain.refusals import InvalidPriority


class Priority(str, Enum):
    """A task's priority, valued by the word the form, the page and the saved data all use."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


DEFAULT_PRIORITY = Priority.MEDIUM
PRIORITY_CHOICES: tuple[str, ...] = tuple(priority.value for priority in Priority)


def parse_priority(value: str) -> Priority:
    """The priority this exact word names, or raise InvalidPriority. Empty text has no default."""
    try:
        return Priority(value)
    except ValueError:
        raise InvalidPriority() from None
