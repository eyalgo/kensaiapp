"""Integration tests of the console report of a failed action at a non-text-byte path (layer 3).

Checks SRS NFR-8 and AC-18 (an induced failure that is not a refusal writes a console message
naming the action and the error, and the browser says the action failed). Pins what
Site._report_failure in web/routes.py writes to the console's error stream when an action fails
with an OSError whose text holds the path os.fsdecode(b"/tmp/caf\\xe9"): the action's plain
sentence first, then the error's kind and text exactly as the system reported it, with the path as
\\udce9 and never rewritten to \\xe9, and writing them raises nothing (docs/CONTENT.md RN-35, SDD
§ 4 OB-3). The stream is Python's own: a text wrapper over a byte buffer with the error handler
Python opens sys.stderr with, because pytest's capture encodes strictly and would raise on the
message form for a reason that is the capture's and not the tracker's. The real Site and Tracker
are used, the failure enters through a Tracker handed to Site, and no product name is patched.
"""

from __future__ import annotations

import contextlib
import io
import os
from pathlib import Path
from typing import NoReturn
from urllib.parse import urlencode

import pytest
from test_comment_routes import add_comment
from test_routes import HOST
from test_task_routes import MovableClock, location

from application import Tracker, TrackerState
from domain import empty_state
from persistence import SavedData
from tests.fakes import FakeSaver
from web import Response, Site

PATH = os.fsdecode(b"/tmp/caf\xe9")
PATH_AS_REPORTED = r"/tmp/caf\udce9"
SENTENCE = "The tracker couldn't add your comment, and nothing was changed."
MISSING_TASK = 5
TYPED = "Hi"
FAILURE_REDIRECT = (
    f"/tasks/{MISSING_TASK}?{urlencode({'comment_failed': 'add', 'comment_text': TYPED})}"
)

# Each error form: the arguments of the OSError, and the second console line it must produce.
ERROR_FORMS = {
    "message": (
        (f"cannot write {PATH}",),
        f"OSError: cannot write {PATH_AS_REPORTED}",
    ),
    "errno": (
        (92, "Illegal byte sequence", PATH),
        f"OSError: [Errno 92] Illegal byte sequence: '{PATH_AS_REPORTED}'",
    ),
}


class CommentAddFails(Tracker):
    """A Tracker whose comment add raises the error it was given, as a failed write would."""

    def __init__(
        self, failure: OSError, state: TrackerState, saver: FakeSaver, clock: MovableClock
    ) -> None:
        super().__init__(state, saver, clock)
        self._failure = failure

    def add_task_comment(self, task_id: int, text: str) -> NoReturn:
        raise self._failure


def fail_comment_add(tmp_path: Path, error_args: tuple[object, ...]) -> tuple[Response, bytes]:
    """Post a comment add that fails with the error; answer the response and the stream's bytes."""
    saver = FakeSaver(passes_to=SavedData(tmp_path / "data"))
    tracker = CommentAddFails(OSError(*error_args), empty_state(), saver, MovableClock())
    buffer = io.BytesIO()
    stream = io.TextIOWrapper(buffer, encoding="utf-8", errors="backslashreplace")
    with contextlib.redirect_stderr(stream):
        response = add_comment(Site(tracker, HOST), TYPED, task=MISSING_TASK)
    stream.flush()
    return response, buffer.getvalue()


@pytest.mark.parametrize("form", ERROR_FORMS)
def test_failed_action_prints_its_sentence_then_the_error_as_reported(
    tmp_path: Path, form: str
) -> None:
    error_args, error_line = ERROR_FORMS[form]
    _, written = fail_comment_add(tmp_path, error_args)

    lines = written.decode("utf-8").splitlines()
    assert lines == [SENTENCE, error_line]
    sentence, reported = lines
    assert "caf" not in sentence
    assert "\\xe9" not in sentence
    assert "\xe9" not in sentence
    assert "\\xe9" not in reported
    assert "\xe9" not in reported
    assert written.endswith(b"\n")


@pytest.mark.parametrize("form", ERROR_FORMS)
def test_failed_action_answers_with_its_failure_response(tmp_path: Path, form: str) -> None:
    error_args, _ = ERROR_FORMS[form]
    response, _ = fail_comment_add(tmp_path, error_args)

    assert location(response) == FAILURE_REDIRECT
