"""Tests for `flow_usage.py` — what a `/development` flow run spent, one row per step.

Fixtures below are shaped off the live disk, not invented: the tree shape, the journal record
shapes, and the meta-sidecar shape were read from this machine's own
`~/.claude/projects/*/*/subagents/workflows/*/` on 2026-09-07, the same day the plan was
written — see the plan at `system/projects/tools/journey/shukuba/trail/`,
`2026-09-07_the-step-reader-has-a-plan.md`.
"""

from __future__ import annotations

import ast
import inspect
import json
from pathlib import Path

import pytest

import flow_usage
import run_usage


# ── Task 1 — the workflow runs are found ───────────────────────────────


def _make_workflow_run(root: Path, slug: str, sid: str, wf_id: str) -> Path:
    """`<root>/<slug>/<sid>/subagents/workflows/<wf_id>/journal.jsonl` — the real tree shape."""
    run_dir = root / slug / sid / "subagents" / "workflows" / wf_id
    run_dir.mkdir(parents=True)
    (run_dir / "journal.jsonl").write_text("")
    return run_dir


def test_a_directory_with_a_journal_is_yielded_one_without_is_not(tmp_path):
    good = _make_workflow_run(tmp_path, "slug-a", "sid-1", "wf_good")
    # A workflows sibling with no journal.jsonl at all.
    no_journal = tmp_path / "slug-a" / "sid-1" / "subagents" / "workflows" / "wf_bad"
    no_journal.mkdir(parents=True)

    runs = flow_usage.flow_runs(tmp_path, flow_usage.Files())
    assert [r.run_dir for r in runs] == [good]


def test_flat_agent_tool_sibling_is_never_yielded(tmp_path):
    _make_workflow_run(tmp_path, "slug-a", "sid-1", "wf_good")
    # The flat sibling: <slug>/<sid>/subagents/agent-*.jsonl, no workflows/ level at all.
    flat_dir = tmp_path / "slug-a" / "sid-1" / "subagents"
    (flat_dir / "agent-flatid.jsonl").write_text("")

    runs = flow_usage.flow_runs(tmp_path, flow_usage.Files())
    assert len(runs) == 1
    assert runs[0].wf_id == "wf_good"


def test_interactive_session_transcript_is_never_yielded(tmp_path):
    _make_workflow_run(tmp_path, "slug-a", "sid-1", "wf_good")
    # <slug>/<sid>.jsonl — an interactive session's own transcript, flat under the slug.
    (tmp_path / "slug-a" / "sid-1.jsonl").write_text("")

    runs = flow_usage.flow_runs(tmp_path, flow_usage.Files())
    assert len(runs) == 1


def test_wf_id_session_id_and_slug_are_read_off_the_path(tmp_path):
    _make_workflow_run(tmp_path, "my-slug", "my-sid", "wf_abc123")
    runs = flow_usage.flow_runs(tmp_path, flow_usage.Files())
    assert len(runs) == 1
    run = runs[0]
    assert run.wf_id == "wf_abc123"
    assert run.session_id == "my-sid"
    assert run.slug == "my-slug"


def test_nonexistent_projects_root_yields_nothing_and_does_not_raise(tmp_path):
    missing = tmp_path / "does-not-exist"
    runs = flow_usage.flow_runs(missing, flow_usage.Files())
    assert runs == ()


def test_flow_runs_are_sorted_by_wf_id(tmp_path):
    _make_workflow_run(tmp_path, "slug-a", "sid-1", "wf_zzz")
    _make_workflow_run(tmp_path, "slug-a", "sid-2", "wf_aaa")
    runs = flow_usage.flow_runs(tmp_path, flow_usage.Files())
    assert [r.wf_id for r in runs] == ["wf_aaa", "wf_zzz"]


class TestFilesFindWorkflowDirs:
    def test_finds_a_real_directory_holding_a_journal(self, tmp_path):
        run_dir = _make_workflow_run(tmp_path, "slug-a", "sid-1", "wf_good")
        files = flow_usage.Files()
        assert files.find_workflow_dirs(tmp_path) == [run_dir]

    def test_a_nonexistent_root_yields_no_matches(self, tmp_path):
        files = flow_usage.Files()
        assert files.find_workflow_dirs(tmp_path / "does-not-exist") == []


# ── Task 2 — the journal names each agent's step and its role ─────────────


def _started(agent_id: str) -> str:
    return json.dumps({"type": "started", "key": f"v2:{agent_id}", "agentId": agent_id})


def _result(agent_id: str, result) -> str:
    return json.dumps(
        {"type": "result", "key": f"v2:{agent_id}", "agentId": agent_id, "result": result}
    )


def _failed(agent_id: str) -> str:
    return json.dumps({"type": "failed", "key": f"v2:{agent_id}", "agentId": agent_id})


def test_status_ok_with_artifact_maps_to_step_and_produce_role():
    journal = "\n".join(
        [
            _started("a1"),
            _result(
                "a1", {"step": "development-specs", "status": "ok", "artifact": "change_spec.md"}
            ),
        ]
    )
    parsed = flow_usage.steps_from(journal)
    assert parsed.steps == (
        flow_usage.AgentStep(agent_id="a1", step="development-specs", role=flow_usage.Role.PRODUCE),
    )


def test_result_findings_maps_to_step_and_audit_role_as_a_separate_entry():
    journal = "\n".join(
        [
            _started("a1"),
            _result(
                "a1", {"step": "development-specs", "status": "ok", "artifact": "change_spec.md"}
            ),
            _started("a2"),
            _result(
                "a2", {"step": "development-specs", "result": "findings", "findings": 7}
            ),
        ]
    )
    parsed = flow_usage.steps_from(journal)
    assert set(parsed.steps) == {
        flow_usage.AgentStep(agent_id="a1", step="development-specs", role=flow_usage.Role.PRODUCE),
        flow_usage.AgentStep(agent_id="a2", step="development-specs", role=flow_usage.Role.AUDIT),
    }
    # Two agents on the same step are two separate entries, not merged into one.
    assert len(parsed.steps) == 2


def test_plain_string_result_yields_no_step_and_is_counted_step_less():
    journal = "\n".join([_started("a1"), _result("a1", "some plain string result")])
    parsed = flow_usage.steps_from(journal)
    assert parsed.steps == ()
    assert parsed.step_less == ("a1",)


def test_dict_result_with_no_step_yields_no_step_and_is_counted_step_less():
    journal = "\n".join([_started("a1"), _result("a1", {"status": "ok", "artifact": "x.md"})])
    parsed = flow_usage.steps_from(journal)
    assert parsed.steps == ()
    assert parsed.step_less == ("a1",)


def test_started_with_no_later_result_or_failed_is_unfinished():
    journal = "\n".join(
        [_started("a1"), _started("a2"), _result("a1", {"step": "s", "status": "ok"})]
    )
    parsed = flow_usage.steps_from(journal)
    assert parsed.unfinished == ("a2",)


def test_failed_record_marks_agent_failed_and_is_not_unfinished():
    journal = "\n".join([_started("a1"), _failed("a1")])
    parsed = flow_usage.steps_from(journal)
    assert parsed.failed == ("a1",)
    assert parsed.unfinished == ()


def test_malformed_line_is_skipped_rather_than_fatal():
    journal = "\n".join([_started("a1"), "{not json", _result("a1", {"step": "s", "status": "ok"})])
    parsed = flow_usage.steps_from(journal)
    assert parsed.steps == (
        flow_usage.AgentStep(agent_id="a1", step="s", role=flow_usage.Role.PRODUCE),
    )


def test_a_step_present_but_neither_produce_nor_audit_shape_is_step_less_not_guessed():
    # Defensive: the plan's own measurement found only these two shapes on the live disk. A
    # third is not attributed a role — it is reported as step-less, the same as no step at all.
    journal = "\n".join([_started("a1"), _result("a1", {"step": "s"})])
    parsed = flow_usage.steps_from(journal)
    assert parsed.steps == ()
    assert parsed.step_less == ("a1",)


def test_empty_journal_yields_nothing_and_does_not_raise():
    parsed = flow_usage.steps_from("")
    assert parsed.steps == ()
    assert parsed.step_less == ()
    assert parsed.unfinished == ()
    assert parsed.failed == ()


# ── Task 3 — the meta sidecar names the agent ──────────────────────────


def _write_meta(run_dir: Path, agent_id: str, text: str) -> None:
    (run_dir / f"agent-{agent_id}.meta.json").write_text(text)


def test_meta_with_no_model_returns_type_and_none_for_model(tmp_path):
    _write_meta(tmp_path, "a1", json.dumps({"agentType": "developer", "spawnDepth": 1}))
    meta = flow_usage.agent_meta(tmp_path, "a1", flow_usage.Files())
    assert meta.agent_type == "developer"
    assert meta.model is None


def test_meta_with_a_model_returns_both(tmp_path):
    _write_meta(
        tmp_path,
        "a1",
        json.dumps({"agentType": "workflow-subagent", "spawnDepth": 1, "model": "haiku"}),
    )
    meta = flow_usage.agent_meta(tmp_path, "a1", flow_usage.Files())
    assert meta.agent_type == "workflow-subagent"
    assert meta.model == "haiku"


def test_missing_sidecar_returns_none_for_both_and_does_not_raise(tmp_path):
    meta = flow_usage.agent_meta(tmp_path, "no-such-agent", flow_usage.Files())
    assert meta.agent_type is None
    assert meta.model is None


def test_malformed_meta_json_is_treated_as_missing_not_a_crash(tmp_path):
    _write_meta(tmp_path, "a1", "{not json")
    meta = flow_usage.agent_meta(tmp_path, "a1", flow_usage.Files())
    assert meta.agent_type is None
    assert meta.model is None


class TestFilesReadText:
    def test_reads_a_real_files_whole_text(self, tmp_path):
        path = tmp_path / "t.json"
        path.write_text('{"a": 1}')
        assert flow_usage.Files().read_text(path) == '{"a": 1}'

    def test_returns_none_for_a_missing_file(self, tmp_path):
        assert flow_usage.Files().read_text(tmp_path / "does-not-exist") is None


# ── Task 4 — an agent's spend uses the sibling's accumulator, not a copy ─────


def _usage_line(
    model="claude-sonnet-5",
    input_tokens=1,
    output_tokens=1,
    cache_read=0,
    cache_write_1h=0,
    cache_write_5m=0,
    thinking=None,
    timestamp="2026-09-07T00:00:00.000Z",
):
    usage = {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cache_read_input_tokens": cache_read,
        "cache_creation_input_tokens": cache_write_1h + cache_write_5m,
        "cache_creation": {
            "ephemeral_1h_input_tokens": cache_write_1h,
            "ephemeral_5m_input_tokens": cache_write_5m,
        },
    }
    if thinking is not None:
        usage["output_tokens_details"] = {"thinking_tokens": thinking}
    return json.dumps(
        {
            "type": "assistant",
            "timestamp": timestamp,
            "message": {"model": model, "usage": usage},
        }
    )


def _write_agent_transcript(run_dir: Path, agent_id: str, lines: list[str]) -> Path:
    path = run_dir / f"agent-{agent_id}.jsonl"
    path.write_text("\n".join(lines) + "\n")
    return path


def test_flow_usage_defines_no_second_five_class_accumulator():
    source = inspect.getsource(flow_usage)
    assert "def spend_by_model" not in source
    assert "def usage_records" not in source


def test_agent_spend_calls_run_usages_own_functions_not_a_copy():
    source = inspect.getsource(flow_usage.agent_spend)
    assert "run_usage.usage_records(" in source
    assert "run_usage.spend_by_model(" in source


def test_a_workflow_agent_transcript_produces_the_same_modelspend_run_usage_would(tmp_path):
    _write_agent_transcript(tmp_path, "a1", [_usage_line(input_tokens=5, output_tokens=7)])
    files = flow_usage.Files()

    flow_spend = flow_usage.agent_spend(tmp_path, "a1", files)

    path = tmp_path / "agent-a1.jsonl"
    sibling_records = run_usage.usage_records(path, files)
    sibling_spend = run_usage.spend_by_model(sibling_records)

    assert flow_spend == sibling_spend
    assert flow_spend["claude-sonnet-5"].input == 5
    assert flow_spend["claude-sonnet-5"].output == 7


def test_a_missing_agent_file_returns_an_empty_spend_not_a_raise(tmp_path):
    spend = flow_usage.agent_spend(tmp_path, "no-such-agent", flow_usage.Files())
    assert spend == {}


def test_agent_spend_does_not_raise_on_a_truncated_final_line(tmp_path):
    _write_agent_transcript(tmp_path, "a1", [_usage_line()])
    path = tmp_path / "agent-a1.jsonl"
    with path.open("a") as f:
        f.write('{"type": "assistant", "message": {"usage"')  # truncated, no trailing newline
    spend = flow_usage.agent_spend(tmp_path, "a1", flow_usage.Files())
    assert spend["claude-sonnet-5"].input == 1


def test_flow_usage_defines_no_spend_accumulator_of_its_own():
    """`_add_spend` and `_merge_spend` moved to `run_usage.py` when a third reader wanted them.
    They must not grow back here: the rule they encode — no class summed with another, and a
    `thinking` of `None` meaning "nothing carried `output_tokens_details`" rather than zero — is
    one rule, and a second copy is a second place for it to drift.

    Checked in the parse tree, not by a text search: this module's own docstring names
    `run_usage.add_spend` / `merge_spend`, so a string search passes on the prose alone and would
    keep passing over a hand-rolled accumulator sitting right beneath it.
    """
    tree = ast.parse(Path(flow_usage.__file__).read_text())
    defined = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    assert not defined & {"_add_spend", "_merge_spend", "add_spend", "merge_spend"}


def test_the_fold_calls_the_siblings_accumulator():
    """And it must actually call it — the guard above only proves nothing was re-declared."""
    tree = ast.parse(Path(flow_usage.__file__).read_text())
    called = {
        ast.unparse(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)
    }
    assert "run_usage.merge_spend" in called


def test_folding_two_agents_matches_the_siblings_own_arithmetic():
    """The behaviour the four moved tests covered, kept here as an end-to-end check that the fold
    this module performs is the sibling's arithmetic and not an accident of ordering."""
    a = {"sonnet": run_usage.ModelSpend(input=1, output=2)}
    b = {"sonnet": run_usage.ModelSpend(input=10, output=20), "haiku": run_usage.ModelSpend(input=5)}
    merged = run_usage.merge_spend(a, b)
    assert merged["sonnet"] == run_usage.ModelSpend(input=11, output=22)
    assert merged["haiku"] == run_usage.ModelSpend(input=5)


# ── Task 5 — a run aggregates per step, and step-less agents fall back by name ──


def _flow_run_fixture(
    tmp_path: Path,
    journal_lines: list[str],
    transcripts: dict[str, list[str]] | None = None,
    metas: dict[str, dict] | None = None,
) -> flow_usage.FlowRun:
    """A full workflow-run tree under `tmp_path`, matching the plan's real shape."""
    run_dir = _make_workflow_run(tmp_path, "slug-a", "sid-1", "wf_test")
    (run_dir / "journal.jsonl").write_text("\n".join(journal_lines))
    for agent_id, lines in (transcripts or {}).items():
        _write_agent_transcript(run_dir, agent_id, lines)
    for agent_id, meta in (metas or {}).items():
        _write_meta(run_dir, agent_id, json.dumps(meta))
    return flow_usage.FlowRun(wf_id="wf_test", session_id="sid-1", slug="slug-a", run_dir=run_dir)


def test_read_run_reads_the_journal_and_every_named_agent(tmp_path):
    flow_run = _flow_run_fixture(
        tmp_path,
        [_started("a1"), _result("a1", {"step": "s", "status": "ok", "artifact": "x.md"})],
        transcripts={"a1": [_usage_line(input_tokens=3)]},
        metas={"a1": {"agentType": "developer"}},
    )
    run = flow_usage.read_run(flow_run, flow_usage.Files())
    assert len(run.agents) == 1
    agent = run.agents[0]
    assert agent.agent_id == "a1"
    assert agent.step == "s"
    assert agent.role == flow_usage.Role.PRODUCE
    assert agent.agent_type == "developer"
    assert agent.spend["claude-sonnet-5"].input == 3


def test_two_agents_same_step_different_role_are_two_rows(tmp_path):
    flow_run = _flow_run_fixture(
        tmp_path,
        [
            _started("a1"),
            _result("a1", {"step": "development-specs", "status": "ok", "artifact": "x.md"}),
            _started("a2"),
            _result("a2", {"step": "development-specs", "result": "findings", "findings": 3}),
        ],
    )
    run = flow_usage.read_run(flow_run, flow_usage.Files())
    rows = flow_usage.aggregate(run)
    assert len(rows) == 2
    labels = {(r.label, r.role) for r in rows}
    assert labels == {
        ("development-specs", flow_usage.Role.PRODUCE),
        ("development-specs", flow_usage.Role.AUDIT),
    }


def test_two_agents_same_step_same_role_merge_into_one_row_with_summed_classes(tmp_path):
    flow_run = _flow_run_fixture(
        tmp_path,
        [
            _started("a1"),
            _result("a1", {"step": "development-specs", "status": "ok", "artifact": "x.md"}),
            _started("a2"),
            _result("a2", {"step": "development-specs", "status": "ok", "artifact": "y.md"}),
        ],
        transcripts={
            "a1": [_usage_line(input_tokens=3)],
            "a2": [_usage_line(input_tokens=4)],
        },
    )
    run = flow_usage.read_run(flow_run, flow_usage.Files())
    rows = flow_usage.aggregate(run)
    assert len(rows) == 1
    row = rows[0]
    assert set(row.agent_ids) == {"a1", "a2"}
    assert row.spend["claude-sonnet-5"].input == 7


def test_agent_with_no_step_falls_back_to_its_agent_type_marked_fallback(tmp_path):
    flow_run = _flow_run_fixture(
        tmp_path,
        [_started("a1"), _result("a1", "plain string, no step")],
        metas={"a1": {"agentType": "workflow-subagent"}},
    )
    run = flow_usage.read_run(flow_run, flow_usage.Files())
    rows = flow_usage.aggregate(run)
    assert len(rows) == 1
    row = rows[0]
    assert row.label == "workflow-subagent"
    assert row.is_fallback is True
    assert row.role is None


def test_no_row_anywhere_carries_the_sum_of_two_classes(tmp_path):
    # Every class gets a distinct value, so any class standing in for a sum of two others
    # would land on a number no class was given. A pairwise-distinct fixture is what makes
    # that detectable at all -- with 0s or repeats a summed column reads as a correct one.
    flow_run = _flow_run_fixture(
        tmp_path,
        [_started("a1"), _result("a1", {"step": "s", "status": "ok", "artifact": "x.md"})],
        transcripts={
            "a1": [
                _usage_line(
                    input_tokens=5,
                    output_tokens=9,
                    cache_read=17,
                    cache_write_1h=33,
                    cache_write_5m=65,
                )
            ]
        },
    )
    run = flow_usage.read_run(flow_run, flow_usage.Files())
    row = flow_usage.aggregate(run)[0]
    spend = row.spend["claude-sonnet-5"]
    assert (
        spend.input,
        spend.output,
        spend.cache_read,
        spend.cache_write_1h,
        spend.cache_write_5m,
    ) == (5, 9, 17, 33, 65)


def test_an_agent_named_in_the_journal_with_no_transcript_is_counted_not_skipped(tmp_path):
    # Task 4: "an agent file that does not exist returns an empty spend and is counted, not
    # skipped silently" -- the row exists with no models under it, and coverage sees the agent.
    flow_run = _flow_run_fixture(
        tmp_path,
        [_started("a1"), _result("a1", {"step": "s", "status": "ok", "artifact": "x.md"})],
    )
    run = flow_usage.read_run(flow_run, flow_usage.Files())
    rows = flow_usage.aggregate(run)
    assert len(rows) == 1
    assert rows[0].agent_ids == ("a1",)
    assert rows[0].spend == {}
    assert flow_usage.coverage(run).with_step == 1


def test_an_agent_whose_sidecar_is_missing_is_still_reported(tmp_path):
    # Task 3: "a missing sidecar returns None for both and does not raise; the agent is still
    # reported" -- it does not vanish from the rows just because nothing named it.
    flow_run = _flow_run_fixture(
        tmp_path,
        [_started("a1"), _result("a1", "plain string, no step")],
        transcripts={"a1": [_usage_line(input_tokens=2)]},
    )
    run = flow_usage.read_run(flow_run, flow_usage.Files())
    assert run.agents[0].agent_type is None
    rows = flow_usage.aggregate(run)
    assert len(rows) == 1
    assert rows[0].agent_ids == ("a1",)
    assert rows[0].spend["claude-sonnet-5"].input == 2


def test_a_run_with_no_agents_returns_no_rows_and_does_not_raise(tmp_path):
    flow_run = _flow_run_fixture(tmp_path, [])
    run = flow_usage.read_run(flow_run, flow_usage.Files())
    assert flow_usage.aggregate(run) == ()


# ── Task 6 — coverage is stated, never implied ─────────────────────────


def test_each_of_the_four_figures_is_independent_an_agent_counts_in_both_2_and_3(tmp_path):
    flow_run = _flow_run_fixture(
        tmp_path,
        [
            _started("a1"),  # never resolves -> without_step AND started_no_result
            _started("a2"),
            _result("a2", {"step": "s", "status": "ok", "artifact": "x.md"}),  # with_step
        ],
    )
    run = flow_usage.read_run(flow_run, flow_usage.Files())
    cov = flow_usage.coverage(run)
    assert cov.with_step == 1
    assert cov.without_step == 1
    assert cov.started_no_result == 1


def test_agent_file_with_no_started_record_at_all_is_counted_in_the_fourth_figure(tmp_path):
    flow_run = _flow_run_fixture(
        tmp_path,
        [_started("a1"), _result("a1", {"step": "s", "status": "ok", "artifact": "x.md"})],
        transcripts={"a1": [], "orphan": []},  # "orphan" has a transcript file, no journal entry
    )
    run = flow_usage.read_run(flow_run, flow_usage.Files())
    cov = flow_usage.coverage(run)
    assert cov.files_with_no_journal_entry == 1


def test_a_fully_clean_run_reports_zeroes_for_the_other_three_figures(tmp_path):
    flow_run = _flow_run_fixture(
        tmp_path,
        [_started("a1"), _result("a1", {"step": "s", "status": "ok", "artifact": "x.md"})],
        transcripts={"a1": []},
    )
    run = flow_usage.read_run(flow_run, flow_usage.Files())
    cov = flow_usage.coverage(run)
    assert cov.with_step == 1
    assert cov.without_step == 0
    assert cov.started_no_result == 0
    assert cov.files_with_no_journal_entry == 0


# ── Task 7 — the report renders, and `--json` carries the same numbers ────


def test_rendered_output_states_the_fallback_rule_and_the_coverage_figures(tmp_path):
    flow_run = _flow_run_fixture(
        tmp_path,
        [_started("a1"), _result("a1", {"step": "s", "status": "ok", "artifact": "x.md"})],
        transcripts={"a1": [_usage_line()]},
    )
    run = flow_usage.read_run(flow_run, flow_usage.Files())
    text = flow_usage.render([run])
    assert "fallback" in text.lower()
    assert "agenttype" in text.lower()
    assert "with a step" in text or "with_step" in text
    assert "no journal entry" in text


def test_no_rendered_column_or_total_row_sums_two_classes(tmp_path):
    flow_run = _flow_run_fixture(
        tmp_path,
        [_started("a1"), _result("a1", {"step": "s", "status": "ok", "artifact": "x.md"})],
        transcripts={"a1": [_usage_line(input_tokens=11, output_tokens=13)]},
    )
    run = flow_usage.read_run(flow_run, flow_usage.Files())
    text = flow_usage.render([run])
    assert "input=11" in text
    assert "output=13" in text
    assert "24" not in text  # 11 + 13, would only appear if a column summed two classes


def test_json_round_trips_and_carries_every_figure_the_table_shows(tmp_path):
    flow_run = _flow_run_fixture(
        tmp_path,
        [_started("a1"), _result("a1", {"step": "s", "status": "ok", "artifact": "x.md"})],
        transcripts={"a1": [_usage_line(input_tokens=5)]},
    )
    run = flow_usage.read_run(flow_run, flow_usage.Files())
    payload = json.loads(flow_usage.render_json([run]))
    assert payload["runs"][0]["wf_id"] == "wf_test"
    assert payload["runs"][0]["coverage"]["with_step"] == 1
    assert payload["runs"][0]["rows"][0]["spend"]["claude-sonnet-5"]["input"] == 5


def test_the_rendered_table_names_the_agent_type_of_a_step_row(tmp_path):
    # Task 7 names the table's columns: "run, step, role, agent type, model, five classes,
    # thinking". The agent type is one of them, and it is a different fact from the step and
    # from the role -- a reader must be able to see which agent ran `development-specs`, not
    # only that something did. The fallback row happens to be *keyed* by the agent type, so a
    # step row is the only place this column can be checked for.
    flow_run = _flow_run_fixture(
        tmp_path,
        [
            _started("a1"),
            _result(
                "a1", {"step": "development-specs", "status": "ok", "artifact": "x.md"}
            ),
        ],
        transcripts={"a1": [_usage_line()]},
        metas={"a1": {"agentType": "product-owner", "model": "claude-opus-5"}},
    )
    run = flow_usage.read_run(flow_run, flow_usage.Files())
    text = flow_usage.render([run])
    step_line = next(
        line for line in text.splitlines() if "development-specs" in line
    )
    assert "product-owner" in step_line


def test_json_carries_the_agent_type_the_table_shows(tmp_path):
    # Task 7: "the `--json` path emits the same figures as data" -- the agent-type column is
    # one of them, so a reader consuming the JSON is not handed less than the table shows.
    flow_run = _flow_run_fixture(
        tmp_path,
        [
            _started("a1"),
            _result(
                "a1", {"step": "development-specs", "status": "ok", "artifact": "x.md"}
            ),
        ],
        transcripts={"a1": [_usage_line()]},
        metas={"a1": {"agentType": "product-owner", "model": "claude-opus-5"}},
    )
    run = flow_usage.read_run(flow_run, flow_usage.Files())
    payload = json.loads(flow_usage.render_json([run]))
    assert payload["runs"][0]["rows"][0]["agent_types"] == ["product-owner"]


def test_thinking_is_rendered_as_a_share_of_output_never_added_to_it(tmp_path):
    # Reached-when 3: "thinking is reported as a share of output, never added to it." The
    # rendered output figure stays exactly what the transcript carried; thinking is reported
    # beside it as its own figure, and 40 + 100 appears nowhere.
    flow_run = _flow_run_fixture(
        tmp_path,
        [_started("a1"), _result("a1", {"step": "s", "status": "ok", "artifact": "x.md"})],
        transcripts={"a1": [_usage_line(input_tokens=7, output_tokens=100, thinking=40)]},
    )
    run = flow_usage.read_run(flow_run, flow_usage.Files())
    text = flow_usage.render([run])
    assert "output=100" in text
    assert "thinking=40" in text
    assert "output=140" not in text
    payload = json.loads(flow_usage.render_json([run]))
    spend = payload["runs"][0]["rows"][0]["spend"]["claude-sonnet-5"]
    assert spend["output"] == 100
    assert spend["thinking"] == 40


def test_a_run_with_no_readable_agents_renders_a_line_saying_so(tmp_path):
    flow_run = _flow_run_fixture(tmp_path, [])
    run = flow_usage.read_run(flow_run, flow_usage.Files())
    text = flow_usage.render([run])
    assert "no agents" in text.lower()


def test_render_with_no_runs_at_all_says_so_rather_than_an_empty_table():
    text = flow_usage.render([])
    assert "no workflow runs" in text.lower()


# ── Task 8 — the CLI ────────────────────────────


class TestCompositionRoot:
    def test_no_module_level_name_holds_the_expanded_projects_root(self):
        default_root = Path.home() / ".claude" / "projects"
        holders = [
            name
            for name, value in vars(flow_usage).items()
            if value == default_root or value == str(default_root)
        ]
        assert holders == []

    def test_build_reader_resolves_the_default_projects_root(self):
        reader = flow_usage.build_reader()
        assert reader.projects_root == Path.home() / ".claude" / "projects"
        assert isinstance(reader.files, flow_usage.Files)

    def test_build_reader_honors_an_explicit_projects_root(self, tmp_path):
        reader = flow_usage.build_reader(tmp_path)
        assert reader.projects_root == tmp_path

    def test_only_build_reader_constructs_a_files(self):
        source = Path(flow_usage.__file__).read_text()
        import ast as _ast

        tree = _ast.parse(source)
        constructing_functions = set()
        for node in _ast.walk(tree):
            if isinstance(node, _ast.FunctionDef):
                for call in _ast.walk(node):
                    if isinstance(call, _ast.Call) and isinstance(call.func, _ast.Name):
                        if call.func.id == "Files":
                            constructing_functions.add(node.name)
        assert constructing_functions == {"build_reader"}

    def test_main_obtains_ports_from_build_reader_and_constructs_none_itself(self):
        source = inspect.getsource(flow_usage.main)
        assert "build_reader(" in source
        assert "Files(" not in source


def test_no_arguments_reads_every_workflow_run_under_the_projects_root(tmp_path, capsys):
    _make_workflow_run(tmp_path, "slug-a", "sid-1", "wf_one")
    _make_workflow_run(tmp_path, "slug-a", "sid-2", "wf_two")
    exit_code = flow_usage.main(["--projects-root", str(tmp_path)])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "wf_one" in out
    assert "wf_two" in out


def test_wf_flag_reads_only_that_run(tmp_path, capsys):
    _make_workflow_run(tmp_path, "slug-a", "sid-1", "wf_one")
    _make_workflow_run(tmp_path, "slug-a", "sid-2", "wf_two")
    exit_code = flow_usage.main(["--projects-root", str(tmp_path), "--wf", "wf_one"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "wf_one" in out
    assert "wf_two" not in out


def test_unknown_wf_id_exits_non_zero_naming_the_id(tmp_path, capsys):
    _make_workflow_run(tmp_path, "slug-a", "sid-1", "wf_one")
    exit_code = flow_usage.main(["--projects-root", str(tmp_path), "--wf", "wf_does_not_exist"])
    assert exit_code != 0
    err = capsys.readouterr().err
    assert "wf_does_not_exist" in err


def test_json_and_table_report_the_same_numbers(tmp_path, capsys):
    run_dir = _make_workflow_run(tmp_path, "slug-a", "sid-1", "wf_one")
    (run_dir / "journal.jsonl").write_text(
        "\n".join(
            [_started("a1"), _result("a1", {"step": "s", "status": "ok", "artifact": "x.md"})]
        )
    )
    _write_agent_transcript(run_dir, "a1", [_usage_line(input_tokens=9)])

    flow_usage.main(["--projects-root", str(tmp_path)])
    table_out = capsys.readouterr().out
    assert "input=9" in table_out

    flow_usage.main(["--projects-root", str(tmp_path), "--json"])
    json_out = capsys.readouterr().out
    payload = json.loads(json_out)
    assert payload["runs"][0]["rows"][0]["spend"]["claude-sonnet-5"]["input"] == 9
