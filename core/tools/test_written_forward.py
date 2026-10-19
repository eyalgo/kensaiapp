"""Tests for `written_forward.py`'s pure half — the phrase set and the scope predicate.

No git, no filesystem, no repo. `written_forward.py` is the single source the pytest, the
`pre-commit` shim, and the `PreToolUse` harness hook all read, so that three copies of one phrase
set cannot drift.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

import written_forward as wf


# --- PATTERNS — each shape matches its own one-line input ------------------------------


def _matches(text: str) -> bool:
    return bool(wf.violations_in(text))


def test_p1_status_stub_matches():
    assert _matches("**Status: stub.**")


def test_p2_this_is_a_stub_matches():
    assert _matches("This file is a stub.")


def test_p3_not_yet_variants_match():
    assert _matches("not yet built")
    assert _matches("not yet wired")
    assert _matches("not yet written")
    assert _matches("not yet implemented")


def test_p4_planned_later_matches():
    assert _matches("planned later")


def test_p5_not_yet_stood_up_matches():
    assert _matches("⚠ not yet stood up")


def test_p6_currently_a_stub_matches():
    assert _matches("currently a stub")


def test_p7_stub_marker_matches():
    assert _matches("STUB — always PASS.")


def test_p8_tbd_marker_matches():
    assert _matches("Layers 6–7 — TBD")


# --- case sensitivity is a deliberate discriminator on P7/P8 ----------------------------


def test_lowercase_stub_alone_does_not_match():
    assert not _matches("a doctrine stub, a directory stub, or a test stub")


def test_lowercase_tbd_does_not_match():
    assert not _matches("the value here is tbd, ask the owner")


# --- use versus mention: fence / inline-code / double-quote stripping -------------------


def test_fenced_backtick_block_is_not_a_match():
    text = "```\nStatus: stub\n```\n"
    assert not _matches(text)


def test_fenced_tilde_block_is_not_a_match():
    text = "~~~\nStatus: stub\n~~~\n"
    assert not _matches(text)


def test_inline_code_span_is_not_a_match():
    assert not _matches("Quoting `Status: stub` as an example of the rule.")


def test_double_quoted_span_is_not_a_match():
    assert not _matches('The banned phrase is "not yet wired", written out.')


def test_blockquote_is_a_match():
    assert _matches("> **Status: stub.**")


# --- violations_in return shape ----------------------------------------------------------


def test_violations_in_returns_one_based_line_numbers_and_stripped_text():
    text = "line one\nStatus: stub\nline three\n"
    hits = wf.violations_in(text)
    assert hits == [(2, "Status: stub")]


# --- the docstring's WHERE IT LOOKS — the live-journey change and its ground -------------


def test_docstring_states_the_live_journey_change_and_names_its_ground():
    """The docstring no longer says a project's `journey/` stays out, unqualified — only its
    retired half does — and names `check_journey_links.py` as the owner of *live*ness (owner's
    ruling, 2026-08-31; station: the-checker-reads-a-live-seed)."""
    assert "journey/` is a record and stays out —" not in wf.__doc__
    assert "check_journey_links.py" in wf.__doc__
    assert "2026-08-31" in wf.__doc__


def test_docstring_says_the_doctrine_exempts_a_sentence_kind_not_a_folder():
    """The rest of task 2's intent, which the negative assertion above cannot carry: § WHERE IT
    LOOKS has to say *why* the location exemption was wrong — the doctrine exempts a sentence
    kind, cited to the clause that says so — and has to qualify what is still out. Without these
    the test above passes on a docstring that merely dropped the old sentence."""
    assert "written_forward.md:108-110" in wf.__doc__
    assert "sentence *kind*" in wf.__doc__
    assert "stay out" in wf.__doc__
    # Named individually rather than as one phrase: the sentence gained `drop/` on 2026-09-04 and a
    # bar pinned to the whole clause fails on a widening that keeps its meaning exactly.
    for bin_ in ("`trail/`", "`drop/`", "`parked/`"):
        assert bin_ in wf.__doc__, bin_


# --- in_scope --------------------------------------------------------------------------


def test_in_scope_true_for_authored_roots():
    assert wf.in_scope("AGENTS.md")
    assert wf.in_scope("CLAUDE.md")
    assert wf.in_scope("kensaiapp.md")
    assert wf.in_scope("core/doctrine/governance/x.md")
    assert wf.in_scope("system/loaders/pm.md")
    assert wf.in_scope(".claude/skills/s/SKILL.md")


def test_in_scope_false_for_record_subtrees():
    assert not wf.in_scope(".claude/skills/s/evals/inputs/x.md")
    assert not wf.in_scope(".claude/skills/s/evidence/iteration-1/result.md")
    assert not wf.in_scope(".claude/skills/s/examples/v1/x.md")


def test_in_scope_true_for_the_instances_own_doctrine():
    """Added 2026-08-14 — the files an agent loads to act include the instance's own governing set."""
    assert wf.in_scope("system/doctrine/ai_responsibility.md")
    assert wf.in_scope("system/experience/visual_restrictions.md")
    assert wf.in_scope("system/projects/dev-skills/doctrine/skills_doctrine.md")


def test_in_scope_false_for_the_journey_of_the_project_named_doctrine():
    """The reason `system/projects/*/doctrine/` is positional and not a substring test.

    `system/projects/doctrine/` is a project, and its live `journey/nemawashi/` is now in scope
    (station: the-checker-reads-a-live-seed) — but a `"/doctrine/" in path` test would still be
    wrong, because it would scope in that project's `trail/`, which stays a record.
    """
    assert wf.in_scope("system/projects/doctrine/doctrine/doctrine_doctrine.md")
    assert wf.in_scope("system/projects/doctrine/journey/nemawashi/seed.md")
    assert not wf.in_scope("system/projects/doctrine/journey/shukuba/trail/station.md")


def test_in_scope_false_outside_scoped_roots():
    assert not wf.in_scope("docs/proposals/p/ad_hoc_plan.md")


# --- the live journey — seedbed roots, `unpicked/`, open station roots (owner's ruling, 2026-08-31)


def test_in_scope_true_for_a_project_seedbed_root_seed():
    """A seed at a project seedbed root is live and in scope."""
    assert wf.in_scope("system/projects/tools/journey/nemawashi/seed.md")


def test_in_scope_false_for_the_same_seed_retired_or_parked():
    assert not wf.in_scope("system/projects/tools/journey/nemawashi/trail/seed.md")
    assert not wf.in_scope("system/projects/tools/journey/shukuba/parked/station.md")


def test_in_scope_true_for_the_instance_seedbed_and_false_for_its_trail():
    assert wf.in_scope("system/nemawashi/seed.md")
    assert wf.in_scope("system/shukuba/station.md")
    assert not wf.in_scope("system/nemawashi/trail/seed.md")
    assert not wf.in_scope("system/shukuba/trail/station.md")


def test_in_scope_true_for_an_open_station_at_the_project_layer():
    assert wf.in_scope("system/projects/tools/journey/shukuba/2026-09-01_station.md")


def test_in_scope_true_for_the_unpicked_candidate_pool_at_both_layers():
    assert wf.in_scope("system/nemawashi/unpicked/idea.md")
    assert wf.in_scope("system/projects/tools/journey/nemawashi/unpicked/idea.md")


def test_in_scope_false_for_a_folder_readme_in_the_live_journey():
    """A folder README.md is the folder's own description, not a seed."""
    assert not wf.in_scope("system/nemawashi/README.md")
    assert not wf.in_scope("system/shukuba/README.md")
    assert not wf.in_scope("system/nemawashi/unpicked/README.md")
    assert not wf.in_scope("system/projects/tools/journey/nemawashi/README.md")


def test_scoped_roots_predating_the_live_journey_change_are_unaffected():
    """Reached-when 1's last clause: every path the suite pinned before this station still
    resolves exactly as it did — the live-journey patterns are provably an addition, not a
    rewrite of the pre-existing scope."""
    unchanged = [
        ("AGENTS.md", True),
        ("CLAUDE.md", True),
        ("kensaiapp.md", True),
        ("core/doctrine/governance/x.md", True),
        ("system/loaders/pm.md", True),
        (".claude/skills/s/SKILL.md", True),
        (".claude/skills/s/evals/inputs/x.md", False),
        (".claude/skills/s/evidence/iteration-1/result.md", False),
        (".claude/skills/s/examples/v1/x.md", False),
        ("system/doctrine/ai_responsibility.md", True),
        ("system/experience/visual_restrictions.md", True),
        ("system/projects/dev-skills/doctrine/skills_doctrine.md", True),
        ("system/projects/doctrine/doctrine/doctrine_doctrine.md", True),
        ("system/projects/doctrine/journey/shukuba/trail/station.md", False),
        ("docs/proposals/p/ad_hoc_plan.md", False),
        ("core/tools/written_forward.py", False),
        ("skills/g/.claude/skills/x/SKILL.md", True),
        (".claude/skills/x/SKILL.md", True),
        ("skills/g/.claude/skills/x/evals/inputs/y.md", False),
        ("skills/g/README.md", True),
        ("system/projects/dev-skills/journey/x.md", False),
    ]
    for path, expected in unchanged:
        assert wf.in_scope(path) is expected, path


def test_in_scope_false_for_non_markdown():
    assert not wf.in_scope("core/tools/written_forward.py")


# --- the folder-seed shape — only `seed.md` is gated, and only at a live bin --------------
#
# A seed is `<slug>.md` or a folder `<slug>/` holding `seed.md` plus, per sealed unit,
# `<key>_report.md` and `<key>_recommendations.md`. Only `seed.md` is under this gate — the reports
# are records (`written_forward.md` § *What this does not touch*, "The journey is the record").


def test_in_scope_true_for_a_folder_seeds_seed_md_at_a_project_root_and_under_unpicked():
    assert wf.in_scope("system/projects/tools/journey/nemawashi/2026-09-01_a-seed/seed.md")
    assert wf.in_scope(
        "system/projects/tools/journey/nemawashi/unpicked/2026-09-01_a-seed/seed.md"
    )


def test_in_scope_false_for_a_folder_seeds_seed_md_under_trail_or_drop():
    assert not wf.in_scope(
        "system/projects/tools/journey/nemawashi/trail/2026-09-01_a-seed/seed.md"
    )
    assert not wf.in_scope(
        "system/projects/tools/journey/nemawashi/drop/2026-09-01_a-seed/seed.md"
    )


def test_in_scope_true_for_a_folder_seeds_seed_md_at_the_instance_seedbed():
    assert wf.in_scope("system/nemawashi/2026-09-01_a-seed/seed.md")
    assert wf.in_scope("system/nemawashi/unpicked/2026-09-01_a-seed/seed.md")


def test_in_scope_false_for_a_folder_seeds_seed_md_at_the_instance_trail_or_drop():
    assert not wf.in_scope("system/nemawashi/trail/2026-09-01_a-seed/seed.md")
    assert not wf.in_scope("system/nemawashi/drop/2026-09-01_a-seed/seed.md")


def test_in_scope_false_for_a_folder_seeds_report_and_recommendations_at_every_root():
    for root in ("", "unpicked/", "trail/", "drop/"):
        report = f"system/nemawashi/{root}2026-09-01_a-seed/2026-09-05_a-key_report.md"
        recommendations = (
            f"system/nemawashi/{root}2026-09-01_a-seed/2026-09-05_a-key_recommendations.md"
        )
        assert not wf.in_scope(report), report
        assert not wf.in_scope(recommendations), recommendations


def test_scan_tree_reports_a_folder_seeds_seed_md_narrating_its_own_maturity(tmp_path):
    repo = _repo(tmp_path)
    relative = "system/projects/p/journey/nemawashi/2026-09-01_a-seed/seed.md"
    _commit_file(repo, relative, _NARRATES_ITS_OWN_MATURITY)

    assert relative in wf.scan_tree(repo)


def test_scan_tree_ignores_a_folder_seeds_report_narrating_the_seeds_own_maturity(tmp_path):
    """The report is a record of what the run did — it may legitimately describe a seed as a
    stub — and this gate does not read records (`WHERE IT LOOKS`)."""
    repo = _repo(tmp_path)
    relative = "system/projects/p/journey/nemawashi/2026-09-01_a-seed/2026-09-05_a-key_report.md"
    _commit_file(repo, relative, _NARRATES_ITS_OWN_MATURITY)

    assert wf.scan_tree(repo) == {}


# --- the grouped root — a skill that moved under `skills/<group>/` (station: the-two-gates) ---


def test_in_scope_true_for_a_skill_under_the_grouped_root():
    """The second root brings a moved skill's SKILL.md into scope; the flat root is unchanged."""
    assert wf.in_scope("skills/g/.claude/skills/x/SKILL.md")
    assert wf.in_scope(".claude/skills/x/SKILL.md")


def test_in_scope_false_for_record_subtrees_under_the_grouped_root():
    """Condition 2 — the record exclusion wins under the second root too, the way
    `test_in_scope_false_for_record_subtrees` proves it under the flat one."""
    assert not wf.in_scope("skills/g/.claude/skills/x/evals/inputs/y.md")
    assert not wf.in_scope("skills/g/.claude/skills/x/evidence/iteration-1/result.md")
    assert not wf.in_scope("skills/g/.claude/skills/x/examples/v1/x.md")


def test_in_scope_true_for_any_markdown_under_a_grouped_skill_root():
    """Condition 3 — the breadth of the bare `"skills/"` prefix is pinned: it scopes every
    markdown file under a group root, not only `SKILL.md`, symmetrically with `".claude/skills/"`
    scoping the whole flat tree."""
    assert wf.in_scope("skills/g/README.md")
    assert wf.in_scope("skills/g/.claude/skills/x/notes.md")


def test_in_scope_false_for_a_path_that_merely_contains_skills_without_starting_with_it():
    """Condition 4 — the near-miss a prefix invites: `dev-skills` contains the literal `skills/`
    but the path does not start with it, so it stays out of scope."""
    assert not wf.in_scope("system/projects/dev-skills/journey/x.md")


# --- module surface -----------------------------------------------------------------------


def test_pattern_count_and_record_segments():
    assert len(wf.PATTERNS) == 8
    assert wf.RECORD_SEGMENTS == ("/evals/", "/evidence/", "/examples/")


# =========================================================================================
# The repo-facing half, and the CLI both hooks reach — layer 2, real tmp_path git repos.
# =========================================================================================


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=True
    ).stdout


def _repo(tmp_path: Path) -> Path:
    """An initialized git repo, ready to commit into."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@example.com")
    _git(repo, "config", "user.name", "t")
    return repo


def _commit_file(repo: Path, relative: str, content: str) -> None:
    path = repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    _git(repo, "add", relative)
    _git(repo, "commit", "-qm", relative)


def _stage_file(repo: Path, relative: str, content: str) -> None:
    path = repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    _git(repo, "add", relative)


# --- scoped_markdown reads the repo passed, not the module's location -------------------


def test_scoped_markdown_reads_the_repo_passed(tmp_path):
    repo = _repo(tmp_path)
    _commit_file(repo, "core/doctrine/a.md", "clean\n")

    files = wf.scoped_markdown(repo)

    assert files == ["core/doctrine/a.md"]


def test_scoped_markdown_includes_untracked_not_ignored(tmp_path):
    repo = _repo(tmp_path)
    (repo / "core" / "doctrine").mkdir(parents=True)
    (repo / "core" / "doctrine" / "untracked.md").write_text("clean\n", encoding="utf-8")

    assert "core/doctrine/untracked.md" in wf.scoped_markdown(repo)


def test_scoped_markdown_excludes_a_gitignored_file(tmp_path):
    repo = _repo(tmp_path)
    (repo / ".gitignore").write_text("core/doctrine/ignored.md\n", encoding="utf-8")
    _git(repo, "add", ".gitignore")
    _git(repo, "commit", "-qm", "gitignore")
    (repo / "core" / "doctrine").mkdir(parents=True)
    (repo / "core" / "doctrine" / "ignored.md").write_text("clean\n", encoding="utf-8")

    assert "core/doctrine/ignored.md" not in wf.scoped_markdown(repo)


def test_gitignore_ignores_grouped_and_flat_eval_workspaces_but_not_evals_json(tmp_path):
    """Conditions 5 and 6 (station: the-two-gates) — the `.gitignore` gains a second form
    alongside the flat one, proved by `git check-ignore` rather than by a command run once.

    Condition 7's answer, recorded here because this is where the interaction is provable:
    `scoped_markdown()` enumerates through `git ls-files --exclude-standard`, so a normally-staged
    workspace file never reaches `in_scope()` at all — `.gitignore` alone is what keeps it out.
    `in_scope()`'s own `/evals/` segment exclusion (condition 2) is the belt for the one path
    `.gitignore` cannot stop: a file force-added with `git add -f`, which bypasses `.gitignore`
    but still lands under an `/evals/` segment and is still excluded there. Belt-and-braces, not a
    dead second gate.
    """
    repo = _repo(tmp_path)
    _commit_file(
        repo,
        ".gitignore",
        ".claude/skills/*/evals/workspace/\n"
        "skills/*/.claude/skills/*/evals/workspace/\n",
    )

    grouped = _git(repo, "check-ignore", "-v", "skills/g/.claude/skills/x/evals/workspace/f.md")
    assert "skills/*/.claude/skills/*/evals/workspace/" in grouped

    flat = _git(repo, "check-ignore", "-v", ".claude/skills/x/evals/workspace/f.md")
    assert ".claude/skills/*/evals/workspace/" in flat

    with pytest.raises(subprocess.CalledProcessError):
        _git(repo, "check-ignore", "-v", "skills/g/.claude/skills/x/evals/evals.json")


def test_scoped_markdown_excludes_a_record_subtree_even_when_tracked(tmp_path):
    repo = _repo(tmp_path)
    _commit_file(repo, ".claude/skills/s/evals/inputs/x.md", "Status: stub\n")

    assert wf.scoped_markdown(repo) == []


# --- the live journey, by effect on a fixture tree — reached-when 1 ----------------------
#
# Reached-when 1 asks for the scope change to be "asserted by effect on a fixture tree, one test
# per folder, not by reading the constant back". The `in_scope` cases above read a path string;
# these build the folder, put a seed in it that narrates its own maturity, and ask the scanner
# what it reports — so `scoped_markdown`'s `git ls-files` walk and `violations_in` are in the
# loop, not just the predicate. The same seed body is used in every folder, so the only variable
# is where the file sits.


_NARRATES_ITS_OWN_MATURITY = (
    "# 根回し Nemawashi seed — the route\n"
    "\n"
    "**Status: stub.** The checklist is not yet written.\n"
)

_LIVE_JOURNEY_FOLDERS = [
    "system/nemawashi/2026-09-01_seed.md",
    "system/nemawashi/unpicked/2026-09-01_seed.md",
    "system/shukuba/2026-09-01_station.md",
    "system/projects/p/journey/nemawashi/2026-09-01_seed.md",
    "system/projects/p/journey/nemawashi/unpicked/2026-09-01_seed.md",
    "system/projects/p/journey/shukuba/2026-09-01_station.md",
]

_RETIRED_JOURNEY_FOLDERS = [
    "system/nemawashi/trail/2026-09-01_seed.md",
    "system/shukuba/trail/2026-09-01_station.md",
    "system/projects/p/journey/nemawashi/trail/2026-09-01_seed.md",
    "system/projects/p/journey/shukuba/trail/2026-09-01_station.md",
    "system/projects/p/journey/shukuba/parked/2026-09-01_station.md",
]


@pytest.mark.parametrize("relative", _LIVE_JOURNEY_FOLDERS)
def test_scan_tree_reports_a_seed_narrating_its_own_maturity_in_each_live_folder(
    tmp_path, relative
):
    """A seedbed root, an `unpicked/` pool and an open station root, at both layers."""
    repo = _repo(tmp_path)
    _commit_file(repo, relative, _NARRATES_ITS_OWN_MATURITY)

    assert relative in wf.scan_tree(repo)


@pytest.mark.parametrize("relative", _RETIRED_JOURNEY_FOLDERS)
def test_scan_tree_ignores_the_same_seed_in_each_retired_folder(tmp_path, relative):
    """`trail/` and `parked/` are the record the doctrine's carve-out protects. Identical bytes
    to the live case above, so a hit here would be about the folder and nothing else."""
    repo = _repo(tmp_path)
    _commit_file(repo, relative, _NARRATES_ITS_OWN_MATURITY)

    assert wf.scan_tree(repo) == {}


@pytest.mark.parametrize(
    "relative",
    [
        "system/nemawashi/README.md",
        "system/nemawashi/unpicked/README.md",
        "system/projects/p/journey/shukuba/README.md",
    ],
)
def test_scan_tree_ignores_a_folder_readme_sitting_in_a_live_journey_folder(tmp_path, relative):
    """A folder's own description is not a seed, so it is out even at a live root."""
    repo = _repo(tmp_path)
    _commit_file(repo, relative, _NARRATES_ITS_OWN_MATURITY)

    assert wf.scan_tree(repo) == {}


def test_scan_tree_over_a_whole_journey_reports_the_live_half_and_only_it(tmp_path):
    """The folders together, in one tree: nothing leaks across, and every live folder is
    still found when the retired ones sit beside it."""
    repo = _repo(tmp_path)
    for relative in _LIVE_JOURNEY_FOLDERS + _RETIRED_JOURNEY_FOLDERS:
        _commit_file(repo, relative, _NARRATES_ITS_OWN_MATURITY)

    assert sorted(wf.scan_tree(repo)) == sorted(_LIVE_JOURNEY_FOLDERS)


def test_scoped_markdown_over_this_instance_returns_more_than_100_paths():
    """Guard the guard: keeps the intent of the old whole-repo file-count check, now that the
    vacuous-pass risk moved into a function that takes a root."""
    instance_repo = Path(__file__).resolve().parents[2]

    files = wf.scoped_markdown(instance_repo)

    assert len(files) > 100, f"only {len(files)} markdown files found under {instance_repo}"


# --- scan_staged reads the index, not the working tree -----------------------------------


def test_scan_staged_reports_a_file_staged_dirty(tmp_path):
    repo = _repo(tmp_path)
    _stage_file(repo, "core/doctrine/x.md", "Status: stub\n")

    found = wf.scan_staged(repo)

    assert found == {"core/doctrine/x.md": [(1, "Status: stub")]}


def test_scan_staged_reports_nothing_when_the_clean_version_is_staged(tmp_path):
    repo = _repo(tmp_path)
    _commit_file(repo, "core/doctrine/x.md", "clean\n")
    (repo / "core" / "doctrine" / "x.md").write_text("Status: stub\n", encoding="utf-8")
    # working tree is dirty; the index still holds the clean version.

    assert wf.scan_staged(repo) == {}


def test_scan_staged_reports_nothing_for_a_dirty_unstaged_file(tmp_path):
    repo = _repo(tmp_path)
    _commit_file(repo, "core/doctrine/x.md", "clean\n")
    (repo / "core" / "doctrine" / "x.md").write_text("Status: stub\n", encoding="utf-8")
    # never staged — dirty on disk only.

    assert wf.scan_staged(repo) == {}


def test_a_staged_deletion_produces_no_read_and_no_error(tmp_path):
    repo = _repo(tmp_path)
    _commit_file(repo, "core/doctrine/x.md", "clean\n")
    _git(repo, "rm", "-q", "core/doctrine/x.md")

    assert wf.scan_staged(repo) == {}


def test_scan_staged_reads_the_added_half_of_a_staged_rename(tmp_path):
    """`--no-renames` is what makes a rename appear as its two halves, so the added path is
    read on its own. Under git's default rename detection the pair collapses to a single `R`
    entry, which `--diff-filter=ACM` drops — and a file renamed *and* dirtied would slip the
    gate entirely."""
    repo = _repo(tmp_path)
    body = "\n".join(f"line {n} of ordinary prose that stays identical" for n in range(40))
    _commit_file(repo, "core/doctrine/a.md", body + "\n")
    _git(repo, "mv", "core/doctrine/a.md", "core/doctrine/b.md")
    _stage_file(repo, "core/doctrine/b.md", body + "\nStatus: stub\n")

    assert wf.scan_staged(repo) == {"core/doctrine/b.md": [(41, "Status: stub")]}


def test_scan_tree_skips_a_tracked_path_missing_from_disk(tmp_path):
    """A tracked file deleted from the working tree is still listed by `git ls-files`; reading
    it would raise, so `--report` must skip it rather than crash."""
    repo = _repo(tmp_path)
    _commit_file(repo, "core/doctrine/gone.md", "Status: stub\n")
    _commit_file(repo, "core/doctrine/here.md", "Status: stub\n")
    (repo / "core" / "doctrine" / "gone.md").unlink()

    assert wf.scan_tree(repo) == {"core/doctrine/here.md": [(1, "Status: stub")]}


# --- the CLI ------------------------------------------------------------------------------


def test_staged_exits_1_and_prints_the_offending_path_and_line(tmp_path, capsys):
    repo = _repo(tmp_path)
    _stage_file(repo, "core/doctrine/x.md", "Status: stub\n")

    code = wf.main(["--staged", "--repo", str(repo)])

    assert code == 1
    err = capsys.readouterr().err
    assert "core/doctrine/x.md:1:" in err
    assert "Write it forward" in err
    assert "--no-verify" in err


def test_staged_message_says_the_whole_staged_file_is_read(tmp_path, capsys):
    """The two surfaces read different things, deliberately: the `PreToolUse` guard reads only
    the text being written, this reads the whole staged blob. So a clean edit to a file carrying
    older debt passes the guard and is refused here — the ratchet working, not an inconsistency.
    The message a person is stopped by has to say that, or the sequence reads as a contradiction:
    the line they are shown is one they did not write."""
    repo = _repo(tmp_path)
    _commit_file(repo, "core/doctrine/x.md", "Status: stub\nkeep this line\n")
    _stage_file(repo, "core/doctrine/x.md", "Status: stub\nkeep this line, edited cleanly\n")

    assert wf.main(["--staged", "--repo", str(repo)]) == 1
    err = capsys.readouterr().err
    assert "whole staged file" in err
    assert "ratchet" in err


def test_staged_exits_0_on_a_clean_index(tmp_path):
    repo = _repo(tmp_path)
    _commit_file(repo, "core/doctrine/x.md", "clean\n")

    assert wf.main(["--staged", "--repo", str(repo)]) == 0


def test_staged_exits_0_on_an_empty_index(tmp_path):
    repo = _repo(tmp_path)

    assert wf.main(["--staged", "--repo", str(repo)]) == 0


def test_report_exits_0_over_a_repo_that_carries_violations_and_prints_them(tmp_path, capsys):
    repo = _repo(tmp_path)
    _commit_file(repo, "core/doctrine/x.md", "Status: stub\n")

    code = wf.main(["--report", "--repo", str(repo)])

    assert code == 0
    out = capsys.readouterr().out
    assert "core/doctrine/x.md:1:" in out
    assert "1 files, 1 lines" in out


def test_repo_flag_defaults_to_show_toplevel_in_process_cwd(tmp_path, capsys, monkeypatch):
    repo = _repo(tmp_path)
    _commit_file(repo, "core/doctrine/x.md", "Status: stub\n")
    monkeypatch.chdir(repo)

    code = wf.main(["--report"])

    assert code == 0
    assert "core/doctrine/x.md:1:" in capsys.readouterr().out


def test_neither_staged_nor_report_is_a_usage_error(tmp_path):
    repo = _repo(tmp_path)

    with pytest.raises(SystemExit) as excinfo:
        wf.main(["--repo", str(repo)])

    assert excinfo.value.code == 2


def test_both_staged_and_report_is_a_usage_error(tmp_path):
    repo = _repo(tmp_path)

    with pytest.raises(SystemExit) as excinfo:
        wf.main(["--staged", "--report", "--repo", str(repo)])

    assert excinfo.value.code == 2


# --- integrity review: the plan's Task 3 behaviour at project level ----------------------------
#
# Written from `shukuba-refine-runs-and-its-seed-becomes-a-folder.md` § Task 3, not from the code:
# "`…/nemawashi/<slug>/<key>_report.md` and `…_recommendations.md` are out of scope at every root."


def test_in_scope_false_for_a_project_folder_seeds_report_and_recommendations_at_every_root():
    for root in ("", "unpicked/", "trail/", "drop/"):
        base = f"system/projects/tools/journey/nemawashi/{root}2026-09-01_a-seed"
        for leaf in ("2026-09-05_a-key_report.md", "2026-09-05_a-key_recommendations.md"):
            assert not wf.in_scope(f"{base}/{leaf}"), f"{base}/{leaf}"


def test_in_scope_false_for_a_folder_seed_shape_under_a_shukuba_root():
    """The folder form is a seed's only; a station folder never gains a gated `seed.md`."""
    assert not wf.in_scope("system/projects/tools/journey/shukuba/2026-09-01_a-station/seed.md")
    assert not wf.in_scope("system/shukuba/2026-09-01_a-station/seed.md")


def test_in_scope_false_for_a_file_literally_named_seed_md_at_a_trail_or_drop_root():
    """`trail/seed.md` is a flat trail entry, not a folder-seed whose slug is `trail`."""
    for bin_ in ("trail", "drop"):
        assert not wf.in_scope(f"system/nemawashi/{bin_}/seed.md")
        assert not wf.in_scope(f"system/projects/tools/journey/nemawashi/{bin_}/seed.md")
