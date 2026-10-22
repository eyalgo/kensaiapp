#!/usr/bin/env python3
"""run_intelligence.py — the one resolution of a run's model, effort and source.

WHY THIS EXISTS

A launcher hands its run a model and an effort, and stamps the same three facts on the run's
telemetry (`run_telemetry.sh`'s `model=`, `effort=`, `source=`). Where they come from has one
precedence — the skill's `intelligence/` file, else a tier the caller named, else nothing — and
that precedence used to live inline in the skill launcher alone. Twelve launchers now need it, so
it lives here once, and a launcher hands its run and its stamp the one answer this prints: the
stamp and the run cannot disagree when there is only one resolution.

This composes the two readers that already exist and adds nothing to either: `intelligence.read`
reads one skill's file, `model_assignment.resolve` maps a tier to a provider's model. It reads no
environment and spawns nothing.

THE ORDER

1. A skill dir is given and has an `intelligence/` folder. A tier as well is refused, exit 6,
   whatever the folder holds — a file for the provider, none, or a malformed one: the folder is
   the skill declaring its own intelligence, and a tier must not silently win over it or lose to
   it. Otherwise the file answers (exit 0, `source=intelligence`), or its absence is exit 4 and
   its breakage exit 2, each on `intelligence.py`'s own stderr.
2. Else a tier is given: `model_assignment`'s answer (exit 0, `source=tier`, a null effort
   printed empty), or exit 5 on `model_assignment.py`'s own stderr.
3. Else exit 0, `source=default`, and an empty model and effort.

An absent folder is not a status of its own — `intelligence.py`'s exit 3 existed so a caller could
reach steps 2 and 3, which this performs itself. The folder's existence is read off what `read`
does (returns, raises, or answers `None`); the directory is never tested a second time.

THE COMMAND LINE

    run_intelligence.py --provider <claude|codex|gemini|hf|ollama>
                        [--skill-dir <dir>] [--tier <tier>]

On exit 0, stdout is exactly `model=<id or empty>`, `effort=<level or empty>`,
`source=<intelligence|tier|default>`, in that order. Exits: 0 · 2 malformed file · 4 missing file ·
5 unknown tier · 6 tier on a declared skill · 64 usage. A usage error takes 64 rather than
argparse's own 2, which would read as a malformed intelligence file to a launcher that `case`s on
the status.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum, IntEnum
from pathlib import Path
from typing import NoReturn

import intelligence
import model_assignment

__version__ = "1.3.2"

PROVIDERS = ("claude", "codex", "gemini", "hf", "ollama")


class Source(str, Enum):
    """Where a run's model and effort came from — the three values `kensai.source` carries."""

    INTELLIGENCE = "intelligence"
    TIER = "tier"
    DEFAULT = "default"


class Exit(IntEnum):
    """The statuses a launcher `case`s on. 2 and 4 are `intelligence.py`'s own."""

    OK = 0
    MALFORMED = 2
    MISSING_FILE = 4
    UNKNOWN_TIER = 5
    TIER_ON_DECLARED_SKILL = 6
    USAGE = 64


class TierOnDeclaredSkill(ValueError):
    """A tier was named for a skill whose `intelligence/` folder declares its own model. `main`
    converts it to exit 6; the skill launcher turns that status into its own refusal."""


@dataclass(frozen=True)
class Resolution:
    model: str
    effort: str
    source: Source


# The aliases are evaluated at import, which `from __future__ import annotations` does not defer, so
# the union is a string: a launcher run under a PATH that reaches macOS's /usr/bin/python3 (3.9,
# below the 3.13 floor, and still what every other tool a launcher calls imports under) would
# otherwise die here on `type | None` before answering.
ReadIntelligence = Callable[[Path, str], "intelligence.Intelligence | None"]
ResolveTier = Callable[[str, str], model_assignment.ModelAssignment]


def resolve(
    provider: str,
    *,
    skill_dir: Path | None,
    tier: str | None,
    read_intelligence: ReadIntelligence,
    resolve_tier: ResolveTier,
) -> Resolution:
    """The run's model, effort and source, in THE ORDER above. A reader's own exception
    propagates unchanged, except that any answer from an existing folder — a file, a missing one,
    a malformed one — becomes `TierOnDeclaredSkill` when a tier was also named."""
    if skill_dir is not None:
        try:
            found = read_intelligence(skill_dir, provider)
        except (intelligence.MissingIntelligence, intelligence.MalformedIntelligence):
            if tier is not None:
                raise _tier_refused(tier, skill_dir) from None
            raise
        if found is not None:
            if tier is not None:
                raise _tier_refused(tier, skill_dir)
            effort = found.effort.value if found.effort else ""
            return Resolution(found.model, effort, Source.INTELLIGENCE)
    if tier is not None:
        assignment = resolve_tier(provider, tier)
        return Resolution(assignment.model, assignment.reasoning_effort or "", Source.TIER)
    return Resolution("", "", Source.DEFAULT)


def _tier_refused(tier: str, skill_dir: Path) -> TierOnDeclaredSkill:
    return TierOnDeclaredSkill(
        f"tier {tier!r} is refused for {skill_dir} — its intelligence/ folder declares the run's "
        "model and effort, and a tier must not win over it or lose to it"
    )


class _Parser(argparse.ArgumentParser):
    """argparse, except that a usage error exits `Exit.USAGE` rather than 2."""

    def error(self, message: str) -> NoReturn:
        self.print_usage(sys.stderr)
        print(f"{self.prog}: error: {message}", file=sys.stderr)
        sys.exit(Exit.USAGE)


def parser() -> argparse.ArgumentParser:
    result = _Parser(
        prog="run_intelligence.py", description="Resolve a run's model, effort and source."
    )
    result.add_argument("--provider", required=True, choices=PROVIDERS)
    result.add_argument("--skill-dir", type=Path)
    result.add_argument("--tier")
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        resolution = resolve(
            args.provider,
            skill_dir=args.skill_dir,
            tier=args.tier,
            read_intelligence=intelligence.read,
            resolve_tier=model_assignment.resolve,
        )
    except TierOnDeclaredSkill as error:
        print(f"run-intelligence: {error}", file=sys.stderr)
        return Exit.TIER_ON_DECLARED_SKILL
    except (
        model_assignment.UnknownProvider,
        model_assignment.UnknownTier,
        model_assignment.NoModelForTier,
    ) as error:
        print(f"model-assignment: {error}", file=sys.stderr)
        return Exit.UNKNOWN_TIER
    except intelligence.MissingIntelligence as error:
        print(f"intelligence: {error}", file=sys.stderr)
        return Exit.MISSING_FILE
    except intelligence.MalformedIntelligence as error:
        print(f"intelligence: {error}", file=sys.stderr)
        return Exit.MALFORMED
    print(f"model={resolution.model}")
    print(f"effort={resolution.effort}")
    print(f"source={resolution.source.value}")
    return Exit.OK


if __name__ == "__main__":
    sys.exit(main())
