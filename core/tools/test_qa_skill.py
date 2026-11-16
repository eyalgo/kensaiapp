"""Layer-6 pins on QA's skill, `red-behaviour`: the shape of its folder, its launcher and its rich
prompt. They read the committed tree, because the property is where the files are and what a few
literal lines hold.

A string test cannot decide what a sentence means. What the prompts say about the scenario rules
and the four no-way-in states is read in the diff; these pin only the anchors a launcher or a
cross-reference needs to find.
"""

from __future__ import annotations

import re
from pathlib import Path

import chain_development
import intelligence
import record_declarations

_REPO = Path(__file__).resolve().parents[2]
_SKILL = _REPO / "skills" / "qa" / ".claude" / "skills" / "red-behaviour"
_SEVEN_FILES = (
    "SKILL.md",
    "launcher.md",
    "prompts/thin.md",
    "prompts/rich.md",
    "references/qa_record_template.md",
    "intelligence/claude.md",
    "intelligence/codex.md",
)


def _lines(relative: str) -> list[str]:
    return (_SKILL / relative).read_text(encoding="utf-8").splitlines()


def test_the_skill_folder_holds_its_seven_files():
    for relative in _SEVEN_FILES:
        path = _SKILL / relative

        assert path.is_file(), relative
        assert path.stat().st_size > 0, relative


def test_the_record_template_labels_are_the_declared_slots_in_order():
    record = record_declarations.parse(
        (_SKILL / "references" / "qa_record_template.md").read_text(encoding="utf-8"))
    prefixes = [field.prefix for field in record_declarations.QA_RECORD_SLOTS]
    labels = [
        next(prefix for prefix in prefixes if line.text.startswith(prefix))
        for line in record.lines
        if any(line.text.startswith(prefix) for prefix in prefixes)
    ]

    assert labels == prefixes


def test_the_launcher_names_the_qa_agent_and_its_arguments():
    lines = _lines("launcher.md")

    assert any(line.startswith("**Agent:** qa") for line in lines)
    assert any(line.startswith("**Arguments:** <project> <key>") for line in lines)
    assert not any(line.startswith(("**Model:**", "**Effort:**")) for line in lines)


def test_the_rich_prompt_anchors_on_the_behave_way_in_line():
    assert "**Behave way in:**" in (_SKILL / "prompts" / "rich.md").read_text(encoding="utf-8")


def test_rich_lists_the_no_reach_answer_the_run_acts_on():
    answers = [line for line in _lines("prompts/rich.md") if line.startswith("- **`qa red: ")]

    assert any(line.startswith('- **`qa red: no reach — "{no-reach line}"`**') for line in answers)


def test_the_qa_skill_reads_on_codex():
    found = intelligence.read(_SKILL, "codex")

    assert (found.model, found.effort) == ("gpt-6.1-sol", "high")
    assert "## Why" in _lines("intelligence/codex.md")


_QA_LOADER = _REPO / "core" / "roles" / "loaders" / "qa_global.md"


def test_the_qa_loader_names_neither_retired_string():
    text = _QA_LOADER.read_text(encoding="utf-8")

    assert "Not a step in the chain" not in text
    assert "create_acceptance" not in text  # the retired prompt, by a stem short enough that no search for its name lists this file


def test_the_qa_loader_names_its_skill():
    assert "red-behaviour" in _QA_LOADER.read_text(encoding="utf-8")


def test_the_qa_loader_no_longer_says_the_two_asks_are_not_built():
    text = _QA_LOADER.read_text(encoding="utf-8")

    # An ask written as unbuilt: the word "ask" and "not built yet" in one sentence.
    for sentence in text.replace("\n", " ").split(". "):
        assert not ("ask" in sentence and "not built yet" in sentence), sentence
    for old in ("That ask is not built yet.",
                "will be allowed to ask once, saying why",
                "will be allowed to ask you once to change your scenarios",
                "one ask each of you are not built yet"):
        assert old not in text, old
    # What the chain does now, once for each seat.
    assert "The Architect may send the walk back to your step once" in text
    assert "the Developer may send the walk back to your step once" in text
    assert "The chain takes one ask from the Developer and one from the Architect" in text


def test_the_qa_loader_no_longer_says_the_closing_step_is_not_built():
    loader = _QA_LOADER.read_text(encoding="utf-8")
    skill = (_SKILL / "SKILL.md").read_text(encoding="utf-8")

    assert "The closing step that runs every scenario on the final code is not built yet." not in loader
    assert "The closing step that runs every scenario on the final code is not built yet." not in skill


# --- the skill does what the chain now expects (Task 19) -------------------------------------


def _text(relative: str) -> str:
    return (_SKILL / relative).read_text(encoding="utf-8")


def test_the_skill_names_the_decision_the_verdict_and_the_paths_command():
    text = _text("SKILL.md")

    for command in ("--qa-applies", "--check-qa-red", "target --kind qa"):
        assert command in text, command


def test_the_skill_writes_qas_record_before_it_asks_the_draft_verdict():
    # The draft verdict reads each scenario's kind from the record in the working tree, so a run
    # that asked before writing it would be refused for a record it has not written yet.
    text = _text("SKILL.md")

    assert text.index("references/qa_record_template.md") < text.index("--check-qa-red")


def test_every_command_in_the_skill_runs_on_the_locked_python():
    tool_lines = [line for line in _text("SKILL.md").splitlines()
                  if line.startswith('"<CORE>/tools/')]

    assert len(tool_lines) >= 4  # resolve, --qa-applies, target --kind qa, --check-qa-red
    for line in tool_lines:
        assert line.startswith('"<CORE>/tools/locked_python.sh" '), line


def test_the_skill_no_longer_says_it_writes_no_file_and_no_longer_says_the_closing_step_is_unbuilt():
    text = _text("SKILL.md")
    description = text.split("when_to_use:", 1)[0]

    for sentence in ("It writes no file, makes no commit and runs no scenario",
                     "Four pieces are not built yet",
                     "that function is not built yet",
                     "No file, no commit, no run of a scenario",
                     "It describes the scenarios in its closing message",
                     "the chain step, the red commit, the verdict"):
        assert sentence not in text, sentence
    assert "not built yet" not in description
    # What stays true: the refusal for posture. The two asks are no longer unbuilt: the chain
    # takes one from each seat. The closing step is built, so its sentence is gone.
    assert "The closing step that runs every scenario on the final code is not built yet." not in text
    assert "The chain takes one ask from the developer and one from the Architect" in text
    assert "The developer's and the Architect's one ask each of QA are not built yet" not in text
    assert "red-behaviour wrote no file and made no commit." in text


def test_the_launcher_no_longer_says_no_chain_step_launches_it():
    text = _text("launcher.md")

    assert "No chain step launches the skill yet" not in text
    assert "The chain launches it as its `red-behaviour` step" in text


def test_the_rich_prompts_closing_message_section_no_longer_carries_not_built_yet_for_running_committing_and_the_record():
    text = _text("prompts/rich.md")

    for sentence in ("## What is not built yet",
                     "Running the scenarios, committing their red and writing QA's record are not"
                     " built yet",
                     "No scenario was run.",
                     "and wrote no file.",
                     "red-behaviour described"):
        assert sentence not in text, sentence
    assert "## Asking the verdict, and what each answer means" in text
    assert "red-behaviour committed 1 scenario for the change `{key}` as its red." in text


# --- the pipeline's tables name QA's stage and halts (Task 20) -------------------------------

_DOCTRINE = _REPO / "core" / "doctrine"
_AFTER_THE_SPEC = "after the spec, before the design"


def _doctrine_lines(relative: str) -> list[str]:
    return (_DOCTRINE / relative).read_text(encoding="utf-8").splitlines()


def test_the_testing_doctrine_places_layers_6_and_7_after_the_spec_before_the_design():
    lines = _doctrine_lines("engineering/testing_doctrine.md")
    description = next(line for line in lines if line.startswith("description:"))
    bullet = next(line for line in lines if line.startswith("- **Layers 6–7"))

    assert _AFTER_THE_SPEC in description
    assert _AFTER_THE_SPEC in bullet


def test_the_stage_table_holds_a_red_behaviour_row_between_the_product_owners_and_the_architects():
    rows = [line for line in _doctrine_lines("flow/development_flow.md")
            if line.startswith("| ") and "`development-specs`" in line
            or line.startswith(("| 1a |", "| 2 |"))]

    assert [row.split("|")[1].strip() for row in rows] == ["1", "1a", "2"]
    assert "`red-behaviour`" in rows[1] and "QA" in rows[1]


def test_the_halts_table_holds_a_row_for_each_of_the_six_halt_names():
    rows = [line for line in _doctrine_lines("flow/step_outcome_contract.md")
            if line.startswith("| `")]
    first_cells = [row.split("|")[1] for row in rows]

    for name in ("qa-red-refused", "qa-record-refused", "qa-main-red", "behave-unavailable",
                 "missing-qa-red", "no-way-in"):
        assert any(f"`{name}" in cell for cell in first_cells), name


def _halts_row(name: str) -> str:
    return next(line for line in _doctrine_lines("flow/step_outcome_contract.md")
                if line.startswith(f"| `{name}"))


def test_the_halts_table_holds_a_qa_runs_spent_row():
    rows = [line for line in _doctrine_lines("flow/step_outcome_contract.md")
            if line.startswith("| `")]
    first_cells = [row.split("|")[1] for row in rows]

    assert any(cell.strip().startswith("`qa-runs-spent") for cell in first_cells)


def test_the_qa_record_refused_row_names_the_ask():
    row = _halts_row("qa-record-refused")

    assert "made before the ask" in row


def test_the_missing_qa_red_row_names_the_ask():
    row = _halts_row("missing-qa-red")

    assert "an accepted ask" in row
    assert "retry of its own" in row


def test_the_missing_qa_red_row_names_the_no_reach_record():
    assert "No reach:" in _halts_row("missing-qa-red")


def test_the_step_enum_names_red_behaviour():
    step_line = next(line for line in _doctrine_lines("flow/step_outcome_contract.md")
                     if line.lstrip().startswith("step:"))

    assert '"development-specs" | "red-behaviour" | "development-design"' in step_line


def test_the_handoff_table_names_qa_record():
    rows = [line for line in _doctrine_lines("flow/folder_state_handoff.md")
            if line.startswith("| ") and "`qa_record.md`" in line]

    assert rows
    assert any("`red-behaviour`" in row for row in rows)


# What a re-run reads. The reason of an accepted ask comes from the change's ask record, read as a
# file, and only on a run the chain launched again; the pins anchor on short strings because the
# prose wraps.

def _collapse_text(text: str) -> str:
    return " ".join(text.split())


def _collapse(path: Path) -> str:
    return _collapse_text(path.read_text(encoding="utf-8"))


def _step_five() -> str:
    text = _text("SKILL.md")
    return text[text.index("### Step 5 "):text.index("### Step 6 ")]


def test_the_skill_names_the_ask_record_it_reads_the_reason_from_before_it_writes_the_scenarios():
    text = _collapse(_SKILL / "SKILL.md")
    record = "system/logs/chain-qa-<project>-<key>.json"
    before_step_seven = text[:text.index("### Step 7 ")]

    assert record in before_step_seven
    assert "reason" in before_step_seven[before_step_seven.index(record):]
    assert "--qa-ask-place" not in text


def test_the_ask_record_the_skill_reads_is_the_one_the_chain_writes_under_the_main_checkout():
    """CP-1365: the place is the chain's own record, under the main checkout, and the names the run
    reads in it are the ones the chain writes. Taken from the chain, so a renamed field or file
    fails here rather than leaving the skill reading a record that no longer exists."""
    text = _collapse(_SKILL / "SKILL.md")
    store = chain_development.QaAskStore(None, "$REPO_ROOT/system/logs")
    record = store.path("<project>", "<key>")

    assert 'WORKTREE="$REPO_ROOT/.worktrees/<key>"' in text
    assert f"`{record}`" in text
    assert {"open", "answered"} <= chain_development.QaAsks().to_json().keys()
    for name in ("open", "answered", "asker", "step", "answer", "reason"):
        assert f"`{name}`" in text, name
    assert f"`{chain_development.QaAskPhase.RE_RUN.value}`" in text
    assert f"`{chain_development.QA_ASK_ACCEPTED}`" in text


def test_the_skill_reads_the_reason_beside_the_spec_and_never_in_its_place():
    text = _collapse_text(_step_five())

    assert "The reason is read beside the spec, never in its place" in text
    assert "The scenarios are still written from `change_spec.md` as written" in text
    assert "raise it as a question in the review notes" in text
    assert "do not rewrite the rule" in text


def test_a_run_that_is_not_a_re_run_reads_no_reason_and_step_5_keeps_its_five_inputs():
    step_five = _step_five()
    collapsed = _collapse_text(step_five)
    numbered = [line for line in step_five.splitlines() if line[:2].rstrip(".").isdigit()]

    assert "A run the chain launched again on an accepted ask reads that ask's reason" in collapsed
    assert len(numbered) == 5
    assert "Read no `change_design.md` and no `tl_instruction.md`" in collapsed
    assert "On every other run no reason is read" in collapsed


# The sentences that said no seat's skill asks yet are corrected where they stand.

_FLOW = _REPO / "core" / "doctrine" / "flow" / "development_flow.md"
_SEAT_SKILLS = (
    _REPO / "skills" / "developer" / ".claude" / "skills" / "development-implementation",
    _REPO / "skills" / "architect" / ".claude" / "skills" / "development-design",
)
_THE_STATIONS_CHECK = re.compile(
    r"does not make one yet|make[s]? an ask yet|does not read the reason", re.IGNORECASE)


def _files_under(folder: Path) -> list[Path]:
    return sorted(path for path in folder.rglob("*") if path.is_file())


def _the_five_edited_prose_files() -> list[Path]:
    seats = (folder / "SKILL.md" for folder in _SEAT_SKILLS)
    return [_QA_LOADER, _SKILL / "SKILL.md", _FLOW, *seats]


def test_the_qa_loader_says_each_seats_skill_makes_its_ask_and_red_behaviour_reads_the_reason():
    text = _collapse(_QA_LOADER)

    assert "`development-design` does not make one yet" not in text
    assert "`development-implementation` does not make one yet" not in text
    assert "makes an ask yet, and `red-behaviour` does not read the reason" not in text
    assert "`development-design` makes that ask, and the chain takes it." in text
    assert "`development-implementation` makes that ask, and the chain takes it." in text
    assert ("Each seat's skill makes that seat's ask. Run again on an accepted ask, "
            "`red-behaviour` reads the ask's reason beside the spec, never in its place.") in text
    assert "The Architect may send the walk back to your step once" in text
    assert "the Developer may send the walk back to your step once" in text
    assert "The chain takes one ask from the Developer and one from the Architect" in text
    assert "you raise it as a question in your review notes and do not rewrite the rule" in text


def test_the_skills_line_39_says_each_seat_asks_and_the_skill_reads_the_reason_on_a_re_run():
    text = _collapse(_SKILL / "SKILL.md")

    assert "makes an ask yet, and this skill does not read the reason" not in text
    assert ("Each seat's skill makes that seat's ask. Run again on an accepted ask, "
            "this skill reads the ask's reason before it writes the scenarios (Step 5).") in text
    assert "The chain takes one ask from the developer and one from the Architect" in text


def test_the_pipeline_doc_no_longer_says_neither_seat_asks():
    text = _collapse(_FLOW)

    assert "Neither seat's skill makes an ask yet." not in text
    assert "Each seat's skill makes that seat's ask." in text
    assert "No later stage reads QA's files" in text


def test_the_stations_own_check_matches_no_line_in_the_five_files():
    files = [_QA_LOADER, *_files_under(_SKILL), _FLOW, *(path for folder in _SEAT_SKILLS
                                                          for path in _files_under(folder))]
    hits = [f"{path.name}:{number}" for path in files
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
            if _THE_STATIONS_CHECK.search(line)]

    assert hits == []


def test_no_not_built_yet_line_remains_in_the_five_edited_prose_files():
    for path in _the_five_edited_prose_files():
        for line in path.read_text(encoding="utf-8").splitlines():
            assert "not built yet" not in line, (path.name, line[:80])
    assert ("`development-design` makes that ask, and the chain takes it."
            in _collapse(_QA_LOADER))
