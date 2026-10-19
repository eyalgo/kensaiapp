#!/usr/bin/env python3
"""Refuse newly staged hardcoded paths to the resolved Kensaiapp core.

The repository still contains historical hardcoded references, so this is a forward-only gate:
it reads added staged lines rather than declaring the old tree clean.  Rules are exempt because
their paths are literal matching data; tests and historical records may contain worked examples.
Every other newly authored line reaches shared core through ``<CORE>``.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

__version__ = "1.1.0"

_LITERAL_CORE = re.compile(r"(?<![$A-Za-z0-9_])" + "core" + "/")
_HUNK = re.compile(r"^@@ -(?:\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@")


@dataclass(frozen=True)
class Hit:
    """One newly staged line that bypasses the resolved-core token."""

    path: str
    line: int
    text: str


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def _is_record(path: Path) -> bool:
    return (
        "evidence" in path.parts
        or path.name == "code-integrity-report.md"
        or ("references" in path.parts and path.name.endswith("_ratification_verdict.md"))
    )


def is_exempt(relative: str) -> bool:
    """Whether staged prose may legitimately contain the literal being checked."""
    path = Path(relative)
    return (
        path.name.startswith("test_")
        or path == Path("core") / "templates" / "change_request_template.md"
        or _is_record(path)
        or path.parts[:2] == ("core", "doctrine")
        or path.parts[:2] == (".claude", "rules")
    )


def staged_paths(repo: Path) -> list[str]:
    """Tracked destinations with staged content, including additions and renames."""
    output = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "-z", "--diff-filter=ACMR"],
        cwd=repo,
        capture_output=True,
        check=True,
    ).stdout.decode("utf-8", errors="surrogateescape")
    return sorted(path for path in output.split("\0") if path and not is_exempt(path))


def added_lines(repo: Path, relative: str) -> list[tuple[int, str]]:
    """New-side line numbers and text for additions in one staged patch."""
    patch = _git(
        repo,
        "diff",
        "--cached",
        "--unified=0",
        "--no-color",
        "--no-ext-diff",
        "--",
        relative,
    )
    result: list[tuple[int, str]] = []
    new_line: int | None = None
    for raw in patch.splitlines():
        hunk = _HUNK.match(raw)
        if hunk:
            new_line = int(hunk.group(1))
            continue
        if new_line is None:
            continue
        if raw.startswith("+"):
            result.append((new_line, raw[1:]))
            new_line += 1
        elif raw.startswith("-") or raw.startswith("\\"):
            continue
        else:
            new_line += 1
    return result


def scan_staged(repo: Path) -> list[Hit]:
    """Return every newly staged literal resolved-core path."""
    hits: list[Hit] = []
    for relative in staged_paths(repo):
        for line, text in added_lines(repo, relative):
            if _LITERAL_CORE.search(text):
                hits.append(Hit(relative, line, text.strip()))
    return hits


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Refuse newly staged paths that bypass the <CORE> indirection token."
    )
    result.add_argument("--repo", default=".", help="repository whose index is checked")
    result.add_argument("--staged", action="store_true", help="check added lines in the index")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if not args.staged:
        print("core-indirection: --staged is required", file=sys.stderr)
        return 2
    hits = scan_staged(Path(args.repo).resolve())
    for hit in hits:
        print(
            f"{hit.path}:{hit.line}: hardcoded resolved-core path; use <CORE>: {hit.text}",
            file=sys.stderr,
        )
    return 1 if hits else 0


if __name__ == "__main__":
    raise SystemExit(main())
