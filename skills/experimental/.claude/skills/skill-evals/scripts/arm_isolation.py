#!/usr/bin/env python3
"""Detects when one eval arm's executor operated inside its sibling arm's directory.

Both arms of a case (`with_skill` / `without_skill`, or any other pair a skill's evals.json declares)
run concurrently in sibling directories under `<workspace>/<case>/`, and nothing else on this harness
attributes a write to an arm: `harvest_run.py` computes its delta from a hash diff against the tree as
staged, which records that a file appeared and never which agent wrote it.

The one surviving signal is each arm's own account of what it did, at
`<case>/<arm>/outputs/transcript.md` — a file the harness already instructs every executor to write
(`run-skill-evals.js:312`), so this check reads something the harness already guarantees exists, in a
location it already fixes.

This is a self-report check: an arm that crosses into its sibling's directory and never mentions it in
its transcript is not caught. What it does catch, it catches honestly — a missing transcript is
recorded as `unchecked`, distinguishably from an arm that was read and found clean, so silence never
renders as a pass.

Advisory, not fatal: this module finds crossings, it does not decide what to do about them. A
contaminated round still produced real files and a real benchmark; the caller
(`aggregate_benchmark.py`) annotates the round with what this module found and changes nothing else
about it — no exclusion from the aggregate, no exit-code change.

Usage:
    arm_isolation.py <workspace-dir>

Prints JSON to stdout: schema_version, checked, cases_checked, arms_checked, flagged,
recovered, unchecked.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

SCHEMA_VERSION = 1


class ArmCheckStatus(str, Enum):
    """A closed set of outcomes for one arm's check — never widen this with an ad-hoc string
    elsewhere; add a member here instead."""

    CLEAN = "clean"
    FLAGGED = "flagged"
    RECOVERED = "recovered"
    UNCHECKED = "unchecked"


@dataclass(frozen=True)
class ArmCheck:
    """The outcome of reading one arm's transcript against its siblings' names."""

    case: str
    arm: str
    status: ArmCheckStatus
    sibling: str | None = None
    matched: str | None = None


@dataclass(frozen=True)
class IsolationResult:
    """What the check found, plus enough of what it looked at to make a clean pass trustworthy."""

    cases_checked: int
    checks: tuple[ArmCheck, ...] = field(default_factory=tuple)

    @property
    def flagged(self) -> list[ArmCheck]:
        return [c for c in self.checks if c.status is ArmCheckStatus.FLAGGED]

    @property
    def recovered(self) -> list[ArmCheck]:
        """Arms that named a sibling but produced in their own tree — the fence catching a bad path.
        Kept out of `flagged` on purpose: these rounds are measurable, and calling them contaminated
        is what made a working fence read as a spoiled round."""
        return [c for c in self.checks if c.status is ArmCheckStatus.RECOVERED]

    @property
    def unchecked(self) -> list[ArmCheck]:
        return [c for c in self.checks if c.status is ArmCheckStatus.UNCHECKED]

    @property
    def arms_checked(self) -> int:
        """Arms whose transcript was actually read — excludes the unchecked ones, so this count
        answers 'how many arms it read', not 'how many arms exist'."""
        return sum(1 for c in self.checks if c.status is not ArmCheckStatus.UNCHECKED)

    def to_dict(self) -> dict:
        return {
            "schema_version": SCHEMA_VERSION,
            "checked": True,
            "cases_checked": self.cases_checked,
            "arms_checked": self.arms_checked,
            "flagged": [
                {"case": c.case, "arm": c.arm, "sibling": c.sibling, "matched": c.matched}
                for c in self.flagged
            ],
            "recovered": [
                {"case": c.case, "arm": c.arm, "sibling": c.sibling, "matched": c.matched}
                for c in self.recovered
            ],
            "unchecked": [{"case": c.case, "arm": c.arm} for c in self.unchecked],
        }


def find_case_dirs(workspace: Path) -> list[Path]:
    """Case directories directly under the workspace root.

    A round's non-case entries — benchmark.json, benchmark.md, run_manifest.json,
    stage_manifest.json, and in some rounds fixture_guard.json / fixture_guard_report.md — are all
    files, never directories, on this harness. Filtering to directories excludes them without naming
    them; nothing here needs to know their filenames.
    """
    if not workspace.is_dir():
        return []
    return sorted((d for d in workspace.iterdir() if d.is_dir()), key=lambda d: d.name)


def _arm_dirs(case_dir: Path) -> list[Path]:
    return sorted((d for d in case_dir.iterdir() if d.is_dir()), key=lambda d: d.name)


def _find_sibling_mention(text: str, sibling: str) -> str | None:
    """The first line naming `sibling` as a whole path/word segment, or None.

    A word-boundary match (not a bare substring) so a sibling name is never mistaken for a
    accidentally-overlapping run of characters inside an unrelated identifier or case name.
    """
    pattern = re.compile(rf"\b{re.escape(sibling)}\b")
    for line in text.splitlines():
        if pattern.search(line):
            return line.strip()
    return None


def _check_arm(case_dir: Path, arm_dir: Path, sibling_names: list[str]) -> ArmCheck:
    transcript = arm_dir / "outputs" / "transcript.md"
    if not transcript.is_file():
        return ArmCheck(case=case_dir.name, arm=arm_dir.name, status=ArmCheckStatus.UNCHECKED)

    # Decoded defensively because this check is advisory and must never cost a round its benchmark: a
    # transcript is free text written by a model, and it is the one untrusted input this module reads.
    # Left to raise, a single undecodable byte in any one arm would propagate out of
    # aggregate_benchmark.py and strand a ~30M-token round with no benchmark.json at all — the exact
    # harm the advisory-not-fatal rule exists to prevent. U+FFFD is not a word character, so the
    # word-boundary sibling match below is unaffected by a replacement.
    text = transcript.read_text(encoding="utf-8", errors="replace")
    for sibling in sibling_names:
        matched = _find_sibling_mention(text, sibling)
        if matched is None:
            continue
        # A mention alone cannot tell going-there from refusing-to-go-there, and since 701db7f the
        # executor prompt actively instructs a well-behaved run to say so: handed a path outside its
        # own tree, it must stop, name what it was given, and use its own. That recovery note reads
        # exactly like a crossing to a text scan. Measured in product-prd iteration-7, where the
        # fence worked, nothing crossed, and the round was still headed CONTAMINATED.
        #
        # The discriminator is a fact, not prose: WHERE THE WORK LANDED.
        #   - crossed  -> this arm's own product tree is untouched; its output went next door
        #     (iteration-6: run_delta created/modified/deleted all empty, and it graded 0.0)
        #   - recovered -> this arm produced in its OWN tree despite naming the sibling
        #     (iteration-7: created ['mailmate/docs/PRD.md'], and it graded 1.0)
        #
        # `recovered` is reported rather than folded into `clean`, because it is not nothing: it
        # means something handed this arm a path outside its own tree and the fence caught it. That
        # is a live harness fault worth seeing, just not a spoiled measurement.
        status = (
            ArmCheckStatus.RECOVERED if _produced_in_own_tree(arm_dir) else ArmCheckStatus.FLAGGED
        )
        return ArmCheck(
            case=case_dir.name, arm=arm_dir.name, status=status,
            sibling=sibling, matched=matched,
        )
    return ArmCheck(case=case_dir.name, arm=arm_dir.name, status=ArmCheckStatus.CLEAN)


def _produced_in_own_tree(arm_dir: Path) -> bool:
    """Did this arm change anything inside its own staged product?

    Reads the run_delta.json harvest_run.py already wrote — the recorded fact of what appeared in
    this arm's tree. A missing or unreadable delta answers False: an arm with no evidence that it
    produced anything of its own is the shape of one whose work went elsewhere, and on an advisory
    check the safer read is the one that keeps looking.
    """
    delta_file = arm_dir / "outputs" / "run_delta.json"
    try:
        delta = json.loads(delta_file.read_text(encoding="utf-8", errors="replace"))
    except (OSError, ValueError):
        return False
    return any(delta.get(k) for k in ("created", "modified", "deleted"))


def check_arm_isolation(workspace: Path) -> IsolationResult:
    """Read every arm's transcript under `workspace` for a path naming its sibling arm.

    Siblings are derived per case, from the case directory's own subdirectories — never a hardcoded
    pair — so a case with a third arm, or arms named something other than `with_skill` /
    `without_skill`, is still checked; a case with exactly one arm has no sibling to cross into.
    """
    case_dirs = find_case_dirs(workspace)
    checks: list[ArmCheck] = []

    for case_dir in case_dirs:
        arm_dirs = _arm_dirs(case_dir)
        arm_names = [d.name for d in arm_dirs]
        for arm_dir in arm_dirs:
            siblings = [name for name in arm_names if name != arm_dir.name]
            checks.append(_check_arm(case_dir, arm_dir, siblings))

    return IsolationResult(cases_checked=len(case_dirs), checks=tuple(checks))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="arm_isolation.py",
        description="Detect when one eval arm's executor operated inside its sibling arm's directory.",
    )
    parser.add_argument("workspace", help="A round's workspace directory (holds the case dirs).")
    args = parser.parse_args(argv)

    workspace = Path(args.workspace).resolve()
    if not workspace.is_dir():
        print(f"arm-isolation: no such workspace: {workspace}", file=sys.stderr)
        return 2

    result = check_arm_isolation(workspace)
    print(json.dumps(result.to_dict()))

    if result.flagged:
        print(
            f"arm-isolation: {len(result.flagged)} crossing(s) found across "
            f"{result.cases_checked} case(s):",
            file=sys.stderr,
        )
        for c in result.flagged:
            print(f"  {c.case}/{c.arm} names sibling arm {c.sibling}: {c.matched}", file=sys.stderr)
    else:
        print(
            f"arm-isolation: checked {result.arms_checked} arm(s) across "
            f"{result.cases_checked} case(s) — no crossings",
            file=sys.stderr,
        )
    if result.unchecked:
        print(
            f"arm-isolation: {len(result.unchecked)} arm(s) had no transcript to read",
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
