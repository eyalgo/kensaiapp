"""Tests for `check_brief_quotes.py` — runs the real script on a real brief file, against a small
repo holding the files the brief cites. The guard it reaches is the host's real one."""

import subprocess
import sys
from pathlib import Path

_TOOL = Path(__file__).resolve().parent / "check_brief_quotes.py"


def _repo(tmp_path: Path) -> Path:
    root = tmp_path / "instance"
    (root / "docs").mkdir(parents=True)
    (root / "docs" / "note.md").write_text(
        "# Note\n\nthe cut reads the owner's words\nsomething else entirely\n"
    )
    return root


def _run(brief: Path, root: Path):
    return subprocess.run(
        [sys.executable, str(_TOOL), str(brief), "--root", str(root)],
        capture_output=True,
        text=True,
    )


def test_a_quote_at_its_lines_passes(tmp_path):
    root = _repo(tmp_path)
    brief = tmp_path / "brief.md"
    brief.write_text('The ask: docs/note.md:L3 "the cut reads the owner\'s words"\n')
    result = _run(brief, root)
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout == ""


def test_a_quote_on_other_lines_is_named_with_where_it_is(tmp_path):
    root = _repo(tmp_path)
    brief = tmp_path / "brief.md"
    brief.write_text('The ask: docs/note.md:L4 "the cut reads the owner\'s words"\n')
    result = _run(brief, root)
    assert result.returncode == 1
    assert "docs/note.md:4" in result.stdout and "is at docs/note.md:" in result.stdout


def test_a_quote_nowhere_in_the_file_is_named(tmp_path):
    root = _repo(tmp_path)
    brief = tmp_path / "brief.md"
    brief.write_text('The ask: docs/note.md:L3 "words the owner never wrote here"\n')
    result = _run(brief, root)
    assert result.returncode == 1
    assert "is not in this file" in result.stdout


def test_an_unresolvable_path_is_skipped_not_reported(tmp_path):
    root = _repo(tmp_path)
    brief = tmp_path / "brief.md"
    brief.write_text('Elsewhere: other/repo/file.md:L3 "anything at all, unprovable"\n')
    result = _run(brief, root)
    assert result.returncode == 0, result.stdout


def test_a_missing_brief_exits_2(tmp_path):
    result = _run(tmp_path / "absent.md", tmp_path)
    assert result.returncode == 2
    assert "cannot check" in result.stderr


def test_every_run_counts_what_it_checked_and_skipped(tmp_path):
    root = _repo(tmp_path)
    brief = tmp_path / "brief.md"
    brief.write_text(
        'docs/note.md:L3 "the cut reads the owner\'s words"\n\n'
        'other/repo/file.md:L3 "anything at all, unprovable"\n'
    )
    result = _run(brief, root)
    assert result.returncode == 0, result.stdout
    assert "2 citations: 1 checked" in result.stderr and "1 skipped as unresolvable" in result.stderr


def test_a_wrong_root_is_visible_as_nothing_checked(tmp_path):
    _repo(tmp_path)
    brief = tmp_path / "brief.md"
    brief.write_text('docs/note.md:L3 "words the owner never wrote here"\n')
    result = _run(brief, tmp_path / "elsewhere")
    assert result.returncode == 0
    assert "1 citations: 0 checked" in result.stderr


def test_a_quote_past_the_window_is_named_with_why(tmp_path):
    root = _repo(tmp_path)
    brief = tmp_path / "brief.md"
    brief.write_text("docs/note.md:L3\n\n\"the cut reads the owner's words\"\n")
    result = _run(brief, root)
    assert result.returncode == 1
    assert "cited with no quoted text" in result.stdout and "300 characters" in result.stdout
