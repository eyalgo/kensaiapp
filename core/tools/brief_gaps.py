#!/usr/bin/env python3
"""The ledger of what briefs left out — computed from the run reports, never maintained by hand.

`delegate_contract.md` § 5 already makes every delegated run write down *"A brief that was incomplete
— what it did not say, and what you had to reason out to proceed"*, and says why: *"absorbed
silently, the next run hits the same gap."* The reports exist. Nothing reads them, so every gap is
recorded once and lost.

**Why this is computed and not a file.** A hand-kept ledger is prose nobody is obliged to read — the
failure `delegate_contract.md` § *Sections* names for the report itself — and it drifts from the
reports the moment one is edited. It would also need a home the manifest does not grant:
`kensaiapp_structure.md` § App-level says the instance carries *"three things of its own at app
level"* — a bearing, a seedbed and a router station. Reading the reports needs no new home and cannot
drift from them.

Usage:  python3 <CORE>/tools/brief_gaps.py [--repo .]
"""

from __future__ import annotations

import argparse
import os
import re
from dataclasses import dataclass

__version__ = "1.1.0"

REPORT_NAME = "delegate-report.md"

# § 5 is written two ways across the 12 real reports — bold bullets and a two-column table — and
# none of them use the contract's prescribed "A brief that was incomplete" label. Matching the label
# found 2 gaps in 12 reports; the reports were not the problem. So both shapes are read, and an entry
# earns a row by *naming the brief*, which is how a run actually writes it: "Brief named no model
# tier", "Brief inherited two seed numbers", "The brief did not say where…".
_HEADING = re.compile(r"^#{2,4}\s")
_PROBLEMS = re.compile(r"^#{2,4}\s*\d*\.?\s*Problems hit", re.I)
_BULLET = re.compile(r"^\s*[-*]\s*\*\*(?P<title>[^*]+)\*\*\s*[—-]?\s*(?P<rest>.*)$")
_ROW = re.compile(r"^\s*\|\s*\*\*(?P<title>[^*]+)\*\*\s*\|(?P<rest>.*)\|\s*$")
_MENTIONS_BRIEF = re.compile(r"\bbrief\b", re.I)
_NO_TIER = re.compile(r"brief (?:named|carried) no (?:model )?tier", re.I)
_SKIP = re.compile(r"\bno gap found\b", re.I)


@dataclass(frozen=True)
class Gap:
    report: str
    kind: str   # "no-tier" | "incomplete"
    text: str


# A nested checkout holds a whole second copy of the tree, reports included, so walking into one
# counts every report twice — and a checkout whose worktree was pruned keeps serving the state it
# died in, which is worse than a duplicate because it is stale. Measured 2026-09-03 in this repo:
# 486 reports found, 359 of them inside nested checkouts. Both live worktrees (`.claude/worktrees/`)
# and the older top-level `.worktrees/` are skipped by directory name.
_SKIP_DIRS = frozenset({".git", "node_modules", "__pycache__", ".worktrees", "worktrees"})


def reports_in(repo: str) -> list[str]:
    found = []
    for dirpath, dirnames, filenames in os.walk(repo):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
        if REPORT_NAME in filenames:
            found.append(os.path.join(dirpath, REPORT_NAME))
    return sorted(found)


def _problem_entries(text: str) -> list[str]:
    """Every § 5 entry, in either shape it is written in. Stops at the next heading, so § 6's
    surfaced-not-settled list is not swept in with it."""
    entries, inside = [], False
    for line in text.splitlines():
        if _PROBLEMS.match(line):
            inside = True
            continue
        if inside and _HEADING.match(line):
            break
        if not inside:
            continue
        match = _BULLET.match(line) or _ROW.match(line)
        if match:
            entries.append(f"{match.group('title').strip()} — {match.group('rest').strip()}".strip(" —"))
    return entries


def gaps_in_report(path: str) -> list[Gap]:
    try:
        text = open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return []
    gaps = []
    if _NO_TIER.search(text):
        gaps.append(Gap(path, "no-tier", "the brief named no model tier"))
    for entry in _problem_entries(text):
        if _SKIP.search(entry) or not _MENTIONS_BRIEF.search(entry):
            continue
        if _NO_TIER.search(entry):
            continue  # already recorded once, from wherever the report put it
        gaps.append(Gap(path, "incomplete", entry))
    return gaps


def gaps_in(repo: str) -> list[Gap]:
    """The ledger: what briefs left out. Brief-scoped on purpose — its reader is about to write one,
    and a truncating `Read` is not their problem."""
    return [gap for report in reports_in(repo) for gap in gaps_in_report(report)]


def routable_in(repo: str) -> list[Gap]:
    """The wider set routing works on: every brief gap, plus any § 5 entry a routing rule claims even
    though it never names a brief. The `task_map` entries are exactly that — a run reporting that
    doctrine could not be reached is not describing a briefing failure, and it is the case a
    brief-scoped ledger would bury."""
    found = gaps_in(repo)
    seen = {(g.report, g.text) for g in found}
    for report in reports_in(repo):
        try:
            text = open(report, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        for entry in _problem_entries(text):
            if _SKIP.search(entry) or (report, entry) in seen:
                continue
            if any(matcher.search(entry) for matcher, _, _ in _RULES if not _MENTIONS_BRIEF.search(entry)):
                found.append(Gap(report, "routed-elsewhere", entry))
                seen.add((report, entry))
    return found


# ── routing ────────────────────────────────────────────────────────────────
# A ledger only earns its keep if rows leave it. Each rule below names who owns a gap's fix, and
# `closed` marks the ones a gate already catches — those are history, not work. The `task_map` rule
# is the one that matters most: several real reports record "no row for this", which is a
# doctrine-routing defect, and a ledger with no routing would file it under "briefing".

_GUARD = ".claude/hooks/brief_anchor_guard.py"
_STEP4 = "`agent-invoke` § Step 4"

_RULES = (
    # (matcher, owner, closed)
    (re.compile(r"line numbers?\b.*\bstale|stale\b.*\bline numbers?|citation", re.I), _GUARD, True),
    (re.compile(r"not (?:reachable|granted)|could not reach|no access to", re.I), _GUARD, True),
    (re.compile(r"task[_ ]map", re.I), "`<CORE>/doctrine/task_map.md` — not the brief", False),
)


@dataclass(frozen=True)
class Route:
    owner: str
    closed: bool
    why: str = ""


def route(gap: Gap, repeats: int = 1) -> Route:
    if gap.kind == "no-tier":
        return Route(_GUARD, True, "the guard refuses a no-pin agent's brief that names no tier")
    for matcher, owner, closed in _RULES:
        if matcher.search(gap.text):
            return Route(owner, closed, "matched a standing rule")
    if repeats > 1:
        return Route(_STEP4, False, f"seen in {repeats} runs — a repeat is a spec defect")
    return Route("", False, "seen once, fits no rule — left for a second sighting")


def route_all(gaps: list[Gap]) -> list[tuple[Gap, Route]]:
    counts: dict[str, int] = {}
    for gap in gaps:
        counts[gap.text] = counts.get(gap.text, 0) + 1
    return [(gap, route(gap, counts[gap.text])) for gap in gaps]


def render_routed(routed: list[tuple[Gap, Route]]) -> str:
    closed = [(g, r) for g, r in routed if r.closed]
    open_ = [(g, r) for g, r in routed if not r.closed]
    out = []
    if open_:
        out.append("## Open — these still cost a run\n")
        out.append("| gap | owner | why | report |")
        out.append("|---|---|---|---|")
        for gap, r in open_:
            owner = r.owner or "*unrouted*"
            out.append(f"| {gap.text.replace('|', chr(92) + '|')} | {owner} | {r.why} | `{gap.report}` |")
        out.append("")
    if closed:
        out.append("## Closed — a gate already catches these\n")
        out.append("| gap | closed by | report |")
        out.append("|---|---|---|")
        for gap, r in closed:
            out.append(f"| {gap.text.replace('|', chr(92) + '|')} | `{r.owner}` | `{gap.report}` |")
        out.append("")
    return "\n".join(out) if out else "No brief gaps recorded in any run report.\n"


def render(gaps: list[Gap]) -> str:
    """A table, one row per gap, newest first — never paragraphs. A ledger that invites prose gets
    prose, and prose is what nobody reads."""
    if not gaps:
        return "No brief gaps recorded in any run report.\n"
    rows = ["| gap | kind | report |", "|---|---|---|"]
    for gap in reversed(gaps):
        text = gap.text.replace("|", "\\|")
        rows.append(f"| {text} | {gap.kind} | `{gap.report}` |")
    return "\n".join(rows) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="brief_gaps.py",
        description="What briefs left out, read off every delegate-report.md in the repo.",
    )
    parser.add_argument("--repo", default=".", help="repo to scan (default: cwd)")
    parser.add_argument(
        "--route",
        action="store_true",
        help="say who owns each gap's fix, and which are already closed by a gate",
    )
    args = parser.parse_args()
    if args.route:
        print(render_routed(route_all(routable_in(args.repo))), end="")
    else:
        print(render(gaps_in(args.repo)), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
