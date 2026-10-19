"""Live machinery may not order the opposite of the journey-pointer repair rule.

WHY THIS EXISTS
    `found_while_walking.md` § *A broken journey pointer is repaired, and the triple is what stops
    it breaking* states the rule with no exception — "repaired by the session that finds it" — and
    `core/docs/journey_move.md` § *After the move, say which pointers it broke* is the
    one shared mechanic that carries it: **"Repair what it names"**. Every skill that runs
    `check_journey_links.py` after a move delegates to that section rather than restating it.

    A second copy is a copy free to drift, and one did. The section
    `found_while_walking.md` § *One class is surfaced rather than fixed* was deleted when the rule
    changed from surface-only to repair, and a skill went on citing it — together with an
    imperative, "do not repair it", attributed to the very shared section that now says the
    opposite.

    The station `the-cold-read-is-answered` stated the bar as a grep. The grep passed while the
    contradiction stood, because the deleted heading is wrapped across a line in the citing file
    and a literal search for the phrase matches nothing. **That is why every check here folds
    whitespace before matching** — a bar that greps a wrapping phrase cannot pass, and a filter
    matching nothing is indistinguishable from a filter that works.

WHAT IS IN SCOPE
    Machinery the next session loads: `.claude/skills/`, `.claude/agents/` and `core/`. A record of
    a run that happened — a `trail/` or `drop/` seed, a `docs/` delegate report, a closed station —
    is deliberately out: it is correct as history, exactly as `check_journey_links.py` treats the
    retired seedbeds.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
# The flat root and every group under the grouped root, `skills/<group>/.claude/skills/`.
SKILL_ROOTS = (REPO / ".claude" / "skills", *sorted((REPO / "skills").glob("*/.claude/skills")))

# The heading `found_while_walking.md` no longer carries. Citing it routes a reader to nothing, and
# every live citation of it also carried the pre-change rule.
DELETED_HEADING = "One class is surfaced rather than fixed"

# Machinery, not record. A `docs/` report and a `trail/` seed say what a past run did and are left
# as written; these three trees say what the next run must do.
MACHINERY_ROOTS = (".claude/skills", "skills", ".claude/agents", "core")

# Orders to leave a broken journey pointer alone. Each is an imperative addressed to the run, not a
# description of the tool: `check_journey_links.py`'s own "reports; it does not repair" is a fact
# about the tool and is not in this set — what the *session* then owes is the doctrine's, and the
# doctrine says repair.
LEAVE_IT_ORDERS = (
    "do not repair",  # the literal the station's own bar greps for
    "reported, not repaired",
    "rather than work for anyone here",
)

_WS = re.compile(r"\s+")


def _folded(path: Path) -> str:
    """The file's text with every whitespace run folded to one space.

    Load-bearing: the citation this test exists to catch is broken across a line, so an unfolded
    search reports the file clean.
    """
    return _WS.sub(" ", path.read_text())


def _machinery_files() -> list[Path]:
    out: list[Path] = []
    for root in MACHINERY_ROOTS:
        base = REPO / root
        if base.is_dir():
            out += sorted(p for p in base.rglob("*.md") if p.is_file())
    return out


def _skill_files_running_the_checker() -> list[Path]:
    return [
        p
        for root in SKILL_ROOTS
        for p in sorted(root.rglob("*.md"))
        if "check_journey_links.py" in p.read_text()
    ]


def test_the_deleted_heading_is_cited_by_no_live_machinery_file():
    """`found_while_walking.md` § *One class is surfaced rather than fixed* was replaced. Nothing
    the next session loads may still send a reader to it."""
    citing = [
        p.relative_to(REPO).as_posix()
        for p in _machinery_files()
        if DELETED_HEADING in _folded(p)
    ]
    assert citing == [], (
        f"live machinery cites the deleted heading {DELETED_HEADING!r}: {citing}. "
        "The section is now `A broken journey pointer is repaired, and the triple is what stops "
        "it breaking`, and it says the opposite of what the old one said."
    )


def test_a_skill_that_runs_the_checker_names_at_least_one():
    """A guard on the guard: if the invocation is ever renamed, the test below would pass by
    checking nothing at all."""
    assert _skill_files_running_the_checker(), (
        "no skill names check_journey_links.py — the contradiction check below would be vacuous"
    )


@pytest.mark.parametrize("order", LEAVE_IT_ORDERS)
def test_no_skill_running_the_checker_orders_the_pointer_left_unrepaired(order):
    """`journey_move.md` § *After the move…* says "Repair what it names"; a skill that runs the
    checker delegates to it and may not restate the pre-change order."""
    offenders = [
        p.relative_to(REPO).as_posix()
        for p in _skill_files_running_the_checker()
        if order in _folded(p)
    ]
    assert offenders == [], (
        f"{offenders} order a broken journey pointer left alone ({order!r}), against "
        "`found_while_walking.md` § *A broken journey pointer is repaired…* — clause 1, with no "
        "exception — and against the shared mechanic they cite, which says `Repair what it names`."
    )


def test_the_shared_mechanic_still_orders_the_repair():
    """The other half of the same invariant: the one file the skills delegate to must carry the
    order they are forbidden to contradict, or every assertion above is a bar against nothing."""
    shared = _folded(REPO / "core" / "docs" / "journey_move.md")
    assert "Repair what it names" in shared
    for order in LEAVE_IT_ORDERS:
        assert order not in shared
