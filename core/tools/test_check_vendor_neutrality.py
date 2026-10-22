#!/usr/bin/env python3
"""Contract tests for `check_vendor_neutrality.py`.

Correctness is proved on synthetic fixtures — `tmp_path` git repos and bare strings — never on
an assertion that the live `core/` tree is clean. The tree is known dirty until the sweep station
repairs it, and a suite that required cleanliness could not land on this branch (Task 4's own
behaviours). A handful of tests below do read specific, named lines of the real repo — the live
cases the plan and the station cite by path and line — but each asserts only that one line's own
verdict, never that the file or the tree around it is otherwise clean. The checks of this
instance's own tree — its project set, the allowlist tuned to it, the records a repair points at —
are `system/tests/test_instance_vendor_neutrality.py`.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

import check_vendor_neutrality as cvn
from check_vendor_neutrality import (
    Hit,
    _real_project_names,
    _tracked_files,
    apply_allowlist,
    load_allowlist,
    scan_repo,
    scan_text,
)

REPO = Path(__file__).resolve().parents[2]


# --- scan_text: host-path detection (Task 1) ---------------------------------------------------


def test_a_real_project_segment_is_reported():
    """`system/projects/tools/` — `tools` is a real project of this instance."""
    hits = scan_text("f.md", "See system/projects/tools/journey/x.md for detail.", {"tools"})
    assert hits == [Hit(path="f.md", line=1, kind="host-path", text=hits[0].text)]


def test_a_placeholder_segment_is_not_reported():
    """`system/projects/<name>/` is the shape a vendored file is supposed to use."""
    hits = scan_text("f.md", "See `system/projects/<name>/agari.md`.", {"tools"})
    assert hits == []


def test_a_segment_naming_no_real_project_is_not_reported():
    """`example-product` names nothing under `system/projects/` — a bare identity token, not a real project
    directory."""
    hits = scan_text("f.md", "bare identity: `system/projects/example-product`, rejected here.", {"tools"})
    assert hits == []


def test_a_host_path_inside_an_inline_code_span_is_still_reported():
    """The whole point: a naive use-versus-mention strip erases 17 of 19 live host references, and
    a check that strips code spans looks green while catching almost nothing."""
    hits = scan_text("f.md", "`system/projects/tools/journey/x.md`", {"tools"})
    assert len(hits) == 1
    assert hits[0].kind == "host-path"


def test_a_glob_segment_is_not_reported():
    hits = scan_text("f.md", "`system/projects/*/doctrine/`", {"tools"})
    assert hits == []


def test_two_real_segments_on_one_line_are_still_one_hit():
    """Multiple matches on one line report the line once — the line is the unit of a hit."""
    hits = scan_text(
        "f.md",
        "system/projects/tools/ and system/projects/scripts/ both cited.",
        {"tools", "scripts"},
    )
    assert len(hits) == 1
    assert hits[0].line == 1


def test_a_clean_line_is_not_reported():
    hits = scan_text("f.md", "nothing here names a host-only path.", {"tools"})
    assert hits == []


def test_line_numbers_are_one_based():
    hits = scan_text("f.md", "clean\nsystem/projects/tools/\nclean\n", {"tools"})
    assert [h.line for h in hits] == [2]


# --- _real_project_names ----------------------------------------------------------------------


def test_real_project_names_reads_system_projects_at_run_time(tmp_path):
    (tmp_path / "system" / "projects" / "alpha").mkdir(parents=True)
    (tmp_path / "system" / "projects" / "beta").mkdir(parents=True)
    (tmp_path / "system" / "projects" / ".hidden").mkdir(parents=True)
    (tmp_path / "system" / "projects" / "not-a-dir.md").write_text("x\n")

    assert _real_project_names(tmp_path) == {"alpha", "beta"}


def test_real_project_names_empty_when_system_projects_is_absent(tmp_path):
    assert _real_project_names(tmp_path) == set()


# --- _tracked_files: git ls-files, scoped to the two roots (Task 1 behaviour 4) ----------------


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=True
    ).stdout


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@example.com")
    _git(repo, "config", "user.name", "t")
    return repo


def _commit_file(repo: Path, relative: str, content: str = "x\n") -> None:
    path = repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    _git(repo, "add", relative)
    _git(repo, "commit", "-qm", relative)


def test_tracked_files_reads_every_root_and_nothing_outside_them(tmp_path):
    repo = _repo(tmp_path)
    _commit_file(repo, "core/tools/a.py")
    _commit_file(repo, ".claude/skills/s/SKILL.md")
    _commit_file(repo, "skills/g/.claude/skills/t/SKILL.md")
    _commit_file(repo, "system/projects/alpha/project.md")  # outside every root

    files = _tracked_files(repo)

    assert files == [
        ".claude/skills/s/SKILL.md",
        "core/tools/a.py",
        "skills/g/.claude/skills/t/SKILL.md",
    ]


def test_tracked_files_excludes_test_prefixed_files(tmp_path):
    """A test's own fixtures name the strings this check looks for — counting them would let
    every future test author dodge the rule by writing one."""
    repo = _repo(tmp_path)
    _commit_file(repo, "core/tools/a.py")
    _commit_file(repo, "core/tools/test_a.py")

    assert _tracked_files(repo) == ["core/tools/a.py"]


def test_tracked_files_excludes_untracked_scratch(tmp_path):
    repo = _repo(tmp_path)
    _commit_file(repo, "core/tools/a.py")
    (repo / "core" / "tools" / "scratch.py").write_text("x\n", encoding="utf-8")

    assert _tracked_files(repo) == ["core/tools/a.py"]


def test_tracked_files_excludes_the_allowlist_file(tmp_path):
    """The allowlist file spells the literal pattern this check catches, once per entry — the
    check would report itself and the sweep would never converge. Same reasoning as the
    `test_`-prefix exclusion: a file that exists to *contain* the string this check looks for is
    not itself scanned."""
    repo = _repo(tmp_path)
    _commit_file(repo, "core/tools/a.py")
    _commit_file(repo, "core/tools/vendor_neutrality_allowlist.json", "{}\n")

    assert _tracked_files(repo) == ["core/tools/a.py"]


def test_tracked_files_still_scans_another_json_under_core_tools(tmp_path):
    """The exclusion is narrow: it names the one file, not every `.json` under `core/tools/`."""
    repo = _repo(tmp_path)
    _commit_file(repo, "core/tools/other.json", "{}\n")

    assert _tracked_files(repo) == ["core/tools/other.json"]


def test_scan_repo_does_not_report_a_hit_that_exists_only_in_the_allowlist_file(tmp_path):
    """A hit that lives only inside the allowlist file's own text — the pattern it spells to
    excuse a site elsewhere — is not reported at all, never mind excused via `apply_allowlist`."""
    repo = _repo(tmp_path)
    _commit_file(
        repo,
        "core/tools/vendor_neutrality_allowlist.json",
        '{"x.md:system/projects/alpha": "reason"}\n',
    )
    (repo / "system" / "projects" / "alpha").mkdir(parents=True)

    assert scan_repo(repo) == []


# --- scan_repo -------------------------------------------------------------------------------


def test_scan_repo_finds_a_real_host_path_hit(tmp_path):
    repo = _repo(tmp_path)
    _commit_file(repo, "core/doctrine/x.md", "cites system/projects/alpha/journey/x.md\n")
    (repo / "system" / "projects" / "alpha").mkdir(parents=True)

    hits = scan_repo(repo)

    assert [(h.path, h.line) for h in hits] == [("core/doctrine/x.md", 1)]


def test_scan_repo_reads_the_claude_skills_root_too(tmp_path):
    """Task 1's intent names two roots, and `.claude/skills/` is in scope by the owner's ruling of
    2026-08-31. A hit there is reported end-to-end, not merely visible to `_tracked_files`."""
    repo = _repo(tmp_path)
    _commit_file(repo, ".claude/skills/s/SKILL.md", "cites system/projects/alpha/agari.md\n")
    (repo / "system" / "projects" / "alpha").mkdir(parents=True)

    hits = scan_repo(repo)

    assert [(h.path, h.line, h.kind) for h in hits] == [
        (".claude/skills/s/SKILL.md", 1, "host-path")
    ]


def test_scan_repo_reads_the_grouped_skills_root_too(tmp_path):
    """A grouped skill (`skills/<group>/.claude/skills/<name>/`) is admitted into a satellite by
    `--add-dir`, so it is vendored exactly as a flat one is. Moving a skill into a group must not
    move it out of this check."""
    repo = _repo(tmp_path)
    _commit_file(
        repo, "skills/g/.claude/skills/s/SKILL.md", "cites system/projects/alpha/agari.md\n"
    )
    (repo / "system" / "projects" / "alpha").mkdir(parents=True)

    hits = scan_repo(repo)

    assert [(h.path, h.line, h.kind) for h in hits] == [
        ("skills/g/.claude/skills/s/SKILL.md", 1, "host-path")
    ]


def test_scan_repo_is_not_vacuous_with_no_root_to_scan(tmp_path):
    """Behaviour 5 — with none of `core/`, `.claude/skills/` or `skills/` present, fail loudly rather than
    reporting a silent, indistinguishable-from-clean zero."""
    repo = _repo(tmp_path)
    _commit_file(repo, "docs/readme.md")

    with pytest.raises(RuntimeError):
        scan_repo(repo)


# --- _tracked_files: a record holds what was true at a moment — not scanned (Task 2) -----------

# Decision 1: 15 of the 50 sit in artifacts that exist to hold what was true at a moment —
# evidence/** (11), a code-integrity-report.md (3), and a skill's own ratification verdict under
# references/ (1). Rewriting one falsifies the record. This is the owner's own live-versus-retired
# split (2026-08-31), already drawn in code for a different rule at `written_forward.py:36-39` —
# this check should not disagree with it silently.


def test_tracked_files_excludes_a_file_under_an_evidence_segment(tmp_path):
    repo = _repo(tmp_path)
    _commit_file(repo, "core/tools/a.py")
    _commit_file(repo, ".claude/skills/x/evidence/iteration-1/run.json", "{}\n")

    assert _tracked_files(repo) == ["core/tools/a.py"]


def test_tracked_files_still_scans_a_file_merely_named_evidence_md(tmp_path):
    """The exclusion is a path *segment*, `evidence/` — not a substring of a filename."""
    repo = _repo(tmp_path)
    _commit_file(repo, "core/doctrine/evidence.md", "cites system/projects/alpha/x.md\n")

    assert _tracked_files(repo) == ["core/doctrine/evidence.md"]


def test_tracked_files_excludes_code_integrity_report_wherever_it_sits(tmp_path):
    repo = _repo(tmp_path)
    _commit_file(repo, "core/tools/a.py")
    _commit_file(repo, "core/launchers/ad-hoc-flow/code-integrity-report.md", "x\n")
    _commit_file(repo, ".claude/skills/x/nested/dir/code-integrity-report.md", "x\n")

    assert _tracked_files(repo) == ["core/tools/a.py"]


def test_tracked_files_excludes_a_ratification_verdict_under_references(tmp_path):
    repo = _repo(tmp_path)
    _commit_file(repo, "core/tools/a.py")
    _commit_file(
        repo, ".claude/skills/x/references/x_ratification_verdict.md", "cites system/x\n"
    )

    assert _tracked_files(repo) == ["core/tools/a.py"]


def test_tracked_files_still_scans_a_ratification_verdict_outside_references(tmp_path):
    """The exclusion is `references/<name>_ratification_verdict.md` — the shape decision 1 names —
    not any file whose name ends `_ratification_verdict.md` anywhere in the tree."""
    repo = _repo(tmp_path)
    _commit_file(repo, ".claude/skills/x/x_ratification_verdict.md", "x\n")

    assert _tracked_files(repo) == [".claude/skills/x/x_ratification_verdict.md"]


def test_tracked_files_still_scans_another_file_under_references(tmp_path):
    """The exclusion is narrow: an ordinary reference file in the same directory is still
    scanned."""
    repo = _repo(tmp_path)
    _commit_file(repo, ".claude/skills/x/references/other.md", "cites system/x\n")

    assert _tracked_files(repo) == [".claude/skills/x/references/other.md"]


def test_docstring_states_the_record_exclusion_and_its_ground():
    assert "evidence/" in cvn.__doc__
    assert "code-integrity-report.md" in cvn.__doc__
    assert "written_forward.py:36-39" in cvn.__doc__
    assert "live-versus-retired" in cvn.__doc__


def _is_one_of_the_three_record_shapes(relative: str) -> bool:
    """Decision 5's three shapes, written out here rather than borrowed from `cvn._is_record`, so
    the live test below checks the exclusion against the rule instead of against itself."""
    parts = Path(relative).parts
    name = parts[-1]
    return (
        "evidence" in parts[:-1]
        or name == "code-integrity-report.md"
        or ("references" in parts[:-1] and name.endswith("_ratification_verdict.md"))
    )


def test_over_the_live_tree_the_exclusion_drops_records_and_only_records():
    """Re-derive the drop, do not assume it — over the real tree, not a fixture. What the exclusion
    removes is non-empty, so a rule that stopped matching cannot pass, and every file it removes is
    one of decision 5's record shapes, so it never hides a live file. It pins no count: a count of
    the records that happen to exist breaks on the next report a run writes, which is how the
    `== 15` this replaces went red at 19 without the check changing."""
    tracked_now = set(_tracked_files(REPO))
    raw_all = subprocess.run(
        ["git", "ls-files", "-z", "--", *cvn.ROOTS, *cvn.ROOT_FILES], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout.split("\0")
    tracked_before_record_exclusion = {
        p
        for p in raw_all
        if p and not Path(p).name.startswith("test_") and p != cvn._ALLOWLIST_RELATIVE
    }
    record_only = tracked_before_record_exclusion - tracked_now

    assert record_only, "the record exclusion dropped nothing from the live tree"
    not_records = sorted(p for p in record_only if not _is_one_of_the_three_record_shapes(p))
    assert not not_records, f"the exclusion dropped files that are not records: {not_records}"


def test_no_ratification_verdict_ships():
    """A verdict under a skill's `references/` is a record, so the scan above leaves it unread —
    and a release would carry it unchecked for the names this check rules out. It is kept out of
    the shipped tree instead of scanned, the way evidence is: the verdict's one home is
    `system/projects/<managing-project>/docs/` (`core/doctrine/kaizen/ratification.md` § 5), which
    a release does not carry, so a verdict anywhere under the vendored roots is misplaced."""
    shipped = subprocess.run(
        ["git", "ls-files", "-z", "--", *cvn.ROOTS, *cvn.ROOT_FILES], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout.split("\0")
    verdicts = sorted(p for p in shipped if p.endswith("_ratification_verdict.md"))
    assert not verdicts, (
        f"{verdicts} would ship unscanned — move each to "
        f"system/projects/<managing-project>/docs/ (ratification.md § 5)."
    )


# --- Live cases named by the plan and the station ------------------------------------------


def _line_containing(path: str, marker: str) -> str:
    """The one live line in `path` holding `marker`, located by text rather than by number.

    These live-case tests read the real tree, so a line number pins a position and not a subject:
    an edit anywhere above the site re-numbers it and the test then asserts a verdict about some
    other line. Both failure modes showed up on 2026-09-01 in one commit — the versioning case
    failed loudly because its site had been repaired away, and the structure case **passed**
    because its subject had moved from :132 to :139 and the line it read happened to be clean. The
    silent one is the dangerous half, which is why the marker must match exactly once.
    """
    lines = (REPO / path).read_text(encoding="utf-8").splitlines()
    hits = [line for line in lines if marker in line]
    assert len(hits) == 1, (
        f"expected exactly one line in {path} containing {marker!r}, found {len(hits)} — a "
        f"live-case test cannot pick between several, and zero means the site is gone"
    )
    return hits[0]


# --- apply_allowlist: the key is a text anchor, not a line number (Task 1) ---------------------

# An entry is keyed `path:<anchor>` -- the anchor a snippet of the excused line's own text,
# resolved by substring match against the raw hits in that path at run time. A line number is a
# position, not an identity: any edit above the site re-numbers it, and the entry then excuses a
# line that no longer holds the hit. The anchor survives exactly that edit -- it names what the
# entry excuses, not where it sat.


def test_an_allowlisted_site_is_not_reported():
    raw = [Hit(path="f.md", line=5, kind="host-path", text="the excused text lives here")]
    reported, stale = apply_allowlist(raw, {"f.md:excused text": "marked host-only provenance"})
    assert reported == []
    assert stale == []


def test_the_same_path_at_a_different_site_is_still_reported():
    raw = [
        Hit(path="f.md", line=5, kind="host-path", text="the first excused site"),
        Hit(path="f.md", line=9, kind="host-path", text="a second, unexcused site"),
    ]
    reported, stale = apply_allowlist(raw, {"f.md:first excused": "marked host-only provenance"})
    assert [h.line for h in reported] == [9]


def test_a_key_with_no_anchor_is_refused_rather_than_excusing_the_whole_file(tmp_path):
    """`f.md` and `f.md:` both reduce to an empty anchor, which substring-matches every hit in that
    path — a blanket file exemption, the thing this allowlist exists instead of. With two hits the
    ambiguity guard would catch it; with exactly one it excused the site silently, which is why the
    refusal belongs at load time and not in the resolver.

    Surfaced by the code-integrity pass on `the-allowlist-survives-an-edit` (item 3) and closed here.
    """
    for key in ("core/doctrine/setup/kensaiapp_structure.md", "core/doctrine/setup/kensaiapp_structure.md:", "f.md:   "):
        path = tmp_path / "allow.json"
        path.write_text(json.dumps({key: "a stated reason"}), encoding="utf-8")
        with pytest.raises(ValueError, match="carries no anchor"):
            load_allowlist(path)


def test_the_shipped_allowlist_has_no_anchorless_key():
    """The refusal above is enforcement; this is the live tree's state, which must never need it."""
    for key in load_allowlist():
        assert key.partition(":")[2].strip(), f"{key!r} carries no anchor"


def test_an_allowlist_entry_naming_a_site_with_no_hit_is_stale():
    reported, stale = apply_allowlist([], {"f.md:5": "marked host-only provenance"})
    assert reported == []
    assert stale == ["f.md:5"]


def test_an_entry_resolves_to_the_site_wherever_its_line_now_sits():
    """The anchor is matched against the hit's own text, never its line number -- the same anchor
    excuses the site whether it sits at line 5 or line 50."""
    key = "f.md:the excused text"
    raw_at_five = [Hit(path="f.md", line=5, kind="host-path", text="the excused text, early")]
    raw_at_fifty = [Hit(path="f.md", line=50, kind="host-path", text="the excused text, late")]

    reported_five, stale_five = apply_allowlist(raw_at_five, {key: "reason"})
    reported_fifty, stale_fifty = apply_allowlist(raw_at_fifty, {key: "reason"})

    assert reported_five == []
    assert stale_five == []
    assert reported_fifty == []
    assert stale_fifty == []


def test_inserting_lines_above_the_site_does_not_go_stale():
    """Reached-when 2 -- proved by mutating a fixture, not by argument. `scan_text` re-numbers the
    site when lines are inserted above it; the anchor-keyed entry must not notice."""
    real_names = {"tools"}
    key = "f.md:system/projects/tools/journey/x.md"
    original = "line one\nline two\n`system/projects/tools/journey/x.md` cited here\n"
    mutated_by_an_edit_above = "inserted a\ninserted b\ninserted c\n" + original

    raw_before = scan_text("f.md", original, real_names)
    raw_after = scan_text("f.md", mutated_by_an_edit_above, real_names)
    assert raw_before[0].line == 3
    assert raw_after[0].line == 6  # the same site, re-numbered by the insertion above it

    reported_before, stale_before = apply_allowlist(raw_before, {key: "reason"})
    reported_after, stale_after = apply_allowlist(raw_after, {key: "reason"})

    assert reported_before == []
    assert stale_before == []
    assert reported_after == []
    assert stale_after == []


def test_editing_the_excused_line_makes_the_entry_stale_and_the_site_reported():
    """Both, not either -- the entry must not survive the thing it excuses changing, and the edited
    line (still a real hit, on a different real project) is not silently swallowed either."""
    real_names = {"tools", "other"}
    key = "f.md:system/projects/tools/journey/x.md"
    edited_text = "`system/projects/other/journey/x.md` cited here\n"

    raw = scan_text("f.md", edited_text, real_names)
    reported, stale = apply_allowlist(raw, {key: "reason"})

    assert stale == [key]
    assert [h.line for h in reported] == [1]


def test_an_anchor_matching_two_lines_in_one_file_is_refused():
    """An entry that silently excuses two sites -- or silently picks one -- is the failure this
    trades for the old one. Refused loudly instead, naming the file and every matching line."""
    raw = [
        Hit(path="f.md", line=5, kind="host-path", text="system/projects/tools/a"),
        Hit(path="f.md", line=9, kind="host-path", text="system/projects/tools/b"),
    ]

    with pytest.raises(ValueError) as exc_info:
        apply_allowlist(raw, {"f.md:system/projects/tools": "reason"})

    message = str(exc_info.value)
    assert "f.md" in message
    assert "5" in message
    assert "9" in message


def test_an_anchor_matching_no_hit_line_in_its_path_is_stale():
    """The existing behaviour, unchanged -- an anchor that matches nothing is reported stale, not
    silently dropped and not an error."""
    raw = [Hit(path="f.md", line=5, kind="host-path", text="system/projects/tools/a")]
    reported, stale = apply_allowlist(raw, {"f.md:not-present-anywhere": "reason"})
    assert stale == ["f.md:not-present-anywhere"]
    assert reported == raw


# --- load_allowlist ----------------------------------------------------------------------------


def test_load_allowlist_reads_path_line_to_reason(tmp_path):
    allowlist = tmp_path / "allow.json"
    allowlist.write_text(json.dumps({"f.md:5": "the reason"}), encoding="utf-8")
    assert load_allowlist(allowlist) == {"f.md:5": "the reason"}


def test_load_allowlist_missing_file_is_an_empty_allowlist(tmp_path):
    assert load_allowlist(tmp_path / "nope.json") == {}


def test_load_allowlist_rejects_an_entry_with_no_reason(tmp_path):
    """A malformed allowlist fails loudly rather than being silently trusted."""
    allowlist = tmp_path / "allow.json"
    allowlist.write_text(json.dumps({"f.md:5": ""}), encoding="utf-8")
    with pytest.raises(ValueError):
        load_allowlist(allowlist)


def test_load_allowlist_rejects_an_entry_with_a_blank_reason(tmp_path):
    allowlist = tmp_path / "allow.json"
    allowlist.write_text(json.dumps({"f.md:5": "   "}), encoding="utf-8")
    with pytest.raises(ValueError):
        load_allowlist(allowlist)


def test_main_fails_on_a_malformed_allowlist_rather_than_trusting_it(tmp_path, monkeypatch):
    """Task 2's intent is that the *checker* fails on a malformed allowlist, not only the loader
    called in isolation — a run that swallowed the error would silently trust the file."""
    repo = _repo(tmp_path)
    _commit_file(repo, "core/tools/a.py", "clean\n")
    allowlist = repo / "allow.json"
    allowlist.write_text(json.dumps({"core/tools/a.py:1": ""}), encoding="utf-8")
    monkeypatch.setattr(cvn, "ALLOWLIST_PATH", allowlist)

    with pytest.raises(ValueError):
        cvn.main(["--repo", str(repo), "--quiet"])


def test_main_refuses_an_ambiguous_anchor_rather_than_running_past_it(tmp_path, monkeypatch):
    """Task 1's fourth behaviour has to reach a *run*. `apply_allowlist` raising proves the check
    exists; only driving `main()` proves the checker stops on it instead of reporting around it,
    and naming both lines is what makes the refusal actionable rather than merely loud."""
    repo = _repo(tmp_path)
    _commit_file(
        repo,
        "core/doctrine/a.md",
        "cites system/projects/alpha/one.md\ncites system/projects/alpha/two.md\n",
    )
    (repo / "system" / "projects" / "alpha").mkdir(parents=True)
    allowlist = repo / "allow.json"
    allowlist.write_text(
        json.dumps({"core/doctrine/a.md:system/projects/alpha": "reason"}), encoding="utf-8"
    )
    monkeypatch.setattr(cvn, "ALLOWLIST_PATH", allowlist)

    with pytest.raises(ValueError) as exc_info:
        cvn.main(["--repo", str(repo), "--quiet"])

    message = str(exc_info.value)
    assert "core/doctrine/a.md" in message
    assert "(1, 2)" in message  # both sites named, not just a count


# --- The shipped allowlist's own entry — kensaiapp_structure.md § Prompts layer ----------------

# The worked example's anchor, a snippet of its own text -- not a line number. This is the whole
# point of Task 1's key: the constant below needs no lookup against the file's current line count,
# because the entry it names now survives whatever edit moves it. (Before this task, these three
# tests located the site with `_worked_example_key()`, resolving the current line at read time —
# necessary only because the key itself was line-pinned. The anchor-keyed entry doesn't need a
# helper: the key IS the constant.)
WORKED_EXAMPLE_ANCHOR = "system/projects/product-planning"
STRUCTURE_PATH = "core/doctrine/setup/kensaiapp_structure.md"
SHIPPED_WORKED_EXAMPLE_KEY = f"{STRUCTURE_PATH}:{WORKED_EXAMPLE_ANCHOR}"


def test_the_shipped_entry_is_keyed_by_anchor_with_a_reason():
    allow = load_allowlist()
    assert SHIPPED_WORKED_EXAMPLE_KEY in allow, (
        f"the allowlist does not cover {SHIPPED_WORKED_EXAMPLE_KEY!r} — the shipped entry must "
        "be re-expressed in the path:<anchor> form"
    )
    assert allow[SHIPPED_WORKED_EXAMPLE_KEY].strip()


def test_no_shipped_allowlist_key_is_pinned_to_a_line_number():
    """Reached-when 1 — `path:line` is gone from the allowlist *format*, not merely from the one
    entry that broke. A key whose anchor is a bare number is the old, edit-fragile form coming
    back, and it comes back silently: it resolves against a hit whose text happens to contain that
    digit, so nothing else in this suite would notice."""
    for key in load_allowlist():
        _, _, anchor = key.partition(":")
        assert anchor, f"{key!r} carries no anchor — the key form is `path:<anchor>`"
        assert not anchor.isdigit(), f"{key!r} is line-pinned — the form this station replaced"


def test_no_shipped_allowlist_reason_says_only_provenance():
    """The station's own guardrail: 'no entry says only "provenance"' — every reason names why
    *that* site's citation is legitimate host-only provenance, not the word alone."""
    for key, reason in load_allowlist().items():
        assert reason.strip().lower() != "provenance", f"{key!r}: reason says only 'provenance'"


# --- scan_text: journey-stem detection (Task 3) -------------------------------------------------


def test_a_bare_dated_stem_with_no_path_is_reported():
    """A seed's path spells its position, so a pick/unpick/retire renames the file and kills a
    pointer on the host too — not only in a satellite. `versioning.md:95`'s live case: no path
    prefix at all, just the stem."""
    hits = scan_text(
        "f.md", "`2026-08-03_stamped-templates-never-resync` in the tools project's journey.", set()
    )
    assert len(hits) == 1
    assert hits[0].kind == "journey-stem"


def test_a_bare_dated_stem_with_md_extension_is_reported():
    """`check_satellites.py:10`'s original text: a bare stem, `.md` extension, no path prefix —
    fixed here as a fixture; `the-layer-passes-it` (Task 3) repaired the live site itself."""
    hits = scan_text(
        "f.py", "`2026-08-23_two-of-the-audit-satellites-three-layers-are-copies.md`).", set()
    )
    assert len(hits) == 1
    assert hits[0].kind == "journey-stem"


def test_a_stem_immediately_followed_by_a_slash_is_a_folder_not_reported():
    """`kensaiapp_structure.md` § Root's live case: `2026-08-03_perplexity-outside-review/` is a
    `docs/reviews/` folder, not a journey artifact."""
    hits = scan_text("f.md", "First folder: `2026-08-03_perplexity-outside-review/`.", set())
    assert hits == []


def test_a_prefixed_journey_stem_that_is_also_a_host_path_is_reported_once():
    hits = scan_text(
        "f.md",
        "See `system/projects/tools/journey/nemawashi/trail/2026-08-23_x.md` for the record.",
        {"tools"},
    )
    assert len(hits) == 1
    assert hits[0].kind == "host-path+journey-stem"


def test_a_stem_with_extra_slug_characters_after_md_and_slash_is_not_reported():
    """The `.md` check only consumes an immediate `.md`; a longer word is not truncated into a
    false stem+`.md`+`/` match."""
    hits = scan_text("f.md", "`2026-08-03_perplexity-outside-review-notes/`.", set())
    assert hits == []


# --- Live cases: the journey subset ------------------------------------------------------------


def test_no_live_journey_pointer_survives_in_core_or_skills():
    """The owner's ruling of 2026-08-31: settled machinery cites the fact's owner, never a seed or a
    station, and naming one instead of pathing it is the half-measure rather than the fix.

    This replaces a live-case test that asserted `versioning.md` still carried a bare stem. It did,
    and `the-layer-passes-it` allowlisted nine such pointers as provenance because the station's bar
    never restated the ruling. They were repaired instead, and this asserts the layer stays that way
    rather than asserting one site still holds the defect.
    """
    # Was `kind != "host-path"` — a proxy for "journey-stem" that held only while there were
    # exactly two kinds. The product-name kind (Task 6) walked straight through it, which is how a
    # filter phrased as "not the other one" fails: it silently widens the moment a third arrives.
    reported = [h for h in scan_repo(REPO) if "journey-stem" in h.kind]
    assert reported == [], (
        "a journey artifact is cited in vendored machinery again: "
        + ", ".join(f"{h.path}:{h.line}" for h in reported)
    )




def test_live_case_kensaiapp_structure_132_review_folder_is_not_reported():
    line = _line_containing("core/doctrine/setup/kensaiapp_structure.md", "2026-08-03_perplexity-outside-review/")
    hits = scan_text("core/doctrine/setup/kensaiapp_structure.md", line, set())
    assert hits == []


def test_an_unformatted_dated_stem_with_no_backtick_wrapping_at_all_is_reported():
    """A journey-stem with no markdown formatting whatsoever — no backticks, no code span —
    is still caught. `core/launchers/product-content/launcher.sh:54` was the live case this
    pinned (the continuation line of a wrapped host-path citation at `:53`) before
    `the-layer-passes-it` repaired it (Task 3); made synthetic here so it does not rot when the
    site it names moves or gets fixed."""
    hits = scan_text(
        "f.sh", "#   2026-08-23_nothing-checks-a-launchers-reporter-name-against-the-registry.md).", set()
    )
    assert len(hits) == 1
    assert hits[0].kind == "journey-stem"


# --- scan_repo counts both kinds (the set is now countable end-to-end) --------------------------


def test_scan_repo_counts_host_path_and_journey_stem_hits_together(tmp_path):
    repo = _repo(tmp_path)
    _commit_file(repo, "core/doctrine/a.md", "system/projects/alpha/journey/x.md\n")
    _commit_file(repo, "core/doctrine/b.md", "2026-01-01_a-seed in the journey\n")
    (repo / "system" / "projects" / "alpha").mkdir(parents=True)

    hits = scan_repo(repo)

    kinds = {(h.path, h.kind) for h in hits}
    assert ("core/doctrine/a.md", "host-path") in kinds
    assert ("core/doctrine/b.md", "journey-stem") in kinds


# --- main() (Task 4) --------------------------------------------------------------------------


def _allowlist_with_no_entries(repo: Path) -> Path:
    path = repo / "allow.json"
    path.write_text("{}", encoding="utf-8")
    return path


def test_main_returns_zero_on_a_clean_tree(tmp_path, monkeypatch):
    repo = _repo(tmp_path)
    _commit_file(repo, "core/tools/a.py", "clean\n")
    monkeypatch.setattr(cvn, "ALLOWLIST_PATH", _allowlist_with_no_entries(repo))

    assert cvn.main(["--repo", str(repo), "--quiet"]) == 0


def test_main_returns_one_when_a_hit_is_found(tmp_path, monkeypatch):
    repo = _repo(tmp_path)
    _commit_file(repo, "core/doctrine/a.md", "system/projects/alpha/journey/x.md\n")
    (repo / "system" / "projects" / "alpha").mkdir(parents=True)
    monkeypatch.setattr(cvn, "ALLOWLIST_PATH", _allowlist_with_no_entries(repo))

    assert cvn.main(["--repo", str(repo), "--quiet"]) == 1


def test_main_returns_one_when_only_a_stale_allowlist_entry_is_found(tmp_path, monkeypatch):
    repo = _repo(tmp_path)
    _commit_file(repo, "core/tools/a.py", "clean\n")
    allowlist = repo / "allow.json"
    stale_entry = {"core/doctrine/gone.md:1": "no longer real"}
    allowlist.write_text(json.dumps(stale_entry), encoding="utf-8")
    monkeypatch.setattr(cvn, "ALLOWLIST_PATH", allowlist)

    assert cvn.main(["--repo", str(repo), "--quiet"]) == 1


def test_main_prints_each_hit_and_the_totals(tmp_path, monkeypatch, capsys):
    repo = _repo(tmp_path)
    _commit_file(repo, "core/doctrine/a.md", "system/projects/alpha/journey/x.md\n")
    (repo / "system" / "projects" / "alpha").mkdir(parents=True)
    monkeypatch.setattr(cvn, "ALLOWLIST_PATH", _allowlist_with_no_entries(repo))

    exit_code = cvn.main(["--repo", str(repo)])

    out = capsys.readouterr().out
    assert exit_code == 1
    assert "core/doctrine/a.md:1" in out
    assert "1 hits, 0 stale allowlist entries" in out


def test_main_prints_a_clean_message_when_nothing_is_found(tmp_path, monkeypatch, capsys):
    repo = _repo(tmp_path)
    _commit_file(repo, "core/tools/a.py", "clean\n")
    monkeypatch.setattr(cvn, "ALLOWLIST_PATH", _allowlist_with_no_entries(repo))

    exit_code = cvn.main(["--repo", str(repo)])

    assert exit_code == 0
    assert "clean" in capsys.readouterr().out


def test_main_names_each_stale_entry_in_its_report(tmp_path, monkeypatch, capsys):
    """Reached-when 5 — the stale-entry *report* is kept, not just the exit code. A durable key
    makes a stale entry more meaningful, not redundant: it stops being drift and starts being
    evidence that the thing it excused has changed, which a reader can only act on if the report
    names the key."""
    repo = _repo(tmp_path)
    _commit_file(repo, "core/tools/a.py", "clean\n")
    allowlist = repo / "allow.json"
    allowlist.write_text(
        json.dumps({"core/doctrine/gone.md:an-anchor": "no longer real"}), encoding="utf-8"
    )
    monkeypatch.setattr(cvn, "ALLOWLIST_PATH", allowlist)

    exit_code = cvn.main(["--repo", str(repo)])

    out = capsys.readouterr().out
    assert exit_code == 1
    assert "core/doctrine/gone.md:an-anchor: STALE allowlist entry" in out
    assert "0 hits, 1 stale allowlist entries" in out


# --- Task 4: wiring and the precedent alongside it ----------------------------------------------


def test_pytest_collects_this_module_alongside_its_precedent():
    """`python3 -m pytest core/tools/ -q` collects both — the widened check and the narrow one it
    sits beside, unmodified."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "core/tools/test_check_vendor_neutrality.py",
         "core/tools/test_templates_are_instance_neutral.py", "-q", "--collect-only"],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


# --- Task 3: the module docstring states the anchor key, not path:line --------------------------


def test_docstring_no_longer_describes_a_path_line_key():
    assert "path:line" not in cvn.__doc__


def test_docstring_names_the_failure_that_produced_the_anchor_key():
    """Decision 2 must name why a line number was refused: the shipped entry went stale four
    commits after it was written, from an edit nine lines above the site it excused."""
    assert "four commits" in cvn.__doc__
    assert "nine lines" in cvn.__doc__


# --- product names: the third hit kind ---------------------------------------------------------
#
# The rule is `shared_core_instance.md` § *So a shared file names no product* — "Name no product in
# a file a satellite reads", every product name counting, not only a private one (the owner's
# ruling of 2026-09-02). Until this task nothing enforced it: the doctrine records the layer
# re-acquiring names after each sweep, 6 to 11 launchers between 2026-09-01 and 2026-09-05,
# "without anyone breaking a rule".


def _instance(root: Path, projects: dict[str, str]) -> Path:
    """A minimal instance tree: one `project.md` per name, carrying its `Product path:` line."""
    for name, product_path in projects.items():
        card = root / "system" / "projects" / name
        card.mkdir(parents=True, exist_ok=True)
        (card / "project.md").write_text(
            f"# Project Context — {name}\n\n**Product path:** {product_path}   <!-- a comment -->\n",
            encoding="utf-8",
        )
    return root


def test_satellite_roots_are_read_off_the_roster(tmp_path):
    """`system/satellites.md` carries the paths — and deliberately not the product names, which is
    why this is two steps rather than one."""
    (tmp_path / "system").mkdir(parents=True)
    (tmp_path / "system" / "satellites.md").write_text(
        "# Satellites of this host\n\n"
        "## Consumers\n\n"
        "| satellite | path |\n|---|---|\n"
        "| `alpha` | `/tmp/does-not-matter/alpha` |\n"
        "| `beta` | `/tmp/does-not-matter/beta` |\n\n"
        "## Producers\n\n"
        "| satellite | path |\n|---|---|\n"
        "| `gamma` | `/tmp/does-not-matter/gamma` |\n",
        encoding="utf-8",
    )
    assert cvn._satellite_roots(tmp_path) == [
        Path("/tmp/does-not-matter/alpha"),
        Path("/tmp/does-not-matter/beta"),
        Path("/tmp/does-not-matter/gamma"),
    ]


def test_a_missing_roster_yields_no_satellites(tmp_path):
    assert cvn._satellite_roots(tmp_path) == []


def test_only_an_external_product_contributes_a_name(tmp_path):
    """The discriminator, and the whole reason this hit kind is usable.

    An instance's own machinery is declared with a RELATIVE product path — `core/tools`,
    `.claude/skills`, `core/doctrine` — and taking those basenames would make `tools`, `skills` and
    `doctrine` product names and fire this check on most of the vendored layer. An external product
    is declared with an absolute path, which is the same absolute-versus-relative test every
    launcher already applies to decide `--add-dir`.
    """
    root = _instance(
        tmp_path,
        {
            "widget": "/somewhere/outside/widget-app",
            "machinery": "core/tools",
            "layer": ".claude/skills",
            "tilde": "~/products/gizmo",
        },
    )
    assert cvn._product_names_of(root) == {"widget-app", "widget", "gizmo", "tilde"}


def test_a_project_with_no_product_path_line_is_skipped(tmp_path):
    card = tmp_path / "system" / "projects" / "empty"
    card.mkdir(parents=True)
    (card / "project.md").write_text("# Project Context — empty\n\nnothing here\n", encoding="utf-8")
    assert cvn._product_names_of(tmp_path) == set()


def test_a_product_name_in_prose_is_reported():
    hits = scan_text("f.md", "The run authors the widget-app PRD.", set(), product_names={"widget-app"})
    assert [hit.kind for hit in hits] == ["product-name"]


def test_a_product_name_is_matched_case_insensitively():
    hits = scan_text("f.md", "Widget-App is the case material.", set(), product_names={"widget-app"})
    assert [hit.kind for hit in hits] == ["product-name"]


def test_a_product_name_inside_a_longer_word_is_not_a_hit():
    """`gizmo` must not fire on `gizmology`, or the check becomes noise its reader learns to skip."""
    hits = scan_text("f.md", "A note on gizmology and gizmos-adjacent work.", set(), product_names={"gizmo"})
    assert hits == []


def test_a_product_name_is_still_seen_inside_a_code_span():
    """Same reasoning the host-path kind already settled: a naive use-versus-mention strip erases
    most live references and leaves a check that looks green."""
    hits = scan_text("f.md", "see `widget-app/docs/PRD.md`", set(), product_names={"widget-app"})
    assert [hit.kind for hit in hits] == ["product-name"]


def test_a_line_tripping_a_host_path_and_a_product_name_is_reported_once_naming_both():
    hits = scan_text(
        "f.md",
        "system/projects/tools/ holds the widget-app notes.",
        {"tools"},
        product_names={"widget-app"},
    )
    assert len(hits) == 1
    assert hits[0].kind == "host-path+product-name"


def test_no_product_names_configured_leaves_every_line_clean():
    """The default is empty, so a caller that knows nothing of products sees the check it always
    saw — which is what keeps every pre-existing call site meaning what it meant."""
    assert scan_text("f.md", "The widget-app PRD.", set()) == []


# --- the third kind's coverage is stated, because it can silently shrink -----------------------


def _git_repo(root: Path) -> Path:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=root, check=True)
    return root


def test_product_name_sources_names_the_roots_it_could_not_read(tmp_path):
    """The one hazard this hit kind carries that the other two do not.

    The host-path and journey-stem kinds are decided from `repo` alone. This one reads OTHER
    instances, so a satellite that is absent, moved or unreadable means fewer names and a quieter
    run — a result indistinguishable from a clean one. So the sources are reported rather than
    assumed, the way the scan already reports its roots.
    """
    host = _instance(tmp_path / "host", {"local": "/outside/widget-app"})
    (host / "system").mkdir(parents=True, exist_ok=True)
    present = _instance(tmp_path / "present", {"remote": "/outside/gizmo"})
    absent = tmp_path / "gone"
    (host / "system" / "satellites.md").write_text(
        "| satellite | path |\n|---|---|\n"
        f"| `present` | `{present}` |\n"
        f"| `absent` | `{absent}` |\n",
        encoding="utf-8",
    )

    sources = cvn.product_name_sources(host)
    assert sources.names == {"widget-app", "local", "gizmo", "remote"}
    assert sources.read_roots == [host, present]
    assert sources.unread_roots == [absent]


def test_scan_repo_reports_a_product_name_in_a_vendored_file(tmp_path):
    repo = _git_repo(tmp_path)
    _instance(repo, {"local": "/outside/widget-app"})
    (repo / "core").mkdir()
    (repo / "core" / "note.md").write_text("The widget-app case.\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)

    hits = scan_repo(repo)
    assert [(hit.path, hit.kind) for hit in hits] == [("core/note.md", "product-name")]


def test_a_test_file_naming_a_product_is_reported(tmp_path):
    """A fixture ships with a release like any other file. The doctrine's carve-out says the name
    in a test "is a stand-in and is simply renamed" — renamed, which is what `--fix` does, never
    left unread. Reversed 2026-10-03, when a release cut from `core/` would have shipped two."""
    repo = _git_repo(tmp_path)
    _instance(repo, {"local": "/outside/widget-app"})
    (repo / "core").mkdir()
    (repo / "core" / "test_thing.py").write_text("# widget-app fixture\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)

    assert [(hit.path, hit.kind) for hit in scan_repo(repo)] == [
        ("core/test_thing.py", "product-name")
    ]


# --- satellite names, the home path and fixtures: what a release must not carry ---------------
# Every name below is invented. This file is scanned for real names like any other test file.


def _roster(root: Path, text: str) -> None:
    (root / "system").mkdir(parents=True, exist_ok=True)
    (root / "system" / "satellites.md").write_text(text, encoding="utf-8")


ROSTER = (
    "## Consumers\n\n| satellite | path |\n|---|---|\n"
    "| `kensaiapp-quill` | `/abs/kensaiapp-quill` |\n"
    "| `kensaiapp-ledger` | `/abs/kensaiapp-ledger` |\n\n"
    "## Names a release must not carry\n\n| name | why |\n|---|---|\n"
    "| `Quillco` | the platform kensaiapp-quill builds for |\n"
)


def test_declared_names_are_the_satellites_and_the_declared_section(tmp_path):
    """A release names no satellite (the owner, 2026-10-06), so each roster row's name counts,
    whole, beside every name the declared section lists."""
    _roster(tmp_path, ROSTER)
    assert cvn._declared_names(tmp_path) == {"Quillco", "kensaiapp-quill", "kensaiapp-ledger"}


def test_a_satellite_name_in_a_vendored_file_is_reported(tmp_path):
    _roster(tmp_path, ROSTER)
    names = cvn._declared_names(tmp_path)
    hits = scan_text("f.md", "the worked example is `kensaiapp-ledger`", set(), declared_names=names)
    assert [hit.kind for hit in hits] == ["declared-name"]


def test_a_longer_name_that_starts_with_a_satellite_name_is_not_it(tmp_path):
    """An agent called `kensaiapp-ledgerer` is not the satellite `kensaiapp-ledger`: the name is
    matched whole, so the agent's name does not fire."""
    _roster(tmp_path, ROSTER)
    names = cvn._declared_names(tmp_path)
    assert scan_text("f.md", "spawn a `kensaiapp-ledgerer`", set(), declared_names=names) == []


def test_no_roster_declares_nothing(tmp_path):
    assert cvn._declared_names(tmp_path) == set()


def test_a_satellite_name_is_never_cut_down_to_its_suffix(tmp_path):
    """Stripping `kensaiapp-` made `audit` a name and fired on 800 lines of ordinary prose."""
    _roster(tmp_path, ROSTER)
    names = cvn._declared_names(tmp_path)
    assert scan_text("f.md", "run the audit", set(), declared_names=names) == []


def test_a_declared_name_inside_a_satellite_name_is_seen(tmp_path):
    _roster(tmp_path, ROSTER)
    names = cvn._declared_names(tmp_path)
    hits = scan_text("f.md", "`kensaiapp-quillco` lives elsewhere", set(), declared_names=names)
    assert [hit.kind for hit in hits] == ["declared-name"]


def test_a_name_inside_a_tool_id_is_still_seen():
    """`\\b` treats `_` as part of a word, so `mcp__quillco-docs` hid the name."""
    hits = scan_text("f.md", "`mcp__quillco-docs`", set(), declared_names={"Quillco"})
    assert [hit.kind for hit in hits] == ["declared-name"]


def test_a_home_path_is_reported():
    hits = scan_text("f.py", '"cwd": "/Users/someone/projects/x"', set(), home="/Users/someone")
    assert [hit.kind for hit in hits] == ["home-path"]


def test_a_home_path_spelled_as_a_claude_project_folder_is_reported():
    """Claude Code names a project's transcript folder after its path, `/` turned to `-`, so a
    transcript path carries the home as `-Users-someone`."""
    line = 'Path("/projects/-Users-someone/sid-1.jsonl")'
    hits = scan_text("test_f.py", line, set(), home="/Users/someone", fixture=True)
    assert [hit.kind for hit in hits] == ["home-path"]


def test_a_fixture_is_read_for_names_but_not_for_host_paths_or_journey_stems():
    text = "system/projects/tools/ 2026-01-01_a-seed.md Quillco"
    hits = scan_text("test_x.py", text, {"tools"}, declared_names={"Quillco"}, fixture=True)
    assert [hit.kind for hit in hits] == ["declared-name"]


def test_scan_repo_reads_test_files_for_names(tmp_path):
    repo = _repo(tmp_path)
    _roster(repo, ROSTER)
    _commit_file(repo, "core/tools/test_a.py", 'NAME = "Quillco"\n')
    hits = scan_repo(repo)
    assert [(hit.path, hit.kind) for hit in hits] == [("core/tools/test_a.py", "declared-name")]


def test_scan_repo_reads_the_root_files_a_release_ships(tmp_path):
    repo = _repo(tmp_path)
    _roster(repo, ROSTER)
    _commit_file(repo, "core/x.md", "clean\n")
    _commit_file(repo, "AGENTS.md", "@kensaiapp-quill.md\n")
    _commit_file(repo, "Containerfile", 'SEED_REPO="/seed/kensaiapp-ledger"\n')
    assert sorted(hit.path for hit in scan_repo(repo)) == ["AGENTS.md", "Containerfile"]


def test_scan_repo_leaves_about_to_the_instance_that_manages_it(tmp_path):
    """`about/` ships, but its files are handed over unedited by another instance, which repairs
    them; a hit there is reported back, not raised here."""
    repo = _repo(tmp_path)
    _roster(repo, ROSTER)
    _commit_file(repo, "core/x.md", "clean\n")
    _commit_file(repo, "about/guide.md", "checked against kensaiapp-quill\n")
    assert scan_repo(repo) == []


def test_scan_repo_reads_the_whole_claude_layer(tmp_path):
    """A release carries `.claude/` whole — agents and hooks, not only skills."""
    repo = _repo(tmp_path)
    _roster(repo, ROSTER)
    _commit_file(repo, ".claude/agents/a.md", "built for Quillco\n")
    assert [hit.path for hit in scan_repo(repo)] == [".claude/agents/a.md"]


# --- repair ------------------------------------------------------------------------------------


def test_a_stand_in_is_stable_and_distinct_per_name():
    assert cvn.stand_in("Quillco") == cvn.stand_in("quillco")
    assert cvn.stand_in("Quillco") != cvn.stand_in("Inkwell")
    assert "quillco" not in cvn.stand_in("Quillco").lower()


def test_repair_text_renames_the_longest_name_whole_and_the_home_path():
    text = 'a = "kensaiapp-quill"; b = "quill"; c = "/Users/someone/x"'
    out = cvn.repair_text(text, {"kensaiapp-quill", "quill"}, "/Users/someone")
    assert out == (
        f'a = "{cvn.stand_in("kensaiapp-quill")}"; b = "{cvn.stand_in("quill")}"; '
        f'c = "{cvn.HOME_STAND_IN}/x"'
    )


def test_repair_text_renames_the_home_path_spelled_as_a_project_folder():
    out = cvn.repair_text('Path("/projects/-Users-someone/s.jsonl")', set(), "/Users/someone")
    assert out == 'Path("/projects/-home-user/s.jsonl")'


def _fixture_hit(path: str) -> Hit:
    return Hit(path=path, line=1, kind="declared-name", text="")


def _write(root: Path, relative: str, text: str) -> None:
    (root / relative).write_text(text, encoding="utf-8")


def test_repair_keeps_a_rewrite_that_breaks_no_test(tmp_path):
    _write(tmp_path, "test_a.py", 'N = "Quillco"\n')
    done = cvn.repair(tmp_path, [_fixture_hit("test_a.py")], {"Quillco"}, None, lambda r, p: set())
    assert done.kept == ["test_a.py"]
    assert "Quillco" not in (tmp_path / "test_a.py").read_text(encoding="utf-8")


def test_repair_keeps_a_rewrite_when_the_file_was_already_red(tmp_path):
    """A live-tree test waiting on this very sweep fails before and after; that is not the
    rewrite's doing."""
    _write(tmp_path, "test_a.py", 'N = "Quillco"\n')
    done = cvn.repair(
        tmp_path, [_fixture_hit("test_a.py")], {"Quillco"}, None, lambda r, p: {"test_a.py::live"}
    )
    assert done.kept == ["test_a.py"]


def test_repair_puts_back_a_rewrite_that_turns_a_test_red(tmp_path):
    _write(tmp_path, "test_a.py", 'N = "Quillco"\n')
    seen = []

    def failures(repo, relative):
        text = (repo / relative).read_text(encoding="utf-8")
        seen.append(text)
        return set() if "Quillco" in text else {"test_a.py::t"}

    done = cvn.repair(tmp_path, [_fixture_hit("test_a.py")], {"Quillco"}, None, failures)
    assert done.reverted == ["test_a.py"]
    assert "Quillco" not in seen[-1]  # asked again against the rewrite
    assert (tmp_path / "test_a.py").read_text(encoding="utf-8") == 'N = "Quillco"\n'


def test_repair_puts_back_a_file_it_cannot_run(tmp_path):
    _write(tmp_path, "test_a.py", 'N = "Quillco"\n')
    done = cvn.repair(tmp_path, [_fixture_hit("test_a.py")], {"Quillco"}, None, lambda r, p: None)
    assert done.reverted == ["test_a.py"]


def test_repair_never_touches_prose(tmp_path):
    """A name in doctrine carries a claim; renaming it leaves a false sentence. Hand repair."""
    _write(tmp_path, "a.md", "built for Quillco\n")
    done = cvn.repair(tmp_path, [_fixture_hit("a.md")], {"Quillco"}, None, lambda r, p: set())
    assert done.kept == [] and done.reverted == []


# --- a project a release ships whole: its own folders are read for names and the home path -----
# Every name below is invented, like the roster's above.

SHIPPED = (
    ROSTER
    + "\n## Projects a release ships\n\n| project | names it carries | why |\n|---|---|---|\n"
    + "| `widget` | `gadget-old` | the example |\n"
)


def _shipped_repo(tmp_path: Path) -> Path:
    repo = _repo(tmp_path)
    _roster(repo, SHIPPED)
    _commit_file(repo, "core/a.md")
    _commit_file(
        repo,
        "system/projects/widget/project.md",
        "**Product path:** products/widget   <!-- relative -->\n",
    )
    return repo


def test_shipped_projects_read_with_the_names_each_carries(tmp_path):
    _roster(tmp_path, SHIPPED)
    assert cvn._shipped_projects(tmp_path) == {"widget": {"gadget-old"}}


def test_no_shipped_section_ships_nothing_and_lists_no_files(tmp_path):
    """No project declared must be no files — never a bare `git ls-files` over the whole repo."""
    repo = _repo(tmp_path)
    _roster(repo, ROSTER)
    _commit_file(repo, "docs/a.md")
    assert _tracked_files(repo, shipped=True) == []


def test_a_shipped_project_brings_its_card_folder_and_its_in_repo_product(tmp_path):
    repo = _shipped_repo(tmp_path)
    assert list(cvn._shipped_roots(repo)) == ["system/projects/widget/", "products/widget/"]


def test_an_absolute_product_path_ships_nothing_from_this_repo(tmp_path):
    repo = _repo(tmp_path)
    _roster(repo, SHIPPED)
    _commit_file(repo, "system/projects/widget/project.md", "**Product path:** /abs/widget\n")
    assert list(cvn._shipped_roots(repo)) == ["system/projects/widget/"]


def test_a_shipped_projects_trail_is_left_out(tmp_path):
    repo = _shipped_repo(tmp_path)
    _commit_file(repo, "products/widget/docs/PRD.md")
    _commit_file(repo, "products/widget/docs/trail/prd/cycle-1.md")
    assert _tracked_files(repo, shipped=True) == [
        "products/widget/docs/PRD.md",
        "system/projects/widget/project.md",
    ]


def test_a_shipped_file_reports_a_name_and_the_home_path_but_not_its_own_paths(tmp_path):
    """The project ships with its journey, so a path into it and a dated stem point at something
    the reader has; a satellite's name and the home path do not."""
    repo = _shipped_repo(tmp_path)
    _commit_file(
        repo,
        "products/widget/docs/PRD.md",
        "system/projects/widget/ 2026-01-01_a-seed.md\nbuilt in kensaiapp-quill\nat /Users/someone/x\n",
    )
    hits = [(h.path, h.line, h.kind) for h in scan_repo(repo, home="/Users/someone")]
    assert hits == [
        ("products/widget/docs/PRD.md", 2, "declared-name"),
        ("products/widget/docs/PRD.md", 3, "home-path"),
    ]


def test_a_shipped_file_pointing_at_a_project_that_does_not_ship_is_a_hit(tmp_path):
    repo = _shipped_repo(tmp_path)
    _commit_file(repo, "system/projects/private/project.md", "**Product path:** products/private\n")
    _commit_file(repo, "products/widget/docs/PRD.md", "see system/projects/private/\n")
    assert [(h.path, h.kind) for h in scan_repo(repo)] == [
        ("products/widget/docs/PRD.md", "host-path")
    ]


def test_a_name_the_row_carries_is_not_a_hit_there_and_still_is_in_core(tmp_path):
    repo = _shipped_repo(tmp_path)
    (repo / "system" / "satellites.md").write_text(
        SHIPPED.replace("| `Quillco` |", "| `gadget-old` | a retired product |\n| `Quillco` |"),
        encoding="utf-8",
    )
    _commit_file(repo, "products/widget/docs/PRD.md", "drawn from gadget-old\n")
    _commit_file(repo, "core/b.md", "drawn from gadget-old\n")
    assert [(h.path, h.kind) for h in scan_repo(repo)] == [("core/b.md", "declared-name")]


def test_a_two_column_shipped_row_carries_its_names_and_is_no_declared_name(tmp_path):
    """Without the "why" column the row has the roster's two-backticked-cells shape; it must not be
    read as a satellite, which would make the shipped project a name the release refuses."""
    roster = ROSTER + "\n## Projects a release ships\n\n| `widget` | `gadget-old` |\n"
    _roster(tmp_path, roster)
    assert cvn._shipped_projects(tmp_path) == {"widget": {"gadget-old"}}
    assert "widget" not in cvn._declared_names(tmp_path)


def test_a_shipped_project_with_no_card_is_refused_not_passed(tmp_path):
    repo = _repo(tmp_path)
    _roster(repo, SHIPPED)
    _commit_file(repo, "core/a.md")
    with pytest.raises(RuntimeError, match="does not exist"):
        scan_repo(repo)


def test_a_shipped_folder_that_tracks_nothing_is_refused(tmp_path):
    repo = _shipped_repo(tmp_path)  # products/widget/ holds no tracked file
    with pytest.raises(RuntimeError, match="tracks no file"):
        scan_repo(repo)


def test_a_product_path_of_the_repo_root_ships_nothing_from_it(tmp_path):
    repo = _repo(tmp_path)
    _roster(repo, SHIPPED)
    _commit_file(repo, "system/projects/widget/project.md", "**Product path:** .\n")
    assert list(cvn._shipped_roots(repo)) == ["system/projects/widget/"]


def test_a_product_inside_a_vendored_root_is_refused(tmp_path):
    repo = _repo(tmp_path)
    _roster(repo, SHIPPED)
    _commit_file(repo, "system/projects/widget/project.md", "**Product path:** core/tools\n")
    with pytest.raises(RuntimeError, match="overlaps a vendored root"):
        cvn._shipped_roots(repo)


def test_fix_never_rewrites_a_shipped_projects_tests(tmp_path, monkeypatch):
    """Its tests are the product's own and their names are real — not stand-ins."""
    repo = _shipped_repo(tmp_path)
    _commit_file(repo, "products/widget/tests/test_w.py", "# from gadget-old, built in kensaiapp-quill\n")
    seen = []
    monkeypatch.setattr(cvn, "repair", lambda r, hits, *a: seen.extend(hits) or cvn.Repair())
    monkeypatch.setattr(cvn, "ALLOWLIST_PATH", tmp_path / "none.json")
    cvn.main(["--repo", str(repo), "--fix", "--quiet"])
    assert seen == []
