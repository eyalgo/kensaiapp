"""Tests for `run_intelligence.py` — the one resolution of a run's model, effort and source.

The order under test is the design's (change_design.md § Sub-job A): a skill's `intelligence/`
folder first, then a named tier through `model_assignment`, then `default`. The command line is
what every launcher calls, so most cases drive it as a subprocess and compare its stderr byte for
byte with the reader it re-raises; the function is driven directly where the readers it is given
are the point.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

import intelligence
import model_assignment
import run_intelligence

_SCRIPT = Path(__file__).resolve().parent / "run_intelligence.py"
_INTELLIGENCE = Path(__file__).resolve().parent / "intelligence.py"
_MODEL_ASSIGNMENT = Path(__file__).resolve().parent / "model_assignment.py"

_SOURCES = {"intelligence", "tier", "default"}


def _run(*args: str | Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *map(str, args)], capture_output=True, text=True
    )


def _skill_with(tmp_path: Path, provider: str, text: str) -> Path:
    skill_dir = tmp_path / "some-skill"
    (skill_dir / "intelligence").mkdir(parents=True)
    (skill_dir / "intelligence" / f"{provider}.md").write_text(text)
    return skill_dir


def _answer(result: subprocess.CompletedProcess) -> dict[str, str]:
    lines = result.stdout.splitlines()
    return dict(line.split("=", 1) for line in lines)


def _good(tmp_path: Path) -> Path:
    return _skill_with(tmp_path, "claude", "**Model:** claude-opus-5-5\n**Effort:** high\n")


def _missing(tmp_path: Path) -> Path:
    return _skill_with(tmp_path, "codex", "**Model:** gpt-6-luna\n")


def _malformed(tmp_path: Path) -> Path:
    return _skill_with(tmp_path, "claude", "**Model:** opus\n")


# --- exit 0: the three sources ----------------------------------------------------------------


def test_intelligence_file_gives_model_effort_and_source_intelligence(tmp_path):
    result = _run("--provider", "claude", "--skill-dir", _good(tmp_path))

    assert result.returncode == 0, result.stderr
    assert _answer(result) == {
        "model": "claude-opus-5-5", "effort": "high", "source": "intelligence",
    }
    assert result.stderr == ""


def test_intelligence_file_without_an_effort_gives_an_empty_effort(tmp_path):
    skill_dir = _skill_with(tmp_path, "claude", "**Model:** claude-haiku-5\n")

    result = _run("--provider", "claude", "--skill-dir", skill_dir)

    assert result.returncode == 0, result.stderr
    assert _answer(result) == {"model": "claude-haiku-5", "effort": "", "source": "intelligence"}


def test_absent_intelligence_folder_and_no_tier_is_default_with_an_empty_pair(tmp_path):
    skill_dir = tmp_path / "bare-skill"
    skill_dir.mkdir()

    result = _run("--provider", "claude", "--skill-dir", skill_dir)

    assert result.returncode == 0, result.stderr
    assert _answer(result) == {"model": "", "effort": "", "source": "default"}


def test_a_skill_dir_that_does_not_exist_is_default(tmp_path):
    """Added beyond the instruction: a launcher hands over a path it resolved, but nothing stops
    that path from being gone by the time the resolver reads it. No folder is no folder."""
    result = _run("--provider", "claude", "--skill-dir", tmp_path / "nowhere")

    assert result.returncode == 0, result.stderr
    assert _answer(result) == {"model": "", "effort": "", "source": "default"}


@pytest.mark.parametrize(("provider", "model", "effort"), [
    ("claude", "sonnet", ""),
    ("codex", "gpt-5.6-terra", "medium"),
])
def test_absent_folder_with_a_tier_is_tier_with_the_assignment_answer(
    tmp_path, provider, model, effort
):
    skill_dir = tmp_path / "bare-skill"
    skill_dir.mkdir()

    result = _run("--provider", provider, "--skill-dir", skill_dir, "--tier", "sonnet")

    assert result.returncode == 0, result.stderr
    assert _answer(result) == {"model": model, "effort": effort, "source": "tier"}


def test_no_skill_dir_with_a_tier_is_tier():
    result = _run("--provider", "claude", "--tier", "fable")

    assert result.returncode == 0, result.stderr
    assert _answer(result) == {"model": "fable", "effort": "", "source": "tier"}


def test_no_skill_dir_and_no_tier_is_default():
    """Added beyond the instruction: the call cold-read and launch-eval-fix make — a provider
    and nothing else."""
    result = _run("--provider", "codex")

    assert result.returncode == 0, result.stderr
    assert _answer(result) == {"model": "", "effort": "", "source": "default"}


# --- the refusals, each with the reader's own stderr -----------------------------------------


def test_unknown_tier_exits_5_with_model_assignments_exact_stderr():
    reference = subprocess.run(
        [sys.executable, str(_MODEL_ASSIGNMENT), "--provider", "claude", "--tier", "gpt"],
        capture_output=True, text=True,
    )

    result = _run("--provider", "claude", "--tier", "gpt")

    assert result.returncode == 5
    assert result.stdout == ""
    assert reference.stderr.startswith("model-assignment: unknown model tier 'gpt'")
    assert result.stderr == reference.stderr


@pytest.mark.parametrize("make_skill", [_good, _missing, _malformed],
                         ids=["good", "missing", "malformed"])
def test_folder_plus_tier_exits_6_for_a_good_a_missing_and_a_malformed_file(
    tmp_path, make_skill
):
    result = _run("--provider", "claude", "--skill-dir", make_skill(tmp_path), "--tier", "sonnet")

    assert result.returncode == 6
    assert result.stdout == ""
    assert len(result.stderr.splitlines()) == 1
    assert result.stderr.startswith("run-intelligence: ")


def test_a_folder_plus_an_unknown_tier_is_still_exit_6(tmp_path):
    """Added beyond the instruction: exit 6 is decided before the tier is looked up, so a tier
    that does not exist on a declared skill is the declared-skill refusal, not exit 5. The skill
    launcher never reaches this — it refuses an unknown tier before resolving the skill — but the
    resolver's own order must not depend on its caller's."""
    result = _run("--provider", "claude", "--skill-dir", _good(tmp_path), "--tier", "gpt")

    assert result.returncode == 6


def test_missing_provider_file_exits_4_with_intelligence_exact_stderr(tmp_path):
    skill_dir = _missing(tmp_path)
    reference = subprocess.run(
        [sys.executable, str(_INTELLIGENCE), "--skill-dir", str(skill_dir),
         "--provider", "claude"],
        capture_output=True, text=True,
    )

    result = _run("--provider", "claude", "--skill-dir", skill_dir)

    assert reference.returncode == 4
    assert result.returncode == 4
    assert result.stdout == ""
    assert result.stderr == reference.stderr


def test_malformed_file_exits_2_with_intelligence_exact_stderr(tmp_path):
    skill_dir = _malformed(tmp_path)
    reference = subprocess.run(
        [sys.executable, str(_INTELLIGENCE), "--skill-dir", str(skill_dir),
         "--provider", "claude"],
        capture_output=True, text=True,
    )

    result = _run("--provider", "claude", "--skill-dir", skill_dir)

    assert reference.returncode == 2
    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == reference.stderr


# --- the shape of every answer ---------------------------------------------------------------


def _every_exit_zero_call(tmp_path: Path) -> list[list[str | Path]]:
    bare = tmp_path / "bare"
    bare.mkdir()
    return [
        ["--provider", "claude", "--skill-dir", _good(tmp_path)],
        ["--provider", "claude", "--skill-dir", bare],
        ["--provider", "codex", "--skill-dir", bare, "--tier", "haiku"],
        ["--provider", "gemini", "--tier", "opus"],
        ["--provider", "claude"],
    ]


def test_stdout_is_exactly_three_lines_on_every_exit_zero_path(tmp_path):
    for args in _every_exit_zero_call(tmp_path):
        result = _run(*args)

        assert result.returncode == 0, (args, result.stderr)
        keys = [line.split("=", 1)[0] for line in result.stdout.splitlines()]
        assert keys == ["model", "effort", "source"], (args, result.stdout)
        assert result.stdout.endswith("\n")


def test_source_is_always_one_of_the_three_values(tmp_path):
    seen = set()
    for args in _every_exit_zero_call(tmp_path):
        source = _answer(_run(*args))["source"]
        assert source in _SOURCES, (args, source)
        seen.add(source)

    assert seen == _SOURCES
    assert {member.value for member in run_intelligence.Source} == _SOURCES


@pytest.mark.parametrize("args", [
    [],
    ["--tier", "sonnet"],
    ["--provider", "claude", "--model", "opus"],
    ["--provider", "not-a-provider"],
    ["--provider", "claude", "--entry", "reviewer"],
    ["--provider", "claude", "--entry", "runner"],
], ids=["no provider", "missing provider", "unknown option", "unknown provider", "unknown entry",
        "the retired runner entry"])
def test_a_usage_error_never_exits_0_2_4_5_or_6(args):
    result = _run(*args)

    assert result.returncode not in (0, 2, 4, 5, 6)
    assert result.returncode == run_intelligence.Exit.USAGE
    assert result.stdout == ""
    assert "usage:" in result.stderr


# --- the readers are handed in ---------------------------------------------------------------


def test_the_resolver_is_given_its_two_readers(tmp_path):
    calls = []

    def read_intelligence(skill_dir, provider):
        calls.append(("read", skill_dir, provider))
        return intelligence.Intelligence("stub-model", None, Path(skill_dir) / "x.md")

    def resolve_tier(provider, tier):
        calls.append(("tier", provider, tier))
        return model_assignment.ModelAssignment("stub-tier-model", "low")

    from_file = run_intelligence.resolve(
        "claude", skill_dir=tmp_path, tier=None,
        read_intelligence=read_intelligence, resolve_tier=resolve_tier,
    )
    from_tier = run_intelligence.resolve(
        "codex", skill_dir=None, tier="opus",
        read_intelligence=read_intelligence, resolve_tier=resolve_tier,
    )

    source = run_intelligence.Source
    assert from_file == run_intelligence.Resolution("stub-model", "", source.INTELLIGENCE)
    assert from_tier == run_intelligence.Resolution("stub-tier-model", "low", source.TIER)
    assert calls == [("read", tmp_path, "claude"), ("tier", "codex", "opus")]


def test_a_reader_that_answers_none_falls_through_to_the_tier(tmp_path):
    """Added beyond the instruction: the folder's absence is `read` returning None — the resolver
    never looks at the directory a second time (design § 4, Sub-job A hint)."""
    resolution = run_intelligence.resolve(
        "claude", skill_dir=tmp_path, tier="haiku",
        read_intelligence=lambda *_: None,
        resolve_tier=lambda provider, tier: model_assignment.ModelAssignment(tier),
    )

    assert resolution == run_intelligence.Resolution("haiku", "", run_intelligence.Source.TIER)


def test_a_folder_plus_a_tier_raises_before_the_tier_is_resolved(tmp_path):
    def resolve_tier(provider, tier):
        raise AssertionError("the tier must not be resolved on a declared skill")

    def read_intelligence(*_):
        raise intelligence.MalformedIntelligence("broken")

    with pytest.raises(run_intelligence.TierOnDeclaredSkill):
        run_intelligence.resolve(
            "claude", skill_dir=tmp_path, tier="sonnet",
            read_intelligence=read_intelligence, resolve_tier=resolve_tier,
        )


# --- hf: a fourth provider, with no `fable` model --------------------------------------------------


def test_hf_tier_resolves():
    result = _run("--provider", "hf", "--tier", "opus")

    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        f"model={model_assignment.ASSIGNMENTS['hf']['opus'].model}",
        "effort=",
        "source=tier",
    ]


def test_hf_fable_is_refused_by_name_with_exit_5():
    result = _run("--provider", "hf", "--tier", "fable")

    assert result.returncode == 5
    assert result.stdout == ""
    assert result.stderr.strip() == (
        "model-assignment: provider 'hf' has no model for tier 'fable'"
    )


# --- ollama: a fifth provider, with a local model in every tier -------------------------------


def test_ollama_tier_resolves():
    result = _run("--provider", "ollama", "--tier", "opus")

    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        "model=qwen3.8:27b",
        "effort=",
        "source=tier",
    ]
