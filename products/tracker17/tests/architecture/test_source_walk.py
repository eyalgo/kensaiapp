"""Layer-6 proof of what the source walk leaves out: three root folders and the compiled-file folder.

Checks SRS NFR-9 (the code keeps its parts apart) and acceptance criterion AC-5. NFDR QC-1 is the
clause: the walk skips the tests, behave and virtual-environment folders at the root by name, and
fails on any other root folder that holds a Python module, whatever its name begins with. Each case
builds a root under a temporary directory, plants files in it and hands the root to the walk, so
the walk is shown to see a code-holding dot-folder and to skip only what it is named to skip.
"""

from __future__ import annotations

from pathlib import Path

from test_shapes import PARTS, top_level_parts

SKIPPED_ROOT_FOLDERS = {"tests", ".behave", ".venv"}
SKIPPED_ANYWHERE = "__pycache__"
THE_SIX_PARTS = (
    "domain/model.py",
    "application/service.py",
    "persistence/store.py",
    "web/site.py",
    "main.py",
    "errors.py",
)
SKIPPED_FILES = (
    "tests/x.py",
    ".behave/features/x.py",
    ".venv/x.py",
    "__pycache__/x.py",
    "domain/__pycache__/x.py",
)


def plant(root: Path, *relatives: str) -> None:
    for relative in relatives:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("x = 1\n", encoding="utf-8")


def root_with_skipped_files(root: Path) -> Path:
    """The six parts and every file the walk leaves out, so the cases cannot drift apart."""
    plant(root, *THE_SIX_PARTS, *SKIPPED_FILES)
    return root


def test_a_code_holding_dot_folder_fails_the_parts_comparison(walk_of, tmp_path: Path) -> None:
    """QC-1: a dot-folder at the root that holds code is a part the comparison reports."""
    plant(root_with_skipped_files(tmp_path), ".other/x.py")
    parts = top_level_parts(walk_of(tmp_path))
    assert parts != PARTS
    assert ".other" in parts
    (tmp_path / ".other" / "x.py").unlink()
    assert top_level_parts(walk_of(tmp_path)) == PARTS


def test_the_named_folders_and_pycache_stay_skipped(walk_of, tmp_path: Path) -> None:
    """QC-1: the three named root folders and the compiled-file folder are not walked."""
    walk = walk_of(root_with_skipped_files(tmp_path))
    assert top_level_parts(walk) == PARTS
    for module in walk.modules():
        assert module.path.parts[0] not in SKIPPED_ROOT_FOLDERS, module.path
        assert SKIPPED_ANYWHERE not in module.path.parts, module.path


def test_a_dot_named_file_at_the_root_is_walked_as_its_own_part(walk_of, tmp_path: Path) -> None:
    """QC-1: a file at the root whose name begins with a dot is a part of its own."""
    plant(tmp_path, *THE_SIX_PARTS, ".x.py")
    assert top_level_parts(walk_of(tmp_path)) == PARTS | {".x"}


def test_a_dot_or_named_folder_inside_a_part_is_walked_as_that_part(
    walk_of, tmp_path: Path
) -> None:
    """QC-1: the skipped names count at the root only; below it they belong to the part."""
    inside = ("web/.hidden/y.py", "domain/.venv/x.py", "domain/tests/x.py")
    plant(tmp_path, *THE_SIX_PARTS, *inside)
    walk = walk_of(tmp_path)
    part_of = {str(module.path): module.part for module in walk.modules()}
    assert {path: part_of.get(path) for path in inside} == {
        "web/.hidden/y.py": "web",
        "domain/.venv/x.py": "domain",
        "domain/tests/x.py": "domain",
    }
    assert top_level_parts(walk) == PARTS


def test_near_names_of_the_skipped_folders_are_walked(walk_of, tmp_path: Path) -> None:
    """QC-1: a name is skipped only when it matches exactly.

    The root holds no folder named tests, because a filesystem that ignores case would make the
    capitalised one the same folder as the skipped one.
    """
    plant(tmp_path, *THE_SIX_PARTS, ".venvs/x.py", ".behave2/x.py", "Tests/x.py")
    parts = top_level_parts(walk_of(tmp_path))
    assert parts == PARTS | {".venvs", ".behave2", "Tests"}
    assert parts != PARTS
