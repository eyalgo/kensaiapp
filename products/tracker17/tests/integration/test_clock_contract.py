"""The one `Clock` fake is checked on its own, and the contract for `now` is run against it (layers 1, 2).

Checks SRS NFR-10 and NFR-11: the tests are plain enough to read cold, and every test that needs a
clock hands in the one fake, which these checks hold to its own reads and controls. NFDR QC-64 and
SDD § 4 TS-6 are the clauses. The fake, in tests/fakes.py, has no base class and no `save`; each
control a test used to get from a stand-in of its own is checked here with no real clock, file or
process. The contract suite, in the second half of this module, states what `now` gives once and
runs it twice: handed `SystemClock`, which reads the machine's clock and touches no file, and
handed the fake. The contract is the one in application/contracts.py.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

import pytest

from tests.fakes import FakeClock

FIRST = datetime(2026, 10, 11, 9, 30, tzinfo=UTC)
SECOND = datetime(2026, 10, 11, 9, 45, tzinfo=UTC)
THIRD = datetime(2026, 10, 11, 10, 0, tzinfo=UTC)
LATER = datetime(2026, 10, 12, 8, 0, tzinfo=UTC)
NAIVE = datetime(2026, 10, 11, 9, 30)
PLUS_TWO_HOURS = datetime(2026, 10, 11, 9, 30, tzinfo=timezone(timedelta(hours=2)))
MINUTE = timedelta(minutes=1)


def test_a_fixed_clock_gives_its_one_instant_on_every_read() -> None:
    clock = FakeClock(FIRST)

    assert [clock.now(), clock.now(), clock.now()] == [FIRST, FIRST, FIRST]


def test_a_sequence_gives_each_instant_in_order_then_the_last_again() -> None:
    clock = FakeClock(FIRST, SECOND, THIRD)

    reads = [clock.now() for _ in range(5)]

    assert reads == [FIRST, SECOND, THIRD, THIRD, THIRD]


def test_a_clock_that_runs_out_gives_each_instant_once_then_fails() -> None:
    clock = FakeClock(FIRST, SECOND, runs_out=True)

    assert [clock.now(), clock.now()] == [FIRST, SECOND]
    with pytest.raises(AssertionError, match="more times than it was given instants"):
        clock.now()


def test_a_stepping_clock_gives_each_later_read_one_step_after_the_one_before() -> None:
    clock = FakeClock(FIRST, SECOND, step=MINUTE)

    reads = [clock.now() for _ in range(5)]

    assert reads == [
        FIRST,
        SECOND,
        SECOND + MINUTE,
        SECOND + 2 * MINUTE,
        SECOND + 3 * MINUTE,
    ]


def test_instant_reads_the_next_instant_and_does_not_count_as_a_read() -> None:
    clock = FakeClock(FIRST, SECOND)

    seen = clock.instant

    assert seen == FIRST
    assert clock.reads == 0
    assert clock.now() == seen
    assert clock.instant == SECOND
    assert clock.reads == 1


def test_setting_instant_makes_the_next_read_give_it_and_keeps_the_rest_queued() -> None:
    clock = FakeClock(FIRST, SECOND, THIRD)

    clock.instant = LATER

    assert [clock.now(), clock.now(), clock.now()] == [LATER, SECOND, THIRD]


def test_restart_hands_out_the_new_instants_and_resets_reads_to_zero() -> None:
    clock = FakeClock(FIRST)
    clock.now()
    clock.now()

    clock.restart(SECOND, THIRD)

    assert clock.reads == 0
    assert [clock.now(), clock.now(), clock.now()] == [SECOND, THIRD, THIRD]


def test_reads_counts_every_read() -> None:
    clock = FakeClock(FIRST)

    for expected in range(1, 5):
        clock.now()
        assert clock.reads == expected


def test_a_naive_instant_is_refused_by_the_constructor_as_first_and_in_then() -> None:
    with pytest.raises(ValueError, match="naive|aware"):
        FakeClock(NAIVE)
    with pytest.raises(ValueError, match="naive|aware"):
        FakeClock(FIRST, NAIVE)


def test_an_instant_at_plus_two_hours_is_refused_by_the_constructor_as_first_and_in_then() -> None:
    with pytest.raises(ValueError, match="UTC"):
        FakeClock(PLUS_TWO_HOURS)
    with pytest.raises(ValueError, match="UTC"):
        FakeClock(FIRST, PLUS_TWO_HOURS)


def test_restart_and_the_instant_setter_refuse_a_naive_instant_and_one_off_utc() -> None:
    clock = FakeClock(FIRST)

    for refused in (NAIVE, PLUS_TWO_HOURS):
        with pytest.raises(ValueError):
            clock.restart(refused)
        with pytest.raises(ValueError):
            clock.instant = refused

    assert clock.now() == FIRST


def test_step_together_with_runs_out_is_refused() -> None:
    with pytest.raises(ValueError, match="step"):
        FakeClock(FIRST, step=MINUTE, runs_out=True)


def test_the_fake_has_no_base_class_and_defines_no_save() -> None:
    assert FakeClock.__bases__ == (object,)
    assert not hasattr(FakeClock, "save")
