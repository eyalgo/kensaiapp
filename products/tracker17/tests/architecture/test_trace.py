"""The pointer test: every path and requirement a docstring names exists (SDD § 4 TS-4).

Checks SRS NFR-9 (a reader can reach the code that builds a feature from the requirement) and
acceptance criterion AC-5 (the trace). NFDR QC-11 is the clause. The entry module's docstring and
each test module's docstring are read. Each path they name must exist under the product root, and
each requirement identifier must be defined in docs/SRS.md. The feature words whose slice has
landed are listed in LANDED_FEATURE_WORDS, and each later slice adds its own word there. The file
also checks the other way: every word in SDD § 4 TS-3's table that has its domain/<word>.py must be
listed as landed. Those words are read from docs/SDD.md when the tests run.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

PRODUCT_ROOT = Path(__file__).resolve().parent.parent.parent
TESTS_DIRECTORY = PRODUCT_ROOT / "tests"
SRS = (PRODUCT_ROOT / "docs" / "SRS.md").read_text(encoding="utf-8")
SDD = (PRODUCT_ROOT / "docs" / "SDD.md").read_text(encoding="utf-8")
FEATURE_WORD_HEADER = "Feature word"
DOMAIN_DIRECTORY = PRODUCT_ROOT / "domain"
LANDED_FEATURE_WORDS = [
    "projects",
    "assignees",
    "tasks",
    "workflow",
    "priorities",
    "labels",
    "due_dates",
    "comments",
]
PATH = re.compile(r"(?<![\w/.<-])((?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_-]+\.(?:py|css|md|toml|txt))\b")
REQUIREMENT = re.compile(r"\b(?:NFR|FR|DR|AC|C)-\d+\b")


def docstring_of(path: Path) -> str:
    return ast.get_docstring(ast.parse(path.read_text(encoding="utf-8"))) or ""


def entry_docstring(word: str = "projects") -> str:
    return docstring_of(PRODUCT_ROOT / "domain" / f"{word}.py")


def modules_under_test() -> list[Path]:
    return sorted(TESTS_DIRECTORY.rglob("test_*.py"))


def named_paths(text: str) -> list[str]:
    return PATH.findall(text)


def missing_paths(text: str, root: Path = PRODUCT_ROOT) -> list[str]:
    return [path for path in named_paths(text) if not (root / path).exists()]


def named_requirements(text: str) -> list[str]:
    return REQUIREMENT.findall(text)


def unknown_requirements(text: str, srs: str = SRS) -> list[str]:
    return [
        identifier
        for identifier in named_requirements(text)
        if re.search(rf"^- \*\*{identifier}:\*\*", srs, re.MULTILINE) is None
    ]


def table_cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def feature_words(text: str = SDD) -> list[str]:
    """The words in the Feature word column of the table headed by that cell, in row order."""
    lines = text.splitlines()
    for position, line in enumerate(lines):
        header = table_cells(line) if line.lstrip().startswith("|") else []
        if FEATURE_WORD_HEADER not in header:
            continue
        column = header.index(FEATURE_WORD_HEADER)
        words: list[str] = []
        for row in lines[position + 2 :]:
            if not row.lstrip().startswith("|"):
                break
            cells = table_cells(row)
            if len(cells) > column:
                words.append(cells[column].strip("`"))
        return words
    return []


FEATURE_WORDS = feature_words()


def unlisted_feature_words(
    words: list[str] = FEATURE_WORDS,
    landed: list[str] = LANDED_FEATURE_WORDS,
    domain: Path = DOMAIN_DIRECTORY,
) -> list[str]:
    """The words, in table order, that have their file in domain and are not listed as landed."""
    return [word for word in words if (domain / f"{word}.py").is_file() and word not in landed]


def test_every_path_named_in_the_entry_docstring_exists() -> None:
    for word in LANDED_FEATURE_WORDS:
        text = entry_docstring(word)
        assert named_paths(text), f"the {word} entry docstring names no path"
        assert missing_paths(text) == []


def test_every_path_named_in_a_test_module_docstring_exists() -> None:
    assert modules_under_test()
    for module in modules_under_test():
        assert missing_paths(docstring_of(module)) == [], module.name


def test_every_requirement_identifier_named_exists_in_the_srs() -> None:
    """QC-11, in the entry docstring and in each test module's docstring."""
    texts = [entry_docstring(word) for word in LANDED_FEATURE_WORDS]
    texts += [docstring_of(module) for module in modules_under_test()]
    for text in texts:
        assert unknown_requirements(text) == []


def test_every_test_module_names_a_requirement_or_acceptance_criterion() -> None:
    """QC-11."""
    unnamed = [
        str(module.relative_to(PRODUCT_ROOT))
        for module in modules_under_test()
        if not named_requirements(docstring_of(module))
    ]
    assert unnamed == []


def test_each_landed_feature_word_has_its_domain_module() -> None:
    for word in LANDED_FEATURE_WORDS:
        assert (PRODUCT_ROOT / "domain" / f"{word}.py").is_file(), word


def test_projects_entry_docstring_names_its_parts() -> None:
    """QC-11: at least one requirement, one application module, one web module, one test module."""
    text = entry_docstring("projects")
    paths = named_paths(text)
    assert named_requirements(text)
    assert any(path.startswith("application/") for path in paths)
    assert any(path.startswith("web/") for path in paths)
    assert any(path.startswith("tests/") for path in paths)


def test_assignees_entry_names_requirements_and_existing_participants() -> None:
    """QC-11, CP-102: the Assignees entry names its requirements, its parts and its checking tests.

    The tests this change adds after the domain task are named by the task that writes them, so a
    path is named here only once its file exists.
    """
    text = entry_docstring("assignees")
    paths = named_paths(text)
    assert {"FR-20", "FR-22", "FR-39", "FR-40", "DR-4", "NFR-9"} <= set(named_requirements(text))
    assert any(path.startswith("application/") for path in paths)
    assert any(path.startswith("web/") for path in paths)
    assert "tests/unit/test_assignees.py" in paths
    assert "tests/unit/test_state.py" in paths
    assert missing_paths(text) == []
    assert unknown_requirements(text) == []


ASSIGNEE_PARTICIPANTS = [
    "application/tracker.py",
    "persistence/saved_data.py",
    "web/pages.py",
    "web/routes.py",
]
ASSIGNEE_CHECKING_TESTS = [
    "tests/unit/test_assignees.py",
    "tests/unit/test_state.py",
    "tests/integration/test_assignee_tracker.py",
    "tests/integration/test_saved_data.py",
    "tests/integration/test_start.py",
    "tests/integration/test_people_pages.py",
    "tests/integration/test_people_routes.py",
    "tests/integration/test_pages.py",
    "tests/integration/test_routes.py",
    "tests/e2e/test_people.py",
]


def test_assignees_entry_names_all_participating_modules_and_checks() -> None:
    """CP-102: the final entry docstring names every participating production module and every
    test module that checks the feature, and each named path exists."""
    text = entry_docstring("assignees")
    paths = named_paths(text)
    assert {"FR-20", "FR-22", "FR-39", "FR-40", "DR-4", "NFR-9"} <= set(named_requirements(text))
    for participant in ASSIGNEE_PARTICIPANTS:
        assert participant in paths, participant
    for checking in ASSIGNEE_CHECKING_TESTS:
        assert checking in paths, checking
    assert missing_paths(text) == []
    assert unknown_requirements(text) == []


def test_the_pointer_checks_can_fail() -> None:
    """A path that is not there, and an identifier SRS.md does not define, are reported."""
    assert missing_paths("See domain/nowhere.py and web/pages.py.") == ["domain/nowhere.py"]
    assert unknown_requirements("Realizes FR-9999 and FR-10 and QC-11.") == ["FR-9999"]
    assert unknown_requirements("Realizes FR-10 and NFR-9.") == []


FEATURE_TABLE_HEADER = "| PRD Core Feature | Feature word | SRS requirements |"


def table_text(*rows: str) -> str:
    unrelated = "| Name | Kind |\n|---|---|\n| `alpha` | one |\n| `beta` | two |\n"
    table = "\n".join([FEATURE_TABLE_HEADER, "|---|---|---|", *rows])
    return f"{unrelated}\n{table}\n\nA paragraph follows.\n"


def test_the_feature_words_are_read_from_the_table() -> None:
    text = table_text(
        "| Projects | `projects` | FR-10 |",
        "| Tasks | `tasks` | FR-15 |",
        "| Labels | `labels` | FR-23 |",
    )
    assert feature_words(text) == ["projects", "tasks", "labels"]


def test_the_reader_finds_the_words_only_in_the_table_whose_header_holds_the_cell() -> None:
    text = table_text("| Projects | `projects` | FR-10 |") + "| Late | `late` | FR-1 |\n"
    words = feature_words(text)
    assert "alpha" not in words
    assert "beta" not in words
    assert "late" not in words
    assert words == ["projects"]


def test_the_reader_returns_nothing_when_no_header_matches() -> None:
    assert feature_words("| Name | Kind |\n|---|---|\n| `alpha` | one |\n") == []


def test_the_reader_skips_a_row_shorter_than_the_header() -> None:
    text = table_text(
        "| Projects | `projects` | FR-10 |",
        "| Tasks |",
        "| Labels | `labels` | FR-23 |",
    )
    assert feature_words(text) == ["projects", "labels"]


def test_the_reader_reads_the_column_the_header_names() -> None:
    text = (
        "| Feature word | SRS requirements | PRD Core Feature |\n"
        "|---|---|---|\n"
        "| `projects` | FR-10 | Projects |\n"
        "| `tasks` | FR-15 | Tasks |\n"
    )
    assert feature_words(text) == ["projects", "tasks"]


def test_the_real_table_yields_its_eleven_words() -> None:
    """CP-48's list, stated once here as the SDD states it, to guard the reader's layout."""
    assert feature_words() == [
        "projects",
        "tasks",
        "workflow",
        "priorities",
        "assignees",
        "labels",
        "due_dates",
        "comments",
        "filtering",
        "sorting",
        "summary",
    ]


def build_domain(directory: Path, *names: str) -> Path:
    directory.mkdir()
    for name in names:
        (directory / name).write_text('"""A module."""\n', encoding="utf-8")
    return directory


def test_each_feature_word_with_its_domain_module_is_listed_as_landed() -> None:
    """QC-11, the reverse direction. The whole offender list is asserted, so a report names all."""
    assert feature_words()
    assert unlisted_feature_words() == []


def test_the_reverse_check_can_fail(tmp_path: Path) -> None:
    domain = build_domain(
        tmp_path / "domain", "projects.py", "tasks.py", "labels.py", "helpers.py", "__init__.py"
    )
    words = ["projects", "tasks", "labels", "sorting"]
    assert unlisted_feature_words(words, ["projects"], domain) == ["tasks", "labels"]
    assert unlisted_feature_words(words, ["projects", "tasks"], domain) == ["labels"]
    assert unlisted_feature_words(words, words, domain) == []


def test_the_reverse_check_leaves_the_products_domain_directory_as_found(tmp_path: Path) -> None:
    before = sorted(path.name for path in DOMAIN_DIRECTORY.iterdir())
    test_the_reverse_check_can_fail(tmp_path)
    assert sorted(path.name for path in DOMAIN_DIRECTORY.iterdir()) == before


def test_the_reverse_check_ignores_a_word_with_no_file(tmp_path: Path) -> None:
    domain = build_domain(tmp_path / "domain", "projects.py")
    assert unlisted_feature_words(["sorting"], [], domain) == []
    assert unlisted_feature_words(["sorting"], ["sorting"], domain) == []


def test_the_reverse_check_ignores_a_module_that_is_no_table_words_entry(tmp_path: Path) -> None:
    domain = build_domain(tmp_path / "domain", "refusals.py", "state.py", "text.py", "__init__.py")
    assert unlisted_feature_words(["projects", "tasks"], [], domain) == []


TASK_FEATURE_ENTRIES = {
    "tasks": {"FR-15", "FR-39", "FR-40", "DR-2"},
    "priorities": {"FR-15", "FR-36"},
    "due_dates": {"FR-24", "FR-25", "FR-26"},
}


def test_task_feature_entries_name_requirements_existing_participants_and_checks() -> None:
    """QC-11, CP-138: each new entry names its SRS requirements, an application module, a web
    module and the test modules present at this point, and every path it names exists."""
    for word, requirements in TASK_FEATURE_ENTRIES.items():
        text = entry_docstring(word)
        paths = named_paths(text)
        assert requirements <= set(named_requirements(text)), word
        assert any(path.startswith("application/") for path in paths), word
        assert any(path.startswith("web/") for path in paths), word
        assert f"tests/unit/test_{word}.py" in paths, word
        assert missing_paths(text) == [], word
        assert unknown_requirements(text) == [], word


def test_no_excluded_feature_entry_exists() -> None:
    """CP-139, CP-209: the landed words are the only feature words that have a domain module, and
    the Labels entry is among them."""
    others = [word for word in FEATURE_WORDS if (DOMAIN_DIRECTORY / f"{word}.py").is_file()]
    assert sorted(others) == sorted(LANDED_FEATURE_WORDS)
    assert (DOMAIN_DIRECTORY / "labels.py").is_file()


LABEL_PARTICIPANTS = [
    "application/tracker.py",
    "application/__init__.py",
    "web/pages.py",
    "web/routes.py",
]
LABEL_CHECKING_TESTS = [
    "tests/unit/test_labels.py",
    "tests/unit/test_tasks.py",
    "tests/architecture/test_shapes.py",
    "tests/architecture/test_trace.py",
    "tests/integration/test_label_tracker.py",
    "tests/integration/test_label_pages.py",
    "tests/integration/test_label_routes.py",
    "tests/integration/test_label_listener.py",
    "tests/integration/test_saved_data.py",
    "tests/integration/test_start.py",
    "tests/integration/test_routes.py",
    "tests/integration/test_timed_run.py",
    "tests/e2e/test_labels.py",
    "tests/timed_run.py",
]


def test_labels_entry_names_requirements_participants_and_checks() -> None:
    """QC-11, CP-200: the Labels entry names FR-23 and FR-40, every participating application and
    web module and every module that checks the feature, and each named path exists."""
    text = entry_docstring("labels")
    paths = named_paths(text)
    assert {"FR-23", "FR-40"} <= set(named_requirements(text))
    for participant in LABEL_PARTICIPANTS:
        assert participant in paths, participant
    for checking in LABEL_CHECKING_TESTS:
        assert checking in paths, checking
    assert missing_paths(text) == []
    assert unknown_requirements(text) == []


def test_every_label_checking_module_names_a_requirement_or_acceptance_criterion() -> None:
    """CP-200: each test module the label change adds names what it checks."""
    for checking in LABEL_CHECKING_TESTS:
        module = PRODUCT_ROOT / checking
        assert module.is_file(), checking
        assert named_requirements(docstring_of(module)), checking


COMMENT_REQUIREMENTS = {"FR-28", "FR-29", "FR-30", "FR-39", "FR-40", "DR-3", "DR-6"}
COMMENT_CHECKING_TESTS = (
    "tests/unit/test_comments.py",
    "tests/integration/test_comment_tracker.py",
    "tests/integration/test_comment_pages.py",
)


def test_comments_entry_has_existing_trace_paths_and_landed_word() -> None:
    """QC-11, CP-266, CP-274: the Comments entry names its requirements, an application module, a
    web module and the checking tests present at this point, and `comments` is listed as landed."""
    text = entry_docstring("comments")
    paths = named_paths(text)
    assert COMMENT_REQUIREMENTS <= set(named_requirements(text))
    assert any(path.startswith("application/") for path in paths)
    assert any(path.startswith("web/") for path in paths)
    assert set(COMMENT_CHECKING_TESTS) <= set(paths)
    assert "comments" in LANDED_FEATURE_WORDS
    assert missing_paths(text) == []
    assert unknown_requirements(text) == []


COMMENT_PARTICIPANTS = (
    "application/tracker.py",
    "application/__init__.py",
    "web/pages.py",
    "web/routes.py",
)
COMMENT_EVERY_CHECK = (
    *COMMENT_CHECKING_TESTS,
    "tests/unit/test_tasks.py",
    "tests/architecture/test_shapes.py",
    "tests/architecture/test_trace.py",
    "tests/integration/test_comment_routes.py",
    "tests/integration/test_routes.py",
    "tests/integration/test_task_pages.py",
    "tests/integration/test_saved_data.py",
    "tests/integration/test_start.py",
    "tests/e2e/test_comments.py",
)


def test_comments_entry_names_every_participating_module_and_check() -> None:
    """QC-11, CP-266: the finished Comments entry names its requirements, every application and
    web module that takes part and every unit, integration, start, architecture and browser module
    that checks it, and each named path exists and each named test module names what it checks."""
    text = entry_docstring("comments")
    paths = named_paths(text)
    assert COMMENT_REQUIREMENTS <= set(named_requirements(text))
    for participant in COMMENT_PARTICIPANTS:
        assert participant in paths, participant
    for checking in COMMENT_EVERY_CHECK:
        assert checking in paths, checking
        module = PRODUCT_ROOT / checking
        assert module.is_file(), checking
        assert named_requirements(docstring_of(module)), checking
    assert missing_paths(text) == []
    assert unknown_requirements(text) == []
