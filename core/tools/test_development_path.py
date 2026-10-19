"""Tests for `development_path.py`.

The CLI is exercised two ways: through `main()` with an injected `Git`, where the point is the
tool's own logic, and through a real `python3` subprocess, where the point is the shipped entry
point. The tool path comes from this file's location, never the working directory.
"""

from __future__ import annotations

import io
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import NoReturn

import pytest

import development_path
from development_path import (
    Git,
    GitRepos,
    LayoutRepos,
    ToolError,
    main,
    parse_product_path,
    resolve,
    resolve_from_paths,
    target,
    validate_contract,
)

TOOL = str(Path(__file__).resolve().parent / "development_path.py")


def run_cli(*args: str, cwd: Path) -> subprocess.CompletedProcess:
    """The real entry point, from a working directory that is not the repo."""
    return subprocess.run([sys.executable, TOOL, *args], capture_output=True, text=True, cwd=cwd)


# --- fixture repositories -----------------------------------------------------------------------

KEY = "2026-09-29_example-change"
PROJECT = "proj"

RelativeSetup = tuple[Path, Path]  # (instance repo, its worktree on KEY)
FixedSetup = tuple[Path, Path, Path, Path]  # (instance, its worktree, product, its worktree)


def git(cwd: Path, *args: str) -> str:
    """Run git in a throwaway fixture repo, with an identity and no hooks or signing of its own."""
    result = subprocess.run(
        ["git", "-C", str(cwd), "-c", "user.name=fixture",
         "-c", "user.email=fixture@example.invalid", "-c", "commit.gpgsign=false",
         "-c", "core.hooksPath=/dev/null", *args],
        capture_output=True, text=True, check=True)
    return result.stdout.strip()


def make_repo(path: Path, files: dict[str, str] | None = None) -> Path:
    """A git repo on `main` with one commit holding `files`."""
    path.mkdir(parents=True, exist_ok=True)
    git(path, "init", "-q", "-b", "main")
    for name, text in (files or {}).items():
        (path / name).parent.mkdir(parents=True, exist_ok=True)
        (path / name).write_text(text, encoding="utf-8")
    git(path, "add", "-A")
    git(path, "commit", "-q", "--allow-empty", "-m", "init")
    return path


def add_worktree(repo: Path, key: str = KEY) -> Path:
    """`<repo>/.worktrees/<key>` on a new branch `<key>` — the layout the flow creates."""
    worktree = repo / ".worktrees" / key
    git(repo, "worktree", "add", "-q", "-b", key, str(worktree))
    return worktree


def project_md(product_path: str) -> dict[str, str]:
    return {f"system/projects/{PROJECT}/project.md":
            f"# Project\n\n**Product path:** {product_path}   <!-- note -->\n"}


@pytest.fixture
def root(tmp_path: Path) -> Path:
    """`tmp_path` with symlinks resolved, so it compares equal to the paths git reports."""
    return tmp_path.resolve()


@pytest.fixture
def relative_setup(root: Path) -> RelativeSetup:
    """An instance repo whose product is `products/app` inside it, with the change's worktree."""
    instance = make_repo(root / "instance",
                         {**project_md("products/app"), "products/app/README.md": "app\n"})
    return instance, add_worktree(instance)


@pytest.fixture
def fixed_setup(root: Path) -> FixedSetup:
    """An instance repo and a separate product repo, each with the change's worktree."""
    product = make_repo(root / "product", {"src/app.py": "print('app')\n"})
    instance = make_repo(root / "instance", project_md(str(product)))
    return instance, add_worktree(instance), product, add_worktree(product)


class StubRepos:
    """Repository identities handed in, so `resolve` is tested without a filesystem or git."""

    def instance_repo(self, worktree: str) -> str:
        return "/abs/instance"

    def product_repo(self, product_path: str) -> str:
        return product_path

    def is_instance_repo(self, product_repo: str, instance_repo: str) -> bool:
        return product_repo == instance_repo


class ExplodingGit:
    """A `Git` that fails the test the moment anything asks it a question."""

    def __getattr__(self, name: str) -> NoReturn:
        raise AssertionError(f"git was asked '{name}' under --no-check-git")


def run_main(*args: str, git: object | None = None,
             home: str = "/nonexistent-home") -> tuple[int, str]:
    """`main()` in-process with an injected `Git` and home directory; the exit code and what it
    printed."""
    out = io.StringIO()
    code = main(list(args), git=git if git is not None else Git(), stdout=out, home=home)
    return code, out.getvalue()


def layout(root: Path, product_path: str) -> Path:
    """`<root>/instance/.worktrees/<KEY>` holding a project.md — the flow's layout, with no git
    at all."""
    worktree = root / "instance" / ".worktrees" / KEY
    for name, text in project_md(product_path).items():
        (worktree / name).parent.mkdir(parents=True, exist_ok=True)
        (worktree / name).write_text(text, encoding="utf-8")
    return worktree


class BrokenGit(Git):
    """A `Git` whose repository question fails in a way the tool did not foresee."""

    def main_worktree(self, path: str) -> str | None:
        raise RuntimeError("boom")


# --- the resolver's pure parts ----------------------------------------------------------------


def test_resolve_relative_topology() -> None:
    content = "**Product path:** projects/my-product"
    result = resolve(content, "/abs/instance/.worktrees/key1", "proj", "key1", StubRepos())
    assert result["kind"] == "relative"
    assert result["product_repo"] == "/abs/instance"
    assert result["code_worktree"] == "/abs/instance/.worktrees/key1"
    assert result["delivery_repos"] == ["instance"]


def test_resolve_fixed_topology() -> None:
    content = "**Product path:** /abs/product-repo"
    result = resolve(content, "/abs/instance/.worktrees/key1", "proj", "key1", StubRepos())
    assert result["kind"] == "fixed"
    assert result["product_repo"] == "/abs/product-repo"
    assert result["code_worktree"] == "/abs/product-repo/.worktrees/key1"
    assert result["pipeline_repo"] == "/abs/instance"
    assert result["delivery_repos"] == ["product", "instance"]


def test_resolve_an_absolute_path_the_repos_call_the_instance_is_relative() -> None:
    content = "**Product path:** /abs/instance"
    result = resolve(content, "/abs/instance/.worktrees/key1", "proj", "key1", StubRepos())
    assert result["kind"] == "relative"
    assert result["product_path"] == "/abs/instance"
    assert result["code_worktree"] == "/abs/instance/.worktrees/key1"
    assert result["delivery_repos"] == ["instance"]


def test_target_command() -> None:
    contract = {
        "code_repo": "c_r", "code_worktree": "c_w",
        "pipeline_repo": "p_r", "pipeline_worktree": "p_w",
        "delivery_repos": ["d_r"]
    }
    assert target(contract, "code") == {"repo": "c_r", "worktree": "c_w"}
    assert target(contract, "pipeline") == {"repo": "p_r", "worktree": "p_w"}
    assert target(contract, "delivery") == {"repos": ["d_r"]}

    with pytest.raises(ToolError, match="invalid-target-kind"):
        target(contract, "unknown")


def test_no_module_level_subprocess_call_outside_git() -> None:
    """Every git question goes through the injected `Git`; nothing else in the module spawns a
    process, so a fake `Git` really does isolate a test from the machine."""
    source = Path(development_path.__file__).read_text(encoding="utf-8")
    assert source.count("subprocess.run(") == 1
    git_body = source[source.index("class Git:"):source.index("# --- parsing")]
    assert "subprocess.run(" in git_body


def test_cli_help(tmp_path: Path) -> None:
    res = run_cli("--help", cwd=tmp_path)
    assert res.returncode == 0
    assert "usage:" in res.stdout


def test_cli_version(tmp_path: Path) -> None:
    res = run_cli("--version", cwd=tmp_path)
    assert res.returncode == 0
    assert development_path.__version__ in res.stdout


class TestGit:
    def test_main_worktree_from_a_linked_worktree_is_the_main_checkout(
            self, relative_setup: RelativeSetup) -> None:
        instance, worktree = relative_setup
        assert Git().main_worktree(str(worktree)) == str(instance)
        assert Git().main_worktree(str(instance)) == str(instance)

    def test_main_worktree_outside_a_repo_is_none(self, root: Path) -> None:
        assert Git().main_worktree(str(root)) is None


class TestRepositoryIdentity:
    def test_instance_repo_is_the_main_checkout_not_the_linked_worktree(
            self, relative_setup: RelativeSetup) -> None:
        instance, worktree = relative_setup
        contract = resolve_from_paths(str(worktree), PROJECT, KEY, GitRepos(Git()))
        assert contract["instance_repo"] == str(instance)
        assert contract["instance_worktree"] == str(worktree)
        assert contract["pipeline_repo"] == str(instance)
        assert contract["code_repo"] == str(instance)
        assert contract["code_worktree"] == str(worktree)

    def test_fixed_product_path_naming_a_subdirectory_resolves_to_the_repo_root(
            self, root: Path) -> None:
        product = make_repo(root / "product", {"src/app.py": "x\n"})
        add_worktree(product)
        instance = make_repo(root / "instance", project_md(str(product / "src")))
        worktree = add_worktree(instance)
        contract = resolve_from_paths(str(worktree), PROJECT, KEY, GitRepos(Git()))
        assert contract["product_path"] == str(product / "src")
        assert contract["product_repo"] == str(product)
        assert contract["product_worktree"] == str(product / ".worktrees" / KEY)
        assert contract["code_worktree"] == str(product / ".worktrees" / KEY)
        validate_contract(contract, Git())

    def test_valid_fixed_topology_passes(self, fixed_setup: FixedSetup) -> None:
        instance, worktree, product, product_worktree = fixed_setup
        contract = resolve_from_paths(str(worktree), PROJECT, KEY, GitRepos(Git()))
        assert contract["instance_repo"] == str(instance)
        assert contract["product_repo"] == str(product)
        assert contract["code_worktree"] == str(product_worktree)
        validate_contract(contract, Git())

    def test_valid_relative_topology_passes(self, relative_setup: RelativeSetup) -> None:
        _, worktree = relative_setup
        validate_contract(resolve_from_paths(str(worktree), PROJECT, KEY, GitRepos(Git())), Git())

    def test_product_worktree_that_is_a_plain_directory_is_missing(self, root: Path) -> None:
        product = make_repo(root / "product", {"src/app.py": "x\n"})
        (product / ".worktrees" / KEY).mkdir(parents=True)
        instance = make_repo(root / "instance", project_md(str(product)))
        worktree = add_worktree(instance)
        contract = resolve_from_paths(str(worktree), PROJECT, KEY, GitRepos(Git()))
        with pytest.raises(ToolError, match="product-worktree-missing") as caught:
            validate_contract(contract, Git())
        assert "not the root of a git worktree" in caught.value.message

    def test_product_worktree_belonging_to_another_repo_is_refused(self, root: Path) -> None:
        """A same-named branch in the wrong repository must not satisfy validation."""
        product = make_repo(root / "product", {"src/app.py": "x\n"})
        stray = make_repo(product / ".worktrees" / KEY)
        git(stray, "checkout", "-q", "-b", KEY)
        instance = make_repo(root / "instance", project_md(str(product)))
        worktree = add_worktree(instance)
        contract = resolve_from_paths(str(worktree), PROJECT, KEY, GitRepos(Git()))
        with pytest.raises(ToolError, match="product-worktree-missing") as caught:
            validate_contract(contract, Git())
        assert str(stray) in caught.value.message
        assert str(product) in caught.value.message

    def test_product_worktree_of_another_repo_on_the_key_branch_is_refused(
            self, root: Path) -> None:
        product = make_repo(root / "product", {"src/app.py": "x\n"})
        other = make_repo(root / "other")
        (product / ".worktrees").mkdir()
        git(other, "worktree", "add", "-q", "-b", KEY, str(product / ".worktrees" / KEY))
        instance = make_repo(root / "instance", project_md(str(product)))
        worktree = add_worktree(instance)
        contract = resolve_from_paths(str(worktree), PROJECT, KEY, GitRepos(Git()))
        with pytest.raises(ToolError, match="product-worktree-missing") as caught:
            validate_contract(contract, Git())
        assert str(other) in caught.value.message

    def test_instance_worktree_of_a_different_repo_than_the_contract_says_is_refused(
            self, relative_setup: RelativeSetup, root: Path) -> None:
        _, worktree = relative_setup
        contract = resolve_from_paths(str(worktree), PROJECT, KEY, GitRepos(Git()))
        elsewhere = make_repo(root / "elsewhere")
        contract = {**contract, "instance_repo": str(elsewhere), "pipeline_repo": str(elsewhere)}
        with pytest.raises(ToolError, match="instance-worktree-missing") as caught:
            validate_contract(contract, Git())
        assert str(elsewhere) in caught.value.message

    def test_instance_worktree_that_is_a_subdirectory_is_not_a_worktree_root(
            self, relative_setup: RelativeSetup) -> None:
        _, worktree = relative_setup
        contract = resolve_from_paths(str(worktree), PROJECT, KEY, GitRepos(Git()))
        subdir = str(worktree / "system")
        contract = {**contract, "instance_worktree": subdir, "pipeline_worktree": subdir}
        with pytest.raises(ToolError, match="instance-worktree-missing") as caught:
            validate_contract(contract, Git())
        assert str(worktree) in caught.value.message


class TestBranchTopology:
    def test_git_branch_of_a_detached_head_is_none(self, relative_setup: RelativeSetup) -> None:
        _, worktree = relative_setup
        git(worktree, "checkout", "-q", "--detach")
        assert Git().branch(str(worktree)) is None
        assert Git().branch(str(worktree.parent.parent)) == "main"

    def test_detached_instance_worktree_is_refused(self, relative_setup: RelativeSetup) -> None:
        _, worktree = relative_setup
        git(worktree, "checkout", "-q", "--detach")
        contract = resolve_from_paths(str(worktree), PROJECT, KEY, GitRepos(Git()))
        with pytest.raises(ToolError, match="branch-topology-missing") as caught:
            validate_contract(contract, Git())
        assert "detached HEAD" in caught.value.message

    def test_wrong_key_names_both_branches(self, relative_setup: RelativeSetup) -> None:
        _, worktree = relative_setup
        contract = resolve_from_paths(str(worktree), PROJECT, "2026-09-29_other", GitRepos(Git()))
        with pytest.raises(ToolError, match="branch-topology-missing") as caught:
            validate_contract(contract, Git())
        assert f"'{KEY}'" in caught.value.message
        assert "'2026-09-29_other'" in caught.value.message

    def test_product_worktree_on_another_branch_is_refused(self, fixed_setup: FixedSetup) -> None:
        _, worktree, _, product_worktree = fixed_setup
        git(product_worktree, "checkout", "-q", "-b", "elsewhere")
        contract = resolve_from_paths(str(worktree), PROJECT, KEY, GitRepos(Git()))
        with pytest.raises(ToolError, match="branch-topology-missing") as caught:
            validate_contract(contract, Git())
        assert str(product_worktree) in caught.value.message
        assert "'elsewhere'" in caught.value.message


class TestParseProductPath:
    @pytest.mark.parametrize("line, expected", [
        ("**Product path:** core/tools", ("relative", "core/tools")),
        ("**Product path:** .claude   <!-- nominal anchor -->", ("relative", ".claude")),
        ("**Product path:** core/tools<!-- tight -->", ("relative", "core/tools")),
        ("**Product path:** core/tools <!-- one --> <!-- two -->", ("relative", "core/tools")),
        ("**Product path:** /abs/product   <!-- absolute -->", ("fixed", "/abs/product")),
        ("**Product path:**\t/abs/product\t", ("fixed", "/abs/product")),
        ("**Product path:** products/my app", ("relative", "products/my app")),
    ])
    def test_value_is_the_field_minus_trailing_comments(
            self, line: str, expected: tuple[str, str]) -> None:
        content = f"# Project\n\n{line}\n**Execution type:** headless\n"
        assert parse_product_path(content) == expected

    def test_only_the_first_declaration_counts(self) -> None:
        content = "**Product path:** first\n**Product path:** /second\n"
        assert parse_product_path(content) == ("relative", "first")

    def test_an_empty_first_declaration_is_not_rescued_by_a_later_one(self) -> None:
        with pytest.raises(ToolError, match="missing-product-path"):
            parse_product_path("**Product path:**  <!-- empty -->\n**Product path:** core/tools\n")

    def test_an_indented_or_prefixed_field_is_not_the_field(self) -> None:
        with pytest.raises(ToolError, match="missing-product-path"):
            parse_product_path("  **Product path:** core/tools\n")
        with pytest.raises(ToolError, match="missing-product-path"):
            parse_product_path("- **Product path:** core/tools\n")

    @pytest.mark.parametrize("value", [
        "core/tools <!-- note --> trailing",
        "core/tools <!-- unterminated",
        "core/tools --> stray",
    ])
    def test_a_comment_that_is_not_trailing_is_malformed(self, value: str) -> None:
        with pytest.raises(ToolError, match="invalid-product-path") as caught:
            parse_product_path(f"**Product path:** {value}\n")
        assert value in caught.value.message

    @pytest.mark.parametrize("value", ["..", "../sibling", "products/../../outside", "./.."])
    def test_a_relative_value_that_leaves_the_instance_is_invalid(self, value: str) -> None:
        with pytest.raises(ToolError, match="invalid-product-path") as caught:
            parse_product_path(f"**Product path:** {value}\n")
        assert f"'{value}'" in caught.value.message
        assert "absolute path" in caught.value.message

    def test_a_tilde_value_with_no_home_given_is_invalid(self) -> None:
        with pytest.raises(ToolError, match="invalid-product-path") as caught:
            parse_product_path("**Product path:** ~/products/app\n")
        assert "~" in caught.value.message

    @pytest.mark.parametrize("value, expected", [
        ("~/products/app", "/home/owner/products/app"),
        ("~/products/app   <!-- note -->", "/home/owner/products/app"),
        ("~/", "/home/owner/"),
    ])
    def test_a_leading_tilde_slash_expands_to_home_and_is_absolute(
            self, value: str, expected: str) -> None:
        """The chain launcher expands `~/` to `$HOME` (`launcher.sh`, `"~"/*`); the tool reads
        the same card the same way (cold read 2026-09-29, D4)."""
        content = f"**Product path:** {value}\n"
        assert parse_product_path(content, home="/home/owner") == ("fixed", expected)

    @pytest.mark.parametrize("value", ["~", "~owner/products/app", "~products"])
    def test_a_tilde_the_launcher_does_not_expand_stays_invalid(self, value: str) -> None:
        with pytest.raises(ToolError, match="invalid-product-path") as caught:
            parse_product_path(f"**Product path:** {value}\n", home="/home/owner")
        assert f"'{value}'" in caught.value.message

    def test_missing_field_message_says_what_to_add(self) -> None:
        with pytest.raises(ToolError, match="missing-product-path") as caught:
            parse_product_path("# Project\n")
        assert "**Product path:**" in caught.value.message


class TestProductPathTarget:
    """`validate` proves the declared product location is real: inside the instance worktree and
    its repository for `relative`, a git repository of its own for `fixed`."""

    def relative(self, root: Path, product_path: str, files: dict[str, str] | None = None) -> dict:
        instance = make_repo(root / "instance", {**project_md(product_path), **(files or {})})
        worktree = add_worktree(instance)
        return resolve_from_paths(str(worktree), PROJECT, KEY, GitRepos(Git()))

    def test_the_instance_root_itself_is_a_valid_relative_product(self, root: Path) -> None:
        validate_contract(self.relative(root, "."), Git())

    def test_a_missing_relative_product_is_invalid(self, root: Path) -> None:
        contract = self.relative(root, "products/app")
        with pytest.raises(ToolError, match="invalid-product-path") as caught:
            validate_contract(contract, Git())
        assert "'products/app'" in caught.value.message
        assert contract["instance_worktree"] in caught.value.message

    def test_a_relative_product_that_is_a_file_is_invalid(self, root: Path) -> None:
        contract = self.relative(root, "products/app", {"products/app": "not a directory\n"})
        with pytest.raises(ToolError, match="invalid-product-path") as caught:
            validate_contract(contract, Git())
        assert "not a directory" in caught.value.message

    def test_a_relative_product_symlinked_out_of_the_worktree_is_invalid(self, root: Path) -> None:
        outside = root / "outside"
        outside.mkdir()
        instance = make_repo(root / "instance", project_md("products/app"))
        (instance / "products").mkdir()
        (instance / "products" / "app").symlink_to(outside)
        git(instance, "add", "-A")
        git(instance, "commit", "-q", "-m", "link")
        worktree = add_worktree(instance)
        contract = resolve_from_paths(str(worktree), PROJECT, KEY, GitRepos(Git()))
        with pytest.raises(ToolError, match="invalid-product-path") as caught:
            validate_contract(contract, Git())
        assert str(outside) in caught.value.message

    def test_a_relative_product_that_is_a_nested_repository_is_invalid(self, root: Path) -> None:
        instance = make_repo(root / "instance", project_md("products/app"))
        worktree = add_worktree(instance)
        nested = make_repo(worktree / "products" / "app", {"a.py": "x\n"})
        contract = resolve_from_paths(str(worktree), PROJECT, KEY, GitRepos(Git()))
        with pytest.raises(ToolError, match="invalid-product-path") as caught:
            validate_contract(contract, Git())
        assert str(nested) in caught.value.message
        assert "absolute" in caught.value.message

    def test_resolve_without_validation_does_not_require_the_product_to_exist(
            self, root: Path) -> None:
        assert self.relative(root, "products/app")["product_path"] == "products/app"

    def test_a_fixed_product_path_that_does_not_exist_is_unresolved(self, root: Path) -> None:
        instance = make_repo(root / "instance", project_md(str(root / "gone")))
        worktree = add_worktree(instance)
        with pytest.raises(ToolError, match="product-repo-unresolved") as caught:
            resolve_from_paths(str(worktree), PROJECT, KEY, GitRepos(Git()))
        assert "does not exist" in caught.value.message
        assert str(root / "gone") in caught.value.message

    def test_a_fixed_product_path_outside_any_repository_is_unresolved(self, root: Path) -> None:
        (root / "plain").mkdir()
        instance = make_repo(root / "instance", project_md(str(root / "plain")))
        worktree = add_worktree(instance)
        with pytest.raises(ToolError, match="product-repo-unresolved") as caught:
            resolve_from_paths(str(worktree), PROJECT, KEY, GitRepos(Git()))
        assert "not inside a git repository" in caught.value.message

    def test_validate_refuses_a_contract_whose_product_path_is_in_another_repo(
            self, fixed_setup: FixedSetup, root: Path) -> None:
        _, worktree, _, _ = fixed_setup
        contract = resolve_from_paths(str(worktree), PROJECT, KEY, GitRepos(Git()))
        other = make_repo(root / "other")
        with pytest.raises(ToolError, match="product-repo-unresolved") as caught:
            validate_contract({**contract, "product_path": str(other)}, Git())
        assert str(other) in caught.value.message


class TestNoCheckGit:
    def test_layout_instance_repo_is_the_folder_holding_worktrees(self, root: Path) -> None:
        worktree = root / "instance" / ".worktrees" / KEY
        assert LayoutRepos().instance_repo(str(worktree)) == str(root / "instance")

    def test_layout_instance_repo_outside_a_worktrees_folder_is_the_worktree(
            self, root: Path) -> None:
        assert LayoutRepos().instance_repo(str(root / "instance")) == str(root / "instance")

    def test_layout_product_repo_is_the_declared_path(self, root: Path) -> None:
        assert LayoutRepos().product_repo(str(root / "product") + "/") == str(root / "product")

    def test_resolve_runs_no_git_at_all(self, root: Path) -> None:
        worktree = layout(root, str(root / "product"))
        code, out = run_main("resolve", "--worktree", str(worktree), "--project", PROJECT,
                             "--key", KEY, "--no-check-git", git=ExplodingGit())
        assert code == 0
        contract = json.loads(out)
        assert contract["instance_repo"] == str(root / "instance")
        assert contract["product_repo"] == str(root / "product")
        assert contract["code_worktree"] == str(root / "product" / ".worktrees" / KEY)
        assert contract["pipeline_worktree"] == str(worktree)

    def test_target_runs_no_git_at_all(self, root: Path) -> None:
        worktree = layout(root, "products/app")
        code, out = run_main("target", "--worktree", str(worktree), "--project", PROJECT,
                             "--key", KEY, "--kind", "code", "--no-check-git",
                             git=ExplodingGit())
        assert code == 0
        assert json.loads(out) == {"repo": str(root / "instance"), "worktree": str(worktree)}

    def test_the_audited_probe_resolves_outside_any_repository(self, root: Path) -> None:
        """audit-report-2.md: `resolve --no-check-git` on a non-git worktree failed with
        instance-repo-unresolved."""
        worktree = layout(root, "products/app")
        res = run_cli("resolve", "--worktree", str(worktree), "--project", PROJECT, "--key", KEY,
                      "--no-check-git", cwd=root)
        assert res.returncode == 0, res.stdout + res.stderr
        assert json.loads(res.stdout)["kind"] == "relative"

    def test_the_value_is_still_checked(self, root: Path) -> None:
        worktree = layout(root, "../outside")
        code, out = run_main("resolve", "--worktree", str(worktree), "--project", PROJECT,
                             "--key", KEY, "--no-check-git", git=ExplodingGit())
        assert code == 1
        assert json.loads(out)["error"] == "invalid-product-path"

    @pytest.mark.parametrize("command", [["validate"], ["resolve", "--strict"],
                                         ["target", "--kind", "code", "--strict"]])
    def test_it_cannot_be_combined_with_a_git_check(
            self, root: Path, command: list[str], capsys: pytest.CaptureFixture[str]) -> None:
        worktree = layout(root, "products/app")
        with pytest.raises(SystemExit) as caught:
            run_main(*command, "--worktree", str(worktree), "--project", PROJECT, "--key", KEY,
                     "--no-check-git", git=ExplodingGit())
        assert caught.value.code == 2
        assert "--no-check-git" in capsys.readouterr().err


class TestErrorSurface:
    def args(self, worktree: Path, *extra: str) -> list[str]:
        return ["--worktree", str(worktree), "--project", PROJECT, "--key", KEY, *extra]

    def test_json_error_carries_code_message_project_and_key(self, root: Path) -> None:
        code, out = run_main("resolve", *self.args(root / "absent"))
        assert code == 1
        error = json.loads(out)
        assert set(error) == {"error", "message", "project", "key"}
        assert error["error"] == "instance-worktree-missing"
        assert str(root / "absent") in error["message"]
        assert (error["project"], error["key"]) == (PROJECT, KEY)

    def test_json_error_honours_pretty(self, root: Path) -> None:
        _, out = run_main("resolve", *self.args(root / "absent", "--pretty"))
        assert out.startswith("{\n  ")

    def test_text_error_is_one_line_on_stderr_naming_the_code(self, root: Path) -> None:
        res = run_cli("resolve", *self.args(root / "absent", "--format", "text"), cwd=root)
        assert res.returncode == 1
        assert res.stdout == ""
        lines = res.stderr.splitlines()
        assert len(lines) == 1
        assert lines[0].startswith("instance-worktree-missing: ")
        assert str(root / "absent") in lines[0]

    def test_a_worktree_that_is_a_file_is_missing(self, root: Path) -> None:
        (root / "file").write_text("x")
        code, out = run_main("resolve", *self.args(root / "file"))
        assert (code, json.loads(out)["error"]) == (1, "instance-worktree-missing")

    def test_missing_project_doc_names_the_project_and_the_path(self, root: Path) -> None:
        code, out = run_main("resolve", *self.args(root))
        error = json.loads(out)
        assert (code, error["error"]) == (1, "missing-project-doc")
        assert f"'{PROJECT}'" in error["message"]
        assert str(root / "system" / "projects" / PROJECT / "project.md") in error["message"]

    def test_a_project_doc_that_is_a_directory_is_missing(self, root: Path) -> None:
        (root / "system" / "projects" / PROJECT / "project.md").mkdir(parents=True)
        code, out = run_main("resolve", *self.args(root))
        assert (code, json.loads(out)["error"]) == (1, "missing-project-doc")

    def test_invalid_target_kind_is_a_json_error_raised_before_any_resolution(
            self, root: Path) -> None:
        code, out = run_main("target", *self.args(root / "absent", "--kind", "bogus"),
                             git=ExplodingGit())
        error = json.loads(out)
        assert (code, error["error"]) == (1, "invalid-target-kind")
        assert "'bogus'" in error["message"]
        assert "code, pipeline, delivery" in error["message"]

    def test_invalid_target_kind_through_the_real_entry_point(self, root: Path) -> None:
        res = run_cli("target", *self.args(root, "--kind", "bogus", "--format", "json"), cwd=root)
        assert res.returncode == 1
        assert json.loads(res.stdout)["error"] == "invalid-target-kind"

    def test_validate_defaults_to_compact_text(
            self, relative_setup: RelativeSetup, root: Path) -> None:
        _, worktree = relative_setup
        res = run_cli("validate", *self.args(worktree), cwd=root)
        assert (res.returncode, res.stdout) == (0, "valid\n")

    def test_validate_prints_json_on_request(self, relative_setup: RelativeSetup) -> None:
        _, worktree = relative_setup
        code, out = run_main("validate", *self.args(worktree, "--format", "json"))
        assert (code, json.loads(out)) == (0, {"status": "valid"})

    def test_resolve_and_target_default_to_json(self, relative_setup: RelativeSetup) -> None:
        _, worktree = relative_setup
        assert json.loads(run_main("resolve", *self.args(worktree))[1])["kind"] == "relative"
        assert "repo" in json.loads(run_main("target", *self.args(worktree, "--kind", "code"))[1])

    def test_an_unforeseen_failure_is_still_a_json_error(
            self, relative_setup: RelativeSetup) -> None:
        _, worktree = relative_setup
        code, out = run_main("resolve", *self.args(worktree), git=BrokenGit())
        error = json.loads(out)
        assert (code, error["error"]) == (1, "unknown")
        assert "RuntimeError" in error["message"] and "boom" in error["message"]
        assert (error["project"], error["key"]) == (PROJECT, KEY)

    def test_missing_product_worktree_says_how_to_create_it(self, root: Path) -> None:
        product = make_repo(root / "product", {"src/app.py": "x\n"})
        instance = make_repo(root / "instance", project_md(str(product)))
        worktree = add_worktree(instance)
        code, out = run_main("validate", *self.args(worktree, "--format", "json"))
        error = json.loads(out)
        assert (code, error["error"]) == (1, "product-worktree-missing")
        assert f"git -C '{product}' worktree add '{product / '.worktrees' / KEY}' '{KEY}'" in \
            error["message"]

    def test_a_worktree_outside_any_repository_says_what_it_must_be(self, root: Path) -> None:
        contract = {"kind": "relative", "key": KEY, "product_path": ".",
                    "instance_worktree": str(root), "instance_repo": str(root)}
        with pytest.raises(ToolError, match="instance-repo-unresolved") as caught:
            validate_contract(contract, Git())
        assert f"must be a git worktree of '{root}'" in caught.value.message


class TestFlagValues:
    """The three required flags become paths and a branch name, so each is checked for a shape
    that cannot reach outside where it is meant to point."""

    def refused(self, capsys: pytest.CaptureFixture[str], *args: str) -> str:
        with pytest.raises(SystemExit) as caught:
            run_main(*args, git=ExplodingGit())
        assert caught.value.code == 2
        return capsys.readouterr().err

    def test_a_relative_worktree_is_refused(self, capsys: pytest.CaptureFixture[str]) -> None:
        err = self.refused(capsys, "resolve", "--worktree", "instance/.worktrees/k",
                           "--project", PROJECT, "--key", KEY)
        assert "--worktree" in err and "'instance/.worktrees/k'" in err and "absolute" in err

    @pytest.mark.parametrize("project", ["", ".", "..", "../other", "a/b", " "])
    def test_a_project_that_is_not_one_plain_name_is_refused(
            self, root: Path, capsys: pytest.CaptureFixture[str], project: str) -> None:
        err = self.refused(capsys, "resolve", "--worktree", str(root), "--project", project,
                           "--key", KEY)
        assert "--project" in err and f"'{project}'" in err

    @pytest.mark.parametrize("key", ["", ".", "..", "a/b", "-x", ".hidden", "a..b", "a b",
                                     "a~1", "a^", "a:b", "a?", "a*", "a[", "a\\b", "x.lock", "x."])
    def test_a_key_that_is_not_one_branch_and_directory_name_is_refused(
            self, root: Path, capsys: pytest.CaptureFixture[str], key: str) -> None:
        err = self.refused(capsys, "resolve", "--worktree", str(root), "--project", PROJECT,
                           f"--key={key}")
        assert "--key" in err and f"'{key}'" in err

    def test_a_trailing_slash_on_the_worktree_is_normalised(
            self, relative_setup: RelativeSetup) -> None:
        _, worktree = relative_setup
        code, out = run_main("resolve", "--worktree", f"{worktree}/", "--project", PROJECT,
                             "--key", KEY)
        assert code == 0
        assert json.loads(out)["instance_worktree"] == str(worktree)


# --- the shipped entry point over real repositories ---------------------------------------------

CONTRACT_KEYS = ["kind", "project", "key", "product_path", "instance_repo", "instance_worktree",
                 "product_repo", "product_worktree", "code_repo", "code_worktree", "pipeline_repo",
                 "pipeline_worktree", "delivery_repos"]


def cli(command: str, worktree: Path, *extra: str, key: str = KEY) -> subprocess.CompletedProcess:
    """One command through the real entry point, run from `/` — no repository at all."""
    return run_cli(command, "--worktree", str(worktree), "--project", PROJECT, "--key", key,
                   *extra, cwd=Path("/"))


class TestCliFixedTopology:
    def test_resolve_prints_the_proposal_shape_with_git_resolved_identities(
            self, fixed_setup: FixedSetup) -> None:
        instance, worktree, product, product_worktree = fixed_setup
        res = cli("resolve", worktree)
        assert res.returncode == 0, res.stderr
        contract = json.loads(res.stdout)
        assert list(contract) == CONTRACT_KEYS
        assert contract == {
            "kind": "fixed", "project": PROJECT, "key": KEY, "product_path": str(product),
            "instance_repo": str(instance), "instance_worktree": str(worktree),
            "product_repo": str(product), "product_worktree": str(product_worktree),
            "code_repo": str(product), "code_worktree": str(product_worktree),
            "pipeline_repo": str(instance), "pipeline_worktree": str(worktree),
            "delivery_repos": ["product", "instance"],
        }

    def test_validate_and_strict_resolve_pass(self, fixed_setup: FixedSetup) -> None:
        _, worktree, _, _ = fixed_setup
        assert (cli("validate", worktree).returncode, cli("validate", worktree).stdout) == \
            (0, "valid\n")
        assert cli("resolve", worktree, "--strict").returncode == 0

    def test_targets_in_json_and_text(self, fixed_setup: FixedSetup) -> None:
        instance, worktree, product, product_worktree = fixed_setup
        assert json.loads(cli("target", worktree, "--kind", "code").stdout) == \
            {"repo": str(product), "worktree": str(product_worktree)}
        assert json.loads(cli("target", worktree, "--kind", "pipeline").stdout) == \
            {"repo": str(instance), "worktree": str(worktree)}
        assert json.loads(cli("target", worktree, "--kind", "delivery").stdout) == \
            {"repos": ["product", "instance"]}
        assert cli("target", worktree, "--kind", "code", "--format", "text").stdout == \
            f"repo={product}\nworktree={product_worktree}\n"
        assert cli("target", worktree, "--kind", "delivery", "--format", "text").stdout == \
            "repos=product,instance\n"

    def test_resolve_text_is_one_key_value_line_per_field(self, fixed_setup: FixedSetup) -> None:
        _, worktree, product, product_worktree = fixed_setup
        lines = cli("resolve", worktree, "--format", "text").stdout.splitlines()
        assert [line.split("=", 1)[0] for line in lines] == CONTRACT_KEYS
        assert "kind=fixed" in lines
        assert f"code_worktree={product_worktree}" in lines
        assert "delivery_repos=product,instance" in lines


class TestCliRelativeTopology:
    def test_resolve_routes_everything_to_the_instance(self, relative_setup: RelativeSetup) -> None:
        instance, worktree = relative_setup
        contract = json.loads(cli("resolve", worktree, "--strict").stdout)
        assert list(contract) == CONTRACT_KEYS
        assert contract["kind"] == "relative"
        assert contract["product_path"] == "products/app"
        for side in ("instance", "product", "code", "pipeline"):
            assert contract[f"{side}_repo"] == str(instance)
            assert contract[f"{side}_worktree"] == str(worktree)
        assert contract["delivery_repos"] == ["instance"]

    def test_validate_passes(self, relative_setup: RelativeSetup) -> None:
        _, worktree = relative_setup
        assert cli("validate", worktree).stdout == "valid\n"


class TestTildeProductPath:
    """A card declaring `~/…` resolves as the absolute path under the home directory, the way the
    chain launcher already reads it (cold read 2026-09-29, D4)."""

    def test_main_expands_against_the_home_it_is_given(self, root: Path) -> None:
        home = root / "home"
        product = make_repo(home / "products" / "thing", {"src/app.py": "x\n"})
        product_worktree = add_worktree(product)
        instance = make_repo(root / "instance", project_md("~/products/thing"))
        worktree = add_worktree(instance)
        code, out = run_main("resolve", "--strict", "--worktree", str(worktree), "--project",
                             PROJECT, "--key", KEY, git=Git(), home=str(home))
        assert code == 0, out
        contract = json.loads(out)
        assert contract["kind"] == "fixed"
        assert contract["product_path"] == str(product)
        assert contract["product_repo"] == str(product)
        assert contract["product_worktree"] == str(product_worktree)
        assert contract["delivery_repos"] == ["product", "instance"]

    def test_the_real_entry_point_reads_home_from_the_environment(self, root: Path) -> None:
        home = root / "home"
        product = make_repo(home / "products" / "thing", {"src/app.py": "x\n"})
        add_worktree(product)
        instance = make_repo(root / "instance", project_md("~/products/thing"))
        worktree = add_worktree(instance)
        res = subprocess.run([sys.executable, TOOL, "resolve", "--strict", "--worktree",
                              str(worktree), "--project", PROJECT, "--key", KEY],
                             capture_output=True, text=True, cwd="/",
                             env={"HOME": str(home), "PATH": "/usr/bin:/bin:/usr/local/bin"})
        assert res.returncode == 0, res.stdout + res.stderr
        assert json.loads(res.stdout)["product_repo"] == str(product)

    def test_a_tilde_path_inside_the_instance_is_one_repo(self, root: Path) -> None:
        home = root / "home"
        instance = make_repo(home / "instance",
                             {**project_md("~/instance/products/app"), "products/app/x": "x\n"})
        worktree = add_worktree(instance)
        code, out = run_main("resolve", "--strict", "--worktree", str(worktree), "--project",
                             PROJECT, "--key", KEY, git=Git(), home=str(home))
        assert code == 0, out
        assert json.loads(out)["kind"] == "relative"


class TestAbsoluteProductPathInsideTheInstance:
    """An absolute `**Product path:**` that names a directory of the instance repository itself is
    one repo, not two: the product has no git repository of its own, so it is `relative`, with the
    instance as its one delivery repo, and `product_path` still echoes the value as declared. The
    cold read of 2026-09-29 (B1) found the tool calling it `fixed`, which sent `tobiishi-seal` down
    the two-repo path while `development-worktree` opened one worktree."""

    @staticmethod
    def setup(root: Path, product: str = "products/app") -> tuple[Path, Path, str]:
        instance_dir = root / "instance"
        declared = str(instance_dir / product) if product else str(instance_dir)
        instance = make_repo(instance_dir, {**project_md(declared), "products/app/README.md": "a\n"})
        return instance, add_worktree(instance), declared

    def test_resolve_is_relative_with_one_delivery_repo(self, root: Path) -> None:
        instance, worktree, declared = self.setup(root)
        contract = resolve_from_paths(str(worktree), PROJECT, KEY, GitRepos(Git()))
        assert contract["kind"] == "relative"
        assert contract["product_path"] == declared
        assert contract["delivery_repos"] == ["instance"]
        for side in ("instance", "product", "code", "pipeline"):
            assert contract[f"{side}_repo"] == str(instance)
            assert contract[f"{side}_worktree"] == str(worktree)

    def test_the_instance_root_itself_is_one_repo(self, root: Path) -> None:
        _, worktree, declared = self.setup(root, product="")
        contract = resolve_from_paths(str(worktree), PROJECT, KEY, GitRepos(Git()))
        assert (contract["kind"], contract["product_path"]) == ("relative", declared)
        validate_contract(contract, Git())

    def test_validate_proves_the_product_in_the_change_worktree(self, root: Path) -> None:
        _, worktree, _ = self.setup(root)
        assert cli("validate", worktree).stdout == "valid\n"
        assert json.loads(cli("resolve", worktree, "--strict").stdout)["kind"] == "relative"

    def test_validate_refuses_a_product_the_change_branch_does_not_carry(self, root: Path) -> None:
        instance, worktree, _ = self.setup(root)
        (instance / "products" / "later").mkdir()
        (instance / "products" / "later" / "README.md").write_text("x\n", encoding="utf-8")
        project_doc = worktree / "system" / "projects" / PROJECT / "project.md"
        project_doc.write_text(f"**Product path:** {instance / 'products' / 'later'}\n",
                               encoding="utf-8")
        res = cli("validate", worktree, "--format", "json")
        assert res.returncode == 1
        assert json.loads(res.stdout)["error"] == "invalid-product-path"

    def test_a_separate_repository_nested_in_the_instance_directory_stays_fixed(
            self, root: Path) -> None:
        instance_dir = root / "instance"
        nested = instance_dir / "vendor" / "product"
        instance = make_repo(instance_dir, project_md(str(nested)))
        make_repo(nested, {"src/app.py": "x\n"})
        worktree = add_worktree(instance)
        contract = resolve_from_paths(str(worktree), PROJECT, KEY, GitRepos(Git()))
        assert contract["kind"] == "fixed"
        assert contract["product_repo"] == str(nested)
        assert contract["delivery_repos"] == ["product", "instance"]

    def test_the_layout_reading_agrees_without_git(self, root: Path) -> None:
        inside = layout(root, str(root / "instance" / "products" / "app"))
        code, out = run_main("resolve", "--worktree", str(inside), "--project", PROJECT,
                             "--key", KEY, "--no-check-git", git=ExplodingGit())
        assert code == 0
        contract = json.loads(out)
        assert (contract["kind"], contract["delivery_repos"]) == ("relative", ["instance"])
        assert contract["code_worktree"] == str(inside)

    def test_a_sibling_sharing_the_instance_prefix_is_not_inside_it(self, root: Path) -> None:
        worktree = layout(root, str(root / "instance-other"))
        code, out = run_main("resolve", "--worktree", str(worktree), "--project", PROJECT,
                             "--key", KEY, "--no-check-git", git=ExplodingGit())
        assert code == 0
        assert json.loads(out)["kind"] == "fixed"


def _scenario(name: str, root: Path) -> tuple[Path, list[str], str]:
    """One failing layout: the worktree to pass, extra CLI arguments, and the error it must give."""
    if name == "missing-project-doc":
        instance = make_repo(root / "instance")
        return add_worktree(instance), ["resolve"], name
    if name == "missing-product-path":
        instance = make_repo(root / "instance", {f"system/projects/{PROJECT}/project.md": "# P\n"})
        return add_worktree(instance), ["resolve"], name
    if name == "invalid-product-path":
        instance = make_repo(root / "instance", project_md("products/app"))
        return add_worktree(instance), ["validate"], name
    if name == "instance-worktree-missing":
        return root / "instance" / ".worktrees" / KEY, ["resolve"], name
    if name == "instance-repo-unresolved":
        return layout(root, "products/app"), ["resolve"], name
    if name == "product-repo-unresolved":
        instance = make_repo(root / "instance", project_md(str(root / "no-such-product")))
        return add_worktree(instance), ["resolve"], name
    if name == "product-worktree-missing":
        product = make_repo(root / "product")
        instance = make_repo(root / "instance", project_md(str(product)))
        return add_worktree(instance), ["resolve", "--strict"], name
    if name == "branch-topology-missing":
        instance = make_repo(root / "instance",
                             {**project_md("products/app"), "products/app/a.py": "x\n"})
        worktree = add_worktree(instance)
        git(worktree, "checkout", "-q", "-b", "not-the-key")
        return worktree, ["validate"], name
    assert name == "invalid-target-kind"
    instance = make_repo(root / "instance", project_md("products/app"))
    return add_worktree(instance), ["target", "--kind", "everything"], name


FAILURE_CODES = ["missing-project-doc", "missing-product-path", "invalid-product-path",
                 "instance-worktree-missing", "instance-repo-unresolved", "product-repo-unresolved",
                 "product-worktree-missing", "branch-topology-missing", "invalid-target-kind"]


class TestCliFailureContract:
    """Every code in the proposal's failure contract, through the real entry point, in both
    formats: exit nonzero, structured JSON on stdout, or one line on stderr."""

    @pytest.mark.parametrize("name", FAILURE_CODES)
    def test_json(self, root: Path, name: str) -> None:
        worktree, command, expected = _scenario(name, root)
        res = cli(command[0], worktree, *command[1:], "--format", "json")
        assert res.returncode == 1, res.stdout + res.stderr
        error = json.loads(res.stdout)
        assert error["error"] == expected
        assert error["message"]
        assert (error["project"], error["key"]) == (PROJECT, KEY)
        assert res.stderr == ""

    @pytest.mark.parametrize("name", FAILURE_CODES)
    def test_text(self, root: Path, name: str) -> None:
        worktree, command, expected = _scenario(name, root)
        res = cli(command[0], worktree, *command[1:], "--format", "text")
        assert res.returncode == 1
        assert res.stdout == ""
        assert len(res.stderr.splitlines()) == 1
        assert res.stderr.startswith(f"{expected}: ")

    def test_the_proposal_list_is_every_code_the_tool_can_raise(self) -> None:
        """A new code needs a proposal change first; `unknown` is the one catch-all."""
        source = Path(development_path.__file__).read_text(encoding="utf-8")
        raised = set(re.findall(r'ToolError\(\s*f?"([a-z{}-]+)"', source))
        expanded = {code.replace("{side}", side) for code in raised
                    for side in ("instance", "product")}
        assert expanded - {"unknown"} <= set(FAILURE_CODES)

    def test_wrong_key_for_a_fixed_product_is_refused(
            self, fixed_setup: FixedSetup, root: Path) -> None:
        _, worktree, _, _ = fixed_setup
        other = "2026-09-29_other-change"
        res = cli("validate", worktree, "--format", "json", key=other)
        assert json.loads(res.stdout)["error"] == "branch-topology-missing"


class TestProductInsideGitMetadata:
    def test_the_git_directory_is_not_a_product(self, root: Path) -> None:
        instance = make_repo(root / "instance", project_md(".git"))
        contract = resolve_from_paths(str(instance), PROJECT, "main", GitRepos(Git()))
        with pytest.raises(ToolError, match="invalid-product-path") as caught:
            validate_contract(contract, Git())
        assert "None" not in caught.value.message
        assert "outside the working tree" in caught.value.message

    def test_another_worktree_inside_the_instance_is_not_its_product(self, root: Path) -> None:
        instance = make_repo(root / "instance", project_md(f".worktrees/{KEY}"))
        linked = add_worktree(instance)
        contract = resolve_from_paths(str(instance), PROJECT, "main", GitRepos(Git()))
        with pytest.raises(ToolError, match="invalid-product-path") as caught:
            validate_contract(contract, Git())
        assert str(linked) in caught.value.message
