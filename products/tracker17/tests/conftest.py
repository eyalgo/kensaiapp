"""Three duties for every test run: the import shim, the collection rule and the source walk.

The shim puts the project root on sys.path so a test can import its subject by module name. The
frame ships no build system and does not install the product itself, so a module at the project
root cannot be imported by package name without it.

The collection rule keeps ``pytest tests/`` from collecting ``tests/e2e/``. The two are separate
suites (docs/nfdr.md § 10): the end-to-end one needs the browser the lock file installs, which the
machine's own pytest does not have. ``pytest tests/e2e/`` names the directory and collects it.

The source walk is the ``walk_of`` fixture: it reads every product module outside ``tests/`` as a
syntax tree, so the layer-6 tests in ``tests/architecture/`` walk code and never run it. A walk
that finds no module in the part it covers fails, so a wrong root cannot pass by finding nothing
(docs/nfdr.md § 1.2).
"""

from __future__ import annotations

import ast
import sys
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path

import pytest

TESTS_DIRECTORY = Path(__file__).resolve().parent
END_TO_END_DIRECTORY = TESTS_DIRECTORY / "e2e"

sys.path.insert(0, str(TESTS_DIRECTORY.parent))


def _command_line_names_end_to_end(arguments: list[str]) -> bool:
    for argument in arguments:
        path_part = argument.split("::", 1)[0]
        resolved = Path(path_part).resolve()
        if resolved == END_TO_END_DIRECTORY or END_TO_END_DIRECTORY in resolved.parents:
            return True
    return False


def pytest_ignore_collect(collection_path: Path, config: pytest.Config) -> bool | None:
    inside_end_to_end = (
        collection_path == END_TO_END_DIRECTORY or END_TO_END_DIRECTORY in collection_path.parents
    )
    if not inside_end_to_end:
        return None
    return not _command_line_names_end_to_end([str(arg) for arg in config.invocation_params.args])


@dataclass(frozen=True)
class Module:
    """One product module: where it is, which part it belongs to, and its syntax tree."""

    path: Path
    part: str
    tree: ast.Module

    def imported(self) -> list[str]:
        """Every dotted name this module imports. A relative import names the module's own part."""
        names: list[str] = []
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                names.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                if node.level > 0:
                    names.append(self.part)
                    continue
                base = node.module or ""
                names.append(base)
                names.extend(f"{base}.{alias.name}" for alias in node.names)
        return names

    def calls(self) -> list[tuple[str, ast.Call]]:
        """Every call, with the dotted name of what is called (empty when it has none)."""
        return [
            (dotted(node.func) or "", node)
            for node in ast.walk(self.tree)
            if isinstance(node, ast.Call)
        ]


def dotted(node: ast.AST) -> str | None:
    """The dotted name an expression spells, such as ``os.replace``, or None."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = dotted(node.value)
        return f"{base}.{node.attr}" if base else None
    return None


class SourceWalk:
    """Every Python module under a root that is not a test, a hidden folder or generated."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def modules(self, part: str | None = None) -> list[Module]:
        found = [module for module in self._all() if part is None or module.part == part]
        assert found, f"no module to walk for {part or 'the product'} under {self.root}"
        return found

    def _all(self) -> Iterator[Module]:
        for path in sorted(self.root.rglob("*.py")):
            relative = path.relative_to(self.root)
            skipped = relative.parts[0] == "tests" or any(
                piece.startswith(".") or piece == "__pycache__" for piece in relative.parts
            )
            if skipped:
                continue
            part = relative.parts[0] if len(relative.parts) > 1 else relative.stem
            yield Module(relative, part, ast.parse(path.read_text(encoding="utf-8")))


@pytest.fixture
def walk_of() -> Callable[[Path | None], SourceWalk]:
    """Build a walk over a root; with none given, over the product itself."""

    def build(root: Path | None = None) -> SourceWalk:
        return SourceWalk(root or TESTS_DIRECTORY.parent)

    return build
