"""Layer-6 shape walks: the parts, who names a concrete class, the contracts, errors, immutability.

Checks SRS NFR-9 (the code keeps its parts apart) and NFR-8, and acceptance criterion AC-5. NFDR
QC-1, QC-2, QC-3, QC-4 and QC-6 are the ones each test names. Each walk reads every module outside
tests/ as a syntax tree and fails when its part holds no module.
"""

from __future__ import annotations

import ast
import builtins
import dataclasses
from pathlib import Path

import pytest

import errors
from domain import TrackerState

PARTS = {"domain", "application", "persistence", "web", "main", "errors"}
CONTRACTS = {"Saver", "Clock"}
BUILTIN_EXCEPTIONS = {
    name
    for name, value in vars(builtins).items()
    if isinstance(value, type) and issubclass(value, BaseException)
}
BASE_ERROR = "AppError"


def classes(walk, part: str | None = None) -> list[tuple[str, ast.ClassDef]]:
    return [
        (str(module.path), node)
        for module in walk.modules(part)
        for node in ast.walk(module.tree)
        if isinstance(node, ast.ClassDef)
    ]


def base_names(node: ast.ClassDef) -> list[str]:
    return [ast.unparse(base).split(".")[-1] for base in node.bases]


def top_level_parts(walk) -> set[str]:
    return {module.part for module in walk.modules()}


def concrete_classes_named_outside_main(walk) -> list[str]:
    own_part = {
        node.name: part for part in ("persistence", "web") for _, node in classes(walk, part)
    }
    found = []
    for module in walk.modules():
        if module.part == "main":
            continue
        for node in ast.walk(module.tree):
            names = []
            if isinstance(node, ast.Name):
                names = [node.id]
            elif isinstance(node, ast.Attribute):
                names = [node.attr]
            elif isinstance(node, ast.alias):
                names = [node.name]
            found += [
                f"{module.path}: {name}"
                for name in names
                if name in own_part and own_part[name] != module.part
            ]
    return found


def classes_inheriting_a_contract(walk) -> list[str]:
    return [
        f"{path}: {node.name}" for path, node in classes(walk) if CONTRACTS & set(base_names(node))
    ]


def error_shape_violations(walk) -> list[str]:
    declared = {node.name: base_names(node) for _, node in classes(walk)}
    where = {node.name: path for path, node in classes(walk)}

    def is_exception(name: str, seen: frozenset[str] = frozenset()) -> bool:
        if name in seen:
            return False
        return any(
            base in BUILTIN_EXCEPTIONS or (base in declared and is_exception(base, seen | {name}))
            for base in declared.get(name, [])
        )

    def derives_from_base(name: str, seen: frozenset[str] = frozenset()) -> bool:
        if name in seen:
            return False
        return any(
            base == BASE_ERROR or (base in declared and derives_from_base(base, seen | {name}))
            for base in declared.get(name, [])
        )

    found = []
    for name, bases in declared.items():
        if name == BASE_ERROR:
            if where[name] != "errors.py" or bases != ["Exception"]:
                found.append(f"{where[name]}: {name} must derive from Exception alone")
            continue
        if {"Exception", "BaseException"} & set(bases):
            found.append(f"{where[name]}: {name} derives directly from Exception")
        if is_exception(name) and not derives_from_base(name):
            found.append(f"{where[name]}: {name} does not derive from {BASE_ERROR}")
    return found


def _is_frozen_dataclass(node: ast.ClassDef) -> bool | None:
    """None when the class is not a dataclass, else whether it is declared frozen=True."""
    for decorator in node.decorator_list:
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        if ast.unparse(target).split(".")[-1] != "dataclass":
            continue
        if not isinstance(decorator, ast.Call):
            return False
        return any(
            keyword.arg == "frozen"
            and isinstance(keyword.value, ast.Constant)
            and keyword.value.value is True
            for keyword in decorator.keywords
        )
    return None


def unfrozen_domain_dataclasses(walk) -> list[str]:
    return [
        f"{path}: {node.name}"
        for path, node in classes(walk, "domain")
        if _is_frozen_dataclass(node) is False
    ]


def test_the_top_level_parts_are_the_five_the_sdd_names(walk_of) -> None:
    """QC-1: the four directories, main.py and errors.py, and no other Python at the root."""
    assert top_level_parts(walk_of()) == PARTS


def test_concrete_persistence_and_web_classes_are_named_only_in_main(walk_of) -> None:
    """QC-2."""
    assert concrete_classes_named_outside_main(walk_of()) == []
    named_in_main = {
        node.id
        for node in ast.walk(walk_of().modules("main")[0].tree)
        if isinstance(node, ast.Name)
    }
    assert {"SavedData", "listen"} <= named_in_main


def test_no_class_inherits_saver_or_clock(walk_of) -> None:
    """QC-3."""
    assert classes_inheriting_a_contract(walk_of()) == []
    declared = {node.name for _, node in classes(walk_of(), "application")}
    assert CONTRACTS <= declared


def test_one_base_error_and_every_other_derives_from_it(walk_of) -> None:
    """QC-4: AppError derives from Exception, and no other class does."""
    assert issubclass(errors.AppError, Exception)
    assert errors.AppError.__bases__ == (Exception,)
    assert error_shape_violations(walk_of()) == []
    assert BASE_ERROR in {node.name for _, node in classes(walk_of())}


def test_domain_dataclasses_are_frozen(walk_of) -> None:
    """QC-6."""
    assert unfrozen_domain_dataclasses(walk_of()) == []
    frozen = [
        node.name for _, node in classes(walk_of(), "domain") if _is_frozen_dataclass(node) is True
    ]
    assert {"Project", "TrackerState"} <= set(frozen)


def test_only_the_task_features_are_added_to_domain() -> None:
    """CP-105, CP-139, CP-200, CP-209, CP-238, CP-274, CP-293, CP-313: the Assignees, Tasks,
    Priorities, Labels, Due dates, Comments and Workflow entries exist, no later feature module
    does, and the state holds exactly what the saved form holds, the one operator name included."""
    domain = Path(__file__).resolve().parent.parent.parent / "domain"
    for landed in (
        "assignees",
        "tasks",
        "workflow",
        "priorities",
        "labels",
        "due_dates",
        "comments",
    ):
        assert (domain / f"{landed}.py").is_file(), landed
    for later in ("filtering", "sorting", "summary"):
        assert not (domain / f"{later}.py").exists(), later
    fields = {field.name for field in dataclasses.fields(TrackerState)}
    assert fields == {
        "projects",
        "next_project_id",
        "assignees",
        "tasks",
        "next_task_id",
        "operator_name",
    }


def test_each_walk_fails_when_its_directory_holds_no_module(walk_of, tmp_path: Path) -> None:
    empty = walk_of(tmp_path)
    for walk in (
        top_level_parts,
        concrete_classes_named_outside_main,
        classes_inheriting_a_contract,
        error_shape_violations,
        unfrozen_domain_dataclasses,
    ):
        with pytest.raises(AssertionError):
            walk(empty)


def test_each_walk_finds_a_violation_planted_where_it_looks(walk_of, tmp_path: Path) -> None:
    """The walks can fail: one planted violation per clause is reported."""
    planted = {
        "stray/x.py": "x = 1\n",
        "errors.py": "class AppError(Exception):\n    pass\n",
        "persistence/store.py": "class Store:\n    pass\n",
        "web/site.py": "from persistence import Store\nclass Page(Store):\n    pass\n",
        "application/contracts.py": "class Saver:\n    pass\n",
        "application/impl.py": (
            "class Mine(Saver):\n    pass\n"
            "class Raw(Exception):\n    pass\n"
            "class Other(ValueError):\n    pass\n"
        ),
        "domain/value.py": (
            "from dataclasses import dataclass\n"
            "@dataclass\nclass Loose:\n    x: int\n"
            "@dataclass(frozen=False)\nclass Mutable:\n    x: int\n"
        ),
        "main.py": "x = 1\n",
    }
    for relative, source in planted.items():
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source, encoding="utf-8")
    walk = walk_of(tmp_path)
    assert top_level_parts(walk) != PARTS
    assert concrete_classes_named_outside_main(walk)
    assert classes_inheriting_a_contract(walk)
    problems = error_shape_violations(walk)
    assert any("Raw" in problem for problem in problems)
    assert any("Other" in problem for problem in problems)
    assert len(unfrozen_domain_dataclasses(walk)) == 2
