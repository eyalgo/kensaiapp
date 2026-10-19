#!/usr/bin/env python3
"""A file may not announce its own state, and may not claim what is unbuilt.

WHY THIS EXISTS
    `<CORE>/doctrine/governance/written_forward.md` owns the rule: a file states what is true now,
    and the story of how it got here lives in git. The rule is old and was enforced by hand — the
    same class of sentence was stripped out in `b21b2c0` ("Doctrine states the rule; git log holds
    why it was added") and in `be59b2f`, which removed three "not yet wired" markers as "a
    build-state claim with nothing keeping it honest as the state changed."

    It kept coming back, and a cold read said why
    (`system/projects/product-definition/docs/cdo-loader-coldread/global.md`): a defect that
    survives a rule aimed squarely at it is evidence the rule was written somewhere that does not
    bind. So the habit becomes a check.

    A build-state claim is the sharp case, because it is *accurate on the day it is written*. It
    goes false silently, and the session that finishes the work is not reading the three other
    files that describe it as unfinished — which is exactly how one station came to be called "not
    yet wired" in three places long after the role existed
    (`core/doctrine/setup/setting_up_a_project.md` § Which of these exist today).

WHAT COUNTS
    A curated phrase set, and nothing beyond it. The set is deliberately narrow: a pattern cannot
    tell a live constraint ("do not merge these two — they drift") from a story about an edit
    ("originally one file; we split it because it drifted"), and a pattern that tried would delete
    the reasoning the rule exists to preserve.

        status: stub · this is a stub
        not yet built / wired / written / implemented
        planned later · ⚠ not yet
        currently a stub · STUB · TBD

    The judgement half — rationale told as a story, a file describing how it was made, a date doing
    work in live prose — is `<CORE>/doctrine/kaizen/lenses/provenance.md`, run by an auditor.

WHERE IT LOOKS
    The files an agent loads in order to act. The rule binds every authored file, but a **record**
    — a trail entry, a parked station, a cold-read report, a proposal — exists to hold
    what was true at a moment, and "`X` is a stub" is the finding it was written to carry. Scanning
    records would contradict the doctrine's own carve-out and would drown the real hits: measured
    over the whole tree, the great majority of matches are findings *about* a file rather than a
    file describing itself. Those are the lens's to judge, one document at a time.

    The instance's own governing files are in that set and were missing from it until 2026-08-14:
    `system/doctrine/`, `system/projects/<name>/doctrine/` and `system/experience/`. A project's
    doctrine is loaded to act; the same project's `journey/` joined this set on 2026-09-01, but only
    its **live** half. The doctrine (`core/doctrine/governance/written_forward.md:108-110`) exempts a
    sentence *kind* — a record's job is recording what happened, and narrating its own maturity is
    not — not a folder, and a live seed or station narrating its own maturity is exactly that
    sentence. The owner ruled on 2026-08-31 that a live seed or station counts. *Live* is
    `check_journey_links.py`'s `_live_files()` — the seedbed roots, `unpicked/`, and open
    station roots, at both the instance and project layer — borrowed here by citation rather than
    restated. `trail/`, `drop/` and `parked/` stay out: a retired, killed or parked artifact is the record the
    carve-out protects, holding what was true at the moment it stopped moving — which is also why
    the project pattern stays positional rather than a prefix, and why it cannot be a substring test
    for `/doctrine/`: one project is *named* `doctrine`, and its retired seeds would come with it.

WHAT IS DELIBERATELY NOT A MATCH — use versus mention
    Quoting a phrase is not making the claim. Three forms are stripped before matching: a fenced
    code block, an inline code span, and a double-quoted span. Without this, the two files that
    *state* the rule fail it, and so does its owner:
    `core/doctrine/setup/setting_up_a_project.md` writes "not yet wired" inside the very sentence
    warning against it.

    A blockquote is NOT a mention. `core/roles/loaders/content_manager_global.md` puts its stub
    announcement in one, so exempting blockquotes would exempt the clearest violation in the repo.
    To show a sample of a document, fence it.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

__version__ = "1.4.3"

# What an agent loads in order to act. A record lives outside this set on purpose — see
# WHERE IT LOOKS above.
SCOPED_ROOTS = (
    "AGENTS.md",
    "CLAUDE.md",
    "kensaiapp.md",
    ".claude/agents/",
    ".claude/skills/",
    "skills/",
    "core/docs/",
    "core/doctrine/",
    "core/prompts/",
    "core/roles/",
    "core/templates/",
    "system/doctrine/",
    "system/experience/",
    "system/loaders/",
)

# A scoped root that cannot be written as a prefix. `system/projects/<name>/doctrine/` is in scope
# and `system/projects/<name>/journey/trail|parked/` is not, so the segment has to be matched
# positionally — and it must be the *third* segment. A substring test for "/doctrine/" would pull
# in the whole journey of the project that is itself named `doctrine`, whose retired half is a
# record.
#
# The live journey joined 2026-09-01 (owner's ruling, 2026-08-31) — a seedbed root, `unpicked/`, or
# an open station root, at the instance layer (`system/nemawashi/`, `system/shukuba/`) and the
# project layer (`system/projects/<name>/journey/{nemawashi,shukuba}/`). `check_journey_links.py`
# already fixes *live* to mean exactly this set (`:65-92`); these two patterns borrow it rather
# than restating it. `trail/`, `drop/` and `parked/` are excluded by construction: the only sub-folder
# either pattern admits is `unpicked/`, so a filename one level under any of the three carries an
# extra `/` the pattern's final `[^/]+\.md$` cannot cross. `drop/` therefore needs no code change
# here and is named anyway, because a list of the exclusions that is one short reads as a gap. `README.md` is excluded too — a folder's
# own description, not a seed.
#
# A seed is `<slug>.md` or a folder `<slug>/` holding `seed.md` plus, per reviewed unit (sealed or halted),
# `<key>_report.md` and `<key>_recommendations.md` (`kensaiapp_structure.md` § 2). Only `seed.md` is
# under this gate — the reports are records, out by the same "WHAT THIS DOES NOT TOUCH" carve-out
# a `trail/` entry is (§ *What this does not touch*, "The journey is the record"). Nemawashi-only:
# a station never takes the folder form, so the pattern below never admits `shukuba`. Because the
# filename is fixed to the literal `seed.md`, no `(?!README\.md$)` guard is needed — `README.md`
# can never match a pattern whose last segment is pinned to a different name.
#
# `(?!trail/|drop/)` guards the slug segment itself: without it, `nemawashi/trail/seed.md` — a
# file literally *named* `seed.md` sitting at `trail/`'s own root, the flat shape's edge case —
# would read `trail` as a folder-seed's slug and admit a `trail/` file this gate must keep out. The
# lookahead only excludes an exact `trail`/`drop` segment, so a slug that merely starts with either
# word (`trailblazer_seed/seed.md`) is unaffected.
_FOLDER_SEED_SLUG = r"(?:unpicked/)?(?!trail/|drop/)[^/]+/seed\.md$"

SCOPED_PATTERNS = (
    re.compile(r"^system/projects/[^/]+/doctrine/"),
    re.compile(r"^system/(?:nemawashi|shukuba)/(?:unpicked/)?(?!README\.md$)[^/]+\.md$"),
    re.compile(
        r"^system/projects/[^/]+/journey/(?:nemawashi|shukuba)/"
        r"(?:unpicked/)?(?!README\.md$)[^/]+\.md$"
    ),
    re.compile(rf"^system/nemawashi/{_FOLDER_SEED_SLUG}"),
    re.compile(rf"^system/projects/[^/]+/journey/nemawashi/{_FOLDER_SEED_SLUG}"),
)

# A record family sitting inside a scoped root — see WHERE IT LOOKS above. Excluded even when
# the file it belongs to is tracked and otherwise in scope.
RECORD_SEGMENTS = ("/evals/", "/evidence/", "/examples/")

PATTERNS = (
    re.compile(r"status:\s*stub", re.IGNORECASE),
    re.compile(r"\bthis\s+(?:\w+\s+)?(?:is|remains)\s+(?:a|still\s+a)\s+stub\b", re.IGNORECASE),
    re.compile(r"\bnot\s+yet\s+(?:built|wired|written|implemented)\b", re.IGNORECASE),
    re.compile(r"\bplanned\s+later\b", re.IGNORECASE),
    re.compile(r"⚠\s*not\s+yet\b", re.IGNORECASE),
    re.compile(r"\bcurrently\s+(?:a|still\s+a)\s+stub\b", re.IGNORECASE),
    # Case-sensitive by design: lowercase "stub" in scope is almost always a doctrine stub, a
    # directory stub, or a test stub. Uppercase STUB is a marker a file puts on itself.
    re.compile(r"\bSTUB\b"),
    # Case-sensitive by design: lowercase "tbd" is ordinary prose; uppercase TBD is the marker.
    re.compile(r"\bTBD\b"),
)

_INLINE_CODE = re.compile(r"`[^`]*`")
_DOUBLE_QUOTED = re.compile(r"[\"“][^\"“”]*[\"”]")
_FENCE = re.compile(r"^\s*(?:```|~~~)")


def in_scope(relative: str) -> bool:
    """True for a markdown file an agent loads in order to act; false for a record."""
    if not relative.endswith(".md"):
        return False
    if any(segment in relative for segment in RECORD_SEGMENTS):
        return False
    return relative.startswith(SCOPED_ROOTS) or any(
        pattern.match(relative) for pattern in SCOPED_PATTERNS
    )


def _mentions_stripped(line: str) -> str:
    """Drop the spans where a phrase is being quoted rather than claimed."""
    return _DOUBLE_QUOTED.sub(" ", _INLINE_CODE.sub(" ", line))


def violations_in(text: str) -> list[tuple[int, str]]:
    """1-based line numbers and stripped line text for every matching line."""
    hits: list[tuple[int, str]] = []
    in_fence = False
    for number, line in enumerate(text.splitlines(), start=1):
        if _FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        candidate = _mentions_stripped(line)
        if any(pattern.search(candidate) for pattern in PATTERNS):
            hits.append((number, line.strip()))
    return hits


# =========================================================================================
# The repo-facing half — three questions about a repo passed in as an argument, and the
# CLI both the `pre-commit` shim and the `PreToolUse` guard reach.
#
# The repo is a parameter. There is no module-level REPO: every satellite
# routes `core.hooksPath` to this instance's `core/githooks`, so
# the `pre-commit` shim runs from this core while git commits in theirs. A path derived
# from this module's own `__file__` would scan this repo and pass every commit made there.
# =========================================================================================


def scoped_markdown(repo) -> list[str]:
    """Tracked and untracked-not-ignored `.md` files in scope, under `repo`."""
    out = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard", "*.md"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return sorted({p for p in out.split("\0") if p and in_scope(p)})


def staged_markdown(repo) -> list[str]:
    """In-scope `.md` files added, copied or modified in the index — never a deletion.

    `--no-renames`: a staged rename then appears as its two halves, and the added path is
    read on its own (`commit_builder.py` makes the same choice, for the same reason).
    """
    out = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM", "--no-renames", "-z"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return [p for p in out.split("\0") if p and in_scope(p)]


def staged_text(repo, relative: str) -> str:
    """The index's copy of `relative` — what will actually be committed."""
    return subprocess.run(
        ["git", "show", f":{relative}"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def scan_tree(repo) -> dict[str, list[tuple[int, str]]]:
    """Every in-scope working-tree file's violations, keyed by relative path."""
    repo_path = Path(repo)
    found: dict[str, list[tuple[int, str]]] = {}
    for relative in scoped_markdown(repo):
        path = repo_path / relative
        if not path.is_file():
            continue
        hits = violations_in(path.read_text(encoding="utf-8"))
        if hits:
            found[relative] = hits
    return found


def scan_staged(repo) -> dict[str, list[tuple[int, str]]]:
    """Every in-scope staged file's violations, keyed by relative path — the index only."""
    found: dict[str, list[tuple[int, str]]] = {}
    for relative in staged_markdown(repo):
        hits = violations_in(staged_text(repo, relative))
        if hits:
            found[relative] = hits
    return found


WRITE_IT_FORWARD = (
    "Write it forward — name the capability in the present tense, or keep only the "
    "instruction the reader acts on. See <CORE>/doctrine/governance/written_forward.md."
)

# The two surfaces read different things, deliberately — and the message is where that is
# said, because the person it stops is the one who needs to know: the line they are shown
# can be one they did not write.
_WHOLE_BLOB = (
    "The whole staged file is read, not only the lines this commit changes — the "
    "`Edit|Write` guard reads the text being written, this reads what will land. So a "
    "clean edit to a file carrying older debt passes there and is refused here: that is "
    "the ratchet, and the file is clean once whoever stages it writes those lines forward."
)

_NO_VERIFY = (
    "Bypass with `git commit --no-verify` — the commit lands, and this file's debt is "
    "still there for the next person who stages it."
)


def _report(found: dict[str, list[tuple[int, str]]]) -> str:
    lines = [
        f"{path}:{number}: {text}"
        for path, hits in sorted(found.items())
        for number, text in hits
    ]
    total_lines = sum(len(hits) for hits in found.values())
    lines.append(f"{len(found)} files, {total_lines} lines")
    return "\n".join(lines)


def _show_toplevel(cwd: str | None = None) -> str:
    return subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="written_forward.py")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--staged", action="store_true", help="blocking — exit 1 on any hit")
    mode.add_argument("--report", action="store_true", help="never blocking — exit 0 always")
    parser.add_argument("--repo", help="defaults to `git rev-parse --show-toplevel` in cwd")
    args = parser.parse_args(argv)

    repo = args.repo or _show_toplevel()

    if args.report:
        print(_report(scan_tree(repo)))
        return 0

    found = scan_staged(repo)
    if not found:
        return 0
    offenses = "\n".join(
        f"{path}:{number}: {text}" for path, hits in sorted(found.items()) for number, text in hits
    )
    print(
        f"{offenses}\n\n{WRITE_IT_FORWARD}\n\n{_WHOLE_BLOB}\n\n{_NO_VERIFY}",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
