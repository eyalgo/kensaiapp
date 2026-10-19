"""The suite map: the one map from instance paths to the suites that guard them.

The lookup tests run on small maps handed in. The live tests hold the module's own map against this
instance's tracked tree (`git ls-files`), because the property is about what the tree contains,
and a list written here would go stale the day a path is added.
"""

from __future__ import annotations

import subprocess
from pathlib import Path, PurePosixPath

import pytest

import suite_map
from suite_map import Entry, Suite, SuiteMap, SuiteMapError

_REPO = Path(__file__).resolve().parents[2]
_TEMPLATES = PurePosixPath("core/templates")


def _map(*entries: Entry, suites: tuple[str, ...] = ("a", "b", "c")) -> SuiteMap:
    return SuiteMap(
        suites=tuple(Suite(name, ("run", name)) for name in suites),
        entries=entries,
    )


def _names(suites) -> list[str]:
    return [suite.name for suite in suites]


def _tracked() -> list[str]:
    out = subprocess.run(
        ["git", "-C", str(_REPO), "ls-files"], capture_output=True, text=True, check=True
    ).stdout
    return out.splitlines()


def _is_test_file(path: str) -> bool:
    name = PurePosixPath(path).name
    return (name.startswith("test_") and name.endswith(".py")) or name.endswith(".test.js")


def _path_arguments(suite: Suite) -> list[PurePosixPath]:
    """The command's arguments that name something in the tree, other than the root itself."""
    found = []
    for argument in suite.command:
        if argument != "." and (_REPO / argument).exists():
            found.append(PurePosixPath(argument))
    return found


# --- the lookup (CP-532) ---------------------------------------------------------------------


def test_paths_answer_the_union_of_their_entries_suites():
    sm = _map(Entry("x/**", ("a",)), Entry("y/**", ("b",)))
    assert _names(suite_map.suites_for(["x/1.py", "y/2.py"], sm)) == ["a", "b"]


def test_suites_come_in_map_order_once_each():
    sm = _map(Entry("x/**", ("c", "a")), Entry("y/**", ("b", "a")))
    answered = suite_map.suites_for(["y/2.py", "x/1.py"], sm)
    assert _names(answered) == ["a", "b", "c"]


def test_suites_follow_declaration_order_not_entry_order():
    sm = _map(Entry("x/**", ("c",)), Entry("y/**", ("a",)))
    assert _names(suite_map.suites_for(["x/1.py", "y/2.py"], sm)) == ["a", "c"]


def test_a_suite_two_entries_share_is_answered_once():
    sm = _map(Entry("x/**", ("a",)), Entry("y/**", ("a",)))
    assert _names(suite_map.suites_for(["x/1.py", "y/2.py"], sm)) == ["a"]


def test_no_paths_answer_no_suites():
    sm = _map(Entry("x/**", ("a",)))
    assert suite_map.suites_for([], sm) == []


# --- the pattern (CP-533) --------------------------------------------------------------------


def test_single_star_stays_within_one_segment():
    sm = _map(Entry("core/*", ("a",)), Entry("*", ("b",)))
    assert suite_map.unmatched(["core/a.py"], sm) == []
    assert _names(suite_map.suites_for(["core/a.py"], sm)) == ["a"]
    assert _names(suite_map.suites_for(["core/x/a.py"], sm)) == []
    assert _names(suite_map.suites_for(["README.md"], sm)) == ["b"]
    assert _names(suite_map.suites_for(["docs/a.md"], sm)) == []


def test_double_star_spans_any_depth_including_none():
    sm = _map(Entry("core/**", ("a",)))
    assert _names(suite_map.suites_for(["core/a.py"], sm)) == ["a"]
    assert _names(suite_map.suites_for(["core/x/y/a.py"], sm)) == ["a"]


def test_double_star_matches_no_segment_in_the_middle():
    sm = _map(Entry("x/**/b.py", ("a",)))
    assert _names(suite_map.suites_for(["x/b.py"], sm)) == ["a"]
    assert _names(suite_map.suites_for(["x/y/z/b.py"], sm)) == ["a"]
    assert _names(suite_map.suites_for(["x/y/c.py"], sm)) == []


def test_a_trailing_double_star_matches_no_segment():
    # CP-533: `**` matches any number of whole segments, "including none" — so `core/**` with
    # `**` taking no segment is `core` itself.
    sm = _map(Entry("core/**", ("a",)))
    assert _names(suite_map.suites_for(["core"], sm)) == ["a"]
    assert suite_map.unmatched(["core"], sm) == []
    assert suite_map.unmatched(["corex/a.py"], sm) == ["corex/a.py"]


def test_wildcards_match_names_that_begin_with_a_dot():
    # CP-533 makes no exception for a leading dot, and CP-536 has to see tracked dotfiles.
    sm = _map(Entry("*", ("a",)), Entry("core/**", ("b",)))
    assert _names(suite_map.suites_for([".gitignore"], sm)) == ["a"]
    assert _names(suite_map.suites_for(["core/.hidden/x.py"], sm)) == ["b"]


# --- the unmatched report (CP-534) -----------------------------------------------------------


def test_unmatched_paths_are_reported_once_in_input_order():
    sm = _map(Entry("known/**", ("a",)))
    assert suite_map.unmatched(["b", "known/x", "a", "b"], sm) == ["b", "a"]


def test_an_unmatched_path_is_reported_not_raised():
    sm = _map(Entry("known/**", ("a",)))
    assert suite_map.suites_for(["nowhere/x.py"], sm) == []
    assert suite_map.unmatched(["nowhere/x.py"], sm) == ["nowhere/x.py"]


def test_an_entry_may_name_no_suite():
    sm = _map(Entry("docs/**", ()))
    assert suite_map.unmatched(["docs/a.md"], sm) == []
    assert suite_map.suites_for(["docs/a.md"], sm) == []


# --- the integrity check (CP-535) ------------------------------------------------------------


def test_an_entry_naming_an_undeclared_suite_is_refused_by_name():
    sm = _map(Entry("x/**", ("a", "ghost")))
    with pytest.raises(SuiteMapError, match="ghost"):
        suite_map.check(sm)


def test_a_suite_declared_twice_is_refused_by_name():
    sm = _map(Entry("x/**", ("a",)), suites=("a", "twice", "twice"))
    with pytest.raises(SuiteMapError, match="twice"):
        suite_map.check(sm)


# --- the real map over this instance (CP-536 to CP-539) --------------------------------------


def test_every_tracked_path_matches_an_entry():
    missing = suite_map.unmatched(_tracked())
    report = "tracked paths that no entry of suite_map.SUITE_MAP matches:\n" + "\n".join(missing)
    assert missing == [], report


def test_a_new_top_level_folder_is_unmatched():
    assert suite_map.unmatched(["a-folder-no-entry-names/x.py"]) == ["a-folder-no-entry-names/x.py"]


def test_every_tracked_test_file_is_run_by_a_suite():
    covering = [path for suite in suite_map.SUITE_MAP.suites for path in _path_arguments(suite)]
    unrun = []
    for tracked in _tracked():
        file = PurePosixPath(tracked)
        if not _is_test_file(tracked) or _TEMPLATES in file.parents:
            continue
        if not any(path == file or path in file.parents for path in covering):
            unrun.append(tracked)
    assert unrun == [], "tracked test files that no suite's command runs:\n" + "\n".join(unrun)


def test_the_real_map_passes_its_integrity_check():
    suite_map.check()


def test_each_entry_answers_its_suites():
    expected = {
        "core/tools/x.py": ["tools", "launchers", "hooks", "claude-tests", "system-readers"],
        ".claude/hooks/x.py": ["tools", "launchers", "hooks", "claude-tests", "workflows",
                               "system-readers"],
        "skills/g/x.md": ["tools", "launchers", "hooks", "skill-local", "system-readers"],
        "system/projects/p/journey/x.md": ["system-readers", "journey-links"],
        "products/p/x.py": ["products"],
        "README.md": ["tools", "launchers", "hooks", "system-readers"],
        "docs/x.md": [],
        "about/x.md": [],
    }
    for path, names in expected.items():
        assert _names(suite_map.suites_for([path])) == names, path


def test_each_entry_is_what_cp_539_names():
    # CP-539: "The map reads as follows" — the pattern table, row for row and in its order. Since
    # 2026-10-18 `core/**`, `.claude/**` and `skills/**` also run `system-readers`: the checks of
    # this instance's tree left `core/tools/` for `system/tests/`, and an edit under those roots
    # can still break them.
    expected = [
        ("core/**", ("tools", "launchers", "hooks", "claude-tests", "system-readers")),
        (
            ".claude/**",
            ("tools", "launchers", "hooks", "claude-tests", "workflows", "system-readers"),
        ),
        ("skills/**", ("tools", "launchers", "hooks", "skill-local", "system-readers")),
        ("system/**", ("system-readers", "journey-links")),
        ("products/**", ("products",)),
        ("*", ("tools", "launchers", "hooks", "system-readers")),
        ("docs/**", ()),
        ("about/**", ()),
    ]
    assert [(entry.pattern, entry.suites) for entry in suite_map.SUITE_MAP.entries] == expected


def _skill_local_directories() -> list[str]:
    skills = (path for path in _tracked() if path.startswith("skills/") and _is_test_file(path))
    return sorted({str(PurePosixPath(path).parent) for path in skills if path.endswith(".py")})


def test_each_suite_runs_what_cp_539_names():
    system_readers = (
        "system/tests/",
        "core/tools/test_written_forward.py",
        "core/tools/test_check_vendor_neutrality.py",
        "core/tools/test_templates_are_instance_neutral.py",
        "core/tools/test_journey_status.py",
    )
    expected = {
        "tools": ("python3", "-m", "pytest", "-q", "core/tools/"),
        "launchers": ("python3", "-m", "pytest", "-q", "core/launchers/"),
        "hooks": ("python3", "-m", "pytest", "-q", ".claude/hooks/"),
        "claude-tests": ("python3", "-m", "pytest", "-q", ".claude/tests/"),
        "workflows": ("node", "--test", ".claude/workflows/tests/"),
        "skill-local": ("python3", "-m", "pytest", "-q", *_skill_local_directories()),
        "products": ("python3", "-m", "pytest", "-q", "products/"),
        "system-readers": ("python3", "-m", "pytest", "-q", *system_readers),
        "journey-links": ("python3", "core/tools/check_journey_links.py", "--repo", "."),
    }
    declared = {suite.name: suite.command for suite in suite_map.SUITE_MAP.suites}
    assert declared == expected
    assert [suite.name for suite in suite_map.SUITE_MAP.suites] == list(expected)
