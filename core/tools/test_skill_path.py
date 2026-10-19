"""Tests for `skill_path.py` — the one resolver that turns a skill name into its directory
under either the flat layout (`<root>/.claude/skills/<name>`) or the grouped layout
(`<root>/skills/<group>/.claude/skills/<name>`).

Task 1 covers the importable resolution, `resolve_skill_dir`. Task 2 (command-line form) and
Task 3 (`instance_root`, the inverse) each add their own section below, appended by later tasks
in this same file per the plan's per-task test-file-section convention.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import skill_path
from skill_path import Resolution, resolve_skill_dir

_SCRIPT = Path(__file__).resolve().parent / "skill_path.py"


def _make_flat(root, name):
    d = root / ".claude" / "skills" / name
    d.mkdir(parents=True)
    return d


def _make_grouped(root, group, name):
    d = root / "skills" / group / ".claude" / "skills" / name
    d.mkdir(parents=True)
    return d


# --- resolve_skill_dir -----------------------------------------------------------------------


def test_flat_skill_resolves_found(tmp_path):
    flat = _make_flat(tmp_path, "x")

    result = resolve_skill_dir(tmp_path, "x")

    assert result.status == skill_path.FOUND
    assert result.path == flat


def test_flat_wins_when_both_layouts_hold_the_name(tmp_path):
    flat = _make_flat(tmp_path, "x")
    _make_grouped(tmp_path, "g", "x")

    result = resolve_skill_dir(tmp_path, "x")

    assert result.status == skill_path.FOUND
    assert result.path == flat


def test_single_grouped_match_resolves_when_no_flat_directory_exists(tmp_path):
    grouped = _make_grouped(tmp_path, "g", "x")

    result = resolve_skill_dir(tmp_path, "x")

    assert result.status == skill_path.FOUND
    assert result.path == grouped


def test_zero_matches_is_not_found(tmp_path):
    result = resolve_skill_dir(tmp_path, "x")

    assert result.status == skill_path.NOT_FOUND
    assert result.path is None


def test_two_matches_is_ambiguous_and_returns_no_directory(tmp_path):
    a = _make_grouped(tmp_path, "a", "x")
    b = _make_grouped(tmp_path, "b", "x")

    result = resolve_skill_dir(tmp_path, "x")

    assert result.status == skill_path.AMBIGUOUS
    assert result.path is None
    assert result.matches == tuple(sorted([a, b]))


def test_not_found_and_ambiguous_are_different_statuses(tmp_path):
    not_found = resolve_skill_dir(tmp_path, "x")

    _make_grouped(tmp_path, "a", "y")
    _make_grouped(tmp_path, "b", "y")
    ambiguous = resolve_skill_dir(tmp_path, "y")

    assert not_found.status != ambiguous.status


def test_a_name_that_is_a_path_is_refused_regardless_of_the_tree():
    for bad_name in ("a/b", "../x", ".hidden", ".", ""):
        result = resolve_skill_dir("/does/not/exist", bad_name)
        assert result.status == skill_path.INVALID_NAME, bad_name
        assert result.path is None, bad_name


def test_never_raises_on_a_root_that_does_not_exist():
    result = resolve_skill_dir("/does/not/exist/at/all", "x")

    assert result.status == skill_path.NOT_FOUND


def test_never_raises_on_a_root_that_is_a_regular_file(tmp_path):
    f = tmp_path / "not-a-dir"
    f.write_text("x")

    result = resolve_skill_dir(f, "x")

    assert result.status == skill_path.NOT_FOUND


def test_never_raises_on_an_empty_root_directory(tmp_path):
    result = resolve_skill_dir(tmp_path, "x")

    assert result.status == skill_path.NOT_FOUND


def test_symlinked_flat_layer_resolves_under_the_satellite_root(tmp_path):
    host = tmp_path / "host"
    _make_flat(host, "x")
    sat = tmp_path / "sat"
    sat.mkdir()
    (sat / ".claude").mkdir()
    os.symlink(host / ".claude" / "skills", sat / ".claude" / "skills")

    result = resolve_skill_dir(sat, "x")

    assert result.status == skill_path.FOUND
    assert str(result.path).startswith(str(sat))
    assert not str(result.path).startswith(str(host))


def test_symlinked_grouped_layer_resolves_under_the_satellite_root(tmp_path):
    host = tmp_path / "host"
    _make_grouped(host, "g", "x")
    sat = tmp_path / "sat"
    sat.mkdir()
    os.symlink(host / "skills", sat / "skills")

    result = resolve_skill_dir(sat, "x")

    assert result.status == skill_path.FOUND
    assert str(result.path).startswith(str(sat))
    assert not str(result.path).startswith(str(host))


def test_a_regular_file_at_the_flat_path_falls_through_to_the_grouped_scan(tmp_path):
    flat_parent = tmp_path / ".claude" / "skills"
    flat_parent.mkdir(parents=True)
    (flat_parent / "x").write_text("not a directory")
    grouped = _make_grouped(tmp_path, "g", "x")

    result = resolve_skill_dir(tmp_path, "x")

    assert result.status == skill_path.FOUND
    assert result.path == grouped


def test_returned_path_is_absolute_even_when_root_is_relative(tmp_path, monkeypatch):
    _make_flat(tmp_path, "x")
    monkeypatch.chdir(tmp_path)

    result = resolve_skill_dir(".", "x")

    assert result.status == skill_path.FOUND
    assert os.path.isabs(result.path)


# --- a name is a name, not a pattern ------------------------------------------------------------
# The contract is "a skill name in, its directory out" — so a name no skill has is zero matches,
# i.e. not found. The flat branch already answers a metacharacter name that way (`os.path.isdir`
# is literal); the grouped branch must agree, or one name gets two different answers depending on
# which layout it stands in — a silent wrong answer of exactly the kind this resolver exists to
# remove.


def test_a_metacharacter_name_does_not_resolve_to_another_skills_directory(tmp_path):
    _make_grouped(tmp_path, "g", "thing")

    for pattern_name in ("*", "th?ng", "[t]hing"):
        result = resolve_skill_dir(tmp_path, pattern_name)

        assert result.status == skill_path.NOT_FOUND, pattern_name
        assert result.path is None, pattern_name


def test_flat_and_grouped_answer_a_metacharacter_name_alike(tmp_path):
    flat_root = tmp_path / "flat"
    _make_flat(flat_root, "thing")
    grouped_root = tmp_path / "grouped"
    _make_grouped(grouped_root, "g", "thing")

    assert (resolve_skill_dir(flat_root, "*").status
            == resolve_skill_dir(grouped_root, "*").status)


def test_a_root_whose_own_path_holds_a_metacharacter_still_resolves(tmp_path):
    # The root is a path the caller hands in, never a pattern — a directory legitimately named
    # `inst[1]` must resolve its skills like any other root.
    root = tmp_path / "inst[1]"
    grouped = _make_grouped(root, "g", "thing")

    result = resolve_skill_dir(root, "thing")

    assert result.status == skill_path.FOUND
    assert result.path == grouped


def test_module_version_is_semver():
    assert re.fullmatch(r"\d+\.\d+\.\d+", skill_path.__version__)


def test_resolution_is_frozen(tmp_path):
    _make_flat(tmp_path, "x")
    result = resolve_skill_dir(tmp_path, "x")

    assert isinstance(result, Resolution)
    try:
        result.status = skill_path.NOT_FOUND
    except Exception:
        pass
    else:
        raise AssertionError("Resolution must be frozen")


# --- command-line form -------------------------------------------------------------------------
# Every test here runs the module as a real subprocess — an importable function proven only by
# import says nothing about what a shell sees, and the eight bash launchers this contract serves
# branch on stdout/stderr/exit code, not on a Python return value.


def _run(args, cwd=None):
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *args],
        capture_output=True, text=True, cwd=cwd,
    )


def test_cli_flat_skill_exits_0_and_prints_the_directory(tmp_path):
    flat = _make_flat(tmp_path, "x")

    result = _run(["x", "--root", str(tmp_path)])

    assert result.returncode == skill_path.EXIT_OK
    assert result.stdout == f"{flat}\n"
    assert result.stderr == ""


def test_cli_grouped_single_match_exits_0_and_prints_the_directory(tmp_path):
    grouped = _make_grouped(tmp_path, "g", "x")

    result = _run(["x", "--root", str(tmp_path)])

    assert result.returncode == skill_path.EXIT_OK
    assert result.stdout == f"{grouped}\n"


def test_cli_no_match_exits_3_with_empty_stdout_and_stderr_names_skill_and_root(tmp_path):
    result = _run(["x", "--root", str(tmp_path)])

    assert result.returncode == skill_path.EXIT_NOT_FOUND
    assert result.stdout == ""
    assert "x" in result.stderr
    assert str(tmp_path) in result.stderr


def test_cli_two_grouped_matches_exits_4_with_empty_stdout_and_both_on_stderr(tmp_path):
    a = _make_grouped(tmp_path, "a", "x")
    b = _make_grouped(tmp_path, "b", "x")

    result = _run(["x", "--root", str(tmp_path)])

    assert result.returncode == skill_path.EXIT_AMBIGUOUS
    assert result.stdout == ""
    assert str(a) in result.stderr
    assert str(b) in result.stderr


def test_cli_root_omitted_resolves_against_the_process_cwd(tmp_path):
    flat = _make_flat(tmp_path, "x")

    result = _run(["x"], cwd=str(tmp_path))

    assert result.returncode == skill_path.EXIT_OK
    assert result.stdout == f"{flat}\n"


def test_cli_a_path_shaped_name_exits_2_with_empty_stdout(tmp_path):
    for bad_name in ("a/b", ".hidden"):
        result = _run([bad_name, "--root", str(tmp_path)])
        assert result.returncode == 2, bad_name
        assert result.stdout == "", bad_name


def test_cli_no_name_argument_exits_2():
    result = _run([])

    assert result.returncode == 2


def test_cli_exit_constants_are_0_3_4():
    assert skill_path.EXIT_OK == 0
    assert skill_path.EXIT_NOT_FOUND == 3
    assert skill_path.EXIT_AMBIGUOUS == 4


# --- instance_root (the inverse) -----------------------------------------------------------------
# Path arithmetic only — no fixture builds any directory on disk; instance_root never probes.


def test_instance_root_of_a_flat_skill_directory(tmp_path):
    skill_dir = tmp_path / ".claude" / "skills" / "x"

    assert skill_path.instance_root(skill_dir) == tmp_path


def test_instance_root_of_a_grouped_skill_directory_is_the_top_root_not_the_group(tmp_path):
    skill_dir = tmp_path / "skills" / "g" / ".claude" / "skills" / "x"

    result = skill_path.instance_root(skill_dir)

    assert result == tmp_path
    assert result != tmp_path / "skills" / "g"


def test_instance_root_of_a_relative_input_is_absolute(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    result = skill_path.instance_root(Path(".claude") / "skills" / "x")

    assert result.is_absolute()
    assert result == tmp_path


def test_instance_root_of_a_symlinked_layer_keeps_the_callers_root(tmp_path):
    # A satellite's .claude/skills may be a directory symlink into its host (every consumer carried
    # one before every host skill was grouped) — instance_root must never canonicalize, so it
    # returns the satellite's own root, never the host's.
    host = tmp_path / "host"
    (host / ".claude" / "skills" / "x").mkdir(parents=True)
    sat = tmp_path / "sat"
    (sat / ".claude").mkdir(parents=True)
    os.symlink(host / ".claude" / "skills", sat / ".claude" / "skills")

    result = skill_path.instance_root(sat / ".claude" / "skills" / "x")

    assert result == sat


def test_instance_root_falls_back_to_three_levels_up_for_a_shape_matching_neither_layout(tmp_path):
    # A directory that is neither exactly <root>/.claude/skills/<name> nor
    # <root>/skills/<group>/.claude/skills/<name> — today's unconditional behaviour, unchanged.
    odd_dir = tmp_path / "some" / "other" / "shape" / "x"

    result = skill_path.instance_root(odd_dir)

    assert result == tmp_path / "some"


def test_instance_root_never_raises_for_a_path_that_does_not_exist_on_disk():
    result = skill_path.instance_root("/does/not/exist/.claude/skills/x")

    assert result == Path("/does/not/exist")
