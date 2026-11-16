"""Layer-6 pins on the two seats' skills that may ask QA's step to change its scenarios.

The seats are derived, never listed: the chain's `_ASKERS` names the steps whose runs may ask, and
`CHANGE_STEPS` maps each step to the skill that runs it. A third asker the chain gains is held to
these rules the day it lands. The pins read the committed prose, collapse its whitespace, and anchor
on a command token, an identifier or a few words of a sentence, never on a whole wrapped line.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pytest

import chain_development

_REPO = Path(__file__).resolve().parents[2]
_SECTION = "Asking QA to change its scenarios"
_RUNNER = '"<CORE>/tools/locked_python.sh" "<CORE>/tools/chain_development.py"'
_ASK_PLACE = f"{_RUNNER} --qa-ask-place <key>"
_QA_APPLIES = f"{_RUNNER} --qa-applies <key>"
_NAMED_NOWHERE = (
    "qa_ask.md", "qa_record", "features/", ".feature", "--kind qa", "scenario_folder",
)

# What is true of one seat and not another, keyed by the step id the chain derives.
_TRIGGER = {
    "implementation": "cannot be built as its spec and plan state",
    "design": "cannot be made testable through the way in the product's NFDR records",
}
_NO_COMMIT_AFTER = {
    "implementation": ("no `implementation complete` closing commit", "no pause commit"),
    "design": ("no `change_design.md` is committed",),
}
_SEAT_NAME = {
    "implementation": "developer",
    "design": "architect",
}
_NOTE_PLACE = {
    "implementation": "`Developer Review Notes`",
    "design": "`## Architect Review Notes`",
}


@dataclass(frozen=True)
class Seat:
    step_id: str
    skill: str
    path: Path
    text: str


def _collapse(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def _seats() -> list[Seat]:
    seats = []
    for step in chain_development.CHANGE_STEPS:
        if step.id not in chain_development._ASKERS:
            continue
        found = sorted(_REPO.glob(f"skills/*/.claude/skills/{step.skill}/SKILL.md"))
        assert len(found) == 1, f"{step.skill}: {found}"
        seats.append(Seat(step.id, step.skill, found[0], _collapse(found[0].read_text("utf-8"))))
    return seats


_SEATS = _seats()
_EACH_SEAT = pytest.mark.parametrize("seat", _SEATS, ids=[seat.step_id for seat in _SEATS])


def _section(seat: Seat) -> str:
    """The seat's own section on asking, up to the next heading of its level or above."""
    heading = rf"#{{3,4}} {re.escape(_SECTION)} "
    match = re.search(heading + r"(.*?)(?= #{2,4} |$)", seat.text)
    assert match, f"{seat.skill} has no section {_SECTION}"
    return match.group(1)


@_EACH_SEAT
def test_the_seat_states_when_it_asks_and_only_on_a_change_qas_step_applied_to(seat):
    section = _section(seat)

    assert _TRIGGER[seat.step_id] in section
    assert "one of QA's scenarios, or a step definition it runs on, changes" in section
    assert _QA_APPLIES in section
    assert "only on a change QA's step applied to" in section
    assert ("A change QA's step passed has no scenarios, and the chain turns that ask down"
            in section)


@_EACH_SEAT
def test_the_seat_asks_at_most_once_and_a_second_ask_is_turned_down(seat):
    section = _section(seat)

    assert "asks at most once on one change" in section
    assert "turns down a second ask from it" in section


@_EACH_SEAT
def test_the_seat_says_the_ask_is_its_reason_and_an_ask_with_no_reason_is_turned_down(seat):
    section = _section(seat)

    assert "Its whole text is its reason, in plain text" in section
    assert "names the scenario or step definition that must change" in section
    assert "what must change in it" in section
    assert "why the run cannot go on without that change" in section
    assert "turns down an ask with no reason" in section


@_EACH_SEAT
def test_the_seat_writes_the_ask_where_the_chain_prints_and_leaves_it_uncommitted(seat):
    section = _section(seat)
    place = section.index(_ASK_PLACE)
    after = section[place:place + 400]

    assert "--instance-root" in after
    assert "--project" in after
    assert "main checkout" in section
    assert "never `$WORKTREE`" in section
    assert "Leave the ask uncommitted" in section


@_EACH_SEAT
def test_the_seat_names_no_ask_file_and_no_ask_folder_and_no_route_to_qas_files(seat):
    assert "--qa-ask-place" in seat.text
    for forbidden in _NAMED_NOWHERE:
        assert forbidden not in seat.text, forbidden


@_EACH_SEAT
def test_the_seat_states_what_it_does_when_the_ask_place_command_exits_non_zero(seat):
    section = _section(seat)

    assert "exits non-zero" in section
    assert "the run leaves no ask" in section
    assert "at no other path" in section
    assert f"records the command's message in {_NOTE_PLACE[seat.step_id]}" in section
    assert "goes on as a run that left no ask" in section


@_EACH_SEAT
def test_the_asking_run_ends_at_the_ask_with_no_commit_after_it_and_no_halt_report(seat):
    section = _section(seat)

    assert "The ask is the run's last act" in section
    assert "commits made before the ask stand" in section.lower()
    for no_commit in _NO_COMMIT_AFTER[seat.step_id]:
        assert no_commit in section
    assert "An ask is not a halt, so the run writes no `halt_report.md` for it" in section


def test_the_asking_run_is_named_among_the_ways_each_seat_ends():
    implementation = next(seat for seat in _SEATS if seat.step_id == "implementation")
    design = next(seat for seat in _SEATS if seat.step_id == "design")
    workflow_three = re.search(r"3\. Close — (.*?) ### Step 1 ", implementation.text)
    signal = re.search(r'Signal: \*\*"change_design: clean\."\*\*(.*?)(?= #{2,4} |$)', design.text)

    assert workflow_three and "leave an ask of QA's step and end" in workflow_three.group(1)
    assert signal and "change_design: asked QA to change its scenarios." in signal.group(1)


@_EACH_SEAT
def test_the_seat_says_the_chain_answers_the_ask_when_the_run_ends(seat):
    section = _section(seat)

    assert "The chain answers the ask when the run ends" in section
    assert "An accepted ask runs QA's step again" in section
    comes_back = f"the walk comes back to the {_SEAT_NAME[seat.step_id]} in a new run of this skill"
    assert comes_back in section
    assert "A turned-down ask lets the run's end count as it would with no ask left" in section


def _developer() -> Seat:
    return next(seat for seat in _SEATS if seat.step_id == "implementation")


def test_the_developers_skill_says_the_plan_before_the_ask_stands():
    section = _section(_developer())

    assert "A plan written before the ask stands" in section
    assert "works from the same `tl_instruction.md`, from its first unfinished task" in section
    assert "asks for no new plan" in section
    assert "does not edit `tl_instruction.md`" in section


def test_the_developers_skill_says_the_ask_is_its_only_way_back_to_qas_files():
    section = _section(_developer())

    assert "The ask is the developer's only way back to QA's files" in section
    assert ("QA's files are the change's scenarios, the step definitions they run on, "
            "and QA's record") in section
    assert "never writes, edits, commits, moves or deletes any of them" in section
