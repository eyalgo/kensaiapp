"""Characterization tests for the report's run aggregation.

Deterministic: pure arithmetic over per-query records, no browser and no HTML
assertions — this pins the numbers the report is built from, not its markup.

``aggregate_runs`` was a closure nested inside ``generate_html``, unreachable and
unchecked. It carries a second, independent copy of the same subtract-from-runs
shape as the loop's stats, so the two can drift apart and disagree about the same
run — the HTML saying one thing and the terminal another. These tests pin them to
the same rule, and the mirror of the loop's test is deliberate: a fact with two
implementations needs the same assertion in both places until it has one.
"""

import pytest

from scripts.generate_report import aggregate_runs


def _q(should_trigger: bool, triggers: int, runs: int, errors: int = 0) -> dict:
    return {
        "query": f"q(trigger={should_trigger})",
        "should_trigger": should_trigger,
        "triggers": triggers,
        "runs": runs,
        "errors": errors,
    }


def test_a_positive_query_is_correct_when_it_triggers():
    assert aggregate_runs([_q(True, 3, 3)]) == (3, 3)


def test_a_negative_query_is_correct_when_it_stays_quiet():
    """Correctness inverts for should-not-trigger queries — silence is the pass."""
    assert aggregate_runs([_q(False, 0, 3)]) == (3, 3)


def test_a_negative_query_that_fires_is_wrong():
    assert aggregate_runs([_q(False, 3, 3)]) == (0, 3)


def test_mixed_results_add_up():
    correct, total = aggregate_runs([_q(True, 2, 3), _q(False, 1, 3)])
    assert (correct, total) == (2 + 2, 6)


def test_errored_runs_are_not_scored_as_correct():
    """The report's version of the rule the loop's stats hold. A crashed run on a
    negative query used to land in ``runs - triggers`` and count as a point in the
    skill's favour — the harness rewarding itself for failing to run."""
    correct, total = aggregate_runs([_q(False, 0, 0, errors=3)])
    assert correct == 0
    assert total == 0


def test_errored_runs_do_not_inflate_the_denominator_either():
    """Excluded from both halves, so the ratio stays a statement about runs that
    actually answered."""
    correct, total = aggregate_runs([_q(True, 2, 2, errors=2)])
    assert (correct, total) == (2, 2)


@pytest.mark.parametrize("results", [[], [_q(True, 0, 0)]])
def test_empty_and_degenerate_inputs_are_safe(results):
    correct, total = aggregate_runs(results)
    assert correct == 0
    assert total == 0


def test_records_without_an_errors_field_still_work():
    """Result JSON written before the third outcome existed must still render."""
    legacy = {"query": "q", "should_trigger": False, "triggers": 0, "runs": 4}
    assert aggregate_runs([legacy]) == (4, 4)


def test_missing_keys_default_rather_than_raise():
    """The renderer reads with ``.get`` today and must keep tolerating sparse
    records — a half-written results file should not crash the report."""
    assert aggregate_runs([{"query": "q"}]) == (0, 0)
