"""pick.py's checks, through its injected git runner — no real repo is touched."""

import sys
from datetime import date
from pathlib import Path

import subprocess

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import pick  # noqa: E402

PROJECT = "demo"


class FakeGit:
    def __init__(self, status: str = ""):
        self.status = status
        self.calls: list[list[str]] = []

    def __call__(self, root: Path, args: list[str]) -> str:
        self.calls.append(args)
        if args[0] == "status":
            return self.status
        if args[0] == "mv":
            (root / args[1]).rename(root / args[2])
        return ""


def _journey(root: Path) -> Path:
    j = root / "system" / "projects" / PROJECT / "journey"
    for d in ("nemawashi/unpicked", "nemawashi/trail", "nemawashi/drop",
              "shukuba/parked", "shukuba/trail", "tobiishi/trail"):
        (j / d).mkdir(parents=True)
    (j / "nemawashi" / "README.md").write_text("readme")
    (j / "shukuba" / "README.md").write_text("readme")
    return j


def _seed(j: Path, name: str, body: str = "- [ ] a station\n") -> None:
    (j / "nemawashi" / "unpicked" / f"{name}.md").write_text(body)


def _record(seed: str, condition: str = "none") -> str:
    return f"Seed: {seed}\nCondition: {condition}\n\nWhy: it is next.\n"


def test_check_lists_the_pool(tmp_path):
    j = _journey(tmp_path)
    _seed(j, "2026-09-01_a")
    _seed(j, "2026-09-02_b")
    assert pick.check(tmp_path, PROJECT, FakeGit()) == ["2026-09-01_a", "2026-09-02_b"]


def test_apply_moves_the_one_seed_to_the_root(tmp_path):
    j = _journey(tmp_path)
    _seed(j, "2026-09-01_a")
    _seed(j, "2026-09-02_b")
    git = FakeGit()
    old, new = pick.apply(tmp_path, PROJECT, _record("2026-09-01_a"), git)
    assert (tmp_path / new).exists() and not (tmp_path / old).exists()
    assert (j / "nemawashi" / "unpicked" / "2026-09-02_b.md").exists()
    assert [c[0] for c in git.calls].count("mv") == 1


def test_apply_moves_a_folder_seed_whole(tmp_path):
    j = _journey(tmp_path)
    folder = j / "nemawashi" / "unpicked" / "2026-09-01_a"
    folder.mkdir()
    (folder / "seed.md").write_text("- [ ] a station\n")
    _, new = pick.apply(tmp_path, PROJECT, _record("2026-09-01_a"), FakeGit())
    assert (tmp_path / new / "seed.md").exists()


@pytest.mark.parametrize(
    "arrange, record, reason",
    [
        (lambda j: _seed(j, "x"), _record("missing"), "not exactly one seed"),
        (lambda j: _seed(j, "x"), "Seed: x\nSeed: y\nCondition: none\n", "exactly one seed"),
        (lambda j: _seed(j, "x"), "Condition: none\n", "exactly one seed"),
        (lambda j: _seed(j, "x"), "Seed: x\n", "Condition"),
        (lambda j: _seed(j, "x"), _record("x", "waits on y"), "prevents starting"),
        (lambda j: _seed(j, "x", "- [x] done\n"), _record("x"), "fully walked"),
        (lambda j: (_seed(j, "x"), (j / "nemawashi" / "trail" / "x.md").write_text("")),
         _record("x"), "also in trail"),
    ],
)
def test_apply_refuses_an_invalid_selection(tmp_path, arrange, record, reason):
    j = _journey(tmp_path)
    arrange(j)
    git = FakeGit()
    with pytest.raises(pick.Refused, match=reason):
        pick.apply(tmp_path, PROJECT, record, git)
    assert not any(c[0] == "mv" for c in git.calls)


@pytest.mark.parametrize(
    "arrange, status, reason",
    [
        (lambda j: (j / "nemawashi" / "2026-09-03_active.md").write_text(""), "", "already active"),
        (lambda j: (j / "shukuba" / "2026-09-03_station.md").write_text(""), "", "station is open"),
        (lambda j: (j / "tobiishi" / "2026-09-03_unit").mkdir(), "", "change unit is open"),
        (lambda j: None, " M somefile\n", "not clean"),
    ],
)
def test_check_refuses_a_journey_not_ready(tmp_path, arrange, status, reason):
    j = _journey(tmp_path)
    _seed(j, "x")
    arrange(j)
    with pytest.raises(pick.Refused, match=reason):
        pick.check(tmp_path, PROJECT, FakeGit(status))


def test_check_reads_only_the_projects_journey_and_the_ppm_context(tmp_path):
    j = _journey(tmp_path)
    _seed(j, "2026-09-01_a")
    git = FakeGit()
    pick.check(tmp_path, PROJECT, git)
    status = [c for c in git.calls if c[0] == "status"]
    assert status == [["status", "--porcelain", "--",
                       str(Path("system") / "projects" / PROJECT / "journey"),
                       str(Path("system") / "contexts" / "CONTEXT_PPM.md")]]


def test_check_ignores_another_projects_edit_in_a_real_checkout(tmp_path):
    j = _journey(tmp_path)
    _seed(j, "2026-09-01_a")
    other = tmp_path / "products" / "other" / "docs"
    other.mkdir(parents=True)
    (other / "notes.md").write_text("x")
    for args in (["init", "-q"], ["add", "-A"],
                 ["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "base"]):
        subprocess.run(["git", "-C", str(tmp_path), *args], check=True)
    (other / "notes.md").write_text("edited by another project's walk")
    assert pick.check(tmp_path, PROJECT, pick.run_git) == ["2026-09-01_a"]
    (j / "nemawashi" / "unpicked" / "2026-09-01_a.md").write_text("edited")
    with pytest.raises(pick.Refused, match="not clean"):
        pick.check(tmp_path, PROJECT, pick.run_git)


def test_check_passes_with_tobiishi_trail_and_drop_only(tmp_path):
    j = _journey(tmp_path)
    _seed(j, "2026-09-01_a")
    (j / "tobiishi" / "drop" / "2026-09-19_x").mkdir(parents=True)
    assert pick.check(tmp_path, PROJECT, FakeGit()) == ["2026-09-01_a"]


def test_check_refuses_an_open_unit_beside_tobiishi_drop(tmp_path):
    j = _journey(tmp_path)
    _seed(j, "2026-09-01_a")
    (j / "tobiishi" / "drop" / "2026-09-19_x").mkdir(parents=True)
    (j / "tobiishi" / "2026-09-19_x").mkdir()
    with pytest.raises(pick.Refused, match="a change unit is open: 2026-09-19_x"):
        pick.check(tmp_path, PROJECT, FakeGit())


def test_check_refuses_an_empty_pool(tmp_path):
    _journey(tmp_path)
    with pytest.raises(pick.Refused, match="pool is empty"):
        pick.check(tmp_path, PROJECT, FakeGit())


def test_check_refuses_an_unknown_project(tmp_path):
    with pytest.raises(pick.Refused, match="no seedbed"):
        pick.check(tmp_path, PROJECT, FakeGit())


def test_main_prints_a_refusal_and_exits_1(tmp_path, capsys):
    _journey(tmp_path)
    assert pick.main(["--root", str(tmp_path), "--project", PROJECT, "check"], git=FakeGit()) == 1
    assert "REFUSED" in capsys.readouterr().err


TODAY = date(2026, 9, 17)
CONTEXT = """# CONTEXT_PPM

**Updated:** 2026-09-01

## Picked seeds

## In flight

- hand-written.
"""


def _context(root: Path, text: str = CONTEXT) -> Path:
    path = root / pick.PPM_CONTEXT
    path.parent.mkdir(parents=True)
    path.write_text(text)
    return path


def test_record_appends_the_pick_to_an_empty_section(tmp_path):
    path = _context(tmp_path)
    assert pick.record_in_ppm_context(tmp_path, PROJECT, "2026-09-01_a", TODAY) == pick.PPM_CONTEXT
    assert path.read_text() == CONTEXT.replace(
        "## Picked seeds\n",
        "## Picked seeds\n\n- `demo · nemawashi · 2026-09-01_a` — picked 2026-09-17\n",
    )


def test_record_keeps_another_projects_pick_and_appends_below_it(tmp_path):
    other = "- `other · nemawashi · 2026-08-01_z` — picked 2026-08-02\n"
    before = CONTEXT.replace("## Picked seeds\n", f"## Picked seeds\n\n{other}")
    path = _context(tmp_path, before)
    pick.record_in_ppm_context(tmp_path, PROJECT, "2026-09-01_a", TODAY)
    assert path.read_text() == before.replace(
        other, other + "- `demo · nemawashi · 2026-09-01_a` — picked 2026-09-17\n"
    )


def test_record_skips_an_instance_with_no_context(tmp_path):
    assert pick.record_in_ppm_context(tmp_path, PROJECT, "2026-09-01_a", TODAY) is None


def test_record_skips_a_context_with_no_picked_section(tmp_path):
    text = CONTEXT.replace("## Picked seeds\n\n", "")
    path = _context(tmp_path, text)
    assert pick.record_in_ppm_context(tmp_path, PROJECT, "2026-09-01_a", TODAY) is None
    assert path.read_text() == text


def _apply_via_main(tmp_path, capsys) -> list[str]:
    j = _journey(tmp_path)
    _seed(j, "2026-09-01_a")
    record = tmp_path / "record.txt"
    record.write_text(_record("2026-09-01_a"))
    argv = ["--root", str(tmp_path), "--project", PROJECT, "apply", "--record", str(record)]
    assert pick.main(argv, git=FakeGit(), today=TODAY) == 0
    return capsys.readouterr().out.splitlines()


def test_main_prints_the_context_path_third(tmp_path, capsys):
    path = _context(tmp_path)
    out = _apply_via_main(tmp_path, capsys)
    assert out[2] == str(pick.PPM_CONTEXT)
    assert "`demo · nemawashi · 2026-09-01_a`" in path.read_text()


def test_main_prints_a_skip_and_still_moves_the_seed(tmp_path, capsys):
    out = _apply_via_main(tmp_path, capsys)
    assert out[2] == "no PPM context — skipped"
    assert (tmp_path / out[1]).exists()


def test_record_appends_to_a_last_section_with_no_trailing_newline(tmp_path):
    other = "- `other · nemawashi · 2026-08-01_z` — picked 2026-08-02"
    path = _context(tmp_path, f"# CONTEXT_PPM\n\n## Picked seeds\n\n{other}")
    pick.record_in_ppm_context(tmp_path, PROJECT, "2026-09-01_a", TODAY)
    assert path.read_text() == (
        f"# CONTEXT_PPM\n\n## Picked seeds\n\n{other}\n"
        "- `demo · nemawashi · 2026-09-01_a` — picked 2026-09-17\n"
    )


def test_main_prints_a_skip_for_a_context_with_no_picked_section(tmp_path, capsys):
    _context(tmp_path, CONTEXT.replace("## Picked seeds\n\n", ""))
    assert _apply_via_main(tmp_path, capsys)[2] == "no PPM context — skipped"
