#!/usr/bin/env python3
"""Contract tests for `check_journey_links.py`.

The two that matter are the line-wrap case and the scope case: both are defects the tool exists to
catch and both are invisible to the obvious implementation. A `grep` for a path finds nothing when
the path wraps inside a backtick span, and a repo-wide sweep drowns the live seedbeds in hundreds of
`trail/` references that are correct as history.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from check_journey_links import (
    Dead,
    _live_files,
    dead_links,
    default_host,
    docs_files,
    instance_name,
    instance_roots,
    docs_roots,
    main,
    malformed_links,
    malformed_triples,
    pointers,
    product_docs_roots,
)


def _instance(tmp_path: Path) -> Path:
    """A minimal instance tree: one project journey plus the instance seedbed."""
    for d in [
        "system/nemawashi/unpicked",
        "system/nemawashi/trail",
        "system/nemawashi/drop",
        "system/shukuba",
        "system/projects/alpha/journey/nemawashi/unpicked",
        "system/projects/alpha/journey/nemawashi/trail",
        "system/projects/alpha/journey/nemawashi/drop",
        "system/projects/alpha/journey/shukuba/parked",
    ]:
        (tmp_path / d).mkdir(parents=True, exist_ok=True)
    return tmp_path


# --- pointers() ------------------------------------------------------------------


def test_a_pointer_that_wraps_a_line_is_still_found():
    """The defect that makes an eye-check and a naive grep both pass."""
    text = (
        "See\n"
        "`system/projects/alpha/journey/nemawashi/unpicked/\n"
        "  2026-01-01_a-seed.md` for the rest.\n"
    )
    assert pointers(text) == [
        "system/projects/alpha/journey/nemawashi/unpicked/2026-01-01_a-seed.md"
    ]


def test_prose_containing_a_slash_is_not_a_pointer():
    assert pointers("`journey/nemawashi/ is the seedbed`") == []
    assert pointers("`system/projects/alpha/project.md`") == []


def test_every_seedbed_position_is_recognised():
    for p in [
        "system/nemawashi/2026-01-01_x.md",
        "system/nemawashi/unpicked/2026-01-01_x.md",
        "system/nemawashi/trail/2026-01-01_x.md",
        "system/nemawashi/drop/2026-01-01_x.md",
        "system/shukuba/2026-01-01_x.md",
        "system/projects/alpha/journey/nemawashi/2026-01-01_x.md",
        "system/projects/alpha/journey/nemawashi/unpicked/2026-01-01_x.md",
        "system/projects/alpha/journey/nemawashi/drop/2026-01-01_x.md",
        "system/projects/alpha/journey/shukuba/parked/2026-01-01_x.md",
    ]:
        assert pointers(f"`{p}`") == [p], p


# --- dead_links() ----------------------------------------------------------------


def test_a_resolving_pointer_is_not_dead(tmp_path):
    repo = _instance(tmp_path)
    target = "system/projects/alpha/journey/nemawashi/unpicked/2026-01-01_target.md"
    (repo / target).write_text("# target\n")
    (repo / "system/nemawashi/unpicked/2026-01-01_source.md").write_text(f"points at `{target}`\n")
    assert dead_links(repo) == []


def test_a_pointer_at_a_moved_seed_is_dead(tmp_path):
    """The whole point: the seed was retired, so the `unpicked/` path no longer resolves."""
    repo = _instance(tmp_path)
    (repo / "system/projects/alpha/journey/nemawashi/trail/2026-01-01_target.md").write_text("x\n")
    stale = "system/projects/alpha/journey/nemawashi/unpicked/2026-01-01_target.md"
    (repo / "system/nemawashi/unpicked/2026-01-01_source.md").write_text(f"`{stale}`\n")

    found = dead_links(repo)
    assert [d.target for d in found] == [stale]
    assert found[0].source == "system/nemawashi/unpicked/2026-01-01_source.md"


def test_a_pointer_at_a_dropped_seed_resolves(tmp_path):
    """The case the drop verb creates: three live seeds cite a seed that is killed, and the file is
    still there. A path `drop/` is not in the pattern is not reported dead — it is not recognised as a
    journey path at all, so it is skipped silently, which reads exactly like a pass."""
    repo = _instance(tmp_path)
    target = "system/nemawashi/drop/2026-01-01_killed.md"
    (repo / target).write_text("# killed\n")
    (repo / "system/nemawashi/unpicked/2026-01-01_source.md").write_text(f"points at `{target}`\n")
    assert pointers(f"`{target}`") == [target]
    assert dead_links(repo) == []


def test_a_pointer_at_a_seed_that_was_dropped_is_dead(tmp_path):
    """And the inverse — the pointer still names the pool, so the drop broke it and it is reported."""
    repo = _instance(tmp_path)
    (repo / "system/nemawashi/drop/2026-01-01_killed.md").write_text("x\n")
    stale = "system/nemawashi/unpicked/2026-01-01_killed.md"
    (repo / "system/nemawashi/2026-01-01_source.md").write_text(f"`{stale}`\n")
    assert [d.target for d in dead_links(repo)] == [stale]


def test_drop_is_out_of_scope_by_default_and_in_scope_under_all(tmp_path):
    """A dropped seed is a record, like a retired one — its pointers are correct as history."""
    repo = _instance(tmp_path)
    (repo / "system/nemawashi/drop/2026-01-01_killed.md").write_text(
        "`system/projects/alpha/journey/nemawashi/2026-01-01_gone.md`\n"
    )
    assert dead_links(repo) == []
    assert len(dead_links(repo, everywhere=True)) == 1


def test_trail_is_out_of_scope_by_default_and_in_scope_under_all(tmp_path):
    """A retired seed naming where a sibling sat is correct as history."""
    repo = _instance(tmp_path)
    (repo / "system/nemawashi/trail/2026-01-01_retired.md").write_text(
        "`system/projects/alpha/journey/nemawashi/2026-01-01_gone.md`\n"
    )
    assert dead_links(repo) == []
    assert len(dead_links(repo, everywhere=True)) == 1


def test_the_same_dead_target_twice_in_one_file_is_reported_once(tmp_path):
    repo = _instance(tmp_path)
    stale = "system/projects/alpha/journey/nemawashi/2026-01-01_gone.md"
    (repo / "system/nemawashi/unpicked/2026-01-01_source.md").write_text(f"`{stale}` and `{stale}`\n")
    assert len(dead_links(repo)) == 1


def test_readme_files_are_not_scanned(tmp_path):
    """Seedbed READMEs describe the shape and name example paths that need not exist."""
    repo = _instance(tmp_path)
    (repo / "system/nemawashi/README.md").write_text(
        "`system/projects/alpha/journey/nemawashi/2026-01-01_example.md`\n"
    )
    assert dead_links(repo) == []


# --- main() ----------------------------------------------------------------------


def test_exit_code_is_information_not_a_gate(tmp_path, capsys):
    repo = _instance(tmp_path)
    assert main(["--repo", str(repo)]) == 0
    assert "resolves" in capsys.readouterr().out

    (repo / "system/nemawashi/unpicked/2026-01-01_source.md").write_text(
        "`system/projects/alpha/journey/nemawashi/2026-01-01_gone.md`\n"
    )
    assert main(["--repo", str(repo)]) == 1


def test_it_never_repairs(tmp_path):
    """The tool reports. A run must leave every file byte-identical."""
    repo = _instance(tmp_path)
    src = repo / "system/nemawashi/unpicked/2026-01-01_source.md"
    body = "`system/projects/alpha/journey/nemawashi/2026-01-01_gone.md`\n"
    src.write_text(body)
    main(["--repo", str(repo), "--quiet"])
    assert src.read_text() == body


def test_a_non_instance_root_is_usage_not_a_finding(tmp_path, capsys):
    assert main(["--repo", str(tmp_path)]) == 2
    assert "is this an instance root?" in capsys.readouterr().err


@pytest.mark.parametrize("flag", ["--quiet"])
def test_quiet_prints_nothing(tmp_path, capsys, flag):
    repo = _instance(tmp_path)
    (repo / "system/nemawashi/unpicked/2026-01-01_source.md").write_text(
        "`system/projects/alpha/journey/nemawashi/2026-01-01_gone.md`\n"
    )
    assert main(["--repo", str(repo), flag]) == 1
    assert capsys.readouterr().out == ""


# --- the project-relative shape --------------------------------------------------
#
# A routing seed names the project in prose and leaves the path bare in the span. Before the tool
# matched this shape it produced no finding for it at all, which reads exactly like a clean file —
# measured 2026-09-05, when a run reported one dead pointer over thirty it could not see.


def test_a_project_relative_pointer_is_a_pointer():
    assert pointers("`journey/nemawashi/unpicked/2026-01-01_a-seed.md`") == [
        "journey/nemawashi/unpicked/2026-01-01_a-seed.md"
    ]
    assert pointers("`journey/shukuba/trail/2026-01-01_a-station.md`") == [
        "journey/shukuba/trail/2026-01-01_a-station.md"
    ]


def test_a_placeholder_is_not_a_project_relative_pointer():
    """`<seed>.md` is a template's grammar, not a file anyone can resolve."""
    assert pointers("`journey/nemawashi/unpicked/<seed>.md`") == []


def test_a_project_relative_pointer_resolves_under_any_project(tmp_path):
    repo = _instance(tmp_path)
    (repo / "system/projects/alpha/journey/nemawashi/unpicked/2026-01-01_a-seed.md").write_text("x")
    (repo / "system/nemawashi/unpicked/router.md").write_text(
        "`alpha`'s `journey/nemawashi/unpicked/2026-01-01_a-seed.md`\n"
    )
    assert dead_links(repo) == []


def test_a_project_relative_pointer_that_resolves_nowhere_is_dead(tmp_path):
    repo = _instance(tmp_path)
    (repo / "system/nemawashi/unpicked/router.md").write_text(
        "`alpha`'s `journey/nemawashi/unpicked/2026-01-01_a-seed.md`\n"
    )
    dead = dead_links(repo)
    assert [d.target for d in dead] == ["journey/nemawashi/unpicked/2026-01-01_a-seed.md"]


def test_the_whole_relative_path_must_match_not_the_filename(tmp_path):
    """Seed basenames are not unique across this tree, so a filename search would lie.

    The target names `unpicked/`; the file sits in `trail/`. That is precisely the move that kills a
    pointer, so resolving it on the basename would report the seedbed clean at the one moment it is
    not.
    """
    repo = _instance(tmp_path)
    (repo / "system/projects/alpha/journey/nemawashi/trail/2026-01-01_a-seed.md").write_text("x")
    (repo / "system/nemawashi/unpicked/router.md").write_text(
        "`alpha`'s `journey/nemawashi/unpicked/2026-01-01_a-seed.md`\n"
    )
    assert [d.target for d in dead_links(repo)] == [
        "journey/nemawashi/unpicked/2026-01-01_a-seed.md"
    ]


# --- the folder-seed shape — `<slug>/seed.md`, and its per-unit report/recommendations --------
#
# A seed becomes a folder holding `seed.md` plus, per sealed unit, `<key>_report.md` and
# `<key>_recommendations.md`. Every path below is nemawashi-only — a shukuba station never takes
# the folder form.


def _write(repo: Path, relative: str, content: str) -> None:
    path = repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_a_folder_seed_path_is_a_pointer_at_a_seedbed_root_and_under_unpicked_trail_drop():
    for bin_ in ("", "unpicked/", "trail/", "drop/"):
        p = f"system/nemawashi/{bin_}2026-01-01_a-seed/seed.md"
        assert pointers(f"`{p}`") == [p], p


def test_a_folder_seeds_report_path_is_a_pointer_at_every_bin():
    for bin_ in ("", "unpicked/", "trail/", "drop/"):
        p = (
            f"system/projects/alpha/journey/nemawashi/{bin_}"
            "2026-01-01_a-seed/2026-02-01_unit_report.md"
        )
        assert pointers(f"`{p}`") == [p], p


def test_the_relative_folder_seed_shape_is_a_pointer():
    assert pointers("`journey/nemawashi/unpicked/2026-01-01_a-seed/seed.md`") == [
        "journey/nemawashi/unpicked/2026-01-01_a-seed/seed.md"
    ]
    assert pointers("`journey/nemawashi/2026-01-01_a-seed/2026-02-01_unit_recommendations.md`") == [
        "journey/nemawashi/2026-01-01_a-seed/2026-02-01_unit_recommendations.md"
    ]


def test_a_folder_seeds_seed_md_at_root_or_unpicked_is_live_by_default(tmp_path):
    repo = _instance(tmp_path)
    target = "system/nemawashi/2026-01-01_a-seed/seed.md"
    _write(repo, target, "# seed\n")
    (repo / "system/nemawashi/unpicked/2026-01-02_source.md").write_text(f"`{target}`\n")

    assert dead_links(repo) == []


def test_a_dead_pointer_at_a_folder_seeds_seed_md_is_reported(tmp_path):
    repo = _instance(tmp_path)
    stale = "system/nemawashi/2026-01-01_gone/seed.md"
    (repo / "system/nemawashi/unpicked/2026-01-02_source.md").write_text(f"`{stale}`\n")

    assert [d.target for d in dead_links(repo)] == [stale]


def test_a_folder_seed_under_trail_or_drop_is_scanned_only_under_all(tmp_path):
    repo = _instance(tmp_path)
    _write(
        repo,
        "system/nemawashi/trail/2026-01-01_a-seed/seed.md",
        "`system/projects/alpha/journey/nemawashi/2026-01-01_gone.md`\n",
    )
    assert dead_links(repo) == []
    assert len(dead_links(repo, everywhere=True)) == 1


def test_a_flat_pointer_resolves_once_the_seed_it_names_has_become_a_folder(tmp_path):
    """The plan's own "Decided here": a pointer written as `<slug>.md` resolves when
    `<slug>/seed.md` exists — the folder migration is invisible to a pointer aimed at the idea."""
    repo = _instance(tmp_path)
    flat_target = "system/nemawashi/unpicked/2026-01-01_a-seed.md"
    _write(repo, "system/nemawashi/unpicked/2026-01-01_a-seed/seed.md", "# seed\n")
    (repo / "system/nemawashi/2026-01-02_source.md").write_text(f"`{flat_target}`\n")

    assert dead_links(repo) == []


def test_a_flat_pointer_is_dead_when_neither_the_flat_file_nor_the_folder_form_exists(tmp_path):
    repo = _instance(tmp_path)
    flat_target = "system/nemawashi/unpicked/2026-01-01_gone.md"
    (repo / "system/nemawashi/2026-01-02_source.md").write_text(f"`{flat_target}`\n")

    assert [d.target for d in dead_links(repo)] == [flat_target]


def test_a_relative_flat_pointer_resolves_once_the_seed_it_names_has_become_a_folder(tmp_path):
    repo = _instance(tmp_path)
    _write(
        repo,
        "system/projects/alpha/journey/nemawashi/unpicked/2026-01-01_a-seed/seed.md",
        "x",
    )
    (repo / "system/nemawashi/unpicked/router.md").write_text(
        "`alpha`'s `journey/nemawashi/unpicked/2026-01-01_a-seed.md`\n"
    )
    assert dead_links(repo) == []


# --- integrity review: the plan's Task 2 behaviours the implementation's tests left open -------
#
# Written from `shukuba-refine-runs-and-its-seed-becomes-a-folder.md` § Task 2, not from the code.


@pytest.mark.parametrize(
    "seed_md",
    [
        "system/nemawashi/2026-01-01_a-seed/seed.md",
        "system/nemawashi/unpicked/2026-01-01_a-seed/seed.md",
        "system/projects/alpha/journey/nemawashi/2026-01-01_a-seed/seed.md",
        "system/projects/alpha/journey/nemawashi/unpicked/2026-01-01_a-seed/seed.md",
    ],
)
def test_a_live_folder_seeds_seed_md_is_checked_as_a_source_by_default(tmp_path, seed_md):
    """"A folder-seed's `seed.md` at a seedbed root or in `unpicked/` is a live file" — its own
    dead pointer is reported without `--all`."""
    repo = _instance(tmp_path)
    stale = "system/nemawashi/unpicked/2026-01-01_gone.md"
    _write(repo, seed_md, f"`{stale}`\n")

    assert [(d.source, d.target) for d in dead_links(repo)] == [(seed_md, stale)]


@pytest.mark.parametrize("bin_", ["trail", "drop"])
def test_a_folder_seeds_seed_md_under_trail_or_drop_is_checked_only_under_all(tmp_path, bin_):
    repo = _instance(tmp_path)
    _write(
        repo,
        f"system/projects/alpha/journey/nemawashi/{bin_}/2026-01-01_a-seed/seed.md",
        "`system/nemawashi/unpicked/2026-01-01_gone.md`\n",
    )

    assert dead_links(repo) == []
    assert [d.target for d in dead_links(repo, everywhere=True)] == [
        "system/nemawashi/unpicked/2026-01-01_gone.md"
    ]


def test_the_relative_folder_seed_shape_is_a_pointer_under_trail_and_drop():
    for bin_ in ("trail/", "drop/"):
        for leaf in ("seed.md", "2026-02-01_unit_report.md"):
            p = f"journey/nemawashi/{bin_}2026-01-01_a-seed/{leaf}"
            assert pointers(f"`{p}`") == [p], p


def test_a_pointer_to_a_folder_seeds_report_resolves_when_it_exists_and_is_dead_when_not(tmp_path):
    repo = _instance(tmp_path)
    folder = "system/projects/alpha/journey/nemawashi/unpicked/2026-01-01_a-seed"
    alive = f"{folder}/2026-02-01_unit_report.md"
    dead = f"{folder}/2026-02-02_other_recommendations.md"
    _write(repo, f"{folder}/seed.md", "# seed\n")
    _write(repo, alive, "# report\n")
    (repo / "system/nemawashi/2026-01-02_source.md").write_text(f"`{alive}` and `{dead}`\n")

    assert [d.target for d in dead_links(repo)] == [dead]


def test_a_relative_pointer_into_a_folder_seed_resolves_and_is_dead_when_missing(tmp_path):
    repo = _instance(tmp_path)
    _write(
        repo,
        "system/projects/alpha/journey/nemawashi/unpicked/2026-01-01_a-seed/"
        "2026-02-01_unit_report.md",
        "# report\n",
    )
    alive = "journey/nemawashi/unpicked/2026-01-01_a-seed/2026-02-01_unit_report.md"
    dead = "journey/nemawashi/unpicked/2026-01-01_a-seed/2026-02-09_missing_report.md"
    (repo / "system/nemawashi/unpicked/router.md").write_text(f"`{alive}` `{dead}`\n")

    assert [d.target for d in dead_links(repo)] == [dead]


def test_a_relative_flat_pointer_is_dead_when_neither_form_exists(tmp_path):
    repo = _instance(tmp_path)
    target = "journey/nemawashi/unpicked/2026-01-01_gone.md"
    (repo / "system/nemawashi/unpicked/router.md").write_text(f"`alpha`'s `{target}`\n")

    assert [d.target for d in dead_links(repo)] == [target]


def test_a_flat_pointer_still_resolves_to_the_flat_file_when_it_exists(tmp_path):
    """The folder-form fallback is a second try, never a replacement: the plain file-seed case keeps
    its answer."""
    repo = _instance(tmp_path)
    target = "system/projects/alpha/journey/nemawashi/unpicked/2026-01-01_a-seed.md"
    _write(repo, target, "# seed\n")
    (repo / "system/nemawashi/2026-01-02_source.md").write_text(f"`{target}`\n")

    assert dead_links(repo) == []

# --- the triple shape — `<project> · <kind> · <name>` -----------------------------
#
# A path pointer names a journey artifact's *position*, which a pick, un-pick, retire, drop or park
# renames out from under it. The triple names the artifact instead — project, kind and name — none
# of which a move changes (`single_source.md` § *A pointer at a journey artifact names project, kind
# and name`), which is where the written form is pinned. Every fixture below is invented — a real
# project name or a real dated stem in vendored machinery is the citation
# `check_vendor_neutrality.py` § *An allowlist entry may not excuse a journey pointer* refuses, and
# a `test_`-prefixed file is out of its scan only because a fixture name is a stand-in.

_TRIPLE = "alpha · nemawashi · 2026-01-01_a-seed-with-a-name-long-enough-to-wrap-a-line"


# pointers() ------------------------------------------------------------------------


def test_a_well_formed_triple_in_a_span_is_returned():
    assert pointers(f"`{_TRIPLE}`") == [_TRIPLE]


def test_a_triple_split_across_a_line_break_inside_the_span_is_returned_identically():
    """The trap the one-span form exists to defeat — same defect the path shapes already guard."""
    text = (
        "See\n"
        "`alpha · nemawashi ·\n"
        "  2026-01-01_a-seed-with-a-name-long-enough-to-wrap-a-line` for the rest.\n"
    )
    assert pointers(text) == [_TRIPLE]


def test_a_middot_sequence_outside_any_backtick_span_is_not_returned():
    assert pointers(_TRIPLE) == []


def test_a_triple_with_an_invalid_kind_is_not_returned():
    assert pointers("`alpha · seedbed · 2026-01-01_a-seed`") == []


def test_a_triple_whose_name_carries_dot_md_or_a_slash_is_not_returned():
    assert pointers("`alpha · nemawashi · 2026-01-01_a-seed.md`") == []
    assert pointers("`alpha · nemawashi · 2026-01-01_a-seed/seed.md`") == []


def test_a_path_pointer_is_still_returned_and_a_triple_is_distinguishable_from_it():
    path = "system/nemawashi/unpicked/2026-01-01_a-seed.md"
    found = pointers(f"`{path}` and `{_TRIPLE}`")
    assert found == [path, _TRIPLE]
    # a caller tells them apart on the presence of a slash — a triple never has one
    assert "/" in found[0] and "/" not in found[1]


# resolves() / dead_links() — the five positions ------------------------------------


@pytest.mark.parametrize(
    "triple, artifact",
    [
        (
            "alpha · nemawashi · 2026-01-01_a-seed",
            "system/projects/alpha/journey/nemawashi/2026-01-01_a-seed.md",
        ),
        (
            "alpha · nemawashi · 2026-01-01_a-seed",
            "system/projects/alpha/journey/nemawashi/unpicked/2026-01-01_a-seed.md",
        ),
        (
            "alpha · nemawashi · 2026-01-01_a-seed",
            "system/projects/alpha/journey/nemawashi/trail/2026-01-01_a-seed.md",
        ),
        (
            "alpha · nemawashi · 2026-01-01_a-seed",
            "system/projects/alpha/journey/nemawashi/drop/2026-01-01_a-seed.md",
        ),
        (
            "alpha · shukuba · 2026-01-01_a-station",
            "system/projects/alpha/journey/shukuba/parked/2026-01-01_a-station.md",
        ),
    ],
)
def test_a_triple_resolves_to_its_artifact_in_any_of_the_five_positions(tmp_path, triple, artifact):
    """The property the whole idea rests on — one unchanged triple, five positions."""
    repo = _instance(tmp_path)
    _write(repo, artifact, "x\n")
    (repo / "system/nemawashi/unpicked/2026-01-02_source.md").write_text(f"`{triple}`\n")

    assert dead_links(repo) == []


def test_a_folder_seed_resolves_by_its_folder_name_never_a_file_inside_it(tmp_path):
    repo = _instance(tmp_path)
    _write(repo, "system/projects/alpha/journey/nemawashi/2026-01-01_a-seed/seed.md", "# seed\n")
    triple = "alpha · nemawashi · 2026-01-01_a-seed"
    (repo / "system/nemawashi/unpicked/2026-01-02_source.md").write_text(f"`{triple}`\n")

    assert dead_links(repo) == []


def test_a_tobiishi_resolves_by_its_folder_name(tmp_path):
    repo = _instance(tmp_path)
    (repo / "system/projects/alpha/journey/tobiishi/2026-01-01_a-change").mkdir(parents=True)
    triple = "alpha · tobiishi · 2026-01-01_a-change"
    (repo / "system/nemawashi/unpicked/2026-01-02_source.md").write_text(f"`{triple}`\n")

    assert dead_links(repo) == []


def test_a_tobiishi_in_trail_resolves_by_its_folder_name(tmp_path):
    repo = _instance(tmp_path)
    (repo / "system/projects/alpha/journey/tobiishi/trail/2026-01-01_a-change").mkdir(parents=True)
    triple = "alpha · tobiishi · 2026-01-01_a-change"
    (repo / "system/nemawashi/unpicked/2026-01-02_source.md").write_text(f"`{triple}`\n")

    assert dead_links(repo) == []


def test_a_tobiishi_in_drop_resolves_by_its_folder_name(tmp_path):
    repo = _instance(tmp_path)
    (repo / "system/projects/alpha/journey/tobiishi/drop/2026-01-01_a-change").mkdir(parents=True)
    triple = "alpha · tobiishi · 2026-01-01_a-change"
    (repo / "system/nemawashi/unpicked/2026-01-02_source.md").write_text(f"`{triple}`\n")

    assert dead_links(repo) == []


def test_the_instance_project_token_resolves_under_the_instance_seedbed(tmp_path):
    repo = _instance(tmp_path)
    _write(repo, "system/nemawashi/unpicked/2026-01-01_a-seed.md", "x\n")
    triple = "instance · nemawashi · 2026-01-01_a-seed"
    (repo / "system/shukuba/source.md").write_text(f"`{triple}`\n")

    assert dead_links(repo) == []


def test_the_instance_project_token_does_not_resolve_to_a_same_named_project_seed(tmp_path):
    repo = _instance(tmp_path)
    _write(repo, "system/projects/alpha/journey/nemawashi/2026-01-01_a-seed.md", "x\n")
    triple = "instance · nemawashi · 2026-01-01_a-seed"
    (repo / "system/shukuba/source.md").write_text(f"`{triple}`\n")

    assert [d.target for d in dead_links(repo)] == [triple]


def test_a_triple_naming_a_real_name_under_the_wrong_kind_does_not_resolve(tmp_path):
    repo = _instance(tmp_path)
    _write(repo, "system/projects/alpha/journey/nemawashi/2026-01-01_a-seed.md", "x\n")
    triple = "alpha · shukuba · 2026-01-01_a-seed"
    (repo / "system/nemawashi/unpicked/source.md").write_text(f"`{triple}`\n")

    assert [d.target for d in dead_links(repo)] == [triple]


def test_a_triple_naming_a_real_name_under_the_wrong_project_does_not_resolve(tmp_path):
    repo = _instance(tmp_path)
    _write(repo, "system/projects/alpha/journey/nemawashi/2026-01-01_a-seed.md", "x\n")
    triple = "beta · nemawashi · 2026-01-01_a-seed"
    (repo / "system/nemawashi/unpicked/source.md").write_text(f"`{triple}`\n")

    assert [d.target for d in dead_links(repo)] == [triple]


# dead_links() — dead-naming and the corrupted-count property ----------------------


def test_a_dead_triple_is_named_with_the_triple_as_its_target(tmp_path):
    repo = _instance(tmp_path)
    stale = "alpha · nemawashi · 2026-01-01_gone"
    (repo / "system/nemawashi/unpicked/source.md").write_text(f"`{stale}`\n")

    assert [d.target for d in dead_links(repo)] == [stale]


def test_corrupting_one_good_triple_raises_the_dead_count_by_exactly_one(tmp_path):
    """A resolver that silently matches nothing reports identically to one that works — so this
    asserts the rise, never merely the clean start."""
    repo = _instance(tmp_path)
    _write(repo, "system/projects/alpha/journey/nemawashi/2026-01-01_a-seed.md", "x\n")
    good = "alpha · nemawashi · 2026-01-01_a-seed"
    source = repo / "system/nemawashi/unpicked/source.md"
    source.write_text(f"`{good}`\n")
    assert dead_links(repo) == []

    corrupted = "alpha · nemawashi · 2026-01-01_gone"
    source.write_text(f"`{corrupted}`\n")
    assert len(dead_links(repo)) == 1


def test_exit_code_for_a_dead_triple_matches_the_path_case(tmp_path):
    repo = _instance(tmp_path)
    (repo / "system/nemawashi/unpicked/source.md").write_text(
        "`alpha · nemawashi · 2026-01-01_gone`\n"
    )
    assert main(["--repo", str(repo)]) == 1

    (repo / "system/nemawashi/unpicked/source.md").write_text("no pointers here\n")
    assert main(["--repo", str(repo)]) == 0


def test_all_widens_triple_scope_to_trail_drop_parked_same_as_paths(tmp_path):
    repo = _instance(tmp_path)
    (repo / "system/nemawashi/trail/2026-01-01_retired.md").write_text(
        "`alpha · nemawashi · 2026-01-01_gone`\n"
    )
    assert dead_links(repo) == []
    assert len(dead_links(repo, everywhere=True)) == 1


def test_a_file_carrying_both_a_path_pointer_and_a_triple_reports_each_independently(tmp_path):
    repo = _instance(tmp_path)
    dead_path = "system/projects/alpha/journey/nemawashi/unpicked/2026-01-01_gone.md"
    dead_triple = "alpha · nemawashi · 2026-01-01_also-gone"
    (repo / "system/nemawashi/unpicked/source.md").write_text(
        f"`{dead_path}` and `{dead_triple}`\n"
    )

    found = {d.target for d in dead_links(repo)}
    assert found == {dead_path, dead_triple}


# --- integrity pass — behaviours the station states that no test above asserts -------
#
# Written from `the-checker-resolves-the-key`'s plan (Tasks 1-3 and reached-when 2), never from
# the implementation: each one names a sentence of the intent that had no test.


def test_a_break_before_the_middot_returns_the_same_string_as_an_unwrapped_triple():
    """Task 1 says a wrapped triple comes back *identically*. The collapse is not symmetric around
    the separator — a break before `·` eats the space that preceded it, a break after eats the one
    that followed — so both sides of the separator need the same answer."""
    stem = "2026-01-01_a-seed-with-a-name-long-enough-to-wrap-a-line"
    before = f"See `alpha · nemawashi\n· {stem}` end.\n"
    after = f"See `alpha · nemawashi ·\n{stem}` end.\n"
    assert pointers(before) == pointers(after) == [_TRIPLE]


@pytest.mark.parametrize("bin_", ["", "unpicked", "trail", "drop"])
def test_the_instance_token_resolves_in_every_bin_of_the_instance_seedbed(tmp_path, bin_):
    """Task 2: `instance · nemawashi · <name>` resolves under `system/nemawashi/` *and its bins*."""
    repo = _instance(tmp_path)
    where = f"system/nemawashi/{bin_}/2026-01-01_a-seed.md" if bin_ else "system/nemawashi/2026-01-01_a-seed.md"
    _write(repo, where, "x\n")
    (repo / "system/shukuba/source.md").write_text("`instance · nemawashi · 2026-01-01_a-seed`\n")

    assert dead_links(repo) == []


def test_the_instance_token_resolves_a_station_under_the_router(tmp_path):
    """`single_source.md` § *A pointer at a journey artifact names project, kind and name* names
    both instance-level seedbeds — the seedbed and the router station."""
    repo = _instance(tmp_path)
    _write(repo, "system/shukuba/2026-01-01_a-station.md", "x\n")
    (repo / "system/nemawashi/unpicked/source.md").write_text(
        "`instance · shukuba · 2026-01-01_a-station`\n"
    )

    assert dead_links(repo) == []


def test_an_instance_tobiishi_never_resolves(tmp_path):
    """The doctrine's own claim: there is no instance Tobiishi, so the triple naming one is dead."""
    repo = _instance(tmp_path)
    _write(repo, "system/projects/alpha/journey/tobiishi/2026-01-01_a-change/x.md", "x\n")
    triple = "instance · tobiishi · 2026-01-01_a-change"
    (repo / "system/nemawashi/unpicked/source.md").write_text(f"`{triple}`\n")

    assert [d.target for d in dead_links(repo)] == [triple]


def test_a_tobiishi_named_by_a_file_rather_than_a_folder_does_not_resolve(tmp_path):
    """Task 2: a Tobiishi resolves by its folder name, *never* by a file — the negative half."""
    repo = _instance(tmp_path)
    _write(repo, "system/projects/alpha/journey/tobiishi/2026-01-01_a-change.md", "x\n")
    triple = "alpha · tobiishi · 2026-01-01_a-change"
    (repo / "system/nemawashi/unpicked/source.md").write_text(f"`{triple}`\n")

    assert [d.target for d in dead_links(repo)] == [triple]


def test_the_printed_report_shows_a_dead_triple_with_its_three_parts(tmp_path, capsys):
    """Reached-when 2: a dead triple is named *with its three parts shown*, so a reader can see
    which of them is wrong. Asserting the return value alone never reaches the printed line."""
    repo = _instance(tmp_path)
    stale = "alpha · nemawashi · 2026-01-01_gone"
    (repo / "system/nemawashi/unpicked/source.md").write_text(f"`{stale}`\n")

    assert main(["--repo", str(repo)]) == 1
    assert stale in capsys.readouterr().out


@pytest.mark.parametrize(
    "source",
    [
        "system/nemawashi/drop/2026-01-01_killed.md",
        "system/projects/alpha/journey/shukuba/parked/2026-01-01_parked.md",
    ],
)
def test_all_widens_triple_scope_to_drop_and_parked_too(tmp_path, source):
    """Task 3: `--all` widens to trail/, drop/ *and* parked/ for triples exactly as for paths."""
    repo = _instance(tmp_path)
    _write(repo, source, "`alpha · nemawashi · 2026-01-01_gone`\n")

    assert dead_links(repo) == []
    assert len(dead_links(repo, everywhere=True)) == 1


# --- the-cold-read-is-answered, Task 1 — a double-backtick span parses --------------
#
# `` `([^`]+)` `` meets `` `` `x` `` `` , pairs the wrong ticks, leaves one over, and every span
# after it in the file is offset by one — the line-wrap trap's newer sibling.


def test_a_double_backtick_span_does_not_hide_the_pointer_after_it():
    """The defect Task 1 fixes: the naive regex mis-pairs the ticks inside a double-backtick span
    and every span after it in the file goes invisible."""
    target = "system/nemawashi/2026-01-01_a-target.md"
    text = f"See `` `x` `` and then `{target}` for the rest.\n"
    assert pointers(text) == [target]


def test_a_pointer_after_a_triple_backtick_fence_is_still_found():
    """Triple-backtick and longer runs behave the same way."""
    target = "system/nemawashi/2026-01-01_a-target.md"
    text = "```\nsome code, not a pointer\n```\n" + f"Then `{target}`.\n"
    assert pointers(text) == [target]


@pytest.mark.parametrize("fence", ["`" * n for n in (4, 5, 6)])
def test_a_pointer_after_a_run_longer_than_three_is_still_found(fence):
    """Integrity pass — the task states "triple-backtick **and longer** runs behave the same way"
    and only the triple was asserted. A run of N closes on a run of N whatever N is, so a fence
    the house has not used yet must not offset the spans after it either."""
    target = "system/nemawashi/2026-01-01_a-target.md"
    text = f"See {fence} `x` {fence} and then `{target}`.\n"
    assert pointers(text) == [target]


def test_a_fenced_blocks_own_inner_backticks_do_not_produce_a_pointer():
    """A fenced block's content is one span — a single backtick inside it, around what looks like
    a path, is literal prose inside that span, not a top-level span of its own."""
    text = (
        "```\n"
        "See `system/nemawashi/2026-01-01_inside-a-fence.md` for reference.\n"
        "```\n"
    )
    assert pointers(text) == []


# --- the-cold-read-is-answered, Task 2 — a triple cannot absorb the prose around it -------------
#
# `pointers()`'s general wrap-collapse strips `\s*\n\s*` to nothing, which is right for a path
# (whose segments touch directly) and wrong for a triple, whose three parts are space-separated.


def test_a_wrap_does_not_merge_prose_into_the_triples_project():
    """The bug: stripping the wrap to nothing merges prose sharing the span into the project."""
    text = "`see\nalpha · nemawashi · 2026-01-01_x` end.\n"
    assert pointers(text) == []


def test_a_wrap_before_the_triple_yields_the_identical_string():
    stem = "2026-01-01_a-seed-with-a-name-long-enough-to-wrap-a-line"
    text = f"See\n`\nalpha · nemawashi · {stem}` end.\n"
    assert pointers(text) == [f"alpha · nemawashi · {stem}"]


def test_a_wrap_after_the_triple_yields_the_identical_string():
    stem = "2026-01-01_a-seed-with-a-name-long-enough-to-wrap-a-line"
    text = f"`alpha · nemawashi · {stem}\n` end.\n"
    assert pointers(text) == [f"alpha · nemawashi · {stem}"]


# --- the-cold-read-is-answered, Task 3 — a real artifact's name is expressible ------------------
#
# `dev-skills · shukuba · 2026-07-06_build-development-code-review.design` names a station that
# really exists (`system/projects/dev-skills/journey/shukuba/trail/
# 2026-07-06_build-development-code-review.design.md`) and that no triple could express before
# this task — `_TRIPLE_NAME` admitted no dot at all.


def test_a_dotted_stem_is_a_valid_triple_name():
    assert pointers("`dev-skills · shukuba · 2026-07-06_build-development-code-review.design`") == [
        "dev-skills · shukuba · 2026-07-06_build-development-code-review.design"
    ]


def test_a_dotted_triple_resolves_against_a_fixture_holding_the_dotted_artifact(tmp_path):
    """Same shape as the real station on disk,
    `system/projects/dev-skills/journey/shukuba/trail/
    2026-07-06_build-development-code-review.design.md` — a fixture, per this file's own house
    style of never citing a real project as a case (`check_vendor_neutrality.py`)."""
    repo = _instance(tmp_path)
    triple = "alpha · shukuba · 2026-01-01_a-station.design"
    _write(repo, "system/projects/alpha/journey/shukuba/trail/2026-01-01_a-station.design.md", "x\n")
    (repo / "system/nemawashi/unpicked/source.md").write_text(f"`{triple}`\n")

    # A resolver that silently matches nothing reports identically to one that works
    # (`test_corrupting_one_good_triple_raises_the_dead_count_by_exactly_one`), so the positive
    # match is asserted too, not just the absence of a dead pointer.
    assert pointers(f"`{triple}`") == [triple]
    assert dead_links(repo) == []


def test_a_name_ending_dot_md_is_still_refused():
    """The triple names an artifact, not a file — `.md` still does not belong in `<name>`."""
    assert pointers("`alpha · nemawashi · 2026-01-01_a-seed.md`") == []


def test_a_name_with_a_slash_is_still_refused():
    assert pointers("`alpha · nemawashi · 2026-01-01_a-seed/seed.md`") == []


# --- the-cold-read-is-answered, Task 4 — a near-miss is reported as malformed -------------------
#
# A span that looks like a triple but does not match is reported rather than dropped — the tool's
# founding complaint (a shape it cannot match produces no finding at all) applied to its own newest
# form. A malformed triple is never counted as dead and never returned by pointers().


@pytest.mark.parametrize(
    "span",
    [
        "alpha · shukba · 2026-01-01_x",  # kind typo, one edit from `shukuba`
        "alpha ・ nemawashi ・ 2026-01-01_x",  # wrong separator (U+30FB, not the pinned U+00B7)
        "alpha · nemawashi · a-seed",  # no date
    ],
)
def test_a_near_miss_triple_is_reported_as_malformed(span):
    assert malformed_triples(f"`{span}`") == [span]
    assert pointers(f"`{span}`") == []  # never a live pointer


@pytest.mark.parametrize(
    "span",
    [
        "PRD · SRS · SDD",
        "tests 164 · pass 164 · fail 0",
        "blocking · skill-general · stability",
        "<project> · <kind> · <name>",
        "instance · tobiishi · …",
    ],
)
def test_ordinary_three_part_middot_prose_is_not_reported_as_malformed(span):
    assert malformed_triples(f"`{span}`") == []


@pytest.mark.parametrize(
    "span",
    [
        "<project> · nemawashi · 2026-01-01_x",  # placeholder project, both triggers otherwise live
        "alpha · nemawashi · <YYYY-MM-DD>_<slug>",  # placeholder name, kind-like part 2
        "alpha · nemawashi · …",  # elision, kind-like part 2
    ],
)
def test_a_placeholder_part_is_never_reported_however_near_the_rest_is(span):
    """Integrity pass — the task states "a part containing `<`, `>` or `…` makes the span a
    placeholder and is never reported at all", and the false-positive set above exercises that
    guard through one case only (`instance · tobiishi · …`). Each span here would fire on
    `_kind_like(parts[1])` alone; the guard is the only thing stopping it, so removing the guard
    must turn each of these red."""
    assert malformed_triples(f"`{span}`") == []


def test_a_genuine_triple_is_not_reported_as_malformed():
    assert malformed_triples(f"`{_TRIPLE}`") == []


def test_a_malformed_triple_is_never_counted_as_dead_or_returned_by_pointers(tmp_path):
    repo = _instance(tmp_path)
    span = "alpha · shukba · 2026-01-01_x"
    (repo / "system/nemawashi/unpicked/source.md").write_text(f"`{span}`\n")

    assert dead_links(repo) == []
    assert [(m.source, m.span) for m in malformed_links(repo)] == [
        ("system/nemawashi/unpicked/source.md", span)
    ]


def test_malformed_scope_follows_the_same_live_seedbed_rule_as_dead(tmp_path):
    repo = _instance(tmp_path)
    span = "alpha · shukba · 2026-01-01_x"
    (repo / "system/nemawashi/trail/2026-01-01_retired.md").write_text(f"`{span}`\n")

    assert malformed_links(repo) == []
    assert len(malformed_links(repo, everywhere=True)) == 1


def test_a_self_quoted_genuine_triple_inside_a_double_backtick_is_not_malformed():
    """Found while walking this task's own real-repo verification: a genuine triple shown via the
    house's own `` `x` `` display idiom (double backticks around a single-backtick-quoted value,
    used to visibly show the backtick) carries the quoting backticks into the span's raw content —
    `_unwrap_self_quote` strips them before either pointers() or the malformed check looks at it."""
    triple = "doctrine · nemawashi · 2026-09-10_a-journey-artifact-is-cited-by-project-kind-and-name"
    text = f"See `` `{triple}` ``.\n"
    assert pointers(text) == [triple]
    assert malformed_triples(text) == []


def test_main_prints_a_malformed_triple_without_changing_the_exit_code(tmp_path, capsys):
    """The tool's founding complaint applied to its own newest form: a shape it cannot match must
    not read exactly like a clean file. Reported, but never counted toward the exit code."""
    repo = _instance(tmp_path)
    span = "alpha · shukba · 2026-01-01_x"
    (repo / "system/nemawashi/unpicked/source.md").write_text(f"`{span}`\n")

    assert main(["--repo", str(repo)]) == 0
    out = capsys.readouterr().out
    assert span in out
    assert "malformed" in out.lower()


# --- a live folder-seed is scanned whole, not only its seed.md ------------------------------


@pytest.mark.parametrize(
    "name", ["2026-01-01_k_recommendations.md", "2026-01-01_what-the-ppm-did_report.md"]
)
def test_a_dead_pointer_in_a_live_folder_seeds_other_file_is_reported(tmp_path, name):
    """A recommendations file or a retire report sits beside seed.md and is live for as long as its
    seed is — a recommendations file names seeds to cut, retire or drop. A scope that reads only
    seed.md reports a dead pointer there as nothing at all."""
    repo = _instance(tmp_path)
    seed = "system/projects/alpha/journey/nemawashi/2026-01-01_a-seed"
    _write(repo, f"{seed}/seed.md", "x\n")
    dead = "system/projects/alpha/journey/nemawashi/unpicked/2026-01-01_gone.md"
    _write(repo, f"{seed}/{name}", f"`{dead}`\n")
    assert [d.target for d in dead_links(repo)] == [dead]


def test_a_folder_seeds_other_file_under_trail_is_scanned_only_under_all(tmp_path):
    """Widening a folder-seed to its whole folder must not widen the bins: history stays out of the
    default scope, and --all still reaches it."""
    repo = _instance(tmp_path)
    seed = "system/projects/alpha/journey/nemawashi/trail/2026-01-01_a-seed"
    _write(repo, f"{seed}/seed.md", "x\n")
    dead = "system/projects/alpha/journey/nemawashi/unpicked/2026-01-01_gone.md"
    _write(repo, f"{seed}/2026-01-01_k_recommendations.md", f"`{dead}`\n")
    assert dead_links(repo) == []
    assert [d.target for d in dead_links(repo, everywhere=True)] == [dead]


# --- product_docs_roots() — the docs/ folder each project card's Product path names ----------
#
# A product's open-issues companion names the seed watching an item, and it lives in the product's
# docs/, often in another repository — found 2026-09-14 in a satellite's product, where a retire broke one and
# nothing reported it. The card's `**Product path:**` line is the only record of where that is.


def _card(repo: Path, project: str, product_path: str) -> None:
    _write(
        repo,
        f"system/projects/{project}/project.md",
        f"# {project}\n\n**Product path:** {product_path}   <!-- relative → internal · absolute →"
        " external -->\n",
    )


def test_a_relative_product_path_names_a_docs_folder_under_the_instance(tmp_path):
    repo = _instance(tmp_path)
    _card(repo, "alpha", "products/widget")
    (repo / "products/widget/docs").mkdir(parents=True)
    assert product_docs_roots(repo) == [repo / "products/widget/docs"]


def test_an_absolute_product_path_names_a_docs_folder_outside_the_instance(tmp_path):
    repo = _instance(tmp_path / "instance")
    product = tmp_path / "elsewhere" / "widget"
    _card(repo, "alpha", str(product))
    (product / "docs").mkdir(parents=True)
    assert product_docs_roots(repo) == [product / "docs"]


def test_a_product_with_no_docs_folder_contributes_nothing(tmp_path):
    repo = _instance(tmp_path)
    _card(repo, "alpha", "products/widget")
    (repo / "products/widget").mkdir(parents=True)
    assert product_docs_roots(repo) == []


def test_a_card_with_no_product_path_line_contributes_nothing(tmp_path):
    repo = _instance(tmp_path)
    _write(repo, "system/projects/alpha/project.md", "# alpha\n\nno product declared\n")
    assert product_docs_roots(repo) == []


def test_two_cards_sharing_a_product_give_one_docs_folder(tmp_path):
    repo = _instance(tmp_path)
    _card(repo, "alpha", "products/widget")
    _card(repo, "beta", "products/widget")
    (repo / "products/widget/docs").mkdir(parents=True)
    assert product_docs_roots(repo) == [repo / "products/widget/docs"]


def test_a_placeholder_product_path_contributes_nothing(tmp_path):
    """An unstamped card still carries the template's `<path>`; it names no folder."""
    repo = _instance(tmp_path)
    _card(repo, "alpha", "<path>")
    assert product_docs_roots(repo) == []


# --- docs_roots() and docs_files() — which docs/ files are read ------------------------------
#
# Two kinds of docs/ are read, by the owner's ruling of 2026-09-14: each project's product docs/,
# and the instance's own docs/findings/. The rest of the instance's docs/ — proposals/, reviews/ —
# is not, and a trail/ under any of them is history, correct as it stands.


def test_docs_roots_are_the_instance_findings_and_each_product_docs_folder(tmp_path):
    repo = _instance(tmp_path)
    (repo / "docs/findings").mkdir(parents=True)
    _card(repo, "alpha", "products/widget")
    (repo / "products/widget/docs").mkdir(parents=True)
    assert docs_roots(repo) == [repo / "docs/findings", repo / "products/widget/docs"]


def test_the_instance_docs_proposals_folder_is_not_a_docs_root(tmp_path):
    repo = _instance(tmp_path)
    (repo / "docs/findings").mkdir(parents=True)
    (repo / "docs/proposals").mkdir(parents=True)
    assert docs_roots(repo) == [repo / "docs/findings"]


def test_an_instance_with_no_findings_folder_has_only_its_product_docs_roots(tmp_path):
    repo = _instance(tmp_path)
    _card(repo, "alpha", "products/widget")
    (repo / "products/widget/docs").mkdir(parents=True)
    assert docs_roots(repo) == [repo / "products/widget/docs"]


def test_docs_files_reads_markdown_at_any_depth_including_a_readme(tmp_path):
    root = tmp_path / "docs"
    _write(root, "README.md", "x\n")
    _write(root, "architecture_open_issues.md", "x\n")
    _write(root, "adr/0001-a-decision.md", "x\n")
    assert docs_files([root]) == [
        root / "README.md",
        root / "adr/0001-a-decision.md",
        root / "architecture_open_issues.md",
    ]


def test_docs_files_leaves_out_everything_under_a_trail_folder(tmp_path):
    root = tmp_path / "docs"
    _write(root, "trail/architecture/cycle-13.md", "x\n")
    _write(root, "sdd/trail/cycle-2.md", "x\n")
    _write(root, "trail.md", "x\n")
    assert docs_files([root]) == [root / "trail.md"]


def test_docs_files_ignores_a_file_that_is_not_markdown(tmp_path):
    root = tmp_path / "docs"
    _write(root, "diagram.svg", "x\n")
    assert docs_files([root]) == []


def test_docs_files_over_a_root_that_does_not_exist_is_empty(tmp_path):
    assert docs_files([tmp_path / "docs/findings"]) == []


# --- dead_links() and malformed_links() read the docs scope beside the live seedbeds ----------
#
# A companion's `Tracked by:` line names a seed, and a finding names the seed it was met on; both
# stay in use after the seed moves. A file inside the instance is named as the seedbeds' own files
# are, by its repo-relative path; a product outside it can only be named by where it is.

_GONE = "system/projects/alpha/journey/nemawashi/unpicked/2026-01-01_gone.md"


def test_a_dead_pointer_in_an_external_product_companion_is_named_by_its_absolute_path(tmp_path):
    repo = _instance(tmp_path / "instance")
    product = tmp_path / "elsewhere" / "widget"
    _card(repo, "alpha", str(product))
    _write(product, "docs/architecture_open_issues.md", f"- **Tracked by:** `{_GONE}`\n")
    assert [(d.source, d.target) for d in dead_links(repo)] == [
        ((product / "docs/architecture_open_issues.md").as_posix(), _GONE)
    ]


def test_a_dead_pointer_in_a_finding_is_named_by_its_repo_relative_path(tmp_path):
    repo = _instance(tmp_path)
    _write(repo, "docs/findings/2026-01-01_a-finding.md", f"`{_GONE}`\n")
    assert [(d.source, d.target) for d in dead_links(repo)] == [
        ("docs/findings/2026-01-01_a-finding.md", _GONE)
    ]


def test_a_resolving_triple_in_a_product_companion_is_not_dead(tmp_path):
    repo = _instance(tmp_path)
    _write(repo, "system/projects/alpha/journey/nemawashi/trail/2026-01-01_a-seed.md", "x\n")
    _card(repo, "alpha", "products/widget")
    _write(
        repo,
        "products/widget/docs/architecture_open_issues.md",
        "- **Tracked by:** `alpha · nemawashi · 2026-01-01_a-seed`\n",
    )
    assert dead_links(repo) == []


def test_a_dead_pointer_in_a_proposal_is_not_read(tmp_path):
    repo = _instance(tmp_path)
    _write(repo, "docs/proposals/a-proposal.md", f"`{_GONE}`\n")
    assert dead_links(repo) == []


def test_a_malformed_triple_in_a_finding_is_reported(tmp_path):
    repo = _instance(tmp_path)
    span = "alpha · shukba · 2026-01-01_x"
    _write(repo, "docs/findings/2026-01-01_a-finding.md", f"`{span}`\n")
    assert [(m.source, m.span) for m in malformed_links(repo)] == [
        ("docs/findings/2026-01-01_a-finding.md", span)
    ]


def test_everywhere_reads_the_same_docs_files_and_a_product_trail_stays_out(tmp_path):
    """`--all` widens the seedbeds' bins, and nothing about docs/: the owner left it out."""
    repo = _instance(tmp_path)
    _card(repo, "alpha", "products/widget")
    _write(repo, "products/widget/docs/trail/architecture/cycle-1.md", f"`{_GONE}`\n")
    _write(repo, "docs/findings/2026-01-01_a-finding.md", f"`{_GONE}`\n")
    expected = [("docs/findings/2026-01-01_a-finding.md", _GONE)]
    assert [(d.source, d.target) for d in dead_links(repo)] == expected
    assert [(d.source, d.target) for d in dead_links(repo, everywhere=True)] == expected


def test_the_live_seedbed_scope_never_returns_a_docs_file(tmp_path):
    """`test_journey_pointers_are_triples.py` holds the live seedbeds to the triple through
    `_live_files()`; a docs file there would put every finding and companion under that gate."""
    repo = _instance(tmp_path)
    _card(repo, "alpha", "products/widget")
    _write(repo, "products/widget/docs/architecture_open_issues.md", f"`{_GONE}`\n")
    _write(repo, "docs/findings/2026-01-01_a-finding.md", f"`{_GONE}`\n")
    assert _live_files(repo, everywhere=False) == []
    assert _live_files(repo, everywhere=True) == []


# --- main() says which scope it read ------------------------------------------------------------


def test_the_clean_report_names_the_docs_scope_it_read(tmp_path, capsys):
    """A caller reading "every pointer resolves" must be told what was read, or a clean run over the
    seedbeds alone is indistinguishable from one that also read the companions and findings."""
    repo = _instance(tmp_path)
    assert main(["--repo", str(repo)]) == 0
    out = capsys.readouterr().out
    assert "docs/findings/" in out
    assert "product docs/" in out


def test_a_dead_pointer_in_a_finding_fails_the_exit_code_and_names_the_finding(tmp_path, capsys):
    repo = _instance(tmp_path)
    _write(repo, "docs/findings/2026-01-01_a-finding.md", f"`{_GONE}`\n")
    assert main(["--repo", str(repo)]) == 1
    out = capsys.readouterr().out
    assert "docs/findings/2026-01-01_a-finding.md" in out
    assert f"-> {_GONE}" in out


# --- the journey-relative shape — a span that starts at the kind, `nemawashi/…`, `shukuba/…` ----
#
# A seed citing its own project's journey drops both `system/projects/<p>/` and `journey/`, so the
# span starts at the kind. Neither path pattern above matched it, so it produced no finding at all:
# measured 2026-09-15, ten such pointers were dead across seven live seeds on a run that reported
# every pointer resolves.


@pytest.mark.parametrize(
    "span",
    [
        "nemawashi/2026-01-01_a-seed.md",
        "nemawashi/unpicked/2026-01-01_a-seed.md",
        "nemawashi/trail/2026-01-01_a-seed.md",
        "nemawashi/drop/2026-01-01_a-seed.md",
        "shukuba/2026-01-01_a-station.md",
        "shukuba/trail/2026-01-01_a-station.md",
        "shukuba/parked/2026-01-01_a-station.md",
        "tobiishi/trail/2026-01-01_a-unit.md",
    ],
)
def test_a_journey_relative_pointer_is_returned_as_written(span):
    assert pointers(f"see `{span}` here") == [span]


@pytest.mark.parametrize(
    "span",
    [
        "nemawashi/2026-01-01_a-seed/seed.md",
        "nemawashi/unpicked/2026-01-01_a-seed/seed.md",
        "nemawashi/trail/2026-01-01_a-seed/2026-02-02_a-key_report.md",
    ],
)
def test_a_journey_relative_pointer_into_a_folder_seed_is_returned(span):
    assert pointers(f"`{span}`") == [span]


def test_a_journey_relative_pointer_that_wraps_a_line_is_still_found():
    text = "the station\n`shukuba/trail/\n  2026-01-01_a-station.md`, closed.\n"
    assert pointers(text) == ["shukuba/trail/2026-01-01_a-station.md"]


@pytest.mark.parametrize(
    "span",
    [
        "nemawashi/<seed>.md",
        "shukuba/trail/",
        "shukuba/2026-01-01_a-station",
        "shukuba/trail/2026-01-01_a-station/extra/deep.md",
    ],
)
def test_a_placeholder_a_bare_folder_or_an_unshaped_span_is_not_a_journey_relative_pointer(span):
    assert pointers(f"`{span}`") == []


def test_the_anchored_and_project_relative_shapes_are_returned_unchanged_beside_it():
    text = (
        "`system/nemawashi/unpicked/2026-01-01_a.md` "
        "`journey/nemawashi/unpicked/2026-01-01_b.md` "
        "`nemawashi/unpicked/2026-01-01_c.md`"
    )
    assert pointers(text) == [
        "system/nemawashi/unpicked/2026-01-01_a.md",
        "journey/nemawashi/unpicked/2026-01-01_b.md",
        "nemawashi/unpicked/2026-01-01_c.md",
    ]


# --- a journey-relative pointer resolves against the journey its source sits in ------------------
#
# A reader takes `shukuba/trail/<station>.md` from the file it is written in: a project seed's own
# `journey/`, the instance seedbed's `system/`. Searching every project instead would call a pointer
# alive on the strength of another project's file — the real case, 2026-09-15, a dev-skills seed
# citing a station only `tools` holds. A source with no journey of its own (a finding, a product
# companion) names no base, so every base is searched, as the project-relative shape already is.

_STATION = "shukuba/trail/2026-01-01_a-station.md"
_ALPHA_SEED = "system/projects/alpha/journey/nemawashi/unpicked/2026-01-01_source.md"


def test_a_journey_relative_pointer_resolves_in_its_own_projects_journey(tmp_path):
    repo = _instance(tmp_path)
    _write(repo, f"system/projects/alpha/journey/{_STATION}", "x")
    _write(repo, _ALPHA_SEED, f"`{_STATION}`\n")
    assert dead_links(repo) == []


def test_a_journey_relative_pointer_held_only_by_another_project_is_dead(tmp_path):
    repo = _instance(tmp_path)
    _write(repo, f"system/projects/beta/journey/{_STATION}", "x")
    _write(repo, _ALPHA_SEED, f"`{_STATION}`\n")
    assert dead_links(repo) == [Dead(_ALPHA_SEED, _STATION)]


def test_an_instance_seedbed_source_resolves_against_system(tmp_path):
    repo = _instance(tmp_path)
    _write(repo, "system/nemawashi/trail/2026-01-01_a-seed.md", "x")
    _write(repo, "system/nemawashi/unpicked/router.md", "`nemawashi/trail/2026-01-01_a-seed.md`\n")
    assert dead_links(repo) == []


def test_an_instance_seedbed_source_does_not_resolve_into_a_project(tmp_path):
    repo = _instance(tmp_path)
    _write(repo, f"system/projects/alpha/journey/{_STATION}", "x")
    _write(repo, "system/nemawashi/unpicked/router.md", f"`{_STATION}`\n")
    assert [d.target for d in dead_links(repo)] == [_STATION]


def test_a_finding_resolves_a_journey_relative_pointer_held_by_any_journey(tmp_path):
    repo = _instance(tmp_path)
    _write(repo, f"system/projects/alpha/journey/{_STATION}", "x")
    _write(repo, "docs/findings/2026-01-01_a-finding.md", f"`{_STATION}`\n")
    assert dead_links(repo) == []


def test_a_finding_names_a_journey_relative_pointer_no_journey_holds(tmp_path):
    repo = _instance(tmp_path)
    _write(repo, "docs/findings/2026-01-01_a-finding.md", f"`{_STATION}`\n")
    assert dead_links(repo) == [Dead("docs/findings/2026-01-01_a-finding.md", _STATION)]


def test_a_journey_relative_flat_pointer_resolves_once_its_seed_is_a_folder(tmp_path):
    repo = _instance(tmp_path)
    _write(repo, "system/projects/alpha/journey/nemawashi/unpicked/2026-01-01_a-seed/seed.md", "x")
    _write(repo, _ALPHA_SEED, "`nemawashi/unpicked/2026-01-01_a-seed.md`\n")
    assert dead_links(repo) == []


def test_a_source_inside_a_folder_seed_resolves_against_its_projects_journey(tmp_path):
    repo = _instance(tmp_path)
    _write(repo, f"system/projects/alpha/journey/{_STATION}", "x")
    _write(repo, "system/projects/alpha/journey/nemawashi/unpicked/2026-01-01_a-seed/seed.md",
           f"`{_STATION}`\n")
    assert dead_links(repo) == []


def test_under_all_a_trail_source_resolves_against_its_own_journey(tmp_path):
    repo = _instance(tmp_path)
    _write(repo, f"system/projects/alpha/journey/{_STATION}", "x")
    _write(repo, "system/projects/alpha/journey/nemawashi/trail/2026-01-01_retired.md",
           f"`{_STATION}`\n")
    assert dead_links(repo, everywhere=True) == []


# --- the fifth shape: bin-relative, and the two suffixes every path shape may carry ---------------
#
# A seed citing a sibling in its own seedbed drops the kind too: `unpicked/<seed>.md`,
# `trail/<seed>/`. And a pointer at a place in a file carries `:<lines>`, one at a folder a trailing
# `/`. None of these matched, so a pool written in them read clean with dead pointers in it:
# measured 2026-09-25 in a satellite's pool, three dead and about thirty live, all unreported.


@pytest.mark.parametrize(
    "span",
    [
        "unpicked/2026-01-01_a-seed.md",
        "unpicked/2026-01-01_a-seed/",
        "unpicked/2026-01-01_a-seed/seed.md",
        "trail/2026-01-01_a-seed.md",
        "trail/2026-01-01_a-seed/",
        "drop/2026-01-01_a-seed.md",
        "parked/2026-01-01_a-station.md",
    ],
)
def test_a_bin_relative_pointer_is_returned_as_written(span):
    assert pointers(f"see `{span}` here") == [span]


@pytest.mark.parametrize(
    "span, target",
    [
        ("shukuba/trail/2026-01-01_a-station.md:46-54", "shukuba/trail/2026-01-01_a-station.md"),
        ("unpicked/2026-01-01_a-seed.md:12", "unpicked/2026-01-01_a-seed.md"),
        ("system/nemawashi/trail/2026-01-01_a-seed.md:160-163",
         "system/nemawashi/trail/2026-01-01_a-seed.md"),
        ("journey/shukuba/2026-01-01_a-station.md:36", "journey/shukuba/2026-01-01_a-station.md"),
    ],
)
def test_a_line_suffix_is_dropped_and_the_pointer_kept(span, target):
    assert pointers(f"`{span}`") == [target]


@pytest.mark.parametrize(
    "span",
    ["nemawashi/trail/2026-01-01_a-seed/", "tobiishi/trail/2026-01-01_a-unit/",
     "system/projects/alpha/journey/nemawashi/trail/2026-01-01_a-seed/"],
)
def test_a_trailing_slash_names_a_folder_and_is_a_pointer(span):
    assert pointers(f"`{span}`") == [span]


@pytest.mark.parametrize(
    "span",
    ["trail/prd/cycle-3.md", "unpicked/", "trail/<seed>.md", "docs/trail/srs/cycle-29.md",
     "unpicked/a-seed.md", "shukuba/trail/"],
)
def test_an_undated_or_unshaped_bin_span_is_not_a_pointer(span):
    assert pointers(f"`{span}`") == []


def test_a_bin_relative_pointer_resolves_in_its_own_seedbed(tmp_path):
    repo = _instance(tmp_path)
    _write(repo, "system/projects/alpha/journey/nemawashi/unpicked/2026-01-01_a-seed.md", "x")
    _write(repo, _ALPHA_SEED, "`unpicked/2026-01-01_a-seed.md`\n")
    assert dead_links(repo) == []


def test_a_bin_relative_pointer_whose_seed_moved_is_dead(tmp_path):
    repo = _instance(tmp_path)
    _write(repo, "system/projects/alpha/journey/nemawashi/trail/2026-01-01_a-seed.md", "x")
    _write(repo, _ALPHA_SEED, "`unpicked/2026-01-01_a-seed.md`\n")
    assert dead_links(repo) == [Dead(_ALPHA_SEED, "unpicked/2026-01-01_a-seed.md")]


def test_a_bin_relative_flat_pointer_resolves_once_its_seed_is_a_folder(tmp_path):
    repo = _instance(tmp_path)
    _write(repo, "system/projects/alpha/journey/nemawashi/unpicked/2026-01-01_a-seed/seed.md", "x")
    _write(repo, _ALPHA_SEED, "`unpicked/2026-01-01_a-seed.md`\n")
    assert dead_links(repo) == []


def test_a_bin_relative_pointer_resolves_in_its_journeys_stations(tmp_path):
    repo = _instance(tmp_path)
    _write(repo, f"system/projects/alpha/journey/{_STATION}", "x")
    _write(repo, _ALPHA_SEED, "`trail/2026-01-01_a-station.md`\n")
    assert dead_links(repo) == []


def test_a_bin_relative_pointer_held_only_by_another_project_is_dead(tmp_path):
    repo = _instance(tmp_path)
    _write(repo, "system/projects/beta/journey/nemawashi/trail/2026-01-01_a-seed.md", "x")
    _write(repo, _ALPHA_SEED, "`trail/2026-01-01_a-seed.md`\n")
    assert [d.target for d in dead_links(repo)] == ["trail/2026-01-01_a-seed.md"]


def test_a_folder_pointer_resolves_on_the_folder_and_dies_without_it(tmp_path):
    repo = _instance(tmp_path)
    _write(repo, "system/projects/alpha/journey/nemawashi/trail/2026-01-01_a-seed/seed.md", "x")
    _write(repo, _ALPHA_SEED,
           "`nemawashi/trail/2026-01-01_a-seed/` `nemawashi/trail/2026-01-01_gone/`\n")
    assert [d.target for d in dead_links(repo)] == ["nemawashi/trail/2026-01-01_gone/"]


def test_a_line_suffixed_pointer_resolves_on_its_file(tmp_path):
    repo = _instance(tmp_path)
    _write(repo, f"system/projects/alpha/journey/{_STATION}", "x")
    _write(repo, _ALPHA_SEED, f"`{_STATION}:46-54` `shukuba/trail/2026-01-01_gone.md:3`\n")
    assert [d.target for d in dead_links(repo)] == ["shukuba/trail/2026-01-01_gone.md"]


@pytest.mark.parametrize(
    "span, target",
    [
        ("shukuba/trail/2026-01-01_a-station.md:L46", "shukuba/trail/2026-01-01_a-station.md"),
        ("shukuba/trail/2026-01-01_a-station.md:L12-L20", "shukuba/trail/2026-01-01_a-station.md"),
        ("shukuba/trail/2026-01-01_a-station.md:46–54", "shukuba/trail/2026-01-01_a-station.md"),
    ],
)
def test_the_citation_line_forms_are_dropped_too(span, target):
    assert pointers(f"`{span}`") == [target]


def test_a_bin_resolves_only_under_the_kinds_that_keep_it(tmp_path):
    """`unpicked/` is nemawashi's alone and `parked/` shukuba's: a same-named file under another
    kind's folder of that name is not the artifact the pointer names."""
    repo = _instance(tmp_path)
    _write(repo, "system/projects/alpha/journey/shukuba/unpicked/2026-01-01_a-seed.md", "x")
    _write(repo, "system/projects/alpha/journey/nemawashi/parked/2026-01-01_a-station.md", "x")
    _write(repo, _ALPHA_SEED,
           "`unpicked/2026-01-01_a-seed.md` `parked/2026-01-01_a-station.md`\n")
    assert [d.target for d in dead_links(repo)] == [
        "unpicked/2026-01-01_a-seed.md", "parked/2026-01-01_a-station.md"]


def test_a_journey_relative_folder_pointer_resolves_on_the_folder(tmp_path):
    repo = _instance(tmp_path)
    _write(repo, "system/projects/alpha/journey/tobiishi/trail/2026-01-01_a-unit/change_spec.md", "x")
    _write(repo, _ALPHA_SEED,
           "`journey/tobiishi/trail/2026-01-01_a-unit/` `journey/tobiishi/trail/2026-01-01_gone/`\n")
    assert [d.target for d in dead_links(repo)] == ["journey/tobiishi/trail/2026-01-01_gone/"]


# --- the four-part key: a pointer into another instance --------------------------
#
# A satellite cites its host's journey. A three-part key resolves only in the repository being
# checked, so a correct pointer read as dead; the fourth part names the instance, and the host's
# roster says where that instance is.


def _named_instance(root: Path, name: str) -> Path:
    _instance(root)
    (root / "kensaiapp.md").write_text(f"# {name}\n\nWhat is true of this instance.\n")
    return root


def _host_with(tmp_path: Path, satellites: dict[str, Path]) -> Path:
    host = _named_instance(tmp_path / "host", "the-host")
    rows = "\n".join(f"| `{name}` | `{path}` |" for name, path in satellites.items())
    (host / "system" / "satellites.md").write_text(
        "# Satellites\n\n## Consumers — build their own product here\n\n"
        "| satellite | path |\n|---|---|\n" + rows + "\n"
    )
    return host


def test_a_four_part_key_is_a_pointer():
    key = "the-host · alpha · nemawashi · 2026-01-01_a-seed"
    assert pointers(f"`{key}`") == [key]


def test_a_four_part_key_wrapped_inside_its_span_is_returned_whole():
    assert pointers("`the-host · alpha ·\n  nemawashi · 2026-01-01_a-seed`") == [
        "the-host · alpha · nemawashi · 2026-01-01_a-seed"
    ]


def test_instance_roots_name_the_host_the_repo_and_every_rostered_satellite(tmp_path):
    sat = _named_instance(tmp_path / "sat", "a-satellite")
    other = tmp_path / "elsewhere"
    host = _host_with(tmp_path, {"a-satellite": sat, "another": other})

    assert instance_roots(sat, host) == {"the-host": host, "a-satellite": sat, "another": other}


def test_an_instance_is_named_by_its_kensaiapp_md_heading_else_its_folder(tmp_path):
    assert instance_name(_named_instance(tmp_path / "x", "declared-name")) == "declared-name"
    assert instance_name(_instance(tmp_path / "bare")) == "bare"


def test_a_four_part_key_into_the_host_resolves_from_a_satellite(tmp_path):
    sat = _named_instance(tmp_path / "sat", "a-satellite")
    host = _host_with(tmp_path, {"a-satellite": sat})
    _write(host, "system/projects/alpha/journey/nemawashi/trail/2026-01-01_a-seed/seed.md", "x\n")
    (sat / "system/nemawashi/unpicked/2026-01-02_source.md").write_text(
        "`the-host · alpha · nemawashi · 2026-01-01_a-seed`\n"
    )

    assert dead_links(sat, instances=instance_roots(sat, host)) == []


def test_a_four_part_key_is_dead_once_the_artifact_leaves_the_other_instance(tmp_path):
    """The point of a key over prose: a drop in the host still shows up in the satellite."""
    sat = _named_instance(tmp_path / "sat", "a-satellite")
    host = _host_with(tmp_path, {"a-satellite": sat})
    key = "the-host · alpha · nemawashi · 2026-01-01_a-seed"
    (sat / "system/nemawashi/unpicked/2026-01-02_source.md").write_text(f"`{key}`\n")

    assert [d.target for d in dead_links(sat, instances=instance_roots(sat, host))] == [key]


def test_a_four_part_key_never_resolves_against_the_repo_being_checked(tmp_path):
    """Same project and seed in the satellite itself — the key names the host, so that is no help."""
    sat = _named_instance(tmp_path / "sat", "a-satellite")
    host = _host_with(tmp_path, {"a-satellite": sat})
    _write(sat, "system/projects/alpha/journey/nemawashi/2026-01-01_a-seed.md", "x\n")
    key = "the-host · alpha · nemawashi · 2026-01-01_a-seed"
    (sat / "system/nemawashi/unpicked/2026-01-02_source.md").write_text(f"`{key}`\n")

    assert [d.target for d in dead_links(sat, instances=instance_roots(sat, host))] == [key]


def test_a_four_part_key_naming_its_own_instance_resolves_locally(tmp_path):
    repo = _named_instance(tmp_path / "me", "me")
    _write(repo, "system/projects/alpha/journey/nemawashi/2026-01-01_a-seed.md", "x\n")
    (repo / "system/nemawashi/unpicked/2026-01-02_source.md").write_text(
        "`me · alpha · nemawashi · 2026-01-01_a-seed`\n"
    )

    assert dead_links(repo) == []


def test_a_host_key_reaches_a_satellite_and_one_satellite_reaches_another(tmp_path):
    one = _named_instance(tmp_path / "one", "sat-one")
    two = _named_instance(tmp_path / "two", "sat-two")
    host = _host_with(tmp_path, {"sat-one": one, "sat-two": two})
    _write(two, "system/projects/alpha/journey/shukuba/trail/2026-01-01_a-station.md", "x\n")
    key = "sat-two · alpha · shukuba · 2026-01-01_a-station"
    for repo in (host, one):
        (repo / "system/nemawashi/unpicked/2026-01-02_source.md").write_text(f"`{key}`\n")
        assert dead_links(repo, instances=instance_roots(repo, host)) == []


def test_an_unknown_instance_is_dead_and_the_report_says_which_name(tmp_path, capsys):
    sat = _named_instance(tmp_path / "sat", "a-satellite")
    host = _host_with(tmp_path, {"a-satellite": sat})
    key = "the-hots · alpha · nemawashi · 2026-01-01_a-seed"
    (sat / "system/nemawashi/unpicked/2026-01-02_source.md").write_text(f"`{key}`\n")

    assert main(["--repo", str(sat), "--host", str(host)]) == 1
    out = capsys.readouterr().out
    assert key in out
    assert "no instance named the-hots" in out


def test_a_rostered_instance_missing_from_disk_is_dead_and_says_so(tmp_path, capsys):
    sat = _named_instance(tmp_path / "sat", "a-satellite")
    host = _host_with(tmp_path, {"a-satellite": sat, "gone": tmp_path / "gone"})
    key = "gone · alpha · nemawashi · 2026-01-01_a-seed"
    (sat / "system/nemawashi/unpicked/2026-01-02_source.md").write_text(f"`{key}`\n")

    assert main(["--repo", str(sat), "--host", str(host)]) == 1
    assert "instance gone is not on disk" in capsys.readouterr().out


def test_main_resolves_a_host_key_from_a_satellite_end_to_end(tmp_path, capsys):
    sat = _named_instance(tmp_path / "sat", "a-satellite")
    host = _host_with(tmp_path, {"a-satellite": sat})
    _write(host, "system/nemawashi/2026-01-01_a-seed.md", "x\n")
    (sat / "system/nemawashi/unpicked/2026-01-02_source.md").write_text(
        "`the-host · instance · nemawashi · 2026-01-01_a-seed`\n"
    )

    assert main(["--repo", str(sat), "--host", str(host)]) == 0


@pytest.mark.parametrize(
    "span",
    [
        "the-host · alpha · shukba · 2026-01-01_x",  # kind typo in a four-part key
        "the-host · alpha · nemawashi · a-seed",  # no date
    ],
)
def test_a_near_miss_four_part_key_is_reported_as_malformed(span):
    assert malformed_triples(f"`{span}`") == [span]
    assert pointers(f"`{span}`") == []


def test_a_genuine_four_part_key_is_not_reported_as_malformed():
    assert malformed_triples("`the-host · alpha · nemawashi · 2026-01-01_a-seed`") == []


def test_four_part_middot_prose_is_not_reported_as_malformed():
    assert malformed_triples("`tests 164 · pass 164 · fail 0 · skip 1`") == []


def test_the_default_host_is_the_instance_holding_the_core(tmp_path):
    (tmp_path / "core").mkdir()
    assert default_host(tmp_path / "core") == tmp_path


def test_a_pinned_core_defaults_to_the_host_the_pin_was_made_from(tmp_path):
    """A satellite runs on a pin: a copy of core/ with no system/ beside it, so no roster."""
    host = tmp_path / "the-host"
    pinned = tmp_path / "pins" / "p1"
    (pinned / "core").mkdir(parents=True)
    (pinned / "pin.json").write_text(
        json.dumps({"id": "p1", "source_host_root": str(host), "source_head": None})
    )
    assert default_host(pinned / "core") == host


def test_an_instances_own_name_wins_over_a_roster_row_reusing_it(tmp_path):
    sat = _named_instance(tmp_path / "sat", "a-satellite")
    host = _host_with(tmp_path, {"the-host": tmp_path / "x", "a-satellite": tmp_path / "y"})

    roots = instance_roots(sat, host)
    assert roots["the-host"] == host
    assert roots["a-satellite"] == sat
