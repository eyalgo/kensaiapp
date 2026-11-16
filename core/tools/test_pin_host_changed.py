"""Contract tests for `pin_host_changed.py` — does a pin's source host differ from the pin?

Two tiers. `compare`'s decision is a unit, handed the fake `HostTree` from
`pin_host_changed_test_support.py` (layer 1, nothing real touched); the fake and the real adapter
are held to one contract suite. Every other case is layer 2: it builds its own throwaway host under
`tmp_path`, makes its pin into a sibling directory and runs `compare` on the real `HostTree`, so
nothing here reads or writes the real `~/.kensaiapp/pins/`. The host is a real git work tree
wherever the case needs git's ignore rules and `HEAD`; the non-git case builds a plain directory.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import pin
import pin_host_changed
from pin_host_changed import HostTree, Verdict
from pin_host_changed_test_support import FakeHostTree

_TOOLS = Path(__file__).parent


def _compare(source_pin: pin.Pin) -> Verdict:
    """`compare` on the real adapter — the layer-2 form every case below `TestDecision` uses."""
    return pin_host_changed.compare(source_pin, HostTree())


def _git(*args: str, cwd: Path) -> str:
    result = subprocess.run(
        ["git", *args], cwd=str(cwd), check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


def _init_git_host(root: Path) -> Path:
    """A git work tree with a tracked file in each of the three trees, a real copy of the two
    modules the CLI needs under `core/tools/`, a `system/` file that belongs to no tree, and a
    `.gitignore` matching a log file and `__pycache__/`. Everything is committed."""
    root.mkdir()
    _git("init", "-q", cwd=root)
    _git("config", "user.email", "host@example.com", cwd=root)
    _git("config", "user.name", "Host", cwd=root)

    (root / "core" / "tools").mkdir(parents=True)
    (root / "core" / "tools" / "tool.py").write_text("print('tracked')\n")
    shutil.copy2(_TOOLS / "pin.py", root / "core" / "tools" / "pin.py")
    shutil.copy2(_TOOLS / "pin_host_changed.py", root / "core" / "tools" / "pin_host_changed.py")
    (root / ".claude" / "skills" / "example").mkdir(parents=True)
    (root / ".claude" / "skills" / "example" / "SKILL.md").write_text("tracked skill\n")
    (root / "skills" / "grp").mkdir(parents=True)
    (root / "skills" / "grp" / "SKILL.md").write_text("grouped\n")
    (root / "system").mkdir()
    (root / "system" / "outside.md").write_text("outside the three trees\n")
    (root / ".gitignore").write_text("core/ignored.log\n__pycache__/\n")

    _git("add", "-A", cwd=root)
    _git("commit", "-q", "-m", "initial", cwd=root)
    return root


@pytest.fixture
def pins_home(tmp_path):
    home = tmp_path / "pins"
    home.mkdir()
    return home


@pytest.fixture
def host(tmp_path):
    return _init_git_host(tmp_path / "host")


@pytest.fixture
def made(host, pins_home):
    """The pin of `host` as it stands, before any test edits the host."""
    return pin.make(host, pins_home)


def _run_cli(pin_root: Path, *, script: Path | None = None) -> subprocess.CompletedProcess:
    script = script or (pin_root / "core" / "tools" / "pin_host_changed.py")
    return subprocess.run(
        [sys.executable, "-B", str(script), "--pin", str(pin_root)],
        capture_output=True,
        text=True,
    )


def _snapshot(root: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


_HOST = Path("/fake/host")
_PIN = Path("/fake/pin")


def _fake_pin() -> pin.Pin:
    return pin.Pin(root=_PIN, core=_PIN / "core", source_host_root=_HOST, id="fake")


def _tree(**seeded) -> FakeHostTree:
    return FakeHostTree(host_root=_HOST, pin_root=_PIN, **seeded)


class TestDecision:
    """`compare`'s verdict from what its `HostTree` answers — layer 1, the fake handed in."""

    def test_a_host_folder_that_is_gone_is_host_gone(self):
        tree = _tree(host_dir=False, host_files=["core/a"], pin_files=["core/a"])

        assert pin_host_changed.compare(_fake_pin(), tree) is Verdict.HOST_GONE

    def test_the_same_files_on_both_sides_are_unchanged(self):
        tree = _tree(host_files=["core/a", "skills/b"], pin_files=["skills/b", "core/a"])

        assert pin_host_changed.compare(_fake_pin(), tree) is Verdict.UNCHANGED

    def test_a_file_on_the_host_only_is_changed(self):
        tree = _tree(host_files=["core/a", "core/new"], pin_files=["core/a"])

        assert pin_host_changed.compare(_fake_pin(), tree) is Verdict.CHANGED

    def test_a_listed_file_the_host_no_longer_holds_is_absent_from_the_host_side(self):
        tree = _tree(host_files=["core/a", "core/gone"], held=["core/a"], pin_files=["core/a"])

        assert pin_host_changed.compare(_fake_pin(), tree) is Verdict.UNCHANGED

    def test_a_pin_only_file_the_host_ignores_is_unchanged(self):
        tree = _tree(
            host_files=["core/a"], pin_files=["core/a", "core/x.pyc"], ignored=["core/x.pyc"]
        )

        assert pin_host_changed.compare(_fake_pin(), tree) is Verdict.UNCHANGED
        assert tree.ignore_asks == [["core/x.pyc"]]

    def test_a_pin_only_file_the_host_does_not_ignore_is_changed(self):
        tree = _tree(host_files=["core/a"], pin_files=["core/a", "core/kept"])

        assert pin_host_changed.compare(_fake_pin(), tree) is Verdict.CHANGED

    def test_a_non_git_host_asks_no_ignore_rules_and_a_pin_only_file_is_changed(self):
        tree = _tree(
            host_files=["core/a"],
            pin_files=["core/a", "core/x.pyc"],
            git=False,
            ignored=["core/x.pyc"],
        )

        assert pin_host_changed.compare(_fake_pin(), tree) is Verdict.CHANGED
        assert tree.ignore_asks == []

    def test_a_file_that_differs_from_its_pinned_copy_is_changed(self):
        tree = _tree(
            host_files=["core/a", "core/b"], pin_files=["core/a", "core/b"], differing=["core/b"]
        )

        assert pin_host_changed.compare(_fake_pin(), tree) is Verdict.CHANGED


# The world every contract case reads: a git or a plain host with a file the pin holds alike, a
# file it holds otherwise, a link whose target is gone and a byte-code file the host ignores and
# only the pin holds.
_SAME = "core/same.txt"
_OTHER = "core/other.txt"
_DANGLING = "core/dangling"
_IGNORED = "core/cache.pyc"


class HostTreeContract:
    """What every `HostTree` answers, real or fake. `make` returns `(tree, host_root, pin_root)`
    for the world above, its host a git work tree when `git` is true."""

    def make(self, tmp_path: Path, *, git: bool):
        raise NotImplementedError

    def test_the_host_folder_is_a_folder_and_a_missing_one_is_not(self, tmp_path):
        tree, host_root, _ = self.make(tmp_path, git=True)

        assert tree.is_dir(host_root)
        assert not tree.is_dir(host_root.parent / "no-such-host")

    @pytest.mark.parametrize("git", [True, False], ids=["git", "non-git"])
    def test_the_host_listing_names_its_files_and_its_link(self, tmp_path, git):
        tree, host_root, _ = self.make(tmp_path, git=git)

        assert sorted(tree.host_files(host_root)) == sorted([_SAME, _OTHER, _DANGLING])

    def test_the_pin_listing_names_every_file_the_pin_holds(self, tmp_path):
        tree, _, pin_root = self.make(tmp_path, git=True)

        assert sorted(tree.pin_files(pin_root)) == sorted([_SAME, _OTHER, _IGNORED])

    def test_a_file_and_a_link_whose_target_is_gone_are_held_and_a_missing_path_is_not(
        self, tmp_path
    ):
        tree, host_root, _ = self.make(tmp_path, git=True)

        assert tree.holds(host_root / _SAME)
        assert tree.holds(host_root / _DANGLING)
        assert not tree.holds(host_root / "core" / "never-there")

    @pytest.mark.parametrize("git", [True, False], ids=["git", "non-git"])
    def test_a_git_host_is_a_work_tree_and_a_plain_one_is_not(self, tmp_path, git):
        tree, host_root, _ = self.make(tmp_path, git=git)

        assert tree.is_git_work_tree(host_root) is git

    def test_the_ignore_rules_match_the_ignored_file_only(self, tmp_path):
        tree, host_root, _ = self.make(tmp_path, git=True)

        assert tree.ignored(host_root, [_IGNORED, _SAME]) == {_IGNORED}

    def test_a_file_is_the_same_as_its_copy_and_not_as_a_changed_one(self, tmp_path):
        tree, host_root, pin_root = self.make(tmp_path, git=True)

        assert tree.same_file(host_root / _SAME, pin_root / _SAME)
        assert not tree.same_file(host_root / _OTHER, pin_root / _OTHER)


class TestFakeHostTree(HostTreeContract):
    def make(self, tmp_path: Path, *, git: bool):
        host_root, pin_root = tmp_path / "host", tmp_path / "pin"
        tree = FakeHostTree(
            host_root=host_root,
            pin_root=pin_root,
            host_files=[_SAME, _OTHER, _DANGLING],
            pin_files=[_SAME, _OTHER, _IGNORED],
            git=git,
            ignored=[_IGNORED],
            differing=[_OTHER],
        )
        return tree, host_root, pin_root


class TestRealHostTree(HostTreeContract):
    def make(self, tmp_path: Path, *, git: bool):
        host_root, pin_root = tmp_path / "host", tmp_path / "pin"
        (host_root / "core").mkdir(parents=True)
        (host_root / _SAME).write_text("alike\n")
        (host_root / _OTHER).write_text("on the host\n")
        os.symlink("../nowhere", host_root / _DANGLING)
        (host_root / ".gitignore").write_text("*.pyc\n")
        if git:
            _git("init", "-q", cwd=host_root)
            _git("config", "user.email", "host@example.com", cwd=host_root)
            _git("config", "user.name", "Host", cwd=host_root)
            _git("add", "-A", cwd=host_root)
            _git("commit", "-q", "-m", "world", cwd=host_root)
        (pin_root / "core").mkdir(parents=True)
        (pin_root / _SAME).write_text("alike\n")
        (pin_root / _OTHER).write_text("in the pin\n")
        (pin_root / _IGNORED).write_text("byte code\n")
        return HostTree(), host_root, pin_root


class TestChanged:
    def test_a_pin_equal_to_its_host_is_unchanged(self, made):
        assert _compare(made) is Verdict.UNCHANGED

    def test_a_content_edit_is_a_change(self, host, made):
        (host / "core" / "tools" / "tool.py").write_text("print('edited')\n")

        assert _compare(made) is Verdict.CHANGED

    def test_a_content_edit_of_the_same_size_is_a_change(self, host, made):
        # Same length, same mode: only the bytes differ, so only a byte comparison can see it.
        (host / "core" / "tools" / "tool.py").write_text("print('tracXed')\n")
        assert (host / "core" / "tools" / "tool.py").stat().st_size == (
            made.root / "core" / "tools" / "tool.py"
        ).stat().st_size

        assert _compare(made) is Verdict.CHANGED

    def test_an_untracked_not_ignored_file_in_core_is_a_change(self, host, made):
        (host / "core" / "tools" / "new_tool.py").write_text("print('new')\n")

        assert _compare(made) is Verdict.CHANGED

    def test_a_file_deleted_from_the_host_is_a_change(self, host, made):
        # Deleted from the working tree only: nothing staged, nothing committed, so
        # `git ls-files` still lists the path and the comparison must not read it as present.
        (host / ".claude" / "skills" / "example" / "SKILL.md").unlink()
        assert ".claude/skills/example/SKILL.md" in pin.host_files(host)

        assert _compare(made) is Verdict.CHANGED

    def test_an_executable_bit_alone_is_a_change(self, host, made):
        target = host / "core" / "tools" / "tool.py"
        target.chmod(target.stat().st_mode | 0o111)

        assert _compare(made) is Verdict.CHANGED


_SKILL_TARGET = "../../skills/seat/.claude/skills/g"
_OTHER_SKILL_TARGET = "../../skills/seat/.claude/skills/h"
_AGENT_TARGET = "../../skills/seat/.claude/agents/seat.md"


def _host_with_links(root: Path) -> Path:
    """A git host whose flat `.claude/` layer holds three tracked relative links into the group
    `seat`: a skill directory `g`, and an agent file. A second skill `h` exists to retarget to."""
    host = _init_git_host(root)
    for name in ("g", "h"):
        skill = host / "skills" / "seat" / ".claude" / "skills" / name
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(f"{name}\n")
    agent = host / "skills" / "seat" / ".claude" / "agents" / "seat.md"
    agent.parent.mkdir(parents=True)
    agent.write_text("seat agent\n")
    (host / ".claude" / "agents").mkdir(parents=True)
    os.symlink(_SKILL_TARGET, host / ".claude" / "skills" / "g")
    os.symlink(_AGENT_TARGET, host / ".claude" / "agents" / "seat.md")
    _git("add", "-A", cwd=host)
    _git("commit", "-q", "-m", "links", cwd=host)
    return host


class TestLinks:
    def test_host_with_links_pinned_and_untouched_is_unchanged(self, tmp_path, pins_home):
        host = _host_with_links(tmp_path / "host")
        made = pin.make(host, pins_home)

        assert _compare(made) is Verdict.UNCHANGED

    def test_a_link_retargeted_on_the_host_is_changed(self, tmp_path, pins_home):
        host = _host_with_links(tmp_path / "host")
        made = pin.make(host, pins_home)
        (host / ".claude" / "skills" / "g").unlink()
        os.symlink(_OTHER_SKILL_TARGET, host / ".claude" / "skills" / "g")

        assert _compare(made) is Verdict.CHANGED

    def test_a_link_on_the_host_and_a_file_in_the_pin_is_changed(self, tmp_path, pins_home):
        host = _host_with_links(tmp_path / "host")
        made = pin.make(host, pins_home)
        pinned = made.root / ".claude" / "agents" / "seat.md"
        pinned.unlink()
        pinned.write_text("seat agent\n")  # the bytes the host's link reads, as a plain file

        assert _compare(made) is Verdict.CHANGED

    def test_a_file_on_the_host_and_a_link_in_the_pin_is_changed(self, tmp_path, pins_home):
        host = _host_with_links(tmp_path / "host")
        made = pin.make(host, pins_home)
        on_host = host / ".claude" / "agents" / "seat.md"
        on_host.unlink()
        on_host.write_text("seat agent\n")  # the bytes the pin's link reads, as a plain file

        assert _compare(made) is Verdict.CHANGED

    def test_a_dangling_link_pinned_and_untouched_is_unchanged(self, tmp_path, pins_home):
        host = _host_with_links(tmp_path / "host")
        os.symlink("../../skills/gone/.claude/skills/x", host / ".claude" / "skills" / "x")
        made = pin.make(host, pins_home)

        assert _compare(made) is Verdict.UNCHANGED

    def test_host_without_links_behaves_as_before(self, host, made):
        assert _compare(made) is Verdict.UNCHANGED
        (host / "core" / "tools" / "tool.py").write_text("print('edited')\n")

        assert _compare(made) is Verdict.CHANGED


class TestRootLockFiles:
    def test_a_changed_lock_reads_changed(self, host, pins_home):
        (host / "uv.lock").write_text("version = 1\n")
        _git("add", "uv.lock", cwd=host)
        _git("commit", "-q", "-m", "lock", cwd=host)
        pinned = pin.make(host, pins_home)
        assert _compare(pinned) is Verdict.UNCHANGED

        (host / "uv.lock").write_text("version = 2\n")

        assert _compare(pinned) is Verdict.CHANGED

    def test_a_pin_from_before_the_lock_reads_changed(self, host, made):
        for name in (".python-version", "pyproject.toml", "uv.lock"):
            (host / name).write_text(f"{name} added after the pin\n")

        assert _compare(made) is Verdict.CHANGED

    def test_a_lock_file_deleted_from_the_host_reads_changed(self, host, pins_home):
        (host / ".python-version").write_text("3.14\n")
        pinned = pin.make(host, pins_home)
        (host / ".python-version").unlink()

        assert _compare(pinned) is Verdict.CHANGED


class TestUnchanged:
    def test_a_file_the_host_ignores_that_only_the_pin_holds_is_not_a_change(self, made):
        cache = made.root / "core" / "tools" / "__pycache__"
        cache.mkdir()
        (cache / "pin.cpython-314.pyc").write_bytes(b"\0bytecode")

        assert _compare(made) is Verdict.UNCHANGED

    def test_a_file_the_host_ignores_that_only_the_host_holds_is_not_a_change(self, host, made):
        (host / "core" / "ignored.log").write_text("noise added after the pin\n")

        assert _compare(made) is Verdict.UNCHANGED

    def test_a_file_outside_the_three_trees_is_never_considered(self, host, made):
        (host / "system" / "outside.md").write_text("edited\n")
        (host / "system" / "another.md").write_text("new\n")

        assert _compare(made) is Verdict.UNCHANGED

    def test_head_moved_only_outside_the_three_trees_is_unchanged(self, host, made):
        (host / "system" / "outside.md").write_text("committed edit\n")
        _git("add", "-A", cwd=host)
        _git("commit", "-q", "-m", "system only", cwd=host)
        assert _git("rev-parse", "HEAD", cwd=host) != made.source_head

        assert _compare(made) is Verdict.UNCHANGED

    def test_head_at_source_head_with_an_uncommitted_edit_is_changed(self, host, made):
        (host / "skills" / "grp" / "SKILL.md").write_text("edited, not committed\n")
        assert _git("rev-parse", "HEAD", cwd=host) == made.source_head

        assert _compare(made) is Verdict.CHANGED

    def test_a_host_symlink_pinned_as_a_link_and_untouched_is_unchanged(self, host, pins_home):
        (host / "core" / "real.txt").write_text("the target\n")
        (host / "core" / "link.txt").symlink_to("real.txt")
        _git("add", "-A", cwd=host)
        _git("commit", "-q", "-m", "a symlink", cwd=host)
        made = pin.make(host, pins_home)
        assert (made.root / "core" / "link.txt").is_symlink()  # the pin holds the link itself

        assert _compare(made) is Verdict.UNCHANGED


class TestNonGitHost:
    def test_a_non_git_host_considers_every_file(self, tmp_path, pins_home):
        plain = tmp_path / "plain"
        (plain / "core").mkdir(parents=True)
        (plain / "core" / "tool.py").write_text("print('whole')\n")
        (plain / ".gitignore").write_text("*.log\n")
        made = pin.make(plain, pins_home)
        assert _compare(made) is Verdict.UNCHANGED

        (plain / "core" / "noise.log").write_text("a .gitignore here would match this\n")

        assert _compare(made) is Verdict.CHANGED


class TestHostGone:
    def test_a_missing_host_is_host_gone(self, host, made):
        shutil.rmtree(host)

        assert _compare(made) is Verdict.HOST_GONE


class TestCli:
    def test_the_cli_prints_the_verdict_and_the_host(self, host, made, tmp_path):
        unchanged = _run_cli(made.root)

        (host / "core" / "tools" / "tool.py").write_text("print('edited')\n")
        changed = _run_cli(made.root)

        shutil.rmtree(host)
        gone = _run_cli(made.root)

        assert (unchanged.returncode, changed.returncode, gone.returncode) == (0, 0, 0)
        expected_host = str(made.source_host_root)
        assert unchanged.stdout.splitlines() == ["verdict=unchanged", f"host={expected_host}"]
        assert changed.stdout.splitlines() == ["verdict=changed", f"host={expected_host}"]
        assert gone.stdout.splitlines() == ["verdict=host-gone", f"host={expected_host}"]

    def test_the_cli_refuses_a_path_that_is_not_a_pin(self, tmp_path):
        not_a_pin = tmp_path / "empty"
        not_a_pin.mkdir()

        result = _run_cli(not_a_pin, script=_TOOLS / "pin_host_changed.py")

        assert result.returncode != 0
        assert result.stdout == ""
        assert str(not_a_pin) in result.stderr

    def test_the_comparison_writes_nothing_into_the_pin(self, host, made):
        # The pin's own core/tools holds a real pin.py and pin_host_changed.py for the CLI to
        # import — the shape a pinned launch runs in. A bytecode write there would add a file.
        assert (made.root / "core" / "tools" / "pin.py").is_file()
        before = _snapshot(made.root)
        (host / "core" / "tools" / "tool.py").write_text("print('edited')\n")

        result = _run_cli(made.root)

        assert result.returncode == 0, result.stderr
        assert _snapshot(made.root) == before
        assert not list(made.root.rglob("__pycache__"))


class TestHeader:
    @pytest.mark.parametrize(
        "phrase",
        [
            "core/",
            ".claude/",
            "skills/",
            ".python-version",
            "pyproject.toml",
            "uv.lock",
            "uncommitted",
            "ignored",
            "journey",
            "product",
        ],
    )
    def test_the_header_states_what_changed_means(self, phrase):
        assert phrase in (pin_host_changed.__doc__ or "")
