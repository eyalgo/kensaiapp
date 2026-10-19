"""Tests for `provenance_test_support.py` — the helper every instrumented launcher's suite calls to
prove its own `instrument_run` call hands over the four provenance keys (CP-229, CP-230).

A helper whose one job is to fail on a dropped key has to be shown failing on one, on a synthetic
`launcher.sh` per case, so the helper is proved apart from the launchers it is pointed at.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from provenance_test_support import (
    PROVENANCE_KEYS,
    assert_instrument_run_call_carries_provenance,
    assert_provenance_stamped,
    isolated_host,
    place_own_skill,
    telemetry_pairs,
)

_FULL_CALL = (
    '  instrument_run skill="$skill" provider=claude model="$run_model" '
    'effort="$run_effort" source="$run_source"'
)


def _launcher(tmp_path: Path, *lines: str) -> Path:
    path = tmp_path / "launcher.sh"
    path.write_text("\n".join(["#!/usr/bin/env bash", "set -euo pipefail", *lines]) + "\n")
    return path


def test_the_four_keys_are_the_ones_instrument_run_stamps():
    assert PROVENANCE_KEYS == ("provider", "model", "effort", "source")


def test_a_call_line_carrying_all_four_keys_passes(tmp_path):
    assert_instrument_run_call_carries_provenance(_launcher(tmp_path, _FULL_CALL))


@pytest.mark.parametrize("dropped", PROVENANCE_KEYS)
def test_a_call_missing_any_one_of_the_four_keys_fails(tmp_path, dropped):
    call = " ".join(token for token in _FULL_CALL.split(" ") if not token.startswith(f"{dropped}="))
    launcher = _launcher(tmp_path, call)

    with pytest.raises(AssertionError, match=rf"\b{dropped}\b"):
        assert_instrument_run_call_carries_provenance(launcher)


def test_a_comment_naming_all_four_does_not_satisfy_a_bare_call(tmp_path):
    launcher = _launcher(
        tmp_path,
        "# instrument_run skill=x provider=claude model=m effort=e source=s",
        "  # instrument_run provider= model= effort= source=",
        "  instrument_run",
    )

    with pytest.raises(AssertionError):
        assert_instrument_run_call_carries_provenance(launcher)


def test_a_trailing_comment_on_the_call_line_does_not_supply_a_key(tmp_path):
    """Added beyond the instruction: a key named only in the call line's own trailing comment
    is a comment too — the same failure CP-230 names, one column to the right."""
    launcher = _launcher(
        tmp_path,
        '  instrument_run provider=claude model="$m" effort="$e"   # source= is stamped elsewhere',
    )

    with pytest.raises(AssertionError, match=r"\bsource\b"):
        assert_instrument_run_call_carries_provenance(launcher)


def test_a_key_that_only_ends_in_a_key_name_does_not_count(tmp_path):
    """Added beyond the instruction: `run_model=` is not `model=`. A substring search would take
    it for one."""
    launcher = _launcher(
        tmp_path,
        '  instrument_run provider=claude run_model="$m" effort="$e" source="$s"',
    )

    with pytest.raises(AssertionError, match=r"\bmodel\b"):
        assert_instrument_run_call_carries_provenance(launcher)


def test_keys_on_a_backslash_continued_line_fail(tmp_path):
    launcher = _launcher(
        tmp_path,
        '  instrument_run skill="$skill" \\',
        '    provider=claude model="$run_model" effort="$run_effort" source="$run_source"',
    )

    with pytest.raises(AssertionError):
        assert_instrument_run_call_carries_provenance(launcher)


def test_a_file_with_no_call_fails_naming_the_file(tmp_path):
    launcher = _launcher(tmp_path, 'echo "nothing is instrumented here"')

    with pytest.raises(AssertionError, match=str(launcher)):
        assert_instrument_run_call_carries_provenance(launcher)


def test_the_library_definition_and_source_lines_are_not_calls(tmp_path):
    launcher = _launcher(
        tmp_path,
        'INSTRUMENT_LIB="$CORE_DIR/tools/instrument_run.sh"',
        '  source "$INSTRUMENT_LIB"',
        'echo "instrument_run provider= model= effort= source="',
    )

    with pytest.raises(AssertionError, match="no instrument_run call"):
        assert_instrument_run_call_carries_provenance(launcher)


def test_every_call_in_the_file_is_held_to_the_rule(tmp_path):
    """Added beyond the instruction: a file with a second, bare call alongside a stamping one
    has a run that goes out unstamped."""
    launcher = _launcher(tmp_path, _FULL_CALL, "  instrument_run")

    with pytest.raises(AssertionError):
        assert_instrument_run_call_carries_provenance(launcher)


# --- the printed Telemetry: line ---------------------------------------------------------------

_TELEMETRY = (
    "Provider:  claude\n"
    "          Telemetry:    kensai.arm=cold-read,kensai.run_id=r-1,kensai.skill=s,"
    "kensai.project=p,kensai.product=q,kensai.provider=claude,kensai.source=default"
    " → http://127.0.0.1:9/v1\n"
)


def test_telemetry_pairs_reads_the_one_line_in_order_without_the_prefix():
    assert telemetry_pairs(_TELEMETRY) == [
        ("arm", "cold-read"),
        ("run_id", "r-1"),
        ("skill", "s"),
        ("project", "p"),
        ("product", "q"),
        ("provider", "claude"),
        ("source", "default"),
    ]


def test_telemetry_pairs_fails_when_no_line_carries_attributes():
    with pytest.raises(AssertionError, match="Telemetry"):
        telemetry_pairs("          Telemetry:    OTLP → http://x\n")


def test_the_stamp_passes_when_its_pairs_follow_the_named_existing_ones():
    assert_provenance_stamped(_TELEMETRY, provider="claude", source="default", after=("project",))


@pytest.mark.parametrize(
    "expected",
    [
        {"provider": "codex", "source": "default"},
        {"provider": "claude", "source": "tier"},
        {"provider": "claude", "model": "m", "source": "default"},
        {"provider": "claude", "effort": "high", "source": "default"},
        {"provider": "claude"},
    ],
    ids=["wrong-provider", "wrong-source", "unexpected-model", "unexpected-effort", "extra-source"],
)
def test_the_stamp_fails_on_any_pair_it_does_not_expect(expected):
    with pytest.raises(AssertionError):
        assert_provenance_stamped(_TELEMETRY, **expected)


def test_the_stamp_fails_when_a_provenance_pair_precedes_an_existing_one():
    reordered = _TELEMETRY.replace(
        "kensai.project=p,kensai.product=q,kensai.provider=claude",
        "kensai.provider=claude,kensai.project=p,kensai.product=q",
    )
    with pytest.raises(AssertionError, match="project"):
        assert_provenance_stamped(
            reordered, provider="claude", source="default", after=("project",)
        )



# --- the isolated host -------------------------------------------------------------------------


def test_an_isolated_host_puts_the_launcher_under_its_own_core_beside_the_named_tools(tmp_path):
    script = tmp_path / "src" / "demo" / "launcher.sh"
    script.parent.mkdir(parents=True)
    script.write_text("#!/usr/bin/env bash\n")
    copied = isolated_host(tmp_path / "host", script, tools=("skill_path.py",))

    assert copied == tmp_path / "host" / "core" / "launchers" / "demo" / "launcher.sh"
    assert copied.read_text() == "#!/usr/bin/env bash\n"
    copied_tools = sorted(p.name for p in (tmp_path / "host" / "core" / "tools").iterdir())
    assert copied_tools == ["skill_path.py"]
    assert (tmp_path / "host" / "pin.json").is_file()


def test_an_own_skill_is_placed_where_the_skill_resolver_finds_it(tmp_path):
    skill_dir = place_own_skill(tmp_path, "demo", "**Model:** m\n")

    assert skill_dir == tmp_path / ".claude" / "skills" / "demo"
    assert (skill_dir / "intelligence" / "claude.md").read_text() == "**Model:** m\n"
    assert not (place_own_skill(tmp_path, "bare") / "intelligence").exists()
