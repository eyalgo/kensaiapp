"""Characterization tests for the confusion matrix behind the loop's verbose stats.

Deterministic: pure arithmetic over per-query records, no subprocess and no model
call. Companion to ``test_run_loop.py``, which pins the module's import and CLI
contract but nothing about what the numbers mean.

The maths lived in a closure nested inside ``run_loop``'s ``if verbose:`` block,
so nothing could reach it and nothing ever checked it. It is now module-level,
which is the only reason these tests can exist.

What they pin is one rule with teeth: **a run that errored is not a run that
answered.** Every negative cell here is derived by subtraction — ``fn = positive
runs - tp``, ``tn = negative runs - fp`` — so any crashed run swept into the run
count is silently booked as a false negative on a should-trigger query and a true
negative on a should-not. That deflates recall and inflates accuracy at the same
time, and it does it invisibly, which is the combination that cost two hours of
reading a broken harness as a wording problem.
"""

import pytest

from scripts.run_loop import compute_stats


def _q(should_trigger: bool, triggers: int, runs: int, errors: int = 0) -> dict:
    """One per-query record, the shape ``run_eval`` emits.

    ``runs`` counts runs that answered the question. ``errors`` counts runs that
    never got to answer it. They are deliberately separate totals.
    """
    return {
        "query": f"q(trigger={should_trigger})",
        "should_trigger": should_trigger,
        "triggers": triggers,
        "runs": runs,
        "errors": errors,
        "trigger_rate": (triggers / runs) if runs else 0.0,
        "pass": (triggers / runs >= 0.5) if runs else False,
    }


def test_a_perfect_run_scores_perfectly():
    stats = compute_stats([_q(True, 3, 3), _q(False, 0, 3)])
    assert (stats["tp"], stats["fn"], stats["fp"], stats["tn"]) == (3, 0, 0, 3)
    assert stats["precision"] == 1.0
    assert stats["recall"] == 1.0
    assert stats["accuracy"] == 1.0


def test_a_skill_that_never_fires_has_zero_recall():
    """The exact signature of the broken harness — every positive missed, every
    negative trivially correct, and a precision of 1.0 that means nothing because
    there were no positives to be wrong about."""
    stats = compute_stats([_q(True, 0, 3), _q(False, 0, 3)])
    assert stats["recall"] == 0.0
    assert stats["tp"] == 0
    assert stats["fn"] == 3


def test_a_skill_that_always_fires_has_perfect_recall_and_poor_precision():
    stats = compute_stats([_q(True, 3, 3), _q(False, 3, 3)])
    assert stats["recall"] == 1.0
    assert stats["precision"] == 0.5
    assert stats["fp"] == 3


def test_errored_runs_are_not_counted_as_missed_triggers():
    """THE rule. Three positive runs, one triggered, two crashed. The skill was
    asked once and answered once — recall is 1.0, not 0.33. Booking the crashes
    as false negatives would blame the description for an infrastructure fault."""
    stats = compute_stats([_q(True, 1, 1, errors=2)])
    assert stats["tp"] == 1
    assert stats["fn"] == 0
    assert stats["recall"] == 1.0
    assert stats["errors"] == 2


def test_errored_runs_are_not_counted_as_correct_negatives():
    """The mirror. A crashed run on a should-not-trigger query is not evidence of
    good behaviour, and counting it as a true negative inflates accuracy."""
    stats = compute_stats([_q(False, 0, 0, errors=3)])
    assert stats["tn"] == 0
    assert stats["fp"] == 0
    assert stats["errors"] == 3


def test_errors_are_reported_so_a_broken_run_is_visible():
    """The number that would have ended the confusion on sight."""
    stats = compute_stats([_q(True, 2, 2, errors=1), _q(False, 0, 3, errors=4)])
    assert stats["errors"] == 5


def test_a_run_where_everything_errored_does_not_look_like_a_result():
    """If nothing answered, the honest report is 'no data', not a confident 0%."""
    stats = compute_stats([_q(True, 0, 0, errors=3), _q(False, 0, 0, errors=3)])
    assert stats["total"] == 0
    assert stats["errors"] == 6


@pytest.mark.parametrize("results", [[], [_q(True, 0, 0)], [_q(False, 0, 0)]])
def test_empty_and_degenerate_inputs_do_not_divide_by_zero(results):
    stats = compute_stats(results)
    for key in ("precision", "recall", "accuracy"):
        assert 0.0 <= stats[key] <= 1.0


def test_records_without_an_errors_field_still_work():
    """Older result JSON on disk predates the third outcome and must still render."""
    legacy = {"query": "q", "should_trigger": True, "triggers": 2, "runs": 2, "pass": True}
    stats = compute_stats([legacy])
    assert stats["tp"] == 2
    assert stats["errors"] == 0
