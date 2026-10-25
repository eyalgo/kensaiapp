#!/usr/bin/env python3
"""check_brief_quotes.py — name every citation in a brief file whose quoted text is not at its lines.

A brief cites a file as `path:L12-L20 "the sentence that is actually there"`. A skill that reads the
brief builds on those quotes, so a quote that is not at its lines grounds its output in text nobody
wrote there. `seeds-from-idea` runs this on its brief before it cuts, and `ad-hoc-plan` before
it plans, and each stops on any line it prints.

The check is `.claude/hooks/brief_anchor_guard.py`'s, the one `agent-invoke`'s briefs pass at spawn
time; this file reaches it rather than copying it, so both read citations the same way. It asserts
only what that guard can prove: a path it cannot resolve is skipped, never reported.

Usage: check_brief_quotes.py <brief> [--root <dir>]
  <brief>   the brief file
  --root    the directory a relative citation resolves against (default: the current directory)

Exit codes: 0 every resolvable citation holds its quote; 1 one or more do not, each printed on its
own line; 2 the brief or the guard could not be read. It always ends with one line on stderr counting
the citations it checked and the ones it skipped as unresolvable, so a run against the wrong root —
every citation skipped — is visible rather than a silent pass.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import sys

__version__ = "1.0.1"


def _guard_path() -> str:
    """The guard beside the host's `core/`: this file sits at `<host>/core/tools/`."""
    host = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    return os.path.join(host, ".claude", "hooks", "brief_anchor_guard.py")


def _load_guard(path: str):
    spec = importlib.util.spec_from_file_location("brief_anchor_guard", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_NO_QUOTE = "cited with no quoted text"
_NO_QUOTE_HINT = (
    " (the check reads a quote only in the 300 characters after its citation and not across a blank"
    " line: keep it on the citation's line and under about 250 characters, eliding with … if needed)"
)


def check(text: str, root: str, guard_path: str | None = None) -> tuple[list[str], int, int]:
    """(problems, citations, resolved): one line per citation whose quote is not at its lines, how
    many citations the brief holds, and how many of them resolve to a file under `root` — the rest
    are skipped, so a count of zero resolved says the check proved nothing."""
    guard = _load_guard(guard_path or _guard_path())
    citations = [m.group("path") for m in guard._CITATION.finditer(text)]
    resolved = sum(1 for path in citations if guard._resolve(path, root) is not None)
    found = [
        line + _NO_QUOTE_HINT if line.endswith(_NO_QUOTE + ", so nothing here can be checked") else line
        for line in guard._citation_problems(text, root)
    ]
    return found, len(citations), resolved


def problems(text: str, root: str, guard_path: str | None = None) -> list[str]:
    """One line per citation whose quote is not at its lines."""
    return check(text, root, guard_path)[0]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("brief")
    parser.add_argument("--root", default=os.getcwd())
    args = parser.parse_args(argv)
    try:
        text = open(args.brief, encoding="utf-8").read()
        found, citations, resolved = check(text, args.root)
    except (OSError, ImportError, AttributeError) as exc:
        print(f"check_brief_quotes: cannot check {args.brief}: {exc}", file=sys.stderr)
        return 2
    for line in found:
        print(line)
    print(
        f"{citations} citations: {resolved} checked against {args.root}, "
        f"{citations - resolved} skipped as unresolvable",
        file=sys.stderr,
    )
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
