"""Characterization tests for the trigger detector in ``run_eval``.

Deterministic: the stream is synthesized line by line and handed straight to the
scanner, so there is no subprocess, no live model call and no network — the same
bargain ``test_utils_claude_text_call.py`` makes, and the same
build-the-events-inline approach ``skill-evals/scripts/test_collect_timing.py``
uses for transcripts (the repo has no captured stream-json to replay).

These pin the thing that made the whole trigger harness read ``recall=0%`` for
every skill: the detector answered *"was the skill the FIRST thing this run
did?"* when the question is *"did the skill fire AT ALL?"*. A model orients
before it acts, so the skill is rarely the literal first move, and every skill
scored zero regardless of its description.

The scanner is deliberately split from the process management it used to be
welded to. ``scan_stream_for_trigger`` decides, from events alone, whether a
named skill was invoked; ``run_single_query`` owns Popen, the timeout, and the
crash-vs-quiet distinction. Only the first is unit-testable, and it is where the
bug lived.
"""

import json

import pytest

from scripts.run_eval import Outcome, scan_stream_for_trigger

TARGET = "product-srs"


# --- event builders — the shapes run_eval parses out of `claude -p` -----------


def _tool_start(name: str) -> str:
    """A `content_block_start` announcing a tool call, before its input arrives."""
    return json.dumps({
        "type": "stream_event",
        "event": {
            "type": "content_block_start",
            "content_block": {"type": "tool_use", "name": name},
        },
    })


def _tool_input(partial: str) -> str:
    """An `input_json_delta` — the tool's arguments, streamed in fragments."""
    return json.dumps({
        "type": "stream_event",
        "event": {
            "type": "content_block_delta",
            "delta": {"type": "input_json_delta", "partial_json": partial},
        },
    })


def _event(kind: str) -> str:
    return json.dumps({"type": "stream_event", "event": {"type": kind}})


def _assistant_tool_use(name: str, tool_input: dict) -> str:
    """The full assistant message, which arrives only after the tool has run."""
    return json.dumps({
        "type": "assistant",
        "message": {"content": [{"type": "tool_use", "name": name, "input": tool_input}]},
    })


def _result() -> str:
    return json.dumps({"type": "result", "subtype": "success"})


# --- the regression this whole exercise exists for ---------------------------


def test_skill_firing_after_an_unrelated_tool_is_still_a_trigger():
    """THE regression. A run that greps before reaching for the skill has still
    used the skill. The old detector returned False the moment it saw a tool that
    was not Skill/Read, stopped watching, and reported a non-trigger — which is
    why five substantially different descriptions produced bit-identical zeros."""
    stream = [
        _tool_start("Bash"),
        _tool_input('{"command": "ls"}'),
        _event("content_block_stop"),
        _tool_start("Skill"),
        _tool_input(f'{{"skill": "{TARGET}"}}'),
        _event("content_block_stop"),
        _result(),
    ]
    assert scan_stream_for_trigger(stream, TARGET) is True


def test_a_todo_write_first_does_not_conclude_the_run():
    """Same shape, different first tool — models very commonly plan before acting."""
    stream = [
        _tool_start("TodoWrite"),
        _tool_input('{"todos": []}'),
        _event("content_block_stop"),
        _tool_start("Skill"),
        _tool_input(f'{{"skill": "{TARGET}"}}'),
        _result(),
    ]
    assert scan_stream_for_trigger(stream, TARGET) is True


def test_an_unrelated_read_does_not_conclude_the_run():
    """`Read` used to be treated as a candidate and then settled the verdict at
    content_block_stop, so opening any unrelated file ended the watch."""
    stream = [
        _tool_start("Read"),
        _tool_input('{"file_path": "/etc/hosts"}'),
        _event("content_block_stop"),
        _tool_start("Skill"),
        _tool_input(f'{{"skill": "{TARGET}"}}'),
        _result(),
    ]
    assert scan_stream_for_trigger(stream, TARGET) is True


def test_message_stop_between_turns_does_not_conclude_the_run():
    """`message_stop` ends every assistant message, not just the last one. Treating
    it as the end of the run cut the watch off at the first turn."""
    stream = [
        _tool_start("Grep"),
        _event("content_block_stop"),
        _event("message_stop"),
        _tool_start("Skill"),
        _tool_input(f'{{"skill": "{TARGET}"}}'),
        _result(),
    ]
    assert scan_stream_for_trigger(stream, TARGET) is True


# --- behaviour that was already right and must stay right --------------------


def test_skill_firing_first_is_a_trigger():
    stream = [
        _tool_start("Skill"),
        _tool_input(f'{{"skill": "{TARGET}"}}'),
        _result(),
    ]
    assert scan_stream_for_trigger(stream, TARGET) is True


def test_a_run_that_never_calls_the_skill_is_not_a_trigger():
    stream = [
        _tool_start("Bash"),
        _tool_input('{"command": "ls"}'),
        _event("content_block_stop"),
        _event("message_stop"),
        _result(),
    ]
    assert scan_stream_for_trigger(stream, TARGET) is False


def test_a_different_skill_is_not_this_skill():
    """The name has to match the skill under test, or every eval measures the
    wrong instrument."""
    stream = [
        _tool_start("Skill"),
        _tool_input('{"skill": "some-other-skill"}'),
        _result(),
    ]
    assert scan_stream_for_trigger(stream, TARGET) is False


def test_the_full_assistant_message_is_a_fallback_path():
    """Partial-message events are the fast path; the complete assistant message
    arrives after the tool runs and must also be understood."""
    stream = [_assistant_tool_use("Skill", {"skill": TARGET}), _result()]
    assert scan_stream_for_trigger(stream, TARGET) is True


def test_only_the_first_tool_use_in_a_message_used_to_be_examined():
    """A single assistant message can carry several tool_use blocks. The old code
    returned inside the loop over them, so anything after the first was invisible."""
    message = json.dumps({
        "type": "assistant",
        "message": {
            "content": [
                {"type": "tool_use", "name": "Bash", "input": {"command": "ls"}},
                {"type": "tool_use", "name": "Skill", "input": {"skill": TARGET}},
            ]
        },
    })
    assert scan_stream_for_trigger([message, _result()], TARGET) is True


# --- robustness --------------------------------------------------------------


def test_a_stream_that_ends_without_a_result_event_still_returns():
    """A truncated stream must produce a verdict rather than hang or raise —
    the run may have been killed at the timeout."""
    stream = [_tool_start("Bash"), _tool_input('{"command": "ls"}')]
    assert scan_stream_for_trigger(stream, TARGET) is False


def test_unparseable_lines_are_skipped_not_fatal():
    """Partial writes and interleaved noise are normal on a streamed pipe."""
    stream = [
        "not json at all",
        "",
        _tool_start("Skill"),
        _tool_input(f'{{"skill": "{TARGET}"}}'),
        _result(),
    ]
    assert scan_stream_for_trigger(stream, TARGET) is True


def test_input_split_across_several_deltas_is_reassembled():
    """`input_json_delta` fragments arbitrarily; the name can straddle a boundary."""
    stream = [
        _tool_start("Skill"),
        _tool_input('{"skill": "prod'),
        _tool_input('uct-srs"}'),
        _result(),
    ]
    assert scan_stream_for_trigger(stream, TARGET) is True


def test_scanning_stops_at_the_result_event():
    """`result` is the one true terminator. Anything after it belongs to no run."""
    stream = [
        _event("message_stop"),
        _result(),
        _tool_start("Skill"),
        _tool_input(f'{{"skill": "{TARGET}"}}'),
    ]
    assert scan_stream_for_trigger(stream, TARGET) is False


# --- the third outcome -------------------------------------------------------


def test_outcome_distinguishes_a_crash_from_a_quiet_run():
    """A crashed run and a run that simply did not reach for the skill are
    different facts. Collapsing them is what made a broken harness look like a
    bad description for two hours: stderr went to DEVNULL and the exception path
    recorded False, so infrastructure failure scored exactly like a miss."""
    assert Outcome.ERRORED != Outcome.NOT_TRIGGERED
    assert Outcome.TRIGGERED != Outcome.NOT_TRIGGERED


def test_outcomes_survive_a_process_boundary():
    """Results cross a ProcessPoolExecutor, so every outcome must pickle."""
    import pickle

    for outcome in (Outcome.TRIGGERED, Outcome.NOT_TRIGGERED, Outcome.ERRORED):
        assert pickle.loads(pickle.dumps(outcome)) is outcome


@pytest.mark.parametrize(
    "outcome,expected",
    [(Outcome.TRIGGERED, True), (Outcome.NOT_TRIGGERED, False), (Outcome.ERRORED, False)],
)
def test_only_a_trigger_counts_as_a_trigger(outcome, expected):
    assert (outcome is Outcome.TRIGGERED) is expected
