"""Layer-6 walk of the scenario folder: what it reads, and what it leaves out.

Checks SRS NFR-9 (the code keeps its parts apart) and acceptance criterion AC-5. NFDR QC-19 is the
clause: no module outside the tests folder imports from it, and the clause binds the Behave
scenario folder too. Each case builds a root under a temporary directory, plants files in it and
hands the root to the scenario folder's own walk, so the walk is shown to read every folder it is
not told to skip and to fail when the folder exists and it reads nothing.
"""

from __future__ import annotations

from pathlib import Path

import pytest

_FOLDER = ".behave"


def _plant(root: Path, *relatives: str, text: str = "x = 1\n") -> None:
    for relative in relatives:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")


def _paths(walk) -> list[str]:
    return [module.path.as_posix() for module in walk.modules()]


def test_a_root_without_a_behave_entry_reads_nothing(behave_walk_of, tmp_path: Path) -> None:
    """CP-797: an absent entry is not a failure of the walk, and nothing is read."""
    assert behave_walk_of(tmp_path).modules() == []


def test_an_empty_behave_folder_fails_naming_the_folder(behave_walk_of, tmp_path: Path) -> None:
    """CP-799: the folder exists and holds no module."""
    (tmp_path / _FOLDER).mkdir()
    with pytest.raises(AssertionError, match=_FOLDER):
        behave_walk_of(tmp_path).modules()


def test_only_skipped_files_fail_naming_the_folder(behave_walk_of, tmp_path: Path) -> None:
    """CP-798, CP-799: files only under the virtual environment and a compiled-file folder."""
    _plant(tmp_path, ".behave/.venv/lib/pkg.py", ".behave/features/__pycache__/e.py")
    with pytest.raises(AssertionError, match=_FOLDER):
        behave_walk_of(tmp_path).modules()


def test_a_plain_file_named_behave_fails_naming_the_folder(behave_walk_of, tmp_path: Path) -> None:
    """CP-799: an entry that is a file and not a folder leaves nothing to read."""
    (tmp_path / _FOLDER).write_text("x = 1\n", encoding="utf-8")
    with pytest.raises(AssertionError, match=_FOLDER):
        behave_walk_of(tmp_path).modules()


def test_the_virtual_environment_is_skipped_and_the_rest_read(
    behave_walk_of, tmp_path: Path
) -> None:
    """CP-798: only the folder's own virtual environment is left out."""
    _plant(tmp_path, ".behave/.venv/lib/pkg.py", ".behave/features/a.py")
    paths = _paths(behave_walk_of(tmp_path))
    assert paths == [".behave/features/a.py"]
    assert not any(path.startswith(".behave/.venv/") for path in paths)


def test_named_and_dot_folders_inside_the_folder_are_read(behave_walk_of, tmp_path: Path) -> None:
    """CP-798: a folder named tests, a dot folder and a folder named like the root one are read."""
    _plant(tmp_path, ".behave/tests/y.py", ".behave/.hidden/z.py", ".behave/.behave/d.py")
    assert set(_paths(behave_walk_of(tmp_path))) == {
        ".behave/tests/y.py",
        ".behave/.hidden/z.py",
        ".behave/.behave/d.py",
    }


def test_near_names_and_nested_names_are_read(behave_walk_of, tmp_path: Path) -> None:
    """CP-798: a name is skipped only when it matches exactly, and the virtual-environment name
    counts at the top of the folder only."""
    _plant(
        tmp_path,
        ".behave/.venvs/a.py",
        ".behave/features/__pycache__2/b.py",
        ".behave/features/.venv/c.py",
        ".behave/features/__pycache__/e.py",
    )
    assert set(_paths(behave_walk_of(tmp_path))) == {
        ".behave/.venvs/a.py",
        ".behave/features/__pycache__2/b.py",
        ".behave/features/.venv/c.py",
    }


def test_every_module_path_begins_with_the_folder_and_its_part_is_the_folder(
    behave_walk_of, tmp_path: Path
) -> None:
    """The walk's contract: paths run from the product root, and the part is the folder's name."""
    _plant(tmp_path, ".behave/features/a.py", ".behave/tests/y.py", ".behave/.hidden/z.py")
    modules = behave_walk_of(tmp_path).modules()
    assert modules
    for module in modules:
        assert module.path.as_posix().startswith(".behave/"), module.path
        assert module.part == _FOLDER, module.path


def test_a_relative_import_in_a_nested_folder_is_not_read_as_the_tests_part(
    behave_walk_of, tmp_path: Path
) -> None:
    """CP-801: a relative import names the folder's own part, never the first path piece."""
    _plant(tmp_path, ".behave/tests/w.py", text="from . import x\n")
    (module,) = behave_walk_of(tmp_path).modules()
    assert module.imported() == [_FOLDER]


def test_the_walk_returns_the_existing_module_type(behave_walk_of, walk_of, tmp_path: Path) -> None:
    """The request's reuse: each result is the type the product-root walk returns, and
    imported() works on it."""
    _plant(tmp_path, ".behave/features/a.py", "main.py", text="import os\n")
    (module,) = behave_walk_of(tmp_path).modules()
    (existing,) = walk_of(tmp_path).modules()
    assert type(module) is type(existing)
    assert module.imported() == ["os"]
