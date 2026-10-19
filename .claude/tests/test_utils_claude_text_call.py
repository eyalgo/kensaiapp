"""Characterization tests for the login-based `claude -p` helper.

Deterministic: the subprocess boundary is patched, so there is no live model
call and no network. These pin two things the helper must always do — read the
assistant text from the CLI's JSON ``result`` field, and fail loudly (rather
than return an empty description) when the call produces nothing usable.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from scripts.utils import claude_text_call


def test_claude_text_call_extracts_result():
    """The assistant text is read from the CLI's JSON ``result`` field, and the
    prompt is handed to the subprocess on stdin (never as an argv element, which
    would risk the OS argument-length limit on a large prompt)."""
    completed = MagicMock(
        returncode=0,
        stdout=json.dumps({"type": "result", "result": "hello"}),
        stderr="",
    )
    with patch("scripts.utils.subprocess.run", return_value=completed) as run:
        result = claude_text_call("a long improvement prompt", "some-model")

    assert result == "hello"

    command = run.call_args.args[0]
    kwargs = run.call_args.kwargs
    assert kwargs["input"] == "a long improvement prompt"  # prompt via stdin
    assert "a long improvement prompt" not in command      # not in argv


def test_claude_text_call_errors_on_empty():
    """Empty stdout or a non-zero exit raises a clear error rather than silently
    returning an empty description."""
    empty_stdout = MagicMock(returncode=0, stdout="", stderr="")
    with patch("scripts.utils.subprocess.run", return_value=empty_stdout):
        with pytest.raises(RuntimeError):
            claude_text_call("p", "m")

    nonzero_exit = MagicMock(returncode=1, stdout="", stderr="boom")
    with patch("scripts.utils.subprocess.run", return_value=nonzero_exit):
        with pytest.raises(RuntimeError):
            claude_text_call("p", "m")
