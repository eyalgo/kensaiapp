"""The Comments feature entry point: the comment value and the rules that accept or refuse one.

Realizes SRS FR-28 (adding a comment: its text, the author name and the instant it is written),
FR-29 (comments held in the order written), FR-30 (a comment keeps the name it was written under),
FR-39 and FR-40 (refusals and the comment maximum), DR-3 (the Comment entity), DR-6 (saved comments
are checked by the same rules) and NFR-9 (the trace from the requirement to this code).

Holds the value and the scalar rules only and imports no task or state module, so that
domain/tasks.py can apply them when it appends a comment to a task and when it restores one, with
no cycle. Taking part: application/tracker.py applies the add and saves the result, and
application/__init__.py hands the refusal types on; web/pages.py shows the Comments area, and
web/routes.py turns a submission into an add and each refusal into its reason.

Checked by: tests/unit/test_comments.py and tests/unit/test_tasks.py (the rules, the add and the
restoration), tests/integration/test_comment_tracker.py (the action, the save and the name at the
add), tests/integration/test_comment_pages.py (the comment area on a task's page),
tests/integration/test_comment_routes.py (the add request, its refusals and its failure),
tests/integration/test_routes.py (the route audit, the outbound hook and the recording saver),
tests/integration/test_task_pages.py (the task page's form order and the People link),
tests/architecture/test_shapes.py and tests/architecture/test_trace.py (the entry and the shape),
tests/integration/test_saved_data.py and tests/integration/test_start.py (the saved comments and
the start), tests/e2e/test_comments.py (the keyboard add in the browser).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

from domain.operator_name import check_operator_name
from domain.refusals import BlankComment, OperatorNameNotSet, TextField
from domain.text import LONG_TEXT_MAX, ensure_within


@dataclass(frozen=True)
class Comment:
    """One comment on a task: its text, the name it was written under and when it was written."""

    text: str
    author: str
    created_at: datetime


def check_comment_text(text: str) -> str:
    """The text unchanged, or the refusal of it.

    Checked in order: too long, then blank. A comment is as long as its Unicode code points, and is
    blank when it is empty or every character is whitespace, the set a name already uses. Nothing is
    trimmed, normalized or shortened.
    """
    ensure_within(TextField.COMMENT, text, LONG_TEXT_MAX)
    if all(character.isspace() for character in text):
        raise BlankComment()
    return text


def create_comment(text: str, operator_name: str | None, created_at: datetime) -> Comment:
    """The comment holding the text, the operator name as the author and the instant, or refuse.

    The text is checked first, then the name: no name saved is refused last. The name and the
    instant are copied as given, and nothing is read from a state or a clock.
    """
    checked = check_comment_text(text)
    if operator_name is None:
        raise OperatorNameNotSet()
    return Comment(text=checked, author=operator_name, created_at=created_at)


def check_saved_comment(comment: Comment) -> Comment:
    """The saved comment unchanged, or the refusal of it.

    Its text keeps the comment rules. Its author is a name that was the operator's when the comment
    was written, so it keeps the scalar name rules and is compared with no current name.
    """
    check_comment_text(comment.text)
    check_operator_name(comment.author)
    return comment


def check_saved_comments(comments: Iterable[Comment]) -> tuple[Comment, ...]:
    """The saved comments in the order given, each checked, or the first refusal."""
    return tuple(check_saved_comment(comment) for comment in comments)
