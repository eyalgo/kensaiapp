"""Tests for `chain_usage.py` — what a chain walk spent, per document and per cycle.

Fixtures below are shaped off the live disk, not invented. Every shape was read on 2026-09-09
from this machine's own files, and the reading is named beside the test that depends on it:

- the watcher-log filename shape and its UTC clock — `core/tools/detach_watcher.sh:320`,
  `local log_file="$log_dir/watch-${log_stem}-$(date -u +%Y%m%d-%H%M%S).log"`;
- the `on_complete: ran.` line — `core/tools/watch_agent.py:675`, printed only under the
  `if args.on_complete:` guard at `:814-815`;
- the three run-line forms — read from a walking instance's own `system/logs/`;
- the producer's opening prompt — `skills/cto/.claude/skills/product-srs/launcher.md`'s
  `**Prompt:** invoke the product-srs skill for the {project} project.`;
- the seat name scheme — `core/doctrine/setup/kensaiapp_structure.md`, § *A trail is not the
  document's sibling*,
  `sdd-<project>-run<N>-<cpo|cto|cdo>`.

The project names below (`demo`, `other`) are invented stand-ins. Nothing about a real product
is load-bearing in a test that builds its own tree under `tmp_path`, and `core/` names no
product — `<CORE>/doctrine/setup/shared_core_instance.md` § So a shared file names no product.
"""

from __future__ import annotations

import ast
import inspect
import json
import re
from pathlib import Path

import pytest

import chain
import chain_usage


# ── Task 1 — the population is the watcher logs that carry an `on_complete:` line ──


def _write_log(logs_dir: Path, name: str, body: str) -> Path:
    logs_dir.mkdir(parents=True, exist_ok=True)
    path = logs_dir / name
    path.write_text(body)
    return path


CHAIN_DRIVEN_BODY = "\n".join(
    [
        "watch_agent: watching demo under /instance at 2026-09-09 16:34:08",
        "(run ecef71f7 completed — state: done)",
        "notify: sent.",
        "on_complete: ran.",
        "stop: stopped ecef71f7.",
    ]
)

HAND_LAUNCHED_BODY = "\n".join(
    [
        "watch_agent: watching demo under /instance at 2026-09-09 16:34:08",
        "(run ecef71f7 completed — state: done)",
        "notify: sent.",
        "stop: stopped ecef71f7.",
    ]
)


class TestWatchLogName:
    def test_an_untagged_name_carries_no_tag(self):
        parsed = chain_usage.watch_log_name("watch-demo-20260909-145750.log", "demo")
        assert parsed is not None
        assert parsed.tag is None

    def test_a_tagged_name_carries_the_tag(self):
        parsed = chain_usage.watch_log_name("watch-demo-SRS-20260909-141859.log", "demo")
        assert parsed is not None
        assert parsed.tag == "SRS"

    def test_the_stamp_is_read_as_utc(self):
        # detach_watcher.sh:320 stamps the name with `date -u`, so the filename is UTC and the
        # body's own "at <time>" line is local. Reading it as local time would put every run
        # in the wrong cycle by the machine's offset.
        parsed = chain_usage.watch_log_name("watch-demo-20260909-145750.log", "demo")
        assert parsed is not None
        assert parsed.started_at == 1788965870000  # 2026-09-09T14:57:50Z in epoch ms

    def test_another_projects_log_is_not_matched(self):
        assert chain_usage.watch_log_name("watch-other-20260909-145750.log", "demo") is None

    def test_a_name_with_no_stamp_is_not_matched(self):
        assert chain_usage.watch_log_name("watch-demo.log", "demo") is None

    def test_a_file_that_is_not_a_watcher_log_is_not_matched(self):
        assert chain_usage.watch_log_name("chain-demo-state.json", "demo") is None


class TestChainDriven:
    def test_a_log_carrying_the_on_complete_line_is_chain_driven(self):
        assert chain_usage.chain_driven(CHAIN_DRIVEN_BODY) is True

    def test_a_log_without_it_is_not(self):
        assert chain_usage.chain_driven(HAND_LAUNCHED_BODY) is False


class TestShortIdIn:
    def test_the_completed_form(self):
        assert chain_usage.short_id_in("(run ecef71f7 completed — state: done)") == "ecef71f7"

    def test_the_idle_form(self):
        body = "(run c5cb00ab finished its turn and is idle — status: idle, state: working)"
        assert chain_usage.short_id_in(body) == "c5cb00ab"

    def test_the_done_marker_form(self):
        body = "(run ab135323 declared itself finished at /instance/logs/x.done — status: busy)"
        assert chain_usage.short_id_in(body) == "ab135323"

    def test_a_body_with_no_run_line_yields_none(self):
        assert chain_usage.short_id_in("watch_agent: watching demo\nnotify: sent.\n") is None


class TestSessionIdIn:
    """A `--print` run's watcher (`watch_process.py`) names the run's own session id, which joins
    its transcript directly — such a run is in no `claude agents` listing to join through."""

    def test_the_process_watcher_session_line(self):
        body = (
            "(run process 4242 completed — provider: claude)\n"
            "(run session 0b8f2f6e-5c1a-4a57-9a53-8f9f1f7d2c11)\non_complete: ran.\n"
        )
        assert chain_usage.session_id_in(body) == "0b8f2f6e-5c1a-4a57-9a53-8f9f1f7d2c11"

    def test_a_bg_watcher_body_names_no_session(self):
        assert chain_usage.session_id_in(CHAIN_DRIVEN_BODY) is None


class TestWatchLogs:
    def test_only_chain_driven_logs_are_in_the_population(self, tmp_path):
        _write_log(tmp_path, "watch-demo-20260909-145750.log", CHAIN_DRIVEN_BODY)
        _write_log(tmp_path, "watch-demo-20260909-150000.log", HAND_LAUNCHED_BODY)

        read = chain_usage.watch_logs(tmp_path, "demo", chain_usage.Files())

        assert [log.name for log in read.logs] == ["watch-demo-20260909-145750.log"]
        assert read.not_chain_driven == 1

    def test_a_name_the_reader_cannot_parse_is_named_not_dropped_silently(self, tmp_path):
        _write_log(tmp_path, "watch-demo-20260909-145750.log", CHAIN_DRIVEN_BODY)
        _write_log(tmp_path, "watch-demo-nostamp.log", CHAIN_DRIVEN_BODY)

        read = chain_usage.watch_logs(tmp_path, "demo", chain_usage.Files())

        assert read.unparsed_names == ("watch-demo-nostamp.log",)

    def test_logs_are_sorted_by_their_utc_stamp(self, tmp_path):
        _write_log(tmp_path, "watch-demo-20260909-150000.log", CHAIN_DRIVEN_BODY)
        _write_log(tmp_path, "watch-demo-SRS-20260901-090000.log", CHAIN_DRIVEN_BODY)

        read = chain_usage.watch_logs(tmp_path, "demo", chain_usage.Files())

        assert [log.name for log in read.logs] == [
            "watch-demo-SRS-20260901-090000.log",
            "watch-demo-20260909-150000.log",
        ]

    def test_a_log_carries_its_tag_and_the_short_id_of_the_run_it_watched(self, tmp_path):
        _write_log(tmp_path, "watch-demo-SRS-20260901-090000.log", CHAIN_DRIVEN_BODY)

        read = chain_usage.watch_logs(tmp_path, "demo", chain_usage.Files())

        assert read.logs[0].tag == "SRS"
        assert read.logs[0].short_id == "ecef71f7"

    def test_another_projects_logs_are_never_read(self, tmp_path):
        _write_log(tmp_path, "watch-other-20260909-145750.log", CHAIN_DRIVEN_BODY)

        read = chain_usage.watch_logs(tmp_path, "demo", chain_usage.Files())

        assert read.logs == ()
        assert read.total_seen == 0

    def test_a_nonexistent_logs_dir_reads_nothing_and_does_not_raise(self, tmp_path):
        read = chain_usage.watch_logs(tmp_path / "gone", "demo", chain_usage.Files())
        assert read.logs == ()
        assert read.total_seen == 0


class TestFilesFindWatchLogs:
    def test_finds_a_projects_logs_and_nothing_else(self, tmp_path):
        wanted = _write_log(tmp_path, "watch-demo-20260909-145750.log", "x")
        _write_log(tmp_path, "watch-other-20260909-145750.log", "x")
        (tmp_path / "chain-demo-state.json").write_text("{}")

        assert chain_usage.Files().find_watch_logs(tmp_path, "demo") == [wanted]

    def test_a_nonexistent_dir_yields_no_matches(self, tmp_path):
        assert chain_usage.Files().find_watch_logs(tmp_path / "gone", "demo") == []


def test_the_marker_this_reader_keys_the_population_on_is_the_watchers_own_line():
    # watch_agent.py:675 prints "on_complete: ran." and only under the `if args.on_complete:`
    # guard at :814-815. This reader's marker must stay a prefix of that line, because the
    # whole population rests on it -- a marker that drifts silently reads every chain walk as
    # empty rather than failing.
    watcher = (Path(chain_usage.__file__).parent / "watch_agent.py").read_text()
    assert chain_usage.CHAIN_DRIVEN_MARKER in watcher
    assert 'print("on_complete: ran.", file=sys.stderr, flush=True)' in watcher


def test_the_log_name_shape_this_reader_parses_is_the_one_the_detach_script_writes():
    # detach_watcher.sh:320 is the single writer of these names. The stamp is `date -u`, and
    # this reader reads it as UTC on that basis alone.
    script = (Path(chain_usage.__file__).parent / "detach_watcher.sh").read_text()
    assert 'watch-${log_stem}-$(date -u +%Y%m%d-%H%M%S).log' in script


def test_a_log_body_is_read_as_json_nowhere():
    # A watcher log is prose, not JSONL. This is a guard against a later edit reaching for
    # json.loads on it -- the failure mode would be an empty population that looks like a
    # walk that never ran.
    source = Path(chain_usage.__file__).read_text()
    assert "json.loads(body" not in source


# ── Task 2 — the document a run belongs to comes from chain.py's own registry ──


def _fake_registry():
    """Two specs in the real shape, one of them a launcher two documents share — the ADR /
    NFDR case, which is the only reason a key is not simply a document name."""
    return {
        "SRS": chain.DocumentSpec(
            name="SRS", skill="product-srs", stem="srs", self_answer_arg="SRS"
        ),
        "ADR": chain.DocumentSpec(
            name="ADR", skill="product-architecture", stem="adr",
            self_answer_arg="architecture",
        ),
        "NFDR": chain.DocumentSpec(
            name="NFDR", skill="product-architecture", stem="nfdr",
            self_answer_arg="architecture",
        ),
    }


class TestDocumentKeys:
    def test_a_key_is_minted_per_self_answer_argument_not_per_document(self):
        keys = chain_usage.document_keys(_fake_registry())
        assert [key.key for key in keys] == ["SRS", "architecture"]

    def test_a_key_names_every_document_its_launcher_writes(self):
        keys = chain_usage.document_keys(_fake_registry())
        architecture = next(key for key in keys if key.key == "architecture")
        assert architecture.documents == ("ADR", "NFDR")
        assert architecture.skill == "product-architecture"

    def test_the_real_registry_yields_one_key_per_skill(self):
        # The reader's whole attribution rests on tag <-> skill being a bijection over the
        # registry. If a second skill ever shares a self-answer argument, a tag stops
        # naming one cycle and this test is where that shows up.
        keys = chain_usage.document_keys(chain.DOCUMENT_REGISTRY)
        assert len({key.key for key in keys}) == len(keys)
        assert len({key.skill for key in keys}) == len(keys)

    def test_the_real_registry_carries_the_architecture_pair(self):
        keys = chain_usage.document_keys(chain.DOCUMENT_REGISTRY)
        architecture = next(key for key in keys if key.key == "architecture")
        assert architecture.documents == ("ADR", "NFDR")


class TestKeyForTag:
    def test_a_tag_matches_a_self_answer_argument(self):
        keys = chain_usage.document_keys(chain.DOCUMENT_REGISTRY)
        assert chain_usage.key_for_tag("SRS", keys).key == "SRS"

    def test_the_match_is_case_insensitive(self):
        # The live logs carry `watch-demo-fdr-*` and `watch-demo-SRS-*` on the same
        # day: the doc stem's casing on disk is not uniform.
        keys = chain_usage.document_keys(chain.DOCUMENT_REGISTRY)
        assert chain_usage.key_for_tag("fdr", keys).key == "FDR"

    def test_a_tag_that_names_no_document_yields_none_rather_than_a_guess(self):
        keys = chain_usage.document_keys(chain.DOCUMENT_REGISTRY)
        assert chain_usage.key_for_tag("from-product-docs", keys) is None


class TestKeyForSkill:
    def test_a_skill_matches_its_document(self):
        keys = chain_usage.document_keys(chain.DOCUMENT_REGISTRY)
        assert chain_usage.key_for_skill("product-srs", keys).key == "SRS"

    def test_the_prd_skill_matches_the_prd(self):
        keys = chain_usage.document_keys(chain.DOCUMENT_REGISTRY)
        assert chain_usage.key_for_skill("product-prd", keys).key == "PRD"

    def test_the_architecture_skill_matches_the_pair_key(self):
        keys = chain_usage.document_keys(chain.DOCUMENT_REGISTRY)
        assert chain_usage.key_for_skill("product-architecture", keys).documents == (
            "ADR",
            "NFDR",
        )

    def test_a_skill_no_launcher_names_yields_none(self):
        keys = chain_usage.document_keys(chain.DOCUMENT_REGISTRY)
        assert chain_usage.key_for_skill("seeds-from-product-docs", keys) is None


class TestProducerSkill:
    def test_the_launchers_prompt_literal_names_the_skill(self):
        # skills/cto/.claude/skills/product-srs/launcher.md -- **Prompt:** invoke the product-srs skill for the
        # {project} project.
        text = "invoke the product-srs skill for the demo project."
        assert chain_usage.producer_skill(text) == "product-srs"

    def test_a_prompt_that_continues_past_the_sentence_still_resolves(self):
        # product-sdd/launcher.sh:233 appends four sentences of run instructions after it.
        text = (
            "invoke the product-sdd skill for the demo project. This run holds no seat "
            "(its agent is a tool grant, not a chair): when its Commit step asks for the actor, "
            "pass --role Product to the builder."
        )
        assert chain_usage.producer_skill(text) == "product-sdd"

    def test_a_prompt_naming_no_skill_yields_none(self):
        assert chain_usage.producer_skill("read the SRS and tell me what you think") is None

    def test_no_text_at_all_yields_none(self):
        assert chain_usage.producer_skill(None) is None


class TestFirstUserText:
    def test_the_first_user_record_is_the_one_read(self, tmp_path):
        transcript = tmp_path / "sid.jsonl"
        transcript.write_text(
            "\n".join(
                [
                    json.dumps({"type": "summary", "summary": "not a user record"}),
                    json.dumps(
                        {"type": "user", "message": {"content": "invoke the product-srs skill"}}
                    ),
                    json.dumps({"type": "user", "message": {"content": "a later turn"}}),
                ]
            )
        )
        assert (
            chain_usage.first_user_text(transcript, chain_usage.Files())
            == "invoke the product-srs skill"
        )

    def test_a_block_list_content_is_joined_into_text(self, tmp_path):
        transcript = tmp_path / "sid.jsonl"
        transcript.write_text(
            json.dumps(
                {
                    "type": "user",
                    "message": {
                        "content": [
                            {"type": "text", "text": "invoke the product-uxd skill"},
                            {"type": "text", "text": "for the demo project."},
                        ]
                    },
                }
            )
        )
        text = chain_usage.first_user_text(transcript, chain_usage.Files())
        assert chain_usage.producer_skill(text) == "product-uxd"

    def test_a_malformed_line_is_skipped_rather_than_fatal(self, tmp_path):
        transcript = tmp_path / "sid.jsonl"
        transcript.write_text(
            "\n".join(
                [
                    "{ this is not json",
                    json.dumps({"type": "user", "message": {"content": "invoke the x skill"}}),
                ]
            )
        )
        assert chain_usage.first_user_text(transcript, chain_usage.Files()) == (
            "invoke the x skill"
        )

    def test_a_transcript_that_cannot_be_read_yields_none(self, tmp_path):
        assert chain_usage.first_user_text(tmp_path / "gone.jsonl", chain_usage.Files()) is None

    def test_a_transcript_with_no_user_record_yields_none(self, tmp_path):
        transcript = tmp_path / "sid.jsonl"
        transcript.write_text(json.dumps({"type": "assistant", "message": {"content": "hi"}}))
        assert chain_usage.first_user_text(transcript, chain_usage.Files()) is None


def test_the_registry_is_handed_in_and_never_reached_for_inside_a_unit():
    # `chain.DOCUMENT_REGISTRY` is the single source for what a document is, and this reader
    # imports it rather than restating it -- but a unit that reaches for the module global
    # cannot be given a different registry, which is the defect chain.py's own docstring
    # names under "WHAT IT IS GIVEN, AND WHY THAT IS THE DESIGN".
    #
    # The check is over the parse tree, not the text: the module names the registry in three
    # docstrings, and prose citing the single source is exactly what doctrine asks for. Only a
    # real attribute access inside a function body is a reach.
    tree = ast.parse(Path(chain_usage.__file__).read_text())
    reaching = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        for inner in ast.walk(node):
            if (
                isinstance(inner, ast.Attribute)
                and inner.attr == "DOCUMENT_REGISTRY"
                and isinstance(inner.value, ast.Name)
                and inner.value.id == "chain"
            ):
                reaching.add(node.name)
    assert reaching <= {"main", "build_reader"}


# ── Task 3 — the runs: a log joins to a session, and the seats are their own population ──


def _agents_json(*rows) -> str:
    return json.dumps(list(rows))


def _agent_row(short_id: str, name: str, started_at: int, kind: str = "background") -> dict:
    """One `claude agents --json --all` row in the live shape read on 2026-09-09: an `id`
    that is usually the session id's first eight characters, and three times in 592 rows was
    not — which is why this reader joins on `id` and never on a prefix of `sessionId`."""
    return {
        "id": short_id,
        "cwd": "/instance",
        "kind": kind,
        "startedAt": started_at,
        "sessionId": f"{short_id}-0000-0000-0000-000000000000",
        "name": name,
        "state": "done",
    }


def _usage_line(model="claude-sonnet-5", **usage) -> str:
    payload = {"input_tokens": 1, "output_tokens": 1, "cache_read_input_tokens": 0}
    payload.update(usage)
    return json.dumps(
        {"type": "assistant", "message": {"model": model, "usage": payload},
         "timestamp": "2026-09-09T14:57:50.000Z"}
    )


def _write_transcript(projects_root: Path, slug: str, session_id: str, lines) -> Path:
    (projects_root / slug).mkdir(parents=True, exist_ok=True)
    path = projects_root / slug / f"{session_id}.jsonl"
    path.write_text("\n".join(lines))
    return path


class TestAgentRows:
    def test_a_row_carries_the_short_id_the_watcher_log_names(self):
        rows = chain_usage.agent_rows(_agents_json(_agent_row("ecef71f7", "demo", 1)))
        assert rows[0].id == "ecef71f7"
        assert rows[0].session_id == "ecef71f7-0000-0000-0000-000000000000"

    def test_an_interactive_row_is_kept_because_a_seat_is_joined_by_name(self):
        # run_usage.runs_from drops `kind == "interactive"` on purpose. This reader cannot: it
        # joins by the short id a watcher log names, and dropping a row by kind would turn a
        # joinable run into an unjoinable one for a reason that has nothing to do with the
        # chain.
        rows = chain_usage.agent_rows(
            _agents_json(_agent_row("aaaaaaaa", "owner", 1, kind="interactive"))
        )
        assert len(rows) == 1

    def test_a_row_with_no_session_id_is_dropped_and_counted_nowhere_silently(self):
        rows = chain_usage.agent_rows(json.dumps([{"id": "aaaaaaaa", "name": "x"}]))
        assert rows == ()

    def test_output_that_is_not_json_raises_naming_the_problem(self):
        with pytest.raises(ValueError, match="JSON"):
            chain_usage.agent_rows("not json at all")

    def test_output_that_is_not_an_array_raises(self):
        with pytest.raises(ValueError):
            chain_usage.agent_rows(json.dumps({"id": "aaaaaaaa"}))


class TestSeatRows:
    def test_the_name_scheme_names_the_run_number_and_the_seat(self):
        rows = chain_usage.agent_rows(
            _agents_json(_agent_row("cbd6cde0", "sdd-demo-run17-cpo", 1))
        )
        seats = chain_usage.seat_rows(rows, "demo")
        assert seats[0].seat == "cpo"
        assert seats[0].runner_run == 17

    def test_all_three_seats_are_in_the_population(self):
        rows = chain_usage.agent_rows(
            _agents_json(
                _agent_row("aaaaaaaa", "sdd-demo-run1-cpo", 1),
                _agent_row("bbbbbbbb", "sdd-demo-run1-cto", 2),
                _agent_row("cccccccc", "sdd-demo-run1-cdo", 3),
            )
        )
        assert len(chain_usage.seat_rows(rows, "demo")) == 3

    def test_another_projects_seats_are_never_read(self):
        rows = chain_usage.agent_rows(
            _agents_json(_agent_row("aaaaaaaa", "sdd-other-run1-cpo", 1))
        )
        assert chain_usage.seat_rows(rows, "demo") == ()

    def test_a_run_that_is_not_a_seat_is_never_read(self):
        rows = chain_usage.agent_rows(
            _agents_json(_agent_row("aaaaaaaa", "Launch product PRD for demo", 1))
        )
        assert chain_usage.seat_rows(rows, "demo") == ()

    def test_a_relaunched_seat_under_the_same_name_is_its_own_row(self):
        # Measured 2026-09-09: sdd-demo-run10-cpo appears four times in the agents list,
        # because the runner relaunches a blocked seat under the same name. A reader keyed on
        # the name would collapse four sessions into one and lose three transcripts.
        rows = chain_usage.agent_rows(
            _agents_json(
                _agent_row("aaaaaaaa", "sdd-demo-run10-cpo", 1),
                _agent_row("bbbbbbbb", "sdd-demo-run10-cpo", 2),
            )
        )
        assert len(chain_usage.seat_rows(rows, "demo")) == 2


# ── A run's seats are found by what its record says, not by convention ──
#
# A run record's own head block — "Seats, and the names they answer to", stated in
# `kensaiapp_structure.md`'s trail section — is
# the shape every real record on disk carries; the fixtures below are that shape, never a real
# product's file. The seat line is `  - CTO — `<session-name>`` and the "Standing declared
# move" line beneath it is `- **Standing declared move:** ...` — zero-indent, never mistaken for
# a seat line.


SEAT_BLOCK = "\n".join(
    [
        "- **Round:** 1",
        "- **Seats, and the names they answer to:**",
        "  - CTO — `sdd-demo-run4-cto`",
        "  - CPO — `sdd-demo-run4-cpo`",
        "  - CDO — `sdd-demo-run4-cdo`",
        "- **Standing declared move:** CTO `no_followup` · CPO `no_followup` · CDO `no_followup`",
        "- **Recall outstanding:** none",
    ]
)


class TestRecordSeats:
    def test_the_templates_own_line_shape_yields_the_seat_and_its_name(self):
        seats = chain_usage.record_seats(SEAT_BLOCK)
        assert seats is not None
        cto = next(s for s in seats if s.seat == "cto")
        assert (cto.seat, cto.name, cto.recorded_ids) == ("cto", "sdd-demo-run4-cto", ())

    def test_a_note_wrapped_onto_an_indented_continuation_yields_its_ids_in_order(self):
        block = "\n".join(
            [
                "- **Seats, and the names they answer to:**",
                "  - CTO — `sdd-demo-run10-cto` (Opus 5 since I-3; ids in order: `2750d95c` →",
                "    `0d198084` → `b890b195` → `7e2ac468`)",
                "  - CPO — `sdd-demo-run10-cpo`",
                "  - CDO — `sdd-demo-run10-cdo`",
                "- **Standing declared move:** CPO — `no_followup` · CTO — `no_followup`",
            ]
        )
        seats = chain_usage.record_seats(block)
        assert seats is not None
        cto = next(s for s in seats if s.seat == "cto")
        assert cto.name == "sdd-demo-run10-cto"
        assert cto.recorded_ids == ("2750d95c", "0d198084", "b890b195", "7e2ac468")

    def test_a_single_parenthesized_id_note_yields_that_one_id(self):
        block = "\n".join(
            [
                "- **Seats, and the names they answer to:**",
                "  - CTO — `sdd-demo-run11-cto` (id `61342bd6`)",
                "  - CPO — `sdd-demo-run11-cpo` (id `caff24f5`)",
                "  - CDO — `sdd-demo-run11-cdo` (id `d27de2ee`)",
            ]
        )
        seats = chain_usage.record_seats(block)
        assert seats is not None
        cto = next(s for s in seats if s.seat == "cto")
        assert cto.recorded_ids == ("61342bd6",)

    def test_the_standing_declared_move_line_yields_no_seat(self):
        # It carries a name-shaped token too (`no_followup`), but it is zero-indented, not the
        # two-space seat-line indent, and this reader must never read it as a fourth seat.
        seats = chain_usage.record_seats(SEAT_BLOCK)
        assert seats is not None
        assert {s.seat for s in seats} == {"cto", "cpo", "cdo"}
        assert len(seats) == 3

    def test_a_block_stating_fewer_than_three_seats_yields_nothing(self):
        block = "\n".join(
            [
                "- **Seats, and the names they answer to:**",
                "  - CTO — `sdd-demo-run4-cto`",
                "  - CPO — `sdd-demo-run4-cpo`",
                "- **Standing declared move:** CTO `no_followup` · CPO `no_followup`",
            ]
        )
        assert chain_usage.record_seats(block) is None

    def test_a_text_with_no_seats_header_at_all_yields_nothing(self):
        assert chain_usage.record_seats("nothing here about seats") is None

    def test_a_block_naming_one_seat_twice_does_not_state_three_seats(self):
        # Plan Task 1: "the three (seat, name, recorded ids) it states, or nothing when it does
        # not state three" — three lines that name CTO twice state two seats, not three.
        block = "\n".join(
            [
                "- **Seats, and the names they answer to:**",
                "  - CTO — `sdd-demo-run4-cto`",
                "  - CTO — `sdd-demo-run4-cto-again`",
                "  - CPO — `sdd-demo-run4-cpo`",
            ]
        )
        assert chain_usage.record_seats(block) is None


def _write_run_record(product_path: Path, run: int, body: str = SEAT_BLOCK) -> Path:
    sdd_dir = product_path / "docs" / "trail" / "sdd"
    sdd_dir.mkdir(parents=True, exist_ok=True)
    path = sdd_dir / f"run-{run}.md"
    path.write_text(body)
    return path


class TestProductRunRecords:
    def test_runs_order_numerically_not_lexicographically(self, tmp_path):
        _write_run_record(tmp_path, 9)
        _write_run_record(tmp_path, 10)

        records = chain_usage.product_run_records(tmp_path, chain_usage.Files())

        assert [record.run for record in records] == [9, 10]

    def test_a_records_own_seats_are_parsed(self, tmp_path):
        _write_run_record(tmp_path, 4)

        records = chain_usage.product_run_records(tmp_path, chain_usage.Files())

        assert records[0].seats is not None
        assert len(records[0].seats) == 3

    def test_a_record_that_does_not_parse_carries_no_seats_rather_than_raising(self, tmp_path):
        _write_run_record(tmp_path, 1, body="no seats block here at all")

        records = chain_usage.product_run_records(tmp_path, chain_usage.Files())

        assert records[0].seats is None

    def test_cycle_and_self_answer_files_beside_the_runs_are_never_read_as_one(self, tmp_path):
        _write_run_record(tmp_path, 1)
        sdd_dir = tmp_path / "docs" / "trail" / "sdd"
        (sdd_dir / "cycle-1.md").write_text(SEAT_BLOCK)
        (sdd_dir / "self_answer-1.md").write_text(SEAT_BLOCK)

        records = chain_usage.product_run_records(tmp_path, chain_usage.Files())

        assert [record.run for record in records] == [1]

    def test_a_product_with_no_sdd_trail_yields_no_records_not_an_error(self, tmp_path):
        assert chain_usage.product_run_records(tmp_path, chain_usage.Files()) == ()

    def test_the_engines_own_state_file_beside_a_run_record_is_never_read_as_one(self, tmp_path):
        # The retired engine kept its own state at `run-<N>.state.json`, beside the run's
        # `run-<N>.md` record — a name `run-*.md` was never going to match, and this pins it.
        _write_run_record(tmp_path, 1)
        sdd_dir = tmp_path / "docs" / "trail" / "sdd"
        (sdd_dir / "run-1.state.json").write_text('{"schema_version": 1}')

        records = chain_usage.product_run_records(tmp_path, chain_usage.Files())

        assert [record.run for record in records] == [1]


class TestFilesFindRunRecords:
    def test_finds_a_products_run_records_and_nothing_else(self, tmp_path):
        wanted = _write_run_record(tmp_path, 1)
        sdd_dir = tmp_path / "docs" / "trail" / "sdd"
        (sdd_dir / "cycle-1.md").write_text("x")

        found = chain_usage.Files().find_run_records(tmp_path)

        assert found == [wanted]

    def test_a_nonexistent_sdd_trail_yields_no_matches(self, tmp_path):
        assert chain_usage.Files().find_run_records(tmp_path) == []


class TestSeatRowsFromRecords:
    def test_a_non_default_seat_name_is_found_where_the_pattern_alone_would_miss_it(
        self, tmp_path
    ):
        # The pattern is `sdd-<project>-run<N>-<cpo|cto|cdo>`; a relaunch under a hand-chosen
        # name never matches it, but the record still states it.
        block = "\n".join(
            [
                "- **Seats, and the names they answer to:**",
                "  - CTO — `sdd-demo-run4-cto-relaunched-by-hand`",
                "  - CPO — `sdd-demo-run4-cpo`",
                "  - CDO — `sdd-demo-run4-cdo`",
            ]
        )
        _write_run_record(tmp_path, 4, body=block)
        rows = chain_usage.agent_rows(
            _agents_json(
                _agent_row("aaaaaaaa", "sdd-demo-run4-cto-relaunched-by-hand", 1),
                _agent_row("bbbbbbbb", "sdd-demo-run4-cpo", 2),
                _agent_row("cccccccc", "sdd-demo-run4-cdo", 3),
            )
        )
        records = chain_usage.product_run_records(tmp_path, chain_usage.Files())

        join = chain_usage.seat_rows_from_records(records, rows)

        # The pattern alone never matches the relaunched name — only the record's own text does.
        assert "sdd-demo-run4-cto-relaunched-by-hand" not in {
            s.row.name for s in chain_usage.seat_rows(rows, "demo")
        }
        cto = next(s for s in join.seats if s.seat == "cto")
        assert cto.row.name == "sdd-demo-run4-cto-relaunched-by-hand"
        assert cto.runner_run == 4

    def test_several_rows_under_one_recorded_name_are_several_seat_sessions(self, tmp_path):
        # The runner relaunches a blocked seat under the same name, so one recorded name can
        # join to more than one agent row.
        block = "\n".join(
            [
                "- **Seats, and the names they answer to:**",
                "  - CTO — `sdd-demo-run4-cto`",
                "  - CPO — `sdd-demo-run4-cpo`",
                "  - CDO — `sdd-demo-run4-cdo`",
            ]
        )
        _write_run_record(tmp_path, 4, body=block)
        rows = chain_usage.agent_rows(
            _agents_json(
                _agent_row("aaaaaaaa", "sdd-demo-run4-cto", 1),
                _agent_row("bbbbbbbb", "sdd-demo-run4-cto", 2),
                _agent_row("cccccccc", "sdd-demo-run4-cpo", 3),
                _agent_row("dddddddd", "sdd-demo-run4-cdo", 4),
            )
        )
        records = chain_usage.product_run_records(tmp_path, chain_usage.Files())

        join = chain_usage.seat_rows_from_records(records, rows)

        ctos = [s for s in join.seats if s.seat == "cto"]
        assert len(ctos) == 2
        assert {s.row.id for s in ctos} == {"aaaaaaaa", "bbbbbbbb"}

    def test_a_recorded_name_with_no_agent_row_is_reported_not_dropped(self, tmp_path):
        _write_run_record(tmp_path, 4)  # names sdd-demo-run4-{cto,cpo,cdo}; no rows given
        records = chain_usage.product_run_records(tmp_path, chain_usage.Files())

        join = chain_usage.seat_rows_from_records(records, ())

        assert join.seats == ()
        assert set(join.unmatched) == {
            "sdd-demo-run4-cto",
            "sdd-demo-run4-cpo",
            "sdd-demo-run4-cdo",
        }

    def test_a_run_whose_record_does_not_parse_contributes_no_seats(self, tmp_path):
        _write_run_record(tmp_path, 1, body="no seats block here at all")
        rows = chain_usage.agent_rows(_agents_json(_agent_row("aaaaaaaa", "anything", 1)))
        records = chain_usage.product_run_records(tmp_path, chain_usage.Files())

        join = chain_usage.seat_rows_from_records(records, rows)

        assert join.seats == ()
        assert join.unmatched == ()

    def test_another_products_records_are_never_read(self, tmp_path):
        product_a = tmp_path / "a"
        product_b = tmp_path / "b"
        _write_run_record(product_a, 1)  # sdd-demo-run4-{cto,cpo,cdo}
        block_b = "\n".join(
            [
                "- **Seats, and the names they answer to:**",
                "  - CTO — `sdd-other-run4-cto`",
                "  - CPO — `sdd-other-run4-cpo`",
                "  - CDO — `sdd-other-run4-cdo`",
            ]
        )
        _write_run_record(product_b, 1, body=block_b)
        rows = chain_usage.agent_rows(
            _agents_json(
                _agent_row("aaaaaaaa", "sdd-demo-run4-cto", 1),
                _agent_row("bbbbbbbb", "sdd-other-run4-cto", 2),
            )
        )
        records = chain_usage.product_run_records(product_a, chain_usage.Files())

        join = chain_usage.seat_rows_from_records(records, rows)

        assert {s.row.name for s in join.seats} == {"sdd-demo-run4-cto"}


class TestReadSeats:
    def test_with_no_product_path_the_population_equals_todays_pattern_row_for_row(self):
        rows = chain_usage.agent_rows(
            _agents_json(
                _agent_row("aaaaaaaa", "sdd-demo-run1-cpo", 1),
                _agent_row("bbbbbbbb", "sdd-demo-run1-cto", 2),
                _agent_row("cccccccc", "sdd-demo-run1-cdo", 3),
            )
        )
        reading = chain_usage.read_seats(None, "demo", rows, chain_usage.Files())
        assert reading.seats == chain_usage.seat_rows(rows, "demo")

    def test_with_no_product_path_every_run_is_named_read_by_convention(self):
        rows = chain_usage.agent_rows(
            _agents_json(_agent_row("aaaaaaaa", "sdd-demo-run1-cpo", 1))
        )
        reading = chain_usage.read_seats(None, "demo", rows, chain_usage.Files())
        assert reading.evidence == {1: chain_usage.SeatEvidence.CONVENTION}

    def test_a_record_that_does_not_parse_falls_back_to_the_pattern_named_convention(
        self, tmp_path
    ):
        _write_run_record(tmp_path, 1, body="no seats block here at all")
        rows = chain_usage.agent_rows(
            _agents_json(
                _agent_row("aaaaaaaa", "sdd-demo-run1-cpo", 1),
                _agent_row("bbbbbbbb", "sdd-demo-run1-cto", 2),
                _agent_row("cccccccc", "sdd-demo-run1-cdo", 3),
            )
        )
        reading = chain_usage.read_seats(tmp_path, "demo", rows, chain_usage.Files())
        assert len(reading.seats) == 3
        assert reading.evidence[1] is chain_usage.SeatEvidence.CONVENTION

    def test_a_record_that_parses_is_never_consulted_via_the_pattern(self, tmp_path):
        block = "\n".join(
            [
                "- **Seats, and the names they answer to:**",
                "  - CTO — `sdd-demo-run5-cto-custom`",
                "  - CPO — `sdd-demo-run5-cpo`",
                "  - CDO — `sdd-demo-run5-cdo`",
            ]
        )
        _write_run_record(tmp_path, 5, body=block)
        rows = chain_usage.agent_rows(
            _agents_json(
                _agent_row("aaaaaaaa", "sdd-demo-run5-cto-custom", 1),
                _agent_row("bbbbbbbb", "sdd-demo-run5-cpo", 2),
                _agent_row("cccccccc", "sdd-demo-run5-cdo", 3),
                # A decoy the pattern would match for this exact run, which the record never
                # named — proof the pattern is not consulted once the record parses.
                _agent_row("dddddddd", "sdd-demo-run5-cto", 4),
            )
        )
        reading = chain_usage.read_seats(tmp_path, "demo", rows, chain_usage.Files())

        assert len(reading.seats) == 3
        assert "dddddddd" not in {s.row.id for s in reading.seats}
        assert reading.evidence[5] is chain_usage.SeatEvidence.RECORD

    def test_a_recorded_name_with_no_row_is_carried_as_unmatched(self, tmp_path):
        _write_run_record(tmp_path, 4)  # names sdd-demo-run4-{cto,cpo,cdo}; no rows given
        reading = chain_usage.read_seats(tmp_path, "demo", (), chain_usage.Files())
        assert set(reading.unmatched_recorded_names) == {
            "sdd-demo-run4-cto",
            "sdd-demo-run4-cpo",
            "sdd-demo-run4-cdo",
        }


class TestReadSeatsMissingRecord:
    def test_a_run_with_no_record_file_falls_back_while_a_parsed_run_stays_record_read(
        self, tmp_path
    ):
        # Plan Task 4: "A run whose record cannot be read ... has its seats read by today's name
        # pattern, and the reading says which runs came from which source." Run 2 has seats on
        # the agents list and no run-2.md at all; run 1's record parses.
        block = "\n".join(
            [
                "- **Seats, and the names they answer to:**",
                "  - CTO — `sdd-demo-run1-cto`",
                "  - CPO — `sdd-demo-run1-cpo`",
                "  - CDO — `sdd-demo-run1-cdo`",
            ]
        )
        _write_run_record(tmp_path, 1, body=block)
        rows = chain_usage.agent_rows(
            _agents_json(
                _agent_row("aaaaaaaa", "sdd-demo-run1-cto", 1),
                _agent_row("bbbbbbbb", "sdd-demo-run1-cpo", 2),
                _agent_row("cccccccc", "sdd-demo-run1-cdo", 3),
                _agent_row("dddddddd", "sdd-demo-run2-cto", 4),
                _agent_row("eeeeeeee", "sdd-demo-run2-cpo", 5),
            )
        )
        reading = chain_usage.read_seats(tmp_path, "demo", rows, chain_usage.Files())

        assert {s.row.id for s in reading.seats} == {
            "aaaaaaaa", "bbbbbbbb", "cccccccc", "dddddddd", "eeeeeeee",
        }
        assert reading.evidence == {
            1: chain_usage.SeatEvidence.RECORD,
            2: chain_usage.SeatEvidence.CONVENTION,
        }


class TestRunsFromSeatsEvidence:
    def test_a_seat_carries_the_evidence_its_run_number_was_given(self, tmp_path):
        row = _agent_row("cbd6cde0", "sdd-demo-run17-cpo", 1)
        rows = chain_usage.agent_rows(_agents_json(row))
        seats = chain_usage.seat_rows(rows, "demo")

        runs = chain_usage.runs_from_seats(
            seats,
            tmp_path,
            chain_usage.Files(),
            chain_usage.document_keys(chain.DOCUMENT_REGISTRY),
            evidence={17: chain_usage.SeatEvidence.RECORD},
        )

        assert runs[0].seat_evidence is chain_usage.SeatEvidence.RECORD

    def test_with_no_evidence_given_every_seat_is_convention(self, tmp_path):
        row = _agent_row("cbd6cde0", "sdd-demo-run17-cpo", 1)
        rows = chain_usage.agent_rows(_agents_json(row))
        seats = chain_usage.seat_rows(rows, "demo")

        runs = chain_usage.runs_from_seats(
            seats, tmp_path, chain_usage.Files(),
            chain_usage.document_keys(chain.DOCUMENT_REGISTRY),
        )

        assert runs[0].seat_evidence is chain_usage.SeatEvidence.CONVENTION

    def test_a_run_number_the_evidence_map_does_not_name_defaults_to_convention(self, tmp_path):
        row = _agent_row("cbd6cde0", "sdd-demo-run17-cpo", 1)
        rows = chain_usage.agent_rows(_agents_json(row))
        seats = chain_usage.seat_rows(rows, "demo")

        runs = chain_usage.runs_from_seats(
            seats, tmp_path, chain_usage.Files(),
            chain_usage.document_keys(chain.DOCUMENT_REGISTRY),
            evidence={},
        )

        assert runs[0].seat_evidence is chain_usage.SeatEvidence.CONVENTION


class TestRunsFromLogs:
    def test_an_untagged_log_is_a_producer_and_its_document_comes_from_the_prompt(
        self, tmp_path
    ):
        projects_root = tmp_path / "projects"
        row = _agent_row("ecef71f7", "demo", 1)
        _write_transcript(
            projects_root,
            "slug",
            row["sessionId"],
            [
                json.dumps(
                    {
                        "type": "user",
                        "message": {
                            "content": "invoke the product-srs skill for the demo project."
                        },
                    }
                ),
                _usage_line(input_tokens=11),
            ],
        )
        log = chain_usage.WatchLog(
            name="watch-demo-20260909-145750.log",
            tag=None,
            started_at=1788965870000,
            short_id="ecef71f7",
        )

        runs = chain_usage.runs_from_logs(
            (log,),
            chain_usage.agent_rows(_agents_json(row)),
            projects_root,
            chain_usage.Files(),
            chain_usage.document_keys(chain.DOCUMENT_REGISTRY),
        )

        assert runs[0].kind is chain_usage.Kind.PRODUCER
        assert runs[0].document_key == "SRS"
        assert runs[0].transcript is chain_usage.Transcript.READ
        assert chain_usage.run_spend(runs[0])["claude-sonnet-5"].input == 11

    def test_a_log_naming_its_session_joins_the_transcript_with_no_agent_row(self, tmp_path):
        projects_root = tmp_path / "projects"
        session_id = "0b8f2f6e-5c1a-4a57-9a53-8f9f1f7d2c11"
        _write_transcript(projects_root, "slug", session_id, [_usage_line(output_tokens=9)])
        _write_log(
            tmp_path,
            "watch-demo-SRS-20260925-090000.log",
            f"(run process 4242 completed — provider: claude)\n(run session {session_id})\n"
            "on_complete: ran.\n",
        )
        logs = chain_usage.watch_logs(tmp_path, "demo", chain_usage.Files()).logs

        runs = chain_usage.runs_from_logs(
            logs,
            (),
            projects_root,
            chain_usage.Files(),
            chain_usage.document_keys(chain.DOCUMENT_REGISTRY),
        )

        assert runs[0].session_id == session_id
        assert runs[0].transcript is chain_usage.Transcript.READ
        assert chain_usage.run_spend(runs[0])["claude-sonnet-5"].output == 9

    def test_a_tagged_log_is_a_self_answer_and_needs_no_transcript_for_its_document(
        self, tmp_path
    ):
        projects_root = tmp_path / "projects"
        row = _agent_row("c5cb00ab", "demo-SRS", 1)
        _write_transcript(projects_root, "slug", row["sessionId"], [_usage_line(output_tokens=7)])
        log = chain_usage.WatchLog(
            name="watch-demo-SRS-20260909-141859.log",
            tag="SRS",
            started_at=1788965870000,
            short_id="c5cb00ab",
        )

        runs = chain_usage.runs_from_logs(
            (log,),
            chain_usage.agent_rows(_agents_json(row)),
            projects_root,
            chain_usage.Files(),
            chain_usage.document_keys(chain.DOCUMENT_REGISTRY),
        )

        assert runs[0].kind is chain_usage.Kind.SELF_ANSWER
        assert runs[0].document_key == "SRS"
        assert chain_usage.run_spend(runs[0])["claude-sonnet-5"].output == 7

    def test_a_log_whose_short_id_is_in_no_agent_row_is_reported_not_dropped(self, tmp_path):
        log = chain_usage.WatchLog(
            name="watch-demo-20260909-145750.log",
            tag=None,
            started_at=1788965870000,
            short_id="deadbeef",
        )

        runs = chain_usage.runs_from_logs(
            (log,),
            (),
            tmp_path,
            chain_usage.Files(),
            chain_usage.document_keys(chain.DOCUMENT_REGISTRY),
        )

        assert len(runs) == 1
        assert runs[0].transcript is chain_usage.Transcript.NO_SESSION
        assert runs[0].session_id is None
        assert chain_usage.run_spend(runs[0]) == {}

    def test_a_run_whose_transcript_is_gone_is_reported_not_dropped(self, tmp_path):
        row = _agent_row("ecef71f7", "demo", 1)
        log = chain_usage.WatchLog(
            name="watch-demo-20260909-145750.log",
            tag=None,
            started_at=1788965870000,
            short_id="ecef71f7",
        )

        runs = chain_usage.runs_from_logs(
            (log,),
            chain_usage.agent_rows(_agents_json(row)),
            tmp_path / "empty",
            chain_usage.Files(),
            chain_usage.document_keys(chain.DOCUMENT_REGISTRY),
        )

        assert runs[0].transcript is chain_usage.Transcript.MISSING
        assert runs[0].document_key is None

    def test_a_tag_that_names_no_document_leaves_the_run_unattributed(self, tmp_path):
        row = _agent_row("aaaaaaaa", "demo-x", 1)
        log = chain_usage.WatchLog(
            name="watch-demo-from-product-docs-20260909-145750.log",
            tag="from-product-docs",
            started_at=1788965870000,
            short_id="aaaaaaaa",
        )

        runs = chain_usage.runs_from_logs(
            (log,),
            chain_usage.agent_rows(_agents_json(row)),
            tmp_path,
            chain_usage.Files(),
            chain_usage.document_keys(chain.DOCUMENT_REGISTRY),
        )

        assert runs[0].document_key is None
        assert runs[0].kind is chain_usage.Kind.SELF_ANSWER

    def test_a_runs_started_at_is_the_logs_utc_stamp_not_the_agent_rows_clock(self, tmp_path):
        # The two populations have to share one clock or the cycle boundaries are nonsense.
        # The log's filename is UTC by detach_watcher.sh:320 and the agents list's startedAt is
        # epoch ms, so both are already UTC -- but the log's stamp is the watcher's own
        # detachment, which is the launch this reader orders by.
        row = _agent_row("ecef71f7", "demo", 999)
        log = chain_usage.WatchLog(
            name="watch-demo-20260909-145750.log",
            tag=None,
            started_at=1788965870000,
            short_id="ecef71f7",
        )
        runs = chain_usage.runs_from_logs(
            (log,),
            chain_usage.agent_rows(_agents_json(row)),
            tmp_path,
            chain_usage.Files(),
            chain_usage.document_keys(chain.DOCUMENT_REGISTRY),
        )
        assert runs[0].started_at == 1788965870000


class TestRunsFromSeats:
    def test_a_seat_is_attributed_to_the_document_its_runner_writes(self, tmp_path):
        projects_root = tmp_path / "projects"
        row = _agent_row("cbd6cde0", "sdd-demo-run17-cpo", 1788965870000)
        _write_transcript(projects_root, "slug", row["sessionId"], [_usage_line(output_tokens=5)])
        rows = chain_usage.agent_rows(_agents_json(row))

        runs = chain_usage.runs_from_seats(
            chain_usage.seat_rows(rows, "demo"),
            projects_root,
            chain_usage.Files(),
            chain_usage.document_keys(chain.DOCUMENT_REGISTRY),
        )

        assert runs[0].kind is chain_usage.Kind.SEAT
        assert runs[0].source is chain_usage.Source.SEAT_SESSION
        assert runs[0].document_key == "SDD"
        assert runs[0].seat == "cpo"
        assert chain_usage.run_spend(runs[0])["claude-sonnet-5"].output == 5

    def test_a_seat_takes_its_start_from_the_agents_list(self, tmp_path):
        row = _agent_row("cbd6cde0", "sdd-demo-run17-cpo", 1788965870000)
        rows = chain_usage.agent_rows(_agents_json(row))
        runs = chain_usage.runs_from_seats(
            chain_usage.seat_rows(rows, "demo"),
            tmp_path,
            chain_usage.Files(),
            chain_usage.document_keys(chain.DOCUMENT_REGISTRY),
        )
        assert runs[0].started_at == 1788965870000

    def test_a_seat_whose_transcript_was_pruned_is_reported_not_dropped(self, tmp_path):
        # Six seat transcripts from the demo walk were already gone on 2026-09-09.
        row = _agent_row("cbd6cde0", "sdd-demo-run1-cpo", 1)
        rows = chain_usage.agent_rows(_agents_json(row))
        runs = chain_usage.runs_from_seats(
            chain_usage.seat_rows(rows, "demo"),
            tmp_path / "empty",
            chain_usage.Files(),
            chain_usage.document_keys(chain.DOCUMENT_REGISTRY),
        )
        assert len(runs) == 1
        assert runs[0].transcript is chain_usage.Transcript.MISSING


class TestRunSpan:
    def test_the_span_is_the_transcripts_own_first_to_last(self, tmp_path):
        projects_root = tmp_path / "projects"
        row = _agent_row("ecef71f7", "demo-SRS", 1)
        _write_transcript(
            projects_root,
            "slug",
            row["sessionId"],
            [
                json.dumps(
                    {
                        "type": "assistant",
                        "message": {"model": "m", "usage": {"input_tokens": 1}},
                        "timestamp": "2026-09-09T14:00:00.000Z",
                    }
                ),
                json.dumps(
                    {
                        "type": "assistant",
                        "message": {"model": "m", "usage": {"input_tokens": 1}},
                        "timestamp": "2026-09-09T14:10:00.000Z",
                    }
                ),
            ],
        )
        log = chain_usage.WatchLog(
            name="watch-demo-SRS-20260909-141859.log",
            tag="SRS",
            started_at=1,
            short_id="ecef71f7",
        )
        runs = chain_usage.runs_from_logs(
            (log,),
            chain_usage.agent_rows(_agents_json(row)),
            projects_root,
            chain_usage.Files(),
            chain_usage.document_keys(chain.DOCUMENT_REGISTRY),
        )
        assert chain_usage.run_span(runs[0]) == 600.0

    def test_a_run_with_no_records_has_no_span_rather_than_zero(self, tmp_path):
        log = chain_usage.WatchLog(
            name="watch-demo-20260909-145750.log", tag=None, started_at=1, short_id=None
        )
        runs = chain_usage.runs_from_logs(
            (log,), (), tmp_path, chain_usage.Files(),
            chain_usage.document_keys(chain.DOCUMENT_REGISTRY),
        )
        assert chain_usage.run_span(runs[0]) is None


def test_the_seat_name_scheme_is_the_one_the_structure_map_states():
    # core/doctrine/setup/kensaiapp_structure.md, the paragraph "The archived run record is a
    # frozen format" -- "`sdd-<project>-run<N>-<cpo|cto|cdo>`" and the seat block header. It is
    # a default the retired runner minted, not a fact the harness enforces, which is why this
    # reader calls the seat population a convention and the on_complete: line a measurement.
    structure = (
        Path(chain_usage.__file__).parent.parent.parent
        / "core/doctrine/setup/kensaiapp_structure.md"
    ).read_text()
    assert "`sdd-<project>-run<N>-<cpo|cto|cdo>`" in structure
    assert chain_usage._SEATS_HEADER in structure


def test_the_spend_accumulator_is_the_siblings_and_never_a_second_one():
    # run_usage.spend_by_model owns the five-class split and the thinking-is-a-share rule.
    # A second accumulator here would be a second place for them to drift.
    #
    # Checked as a call in the parse tree rather than a string in the file: this module's own
    # docstring names run_usage.spend_by_model, so a text search passes on the prose alone and
    # would keep passing over a hand-rolled accumulator sitting right beneath it.
    source = Path(chain_usage.__file__).read_text()
    called = {
        ast.unparse(node.func)
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Call)
    }
    assert "run_usage.spend_by_model" in called
    assert "run_usage.usage_records" in called
    assert "cache_read_input_tokens" not in source
    assert "ephemeral_1h_input_tokens" not in source


# ── Task 4 — the cycles, the aggregation, and the coverage this reading states ──


def _run(
    key,
    kind,
    started_at,
    label="l",
    source=chain_usage.Source.WATCH_LOG,
    transcript=chain_usage.Transcript.READ,
    records=(),
    seat_evidence=None,
):
    return chain_usage.ChainRun(
        label=label,
        source=source,
        kind=kind,
        document_key=key,
        session_id="sid",
        started_at=started_at,
        transcript=transcript,
        records=records,
        seat_evidence=seat_evidence,
    )


def _usage(model="m", **kw):
    payload = {"input_tokens": 0, "output_tokens": 0, "cache_read_input_tokens": 0}
    payload.update(kw)
    return (payload, model, "2026-09-09T14:00:00.000Z")


class TestWithCycles:
    def test_a_cycle_opens_at_a_producer_run(self):
        runs = chain_usage.with_cycles(
            (
                _run("SRS", chain_usage.Kind.PRODUCER, 100),
                _run("SRS", chain_usage.Kind.SELF_ANSWER, 200),
                _run("SRS", chain_usage.Kind.PRODUCER, 300),
            )
        )
        assert [run.cycle for run in runs] == [1, 1, 2]

    def test_a_run_before_the_first_producer_is_cycle_zero(self):
        # The live demo walk opens on a self-answer: the chain finds the document already
        # on disk with a companion beside it, answers that companion, and only then re-runs
        # the producer. That leading run is the tail of a cycle whose producer ran before this
        # reading, and calling it cycle 1 would claim a production this reading never saw.
        runs = chain_usage.with_cycles(
            (
                _run("FDR", chain_usage.Kind.SELF_ANSWER, 100),
                _run("FDR", chain_usage.Kind.PRODUCER, 200),
            )
        )
        assert [run.cycle for run in runs] == [0, 1]

    def test_cycles_are_counted_per_document_not_across_the_walk(self):
        runs = chain_usage.with_cycles(
            (
                _run("SRS", chain_usage.Kind.PRODUCER, 100),
                _run("UXD", chain_usage.Kind.PRODUCER, 200),
                _run("SRS", chain_usage.Kind.PRODUCER, 300),
            )
        )
        by_key = {(run.document_key, run.started_at): run.cycle for run in runs}
        assert by_key == {("SRS", 100): 1, ("UXD", 200): 1, ("SRS", 300): 2}

    def test_a_seat_lands_in_the_cycle_its_runner_opened(self):
        # The runner starts its seats a minute or two after it starts, so a seat always falls
        # inside the producer cycle that launched it -- which is the whole reason the cycle
        # rule is producer-opens rather than producer-closes.
        runs = chain_usage.with_cycles(
            (
                _run("SDD", chain_usage.Kind.PRODUCER, 100),
                _run("SDD", chain_usage.Kind.SEAT, 220, source=chain_usage.Source.SEAT_SESSION),
                _run("SDD", chain_usage.Kind.PRODUCER, 400),
                _run("SDD", chain_usage.Kind.SEAT, 520, source=chain_usage.Source.SEAT_SESSION),
            )
        )
        assert [run.cycle for run in runs] == [1, 1, 2, 2]

    def test_runs_out_of_order_are_ordered_before_cycles_are_cut(self):
        runs = chain_usage.with_cycles(
            (
                _run("SRS", chain_usage.Kind.PRODUCER, 300),
                _run("SRS", chain_usage.Kind.PRODUCER, 100),
            )
        )
        assert {(run.started_at, run.cycle) for run in runs} == {(100, 1), (300, 2)}

    def test_an_unattributed_run_gets_no_cycle_rather_than_a_shared_one(self):
        runs = chain_usage.with_cycles(
            (
                _run(None, chain_usage.Kind.PRODUCER, 100),
                _run(None, chain_usage.Kind.SELF_ANSWER, 200),
            )
        )
        assert [run.cycle for run in runs] == [None, None]

    def test_a_run_with_no_start_time_is_left_unplaced(self):
        runs = chain_usage.with_cycles(
            (
                _run("SRS", chain_usage.Kind.PRODUCER, 100),
                _run("SRS", chain_usage.Kind.SEAT, None, source=chain_usage.Source.SEAT_SESSION),
            )
        )
        unplaced = [run for run in runs if run.cycle is None]
        assert [run.kind for run in unplaced] == [chain_usage.Kind.SEAT]


class TestWithin:
    def test_a_run_before_the_window_is_out(self):
        runs = (_run("SRS", chain_usage.Kind.PRODUCER, 100),)
        assert chain_usage.within(runs, since=200, until=None) == ()

    def test_a_run_after_the_window_is_out(self):
        runs = (_run("SRS", chain_usage.Kind.PRODUCER, 300),)
        assert chain_usage.within(runs, since=None, until=200) == ()

    def test_a_run_inside_both_bounds_is_in(self):
        runs = (_run("SRS", chain_usage.Kind.PRODUCER, 250),)
        assert len(chain_usage.within(runs, since=200, until=300)) == 1

    def test_a_run_with_no_start_time_is_never_windowed_out(self):
        # It has no position to judge against the window, and dropping it would be an
        # undercount this reader could not name afterwards.
        runs = (_run("SRS", chain_usage.Kind.PRODUCER, None),)
        assert len(chain_usage.within(runs, since=200, until=300)) == 1

    def test_no_bounds_keeps_everything(self):
        runs = (_run("SRS", chain_usage.Kind.PRODUCER, 1), _run("SRS", chain_usage.Kind.SEAT, 2))
        assert len(chain_usage.within(runs, since=None, until=None)) == 2


class TestParseDay:
    def test_a_date_becomes_midnight_utc(self):
        assert chain_usage.parse_day("2026-09-09") == 1788912000000

    def test_a_bad_date_raises_naming_the_value(self):
        with pytest.raises(ValueError, match="2026-13-45"):
            chain_usage.parse_day("2026-13-45")


class TestByDocument:
    def test_a_documents_spend_is_the_siblings_accumulator_over_every_record_it_holds(self):
        runs = chain_usage.with_cycles(
            (
                _run("SRS", chain_usage.Kind.PRODUCER, 100, records=(_usage(output_tokens=3),)),
                _run("SRS", chain_usage.Kind.SELF_ANSWER, 200,
                     records=(_usage(output_tokens=4),)),
            )
        )
        rows = chain_usage.by_document(runs, chain_usage.document_keys(chain.DOCUMENT_REGISTRY))
        assert rows[0].spend["m"].output == 7

    def test_a_row_counts_the_cycles_and_each_kind_of_run(self):
        runs = chain_usage.with_cycles(
            (
                _run("SDD", chain_usage.Kind.SELF_ANSWER, 50),
                _run("SDD", chain_usage.Kind.PRODUCER, 100),
                _run("SDD", chain_usage.Kind.SEAT, 150, source=chain_usage.Source.SEAT_SESSION),
                _run("SDD", chain_usage.Kind.PRODUCER, 200),
            )
        )
        row = chain_usage.by_document(
            runs, chain_usage.document_keys(chain.DOCUMENT_REGISTRY)
        )[0]
        assert (row.cycles, row.producers, row.self_answers, row.seats) == (2, 2, 1, 1)

    def test_a_row_names_every_document_the_key_covers(self):
        runs = chain_usage.with_cycles((_run("architecture", chain_usage.Kind.PRODUCER, 1),))
        row = chain_usage.by_document(
            runs, chain_usage.document_keys(chain.DOCUMENT_REGISTRY)
        )[0]
        assert row.documents == ("ADR", "NFDR")

    def test_rows_follow_the_registrys_own_order(self):
        runs = chain_usage.with_cycles(
            (
                _run("SDD", chain_usage.Kind.PRODUCER, 100),
                _run("PRD", chain_usage.Kind.PRODUCER, 200),
                _run("SRS", chain_usage.Kind.PRODUCER, 300),
            )
        )
        rows = chain_usage.by_document(runs, chain_usage.document_keys(chain.DOCUMENT_REGISTRY))
        assert [row.key for row in rows] == ["PRD", "SRS", "SDD"]

    def test_the_unattributed_runs_get_their_own_row_last(self):
        runs = chain_usage.with_cycles(
            (
                _run("SRS", chain_usage.Kind.PRODUCER, 100, records=(_usage(output_tokens=1),)),
                _run(None, chain_usage.Kind.SELF_ANSWER, 200,
                     records=(_usage(output_tokens=9),)),
            )
        )
        rows = chain_usage.by_document(runs, chain_usage.document_keys(chain.DOCUMENT_REGISTRY))
        assert rows[-1].key is None
        assert rows[-1].spend["m"].output == 9

    def test_a_document_with_no_runs_gets_no_row(self):
        rows = chain_usage.by_document(
            (), chain_usage.document_keys(chain.DOCUMENT_REGISTRY)
        )
        assert rows == ()


class TestByCycle:
    def test_one_row_per_document_and_cycle(self):
        runs = chain_usage.with_cycles(
            (
                _run("SRS", chain_usage.Kind.PRODUCER, 100, records=(_usage(output_tokens=1),)),
                _run("SRS", chain_usage.Kind.SELF_ANSWER, 150,
                     records=(_usage(output_tokens=2),)),
                _run("SRS", chain_usage.Kind.PRODUCER, 200, records=(_usage(output_tokens=4),)),
            )
        )
        rows = chain_usage.by_cycle(runs, chain_usage.document_keys(chain.DOCUMENT_REGISTRY))
        assert [(row.key, row.cycle, row.spend["m"].output) for row in rows] == [
            ("SRS", 1, 3),
            ("SRS", 2, 4),
        ]

    def test_cycle_zero_is_its_own_row_never_folded_into_cycle_one(self):
        runs = chain_usage.with_cycles(
            (
                _run("FDR", chain_usage.Kind.SELF_ANSWER, 100),
                _run("FDR", chain_usage.Kind.PRODUCER, 200),
            )
        )
        rows = chain_usage.by_cycle(runs, chain_usage.document_keys(chain.DOCUMENT_REGISTRY))
        assert [row.cycle for row in rows] == [0, 1]


class TestCoverage:
    def test_the_three_transcript_states_are_counted_apart(self):
        runs = (
            _run("SRS", chain_usage.Kind.PRODUCER, 1),
            _run("SRS", chain_usage.Kind.PRODUCER, 2,
                 transcript=chain_usage.Transcript.MISSING),
            _run("SRS", chain_usage.Kind.PRODUCER, 3,
                 transcript=chain_usage.Transcript.NO_SESSION),
        )
        cov = chain_usage.coverage(runs, chain_usage.WatchLogs((), 0, (), 0))
        assert (cov.transcripts_read, cov.transcripts_missing, cov.no_session) == (1, 1, 1)

    def test_an_unattributed_run_is_named_not_only_counted(self):
        runs = (_run(None, chain_usage.Kind.SELF_ANSWER, 1, label="watch-x.log"),)
        cov = chain_usage.coverage(runs, chain_usage.WatchLogs((), 0, (), 0))
        assert cov.unattributed == ("watch-x.log",)

    def test_the_excluded_logs_are_carried_through_from_the_population(self):
        logs = chain_usage.WatchLogs((), not_chain_driven=95, unparsed_names=("x.log",),
                                     total_seen=239)
        cov = chain_usage.coverage((), logs)
        assert cov.logs_seen == 239
        assert cov.logs_not_chain_driven == 95
        assert cov.logs_unparsed == ("x.log",)

    def test_each_population_is_counted_on_its_own(self):
        runs = (
            _run("SRS", chain_usage.Kind.PRODUCER, 1),
            _run("SDD", chain_usage.Kind.SEAT, 2, source=chain_usage.Source.SEAT_SESSION),
            _run("SDD", chain_usage.Kind.SEAT, 3, source=chain_usage.Source.SEAT_SESSION),
        )
        cov = chain_usage.coverage(runs, chain_usage.WatchLogs((), 0, (), 0))
        assert (cov.chain_driven_runs, cov.seat_runs) == (1, 2)

    def test_a_run_left_unplaced_by_the_cycle_rule_is_named(self):
        runs = chain_usage.with_cycles(
            (_run("SRS", chain_usage.Kind.SEAT, None, label="sdd-x-run1-cpo",
                  source=chain_usage.Source.SEAT_SESSION),)
        )
        cov = chain_usage.coverage(runs, chain_usage.WatchLogs((), 0, (), 0))
        assert cov.unplaced == ("sdd-x-run1-cpo",)


def test_no_aggregate_ever_sums_two_spend_classes():
    # run_usage.py:31 -- "no output anywhere sums the five classes". The aggregation here adds
    # a class to the same class across runs and never one class to another, and it does that by
    # never adding ModelSpends at all: it re-runs the sibling's accumulator over the combined
    # records.
    source = Path(chain_usage.__file__).read_text()
    for forbidden in [".input +", ".output +", ".cache_read +", ".thinking +"]:
        assert forbidden not in source


# ── Task 5 — the state file, the whole reading, the two renderings and the CLI ──


STATE_FILE = {
    "chain_name": "definition",
    "project": "demo",
    "instance_root": "/instance",
    "product_path": "/product",
    "spine": ["PRD", "Agari", "SRS", "UXD", "DESIGN", "CONTENT", "SDD"],
    "ended": "settled",
    "ended_reason": "every spine document is settled",
    "schema_version": 2,
}


class TestChainState:
    def test_the_facts_this_reader_uses_are_read_off_the_state(self, tmp_path):
        path = tmp_path / "chain-demo-state.json"
        path.write_text(json.dumps(STATE_FILE))
        state = chain_usage.chain_state(path, chain_usage.Files())
        assert state.chain_name == "definition"
        assert state.project == "demo"
        assert state.spine == ("PRD", "Agari", "SRS", "UXD", "DESIGN", "CONTENT", "SDD")
        assert state.ended == "settled"

    def test_a_state_that_cannot_be_read_yields_none_rather_than_raising(self, tmp_path):
        assert chain_usage.chain_state(tmp_path / "gone.json", chain_usage.Files()) is None

    def test_a_state_that_is_not_json_yields_none(self, tmp_path):
        path = tmp_path / "s.json"
        path.write_text("{not json")
        assert chain_usage.chain_state(path, chain_usage.Files()) is None

    def test_the_logs_dir_is_derived_from_the_instance_root_the_state_names(self, tmp_path):
        path = tmp_path / "s.json"
        path.write_text(json.dumps(STATE_FILE))
        state = chain_usage.chain_state(path, chain_usage.Files())
        assert chain_usage.logs_dir_for(state) == Path("/instance/system/logs")

    def test_a_state_with_no_instance_root_derives_no_logs_dir(self, tmp_path):
        path = tmp_path / "s.json"
        path.write_text(json.dumps({"project": "demo"}))
        state = chain_usage.chain_state(path, chain_usage.Files())
        assert chain_usage.logs_dir_for(state) is None


class TestSpineCoverage:
    def test_a_spine_document_with_no_run_in_this_reading_is_named(self):
        keys = chain_usage.document_keys(chain.DOCUMENT_REGISTRY)
        runs = (_run("SRS", chain_usage.Kind.PRODUCER, 1),)
        assert chain_usage.spine_without_runs(("SRS", "UXD"), runs, keys) == ("UXD",)

    def test_a_spine_document_named_by_the_pair_key_counts_as_read(self):
        # The spine names documents (ADR) and this reader keys cycles by the self-answer
        # argument (architecture). Without the mapping, a walked ADR reads as unwalked.
        keys = chain_usage.document_keys(chain.DOCUMENT_REGISTRY)
        runs = (_run("architecture", chain_usage.Kind.PRODUCER, 1),)
        assert chain_usage.spine_without_runs(("ADR", "NFDR"), runs, keys) == ()

    def test_a_spine_entry_the_registry_does_not_know_is_named_too(self):
        keys = chain_usage.document_keys(chain.DOCUMENT_REGISTRY)
        assert chain_usage.spine_without_runs(("MYSTERY",), (), keys) == ("MYSTERY",)


def _tree(tmp_path, *, logs, agents, transcripts):
    """A whole walk on disk: a logs dir, an agents list, and the transcripts they join to."""
    logs_dir = tmp_path / "logs"
    for name, body in logs:
        _write_log(logs_dir, name, body)
    projects_root = tmp_path / "projects"
    for session_id, lines in transcripts.items():
        _write_transcript(projects_root, "slug", session_id, lines)
    return logs_dir, projects_root, _agents_json(*agents)


class TestReadWalk:
    def test_both_populations_land_in_one_reading(self, tmp_path):
        producer = _agent_row("ecef71f7", "demo", 1)
        seat = _agent_row("cbd6cde0", "sdd-demo-run1-cpo", 1788965999000)
        logs_dir, projects_root, agents = _tree(
            tmp_path,
            logs=[("watch-demo-20260909-145750.log", CHAIN_DRIVEN_BODY)],
            agents=[producer, seat],
            transcripts={
                producer["sessionId"]: [
                    json.dumps(
                        {
                            "type": "user",
                            "message": {"content": "invoke the product-sdd skill for demo"},
                        }
                    ),
                    _usage_line(output_tokens=2),
                ],
                seat["sessionId"]: [_usage_line(output_tokens=30)],
            },
        )
        # The log body names run ecef71f7, which is the producer row.
        reading = chain_usage.read_walk(
            logs_dir=logs_dir,
            project="demo",
            agents_json_text=agents,
            projects_root=projects_root,
            files=chain_usage.Files(),
            keys=chain_usage.document_keys(chain.DOCUMENT_REGISTRY),
            since=None,
            until=None,
        )
        assert reading.coverage.chain_driven_runs == 1
        assert reading.coverage.seat_runs == 1
        row = chain_usage.by_document(reading.runs, reading.keys)[0]
        assert row.key == "SDD"
        assert row.spend["claude-sonnet-5"].output == 32

    def test_the_window_is_applied_to_both_populations(self, tmp_path):
        seat = _agent_row("cbd6cde0", "sdd-demo-run1-cpo", 1)
        logs_dir, projects_root, agents = _tree(
            tmp_path,
            logs=[("watch-demo-19990101-000000.log", CHAIN_DRIVEN_BODY)],
            agents=[seat],
            transcripts={},
        )
        reading = chain_usage.read_walk(
            logs_dir=logs_dir,
            project="demo",
            agents_json_text=agents,
            projects_root=projects_root,
            files=chain_usage.Files(),
            keys=chain_usage.document_keys(chain.DOCUMENT_REGISTRY),
            since=chain_usage.parse_day("2026-09-01"),
            until=None,
        )
        assert reading.runs == ()

    def test_the_cycles_are_assigned_in_the_reading(self, tmp_path):
        first = _agent_row("aaaaaaaa", "demo", 1)
        second = _agent_row("bbbbbbbb", "demo", 2)
        prompt = json.dumps(
            {"type": "user", "message": {"content": "invoke the product-srs skill for demo"}}
        )
        logs_dir, projects_root, agents = _tree(
            tmp_path,
            logs=[
                (
                    "watch-demo-20260901-090000.log",
                    CHAIN_DRIVEN_BODY.replace("ecef71f7", "aaaaaaaa"),
                ),
                (
                    "watch-demo-20260901-100000.log",
                    CHAIN_DRIVEN_BODY.replace("ecef71f7", "bbbbbbbb"),
                ),
            ],
            agents=[first, second],
            transcripts={
                first["sessionId"]: [prompt],
                second["sessionId"]: [prompt],
            },
        )
        reading = chain_usage.read_walk(
            logs_dir=logs_dir,
            project="demo",
            agents_json_text=agents,
            projects_root=projects_root,
            files=chain_usage.Files(),
            keys=chain_usage.document_keys(chain.DOCUMENT_REGISTRY),
            since=None,
            until=None,
        )
        assert sorted(run.cycle for run in reading.runs) == [1, 2]

    def test_the_product_path_comes_from_the_states_own_field_not_a_new_resolver(self, tmp_path):
        seat = _agent_row("cbd6cde0", "sdd-demo-run4-cpo", 1788965999000)
        logs_dir, projects_root, agents = _tree(
            tmp_path, logs=[], agents=[seat], transcripts={}
        )
        # SEAT_BLOCK (the default body) names sdd-demo-run4-{cto,cpo,cdo} — the file's own run
        # number must agree, since the record's names carry no run number of their own.
        _write_run_record(tmp_path / "product", 4)
        state = chain_usage.ChainStateFacts(
            chain_name="definition", project="demo", instance_root=None,
            product_path=str(tmp_path / "product"), spine=(), ended=None, ended_reason=None,
        )
        reading = chain_usage.read_walk(
            logs_dir=logs_dir,
            project="demo",
            agents_json_text=agents,
            projects_root=projects_root,
            files=chain_usage.Files(),
            keys=chain_usage.document_keys(chain.DOCUMENT_REGISTRY),
            since=None,
            until=None,
            state=state,
        )
        seat_run = next(run for run in reading.runs if run.kind is chain_usage.Kind.SEAT)
        assert seat_run.seat_evidence is chain_usage.SeatEvidence.RECORD

    def test_a_state_with_no_product_path_falls_back_to_the_pattern_for_every_seat(
        self, tmp_path
    ):
        seat = _agent_row("cbd6cde0", "sdd-demo-run1-cpo", 1788965999000)
        logs_dir, projects_root, agents = _tree(
            tmp_path, logs=[], agents=[seat], transcripts={}
        )
        state = chain_usage.ChainStateFacts(
            chain_name="definition", project="demo", instance_root=None,
            product_path=None, spine=(), ended=None, ended_reason=None,
        )
        reading = chain_usage.read_walk(
            logs_dir=logs_dir,
            project="demo",
            agents_json_text=agents,
            projects_root=projects_root,
            files=chain_usage.Files(),
            keys=chain_usage.document_keys(chain.DOCUMENT_REGISTRY),
            since=None,
            until=None,
            state=state,
        )
        seat_run = next(run for run in reading.runs if run.kind is chain_usage.Kind.SEAT)
        assert seat_run.seat_evidence is chain_usage.SeatEvidence.CONVENTION


    def test_with_no_state_the_reading_says_its_seats_were_read_by_the_name_convention(
        self, tmp_path
    ):
        # Station reached-when: "With no --state, the seat population a reading reports is
        # identical to today's, and the reading says its seats were read by the name convention."
        seats = [
            _agent_row("aaaaaaaa", "sdd-demo-run1-cpo", 1788965999000),
            _agent_row("bbbbbbbb", "sdd-demo-run1-cto", 1788965999001),
        ]
        logs_dir, projects_root, agents = _tree(tmp_path, logs=[], agents=seats, transcripts={})
        reading = chain_usage.read_walk(
            logs_dir=logs_dir,
            project="demo",
            agents_json_text=agents,
            projects_root=projects_root,
            files=chain_usage.Files(),
            keys=chain_usage.document_keys(chain.DOCUMENT_REGISTRY),
            since=None,
            until=None,
        )
        seat_ids = {r.session_id for r in reading.runs if r.kind is chain_usage.Kind.SEAT}
        today = chain_usage.seat_rows(chain_usage.agent_rows(agents), "demo")
        assert seat_ids == {s.row.session_id for s in today}

        text = chain_usage.render(reading)
        assert "convention" in text
        assert "stated by each run's own record" not in text
        payload = json.loads(chain_usage.render_json(reading))
        assert "convention" in " ".join(payload["populations"])

    def test_a_recorded_name_no_agent_row_answers_to_is_reported_in_both_renderings(
        self, tmp_path
    ):
        # Plan Task 3: "A recorded name with no agent row is reported, not dropped." The reading's
        # two renderings are the only place a reader of this tool sees anything, so a name
        # computed and then discarded before either is dropped.
        seat = _agent_row("cbd6cde0", "sdd-demo-run4-cpo", 1788965999000)
        logs_dir, projects_root, agents = _tree(tmp_path, logs=[], agents=[seat], transcripts={})
        _write_run_record(tmp_path / "product", 4)  # names sdd-demo-run4-{cto,cpo,cdo}
        state = chain_usage.ChainStateFacts(
            chain_name="definition", project="demo", instance_root=None,
            product_path=str(tmp_path / "product"), spine=(), ended=None, ended_reason=None,
        )
        reading = chain_usage.read_walk(
            logs_dir=logs_dir,
            project="demo",
            agents_json_text=agents,
            projects_root=projects_root,
            files=chain_usage.Files(),
            keys=chain_usage.document_keys(chain.DOCUMENT_REGISTRY),
            since=None,
            until=None,
            state=state,
        )

        text = chain_usage.render(reading)
        json_text = chain_usage.render_json(reading)
        for unanswered in ("sdd-demo-run4-cto", "sdd-demo-run4-cdo"):
            assert unanswered in text
            assert unanswered in json_text


def _reading(runs, *, state=None, logs=None):
    return chain_usage.Reading(
        project="demo",
        runs=chain_usage.with_cycles(tuple(runs)),
        coverage=chain_usage.coverage(
            chain_usage.with_cycles(tuple(runs)), logs or chain_usage.WatchLogs((), 0, (), 0)
        ),
        keys=chain_usage.document_keys(chain.DOCUMENT_REGISTRY),
        state=state,
        since=None,
        until=None,
    )


class TestRender:
    def test_both_population_sentences_are_stated_in_the_readers_own_words(self):
        text = chain_usage.render(_reading([]))
        assert chain_usage.POPULATION_NOTE in text
        assert chain_usage.SEAT_POPULATION_NOTE in text

    def test_the_cycle_rule_is_stated_never_left_implied(self):
        text = chain_usage.render(_reading([]))
        assert chain_usage.CYCLE_NOTE in text

    def test_a_document_row_carries_its_cycles_and_its_five_classes(self):
        runs = [
            _run("SRS", chain_usage.Kind.PRODUCER, 100,
                 records=(_usage(output_tokens=5, input_tokens=2, cache_read_input_tokens=9),)),
        ]
        text = chain_usage.render(_reading(runs))
        assert "SRS" in text
        assert "output=5" in text
        assert "cache_read=9" in text

    def test_thinking_is_reported_beside_output_never_added_to_it(self):
        runs = [
            _run(
                "SRS",
                chain_usage.Kind.PRODUCER,
                100,
                records=(
                    (
                        {
                            "input_tokens": 0,
                            "output_tokens": 100,
                            "cache_read_input_tokens": 0,
                            "output_tokens_details": {"thinking_tokens": 40},
                        },
                        "m",
                        "2026-09-09T14:00:00.000Z",
                    ),
                ),
            )
        ]
        text = chain_usage.render(_reading(runs))
        assert "output=100" in text
        assert "thinking=40" in text
        assert "output=140" not in text

    def test_the_coverage_line_names_what_could_not_be_read(self):
        runs = [
            _run("SRS", chain_usage.Kind.PRODUCER, 100, label="watch-x.log",
                 transcript=chain_usage.Transcript.MISSING)
        ]
        text = chain_usage.render(_reading(runs))
        assert "1 transcript missing" in text or "missing" in text.lower()

    def test_the_state_the_walk_ended_in_is_carried_when_a_state_file_is_given(self):
        state = chain_usage.ChainStateFacts(
            chain_name="definition",
            project="demo",
            instance_root="/instance",
            product_path="/product",
            spine=("SRS",),
            ended="settled",
            ended_reason="every spine document is settled",
        )
        text = chain_usage.render(_reading([], state=state))
        assert "definition" in text
        assert "settled" in text

    def test_a_spine_document_with_no_run_is_named_in_the_report(self):
        state = chain_usage.ChainStateFacts(
            chain_name="definition", project="demo", instance_root=None, product_path=None,
            spine=("SRS", "UXD"), ended=None, ended_reason=None,
        )
        runs = [_run("SRS", chain_usage.Kind.PRODUCER, 100)]
        text = chain_usage.render(_reading(runs, state=state))
        assert "UXD" in text

    def test_a_reading_with_no_runs_says_so_rather_than_an_empty_table(self):
        assert "no runs" in chain_usage.render(_reading([])).lower()

    def test_a_reading_whose_seats_were_all_record_read_says_stated_by_the_records(self):
        runs = [
            _run("SDD", chain_usage.Kind.SEAT, 100, source=chain_usage.Source.SEAT_SESSION,
                 seat_evidence=chain_usage.SeatEvidence.RECORD),
        ]
        text = chain_usage.render(_reading(runs))
        assert "stated by each run's own record" in text

    def test_a_reading_that_fell_back_keeps_the_convention_wording_for_those_runs(self):
        runs = [
            _run("SDD", chain_usage.Kind.SEAT, 100, source=chain_usage.Source.SEAT_SESSION,
                 seat_evidence=chain_usage.SeatEvidence.RECORD),
            _run("SDD", chain_usage.Kind.SEAT, 200, source=chain_usage.Source.SEAT_SESSION,
                 seat_evidence=chain_usage.SeatEvidence.CONVENTION),
        ]
        text = chain_usage.render(_reading(runs))
        assert "convention" in text

    def test_a_reading_with_no_seat_runs_states_neither_half(self):
        runs = [_run("SRS", chain_usage.Kind.PRODUCER, 100)]
        text = chain_usage.render(_reading(runs))
        assert "stated by each run's own record" not in text


class TestRenderRecordReadNeverSaysConvention:
    def test_an_all_record_read_reading_never_calls_its_seats_a_convention(self):
        # Plan Task 5: "SEAT_POPULATION_NOTE stops calling a record-read population a
        # convention, in the text report ... and the JSON both."
        runs = [
            _run("SDD", chain_usage.Kind.SEAT, 100, source=chain_usage.Source.SEAT_SESSION,
                 seat_evidence=chain_usage.SeatEvidence.RECORD),
        ]
        assert "convention" not in chain_usage.render(_reading(runs)).lower()


class TestSeatSourcingLine:
    def test_no_seat_runs_yields_the_empty_string(self):
        runs = (_run("SRS", chain_usage.Kind.PRODUCER, 100),)
        assert chain_usage.seat_sourcing_line(runs) == ""

    def test_all_record_read_names_the_record(self):
        runs = (
            _run("SDD", chain_usage.Kind.SEAT, 100, seat_evidence=chain_usage.SeatEvidence.RECORD),
        )
        assert "record" in chain_usage.seat_sourcing_line(runs)
        assert "convention" not in chain_usage.seat_sourcing_line(runs)

    def test_all_convention_names_the_convention(self):
        runs = (
            _run(
                "SDD", chain_usage.Kind.SEAT, 100,
                seat_evidence=chain_usage.SeatEvidence.CONVENTION,
            ),
        )
        assert "convention" in chain_usage.seat_sourcing_line(runs)

    def test_a_mix_names_both(self):
        runs = (
            _run("SDD", chain_usage.Kind.SEAT, 100, seat_evidence=chain_usage.SeatEvidence.RECORD),
            _run(
                "SDD", chain_usage.Kind.SEAT, 200,
                seat_evidence=chain_usage.SeatEvidence.CONVENTION,
            ),
        )
        line = chain_usage.seat_sourcing_line(runs)
        assert "record" in line
        assert "convention" in line


class TestRenderJson:
    def test_the_json_carries_the_same_figures_as_the_table(self):
        runs = [
            _run("SRS", chain_usage.Kind.PRODUCER, 100, records=(_usage(output_tokens=5),)),
        ]
        payload = json.loads(chain_usage.render_json(_reading(runs)))
        assert payload["documents"][0]["key"] == "SRS"
        assert payload["documents"][0]["spend"]["m"]["output"] == 5
        assert payload["cycles"][0]["cycle"] == 1

    def test_the_json_states_both_populations_and_the_cycle_rule(self):
        payload = json.loads(chain_usage.render_json(_reading([])))
        assert payload["populations"] == [
            chain_usage.POPULATION_NOTE,
            chain_usage.SEAT_POPULATION_NOTE,
        ]
        assert payload["cycle_rule"] == chain_usage.CYCLE_NOTE

    def test_the_json_carries_the_per_run_rows_the_table_summarises(self):
        runs = [
            _run("SRS", chain_usage.Kind.PRODUCER, 100, label="watch-x.log",
                 records=(_usage(output_tokens=5),))
        ]
        payload = json.loads(chain_usage.render_json(_reading(runs)))
        assert payload["runs"][0]["label"] == "watch-x.log"
        assert payload["runs"][0]["kind"] == "producer"
        assert payload["runs"][0]["source"] == "watch-log"
        assert payload["runs"][0]["cycle"] == 1

    def test_the_json_carries_each_seat_runs_evidence(self):
        runs = [
            _run("SDD", chain_usage.Kind.SEAT, 100, source=chain_usage.Source.SEAT_SESSION,
                 seat_evidence=chain_usage.SeatEvidence.RECORD),
            _run("SDD", chain_usage.Kind.SEAT, 200, source=chain_usage.Source.SEAT_SESSION,
                 seat_evidence=chain_usage.SeatEvidence.CONVENTION),
            _run("SRS", chain_usage.Kind.PRODUCER, 300),
        ]
        payload = json.loads(chain_usage.render_json(_reading(runs)))
        by_started = {row["started_at"]: row["seat_evidence"] for row in payload["runs"]}
        assert by_started[100] == "record"
        assert by_started[200] == "convention"
        assert by_started[300] is None

    def test_an_all_record_read_reading_says_so_in_the_json_and_never_says_convention(self):
        # Plan Task 5, the JSON half: "A reading whose runs were all record-read says the seats
        # are stated by each run's own record" — in "the text report ... and the JSON both".
        runs = [
            _run("SDD", chain_usage.Kind.SEAT, 100, source=chain_usage.Source.SEAT_SESSION,
                 seat_evidence=chain_usage.SeatEvidence.RECORD),
        ]
        populations = " ".join(
            json.loads(chain_usage.render_json(_reading(runs)))["populations"]
        )
        assert "stated by each run's own record" in populations
        assert "convention" not in populations.lower()

    def test_a_reading_that_fell_back_keeps_the_convention_wording_in_the_json(self):
        runs = [
            _run("SDD", chain_usage.Kind.SEAT, 100, source=chain_usage.Source.SEAT_SESSION,
                 seat_evidence=chain_usage.SeatEvidence.RECORD),
            _run("SDD", chain_usage.Kind.SEAT, 200, source=chain_usage.Source.SEAT_SESSION,
                 seat_evidence=chain_usage.SeatEvidence.CONVENTION),
        ]
        populations = " ".join(
            json.loads(chain_usage.render_json(_reading(runs)))["populations"]
        )
        assert "convention" in populations

    def test_thinking_stays_null_rather_than_zero_when_nothing_carried_it(self):
        runs = [_run("SRS", chain_usage.Kind.PRODUCER, 100, records=(_usage(output_tokens=5),))]
        payload = json.loads(chain_usage.render_json(_reading(runs)))
        assert payload["documents"][0]["spend"]["m"]["thinking"] is None


class TestCompositionRoot:
    def test_no_module_level_name_holds_the_expanded_projects_root(self):
        default_root = Path.home() / ".claude" / "projects"
        holders = [
            name
            for name, value in vars(chain_usage).items()
            if value == default_root or value == str(default_root)
        ]
        assert holders == []

    def test_build_reader_resolves_the_default_projects_root(self):
        reader = chain_usage.build_reader()
        assert reader.projects_root == Path.home() / ".claude" / "projects"
        assert isinstance(reader.files, chain_usage.Files)

    def test_build_reader_honors_an_explicit_projects_root(self, tmp_path):
        assert chain_usage.build_reader(tmp_path).projects_root == tmp_path

    def test_only_build_reader_constructs_a_port(self):
        tree = ast.parse(Path(chain_usage.__file__).read_text())
        constructing = set()
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            for call in ast.walk(node):
                if isinstance(call, ast.Call) and isinstance(call.func, ast.Name):
                    if call.func.id == "Files":
                        constructing.add(node.name)
                if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute):
                    if call.func.attr == "Processes":
                        constructing.add(node.name)
        assert constructing == {"build_reader"}

    def test_main_obtains_its_ports_from_build_reader_and_constructs_none_itself(self):
        source = inspect.getsource(chain_usage.main)
        assert "build_reader(" in source
        assert "Files(" not in source


class TestCli:
    def _walk_on_disk(self, tmp_path):
        row = _agent_row("ecef71f7", "demo", 1)
        logs_dir, projects_root, agents = _tree(
            tmp_path,
            logs=[("watch-demo-20260909-145750.log", CHAIN_DRIVEN_BODY)],
            agents=[row],
            transcripts={
                row["sessionId"]: [
                    json.dumps(
                        {
                            "type": "user",
                            "message": {"content": "invoke the product-srs skill for demo"},
                        }
                    ),
                    _usage_line(output_tokens=9),
                ]
            },
        )
        agents_file = tmp_path / "agents.json"
        agents_file.write_text(agents)
        return logs_dir, projects_root, agents_file

    def test_a_logs_dir_and_a_project_read_the_walk(self, tmp_path, capsys):
        logs_dir, projects_root, agents_file = self._walk_on_disk(tmp_path)
        code = chain_usage.main(
            [
                "--logs-dir", str(logs_dir),
                "--project", "demo",
                "--agents-json", str(agents_file),
                "--projects-root", str(projects_root),
            ]
        )
        assert code == 0
        out = capsys.readouterr().out
        assert "SRS" in out
        assert "output=9" in out

    def test_the_state_file_supplies_the_project_and_the_logs_dir(self, tmp_path, capsys):
        logs_dir, projects_root, agents_file = self._walk_on_disk(tmp_path)
        state = tmp_path / "chain-demo-state.json"
        state.write_text(
            json.dumps({**STATE_FILE, "instance_root": str(logs_dir.parent.parent)})
        )
        # logs_dir_for appends system/logs, so lay the tree out that way.
        real_logs = logs_dir.parent.parent / "system" / "logs"
        real_logs.mkdir(parents=True)
        for log in logs_dir.iterdir():
            (real_logs / log.name).write_text(log.read_text())

        code = chain_usage.main(
            [
                "--state", str(state),
                "--agents-json", str(agents_file),
                "--projects-root", str(projects_root),
            ]
        )
        assert code == 0
        out = capsys.readouterr().out
        assert "definition" in out
        assert "SRS" in out

    def test_no_project_and_no_state_is_a_usage_error_naming_what_is_missing(
        self, tmp_path, capsys
    ):
        code = chain_usage.main(["--logs-dir", str(tmp_path), "--agents-json", str(tmp_path)])
        assert code != 0
        assert "--project" in capsys.readouterr().err

    def test_json_and_table_report_the_same_numbers(self, tmp_path, capsys):
        logs_dir, projects_root, agents_file = self._walk_on_disk(tmp_path)
        argv = [
            "--logs-dir", str(logs_dir),
            "--project", "demo",
            "--agents-json", str(agents_file),
            "--projects-root", str(projects_root),
        ]
        chain_usage.main(argv)
        assert "output=9" in capsys.readouterr().out

        chain_usage.main(argv + ["--json"])
        payload = json.loads(capsys.readouterr().out)
        assert payload["documents"][0]["spend"]["claude-sonnet-5"]["output"] == 9

    def test_a_bad_since_date_is_a_usage_error(self, tmp_path, capsys):
        logs_dir, projects_root, agents_file = self._walk_on_disk(tmp_path)
        code = chain_usage.main(
            [
                "--logs-dir", str(logs_dir),
                "--project", "demo",
                "--agents-json", str(agents_file),
                "--projects-root", str(projects_root),
                "--since", "yesterday",
            ]
        )
        assert code != 0
        assert "yesterday" in capsys.readouterr().err

    def test_an_unreadable_agents_file_is_a_usage_error_not_an_empty_reading(
        self, tmp_path, capsys
    ):
        logs_dir, projects_root, _agents_file = self._walk_on_disk(tmp_path)
        with pytest.raises(SystemExit):
            chain_usage.main(
                [
                    "--logs-dir", str(logs_dir),
                    "--project", "demo",
                    "--agents-json", str(tmp_path / "gone.json"),
                    "--projects-root", str(projects_root),
                ]
            )

    def test_the_reader_writes_nothing(self, tmp_path):
        logs_dir, projects_root, agents_file = self._walk_on_disk(tmp_path)
        before = sorted(p.relative_to(tmp_path) for p in tmp_path.rglob("*"))
        chain_usage.main(
            [
                "--logs-dir", str(logs_dir),
                "--project", "demo",
                "--agents-json", str(agents_file),
                "--projects-root", str(projects_root),
            ]
        )
        after = sorted(p.relative_to(tmp_path) for p in tmp_path.rglob("*"))
        assert before == after


def test_the_module_carries_the_version_marker_its_kind_takes():
    # versioning.md's table: "Scripts & hooks, Python -- `__version__ = "x.y.z"`". The test
    # file carries none, by the same table: "Test files -- none".
    assert re.fullmatch(r"\d+\.\d+\.\d+", chain_usage.__version__)
    assert "__version__" not in Path(__file__).read_text().split("def test_the_module")[0]
