"""Tests for `brief_gaps.py` — the ledger of what briefs left out, read off the run reports.

`delegate_contract.md` § 5 already makes every run write *"A brief that was incomplete — what it did
not say"*, and warns: *"absorbed silently, the next run hits the same gap."* Twelve reports carry
those entries and nothing reads them.

This is a **computed** ledger, not a maintained one. A hand-kept list is prose nobody is obliged to
read — the exact failure `delegate_contract.md` § Sections names for the report itself — and it would
also need a home the manifest does not allow: `kensaiapp_structure.md` § App-level says the instance
carries *"three things of its own at app level"*. Reading the reports needs no new home and cannot
drift from them.
"""

from pathlib import Path

import brief_gaps

# Both fixtures use the shapes the 12 real reports actually use — bold bullets in one, a table in
# the other — not the contract's prescribed "A brief that was incomplete" label, which no report
# writes. A parser built on the label found 2 gaps in 12 reports; the reports were not the problem.

_REPORT = """# Run report — a thing

## 1. Assignment

Model: Opus 5. **The brief named no tier.**

## 5. Problems hit

- **A tool I could not reach** — `mcp__reddit` was named and not granted; used web search instead.
- **The brief did not say where the output lands** — reasoned it into `docs/`, which may be wrong.
- **A stale path in the seed** — cost a detour; nothing to do with the briefing.

## 6. Surfaced, not settled

- something else
"""

_SECOND = """# Run report — another thing

## 5. Problems hit

| Problem | Detail |
|---|---|
| **Brief inherited two seed numbers** | The seed's figure restated as the job's premise |
| **`Read` truncated the manifest** | 27,097 tokens against a 25,000 cap. Paged the remainder |

## 7. Commits

- abc1234
"""


def _reports(tmp_path: Path, *bodies: str) -> Path:
    root = tmp_path / "repo"
    for index, body in enumerate(bodies):
        folder = root / "docs" / "proposals" / f"run-{index}"
        folder.mkdir(parents=True)
        (folder / "delegate-report.md").write_text(body)
    return root


def test_it_finds_every_report(tmp_path):
    root = _reports(tmp_path, _REPORT, _SECOND)
    assert len(brief_gaps.reports_in(str(root))) == 2


def test_only_the_entries_that_are_about_the_brief_count(tmp_path):
    """§ 5 collects every problem a run hit. Most are not the brief's fault — an unreachable tool, a
    stale path, a truncating Read. The ledger is about briefs, so an entry earns its row by naming
    one."""
    root = _reports(tmp_path, _REPORT)
    gaps = [g for g in brief_gaps.gaps_in(str(root)) if g.kind == "incomplete"]
    assert len(gaps) == 1
    assert "where the output lands" in gaps[0].text
    joined = " ".join(g.text for g in gaps)
    assert "stale path" not in joined and "mcp__reddit" not in joined


def test_a_table_row_is_read_as_well_as_a_bullet(tmp_path):
    """Measured on the 12 real reports: § 5 is written both ways, and a parser that read only
    bullets found two gaps across all of them."""
    root = _reports(tmp_path, _SECOND)
    gaps = [g for g in brief_gaps.gaps_in(str(root)) if g.kind == "incomplete"]
    assert len(gaps) == 1
    assert "inherited two seed numbers" in gaps[0].text
    assert "truncated" not in " ".join(g.text for g in gaps)


def test_a_gap_carries_the_report_it_came_from(tmp_path):
    root = _reports(tmp_path, _REPORT)
    gap = brief_gaps.gaps_in(str(root))[0]
    assert gap.report.endswith("delegate-report.md")
    assert "run-0" in gap.report


def test_the_no_tier_line_counts_as_a_gap_wherever_it_sits(tmp_path):
    """Two real reports record the missing tier in § 1, not § 5. A ledger that only read § 5 would
    miss the single most common gap there is."""
    root = _reports(tmp_path, _REPORT)
    kinds = {g.kind for g in brief_gaps.gaps_in(str(root))}
    assert "no-tier" in kinds


def test_reports_with_no_gaps_contribute_nothing(tmp_path):
    root = _reports(tmp_path, "# Run report\n\n## 5. Problems hit\n\n- **No gap found** — nothing.\n")
    assert brief_gaps.gaps_in(str(root)) == []


def test_the_rendered_ledger_is_a_table_newest_first(tmp_path):
    root = _reports(tmp_path, _REPORT, _SECOND)
    out = brief_gaps.render(brief_gaps.gaps_in(str(root)))
    assert out.count("|") >= 6, "a table, not paragraphs"
    assert "run-" in out


# ── routing: a gap that repeats leaves the ledger by becoming a rule ────────
# The ledger only earns its keep if rows leave it. `--route` says who owns each gap's fix, and the
# answer is often not the brief: several real reports record "the task_map has no row for this",
# which is a doctrine-routing defect a ledger would bury.

def _gap(text: str, kind: str = "incomplete", report: str = "r/delegate-report.md"):
    return brief_gaps.Gap(report, kind, text)


def test_a_missing_tier_is_already_closed_by_the_guard():
    route = brief_gaps.route(_gap("x", kind="no-tier"))
    assert route.closed
    assert "brief_anchor_guard" in route.owner


def test_stale_line_numbers_are_already_closed_by_the_guard():
    route = brief_gaps.route(_gap("The brief's line numbers were stale in six places."))
    assert route.closed
    assert "brief_anchor_guard" in route.owner


def test_an_ungranted_tool_is_already_closed_by_the_guard():
    route = brief_gaps.route(_gap("`DesignSync` is not reachable from this grant — the brief named it"))
    assert route.closed
    assert "brief_anchor_guard" in route.owner


def test_a_task_map_gap_is_not_the_brief_s_problem():
    route = brief_gaps.route(_gap("The brief could not route it — `task_map.md` has no row for the journey"))
    assert not route.closed
    assert "task_map" in route.owner
    assert "Step 4" not in route.owner


def test_a_gap_that_repeats_becomes_a_step_4_rule():
    gaps = [
        _gap("The brief's read list is 4,000 lines before any disk reading", report="a/delegate-report.md"),
        _gap("The brief's read list is 4,000 lines before any disk reading", report="b/delegate-report.md"),
    ]
    routed = brief_gaps.route_all(gaps)
    assert any("Step 4" in r.owner for _, r in routed)


def test_a_one_off_with_no_owner_stays_unrouted():
    routed = brief_gaps.route_all([_gap("something that happened once and fits no rule")])
    (_, route), = routed
    assert route.owner == ""
    assert not route.closed


def test_the_routed_render_separates_closed_from_open():
    gaps = [_gap("x", kind="no-tier"), _gap("something that happened once and fits no rule")]
    out = brief_gaps.render_routed(brief_gaps.route_all(gaps))
    assert "closed" in out.lower()
    assert "brief_anchor_guard" in out


def test_a_gap_that_never_says_brief_still_reaches_routing(tmp_path):
    """Found by running the router over the 12 real reports: v8's entry is "`task_map.md` has no row
    for the journey — reported, not written around", which never says "brief" and so was dropped by
    the ledger's filter — losing the single most valuable routing case. The ledger stays brief-scoped
    because that is what its reader needs; routing takes the wider set."""
    body = (
        "# Run report\n\n## 5. Problems hit\n\n"
        "- **`task_map.md` has no row for the journey — reported, not written around.** "
        "Twenty-six rows, none covering it.\n"
        "- **`Read` truncated the manifest** — 27,097 tokens against a 25,000 cap.\n"
    )
    root = _reports(tmp_path, body)
    assert brief_gaps.gaps_in(str(root)) == [], "not a brief gap, so not on the ledger"
    routed = brief_gaps.route_all(brief_gaps.routable_in(str(root)))
    owners = [r.owner for _, r in routed]
    assert any("task_map" in o for o in owners), "but routing must still see it"
    assert not any("truncated" in g.text for g, _ in routed), "an unroutable non-brief problem stays out"


def test_a_nested_checkout_is_not_walked(tmp_path):
    """A worktree nests a whole second copy of the tree inside the repo, so walking into one counts
    every report twice; a checkout whose worktree was pruned keeps serving the state it died in,
    which is staler still. Measured 2026-09-03 in this repo before the skip landed: 486 reports
    found, 359 of them inside nested checkouts."""
    root = _reports(tmp_path, _REPORT)
    for nest in (".worktrees/old-plan", ".claude/worktrees/agent-abc"):
        folder = root / nest / "docs" / "proposals" / "run-0"
        folder.mkdir(parents=True)
        (folder / "delegate-report.md").write_text(_REPORT)

    found = brief_gaps.reports_in(str(root))
    assert len(found) == 1, f"the nested copies must not be walked: {found}"
    assert not any("worktrees" in path for path in found)
