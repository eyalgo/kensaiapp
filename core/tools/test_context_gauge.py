"""Tests for `context_gauge.py` — the current context of one transcript.

The fixtures are shaped off the transcript records `run_usage.usage_records` already reads: an
`assistant` record whose `message` carries an `id` and a `usage` block. The gauge is handed the
same `Files` port `run_usage` defines, over a real file under `tmp_path`.
"""

from __future__ import annotations

import json
from pathlib import Path

import context_gauge
import run_usage


def _response(message_id: str, *, input_tokens=0, cache_read=0, cache_creation=0) -> dict:
    usage = {
        "input_tokens": input_tokens,
        "cache_read_input_tokens": cache_read,
        "cache_creation_input_tokens": cache_creation,
        "output_tokens": 999,
    }
    return {"type": "assistant", "message": {"id": message_id, "usage": usage}}


def _write(path: Path, records: list[dict], *, tail: str = "") -> Path:
    path.write_text("".join(json.dumps(record) + "\n" for record in records) + tail)
    return path


def test_the_current_context_is_the_last_response_not_the_sum(tmp_path):
    transcript = _write(
        tmp_path / "t.jsonl",
        [
            _response("m1", input_tokens=10, cache_read=100, cache_creation=1000),
            _response("m2", input_tokens=20, cache_read=200, cache_creation=2000),
            _response("m3", input_tokens=30, cache_read=300, cache_creation=3000),
        ],
    )
    assert context_gauge.current_context(transcript, run_usage.Files()) == 3330


def test_a_response_split_across_records_is_read_once(tmp_path):
    transcript = _write(
        tmp_path / "t.jsonl",
        [
            _response("m1", input_tokens=5, cache_read=50, cache_creation=500),
            _response("m2", input_tokens=7, cache_read=70, cache_creation=700),
            _response("m2", input_tokens=7, cache_read=70, cache_creation=700),
            _response("m2", input_tokens=7, cache_read=70, cache_creation=700),
        ],
    )
    assert context_gauge.current_context(transcript, run_usage.Files()) == 777


def test_a_missing_class_counts_as_zero(tmp_path):
    record = {
        "type": "assistant",
        "message": {"id": "m1", "usage": {"input_tokens": 12, "cache_read_input_tokens": 34}},
    }
    transcript = _write(tmp_path / "t.jsonl", [record])
    assert context_gauge.current_context(transcript, run_usage.Files()) == 46


def test_a_missing_transcript_gives_none(tmp_path):
    assert context_gauge.current_context(tmp_path / "absent.jsonl", run_usage.Files()) is None


def test_a_transcript_with_no_assistant_usage_gives_none(tmp_path):
    transcript = _write(
        tmp_path / "t.jsonl",
        [{"type": "user", "message": {"content": "hi"}}, {"type": "assistant", "message": {}}],
    )
    assert context_gauge.current_context(transcript, run_usage.Files()) is None


def test_a_truncated_final_line_is_skipped(tmp_path):
    transcript = _write(
        tmp_path / "t.jsonl",
        [_response("m1", input_tokens=1, cache_read=2, cache_creation=3)],
        tail='{"type": "assistant", "message": {"id": "m2", "usage": {"input_to',
    )
    assert context_gauge.current_context(transcript, run_usage.Files()) == 6


def test_a_null_class_counts_as_zero(tmp_path):
    record = {
        "type": "assistant",
        "message": {
            "id": "m1",
            "usage": {
                "input_tokens": 5,
                "cache_read_input_tokens": None,
                "cache_creation_input_tokens": 7,
            },
        },
    }
    transcript = _write(tmp_path / "t.jsonl", [record])
    assert context_gauge.current_context(transcript, run_usage.Files()) == 12


def test_records_with_no_message_id_are_each_a_response(tmp_path):
    """No id means no identity to compare, so `run_usage` keeps both and the newer one is the
    current context — a first-wins de-duplication would read the older figure."""
    older = {"type": "assistant", "message": {"usage": {"input_tokens": 10}}}
    newer = {"type": "assistant", "message": {"usage": {"input_tokens": 30}}}
    transcript = _write(tmp_path / "t.jsonl", [older, newer])
    assert context_gauge.current_context(transcript, run_usage.Files()) == 30
