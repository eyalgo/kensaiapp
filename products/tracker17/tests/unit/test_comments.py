"""Unit tests of the comment rules in domain/comments.py and domain/tasks.py (layer 1), with no
file and no clock.

Checks SRS FR-28 (adding a comment), FR-29 (comments in the order written), FR-30 (a rename keeps
every earlier author), FR-39 and FR-40 (refusals and the comment maximum), DR-3 (the Comment entity)
and DR-6 (saved comments are checked by the same rules). Change spec rules CP-249, CP-251, CP-253,
CP-254, CP-256 to CP-259, CP-264, CP-266 and CP-267 are the ones each test names.
"""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime, timedelta

import pytest

import domain
import domain.comments
import domain.tasks
from domain import (
    LONG_TEXT_MAX,
    SHORT_TEXT_MAX,
    BlankComment,
    BlankName,
    Comment,
    OperatorNameNotSet,
    TaskNotFound,
    TaskStatus,
    TextField,
    TextTooLong,
    TrackerState,
    add_task_comment,
    check_comment_text,
    check_saved_comment,
    check_saved_comments,
    create_comment,
    restore_state,
    restore_task,
)

NOW = datetime(2026, 10, 12, 12, 32, tzinfo=UTC)
OUTSIDE_THE_BASIC_PLANE = "\U0001f600"
BLANKS = ["", " ", "\t", "\n", "\u00a0", "\u3000", " \t\n\u00a0\u3000 ", "\n\n"]


def _task(task_id: int = 1, status: str = "todo", comments=()):
    return restore_task(
        id=task_id,
        project_id=1,
        title=f"Task {task_id}",
        status=status,
        priority="medium",
        assignee=None,
        labels=("bug",),
        due_date="2026-10-20",
        created_at=NOW,
        comments=comments,
    )


def _state(*tasks, operator_name: str | None = "Sam") -> TrackerState:
    return restore_state(
        [(1, "Alpha", "x"), (2, "Beta", "")],
        3,
        ["Dana"],
        tasks=tasks,
        next_task_id=max((task.id for task in tasks), default=0) + 1,
        operator_name=operator_name,
    )


def test_comment_text_requires_a_non_whitespace_character():
    """CP-256, CP-267: empty and whitespace-only text is blank, U+200B is not."""
    for blank in BLANKS:
        with pytest.raises(BlankComment):
            check_comment_text(blank)
    assert check_comment_text("\u200b") == "\u200b"
    assert check_comment_text(" a ") == " a "


def test_comment_keeps_text_author_and_supplied_instant():
    """CP-249, CP-267: text is exact, the author and the instant are the ones handed in."""
    for text in ("Looks good", "  spaced  ", "one\ntwo\n", '<b>A&B</b> "x"', "\n lead"):
        comment = create_comment(text, "Sam", NOW)
        assert comment == Comment(text=text, author="Sam", created_at=NOW)
    assert create_comment("x", " Lee ", NOW).author == " Lee "


def test_comment_accepts_the_code_point_maximum_without_truncation():
    """CP-254, CP-267: 4,000 code points with line breaks and a non-BMP character are kept whole."""
    text = "a\n" * 1999 + OUTSIDE_THE_BASIC_PLANE + "b"
    assert len(text) == LONG_TEXT_MAX == 4000
    assert check_comment_text(text) == text
    assert create_comment(text, "Sam", NOW).text == text
    with pytest.raises(TextTooLong) as refusal:
        check_comment_text(text + "c")
    assert refusal.value.field is TextField.COMMENT
    assert refusal.value.maximum == LONG_TEXT_MAX
    assert TextField.COMMENT.value == "comment"


def test_comment_refusal_precedence_is_length_blank_then_unset_name():
    """CP-258, CP-267: too long, then blank, then no name saved."""
    with pytest.raises(TextTooLong):
        create_comment(" " * (LONG_TEXT_MAX + 1), None, NOW)
    with pytest.raises(BlankComment):
        create_comment("", None, NOW)
    with pytest.raises(OperatorNameNotSet):
        create_comment("Hi", None, NOW)
    with pytest.raises(TextTooLong):
        add_task_comment(_state(_task(), operator_name=None), 1, "x" * 4001, NOW)
    with pytest.raises(BlankComment):
        add_task_comment(_state(_task(), operator_name=None), 1, "  ", NOW)
    with pytest.raises(OperatorNameNotSet):
        add_task_comment(_state(_task(), operator_name=None), 1, "Hi", NOW)


def test_the_new_refusals_are_refusals_with_no_wording():
    """CP-266: the typed refusals derive from Refusal and carry no message of their own."""
    for refusal in (BlankComment, OperatorNameNotSet):
        assert issubclass(refusal, domain.Refusal)
        assert str(refusal()) == ""


def test_comment_append_preserves_written_order_and_duplicate_text():
    """CP-241, CP-249, CP-267: a new comment goes last whatever its instant, repeated text too."""
    earlier = Comment("first", "Lee", NOW)
    later = Comment("second", "Lee", NOW + timedelta(hours=1))
    state = _state(_task(comments=[later, earlier]))

    after, task = add_task_comment(state, 1, "first", NOW - timedelta(days=1))
    again, task_again = add_task_comment(after, 1, "first", NOW - timedelta(days=1))

    assert task.comments == (later, earlier, Comment("first", "Sam", NOW - timedelta(days=1)))
    assert len(task_again.comments) == 4 and task_again.comments[:3] == task.comments
    assert again.tasks[0] is task_again


def test_comments_can_be_added_in_every_task_status():
    """CP-253, CP-267."""
    for status in TaskStatus:
        _, task = add_task_comment(_state(_task(status=status.value)), 1, "Hi", NOW)
        assert task.status is status
        assert [comment.text for comment in task.comments] == ["Hi"]


def test_unknown_task_precedes_every_comment_refusal():
    """CP-259, CP-267: a missing task is refused first, and nothing changes."""
    for operator_name in ("Sam", None):
        state = _state(_task(), operator_name=operator_name)
        for text in ("Hi", "", "x" * 4001):
            with pytest.raises(TaskNotFound):
                add_task_comment(state, 99, text, NOW)
        assert state == _state(_task(), operator_name=operator_name)


def test_comment_add_changes_only_the_named_tasks_comments():
    """CP-249: every other value of the state and of the task is carried over untouched."""
    kept = _task(2, status="done", comments=[Comment("old", "Lee", NOW)])
    target = _task(1, comments=[Comment("earlier", "Dana", NOW)])
    state = _state(target, kept)

    new_state, task = add_task_comment(state, 1, "added", NOW)

    assert state == _state(target, kept)
    assert new_state.tasks[1] is kept
    assert dataclasses.replace(new_state, tasks=state.tasks) == state
    assert dataclasses.replace(task, comments=target.comments) == target
    assert task.comments[:1] == target.comments

    for refused in ("", " ", "x" * 4001):
        with pytest.raises(domain.Refusal):
            add_task_comment(state, 1, refused, NOW)
    assert state == _state(target, kept)


def test_restore_checks_comment_text_and_historical_author():
    """CP-264, CP-267: blank and over-long text or author refuse; the maxima and any name load."""
    for text in ("", "   ", "\n\u00a0\u3000"):
        with pytest.raises(BlankComment):
            _task(comments=[Comment(text, "Sam", NOW)])
    with pytest.raises(TextTooLong) as long_text:
        _task(comments=[Comment("x" * 4001, "Sam", NOW)])
    assert long_text.value.field is TextField.COMMENT
    for author in ("", " ", "\t\u3000"):
        with pytest.raises(BlankName):
            _task(comments=[Comment("Hi", author, NOW)])
    with pytest.raises(TextTooLong) as long_author:
        _task(comments=[Comment("Hi", "x" * (SHORT_TEXT_MAX + 1), NOW)])
    assert long_author.value.field is TextField.NAME

    boundary = [
        Comment(OUTSIDE_THE_BASIC_PLANE + "x" * 3999, "x" * 199 + OUTSIDE_THE_BASIC_PLANE, NOW),
        Comment("second", "Nobody Now", NOW - timedelta(days=3)),
        Comment("\u200b", "Sam", NOW),
    ]
    assert _task(comments=boundary).comments == tuple(boundary)
    assert _state(_task(comments=boundary), operator_name=None).tasks[0].comments == tuple(boundary)


def test_saved_comment_checks_return_what_they_were_given_in_order():
    """CP-264: the checks hand back the same value, or the same values in the same order."""
    first, second = Comment("a", "Sam", NOW), Comment("b", "Lee", NOW - timedelta(days=1))
    assert check_saved_comment(first) is first
    assert check_saved_comments([first, second]) == (first, second)
    assert check_saved_comments([]) == ()
    with pytest.raises(BlankComment):
        check_saved_comments([first, Comment(" ", "Lee", NOW)])


def test_comment_public_aliases_keep_one_frozen_three_field_value():
    """CP-266: the moved value is the one behind both import paths, still frozen and three-field."""
    assert domain.Comment is domain.tasks.Comment is domain.comments.Comment
    assert [field.name for field in dataclasses.fields(Comment)] == ["text", "author", "created_at"]
    comment = Comment("x", "Sam", NOW)
    with pytest.raises(dataclasses.FrozenInstanceError):
        comment.text = "y"  # type: ignore[misc]
