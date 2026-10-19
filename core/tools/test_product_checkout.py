"""The product checkout reader's suite — `Checkout` against real git repos under `tmp_path`,
`left_dirty` as the pure comparison it is.

The reader is the one place the three chain engines learn what a run left in the product checkout,
so the readings here are made by the real command, never a stand-in for it.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import product_checkout
from product_checkout import Checkout, left_dirty

PATH = "/work/product"


def git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), "-c", "user.name=Test", "-c", "user.email=test@example.com",
         *args],
        check=True, capture_output=True)


def init_repo(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    git(path, "init", "-q")
    return path


def committed_repo(path: Path, name: str = "tracked.txt") -> Path:
    init_repo(path)
    (path / name).write_text("one\n")
    git(path, "add", name)
    git(path, "commit", "-q", "-m", "first")
    return path


# --- Checkout.entries ---------------------------------------------------------------------


def test_entries_lists_each_untracked_file_on_its_own_line(tmp_path):
    repo = init_repo(tmp_path / "repo")
    (repo / "nested" / "deeper").mkdir(parents=True)
    (repo / "nested" / "a.txt").write_text("a")
    (repo / "nested" / "deeper" / "b.txt").write_text("b")

    assert Checkout().entries(str(repo)) == ["?? nested/a.txt", "?? nested/deeper/b.txt"]


def test_entries_lists_a_modified_tracked_file(tmp_path):
    repo = committed_repo(tmp_path / "repo")
    (repo / "tracked.txt").write_text("two\n")

    assert Checkout().entries(str(repo)) == [" M tracked.txt"]


def test_entries_leaves_out_ignored_files(tmp_path):
    repo = committed_repo(tmp_path / "repo")
    (repo / ".gitignore").write_text("logs/\n")
    git(repo, "add", ".gitignore")
    git(repo, "commit", "-q", "-m", "ignore")
    (repo / "logs").mkdir()
    (repo / "logs" / "run.log").write_text("x")

    assert Checkout().entries(str(repo)) == []


def test_entries_is_empty_for_a_clean_checkout(tmp_path):
    repo = committed_repo(tmp_path / "repo")

    assert Checkout().entries(str(repo)) == []


def test_entries_from_a_subfolder_reads_only_that_folder(tmp_path):
    repo = committed_repo(tmp_path / "repo")
    (repo / "sub").mkdir()
    (repo / "at_root.txt").write_text("x")
    (repo / "sub" / "inside.txt").write_text("x")

    assert Checkout().entries(str(repo / "sub")) == ["?? sub/inside.txt"]


def test_entries_from_a_subfolder_ignores_another_folders_edit(tmp_path):
    repo = committed_repo(tmp_path / "repo")
    (repo / "product").mkdir()
    (repo / "other").mkdir()
    (repo / "other" / "notes.md").write_text("x")

    assert Checkout().entries(str(repo / "product")) == []


def test_entries_is_none_outside_a_work_tree(tmp_path):
    plain = tmp_path / "plain"
    plain.mkdir()

    assert Checkout().entries(str(plain)) is None


def test_entries_is_none_for_an_empty_path():
    assert Checkout().entries("") is None


# --- left_dirty ---------------------------------------------------------------------------


def test_left_dirty_is_none_when_nothing_was_recorded_at_launch():
    assert left_dirty(None, ["?? a.txt"], PATH) is None
    assert left_dirty(None, None, PATH) is None
    assert left_dirty(None, [], PATH) is None


def test_left_dirty_is_none_when_no_entry_is_new():
    before = ["?? a.txt", " M b.txt"]

    assert left_dirty(before, list(before), PATH) is None
    assert left_dirty(before, ["?? a.txt"], PATH) is None
    assert left_dirty(before, [], PATH) is None


def test_left_dirty_names_the_path_and_each_new_entry():
    reason = left_dirty([], ["?? a.txt", " M b.txt"], PATH)

    assert reason == (
        "`git status --porcelain` in the product checkout /work/product shows entries it did not "
        "show when the run launched: `?? a.txt`, ` M b.txt`")


def test_left_dirty_never_counts_an_entry_present_at_launch():
    reason = left_dirty([" M old.txt"], [" M old.txt", "?? new.txt"], PATH)

    assert "`?? new.txt`" in reason
    assert "old.txt" not in reason


def test_left_dirty_names_five_entries_and_counts_the_rest():
    after = [f"?? file{number}.txt" for number in range(8)]

    reason = left_dirty([], after, PATH)

    assert reason.endswith(
        ": `?? file0.txt`, `?? file1.txt`, `?? file2.txt`, `?? file3.txt`, `?? file4.txt`, "
        "and 3 more")
    assert "file5.txt" not in reason


def test_left_dirty_names_the_path_when_the_checkout_cannot_be_read_after():
    reason = left_dirty(["?? a.txt"], None, PATH)

    assert reason == (
        "the product checkout /work/product could not be read with `git status --porcelain` when "
        "the run ended, so whether it gained entries is not known")


def test_left_dirty_names_exactly_five_without_a_remainder():
    after = [f"?? file{number}.txt" for number in range(5)]

    assert "more" not in left_dirty([], after, PATH)


def test_the_module_carries_its_version_marker():
    # The shape, never a literal: a merge's --bump lands after the suite that cleared it.
    assert re.fullmatch(r"\d+\.\d+\.\d+", product_checkout.__version__)


# --- added by the code-integrity review ----------------------------------------------------


def test_entries_is_none_for_a_path_that_does_not_exist(tmp_path):
    """CP-509 and the unreadable reason's own advice ("check that the path still exists"): a
    checkout that has gone is unreadable, never empty."""
    assert Checkout().entries(str(tmp_path / "gone")) is None


def test_entries_is_none_when_git_cannot_start(tmp_path, monkeypatch):
    """CP-509, "the status command fails": a `git` that cannot be started at all answers `None`,
    not an exception the engine would carry into its advance."""
    monkeypatch.setenv("PATH", str(tmp_path))

    assert Checkout().entries(str(tmp_path)) is None


def test_entries_never_writes_the_checkouts_index(tmp_path):
    """The guard reads and never writes the checkout (change_spec.md, Out of Scope). A plain
    `git status` refreshes a stale index entry by rewriting `.git/index` — a write into the
    shared checkout, under a lock a concurrent commit there can collide with."""
    repo = committed_repo(tmp_path / "repo")
    tracked = repo / "tracked.txt"
    stat = tracked.stat()
    os.utime(tracked, (stat.st_atime + 100, stat.st_mtime + 100))
    index = (repo / ".git" / "index").read_bytes()

    assert Checkout().entries(str(repo)) == []
    assert (repo / ".git" / "index").read_bytes() == index
