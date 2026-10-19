"""drop.py's refusals, move, teardown and report — on real temporary git repos, with real git.

Nothing here patches drop: the instance root and the git runner are handed to each function, and
the runner is the real one. A worktree, a branch, a SHA and a staged rename are git's own facts, so
they are read back from git and never from a fake.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import drop  # noqa: E402

PROJECT = "demo"
KEY = "2026-09-19_a-change"
SEALED_KEY = "2026-01-01_sealed"
GIT = drop.run_git

JOURNEY = Path("system") / "projects" / PROJECT / "journey"
CONTEXT = Path("system") / "projects" / PROJECT / "contexts" / "CONTEXT_PM.md"

CONTEXT_OPEN = f"""# Project Context — demo

## Current change — PM view

**Status:** Open

`{KEY}` is the only change unit on station `2026-09-19_a-station`.

**Scope boundary:** the station's guardrail.

## Something else

**Status:** Open
"""

SEED_TWO_LEFT = "# a seed\n\n- [x] first item\n- [ ] second item\n- [ ] third item\n"
SEED_ALL_TICKED = "# a seed\n\n- [x] first item\n- [x] second item\n"


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True
    ).stdout


def write(root: Path, relative: Path | str, content: str | bytes) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")


def init_repo(path: Path) -> Path:
    path.mkdir()
    git(path, "init", "-q", "-b", "main")
    git(path, "config", "user.email", "test@example.com")
    git(path, "config", "user.name", "Test")
    git(path, "config", "commit.gpgsign", "false")
    return path


def make_instance(
    tmp_path: Path,
    *,
    seed: str | None = SEED_TWO_LEFT,
    station: bool = True,
    context: str | None = CONTEXT_OPEN,
    product_path: str = ".claude",
) -> Path:
    repo = init_repo(tmp_path / "instance")
    project = Path("system") / "projects" / PROJECT
    write(repo, ".gitignore", ".worktrees/\n")
    write(repo, project / "project.md", f"# demo\n\n**Product path:** {product_path}\n")
    if context is not None:
        write(repo, CONTEXT, context)
    write(repo, JOURNEY / "nemawashi" / "README.md", "readme\n")
    if seed is not None:
        write(repo, JOURNEY / "nemawashi" / "2026-09-19_a-seed.md", seed)
    write(repo, JOURNEY / "shukuba" / "README.md", "readme\n")
    if station:
        write(repo, JOURNEY / "shukuba" / "2026-09-19_a-station.md", "# a station\n")
    write(repo, JOURNEY / "tobiishi" / "trail" / SEALED_KEY / "change_request.md", "sealed\n")
    write(repo, JOURNEY / "tobiishi" / KEY / "change_request.md", "# request\r\n")
    write(repo, JOURNEY / "tobiishi" / KEY / "notes" / "raw.bin", b"\xff\x00\r\n tail")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "init")
    return repo.resolve()


def make_product(tmp_path: Path, ahead: int = 1) -> Path:
    product = init_repo(tmp_path / "product")
    write(product, "README.md", "product\n")
    git(product, "add", "-A")
    git(product, "commit", "-q", "-m", "init")
    add_worktree(product, KEY, ahead=ahead)
    return product.resolve()


def add_worktree(repo: Path, name: str, ahead: int = 0) -> Path:
    path = repo / ".worktrees" / name
    git(repo, "worktree", "add", "-q", str(path), "-b", name)
    for number in range(ahead):
        write(path, f"work-{number}.txt", f"{number}\n")
        git(path, "add", f"work-{number}.txt")
        git(path, "commit", "-q", "-m", f"work {number}")
    return path


def sha(repo: Path, branch: str) -> str:
    return git(repo, "rev-parse", f"refs/heads/{branch}").strip()


def branches(repo: Path) -> set[str]:
    return set(git(repo, "for-each-ref", "--format=%(refname:short)", "refs/heads").split())


def dirty(worktree: Path) -> None:
    write(worktree, "change_request.md", "edited\n")


def state(repo: Path) -> tuple[dict[str, bytes], str, str]:
    """Everything a refusal must leave alone: file bytes, the index, and the worktree list."""
    files = {
        str(p.relative_to(repo)): p.read_bytes()
        for p in sorted(repo.rglob("*"))
        if p.is_file() and p.relative_to(repo).parts[0] not in {".git", ".worktrees"}
    }
    return files, git(repo, "status", "--porcelain"), git(repo, "worktree", "list", "--porcelain")


def tree_bytes(folder: Path) -> dict[str, bytes]:
    return {
        str(p.relative_to(folder)): p.read_bytes() for p in sorted(folder.rglob("*")) if p.is_file()
    }


def unit(repo: Path, where: str = "") -> Path:
    return repo / JOURNEY / "tobiishi" / where / KEY


def named(refusal) -> set[str]:
    """The worktree paths a refusal lists, one per line — whole lines, since one path is a
    prefix of another (`.worktrees/<key>` and `.worktrees/<key>__audit-specs`)."""
    return {line.strip() for line in str(refusal.value).splitlines()[1:]}


def run(capsys, repo: Path, *args: str) -> tuple[int, str, str]:
    code = drop.main(["--root", str(repo), *args])
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def apply_output(capsys, repo: Path) -> tuple[list[str], str]:
    code, out, _ = run(capsys, repo, "apply", PROJECT, KEY)
    assert code == 0
    lines = out.splitlines()
    return lines[:-1], lines[-1]


# --- check: CP-137, CP-138 -------------------------------------------------------------------


def test_check_refuses_a_blank_reason(tmp_path):
    repo = make_instance(tmp_path)
    before = state(repo)
    for reason in ("", "   \t "):
        with pytest.raises(drop.Refused, match="reason.*missing"):
            drop.check(repo, PROJECT, KEY, reason, GIT)
    assert state(repo) == before


def test_check_refuses_a_sealed_key(tmp_path):
    repo = make_instance(tmp_path)
    before = state(repo)
    with pytest.raises(drop.Refused, match="sealed"):
        drop.check(repo, PROJECT, SEALED_KEY, "gone", GIT)
    assert state(repo) == before


def test_check_refuses_a_key_already_in_tobiishi_drop(tmp_path):
    repo = make_instance(tmp_path)
    write(repo, JOURNEY / "tobiishi" / "drop" / "2026-02-02_old" / "change_request.md", "old\n")
    before = state(repo)
    with pytest.raises(drop.Refused, match="already dropped"):
        drop.check(repo, PROJECT, "2026-02-02_old", "gone", GIT)
    assert state(repo) == before


@pytest.mark.parametrize("key", [f"trail/{SEALED_KEY}", f"{KEY}/notes", ".", "..", "README.md"])
def test_check_refuses_a_key_that_is_not_a_folder_directly_under_tobiishi(tmp_path, key):
    """CP-138: the key must name a folder directly under `tobiishi/` — a path into a bin or into a
    unit, a dot segment, or a file there is not an open unit, and nothing changes."""
    repo = make_instance(tmp_path)
    write(repo, JOURNEY / "tobiishi" / "README.md", "readme\n")
    before = state(repo)
    with pytest.raises(drop.Refused):
        drop.check(repo, PROJECT, key, "gone", GIT)
    assert state(repo) == before and unit(repo).is_dir()


def test_check_refuses_an_unknown_key(tmp_path):
    repo = make_instance(tmp_path)
    before = state(repo)
    with pytest.raises(drop.Refused, match="no such open unit"):
        drop.check(repo, PROJECT, "2026-09-19_nowhere", "gone", GIT)
    assert state(repo) == before


@pytest.mark.parametrize("bin_name", ["trail", "drop"])
def test_check_refuses_trail_and_drop_as_keys(tmp_path, bin_name):
    repo = make_instance(tmp_path)
    write(repo, JOURNEY / "tobiishi" / "drop" / "2026-02-02_old" / "change_request.md", "old\n")
    with pytest.raises(drop.Refused, match="no such open unit"):
        drop.check(repo, PROJECT, bin_name, "gone", GIT)


def test_a_refusal_prints_and_exits_1(tmp_path, capsys):
    repo = make_instance(tmp_path)
    code, out, err = run(capsys, repo, "check", PROJECT, SEALED_KEY, "gone")
    assert code == 1 and out == "" and "sealed" in err


# --- check: CP-141 ---------------------------------------------------------------------------


def test_check_passes_a_clean_worktree_and_names_it(tmp_path, capsys):
    repo = make_instance(tmp_path)
    worktree = add_worktree(repo, KEY, ahead=1)
    code, out, _ = run(capsys, repo, "check", PROJECT, KEY, "subject gone upstream")
    assert code == 0 and str(worktree) in out


def test_check_refuses_a_dirty_instance_worktree(tmp_path):
    repo = make_instance(tmp_path)
    worktree = add_worktree(repo, KEY, ahead=1)
    dirty(worktree)
    before = state(repo)
    with pytest.raises(drop.Refused) as refusal:
        drop.check(repo, PROJECT, KEY, "gone", GIT)
    assert str(worktree) in str(refusal.value)
    assert unit(repo, "").is_dir() and worktree.is_dir()
    assert state(repo) == before


def test_check_refuses_an_untracked_file_in_a_worktree(tmp_path):
    repo = make_instance(tmp_path)
    worktree = add_worktree(repo, KEY)
    write(worktree, "scratch.txt", "not added\n")
    with pytest.raises(drop.Refused, match="uncommitted"):
        drop.check(repo, PROJECT, KEY, "gone", GIT)


def test_check_refuses_a_dirty_audit_worktree_and_names_every_dirty_one(tmp_path):
    repo = make_instance(tmp_path)
    worktree = add_worktree(repo, KEY, ahead=1)
    audit = add_worktree(repo, f"{KEY}__audit-specs", ahead=1)
    dirty(audit)
    with pytest.raises(drop.Refused) as only_audit:
        drop.check(repo, PROJECT, KEY, "gone", GIT)
    assert named(only_audit) == {str(audit)}
    dirty(worktree)
    with pytest.raises(drop.Refused) as both:
        drop.check(repo, PROJECT, KEY, "gone", GIT)
    assert named(both) == {str(audit), str(worktree)}
    assert worktree.is_dir() and audit.is_dir()


def test_check_refuses_a_dirty_product_worktree(tmp_path):
    product = make_product(tmp_path)
    repo = make_instance(tmp_path, product_path=str(product))
    write(product / ".worktrees" / KEY, "README.md", "edited\n")
    with pytest.raises(drop.Refused) as refusal:
        drop.check(repo, PROJECT, KEY, "gone", GIT)
    assert str(product / ".worktrees" / KEY) in str(refusal.value)


# --- apply: CP-139, CP-142 -------------------------------------------------------------------


def test_apply_moves_the_unit_into_tobiishi_drop_byte_identical(tmp_path, capsys):
    repo = make_instance(tmp_path)
    before = tree_bytes(unit(repo))
    assert not (repo / JOURNEY / "tobiishi" / "drop").exists()
    apply_output(capsys, repo)
    assert tree_bytes(unit(repo, "drop")) == before
    assert not unit(repo).exists()


def test_apply_marks_the_context_that_names_the_key(tmp_path, capsys):
    repo = make_instance(tmp_path)
    _, status = apply_output(capsys, repo)
    before = CONTEXT_OPEN.splitlines(keepends=True)
    after = (repo / CONTEXT).read_text(encoding="utf-8").splitlines(keepends=True)
    changed = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
    assert len(before) == len(after) and len(changed) == 1
    line = changed[0]
    assert (before[line], after[line]) == ("**Status:** Open\n", "**Status:** Dropped\n")
    assert status.startswith("context: marked")


@pytest.mark.parametrize("context", [CONTEXT_OPEN.replace(KEY, "2026-01-01_other"), None])
def test_apply_leaves_a_context_naming_another_key(tmp_path, capsys, context):
    repo = make_instance(tmp_path, context=context)
    _, status = apply_output(capsys, repo)
    assert status.startswith("context: not marked")
    if context is None:
        assert not (repo / CONTEXT).exists()
    else:
        assert (repo / CONTEXT).read_text(encoding="utf-8") == context


def test_apply_leaves_a_context_naming_a_longer_key_that_begins_with_this_one(tmp_path, capsys):
    """CP-142: a section that names a different key is untouched — and `<key>-follow-up` is a
    different unit's key, even though this unit's key is a prefix of it."""
    context = CONTEXT_OPEN.replace(KEY, f"{KEY}-follow-up")
    repo = make_instance(tmp_path, context=context)
    _, status = apply_output(capsys, repo)
    assert status.startswith("context: not marked")
    assert (repo / CONTEXT).read_bytes() == context.encode("utf-8")


def test_apply_marks_a_context_that_names_the_key_inside_a_path(tmp_path, capsys):
    """CP-142: the section names `<key>` when it cites the unit's folder, not only in backticks."""
    context = CONTEXT_OPEN.replace(f"`{KEY}`", f"`journey/tobiishi/{KEY}/change_request.md`")
    repo = make_instance(tmp_path, context=context)
    _, status = apply_output(capsys, repo)
    assert status.startswith("context: marked")
    assert "**Status:** Dropped\n" in (repo / CONTEXT).read_text(encoding="utf-8")


def test_apply_leaves_a_context_with_no_status_line(tmp_path, capsys):
    context = CONTEXT_OPEN.replace("**Status:** Open\n\n`", "`", 1)
    repo = make_instance(tmp_path, context=context)
    _, status = apply_output(capsys, repo)
    assert status.startswith("context: not marked")
    assert (repo / CONTEXT).read_bytes() == context.encode("utf-8")


def test_apply_prints_every_path_the_commit_declares(tmp_path, capsys):
    repo = make_instance(tmp_path)
    paths, _ = apply_output(capsys, repo)
    staged = set(git(repo, "diff", "--cached", "--name-only", "--no-renames").split())
    assert len(staged) == 4 and set(paths) == staged | {str(CONTEXT)}
    assert paths.count(str(CONTEXT)) == 1


def test_apply_prints_no_context_path_when_it_was_not_marked(tmp_path, capsys):
    repo = make_instance(tmp_path, context=None)
    paths, _ = apply_output(capsys, repo)
    staged = set(git(repo, "diff", "--cached", "--name-only", "--no-renames").split())
    assert set(paths) == staged


def test_apply_refuses_a_key_that_is_not_an_open_unit(tmp_path):
    repo = make_instance(tmp_path)
    before = state(repo)
    with pytest.raises(drop.Refused, match="sealed"):
        drop.apply(repo, PROJECT, SEALED_KEY, GIT)
    assert state(repo) == before


# --- close: CP-140, CP-144 -------------------------------------------------------------------


def apply_then_close(capsys, repo: Path) -> str:
    apply_output(capsys, repo)
    code, out, _ = run(capsys, repo, "close", PROJECT, KEY)
    assert code == 0
    return out


def test_full_tobiishi_drop_run_keeps_the_branch_unmerged(tmp_path, capsys):
    repo = make_instance(tmp_path)
    worktree = add_worktree(repo, KEY, ahead=3)
    prior = sha(repo, KEY)
    assert git(repo, "rev-list", "--count", f"main..{KEY}").strip() == "3"
    assert run(capsys, repo, "check", PROJECT, KEY, "subject gone upstream")[0] == 0
    paths, _ = apply_output(capsys, repo)
    git(repo, "add", "--", str(CONTEXT))
    git(repo, "commit", "-q", "-m", f"drop: {KEY}", "-m", "subject gone upstream")
    assert run(capsys, repo, "close", PROJECT, KEY)[0] == 0
    assert git(repo, "log", "-1", "--format=%s").strip() == f"drop: {KEY}"
    assert git(repo, "log", "-1", "--format=%b").strip() == "subject gone upstream"
    committed = set(git(repo, "show", "--name-only", "--no-renames", "--format=", "HEAD").split())
    assert committed == set(paths)
    assert not worktree.exists() and sha(repo, KEY) == prior
    assert KEY not in git(repo, "branch", "--merged", "main", "--format=%(refname:short)").split()


def test_close_removes_the_audit_worktree_and_keeps_its_branch(tmp_path, capsys):
    repo = make_instance(tmp_path)
    worktree = add_worktree(repo, KEY, ahead=1)
    audit = add_worktree(repo, f"{KEY}__audit-specs", ahead=2)
    prior = sha(repo, f"{KEY}__audit-specs")
    apply_then_close(capsys, repo)
    assert not audit.exists() and not worktree.exists()
    assert sha(repo, f"{KEY}__audit-specs") == prior


def test_close_removes_the_product_worktree_and_keeps_its_branch(tmp_path, capsys):
    product = make_product(tmp_path, ahead=2)
    repo = make_instance(tmp_path, product_path=str(product))
    prior = sha(product, KEY)
    out = apply_then_close(capsys, repo)
    assert not (product / ".worktrees" / KEY).exists()
    assert sha(product, KEY) == prior
    assert str(product / ".worktrees" / KEY) in out


def test_close_with_no_worktree_reports_nothing_to_close(tmp_path, capsys):
    repo = make_instance(tmp_path)
    out = apply_then_close(capsys, repo)
    assert "nothing to close" in out
    assert "worktree closed" not in out


def test_close_with_a_branch_but_no_worktree_keeps_it_and_never_denies_it(tmp_path, capsys):
    """CP-140/CP-144: with no worktree there is nothing to close, but a branch `<key>` that exists
    is kept — so any line of the report that speaks of a branch says it was kept."""
    repo = make_instance(tmp_path)
    git(repo, "branch", KEY)
    prior = sha(repo, KEY)
    out = apply_then_close(capsys, repo)
    assert sha(repo, KEY) == prior
    assert "nothing to close" in out
    assert all("kept" in line for line in out.splitlines() if "branch" in line)


def test_close_never_deletes_a_branch(tmp_path, capsys):
    repo = make_instance(tmp_path)
    add_worktree(repo, KEY, ahead=1)
    add_worktree(repo, f"{KEY}__audit-specs", ahead=1)
    before = branches(repo)
    apply_then_close(capsys, repo)
    assert before <= branches(repo)


def test_close_refuses_when_the_unit_is_not_in_drop_yet(tmp_path, capsys):
    repo = make_instance(tmp_path)
    worktree = add_worktree(repo, KEY)
    code, _, err = run(capsys, repo, "close", PROJECT, KEY)
    assert code == 1 and "apply" in err and worktree.is_dir()


def test_a_tobiishi_drop_leaves_station_seed_and_seal_untouched(tmp_path, capsys):
    repo = make_instance(tmp_path)
    add_worktree(repo, KEY, ahead=1)
    shukuba, nemawashi = repo / JOURNEY / "shukuba", repo / JOURNEY / "nemawashi"
    before = tree_bytes(shukuba), tree_bytes(nemawashi)
    apply_then_close(capsys, repo)
    assert (tree_bytes(shukuba), tree_bytes(nemawashi)) == before


# --- close: where the journey stands (CP-144) ------------------------------------------------


def test_close_reports_items_remaining_and_quotes_the_next(tmp_path, capsys):
    repo = make_instance(tmp_path, seed=SEED_TWO_LEFT)
    out = apply_then_close(capsys, repo)
    assert "still open" in out and "2 " in out and "second item" in out
    assert "retire" not in out.lower()


def test_close_reports_the_retire_owed_when_none_remain(tmp_path, capsys):
    repo = make_instance(tmp_path, seed=SEED_ALL_TICKED)
    out = apply_then_close(capsys, repo)
    assert "retire is owed to the Scrum Master (nemawashi-retire)" in out


def test_close_reports_no_active_seed(tmp_path, capsys):
    repo = make_instance(tmp_path, seed=None)
    out = apply_then_close(capsys, repo)
    assert "no active seed" in out


def test_close_reports_no_open_station(tmp_path, capsys):
    repo = make_instance(tmp_path, station=False)
    out = apply_then_close(capsys, repo)
    assert "no station is open" in out and "still open" not in out


def test_the_report_runs_in_order(tmp_path, capsys):
    repo = make_instance(tmp_path)
    add_worktree(repo, KEY, ahead=1)
    lines = apply_then_close(capsys, repo).splitlines()
    markers = ["dropped:", "worktree closed:", "branch kept:", "context:", "station:", "seed:"]
    positions = [next(i for i, line in enumerate(lines) if line.startswith(m)) for m in markers]
    assert positions == sorted(positions) and len(set(positions)) == len(markers)
    assert str(JOURNEY / "tobiishi" / "drop" / KEY) in lines[positions[0]]
    assert lines[positions[3]].startswith("context: marked")
