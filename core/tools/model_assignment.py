#!/usr/bin/env python3
"""Resolve stable Kensaiapp model tiers for a concrete provider."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from typing import Sequence

__version__ = "2.3.0"

TIERS = ("fable", "opus", "sonnet", "haiku")


@dataclass(frozen=True)
class ModelAssignment:
    """One provider's concrete execution settings for a Kensaiapp tier."""

    model: str
    reasoning_effort: str | None = None


ASSIGNMENTS: dict[str, dict[str, ModelAssignment]] = {
    "claude": {
        "fable": ModelAssignment("fable"),
        "opus": ModelAssignment("opus"),
        "sonnet": ModelAssignment("sonnet"),
        "haiku": ModelAssignment("haiku"),
    },
    "codex": {
        "fable": ModelAssignment("gpt-5.6-sol", "xhigh"),
        "opus": ModelAssignment("gpt-5.6-sol", "high"),
        "sonnet": ModelAssignment("gpt-5.6-terra", "medium"),
        "haiku": ModelAssignment("gpt-5.6-luna", "low"),
    },
    "gemini": {
        "fable": ModelAssignment("gemini-3.1-pro-high", "high"),
        "opus": ModelAssignment("gemini-3.1-pro-low", "low"),
        "sonnet": ModelAssignment("gemini-3.8-flash-medium", "medium"),
        "haiku": ModelAssignment("gemini-3.8-flash-low", "low"),
    },
    # Hugging Face's router serves open models only, and names three slots, so
    # "fable" has no entry: resolve() refuses it by name rather than defaulting.
    "hf": {
        "opus": ModelAssignment("zai-org/GLM-5.3:novita"),
        "sonnet": ModelAssignment("MiniMaxAI/MiniMax-M3:novita"),
        "haiku": ModelAssignment("deepseek-ai/DeepSeek-V4.1-Flash:novita"),
    },
    # The owner's local Ollama models. A local model takes no reasoning effort, so none is set;
    # "fable" and "opus" share the largest model (owner's ruling, 2026-10-08).
    "ollama": {
        "fable": ModelAssignment("qwen3.8:27b"),
        "opus": ModelAssignment("qwen3.8:27b"),
        "sonnet": ModelAssignment("qwen3-coder:30b"),
        "haiku": ModelAssignment("qwen2.5-coder:14b"),
    },
}


class UnknownProvider(ValueError):
    pass


class UnknownTier(ValueError):
    pass


class NoModelForTier(ValueError):
    """A known tier that this provider's table assigns no model to."""


def resolve(provider: str, tier: str) -> ModelAssignment:
    """Return the concrete model settings for ``provider`` at ``tier``."""

    try:
        provider_assignments = ASSIGNMENTS[provider]
    except KeyError as error:
        available = ", ".join(sorted(ASSIGNMENTS))
        raise UnknownProvider(
            f"unknown provider {provider!r}; available providers: {available}"
        ) from error
    if tier not in TIERS:
        available = ", ".join(TIERS)
        raise UnknownTier(f"unknown model tier {tier!r}; available tiers: {available}")
    try:
        return provider_assignments[tier]
    except KeyError as error:
        raise NoModelForTier(
            f"provider {provider!r} has no model for tier {tier!r}"
        ) from error


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Resolve a Kensaiapp model tier for one provider."
    )
    result.add_argument("--provider", required=True)
    result.add_argument("--tier", required=True)
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        assignment = resolve(args.provider, args.tier)
    except (UnknownProvider, UnknownTier, NoModelForTier) as error:
        print(f"model-assignment: {error}", file=sys.stderr)
        return 2
    print(json.dumps(asdict(assignment), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
