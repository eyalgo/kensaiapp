"""Tests for `create_change_worktree.py`.

Every case builds real git repositories in `tmp_path` and drives `main()` with a collaborator handed
in, so what is asserted is what git and the filesystem hold afterwards. Nothing here patches the
module under test. A refusal is judged by a snapshot of the three things a run could change in a
repository — its branch list, its worktree list and its `info/exclude` bytes — taken
independently of the tool's own snapshot code.
"""

from __future__ import annotations

import ast
import io
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

import create_change_worktree
import development_path
from create_change_worktree import WorktreeGit, main, resolve_topology

KEY = "2026-10-01_example-change"
PROJECT = "proj"


# --- fixture repositories -----------------------------------------------------------------------


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


def project_md(product_path: str) -> dict[str, str]:
    return {f"system/projects/{PROJECT}/project.md":
            f"# Project\n\n**Product path:** {product_path}   <!-- note -->\n"}


def snapshot(repo: Path) -> tuple[str, str, bytes | None]:
    """What a run could change in `repo`: branches, worktrees, and the exclude file's bytes."""
    exclude = repo / ".git" / "info" / "exclude"
    return (git(repo, "branch", "--list"), git(repo, "worktree", "list", "--porcelain"),
            exclude.read_bytes() if exclude.exists() else None)


@pytest.fixture
def root(tmp_path: Path) -> Path:
    """`tmp_path` with symlinks resolved, so it compares equal to the paths git reports."""
    return tmp_path.resolve()


@pytest.fixture
def instance(root: Path) -> Path:
    """An instance repo whose product is `products/app` inside it (a `relative` project)."""
    return make_repo(root / "instance",
                     {**project_md("products/app"), "products/app/README.md": "app\n"})


def run(root: Path, *flags: str, collaborator: WorktreeGit | None = None
        ) -> tuple[int, dict]:
    """The command, through `main()`: its exit code and the one JSON object it printed."""
    out = io.StringIO()
    code = main(list(flags), git=collaborator if collaborator is not None else WorktreeGit(),
                stdout=out, home=str(root))
    return code, json.loads(out.getvalue())


def create(root: Path, instance_path: Path | str, *, project: str = PROJECT, key: str = KEY,
           collaborator: WorktreeGit | None = None) -> tuple[int, dict]:
    return run(root, "--instance", str(instance_path), "--project", project, "--key", key,
               collaborator=collaborator)


# --- the command line and the first refusals (task 1) -------------------------------------------


def test_version_flag_prints_version(capsys):
    with pytest.raises(SystemExit) as exit_info:
        main(["--version"])
    assert exit_info.value.code == 0
    assert capsys.readouterr().out.strip() == create_change_worktree.__version__


def test_missing_key_exits_two_with_usage(capsys):
    with pytest.raises(SystemExit) as exit_info:
        main(["--instance", "/nowhere", "--project", PROJECT])
    assert exit_info.value.code == 2
    assert "usage:" in capsys.readouterr().err


def test_invalid_change_key_is_a_json_refusal(root: Path, instance: Path):
    before = snapshot(instance)

    code, report = create(root, instance, key="../x")

    assert code == 1
    assert report["status"] == "failed"
    assert report["error"] == "invalid-change-key"
    assert report["changed"] is False
    assert report["repos"] is None
    assert snapshot(instance) == before


def test_invalid_project_name_is_a_json_refusal(root: Path, instance: Path):
    before = snapshot(instance)

    code, report = create(root, instance, project="a/b")

    assert code == 1
    assert report["error"] == "invalid-project-name"
    assert report["changed"] is False
    assert report["repos"] is None
    assert snapshot(instance) == before


def test_missing_product_directory_reports_path_tool_code(root: Path):
    instance = make_repo(root / "instance", project_md(str(root / "no-such-product")))
    before = snapshot(instance)

    code, report = create(root, instance)

    assert code == 1
    assert report["error"] == "product-repo-unresolved"
    assert report["changed"] is False
    assert report["repos"] is None
    assert snapshot(instance) == before


def test_unknown_project_reports_path_tool_code(root: Path, instance: Path):
    code, report = create(root, instance, project="no-such-project")

    assert code == 1
    assert report["error"] == "missing-project-doc"
    assert report["changed"] is False
    assert report["repos"] is None


@pytest.mark.parametrize("where", ["outside-any-repository", "path-that-does-not-exist"])
def test_unresolvable_instance_reports_instance_repo_unresolved(root: Path, where: str):
    location = root / "plain-folder"
    location.mkdir()
    instance_path = location if where == "outside-any-repository" else location / "missing"

    code, report = create(root, instance_path)

    assert code == 1
    assert report["error"] == "instance-repo-unresolved"
    assert report["changed"] is False
    assert report["repos"] is None


def test_unforeseen_exception_is_json_unknown(root: Path, instance: Path):
    class ExplodingGit(WorktreeGit):
        def main_worktree(self, path: str) -> str | None:
            raise RuntimeError("boom")

    code, report = create(root, instance, collaborator=ExplodingGit())

    assert code == 1
    assert report["status"] == "failed"
    assert report["error"] == "unknown"
    assert "boom" in report["message"]


def test_instance_may_be_any_path_inside_the_repository(root: Path, instance: Path):
    (instance / "products").mkdir(exist_ok=True)

    topology = resolve_topology(str(instance / "products"), PROJECT, KEY, WorktreeGit(), str(root))

    assert [(target.role, target.repo) for target in topology.targets] == [
        ("instance", str(instance))]
    assert topology.targets[0].worktree == str(instance / ".worktrees" / KEY)


def test_pretty_prints_one_json_object(root: Path, instance: Path, capsys):
    main(["--instance", str(instance), "--project", PROJECT, "--key", "../x", "--pretty"],
         git=WorktreeGit(), home=str(root))

    printed = capsys.readouterr().out
    assert json.loads(printed)["error"] == "invalid-change-key"
    assert printed.count("\n") > 1


# --- preflight: refusals that leave every repository as it was (task 2) -------------------------


@pytest.fixture
def fixed(root: Path) -> tuple[Path, Path]:
    """An instance repo and the separate product repo its project declares (a `fixed` project)."""
    product = make_repo(root / "product", {"src/app.py": "print('app')\n"})
    instance = make_repo(root / "instance", project_md(str(product)))
    return instance, product


def refused(root: Path, instance: Path, error: str, *others: Path,
            key: str = KEY) -> dict:
    """Run the command and require the refusal `error`, with every repository as it was."""
    before = [snapshot(repo) for repo in (instance, *others)]

    code, report = create(root, instance, key=key)

    assert (code, report["status"], report["error"]) == (1, "failed", error)
    assert report["changed"] is False
    assert [snapshot(repo) for repo in (instance, *others)] == before
    return report


def state(report: dict, role: str) -> dict:
    return next(entry for entry in report["repos"] if entry["role"] == role)


def test_branch_exists_in_instance_is_refused_unchanged(root: Path, instance: Path):
    git(instance, "branch", KEY)

    report = refused(root, instance, "branch-exists")

    assert state(report, "instance")["branch_exists"] is True
    assert state(report, "instance")["worktree_exists"] is False


def test_branch_only_in_product_refuses_before_any_instance_change(
        root: Path, fixed: tuple[Path, Path]):
    instance, product = fixed
    git(product, "branch", KEY)

    report = refused(root, instance, "branch-exists", product)

    assert git(instance, "branch", "--list", KEY) == ""
    assert not (instance / ".git" / "info" / "exclude").read_text().count(".worktrees")
    assert state(report, "instance")["branch_exists"] is False
    assert state(report, "product")["branch_exists"] is True


def occupy_with_directory(path: Path) -> None:
    path.mkdir(parents=True)


def occupy_with_file(path: Path) -> None:
    path.parent.mkdir(parents=True)
    path.write_text("not a worktree\n")


def occupy_with_symlink(path: Path) -> None:
    path.parent.mkdir(parents=True)
    path.symlink_to(path.parent.parent)


def occupy_with_broken_symlink(path: Path) -> None:
    path.parent.mkdir(parents=True)
    path.symlink_to(path.parent / "nowhere")


@pytest.mark.parametrize("occupy", [occupy_with_directory, occupy_with_file,
                                    occupy_with_symlink, occupy_with_broken_symlink])
def test_occupied_worktree_path_is_refused(root: Path, instance: Path, occupy):
    occupy(instance / ".worktrees" / KEY)

    report = refused(root, instance, "worktree-exists")

    assert state(report, "instance")["worktree_exists"] is True
    assert state(report, "instance")["branch_exists"] is False


def test_registered_worktree_with_missing_directory_is_refused(
        root: Path, fixed: tuple[Path, Path]):
    instance, product = fixed
    detached = product / ".worktrees" / KEY
    git(product, "worktree", "add", "-q", "--detach", str(detached))
    shutil.rmtree(detached)

    report = refused(root, instance, "worktree-exists", product)

    assert state(report, "product")["worktree_exists"] is True
    assert state(report, "instance")["worktree_exists"] is False


def test_repo_without_a_commit_is_refused(root: Path):
    unborn = root / "instance"
    unborn.mkdir()
    git(unborn, "init", "-q", "-b", "main")
    for name, text in project_md("products/app").items():
        (unborn / name).parent.mkdir(parents=True, exist_ok=True)
        (unborn / name).write_text(text)

    refused(root, unborn, "head-unborn")


def test_invalid_branch_name_refuses_before_any_change(root: Path, instance: Path):
    # The path tool's key check lets `@{` through; git refuses it as a ref name.
    refused(root, instance, "invalid-branch-name", key="a@{b")


def test_worktrees_path_that_is_a_file_is_refused(root: Path, instance: Path):
    (instance / ".worktrees").write_text("a file where the folder belongs\n")

    refused(root, instance, "worktrees-dir-blocked")


@pytest.mark.skipif(os.geteuid() == 0, reason="root can write an unwritable file")
def test_unwritable_exclude_is_refused(root: Path, instance: Path):
    exclude = instance / ".git" / "info" / "exclude"
    exclude.chmod(0o444)
    try:
        refused(root, instance, "exclude-unwritable")
    finally:
        exclude.chmod(0o644)


def test_relative_product_untracked_at_head_is_refused(root: Path):
    instance = make_repo(root / "instance", project_md("products/app"))
    (instance / "products" / "app").mkdir(parents=True)

    refused(root, instance, "product-path-not-at-head")


def test_absolute_product_path_inside_the_instance_is_one_repository(root: Path):
    """An absolute `Product path:` naming a directory of the instance is `relative`: one
    repository, checked at `HEAD`, and the branch is later cut from the commit captured here."""
    inside = root / "inside"
    inside.mkdir()
    files = {**project_md(str(inside / "products" / "app")), "products/app/README.md": "app\n"}
    make_repo(inside, files)
    topology = resolve_topology(str(inside), PROJECT, KEY, WorktreeGit(), str(root))

    plans = create_change_worktree.preflight(topology, WorktreeGit())

    assert topology.contract["kind"] == "relative"
    assert [plan.target.role for plan in plans] == ["instance"]
    assert plans[0].commit == git(inside, "rev-parse", "HEAD")


def test_refusal_names_what_failed_and_the_action(root: Path, instance: Path):
    git(instance, "branch", KEY)
    branch_message = create(root, instance)[1]["message"]
    git(instance, "branch", "-q", "-D", KEY)
    (instance / ".worktrees" / KEY).mkdir(parents=True)
    path_message = create(root, instance)[1]["message"]

    actions = ("delete", "remove", "choose", "pick", "pass", "commit", "create", "make", "fix")
    path_fault = str(instance / ".worktrees" / KEY)
    for message, fault in ((branch_message, KEY), (path_message, path_fault)):
        assert str(instance) in message
        assert fault in message
        assert any(action in message for action in actions), message


# --- create, exclude and confirm: the success path (task 3) -------------------------------------


def listing(repo: Path) -> dict[str, str | None]:
    """`git worktree list --porcelain` as `{worktree path: branch name or None}`."""
    entries: dict[str, str | None] = {}
    path = ""
    for line in git(repo, "worktree", "list", "--porcelain").splitlines():
        if line.startswith("worktree "):
            path = line[len("worktree "):]
            entries[path] = None
        elif line.startswith("branch refs/heads/"):
            entries[path] = line[len("branch refs/heads/"):]
    return entries


def assert_created(entry: dict, repo: Path, role: str, key: str = KEY) -> None:
    """One `repos` entry equals what git itself says about `repo`."""
    worktree = str(repo / ".worktrees" / key)
    assert entry == {"role": role, "repo": str(repo), "branch": key, "worktree": worktree}
    assert listing(repo)[worktree] == key
    assert git(repo, "branch", "--list", key).lstrip("+* ") == key
    assert git(repo, "rev-parse", key) == git(repo, "rev-parse", "main")


def test_relative_success_reports_git_identities(root: Path, instance: Path):
    code, report = create(root, instance)

    assert code == 0
    assert (report["status"], report["kind"], report["project"], report["key"]) == (
        "created", "relative", PROJECT, KEY)
    assert len(report["repos"]) == 1
    assert_created(report["repos"][0], instance, "instance")
    assert WorktreeGit().exclude_matches(str(instance), KEY)


def test_fixed_success_creates_both_pairs(root: Path, fixed: tuple[Path, Path]):
    instance, product = fixed

    code, report = create(root, instance)

    assert code == 0
    assert report["kind"] == "fixed"
    assert [entry["role"] for entry in report["repos"]] == ["instance", "product"]
    assert_created(report["repos"][0], instance, "instance")
    assert_created(report["repos"][1], product, "product")
    assert WorktreeGit().exclude_matches(str(product), KEY)


def test_branch_is_cut_from_main_worktree_head_not_the_linked_worktree(
        root: Path, instance: Path):
    other = instance / ".worktrees" / "other"
    git(instance, "worktree", "add", "-q", "-b", "other", str(other))
    (other / "elsewhere.txt").write_text("a commit the main working tree does not have\n")
    git(other, "add", "-A")
    git(other, "commit", "-q", "-m", "elsewhere")

    code, report = create(root, other)

    assert code == 0
    assert git(instance, "rev-parse", KEY) == git(instance, "rev-parse", "HEAD")
    assert git(instance, "rev-parse", KEY) != git(other, "rev-parse", "HEAD")
    assert report["repos"][0]["repo"] == str(instance)


def test_symlinked_instance_path_reports_git_strings(root: Path, instance: Path):
    link = root / "via-link"
    link.symlink_to(instance)

    code, report = create(root, link)

    assert code == 0
    entry = report["repos"][0]
    assert entry["repo"] == str(instance)
    assert entry["worktree"] in listing(instance)


@pytest.mark.parametrize("pattern", [".worktrees/", "/.worktrees/", ".worktrees/*", "*"])
def test_matching_exclude_line_stays_byte_identical(root: Path, instance: Path, pattern: str):
    exclude = instance / ".git" / "info" / "exclude"
    exclude.write_bytes(f"# local\n{pattern}\n".encode())
    before = exclude.read_bytes()

    code, _ = create(root, instance)

    assert code == 0
    assert exclude.read_bytes() == before


def test_missing_exclude_file_is_created_with_one_matching_line(
        root: Path, fixed: tuple[Path, Path]):
    instance, product = fixed
    shutil.rmtree(product / ".git" / "info")

    code, _ = create(root, instance)

    exclude = product / ".git" / "info" / "exclude"
    assert code == 0
    assert exclude.read_text().splitlines() == [".worktrees/"]
    assert WorktreeGit().exclude_matches(str(product), KEY)


def test_exclude_without_final_newline_gets_exactly_one_new_line(root: Path, instance: Path):
    exclude = instance / ".git" / "info" / "exclude"
    exclude.write_bytes(b"# kept\n*.log")

    code, _ = create(root, instance)

    assert code == 0
    assert exclude.read_bytes() == b"# kept\n*.log\n.worktrees/\n"


def test_second_key_does_not_append_a_second_line(root: Path, instance: Path):
    create(root, instance)
    exclude = instance / ".git" / "info" / "exclude"
    after_first = exclude.read_bytes()

    code, _ = create(root, instance, key="2026-10-01_another-change")

    assert code == 0
    assert exclude.read_bytes() == after_first


def test_success_validates_with_development_path(root: Path, instance: Path):
    _, report = create(root, instance)
    out = io.StringIO()

    code = development_path.main(
        ["validate", "--worktree", report["repos"][0]["worktree"], "--project", PROJECT,
         "--key", KEY], stdout=out, home=str(root))

    assert (code, out.getvalue().strip()) == (0, "valid")


def test_second_run_for_the_same_key_is_refused(root: Path, instance: Path):
    create(root, instance)
    before = snapshot(instance)

    code, report = create(root, instance)

    assert (code, report["error"]) == (1, "branch-exists")
    assert report["changed"] is False
    assert snapshot(instance) == before
    assert state(report, "instance")["worktree_exists"] is True


@pytest.mark.parametrize("writes_before_failing", [False, True])
def test_exclude_write_failure_reports_exclude_write_failed(
        root: Path, instance: Path, writes_before_failing: bool):
    class FailingExclude(WorktreeGit):
        def append_exclude_line(self, repo: str) -> None:
            if writes_before_failing:
                super().append_exclude_line(repo)
            raise OSError("disk full")

    before = snapshot(instance)

    code, report = create(root, instance, collaborator=FailingExclude())

    assert (code, report["error"]) == (1, "exclude-write-failed")
    assert report["changed"] is (snapshot(instance) != before)
    assert report["changed"] is writes_before_failing
    assert state(report, "instance")["worktree_exists"] is False


def test_branch_is_cut_from_the_commit_preflight_saw_not_a_moved_head(root: Path, instance: Path):
    class MovesHead(WorktreeGit):
        """Commits to the main working tree between preflight and `worktree add`."""

        def append_exclude_line(self, repo: str) -> None:
            super().append_exclude_line(repo)
            (Path(repo) / "late.txt").write_text("arrived mid-run\n")
            git(Path(repo), "add", "late.txt")
            git(Path(repo), "commit", "-q", "-m", "late")

    seen = git(instance, "rev-parse", "HEAD")

    code, _ = create(root, instance, collaborator=MovesHead())

    assert code == 0
    assert git(instance, "rev-parse", KEY) == seen
    assert git(instance, "rev-parse", "HEAD") != seen


# --- failure after a change: the report is what the repositories hold (task 4) ------------------


class FailsAdd(WorktreeGit):
    """The real collaborator, except that `worktree add` fails in one repository — optionally
    after leaving the branch behind, the way a `worktree add -b` that dies partway can."""

    def __init__(self, failing_repo: Path, *, leaves_branch: bool = False) -> None:
        self.failing_repo = str(failing_repo)
        self.leaves_branch = leaves_branch

    def add_worktree(self, repo: str, worktree: str, key: str, commit: str) -> None:
        if repo != self.failing_repo:
            return super().add_worktree(repo, worktree, key, commit)
        if self.leaves_branch:
            git(Path(repo), "branch", key, commit)
        raise OSError("injected: worktree add failed")


class RefusesConfirm(WorktreeGit):
    """The real collaborator, except that confirm finds the new worktree on the wrong branch."""

    def branch(self, path: str) -> str | None:
        return "some-other-branch"


def fresh_state(repo: Path, role: str) -> dict:
    """What `repos[]` must say about `repo`, read from git now."""
    worktree = repo / ".worktrees" / KEY
    return {"role": role, "repo": str(repo),
            "worktree": next((path for path in listing(repo) if path.endswith(f"/{KEY}")),
                             str(worktree)),
            "branch_exists": git(repo, "branch", "--list", KEY) != "",
            "worktree_exists": worktree.exists() or str(worktree) in listing(repo)}


def test_product_add_failure_reports_actual_state(root: Path, fixed: tuple[Path, Path]):
    instance, product = fixed

    code, report = create(root, instance, collaborator=FailsAdd(product))

    assert (code, report["error"]) == (1, "worktree-add-failed")
    assert report["changed"] is True
    assert state(report, "instance") == fresh_state(instance, "instance")
    assert state(report, "product") == fresh_state(product, "product")
    assert state(report, "instance")["branch_exists"] is True
    assert state(report, "instance")["worktree_exists"] is True
    assert state(report, "product")["branch_exists"] is False
    assert state(report, "product")["worktree_exists"] is False
    assert str(instance / ".worktrees" / KEY) in listing(instance)


def test_failed_add_that_created_the_branch_reports_branch_exists(root: Path, instance: Path):
    (instance / ".git" / "info" / "exclude").write_text(".worktrees/\n")

    code, report = create(root, instance, collaborator=FailsAdd(instance, leaves_branch=True))

    assert (code, report["error"]) == (1, "worktree-add-failed")
    assert report["changed"] is True
    assert state(report, "instance")["branch_exists"] is True
    assert state(report, "instance")["worktree_exists"] is False


def test_confirm_refusal_is_a_failure_after_a_change(root: Path, instance: Path):
    code, report = create(root, instance, collaborator=RefusesConfirm())

    assert (code, report["error"]) == (1, "branch-topology-missing")
    assert report["changed"] is True
    assert state(report, "instance") == fresh_state(instance, "instance")


@pytest.mark.parametrize("scenario", ["product-add-fails", "add-leaves-branch", "confirm-refuses"])
def test_nothing_created_is_removed_on_failure(root: Path, fixed: tuple[Path, Path],
                                               scenario: str):
    instance, product = fixed
    collaborator = {"product-add-fails": FailsAdd(product),
                    "add-leaves-branch": FailsAdd(product, leaves_branch=True),
                    "confirm-refuses": RefusesConfirm()}[scenario]

    code, _ = create(root, instance, collaborator=collaborator)

    assert code == 1
    assert git(instance, "branch", "--list", KEY) != ""
    assert str(instance / ".worktrees" / KEY) in listing(instance)
    assert (instance / ".worktrees" / KEY).is_dir()
    assert (git(product, "branch", "--list", KEY) != "") is (scenario != "product-add-fails")


# --- development_path.py stays resolve-and-validate only (task 5, CP-208) ------------------------

DEVELOPMENT_PATH = Path(__file__).resolve().parent / "development_path.py"

# Git words that make or move a branch or a worktree, or change the index or a ref.
GIT_WRITING_WORDS = {"add", "checkout", "switch", "reset", "update-ref", "commit", "merge",
                     "branch", "mv", "rm", "prune", "repair", "move", "remove", "init", "clone"}
FILE_WRITING_CALLS = {"write_text", "write_bytes", "mkdir", "touch", "unlink", "rmdir", "rename",
                      "replace", "makedirs", "remove", "rmtree", "symlink_to", "chmod"}


def writes_found_in(source: str) -> list[str]:
    """Every site in `source` that names a git verb which writes, or writes a file."""
    found = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Constant) and node.value in GIT_WRITING_WORDS:
            found.append(f"git word {node.value!r} at line {node.lineno}")
        if isinstance(node, ast.Call):
            callee = node.func
            name = callee.attr if isinstance(callee, ast.Attribute) else getattr(callee, "id", "")
            if name in FILE_WRITING_CALLS:
                found.append(f"{name}() at line {node.lineno}")
            if name == "open":
                mode = node.args[1] if len(node.args) > 1 else next(
                    (keyword.value for keyword in node.keywords if keyword.arg == "mode"), None)
                if isinstance(mode, ast.Constant) and set("wax+") & set(str(mode.value)):
                    found.append(f"open() for writing at line {node.lineno}")
    return found


def test_the_guard_sees_a_writing_source():
    offending = ('import subprocess\n'
                 'subprocess.run(["git", "worktree", "add", "-b", "k", "p"])\n'
                 'open("f", "w")\nPath("x").write_text("y")\n')

    assert len(writes_found_in(offending)) == 3


def test_development_path_source_never_writes():
    assert writes_found_in(DEVELOPMENT_PATH.read_text(encoding="utf-8")) == []


# --- integrity: detectable blockers and exclude isolation (CP-201, CP-202, CP-203) --------------


@pytest.mark.parametrize("kind", ["relative", "fixed"])
@pytest.mark.parametrize("packed", [False, True])
def test_branch_namespace_conflict_refuses_before_any_change(root, kind, packed):
    product = make_repo(root / "product", {"README.md": "product\n"})
    instance = make_repo(root / "instance", {
        **project_md(str(product) if kind == "fixed" else "products/app"),
        "products/app/README.md": "app\n"})
    blocked = product if kind == "fixed" else instance
    git(blocked, "branch", f"{KEY}/existing")
    if packed:
        git(blocked, "pack-refs", "--all", "--prune")
    repos = (instance, product) if kind == "fixed" else (instance,)
    before = [snapshot(repo) for repo in repos]

    code, report = create(root, instance)

    assert code == 1
    assert report["changed"] is False
    assert [snapshot(repo) for repo in repos] == before
    assert str(blocked) in report["message"]
    assert f"{KEY}/existing" in report["message"]
    assert all(entry["branch_exists"] is False for entry in report["repos"])
    assert all(entry["worktree_exists"] is False for entry in report["repos"])


@pytest.mark.skipif(os.geteuid() == 0, reason="root can write an unwritable directory")
@pytest.mark.parametrize("parent_exists", [False, True])
def test_unwritable_product_worktree_parent_refuses_before_instance_changes(
        root, fixed, parent_exists):
    instance, product = fixed
    parent = product / ".worktrees" if parent_exists else product
    parent.mkdir(exist_ok=True)
    before = [snapshot(repo) for repo in fixed]
    parent.chmod(0o555)
    try:
        code, report = create(root, instance)
    finally:
        parent.chmod(0o755)

    assert code == 1
    assert report["changed"] is False
    assert [snapshot(repo) for repo in fixed] == before
    assert str(parent) in report["message"]
    assert all(entry["branch_exists"] is False for entry in report["repos"])
    assert all(entry["worktree_exists"] is False for entry in report["repos"])


@pytest.mark.parametrize("source", ["tracked", "global", "negated-local"])
def test_only_effective_local_exclude_can_suppress_append(root, instance, source):
    exclude = instance / ".git" / "info" / "exclude"
    exclude.write_text("# retained\n")
    if source == "tracked":
        (instance / ".gitignore").write_text(".worktrees/\n")
        git(instance, "add", ".gitignore")
        git(instance, "commit", "-q", "-m", "ignore")
    elif source == "global":
        global_exclude = root / "global-ignore"
        global_exclude.write_text(".worktrees/\n")
        git(instance, "config", "core.excludesFile", str(global_exclude))
    else:
        exclude.write_text("# retained\n.worktrees/*\n!.worktrees/*\n")
    before = exclude.read_bytes()

    code, _ = create(root, instance)

    assert code == 0
    assert exclude.read_bytes() == before + b".worktrees/\n"


def test_fixed_success_validates_with_development_path(root, fixed):
    instance, _ = fixed
    code, report = create(root, instance)
    assert code == 0
    out = io.StringIO()

    validated = development_path.main(
        ["validate", "--worktree", report["repos"][0]["worktree"], "--project", PROJECT,
         "--key", KEY], stdout=out, home=str(root))

    assert (validated, out.getvalue().strip()) == (0, "valid")


# --- the setup phase (CP-474 to CP-478) ----------------------------------------------------------


def card(product_path: str, *, setup: str | None = None, test: str | None = None
         ) -> dict[str, str]:
    """A project card declaring the product, and the `Setup command:` and `Test command:` lines
    when given. A value is written exactly as the card would hold it, comment and all."""
    lines = [f"**Product path:** {product_path}   <!-- note -->"]
    if test is not None:
        lines.append(f"**Test command:** {test}")
    if setup is not None:
        lines.append(f"**Setup command:** {setup}")
    return {f"system/projects/{PROJECT}/project.md": "# Project\n\n" + "\n".join(lines) + "\n"}


def carded_instance(root: Path, *, setup: str | None = None, test: str | None = None) -> Path:
    """An instance whose product is `prod` inside it, with the card lines given."""
    return make_repo(root / "instance", {**card("prod", setup=setup, test=test),
                                         "prod/README.md": "prod\n"})


def carded_fixed(root: Path, *, setup: str | None = None, test: str | None = None
                 ) -> tuple[Path, Path]:
    product = make_repo(root / "product", {"src/app.py": "print('app')\n"})
    instance = make_repo(root / "instance", card(str(product), setup=setup, test=test))
    return instance, product


def test_setup_runs_in_the_in_repo_product_directory(root: Path):
    instance = carded_instance(root, setup="touch marker")

    code, report = create(root, instance)

    worktree = instance / ".worktrees" / KEY
    assert (code, report["status"]) == (0, "created")
    assert (worktree / "prod" / "marker").exists()
    assert not (worktree / "marker").exists()


def test_setup_runs_in_the_external_product_worktree(root: Path):
    instance, product = carded_fixed(root, setup="touch marker")

    code, report = create(root, instance)

    assert (code, report["status"]) == (0, "created")
    assert (product / ".worktrees" / KEY / "marker").exists()
    assert not (instance / ".worktrees" / KEY / "marker").exists()


@pytest.mark.parametrize("setup", [None, "", "none", "none   <!-- nothing to run -->"])
def test_no_setup_runs_nothing_and_reports_as_before(root: Path, setup: str | None):
    baseline = carded_instance(root / "baseline")
    code_before, before = create(root / "baseline", baseline)
    instance = carded_instance(root / "run", setup=setup)

    code, report = create(root / "run", instance)

    assert (code_before, code) == (0, 0)
    assert report.keys() == before.keys()
    for field in ("status", "project", "key", "kind"):
        assert report[field] == before[field]
    assert [(entry["role"], entry["branch"]) for entry in report["repos"]] == [
        (entry["role"], entry["branch"]) for entry in before["repos"]]
    assert all(entry.keys() == before["repos"][0].keys() for entry in report["repos"])
    assert sorted(path.name for path in (instance / ".worktrees" / KEY / "prod").iterdir()) == [
        "README.md"]


def test_trailing_comment_is_not_part_of_the_setup_command(root: Path):
    instance = carded_instance(root, setup="touch marker   <!-- note -->")

    code, _ = create(root, instance)

    product = instance / ".worktrees" / KEY / "prod"
    assert code == 0
    assert (product / "marker").exists()
    assert not [path for path in product.iterdir() if path.name.startswith("<!--")]


def test_setup_output_does_not_reach_stdout(root: Path, capfd):
    instance = carded_instance(root, setup="echo to-out; echo to-err >&2")
    out = io.StringIO()

    code = main(["--instance", str(instance), "--project", PROJECT, "--key", KEY],
                git=WorktreeGit(), stdout=out, home=str(root))

    captured = capfd.readouterr()
    assert code == 0
    assert isinstance(json.loads(out.getvalue()), dict)
    assert "to-out" not in out.getvalue() + captured.out


def test_failing_setup_is_refused_setup_failed(root: Path):
    instance = carded_instance(root, setup="exit 3")

    code, report = create(root, instance)

    product_directory = str(instance / ".worktrees" / KEY / "prod")
    assert (code, report["status"], report["error"]) == (1, "failed", "setup-failed")
    assert report["changed"] is True
    assert all(entry["branch_exists"] is True and entry["worktree_exists"] is True
               for entry in report["repos"])
    assert "exit 3" in report["message"]
    assert product_directory in report["message"]
    assert "status 3" in report["message"]


def test_setup_failure_message_carries_its_error_output(root: Path):
    _, with_error = create(root / "a", carded_instance(root / "a", setup="echo boom >&2; exit 1"))
    _, with_output = create(root / "b",
                            carded_instance(root / "b", setup="echo only-out; exit 1"))

    assert "boom" in with_error["message"]
    assert "only-out" in with_output["message"]
    assert "only-out" not in with_error["message"]


def test_setup_that_cannot_start_is_setup_failed(root: Path):
    instance = carded_instance(root, setup="/nonexistent/executable --flag")

    code, report = create(root, instance)

    assert (code, report["error"]) == (1, "setup-failed")


def test_setup_failure_removes_nothing(root: Path):
    instance, product = carded_fixed(root, setup="exit 1")

    code, report = create(root, instance)

    assert (code, report["error"]) == (1, "setup-failed")
    for repo in (instance, product):
        assert git(repo, "branch", "--list", KEY) != ""
        assert str(repo / ".worktrees" / KEY) in listing(repo)


def test_setup_does_not_run_when_confirm_refuses(root: Path):
    instance = carded_instance(root, setup="touch marker")

    code, report = create(root, instance, collaborator=RefusesConfirm())

    assert (code, report["error"]) == (1, "branch-topology-missing")
    assert not (instance / ".worktrees" / KEY / "prod" / "marker").exists()


class StartFails(create_change_worktree.ShellRunner):
    """The real collaborator, except that the operating system cannot start the command."""

    def run(self, command: str, directory: str):
        raise OSError("injected: cannot start")


def test_setup_the_system_cannot_start_names_the_system_reason(root: Path):
    instance = carded_instance(root, setup="touch marker")
    out = io.StringIO()

    code = main(["--instance", str(instance), "--project", PROJECT, "--key", KEY],
                git=WorktreeGit(), runner=StartFails(), stdout=out, home=str(root))

    report = json.loads(out.getvalue())
    assert (code, report["error"]) == (1, "setup-failed")
    assert "could not be started" in report["message"]
    assert "injected: cannot start" in report["message"]
    assert "\n" not in report["message"]


def test_setup_stopped_by_a_signal_is_not_reported_as_an_exit_status(root: Path):
    instance = carded_instance(root, setup="kill -9 $$")

    code, report = create(root, instance)

    assert (code, report["error"]) == (1, "setup-failed")
    assert "stopped by signal 9" in report["message"]
    assert "exited with status" not in report["message"]


def test_setup_that_wrote_nothing_says_so(root: Path):
    instance = carded_instance(root, setup="exit 2")

    _, report = create(root, instance)

    assert report["message"].endswith("\nit wrote no output")


# --- the interpreter check (CP-479 to CP-482) ----------------------------------------------------

RELATIVE_INTERPRETER = ".venv/bin/python3"
MAKE_INTERPRETER = "mkdir -p .venv/bin && touch .venv/bin/python3"


def test_missing_relative_interpreter_is_refused(root: Path):
    instance = carded_instance(root, test=f"{RELATIVE_INTERPRETER} -m pytest")

    code, report = create(root, instance)

    looked_at = instance / ".worktrees" / KEY / "prod" / RELATIVE_INTERPRETER
    assert (code, report["status"], report["error"]) == (1, "failed", "test-interpreter-missing")
    assert report["changed"] is True
    assert all(entry["branch_exists"] is True and entry["worktree_exists"] is True
               for entry in report["repos"])
    assert RELATIVE_INTERPRETER in report["message"]
    assert str(looked_at) in report["message"]


def test_setup_that_creates_the_interpreter_passes_the_check(root: Path):
    instance = carded_instance(root, setup=MAKE_INTERPRETER,
                               test=f"{RELATIVE_INTERPRETER} -m pytest")

    code, report = create(root, instance)

    assert (code, report["status"]) == (0, "created")


def test_interpreter_resolves_against_the_product_directory(root: Path):
    instance = carded_instance(root, setup="mkdir -p ../.venv/bin && touch ../.venv/bin/python3",
                               test=f"{RELATIVE_INTERPRETER} -m pytest")

    code, report = create(root, instance)

    assert (instance / ".worktrees" / KEY / RELATIVE_INTERPRETER).exists()
    assert (code, report["error"]) == (1, "test-interpreter-missing")


def test_interpreter_comes_after_leading_assignments(root: Path):
    refused_instance = carded_instance(
        root / "a", test=f"PYTHONPATH=a/b {RELATIVE_INTERPRETER} -m pytest")
    passing_instance = carded_instance(root / "b", test="PYTHONPATH=a/b pytest")

    refused_code, refused_report = create(root / "a", refused_instance)
    passing_code, passing_report = create(root / "b", passing_instance)

    assert (refused_code, refused_report["error"]) == (1, "test-interpreter-missing")
    assert RELATIVE_INTERPRETER in refused_report["message"]
    assert "a/b" not in refused_report["message"].split("is not at")[0]
    assert (passing_code, passing_report["status"]) == (0, "created")


def test_broken_symlink_interpreter_is_missing(root: Path):
    instance = carded_instance(
        root, setup=f"mkdir -p .venv/bin && ln -s /nonexistent/target {RELATIVE_INTERPRETER}",
        test=f"{RELATIVE_INTERPRETER} -m pytest")

    code, report = create(root, instance)

    assert (code, report["error"]) == (1, "test-interpreter-missing")


@pytest.mark.parametrize("test", [
    "pytest tests/", "/usr/bin/env python3 -m pytest", "~/bin/py -m pytest", "none", "",
    None, '".venv/bin/python3'])
def test_unchecked_test_commands_pass(root: Path, test: str | None):
    instance = carded_instance(root, test=test)

    code, report = create(root, instance)

    assert (code, report["status"]) == (0, "created")


def test_failed_setup_skips_the_interpreter_check(root: Path):
    instance = carded_instance(root, setup="exit 1", test=f"{RELATIVE_INTERPRETER} -m pytest")

    code, report = create(root, instance)

    assert (code, report["error"]) == (1, "setup-failed")


def test_interpreter_message_says_whether_a_setup_ran(root: Path):
    _, without_setup = create(root / "a", carded_instance(
        root / "a", test=f"{RELATIVE_INTERPRETER} -m pytest"))
    _, with_setup = create(root / "b", carded_instance(
        root / "b", setup="true", test=f"{RELATIVE_INTERPRETER} -m pytest"))

    assert "declares no **Setup command:**" in without_setup["message"]
    assert "after the setup command 'true' ran" in with_setup["message"]
    assert "declares no" not in with_setup["message"]
