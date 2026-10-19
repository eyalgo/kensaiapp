"""Contract tests for `pin_host_changed.py` — does a pin's source host differ from the pin?

Isolation: every test builds its own throwaway host under `tmp_path` and makes its pin into a
sibling directory, so nothing here reads or writes the real `~/.kensaiapp/pins/`. The host is a
real git work tree wherever the case needs git's ignore rules and `HEAD`; the non-git case builds
a plain directory.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import pin
import pin_host_changed
from pin_host_changed import Verdict

_TOOLS = Path(__file__).parent


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


class TestChanged:
    def test_a_pin_equal_to_its_host_is_unchanged(self, made):
        assert pin_host_changed.compare(made) is Verdict.UNCHANGED

    def test_a_content_edit_is_a_change(self, host, made):
        (host / "core" / "tools" / "tool.py").write_text("print('edited')\n")

        assert pin_host_changed.compare(made) is Verdict.CHANGED

    def test_a_content_edit_of_the_same_size_is_a_change(self, host, made):
        # Same length, same mode: only the bytes differ, so only a byte comparison can see it.
        (host / "core" / "tools" / "tool.py").write_text("print('tracXed')\n")
        assert (host / "core" / "tools" / "tool.py").stat().st_size == (
            made.root / "core" / "tools" / "tool.py"
        ).stat().st_size

        assert pin_host_changed.compare(made) is Verdict.CHANGED

    def test_an_untracked_not_ignored_file_in_core_is_a_change(self, host, made):
        (host / "core" / "tools" / "new_tool.py").write_text("print('new')\n")

        assert pin_host_changed.compare(made) is Verdict.CHANGED

    def test_a_file_deleted_from_the_host_is_a_change(self, host, made):
        # Deleted from the working tree only: nothing staged, nothing committed, so
        # `git ls-files` still lists the path and the comparison must not read it as present.
        (host / ".claude" / "skills" / "example" / "SKILL.md").unlink()
        assert ".claude/skills/example/SKILL.md" in pin.host_files(host)

        assert pin_host_changed.compare(made) is Verdict.CHANGED

    def test_an_executable_bit_alone_is_a_change(self, host, made):
        target = host / "core" / "tools" / "tool.py"
        target.chmod(target.stat().st_mode | 0o111)

        assert pin_host_changed.compare(made) is Verdict.CHANGED


class TestUnchanged:
    def test_a_file_the_host_ignores_that_only_the_pin_holds_is_not_a_change(self, made):
        cache = made.root / "core" / "tools" / "__pycache__"
        cache.mkdir()
        (cache / "pin.cpython-314.pyc").write_bytes(b"\0bytecode")

        assert pin_host_changed.compare(made) is Verdict.UNCHANGED

    def test_a_file_the_host_ignores_that_only_the_host_holds_is_not_a_change(self, host, made):
        (host / "core" / "ignored.log").write_text("noise added after the pin\n")

        assert pin_host_changed.compare(made) is Verdict.UNCHANGED

    def test_a_file_outside_the_three_trees_is_never_considered(self, host, made):
        (host / "system" / "outside.md").write_text("edited\n")
        (host / "system" / "another.md").write_text("new\n")

        assert pin_host_changed.compare(made) is Verdict.UNCHANGED

    def test_head_moved_only_outside_the_three_trees_is_unchanged(self, host, made):
        (host / "system" / "outside.md").write_text("committed edit\n")
        _git("add", "-A", cwd=host)
        _git("commit", "-q", "-m", "system only", cwd=host)
        assert _git("rev-parse", "HEAD", cwd=host) != made.source_head

        assert pin_host_changed.compare(made) is Verdict.UNCHANGED

    def test_head_at_source_head_with_an_uncommitted_edit_is_changed(self, host, made):
        (host / "skills" / "grp" / "SKILL.md").write_text("edited, not committed\n")
        assert _git("rev-parse", "HEAD", cwd=host) == made.source_head

        assert pin_host_changed.compare(made) is Verdict.CHANGED

    def test_a_host_symlink_equal_in_content_to_the_pins_copy_is_unchanged(
        self, host, pins_home
    ):
        (host / "core" / "real.txt").write_text("the target\n")
        (host / "core" / "link.txt").symlink_to("real.txt")
        _git("add", "-A", cwd=host)
        _git("commit", "-q", "-m", "a symlink", cwd=host)
        made = pin.make(host, pins_home)
        assert not (made.root / "core" / "link.txt").is_symlink()  # the pin holds a regular copy

        assert pin_host_changed.compare(made) is Verdict.UNCHANGED


class TestNonGitHost:
    def test_a_non_git_host_considers_every_file(self, tmp_path, pins_home):
        plain = tmp_path / "plain"
        (plain / "core").mkdir(parents=True)
        (plain / "core" / "tool.py").write_text("print('whole')\n")
        (plain / ".gitignore").write_text("*.log\n")
        made = pin.make(plain, pins_home)
        assert pin_host_changed.compare(made) is Verdict.UNCHANGED

        (plain / "core" / "noise.log").write_text("a .gitignore here would match this\n")

        assert pin_host_changed.compare(made) is Verdict.CHANGED


class TestHostGone:
    def test_a_missing_host_is_host_gone(self, host, made):
        shutil.rmtree(host)

        assert pin_host_changed.compare(made) is Verdict.HOST_GONE


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
        "phrase", ["core/", ".claude/", "skills/", "uncommitted", "ignored", "journey", "product"]
    )
    def test_the_header_states_what_changed_means(self, phrase):
        assert phrase in (pin_host_changed.__doc__ or "")
