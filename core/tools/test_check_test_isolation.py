"""check_test_isolation.py — every kind, each end of its pattern, and both modes.

Every input is made here: a throwaway repo under `tmp_path`, its own projects and commits, and a home
handed to the check rather than read off the machine — this file is held to the rule it tests.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

import check_test_isolation as cti

HOME = "/home/someone-made-up"


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", *args],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def _sha_shaped(sha: str) -> bool:
    """Whether the check reads both `sha` and its nine-character prefix as a SHA."""
    return all(cti.HEX_TOKEN.fullmatch(form) for form in (sha, sha[:9]))


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "system" / "projects" / "alpha" / "docs").mkdir(parents=True)
    (root / "system" / "projects" / "alpha" / "docs" / "note.md").write_text("x\n")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "--no-verify", "-m", "seed")
    # The commit tests quote HEAD and its nine-character prefix, and the check reads a token as a
    # SHA only when it holds a digit and a letter (`HEX_TOKEN`). About one prefix in seventy is
    # all digits, so the head is re-rolled with empty commits until both forms are SHA-shaped.
    while not _sha_shaped(_git(root, "rev-parse", "HEAD")):
        _git(root, "commit", "-q", "--no-verify", "--allow-empty", "-m", "re-roll the head")
    return root


def _scan(repo: Path, path: str, text: str) -> list[cti.Hit]:
    r = cti.Repo(repo)
    return cti.scan_text(
        path, text, home=HOME, projects=r.projects(), exists=r.exists, commits=r.commits
    )


def _kinds(hits: list[cti.Hit]) -> list[str]:
    return [hit.kind for hit in hits]


class TestTestFile:
    @pytest.mark.parametrize(
        "path",
        [
            "tests/a.py",
            "pkg/test/a.rs",
            "web/__tests__/a.js",
            "spec/a.rb",
            "core/tools/test_x.py",
            "x_test.go",
            "a.test.ts",
            "a.spec.js",
            "conftest.py",
            "AppTests.swift",
            "AppTest.swift",
            "checks/a.bats",
            "core/tools/launcher_telemetry_test_support.py",
            "core/tools/test_support_python3_stub.py",
        ],
    )
    def test_named_as_a_test(self, path):
        assert cti.is_test_file(path)

    @pytest.mark.parametrize("path", ["core/tools/x.py", "docs/testing.md", "src/latest.py"])
    def test_not_a_test(self, path):
        assert not cti.is_test_file(path)


class TestHomePath:
    def test_the_running_home_written_out_is_a_hit(self, repo):
        assert _kinds(_scan(repo, "tests/a.py", f'p = "{HOME}/notes"\n')) == ["home-path"]

    def test_another_home_is_not(self, repo):
        assert _scan(repo, "tests/a.py", 'p = "/home/elsewhere/notes"\n') == []


class TestHomeLookup:
    @pytest.mark.parametrize(
        "line",
        [
            "root = Path.home() / 'x'",  # test-isolation: allowed — fixture text for the check
            "p = os.path.expanduser('~/x')",  # test-isolation: allowed — fixture text for the check
            "h = os.environ['HOME']",  # test-isolation: allowed — fixture text for the check
            'h = os.environ.get("HOME")',  # test-isolation: allowed — fixture text for the check
            'h = os.getenv("HOME")',  # test-isolation: allowed — fixture text for the check
            "const h = process.env.HOME;",  # test-isolation: allowed — fixture text for the check
            "const h = os.homedir();",  # test-isolation: allowed — fixture text for the check
            "let h = dirs::home_dir();",  # test-isolation: allowed — fixture text for the check
            'let h = std::env::var("HOME");',  # test-isolation: allowed — fixture text for the check
            "let h = FileManager.default.homeDirectoryForCurrentUser",  # test-isolation: allowed — fixture text for the check
            "let h = NSHomeDirectory()",  # test-isolation: allowed — fixture text for the check
            'const h = process.env["HOME"];',  # test-isolation: allowed — fixture text for the check
            "const h = process.env.USERPROFILE;",  # test-isolation: allowed — fixture text for the check
            "h = os.environ['USERPROFILE']",  # test-isolation: allowed — fixture text for the check
            'p = os.path.expandvars("$HOME/x")',  # test-isolation: allowed — fixture text for the check
            'let h = std::env::var_os("HOME");',  # test-isolation: allowed — fixture text for the check
            "h, _ := os.UserHomeDir()",  # test-isolation: allowed — fixture text for the check
        ],
    )
    def test_a_read_is_a_hit(self, repo, line):
        assert _kinds(_scan(repo, "tests/a.py", line + "\n")) == ["home-lookup"]

    @pytest.mark.parametrize(
        "line",
        [
            'monkeypatch.setenv("HOME", str(tmp_path))',
            "os.environ['HOME'] = str(tmp_path)",
            'env = {"HOME": str(tmp_path)}',
            'expected = "~/x expands to {home}/x"',
            'run("cat $HOME/.env")',
        ],
    )
    def test_a_write_or_text_is_not(self, repo, line):
        assert _scan(repo, "tests/a.py", line + "\n") == []

    def test_a_comparison_is_still_a_read(self, repo):
        line = "assert os.environ['HOME'] == x"  # test-isolation: allowed — fixture text for the check
        assert _kinds(_scan(repo, "tests/a.py", line + "\n")) == ["home-lookup"]


class TestPrivateProject:
    def test_a_real_path_in_a_real_project_is_a_hit(self, repo):
        hits = _scan(repo, "tests/a.py", 'p = root / "system/projects/alpha/docs/note.md"\n')
        assert _kinds(hits) == ["private-project"]

    def test_the_project_folder_itself_is_a_hit(self, repo):
        assert _kinds(_scan(repo, "tests/a.py", 'p = "system/projects/alpha"\n')) == ["private-project"]

    def test_a_made_up_path_under_a_real_project_is_not(self, repo):
        assert _scan(repo, "tests/a.py", 'parse("system/projects/alpha/journey/x.md")\n') == []

    def test_a_project_that_does_not_exist_is_not(self, repo):
        assert _scan(repo, "tests/a.py", '"system/projects/<name>/docs"\n') == []

    def test_a_project_reading_itself_is_not(self, repo):
        path = "system/projects/alpha/tests/test_a.py"
        assert _scan(repo, path, '"system/projects/alpha/docs/note.md"\n') == []

    def test_the_instances_own_check_reading_its_tree_is_not(self, repo):
        path = "system/tests/test_tree.py"
        assert _scan(repo, path, 'p = root / "system/projects/alpha/docs/note.md"\n') == []

    def test_a_comment_citing_a_real_path_is_not(self, repo):
        assert _scan(repo, "tests/a.py", "# see system/projects/alpha/docs/note.md\n") == []


class TestCommit:
    def test_a_quoted_real_commit_is_a_hit(self, repo):
        sha = _git(repo, "rev-parse", "HEAD")
        assert _kinds(_scan(repo, "tests/a.py", f'BASE = "{sha}"\n')) == ["commit"]
        assert _kinds(_scan(repo, "tests/a.py", f"BASE = '{sha[:9]}'\n")) == ["commit"]

    def test_a_cited_commit_is_not(self, repo):
        sha = _git(repo, "rev-parse", "HEAD")
        assert _scan(repo, "tests/a.py", f"# fixed at `{sha[:9]}`\n") == []

    def test_a_made_up_sha_is_not(self, repo):
        assert _scan(repo, "tests/a.py", 'BASE = "abc1234def5678"\n') == []

    def test_a_commit_inside_a_longer_string_is_a_hit(self, repo):
        sha = _git(repo, "rev-parse", "HEAD")[:9]
        assert _kinds(_scan(repo, "tests/a.py", f'run("git diff {sha}..HEAD")\n')) == ["commit"]
        assert _kinds(_scan(repo, "tests/a.py", f'args = ["--base={sha}"]\n')) == ["commit"]

    def test_a_commit_in_a_docstring_is_not(self, repo):
        sha = _git(repo, "rev-parse", "HEAD")[:9]
        text = f'def test_x():\n    """Fixed at {sha}, see there."""\n    assert True\n'
        assert _scan(repo, "tests/a.py", text) == []

    def test_a_commit_in_recorded_data_is_not(self, repo):
        sha = _git(repo, "rev-parse", "HEAD")
        assert _scan(repo, "tests/capture.json", f'{{"commit": "{sha}"}}\n') == []

    def test_a_tree_is_not_a_commit(self, repo):
        tree = _git(repo, "rev-parse", "HEAD^{tree}")
        assert _scan(repo, "tests/a.py", f'T = "{tree}"\n') == []


class TestComments:
    def test_a_home_lookup_in_a_comment_is_not(self, repo):
        assert _scan(repo, "tests/a.py", "# both read Path.home(), so we patch it\n") == []  # test-isolation: allowed — fixture text for the check

    def test_a_home_lookup_in_a_docstring_is_not(self, repo):
        text = '"""Both read Path.home() so we patch it."""\nx = 1\n'  # test-isolation: allowed — fixture text for the check
        assert _scan(repo, "tests/a.py", text) == []

    def test_a_home_lookup_in_a_js_line_comment_is_not(self, repo):
        assert _scan(repo, "a.test.js", "// os.homedir() is mocked below\n") == []  # test-isolation: allowed — fixture text for the check

    def test_the_real_home_in_a_comment_is_still_a_hit(self, repo):
        assert _kinds(_scan(repo, "tests/a.py", f"# ran at {HOME}/x\n")) == ["home-path"]

    def test_a_file_that_does_not_tokenize_falls_back_to_line_comments(self, repo):
        text = "def broken(:\n# Path.home() here\nx = Path.home()\n"  # test-isolation: allowed — fixture text for the check
        hits = _scan(repo, "tests/a.py", text)
        assert [(h.line, h.kind) for h in hits] == [(3, "home-lookup")]


class TestShell:
    def test_a_home_read_in_a_shell_test_is_a_hit(self, repo):
        assert _kinds(_scan(repo, "tests/t.bats", 'run cat "$HOME/.claude/settings.json"\n')) == ["home-lookup"]
        assert _kinds(_scan(repo, "tests/t.sh", "ls ~/projects\n")) == ["home-lookup"]

    def test_a_shell_test_that_sets_its_own_home_is_not(self, repo):
        text = 'export HOME="$BATS_TEST_TMPDIR"\nrun cat "$HOME/x"\n'
        assert _scan(repo, "tests/t.bats", text) == []

    def test_dollar_home_in_a_python_string_is_not(self, repo):
        assert _scan(repo, "tests/a.py", 'run("cat $HOME/.env")\n') == []


class TestExcuse:
    def test_a_reasoned_excuse_clears_the_line(self, repo):
        line = f'p = "{HOME}"  # test-isolation: allowed — the guard\'s own subject\n'
        assert _scan(repo, "tests/a.py", line) == []

    def test_an_excuse_with_no_reason_clears_nothing(self, repo):
        line = f'p = "{HOME}"  # test-isolation: allowed —\n'
        assert _kinds(_scan(repo, "tests/a.py", line)) == ["home-path"]


class TestOneLineOnce:
    def test_several_kinds_on_one_line_report_once(self, repo):
        line = f'p = Path.home() / "{HOME}"'  # test-isolation: allowed — fixture text for the check
        hits = _scan(repo, "tests/a.py", line + "\n")
        assert _kinds(hits) == ["home-path+home-lookup"]


class TestMain:
    def _stage(self, repo: Path, relative: str, text: str) -> None:
        (repo / relative).parent.mkdir(parents=True, exist_ok=True)
        (repo / relative).write_text(text)
        _git(repo, "add", relative)

    def test_staged_reads_the_index_and_only_test_files(self, repo, capsys):
        self._stage(repo, "tests/test_a.py", f'P = "{HOME}/x"\n')
        self._stage(repo, "src/a.py", f'P = "{HOME}/x"\n')
        (repo / "tests" / "test_a.py").write_text("clean = 1\n")  # the working tree differs

        assert cti.main(["--staged", "--repo", str(repo)], home=HOME) == 1
        err = capsys.readouterr().err
        assert f"tests/test_a.py:1: [home-path] P = \"{HOME}/x\"" in err
        assert "src/a.py" not in err
        assert "1 lines in 1 test files" in err
        assert "testing_doctrine.md" in err
        assert "test-isolation: allowed — <reason>" in err
        assert "Fix these lines on this branch" in err
        assert "found_while_walking.md" in err

    def test_staged_clean_exits_zero_and_prints_nothing(self, repo, capsys):
        self._stage(repo, "tests/test_a.py", "x = 1\n")
        assert cti.main(["--staged", "--repo", str(repo)], home=HOME) == 0
        assert capsys.readouterr().err == ""

    def test_staged_ignores_a_deletion(self, repo):
        self._stage(repo, "tests/test_a.py", f'P = "{HOME}"  # test-isolation: allowed — seed\n')
        _git(repo, "commit", "-q", "--no-verify", "-m", "add")
        _git(repo, "rm", "-q", "tests/test_a.py")
        assert cti.main(["--staged", "--repo", str(repo)], home=HOME) == 0

    def test_all_reads_every_tracked_test_file(self, repo, capsys):
        self._stage(repo, "tests/test_a.py", f'P = "{HOME}/x"\n')
        _git(repo, "commit", "-q", "--no-verify", "-m", "add")
        assert cti.main(["--all", "--repo", str(repo)], home=HOME) == 1
        assert "tests/test_a.py:1: [home-path]" in capsys.readouterr().err

    def test_a_binary_test_file_is_skipped(self, repo):
        (repo / "tests").mkdir()
        (repo / "tests" / "blob.bin").write_bytes(b"\xff\xfe\x00")
        _git(repo, "add", "tests/blob.bin")
        assert cti.main(["--all", "--repo", str(repo)], home=HOME) == 0
