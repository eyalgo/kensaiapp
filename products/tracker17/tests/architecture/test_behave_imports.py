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
from test_imports import violations
from test_shapes import PARTS, top_level_parts

_FOLDER = ".behave"
_THE_SIX_PARTS = (
    "domain/model.py",
    "application/service.py",
    "persistence/store.py",
    "web/site.py",
    "main.py",
    "errors.py",
)


def _plant(root: Path, *relatives: str, text: str = "x = 1\n") -> None:
    for relative in relatives:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")


def _paths(walk) -> list[str]:
    return [module.path.as_posix() for module in walk.modules()]


def imports_from_tests(walk) -> list[str]:
    """Every import in the scenario folder whose first dotted piece is exactly tests."""
    return [
        f"{module.path}: {name}"
        for module in walk.modules()
        for name in module.imported()
        if name.split(".")[0] == "tests"
    ]


def check_behave_folder(walk) -> None:
    """The real-product check: the folder is there, and nothing in it imports from tests."""
    assert (walk.root / _FOLDER).is_dir(), f"no {_FOLDER} folder under {walk.root}"
    assert imports_from_tests(walk) == []


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


def test_a_dangling_link_named_behave_fails_naming_the_folder(
    behave_walk_of, tmp_path: Path
) -> None:
    """CP-797, CP-799: a link whose target is gone is still an entry, and it leaves nothing to
    read, so it fails as a plain file does rather than passing as an absent entry."""
    (tmp_path / _FOLDER).symlink_to(tmp_path / "gone")
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


def test_a_folder_whose_name_ends_in_py_is_read_as_a_folder(behave_walk_of, tmp_path: Path) -> None:
    """CP-798: every subfolder is read whatever its name, one named like a module included, and
    the folder itself is not taken for a module."""
    _plant(tmp_path, ".behave/features/pkg.py/a.py")
    assert _paths(behave_walk_of(tmp_path)) == [".behave/features/pkg.py/a.py"]


def test_modules_come_back_sorted_by_path_from_any_depth(behave_walk_of, tmp_path: Path) -> None:
    """The walk's contract: one module per file, sorted by path, a file directly in the folder
    and one several folders down included."""
    _plant(
        tmp_path,
        ".behave/z.py",
        ".behave/features/steps/b.py",
        ".behave/a.py",
        ".behave/features/m.py",
    )
    assert _paths(behave_walk_of(tmp_path)) == [
        ".behave/a.py",
        ".behave/features/m.py",
        ".behave/features/steps/b.py",
        ".behave/z.py",
    ]


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


def test_a_root_without_a_behave_entry_passes(behave_walk_of, tmp_path: Path) -> None:
    """CP-797: with no scenario folder the check reads nothing and lists nothing."""
    assert imports_from_tests(behave_walk_of(tmp_path)) == []


def test_an_import_from_tests_fails_listing_the_module(behave_walk_of, tmp_path: Path) -> None:
    """CP-800, CP-802: the site is listed, and the same file without the line is clean."""
    _plant(tmp_path, ".behave/features/x.py", text="from tests import conftest\n")
    found = imports_from_tests(behave_walk_of(tmp_path))
    assert (
        ".behave/features/x.py: tests" in found or ".behave/features/x.py: tests.conftest" in found
    )
    _plant(tmp_path, ".behave/features/x.py", text="x = 1\n")
    assert imports_from_tests(behave_walk_of(tmp_path)) == []


def test_an_import_inside_a_function_is_found(behave_walk_of, tmp_path: Path) -> None:
    """CP-800: the statement may sit anywhere in the module."""
    _plant(tmp_path, ".behave/features/a.py", text="def f():\n    import tests\n")
    found = imports_from_tests(behave_walk_of(tmp_path))
    assert ".behave/features/a.py: tests" in found


def test_the_remaining_forms_are_each_found(behave_walk_of, tmp_path: Path) -> None:
    """CP-800: an aliased import, a dotted from-import and one under a condition."""
    _plant(tmp_path, ".behave/features/a.py", text="import tests.x as y\n")
    _plant(tmp_path, ".behave/features/b.py", text="from tests.x import y\n")
    _plant(tmp_path, ".behave/features/c.py", text="if True:\n    import tests\n")
    found = imports_from_tests(behave_walk_of(tmp_path))
    for name in ("a", "b", "c"):
        assert any(entry.startswith(f".behave/features/{name}.py: tests") for entry in found), name


def test_a_multi_name_import_lists_the_tests_name_only(behave_walk_of, tmp_path: Path) -> None:
    """CP-800: the name that is not from tests is not listed."""
    _plant(tmp_path, ".behave/features/a.py", text="import os, tests.x\n")
    found = imports_from_tests(behave_walk_of(tmp_path))
    assert ".behave/features/a.py: tests.x" in found
    assert not any(entry.endswith(": os") for entry in found)


def test_every_site_in_one_run_is_listed(behave_walk_of, tmp_path: Path) -> None:
    """CP-802: one call lists every module that imports from tests, not the first."""
    _plant(tmp_path, ".behave/features/a.py", text="import tests.x\n")
    _plant(tmp_path, ".behave/features/b.py", text="from tests.y import z\n")
    found = imports_from_tests(behave_walk_of(tmp_path))
    assert any(entry.startswith(".behave/features/a.py: ") for entry in found)
    assert any(entry.startswith(".behave/features/b.py: ") for entry in found)


def test_an_import_under_a_skipped_folder_is_not_listed(behave_walk_of, tmp_path: Path) -> None:
    """CP-798: the folder's virtual environment is not its code."""
    _plant(tmp_path, ".behave/.venv/lib/pkg.py", text="import tests\n")
    _plant(tmp_path, ".behave/features/a.py")
    assert imports_from_tests(behave_walk_of(tmp_path)) == []


def test_named_and_dot_folders_are_checked(behave_walk_of, tmp_path: Path) -> None:
    """CP-798, CP-800: a folder named tests and a dot folder inside the scenario folder count."""
    _plant(tmp_path, ".behave/tests/y.py", text="from tests import conftest\n")
    _plant(tmp_path, ".behave/.hidden/z.py", text="import tests\n")
    found = imports_from_tests(behave_walk_of(tmp_path))
    assert any(entry.startswith(".behave/tests/y.py: ") for entry in found)
    assert any(entry.startswith(".behave/.hidden/z.py: ") for entry in found)


def test_near_names_and_nested_names_are_checked(behave_walk_of, tmp_path: Path) -> None:
    """CP-798: a name is skipped only when it matches exactly."""
    planted = (
        ".behave/.venvs/a.py",
        ".behave/features/__pycache__2/b.py",
        ".behave/features/.venv/c.py",
        ".behave/.behave/d.py",
    )
    for relative in planted:
        _plant(tmp_path, relative, text="import tests\n")
    found = imports_from_tests(behave_walk_of(tmp_path))
    for relative in planted:
        assert any(entry.startswith(f"{relative}: ") for entry in found), relative


def test_near_names_and_relative_imports_are_not_imports_from_tests(
    behave_walk_of, tmp_path: Path
) -> None:
    """CP-801: another module's name, and a relative import, are not an import from tests."""
    _plant(
        tmp_path,
        ".behave/features/a.py",
        text="import testsuite\nfrom tests_util import x\nfrom .tests import y\n",
    )
    _plant(tmp_path, ".behave/tests/w.py", text="from . import x\n")
    assert imports_from_tests(behave_walk_of(tmp_path)) == []


def test_third_party_standard_library_and_sibling_imports_pass(
    behave_walk_of, tmp_path: Path
) -> None:
    """CP-803: the check applies no other clause to the scenario folder."""
    text = (
        "from behave import given\nimport httpx\nimport subprocess\n"
        "from server_way_in import request_page\n"
    )
    _plant(tmp_path, ".behave/features/a.py", text=text)
    assert imports_from_tests(behave_walk_of(tmp_path)) == []


def test_the_real_behave_folder_passes_and_is_present(behave_walk_of) -> None:
    """CP-804: the product's own scenario folder is read, and imports nothing from tests."""
    walk = behave_walk_of()
    check_behave_folder(walk)
    assert walk.modules()


def test_the_real_product_check_fails_when_the_root_holds_no_behave_folder(
    behave_walk_of, tmp_path: Path
) -> None:
    """CP-804: a check aimed at a root with no scenario folder cannot pass by reading nothing."""
    with pytest.raises(AssertionError):
        check_behave_folder(behave_walk_of(tmp_path))


def test_the_root_walk_misses_a_planted_import_from_tests(
    behave_walk_of, walk_of, tmp_path: Path
) -> None:
    """CP-806: the product-root walk sees nothing wrong, and this walk lists the site."""
    _plant(tmp_path, *_THE_SIX_PARTS)
    _plant(tmp_path, ".behave/features/x.py", text="from tests import conftest\n")
    for part in PARTS:
        assert violations(walk_of(tmp_path), part) == []
    assert top_level_parts(walk_of(tmp_path)) == PARTS
    found = imports_from_tests(behave_walk_of(tmp_path))
    assert any(entry.startswith(".behave/features/x.py: ") for entry in found)


def test_the_root_walk_misses_an_empty_behave_folder(
    behave_walk_of, walk_of, tmp_path: Path
) -> None:
    """CP-806: the product-root walk sees nothing wrong, and this walk fails naming the folder."""
    _plant(tmp_path, *_THE_SIX_PARTS)
    (tmp_path / _FOLDER).mkdir()
    for part in PARTS:
        assert violations(walk_of(tmp_path), part) == []
    assert top_level_parts(walk_of(tmp_path)) == PARTS
    with pytest.raises(AssertionError, match=_FOLDER):
        imports_from_tests(behave_walk_of(tmp_path))
