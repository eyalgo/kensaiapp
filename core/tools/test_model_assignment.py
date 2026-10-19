"""Contract tests for provider-specific model assignment."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

import model_assignment

_SCRIPT = Path(__file__).resolve().parent / "model_assignment.py"


def test_claude_tiers_resolve_to_the_existing_family_names():
    for tier in model_assignment.TIERS:
        assert model_assignment.resolve("claude", tier) == (
            model_assignment.ModelAssignment(tier)
        )


def test_codex_tiers_resolve_to_model_and_reasoning_effort():
    assert {
        tier: model_assignment.resolve("codex", tier)
        for tier in model_assignment.TIERS
    } == {
        "fable": model_assignment.ModelAssignment("gpt-5.6-sol", "xhigh"),
        "opus": model_assignment.ModelAssignment("gpt-5.6-sol", "high"),
        "sonnet": model_assignment.ModelAssignment("gpt-5.6-terra", "medium"),
        "haiku": model_assignment.ModelAssignment("gpt-5.6-luna", "low"),
    }


def test_gemini_tiers_resolve_to_model_and_reasoning_effort():
    assert {
        tier: model_assignment.resolve("gemini", tier)
        for tier in model_assignment.TIERS
    } == {
        "fable": model_assignment.ModelAssignment("gemini-3.1-pro-high", "high"),
        "opus": model_assignment.ModelAssignment("gemini-3.1-pro-low", "low"),
        "sonnet": model_assignment.ModelAssignment("gemini-3.8-flash-medium", "medium"),
        "haiku": model_assignment.ModelAssignment("gemini-3.8-flash-low", "low"),
    }


def test_unknown_provider_and_tier_are_rejected_plainly():
    for provider, tier, message in (
        ("other", "opus", "unknown provider 'other'"),
        ("codex", "other", "unknown model tier 'other'"),
    ):
        try:
            model_assignment.resolve(provider, tier)
        except ValueError as error:
            assert message in str(error)
        else:
            raise AssertionError(f"accepted {provider=}, {tier=}")


def test_cli_prints_the_resolved_assignment_as_json():
    result = subprocess.run(
        [
            sys.executable,
            str(_SCRIPT),
            "--provider",
            "codex",
            "--tier",
            "opus",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {
        "model": "gpt-5.6-sol",
        "reasoning_effort": "high",
    }


def _run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *arguments],
        text=True,
        capture_output=True,
        check=False,
    )


def test_a_known_tier_the_provider_does_not_assign_is_refused_by_name():
    with pytest.raises(model_assignment.NoModelForTier) as refusal:
        model_assignment.resolve("hf", "fable")

    assert str(refusal.value) == "provider 'hf' has no model for tier 'fable'"


def test_cli_refuses_an_unassigned_tier_by_name():
    result = _run_cli("--provider", "hf", "--tier", "fable")

    assert result.stdout == ""
    assert result.stderr.strip() == (
        "model-assignment: provider 'hf' has no model for tier 'fable'"
    )
    assert result.returncode == 2


def test_cli_keeps_the_unknown_tier_refusal_for_hf():
    result = _run_cli("--provider", "hf", "--tier", "ultra")

    assert result.stdout == ""
    assert result.stderr.strip() == (
        "model-assignment: unknown model tier 'ultra'; "
        "available tiers: fable, opus, sonnet, haiku"
    )
    assert result.returncode == 2


def test_cli_resolves_an_hf_tier():
    result = _run_cli("--provider", "hf", "--tier", "sonnet")

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["model"] == (
        model_assignment.ASSIGNMENTS["hf"]["sonnet"].model
    )


def test_cli_unknown_provider_lists_ollama():
    result = _run_cli("--provider", "not-real", "--tier", "opus")

    assert result.stdout == ""
    assert result.stderr.strip() == (
        "model-assignment: unknown provider 'not-real'; "
        "available providers: claude, codex, gemini, hf, ollama"
    )
    assert result.returncode == 2


_OLLAMA_MODELS = {
    "fable": "qwen3.8:27b",
    "opus": "qwen3.8:27b",
    "sonnet": "qwen3-coder:30b",
    "haiku": "qwen2.5-coder:14b",
}


@pytest.mark.parametrize("tier", model_assignment.TIERS)
def test_every_tier_resolves_to_a_local_model_on_ollama(tier):
    assignment = model_assignment.resolve("ollama", tier)

    claude_models = {a.model for a in model_assignment.ASSIGNMENTS["claude"].values()}
    assert assignment.model == _OLLAMA_MODELS[tier]
    assert assignment.reasoning_effort is None
    assert assignment.model not in claude_models
    assert "claude" not in assignment.model.lower()


def test_cli_resolves_the_fable_tier_on_ollama():
    result = _run_cli("--provider", "ollama", "--tier", "fable")

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["model"] == "qwen3.8:27b"
