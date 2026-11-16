"""Tests for `install_behave_starter.py`.

Three layers. The contract suites hold each port to one behaviour, once against its real adapter
and once against its fake. The engine's unit tests hand the engine those fakes through its
constructor and patch nothing. The CLI tests run the real tool against real files, a real git
repository and the real commit builder.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

import install_behave_starter as installer
from install_behave_starter import CommitRequest, IgnoredPath, UncommittedPath
from install_behave_starter_test_support import FakeCommitter, FakeFilesystem, FakeGit, FakeWorld
from test_support_python3_stub import python3_that_only_fails

TOOLS = Path(__file__).resolve().parent
GITHOOKS = TOOLS.parent / "githooks"
BUILDER = TOOLS / "commit_builder.py"

SUBJECT = "behave-check: install the Behave starter in .behave"
BODY = "No model ran: every file is copied byte-identical."
DIRECTIONAL = "Finish-line: demo — aside: the start-of-run check installed the Behave starter"
REFUSAL = "REFUSED because the message is wrong."


def _git(folder: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(folder), "-c", "user.name=t", "-c", "user.email=t@example.com",
         "-c", "commit.gpgsign=false", *args],
        capture_output=True, text=True, check=True,
    ).stdout


@pytest.fixture(autouse=True)
def _git_identity(monkeypatch):
    """Every commit a case makes, the builder's included, is given a fixed identity. Without it git
    builds one from the machine's host name, and on a Linux machine whose host name has no domain it
    refuses the commit instead."""
    for role in ("AUTHOR", "COMMITTER"):
        monkeypatch.setenv(f"GIT_{role}_NAME", "t")
        monkeypatch.setenv(f"GIT_{role}_EMAIL", "t@example.com")


# ── contract: the filesystem port ────────────────────────────────────────────

class FilesystemContract:
    """One behaviour per test, for a filesystem port. A subclass names how to make one."""

    def make(self, tmp_path: Path):
        """Return the port and an empty root folder to work in."""
        raise NotImplementedError

    def add_link(self, root: Path, name: str, target: Path) -> Path:
        raise NotImplementedError

    def test_filesystem_lists_every_file_of_a_tree_dotfiles_included(self, tmp_path):
        port, root = self.make(tmp_path)
        port.write_bytes(root / ".hidden", b"h")
        port.write_bytes(root / "nested" / "deep" / "a.txt", b"a")

        assert port.list_files(root) == [Path(".hidden"), Path("nested/deep/a.txt")]

    def test_filesystem_writes_bytes_identically_and_creates_parent_folders(self, tmp_path):
        port, root = self.make(tmp_path)
        data = b"\x00\xff\n\r\n tail"

        port.write_bytes(root / "made" / "on" / "write.bin", data)

        assert port.read_bytes(root / "made" / "on" / "write.bin") == data

    def test_filesystem_reports_a_present_path_for_a_file_a_folder_a_link_and_a_dangling_link(
        self, tmp_path
    ):
        port, root = self.make(tmp_path)
        port.write_bytes(root / "file", b"x")
        port.write_bytes(root / "folder" / "inner", b"y")
        self.add_link(root, "link", root / "file")
        self.add_link(root, "dangling", root / "nowhere")

        assert port.is_present(root / "file")
        assert port.is_present(root / "folder")
        assert port.is_present(root / "link")
        assert port.is_present(root / "dangling")
        assert not port.is_present(root / "absent")

    def test_filesystem_removes_a_tree(self, tmp_path):
        port, root = self.make(tmp_path)
        port.write_bytes(root / "tree" / "a" / "b.txt", b"b")
        port.write_bytes(root / "tree" / ".c", b"c")

        port.remove_tree(root / "tree")

        assert not port.is_present(root / "tree")
        assert port.list_files(root) == []

    def test_filesystem_refuses_a_write_it_cannot_make(self, tmp_path):
        port, root = self.make(tmp_path)
        port.write_bytes(root / "file", b"x")

        with pytest.raises(OSError):
            port.write_bytes(root / "file" / "child", b"y")

        assert not port.is_present(root / "file" / "child")


class TestDiskFilesystem(FilesystemContract):
    def make(self, tmp_path):
        root = tmp_path / "root"
        root.mkdir()
        return installer.DiskFilesystem(), root

    def add_link(self, root, name, target):
        link = root / name
        link.symlink_to(target)
        return link


class TestFakeFilesystem(FilesystemContract):
    def make(self, tmp_path):
        self.world = FakeWorld()
        return FakeFilesystem(self.world), Path("/scratch/root")

    def add_link(self, root, name, target):
        link = root / name
        self.world.links.add(link)
        return link


# ── contract: the git port ───────────────────────────────────────────────────

class GitContract:
    """One behaviour per test, for a git port. A subclass names how to make one over a folder."""

    def make(self, tmp_path: Path, *, branch: str | None = "main", tip: bool = True,
             in_repo: bool = True):
        """Return the port, the product folder and the work tree that holds it (None outside).

        `branch` None leaves HEAD detached, which needs a tip."""
        raise NotImplementedError

    def stage(self, folder: Path, name: str) -> None:
        raise NotImplementedError

    def staged(self, folder: Path) -> set[str]:
        raise NotImplementedError

    def tip_id(self, folder: Path) -> str:
        raise NotImplementedError

    def hold(self, folder: Path, name: str, how: str) -> None:
        """Leave `name` (relative to `folder`) as `how` says: `committed`, `untracked`, `staged`,
        `modified` or `deleted`."""
        raise NotImplementedError

    def ignore(self, folder: Path, name: str, rule_file: str) -> None:
        """Leave `name` on disk, ignored by a rule written into `rule_file`, which is committed.
        Both are relative to `folder`; a `name` ending in `/` is a folder."""
        raise NotImplementedError

    def test_git_gives_the_work_tree_of_a_folder_inside_a_repository(self, tmp_path):
        port, folder, work_tree = self.make(tmp_path)

        assert port.work_tree(folder).resolve() == work_tree.resolve()

    def test_git_gives_no_work_tree_for_a_folder_outside_a_repository(self, tmp_path):
        port, folder, _ = self.make(tmp_path, in_repo=False)

        assert port.work_tree(folder) is None

    @pytest.mark.parametrize("branch", ["main", "feature-x", None])
    def test_git_reads_main_another_branch_and_a_detached_head_as_branch_or_none(
        self, tmp_path, branch
    ):
        port, folder, _ = self.make(tmp_path, branch=branch)

        assert port.branch(folder) == branch

    def test_git_reads_an_unborn_main_as_having_no_tip(self, tmp_path):
        unborn, unborn_folder, _ = self.make(tmp_path / "unborn", tip=False)
        born, born_folder, _ = self.make(tmp_path / "born", tip=True)

        assert unborn.has_tip(unborn_folder) is False
        assert born.has_tip(born_folder) is True

    def test_git_unstages_only_the_given_paths(self, tmp_path):
        port, folder, _ = self.make(tmp_path)
        self.stage(folder, "one.txt")
        self.stage(folder, "two.txt")

        port.unstage(folder, ["one.txt"])

        assert self.staged(folder) == {"two.txt"}

    def test_git_short_id_names_the_tip(self, tmp_path):
        port, folder, _ = self.make(tmp_path)

        short = port.short_id(folder)

        assert short and short == short.strip()
        assert self.tip_id(folder).startswith(short)

    def test_git_lists_each_uncommitted_path_under_a_folder_relative_to_the_folder_asked(
        self, tmp_path
    ):
        port, folder, _ = self.make(tmp_path)
        self.hold(folder, ".behave/kept.txt", "committed")
        for how in ("untracked", "staged", "modified", "deleted"):
            self.hold(folder, f".behave/{how}.txt", how)
        self.hold(folder, "outside.txt", "untracked")

        assert port.uncommitted(folder, ".behave") == [
            UncommittedPath(".behave/deleted.txt", ("deleted",)),
            UncommittedPath(".behave/modified.txt", ("modified",)),
            UncommittedPath(".behave/staged.txt", ("staged",)),
            UncommittedPath(".behave/untracked.txt", ("untracked",)),
        ]

    def test_git_lists_nothing_uncommitted_under_a_committed_clean_folder(self, tmp_path):
        port, folder, _ = self.make(tmp_path)
        self.hold(folder, ".behave/kept.txt", "committed")

        assert port.uncommitted(folder, ".behave") == []

    def test_git_lists_each_ignored_path_under_a_folder_with_the_file_holding_its_rule(
        self, tmp_path
    ):
        port, folder, _ = self.make(tmp_path)
        self.hold(folder, ".behave/kept.txt", "committed")
        self.ignore(folder, ".behave/.venv/", ".behave/.gitignore")
        self.ignore(folder, ".behave/run.log", ".gitignore")
        self.ignore(folder, "outside.log", ".gitignore")

        assert port.ignored(folder, ".behave") == [
            IgnoredPath(".behave/.venv/", ".behave/.gitignore"),
            IgnoredPath(".behave/run.log", ".gitignore"),
        ]


class TestGitCli(GitContract):
    def make(self, tmp_path, *, branch="main", tip=True, in_repo=True):
        base = tmp_path / "repo"
        folder = base / "product" if in_repo else tmp_path / "loose"
        folder.mkdir(parents=True)
        if in_repo:
            _git(base, "init", "-q", "-b", "main" if branch is None else branch)
            if tip:
                _git(base, "commit", "-q", "--allow-empty", "-m", "seed")
            if branch is None:
                _git(base, "checkout", "-q", "--detach")
        return installer.GitCli(), folder, (base if in_repo else None)

    def stage(self, folder, name):
        (folder / name).write_text(name)
        _git(folder, "add", name)

    def staged(self, folder):
        return set(_git(folder, "diff", "--cached", "--name-only", "--relative").split())

    def tip_id(self, folder):
        return _git(folder, "rev-parse", "HEAD").strip()

    def hold(self, folder, name, how):
        path = folder / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(name)
        if how == "untracked":
            return
        _git(folder, "add", name)
        if how == "staged":
            return
        _git(folder, "commit", "-q", "-m", f"commit {name}", "--", name)
        if how == "modified":
            path.write_text(f"{name} changed")
        elif how == "deleted":
            path.unlink()

    def ignore(self, folder, name, rule_file):
        rules = folder / rule_file
        rules.parent.mkdir(parents=True, exist_ok=True)
        pattern = name.rstrip("/").rsplit("/", 1)[-1] + ("/" if name.endswith("/") else "")
        with rules.open("a") as stream:
            stream.write(f"{pattern}\n")
        _git(folder, "add", rule_file)
        _git(folder, "commit", "-q", "-m", f"ignore {name}", "--", rule_file)
        path = folder / name.rstrip("/")
        if name.endswith("/"):
            (path / "inner").mkdir(parents=True, exist_ok=True)
            (path / "inner" / "file").write_text("x")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("x")


class TestFakeGit(GitContract):
    def make(self, tmp_path, *, branch="main", tip=True, in_repo=True):
        self.world = FakeWorld(work_tree=Path("/scratch/repo") if in_repo else None, branch=branch)
        if tip:
            self.world.add_commit((), "seed")
        return FakeGit(self.world), Path("/scratch/repo/product"), (
            Path("/scratch/repo") if in_repo else None
        )

    def stage(self, folder, name):
        self.world.index.add(name)

    def staged(self, folder):
        return set(self.world.index)

    def tip_id(self, folder):
        return self.world.commits[-1].full_id

    def hold(self, folder, name, how):
        if how != "committed":
            self.world.uncommitted[name] = (how,)

    def ignore(self, folder, name, rule_file):
        self.world.ignored[name] = rule_file


# ── contract: the committer port ─────────────────────────────────────────────

class CommitterContract:
    """One behaviour per test, for a committer port. A subclass names how to make one."""

    def make(self, tmp_path: Path, *, refusing: bool = False):
        """Return the port and a repository folder on main with one commit in it."""
        raise NotImplementedError

    def write(self, folder: Path, name: str, data: bytes) -> None:
        raise NotImplementedError

    def stage_other(self, folder: Path, name: str) -> None:
        raise NotImplementedError

    def staged(self, folder: Path) -> set[str]:
        raise NotImplementedError

    def tip(self, folder: Path) -> str:
        raise NotImplementedError

    def parent_of_tip(self, folder: Path) -> str:
        raise NotImplementedError

    def changed_by_tip(self, folder: Path) -> set[str]:
        raise NotImplementedError

    def message_of_tip(self, folder: Path) -> str:
        raise NotImplementedError

    @staticmethod
    def request(folder: Path, *paths: str) -> CommitRequest:
        return CommitRequest(
            repository=folder, paths=paths, subject=SUBJECT, body=BODY,
            directional=DIRECTIONAL, role="Product", surface="behave-check",
        )

    def test_committer_commits_the_declared_paths_only_with_the_given_trailers(self, tmp_path):
        port, folder = self.make(tmp_path)
        self.write(folder, ".behave/a.txt", b"a")
        self.write(folder, ".behave/b.txt", b"b")
        before = self.tip(folder)

        outcome = port.commit_only(self.request(folder, ".behave/a.txt", ".behave/b.txt"))

        assert outcome.refusal is None
        assert self.parent_of_tip(folder) == before
        assert self.changed_by_tip(folder) == {".behave/a.txt", ".behave/b.txt"}
        message = self.message_of_tip(folder)
        assert "Role: Product" in message
        assert "Surface: behave-check" in message
        assert "Co-Authored-By:" not in message

    def test_committer_leaves_another_staged_path_staged_and_in_no_commit(self, tmp_path):
        port, folder = self.make(tmp_path)
        self.write(folder, ".behave/a.txt", b"a")
        self.stage_other(folder, "other.txt")

        outcome = port.commit_only(self.request(folder, ".behave/a.txt"))

        assert outcome.refusal is None
        assert self.changed_by_tip(folder) == {".behave/a.txt"}
        assert self.staged(folder) == {"other.txt"}

    def test_committer_returns_the_refusal_reason_read_from_the_builders_output(self, tmp_path):
        port, folder = self.make(tmp_path, refusing=True)
        self.write(folder, ".behave/a.txt", b"a")
        before = self.tip(folder)

        outcome = port.commit_only(self.request(folder, ".behave/a.txt"))

        assert outcome.refusal is not None
        assert "because the message is wrong" in outcome.refusal
        assert "\n" not in outcome.refusal
        assert self.tip(folder) == before


class TestBuilderCommitter(CommitterContract):
    @pytest.fixture(autouse=True)
    def _python3_only_fails(self, tmp_path, monkeypatch):
        # A committer that ran the builder on `python3` would hit this stub and be refused.
        path, _ = python3_that_only_fails(tmp_path)
        monkeypatch.setenv("PATH", path)

    def make(self, tmp_path, *, refusing=False):
        folder = tmp_path / "repo"
        folder.mkdir()
        _git(folder, "init", "-q", "-b", "main")
        _git(folder, "commit", "-q", "--allow-empty", "-m", "seed")
        hooks = GITHOOKS
        if refusing:
            hooks = tmp_path / "refusing-hooks"
            hooks.mkdir()
            hook = hooks / "commit-msg"
            hook.write_text(
                f"#!/bin/sh\necho 'first line of noise' >&2\necho '{REFUSAL}' >&2\nexit 1\n"
            )
            hook.chmod(0o755)
        _git(folder, "config", "core.hooksPath", str(hooks))
        committer = installer.BuilderCommitter(builder=BUILDER, python=sys.executable)
        return committer, folder

    def write(self, folder, name, data):
        path = folder / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def stage_other(self, folder, name):
        (folder / name).write_text(name)
        _git(folder, "add", name)

    def staged(self, folder):
        return set(_git(folder, "diff", "--cached", "--name-only").split())

    def tip(self, folder):
        return _git(folder, "rev-parse", "HEAD").strip()

    def parent_of_tip(self, folder):
        return _git(folder, "rev-parse", "HEAD~1").strip()

    def changed_by_tip(self, folder):
        return set(_git(folder, "diff", "--name-only", "HEAD~1", "HEAD").split())

    def message_of_tip(self, folder):
        return _git(folder, "log", "-1", "--format=%B")


class TestFakeCommitter(CommitterContract):
    def make(self, tmp_path, *, refusing=False):
        self.world = FakeWorld()
        self.world.add_commit((), "seed")
        committer = FakeCommitter(self.world, refuse_with=REFUSAL if refusing else None)
        return committer, Path("/scratch/repo")

    def write(self, folder, name, data):
        self.world.files[folder / name] = data

    def stage_other(self, folder, name):
        self.world.index.add(name)

    def staged(self, folder):
        return set(self.world.index)

    def tip(self, folder):
        return self.world.commits[-1].full_id

    def parent_of_tip(self, folder):
        return self.world.commits[-1].parent

    def changed_by_tip(self, folder):
        return set(self.world.commits[-1].changed)

    def message_of_tip(self, folder):
        return self.world.commits[-1].message


# ── the install engine, over fakes ───────────────────────────────────────────

STARTER = Path("/core/templates/behave-starter")
PRODUCT = Path("/scratch/repo/product")
INTO = PRODUCT / ".behave"
STARTER_FILES = {
    "README.md": b"# readme\n",
    "pyproject.toml": b"[project]\nname = 'x'\n",
    ".gitignore": b".venv/\n",
    "features/environment.py": b"\x00\xff binary-ish\n",
    "features/steps/steps.py": b"# steps\n",
}


class Scene:
    """The engine over fakes: the world, the three fakes, the stderr stream and the engine."""

    def __init__(self, *, world=None, fail_on_write=None, refuse_with=None, raise_error=None,
                 git_raises_on=None):
        import io

        self.world = world if world is not None else FakeWorld()
        if world is None:
            self.world.add_commit((), "seed")
        for name, data in STARTER_FILES.items():
            self.world.files[STARTER / name] = data
        self.filesystem = FakeFilesystem(self.world, fail_on_write=fail_on_write)
        self.git = FakeGit(self.world, raise_on=git_raises_on)
        self.committer = FakeCommitter(self.world, refuse_with=refuse_with,
                                       raise_error=raise_error)
        self.stderr = io.StringIO()
        self.installer = installer.Installer(
            filesystem=self.filesystem, git=self.git, committer=self.committer,
            stderr=self.stderr, starter=STARTER, into=INTO, project="demo", launch="product-qa",
        )

    def lines(self) -> list[str]:
        return self.stderr.getvalue().splitlines()

    def installed_files(self) -> list[Path]:
        return [path for path in self.world.files if path.is_relative_to(INTO)]

    def event_names(self) -> list[str]:
        return [event[0] for event in self.world.events]


def test_installed_writes_every_starter_file_byte_identical_under_into():
    scene = Scene()

    assert scene.installer.install() == 0

    for name, data in STARTER_FILES.items():
        assert scene.world.files[INTO / name] == data
    assert len(scene.installed_files()) == len(STARTER_FILES)


def test_installed_hands_the_committer_exactly_the_folders_paths_with_the_declared_trailers():
    scene = Scene()

    scene.installer.install()

    [request] = scene.committer.requests
    assert request.repository == PRODUCT
    assert sorted(request.paths) == sorted(f".behave/{name}" for name in STARTER_FILES)
    assert request.role == "Product"
    assert request.surface == "behave-check"
    assert request.directional.startswith("Finish-line: demo — aside: ")
    assert request.subject == "behave-check: install the Behave starter in .behave"
    assert "product-qa" in request.body and "demo" in request.body
    assert not hasattr(request, "co_authored_by")


def test_installed_prints_one_line_naming_project_product_folder_main_and_the_short_id(capsys):
    scene = Scene()

    status = scene.installer.install()

    assert status == 0
    [line] = scene.lines()
    short = scene.git.short_id(PRODUCT)
    for named in ("product-qa", "demo", str(PRODUCT), ".behave", "main", short):
        assert named in line
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("present", ["file", "folder", "link", "dangling"])
def test_into_present_writes_nothing_prints_nothing_and_returns_zero(present, capsys):
    scene = Scene()
    if present == "file":
        scene.world.files[INTO] = b"a file named like the folder"
    elif present == "folder":
        scene.world.files[INTO / "held"] = b"x"
    else:
        scene.world.links.add(INTO)
    before = dict(scene.world.files)

    status = scene.installer.install()

    assert status == 0
    assert scene.lines() == []
    assert scene.world.files == before
    assert scene.filesystem.write_count == 0
    assert scene.committer.requests == []
    assert capsys.readouterr().out == ""


# ── an existing .behave: held paths stop the launch ─────────────────────────────

def _scene_with_existing_folder() -> Scene:
    scene = Scene()
    scene.world.files[INTO / "README.md"] = b"committed\n"
    return scene


@pytest.mark.parametrize("how", ["untracked", "staged", "modified", "deleted"])
def test_an_uncommitted_path_inside_an_existing_folder_stops_naming_it_and_writes_nothing(how):
    scene = _scene_with_existing_folder()
    scene.world.uncommitted[".behave/features/mine.feature"] = (how,)
    files_before = dict(scene.world.files)

    status = scene.installer.install()

    assert status == 1
    [line] = scene.lines()
    assert line.startswith("product-qa:")
    assert f".behave/features/mine.feature ({how})" in line
    assert str(PRODUCT) in line and "demo" in line and "the launch stopped" in line
    assert scene.world.files == files_before
    assert scene.filesystem.write_count == 0
    assert scene.committer.requests == []
    assert "unstage" not in scene.event_names() and "remove" not in scene.event_names()


def test_an_ignored_path_inside_an_existing_folder_stops_naming_it_and_writes_nothing():
    scene = _scene_with_existing_folder()
    scene.world.ignored[".behave/run.log"] = ".gitignore"
    files_before = dict(scene.world.files)

    status = scene.installer.install()

    assert status == 1
    [line] = scene.lines()
    assert ".behave/run.log (ignored)" in line
    assert scene.world.files == files_before
    assert scene.filesystem.write_count == 0
    assert scene.committer.requests == []


def test_every_held_path_is_named_in_one_line():
    scene = _scene_with_existing_folder()
    scene.world.uncommitted[".behave/a.feature"] = ("untracked",)
    scene.world.uncommitted[".behave/b.py"] = ("staged", "modified")
    scene.world.ignored[".behave/c.log"] = ".gitignore"

    assert scene.installer.install() == 1

    [line] = scene.lines()
    for named in (".behave/a.feature (untracked)", ".behave/b.py (staged and modified)",
                  ".behave/c.log (ignored)"):
        assert named in line


def test_a_path_the_starters_own_gitignore_ignores_does_not_stop_the_launch():
    # The starter's own `.gitignore` ignores the environment and caches a scenario run leaves in
    # the folder, so a folder that has run its scenarios is still committed and clean.
    scene = _scene_with_existing_folder()
    scene.world.ignored[".behave/.venv/"] = ".behave/.gitignore"
    scene.world.ignored[".behave/features/__pycache__/"] = ".behave/.gitignore"

    assert scene.installer.install() == 0
    assert scene.lines() == []


def test_a_committed_clean_existing_folder_installs_nothing_and_goes_on():
    scene = _scene_with_existing_folder()
    files_before = dict(scene.world.files)

    assert scene.installer.install() == 0
    assert scene.lines() == []
    assert scene.world.files == files_before
    assert scene.committer.requests == []


def test_an_existing_folder_in_no_work_tree_goes_on_silently():
    scene = Scene(world=_world_for(dict(work_tree=None)))
    scene.world.files[INTO / "README.md"] = b"x\n"
    scene.world.uncommitted[".behave/README.md"] = ("untracked",)

    assert scene.installer.install() == 0
    assert scene.lines() == []


CANNOT_LAND = [
    pytest.param(dict(work_tree=None), "is in no git work tree", id="no-work-tree"),
    pytest.param(dict(branch="feature-x"), "has feature-x checked out, not main", id="feature-x"),
    pytest.param(dict(branch=None), "has a detached HEAD checked out, not main", id="detached"),
    pytest.param(dict(unborn=True), "has no commit yet", id="unborn-main"),
]


def _world_for(settings: dict) -> FakeWorld:
    world = FakeWorld(work_tree=settings.get("work_tree", Path("/scratch/repo")),
                      branch=settings.get("branch", "main"))
    if not settings.get("unborn"):
        world.add_commit((), "seed")
    return world


@pytest.mark.parametrize("settings, reason", CANNOT_LAND)
def test_a_commit_that_cannot_land_writes_nothing_and_names_the_reason(settings, reason, capsys):
    scene = Scene(world=_world_for(settings))

    status = scene.installer.install()

    assert status == 0
    assert scene.installed_files() == []
    assert scene.world.index == set()
    assert scene.committer.requests == []
    [line] = scene.lines()
    assert line.startswith("product-qa:")
    assert "demo" in line and str(PRODUCT) in line and reason in line
    assert "Nothing was written." in line
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("settings, reason", CANNOT_LAND)
def test_preconditions_are_checked_before_the_first_write(settings, reason):
    scene = Scene(world=_world_for(settings))

    scene.installer.install()

    assert scene.filesystem.write_count == 0
    assert "write" not in scene.event_names()


def test_a_refused_commit_is_undone_unstaged_then_removed_and_stops_quoting_the_refusal():
    scene = Scene(refuse_with="REFUSED because the message is wrong.")

    status = scene.installer.install()

    assert status == 1
    names = scene.event_names()
    assert names.index("unstage") < names.index("remove")
    assert scene.installed_files() == []
    assert scene.world.index == set()
    [line] = scene.lines()
    assert "did not land: REFUSED because the message is wrong. What the install wrote" in line
    assert "the launch stopped" in line
    assert "The next launch tries again" not in line


def test_a_write_failing_mid_copy_is_undone():
    scene = Scene(fail_on_write=3)

    status = scene.installer.install()

    assert status == 0
    assert scene.installed_files() == []
    assert scene.world.index == set()
    assert scene.committer.requests == []
    [line] = scene.lines()
    assert "did not land: scripted write failure on write 3" in line


def test_an_unexpected_port_failure_is_undone_and_raised():
    scene = Scene(raise_error=RuntimeError("the committer broke"))

    with pytest.raises(RuntimeError, match="the committer broke"):
        scene.installer.install()

    assert scene.installed_files() == []
    names = scene.event_names()
    assert names.index("unstage") < names.index("remove")


def test_a_failure_after_the_commit_landed_is_raised_and_undoes_nothing():
    scene = Scene(git_raises_on="short_id")

    with pytest.raises(RuntimeError, match="short_id"):
        scene.installer.install()

    assert len(scene.installed_files()) == len(STARTER_FILES)
    assert "remove" not in scene.event_names()
    assert scene.world.commits[-1].changed


def test_a_starter_holding_no_file_is_an_error_before_anything_is_written():
    scene = Scene()
    for name in STARTER_FILES:
        del scene.world.files[STARTER / name]

    with pytest.raises(FileNotFoundError, match="holds no file"):
        scene.installer.install()

    assert scene.filesystem.write_count == 0


def test_the_unexpected_error_line_names_launch_product_project_and_the_folder():
    scene = Scene()

    line = scene.installer.unexpected_error_line(RuntimeError("it broke."))

    assert line.startswith("product-qa: installing the Behave starter into ")
    assert "failed with an unexpected error, and the launch stopped: it broke. Before" in line
    assert str(PRODUCT) in line and "demo" in line and "uncommitted .behave" in line


# ── the CLI: the real tool over real files, a real repository and the real builder ──────────

TOOL = TOOLS / "install_behave_starter.py"


def _starter(folder: Path) -> Path:
    for name, data in STARTER_FILES.items():
        path = folder / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return folder


def _repository(folder: Path) -> Path:
    folder.mkdir()
    _git(folder, "init", "-q", "-b", "main")
    _git(folder, "commit", "-q", "--allow-empty", "-m", "seed")
    _git(folder, "config", "core.hooksPath", str(GITHOOKS))
    return folder


def _run_cli(starter: Path, into: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TOOL), "--starter", str(starter), "--into", str(into),
         "--project", "demo", "--launch", "product-qa"],
        capture_output=True, text=True,
    )


def test_cli_installs_into_a_scratch_repository_and_exits_zero_with_stdout_empty(tmp_path):
    starter = _starter(tmp_path / "starter")
    product = _repository(tmp_path / "product")
    before = _git(product, "rev-parse", "HEAD").strip()

    result = _run_cli(starter, product / ".behave")

    assert result.returncode == 0
    assert result.stdout == ""
    assert len(result.stderr.splitlines()) == 1
    for name, data in STARTER_FILES.items():
        assert (product / ".behave" / name).read_bytes() == data
    assert _git(product, "rev-parse", "HEAD~1").strip() == before
    changed = set(_git(product, "diff", "--name-only", "HEAD~1", "HEAD").split())
    assert changed == {f".behave/{name}" for name in STARTER_FILES}


def test_cli_installs_into_a_product_folder_inside_a_larger_repository(tmp_path):
    # CP-1240 asks only that the product folder lie in a git work tree on main, and a product
    # folder is often a folder inside the repository rather than its root: the commit holds the
    # folder's files at their place in that repository, and a path staged elsewhere stays staged.
    starter = _starter(tmp_path / "starter")
    repository = tmp_path / "repository"
    product = repository / "products" / "demo"
    product.mkdir(parents=True)
    (product / "README.md").write_text("mine\n")
    _git(repository, "init", "-q", "-b", "main")
    _git(repository, "add", "products/demo/README.md")
    _git(repository, "commit", "-q", "-m", "seed")
    _git(repository, "config", "core.hooksPath", str(GITHOOKS))
    (repository / "other.txt").write_text("someone else's work\n")
    _git(repository, "add", "other.txt")
    before = _git(repository, "rev-parse", "HEAD").strip()

    result = _run_cli(starter, product / ".behave")

    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
    assert len(result.stderr.splitlines()) == 1
    for name, data in STARTER_FILES.items():
        assert (product / ".behave" / name).read_bytes() == data
    assert _git(repository, "rev-parse", "HEAD~1").strip() == before
    changed = set(_git(repository, "diff", "--name-only", "HEAD~1", "HEAD").split())
    assert changed == {f"products/demo/.behave/{name}" for name in STARTER_FILES}
    assert set(_git(repository, "diff", "--cached", "--name-only").split()) == {"other.txt"}


def test_cli_into_present_is_silent_and_exits_zero(tmp_path):
    starter = _starter(tmp_path / "starter")
    product = _repository(tmp_path / "product")
    (product / ".behave").mkdir()

    result = _run_cli(starter, product / ".behave")

    assert result.returncode == 0
    assert (result.stdout, result.stderr) == ("", "")
    assert list((product / ".behave").iterdir()) == []


def test_cli_in_no_repository_exits_zero_with_one_line_and_writes_nothing(tmp_path):
    starter = _starter(tmp_path / "starter")
    product = tmp_path / "product"
    product.mkdir()

    result = _run_cli(starter, product / ".behave")

    assert result.returncode == 0
    assert result.stdout == ""
    assert len(result.stderr.splitlines()) == 1
    assert not (product / ".behave").exists()


def _installed_repository(tmp_path: Path) -> tuple[Path, Path]:
    """A scratch repository on main whose `.behave` the tool installed and committed."""
    starter = _starter(tmp_path / "starter")
    product = _repository(tmp_path / "product")
    assert _run_cli(starter, product / ".behave").returncode == 0
    return starter, product


def _tree(folder: Path) -> dict[str, bytes]:
    return {
        path.relative_to(folder).as_posix(): path.read_bytes()
        for path in sorted(folder.rglob("*"))
        if path.is_file() and ".git" not in path.relative_to(folder).parts
    }


def test_cli_an_untracked_file_in_an_existing_folder_exits_one_naming_it_and_changes_nothing(
    tmp_path
):
    starter, product = _installed_repository(tmp_path)
    (product / ".behave" / "features" / "mine.feature").write_text("Feature: mine\n")
    tree, tip = _tree(product), _git(product, "rev-parse", "HEAD")

    result = _run_cli(starter, product / ".behave")

    assert result.returncode == 1
    assert result.stdout == ""
    [line] = result.stderr.splitlines()
    assert ".behave/features/mine.feature (untracked)" in line
    assert (_tree(product), _git(product, "rev-parse", "HEAD")) == (tree, tip)


def test_cli_an_ignored_file_in_an_existing_folder_exits_one_naming_it_and_changes_nothing(
    tmp_path
):
    starter, product = _installed_repository(tmp_path)
    (product / ".gitignore").write_text("*.log\n")
    _git(product, "add", ".gitignore")
    _git(product, "commit", "-q", "--no-verify", "-m", "ignore logs")
    (product / ".behave" / "run.log").write_text("x\n")
    tree, tip = _tree(product), _git(product, "rev-parse", "HEAD")

    result = _run_cli(starter, product / ".behave")

    assert result.returncode == 1
    [line] = result.stderr.splitlines()
    assert ".behave/run.log (ignored)" in line
    assert (_tree(product), _git(product, "rev-parse", "HEAD")) == (tree, tip)


def test_cli_a_committed_folder_holding_what_its_own_gitignore_ignores_exits_zero_silently(
    tmp_path
):
    starter, product = _installed_repository(tmp_path)
    (product / ".behave" / ".venv" / "lib").mkdir(parents=True)
    (product / ".behave" / ".venv" / "lib" / "site.py").write_text("x\n")
    tip = _git(product, "rev-parse", "HEAD")

    result = _run_cli(starter, product / ".behave")

    assert (result.returncode, result.stdout, result.stderr) == (0, "", "")
    assert _git(product, "rev-parse", "HEAD") == tip


def test_cli_a_refused_commit_exits_one_quoting_the_refusal_and_leaves_no_folder(tmp_path):
    starter = _starter(tmp_path / "starter")
    product = _repository(tmp_path / "product")
    hooks = tmp_path / "refusing-hooks"
    hooks.mkdir()
    (hooks / "commit-msg").write_text(f"#!/bin/sh\necho '{REFUSAL}' >&2\nexit 1\n")
    (hooks / "commit-msg").chmod(0o755)
    _git(product, "config", "core.hooksPath", str(hooks))
    tip = _git(product, "rev-parse", "HEAD")

    result = _run_cli(starter, product / ".behave")

    assert result.returncode == 1
    assert result.stdout == ""
    [line] = result.stderr.splitlines()
    assert "REFUSED because the message is wrong" in line
    assert not (product / ".behave").exists()
    assert _git(product, "rev-parse", "HEAD") == tip
    assert _git(product, "diff", "--cached", "--name-only") == ""


def test_cli_with_an_unreadable_starter_undoes_exits_one_and_writes_a_message(tmp_path):
    product = _repository(tmp_path / "product")

    result = _run_cli(tmp_path / "no-such-starter", product / ".behave")

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr.strip() != ""
    assert not (product / ".behave").exists()


@pytest.mark.parametrize("argv", [
    [],
    ["--starter", "s", "--into", "i", "--project", "p"],
    ["--starter", "s", "--into", "i", "--project", "p", "--launch", "l", "--unknown", "x"],
])
def test_cli_usage_error_exits_two(argv, capsys):
    assert installer.main(argv) == 2
    assert capsys.readouterr().out == ""


# ── layer 1: the reason read from a builder's captured output ────────────────────────────────


def _builder_result(*, returncode=1, stdout="", stderr=""):
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr=stderr)


def test_the_refusal_reason_is_the_last_non_blank_line_of_stderr():
    result = _builder_result(stderr="noise\n  the reason  \n\n", stdout="not this\n")

    assert installer._refusal_reason(result) == "the reason"


def test_the_refusal_reason_is_read_from_stdout_when_stderr_is_blank():
    result = _builder_result(stderr=" \n", stdout="first\nthe reason\n")

    assert installer._refusal_reason(result) == "the reason"


def test_a_builder_that_printed_nothing_is_named_by_its_exit_status():
    result = _builder_result(returncode=3)

    assert installer._refusal_reason(result) == "the commit builder exited with status 3"
