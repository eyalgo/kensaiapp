"""journey_names: the one statement of what a station's slug and dated stem look like."""

import re

import pytest

import journey_names


@pytest.mark.parametrize("written, stem", [
    ("2026-10-12_the-first-leg", "2026-10-12_the-first-leg"),
    ("2026-10-12_the-first-leg.md", "2026-10-12_the-first-leg"),
    ("2026-10-12_a1", "2026-10-12_a1"),
])
def test_a_dated_stem_reads_with_or_without_its_md_suffix(written, stem):
    assert journey_names.station_stem(written) == stem


@pytest.mark.parametrize("written", [
    "the-first-leg", "2026-10-12_", "2026-10-12_The-Leg", "2026-10-12_-leg", "trail/2026-10-12_x",
    "2026-10-12_x.md.md", "26-10-12_x", "",
])
def test_anything_else_is_not_a_station_stem(written):
    assert journey_names.station_stem(written) is None


def test_the_slug_pattern_is_what_a_stem_carries_after_its_date():
    assert re.fullmatch(journey_names.SLUG, "the-first-leg")
    assert not re.fullmatch(journey_names.SLUG, "-leg")
    assert journey_names.STATION_STEM.pattern.endswith(journey_names.SLUG)
