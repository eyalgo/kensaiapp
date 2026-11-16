"""The Behave starter runs on its own locked `uv` setup, and the proof of it leaves the repository
as found.

WHY THIS EXISTS
    `core/templates/behave-starter/` is a folder a product receives whole, as `.behave`. Nothing in
    the repository would notice if its lock drifted from its `pyproject.toml`, if a way in stopped
    working, or if a run started writing into the product: the starter's own files are not
    collected by the suite (`test_suite_map.py` skips test files under `core/templates/`). This
    file is the proof that `uv run --locked behave`, run inside the folder, goes green on the three
    scenarios, goes red naming the scenario once one fails, and leaves the product's own
    `pyproject.toml` and `uv.lock` as they were.

HOW IT RUNS THE COMMAND
    With no shell, in a scratch copy of the starter under `tmp_path` outside the repository.
    `PATH` is built, not inherited: the folder `uv` is found in, followed by `os.defpath`. The
    run is handed a fresh `HOME`, so Behave reads no `~/.behaverc`, and the toolchain settings
    `pytest_guardrails` pins (where `uv` keeps its cache and its Pythons, and where Playwright
    keeps its browsers), because under an empty home `uv` would fetch every package again and
    Playwright would find no browser.

WHY THE REPOSITORY CHECK CAN GO RED
    `test_the_proof_leaves_the_starter_and_the_repository_as_found` compares
    `git status --porcelain` before and after the runs. Under `-n 32`, another test that writes
    into the working tree between the two reads makes it red. That is the other test's defect, and
    this check is the one that shows it.
"""

from __future__ import annotations

import ast
import os
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = REPO_ROOT / "core" / "templates"
STARTER = TEMPLATES / "behave-starter"

COMMAND = ["uv", "run", "--locked", "behave"]
TOOLCHAIN_SETTINGS = ("UV_CACHE_DIR", "UV_PYTHON_INSTALL_DIR", "PLAYWRIGHT_BROWSERS_PATH")
DIRECT_DEPENDENCIES = {"behave", "httpx", "playwright"}
SUMMARY_LINE = re.compile(r"^(\d+) scenarios? passed, (\d+) failed, (\d+) skipped", re.MULTILINE)
FOLDER_FILES = {
    ".gitignore",
    "README.md",
    "pyproject.toml",
    "uv.lock",
    "features/environment.py",
    "features/command.feature",
    "features/server.feature",
    "features/browser.feature",
    "features/command_way_in.py",
    "features/server_way_in.py",
    "features/browser_way_in.py",
    "features/steps/command_steps.py",
    "features/steps/page_steps.py",
    "features/steps/server_steps.py",
    "features/steps/browser_steps.py",
}
PLANTED_FEATURE = (
    "Feature: A planted failure\n"
    "\n"
    "  Scenario: A planted scenario whose step fails\n"
    "    Given a step that fails\n"
)
PLANTED_STEPS = (
    "from behave import given\n"
    "\n"
    "\n"
    '@given("a step that fails")\n'
    "def a_step_that_fails(context):\n"
    '    raise AssertionError("planted failure")\n'
)
PRODUCT_PYPROJECT = (
    "[project]\n"
    'name = "scratch-product"\n'
    'version = "0.0.0"\n'
    'requires-python = ">=3.11"\n'
)


def _files_under(folder: Path) -> dict[str, bytes]:
    """Every file under a folder, ignored ones included, as {relative path: bytes}."""
    return {
        path.relative_to(folder).as_posix(): path.read_bytes()
        for path in sorted(folder.rglob("*"))
        if path.is_file()
    }


def _repository_status() -> str:
    return subprocess.run(
        ["git", "-C", str(REPO_ROOT), "status", "--porcelain"],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
    ).stdout


def _built_path() -> str:
    uv = shutil.which("uv")
    assert uv is not None, "uv is not on the PATH the suite runs with"
    return os.pathsep.join([str(Path(uv).parent), os.defpath])


def _command_environment(home: Path, **extra: str) -> dict[str, str]:
    """What a run of the command sees: the built PATH, a fresh HOME, the toolchain settings."""
    toolchain = {name: os.environ[name] for name in TOOLCHAIN_SETTINGS if name in os.environ}
    return {"PATH": _built_path(), "HOME": str(home), **toolchain, **extra}


def _run(command: list[str], working_directory: Path, home: Path, **extra: str):
    """Run a command with no shell, stderr merged into stdout, on the built environment."""
    return subprocess.run(
        command,
        cwd=working_directory,
        env=_command_environment(home, **extra),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )


def _summary(output: str) -> tuple[int, int, int]:
    """(passed, failed, skipped) scenarios, from Behave's summary line."""
    found = SUMMARY_LINE.search(output)
    assert found, f"no scenario summary in the output:\n{output}"
    return int(found.group(1)), int(found.group(2)), int(found.group(3))


def _plant_failure(folder: Path) -> None:
    """Add one scenario whose step fails to the folder, leaving the starter's own files as they
    are."""
    (folder / "features" / "planted.feature").write_text(PLANTED_FEATURE, encoding="utf-8")
    (folder / "features" / "steps" / "planted_steps.py").write_text(PLANTED_STEPS, encoding="utf-8")


def _make_product(root: Path, home: Path) -> Path:
    """A scratch product whose root holds a `pyproject.toml` and a `uv.lock` that pin no Behave,
    with the starter copied in as `.behave`."""
    root.mkdir()
    (root / "pyproject.toml").write_text(PRODUCT_PYPROJECT, encoding="utf-8")
    locked = _run(["uv", "lock"], root, home)
    assert locked.returncode == 0, locked.stdout
    shutil.copytree(STARTER, root / ".behave")
    return root


def _product_files(root: Path) -> dict[str, bytes]:
    return {name: (root / name).read_bytes() for name in ("pyproject.toml", "uv.lock")}


def _imported_modules(path: Path) -> set[str]:
    """The top-level module names a Python file imports."""
    names: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module.split(".")[0])
    return names


@pytest.fixture
def scratch(tmp_path: Path) -> Path:
    """A copy of the starter's folder made into the empty `tmp_path`, outside the repository."""
    shutil.copytree(STARTER, tmp_path, dirs_exist_ok=True)
    return tmp_path


@pytest.fixture
def home(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """An empty home for the command, so Behave reads no `~/.behaverc`."""
    return tmp_path_factory.mktemp("home")


# ── layer 5: the command, run for real ───────────────────────────────────────────────────────


def test_green_run_in_an_empty_directory_exits_zero_with_three_scenarios_passed(scratch, home):
    result = _run(COMMAND, scratch, home)

    assert result.returncode == 0, result.stdout
    assert _summary(result.stdout) == (3, 0, 0), result.stdout


def test_a_planted_failing_scenario_exits_non_zero_and_is_reported_failed(scratch, home):
    _plant_failure(scratch)

    result = _run(COMMAND, scratch, home)

    assert result.returncode != 0, result.stdout
    assert _summary(result.stdout) == (3, 1, 0), result.stdout
    assert re.search(
        r"Failing scenarios:\n\s+features/planted\.feature:\d+\s+"
        r"A planted scenario whose step fails",
        result.stdout,
    ), result.stdout


def test_green_run_inside_a_product_with_its_own_pyproject_and_lock_leaves_both_files_byte_identical(
    tmp_path, home
):
    product = _make_product(tmp_path / "product", home)
    before = _product_files(product)

    result = _run(COMMAND, product / ".behave", home)

    assert result.returncode == 0, result.stdout
    assert _summary(result.stdout) == (3, 0, 0), result.stdout
    assert _product_files(product) == before


def test_a_planted_failing_scenario_inside_a_product_is_reported_failed_and_leaves_both_files_identical(
    tmp_path, home
):
    product = _make_product(tmp_path / "product", home)
    _plant_failure(product / ".behave")
    before = _product_files(product)

    result = _run(COMMAND, product / ".behave", home)

    assert result.returncode != 0, result.stdout
    assert _summary(result.stdout) == (3, 1, 0), result.stdout
    assert _product_files(product) == before


def test_a_run_leaves_git_status_unchanged_in_a_repository_with_no_ignore_rules(tmp_path, home):
    repository = tmp_path / "repository"
    shutil.copytree(STARTER, repository / ".behave")
    git = ["git", "-C", str(repository), "-c", "user.name=t", "-c", "user.email=t@example.com"]
    environment = {**os.environ, "HOME": str(home)}
    for arguments in (["init", "-q"], ["add", ".behave"], ["commit", "-q", "-m", "starter"]):
        subprocess.run([*git, *arguments], check=True, capture_output=True, env=environment)
    status_before = subprocess.run(
        [*git, "status", "--porcelain"], check=True, capture_output=True, text=True, env=environment
    ).stdout

    result = _run(COMMAND, repository / ".behave", home)

    status_after = subprocess.run(
        [*git, "status", "--porcelain"], check=True, capture_output=True, text=True, env=environment
    ).stdout
    assert result.returncode == 0, result.stdout
    assert status_after == status_before


def test_the_browser_scenario_fails_naming_the_install_when_the_browsers_path_is_empty(
    scratch, home, tmp_path_factory
):
    empty_browsers = tmp_path_factory.mktemp("browsers")

    result = _run(COMMAND, scratch, home, PLAYWRIGHT_BROWSERS_PATH=str(empty_browsers))

    assert result.returncode != 0, result.stdout
    assert "uv run --locked playwright install chromium" in result.stdout
    assert _summary(result.stdout) == (2, 1, 0), result.stdout


def test_the_browser_scenario_fails_naming_the_libraries_install_when_the_driver_cannot_start(
    scratch, home, tmp_path_factory
):
    # A Linux machine without the libraries Playwright's driver loads: the driver exits at once,
    # as `node` does there when `libatomic.so.1` is missing.
    stub_folder = tmp_path_factory.mktemp("node")
    node = stub_folder / "node"
    node.write_text(
        "#!/bin/sh\n"
        "echo \"$0: error while loading shared libraries: libatomic.so.1\" >&2\n"
        "exit 127\n"
    )
    node.chmod(0o755)

    result = _run(COMMAND, scratch, home, PLAYWRIGHT_NODEJS_PATH=str(node))

    assert result.returncode != 0, result.stdout
    assert "uv run --locked playwright install-deps chromium" in result.stdout
    assert _summary(result.stdout) == (2, 1, 0), result.stdout


def test_the_proof_leaves_the_starter_and_the_repository_as_found(scratch, home, tmp_path_factory):
    starter_before = _files_under(STARTER)
    status_before = _repository_status()

    _run(COMMAND, scratch, home)
    red_scratch = tmp_path_factory.mktemp("red")
    shutil.copytree(STARTER, red_scratch, dirs_exist_ok=True)
    _plant_failure(red_scratch)
    _run(COMMAND, red_scratch, home)

    assert _files_under(STARTER) == starter_before
    assert _repository_status() == status_before


# ── layer 6: the folder's shape ──────────────────────────────────────────────────────────────


def test_the_proof_scratch_copy_lies_outside_the_repository(scratch, home, tmp_path_factory):
    assert not scratch.resolve().is_relative_to(REPO_ROOT)
    assert not home.resolve().is_relative_to(REPO_ROOT)
    # Every scratch folder the proof makes, the red copy from `tmp_path_factory` included, sits
    # under this base, so the base lying outside covers each command run.
    assert not tmp_path_factory.getbasetemp().resolve().is_relative_to(REPO_ROOT)


def test_the_scratch_copy_holds_the_starter_whole(scratch):
    assert _files_under(scratch) == _files_under(STARTER)


def test_pyproject_pins_exactly_three_direct_dependencies_each_with_equals():
    pyproject = tomllib.loads((STARTER / "pyproject.toml").read_text(encoding="utf-8"))
    dependencies = pyproject["project"]["dependencies"]

    assert "build-system" not in pyproject
    assert all(re.fullmatch(r"[A-Za-z0-9_.-]+==[0-9][^=<>!~ ]*", item) for item in dependencies)
    assert {item.split("==")[0] for item in dependencies} == DIRECT_DEPENDENCIES
    assert len(dependencies) == len(DIRECT_DEPENDENCIES)


def test_the_command_way_in_imports_standard_library_modules_only():
    imported = _imported_modules(STARTER / "features" / "command_way_in.py")

    assert imported
    assert imported <= set(sys.stdlib_module_names), imported - set(sys.stdlib_module_names)


def test_the_server_way_in_imports_httpx_and_the_browser_way_in_imports_playwright():
    assert "httpx" in _imported_modules(STARTER / "features" / "server_way_in.py")
    assert "playwright" in _imported_modules(STARTER / "features" / "browser_way_in.py")


def test_the_starter_ships_three_scenarios_one_per_way_in_and_names_no_host_but_loopback():
    features = sorted((STARTER / "features").glob("*.feature"))
    scenario_counts = [
        len(re.findall(r"^\s*Scenario:", path.read_text(encoding="utf-8"), re.MULTILINE))
        for path in features
    ]
    sources = [path for path in sorted(STARTER.rglob("*")) if path.suffix in {".py", ".feature"}]

    assert scenario_counts == [1, 1, 1]
    for path in sources:
        text = path.read_text(encoding="utf-8")
        # A URL names its host in the text, or builds it from a name the file sets.
        assert not re.search(r"https?://(?!127\.0\.0\.1\b|\{)", text), path
        assert "localhost" not in text, path
        for assigned in re.findall(r'^LOOPBACK = "([^"]*)"', text, re.MULTILINE):
            assert assigned == "127.0.0.1", path


def test_the_folder_holds_no_wrapper_script_and_no_executable_file():
    files = _files_under(STARTER)

    assert set(files) == FOLDER_FILES
    for name in files:
        assert not (STARTER / name).stat().st_mode & 0o111, f"{name} is executable"
        assert not name.endswith(".sh"), f"{name} is a script"


def test_uv_resolves_on_the_built_path(home):
    environment = _command_environment(home)

    assert shutil.which("uv", path=environment["PATH"]) is not None
    assert environment["HOME"] == str(home)
    assert not any(home.iterdir())
    for name in TOOLCHAIN_SETTINGS:
        assert environment[name] == os.environ[name], name


def test_there_is_one_starter_under_the_templates():
    with_feature_line = [
        path
        for path in sorted(TEMPLATES.rglob("*"))
        if path.is_file()
        and re.search(
            r"^Feature:", path.read_text(encoding="utf-8", errors="replace"), re.MULTILINE
        )
    ]
    environment_hooks = [
        path for path in TEMPLATES.rglob("environment.py") if path.parent.name == "features"
    ]

    assert with_feature_line
    assert all(path.is_relative_to(STARTER) for path in with_feature_line)
    assert len(environment_hooks) == 1
    assert environment_hooks[0].is_relative_to(STARTER)


# ── layer 6: the README ──────────────────────────────────────────────────────────────────────

README = STARTER / "README.md"
WAYS_IN = (
    "features/command_way_in.py",
    "features/server_way_in.py",
    "features/browser_way_in.py",
)
FENCED_BLOCK = re.compile(r"^```[^\n]*\n(.*?)^```[ \t]*$", re.MULTILINE | re.DOTALL)


def _readme() -> str:
    return README.read_text(encoding="utf-8")


def test_readme_has_one_fenced_block_reading_exactly_uv_run_locked_behave():
    blocks = FENCED_BLOCK.findall(_readme())

    assert blocks == ["uv run --locked behave\n"]


def test_readme_says_to_run_the_command_inside_the_folder_and_names_the_folder():
    text = _readme()

    assert "`.behave`" in text
    assert re.search(r"\binside (?:this|the `\.behave`) folder", text)


def test_readme_names_the_browser_install_command():
    outside_blocks = FENCED_BLOCK.sub("", _readme())

    assert "`uv run --locked playwright install chromium`" in outside_blocks
    assert "`uv run --locked playwright install-deps chromium`" in outside_blocks


def test_readme_names_where_scenarios_steps_and_setup_go():
    text = _readme()

    for place in ("`features/`", "`features/steps/`", "`features/environment.py`"):
        assert place in text, place


def test_readme_names_the_three_ways_in_and_that_a_product_uses_one():
    text = _readme()

    assert re.search(r"scenarios use one of the three", text)
    for name in ("command", "server", "browser"):
        assert re.search(rf"\*\*A {name}\*\*", text), name


def test_readme_names_each_way_in_by_a_path_that_exists_and_leaves_no_placeholder():
    text = _readme()

    for path in WAYS_IN:
        assert f"`{path}`" in text, path
        assert (STARTER / path).is_file(), path
    assert not re.search(r"\{[^{}\n]*way-in path\}", text)


def test_readme_says_a_run_leaves_the_products_own_pyproject_and_lock_as_they_were():
    opening = _readme().split("## Run the scenarios")[0]

    assert "`pyproject.toml`" in opening
    assert "`uv.lock`" in opening
    assert "as they were" in opening


def test_readme_names_no_behave_pin_and_no_behave_format_plain():
    text = _readme()

    assert "behave==1.3.3" not in text
    assert "behave --format plain" not in text


# ── layer 6: the card template ───────────────────────────────────────────────────────────────


def test_the_card_template_holds_one_behave_line_and_no_line_naming_the_command():
    lines = (TEMPLATES / "project_template.md").read_text(encoding="utf-8").splitlines()

    assert sum(line.startswith("**Behave:**") for line in lines) == 1
    assert not [line for line in lines if "uv run --locked behave" in line]


# ── layer 6: no live file states the old layout ──────────────────────────────────────────────

OLD_LAYOUT_PHRASES = (
    "behave --format plain",
    "copied, not committed",
    "the check commits nothing",
    "nothing named `features` sits at the root",
    "no `features` at its root",
    "anything named `features` at the root",
    "Its four files",
    "names three dependencies, each a test tool",
)
# This one is matched whatever its case; the others are matched as written.
CASE_INSENSITIVE_PHRASES = {"the check commits nothing"}


def _live_files_under_core() -> list[Path]:
    """Every file under `core/` git tracks or would track, but a changelog and this test file."""
    listed = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "ls-files", "-z", "--cached", "--others"]
        + ["--exclude-standard", "--", "core"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return [
        REPO_ROOT / name
        for name in listed.split("\0")
        if name
        and (REPO_ROOT / name).is_file()
        and Path(name).name != "CHANGELOG.md"
        and (REPO_ROOT / name) != Path(__file__).resolve()
    ]


def _states(text: str, phrase: str) -> bool:
    if phrase in CASE_INSENSITIVE_PHRASES:
        return phrase in text.lower()
    return phrase in text


def test_no_live_file_under_core_states_the_old_layout():
    files = _live_files_under_core()
    found = [
        f"{path.relative_to(REPO_ROOT)}: {phrase}"
        for path in files
        for text in [path.read_text(encoding="utf-8", errors="replace")]
        for phrase in OLD_LAYOUT_PHRASES
        if _states(text, phrase)
    ]

    assert files
    assert found == []
