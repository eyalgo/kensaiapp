"""Tests for the start-of-run list in `pin_run.sh` — `pin_start_checks` and its Behave check.

Layer 1 (unit): a bash wrapper sources the real `pin_run.sh` under `set -euo pipefail` and calls one
function. The installer the check is handed is a recording shell function the wrapper defines, so
a case sees what the check asked the install to do and nothing is installed. The core, the
instance root, the card, the product and the home it is given are folders under `tmp_path`, and the
core holds a copy of `core/templates/behave-starter/`. The environment each subprocess gets is built
here from `PATH`, plus a `HOME` and a `KENSAIAPP_PINS_HOME` under `tmp_path` and a fixed git identity,
so nothing reads or writes the real home and no commit takes its author from the machine. Project
names are scratch words.

Layer 5 (end to end): the real installer, the real tool and the real commit builder run in scratch
git repositories whose hooks are the real `core/githooks`; the core of such a case also holds the
tool, the builder and the runner they go through (`with_real_tooling`).

Every case that runs the list goes through `run_check`, which asserts every `project.md` under the
scratch root holds the bytes it held before the call (CP-1221), so no case carries that assertion
by hand.

The four case tests named in the change's request keep their names: the seal selects them by name at
the commit the change was cut from.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest

import pin
from test_pin_run import (
    _LOCKED_PYTHON_SH,
    _REPO_ROOT,
    _ROOT_LOCK_FILES,
    _hosts_python_version,
    _init_pin_run_host,
)

_TOOLS_DIR = Path(__file__).resolve().parent
_CORE_DIR = _TOOLS_DIR.parent
_PIN_RUN_SH = _TOOLS_DIR / "pin_run.sh"
_STARTER_DIR = _CORE_DIR / "templates" / "behave-starter"
_LAUNCHERS_DIR = _CORE_DIR / "launchers"
_GITHOOKS_DIR = _CORE_DIR / "githooks"

# The identity every commit a case makes is given. Without it git builds one from the machine's host
# name, and on a Linux machine whose host name has no domain it refuses the commit instead.
_GIT_IDENTITY = {
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@example.com",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@example.com",
}

# The recording installer: one line per call holding the arguments it was given, and the status
# `INSTALLER_STATUS` names (0 when it names none).
_WRAPPER = """#!/usr/bin/env bash
set -euo pipefail
source "${PIN_RUN_SH}"
record_installer() {
  echo "$*" >> "${INSTALLER_LOG}"
  return "${INSTALLER_STATUS:-0}"
}
"$@"
"""
_RECORDING_INSTALLER = "record_installer"
_REAL_INSTALLER = "_pin_install_behave_starter"
_FOLDER = ".behave"

# The tool, the builder and the modules they import, which a core carries when the real installer
# runs from it.
_TOOL_MODULES = (
    "check_vendor_neutrality",
    "commit_builder",
    "development_path",
    "empty_home",
    "gate_suite",
    "install_behave_starter",
    "pin",
    "record_declarations",
    "skill_path",
)

# A stop message is one message of five lines (change_text.md, "The lines a launch prints").
_STOP_MESSAGE_LINES = 5
_UNDECIDED_TEMPLATE_LINE = "behave | none — <reason>"
_DEFINITION_LAUNCHERS = ("product-card", "product-docs", "prd-and-finish-line")
_INHERITING_LAUNCHERS = ("companion-self-answer", "product-skeleton")
_INSTANCE_ROOT_FLAG = "--instance-root"


@dataclass(frozen=True)
class Scene:
    """The scratch folders one case runs in."""

    root: Path
    core: Path
    instance: Path
    home: Path
    wrapper: Path

    def product(self, name: str = "prod") -> Path:
        return self.instance / name


def make_scene(root: Path) -> Scene:
    core = root / "core"
    (core / "templates").mkdir(parents=True)
    shutil.copytree(_STARTER_DIR, core / "templates" / "behave-starter")
    instance = root / "instance"
    instance.mkdir()
    home = root / "home"
    home.mkdir()
    wrapper = root / "wrapper.sh"
    wrapper.write_text(_WRAPPER)
    return Scene(root=root, core=core, instance=instance, home=home, wrapper=wrapper)


def behave_line(value: str) -> str:
    return f"**Behave:** {value}"


def write_card(
    instance: Path,
    project: str,
    behave_lines: list[str],
    product_path: str | None = "prod",
) -> Path:
    card = instance / "system" / "projects" / project / "project.md"
    card.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"# Project Context — {project}", ""]
    if product_path is not None:
        lines.append(f"**Product path:** {product_path}   <!-- where the product lives -->")
    lines.extend(behave_lines)
    card.write_text("\n".join(lines) + "\n")
    return card


def make_product(folder: Path, files: dict[str, str] | None = None) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    for relative, text in (files or {}).items():
        target = folder / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
    return folder


def snapshot(root: Path) -> dict[str, tuple]:
    """Every path under `root` with what it holds: bytes for a file, the target for a link."""
    found: dict[str, tuple] = {}
    if not root.is_dir():
        return found
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            found[relative] = ("link", os.readlink(path))
        elif path.is_dir():
            found[relative] = ("dir",)
        else:
            found[relative] = ("file", path.read_bytes())
    return found


def card_bytes(root: Path) -> dict[Path, bytes]:
    return {card: card.read_bytes() for card in sorted(root.rglob("project.md"))}


def installer_log(scene: Scene) -> Path:
    return scene.root / "installer.log"


def installer_calls(scene: Scene) -> list[str]:
    log = installer_log(scene)
    return log.read_text().splitlines() if log.exists() else []


def _environment(
    scene: Scene, env_home: Path | None = None, installer_status: int = 0
) -> dict[str, str]:
    return {
        "PATH": os.environ["PATH"],
        "HOME": str(env_home or scene.home),
        "KENSAIAPP_PINS_HOME": str(scene.root / "pins"),
        "PIN_RUN_SH": str(_PIN_RUN_SH),
        "INSTALLER_LOG": str(installer_log(scene)),
        "INSTALLER_STATUS": str(installer_status),
        **_GIT_IDENTITY,
    }


def with_real_tooling(scene: Scene) -> Scene:
    """Give the scene's core the tool, the builder and the runner the real installer goes
    through, and its instance root the files that runner reads."""
    tools = scene.core / "tools"
    tools.mkdir(parents=True, exist_ok=True)
    for name in _TOOL_MODULES:
        shutil.copy2(_TOOLS_DIR / f"{name}.py", tools / f"{name}.py")
    shutil.copy2(_LOCKED_PYTHON_SH, tools / "locked_python.sh")
    for name in _ROOT_LOCK_FILES:
        shutil.copy2(_REPO_ROOT / name, scene.root / name)
    (scene.root / ".python-version").write_text(_hosts_python_version())
    return scene


def git(folder: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(folder), "-c", "user.name=t", "-c", "user.email=t@example.com",
         "-c", "commit.gpgsign=false", *args],
        capture_output=True, text=True, check=True,
    ).stdout


def make_repository(folder: Path, *, hooks: Path = _GITHOOKS_DIR) -> Path:
    """A git repository on `main` with one commit, whose hooks are `hooks`."""
    make_product(folder, {"README.md": "mine\n"})
    git(folder, "init", "-q", "-b", "main")
    git(folder, "add", "README.md")
    git(folder, "commit", "-q", "-m", "seed")
    git(folder, "config", "core.hooksPath", str(hooks))
    return folder


def refusing_hooks(root: Path) -> Path:
    hooks = root / "refusing-hooks"
    hooks.mkdir()
    hook = hooks / "commit-msg"
    hook.write_text("#!/bin/sh\necho 'the scratch hook refuses every message' >&2\nexit 1\n")
    hook.chmod(0o755)
    return hooks


def staged_names(folder: Path) -> set[str]:
    return set(git(folder, "diff", "--cached", "--name-only").split())


def run_wrapper(
    scene: Scene,
    *command: str,
    cwd: Path | None = None,
    env_home: Path | None = None,
    installer_status: int = 0,
):
    return subprocess.run(
        ["bash", str(scene.wrapper), *command],
        cwd=str(cwd or scene.instance),
        capture_output=True,
        text=True,
        env=_environment(scene, env_home, installer_status),
    )


def run_check(
    scene: Scene,
    launcher: str,
    *launch_args: str,
    definition_project: str = "",
    cwd: Path | None = None,
    process_cwd: Path | None = None,
    env_home: Path | None = None,
    installer: str = _RECORDING_INSTALLER,
    installer_status: int = 0,
):
    """Call `pin_start_checks` as a launch would, and assert no card changed (CP-1221).

    `installer` is the function the list is handed to run the install: the recording one by
    default, `_REAL_INSTALLER` for a case that installs for real.

    `cwd` is the working directory handed to the list as its argument, and the process runs there
    too unless `process_cwd` moves it; `env_home` likewise moves the process's own `HOME` away
    from the home the list is handed. Both exist so a case can tell the list's arguments apart
    from the environment it runs in."""
    working_dir = cwd or scene.instance
    cards_before = card_bytes(scene.root)
    result = run_wrapper(
        scene,
        "pin_start_checks",
        str(scene.core),
        launcher,
        str(working_dir),
        str(scene.home),
        definition_project,
        installer,
        *launch_args,
        cwd=process_cwd or working_dir,
        env_home=env_home,
        installer_status=installer_status,
    )
    assert card_bytes(scene.root) == cards_before
    return result


def words_outside_paths(stderr: str) -> str:
    """The stderr text with every path-shaped token removed, so a fact a message must state in
    its own words is not found inside the card's or the product's path instead."""
    return " ".join(token for token in stderr.split() if "/" not in token)


def names(text: str, word: str) -> bool:
    return re.search(rf"(?<![\w-]){re.escape(word)}(?![\w-])", text) is not None


def assert_silent_pass(result) -> None:
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
    assert result.stderr == ""


def assert_stopped_naming_the_architecture_run(result, project: str) -> None:
    assert result.returncode == 1
    assert result.stdout == ""
    # The card's path holds the project too, so the name is looked for outside every path.
    assert names(words_outside_paths(result.stderr), project)
    assert "product-architecture" in result.stderr
    assert len(result.stderr.splitlines()) == _STOP_MESSAGE_LINES


def starter_files() -> dict[str, bytes]:
    return {
        path.relative_to(_STARTER_DIR).as_posix(): path.read_bytes()
        for path in sorted(_STARTER_DIR.rglob("*"))
        if path.is_file()
    }


def expected_call(scene: Scene, launcher: str, project: str, product: Path) -> str:
    """The one call the check makes to the installer it is handed."""
    return (
        f"{scene.core} --starter {scene.core}/templates/behave-starter "
        f"--into {product}/{_FOLDER} --project {project} --launch {launcher}"
    )


def worktree_files(product: Path) -> dict[str, tuple]:
    """What the product holds, `.git` apart."""
    return {k: v for k, v in snapshot(product).items() if not k.startswith(".git")}


class TestTheFourCases:
    def test_case_no_behave_line_halts_naming_the_architecture_run(self, tmp_path):
        scene = make_scene(tmp_path)
        write_card(scene.instance, "demo", [])
        make_product(scene.product(), {"README.md": "mine\n"})
        product_before = snapshot(scene.product())

        result = run_check(scene, "walk", "demo")

        assert_stopped_naming_the_architecture_run(result, "demo")
        assert "no **Behave:** line" in result.stderr
        assert snapshot(scene.product()) == product_before

    def test_case_template_undecided_line_halts_naming_the_architecture_run(self, tmp_path):
        scene = make_scene(tmp_path)
        write_card(
            scene.instance,
            "demo",
            [behave_line(f"{_UNDECIDED_TEMPLATE_LINE}  <!-- whether the product needs Behave -->")],
        )
        make_product(scene.product(), {"README.md": "mine\n"})
        product_before = snapshot(scene.product())

        result = run_check(scene, "walk", "demo")

        assert_stopped_naming_the_architecture_run(result, "demo")
        assert f'"{_UNDECIDED_TEMPLATE_LINE}"' in result.stderr
        assert "no **Behave:** line" not in result.stderr
        assert snapshot(scene.product()) == product_before

    def test_case_behave_installs_the_starter_and_keeps_an_existing_file(self, tmp_path):
        scene = make_scene(tmp_path)
        write_card(scene.instance, "demo", [behave_line("behave")])
        make_product(
            scene.product(),
            {"README.md": "the product's own readme\n", "src/code.py": "x\n"},
        )
        product_before = snapshot(scene.product())

        result = run_check(scene, "walk", "demo")

        assert_silent_pass(result)
        assert installer_calls(scene) == [expected_call(scene, "walk", "demo", scene.product())]
        assert snapshot(scene.product()) == product_before

    def test_case_none_with_a_reason_passes_and_writes_nothing(self, tmp_path):
        scene = make_scene(tmp_path)
        write_card(scene.instance, "demo", [behave_line("none — a test card")])
        make_product(scene.product(), {"README.md": "mine\n", "src/code.py": "x\n"})
        product_before = snapshot(scene.product())

        result = run_check(scene, "walk", "demo")

        assert_silent_pass(result)
        assert snapshot(scene.product()) == product_before


class TestWhatCountsAsAMadeCall:
    @pytest.mark.parametrize(
        "behave_lines",
        [
            pytest.param([behave_line("none — <reason>")], id="literal-reason-placeholder"),
            pytest.param([behave_line("none")], id="bare-none"),
            pytest.param(["**Behave:**"], id="empty-value"),
            pytest.param([behave_line("yes")], id="yes"),
            pytest.param([behave_line("none —    ")], id="dash-then-only-blanks"),
            pytest.param([behave_line("none - x")], id="ascii-hyphen"),
            pytest.param(
                [behave_line("behave"), behave_line("none — x")], id="two-lines"
            ),
        ],
    )
    def test_undecided_values_halt(self, tmp_path, behave_lines):
        scene = make_scene(tmp_path)
        write_card(scene.instance, "demo", behave_lines)
        make_product(scene.product(), {"README.md": "mine\n"})
        product_before = snapshot(scene.product())

        result = run_check(scene, "walk", "demo")

        assert_stopped_naming_the_architecture_run(result, "demo")
        assert snapshot(scene.product()) == product_before

    def test_two_behave_lines_say_how_many(self, tmp_path):
        scene = make_scene(tmp_path)
        write_card(scene.instance, "demo", [behave_line("behave"), behave_line("none — x")])
        make_product(scene.product())

        result = run_check(scene, "walk", "demo")

        assert result.returncode == 1
        # Outside the paths: a scratch folder's own name can hold a standalone 2.
        assert names(words_outside_paths(result.stderr), "2")

    def test_value_stops_at_the_inline_comment(self, tmp_path):
        scene = make_scene(tmp_path)
        write_card(scene.instance, "demo", [behave_line("behave   <!-- note -->")])
        make_product(scene.product())

        result = run_check(scene, "walk", "demo")

        assert result.returncode == 0, result.stderr
        assert installer_calls(scene) == [expected_call(scene, "walk", "demo", scene.product())]


class TestTheInstall:
    def test_a_non_zero_installer_status_is_the_checks_status(self, tmp_path):
        scene = make_scene(tmp_path)
        write_card(scene.instance, "demo", [behave_line("behave")])
        make_product(scene.product())

        result = run_check(scene, "walk", "demo", installer_status=3)

        assert result.returncode == 3
        assert len(installer_calls(scene)) == 1

    def test_empty_product_receives_the_starter_through_the_installer(self, tmp_path):
        scene = make_scene(tmp_path)
        write_card(scene.instance, "demo", [behave_line("behave")])
        make_product(scene.product())

        result = run_check(scene, "walk", "demo")

        assert_silent_pass(result)
        assert installer_calls(scene) == [expected_call(scene, "walk", "demo", scene.product())]

    @pytest.mark.parametrize("kind", ["home-prefix", "relative", "absolute"])
    def test_product_path_with_home_prefix_installs_under_the_handed_home(self, tmp_path, kind):
        scene = make_scene(tmp_path)
        written, folder = {
            "home-prefix": ("~/handed", scene.home / "handed"),
            "relative": ("handed", scene.instance / "handed"),
            "absolute": (str(tmp_path / "elsewhere"), tmp_path / "elsewhere"),
        }[kind]
        write_card(scene.instance, "demo", [behave_line("behave")], product_path=written)
        make_product(folder)

        result = run_check(scene, "walk", "demo")

        assert result.returncode == 0, result.stderr
        assert installer_calls(scene) == [expected_call(scene, "walk", "demo", folder)]

    # An existing `.behave` is handed to the installer too, which stops the launch on a path in it
    # the product's work tree holds uncommitted or ignores, and otherwise leaves it as it is.
    @pytest.mark.parametrize("setup", ["a-folder", "a-file", "a-link", "a-dangling-link"])
    def test_existing_setup_is_handed_to_the_installer(self, tmp_path, setup):
        scene = make_scene(tmp_path)
        write_card(scene.instance, "demo", [behave_line("behave")])
        make_product(scene.product(), {"README.md": "mine\n"})
        present = scene.product() / _FOLDER
        if setup == "a-folder":
            present.mkdir()
        elif setup == "a-file":
            present.write_text("not a folder\n")
        elif setup == "a-link":
            (scene.product() / "elsewhere").mkdir()
            os.symlink("elsewhere", present)
        else:
            os.symlink("nowhere", present)
        product_before = snapshot(scene.product())

        result = run_check(scene, "walk", "demo")

        assert_silent_pass(result)
        assert installer_calls(scene) == [expected_call(scene, "walk", "demo", scene.product())]
        assert snapshot(scene.product()) == product_before

    def test_existing_setup_under_dry_run_is_handed_to_the_installer_and_takes_its_status(
        self, tmp_path
    ):
        scene = make_scene(tmp_path)
        write_card(scene.instance, "demo", [behave_line("behave")])
        make_product(scene.product(), {f"{_FOLDER}/README.md": "mine\n"})

        result = run_check(scene, "walk", "demo", "--dry-run", installer_status=1)

        assert result.returncode == 1
        assert installer_calls(scene) == [expected_call(scene, "walk", "demo", scene.product())]

    def test_a_root_features_does_not_decide(self, tmp_path):
        scene = make_scene(tmp_path)
        write_card(scene.instance, "demo", [behave_line("behave")])
        make_product(scene.product(), {"features/mine.feature": "Feature: mine\n"})

        result = run_check(scene, "walk", "demo")

        assert_silent_pass(result)
        assert installer_calls(scene) == [expected_call(scene, "walk", "demo", scene.product())]

    @pytest.mark.parametrize(
        "product_path", ["ghost", None], ids=["folder-missing", "card-names-no-folder"]
    )
    # CP-1220: "Every other case is as stated above", so a dry run says the same one line.
    @pytest.mark.parametrize(
        "launch_args", [("demo",), ("demo", "--dry-run")], ids=["launch", "dry-run"]
    )
    def test_missing_product_folder_installs_nothing(self, tmp_path, product_path, launch_args):
        scene = make_scene(tmp_path)
        write_card(scene.instance, "demo", [behave_line("behave")], product_path=product_path)
        instance_before = snapshot(scene.instance)

        result = run_check(scene, "walk", *launch_args)

        assert result.returncode == 0, result.stderr
        assert len(result.stderr.splitlines()) == 1
        assert installer_calls(scene) == []
        assert snapshot(scene.instance) == instance_before
        assert not (scene.instance / "ghost").exists()

    def test_dry_run_calls_no_installer_and_says_it_would_install_and_commit_on_main(
        self, tmp_path
    ):
        scene = make_scene(tmp_path)
        write_card(scene.instance, "demo", [behave_line("behave")])
        write_card(scene.instance, "undecided", [], product_path="prod")
        make_product(scene.product(), {"README.md": "mine\n"})
        product_before = snapshot(scene.product())

        would = run_check(scene, "walk", "demo", "--dry-run")
        stopped = run_check(scene, "walk", "undecided", "--dry-run")

        assert would.returncode == 0, would.stderr
        assert len(would.stderr.splitlines()) == 1
        assert names(words_outside_paths(would.stderr), "demo")
        assert _FOLDER in would.stderr
        assert "commit it on main" in would.stderr
        assert installer_calls(scene) == []
        assert snapshot(scene.product()) == product_before
        assert_stopped_naming_the_architecture_run(stopped, "undecided")

    def test_missing_starter_in_the_core_halts_naming_the_folder(self, tmp_path):
        scene = make_scene(tmp_path)
        shutil.rmtree(scene.core / "templates" / "behave-starter")
        write_card(scene.instance, "demo", [behave_line("behave")])
        make_product(scene.product(), {"README.md": "mine\n"})
        product_before = snapshot(scene.product())

        result = run_check(scene, "walk", "demo")

        assert result.returncode == 1
        assert str(scene.core / "templates" / "behave-starter") in result.stderr
        assert installer_calls(scene) == []
        assert snapshot(scene.product()) == product_before


def real_scene(tmp_path: Path, *, hooks: Path = _GITHOOKS_DIR) -> Scene:
    """A scene whose product is a git repository on `main` and whose core holds the real tool."""
    scene = with_real_tooling(make_scene(tmp_path))
    write_card(scene.instance, "demo", [behave_line("behave")])
    make_repository(scene.product(), hooks=hooks)
    return scene


def run_real(scene: Scene):
    return run_check(scene, "walk", "demo", installer=_REAL_INSTALLER)


class TestTheRealInstall:
    def test_installs_the_folder_byte_identical_and_adds_exactly_one_new_commit_on_main(
        self, tmp_path
    ):
        scene = real_scene(tmp_path)
        product = scene.product()
        before = git(product, "rev-parse", "HEAD").strip()

        result = run_real(scene)

        assert result.returncode == 0, result.stderr
        assert result.stdout == ""
        for relative, content in starter_files().items():
            assert (product / _FOLDER / relative).read_bytes() == content
        assert git(product, "rev-list", "--count", f"{before}..HEAD").strip() == "1"
        assert git(product, "rev-parse", "HEAD~1").strip() == before
        changed = set(git(product, "diff", "--name-only", "HEAD~1", "HEAD").split())
        assert changed == {f"{_FOLDER}/{relative}" for relative in starter_files()}
        message = git(product, "log", "-1", "--format=%B")
        assert "Role: Product" in message
        assert "Surface: behave-check" in message
        assert "Co-Authored-By:" not in message
        assert git(product, "branch", "--show-current").strip() == "main"

    def test_the_install_line_names_project_product_folder_main_and_the_short_id(self, tmp_path):
        scene = real_scene(tmp_path)
        product = scene.product()

        result = run_real(scene)

        (line,) = result.stderr.splitlines()
        assert line.startswith("walk:")
        short_id = git(product, "rev-parse", "--short", "HEAD").strip()
        for fact in ("demo", str(product), _FOLDER, "main", short_id):
            assert fact in line

    def test_a_path_staged_beforehand_stays_staged_and_is_in_no_commit(self, tmp_path):
        scene = real_scene(tmp_path)
        product = scene.product()
        (product / "other.txt").write_text("other\n")
        git(product, "add", "other.txt")

        result = run_real(scene)

        assert result.returncode == 0, result.stderr
        assert staged_names(product) == {"other.txt"}
        assert "other.txt" not in git(product, "diff", "--name-only", "HEAD~1", "HEAD").split()

    # CP-1242: the one line names the launch, the project, the product folder and the reason.
    # The refusing hook's reason is its own words, read from the builder's captured output.
    _CANNOT_LAND_REASON = {
        "not-a-repository": "no git work tree",
        "feature-x": "feature-x checked out",
        "detached-head": "detached HEAD",
    }

    @pytest.mark.parametrize("reason", ["not-a-repository", "feature-x", "detached-head"])
    def test_product_is_left_as_found_where_no_commit_can_land(self, tmp_path, reason):
        if reason == "not-a-repository":
            scene = with_real_tooling(make_scene(tmp_path))
            write_card(scene.instance, "demo", [behave_line("behave")])
            make_product(scene.product(), {"README.md": "mine\n"})
        else:
            scene = real_scene(tmp_path)
            if reason == "feature-x":
                git(scene.product(), "checkout", "-q", "-b", "feature-x")
            else:
                git(scene.product(), "checkout", "-q", "--detach")
        product = scene.product()
        files_before = worktree_files(product)
        in_repository = reason != "not-a-repository"
        tip_before = git(product, "rev-parse", "HEAD").strip() if in_repository else None
        staged_before = staged_names(product) if in_repository else None

        result = run_real(scene)

        assert result.returncode == 0, result.stderr
        (line,) = result.stderr.splitlines()
        assert line.startswith("walk:")
        assert names(words_outside_paths(line), "demo")
        for fact in (str(product), self._CANNOT_LAND_REASON[reason]):
            assert fact in line, fact
        assert not (product / _FOLDER).exists()
        assert worktree_files(product) == files_before
        if in_repository:
            assert git(product, "rev-parse", "HEAD").strip() == tip_before
            assert staged_names(product) == staged_before

    def test_a_refused_commit_is_undone_and_stops_the_launch_quoting_the_refusal(self, tmp_path):
        scene = real_scene(tmp_path, hooks=refusing_hooks(tmp_path))
        product = scene.product()
        files_before = worktree_files(product)
        tip_before = git(product, "rev-parse", "HEAD").strip()

        result = run_real(scene)

        assert result.returncode == 1
        assert result.stdout == ""
        (line,) = result.stderr.splitlines()
        assert line.startswith("walk:")
        assert "the scratch hook refuses every message" in line
        assert not (product / _FOLDER).exists()
        assert worktree_files(product) == files_before
        assert git(product, "rev-parse", "HEAD").strip() == tip_before
        assert staged_names(product) == set()

    def test_second_launch_after_install_passes_silently(self, tmp_path):
        scene = real_scene(tmp_path)
        assert run_real(scene).returncode == 0
        # What a scenario run leaves in the folder, which the starter's own .gitignore ignores.
        (scene.product() / _FOLDER / ".venv").mkdir()
        (scene.product() / _FOLDER / ".venv" / "pyvenv.cfg").write_text("x\n")
        product_after_install = worktree_files(scene.product())

        second = run_real(scene)

        assert_silent_pass(second)
        assert worktree_files(scene.product()) == product_after_install

    @pytest.mark.parametrize("held", ["untracked", "ignored"])
    def test_a_held_path_in_an_existing_folder_stops_the_launch_naming_it(self, tmp_path, held):
        scene = real_scene(tmp_path)
        product = scene.product()
        assert run_real(scene).returncode == 0
        if held == "ignored":
            (product / ".gitignore").write_text("*.log\n")
            git(product, "add", ".gitignore")
            git(product, "commit", "-q", "--no-verify", "-m", "ignore logs")
            name = f"{_FOLDER}/run.log"
        else:
            name = f"{_FOLDER}/features/mine.feature"
        (product / name).write_text("mine\n")
        files_before = worktree_files(product)
        tip_before = git(product, "rev-parse", "HEAD").strip()

        result = run_real(scene)
        dry_run = run_check(scene, "walk", "demo", "--dry-run", installer=_REAL_INSTALLER)

        assert result.returncode == 1
        assert result.stdout == ""
        (line,) = result.stderr.splitlines()
        assert line.startswith("walk:")
        assert f"{name} ({held})" in line
        assert worktree_files(product) == files_before
        assert git(product, "rev-parse", "HEAD").strip() == tip_before
        assert (dry_run.returncode, dry_run.stderr) == (1, result.stderr)


class TestWhichLaunchesAreChecked:
    @pytest.mark.parametrize("launcher", _DEFINITION_LAUNCHERS)
    @pytest.mark.parametrize(
        "behave_lines", [[], [behave_line("behave")]], ids=["undecided", "behave"]
    )
    def test_definition_launchers_are_never_checked(self, tmp_path, launcher, behave_lines):
        scene = make_scene(tmp_path)
        write_card(scene.instance, "demo", behave_lines)
        make_product(scene.product(), {"README.md": "mine\n"})
        before = snapshot(scene.root)

        result = run_check(scene, launcher, "demo")

        assert_silent_pass(result)
        assert snapshot(scene.root) == before

    @pytest.mark.parametrize(
        ("launcher", "launch_args"),
        [
            pytest.param("skill", ["development-specs", "demo"], id="skill"),
            pytest.param("change", [], id="change-without-an-argument"),
            pytest.param("an-unknown-launcher", ["demo"], id="unknown-launcher"),
            pytest.param("change", ["ghost"], id="change-with-no-card"),
            pytest.param("walk", ["demo", "--stop"], id="stop"),
            pytest.param("walk", ["../demo"], id="dotted-project"),
            pytest.param("walk", ["a/b"], id="slashed-project"),
            pytest.param(
                "walk", [_INSTANCE_ROOT_FLAG, "elsewhere", "demo"], id="walk-takes-no-root-flag"
            ),
        ],
    )
    def test_launches_that_are_not_checked_pass_silently(self, tmp_path, launcher, launch_args):
        scene = make_scene(tmp_path)
        undecided = []
        write_card(scene.instance, "demo", undecided)
        write_card(scene.instance, "../demo", undecided, product_path=None)
        write_card(scene.instance, "a/b", undecided, product_path=None)
        write_card(scene.instance / "elsewhere", "demo", undecided)
        make_product(scene.product(), {"README.md": "mine\n"})
        before = snapshot(scene.root)

        result = run_check(scene, launcher, *launch_args)

        assert_silent_pass(result)
        assert snapshot(scene.root) == before

    def test_launches_that_name_a_project_are_checked(self, tmp_path):
        scene = make_scene(tmp_path)
        write_card(scene.instance, "demo", [], product_path=None)

        cold_read = run_check(scene, "cold-read", "some-skill", "--project", "demo")

        assert_stopped_naming_the_architecture_run(cold_read, "demo")

    @pytest.mark.parametrize(
        ("launcher", "launch_args"),
        [
            pytest.param("companion-self-answer", ["demo", "FDR"], id="companion-self-answer"),
            pytest.param("product-skeleton", ["demo"], id="product-skeleton"),
        ],
    )
    @pytest.mark.parametrize("root_form", ["absolute", "relative-to-cwd"])
    def test_instance_root_flag_moves_where_the_card_is_read(
        self, tmp_path, launcher, launch_args, root_form
    ):
        scene = make_scene(tmp_path)
        other = scene.instance / "other"
        write_card(scene.instance, "demo", [behave_line("none — in the cwd")])
        write_card(other, "demo", [], product_path=None)
        given = str(other) if root_form == "absolute" else "other"

        result = run_check(scene, launcher, _INSTANCE_ROOT_FLAG, given, *launch_args)

        assert_stopped_naming_the_architecture_run(result, "demo")

    def test_cold_read_reads_the_project_its_launcher_reads(self, tmp_path):
        # CP-1212: "the card the launcher itself reads". cold-read's own parse takes every
        # `--project <value>` pair in turn, so a repeated flag leaves the last value standing.
        scene = make_scene(tmp_path)
        write_card(scene.instance, "made", [behave_line("none — a test card")], product_path=None)
        write_card(scene.instance, "undecided", [], product_path=None)

        last_undecided = run_check(
            scene, "cold-read", "some-skill", "--project", "made", "--project", "undecided"
        )
        last_made = run_check(
            scene, "cold-read", "some-skill", "--project", "undecided", "--project", "made"
        )

        assert_stopped_naming_the_architecture_run(last_undecided, "undecided")
        assert_silent_pass(last_made)

    def test_the_list_reads_cwd_and_home_only_from_its_arguments(self, tmp_path):
        # Sub-job A: it "reads the environment only through these arguments". The process runs
        # somewhere else, under a HOME of its own, and each of those holds what a misreading
        # would act on: an undecided card in the process's folder, a product under its HOME.
        scene = make_scene(tmp_path)
        write_card(scene.instance, "demo", [behave_line("behave")], product_path="~/handed")
        handed = make_product(scene.home / "handed")
        process_dir = tmp_path / "process-cwd"
        write_card(process_dir, "demo", [], product_path=None)
        env_home = tmp_path / "process-home"
        env_product = make_product(env_home / "handed")

        result = run_check(scene, "walk", "demo", process_cwd=process_dir, env_home=env_home)

        assert result.returncode == 0, result.stderr
        assert installer_calls(scene) == [expected_call(scene, "walk", "demo", handed)]
        assert snapshot(env_product) == {}

    def test_inherited_definition_exemption_covers_only_two_launchers(self, tmp_path):
        scene = make_scene(tmp_path)
        write_card(scene.instance, "demo", [], product_path=None)

        answer = run_check(scene, "companion-self-answer", "demo", "FDR", definition_project="demo")
        skeleton = run_check(scene, "product-skeleton", "demo", definition_project="demo")
        walk = run_check(scene, "walk", "demo", definition_project="demo")
        other_project = run_check(
            scene, "companion-self-answer", "demo", "FDR", definition_project="another"
        )

        assert_silent_pass(answer)
        assert_silent_pass(skeleton)
        assert_stopped_naming_the_architecture_run(walk, "demo")
        assert_stopped_naming_the_architecture_run(other_project, "demo")

    @pytest.mark.parametrize(
        "launch_args",
        [
            pytest.param(["--keep-awake", "p"], id="keep-awake-first"),
            pytest.param(["--dry-run", "p"], id="dry-run-first"),
            pytest.param(["--keep-awake", "--dry-run", "p"], id="two-flags-first"),
            pytest.param(["--dry-run", "--dry-run", "p"], id="repeated-flag-first"),
            pytest.param([_INSTANCE_ROOT_FLAG, "other", "--keep-awake", "p"], id="root-then-flag"),
            pytest.param(["", "p"], id="empty-word-first"),
            pytest.param(["p"], id="project-only"),
            pytest.param(["p", "--keep-awake"], id="project-then-keep-awake"),
            pytest.param(["p", "--dry-run"], id="project-then-dry-run"),
        ],
    )
    def test_product_card_project_is_read_past_any_flag(self, tmp_path, launch_args):
        # CP-1249, CP-1252: the launcher's one bare word names the project wherever it stands.
        scene = make_scene(tmp_path)

        result = run_wrapper(scene, "_pin_launch_project", "product-card", *launch_args)

        assert result.returncode == 0, result.stderr
        assert result.stdout == "p\n"

    @pytest.mark.parametrize(
        "launch_args",
        [
            pytest.param([], id="no-arguments"),
            pytest.param(["--keep-awake", "--dry-run"], id="flags-only"),
            pytest.param(["", "--dry-run"], id="empty-word-and-flag"),
        ],
    )
    def test_a_product_card_launch_with_no_bare_word_names_no_project(self, tmp_path, launch_args):
        # The arm returns nothing when no word is left, so the launcher's own refusal stands.
        scene = make_scene(tmp_path)

        result = run_wrapper(scene, "_pin_launch_project", "product-card", *launch_args)

        assert result.returncode == 0, result.stderr
        assert result.stdout == ""

    @pytest.mark.parametrize("launcher", ["walk", "change"])
    def test_other_launchers_still_name_no_project_past_a_flag(self, tmp_path, launcher):
        # CP-1254: the other first-positional launchers keep their lookup.
        scene = make_scene(tmp_path)

        result = run_wrapper(scene, "_pin_launch_project", launcher, "--dry-run", "p")

        assert result.returncode == 0, result.stderr
        assert result.stdout == ""

    @pytest.mark.parametrize(
        "behave_lines", [[], [behave_line("behave")]], ids=["undecided", "behave"]
    )
    def test_a_product_card_launch_is_never_stopped_in_any_flag_order(self, tmp_path, behave_lines):
        # CP-1251: the launcher is a definition launcher, whatever its argument order.
        scene = make_scene(tmp_path)
        write_card(scene.instance, "demo", behave_lines, product_path=None)
        before = snapshot(scene.root)

        result = run_check(scene, "product-card", "--keep-awake", "demo")

        assert_silent_pass(result)
        assert snapshot(scene.root) == before

    @pytest.mark.parametrize("launcher", ["walk", "change"])
    def test_walk_and_change_on_their_own_are_still_stopped_over_an_undecided_card(
        self, tmp_path, launcher
    ):
        # CP-1253: outside a definition launch, the exemption reaches neither.
        scene = make_scene(tmp_path)
        write_card(scene.instance, "demo", [behave_line(_UNDECIDED_TEMPLATE_LINE)])

        result = run_check(scene, launcher, "demo")

        assert_stopped_naming_the_architecture_run(result, "demo")


def _usage_project_argument(launcher_source: str) -> str:
    """What a launcher's own `usage` text says about a project: `first`, `flag` or `none`."""
    found = re.search(
        r"usage: (?:<CORE>/launchers/[\w-]+/launcher\.sh|launch-[\w-]+)(?: ([^\n\"]*))?",
        launcher_source,
    )
    assert found, "a launcher states no usage line the table can be held to"
    arguments = (found.group(1) or "").split()
    if "--project <project>" in (found.group(1) or ""):
        return "flag"
    if arguments and arguments[0] == "<project>":
        return "first"
    return "none"


class TestTheProjectTableMatchesTheLaunchers:
    def test_the_project_table_matches_every_launchers_own_usage(self, tmp_path):
        scene = make_scene(tmp_path)
        launcher_sources = sorted(_LAUNCHERS_DIR.glob("*/launcher.sh"))
        assert launcher_sources
        mismatches: list[str] = []

        for source in launcher_sources:
            name = source.parent.name
            text = source.read_text()
            first = run_wrapper(scene, "_pin_launch_project", name, "probeproject").stdout.strip()
            flagged = run_wrapper(
                scene, "_pin_launch_project", name, "a-skill", "--project", "probeproject"
            ).stdout.strip()
            read = (
                "first"
                if first == "probeproject"
                else "flag"
                if flagged == "probeproject"
                else "none"
            )
            if read != _usage_project_argument(text):
                usage = _usage_project_argument(text)
                mismatches.append(f"{name}: the list reads {read}; its usage says {usage}")

            root = run_wrapper(
                scene,
                "_pin_launch_instance_root",
                name,
                "/probe/cwd",
                _INSTANCE_ROOT_FLAG,
                "/probe/other",
                "probeproject",
            ).stdout.strip()
            takes_root_flag = '[ "${1:-}" = "--instance-root" ]' in text
            if root != ("/probe/other" if takes_root_flag else "/probe/cwd"):
                mismatches.append(
                    f"{name}: root {root!r}; its source takes the flag: {takes_root_flag}"
                )

        assert mismatches == []

    def test_every_exempted_or_inheriting_name_is_a_launcher_on_disk(self):
        for name in (*_DEFINITION_LAUNCHERS, *_INHERITING_LAUNCHERS):
            assert (_LAUNCHERS_DIR / name / "launcher.sh").is_file(), name


# --- the hook, seen through launchers (layer 5) ---

# A stub launcher named after a real one: it enters the pin, records that it started, and then
# runs the nested launches `STUB_NESTED` lists, one `<launcher> <arguments>` per line, recording
# the status of any that stops.
_NAMED_STUB = """#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
SCRIPT_PATH="${SCRIPT_DIR}/$(basename "${BASH_SOURCE[0]}")"
CORE_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd -P)"

source "${CORE_DIR}/tools/pin_run.sh"
__ENTER__ "${CORE_DIR}" "${SCRIPT_PATH}" "$@" || exit $?

echo "$(basename "${SCRIPT_DIR}") $*" >> "${STUB_RECORD}"

# The nested launches get no list of their own, or each would start the list again.
nested_lines="${STUB_NESTED:-}"
unset STUB_NESTED

while IFS= read -r nested; do
  [ -n "${nested}" ] || continue
  # Word splitting is the point: a nested line is a launcher name and its arguments.
  bash "${CORE_DIR}/launchers/${nested%% *}/launcher.sh" ${nested#* } \
    || echo "nested ${nested} stopped with $?" >> "${STUB_RECORD}"
done <<< "${nested_lines}"
"""

_STUB_LAUNCHERS = {
    "walk": "pin_enter",
    "build-idea": "pin_enter_renewing",
    "product-card": "pin_enter",
    "product-skeleton": "pin_enter",
    "companion-self-answer": "pin_enter",
}


def _named_host(root: Path) -> Path:
    """A throwaway host whose stub launchers carry real launchers' names and source the real
    `pin_run.sh`; its core holds the Behave starter, so a pin of it does too."""
    _init_pin_run_host(root)
    shutil.copytree(_STARTER_DIR, root / "core" / "templates" / "behave-starter")
    for name in _TOOL_MODULES:
        target = root / "core" / "tools" / f"{name}.py"
        if not target.exists():
            shutil.copy2(_TOOLS_DIR / f"{name}.py", target)
    for name, entry in _STUB_LAUNCHERS.items():
        folder = root / "core" / "launchers" / name
        folder.mkdir(parents=True)
        launcher = folder / "launcher.sh"
        launcher.write_text(_NAMED_STUB.replace("__ENTER__", entry))
        launcher.chmod(0o755)
    return root


@dataclass(frozen=True)
class Launch:
    result: subprocess.CompletedProcess
    started: list[str]


def _launch_environment(tmp_path: Path, record: Path, **extra: str) -> dict[str, str]:
    return {
        "PATH": os.environ["PATH"],
        "HOME": str(tmp_path),
        "KENSAIAPP_PINS_HOME": str(tmp_path / "pins"),
        "STUB_RECORD": str(record),
        **_GIT_IDENTITY,
        **extra,
    }


def launch(tmp_path: Path, launcher: Path, *launch_args: str, nested: str = "") -> Launch:
    record = tmp_path / "record.txt"
    instance = tmp_path / "instance"
    instance.mkdir(exist_ok=True)
    cards_before = card_bytes(tmp_path)
    result = subprocess.run(
        ["bash", str(launcher), *launch_args],
        cwd=str(instance),
        capture_output=True,
        text=True,
        env=_launch_environment(tmp_path, record, STUB_NESTED=nested),
    )
    assert card_bytes(tmp_path) == cards_before
    started = record.read_text().splitlines() if record.exists() else []
    return Launch(result=result, started=started)


def _pinned_launcher(tmp_path: Path, name: str) -> Path:
    """The stub launcher `name` inside a pin of a throwaway host, so a launch through it decides
    its pin by rule 1 and makes no second one."""
    host = _named_host(tmp_path / "host")
    pins_home = tmp_path / "pins"
    pins_home.mkdir()
    made = pin.make(host, pins_home)
    return made.core / "launchers" / name / "launcher.sh"


def _prepare_instance(tmp_path: Path, behave_lines: list[str], project: str = "p") -> Path:
    instance = tmp_path / "instance"
    write_card(instance, project, behave_lines)
    return make_product(instance / "prod")


class TestTheHook:
    def test_launch_over_an_undecided_card_stops_before_the_agent_starts(self, tmp_path):
        stub = _pinned_launcher(tmp_path, "walk")
        _prepare_instance(tmp_path, [])

        run = launch(tmp_path, stub, "p")

        assert run.result.returncode != 0
        assert "product-architecture" in run.result.stderr
        assert run.started == []

    def test_launch_over_a_made_call_card_starts_without_output(self, tmp_path):
        stub = _pinned_launcher(tmp_path, "walk")
        _prepare_instance(tmp_path, [behave_line("none — a test card")])

        run = launch(tmp_path, stub, "p")

        assert run.result.returncode == 0, run.result.stderr
        assert run.started == ["walk p"]
        assert "Behave" not in run.result.stderr + run.result.stdout

    def test_the_list_runs_once_across_the_reexec(self, tmp_path):
        host = _named_host(tmp_path / "host")
        (tmp_path / "pins").mkdir()
        product = make_repository(_prepare_instance(tmp_path, [behave_line("behave")]))

        run = launch(tmp_path, host / "core" / "launchers" / "walk" / "launcher.sh", "p")

        assert run.result.returncode == 0, run.result.stderr
        assert run.started == ["walk p"]
        assert [line for line in run.result.stderr.splitlines() if str(product) in line] != []
        assert len([line for line in run.result.stderr.splitlines() if str(product) in line]) == 1
        assert (product / _FOLDER).is_dir()
        assert git(product, "log", "-1", "--format=%s").startswith("behave-check:")

    def test_dry_run_without_a_pin_runs_the_list_on_the_early_return(self, tmp_path):
        host = _named_host(tmp_path / "host")
        (tmp_path / "pins").mkdir()
        walk = host / "core" / "launchers" / "walk" / "launcher.sh"
        product = _prepare_instance(tmp_path, [behave_line("behave")])
        product_before = snapshot(product)

        would = launch(tmp_path, walk, "p", "--dry-run")
        write_card(tmp_path / "instance", "undecided", [])
        stopped = launch(tmp_path, walk, "undecided", "--dry-run")

        assert would.result.returncode == 0, would.result.stderr
        assert len([line for line in would.result.stderr.splitlines() if str(product) in line]) == 1
        assert snapshot(product) == product_before
        assert stopped.result.returncode != 0
        assert "product-architecture" in stopped.result.stderr

    def test_the_renewing_entry_runs_the_list(self, tmp_path):
        stub = _pinned_launcher(tmp_path, "build-idea")
        _prepare_instance(tmp_path, [])

        run = launch(tmp_path, stub, "p")

        assert run.result.returncode != 0
        assert "product-architecture" in run.result.stderr
        assert run.started == []

    def test_stop_is_not_stopped_by_the_list(self, tmp_path):
        stub = _pinned_launcher(tmp_path, "walk")
        _prepare_instance(tmp_path, [])

        run = launch(tmp_path, stub, "p", "--stop")

        assert run.result.returncode == 0, run.result.stderr
        assert run.started == ["walk p --stop"]

    def test_a_definition_launch_passes_its_exemption_to_the_two_launches_it_starts(self, tmp_path):
        stub = _pinned_launcher(tmp_path, "product-card")
        _prepare_instance(tmp_path, [])

        run = launch(
            tmp_path,
            stub,
            "p",
            nested="product-skeleton p\ncompanion-self-answer p FDR\nwalk p",
        )

        assert run.result.returncode == 0, run.result.stderr
        assert run.started == [
            "product-card p",
            "product-skeleton p",
            "companion-self-answer p FDR",
            "nested walk p stopped with 1",
        ]
        assert "product-architecture" in run.result.stderr
        assert len(run.result.stderr.splitlines()) == _STOP_MESSAGE_LINES

    @pytest.mark.parametrize(
        "behave_lines",
        [[behave_line(_UNDECIDED_TEMPLATE_LINE)], []],
        ids=["template-undecided-line", "no-behave-line"],
    )
    @pytest.mark.parametrize(
        "launch_args",
        [
            pytest.param(["--keep-awake", "p"], id="keep-awake-first"),
            pytest.param(["--dry-run", "p"], id="dry-run-first"),
            pytest.param(["--keep-awake", "--dry-run", "p"], id="two-flags-first"),
        ],
    )
    def test_a_flag_first_product_card_launch_hands_its_exemption_to_the_two_launches_it_starts(
        self, tmp_path, launch_args, behave_lines
    ):
        # CP-1249, CP-1251, CP-1256: CP-1256 names the template's undecided line as the card.
        stub = _pinned_launcher(tmp_path, "product-card")
        _prepare_instance(tmp_path, behave_lines)

        run = launch(
            tmp_path,
            stub,
            *launch_args,
            nested="product-skeleton p\ncompanion-self-answer p FDR",
        )

        assert run.result.returncode == 0, run.result.stderr
        assert run.started == [
            f"product-card {' '.join(launch_args)}",
            "product-skeleton p",
            "companion-self-answer p FDR",
        ]
        assert "product-architecture" not in run.result.stderr

    def test_a_project_first_product_card_launch_keeps_its_exemption(self, tmp_path):
        # CP-1252: the order that already worked is unchanged.
        stub = _pinned_launcher(tmp_path, "product-card")
        _prepare_instance(tmp_path, [])

        run = launch(
            tmp_path,
            stub,
            "p",
            "--keep-awake",
            nested="product-skeleton p\ncompanion-self-answer p FDR",
        )

        assert run.result.returncode == 0, run.result.stderr
        assert run.started == [
            "product-card p --keep-awake",
            "product-skeleton p",
            "companion-self-answer p FDR",
        ]
        assert "product-architecture" not in run.result.stderr

    def test_the_exemption_under_a_flag_first_launch_does_not_reach_a_walk(self, tmp_path):
        # CP-1253: the exemption still covers only the two launchers.
        stub = _pinned_launcher(tmp_path, "product-card")
        _prepare_instance(tmp_path, [])

        run = launch(tmp_path, stub, "--keep-awake", "p", nested="walk p")

        assert run.result.returncode == 0, run.result.stderr
        assert run.started == ["product-card --keep-awake p", "nested walk p stopped with 1"]
        assert "product-architecture" in run.result.stderr
        assert len(run.result.stderr.splitlines()) == _STOP_MESSAGE_LINES

    def test_the_exemption_under_a_flag_first_launch_covers_only_its_own_project(self, tmp_path):
        # CP-1253: a nested launch for another project over an undecided card is still stopped.
        stub = _pinned_launcher(tmp_path, "product-card")
        _prepare_instance(tmp_path, [])
        write_card(tmp_path / "instance", "q", [])

        run = launch(
            tmp_path,
            stub,
            "--keep-awake",
            "p",
            nested="companion-self-answer q FDR\nproduct-skeleton q",
        )

        assert run.result.returncode == 0, run.result.stderr
        assert run.started == [
            "product-card --keep-awake p",
            "nested companion-self-answer q FDR stopped with 1",
            "nested product-skeleton q stopped with 1",
        ]

    def test_a_flag_first_launch_with_an_instance_root_hands_its_exemption_on(self, tmp_path):
        # CP-1249: the `--instance-root` pair and a flag both stand before the project.
        stub = _pinned_launcher(tmp_path, "product-card")
        write_card(tmp_path / "instance" / "other", "p", [])

        run = launch(
            tmp_path,
            stub,
            _INSTANCE_ROOT_FLAG,
            "other",
            "--keep-awake",
            "p",
            nested=(
                f"product-skeleton {_INSTANCE_ROOT_FLAG} other p\n"
                f"companion-self-answer {_INSTANCE_ROOT_FLAG} other p FDR"
            ),
        )

        assert run.result.returncode == 0, run.result.stderr
        assert run.started == [
            "product-card --instance-root other --keep-awake p",
            "product-skeleton --instance-root other p",
            "companion-self-answer --instance-root other p FDR",
        ]
        assert "product-architecture" not in run.result.stderr


def _real_launch(tmp_path: Path, name: str, *launch_args: str) -> subprocess.CompletedProcess:
    """A real launcher from this core, run as it is from a scratch instance. `--dry-run` is
    among the arguments the caller gives, so no agent is launched and no pin is made."""
    instance = tmp_path / "instance"
    instance.mkdir(exist_ok=True)
    (tmp_path / "pins").mkdir(exist_ok=True)
    cards_before = card_bytes(instance)
    result = subprocess.run(
        ["bash", str(_LAUNCHERS_DIR / name / "launcher.sh"), *launch_args],
        cwd=str(instance),
        capture_output=True,
        text=True,
        env=_launch_environment(tmp_path, tmp_path / "record.txt"),
    )
    assert card_bytes(instance) == cards_before
    return result


class TestTheRealLaunchers:
    @pytest.mark.parametrize("launcher", _DEFINITION_LAUNCHERS)
    @pytest.mark.parametrize(
        "behave_lines", [[], [behave_line("behave")]], ids=["undecided", "behave"]
    )
    def test_the_real_definition_launchers_are_not_stopped(self, tmp_path, launcher, behave_lines):
        product = _prepare_instance(tmp_path, behave_lines)
        before = snapshot(tmp_path / "instance")

        result = _real_launch(tmp_path, launcher, "p", "--dry-run")

        assert "has not made its Behave call" not in result.stderr
        assert "Behave starter" not in result.stderr
        assert snapshot(tmp_path / "instance") == before
        assert not (product / _FOLDER).exists()

    def test_the_real_product_skeleton_stops_before_writing(self, tmp_path):
        product = _prepare_instance(tmp_path, [])
        before = snapshot(product)

        result = _real_launch(tmp_path, "product-skeleton", "p", "--dry-run")

        assert result.returncode != 0
        assert "product-architecture" in result.stderr
        assert snapshot(product) == before

    def test_real_launchers_without_a_project_or_a_card_keep_their_own_handling(self, tmp_path):
        _prepare_instance(tmp_path, [])

        # No argument at all: with `--dry-run` the launcher would read that flag as the project.
        no_argument = _real_launch(tmp_path, "change")
        no_card = _real_launch(tmp_path, "change", "ghost", "--dry-run")
        cold_read = _real_launch(tmp_path, "cold-read", "some-skill", "--project", "p", "--dry-run")

        assert no_argument.returncode != 0
        assert "usage:" in no_argument.stderr
        assert "product-architecture" not in no_argument.stderr
        assert no_card.returncode != 0
        assert "ghost" in no_card.stderr
        assert "product-architecture" not in no_card.stderr
        assert cold_read.returncode != 0
        assert "product-architecture" in cold_read.stderr
