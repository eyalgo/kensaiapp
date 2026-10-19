#!/usr/bin/env python3
"""The gate: every live journey pointer is a triple, never a path.

`found_while_walking.md` § *A broken journey pointer is repaired, and the triple is what stops it
breaking* names the triple as the form a pick, un-pick, retire, drop or park cannot break. This test
is the check that holds the live seedbeds to that form, reusing `check_journey_links.py`'s own
`_live_files()` (the scope: seedbed roots, `unpicked/`, and open station roots — `trail/`, `drop/`,
`parked/` and every `docs/` report are out) and `pointers()` (the four path shapes a span can
hold — see that module for the fifth, the triple, matched by `JOURNEY_TRIPLE`).

**It is a test, not a hook and not a lens**: it runs on every `pytest core/tools/` invocation and
needs no install and no wiring. Every test here is self-contained — a `tmp_path` instance it builds
itself. The gate over this instance's own `system/` tree, and the allowances it carries, are
`system/tests/test_instance_journey_pointers.py`; a satellite holds its own pools to the triple only by
standing up a gate of its own.
"""

from __future__ import annotations

from pathlib import Path

import check_journey_links as cjl


def _path_form_pointers(repo: Path) -> list[tuple[str, str]]:
    """Every live pointer that is still path-form rather than a triple, paired with its source file.

    Walks the same scope `check_journey_links.dead_links()` does (`_live_files()`, `--all` off), and
    tells a path from a triple exactly as `pointers()`'s own caller is told to: a triple never
    carries a slash, by construction.
    """
    violations: list[tuple[str, str]] = []
    for f in cjl._live_files(repo, everywhere=False):
        text = f.read_text()
        rel = f.relative_to(repo).as_posix()
        for target in dict.fromkeys(cjl.pointers(text)):
            if not cjl.JOURNEY_TRIPLE.match(target):
                violations.append((rel, target))
    return violations


# --- scope: trail/, drop/, parked/ and docs/ are never converted, so a path pointer left there ---
# --- never fails the gate -------------------------------------------------------------------------


def _instance(tmp_path: Path) -> Path:
    for d in [
        "system/nemawashi/unpicked",
        "system/nemawashi/trail",
        "system/nemawashi/drop",
        "system/shukuba/parked",
        "system/shukuba/trail",
        "system/projects/alpha/journey/nemawashi/unpicked",
        "system/projects/alpha/journey/nemawashi/trail",
        "system/projects/alpha/journey/nemawashi/drop",
        "system/projects/alpha/journey/shukuba/parked",
        "system/projects/alpha/docs",
    ]:
        (tmp_path / d).mkdir(parents=True, exist_ok=True)
    return tmp_path


_A_PATH_POINTER = "system/projects/alpha/journey/nemawashi/unpicked/2026-01-01_gone.md"


def test_a_path_pointer_in_trail_does_not_fail_the_gate(tmp_path):
    repo = _instance(tmp_path)
    (repo / "system/nemawashi/trail/2026-01-01_retired.md").write_text(f"`{_A_PATH_POINTER}`\n")
    assert _path_form_pointers(repo) == []


def test_a_path_pointer_in_drop_does_not_fail_the_gate(tmp_path):
    repo = _instance(tmp_path)
    (repo / "system/nemawashi/drop/2026-01-01_killed.md").write_text(f"`{_A_PATH_POINTER}`\n")
    assert _path_form_pointers(repo) == []


def test_a_path_pointer_in_parked_does_not_fail_the_gate(tmp_path):
    repo = _instance(tmp_path)
    (repo / "system/shukuba/parked/2026-01-01_parked.md").write_text(f"`{_A_PATH_POINTER}`\n")
    assert _path_form_pointers(repo) == []


def test_a_path_pointer_in_a_docs_report_does_not_fail_the_gate(tmp_path):
    """The report sits where a project keeps its working records, beside its `journey/` — the place
    a naive walker of `system/projects/<name>/` would reach. The control writes the same pointer
    into a live seedbed and asserts it IS found, so this test fails if the scope ever widens to
    `docs/`, rather than passing because nothing could have been found."""
    repo = _instance(tmp_path)
    (repo / "system/projects/alpha/docs/a-report.md").write_text(f"`{_A_PATH_POINTER}`\n")
    assert _path_form_pointers(repo) == []

    live = "system/projects/alpha/journey/nemawashi/unpicked/2026-01-01_source.md"
    (repo / live).write_text(f"`{_A_PATH_POINTER}`\n")
    assert _path_form_pointers(repo) == [(live, _A_PATH_POINTER)]


# --- a triple, and a file with no pointers at all, both pass ------------------------------------


def test_a_triple_passes_the_gate(tmp_path):
    repo = _instance(tmp_path)
    (repo / "system/nemawashi/unpicked/2026-01-01_source.md").write_text(
        "`alpha · nemawashi · 2026-01-01_a-seed`\n"
    )
    assert _path_form_pointers(repo) == []


def test_a_file_with_no_pointers_passes_the_gate(tmp_path):
    repo = _instance(tmp_path)
    (repo / "system/nemawashi/unpicked/2026-01-01_source.md").write_text("no pointers here\n")
    assert _path_form_pointers(repo) == []


# --- the failure names the offending file, not just the count -----------------------------------


def test_a_path_form_pointer_is_named_with_its_source_file(tmp_path):
    repo = _instance(tmp_path)
    (repo / "system/nemawashi/unpicked/2026-01-01_source.md").write_text(f"`{_A_PATH_POINTER}`\n")
    assert _path_form_pointers(repo) == [
        ("system/nemawashi/unpicked/2026-01-01_source.md", _A_PATH_POINTER)
    ]


# --- reached-when 3 — shown red first, on a controlled fixture, then removed --------------------


def test_the_gate_fails_when_a_path_pointer_is_introduced_and_passes_once_it_is_removed(tmp_path):
    repo = _instance(tmp_path)
    source = repo / "system/nemawashi/unpicked/2026-01-01_source.md"

    source.write_text("no pointers here\n")
    assert _path_form_pointers(repo) == []

    source.write_text(f"`{_A_PATH_POINTER}`\n")
    assert _path_form_pointers(repo) == [
        ("system/nemawashi/unpicked/2026-01-01_source.md", _A_PATH_POINTER)
    ]

    source.write_text("no pointers here\n")
    assert _path_form_pointers(repo) == []
