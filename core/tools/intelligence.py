#!/usr/bin/env python3
"""intelligence.py — the reader of one skill's intelligence: a model and an optional effort.

WHY THIS EXISTS

A chain run's intelligence is decided by the skill it runs, not by the role's agent file
(`core/doctrine/governance/skill_intelligence.md`). A skill declares it beside itself, in
`<skill dir>/intelligence/<provider>.md`, and every launcher that starts a run on a skill's
behalf reads it here — so what counts as a declaration, and what counts as a defect in one, is
decided once rather than once per launcher.

THE FILE

`**Model:** <the provider's exact model ID>` is required and is one token; in a `claude.md` it
must be a full Claude model ID — `claude-` and a version, never a floating alias (`opus`, `fable`,
`sonnet`, `haiku`). `**Effort:**` is `low`, `medium` or `high` — and, in a `claude.md` alone,
`xhigh` or `max` — and optional: absent or empty means no effort is passed. A field is the
first line that begins with its bold label, a trailing `<!-- … -->` stripped. Every other line is
prose for a reader and is never read.

THE THREE ANSWERS

The skill has no `intelligence/` folder: `read` returns `None`, and each caller decides what
absence means. The folder exists and holds no file for the provider: `MissingIntelligence`. The
file exists and breaks the rules above: `MalformedIntelligence`. Both name the file.

THE COMMAND LINE

    intelligence.py --skill-dir <dir> --provider <p>

prints `model=<id>` and `effort=<level, or empty>` and exits 0. Exit 3, with nothing printed: the
folder is absent. Exit 4, naming the missing file on stderr. Exit 2, naming the malformed file
and why on stderr. A shell launcher reads it through this form and `case`s on the status.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import agent_run

__version__ = "1.2.0"

INTELLIGENCE_DIR = "intelligence"

EXIT_OK = 0
EXIT_MALFORMED = 2
EXIT_NO_FOLDER = 3
EXIT_MISSING_FILE = 4

MODEL_LABEL = "Model"
EFFORT_LABEL = "Effort"
CLAUDE = "claude"
# A full Claude model ID: `claude-` and a name that carries a version digit.
_CLAUDE_MODEL_ID = re.compile(r"claude-(?=[a-z0-9.-]*[0-9])[a-z0-9.-]+")
_TRAILING_COMMENT = re.compile(r"\s*<!--.*-->\s*$")


class MissingIntelligence(ValueError):
    """The skill has an `intelligence/` folder and no file for the provider."""


class MalformedIntelligence(ValueError):
    """An intelligence file whose model or effort is not a legal declaration."""


@dataclass(frozen=True)
class Intelligence:
    model: str
    effort: agent_run.Effort | None
    path: Path


def _field(text: str, label: str) -> str | None:
    """The value of the first line beginning `**<label>:**`, its trailing comment stripped; `None`
    when no line does."""
    prefix = f"**{label}:**"
    for line in text.splitlines():
        if line.startswith(prefix):
            return _TRAILING_COMMENT.sub("", line[len(prefix):]).strip()
    return None


def _refuse_a_path(provider: str) -> None:
    if not provider or "/" in provider or "\\" in provider or provider.startswith("."):
        raise ValueError(
            f"provider {provider!r} is a path, not a provider name — "
            "intelligence/<provider>.md is joined onto a directory and must stay inside it"
        )


def read(skill_dir: str | Path, provider: str) -> Intelligence | None:
    """Read `<skill_dir>/intelligence/<provider>.md`; `None` when the skill has no
    `intelligence/` folder."""
    _refuse_a_path(provider)
    folder = Path(skill_dir) / INTELLIGENCE_DIR
    if not folder.is_dir():
        return None
    path = folder / f"{provider}.md"
    if not path.is_file():
        raise MissingIntelligence(f"no intelligence for provider {provider!r}: {path} is missing")
    text = path.read_text()

    model = _field(text, MODEL_LABEL)
    if not model or len(model.split()) != 1:
        raise MalformedIntelligence(
            f"{path}: **{MODEL_LABEL}:** must be exactly one token, got {model!r}"
        )
    if provider == CLAUDE and not _CLAUDE_MODEL_ID.fullmatch(model):
        raise MalformedIntelligence(
            f"{path}: **{MODEL_LABEL}:** must be a full Claude model ID (claude-…), "
            f"not an alias; got {model!r}"
        )
    effort_text = _field(text, EFFORT_LABEL)
    if not effort_text:
        return Intelligence(model, None, path)
    # Loaded here, where an effort is parsed: a skill that declares none — and a folder that is
    # absent — never loads the runner, so a launcher's own tests may stand a stub in its place.
    import agent_run

    legal = [
        level for level in agent_run.Effort
        if provider == CLAUDE or level not in agent_run.CLAUDE_ONLY_EFFORTS
    ]
    effort = next((level for level in legal if level.value == effort_text), None)
    if effort is None:
        raise MalformedIntelligence(
            f"{path}: **{EFFORT_LABEL}:** must be one of "
            f"{', '.join(level.value for level in legal)}, got {effort_text!r}"
        )
    return Intelligence(model, effort, path)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Read one skill's intelligence for a provider.")
    result.add_argument("--skill-dir", type=Path, required=True)
    result.add_argument("--provider", required=True)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        found = read(args.skill_dir, args.provider)
    except MissingIntelligence as error:
        print(f"intelligence: {error}", file=sys.stderr)
        return EXIT_MISSING_FILE
    except ValueError as error:
        print(f"intelligence: {error}", file=sys.stderr)
        return EXIT_MALFORMED
    if found is None:
        return EXIT_NO_FOLDER
    print(f"model={found.model}")
    print(f"effort={found.effort.value if found.effort else ''}")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
