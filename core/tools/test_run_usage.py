"""Tests for `run_usage.py` — what a background run used, read off its own transcript.

Fixtures below are shaped off the live disk, not invented: `claude agents --json --all` field
names and the `<synthetic>`/thinking-tokens shapes were read from this machine's own
`~/.claude/projects/*/*.jsonl` on 2026-09-04, the same day the plan was written.
"""

from __future__ import annotations

import ast
import dataclasses
import inspect
import json
import os
import re
from pathlib import Path

import pytest

import run_usage


# ── Reader ports (this station) — the two ports, and one composition root ──
#
# `core/doctrine/engineering/languages/python/conventions.md` § Constructs: "A module is given
# its collaborators; it constructs none." These tests hold that against `run_usage.py` itself —
# by effect, via `ast`/`inspect`, never by re-deriving what the ports do from their own bodies.


class TestPortsAndTheCompositionRoot:
    def test_files_finds_transcripts_matching_a_session_id_under_a_root(self, tmp_path):
        project = tmp_path / "proj"
        project.mkdir()
        transcript = project / "sid-1.jsonl"
        transcript.write_text("")
        files = run_usage.Files()
        assert files.find_transcripts("sid-1", tmp_path) == [transcript]

    def test_files_find_transcripts_on_a_root_with_no_match_is_empty(self, tmp_path):
        (tmp_path / "proj").mkdir()
        files = run_usage.Files()
        assert files.find_transcripts("no-such-sid", tmp_path) == []

    def test_files_find_transcripts_on_a_nonexistent_root_is_empty_not_raising(self, tmp_path):
        files = run_usage.Files()
        assert files.find_transcripts("any-sid", tmp_path / "does-not-exist") == []

    def test_files_read_lines_returns_the_lines_of_a_file(self, tmp_path):
        path = tmp_path / "t.txt"
        path.write_text("a\nb\n")
        files = run_usage.Files()
        assert files.read_lines(path) == ["a", "b"]

    def test_files_read_lines_returns_none_for_a_missing_file(self, tmp_path):
        files = run_usage.Files()
        assert files.read_lines(tmp_path / "does-not-exist") is None

    def test_processes_run_returns_stdout_on_success(self):
        out = run_usage.Processes().run(["python3", "-c", "print('hi')"])
        assert out == "hi\n"

    def test_processes_run_raises_system_exit_naming_code_and_stderr_on_nonzero_exit(self):
        with pytest.raises(SystemExit) as exc_info:
            run_usage.Processes().run(
                ["python3", "-c", "import sys; print('boom', file=sys.stderr); sys.exit(3)"]
            )
        message = str(exc_info.value)
        assert "3" in message
        assert "boom" in message

    def test_files_exposes_exactly_the_three_filesystem_capabilities_and_nothing_else(self):
        # "finding the transcripts matching a session id under a root, finding an instance's
        # claude run logs, and reading a file's lines. Nothing else." A fourth capability would
        # be a world-reach nothing sanctioned, and no other test in this file would notice one
        # arriving. The third arrived on 2026-09-25 with --run-logs.
        assert {name for name in vars(run_usage.Files) if not name.startswith("_")} == {
            "find_transcripts",
            "find_run_logs",
            "read_lines",
        }

    def test_processes_exposes_exactly_one_capability(self):
        assert {name for name in vars(run_usage.Processes) if not name.startswith("_")} == {"run"}

    def test_no_module_level_name_holds_the_expanded_projects_root(self):
        # The default root is resolved "not in a unit body and not as an argparse default" —
        # and an argparse default is filled from a module constant evaluated at import, which
        # is the shape this replaced. By effect: importing the module expands no home.
        default_root = Path.home() / ".claude" / "projects"
        holders = [
            name
            for name, value in vars(run_usage).items()
            if value == default_root or value == str(default_root)
        ]
        assert holders == []

    def test_build_reader_resolves_the_default_projects_root(self):
        reader = run_usage.build_reader()
        assert reader.projects_root == Path.home() / ".claude" / "projects"
        assert isinstance(reader.files, run_usage.Files)
        assert isinstance(reader.processes, run_usage.Processes)

    def test_build_reader_honors_an_explicit_projects_root(self, tmp_path):
        reader = run_usage.build_reader(tmp_path)
        assert reader.projects_root == tmp_path

    def test_only_build_reader_constructs_a_files_or_a_processes(self):
        # By effect, not by name: walk every function body in the module and record which one
        # names `Files(` or `Processes(` as a call — `build_reader` should be the only hit.
        source = Path(run_usage.__file__).read_text()
        tree = ast.parse(source)
        constructing_functions = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for call in ast.walk(node):
                    if isinstance(call, ast.Call) and isinstance(call.func, ast.Name):
                        if call.func.id in ("Files", "Processes"):
                            constructing_functions.add(node.name)
        assert constructing_functions == {"build_reader"}

    def test_main_obtains_ports_from_build_reader_and_constructs_none_itself(self):
        source = inspect.getsource(run_usage.main)
        assert "build_reader(" in source
        assert "Files(" not in source
        assert "Processes(" not in source


# ── Task 1 — the population is named, and interactive is out of it ────────


def _agents_json(*rows: dict) -> str:
    return json.dumps(list(rows))


def _row(**overrides) -> dict:
    row = {
        "id": "abc123",
        "cwd": "/home/user/projects/kensai/example-host",
        "kind": "background",
        "startedAt": 1788504031568,
        "sessionId": "4ec3eb2b-7c27-4633-b057-1a5c83257e9f",
        "name": "some run",
        "state": "done",
    }
    row.update(overrides)
    return row


def test_interactive_row_is_excluded_background_row_is_kept():
    text = _agents_json(
        _row(kind="interactive", sessionId="s-interactive"),
        _row(kind="background", sessionId="s-background"),
    )
    parsed = run_usage.runs_from(text)
    assert [r.session_id for r in parsed.runs] == ["s-background"]
    assert parsed.interactive_excluded == 1


def test_row_with_no_name_is_kept_not_skipped():
    text = _agents_json(_row(sessionId="s-1"))
    del_row = json.loads(text)
    del del_row[0]["name"]
    text = json.dumps(del_row)
    parsed = run_usage.runs_from(text)
    assert len(parsed.runs) == 1
    assert parsed.runs[0].name is None


def test_row_missing_session_id_is_dropped_and_counted():
    rows = json.loads(_agents_json(_row()))
    del rows[0]["sessionId"]
    text = json.dumps(rows)
    parsed = run_usage.runs_from(text)
    assert parsed.runs == ()
    assert parsed.dropped_no_session == 1


def test_cwd_state_and_started_at_survive_unchanged():
    text = _agents_json(_row(cwd="/some/path", state="blocked", startedAt=42))
    parsed = run_usage.runs_from(text)
    run = parsed.runs[0]
    assert run.cwd == "/some/path"
    assert run.state == "blocked"
    assert run.started_at == 42


def test_malformed_top_level_json_raises_naming_the_input():
    with pytest.raises(ValueError, match="agents"):
        run_usage.runs_from("{not json")


# ── Task 2 — a session id resolves to one transcript or to none ─────────


class FakeFiles:
    """A scripted answer for each `Files` method — constructed per test, never patched onto the
    module. `transcripts` maps a session id to the list of `Path`s `find_transcripts` answers
    with; `lines` maps a `Path` to the list of lines `read_lines` answers with (absent → `None`,
    the "unreadable" case)."""

    def __init__(self, transcripts: dict | None = None, lines: dict | None = None):
        self._transcripts = transcripts or {}
        self._lines = lines or {}

    def find_transcripts(self, session_id, projects_root):
        return list(self._transcripts.get(session_id, []))

    def read_lines(self, path):
        return self._lines.get(path)


def test_session_id_with_a_file_resolves():
    transcript = Path("/projects/-Users-someone/sid-1.jsonl")
    files = FakeFiles(transcripts={"sid-1": [transcript]})
    result = run_usage.transcript_for("sid-1", Path("/projects"), files)
    assert result == transcript
    assert isinstance(result, Path)


def test_session_id_with_no_file_returns_none():
    files = FakeFiles()
    assert run_usage.transcript_for("no-such-sid", Path("/projects"), files) is None


def test_session_id_under_two_project_slugs_returns_one_deterministic_path():
    first = Path("/projects/project-a/dup-sid.jsonl")
    second = Path("/projects/project-b/dup-sid.jsonl")
    files = FakeFiles(transcripts={"dup-sid": [second, first]})  # scripted out of sorted order
    result = run_usage.transcript_for("dup-sid", Path("/projects"), files)
    assert result == first  # lexicographically first, regardless of the port's own order
    assert result == run_usage.transcript_for("dup-sid", Path("/projects"), files)


def test_nonexistent_projects_root_returns_none_rather_than_raising(tmp_path):
    # A real `Files()` against a real, nonexistent root — proving the port's own contract,
    # not a scripted stand-in for it.
    files = run_usage.Files()
    missing = tmp_path / "does-not-exist"
    assert run_usage.transcript_for("any-sid", missing, files) is None


def test_transcript_for_body_reaches_the_filesystem_only_through_files():
    source = inspect.getsource(run_usage.transcript_for)
    assert "glob" not in source
    assert "os.path" not in source
    assert "open(" not in source


# ── Task 3 — only assistant records with usage are read ────────────


def _usage_line(
    model="claude-sonnet-5", input_tokens=1, output_tokens=1, timestamp="2026-09-04T00:00:00.000Z"
):
    return json.dumps(
        {
            "type": "assistant",
            "timestamp": timestamp,
            "message": {
                "model": model,
                "usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cache_read_input_tokens": 0,
                    "cache_creation_input_tokens": 0,
                    "cache_creation": {
                        "ephemeral_1h_input_tokens": 0,
                        "ephemeral_5m_input_tokens": 0,
                    },
                },
            },
        }
    )


def test_assistant_record_with_usage_is_yielded_others_are_not(tmp_path):
    path = tmp_path / "t.jsonl"
    lines = [
        _usage_line(),
        json.dumps({"type": "user", "message": {"content": "hi"}}),
        json.dumps({"type": "system"}),
        json.dumps({"type": "attachment"}),
    ]
    path.write_text("\n".join(lines) + "\n")
    records = list(run_usage.usage_records(path, run_usage.Files()))
    assert len(records) == 1
    usage, model, timestamp = records[0]
    assert model == "claude-sonnet-5"
    assert usage["input_tokens"] == 1
    assert timestamp == "2026-09-04T00:00:00.000Z"


def test_assistant_record_with_no_usage_is_skipped(tmp_path):
    path = tmp_path / "t.jsonl"
    record = {"type": "assistant", "message": {"model": "claude-sonnet-5"}}
    path.write_text(json.dumps(record) + "\n")
    assert list(run_usage.usage_records(path, run_usage.Files())) == []


def test_truncated_final_line_is_skipped_not_fatal(tmp_path):
    path = tmp_path / "t.jsonl"
    path.write_text(_usage_line() + "\n" + '{"type": "assistant", "message": {"usage"')
    records = list(run_usage.usage_records(path, run_usage.Files()))
    assert len(records) == 1


def test_empty_file_yields_nothing_and_does_not_raise(tmp_path):
    path = tmp_path / "t.jsonl"
    path.write_text("")
    assert list(run_usage.usage_records(path, run_usage.Files())) == []


def test_missing_file_yields_nothing_rather_than_raising(tmp_path):
    # Not covered before this task: every existing case reached `usage_records` through a
    # transcript `transcript_for` had already resolved, so the file always existed. The
    # docstring's own claim — "a missing file yields nothing rather than raising" — had no test.
    missing = tmp_path / "does-not-exist.jsonl"
    assert list(run_usage.usage_records(missing, run_usage.Files())) == []


def _usage_line_with_id(message_id, output_tokens=1, cache_read=0):
    """One `assistant` record carrying an explicit `message.id`.

    The harness writes one record per CONTENT BLOCK of a single API response — thinking, then
    tool_use, then text — and every one of them repeats that response's `message.usage` verbatim
    under the same `message.id`. So a fixture for this behaviour has to be able to say "these two
    records are one response", which `_usage_line` cannot: it writes no id at all.
    """
    return json.dumps(
        {
            "type": "assistant",
            "timestamp": "2026-09-04T00:00:00.000Z",
            "message": {
                "id": message_id,
                "model": "claude-sonnet-5",
                "usage": {
                    "input_tokens": 2,
                    "output_tokens": output_tokens,
                    "cache_read_input_tokens": cache_read,
                    "cache_creation_input_tokens": 0,
                    "cache_creation": {
                        "ephemeral_1h_input_tokens": 0,
                        "ephemeral_5m_input_tokens": 0,
                    },
                },
            },
        }
    )


def test_one_api_response_split_across_content_blocks_is_counted_once(tmp_path):
    # The defect this fixes: three records, one response, one `message.id`, the same usage block
    # repeated verbatim on each. Counting per record multiplied every figure this reader has ever
    # produced — and by a factor that differs per population (1.74x to 3.35x measured on live
    # transcripts 2026-09-09), so it never cancelled out of a comparison between two of them.
    path = tmp_path / "t.jsonl"
    path.write_text(
        "\n".join(_usage_line_with_id("msg_01", output_tokens=212, cache_read=39729) for _ in range(3))
        + "\n"
    )
    records = list(run_usage.usage_records(path, run_usage.Files()))
    assert len(records) == 1
    usage, _model, _timestamp = records[0]
    assert usage["output_tokens"] == 212
    assert usage["cache_read_input_tokens"] == 39729


def test_distinct_api_responses_are_each_counted(tmp_path):
    path = tmp_path / "t.jsonl"
    lines = [_usage_line_with_id("msg_01"), _usage_line_with_id("msg_02"), _usage_line_with_id("msg_03")]
    path.write_text("\n".join(lines) + "\n")
    assert len(list(run_usage.usage_records(path, run_usage.Files()))) == 3


def test_a_record_carrying_no_message_id_is_never_deduplicated(tmp_path):
    # A record with no id has no identity to compare, so two of them are two responses as far as
    # anything here can tell. Dropping the second would be a silent UNDERcount, which is the one
    # failure worse than the overcount this task removes — and every fixture written before this
    # task omits the id, so this is also what keeps their meaning intact.
    path = tmp_path / "t.jsonl"
    path.write_text(_usage_line() + "\n" + _usage_line() + "\n")
    assert len(list(run_usage.usage_records(path, run_usage.Files()))) == 2


def test_the_deduplication_key_is_the_message_id_not_the_usage_payload(tmp_path):
    # Two genuinely different responses can carry identical usage — a cached pair of short turns
    # does exactly that. Keying on the payload would collapse them; keying on the id does not.
    path = tmp_path / "t.jsonl"
    lines = [_usage_line_with_id("msg_01", output_tokens=7), _usage_line_with_id("msg_02", output_tokens=7)]
    path.write_text("\n".join(lines) + "\n")
    assert len(list(run_usage.usage_records(path, run_usage.Files()))) == 2


def test_usage_records_body_reaches_the_filesystem_only_through_files():
    source = inspect.getsource(run_usage.usage_records)
    assert "open(" not in source


# ── Task 4 — the five classes stay apart, and thinking is a share ─────────


def _usage(
    input_tokens=1,
    output_tokens=1,
    cache_read=0,
    ephemeral_1h=0,
    ephemeral_5m=0,
    thinking_tokens=None,
):
    usage = {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cache_read_input_tokens": cache_read,
        "cache_creation_input_tokens": ephemeral_1h + ephemeral_5m,
        "cache_creation": {
            "ephemeral_1h_input_tokens": ephemeral_1h,
            "ephemeral_5m_input_tokens": ephemeral_5m,
        },
    }
    if thinking_tokens is not None:
        usage["output_tokens_details"] = {"thinking_tokens": thinking_tokens}
    return usage


def test_five_classes_are_separate_fields_none_is_their_sum():
    usage = _usage(
        input_tokens=10, output_tokens=20, cache_read=30, ephemeral_1h=40, ephemeral_5m=50
    )
    records = [(usage, "m", "t")]
    spend = run_usage.spend_by_model(records)["m"]
    assert spend.input == 10
    assert spend.output == 20
    assert spend.cache_read == 30
    assert spend.cache_write_1h == 40
    assert spend.cache_write_5m == 50


def test_cache_creation_reconciles_against_the_two_ephemeral_figures():
    records = [(_usage(ephemeral_1h=100, ephemeral_5m=25), "m", "t")]
    spend = run_usage.spend_by_model(records)["m"]
    assert spend.cache_write_1h == 100
    assert spend.cache_write_5m == 25


def test_cache_creation_input_tokens_is_never_carried_as_a_sixth_class():
    # The fixture's `cache_creation_input_tokens` is 125 — the figure the two ephemerals
    # reconcile to. Task 4's intent keeps the parts and refuses the sum: five classes, and
    # `thinking`, which is a share of `output` rather than a class of its own.
    usage = _usage(
        input_tokens=2, output_tokens=3, cache_read=7, ephemeral_1h=100, ephemeral_5m=25
    )
    spend = run_usage.spend_by_model([(usage, "m", "t")])["m"]
    assert {f.name for f in dataclasses.fields(run_usage.ModelSpend)} == {
        "input",
        "output",
        "cache_read",
        "cache_write_1h",
        "cache_write_5m",
        "thinking",
    }
    classes = [
        spend.input,
        spend.output,
        spend.cache_read,
        spend.cache_write_1h,
        spend.cache_write_5m,
    ]
    assert 125 not in classes, "the cache-creation sum is carried as a class"
    assert sum(classes) not in classes, "a class holds the five-class grand total"


def test_thinking_is_an_int_when_only_some_of_a_models_records_carried_details():
    # 9,717 of 10,028 records on the live disk carry `output_tokens_details`, so a model whose
    # records are split across both shapes is the ordinary case, not an edge one.
    records = [
        (_usage(output_tokens=10), "m", "t"),
        (_usage(output_tokens=20, thinking_tokens=7), "m", "t"),
    ]
    spend = run_usage.spend_by_model(records)["m"]
    assert spend.output == 30
    assert spend.thinking == 7


def test_thinking_is_none_when_absent_and_int_when_present():
    no_thinking = run_usage.spend_by_model([(_usage(), "m", "t")])["m"]
    assert no_thinking.thinking is None
    with_thinking = run_usage.spend_by_model([(_usage(thinking_tokens=0), "m", "t")])["m"]
    assert with_thinking.thinking == 0


def test_thinking_is_never_added_to_output():
    records = [(_usage(output_tokens=194, thinking_tokens=112), "m", "t")]
    spend = run_usage.spend_by_model(records)["m"]
    assert spend.output == 194
    assert spend.thinking == 112


def test_synthetic_is_its_own_key_never_folded_into_a_real_model():
    records = [
        (_usage(input_tokens=5), "claude-sonnet-5", "t"),
        (_usage(input_tokens=7), "<synthetic>", "t"),
    ]
    spend = run_usage.spend_by_model(records)
    assert spend["claude-sonnet-5"].input == 5
    assert spend["<synthetic>"].input == 7


def test_two_models_produce_two_rows_one_model_produces_one():
    two = run_usage.spend_by_model([(_usage(), "a", "t"), (_usage(), "b", "t")])
    assert set(two.keys()) == {"a", "b"}
    one = run_usage.spend_by_model([(_usage(), "a", "t"), (_usage(), "a", "t")])
    assert set(one.keys()) == {"a"}


# ── Task 5 — the span is measured, never summed ───────────────


def _at(ts):
    return (_usage(), "m", ts)


def test_two_records_an_hour_apart_give_3600_regardless_of_count_between():
    records = [
        _at("2026-09-04T00:00:00.000Z"),
        _at("2026-09-04T00:20:00.000Z"),
        _at("2026-09-04T00:40:00.000Z"),
        _at("2026-09-04T01:00:00.000Z"),
    ]
    assert run_usage.span_seconds(records) == 3600


def test_one_record_gives_zero():
    assert run_usage.span_seconds([_at("2026-09-04T00:00:00.000Z")]) == 0


def test_no_records_gives_none_not_zero():
    assert run_usage.span_seconds([]) is None


def test_out_of_order_records_still_give_the_full_span():
    records = [
        _at("2026-09-04T00:40:00.000Z"),
        _at("2026-09-04T00:00:00.000Z"),
        _at("2026-09-04T01:00:00.000Z"),
        _at("2026-09-04T00:20:00.000Z"),
    ]
    assert run_usage.span_seconds(records) == 3600


# ── Task 6 — the ledger states what it could not read ─────────────


def _run(session_id, **overrides):
    fields = {
        "session_id": session_id,
        "name": "a run",
        "cwd": "/cwd",
        "state": "done",
        "started_at": 1,
    }
    fields.update(overrides)
    return run_usage.Run(**fields)


def _project(tmp_path, slug="proj"):
    project = tmp_path / slug
    project.mkdir(exist_ok=True)
    return project


def test_one_unreadable_of_three_gives_two_rows_and_coverage(tmp_path):
    project = _project(tmp_path)
    (project / "sid-1.jsonl").write_text(_usage_line())
    (project / "sid-2.jsonl").write_text(_usage_line())
    # sid-3 has no transcript file at all
    runs = [_run("sid-1"), _run("sid-2"), _run("sid-3")]
    led = run_usage.ledger(runs, tmp_path, run_usage.Files())
    assert len(led.rows) == 2
    assert led.coverage.read == 2
    assert led.coverage.unreadable == 1
    assert led.coverage.total == 3
    assert led.coverage.unreadable_ids == ("sid-3",)


def test_transcript_with_no_usage_records_counts_as_read_with_zero_spend(tmp_path):
    project = _project(tmp_path)
    (project / "sid-1.jsonl").write_text(json.dumps({"type": "user", "message": {}}) + "\n")
    led = run_usage.ledger([_run("sid-1")], tmp_path, run_usage.Files())
    assert led.coverage.read == 1
    assert led.coverage.unreadable == 0
    assert led.rows[0].spend == {}
    assert led.rows[0].span_seconds is None


def test_ledger_threads_the_resolved_transcript_as_a_path_into_usage_records(tmp_path):
    """Every path in and out of `ledger` is a `Path` — proven by a spy `Files` that records the
    type of what it was actually asked to read, not by re-deriving the value from the plain
    `str` this used to be."""
    project = _project(tmp_path)
    transcript = project / "sid-1.jsonl"
    transcript.write_text(_usage_line())

    class SpyFiles(run_usage.Files):
        def __init__(self):
            self.read_paths = []

        def read_lines(self, path):
            self.read_paths.append(path)
            return super().read_lines(path)

    files = SpyFiles()
    led = run_usage.ledger([_run("sid-1")], tmp_path, files)
    assert led.coverage.read == 1
    assert files.read_paths == [transcript]
    assert all(isinstance(path, Path) for path in files.read_paths)


def test_coverage_present_even_when_everything_read_cleanly(tmp_path):
    project = _project(tmp_path)
    (project / "sid-1.jsonl").write_text(_usage_line())
    led = run_usage.ledger([_run("sid-1")], tmp_path, run_usage.Files())
    assert led.coverage.read == 1
    assert led.coverage.unreadable == 0
    assert led.coverage.total == 1
    assert led.coverage.unreadable_ids == ()


# ── Task 7 — the two renderings, and neither one totals ────────────


def _ledger_row(session_id="sid-1", spend=None, span=60):
    return run_usage.LedgerRow(
        session_id=session_id,
        name="a run",
        cwd="/cwd",
        state="done",
        started_at=1,
        span_seconds=span,
        spend=spend if spend is not None else {},
    )


def _small_ledger():
    row = _ledger_row(
        spend={"claude-sonnet-5": run_usage.ModelSpend(input=1, output=194, thinking=112)}
    )
    return run_usage.Ledger(
        rows=(row,),
        coverage=run_usage.Coverage(read=1, unreadable=1, total=2, unreadable_ids=("sid-2",)),
    )


def test_both_renderings_carry_the_population_sentence_verbatim():
    # The words the reader defines `kind != "interactive"` by, not merely those two tokens
    # appearing somewhere in the output.
    led = _small_ledger()
    assert run_usage.POPULATION_NOTE in run_usage.render(led)
    assert 'kind != "interactive"' in run_usage.POPULATION_NOTE
    assert json.loads(run_usage.render_json(led))["population"] == run_usage.POPULATION_NOTE


def test_both_renderings_carry_read_unreadable_total_and_name_the_unreadable_ids():
    led = _small_ledger()  # read 1 / unreadable 1 / total 2, the unreadable one being sid-2
    human = run_usage.render(led)
    assert "1 read" in human
    assert "1 unreadable" in human
    assert "2 total" in human
    assert "sid-2" in human
    assert json.loads(run_usage.render_json(led))["coverage"] == {
        "read": 1,
        "unreadable": 1,
        "total": 2,
        "unreadable_ids": ["sid-2"],
        "dropped_no_session": 0,
    }


def test_no_rendered_number_equals_the_grand_total():
    # cache reads ~250x everything else — the trap: a naive summary might print the sum.
    spend = {
        "claude-opus-5": run_usage.ModelSpend(
            input=2, output=3, cache_read=250_000, cache_write_1h=5, cache_write_5m=1, thinking=None
        )
    }
    grand_total = 2 + 3 + 250_000 + 5 + 1
    led = run_usage.Ledger(
        rows=(_ledger_row(spend=spend),),
        coverage=run_usage.Coverage(read=1, unreadable=0, total=1, unreadable_ids=()),
    )
    for text in (run_usage.render(led), run_usage.render_json(led)):
        assert str(grand_total) not in text


def test_render_json_round_trips_and_carries_one_object_per_run():
    led = run_usage.Ledger(
        rows=(_ledger_row("sid-1"), _ledger_row("sid-2")),
        coverage=run_usage.Coverage(read=2, unreadable=0, total=2, unreadable_ids=()),
    )
    payload = json.loads(run_usage.render_json(led))
    assert len(payload["rows"]) == 2
    assert {r["session_id"] for r in payload["rows"]} == {"sid-1", "sid-2"}


def test_thinking_none_renders_no_thinking_figure_not_zero():
    row = _ledger_row(spend={"m": run_usage.ModelSpend(input=1, output=1, thinking=None)})
    coverage = run_usage.Coverage(read=1, unreadable=0, total=1, unreadable_ids=())
    led = run_usage.Ledger(rows=(row,), coverage=coverage)
    assert "thinking" not in run_usage.render(led)
    payload = json.loads(run_usage.render_json(led))
    assert payload["rows"][0]["spend"]["m"]["thinking"] is None


# ── Task 8 (this station) — a dropped row is visible in both renderings ────


def test_dropped_no_session_row_is_visible_in_both_renderings(tmp_path):
    rows = json.loads(_agents_json(_row(sessionId="sid-1"), _row()))
    del rows[1]["sessionId"]
    parsed = run_usage.runs_from(json.dumps(rows))
    assert parsed.dropped_no_session == 1

    project = _project(tmp_path)
    (project / "sid-1.jsonl").write_text(_usage_line())
    led = run_usage.ledger(
        parsed.runs, tmp_path, run_usage.Files(), dropped_no_session=parsed.dropped_no_session
    )

    human = run_usage.render(led)
    assert "Dropped (no sessionId): 1" in human
    payload = json.loads(run_usage.render_json(led))
    assert payload["coverage"]["dropped_no_session"] == 1

    # read + unreadable + dropped == the population before dropping (both rows the fixture
    # carried: the one kept and the one dropped for having no sessionId).
    assert led.coverage.read + led.coverage.unreadable + led.coverage.dropped_no_session == 2


def test_zero_dropped_rows_still_states_the_count_not_silent():
    coverage = run_usage.Coverage(
        read=0, unreadable=0, total=0, unreadable_ids=(), dropped_no_session=0
    )
    led = run_usage.Ledger(rows=(), coverage=coverage)
    assert "Dropped (no sessionId): 0" in run_usage.render(led)
    payload = json.loads(run_usage.render_json(led))
    assert payload["coverage"]["dropped_no_session"] == 0


def test_main_states_a_dropped_row_in_the_human_summary_and_in_the_json(tmp_path, capsys):
    # Reached-when 4 is about the reader's own output, not about `ledger`'s return value: the
    # count has to survive `main`'s wiring from `runs_from` through to both renderings. Every
    # other dropped-row test here calls `ledger` directly and would stay green if that wiring
    # were cut.
    project = _project(tmp_path)
    (project / "sid-1.jsonl").write_text(_usage_line())
    rows = [_row(sessionId="sid-1"), _row()]
    del rows[1]["sessionId"]
    agents_path = tmp_path / "agents.json"
    agents_path.write_text(json.dumps(rows))
    argv = ["--agents-json", str(agents_path), "--projects-root", str(tmp_path)]

    run_usage.main(argv)
    assert "Dropped (no sessionId): 1" in capsys.readouterr().out

    run_usage.main(argv + ["--json"])
    payload = json.loads(capsys.readouterr().out)
    assert payload["coverage"]["dropped_no_session"] == 1
    assert payload["coverage"]["read"] == 1


def test_ledger_defaults_dropped_no_session_to_zero_when_not_passed(tmp_path):
    # A caller that does not know about dropped rows (every pre-existing test) still gets a
    # Coverage that states zero rather than one with no opinion at all.
    project = _project(tmp_path)
    (project / "sid-1.jsonl").write_text(_usage_line())
    led = run_usage.ledger([_run("sid-1")], tmp_path, run_usage.Files())
    assert led.coverage.dropped_no_session == 0


# ── pathlib.Path throughout (this station) ─────────────────


def test_run_usage_module_imports_pathlib_and_neither_os_path_nor_glob():
    source = Path(run_usage.__file__).read_text()
    assert "from pathlib import Path" in source
    assert re.search(r"^import glob$", source, re.MULTILINE) is None
    assert re.search(r"^import os$", source, re.MULTILINE) is None
    assert "os.path" not in source


def test_a_string_projects_root_from_the_command_line_becomes_a_path_at_the_boundary(
    tmp_path, capsys
):
    # By effect: `Files.find_transcripts` calls `projects_root.glob(...)`, so a root that
    # reached it still a `str` could resolve nothing at all. The transcript being read is the
    # proof the conversion happened at the flag, not the annotation saying it should.
    project = _project(tmp_path)
    (project / "sid-1.jsonl").write_text(_usage_line())
    agents_path = _write_agents_json(tmp_path, _row(sessionId="sid-1"))
    run_usage.main(["--agents-json", agents_path, "--projects-root", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert payload["coverage"]["read"] == 1
    assert payload["rows"][0]["spend"]["claude-sonnet-5"]["input"] == 1


def test_ledger_rows_carry_no_path_object_anywhere(tmp_path):
    # Exercised end to end — through the real Files() port, over a real transcript on disk —
    # rather than asserted from a field's type annotation alone.
    project = _project(tmp_path)
    (project / "sid-1.jsonl").write_text(_usage_line())
    led = run_usage.ledger([_run("sid-1")], tmp_path, run_usage.Files())
    for row in led.rows:
        for field in dataclasses.fields(row):
            value = getattr(row, field.name)
            assert not isinstance(value, Path), f"{field.name} carries a Path: {value!r}"
    # `render_json` would have raised on any `Path` it was handed — this is the same fact,
    # proven the other way, over the actual rendering rather than the dataclass alone.
    json.loads(run_usage.render_json(led))


# ── The agents JSON arrives through both ports (this station) ───────────


class FakeProcesses:
    """Records every call, answering with a scripted stdout — constructed per test, never
    patched onto the module."""

    def __init__(self, stdout: str = ""):
        self.calls: list[list[str]] = []
        self._stdout = stdout

    def run(self, argv):
        self.calls.append(list(argv))
        return self._stdout


class RaisingProcesses:
    """A `Processes` that must never be called — proves a code path shells out to nothing by
    failing loudly if it does, rather than by asserting on a global afterward."""

    def run(self, argv):
        raise AssertionError(f"Processes.run must not be called; called with {argv!r}")


def test_agents_json_text_given_a_path_reads_it_through_files_and_never_shells_out(tmp_path):
    path = tmp_path / "agents.json"
    path.write_text("[]")
    text = run_usage._agents_json_text(path, run_usage.Files(), RaisingProcesses())
    assert text.strip() == "[]"


def test_agents_json_text_given_no_path_shells_out_through_processes():
    processes = FakeProcesses(stdout="[]")
    text = run_usage._agents_json_text(None, run_usage.Files(), processes)
    assert text == "[]"
    assert processes.calls == [["claude", "agents", "--json", "--all"]]


def test_agents_json_text_propagates_a_nonzero_exit_as_system_exit():
    class FailingProcesses:
        def run(self, argv):
            raise SystemExit("error: `claude agents --json --all` exited 3: boom")

    with pytest.raises(SystemExit, match="exited 3"):
        run_usage._agents_json_text(None, run_usage.Files(), FailingProcesses())


def test_agents_json_text_body_reaches_the_world_only_through_ports():
    source = inspect.getsource(run_usage._agents_json_text)
    assert "open(" not in source
    assert "subprocess" not in source


# ── Task 8 — the CLI, the docstring and the version ─────────────


def _write_agents_json(tmp_path, *rows):
    path = tmp_path / "agents.json"
    path.write_text(json.dumps(list(rows)))
    return str(path)


def test_agents_json_flag_reads_the_file_and_shells_out_to_nothing(tmp_path):
    agents_path = _write_agents_json(tmp_path, _row(sessionId="sid-1"))
    # A `Processes` that raises if it is ever called — the behaviour this test exists to prove
    # is proven by the fake, not by asserting on a monkeypatched global afterward.
    text = run_usage._agents_json_text(Path(agents_path), run_usage.Files(), RaisingProcesses())
    parsed = run_usage.runs_from(text)
    assert [r.session_id for r in parsed.runs] == ["sid-1"]


def test_no_agents_json_flag_shells_out():
    processes = FakeProcesses(stdout=json.dumps([_row(sessionId="sid-1")]))
    text = run_usage._agents_json_text(None, run_usage.Files(), processes)
    assert processes.calls == [["claude", "agents", "--json", "--all"]]
    parsed = run_usage.runs_from(text)
    assert [r.session_id for r in parsed.runs] == ["sid-1"]


def test_projects_root_defaults_to_the_claude_projects_dir():
    # The behaviour is the flag's default reaching the reader, not a module constant holding
    # the right string — a constant nothing passes would satisfy the second and not the first.
    reader = run_usage.build_reader()
    assert reader.projects_root == Path(os.path.expanduser("~/.claude/projects"))


def test_json_flag_emits_only_the_ledger(tmp_path, capsys):
    agents_path = _write_agents_json(tmp_path, _row(sessionId="sid-1"))
    projects_root = str(tmp_path / "projects")
    run_usage.main(["--agents-json", agents_path, "--projects-root", projects_root, "--json"])
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert "rows" in payload


def test_default_emits_the_human_summary_not_json(tmp_path, capsys):
    agents_path = _write_agents_json(tmp_path, _row(sessionId="sid-1"))
    projects_root = str(tmp_path / "projects")
    run_usage.main(["--agents-json", agents_path, "--projects-root", projects_root])
    out = capsys.readouterr().out
    assert "Population:" in out
    with pytest.raises(json.JSONDecodeError):
        json.loads(out)


def test_version_is_stamped():
    """The marker exists and is well-formed — never its literal value.

    `core/doctrine/governance/versioning.md` puts the bump on the LANDING COMMIT and forbids a
    branch from editing the marker, so a test pinning a value is red at every merge that bumps it
    and green only until the next one. It asserts the shape instead, which is the part a branch
    can actually keep true."""
    assert re.fullmatch(r"\d+\.\d+\.\d+", run_usage.__version__), run_usage.__version__


def test_docstring_states_no_price_model_and_never_sums_and_names_the_cache_creation_split():
    doc = run_usage.__doc__
    assert "No price model" in doc or "no price model" in doc.lower()
    assert "never" in doc.lower() and "sum" in doc.lower()
    assert "cache_creation" in doc
    # the 1h/5m split named as the reason there are five classes, not four
    assert "ephemeral_1h_input_tokens" in doc
    assert "ephemeral_5m_input_tokens" in doc


# ── Adding two spends: one home, because a third reader now wants it ──────


class TestAddAndMergeSpend:
    """`add_spend` / `merge_spend` live here, beside `ModelSpend` and `spend_by_model`, because
    this module owns what a spend IS. They were private in `flow_usage.py` until a third reader
    (`chain_usage.py`) needed the same arithmetic and had to route around them — the next one would
    have copied them or reached into a private name, and a class-by-class accumulator copied twice
    is a rule with three homes to disagree in.
    """

    def test_add_spend_adds_each_class_apart_never_summing_two_classes(self):
        a = run_usage.ModelSpend(input=1, output=2, cache_read=3, cache_write_1h=4, cache_write_5m=5)
        b = run_usage.ModelSpend(
            input=10, output=20, cache_read=30, cache_write_1h=40, cache_write_5m=50
        )
        assert run_usage.add_spend(a, b) == run_usage.ModelSpend(
            input=11, output=22, cache_read=33, cache_write_1h=44, cache_write_5m=55
        )

    def test_add_spend_thinking_stays_none_only_when_both_sides_carry_none(self):
        """`None` means "nothing this model produced carried `output_tokens_details`", which is a
        different fact from zero — so it survives addition only when neither side carried any."""
        a = run_usage.ModelSpend(thinking=None)
        assert run_usage.add_spend(a, run_usage.ModelSpend(thinking=None)).thinking is None
        assert run_usage.add_spend(a, run_usage.ModelSpend(thinking=3)).thinking == 3

    def test_merge_spend_merges_per_model_dicts(self):
        a = {"sonnet": run_usage.ModelSpend(input=1)}
        b = {"sonnet": run_usage.ModelSpend(input=10), "haiku": run_usage.ModelSpend(input=100)}
        merged = run_usage.merge_spend(a, b)
        assert merged["sonnet"].input == 11
        assert merged["haiku"].input == 100

    def test_merge_spend_does_not_mutate_either_argument(self):
        """Not covered where these functions previously lived. `merge_spend` copies its left side,
        and a caller folding many readings into an accumulator would silently corrupt the first
        one if it did not."""
        a = {"sonnet": run_usage.ModelSpend(input=1)}
        b = {"sonnet": run_usage.ModelSpend(input=10)}
        run_usage.merge_spend(a, b)
        assert a == {"sonnet": run_usage.ModelSpend(input=1)}
        assert b == {"sonnet": run_usage.ModelSpend(input=10)}


# ── A `claude --print` run is in no `claude agents` listing — its run log names it ──


def _run_log(logs_dir, name, *events):
    logs_dir.mkdir(parents=True, exist_ok=True)
    path = logs_dir / name
    path.write_text("\n".join(json.dumps(event) for event in events) + "\n")
    return path


def test_runs_from_run_logs_reads_each_claude_run_logs_session(tmp_path):
    logs_dir = tmp_path / "logs"
    _run_log(logs_dir, "claude-demo-20260925-090000-1.jsonl",
             {"type": "system", "subtype": "init", "session_id": "sid-p", "cwd": "/instance"},
             {"type": "result", "subtype": "success", "is_error": False, "session_id": "sid-p"})
    _run_log(logs_dir, "codex-demo-20260925-090000-2.jsonl", {"type": "turn.completed"})

    runs = run_usage.runs_from_run_logs(logs_dir, run_usage.Files())

    assert runs == (
        run_usage.Run(session_id="sid-p", name="claude-demo-20260925-090000-1", cwd="/instance",
                      state="completed", started_at=None),
    )


def test_a_run_log_that_never_named_its_session_is_left_out(tmp_path):
    logs_dir = tmp_path / "logs"
    _run_log(logs_dir, "claude-demo-20260925-090000-1.jsonl", {"type": "kensai.exit", "code": 1})

    assert run_usage.runs_from_run_logs(logs_dir, run_usage.Files()) == ()


def test_main_counts_a_print_run_named_only_by_its_run_log(tmp_path, capsys):
    projects_root = tmp_path / "projects"
    (projects_root / "slug").mkdir(parents=True)
    (projects_root / "slug" / "sid-p.jsonl").write_text(
        json.dumps({"type": "assistant", "timestamp": "2026-09-25T09:00:00Z",
                    "message": {"id": "m1", "model": "claude-sonnet-5",
                                "usage": {"input_tokens": 5, "output_tokens": 3}}}) + "\n"
    )
    logs_dir = tmp_path / "logs"
    _run_log(logs_dir, "claude-demo-20260925-090000-1.jsonl",
             {"type": "system", "subtype": "init", "session_id": "sid-p", "cwd": "/instance"})
    (projects_root / "slug" / "sid-bg.jsonl").write_text(
        (projects_root / "slug" / "sid-p.jsonl").read_text().replace('"m1"', '"m2"')
    )
    # The same session in both populations is one run, never two.
    agents_path = _write_agents_json(tmp_path, _row(sessionId="sid-bg"), _row(sessionId="sid-p"))

    run_usage.main(["--agents-json", agents_path, "--projects-root", str(projects_root),
                    "--run-logs", str(logs_dir), "--json"])

    ledger = json.loads(capsys.readouterr().out)
    assert sorted(row["session_id"] for row in ledger["rows"]) == ["sid-bg", "sid-p"]
    assert "--run-logs" in ledger["population"]
